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

from lab.notebook_enrichment import NAVIGATION, enriquecer_cuaderno
from lab.sources import CATALOG
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
    "gobernanza_datos_dtpm",
    "etl_gtfs_automatizado",
    "red_correspondencias_dtpm",
    "optimizacion_carga_bip",
    "informe_decision_carga",
    "rendimiento_gtfs",
}


def test_los_casos_resueltos_declaran_cuaderno():
    assert set(casos_con_cuaderno()) == CASOS_ESPERADOS


def test_los_problemas_tienen_un_caso_y_un_cuaderno():
    assert len(PROBLEMAS) == 20
    assert {codigo for codigo, *_ in PROBLEMAS} == {f"P{numero:02d}" for numero in range(1, 21)}
    assert all(slug in CASOS_ESPERADOS for _, _, slug, _ in PROBLEMAS)


def test_cada_cuaderno_tiene_estructura_profesional():
    for slug in sorted(CASOS_ESPERADOS):
        modulo = importlib.import_module(f"cases.{slug}.cuaderno")
        cuaderno = modulo.construir
        assert callable(cuaderno)
        construido = cuaderno()
        assert set(construido.fuentes_datos.split()) <= set(CATALOG), (
            f"{slug} declara una fuente que scripts/fetch_data.py no conoce"
        )

        fuente = (ROOT / "cases" / slug / "cuaderno.py").read_text(encoding="utf-8")
        for campo in ("problema=", "solucion=", "flujo=", "mapa=", "aprendizajes="):
            assert campo in fuente, f"{slug} no declara {campo}"
        assert fuente.count("Paso(") >= 8, f"{slug} necesita al menos ocho pasos"


def test_cada_cuaderno_publica_los_tres_motores_y_un_grafico_estadistico():
    for slug in sorted(CASOS_ESPERADOS):
        modulo = importlib.import_module(f"cases.{slug}.cuaderno")
        cuaderno = enriquecer_cuaderno(slug, modulo.construir())
        assert {item.motor for item in cuaderno.implementaciones} == {
            "Pandas + Matplotlib",
            "Polars + Matplotlib",
            "R + ggplot2",
        }
        assert "Contrato común" in cuaderno.guia_multimotor
        assert "Fórmula o regla" in cuaderno.guia_multimotor
        assert "Error frecuente" in cuaderno.guia_multimotor
        assert any(paso.figura for paso in cuaderno.pasos), slug


def test_la_navegacion_sigue_una_unica_ruta_sin_saltos():
    for index, (slug, _) in enumerate(NAVIGATION):
        modulo = importlib.import_module(f"cases.{slug}.cuaderno")
        cuaderno = enriquecer_cuaderno(slug, modulo.construir())
        anterior = NAVIGATION[index - 1][0] if index else None
        siguiente = NAVIGATION[index + 1][0] if index + 1 < len(NAVIGATION) else None
        assert (cuaderno.anterior[1].split("/")[1] if cuaderno.anterior else None) == anterior
        assert (cuaderno.siguiente[1].split("/")[1] if cuaderno.siguiente else None) == siguiente


def test_cada_cuaderno_publicado_tiene_sus_descargables():
    for slug in sorted(CASOS_ESPERADOS):
        base = ROOT / "cases" / slug
        assert (base / "CUADERNO.md").is_file()
        assert (base / "cuaderno" / "pasos.py").is_file()
        assert (base / "cuaderno" / "practica.xlsx").is_file()
        assert (base / "cuaderno" / "colab.ipynb").is_file()
        assert (base / "cuaderno" / "solucion_pandas.py").is_file()
        assert (base / "cuaderno" / "solucion_polars.py").is_file()
        assert (base / "cuaderno" / "solucion.R").is_file()
        assert (base / "cuaderno" / "solucion.Rmd").is_file()
        assert (base / "cuaderno" / "svg" / "flujo.svg").is_file()
        assert (base / "cuaderno" / "svg" / "mapa.svg").is_file()
        assert list((base / "cuaderno").glob("*-caso-completo.zip"))


def test_colab_excel_y_zip_publicados_se_pueden_abrir():
    for slug in sorted(CASOS_ESPERADOS):
        base = ROOT / "cases" / slug / "cuaderno"

        notebook = json.loads((base / "colab.ipynb").read_text(encoding="utf-8"))
        assert notebook["nbformat"] == 4
        assert sum(cell["cell_type"] == "code" for cell in notebook["cells"]) >= 2
        notebook_text = json.dumps(notebook, ensure_ascii=False)
        assert "polars>=1.0" in notebook_text
        assert "solucion_pandas.py" in notebook_text
        assert "solucion_polars.py" in notebook_text
        assert "scripts/fetch_data.py" in notebook_text

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
            assert any(nombre.endswith("solucion_pandas.py") for nombre in nombres)
            assert any(nombre.endswith("solucion_polars.py") for nombre in nombres)
            assert any(nombre.endswith("solucion.R") for nombre in nombres)
            assert any(nombre.endswith("solucion.Rmd") for nombre in nombres)
