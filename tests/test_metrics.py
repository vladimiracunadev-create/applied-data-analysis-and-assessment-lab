"""Pruebas de indicadores y estadística descriptiva (`lab.metrics`)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from lab.metrics import (
    compare_rates,
    coverage,
    describe_numeric,
    indicator_table,
    outliers_iqr,
    percentile,
    safe_ratio,
)


def test_safe_ratio_con_escalares():
    assert safe_ratio(30, 40, scale=100) == 75.0
    assert np.isnan(safe_ratio(1, 0))
    assert np.isnan(safe_ratio(1, None))
    assert np.isnan(safe_ratio(1, float("nan")))


def test_safe_ratio_vectorizado_anula_denominadores_cero():
    resultado = safe_ratio(pd.Series([10, 10, 10]), pd.Series([5, 0, None]), scale=100)
    assert resultado.iloc[0] == 200.0
    assert resultado.iloc[1:].isna().all()


def test_percentile_coincide_con_numpy_y_declara_el_metodo():
    serie = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    for metodo in ("linear", "lower", "higher", "nearest", "midpoint"):
        assert percentile(serie, 0.9, metodo) == pytest.approx(
            float(np.quantile(serie.to_numpy(), 0.9, method=metodo))
        )
    # El método importa: con n = 4 y q = 0.9 los resultados difieren.
    corta = pd.Series([1, 2, 3, 4])
    assert percentile(corta, 0.9, "linear") != percentile(corta, 0.9, "lower")


def test_percentile_valida_sus_argumentos():
    with pytest.raises(ValueError, match="entre 0 y 1"):
        percentile(pd.Series([1]), 90)
    with pytest.raises(ValueError, match="Método inválido"):
        percentile(pd.Series([1]), 0.5, "mágico")


def test_percentile_de_serie_vacia_es_nan():
    assert np.isnan(percentile(pd.Series([], dtype=float), 0.5))
    assert np.isnan(percentile(pd.Series(["a", "b"]), 0.5))


def test_describe_numeric_calculado_a_mano():
    serie = pd.Series([2, 4, 4, 4, 5, 5, 7, 9])
    tabla = describe_numeric(serie, unit="min").set_index("indicador").valor
    assert tabla["valores_usables"] == 8
    assert tabla["media"] == pytest.approx(5.0)
    assert tabla["desviacion_estandar"] == pytest.approx(2.13809, abs=1e-5)
    assert tabla["mediana"] == pytest.approx(4.5)
    assert tabla["iqr"] == pytest.approx(percentile(serie, 0.75) - percentile(serie, 0.25))
    assert tabla["cobertura_pct"] == pytest.approx(100.0)


def test_describe_numeric_informa_cobertura_parcial():
    tabla = describe_numeric(pd.Series([1, None, "x", 3])).set_index("indicador").valor
    assert tabla["filas"] == 4
    assert tabla["valores_usables"] == 2
    assert tabla["cobertura_pct"] == pytest.approx(50.0)
    assert tabla["media"] == pytest.approx(2.0)


def test_describe_numeric_sin_valores_usables_no_estalla():
    tabla = describe_numeric(pd.Series(["a", "b"])).set_index("indicador").valor
    assert tabla["valores_usables"] == 0
    assert np.isnan(tabla["media"])


def test_compare_rates_distingue_ponderada_de_promedio_simple():
    # Una unidad pequeña con 50 % y una grande con 90 %: el promedio simple (70 %)
    # no describe al conjunto, que está en 88.3 %.
    resultado = compare_rates(pd.Series([1, 90]), pd.Series([2, 100]))
    assert resultado.weighted == pytest.approx(100 * 91 / 102)
    assert resultado.simple == pytest.approx(70.0)
    assert resultado.difference == pytest.approx(resultado.weighted - resultado.simple)


def test_compare_rates_ignora_filas_con_denominador_cero_en_el_promedio_simple():
    resultado = compare_rates(pd.Series([1, 1]), pd.Series([2, 0]))
    assert resultado.simple == pytest.approx(50.0)
    assert resultado.weighted == pytest.approx(100.0)


def test_outliers_iqr_marca_el_extremo_y_no_los_nulos():
    serie = pd.Series([10, 11, 12, 13, 14, 200, None])
    marcados = outliers_iqr(serie)
    assert marcados.iloc[5]
    assert not marcados.iloc[6]
    assert marcados.sum() == 1
    # Con k = 3 el criterio es más exigente y marca menos valores.
    assert outliers_iqr(serie, k=3).sum() <= marcados.sum()


def test_outliers_iqr_rechaza_k_negativo_y_tolera_series_no_numericas():
    with pytest.raises(ValueError, match="no puede ser negativo"):
        outliers_iqr(pd.Series([1]), k=-1)
    assert not outliers_iqr(pd.Series(["a", "b"])).any()


def test_coverage():
    assert coverage(pd.Series([1, 2, None, "x"])) == pytest.approx(50.0)
    assert np.isnan(coverage(pd.Series([], dtype=float)))


def test_indicator_table_obliga_a_declarar_unidad_y_definicion():
    tabla = indicator_table({
        "demanda": (1000, "personas", "Suma de pasajeros de viajes válidos"),
        "cumplimiento": (95.2, "%", "100 × realizados / programados"),
    })
    assert list(tabla.columns) == ["indicador", "valor", "unidad", "definicion"]
    assert tabla.unidad.tolist() == ["personas", "%"]
    assert tabla.definicion.str.len().gt(0).all()
