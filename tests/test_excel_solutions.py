"""Pruebas de los libros de Excel resueltos (`scripts/build_excel_solutions.py`).

Qué se verifica aquí y qué no
    Estas pruebas abren el `.xlsx` generado y comprueban su **estructura**: que estén
    todas las hojas, que las columnas derivadas sean fórmulas y no valores, y que cada
    fórmula apunte al rango correcto de la hoja correcta y a la columna correcta.

    Lo que **no** se verifica aquí es el resultado numérico de las fórmulas: evaluarlas
    exige Excel o LibreOffice, que no están disponibles en integración continua. Esa
    comprobación la hace la hoja `30_control` del propio libro al abrirlo, y el acuerdo
    numérico entre implementaciones está cubierto por `tests/test_cross_validation.py`,
    que sí se ejecuta. La distinción es deliberada: declarar como «probado» algo que no
    se ejecutó sería exactamente el defecto que el laboratorio intenta evitar.
"""

from __future__ import annotations

import re

import openpyxl
import pytest
from openpyxl.worksheet.formula import ArrayFormula

from lab.excel import column_letter, data_start_row
from scripts.build_excel_solutions import (
    CALC_COLUMNS,
    COL,
    S_CALCULOS,
    S_CONTROL,
    S_CUMPLIMIENTO,
    S_DEMANDA,
    S_DOC,
    S_OPERADORES,
    S_PROGRAMACION,
    S_REALIZADOS,
    S_RECORRIDOS,
    S_VIAJES,
    build,
)

HOJAS_ESPERADAS = [
    "00_indice", S_VIAJES, S_RECORRIDOS, S_OPERADORES, S_PROGRAMACION, S_CALCULOS,
    S_DEMANDA, S_REALIZADOS, S_CUMPLIMIENTO, S_CONTROL, S_DOC,
]


def texto_formula(celda) -> str:
    """Texto de la fórmula, tanto si openpyxl la lee como matriz dinámica."""
    valor = celda.value
    if isinstance(valor, ArrayFormula):
        return valor.text
    return str(valor) if valor is not None else ""


@pytest.fixture(scope="module")
def libro(tmp_path_factory):
    destino = tmp_path_factory.mktemp("excel")
    ruta = build(1, output_dir=destino)
    return openpyxl.load_workbook(ruta), ruta


def test_el_libro_tiene_todas_las_hojas_en_orden(libro):
    workbook, _ = libro
    assert workbook.sheetnames == HOJAS_ESPERADAS


def test_el_indice_enlaza_cada_hoja_y_explica_las_secciones(libro):
    workbook, _ = libro
    indice = workbook["00_indice"]
    textos = [str(fila[0].value) for fila in indice.iter_rows(min_col=1, max_col=1)
              if fila[0].value]
    for hoja in HOJAS_ESPERADAS[1:]:
        assert hoja in textos, f"{hoja} no aparece en el índice"
    unidos = "\n".join(textos)
    for seccion in ("entradas:", "calculos:", "resultados:", "documentacion:"):
        assert seccion in unidos


def test_las_entradas_quedan_tal_como_vienen_del_csv(libro):
    workbook, _ = libro
    viajes = workbook[S_VIAJES]
    encabezado = data_start_row() - 1
    nombres = [viajes.cell(encabezado, c).value for c in range(1, 7)]
    assert nombres == ["viaje_id", "recorrido_id", "inicio", "fin", "pasajeros", "estado"]
    # Ninguna celda de la zona de entradas contiene una fórmula.
    for fila in viajes.iter_rows(min_row=data_start_row(), max_row=data_start_row() + 20):
        for celda in fila:
            assert not str(celda.value or "").startswith("=")


def test_la_hoja_de_calculos_declara_las_catorce_columnas(libro):
    workbook, _ = libro
    calculos = workbook[S_CALCULOS]
    encabezado = data_start_row() - 1
    nombres = [calculos.cell(encabezado, c + 1).value for c in range(len(CALC_COLUMNS))]
    assert nombres == list(CALC_COLUMNS)
    # La fila de unidades va encima del encabezado y declara las unidades clave.
    unidades = {calculos.cell(encabezado - 1, COL[n] + 1).value
                for n in ("duracion_min", "pasajeros", "meta_min")}
    assert unidades == {"min", "personas"}


def test_las_columnas_derivadas_son_formulas_no_valores(libro):
    workbook, _ = libro
    calculos = workbook[S_CALCULOS]
    primera = data_start_row()
    derivadas = CALC_COLUMNS[6:]
    assert len(derivadas) == 8
    for nombre in derivadas:
        celda = calculos.cell(primera, COL[nombre] + 1)
        assert texto_formula(celda).startswith("="), f"{nombre} no es una fórmula"


def test_el_congelado_y_el_autofiltro_estan_puestos(libro):
    workbook, _ = libro
    calculos = workbook[S_CALCULOS]
    assert calculos.freeze_panes == f"A{data_start_row()}"
    assert calculos.auto_filter.ref is not None
    assert calculos.auto_filter.ref.startswith(f"A{data_start_row() - 1}")


def test_el_cruce_declara_el_valor_para_la_clave_desconocida(libro):
    workbook, _ = libro
    calculos = workbook[S_CALCULOS]
    formula = texto_formula(calculos.cell(data_start_row(), COL["operador_id"] + 1))
    assert "XLOOKUP" in formula
    assert '"SIN CLAVE"' in formula
    assert f"'{S_RECORRIDOS}'!" in formula


def test_la_duracion_usa_el_factor_1440_y_se_protege_de_los_vacios(libro):
    workbook, _ = libro
    formula = texto_formula(
        workbook[S_CALCULOS].cell(data_start_row(), COL["duracion_min"] + 1)
    )
    assert "1440" in formula
    assert formula.startswith("=IF(OR(")


def test_la_bandera_de_demanda_exige_numero_y_no_negativo(libro):
    workbook, _ = libro
    formula = texto_formula(
        workbook[S_CALCULOS].cell(data_start_row(), COL["valido_demanda"] + 1)
    )
    assert "ISNUMBER" in formula
    assert ">=0" in formula


def test_la_puntualidad_solo_se_evalua_donde_aplica(libro):
    workbook, _ = libro
    formula = texto_formula(workbook[S_CALCULOS].cell(data_start_row(), COL["puntual"] + 1))
    # Vacío si el viaje no es realizado o la duración no es válida.
    assert formula.startswith("=IF(OR(")
    assert '""' in formula


def test_el_denominador_de_la_puntualidad_no_usa_el_criterio_distinto_de_vacio(libro):
    """Regresión del defecto documentado en knowledge/countifs-cadena-vacia.md.

    `COUNTIFS(rango, "<>")` cuenta como no vacías las celdas cuya fórmula devuelve
    cadena vacía, de modo que inflaría el denominador y bajaría la puntualidad.
    """
    workbook, _ = libro
    formula = texto_formula(workbook[S_REALIZADOS].cell(data_start_row(), 4))
    assert '">=0"' in formula
    assert '"<>"' not in formula


def test_las_agregaciones_apuntan_al_rango_completo_de_la_hoja_de_calculos(libro):
    workbook, ruta = libro
    calculos = workbook[S_CALCULOS]
    ultima_fila = calculos.max_row
    formula = texto_formula(workbook[S_DEMANDA].cell(data_start_row(), 2))
    assert "SUMIFS" in formula
    rangos = re.findall(rf"'{S_CALCULOS}'!\$([A-Z]+)\$(\d+):\$[A-Z]+\$(\d+)", formula)
    assert rangos, f"la fórmula no referencia {S_CALCULOS}: {formula}"
    for _columna, primera, ultima in rangos:
        assert int(primera) == data_start_row()
        assert int(ultima) == ultima_fila, (
            f"el rango termina en {ultima} y los datos llegan hasta {ultima_fila}"
        )
    # Y la columna sumada es la de pasajeros, no otra.
    assert f"'{S_CALCULOS}'!${column_letter(COL['pasajeros'])}$" in formula


def test_el_cumplimiento_usa_la_programacion_y_division_protegida(libro):
    workbook, _ = libro
    hoja = workbook[S_CUMPLIMIENTO]
    programados = texto_formula(hoja.cell(data_start_row(), 3))
    porcentaje = texto_formula(hoja.cell(data_start_row(), 5))
    assert f"'{S_PROGRAMACION}'!" in programados
    assert "SUMIFS" in programados
    assert porcentaje.startswith("=IF(N(")   # protegida contra denominador cero


def test_la_hoja_de_control_cuenta_las_discrepancias_de_las_tres_hojas(libro):
    workbook, _ = libro
    control = workbook[S_CONTROL]
    primera = data_start_row()
    formulas = [texto_formula(control.cell(primera + n, 2)) for n in range(4)]
    assert f"'{S_DEMANDA}'" in formulas[0]
    assert f"'{S_REALIZADOS}'" in formulas[1]
    assert f"'{S_CUMPLIMIENTO}'" in formulas[2]
    assert formulas[3].startswith("=SUM(")
    for formula in formulas[:3]:
        assert '"REVISAR"' in formula
    criterios = [control.cell(primera + n, 3).value for n in range(4)]
    assert all("0" in str(c) for c in criterios)


def test_la_documentacion_declara_que_son_datos_sinteticos_y_los_supuestos(libro):
    workbook, _ = libro
    nota = str(workbook[S_DOC].cell(3, 1).value)
    assert "sintéticos" in nota
    assert "no es una prueba" in nota.lower()
    for supuesto in ("duplicados exactos", "claves desconocidas", "100 %", "imputado"):
        assert supuesto in nota


def test_los_tres_casos_se_construyen_y_crecen_con_el_volumen(tmp_path):
    tamanos = []
    for caso in (1, 2, 3):
        ruta = build(caso, output_dir=tmp_path)
        assert ruta.exists()
        libro = openpyxl.load_workbook(ruta)
        assert libro.sheetnames == HOJAS_ESPERADAS
        tamanos.append(libro[S_CALCULOS].max_row)
    assert tamanos[0] < tamanos[1] < tamanos[2]


def test_un_caso_invalido_se_rechaza(tmp_path):
    with pytest.raises(ValueError, match="Caso inválido"):
        build(9, output_dir=tmp_path)
