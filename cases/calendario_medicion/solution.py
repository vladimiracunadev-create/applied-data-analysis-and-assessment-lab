"""P11: reconstruir el calendario de medición de un indicador oficial.

El problema
    El «Índice de variación de tiempos de viaje de las personas en ejes de la red vial
    básica de la ciudad de Santiago» tiene una fórmula de dos líneas y **siete reglas
    de exclusión** en su nota al pie. La pregunta: **para un año dado, ¿qué días entran
    en la medición?**

    Es la pregunta que decide el denominador del indicador. Y no se puede contestar
    mirando los datos: hay que leer la metodología.

Las reglas, textuales
    Del documento de DIPRES «VERSIÓN LEY AÑO 2019», Partida 19, nota 1 del indicador:

        «Con el objetivo de homologar la metodología de cálculo empleada por DTPM con
        la utilizada por la UOCT, se consideran sólo días laborales, descartando los
        siguientes casos: Días feriados; Todos los días de los meses de enero, febrero
        y diciembre; Vacaciones de invierno (dos semanas, considerando los calendarios
        escolares); Semana de fiestas patrias; 11 de septiembre; Día del joven
        combatiente. Dado que en algunas ocasiones los incidentes inician en la tarde
        del día anterior, se descartan todos los datos de los días 28 y 29.»

    Y, aparte de las exclusiones, la medición tiene su propio calendario:

        «Las mediciones se efectúan trimestralmente, en los meses de marzo, junio,
        septiembre y noviembre.»

Lo que la reconstrucción revela
    Dos redundancias que no se ven leyendo la lista, y que solo aparecen al medir el
    aporte **exclusivo** de cada regla:

    1. **«Día del joven combatiente» no excluye nada nuevo.** Es el 29 de marzo, y la
       regla de los días 28 y 29 ya lo descarta. Su exclusión exclusiva es cero.
    2. **Excluir enero, febrero y diciembre no afecta a la medición.** Como solo se mide
       en marzo, junio, septiembre y noviembre, esos tres meses estaban fuera de todas
       formas. La regla es redundante respecto del calendario trimestral.

    Ninguna de las dos es un error de la metodología: una regla redundante puede existir
    por prudencia o por herencia histórica. Pero quien reproduce el indicador necesita
    saberlo, porque son dos reglas que puede omitir sin cambiar un solo día.

    Y una tercera cosa, que es la más importante: **la regla de los días 28 y 29 es la
    que más excluye** después de los fines de semana, y es la que nadie adivina.

Tecnologías y por qué estas
    - **`lab.calendars`**: reglas como objetos, con su fuente declarada, de modo que el
      calendario se pueda regenerar, auditar y comparar entre años.
    - **`lab.calendars.easter_sunday`** para validar la parte movible del listado de
      feriados de forma independiente, en lugar de confiar en él.
    - **Un CSV versionado** para los feriados, no una llamada a la API en cada
      ejecución: depender de un servicio de tercero haría el caso irreproducible el día
      que ese servicio desaparezca.
    - **Pandas** y nada más. El problema no es de volumen —son 365 filas— es de
      precisión en las reglas.

Advertencia sobre los feriados
    El listado proviene de un **tercero**, no de la fuente oficial. La API del gobierno
    no resolvía al momento de construir este caso. La parte movible se valida contra el
    cálculo de Pascua; el resto queda declarado como no verificado contra la ley.

Advertencia sobre las vacaciones de invierno
    La metodología dice «dos semanas, considerando los calendarios escolares», sin
    fechas. El calendario escolar cambia cada año y no se obtuvo. **Aquí se declara un
    supuesto** —las dos semanas que empiezan el primer lunes completo de julio— y se
    mide cuánto cambia el resultado si esas fechas se mueven. Un supuesto medido es
    defendible; uno escondido, no.

Reproducir
    python -m cases.calendario_medicion.solution
    python -m cases.calendario_medicion.solution --actualizar-feriados 2026
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lab.calendars import (  # noqa: E402
    DayRule,
    build_calendar,
    by_month,
    date_ranges,
    days_of_month,
    easter_sunday,
    exclusion_report,
    intersect_with,
    overlap_matrix,
    specific_dates,
    summary,
    weekends,
    weeks_containing,
    whole_months,
)
from lab.metrics import indicator_table, safe_ratio  # noqa: E402

HERE = Path(__file__).resolve().parent
FERIADOS = HERE / "feriados.csv"
RESULTS = HERE / "resultados"

#: Cita de la que salen las reglas. Cada regla la lleva en su campo `source`.
CITA = ("DIPRES, «VERSIÓN LEY AÑO 2019», Partida 19 Ministerio de Transporte y "
        "Telecomunicaciones, Capítulo 01, nota 1 del indicador de variación de tiempos "
        "de viaje")

#: Meses en que se mide, según la misma nota.
MESES_DE_MEDICION: tuple[int, ...] = (3, 6, 9, 11)

#: Los tres meses que la metodología excluye por completo.
MESES_EXCLUIDOS: tuple[int, ...] = (1, 2, 12)

#: Supuesto sobre las vacaciones de invierno. La metodología no da fechas.
SUPUESTO_INVIERNO = (
    "Dos semanas que comienzan el primer lunes completo de julio. La metodología dice "
    "«dos semanas, considerando los calendarios escolares» sin precisar fechas, y el "
    "calendario escolar del año no se obtuvo."
)


# -------------------------------------------------------------------------- feriados
def actualizar_feriados(year: int, destino: Path = FERIADOS) -> Path:
    """Descarga el listado de feriados de un año y lo deja versionado, ya validado.

    Valida la parte movible contra `easter_sunday` antes de escribir: si el Viernes
    Santo del listado no coincide con el cálculo, no se guarda. Un listado de feriados
    es un dato de entrada, y un dato de entrada que no pasa su propia validación no
    entra.

    Raises:
        ValueError: si el listado no contiene el Viernes Santo calculado.
    """
    import urllib.request

    from lab.sources import feriados_cl

    fuente = feriados_cl(year)
    with urllib.request.urlopen(fuente.url, timeout=60) as respuesta:  # noqa: S310
        payload = json.load(respuesta)
    if payload.get("status") != "success" or not payload.get("data"):
        raise ValueError(f"El servicio no devolvió datos para {year}: {payload!r}")

    tabla = pd.DataFrame(payload["data"])[["date", "title", "inalienable"]]
    tabla.columns = ["fecha", "nombre", "irrenunciable"]
    tabla["anio"] = year
    tabla["fuente"] = fuente.publisher
    tabla["url"] = fuente.url

    pascua = easter_sunday(year)
    viernes_santo = (pascua - timedelta(days=2)).isoformat()
    sabado_santo = (pascua - timedelta(days=1)).isoformat()
    fechas = set(tabla["fecha"])
    if viernes_santo not in fechas:
        raise ValueError(
            f"El listado de {year} no contiene el Viernes Santo calculado "
            f"({viernes_santo}). No se guardó: un listado que no pasa su propia "
            "validación no entra."
        )
    tabla["validado_contra_pascua"] = tabla["fecha"].isin({viernes_santo, sabado_santo})

    destino.parent.mkdir(parents=True, exist_ok=True)
    existente = cargar_feriados(destino) if destino.exists() else None
    if existente is not None:
        conservar = existente.loc[existente["anio"].ne(year)]
        tabla = pd.concat([conservar, tabla], ignore_index=True)
    tabla = tabla.sort_values("fecha").reset_index(drop=True)
    tabla.to_csv(destino, index=False, encoding="utf-8")
    return destino


def cargar_feriados(origen: Path = FERIADOS) -> pd.DataFrame:
    """Lee el listado versionado de feriados.

    Raises:
        FileNotFoundError: con el comando que lo genera.
    """
    if not Path(origen).exists():
        raise FileNotFoundError(
            f"No existe {origen}. Genérelo con:\n"
            "  python -m cases.calendario_medicion.solution --actualizar-feriados 2026"
        )
    return pd.read_csv(origen, dtype={"fecha": str, "nombre": str})


def validar_feriados(feriados: pd.DataFrame, year: int) -> pd.DataFrame:
    """Comprueba el listado contra lo que se puede verificar por cuenta propia.

    Dos comprobaciones independientes del listado:

    - **Pascua**: Viernes Santo y Sábado Santo se calculan con un algoritmo determinista
      y se contrastan con las fechas del listado.
    - **Fechas fijas por ley**: un conjunto de feriados cae siempre en la misma fecha.
      Su ausencia indica un listado incompleto.

    Lo que **no** se puede verificar aquí son los feriados movibles por la Ley 19.973,
    que se trasladan al lunes según el día de la semana en que caen. Queda declarado.
    """
    del_anio = feriados.loc[feriados["anio"].eq(year)]
    pascua = easter_sunday(year)
    fechas = set(del_anio["fecha"])

    fijos = {
        "01-01": "Año Nuevo",
        "05-01": "Día Nacional del Trabajo",
        "05-21": "Día de las Glorias Navales",
        "07-16": "Virgen del Carmen",
        "08-15": "Asunción de la Virgen",
        "09-18": "Independencia Nacional",
        "09-19": "Glorias del Ejército",
        "11-01": "Día de Todos los Santos",
        "12-08": "Inmaculada Concepción",
        "12-25": "Navidad",
    }
    filas = [
        {"comprobacion": "cantidad de feriados en el listado",
         "resultado": len(del_anio), "veredicto": "—"},
        {"comprobacion": f"Domingo de Pascua calculado ({pascua.isoformat()})",
         "resultado": "no es feriado por sí mismo", "veredicto": "—"},
        {"comprobacion": "Viernes Santo coincide con el cálculo",
         "resultado": (pascua - timedelta(days=2)).isoformat(),
         "veredicto": "sí" if (pascua - timedelta(days=2)).isoformat() in fechas else "NO"},
        {"comprobacion": "Sábado Santo coincide con el cálculo",
         "resultado": (pascua - timedelta(days=1)).isoformat(),
         "veredicto": "sí" if (pascua - timedelta(days=1)).isoformat() in fechas else "NO"},
    ]
    faltantes = [
        nombre for sufijo, nombre in fijos.items()
        if f"{year}-{sufijo}" not in fechas
    ]
    filas.append({
        "comprobacion": f"feriados de fecha fija presentes ({len(fijos)} esperados)",
        "resultado": f"{len(fijos) - len(faltantes)} de {len(fijos)}",
        "veredicto": "sí" if not faltantes else f"faltan: {', '.join(faltantes)}",
    })
    filas.append({
        "comprobacion": "feriados movibles por Ley 19.973",
        "resultado": "no verificable con los medios de este caso",
        "veredicto": "declarado",
    })
    return pd.DataFrame(filas)


# ----------------------------------------------------------------------------- reglas
def _primer_lunes_completo_de_julio(year: int) -> date:
    """Primer lunes de julio cuya semana completa cae dentro del mes."""
    dia = date(year, 7, 1)
    while dia.weekday() != 0:
        dia += timedelta(days=1)
    return dia


def reglas_oficiales(
    year: int,
    feriados: pd.DataFrame | None = None,
    inicio_invierno: date | None = None,
    semanas_invierno: int = 2,
) -> tuple[DayRule, ...]:
    """Las ocho reglas del calendario de medición, cada una con su fuente.

    Args:
        year: año a construir.
        feriados: listado versionado; si no se pasa, se carga del CSV.
        inicio_invierno: primer día de las vacaciones de invierno. Si no se indica, se
            aplica el supuesto declarado en `SUPUESTO_INVIERNO`.
        semanas_invierno: cuántas semanas duran. La metodología dice dos.

    Returns:
        Las reglas en el orden en que aparecen en la metodología citada.
    """
    listado = feriados if feriados is not None else cargar_feriados()
    del_anio = listado.loc[listado["anio"].eq(year), "fecha"]

    arranque = inicio_invierno or _primer_lunes_completo_de_julio(year)
    fin_invierno = arranque + timedelta(days=7 * semanas_invierno - 1)

    return (
        weekends(source=f"{CITA}: «se consideran sólo días laborales»"),
        specific_dates(
            del_anio, name="feriados",
            description=f"Feriados legales de {year} según el listado versionado",
            source=f"{CITA}: «Días feriados»",
        ),
        whole_months(
            MESES_EXCLUIDOS,
            source=f"{CITA}: «Todos los días de los meses de enero, febrero y diciembre»",
        ),
        date_ranges(
            [(arranque, fin_invierno)],
            name="vacaciones_invierno",
            description=(f"{semanas_invierno} semanas desde {arranque.isoformat()} "
                         f"hasta {fin_invierno.isoformat()} (SUPUESTO)"),
            source=f"{CITA}: «Vacaciones de invierno (dos semanas, considerando los "
                   "calendarios escolares)». Fechas no especificadas: supuesto propio",
        ),
        weeks_containing(
            [date(year, 9, 18)],
            name="semana_fiestas_patrias",
            description="Semana de lunes a domingo que contiene el 18 de septiembre",
            source=f"{CITA}: «Semana de fiestas patrias»",
        ),
        specific_dates(
            [date(year, 9, 11)], name="once_de_septiembre",
            description="11 de septiembre",
            source=f"{CITA}: «11 de septiembre»",
        ),
        specific_dates(
            [date(year, 3, 29)], name="dia_joven_combatiente",
            description="29 de marzo, Día del joven combatiente",
            source=f"{CITA}: «Día del joven combatiente»",
        ),
        days_of_month(
            (28, 29), name="dias_28_y_29",
            description="Días 28 y 29 de cada mes",
            source=f"{CITA}: «Dado que en algunas ocasiones los incidentes inician en "
                   "la tarde del día anterior, se descartan todos los datos de los "
                   "días 28 y 29»",
        ),
    )


# ------------------------------------------------------------------------ construcción
def construir(year: int = 2026, **kwargs):
    """Calendario de medición del año indicado."""
    reglas = reglas_oficiales(year, **kwargs)
    return build_calendar(date(year, 1, 1), date(year, 12, 31), reglas)


def dias_medibles(year: int = 2026, **kwargs) -> pd.DataFrame:
    """Cruce del calendario con los meses en que efectivamente se mide."""
    return intersect_with(construir(year, **kwargs), MESES_DE_MEDICION)


def resumen_medicion(year: int = 2026, **kwargs) -> pd.DataFrame:
    """Indicadores del calendario, incluido el efecto del cruce con los trimestres."""
    marco = dias_medibles(year, **kwargs)
    laborales = int((~marco["dia_semana"].isin((5, 6))).sum())
    elegibles = int(marco["incluido"].sum())
    medibles = int(marco["medible"].sum())
    en_meses = int(marco["mes_de_medicion"].sum())
    laborales_en_meses = int(
        (marco["mes_de_medicion"] & ~marco["dia_semana"].isin((5, 6))).sum()
    )
    return indicator_table({
        "dias_del_anio": (len(marco), "días", "Días calendario del año"),
        "dias_laborales": (laborales, "días", "De lunes a viernes"),
        "dias_elegibles": (elegibles, "días",
                           "Tras aplicar las ocho reglas de exclusión"),
        "dias_en_meses_de_medicion": (en_meses, "días",
                                      "Marzo, junio, septiembre y noviembre"),
        "laborales_en_meses_de_medicion": (laborales_en_meses, "días",
                                           "Días laborales de esos cuatro meses"),
        "dias_medibles": (medibles, "días",
                          "Elegibles Y en un mes de medición: el denominador real"),
        "retencion_sobre_laborales_pct": (
            float(safe_ratio(elegibles, laborales, scale=100)), "%",
            "Qué proporción de los días laborales sobrevive a las exclusiones"),
        "medibles_sobre_laborales_del_trimestre_pct": (
            float(safe_ratio(medibles, laborales_en_meses, scale=100)), "%",
            "Proporción de los días laborales de los cuatro meses que es medible"),
    })


def aporte_sobre_medibles(year: int = 2026, **kwargs) -> pd.DataFrame:
    """Cuántos días medibles recuperaría el quitar cada regla, una por una.

    Es la medida que de verdad importa, y es distinta de la exclusión exclusiva sobre
    el año completo. Una regla puede excluir muchos días del año y **ninguno** de los
    días que se miden, si esos días caían fuera de los meses de medición de todas
    formas.

    El caso claro es excluir enero, febrero y diciembre: descarta 90 días del año, 58
    de ellos en exclusiva, y **cero** días medibles, porque la medición solo ocurre en
    marzo, junio, septiembre y noviembre. La regla es redundante respecto del
    calendario trimestral.

    Returns:
        Una fila por regla con su aporte al denominador real, ordenadas de mayor a
        menor, más la columna que marca las reglas sin efecto.
    """
    reglas = reglas_oficiales(year, **kwargs)
    base = int(intersect_with(build_calendar(date(year, 1, 1), date(year, 12, 31), reglas),
                              MESES_DE_MEDICION)["medible"].sum())
    filas = []
    for omitida in reglas:
        resto = tuple(r for r in reglas if r.name != omitida.name)
        sin_ella = int(intersect_with(
            build_calendar(date(year, 1, 1), date(year, 12, 31), resto),
            MESES_DE_MEDICION,
        )["medible"].sum())
        filas.append({
            "regla": omitida.name,
            "medibles_con_la_regla": base,
            "medibles_sin_la_regla": sin_ella,
            "dias_medibles_que_quita": sin_ella - base,
            "afecta_al_denominador": "sí" if sin_ella > base else "NO",
        })
    tabla = pd.DataFrame(filas).sort_values(
        "dias_medibles_que_quita", ascending=False
    ).reset_index(drop=True)
    return tabla


def comparar_anios(years: Sequence[int] = (2024, 2025, 2026, 2027)) -> pd.DataFrame:
    """Aporte de cada regla al denominador real, año por año.

    Distingue dos clases de redundancia, y la distinción importa:

    - **Estructural**: la regla no afecta en **ningún** año porque su objeto cae fuera
      de los meses de medición por construcción. Excluir enero, febrero y diciembre, o
      las vacaciones de invierno de julio, cuando se mide en marzo, junio, septiembre y
      noviembre.
    - **Accidental**: la regla no afecta en **este** año por cómo cayó el calendario.
      Los feriados no quitan ningún día medible en 2026 y sí quitan entre uno y tres en
      2024, 2025 y 2027.

    Confundirlas lleva a eliminar una regla que el año siguiente sí hace falta.

    Returns:
        Una fila por año con los días medibles y lo que quita cada regla.
    """
    filas = []
    for year in years:
        tabla = aporte_sobre_medibles(year).set_index("regla")
        fila: dict[str, object] = {
            "anio": year,
            "dias_medibles": int(tabla["medibles_con_la_regla"].iloc[0]),
        }
        for regla in tabla.index:
            fila[regla] = int(tabla.loc[regla, "dias_medibles_que_quita"])
        filas.append(fila)
    return pd.DataFrame(filas)


def clasificar_redundancias(comparacion: pd.DataFrame) -> pd.DataFrame:
    """Clasifica cada regla en estructuralmente redundante, accidental o efectiva."""
    reglas = [c for c in comparacion.columns if c not in ("anio", "dias_medibles")]
    filas = []
    for regla in reglas:
        valores = comparacion[regla]
        sin_efecto = int((valores == 0).sum())
        if sin_efecto == len(valores):
            clase = "redundante estructural"
            nota = "no afecta en ningún año analizado"
        elif sin_efecto:
            clase = "redundante accidental"
            anios = ", ".join(str(a) for a, v in zip(comparacion["anio"], valores, strict=True) if v == 0)
            clase_anios = anios
            nota = f"sin efecto solo en {clase_anios}; depende de cómo cae el calendario"
        else:
            clase = "efectiva"
            nota = "quita días medibles todos los años"
        filas.append({
            "regla": regla,
            "clasificacion": clase,
            "anios_sin_efecto": sin_efecto,
            "minimo_que_quita": int(valores.min()),
            "maximo_que_quita": int(valores.max()),
            "nota": nota,
        })
    orden = {"efectiva": 0, "redundante accidental": 1, "redundante estructural": 2}
    tabla = pd.DataFrame(filas)
    return tabla.sort_values(
        ["clasificacion", "maximo_que_quita"],
        key=lambda s: s.map(orden) if s.name == "clasificacion" else -s,
    ).reset_index(drop=True)


def sensibilidad_invierno(year: int = 2026, desplazamientos: tuple[int, ...] = (-14, -7, 0, 7, 14)) -> pd.DataFrame:
    """Cuánto cambia el resultado si las vacaciones de invierno se mueven.

    La metodología no da fechas, de modo que el supuesto es propio. Medir su efecto es
    lo que convierte un supuesto escondido en un supuesto declarado: si mover las
    fechas dos semanas no cambia el denominador medible, el supuesto no es crítico; si
    lo cambia, hay que conseguir el calendario escolar antes de publicar el indicador.
    """
    base = _primer_lunes_completo_de_julio(year)
    filas = []
    for desplazamiento in desplazamientos:
        arranque = base + timedelta(days=desplazamiento)
        marco = dias_medibles(year, inicio_invierno=arranque)
        filas.append({
            "inicio_supuesto": arranque.isoformat(),
            "desplazamiento_dias": desplazamiento,
            "dias_elegibles": int(marco["incluido"].sum()),
            "dias_medibles": int(marco["medible"].sum()),
        })
    tabla = pd.DataFrame(filas)
    referencia = tabla.loc[tabla["desplazamiento_dias"].eq(0), "dias_medibles"].iloc[0]
    tabla["diferencia_vs_supuesto"] = tabla["dias_medibles"] - referencia
    return tabla


# ---------------------------------------------------------------------------- informe
def analizar(year: int = 2026) -> dict[str, pd.DataFrame]:
    """Ejecuta el caso completo."""
    feriados = cargar_feriados()
    calendario = construir(year, feriados=feriados)
    marco = intersect_with(calendario, MESES_DE_MEDICION)

    comparacion = comparar_anios()
    reglas = exclusion_report(calendario)
    redundantes = reglas.loc[reglas["exclusiva"].eq(0), ["regla", "descripcion"]].copy()
    redundantes["motivo"] = "otra regla ya excluye todos sus días"

    return {
        "validacion_feriados": validar_feriados(feriados, year),
        "resumen_calendario": summary(calendario),
        "exclusion_por_regla": reglas,
        "reglas_redundantes": redundantes,
        "solapamiento": overlap_matrix(calendario).reset_index(names="regla"),
        "por_mes": by_month(calendario),
        "resumen_medicion": resumen_medicion(year),
        "aporte_sobre_medibles": aporte_sobre_medibles(year, feriados=feriados),
        "sensibilidad_invierno": sensibilidad_invierno(year),
        "comparacion_anios": comparacion,
        "clasificacion_reglas": clasificar_redundancias(comparacion),
        "dias_medibles": marco.loc[marco["medible"],
                                   ["fecha", "mes", "nombre_dia"]].reset_index(drop=True),
    }


def exportar(resultados: dict[str, pd.DataFrame], destino: Path = RESULTS) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    for nombre, tabla in resultados.items():
        tabla.to_csv(destino / f"{nombre}.csv", index=False, encoding="utf-8")
    return destino


def main() -> None:
    from lab.console import enable_utf8

    enable_utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anio", type=int, default=2026)
    parser.add_argument("--actualizar-feriados", type=int, default=None,
                        metavar="AÑO", help="descarga y versiona el listado de ese año")
    args = parser.parse_args()

    if args.actualizar_feriados:
        ruta = actualizar_feriados(args.actualizar_feriados)
        print(f"Listado de feriados de {args.actualizar_feriados} escrito en {ruta.name}")
        return

    year = args.anio
    resultados = analizar(year)

    print(f"=== Validación del listado de feriados de {year} ===")
    print(resultados["validacion_feriados"].to_string(index=False))

    print("\n=== Aporte de cada regla ===")
    columnas = ["regla", "excluye", "exclusiva", "solapada", "aporte_pct"]
    print(resultados["exclusion_por_regla"][columnas].to_string(index=False))

    redundantes = resultados["reglas_redundantes"]
    print(f"\n=== Reglas redundantes dado el resto ({len(redundantes)}) ===")
    print(redundantes.to_string(index=False) if len(redundantes) else "  ninguna")

    print("\n=== Resumen del calendario ===")
    print(resultados["resumen_calendario"].to_string(index=False))

    print("\n=== Días incluidos por mes ===")
    print(resultados["por_mes"].to_string(index=False))

    print("\n=== El denominador real, tras cruzar con los trimestres ===")
    print(resultados["resumen_medicion"].to_string(index=False))

    print("\n=== Cuánto aporta cada regla AL DENOMINADOR REAL ===")
    print(resultados["aporte_sobre_medibles"].to_string(index=False))

    print("\n=== Clasificación de las reglas según su efecto real ===")
    print(resultados["clasificacion_reglas"].to_string(index=False))

    print("\n=== Días medibles y aporte de cada regla, por año ===")
    print(resultados["comparacion_anios"].to_string(index=False))

    print("\n=== Sensibilidad al supuesto de vacaciones de invierno ===")
    print(resultados["sensibilidad_invierno"].to_string(index=False))

    destino = exportar(resultados)
    try:
        legible = destino.relative_to(ROOT).as_posix()
    except ValueError:
        legible = destino.as_posix()
    print(f"\nTablas escritas en {legible}")


if __name__ == "__main__":
    main()
