"""Pruebas del caso P09 (`cases.carga_nocturna.solution`).

Por qué no se usan los datos reales
    El caso cruza el feed del DTPM (12,8 MB, licencia no verificada) con los cinco Excel
    de bip! (CC BY-NC 2.0). Ninguno se versiona.

Qué construyen las pruebas
    Un feed mínimo con **aritmética calculable a mano**, donde cada parada tiene un
    número de llegadas nocturnas que se puede verificar contando:

    - `VENTANA_MEDIANOCHE`: 23:00 → 24:00 cada 30 min, dos salidas (23:00 y 23:30).
      La parada `P_TARDE` está a 40 min del inicio del viaje, de modo que recibe las
      llegadas a las **23:40 y 00:10**. Solo la segunda es nocturna, y solo aparece si
      el cálculo mira el intervalo de segundos de servicio `[86 400, 104 400)`. Es la
      parada que un filtro por hora de reloj pierde.
    - `VENTANA_MADRUGADA`: 00:00 → 01:00 cada 30 min, dos salidas, con la parada
      `P_NOCHE` a cero minutos: llegadas a las **00:00 y 00:30**, las dos nocturnas.
    - `VENTANA_MANANA`: 06:00 → 07:00, que no aporta ninguna llegada nocturna y existe
      para comprobar que no se cuela.

    Y tres locales de carga colocados a propósito: uno abierto de noche, uno cerrado
    con horario conocido, y uno sin horario, que son las tres situaciones que producen
    las cuatro clases del resultado.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from cases.carga_nocturna.solution import (
    CLASE_ABIERTA,
    CLASE_CERRADA,
    CLASE_INDETERMINADA,
    CLASE_SIN_LOCAL,
    NOCHE_FIN,
    NOCHE_INICIO,
    RADIO_M,
    _llegadas_en,
    cargar_servicio,
    clasificar,
    cobertura_del_campo_horario,
    comparar_con_el_atajo,
    informe_de_ventanas,
    intensidad_del_servicio,
    intervalo_de_la_respuesta,
    llegadas_nocturnas,
    lo_que_falta_para_contestar,
    peores_paradas,
    respuesta,
    resumen,
    servicio_por_parada,
    ventanas_de_frecuencia,
)
from lab.geo import grados_por_km
from lab.schedules import parse_series

LAT0, LON0 = -33.45, -70.66
GRADO_LAT_KM, GRADO_LON_KM = grados_por_km(LAT0)

#: Un feed mínimo con las tres ventanas descritas en el docstring del módulo.
ARCHIVOS: dict[str, str] = {
    "frequencies.txt": (
        "trip_id,start_time,end_time,headway_secs\n"
        "T_TARDE,23:00:00,24:00:00,1800\n"      # salidas 23:00 y 23:30
        "T_NOCHE,00:00:00,01:00:00,1800\n"      # salidas 00:00 y 00:30
        "T_MANANA,06:00:00,07:00:00,1800\n"     # salidas 06:00 y 06:30
        "T_MALA,10:00:00,09:00:00,1800\n"       # inválida: fin antes del inicio
        "T_CERO,10:00:00,11:00:00,0\n"          # inválida: intervalo cero
    ),
    "trips.txt": (
        "trip_id,service_id\n"
        "T_TARDE,L\nT_NOCHE,L\nT_MANANA,L\nT_MALA,L\nT_CERO,L\nT_ABS,L\n"
    ),
    "stop_times.txt": (
        "trip_id,stop_id,arrival_time\n"
        "T_TARDE,P_TARDE,0:40:00\n"             # llega 23:40 y 00:10 → 1 nocturna
        "T_NOCHE,P_NOCHE,0:00:00\n"             # llega 00:00 y 00:30 → 2 nocturnas
        "T_NOCHE,P_LEJOS,0:10:00\n"             # llega 00:10 y 00:40 → 2 nocturnas
        "T_MANANA,P_DIA,0:00:00\n"              # 06:00 y 06:30 → ninguna
        "T_ABS,P_ABSOLUTA,07:15:00\n"           # horario absoluto, no nocturno
    ),
    "stops.txt": (
        "stop_id,stop_name,stop_lat,stop_lon,location_type\n"
        f"P_TARDE,Parada tarde,{LAT0},{LON0},0\n"
        f"P_NOCHE,Parada noche,{LAT0 + 0.5 * GRADO_LAT_KM},{LON0},0\n"
        f"P_LEJOS,Parada lejos,{LAT0 + 10 * GRADO_LAT_KM},{LON0},0\n"
        f"P_DIA,Parada de dia,{LAT0},{LON0 + 0.1 * GRADO_LON_KM},0\n"
        f"P_ABSOLUTA,Parada absoluta,{LAT0},{LON0},0\n"
        "N1,Nodo de pasillo,,,3\n"
    ),
}


@pytest.fixture(scope="module")
def feed(tmp_path_factory) -> Path:
    destino = tmp_path_factory.mktemp("feed-noche") / "feed.zip"
    with zipfile.ZipFile(destino, "w") as zf:
        for nombre, contenido in ARCHIVOS.items():
            zf.writestr(nombre, contenido)
    return destino


@pytest.fixture(scope="module")
def tablas(feed) -> dict[str, pd.DataFrame]:
    return cargar_servicio(feed)


def locales_de_prueba() -> pd.DataFrame:
    """Tres locales: uno abierto de noche, uno cerrado, uno sin horario.

    El primero está a 100 m de `P_TARDE`; el segundo y el tercero, a 100 m de
    `P_NOCHE`. `P_LEJOS` queda a 10 km de todo.
    """
    filas = [
        {"codigo": "ABIERTO", "tipo_local": "Centro bip! estándar",
         "lat": LAT0 + 0.1 * GRADO_LAT_KM, "lon": LON0,
         "horario": "Lun a Dom 22:00 a 06:00"},
        {"codigo": "CERRADO", "tipo_local": "Retail",
         "lat": LAT0 + 0.55 * GRADO_LAT_KM, "lon": LON0,
         "horario": "Lun-Dom 08:00-21:00"},
        {"codigo": "SIN_DATO", "tipo_local": "Punto bip!",
         "lat": LAT0 + 0.52 * GRADO_LAT_KM, "lon": LON0,
         "horario": pd.NA},
    ]
    locales = pd.DataFrame(filas)
    horarios = parse_series(locales["horario"])
    locales["horario_interpretado"] = horarios
    locales["horario_conocido"] = [h.parsed for h in horarios]
    from cases.carga_nocturna.solution import _abre_en_alguna_noche

    locales["abre_de_noche"] = [_abre_en_alguna_noche(h) for h in horarios]
    return locales


@pytest.fixture
def locales() -> pd.DataFrame:
    return locales_de_prueba()


# ------------------------------------------------------ la aritmética, a mano
@pytest.mark.parametrize("primero,intervalo,salidas,desde,hasta,esperado", [
    (0, 1800, 2, 0, 18000, 2),          # 00:00 y 00:30, las dos dentro
    (0, 1800, 2, 0, 1800, 1),           # fin exclusivo: solo la de 00:00
    (0, 1800, 2, 1800, 18000, 1),       # inicio inclusivo: solo la de 00:30
    (85200, 1800, 2, 0, 18000, 0),      # 23:40 y 00:10 no caen en [0, 5h)
    (85200, 1800, 2, 86400, 104400, 1), # pero la de 00:10 sí cae tras medianoche
    (21600, 1800, 2, 0, 18000, 0),      # 06:00 y 06:30, ninguna
    (0, 1800, 0, 0, 18000, 0),          # sin salidas
])
def test_contar_llegadas_de_una_progresion(primero, intervalo, salidas, desde, hasta, esperado):
    """La operación que permite no expandir nada. Cada caso es verificable contando."""
    resultado = _llegadas_en(
        np.array([primero], dtype=float), np.array([intervalo], dtype=float),
        np.array([salidas], dtype=float), desde, hasta,
    )
    assert int(resultado[0]) == esperado


def test_las_ventanas_invalidas_se_excluyen(tablas):
    ventanas = ventanas_de_frecuencia(tablas)
    assert set(ventanas["trip_id"]) == {"T_TARDE", "T_NOCHE", "T_MANANA"}
    # end_time exclusivo: de 23:00 a 24:00 cada 30 min son DOS salidas, no tres.
    assert int(ventanas.set_index("trip_id").loc["T_TARDE", "salidas"]) == 2


def test_el_informe_de_ventanas_cuenta_las_que_alcanzan_la_madrugada(tablas):
    informe = informe_de_ventanas(tablas).set_index("service_id")
    assert informe.loc["L", "ventanas"] == 3
    assert informe.loc["L", "salidas"] == 6
    assert informe.loc["L", "ventanas_que_empiezan_antes_de_las_5"] == 1
    assert informe.loc["L", "ventanas_que_terminan_a_las_24"] == 1


# ------------------------------------------------------ las dos ventanas de la noche
def test_las_llegadas_nocturnas_son_las_calculadas_a_mano(tablas):
    llegadas = llegadas_nocturnas(tablas).set_index("stop_id")
    assert set(llegadas.index) == {"P_TARDE", "P_NOCHE", "P_LEJOS"}
    assert llegadas.loc["P_NOCHE", "llegadas"] == 2
    assert llegadas.loc["P_LEJOS", "llegadas"] == 2
    assert llegadas.loc["P_TARDE", "llegadas"] == 1
    assert "P_DIA" not in llegadas.index
    assert "P_ABSOLUTA" not in llegadas.index


def test_la_parada_que_solo_tiene_noche_pasada_la_medianoche(tablas):
    """`P_TARDE` llega a las 00:10 de un bus que salió a las 23:30.

    Es la mitad del cálculo que un filtro sobre la hora de servicio pierde: en el feed
    real son 1 490 paradas.
    """
    llegadas = llegadas_nocturnas(tablas).set_index("stop_id")
    assert llegadas.loc["P_TARDE", "tras_medianoche"] == 1
    assert llegadas.loc["P_TARDE", "llegadas"] == llegadas.loc["P_TARDE", "tras_medianoche"]
    assert llegadas.loc["P_NOCHE", "tras_medianoche"] == 0


def test_el_atajo_cuenta_desplazamientos_como_si_fueran_horas(tablas):
    """La trampa central, medida: el 100 % de lo que toma el atajo son desplazamientos."""
    tabla = comparar_con_el_atajo(tablas).set_index("indicador")["valor"]
    assert tabla["proporcion_relativas"] == 100.0
    assert tabla["paradas_segun_el_atajo"] > tabla["paradas_correctas"]
    assert tabla["paradas_que_el_atajo_inventa"] >= 1
    assert tabla["sobreestimacion"] > 0


def test_el_atajo_toma_la_parada_de_la_manana_que_no_es_nocturna(tablas):
    """`P_DIA` tiene desplazamiento `0:00:00` y sale a las 06:00. El atajo la cuenta."""
    paradas_correctas = set(llegadas_nocturnas(tablas)["stop_id"])
    assert "P_DIA" not in paradas_correctas
    tabla = comparar_con_el_atajo(tablas).set_index("indicador")["valor"]
    # Solo `P_DIA`: su desplazamiento `0:00:00` cae en la ventana leído como reloj.
    # `P_ABSOLUTA` trae `07:15:00`, que es una hora de verdad y queda fuera, de modo
    # que el atajo acierta con ella por la razón equivocada.
    assert tabla["paradas_que_el_atajo_inventa"] == 1


def test_la_intensidad_distingue_una_llegada_de_veinte(tablas):
    servicio = servicio_por_parada(tablas)
    tabla = intensidad_del_servicio(servicio).set_index("estadistico")["llegadas"]
    assert tabla["paradas con servicio nocturno"] == 3
    assert tabla["una sola llegada en 5 h"] == 1
    assert tabla["solo por llegadas tras las 24:00"] == 1


# ------------------------------------------------- la clasificación, las cuatro clases
def paradas_con_servicio(tablas) -> pd.DataFrame:
    stops = pd.read_csv(
        pd.io.common.StringIO(ARCHIVOS["stops.txt"]), dtype=str
    )
    stops = stops[stops["location_type"].fillna("0") == "0"].copy()
    stops["lat"] = pd.to_numeric(stops["stop_lat"])
    stops["lon"] = pd.to_numeric(stops["stop_lon"])
    servicio = servicio_por_parada(tablas)
    return stops.merge(servicio, on="stop_id", how="inner").reset_index(drop=True)


def test_las_cuatro_clases_salen_donde_corresponde(tablas, locales):
    clasificadas = clasificar(paradas_con_servicio(tablas), locales).set_index("stop_id")
    assert clasificadas.loc["P_TARDE", "clase"] == CLASE_ABIERTA
    assert clasificadas.loc["P_NOCHE", "clase"] == CLASE_INDETERMINADA
    assert clasificadas.loc["P_LEJOS", "clase"] == CLASE_SIN_LOCAL


def test_un_local_cerrado_con_horario_conocido_permite_afirmar(tablas):
    """Quitado el local sin horario, `P_NOCHE` pasa de indeterminada a verificada."""
    locales = locales_de_prueba()
    solo_conocidos = locales[locales["horario_conocido"]].reset_index(drop=True)
    clasificadas = clasificar(paradas_con_servicio(tablas), solo_conocidos).set_index("stop_id")
    assert clasificadas.loc["P_NOCHE", "clase"] == CLASE_CERRADA


def test_un_solo_local_sin_horario_vuelve_indeterminada_a_la_parada(tablas):
    """El silencio de un local pesa más que el horario conocido del vecino.

    Es la decisión conservadora correcta: con un local cercano del que no se sabe
    nada, no se puede afirmar que no hay cobertura.
    """
    clasificadas = clasificar(paradas_con_servicio(tablas), locales_de_prueba()).set_index("stop_id")
    fila = clasificadas.loc["P_NOCHE"]
    assert fila["locales_a_300m"] == 2
    assert fila["locales_con_horario"] == 1
    assert fila["clase"] == CLASE_INDETERMINADA


def test_el_radio_es_el_heredado_de_p08():
    assert RADIO_M == 300.0
    assert (NOCHE_INICIO, NOCHE_FIN) == (0, 5 * 3600)


def test_la_respuesta_reparte_el_total_entre_las_cuatro_clases(tablas, locales):
    clasificadas = clasificar(paradas_con_servicio(tablas), locales)
    tabla = respuesta(clasificadas)
    sin_total = tabla[tabla["situacion"] != "TOTAL con servicio nocturno"]
    assert sin_total["paradas"].sum() == len(clasificadas)
    assert tabla["paradas"].iloc[-1] == len(clasificadas)
    indeterminada = tabla.loc[tabla["situacion"] == CLASE_INDETERMINADA].iloc[0]
    assert indeterminada["permite_afirmar"] == "no"


# ---------------------------------------------------------- el intervalo y lo que falta
def test_el_intervalo_tiene_piso_techo_y_ancho(tablas, locales):
    clasificadas = clasificar(paradas_con_servicio(tablas), locales)
    tabla = intervalo_de_la_respuesta(clasificadas).set_index("indicador")["valor"]
    # Una de tres abierta verificada, una indeterminada: piso 33,33 %, techo 66,67 %.
    assert tabla["cobertura_verificada"] == 1
    assert tabla["cobertura_minima_pct"] == pytest.approx(33.33, abs=0.01)
    assert tabla["cobertura_maxima_pct"] == pytest.approx(66.67, abs=0.01)
    assert tabla["ancho_del_intervalo_pp"] == pytest.approx(33.33, abs=0.01)


def test_el_ancho_del_intervalo_es_cero_cuando_no_falta_nada(tablas):
    """Sin locales sin horario no hay indeterminación: el piso y el techo coinciden."""
    locales = locales_de_prueba()
    solo_conocidos = locales[locales["horario_conocido"]].reset_index(drop=True)
    clasificadas = clasificar(paradas_con_servicio(tablas), solo_conocidos)
    tabla = intervalo_de_la_respuesta(clasificadas).set_index("indicador")["valor"]
    assert tabla["ancho_del_intervalo_pp"] == 0.0


def test_lo_que_falta_nombra_el_tipo_de_local_y_cuantos(tablas, locales):
    clasificadas = clasificar(paradas_con_servicio(tablas), locales)
    tabla = lo_que_falta_para_contestar(clasificadas, locales)
    assert list(tabla["tipo_local"]) == ["Punto bip!"]
    assert tabla["locales_por_completar"].iloc[0] == 1
    assert tabla["paradas_que_desbloquean"].iloc[0] == 1
    assert tabla["del_total_sin_horario_pct"].iloc[0] == 100.0


def test_la_cobertura_del_campo_separa_los_tipos(locales):
    tabla = cobertura_del_campo_horario(locales).set_index("tipo_local")
    assert tabla.loc["Punto bip!", "cobertura_pct"] == 0.0
    assert tabla.loc["Retail", "cobertura_pct"] == 100.0
    assert tabla.loc["TOTAL", "locales"] == 3
    assert tabla.loc["TOTAL", "abren_de_noche"] == 1


def test_las_peores_paradas_son_las_que_no_dependen_de_ningun_horario(tablas, locales):
    clasificadas = clasificar(paradas_con_servicio(tablas), locales)
    peores = peores_paradas(clasificadas)
    assert list(peores["stop_id"]) == ["P_LEJOS"]
    assert peores["llegadas_noche"].is_monotonic_decreasing


def test_el_resumen_declara_unidad_y_definicion(tablas, locales):
    clasificadas = clasificar(paradas_con_servicio(tablas), locales)
    tabla = resumen(clasificadas, locales, paradas_totales=5)
    assert list(tabla.columns) == ["indicador", "valor", "unidad", "definicion"]
    assert (tabla["definicion"].str.len() > 10).all()
    fila = tabla.set_index("indicador")["valor"]
    assert fila["con_servicio_nocturno"] == 3
    assert fila["paradas_de_embarque"] == 5
    assert fila["llegadas_nocturnas"] == 5     # 2 + 2 + 1
    assert fila["locales_que_abren_de_noche"] == 1


def test_el_feed_sin_frecuencias_no_revienta(tmp_path):
    """Un feed sin `frequencies.txt` útil no tiene servicio nocturno, y eso no es un error."""
    destino = tmp_path / "vacio.zip"
    with zipfile.ZipFile(destino, "w") as zf:
        zf.writestr("frequencies.txt", "trip_id,start_time,end_time,headway_secs\n")
        zf.writestr("trips.txt", "trip_id,service_id\nT1,L\n")
        zf.writestr("stop_times.txt", "trip_id,stop_id,arrival_time\nT1,P1,07:00:00\n")
    tablas = cargar_servicio(destino)
    assert llegadas_nocturnas(tablas).empty
    assert servicio_por_parada(tablas).empty
