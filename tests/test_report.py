"""Pruebas de los informes (`lab.report`)."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from lab.report import (
    CASE_SECTIONS,
    RESEARCH_SECTIONS,
    Claim,
    Report,
    case_report,
    checklist,
    research_report,
    table_markdown,
)


def completar(report: Report) -> Report:
    for section in report.required:
        report.add(section, f"Contenido de {section}.")
    return report


def test_un_informe_incompleto_no_se_exporta():
    report = case_report("Prueba")
    report.add("contexto", "algo")
    assert len(report.missing()) == len(CASE_SECTIONS) - 1
    with pytest.raises(ValueError, match="no está completo"):
        report.to_markdown()


def test_un_informe_incompleto_se_puede_exportar_declarandolo():
    report = case_report("Prueba")
    report.add("contexto", "algo")
    texto = report.to_markdown(allow_incomplete=True)
    assert "Informe incompleto" in texto
    assert "problema" in texto  # nombra las secciones que faltan


def test_informe_completo_respeta_el_orden_de_las_secciones():
    texto = completar(case_report("Caso")).to_markdown()
    posiciones = [texto.index("## ") if i == 0 else 0 for i in range(1)]
    assert posiciones  # el informe tiene secciones
    orden = [texto.find(titulo) for titulo in
             ("Contexto", "Definición del problema", "Objetivos", "Limitaciones")]
    assert orden == sorted(orden)
    assert all(valor > 0 for valor in orden)


def test_secciones_obligatorias_de_caso_y_de_investigacion():
    assert len(CASE_SECTIONS) == 12
    assert len(RESEARCH_SECTIONS) == 20
    for clave in ("limitaciones", "supuestos", "validacion", "reproducibilidad"):
        assert clave in CASE_SECTIONS
    for clave in ("hipotesis", "sesgos", "incertidumbre", "poblacion_muestra"):
        assert clave in RESEARCH_SECTIONS


def test_una_seccion_vacia_se_rechaza():
    report = case_report("Prueba")
    with pytest.raises(ValueError, match="no puede quedar vacía"):
        report.add("contexto", "   ")


def test_add_devuelve_self_para_encadenar():
    report = case_report("Prueba")
    assert report.add("contexto", "a").add("problema", "b") is report
    assert len(report.sections) == 2


def test_add_table_incorpora_la_tabla_y_su_introduccion():
    frame = pd.DataFrame({"indicador": ["demanda"], "valor": [1000.0]})
    report = case_report("Prueba").add_table("resultados", frame, intro="Indicadores:")
    assert "Indicadores:" in report.sections["resultados"]
    assert "demanda" in report.sections["resultados"]
    assert "1,000.00" in report.sections["resultados"]


def test_claim_exige_respaldo_y_tipo_valido():
    with pytest.raises(ValueError, match="no declara respaldo"):
        Claim("hecho", "algo", "  ")
    with pytest.raises(ValueError, match="Tipo de afirmación inválido"):
        Claim("corazonada", "algo", "respaldo")  # type: ignore[arg-type]


def test_las_afirmaciones_se_imprimen_clasificadas_con_su_leyenda():
    report = completar(case_report("Caso"))
    report.claim("hecho", "454 filas", "recuento directo")
    report.claim("hipotesis", "podría ser la flota", "no contrastado")
    texto = report.to_markdown()
    assert "## Clasificación de afirmaciones" in texto
    assert "454 filas" in texto and "recuento directo" in texto
    # Solo se explican los tipos efectivamente usados.
    assert "**hecho**" in texto and "**hipotesis**" in texto
    assert "**inferencia**" not in texto


def test_metadatos_y_advertencia_en_el_encabezado():
    report = completar(Report("Título", required=("contexto",), author="Equipo",
                              report_date=date(2026, 11, 26),
                              disclaimer="Datos sintéticos."))
    texto = report.to_markdown()
    assert "# Título" in texto
    assert "Autoría: Equipo" in texto
    assert "2026-11-26" in texto
    assert "> Datos sintéticos." in texto


def test_secciones_extra_se_imprimen_despues_de_las_obligatorias():
    report = completar(Report("T", required=("contexto",)))
    report.add("anexo", "material adicional")
    texto = report.to_markdown()
    assert texto.index("Contexto") < texto.index("Anexo")


def test_write_crea_directorios_y_escribe_utf8(tmp_path):
    destino = completar(case_report("Caso con tildes")).write(tmp_path / "sub" / "informe.md")
    assert destino.exists()
    assert "Caso con tildes" in destino.read_text(encoding="utf-8")


def test_write_respeta_la_validacion_de_completitud(tmp_path):
    report = case_report("Prueba")
    report.add("contexto", "algo")
    with pytest.raises(ValueError):
        report.write(tmp_path / "x.md")
    assert report.write(tmp_path / "x.md", allow_incomplete=True).exists()


def test_table_markdown_formatea_flotantes_y_trunca_avisando():
    frame = pd.DataFrame({"v": [1.5, None, 3.25]})
    texto = table_markdown(frame)
    assert "1.50" in texto and "3.25" in texto
    largo = pd.DataFrame({"v": range(50)})
    truncado = table_markdown(largo, max_rows=10)
    assert "Se muestran 10 de 50 filas" in truncado


def test_table_markdown_con_frame_vacio():
    assert "Sin filas" in table_markdown(pd.DataFrame())


def test_checklist_marca_lo_presente_y_lo_ausente():
    tabla = checklist(CASE_SECTIONS, ["contexto", "problema"])
    assert len(tabla) == len(CASE_SECTIONS)
    assert tabla.loc[tabla.clave.eq("contexto"), "presente"].iloc[0] == "sí"
    assert tabla.loc[tabla.clave.eq("limitaciones"), "presente"].iloc[0] == "no"


def test_research_report_tiene_las_veinte_secciones():
    assert research_report("Investigación").required == RESEARCH_SECTIONS
    assert len(completar(research_report("I")).missing()) == 0
