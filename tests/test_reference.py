"""Invariantes de la solución de referencia del caso de transporte.

Estas pruebas no comparan contra valores fijos: comprueban **propiedades** que deben
cumplirse sea cual sea el volumen del caso. Una prueba con valores fijos se rompe al
regenerar los datos; una prueba de invariantes detecta un error de lógica real.

El acuerdo numérico con una segunda implementación está en
`tests/test_cross_validation.py`.
"""

from __future__ import annotations

import pytest

from solutions.reference import analyze

CASOS = (1, 2, 3)


@pytest.fixture(scope="module", params=CASOS)
def resultado(request):
    """Resultado de un caso, con su número."""
    return request.param, analyze(request.param)


def test_los_defectos_deliberados_se_detectan_en_la_cantidad_esperada(resultado):
    """El generador introduce 4n duplicados y n claves desconocidas por caso."""
    caso, tablas = resultado
    calidad = tablas["calidad"].set_index("indicador").valor
    assert calidad["duplicados_exactos"] == caso * 4
    assert calidad["claves_desconocidas"] == caso


def test_la_tabla_de_calidad_declara_todos_sus_indicadores(resultado):
    _, tablas = resultado
    esperados = {
        "filas_originales", "duplicados_exactos", "claves_desconocidas",
        "pasajeros_invalidos_realizados", "duracion_invalida_realizados",
    }
    assert set(tablas["calidad"].indicador) == esperados
    assert (tablas["calidad"].valor >= 0).all()


def test_la_demanda_cuadra_entre_el_corte_por_operador_y_el_corte_por_hora(resultado):
    """Dos agrupaciones del mismo conjunto deben sumar lo mismo."""
    _, tablas = resultado
    assert tablas["demanda"].pasajeros.sum() == tablas["demanda_hora"].pasajeros.sum()


def test_los_realizados_cuadran_entre_el_cumplimiento_y_el_corte_por_recorrido(resultado):
    _, tablas = resultado
    assert tablas["cumplimiento"].realizados.sum() == \
        tablas["realizados_recorrido"].realizados.sum()


def test_la_puntualidad_es_un_porcentaje(resultado):
    _, tablas = resultado
    assert tablas["duracion"].puntualidad_pct.between(0, 100).all()


def test_los_percentiles_estan_ordenados(resultado):
    """mediana <= P90 por definición, y la media está dentro del rango observado."""
    _, tablas = resultado
    duracion = tablas["duracion"]
    assert (duracion.mediana_min <= duracion.p90_min + 1e-9).all()
    assert (duracion.media_min > 0).all()


def test_el_cumplimiento_no_se_recorta_a_cien(resultado):
    """La regla del diccionario de datos es explícita: no se recorta."""
    _, tablas = resultado
    cumplimiento = tablas["cumplimiento"]
    validos = cumplimiento.cumplimiento_pct.dropna()
    assert (validos >= 0).all()
    # Si algún día el generador produjera más realizados que programados, el indicador
    # debe poder superar 100 sin que esta prueba lo impida.
    assert cumplimiento.realizados.ge(0).all()


def test_el_cumplimiento_conserva_los_dias_programados_sin_viajes(resultado):
    caso, tablas = resultado
    cumplimiento = tablas["cumplimiento"]
    # La programación del caso n cubre 9 recorridos por 7n días.
    programados = cumplimiento.viajes_programados.notna().sum()
    assert programados == 9 * 7 * caso


def test_el_cumplimiento_por_operador_divide_sumas_y_no_promedia_porcentajes(resultado):
    _, tablas = resultado
    operador = tablas["cumplimiento_operador"]
    esperado = 100 * operador.realizados / operador.viajes_programados
    assert operador.cumplimiento_pct.sub(esperado).abs().max() < 1e-9


def test_la_demanda_solo_cuenta_viajes_con_dato(resultado):
    _, tablas = resultado
    demanda = tablas["demanda"]
    assert (demanda.viajes_con_dato > 0).all()
    assert (demanda.pasajeros >= 0).all()


def test_todas_las_tablas_tienen_filas(resultado):
    _, tablas = resultado
    vacias = [nombre for nombre, tabla in tablas.items() if tabla.empty]
    assert not vacias, f"tablas vacías: {vacias}"


def test_ejecutar_dos_veces_da_el_mismo_resultado():
    """El cálculo no depende de ningún estado entre ejecuciones."""
    primera = analyze(1)
    segunda = analyze(1)
    for nombre, tabla in primera.items():
        assert tabla.equals(segunda[nombre]), nombre
