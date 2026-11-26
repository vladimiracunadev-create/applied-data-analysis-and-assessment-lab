"""Pruebas de la normalización de texto (`lab.textual`)."""

from __future__ import annotations

import pandas as pd
import pytest

from lab.textual import (
    ABREVIATURAS,
    duplicate_candidates,
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
