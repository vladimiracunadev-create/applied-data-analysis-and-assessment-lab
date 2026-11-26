"""Pruebas de fechas, duraciones y bandas horarias (`lab.dates`)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from lab.dates import (
    DEFAULT_BANDS,
    MINUTES_PER_DAY,
    calendar_features,
    date_quality,
    duration_minutes,
    duration_minutes_excel,
    parse_datetime,
    parse_hms_seconds,
    seconds_to_hms,
    service_day_hour,
    time_band,
)


def test_parse_datetime_separa_vacios_de_no_interpretables():
    resultado = parse_datetime(pd.Series(["2026-10-01 08:00:00", "", None, "no es fecha"]))
    assert resultado.invalid == 1
    assert resultado.empty == 2
    assert resultado.values.notna().sum() == 1
    assert resultado.coverage_pct == pytest.approx(25.0)


def test_parse_datetime_con_formato_explicito_resuelve_la_ambiguedad():
    ambigua = pd.Series(["03-02-2026 10:00"])
    dia_primero = parse_datetime(ambigua, fmt="%d-%m-%Y %H:%M").values.iloc[0]
    mes_primero = parse_datetime(ambigua, fmt="%m-%d-%Y %H:%M").values.iloc[0]
    assert (dia_primero.day, dia_primero.month) == (3, 2)
    assert (mes_primero.day, mes_primero.month) == (2, 3)


def test_parse_datetime_dayfirst_cambia_la_lectura():
    serie = pd.Series(["03/02/2026"])
    assert parse_datetime(serie, dayfirst=True).values.iloc[0].day == 3
    assert parse_datetime(serie, dayfirst=False).values.iloc[0].month == 3


def test_parse_datetime_de_serie_vacia_no_divide_por_cero():
    assert np.isnan(parse_datetime(pd.Series([], dtype=object)).coverage_pct)


def test_duration_minutes_y_su_equivalente_de_excel_coinciden():
    inicio = pd.to_datetime(pd.Series(["2026-10-01 08:00:00", "2026-10-01 08:00:00", None]))
    fin = pd.to_datetime(pd.Series(["2026-10-01 08:45:00", None, "2026-10-01 09:00:00"]))
    minutos = duration_minutes(inicio, fin)
    assert minutos.iloc[0] == pytest.approx(45.0)
    assert minutos.iloc[1:].isna().all()

    # Serial de Excel: días decimales desde 1899-12-30. 45 minutos = 45/1440 de día.
    base = 46296.0  # valor arbitrario; solo importa la diferencia
    excel = duration_minutes_excel(pd.Series([base]), pd.Series([base + 45 / MINUTES_PER_DAY]))
    assert excel.iloc[0] == pytest.approx(45.0)


def test_duration_minutes_no_corrige_duraciones_negativas():
    inicio = pd.to_datetime(pd.Series(["2026-10-01 09:00:00"]))
    fin = pd.to_datetime(pd.Series(["2026-10-01 08:00:00"]))
    assert duration_minutes(inicio, fin).iloc[0] == pytest.approx(-60.0)


def test_parse_hms_seconds_admite_relleno_irregular_y_horas_sobre_24():
    serie = pd.Series(["0:00:00", "00:00:51", "07:16:40", "23:59:59", "24:00:00",
                       "25:10:00", "", "malo", None, "1:60:00"])
    segundos = parse_hms_seconds(serie)
    assert segundos.iloc[0] == 0
    assert segundos.iloc[1] == 51
    assert segundos.iloc[2] == 7 * 3600 + 16 * 60 + 40
    assert segundos.iloc[3] == 86399
    assert segundos.iloc[4] == 86400
    assert segundos.iloc[5] == 25 * 3600 + 10 * 60
    # Lo no interpretable queda nulo, nunca cero: una hora ausente no es la medianoche.
    assert segundos.iloc[6:9].isna().all()
    # Minutos fuera de rango no se aceptan en silencio.
    assert pd.isna(segundos.iloc[9])


def test_el_orden_como_texto_esta_mal_y_convertido_esta_bien():
    """Regresión del defecto encontrado en datos públicos reales."""
    crudo = ["0:00:00", "00:00:51", "00:01:22"]
    assert sorted(crudo) == ["00:00:51", "00:01:22", "0:00:00"], "el texto ordena mal"
    segundos = parse_hms_seconds(pd.Series(crudo))
    assert segundos.is_monotonic_increasing, "convertido a segundos, el orden es correcto"


def test_seconds_to_hms_es_la_inversa_con_relleno_consistente():
    textos = pd.Series(["0:00:00", "00:00:51", "25:10:00", "24:00:00"])
    ida = parse_hms_seconds(textos)
    vuelta = seconds_to_hms(ida)
    assert vuelta.tolist() == ["00:00:00", "00:00:51", "25:10:00", "24:00:00"]
    # La propiedad que importa: con relleno consistente, ordenar el TEXTO da el mismo
    # orden que ordenar los segundos. Con el texto original no ocurría.
    por_texto = sorted(vuelta.tolist())
    por_segundos = seconds_to_hms(ida.sort_values()).tolist()
    assert por_texto == por_segundos == ["00:00:00", "00:00:51", "24:00:00", "25:10:00"]


def test_seconds_to_hms_conserva_los_nulos_y_el_signo():
    resultado = seconds_to_hms(pd.Series([None, -90.0, 3661.0]))
    assert pd.isna(resultado.iloc[0])
    assert resultado.iloc[1] == "-00:01:30"
    assert resultado.iloc[2] == "01:01:01"


def test_service_day_hour_reduce_a_reloj_solo_al_final():
    segundos = parse_hms_seconds(pd.Series(["06:30:00", "23:59:59", "25:10:00", "48:00:00"]))
    horas = service_day_hour(segundos)
    assert horas.tolist() == [6.0, 23.0, 1.0, 0.0]
    # La reducción es la última operación: el valor original conserva la jornada.
    assert segundos.iloc[2] > 86400


def test_time_band_clasifica_los_limites_correctamente():
    horas = pd.to_datetime(pd.Series([
        "2026-10-01 00:00", "2026-10-01 05:59", "2026-10-01 06:00",
        "2026-10-01 08:59", "2026-10-01 09:00", "2026-10-01 17:00",
        "2026-10-01 20:59", "2026-10-01 21:00", "2026-10-01 23:59",
    ]))
    bandas = time_band(horas).tolist()
    assert bandas == ["nocturno", "nocturno", "punta_manana", "punta_manana",
                      "valle_manana", "punta_tarde", "punta_tarde", "tarde_noche",
                      "tarde_noche"]


def test_time_band_deja_nulo_lo_que_no_es_fecha():
    assert pd.isna(time_band(pd.Series([None])).iloc[0])


def test_las_bandas_por_defecto_cubren_las_24_horas_sin_solape():
    cubiertas = sorted(h for _, inicio, fin in DEFAULT_BANDS for h in range(inicio, fin))
    assert cubiertas == list(range(24))


def test_bandas_con_hueco_solape_o_rango_invalido_se_rechazan():
    serie = pd.to_datetime(pd.Series(["2026-10-01 10:00"]))
    with pytest.raises(ValueError, match="no cubren"):
        time_band(serie, (("a", 0, 12),))
    with pytest.raises(ValueError, match="solapan"):
        time_band(serie, (("a", 0, 13), ("b", 12, 24)))
    with pytest.raises(ValueError, match="inválida"):
        time_band(serie, (("a", 10, 10), ("b", 0, 24)))


def test_calendar_features_deriva_todos_los_atributos():
    serie = pd.to_datetime(pd.Series(["2026-10-03 07:30", "2026-10-05 13:00"]))
    rasgos = calendar_features(serie)
    assert rasgos.nombre_dia.tolist() == ["sabado", "lunes"]
    assert rasgos.es_fin_semana.tolist() == [True, False]
    assert rasgos.hora.tolist() == [7, 13]
    assert rasgos.banda.tolist() == ["punta_manana", "valle_tarde"]
    assert rasgos.dia.tolist() == [3, 5]


def test_date_quality_resume_el_estado_de_la_columna():
    tabla = date_quality(pd.Series(["2026-10-01 08:00", "", "malo"]))
    valores = tabla.set_index("indicador").valor
    assert valores["filas"] == 3
    assert valores["no_interpretables"] == 1
    assert valores["interpretadas"] == 1
    assert valores["cobertura_pct"] == pytest.approx(100 / 3, abs=1e-3)
