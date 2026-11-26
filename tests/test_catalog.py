"""Pruebas del catálogo de casos (`lab.catalog`)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab.catalog import (
    CONTENT_FIELDS,
    IDENTITY_FIELDS,
    REQUIRED_FIELDS,
    catalog_frame,
    catalog_markdown,
    competency_matrix,
    discover_cases,
    load_case,
    validate_metadata,
)
from lab.profiles import COMPETENCIES


def metadatos_completos(slug: str = "demo") -> dict:
    datos = {campo: f"valor de {campo}" for campo in CONTENT_FIELDS}
    datos.update({
        "slug": slug,
        "titulo": "Caso de demostración",
        "disciplina": "analisis-de-datos",
        "industria": "generica",
        "dificultad": "intermedio",
        "metodologia": "descriptiva",
        "competencias": ["calidad-datos"],
        "estado": "implementado",
        "tiempo_sugerido_min": 60,
    })
    return datos


def escribir(tmp_path: Path, datos: dict, slug: str = "demo") -> Path:
    carpeta = tmp_path / "cases" / slug
    carpeta.mkdir(parents=True)
    destino = carpeta / "case.json"
    destino.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    return destino


def test_los_campos_obligatorios_son_identidad_mas_contenido():
    assert REQUIRED_FIELDS == IDENTITY_FIELDS + CONTENT_FIELDS
    assert len(set(REQUIRED_FIELDS)) == len(REQUIRED_FIELDS)
    assert len(CONTENT_FIELDS) == 17


def test_metadatos_completos_no_tienen_hallazgos(tmp_path):
    ruta = escribir(tmp_path, metadatos_completos())
    caso = load_case(ruta)
    assert caso.ok, caso.issues
    assert caso.slug == "demo"


def test_campo_faltante_y_campo_vacio_se_detectan(tmp_path):
    datos = metadatos_completos()
    del datos["limitaciones"]
    datos["supuestos"] = []
    problemas = validate_metadata(datos, tmp_path / "cases" / "demo" / "case.json")
    assert any("limitaciones" in p for p in problemas)
    assert any("supuestos" in p and "vacío" in p for p in problemas)


def test_vocabularios_cerrados(tmp_path):
    datos = metadatos_completos()
    datos["dificultad"] = "imposible"
    datos["estado"] = "casi"
    problemas = validate_metadata(datos, tmp_path / "cases" / "demo" / "case.json")
    assert any("dificultad" in p for p in problemas)
    assert any("estado" in p for p in problemas)


def test_competencias_debe_ser_lista_y_tiempo_entero_positivo(tmp_path):
    datos = metadatos_completos()
    datos["competencias"] = "calidad-datos"
    datos["tiempo_sugerido_min"] = -5
    problemas = validate_metadata(datos, tmp_path / "cases" / "demo" / "case.json")
    assert any("'competencias' debe ser una lista" in p for p in problemas)
    assert any("tiempo_sugerido_min" in p for p in problemas)


def test_el_slug_debe_coincidir_con_la_carpeta(tmp_path):
    ruta = escribir(tmp_path, metadatos_completos(slug="otro"), slug="demo")
    caso = load_case(ruta)
    assert any("no coincide con la carpeta" in p for p in caso.issues)


def test_json_invalido_o_inexistente_son_errores_del_repositorio(tmp_path):
    carpeta = tmp_path / "cases" / "roto"
    carpeta.mkdir(parents=True)
    malo = carpeta / "case.json"
    malo.write_text("{no es json", encoding="utf-8")
    with pytest.raises(ValueError, match="no es JSON válido"):
        load_case(malo)
    lista = carpeta / "lista.json"
    lista.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(ValueError, match="objeto JSON"):
        load_case(lista)
    with pytest.raises(FileNotFoundError):
        load_case(carpeta / "no-existe.json")


def test_discover_cases_ordena_y_tolera_la_ausencia_de_carpeta(tmp_path):
    escribir(tmp_path, metadatos_completos("zeta"), slug="zeta")
    escribir(tmp_path, metadatos_completos("alfa"), slug="alfa")
    casos = discover_cases(tmp_path)
    assert [c.slug for c in casos] == ["alfa", "zeta"]
    assert discover_cases(tmp_path / "vacio") == []


def test_catalog_frame_y_markdown(tmp_path):
    escribir(tmp_path, metadatos_completos())
    casos = discover_cases(tmp_path)
    tabla = catalog_frame(casos)
    assert list(tabla.columns)[:4] == ["caso", "titulo", "disciplina", "industria"]
    assert tabla.metadatos_completos.iloc[0] == "sí"
    texto = catalog_markdown(casos)
    assert "demo" in texto and "../cases/demo/README.md" in texto
    assert "Sin casos registrados" in catalog_markdown([])
    assert catalog_frame([]).empty


def test_competency_matrix_cuenta_casos_por_competencia(tmp_path):
    uno = metadatos_completos("uno")
    uno["competencias"] = ["calidad-datos", "sql"]
    dos = metadatos_completos("dos")
    dos["competencias"] = ["calidad-datos"]
    escribir(tmp_path, uno, slug="uno")
    escribir(tmp_path, dos, slug="dos")
    matriz = competency_matrix(discover_cases(tmp_path)).set_index("competencia")
    assert matriz.loc["calidad-datos", "cantidad"] == 2
    assert matriz.loc["sql", "cantidad"] == 1
    assert competency_matrix([]).empty


# ------------------------------------------------- estado real del repositorio
def test_todos_los_casos_del_repositorio_declaran_metadatos_completos():
    casos = discover_cases()
    assert casos, "el repositorio debe tener al menos un caso con case.json"
    incompletos = {c.slug: c.issues for c in casos if not c.ok}
    assert not incompletos, f"casos con metadatos incompletos: {incompletos}"


def test_las_competencias_de_los_casos_existen_en_el_vocabulario():
    desconocidas = {
        competencia
        for caso in discover_cases()
        for competencia in caso.get("competencias", [])
        if competencia not in COMPETENCIES
    }
    assert not desconocidas, f"competencias fuera del vocabulario: {sorted(desconocidas)}"
