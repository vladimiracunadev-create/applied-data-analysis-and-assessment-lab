"""Pruebas de `lab.schedules`: horarios de atención escritos en texto libre.

Qué se prueba, en orden de importancia
    1. **Que lo ilegible sea desconocido y no cerrado.** Es la regla que gobierna el
       módulo, y la que distingue un intérprete honesto de uno que produce cifras
       cómodas. Si esta prueba cae, todo indicador construido encima afirma cosas que
       el dato no respalda.
    2. Que los diez formatos del archivo público real se interpreten, incluido el que
       trae saltos de línea dentro de la celda.
    3. Los casos límite: medianoche, cruce de medianoche, rango invertido, rango vacío,
       horas fuera de rango, `pd.NA` en una columna de tipo `string`.
"""

from __future__ import annotations

import pandas as pd
import pytest

from lab.schedules import (
    DOMINGO,
    JUEVES,
    LUNES,
    MARTES,
    MIERCOLES,
    SABADO,
    SEGUNDOS_POR_DIA,
    VIERNES,
    Schedule,
    coverage,
    covers_window,
    is_open,
    parse_report,
    parse_schedule,
    parse_series,
)

#: Los diez textos distintos del archivo público de lugares de carga bip!, con el
#: número de locales que usa cada uno. Se guardan literales: son el contrato con el
#: dato real, y si el publicador cambia un formato esta tabla lo delata.
TEXTOS_REALES: tuple[tuple[str, int], ...] = (
    ("Lun-Dom 08:00-21:00", 168),
    ("Lunes a Viernes: 6:00 a 23:00 horas, Sábados: 6:30 a 23:00 horas, "
     "Domingos y festivos: 8:00 a 22:30 horas.", 143),
    ("Lun a Sab 08:00 a 21:00 Dom y Festivos 09:00 a 14:00", 15),
    ("Lun a Vie 06:00 a 23:00 Sab 07:00 a 23:00 Dom y Festivos 08:00 a 23:00", 9),
    ("Lun a Vie 07:00 a 22:00 Sab 08:00 a 22:00 Dom y Festivos 09:00 a 22:00", 7),
    ("Lun a Vie 05:30 a 23:00 Sab 06:30 a 23:00 Dom y Festivos 08:00 a 23:00", 2),
    ("Lun a Sab 08:30 a 21:00 Dom y Festivos 09:00 a 14:00", 1),
    ("Lun a Dom 09:00 a 22:00 Festivos 09:00 a 22:00", 1),
    ("Lun a Sab 08:00 a 21:00 Dom y Festivos 09:00 a 21:00", 1),
    ("Lun-Sáb 08:00-22:00\nDom 09:00-22:00 \nFest 08:00-22:00", 1),
)

HORA = 3600


def seg(hora: int, minuto: int = 0) -> int:
    return hora * HORA + minuto * 60


# ------------------------------------------------- la regla que gobierna el módulo
@pytest.mark.parametrize("texto", [
    None,
    "",
    "   ",
    pd.NA,
    float("nan"),
    "consultar en el local",
    "horario variable",
    "de lunes a viernes",          # días sin horas
    "08:00 a 21:00",               # horas sin días
])
def test_lo_que_no_se_entiende_es_desconocido_y_no_cerrado(texto):
    """`None`, nunca `False`. Es la prueba más importante del módulo.

    Convertir lo ilegible en «cerrado» transforma un vacío de datos en una afirmación
    sobre el mundo, y lo hace en la dirección que infla el problema. En el caso P09
    serían 1 579 locales declarados cerrados de madrugada sin que nadie lo haya dicho.
    """
    horario = parse_schedule(texto)
    assert horario.parsed is False
    assert horario.intervals == {}
    assert horario.note, "un horario no interpretado tiene que decir por qué"
    for dia in range(7):
        assert is_open(horario, dia, seg(12)) is None
        assert covers_window(horario, dia, 0, seg(5)) is None


def test_un_dia_que_el_texto_no_menciona_queda_desconocido():
    """«Lun a Vie» no dice nada del fin de semana. No dice que cierre."""
    horario = parse_schedule("Lun a Vie 09:00 a 18:00")
    assert horario.parsed is True
    assert horario.known_days == (LUNES, MARTES, MIERCOLES, JUEVES, VIERNES)
    assert is_open(horario, LUNES, seg(10)) is True
    assert is_open(horario, LUNES, seg(20)) is False      # el texto SÍ habla del lunes
    assert is_open(horario, SABADO, seg(10)) is None      # del sábado, no
    assert is_open(horario, DOMINGO, seg(10)) is None


def test_el_motivo_distingue_sin_dato_de_ilegible():
    """Las dos causas piden acciones distintas: una se completa, la otra se corrige."""
    assert parse_schedule(None).note == "sin dato"
    assert parse_schedule(pd.NA).note == "sin dato"
    assert parse_schedule("").note == "sin dato"
    assert "no a qué días" in parse_schedule("08:00 a 21:00").note
    assert "ningún rango de horas" in parse_schedule("abierto todos los días").note


def test_pd_na_de_una_columna_string_no_se_lee_como_texto():
    """Regresión: `pd.NA` no es un `float`, y la comprobación estrecha lo dejaba pasar.

    Con el error, `pd.NA` se convertía en la cadena «<NA>» y el informe de calidad
    decía «no se reconoce ningún rango de horas» en lugar de «sin dato», sobre los
    1 579 registros donde está el hallazgo del caso.
    """
    columna = pd.Series(["Lun-Dom 08:00-21:00", pd.NA], dtype="string")
    horarios = parse_series(columna)
    assert horarios.iloc[0].parsed is True
    assert horarios.iloc[1].parsed is False
    assert horarios.iloc[1].note == "sin dato"
    assert horarios.iloc[1].source == ""


# ------------------------------------------------------- los formatos del dato real
@pytest.mark.parametrize("texto,registros", TEXTOS_REALES, ids=lambda v: str(v)[:40])
def test_cada_formato_del_archivo_real_se_interpreta(texto, registros):
    horario = parse_schedule(texto)
    assert horario.parsed is True, f"no se interpretó: {texto!r}"
    assert len(horario.known_days) == 7, "los diez textos declaran los siete días"
    assert registros >= 1


@pytest.mark.parametrize("texto,_", TEXTOS_REALES, ids=lambda v: str(v)[:40])
def test_ningun_formato_real_cubre_la_madrugada(texto, _):
    """El hallazgo central de P09, fijado como prueba.

    Si el publicador agrega un local nocturno, esta prueba cae, y debe caer: la
    conclusión del caso dejaría de ser válida y hay que rehacerla.
    """
    horario = parse_schedule(texto)
    for dia in range(7):
        assert covers_window(horario, dia, 0, seg(5)) is False


def test_el_formato_con_saltos_de_linea_se_interpreta_igual():
    """Una celda de Excel con varias líneas es un solo valor, y hay que partirlo."""
    horario = parse_schedule("Lun-Sáb 08:00-22:00\nDom 09:00-22:00 \nFest 08:00-22:00")
    assert horario.opens_at(LUNES) == seg(8)
    assert horario.closes_at(SABADO) == seg(22)
    assert horario.opens_at(DOMINGO) == seg(9)
    assert horario.holiday_intervals == ((seg(8), seg(22)),)


def test_los_tramos_por_tipo_de_dia_no_se_mezclan():
    """El texto más largo del archivo trae tres tramos distintos. Son tres."""
    horario = parse_schedule(
        "Lunes a Viernes: 6:00 a 23:00 horas, Sábados: 6:30 a 23:00 horas, "
        "Domingos y festivos: 8:00 a 22:30 horas."
    )
    assert horario.intervals[LUNES] == ((seg(6), seg(23)),)
    assert horario.intervals[SABADO] == ((seg(6, 30), seg(23)),)
    assert horario.intervals[DOMINGO] == ((seg(8), seg(22, 30)),)
    assert horario.holiday_intervals == ((seg(8), seg(22, 30)),)


def test_festivos_manda_sobre_el_dia_de_la_semana_cuando_se_declara():
    horario = parse_schedule("Lun a Sab 08:00 a 21:00 Dom y Festivos 09:00 a 14:00")
    # Un lunes normal a las 20:00 está abierto; un lunes festivo, no.
    assert is_open(horario, LUNES, seg(20)) is True
    assert is_open(horario, LUNES, seg(20), holiday=True) is False
    assert is_open(horario, LUNES, seg(10), holiday=True) is True


def test_sin_tramo_de_festivos_se_usa_el_del_dia():
    """No se inventa un cierre: si el texto no habla de festivos, manda el día."""
    horario = parse_schedule("Lun-Dom 08:00-21:00")
    assert horario.holiday_intervals == ()
    assert is_open(horario, DOMINGO, seg(10), holiday=True) is True


# ----------------------------------------------------------------- casos límite
def test_el_fin_del_intervalo_es_exclusivo():
    horario = parse_schedule("Lun-Dom 08:00-21:00")
    assert is_open(horario, LUNES, seg(8)) is True
    assert is_open(horario, LUNES, seg(20, 59)) is True
    assert is_open(horario, LUNES, seg(21)) is False


def test_un_rango_invertido_se_lee_como_cruce_de_medianoche():
    """`22:00 a 02:00` es un local nocturno, no un intervalo vacío."""
    horario = parse_schedule("Lun a Dom 22:00 a 02:00")
    assert horario.intervals[LUNES] == ((0, seg(2)), (seg(22), SEGUNDOS_POR_DIA))
    assert is_open(horario, LUNES, seg(23)) is True
    assert is_open(horario, LUNES, seg(1)) is True
    assert is_open(horario, LUNES, seg(12)) is False
    # Y por tanto sí cubriría la madrugada, al contrario que los textos reales.
    assert covers_window(horario, LUNES, 0, seg(5)) is True


def test_atencion_continua():
    for texto in ("Lun a Dom 24 horas", "Lun-Dom 24/7", "Lun a Dom todo el dia"):
        horario = parse_schedule(texto)
        assert horario.parsed is True, texto
        assert is_open(horario, MIERCOLES, 0) is True
        assert is_open(horario, MIERCOLES, SEGUNDOS_POR_DIA - 1) is True


def test_un_rango_de_ancho_cero_se_descarta():
    """`08:00 a 08:00` no es un horario; sin días válidos queda desconocido."""
    assert parse_schedule("Lun a Vie 08:00 a 08:00").parsed is False


def test_las_horas_fuera_de_rango_se_descartan():
    assert parse_schedule("Lun a Vie 08:00 a 99:00").parsed is False
    assert parse_schedule("Lun a Vie 30:00 a 32:00").parsed is False


def test_el_rango_de_dias_que_envuelve_la_semana():
    """`Sab a Lun` son sábado, domingo y lunes."""
    horario = parse_schedule("Sab a Lun 10:00 a 14:00")
    assert horario.known_days == (LUNES, SABADO, DOMINGO)


def test_un_dia_con_dos_tramos_conserva_los_dos():
    horario = parse_schedule("Lun 09:00 a 13:00 Lun 15:00 a 19:00")
    assert horario.intervals[LUNES] == ((seg(9), seg(13)), (seg(15), seg(19)))
    assert is_open(horario, LUNES, seg(14)) is False     # el corte de mediodía
    assert is_open(horario, LUNES, seg(16)) is True
    assert horario.opens_at(LUNES) == seg(9)
    assert horario.closes_at(LUNES) == seg(19)


def test_las_mayusculas_y_las_tildes_no_importan():
    a = parse_schedule("LUN A SÁB 08:00 A 21:00")
    b = parse_schedule("lun a sab 08:00 a 21:00")
    assert a.intervals == b.intervals


@pytest.mark.parametrize("dia,segundo", [(-1, 0), (7, 0), (0, -1), (0, SEGUNDOS_POR_DIA)])
def test_is_open_rechaza_argumentos_fuera_de_rango(dia, segundo):
    horario = parse_schedule("Lun-Dom 08:00-21:00")
    with pytest.raises(ValueError):
        is_open(horario, dia, segundo)


@pytest.mark.parametrize("inicio,fin", [(0, 0), (seg(5), seg(5)), (seg(6), seg(5)), (0, SEGUNDOS_POR_DIA + 1)])
def test_covers_window_rechaza_ventanas_invalidas(inicio, fin):
    horario = parse_schedule("Lun-Dom 08:00-21:00")
    with pytest.raises(ValueError):
        covers_window(horario, LUNES, inicio, fin)


def test_covers_window_pregunta_por_solapamiento_no_por_contencion():
    """Un local abierto de 04:30 a 12:00 sirve de algo en la ventana nocturna."""
    horario = parse_schedule("Lun-Dom 04:30-12:00")
    assert covers_window(horario, LUNES, 0, seg(5)) is True
    assert covers_window(horario, LUNES, 0, seg(4)) is False


# --------------------------------------------------------------- informe de calidad
def test_el_informe_pone_primero_lo_que_no_se_interpreto():
    columna = pd.Series(
        ["Lun-Dom 08:00-21:00"] * 5 + ["consultar"] * 2 + [None] * 3, dtype="object"
    )
    tabla = parse_report(columna)
    assert tabla["interpretado"].iloc[0] == "no"
    assert tabla["registros"].sum() == 10
    no_interpretados = tabla.loc[tabla["interpretado"] == "no", "registros"].sum()
    assert no_interpretados == 5
    assert set(tabla.columns) == {
        "texto", "registros", "interpretado", "dias_declarados",
        "declara_festivos", "motivo",
    }


def test_el_informe_reemplaza_el_salto_de_linea_para_poder_mostrarse():
    tabla = parse_report(pd.Series(["Lun-Sáb 08:00-22:00\nDom 09:00-22:00"]))
    assert "\n" not in tabla["texto"].iloc[0]
    assert "⏎" in tabla["texto"].iloc[0]


def test_la_cobertura_es_el_porcentaje_interpretado():
    columna = pd.Series(["Lun-Dom 08:00-21:00"] * 3 + [None])
    assert coverage(columna) == 75.0
    assert pd.isna(coverage(pd.Series([], dtype="object")))


def test_parse_series_interpreta_cada_texto_una_sola_vez():
    """La deduplicación es lo que hace barato el campo real: 348 valores, 10 textos."""
    columna = pd.Series(["Lun-Dom 08:00-21:00"] * 1000)
    horarios = parse_series(columna)
    assert len(horarios) == 1000
    primero = horarios.iloc[0]
    assert all(h is primero for h in horarios), "debe reutilizarse el mismo objeto"


def test_un_horario_vacio_no_tiene_apertura_ni_cierre():
    vacio = Schedule()
    assert vacio.known_days == ()
    assert vacio.opens_at(LUNES) is None
    assert vacio.closes_at(LUNES) is None
