"""Pruebas de P17: catálogo y brechas de gobernanza DTPM."""

from __future__ import annotations

import pandas as pd
import pytest

from cases.gobernanza_datos_dtpm import solution


def test_catalogo_tiene_identidad_y_vocabulario_controlado():
    catalog = solution.cargar()
    assert len(catalog) == 8
    assert catalog["activo_id"].is_unique
    assert set(catalog["criticidad"]) <= set(solution.WEIGHTS)


def test_puntaje_es_la_suma_publicada_por_criticidad():
    audit = solution.evaluar(solution.cargar())
    expected = (
        3 * audit["brecha_licencia"] + 2 * audit["brecha_esquema"]
        + 2 * audit["brecha_actualizacion"] + 2 * audit["brecha_responsable"]
        + audit["brecha_retencion"]
    )
    pd.testing.assert_series_equal(audit["puntaje_brecha"], expected, check_names=False)
    pd.testing.assert_series_equal(
        audit["puntaje_riesgo"], expected * audit["criticidad"].map(solution.WEIGHTS),
        check_names=False,
    )


def test_no_declarado_se_mide_y_no_se_imputa():
    results = solution.analizar()
    summary = results["resumen"].set_index("indicador")["valor"]
    assert summary["activos catalogados"] == 8
    assert summary["activos sin responsable operativo declarado"] == 6
    assert summary["activos sin retención declarada"] == 5


def test_contrato_roto_falla_con_explicacion(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"activo_id": ["A"]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="columnas requeridas"):
        solution.cargar(path)
