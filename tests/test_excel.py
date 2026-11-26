"""Pruebas de los libros de Excel (`lab.excel`).

Los libros se vuelven a abrir con openpyxl para comprobar el resultado real del
archivo, no la intención del código: hojas presentes, encabezados en su fila,
congelado, autofiltro, formatos y, sobre todo, que las fórmulas quedaron escritas
como fórmulas y no como texto.
"""

from __future__ import annotations

import openpyxl
import pandas as pd
import pytest
from openpyxl.worksheet.formula import ArrayFormula

from lab.excel import (
    NUMBER_FORMATS,
    Sheet,
    column_letter,
    countifs,
    data_start_row,
    duration_minutes_formula,
    range_ref,
    safe_divide,
    sumifs,
    write_workbook,
    xlookup,
)


@pytest.fixture
def frame() -> pd.DataFrame:
    return pd.DataFrame({"operador": ["A", "B"], "pasajeros": [100, 250]})


def formula_text(cell) -> str:
    """Texto de la fórmula, tanto si openpyxl la lee como array dinámico."""
    value = cell.value
    return value.text if isinstance(value, ArrayFormula) else str(value)


def test_column_letter_cubre_una_y_dos_letras():
    assert column_letter(0) == "A"
    assert column_letter(25) == "Z"
    assert column_letter(26) == "AA"
    assert column_letter(27) == "AB"
    with pytest.raises(ValueError, match="negativo"):
        column_letter(-1)


def test_data_start_row_depende_de_la_nota():
    assert data_start_row(has_notes=True) == 6
    assert data_start_row(has_notes=False) == 5


def test_range_ref_cita_el_nombre_de_la_hoja_y_valida_el_rango():
    assert range_ref("10_calculos", 1, 6, 455) == "'10_calculos'!$B$6:$B$455"
    with pytest.raises(ValueError, match="Rango vacío"):
        range_ref("h", 0, 10, 5)


def test_write_workbook_produce_indice_y_hojas_en_orden(tmp_path, frame):
    destino = write_workbook(
        tmp_path / "sub" / "libro.xlsx",
        [Sheet("20_resultados", frame, kind="resultados", notes="resultados finales"),
         Sheet("01_entradas", frame, kind="entradas", notes="datos crudos")],
        title="Prueba", source="datos sintéticos",
    )
    assert destino.exists()
    libro = openpyxl.load_workbook(destino)
    assert libro.sheetnames == ["00_indice", "20_resultados", "01_entradas"]
    indice = libro["00_indice"]
    assert indice["A1"].value == "Prueba"
    # En el índice las secciones se ordenan: entradas antes que resultados.
    assert indice["A6"].value == "01_entradas"
    assert indice["A7"].value == "20_resultados"
    assert "datos sintéticos" in indice["A3"].value


def test_sin_indice_cuando_se_pide_asi(tmp_path, frame):
    destino = write_workbook(tmp_path / "x.xlsx", [Sheet("datos", frame)], include_index=False)
    assert openpyxl.load_workbook(destino).sheetnames == ["datos"]


def test_encabezado_unidades_congelado_y_autofiltro(tmp_path, frame):
    destino = write_workbook(
        tmp_path / "x.xlsx",
        [Sheet("datos", frame, units={"pasajeros": "personas"},
               formats={"pasajeros": "entero"}, notes="una nota")],
    )
    hoja = openpyxl.load_workbook(destino)["datos"]
    assert hoja["A3"].value == "una nota"
    # Unidades sobre el encabezado: así el autofiltro arranca justo encima de los datos.
    assert hoja["B4"].value == "personas"
    assert hoja["A4"].value == "—"  # columna sin unidad declarada
    assert hoja["A5"].value == "operador"
    assert hoja["B5"].value == "pasajeros"
    assert hoja["A6"].value == "A"
    assert hoja.freeze_panes == "A6"
    assert hoja.auto_filter.ref == "A5:B7"
    assert hoja["B6"].number_format == NUMBER_FORMATS["entero"]


def test_las_formulas_se_escriben_como_formulas(tmp_path, frame):
    destino = write_workbook(
        tmp_path / "x.xlsx",
        [Sheet("datos", frame, notes="n",
               formulas={"D6": "=SUM(B6:B7)", "D7": xlookup("A6", "A6:A7", "B6:B7")})],
    )
    hoja = openpyxl.load_workbook(destino)["datos"]
    assert formula_text(hoja["D6"]) == "=SUM(B6:B7)"
    assert "XLOOKUP" in formula_text(hoja["D7"])


def test_nombre_de_hoja_invalido_o_largo_se_rechaza(frame):
    with pytest.raises(ValueError, match="Nombre de hoja inválido"):
        Sheet("con/barra", frame)
    with pytest.raises(ValueError, match="Nombre de hoja inválido"):
        Sheet("x" * 32, frame)
    with pytest.raises(ValueError, match="Nombre de hoja inválido"):
        Sheet("", frame)


def test_formato_desconocido_y_formula_sin_igual_se_rechazan(frame):
    with pytest.raises(ValueError, match="Formatos desconocidos"):
        Sheet("datos", frame, formats={"pasajeros": "moneda_marciana"})
    with pytest.raises(ValueError, match="debe comenzar"):
        Sheet("datos", frame, formulas={"A1": "SUM(B1:B2)"})


def test_libro_sin_hojas_o_con_nombres_repetidos_se_rechaza(tmp_path, frame):
    with pytest.raises(ValueError, match="al menos una hoja"):
        write_workbook(tmp_path / "x.xlsx", [])
    with pytest.raises(ValueError, match="repetidos"):
        write_workbook(tmp_path / "x.xlsx", [Sheet("a", frame), Sheet("a", frame)])


def test_hoja_vacia_no_rompe_la_escritura(tmp_path):
    vacio = pd.DataFrame(columns=["a", "b"])
    destino = write_workbook(tmp_path / "x.xlsx", [Sheet("vacia", vacio, notes="sin filas")])
    hoja = openpyxl.load_workbook(destino)["vacia"]
    assert hoja["A5"].value == "a"
    assert hoja.auto_filter.ref is None


# --------------------------------------------------------------- constructores de fórmula
def test_sumifs_y_countifs():
    assert sumifs("V[pax]", [("V[op]", "$A2")]) == "=SUMIFS(V[pax],V[op],$A2)"
    assert sumifs("V[pax]", [("V[op]", "$A2"), ("V[ok]", "1")]) == \
        "=SUMIFS(V[pax],V[op],$A2,V[ok],1)"
    assert countifs([("V[op]", "$A2")]) == "=COUNTIFS(V[op],$A2)"
    with pytest.raises(ValueError, match="al menos un par"):
        sumifs("V[pax]", [])
    with pytest.raises(ValueError, match="al menos un par"):
        countifs([])


def test_xlookup_declara_siempre_el_valor_por_defecto():
    assert xlookup("A2", "R[id]", "R[op]") == '=XLOOKUP(A2,R[id],R[op],"SIN CLAVE")'
    assert xlookup("A2", "R[id]", "R[op]", '""') == '=XLOOKUP(A2,R[id],R[op],"")'


def test_safe_divide_protege_el_denominador_cero():
    assert safe_divide("D2", "C2") == '=IF(N(C2)=0,"",D2/C2)'
    assert safe_divide("D2", "C2", scale=100) == '=IF(N(C2)=0,"",100*D2/C2)'


def test_duration_minutes_formula_usa_el_factor_1440():
    formula = duration_minutes_formula("C2", "D2")
    assert "1440" in formula
    assert formula.startswith("=IF(OR(")
