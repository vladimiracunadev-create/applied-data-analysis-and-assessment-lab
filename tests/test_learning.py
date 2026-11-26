"""Pruebas del programa de aprendizaje (`lab.learning`).

El validador de secciones es el mecanismo que mantiene vivo el estándar pedagógico:
si una clase publicada pierde la sección de errores frecuentes o la de referencias,
esta suite falla.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from lab.learning import (
    BLOCKS,
    REQUIRED_SECTIONS,
    check_sections,
    coverage_summary,
    discover_lessons,
    learning_map_mermaid,
    load_lesson,
    program_frame,
    program_markdown,
)

SECCIONES_COMPLETAS = "\n".join(f"## {texto.capitalize()} de la clase"
                                for _, texto in REQUIRED_SECTIONS)


def escribir(directorio: Path, nombre: str = "01-demo.md", titulo: str = "Clase de demostración",
             cuerpo: str = SECCIONES_COMPLETAS) -> Path:
    directorio.mkdir(parents=True, exist_ok=True)
    destino = directorio / nombre
    destino.write_text(f"# {titulo}\n\n{cuerpo}\n", encoding="utf-8")
    return destino


def test_el_estandar_declara_diecisiete_secciones():
    assert len(REQUIRED_SECTIONS) == 17
    claves = [clave for clave, _ in REQUIRED_SECTIONS]
    assert len(set(claves)) == 17
    for obligatoria in ("objetivos", "formulas", "errores", "validacion", "referencias",
                        "glosario"):
        assert obligatoria in claves


def test_check_sections_tolera_tildes_y_mayusculas():
    assert check_sections([f"{texto.upper()}" for _, texto in REQUIRED_SECTIONS]) == []
    sin_tildes = ["Formulas matematicas", "Explicacion"]
    faltantes = check_sections(sin_tildes)
    assert "formulas" not in faltantes
    assert "explicacion" not in faltantes
    assert "objetivos" in faltantes


def test_clase_completa_no_tiene_hallazgos(tmp_path):
    leccion = load_lesson(escribir(tmp_path / "00-fundamentos"))
    assert leccion.ok, leccion.issues
    assert leccion.order == 1
    assert leccion.slug == "demo"
    assert leccion.title == "Clase de demostración"
    assert leccion.word_count > 0


def test_clase_incompleta_nombra_las_secciones_que_faltan(tmp_path):
    leccion = load_lesson(escribir(tmp_path / "00-fundamentos",
                                   cuerpo="## Objetivos\n## Glosario"))
    assert not leccion.ok
    assert any("errores" in problema for problema in leccion.issues)
    assert any("referencias" in problema for problema in leccion.issues)
    assert len(leccion.issues) == 15


def test_nombre_de_archivo_y_titulo_obligatorios(tmp_path):
    with pytest.raises(ValueError, match="convención"):
        load_lesson(escribir(tmp_path / "b", nombre="sin-numero.md"))
    sin_titulo = tmp_path / "b" / "02-x.md"
    sin_titulo.parent.mkdir(parents=True, exist_ok=True)
    sin_titulo.write_text("## Objetivos\n", encoding="utf-8")
    with pytest.raises(ValueError, match="título de nivel 1"):
        load_lesson(sin_titulo)


def test_discover_lessons_ordena_por_bloque_y_numero(tmp_path):
    base = tmp_path / "learning"
    escribir(base / "20-programacion", nombre="02-segunda.md")
    escribir(base / "20-programacion", nombre="01-primera.md")
    escribir(base / "00-fundamentos", nombre="01-base.md")
    lecciones = discover_lessons(base)
    assert [leccion.slug for leccion in lecciones] == ["base", "primera", "segunda"]
    assert discover_lessons(tmp_path / "no-existe") == []


def test_archivos_que_no_siguen_la_convencion_se_ignoran(tmp_path):
    base = tmp_path / "learning"
    escribir(base / "00-fundamentos", nombre="01-ok.md")
    (base / "00-fundamentos" / "README.md").write_text("# índice", encoding="utf-8")
    assert len(discover_lessons(base)) == 1


def test_program_frame_y_markdown(tmp_path):
    base = tmp_path / "learning"
    escribir(base / "00-fundamentos", nombre="01-base.md")
    incompleta = escribir(base / "40-analisis", nombre="01-parcial.md",
                          cuerpo="## Objetivos")
    lecciones = discover_lessons(base)
    tabla = program_frame(lecciones)
    assert list(tabla.columns)[:4] == ["bloque", "orden", "clase", "titulo"]
    assert set(tabla.cumple_estandar) == {"sí", "no"}
    assert program_frame([]).empty

    texto = program_markdown(lecciones, base_from="")
    assert "Fundamentos de datos" in texto
    assert "incompleta" in texto          # la clase incompleta se marca, no se oculta
    assert "sin clases publicadas" in texto   # los bloques vacíos se declaran
    assert incompleta.name in texto or "parcial" in texto


def test_coverage_summary_declara_lo_proyectado(tmp_path):
    base = tmp_path / "learning"
    escribir(base / "00-fundamentos", nombre="01-base.md")
    resumen = coverage_summary(discover_lessons(base)).set_index("bloque")
    assert resumen.loc["Fundamentos de datos", "estado"] == "publicado"
    assert resumen.loc["Temas avanzados", "estado"] == "proyectado"
    assert resumen.loc["Temas avanzados", "clases"] == 0
    assert len(resumen) == len(BLOCKS)


def test_mapa_mermaid_encadena_los_bloques():
    mapa = learning_map_mermaid()
    assert mapa.startswith("```mermaid")
    assert "flowchart TD" in mapa
    assert mapa.count("-->") == len(BLOCKS) - 1
    for _, titulo, _ in BLOCKS:
        assert titulo in mapa


# ------------------------------------------------- estado real del repositorio
def test_todas_las_clases_publicadas_cumplen_el_estandar():
    lecciones = discover_lessons()
    assert lecciones, "el repositorio debe tener clases publicadas"
    incumplen = {leccion.reference: leccion.issues for leccion in lecciones if not leccion.ok}
    assert not incumplen, f"clases que no cumplen el estándar: {incumplen}"


def test_las_clases_del_repositorio_estan_en_bloques_declarados():
    bloques = {clave for clave, _, _ in BLOCKS}
    desconocidos = {leccion.block for leccion in discover_lessons()} - bloques
    assert not desconocidos, f"bloques no declarados: {sorted(desconocidos)}"


def test_cada_clase_tiene_contenido_sustantivo():
    # Umbral deliberadamente bajo: detecta una clase con los encabezados puestos y el
    # cuerpo vacío, que pasaría el validador de secciones sin enseñar nada.
    delgadas = [(leccion.reference, leccion.word_count) for leccion in discover_lessons() if leccion.word_count < 600]
    assert not delgadas, f"clases con los encabezados puestos y poco contenido: {delgadas}"
