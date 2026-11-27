"""Validación cruzada de Pandas frente a Polars y R.

Polars es una dependencia opcional y R es un runtime externo. Las pruebas se omiten
cuando la tecnología no está instalada en la máquina local; el trabajo multitecnología
de CI instala ambas y exige que todas se ejecuten.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from cases.education.solution import analyze as pandas_education
from cases.rendimiento_gtfs import solution as rendimiento
from cases.retail.solution import analyze as pandas_retail
from lab.core import read_table
from solutions import reference

ROOT = Path(__file__).resolve().parents[1]
POLARS_AVAILABLE = importlib.util.find_spec("polars") is not None
RSCRIPT = shutil.which("Rscript")
NOTEBOOK_CASES = (
    "bip_lugares_carga",
    "correspondencia_metro",
    "carga_nocturna",
    "gtfs_red_movilidad",
    "rendimiento_gtfs",
    "cobertura_de_carga",
    "calendario_medicion",
    "frecuencia_programada",
    "evolucion_gtfs",
    "informe_decision_carga",
)

KEYS = {
    "calidad": ["indicador"],
    "demanda": ["operador"],
    "demanda_hora": ["hora"],
    "duracion": ["recorrido_id"],
    "cumplimiento": ["recorrido_id", "dia_octubre"],
    "cumplimiento_operador": ["operador"],
    "realizados_recorrido": ["recorrido_id"],
    "metrics_retail": ["product"],
    "metrics_education": ["school"],
    "quality": ["column"],
}


def _polars_to_pandas(frame) -> pd.DataFrame:
    return pd.DataFrame(frame.to_dict(as_series=False))


def _assert_same(expected: pd.DataFrame, actual: pd.DataFrame, keys: list[str]) -> None:
    assert set(expected.columns) == set(actual.columns)
    columns = list(expected.columns)
    left = expected[columns].sort_values(keys, na_position="last").reset_index(drop=True)
    right = actual[columns].sort_values(keys, na_position="last").reset_index(drop=True)
    pd.testing.assert_frame_equal(
        left,
        right,
        check_dtype=False,
        check_exact=False,
        atol=1e-9,
        rtol=1e-9,
    )


@pytest.mark.skipif(not POLARS_AVAILABLE, reason="instale el extra polars")
@pytest.mark.parametrize("case", (1, 2, 3))
def test_polars_reproduce_las_siete_tablas_de_transporte(case):
    from solutions import polars_reference

    expected = reference.analyze(case)
    actual = polars_reference.analyze_transport(case)
    assert set(actual) == set(expected)
    for name in expected:
        _assert_same(expected[name], _polars_to_pandas(actual[name]), KEYS[name])


@pytest.mark.skipif(not POLARS_AVAILABLE, reason="instale el extra polars")
@pytest.mark.parametrize("case_name", ("retail", "education"))
def test_polars_reproduce_los_casos_de_negocio(case_name):
    from solutions import polars_reference

    raw = read_table(ROOT / "cases" / case_name / "input.csv")
    if case_name == "retail":
        expected = pandas_retail(raw)
        actual = polars_reference.analyze_retail()
    else:
        expected = pandas_education(raw)
        actual = polars_reference.analyze_education()

    _assert_same(
        expected["metrics"],
        _polars_to_pandas(actual["metrics"]),
        KEYS[f"metrics_{case_name}"],
    )
    quality_columns = ["column", "nulls", "unique", "rows", "exact_duplicates"]
    _assert_same(
        expected["quality"][quality_columns],
        _polars_to_pandas(actual["quality"])[quality_columns],
        KEYS["quality"],
    )


@pytest.mark.skipif(not POLARS_AVAILABLE, reason="instale el extra polars")
def test_polars_lazy_coincide_con_pandas_en_el_benchmark_gtfs(tmp_path):
    feed = tmp_path / "feed.zip"
    with zipfile.ZipFile(feed, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("stop_times.txt", "trip_id,stop_id\nT1,A\nT1,B\nT2,A\n")

    expected, _ = rendimiento.pandas_completo(feed)
    actual, metadata = rendimiento.polars_csv(feed)

    assert actual is not None
    pd.testing.assert_series_equal(expected, actual, check_names=False)
    assert metadata["estado"].startswith("ejecutado")


def _run_r(case_name: str, destination: Path, number: int = 1) -> dict[str, pd.DataFrame]:
    assert RSCRIPT is not None
    subprocess.run(
        [RSCRIPT, str(ROOT / "solutions" / "r_reference.R"), case_name,
         str(number), str(destination)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return {path.stem: pd.read_csv(path) for path in destination.glob("*.csv")}


@pytest.mark.skipif(RSCRIPT is None, reason="Rscript no está instalado")
@pytest.mark.parametrize("case", (1, 2, 3))
def test_r_reproduce_las_siete_tablas_de_transporte(case, tmp_path):
    expected = reference.analyze(case)
    actual = _run_r("transport", tmp_path / f"transport_{case}", case)
    assert set(actual) == set(expected)
    for name in expected:
        _assert_same(expected[name], actual[name], KEYS[name])


@pytest.mark.skipif(RSCRIPT is None, reason="Rscript no está instalado")
@pytest.mark.parametrize("case_name", ("retail", "education"))
def test_r_reproduce_los_casos_de_negocio(case_name, tmp_path):
    raw = read_table(ROOT / "cases" / case_name / "input.csv")
    expected = pandas_retail(raw) if case_name == "retail" else pandas_education(raw)
    actual = _run_r(case_name, tmp_path / case_name)

    _assert_same(expected["metrics"], actual["metrics"], KEYS[f"metrics_{case_name}"])
    quality_columns = ["column", "nulls", "unique", "rows", "exact_duplicates"]
    _assert_same(
        expected["quality"][quality_columns],
        actual["quality"][quality_columns],
        KEYS["quality"],
    )


@pytest.mark.skipif(not POLARS_AVAILABLE, reason="instale el extra polars")
@pytest.mark.parametrize("slug", NOTEBOOK_CASES)
def test_cada_cuaderno_ejecuta_polars_y_matplotlib(slug, tmp_path):
    pandas_script = ROOT / "cases" / slug / "cuaderno" / "solucion_pandas.py"
    script = ROOT / "cases" / slug / "cuaderno" / "solucion_polars.py"
    pandas_csv = tmp_path / f"{slug}-pandas.csv"
    polars_csv = tmp_path / f"{slug}-polars.csv"
    pandas_chart = tmp_path / f"{slug}-pandas.png"
    chart = tmp_path / f"{slug}-polars.png"
    subprocess.run(
        [sys.executable, str(pandas_script), "--salida", str(pandas_csv),
         "--grafico", str(pandas_chart)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(script), "--salida", str(polars_csv),
         "--grafico", str(chart)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    expected = pd.read_csv(pandas_csv)
    actual = pd.read_csv(polars_csv)
    _assert_same(expected, actual, [expected.columns[0]])
    assert pandas_chart.stat().st_size > 1_000
    assert chart.stat().st_size > 1_000


@pytest.mark.skipif(RSCRIPT is None, reason="Rscript no está instalado")
@pytest.mark.parametrize("slug", NOTEBOOK_CASES)
def test_cada_cuaderno_ejecuta_r_y_ggplot2(slug, tmp_path):
    pandas_script = ROOT / "cases" / slug / "cuaderno" / "solucion_pandas.py"
    script = ROOT / "cases" / slug / "cuaderno" / "solucion.R"
    pandas_csv = tmp_path / f"{slug}-pandas.csv"
    r_csv = tmp_path / f"{slug}-r.csv"
    chart = tmp_path / f"{slug}-r.png"
    subprocess.run(
        [sys.executable, str(pandas_script), "--salida", str(pandas_csv)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    subprocess.run(
        [RSCRIPT, str(script), "--salida", str(r_csv), "--grafico", str(chart)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    expected = pd.read_csv(pandas_csv)
    actual = pd.read_csv(r_csv)
    _assert_same(expected, actual, [expected.columns[0]])
    assert chart.stat().st_size > 1_000
