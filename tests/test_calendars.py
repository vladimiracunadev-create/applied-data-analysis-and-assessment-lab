"""Pruebas del calendario por reglas (`lab.calendars`).

El algoritmo de Pascua se contrasta con fechas publicadas de varios años, incluidos
extremos del rango. Cada constructor de regla se prueba por separado, y los recuentos
de exclusión marginal y solapamiento se verifican contra cálculos hechos a mano sobre
rangos pequeños.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from lab.calendars import (
    FIN_DE_SEMANA,
    NOMBRES_DIA,
    DayRule,
    build_calendar,
    by_month,
    date_ranges,
    days_of_month,
    easter_relative,
    easter_sunday,
    exclusion_report,
    intersect_with,
    overlap_matrix,
    specific_dates,
    summary,
    weekends,
    weeks_containing,
    whole_months,
)

#: Domingos de Pascua publicados, incluidos dos siglos de distancia.
PASCUA = {
    1900: date(1900, 4, 15),
    2000: date(2000, 4, 23),
    2020: date(2020, 4, 12),
    2021: date(2021, 4, 4),
    2022: date(2022, 4, 17),
    2023: date(2023, 4, 9),
    2024: date(2024, 3, 31),
    2025: date(2025, 4, 20),
    2026: date(2026, 4, 5),
    2027: date(2027, 3, 28),
}


# ----------------------------------------------------------------------------- Pascua
@pytest.mark.parametrize(("anio", "esperado"), sorted(PASCUA.items()))
def test_easter_sunday_contra_fechas_publicadas(anio, esperado):
    assert easter_sunday(anio) == esperado


def test_easter_sunday_siempre_cae_en_domingo_y_en_su_ventana():
    for anio in range(1900, 2101):
        pascua = easter_sunday(anio)
        assert pascua.weekday() == 6, f"{anio}: Pascua debe caer en domingo"
        # Por definición, entre el 22 de marzo y el 25 de abril.
        assert date(anio, 3, 22) <= pascua <= date(anio, 4, 25)


def test_easter_sunday_rechaza_anios_fuera_del_rango_de_validez():
    for anio in (1582, 4100, 0):
        with pytest.raises(ValueError, match="rango de validez"):
            easter_sunday(anio)


# ------------------------------------------------------------ constructores de regla
def fechas(inicio: str, fin: str) -> pd.DatetimeIndex:
    return pd.date_range(inicio, fin, freq="D")


def test_weekends_excluye_sabado_y_domingo():
    regla = weekends()
    # 2026-11-23 es lunes; la semana completa son siete días.
    semana = fechas("2026-11-23", "2026-11-29")
    assert regla.apply(semana).tolist() == [False] * 5 + [True, True]
    assert FIN_DE_SEMANA == (5, 6)
    assert NOMBRES_DIA[0] == "lunes" and NOMBRES_DIA[6] == "domingo"


def test_weekends_admite_otros_dias_y_valida():
    solo_domingo = weekends(weekdays_off=(6,))
    semana = fechas("2026-11-23", "2026-11-29")
    assert solo_domingo.apply(semana).sum() == 1
    with pytest.raises(ValueError, match="Días de la semana inválidos"):
        weekends(weekdays_off=(7,))


def test_specific_dates_excluye_exactamente_las_fechas_dadas():
    regla = specific_dates(["2026-09-11", "2026-12-25"], name="f", description="d")
    rango = fechas("2026-09-09", "2026-09-13")
    assert regla.apply(rango).tolist() == [False, False, True, False, False]


def test_whole_months_excluye_los_meses_completos():
    regla = whole_months((1, 2, 12))
    assert regla.apply(fechas("2026-01-01", "2026-01-31")).all()
    assert regla.apply(fechas("2026-03-01", "2026-03-31")).sum() == 0
    assert "enero" in regla.description and "diciembre" in regla.description
    with pytest.raises(ValueError, match="Meses inválidos"):
        whole_months((0, 13))


def test_days_of_month_excluye_el_mismo_dia_en_todos_los_meses():
    regla = days_of_month((28, 29))
    anio = fechas("2026-01-01", "2026-12-31")
    mascara = regla.apply(anio)
    # Doce meses con día 28 y doce con día 29, salvo febrero de 2026 que tiene 28 días.
    assert mascara.sum() == 12 + 11
    assert regla.apply(fechas("2026-03-28", "2026-03-29")).all()
    with pytest.raises(ValueError, match="Días del mes inválidos"):
        days_of_month((0, 32))


def test_date_ranges_incluye_ambos_extremos():
    regla = date_ranges([("2026-07-06", "2026-07-19")], name="r", description="d")
    assert regla.apply(fechas("2026-07-06", "2026-07-19")).all()
    assert not regla.apply(fechas("2026-07-05", "2026-07-05")).any()
    assert not regla.apply(fechas("2026-07-20", "2026-07-20")).any()
    with pytest.raises(ValueError, match="Rango invertido"):
        date_ranges([("2026-07-19", "2026-07-06")], name="r", description="d")


def test_weeks_containing_excluye_la_semana_completa():
    # 2026-09-18 es viernes; la semana de lunes a domingo va del 14 al 20.
    regla = weeks_containing(["2026-09-18"], name="s", description="d")
    assert regla.apply(fechas("2026-09-14", "2026-09-20")).all()
    assert not regla.apply(fechas("2026-09-13", "2026-09-13")).any()
    assert not regla.apply(fechas("2026-09-21", "2026-09-21")).any()


def test_weeks_containing_el_inicio_de_semana_cambia_el_resultado():
    lunes = weeks_containing(["2026-09-18"], name="s", description="d", week_start=0)
    domingo = weeks_containing(["2026-09-18"], name="s", description="d", week_start=6)
    rango = fechas("2026-09-10", "2026-09-25")
    assert lunes.apply(rango).sum() == domingo.apply(rango).sum() == 7
    assert lunes.apply(rango).tolist() != domingo.apply(rango).tolist()
    with pytest.raises(ValueError, match="week_start inválido"):
        weeks_containing(["2026-09-18"], name="s", description="d", week_start=7)


def test_easter_relative_construye_viernes_y_sabado_santo():
    regla = easter_relative((-2, -1), (2026,), name="pascua", description="d")
    # Pascua 2026 es el 5 de abril: Viernes Santo el 3 y Sábado Santo el 4.
    rango = fechas("2026-04-01", "2026-04-06")
    assert regla.apply(rango).tolist() == [False, False, True, True, False, False]


def test_una_regla_con_mascara_de_forma_equivocada_se_detecta():
    mala = DayRule(name="mala", description="d", exclude=lambda f: [True, False])
    with pytest.raises(ValueError, match="forma"):
        mala.apply(fechas("2026-01-01", "2026-01-05"))


# -------------------------------------------------------------------- build_calendar
def test_build_calendar_crea_una_columna_por_regla():
    calendario = build_calendar("2026-11-23", "2026-11-29", [weekends()])
    marco = calendario.frame
    assert len(marco) == 7
    assert list(marco.columns)[:6] == ["fecha", "anio", "mes", "dia", "dia_semana",
                                       "nombre_dia"]
    assert "fin_de_semana" in marco.columns
    assert marco["incluido"].sum() == 5
    assert len(calendario.included) == 5
    assert len(calendario) == 7


def test_build_calendar_valida_sus_entradas():
    with pytest.raises(ValueError, match="Rango invertido"):
        build_calendar("2026-12-31", "2026-01-01", [weekends()])
    with pytest.raises(ValueError, match="sin reglas"):
        build_calendar("2026-01-01", "2026-01-31", [])
    repetida = days_of_month((28,), name="misma")
    otra = days_of_month((29,), name="misma")
    with pytest.raises(ValueError, match="nombre repetido"):
        build_calendar("2026-01-01", "2026-01-31", [repetida, otra])


def test_el_orden_de_las_reglas_no_cambia_el_resultado():
    reglas = [weekends(), days_of_month((28, 29))]
    directo = build_calendar("2026-01-01", "2026-12-31", reglas)
    inverso = build_calendar("2026-01-01", "2026-12-31", list(reversed(reglas)))
    assert directo.frame["incluido"].sum() == inverso.frame["incluido"].sum()


# ----------------------------------------------------------------- exclusión marginal
def test_exclusion_report_distingue_lo_exclusivo_de_lo_solapado():
    """Dos reglas sobre un rango pequeño, con recuentos calculables a mano.

    Enero de 2026: el 1 es jueves. Los días 28 y 29 son miércoles y jueves, de modo
    que ninguno cae en fin de semana: las dos reglas no se solapan en absoluto.
    """
    calendario = build_calendar("2026-01-01", "2026-01-31",
                                [weekends(), days_of_month((28, 29))])
    reporte = exclusion_report(calendario).set_index("regla")
    assert reporte.loc["dias_del_mes", "excluye"] == 2
    assert reporte.loc["dias_del_mes", "exclusiva"] == 2
    assert reporte.loc["dias_del_mes", "solapada"] == 0


def test_exclusion_report_detecta_una_regla_redundante():
    """Una regla cuyos días ya excluye otra tiene exclusión exclusiva cero."""
    calendario = build_calendar(
        "2026-03-01", "2026-03-31",
        [days_of_month((28, 29)),
         specific_dates([date(2026, 3, 29)], name="joven_combatiente",
                        description="29 de marzo")],
    )
    reporte = exclusion_report(calendario).set_index("regla")
    assert reporte.loc["joven_combatiente", "excluye"] == 1
    assert reporte.loc["joven_combatiente", "exclusiva"] == 0
    assert reporte.loc["joven_combatiente", "solapada"] == 1
    assert reporte.loc["joven_combatiente", "aporte_pct"] == 0.0


def test_exclusion_report_incluye_la_fuente_de_cada_regla():
    regla = weekends(source="metodología publicada, nota 1")
    reporte = exclusion_report(build_calendar("2026-01-01", "2026-01-31", [regla]))
    assert reporte.loc[0, "fuente"] == "metodología publicada, nota 1"


def test_overlap_matrix_es_simetrica_con_la_diagonal_en_el_total():
    calendario = build_calendar("2026-01-01", "2026-12-31",
                                [weekends(), days_of_month((28, 29)),
                                 whole_months((1, 2, 12))])
    matriz = overlap_matrix(calendario)
    assert matriz.shape == (3, 3)
    assert (matriz.to_numpy() == matriz.to_numpy().T).all(), "debe ser simétrica"
    for regla in matriz.index:
        assert matriz.loc[regla, regla] == int(calendario.frame[regla].sum())


def test_summary_cuadra_la_suma_de_exclusiones_con_el_solapamiento():
    calendario = build_calendar("2026-01-01", "2026-12-31",
                                [weekends(), days_of_month((28, 29))])
    valores = summary(calendario).set_index("indicador").valor
    assert valores["dias_del_rango"] == 365
    assert valores["dias_laborales"] == 261
    assert valores["dias_incluidos"] + valores["dias_excluidos"] == 365
    # La identidad que tiene que cumplirse siempre.
    assert (valores["suma_de_exclusiones_por_regla"] - valores["solapamiento_total"]
            == valores["dias_excluidos"])


def test_by_month_informa_la_inclusion_relativa_a_los_laborales():
    calendario = build_calendar("2026-01-01", "2026-12-31",
                                [weekends(), whole_months((1,))])
    tabla = by_month(calendario).set_index("mes")
    assert tabla.loc[1, "incluidos"] == 0
    assert tabla.loc[1, "inclusion_pct"] == 0.0
    assert tabla.loc[3, "inclusion_pct"] == 100.0
    assert len(tabla) == 12


def test_intersect_with_separa_lo_elegible_de_lo_medible():
    calendario = build_calendar("2026-01-01", "2026-12-31", [weekends()])
    marco = intersect_with(calendario, (3, 6))
    assert marco["mes_de_medicion"].sum() == 61   # marzo 31 + junio 30
    assert marco["medible"].sum() == int(
        (marco["incluido"] & marco["mes_de_medicion"]).sum()
    )
    # Un día elegible fuera de los meses de medición no es medible.
    abril = marco.loc[marco["mes"].eq(4)]
    assert abril["incluido"].any()
    assert not abril["medible"].any()


def test_exclusion_report_sin_reglas_devuelve_tabla_con_columnas():
    from lab.calendars import Calendar

    vacio = Calendar(frame=pd.DataFrame({"incluido": []}), rules=())
    reporte = exclusion_report(vacio)
    assert reporte.empty
    assert "exclusiva" in reporte.columns
