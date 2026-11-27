"""Contrato del paquete general descargable de todos los casos."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

from scripts.build_all_cases import ARCHIVE_ROOT, DESTINATION, build_bytes

ROOT = Path(__file__).resolve().parents[1]


def test_el_paquete_general_es_determinista_y_esta_al_dia():
    first = build_bytes()
    second = build_bytes()
    assert first == second
    assert DESTINATION.exists()
    with zipfile.ZipFile(DESTINATION) as published:
        assert published.testzip() is None


def test_el_paquete_contiene_los_trece_casos_y_los_cinco_motores():
    with zipfile.ZipFile(io.BytesIO(build_bytes())) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
        manifest = json.loads(archive.read(f"{ARCHIVE_ROOT}/MANIFEST.json"))

    assert manifest["cases"] == 13
    assert manifest["notebooks"] == 10
    assert manifest["engines"] == ["Pandas", "Polars", "R base", "SQL", "Excel"]
    assert manifest["third_party_data_included"] is False
    for case_json in (ROOT / "cases").glob("*/case.json"):
        relative = case_json.relative_to(ROOT).as_posix()
        assert f"{ARCHIVE_ROOT}/{relative}" in names
    assert f"{ARCHIVE_ROOT}/solutions/polars_reference.py" in names
    assert f"{ARCHIVE_ROOT}/solutions/r_reference.R" in names


def test_el_paquete_no_redistribuye_datos_de_terceros():
    with zipfile.ZipFile(io.BytesIO(build_bytes())) as archive:
        names = archive.namelist()
    assert not any("/data/original/" in name for name in names)
    assert not any(name.endswith(("/entradas.xlsx", "/reference.xlsx")) for name in names)


def test_el_paquete_normaliza_texto_para_ser_portable_entre_sistemas():
    with zipfile.ZipFile(io.BytesIO(build_bytes())) as archive:
        readme = archive.read(f"{ARCHIVE_ROOT}/README.md")
    assert b"\r\n" not in readme
