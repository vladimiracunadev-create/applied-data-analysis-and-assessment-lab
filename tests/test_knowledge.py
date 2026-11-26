"""Pruebas de la base de conocimiento (`lab.knowledge`)."""

from __future__ import annotations

from pathlib import Path

import pytest

from lab.knowledge import (
    RECORD_TYPES,
    KnowledgeBase,
    Record,
    load_record,
    search_cli,
    tokenize,
)

ENCABEZADO = """---
id: {id}
tipo: {tipo}
titulo: {titulo}
etiquetas: [{etiquetas}]
fuente: {fuente}
relacionados: [{relacionados}]
---

{cuerpo}
"""


def escribir(tmp_path: Path, record_id: str, tipo: str = "concepto", titulo: str = "Título",
             etiquetas: str = "a, b", relacionados: str = "", cuerpo: str = "Cuerpo del registro.",
             fuente: str = "lab/x.py") -> Path:
    destino = tmp_path / f"{record_id}.md"
    destino.write_text(
        ENCABEZADO.format(id=record_id, tipo=tipo, titulo=titulo, etiquetas=etiquetas,
                          fuente=fuente, relacionados=relacionados, cuerpo=cuerpo),
        encoding="utf-8",
    )
    return destino


def test_un_termino_presente_en_todos_los_registros_sigue_encontrandose(tmp_path):
    # Con la IDF clásica log(N/df) este término pesaría cero y la búsqueda no
    # devolvería nada, lo que en una base pequeña y temática es inaceptable.
    escribir(tmp_path, "uno", cuerpo="julianday en sqlite")
    escribir(tmp_path, "dos", cuerpo="julianday en postgres")
    base = KnowledgeBase.from_directory(tmp_path)
    assert len(base.search("julianday")) == 2


def test_tokenize_normaliza_y_descarta_palabras_vacias():
    tokens = tokenize("El denominador de la razón NO puede ser Cero")
    assert "denominador" in tokens and "cero" in tokens
    assert "el" not in tokens and "de" not in tokens and "la" not in tokens
    assert all(token == token.lower() for token in tokens)


def test_carga_de_un_registro_valido(tmp_path):
    ruta = escribir(tmp_path, "mi-registro", etiquetas="sql, fechas",
                    relacionados="otro-registro", cuerpo="Primera línea.\n\nSegunda.")
    record = load_record(ruta)
    assert record.id == "mi-registro"
    assert record.etiquetas == ("sql", "fechas")
    assert record.relacionados == ("otro-registro",)
    assert record.cuerpo.startswith("Primera línea.")
    assert "sql" in record.text
    assert record.summary(width=20).endswith("…")


def test_rechaza_registros_mal_formados(tmp_path):
    sin_encabezado = tmp_path / "x.md"
    sin_encabezado.write_text("solo cuerpo", encoding="utf-8")
    with pytest.raises(ValueError, match="debe comenzar"):
        load_record(sin_encabezado)

    sin_cierre = tmp_path / "y.md"
    sin_cierre.write_text("---\nid: y\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no está cerrado"):
        load_record(sin_cierre)

    con_tipo_malo = escribir(tmp_path, "z", tipo="ocurrencia")
    with pytest.raises(ValueError, match="fuera de"):
        load_record(con_tipo_malo)

    sin_cuerpo = escribir(tmp_path, "w", cuerpo="   ")
    with pytest.raises(ValueError, match="no tiene cuerpo"):
        load_record(sin_cuerpo)


def test_el_id_debe_coincidir_con_el_nombre_del_archivo(tmp_path):
    destino = tmp_path / "nombre-archivo.md"
    destino.write_text(
        ENCABEZADO.format(id="otro-id", tipo="concepto", titulo="T", etiquetas="a",
                          fuente="f", relacionados="", cuerpo="c"),
        encoding="utf-8")
    with pytest.raises(ValueError, match="no coincide con el nombre del archivo"):
        load_record(destino)


def test_metadato_obligatorio_ausente_y_linea_sin_dos_puntos(tmp_path):
    incompleto = tmp_path / "a.md"
    incompleto.write_text("---\nid: a\ntipo: concepto\n---\n\ncuerpo\n", encoding="utf-8")
    with pytest.raises(ValueError, match="faltan metadatos obligatorios"):
        load_record(incompleto)

    malo = tmp_path / "b.md"
    malo.write_text("---\nid b\n---\n\ncuerpo\n", encoding="utf-8")
    with pytest.raises(ValueError, match="sin ':'"):
        load_record(malo)


def test_identificador_repetido_se_rechaza():
    base = KnowledgeBase()
    base.add(Record("x", "concepto", "T", ("a",), "cuerpo"))
    with pytest.raises(ValueError, match="Identificador repetido"):
        base.add(Record("x", "concepto", "T", ("a",), "cuerpo"))


def test_from_directory_carga_recursivo_y_omite_readme(tmp_path):
    escribir(tmp_path, "uno")
    sub = tmp_path / "sub"
    sub.mkdir()
    escribir(sub, "dos")
    (tmp_path / "README.md").write_text("# índice, no es un registro", encoding="utf-8")
    base = KnowledgeBase.from_directory(tmp_path)
    assert len(base) == 2
    assert KnowledgeBase.from_directory(tmp_path / "no-existe").records == {}


def test_busqueda_ordena_por_relevancia(tmp_path):
    escribir(tmp_path, "muy-relevante", titulo="Denominador cero",
             cuerpo="El denominador cero aparece cuando el denominador es cero.")
    escribir(tmp_path, "poco-relevante", titulo="Otra cosa",
             cuerpo="Menciona el denominador una sola vez.")
    escribir(tmp_path, "nada-que-ver", titulo="Colores", cuerpo="Azul y verde.")
    base = KnowledgeBase.from_directory(tmp_path)
    resultados = base.search("denominador cero")
    assert [h.record.id for h in resultados] == ["muy-relevante", "poco-relevante"]
    assert resultados[0].score > resultados[1].score
    assert "denominador" in resultados[0].matched


def test_busqueda_con_filtros_y_casos_limite(tmp_path):
    escribir(tmp_path, "uno", tipo="error", etiquetas="sql", cuerpo="julianday precision")
    escribir(tmp_path, "dos", tipo="concepto", etiquetas="excel", cuerpo="julianday precision")
    base = KnowledgeBase.from_directory(tmp_path)
    assert [h.record.id for h in base.search("julianday", tipos=["error"])] == ["uno"]
    assert [h.record.id for h in base.search("julianday", etiquetas=["excel"])] == ["dos"]
    assert base.search("palabrainexistente") == []
    assert base.search("de la el") == []   # solo palabras vacías
    with pytest.raises(ValueError, match="límite debe ser positivo"):
        base.search("julianday", limit=0)


def test_consultas_por_tipo_y_etiqueta(tmp_path):
    escribir(tmp_path, "uno", tipo="error", etiquetas="sql, fechas")
    base = KnowledgeBase.from_directory(tmp_path)
    assert len(base.by_type("error")) == 1
    assert base.by_type("concepto") == []
    assert len(base.by_tag("sql")) == 1
    assert base.by_tag("inexistente") == []
    with pytest.raises(ValueError, match="Tipo inválido"):
        base.by_type("ocurrencia")
    with pytest.raises(KeyError, match="No existe el registro"):
        base.get("inexistente")


def test_broken_links_detecta_referencias_rotas(tmp_path):
    escribir(tmp_path, "uno", relacionados="fantasma")
    base = KnowledgeBase.from_directory(tmp_path)
    assert base.broken_links() == [("uno", "fantasma")]


def test_indice_y_estadisticas(tmp_path):
    escribir(tmp_path, "uno", tipo="error")
    base = KnowledgeBase.from_directory(tmp_path)
    indice = base.index_markdown()
    assert "uno" in indice and "error" in indice
    assert "Sin registros" in KnowledgeBase().index_markdown()
    estadisticas = base.stats()
    assert set(estadisticas) == set(RECORD_TYPES)
    assert estadisticas["error"] == 1 and estadisticas["concepto"] == 0


def test_search_cli_devuelve_texto_legible():
    salida = search_cli("denominador", limit=3)
    assert "resultado" in salida or "Sin resultados" in salida


# ------------------------------------------------- estado real del repositorio
def test_la_base_del_repositorio_carga_sin_errores_y_sin_enlaces_rotos():
    base = KnowledgeBase.from_directory()
    assert len(base) >= 10, "la base de conocimiento debe tener contenido real"
    assert base.broken_links() == []


def test_todos_los_registros_del_repositorio_declaran_fuente():
    base = KnowledgeBase.from_directory()
    sin_fuente = [r.id for r in base.records.values() if not r.fuente]
    assert not sin_fuente, f"registros sin fuente declarada: {sin_fuente}"


def test_la_busqueda_encuentra_los_registros_clave_del_repositorio():
    base = KnowledgeBase.from_directory()
    casos = {
        "denominador cero": "denominador-cero",
        "julianday punto flotante": "julianday-precision",
        "valor p": "valor-p-que-significa",
    }
    for consulta, esperado in casos.items():
        ids = [hit.record.id for hit in base.search(consulta, limit=3)]
        assert esperado in ids, f"{consulta!r} no encontró {esperado!r}; devolvió {ids}"
