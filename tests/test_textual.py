"""Pruebas de la normalización de texto (`lab.textual`)."""

from __future__ import annotations

import pandas as pd
import pytest

from lab.textual import (
    ABREVIATURAS,
    duplicate_candidates,
    merge_audit,
    normalization_report,
    normalize_key,
    normalize_label,
    normalize_series,
    similarity,
    strip_accents,
)


def test_strip_accents_conserva_la_letra_base():
    assert strip_accents("Conchalí") == "Conchali"
    assert strip_accents("Ñuñoa") == "Nunoa"
    assert strip_accents("Estación Central") == "Estacion Central"
    assert strip_accents("sin tildes") == "sin tildes"


def test_normalize_key_resuelve_los_tres_casos_que_rompen_un_cruce():
    # Mayúsculas inconsistentes, como FULLCARGA y Fullcarga en el archivo real.
    assert normalize_key("Fullcarga") == normalize_key("FULLCARGA") == "FULLCARGA"
    # Tildes.
    assert normalize_key("Conchalí") == normalize_key("CONCHALI") == "CONCHALI"
    # Espacios al final, como en 'NOMBRE DE FANTASIA '.
    assert normalize_key("NOMBRE DE FANTASIA ") == "NOMBRE DE FANTASIA"


def test_normalize_key_colapsa_espacios_y_quita_puntuacion():
    assert normalize_key("  Av.   Providencia   1208 ") == "AV PROVIDENCIA 1208"
    assert normalize_key("Av. Matta 1200") == normalize_key("Av Matta 1200")


def test_normalize_key_puede_conservar_la_puntuacion():
    assert normalize_key("Av. Matta", keep_punctuation=True) == "AV. MATTA"


def test_normalize_key_expande_abreviaturas_solo_si_se_pide():
    assert normalize_key("Av Providencia") == "AV PROVIDENCIA"
    assert normalize_key("Av Providencia", expand_abbreviations=True) == "AVENIDA PROVIDENCIA"
    assert normalize_key("Gral Velasquez", expand_abbreviations=True) == "GENERAL VELASQUEZ"
    assert all(k == k.upper() for k in ABREVIATURAS)


def test_normalize_key_trata_los_nulos_como_vacio_y_no_como_texto():
    for valor in (None, float("nan"), pd.NA):
        assert normalize_key(valor) == ""
    # Y los nulos que llegaron como texto desde un CSV mal leído.
    assert normalize_key("nan") == ""
    assert normalize_key("NaT") == ""
    assert normalize_key("<NA>") == ""
    assert normalize_key("   ") == ""


def test_normalize_series_devuelve_texto_y_conserva_el_indice():
    serie = pd.Series(["Fullcarga", "FULLCARGA", None], index=[7, 8, 9])
    resultado = normalize_series(serie)
    assert resultado.tolist() == ["FULLCARGA", "FULLCARGA", ""]
    assert list(resultado.index) == [7, 8, 9]
    assert resultado.dtype == "string"


def test_normalize_label_conserva_las_tildes_para_mostrar():
    """La clave sirve para agrupar; la etiqueta, para que una persona lea el informe."""
    assert normalize_label("ÑUÑOA") == "Ñuñoa"
    assert normalize_label("ESTACION CENTRAL") == "Estacion Central"
    assert normalize_label("PEDRO AGUIRRE CERDA") == "Pedro Aguirre Cerda"
    # Las partículas quedan en minúscula, salvo al principio.
    assert normalize_label("SAN JOSE DE MAIPO") == "San Jose de Maipo"
    assert normalize_label("LA GRANJA") == "La Granja"
    assert normalize_label(None) == ""


def test_similarity_es_simetrica_y_acotada():
    assert similarity("Fullcarga", "FULLCARGA") == 1.0
    assert similarity("", "") == 1.0
    assert similarity("algo", "") == 0.0
    izquierda = similarity("LIDER EXPRESS LYON", "LIDER EXPRES LYON")
    derecha = similarity("LIDER EXPRES LYON", "LIDER EXPRESS LYON")
    assert izquierda == derecha
    assert 0.9 < izquierda < 1.0
    assert similarity("METRO", "WALMART") < 0.5


def test_duplicate_candidates_propone_pares_para_revision():
    frame = pd.DataFrame({
        "nombre": ["LIDER EXPRESS LYON", "LIDER EXPRES LYON", "METRO SAN PABLO"],
        "comuna": ["PROVIDENCIA", "PROVIDENCIA", "LO PRADO"],
    })
    pares = duplicate_candidates(frame, ["nombre", "comuna"], threshold=0.9)
    assert len(pares) == 1
    fila = pares.iloc[0]
    assert {fila.fila_a, fila.fila_b} == {0, 1}
    assert fila.parecido >= 0.9


def test_duplicate_candidates_sin_candidatos_devuelve_tabla_vacia_con_columnas():
    frame = pd.DataFrame({"nombre": ["METRO", "WALMART"]})
    pares = duplicate_candidates(frame, ["nombre"])
    assert pares.empty
    assert list(pares.columns) == ["fila_a", "fila_b", "parecido", "texto_a", "texto_b"]


def test_duplicate_candidates_protege_del_coste_cuadratico():
    grande = pd.DataFrame({"nombre": [f"local {n}" for n in range(60)]})
    with pytest.raises(ValueError, match="cuadrática"):
        duplicate_candidates(grande, ["nombre"], max_rows=50)
    with pytest.raises(ValueError, match="Faltan columnas"):
        duplicate_candidates(grande, ["inexistente"])


def test_normalization_report_cuantifica_los_grupos_espurios():
    serie = pd.Series(["Fullcarga", "FULLCARGA", "fullcarga", "Walmart", None])
    tabla = normalization_report(serie, "ENTIDAD").set_index("indicador").valor
    assert tabla["filas"] == 5
    assert tabla["distintos_sin_normalizar"] == 4   # tres variantes + Walmart
    assert tabla["distintos_normalizados"] == 2     # FULLCARGA y WALMART
    assert tabla["grupos_espurios_evitados"] == 2
    assert tabla["vacios_tras_normalizar"] == 1


# --------------------------------------------- la dirección del error que nadie mide
def test_merge_audit_devuelve_las_formas_crudas_de_cada_fusion():
    """`normalization_report` cuenta cuántas fusiones hubo; esta función dice cuáles.

    Es la única parte de una normalización que una persona tiene que confirmar: cada
    fila es la afirmación de que dos textos distintos nombran la misma cosa.
    """
    serie = pd.Series(["FULLCARGA", "Fullcarga", "Fullcarga", "WALMART", "Metro"])
    tabla = merge_audit(serie, "entidad")
    assert len(tabla) == 1
    fila = tabla.iloc[0]
    assert fila["clave_normalizada"] == "FULLCARGA"
    assert fila["formas_crudas"] == 2
    assert fila["filas_afectadas"] == 3
    assert "Fullcarga (2)" in fila["formas"]
    assert "FULLCARGA (1)" in fila["formas"]
    assert fila["columna"] == "entidad"


def test_merge_audit_no_informa_lo_que_no_fusiono():
    """Una columna que la normalización no toca devuelve una tabla vacía."""
    tabla = merge_audit(pd.Series(["UNO", "DOS", "TRES"]), "x")
    assert tabla.empty
    assert list(tabla.columns) == [
        "columna", "clave_normalizada", "formas_crudas", "formas", "filas_afectadas",
    ]


def test_merge_audit_delata_una_fusion_indebida():
    """El caso peligroso: expandir abreviaturas junta dos cosas distintas.

    `AV 100` y `AVENIDA 100` son el mismo lugar. Pero si una entidad se llamara
    literalmente `AV`, la expansión la fundiría con `AVENIDA`. La función no decide:
    pone las formas crudas a la vista para que alguien lo decida.
    """
    serie = pd.Series(["AV 100", "AVENIDA 100"])
    assert merge_audit(serie, "direccion").empty
    con_expansion = merge_audit(serie, "direccion", expand_abbreviations=True)
    assert len(con_expansion) == 1
    assert con_expansion["formas_crudas"].iloc[0] == 2
    assert "AV 100" in con_expansion["formas"].iloc[0]
    assert "AVENIDA 100" in con_expansion["formas"].iloc[0]


def test_merge_audit_ordena_por_cuantas_formas_absorbio():
    serie = pd.Series(["a", "A", "Á", "b", "B"])
    tabla = merge_audit(serie, "x")
    assert tabla["formas_crudas"].is_monotonic_decreasing
    assert tabla["formas_crudas"].iloc[0] == 3


def test_merge_audit_ignora_los_nulos_y_los_vacios():
    serie = pd.Series(["UNO", "uno", None, "", "   "])
    tabla = merge_audit(serie, "x")
    assert len(tabla) == 1
    assert tabla["filas_afectadas"].iloc[0] == 2
