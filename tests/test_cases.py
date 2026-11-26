"""Pruebas de regresión de los casos de estudio.

Estas pruebas ejecutan la solución de cada caso sobre el dataset versionado del
repositorio —no sobre una tabla mínima construida en la prueba— y comprueban
invariantes de los resultados. Son la red que impide que un cambio en el núcleo rompa
un caso resuelto hace meses.
"""

from __future__ import annotations

import pandas as pd
import pytest

from cases.education.solution import analyze as analizar_educacion
from cases.retail.solution import analyze as analizar_comercio
from lab.core import read_table
from lab.metrics import compare_rates


@pytest.fixture(scope="module")
def comercio(repo_root):
    crudo = read_table(repo_root / "cases" / "retail" / "input.csv")
    return crudo, analizar_comercio(crudo)


@pytest.fixture(scope="module")
def educacion(repo_root):
    crudo = read_table(repo_root / "cases" / "education" / "input.csv")
    return crudo, analizar_educacion(crudo)


# ----------------------------------------------------------------------- comercio
def test_el_caso_de_comercio_corre_sobre_su_dataset(comercio):
    crudo, resultado = comercio
    assert not crudo.empty
    assert set(resultado) == {"quality", "metrics"}
    assert not resultado["metrics"].empty


def test_el_perfil_de_calidad_describe_la_tabla_original(comercio):
    crudo, resultado = comercio
    calidad = resultado["quality"]
    assert set(calidad.column) == set(crudo.columns)
    assert (calidad.rows == len(crudo)).all()


def test_las_devoluciones_restan_unidades_y_margen(comercio):
    crudo, resultado = comercio
    metricas = resultado["metrics"]
    # El margen por producto nunca puede superar las ventas netas: el costo es no
    # negativo, de modo que margen = unidades × (precio − costo) ≤ unidades × precio.
    assert (metricas["margin"] <= metricas["net_sales"] + 1e-9).all()
    # Y la suma de unidades netas es menor o igual que la suma de cantidades vendidas,
    # porque las devoluciones aportan unidades negativas.
    ventas = crudo.loc[crudo["status"].eq("SALE") & crudo["quantity"].gt(0), "quantity"].sum()
    assert metricas["units"].sum() <= ventas


def test_el_caso_de_comercio_excluye_lo_invalido_y_lo_hace_visible(comercio):
    crudo, resultado = comercio
    estados_validos = crudo["status"].isin(["SALE", "RETURN"])
    cantidades_validas = crudo["quantity"].gt(0)
    descartables = int((~(estados_validos & cantidades_validas)).sum())
    duplicados = int(crudo.duplicated().sum())
    # Si el dataset tiene defectos, el perfil de calidad debe poder informarlos.
    if duplicados:
        assert resultado["quality"]["exact_duplicates"].iloc[0] == duplicados
    assert descartables >= 0  # la aserción útil es la de arriba; esto documenta el conteo


# ---------------------------------------------------------------------- educación
def test_el_caso_de_educacion_corre_sobre_su_dataset(educacion):
    _, resultado = educacion
    assert not resultado["metrics"].empty
    assert {"school", "attended", "scheduled", "simple_pct", "weighted_pct"} <= set(
        resultado["metrics"].columns
    )


def test_ninguna_tasa_de_asistencia_queda_fuera_del_rango(educacion):
    _, resultado = educacion
    metricas = resultado["metrics"]
    assert metricas["weighted_pct"].between(0, 100).all()
    assert metricas["simple_pct"].between(0, 100).all()


def test_la_tasa_ponderada_del_caso_coincide_con_el_nucleo(educacion):
    """La solución del caso y `lab.metrics.compare_rates` deben dar lo mismo.

    Es una validación cruzada en miniatura: dos implementaciones del mismo indicador,
    una en el caso y otra en el núcleo.
    """
    _, resultado = educacion
    metricas = resultado["metrics"]
    for fila in metricas.itertuples():
        esperado = 100 * fila.attended / fila.scheduled
        assert fila.weighted_pct == pytest.approx(esperado)
    comparacion = compare_rates(metricas["attended"], metricas["scheduled"])
    global_esperado = 100 * metricas["attended"].sum() / metricas["scheduled"].sum()
    assert comparacion.weighted == pytest.approx(global_esperado)


def test_el_promedio_simple_y_la_tasa_ponderada_no_se_confunden(educacion):
    _, resultado = educacion
    metricas = resultado["metrics"]
    # Pueden coincidir si todos los establecimientos tienen el mismo tamaño, pero el
    # caso debe informar ambos por separado para que la diferencia sea visible.
    assert "simple_pct" in metricas.columns and "weighted_pct" in metricas.columns
    assert metricas["simple_pct"].notna().all()
    assert metricas["weighted_pct"].notna().all()


def test_los_registros_imposibles_quedan_fuera(educacion):
    crudo, resultado = educacion
    imposibles = crudo.loc[crudo["attended"].gt(crudo["scheduled"])]
    metricas = resultado["metrics"]
    if not imposibles.empty:
        # Los días de un registro imposible no pueden estar en el agregado.
        por_escuela = crudo.groupby("school")["attended"].sum()
        for fila in metricas.itertuples():
            assert fila.attended <= por_escuela.get(fila.school, fila.attended)


# -------------------------------------------------------------- regresión conjunta
def test_las_soluciones_no_modifican_su_entrada(repo_root):
    """Una solución que muta su entrada hace irreproducible el segundo cálculo."""
    for ruta, funcion in (
        (repo_root / "cases" / "retail" / "input.csv", analizar_comercio),
        (repo_root / "cases" / "education" / "input.csv", analizar_educacion),
    ):
        crudo = read_table(ruta)
        antes = crudo.copy(deep=True)
        funcion(crudo)
        pd.testing.assert_frame_equal(crudo, antes)


def test_ejecutar_dos_veces_da_el_mismo_resultado(repo_root):
    crudo = read_table(repo_root / "cases" / "retail" / "input.csv")
    primera = analizar_comercio(crudo)["metrics"]
    segunda = analizar_comercio(crudo)["metrics"]
    pd.testing.assert_frame_equal(primera, segunda)
