"""Pruebas del caso GTFS (`cases.gtfs_red_movilidad.solution`).

Por qué estas pruebas no usan el feed real
    El feed pesa 12,8 MB, cambia cada pocas semanas y su licencia no está verificada,
    de modo que no se versiona ni se descarga en integración continua. Las pruebas
    construyen un feed **mínimo y sintético que reproduce exactamente los formatos
    problemáticos** encontrados en el feed real: relleno de ceros irregular, horarios
    relativos que empiezan en `0:00:00`, horarios absolutos, una ventana de frecuencia
    que termina a las `24:00:00`, y la jerarquía de `location_type`.

    Así se prueba la lógica —que es lo que puede romperse— con cifras calculables a
    mano, en lugar de depender de una descarga.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd
import pytest

from cases.gtfs_red_movilidad.solution import (
    LOCATION_TYPES,
    ROUTE_TYPES,
    analizar,
    cargar,
    comparar_ingenuo_vs_correcto,
    diagnosticar_horas,
    expandir_frecuencias,
    expediciones_por_hora,
    integridad,
    paradas_sin_uso,
    salidas_programadas,
)

#: Feed mínimo. Dos expediciones de frecuencia y una de horario absoluto.
#:
#:  - `F1`: ventana 06:00:00–07:00:00 cada 600 s → 6 salidas (fin exclusivo).
#:  - `F2`: ventana 23:00:00–24:00:00 cada 1800 s → 2 salidas; el fin a las 24:00:00
#:    reproduce el día de servicio extendido del feed real.
#:  - `A1`: horario absoluto, sale a las 08:30:00.
#:
#: El relleno de ceros es irregular a propósito: `0:00:00` en la primera parada de cada
#: expedición de frecuencia y `00:xx:xx` en las siguientes, igual que en el feed real.
ARCHIVOS = {
    "agency.txt": "agency_id,agency_name\nRM,Red de prueba\n",
    "feed_info.txt": (
        "feed_publisher_name,feed_publisher_url,feed_lang,feed_start_date,feed_end_date,feed_version\n"
        "Prueba,http://ejemplo.invalid,es,20261114,20261231,V1\n"
    ),
    "calendar.txt": (
        "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n"
        "L,1,1,1,1,1,0,0,20261114,20261231\n"
        "S,0,0,0,0,0,1,0,20261114,20261231\n"
    ),
    "routes.txt": (
        "route_id,agency_id,route_short_name,route_type\n"
        "R1,RM,101,3\n"
        "R2,RM,L1,1\n"
    ),
    "trips.txt": (
        "route_id,service_id,trip_id\n"
        "R1,L,F1\n"
        "R2,L,F2\n"
        "R1,L,A1\n"
        "R1,S,S1\n"
    ),
    "stops.txt": (
        "stop_id,stop_name,location_type,stop_lat,stop_lon\n"
        "P1,Parada uno,0,-33.45,-70.66\n"
        "P2,Parada dos,0,-33.46,-70.67\n"
        "P3,Parada sin uso,0,-33.47,-70.68\n"
        "P4,Parada cuatro,0,-33.48,-70.69\n"
        "E1,Estacion,1,-33.44,-70.65\n"
        "N1,Nodo de pasillo,3,,\n"
        "N2,Otro nodo,3,,\n"
        "B1,Area de abordaje,4,,\n"
    ),
    "frequencies.txt": (
        "trip_id,start_time,end_time,headway_secs,exact_times\n"
        "F1,06:00:00,07:00:00,600,0\n"
        "F2,23:00:00,24:00:00,1800,0\n"
    ),
    # S1 pertenece al servicio sábado: debe quedar fuera del cálculo del día laboral.
    "stop_times.txt": (
        "trip_id,arrival_time,departure_time,stop_id,stop_sequence,pickup_type,drop_off_type,timepoint\n"
        "F1,0:00:00,0:00:00,P1,1,0,0,1\n"
        "F1,00:04:30,00:04:30,P2,2,0,0,0\n"
        "F2,0:00:00,0:00:00,P4,1,0,0,1\n"
        "F2,00:03:00,00:03:00,P2,2,0,0,0\n"
        "A1,08:30:00,08:30:00,P1,1,0,0,1\n"
        "A1,08:42:15,08:42:15,P2,2,0,0,0\n"
        "S1,10:00:00,10:00:00,P1,1,0,0,1\n"
    ),
}

#: Salidas esperadas del día laboral, calculadas a mano:
#:   F1: (07:00 − 06:00) / 600 s = 3600/600 = 6
#:   F2: (24:00 − 23:00) / 1800 s = 3600/1800 = 2
#:   A1: 1 expedición de horario absoluto
#: Total = 9. S1 es del servicio sábado y no entra.
SALIDAS_LABORAL = 9


@pytest.fixture(scope="module")
def feed(tmp_path_factory) -> Path:
    destino = tmp_path_factory.mktemp("gtfs") / "feed.zip"
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for nombre, contenido in ARCHIVOS.items():
            z.writestr(nombre, contenido)
    return destino


@pytest.fixture(scope="module")
def tablas(feed: Path) -> dict[str, pd.DataFrame]:
    return cargar(feed)


# --------------------------------------------------------------------------- lectura
def test_carga_las_tablas_como_texto(tablas):
    assert set(tablas) == {"agency", "feed_info", "calendar", "routes", "trips",
                           "stops", "frequencies", "stop_times"}
    # dtype=str en todo: queremos ver los valores tal como vienen.
    assert tablas["stop_times"]["arrival_time"].iloc[0] == "0:00:00"
    # El tipo concreto depende de la versión de pandas; lo que importa es que NO se
    # convirtió a número: la secuencia de parada sigue siendo el texto del archivo.
    assert not pd.api.types.is_numeric_dtype(tablas["stop_times"]["stop_sequence"])
    assert tablas["stop_times"]["stop_sequence"].iloc[0] == "1"


def test_lee_solo_las_columnas_necesarias_de_la_tabla_grande(tablas):
    assert set(tablas["stop_times"].columns) == {
        "trip_id", "arrival_time", "stop_sequence", "stop_id"
    }


def test_el_feed_ausente_explica_como_conseguirlo():
    from cases.gtfs_red_movilidad import solution

    original = solution.FEED
    try:
        solution.FEED = Path("no-existe-en-ningun-lado.zip")
        with pytest.raises(FileNotFoundError, match="fetch_data.py"):
            solution.cargar()
    finally:
        solution.FEED = original


# ---------------------------------------------------------------- trampas 1 y 2
def test_diagnostica_los_horarios_que_no_son_horas(tablas):
    valores = diagnosticar_horas(tablas).set_index("indicador").valor
    assert valores["filas_stop_times"] == 7
    assert valores["expediciones_declaradas"] == 4
    assert valores["expediciones_de_frecuencia"] == 2
    # F1 y F2 aportan 2 filas cada una: 4 filas con horario relativo sobre 7.
    assert valores["filas_con_horario_relativo"] == 4
    assert valores["pct_horario_relativo"] == pytest.approx(100 * 4 / 7)
    assert valores["primeras_paradas_en_cero"] == 2


def test_diagnostica_el_relleno_de_ceros_irregular(tablas):
    valores = diagnosticar_horas(tablas).set_index("indicador").valor
    # Dos valores con una sola cifra de hora (`0:00:00`), cinco con dos.
    assert valores["hora_sin_relleno"] == 2
    assert valores["hora_con_relleno"] == 5
    assert valores["no_interpretables"] == 0


def test_el_orden_como_texto_esta_invertido_y_por_eso_se_convierte(tablas):
    """Reproduce el defecto real: comparar las horas como texto da el orden al revés."""
    primera, segunda = "0:00:00", "00:04:30"
    assert primera > segunda, "como texto, la parada 1 queda después de la 2"
    from lab.dates import parse_hms_seconds

    convertido = parse_hms_seconds(pd.Series([primera, segunda]))
    assert convertido.iloc[0] < convertido.iloc[1], "convertido a segundos, el orden es correcto"


# ------------------------------------------------------------------------- trampa 3
def test_expande_las_ventanas_de_frecuencia_con_fin_exclusivo(tablas):
    expandido = expandir_frecuencias(tablas)
    por_trip = expandido.groupby("trip_id").size().to_dict()
    assert por_trip == {"F1": 6, "F2": 2}, "fin exclusivo: 3600/600 = 6 y 3600/1800 = 2"
    assert len(expandido) == 8


def test_las_salidas_expandidas_estan_separadas_por_el_intervalo(tablas):
    f1 = expandir_frecuencias(tablas).query("trip_id == 'F1'").sort_values("salida_s")
    assert f1.salida.tolist() == ["06:00:00", "06:10:00", "06:20:00",
                                  "06:30:00", "06:40:00", "06:50:00"]
    assert f1.salida_s.diff().dropna().eq(600).all()
    assert f1.hora_reloj.tolist() == [6.0] * 6


def test_una_ventana_que_termina_a_las_24_horas_se_maneja(tablas):
    f2 = expandir_frecuencias(tablas).query("trip_id == 'F2'").sort_values("salida_s")
    assert f2.salida.tolist() == ["23:00:00", "23:30:00"]
    # La salida de las 24:00:00 pertenece a la ventana siguiente: no se genera.
    assert "24:00:00" not in f2.salida.tolist()


def test_las_ventanas_invalidas_se_excluyen_en_lugar_de_romper(tablas):
    malas = tablas.copy()
    malas["frequencies"] = pd.DataFrame({
        "trip_id": ["F1", "F1", "F1", "F1"],
        "start_time": ["06:00:00", "06:00:00", "07:00:00", "no es hora"],
        "end_time": ["07:00:00", "07:00:00", "06:00:00", "08:00:00"],
        "headway_secs": ["600", "0", "600", "600"],
        "exact_times": ["0", "0", "0", "0"],
    })
    expandido = expandir_frecuencias(malas)
    # Solo la primera ventana es válida: intervalo cero, fin anterior al inicio y hora
    # no interpretable quedan fuera.
    assert len(expandido) == 6


def test_las_salidas_de_horario_absoluto_vienen_de_la_primera_parada(tablas):
    programadas = salidas_programadas(tablas)
    assert set(programadas.trip_id) == {"A1", "S1"}
    a1 = programadas.query("trip_id == 'A1'").iloc[0]
    assert a1.salida == "08:30:00"
    assert a1.hora_reloj == 8.0


def test_el_total_del_dia_laboral_es_el_calculado_a_mano(tablas):
    por_hora = expediciones_por_hora(tablas, servicio="L")
    assert por_hora.salidas.sum() == SALIDAS_LABORAL
    # S1 es del servicio sábado y no debe aparecer.
    sabado = expediciones_por_hora(tablas, servicio="S")
    assert sabado.salidas.sum() == 1


def test_el_resultado_declara_de_que_fuente_viene_cada_salida(tablas):
    por_hora = expediciones_por_hora(tablas, servicio="L")
    assert set(por_hora.fuente) == {"frequencies", "stop_times"}
    por_fuente = por_hora.groupby("fuente").salidas.sum().to_dict()
    assert por_fuente == {"frequencies": 8, "stop_times": 1}


def test_el_resultado_separa_los_modos(tablas):
    por_hora = expediciones_por_hora(tablas, servicio="L")
    modos = set(por_hora.modo)
    assert modos <= set(ROUTE_TYPES.values()) | {"otro"}
    assert {"bus", "metro"} <= modos


def test_cuantifica_cuanto_se_equivoca_cada_atajo(tablas):
    tabla = comparar_ingenuo_vs_correcto(tablas, servicio="L")
    correcto = tabla.loc[tabla.error_vs_correcto.eq(0)].iloc[0]
    assert correcto.resultado == SALIDAS_LABORAL

    # El atajo de contar trips.txt: 3 expediciones del servicio L frente a 9 salidas.
    atajo = tabla.iloc[0]
    assert atajo.resultado == 3
    assert atajo.error_vs_correcto == 3 - SALIDAS_LABORAL

    # El fin inclusivo suma una salida por ventana: 2 ventanas, 2 salidas de más.
    inclusivo = tabla.iloc[1]
    assert inclusivo.error_vs_correcto == 2

    # Y el error relativo se calcula en todas las filas: era NaN por un defecto de
    # safe_ratio que esta aserción protege.
    assert tabla.error_relativo_pct.notna().all()


def test_la_comprobacion_aritmetica_independiente_coincide(tablas):
    """Dos caminos sin código común tienen que dar el mismo total."""
    tabla = comparar_ingenuo_vs_correcto(tablas, servicio="L")
    assert tabla.attrs["coincide"] is True
    assert tabla.attrs["comprobacion_aritmetica"] == SALIDAS_LABORAL


# ------------------------------------------------------------------------- trampa 4
def test_las_paradas_sin_uso_se_explican_por_su_tipo(tablas):
    resumen = paradas_sin_uso(tablas).set_index("location_type")
    # Tipo 0: cuatro paradas, tres en horarios, una realmente huérfana.
    assert resumen.loc["0", "filas"] == 4
    assert resumen.loc["0", "en_horarios"] == 3
    assert resumen.loc["0", "fuera_de_horarios"] == 1
    assert bool(resumen.loc["0", "es_defecto_real"]) is True
    # Los demás tipos no deben aparecer en horarios, y eso no es un defecto.
    for tipo in ("1", "3", "4"):
        assert resumen.loc[tipo, "en_horarios"] == 0
        assert bool(resumen.loc[tipo, "es_defecto_real"]) is False


def test_el_conteo_ingenuo_de_paradas_huerfanas_exagera(tablas):
    resumen = paradas_sin_uso(tablas)
    ingenuo = int(resumen.fuera_de_horarios.sum())
    real = int(resumen.loc[resumen.es_defecto_real, "fuera_de_horarios"].sum())
    assert ingenuo == 5, "cinco filas sin horarios"
    assert real == 1, "pero solo una es una parada de verdad"


def test_los_tipos_de_lugar_estan_documentados():
    assert set(LOCATION_TYPES) == {"0", "1", "2", "3", "4"}
    assert all(texto.strip() for texto in LOCATION_TYPES.values())


# ---------------------------------------------------------------------- integridad
def test_comprueba_los_seis_cruces_del_modelo(tablas):
    tabla = integridad(tablas)
    assert len(tabla) == 6
    assert (tabla.huerfanos == 0).all()
    assert set(tabla.veredicto) == {"íntegro"}


def test_detecta_una_clave_huerfana_cuando_existe(tablas):
    roto = tablas.copy()
    roto["stop_times"] = tablas["stop_times"].copy()
    roto["stop_times"].loc[0, "stop_id"] = "NO_EXISTE"
    tabla = integridad(roto)
    fila = tabla.loc[tabla.cruce.str.startswith("stop_times.stop_id")].iloc[0]
    assert fila.huerfanos == 1
    assert fila.veredicto == "claves desconocidas"


# ------------------------------------------------------------------- caso completo
def test_analizar_devuelve_todas_las_tablas(feed: Path):
    resultados = analizar(feed)
    assert set(resultados) == {"inventario", "diagnostico_horas", "integridad",
                               "paradas_por_tipo", "conteo_comparado", "salidas_por_hora"}
    assert not any(tabla.empty for tabla in resultados.values())
    assert resultados["salidas_por_hora"].salidas.sum() == SALIDAS_LABORAL


def test_exportar_escribe_un_csv_por_tabla(feed: Path, tmp_path: Path):
    from cases.gtfs_red_movilidad.solution import exportar

    destino = exportar(analizar(feed), destino=tmp_path / "salida")
    escritos = {p.stem for p in destino.glob("*.csv")}
    assert escritos == {"inventario", "diagnostico_horas", "integridad",
                        "paradas_por_tipo", "conteo_comparado", "salidas_por_hora"}
