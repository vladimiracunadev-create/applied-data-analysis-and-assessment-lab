"""Pruebas de P18: ETL contractual GTFS."""

from __future__ import annotations

import pandas as pd
import pytest

from cases.etl_gtfs_automatizado import solution


def test_tres_publicaciones_producen_particiones_unicas():
    frame = solution.transformar(solution.cargar())
    assert len(frame) == 3
    assert frame["publicacion"].is_monotonic_increasing
    assert frame["particion"].is_unique


def test_todos_los_controles_publicados_cumplen():
    checks = solution.controles(solution.transformar(solution.cargar()))
    assert len(checks) == 5
    assert checks["cumple"].all()


def test_un_corte_duplicado_falla_antes_de_transformar(tmp_path):
    frame = solution.cargar()
    path = tmp_path / "duplicate.csv"
    pd.concat([frame, frame.iloc[[0]]], ignore_index=True).to_csv(path, index=False)
    with pytest.raises(ValueError, match="una sola vez"):
        solution.cargar(path)


def test_parquet_no_se_declara_ejecutado_sin_motor(tmp_path):
    status = solution.analizar()["formatos"].set_index("formato").loc["Parquet", "estado"]
    if solution.parquet_disponible():
        assert status == "disponible"
    else:
        assert status == "no ejecutado"
        with pytest.raises(RuntimeError, match="extra columnar"):
            solution.exportar_parquet(solution.cargar(), tmp_path / "out.parquet")
