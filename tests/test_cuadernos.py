"""Contrato estructural de los cuadernos generados.

La ejecución completa necesita los datos públicos no versionados y se comprueba con
``scripts/build_cuadernos.py --check``. Estas pruebas protegen en CI la parte que sí
puede verificarse sin descargarlos: inventario, estructura y artefactos publicados.
"""

from __future__ import annotations

import importlib
import json
import zipfile
from pathlib import Path

from openpyxl import load_workbook

from scripts.build_cuadernos import PROBLEMAS, casos_con_cuaderno

ROOT = Path(__file__).resolve().parents[1]
CASOS_ESPERADOS = {
    "bip_lugares_carga",
    "calendario_medicion",
    "carga_nocturna",
    "cobertura_de_carga",
    "correspondencia_metro",
    "evolucion_gtfs",
    "frecuencia_programada",
    "gtfs_red_movilidad",
    "informe_decision_carga",
    "rendimiento_gtfs",
}


def test_los_casos_resueltos_declaran_cuaderno():
    assert set(casos_con_cuaderno()) == CASOS_ESPERADOS


def test_los_dieciseis_problemas_tienen_un_caso_y_un_cuaderno():
    assert len(PROBLEMAS) == 16
    assert {codigo for codigo, *_ in PROBLEMAS} == {f"P{numero:02d}" for numero in range(1, 17)}
    assert all(slug in CASOS_ESPERADOS for _, _, slug, _ in PROBLEMAS)


def test_cada_cuaderno_tiene_estructura_profesional():
    for slug in sorted(CASOS_ESPERADOS):
        modulo = importlib.import_module(f"cases.{slug}.cuaderno")
        cuaderno = modulo.construir
        assert callable(cuaderno)

        fuente = (ROOT / "cases" / slug / "cuaderno.py").read_text(encoding="utf-8")
        for campo in ("problema=", "solucion=", "flujo=", "mapa=", "aprendizajes="):
            assert campo in fuente, f"{slug} no declara {campo}"
        assert fuente.count("Paso(") >= 8, f"{slug} necesita al menos ocho pasos"


def test_cada_cuaderno_publicado_tiene_sus_descargables():
    for slug in sorted(CASOS_ESPERADOS):
        base = ROOT / "cases" / slug
        assert (base / "CUADERNO.md").is_file()
        assert (base / "cuaderno" / "pasos.py").is_file()
        assert (base / "cuaderno" / "practica.xlsx").is_file()
        assert (base / "cuaderno" / "colab.ipynb").is_file()
        assert (base / "cuaderno" / "svg" / "flujo.svg").is_file()
        assert (base / "cuaderno" / "svg" / "mapa.svg").is_file()
        assert list((base / "cuaderno").glob("*-caso-completo.zip"))


def test_colab_excel_y_zip_publicados_se_pueden_abrir():
    for slug in sorted(CASOS_ESPERADOS):
        base = ROOT / "cases" / slug / "cuaderno"

        notebook = json.loads((base / "colab.ipynb").read_text(encoding="utf-8"))
        assert notebook["nbformat"] == 4
        assert sum(cell["cell_type"] == "code" for cell in notebook["cells"]) >= 2

        book = load_workbook(base / "practica.xlsx", read_only=True, data_only=False)
        try:
            assert book.sheetnames == [
                "00_indice",
                "01_instrucciones",
                "02_datos",
                "03_formulas",
            ]
        finally:
            book.close()

        [paquete] = list(base.glob("*-caso-completo.zip"))
        with zipfile.ZipFile(paquete) as archive:
            assert archive.testzip() is None
            nombres = set(archive.namelist())
            assert any(nombre.endswith("CUADERNO.md") for nombre in nombres)
            assert any(nombre.endswith("pasos.py") for nombre in nombres)
