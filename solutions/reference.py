"""Solución de referencia del caso de transporte, en Pandas.

Qué calcula
    Siete tablas de resultado a partir de los cuatro CSV de un caso:

    | Tabla | Grano | Contenido |
    | --- | --- | --- |
    | `calidad` | indicador | recuentos de defectos del archivo |
    | `demanda` | operador | pasajeros y viajes con dato |
    | `demanda_hora` | hora de inicio | pasajeros |
    | `duracion` | recorrido | media, mediana, P90 y puntualidad |
    | `cumplimiento` | recorrido × día | programados, realizados y porcentaje |
    | `cumplimiento_operador` | operador | programados, realizados y porcentaje |
    | `realizados_recorrido` | recorrido | viajes realizados |

Reglas aplicadas, tomadas de `docs/diccionario.md`
    1. Se eliminan duplicados exactos antes de contar.
    2. Las claves desconocidas se excluyen de los indicadores por recorrido y se
       reportan aparte en la tabla de calidad.
    3. Un viaje realizado con `pasajeros` nulo o negativo **se conserva** para los
       indicadores operacionales —el viaje ocurrió— y se excluye de las sumas de
       pasajeros.
    4. Los viajes cancelados se excluyen de duración y de demanda.
    5. Una duración es válida si `fin >= inicio`.
    6. El cumplimiento es `realizados / programados` y **no** se recorta a 100 %.
    7. No se imputa ningún valor.

    La puntualidad definida como `duración <= meta` es **pedagógica** y no corresponde
    al indicador oficial de ningún sistema de transporte.

Por qué el código usa banderas y no filtros sucesivos
    Cada indicador tiene su propio conjunto válido: la demanda excluye los viajes sin
    conteo de pasajeros, pero el cumplimiento los incluye. Si el código fuera
    reasignando `t = t[...]`, a la mitad del archivo nadie sabría qué filas quedaron.
    Con banderas explícitas (`done`, `bad_pax`, `bad_duration`), cada cálculo declara
    su propio filtro en el momento de ejecutarse, y la tabla de calidad sale de contar
    esas mismas banderas.

Cómo se valida
    - `tests/test_reference.py` comprueba invariantes del procesamiento.
    - `tests/test_cross_validation.py` confronta cada indicador contra
      `solutions/sql_reference.py`, una implementación independiente en SQL, con
      tolerancia 1e-9.
    - La mediana y el P90 se comparan además contra una implementación en Python puro.

Uso
    python solutions/reference.py 1
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def analyze(case: int) -> dict[str, pd.DataFrame]:
    """Calcula las siete tablas de resultado del caso indicado.

    Args:
        case: número de caso (1, 2 o 3).

    Returns:
        Diccionario de tablas, con las claves documentadas en el encabezado del módulo.
    """
    folder = ROOT / "data" / f"case_{case}"
    trips = pd.read_csv(folder / "viajes.csv")
    routes = pd.read_csv(folder / "recorridos.csv")
    operators = pd.read_csv(folder / "operadores.csv")
    schedule = pd.read_csv(folder / "programacion.csv")

    # --- Regla 1: duplicados exactos, contados antes de eliminarlos ---------------
    original = len(trips)
    t = trips.drop_duplicates().copy()

    # --- Conversión defensiva: lo no convertible queda nulo, no cero ---------------
    t["pasajeros"] = pd.to_numeric(t.pasajeros, errors="coerce")
    for column in ("inicio", "fin"):
        t[column] = pd.to_datetime(t[column], errors="coerce")

    # --- Cruce con control de cardinalidad -----------------------------------------
    # validate='many_to_one' falla si un catálogo tiene su clave repetida, en lugar de
    # duplicar filas en silencio e inflar las sumas.
    t = (t.merge(routes, on="recorrido_id", how="left", validate="many_to_one")
          .merge(operators, on="operador_id", how="left", validate="many_to_one"))

    # --- Banderas de validez, una por regla ----------------------------------------
    done = t.estado.eq("REALIZADO")
    bad_pax = t.pasajeros.isna() | t.pasajeros.lt(0)
    t["duracion_min"] = (t.fin - t.inicio).dt.total_seconds() / 60
    bad_duration = t.duracion_min.isna() | t.duracion_min.lt(0)

    # --- Tabla de calidad: cada defecto con su recuento ----------------------------
    quality = pd.DataFrame({
        "indicador": [
            "filas_originales",
            "duplicados_exactos",
            "claves_desconocidas",
            "pasajeros_invalidos_realizados",
            "duracion_invalida_realizados",
        ],
        "valor": [
            original,
            original - len(t),
            int(t.operador_id.isna().sum()),
            int((done & bad_pax).sum()),
            int((done & bad_duration).sum()),
        ],
    })

    # --- Base operacional: realizados con clave conocida (regla 2 y 4) -------------
    # Conserva los viajes con pasajeros inválidos: el viaje ocurrió (regla 3).
    valid = t.loc[done & t.operador_id.notna()].copy()
    valid["dia_octubre"] = valid.inicio.dt.day
    valid["hora"] = valid.inicio.dt.hour

    # --- Demanda: excluye los viajes sin conteo válido (regla 3) -------------------
    with_pax = valid.loc[~bad_pax.loc[valid.index]]
    demand = (with_pax.groupby("operador")
                      .agg(pasajeros=("pasajeros", "sum"),
                           viajes_con_dato=("viaje_id", "size"))
                      .reset_index())
    hour = with_pax.groupby("hora").pasajeros.sum().reset_index()

    # --- Duración: excluye las duraciones inválidas (regla 5) ----------------------
    dur = valid.loc[~bad_duration.loc[valid.index]].copy()
    dur["puntual"] = dur.duracion_min.le(dur.meta_min)
    duration = (dur.groupby("recorrido_id")
                   .agg(media_min=("duracion_min", "mean"),
                        mediana_min=("duracion_min", "median"),
                        p90_min=("duracion_min", lambda s: s.quantile(0.9)),
                        puntualidad_pct=("puntual", lambda s: 100 * s.mean()))
                   .reset_index())

    # --- Cumplimiento (regla 6) ----------------------------------------------------
    # Cruce externo: conserva los días programados sin viajes (realizados = 0) y
    # detecta viajes en días no programados, que son dos defectos distintos.
    counts = valid.groupby(["recorrido_id", "dia_octubre"]).size().rename("realizados").reset_index()
    compliance = schedule.merge(counts, on=["recorrido_id", "dia_octubre"],
                                how="outer", validate="one_to_one")
    compliance["realizados"] = compliance.realizados.fillna(0).astype(int)
    # División protegida: sin viajes programados no hay indicador, y eso es distinto
    # de un cumplimiento del 0 %.
    compliance["cumplimiento_pct"] = (
        100 * compliance.realizados
        / compliance.viajes_programados.where(compliance.viajes_programados.gt(0))
    )

    # Cumplimiento por operador: suma de realizados sobre suma de programados. No es
    # el promedio de los porcentajes diarios, que daría peso igual a un día con tres
    # viajes programados y a otro con trescientos.
    op = (compliance.merge(routes, on="recorrido_id", validate="many_to_one")
                    .merge(operators, on="operador_id", validate="many_to_one")
                    .groupby("operador")[["realizados", "viajes_programados"]]
                    .sum()
                    .reset_index())
    op["cumplimiento_pct"] = 100 * op.realizados / op.viajes_programados

    return {
        "calidad": quality,
        "demanda": demand,
        "demanda_hora": hour,
        "duracion": duration,
        "cumplimiento": compliance,
        "cumplimiento_operador": op,
        "realizados_recorrido": valid.groupby("recorrido_id").size()
                                     .rename("realizados").reset_index(),
    }


def export(case: int) -> Path:
    """Escribe las siete tablas en `reference_outputs/case_<n>/`, en CSV y en Excel."""
    tables = analyze(case)
    out = ROOT / "reference_outputs" / f"case_{case}"
    out.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out / "resultados_referencia.xlsx", engine="xlsxwriter") as writer:
        for name, df in tables.items():
            df.to_excel(writer, sheet_name=name, index=False)
            df.to_csv(out / f"{name}.csv", index=False)
            writer.sheets[name].freeze_panes(1, 0)
            writer.sheets[name].set_column(0, len(df.columns) - 1, 24)
    return out


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    from lab.console import enable_utf8

    enable_utf8()
    if len(sys.argv) < 2:
        print("Uso: python solutions/reference.py <1|2|3>")
        raise SystemExit(2)
    numero = int(sys.argv[1])
    destino = export(numero)
    resultados = analyze(numero)
    print(resultados["calidad"].to_string(index=False))
    print()
    print(resultados["demanda"].to_string(index=False))
    print(f"\nResultados escritos en {destino.relative_to(ROOT)}")
