"""Validación cruzada: Pandas frente a SQL, indicador por indicador.

Por qué esta suite es la más importante del repositorio
    `solutions/reference.py` y `solutions/sql_reference.py` resuelven el mismo problema
    sin compartir una línea de código: una parte de los CSV ya tipados por pandas y la
    otra de los mismos archivos cargados como texto, con todo el casteo, el cruce y la
    agregación hechos en SQL. Si ambas coinciden, el acuerdo descarta una familia
    entera de errores (tipos, filtros, denominadores, precisión). Si difieren, hay un
    error real en alguna de las dos.

    Esta confrontación ya encontró un defecto: la duración calculada con `julianday`
    difería en el séptimo decimal e invertía la comparación «duración ≤ meta» justo en
    los empates, cambiando la puntualidad en varios puntos porcentuales. Ver
    `knowledge/julianday-precision.md`.

Qué queda deliberadamente fuera
    La mediana y el percentil 90 no se calculan en SQL: SQLite no tiene percentil con
    interpolación lineal, y reimplementarlo en SQL introduciría una tercera
    convención. Se validan contra una implementación en Python puro, escrita aquí, que
    no usa NumPy ni pandas.
"""

from __future__ import annotations

import pandas as pd
import pytest

from lab.metrics import percentile
from lab.sqlbridge import cross_check
from solutions import reference, sql_reference

#: Tolerancia de comparación. Una suma de flotantes en distinto orden puede diferir en
#: el último bit; una diferencia mayor que esto es un error real, no ruido numérico.
TOLERANCIA = 1e-9

CASOS = (1, 2, 3)


@pytest.fixture(scope="module")
def resultados() -> dict[int, tuple[dict, dict]]:
    """Ambas implementaciones, para los tres casos, calculadas una sola vez."""
    return {caso: (reference.analyze(caso), sql_reference.analyze(caso)) for caso in CASOS}


@pytest.mark.parametrize("caso", CASOS)
def test_indicadores_de_calidad_coinciden(caso, resultados):
    pandas_, sql = resultados[caso]
    esperado = pandas_["calidad"].set_index("indicador")["valor"].sort_index()
    obtenido = sql["calidad"].set_index("indicador")["valor"].sort_index()
    assert list(esperado.index) == list(obtenido.index)
    diferencias = {k: (int(esperado[k]), int(obtenido[k]))
                   for k in esperado.index if int(esperado[k]) != int(obtenido[k])}
    assert not diferencias, f"caso {caso}: {diferencias}"


@pytest.mark.parametrize("caso", CASOS)
def test_demanda_por_operador_coincide(caso, resultados):
    pandas_, sql = resultados[caso]
    diferencias = cross_check(pandas_["demanda"], sql["demanda"], ["operador"],
                              ["pasajeros", "viajes_con_dato"], tolerance=TOLERANCIA)
    assert diferencias.empty, diferencias.to_string(index=False)


@pytest.mark.parametrize("caso", CASOS)
def test_demanda_por_hora_coincide(caso, resultados):
    pandas_, sql = resultados[caso]
    diferencias = cross_check(pandas_["demanda_hora"], sql["demanda_hora"], ["hora"],
                              ["pasajeros"], tolerance=TOLERANCIA)
    assert diferencias.empty, diferencias.to_string(index=False)


@pytest.mark.parametrize("caso", CASOS)
def test_duracion_media_y_puntualidad_coinciden(caso, resultados):
    pandas_, sql = resultados[caso]
    columnas = ["recorrido_id", "media_min", "puntualidad_pct"]
    diferencias = cross_check(pandas_["duracion"][columnas], sql["duracion"][columnas],
                              ["recorrido_id"], ["media_min", "puntualidad_pct"],
                              tolerance=TOLERANCIA)
    assert diferencias.empty, diferencias.to_string(index=False)


@pytest.mark.parametrize("caso", CASOS)
def test_cumplimiento_por_recorrido_y_dia_coincide(caso, resultados):
    pandas_, sql = resultados[caso]
    diferencias = cross_check(pandas_["cumplimiento"], sql["cumplimiento"],
                              ["recorrido_id", "dia_octubre"],
                              ["realizados", "viajes_programados"], tolerance=TOLERANCIA)
    assert diferencias.empty, diferencias.to_string(index=False)


@pytest.mark.parametrize("caso", CASOS)
def test_cumplimiento_por_operador_coincide(caso, resultados):
    pandas_, sql = resultados[caso]
    diferencias = cross_check(pandas_["cumplimiento_operador"], sql["cumplimiento_operador"],
                              ["operador"],
                              ["realizados", "viajes_programados", "cumplimiento_pct"],
                              tolerance=TOLERANCIA)
    assert diferencias.empty, diferencias.to_string(index=False)


@pytest.mark.parametrize("caso", CASOS)
def test_realizados_por_recorrido_coincide(caso, resultados):
    pandas_, sql = resultados[caso]
    diferencias = cross_check(pandas_["realizados_recorrido"], sql["realizados_recorrido"],
                              ["recorrido_id"], ["realizados"], tolerance=TOLERANCIA)
    assert diferencias.empty, diferencias.to_string(index=False)


# --------------------------------------------- percentiles en Python puro, sin NumPy
def percentil_manual(valores: list[float], q: float) -> float:
    """Percentil con interpolación lineal, implementado sin NumPy ni pandas.

    `h = (n − 1) · q`; se interpola entre las posiciones ⌊h⌋ y ⌈h⌉. Es la misma
    definición que usa `numpy.quantile(method="linear")` y `PERCENTIL.INC` de Excel,
    escrita a mano para que la comparación sea una verificación y no una tautología.
    """
    datos = sorted(valores)
    n = len(datos)
    if n == 0:
        raise ValueError("No hay valores.")
    if n == 1:
        return float(datos[0])
    h = (n - 1) * q
    bajo = int(h)
    alto = min(bajo + 1, n - 1)
    return float(datos[bajo] + (h - bajo) * (datos[alto] - datos[bajo]))


def test_el_percentil_manual_reproduce_un_caso_calculado_a_mano():
    # n = 4, q = 0.9 → h = 2.7 → 3 + 0.7 · (4 − 3) = 3.7
    assert percentil_manual([1, 2, 3, 4], 0.9) == pytest.approx(3.7)
    assert percentil_manual([5], 0.5) == 5.0
    with pytest.raises(ValueError, match="No hay valores"):
        percentil_manual([], 0.5)


@pytest.mark.parametrize("caso", CASOS)
def test_mediana_y_p90_por_recorrido_contra_implementacion_manual(caso):
    """Valida mediana y P90 de la solución de referencia sin usar NumPy."""
    viajes = pd.read_csv(f"data/case_{caso}/viajes.csv").drop_duplicates()
    recorridos = pd.read_csv(f"data/case_{caso}/recorridos.csv")
    viajes = viajes.merge(recorridos, on="recorrido_id", how="inner")
    viajes = viajes.loc[viajes["estado"].eq("REALIZADO")].copy()
    inicio = pd.to_datetime(viajes["inicio"], errors="coerce")
    fin = pd.to_datetime(viajes["fin"], errors="coerce")
    viajes["duracion_min"] = (fin - inicio).dt.total_seconds() / 60
    viajes = viajes.loc[viajes["duracion_min"].notna() & viajes["duracion_min"].ge(0)]

    esperado = reference.analyze(caso)["duracion"].set_index("recorrido_id")
    for recorrido, grupo in viajes.groupby("recorrido_id"):
        valores = grupo["duracion_min"].tolist()
        assert esperado.loc[recorrido, "mediana_min"] == pytest.approx(
            percentil_manual(valores, 0.50), abs=1e-9)
        assert esperado.loc[recorrido, "p90_min"] == pytest.approx(
            percentil_manual(valores, 0.90), abs=1e-9)
        # Y la utilidad del núcleo coincide con la implementación manual.
        assert percentile(pd.Series(valores), 0.90) == pytest.approx(
            percentil_manual(valores, 0.90), abs=1e-9)


# ------------------------------------------------------ invariantes entre indicadores
@pytest.mark.parametrize("caso", CASOS)
def test_los_totales_cuadran_entre_tablas_en_ambas_implementaciones(caso, resultados):
    for nombre, tablas in zip(("pandas", "sql"), resultados[caso], strict=True):
        assert tablas["demanda"]["pasajeros"].sum() == pytest.approx(
            tablas["demanda_hora"]["pasajeros"].sum()), f"{nombre}: demanda por hora"
        assert tablas["cumplimiento"]["realizados"].sum() == pytest.approx(
            tablas["realizados_recorrido"]["realizados"].sum()), f"{nombre}: realizados"
        assert tablas["duracion"]["puntualidad_pct"].between(0, 100).all(), (
            f"{nombre}: puntualidad fuera de rango")


@pytest.mark.parametrize("caso", CASOS)
def test_la_implementacion_sql_es_de_solo_lectura(caso):
    """El puente de validación no debe poder modificar nada."""
    for sql in sql_reference.QUERIES.values():
        limpio = sql.strip().lower()
        assert limpio.startswith("with") or limpio.startswith("select")


def test_load_raw_avisa_cuando_faltan_los_datos(tmp_path):
    with pytest.raises(FileNotFoundError, match="generate_data.py"):
        sql_reference.load_raw(1, root=tmp_path)


def test_sql_reference_rechaza_un_caso_invalido():
    with pytest.raises(ValueError, match="Caso inválido"):
        sql_reference.analyze(9)
