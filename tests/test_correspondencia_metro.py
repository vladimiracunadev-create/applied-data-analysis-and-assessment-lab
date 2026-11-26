"""Pruebas del caso P10 (`cases.correspondencia_metro.solution`).

Qué construyen las pruebas
    Un inventario sintético de tres estaciones y cuatro filas de bip!, con la misma
    estructura que los archivos reales y con todas las distancias calculables a mano:

    - `CEN` **Centro**, con dos filas en bip! —una por línea, con el sufijo pegado al
      nombre— que están **en el mismo sitio**. Es el caso normal.
    - `PAR` **Partida**, con dos filas separadas **10 km**: reproduce Plaza de Armas.
      Sirve para el detector 2 y para comprobar que la mediana de las dos esconde la
      mitad del error.
    - `SOL` **Solitaria**, con una sola fila que está a **4 km** de donde el GTFS la
      pone: reproduce Santa Lucía. No tiene hermana que la contradiga, de modo que solo
      el detector 4 la ve.

    Y una cuarta fila, `Renombrada`, cuyo nombre no coincide con el del GTFS pero está
    a metros: reproduce `Presidente Pedro Aguirre Cerda` contra `PEDRO AGUIRRE CERDA`,
    el caso que un cruce solo por nombre pierde.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from cases.correspondencia_metro.solution import (
    RADIO_M,
    SUFIJO_DE_LINEA,
    UMBRAL_CONTRA_GTFS_M,
    UMBRAL_ENTRE_FILAS_M,
    cargar,
    conciliar,
    correspondencia,
    criterios_discrepantes,
    detectar_contra_gtfs,
    detectar_entre_filas,
    estaciones_gtfs,
    informe_de_conciliacion,
    informe_de_correspondencia,
    informe_de_grano,
    mejores_correspondencias,
    paradas_de_bus,
    sensibilidad_a_la_fuente,
    tabla_de_detectores,
)
from lab.geo import grados_por_km
from lab.textual import normalize_key

LAT0, LON0 = -33.45, -70.66
GRADO_LAT_KM, GRADO_LON_KM = grados_por_km(LAT0)


def al_norte(km: float) -> float:
    return LAT0 + km * GRADO_LAT_KM


def al_este(km: float) -> float:
    return LON0 + km * GRADO_LON_KM


#: Un feed mínimo con la jerarquía de `location_type` y dos tipos de ruta.
ARCHIVOS: dict[str, str] = {
    "stops.txt": (
        "stop_id,stop_name,stop_lat,stop_lon,location_type,parent_station\n"
        # Las tres estaciones de Metro. CEN-TRO reproduce un id compuesto.
        f"CEN-TRO,Centro,{LAT0},{LON0},1,\n"
        f"PAR,Partida,{al_norte(0)},{al_este(2)},1,\n"
        f"SOL,Solitaria,{al_norte(0)},{al_este(4)},1,\n"
        f"REN,Presidente Renombrada,{al_norte(0)},{al_este(6)},1,\n"
        # Andenes: no son estaciones y no deben contarse como tales.
        f"CEN_V1,Centro Dirección Norte,{LAT0},{LON0},0,CEN-TRO\n"
        f"CEN_V2,Centro Dirección Sur,{LAT0},{LON0},0,CEN-TRO\n"
        # Paradas de bus. B1 y B2 a 100 m de Centro; B3 a 1 km (fuera del radio).
        f"B1,Parada uno,{al_norte(0.1)},{LON0},0,\n"
        f"B2,Parada dos,{al_norte(-0.1)},{LON0},0,\n"
        f"B3,Parada lejana,{al_norte(1.0)},{LON0},0,\n"
        # Una parada a 100 m de Partida y otra a 100 m de Solitaria.
        f"B4,Parada en Partida,{al_norte(0.1)},{al_este(2)},0,\n"
        f"B5,Parada en Solitaria,{al_norte(0.1)},{al_este(4)},0,\n"
        # Un nodo de pasillo sin coordenadas, que no es parada.
        "N1,Nodo,,,3,\n"
    ),
    "routes.txt": (
        "route_id,route_short_name,route_type\n"
        "L1,L1,1\n"          # metro
        "L2,L2,1\n"
        "R101,101,3\n"       # bus
        "R102,102,3\n"
        "R103,103,3\n"
    ),
    "trips.txt": (
        "route_id,trip_id\n"
        "L1,T_M1\nL2,T_M2\nR101,T_B1\nR102,T_B2\nR103,T_B3\n"
    ),
    "stop_times.txt": (
        "trip_id,stop_id\n"
        # El metro pasa por los andenes.
        "T_M1,CEN_V1\nT_M2,CEN_V2\n"
        # 101 pasa por B1 y B4; 102 por B2; 103 por B3 y B5.
        "T_B1,B1\nT_B1,B4\nT_B2,B2\nT_B3,B3\nT_B3,B5\n"
    ),
}


@pytest.fixture(scope="module")
def feed(tmp_path_factory) -> Path:
    destino = tmp_path_factory.mktemp("feed-metro") / "feed.zip"
    with zipfile.ZipFile(destino, "w") as zf:
        for nombre, contenido in ARCHIVOS.items():
            zf.writestr(nombre, contenido)
    return destino


@pytest.fixture(scope="module")
def tablas(feed) -> dict[str, pd.DataFrame]:
    return cargar(feed)


@pytest.fixture
def gtfs(tablas) -> pd.DataFrame:
    return estaciones_gtfs(tablas)


def bip_de_prueba() -> pd.DataFrame:
    """Cuatro filas con la estructura del Excel real.

    `CENTRO L1` y `CENTRO L2` están en el mismo punto. `PARTIDA L1` y `PARTIDA L2`
    están separadas 10 km. `SOLITARIA` tiene una sola fila, 4 km al oeste de donde el
    GTFS pone la estación. `RENOMBRADA` no coincide de nombre pero sí de lugar.
    """
    filas = [
        {"codigo": "L1", "nombre": "CENTRO L1", "lat": LAT0, "lon": LON0},
        {"codigo": "L2", "nombre": "CENTRO L2", "lat": LAT0, "lon": LON0},
        {"codigo": "L1", "nombre": "PARTIDA L1", "lat": al_norte(0), "lon": al_este(2)},
        {"codigo": "L2", "nombre": "PARTIDA L2", "lat": al_norte(10), "lon": al_este(2)},
        # 4 km al norte de donde el GTFS pone la estación, y donde no hay ninguna
        # parada de bus: así el cambio de fuente se ve en el resultado.
        {"codigo": "L1", "nombre": "SOLITARIA", "lat": al_norte(4), "lon": al_este(4)},
        {"codigo": "L1", "nombre": "RENOMBRADA", "lat": al_norte(0), "lon": al_este(6)},
    ]
    tabla = pd.DataFrame(filas)
    tabla["nombre_estacion"] = tabla["nombre"].astype("string").str.replace(
        SUFIJO_DE_LINEA, "", regex=True
    )
    tabla["tiene_sufijo"] = tabla["nombre"].astype("string").str.contains(
        SUFIJO_DE_LINEA, regex=True, na=False
    )
    tabla["clave"] = tabla["nombre_estacion"].map(normalize_key)
    tabla["coordenada_sospechosa"] = False
    tabla["desvio_m"] = 61.0
    return tabla


@pytest.fixture
def bip_metro() -> pd.DataFrame:
    return bip_de_prueba()


# ------------------------------------------------------------- la jerarquía del feed
def test_solo_las_estaciones_son_estaciones(gtfs):
    """Los andenes tienen `location_type = 0` y no deben contarse como estaciones."""
    assert list(gtfs["stop_id"]) == ["CEN-TRO", "PAR", "REN", "SOL"]
    assert len(gtfs) == 4
    assert gtfs["lat"].notna().all()


def test_el_identificador_compuesto_se_detecta(gtfs):
    """El guion en el id delata una estación de combinación."""
    assert int(gtfs["id_compuesto"].sum()) == 1
    assert gtfs.set_index("stop_id").loc["CEN-TRO", "id_compuesto"]


def test_las_paradas_de_bus_exigen_las_dos_condiciones(tablas):
    """Lugar de embarque **y** servido por una ruta de bus. Con una sola, entran andenes."""
    buses = paradas_de_bus(tablas)
    assert set(buses["stop_id"]) == {"B1", "B2", "B3", "B4", "B5"}
    # Los andenes de Metro son location_type 0 pero no los sirve ningún bus.
    assert "CEN_V1" not in set(buses["stop_id"])
    # El nodo de pasillo no es lugar de embarque.
    assert "N1" not in set(buses["stop_id"])


def test_cada_parada_trae_el_conjunto_de_sus_servicios(tablas):
    buses = paradas_de_bus(tablas).set_index("stop_id")
    assert buses.loc["B1", "servicios"] == frozenset({"101"})
    assert buses.loc["B4", "servicios"] == frozenset({"101"})
    assert buses.loc["B5", "servicios"] == frozenset({"103"})


# --------------------------------------------------------------------------- el grano
def test_el_grano_cuadra_despues_de_nombrarlo(gtfs, bip_metro):
    """4 estaciones − 1 combinación + 2 filas con sufijo = … y hay que comprobarlo.

    En el fixture hay dos estaciones con dos filas cada una, de modo que la identidad
    del archivo real no se reproduce tal cual; lo que se comprueba es que la fórmula
    se calcule sobre los conteos correctos.
    """
    tabla = informe_de_grano(gtfs, bip_metro).set_index("indicador")["valor"]
    assert tabla["estaciones_gtfs"] == 4
    assert tabla["filas_bip"] == 6
    assert tabla["estaciones_de_combinacion_gtfs"] == 1
    assert tabla["filas_con_sufijo_de_linea_bip"] == 4
    assert tabla["estaciones_bip_tras_quitar_el_sufijo"] == 4


def test_quitar_el_sufijo_de_linea_reduce_el_grano(bip_metro):
    assert bip_metro["clave"].nunique() == 4
    centro = bip_metro[bip_metro["clave"] == "CENTRO"]
    assert len(centro) == 2
    assert set(centro["codigo"]) == {"L1", "L2"}


@pytest.mark.parametrize("nombre,esperado", [
    ("SAN PABLO L1", "SAN PABLO"),
    ("LA CISTERNA L4A", "LA CISTERNA"),
    ("VICUÑA MACKENNA L4", "VICUÑA MACKENNA"),
    ("SANTA LUCIA", "SANTA LUCIA"),
    ("ESTACION CENTRAL", "ESTACION CENTRAL"),
])
def test_el_sufijo_se_quita_solo_donde_corresponde(nombre, esperado):
    """Una estación que no lleva sufijo no debe quedar mutilada."""
    assert SUFIJO_DE_LINEA.sub("", nombre) == esperado


# --------------------------------------------------------------- los dos criterios
def test_los_dos_criterios_se_calculan_por_separado(gtfs, bip_metro):
    conciliado = conciliar(gtfs, bip_metro).set_index("stop_id")
    # Centro: cruza por nombre y es además el más cercano.
    assert conciliado.loc["CEN-TRO", "cruza_por_nombre"]
    assert conciliado.loc["CEN-TRO", "coinciden_los_criterios"]
    # Renombrada: NO cruza por nombre, pero su vecino más cercano está a metros.
    assert not conciliado.loc["REN", "cruza_por_nombre"]
    assert conciliado.loc["REN", "distancia_al_mas_cercano_m"] < 10


def test_un_cruce_solo_por_nombre_pierde_una_estacion(gtfs, bip_metro):
    tabla = informe_de_conciliacion(conciliar(gtfs, bip_metro)).set_index("indicador")["valor"]
    assert tabla["estaciones_a_conciliar"] == 4
    assert tabla["cruzan_por_nombre"] == 3
    assert tabla["sin_par_por_nombre"] == 1


def test_los_criterios_discrepan_donde_la_coordenada_esta_mal(gtfs, bip_metro):
    conciliado = conciliar(gtfs, bip_metro)
    discrepantes = criterios_discrepantes(conciliado)
    assert "SOL" in set(discrepantes["stop_id"])
    assert "PAR" in set(discrepantes["stop_id"])
    # Los desvíos conocidos van de mayor a menor, y la estación sin par por nombre
    # —que no tiene desvío que medir— queda al final en lugar de encabezar la tabla.
    conocidos = discrepantes["desvio_m"].dropna()
    assert conocidos.is_monotonic_decreasing
    assert discrepantes["desvio_m"].iloc[-1] != discrepantes["desvio_m"].iloc[-1]  # NaN
    assert discrepantes["stop_id"].iloc[-1] == "REN"


# ----------------------------------------------------- lo que el agregado esconde
def test_la_mediana_de_dos_filas_opuestas_esconde_la_mitad_del_error(gtfs, bip_metro):
    """Dos filas separadas 10 km: la mediana cae a 5 km de cada una.

    Es el hallazgo del caso sobre Plaza de Armas: reducir el grano promediando
    coordenadas suaviza un error en lugar de mostrarlo, y lo reduce exactamente a la
    mitad.
    """
    conciliado = conciliar(gtfs, bip_metro).set_index("stop_id")
    fila = conciliado.loc["PAR"]
    assert fila["dispersion_interna_m"] == pytest.approx(5000, rel=0.01)
    assert fila["desvio_m"] == pytest.approx(5000, rel=0.01)
    assert fila["desvio_peor_fila_m"] == pytest.approx(10000, rel=0.01)
    assert fila["filas_discrepantes"]


def test_el_informe_publica_las_dos_cifras(gtfs, bip_metro):
    tabla = informe_de_conciliacion(conciliar(gtfs, bip_metro)).set_index("indicador")["valor"]
    assert tabla["desvio_maximo_peor_fila_m"] > tabla["desvio_maximo_m"]
    assert tabla["estaciones_con_filas_discrepantes"] == 1


def test_una_estacion_coherente_no_tiene_dispersion(gtfs, bip_metro):
    conciliado = conciliar(gtfs, bip_metro).set_index("stop_id")
    assert conciliado.loc["CEN-TRO", "dispersion_interna_m"] == pytest.approx(0.0, abs=1e-6)
    assert not conciliado.loc["CEN-TRO", "filas_discrepantes"]


# ------------------------------------------------------- los detectores y sus ciegos
def test_el_detector_de_filas_hermanas_encuentra_la_separacion(bip_metro):
    tabla = detectar_entre_filas(bip_metro).set_index("estacion")
    assert tabla.loc["PARTIDA", "separacion_maxima_m"] == pytest.approx(10000, rel=0.01)
    assert tabla.loc["PARTIDA", "excede_el_umbral"] == "sí"
    assert tabla.loc["CENTRO", "separacion_maxima_m"] == pytest.approx(0.0, abs=1e-6)
    assert tabla.loc["CENTRO", "excede_el_umbral"] == "no"


def test_el_detector_de_filas_hermanas_es_ciego_a_la_estacion_solitaria(bip_metro):
    """`SOLITARIA` está 4 km mal y este detector no puede verla: no tiene hermana."""
    tabla = detectar_entre_filas(bip_metro)
    assert "SOLITARIA" not in set(tabla["estacion"])
    assert "RENOMBRADA" not in set(tabla["estacion"])


def test_solo_la_fuente_externa_ve_la_estacion_solitaria(gtfs, bip_metro):
    conciliado = conciliar(gtfs, bip_metro)
    contra_gtfs = detectar_contra_gtfs(conciliado)
    assert "SOL" in set(contra_gtfs["stop_id"])
    assert contra_gtfs.set_index("stop_id").loc["SOL", "desvio_m"] == pytest.approx(
        4000, rel=0.01
    )
    # Y la validación interna de P01 no la marcó.
    assert not bip_metro["coordenada_sospechosa"].any()


def test_el_detector_externo_respeta_su_umbral(gtfs, bip_metro):
    conciliado = conciliar(gtfs, bip_metro)
    contra_gtfs = detectar_contra_gtfs(conciliado, umbral_m=UMBRAL_CONTRA_GTFS_M)
    assert (contra_gtfs["desvio_m"] > UMBRAL_CONTRA_GTFS_M).all()
    # Centro está a cero y no debe aparecer.
    assert "CEN-TRO" not in set(contra_gtfs["stop_id"])


def test_la_tabla_de_detectores_declara_el_punto_ciego_de_cada_uno(gtfs, bip_metro):
    """Es el entregable conceptual: tres de los cuatro no necesitan fuente externa."""
    conciliado = conciliar(gtfs, bip_metro)
    tabla = tabla_de_detectores(bip_metro, conciliado)
    assert len(tabla) == 4
    assert (tabla["ciego_a"].str.len() > 10).all()
    assert list(tabla["fuente_externa"]) == ["no", "no", "no", "sí"]
    assert int((tabla["fuente_externa"] == "no").sum()) == 3


def test_el_umbral_entre_filas_es_el_mismo_que_el_de_p01():
    """Coherencia entre casos: el mismo criterio para el mismo tipo de juicio."""
    from cases.bip_lugares_carga.solution import UMBRAL_COORDENADA_M

    assert UMBRAL_ENTRE_FILAS_M == UMBRAL_COORDENADA_M


# ------------------------------------------------------------------ la respuesta de P10
def test_la_correspondencia_cuenta_paradas_y_servicios(tablas, gtfs):
    buses = paradas_de_bus(tablas)
    tabla = correspondencia(gtfs, buses).set_index("stop_id")
    # Centro: B1 (101) y B2 (102) a 100 m; B3 a 1 km queda fuera.
    assert tabla.loc["CEN-TRO", "paradas_de_bus"] == 2
    assert tabla.loc["CEN-TRO", "servicios_distintos"] == 2
    assert tabla.loc["CEN-TRO", "lista_de_servicios"] == "101,102"
    # Partida: solo B4, con el servicio 101.
    assert tabla.loc["PAR", "paradas_de_bus"] == 1
    assert tabla.loc["PAR", "servicios_distintos"] == 1
    # Renombrada no tiene ninguna parada cerca.
    assert tabla.loc["REN", "paradas_de_bus"] == 0
    assert tabla.loc["REN", "servicios_distintos"] == 0


def test_el_radio_excluye_lo_que_esta_justo_afuera(tablas, gtfs):
    """B3 está a 1 km de Centro. Con el radio por defecto queda fuera; con 1,1 km, dentro."""
    buses = paradas_de_bus(tablas)
    estrecho = correspondencia(gtfs, buses).set_index("stop_id")
    amplio = correspondencia(gtfs, buses, radio_m=1100.0).set_index("stop_id")
    assert estrecho.loc["CEN-TRO", "paradas_de_bus"] == 2
    assert amplio.loc["CEN-TRO", "paradas_de_bus"] == 3
    assert amplio.loc["CEN-TRO", "servicios_distintos"] == 3
    assert RADIO_M == 200.0


def test_los_servicios_no_se_cuentan_dos_veces(tablas, gtfs):
    """Dos paradas del mismo servicio cerca de una estación son un servicio, no dos."""
    buses = paradas_de_bus(tablas).copy()
    # B2 pasa a ser del servicio 101, igual que B1.
    buses.loc[buses["stop_id"] == "B2", "servicios"] = [frozenset({"101"})]
    tabla = correspondencia(gtfs, buses).set_index("stop_id")
    assert tabla.loc["CEN-TRO", "paradas_de_bus"] == 2
    assert tabla.loc["CEN-TRO", "servicios_distintos"] == 1


def test_el_informe_de_correspondencia_resume_bien(tablas, gtfs):
    buses = paradas_de_bus(tablas)
    tabla = informe_de_correspondencia(
        correspondencia(gtfs, buses)
    ).set_index("indicador")["valor"]
    assert tabla["estaciones_evaluadas"] == 4
    assert tabla["con_parada_de_bus_cerca"] == 3
    assert tabla["sin_ninguna"] == 1
    assert tabla["con_parada_de_bus_pct"] == 75.0


def test_las_mejores_se_ordenan_por_servicios(tablas, gtfs):
    buses = paradas_de_bus(tablas)
    mejores = mejores_correspondencias(correspondencia(gtfs, buses))
    assert mejores["servicios_distintos"].is_monotonic_decreasing
    assert mejores["stop_id"].iloc[0] == "CEN-TRO"


# ------------------------------------------------------- la sensibilidad a la fuente
def test_cambiar_la_fuente_de_la_coordenada_cambia_la_respuesta(tablas, gtfs, bip_metro):
    """`SOLITARIA` está 4 km mal en bip!: con esa coordenada pierde su parada."""
    conciliado = conciliar(gtfs, bip_metro)
    buses = paradas_de_bus(tablas)
    tabla = sensibilidad_a_la_fuente(conciliado, buses).set_index("indicador")["valor"]
    assert tabla["estaciones_comparables"] == 3
    assert tabla["cambia_el_conteo_de_servicios"] >= 1
    assert tabla["aparecerian_sin_bus"] >= 1
    assert tabla["servicios_totales_con_gtfs"] >= tabla["servicios_totales_con_bip"]


def test_la_correspondencia_acepta_cualquier_par_de_columnas(tablas, gtfs, bip_metro):
    """La función no sabe de dónde viene la coordenada, y ahí está su valor."""
    conciliado = conciliar(gtfs, bip_metro)
    comparables = conciliado.loc[conciliado["cruza_por_nombre"]].reset_index(drop=True)
    buses = paradas_de_bus(tablas)
    con_gtfs = correspondencia(comparables, buses, "lat_gtfs", "lon_gtfs")
    con_bip = correspondencia(comparables, buses, "lat_bip", "lon_bip")
    assert len(con_gtfs) == len(con_bip) == 3
    sol_gtfs = con_gtfs.set_index("stop_id").loc["SOL", "paradas_de_bus"]
    sol_bip = con_bip.set_index("stop_id").loc["SOL", "paradas_de_bus"]
    assert sol_gtfs == 1
    assert sol_bip == 0


def test_una_estacion_sin_coordenada_no_revienta(tablas, gtfs, bip_metro):
    buses = paradas_de_bus(tablas)
    roto = gtfs.copy()
    roto.loc[0, ["lat", "lon"]] = [np.nan, np.nan]
    tabla = correspondencia(roto, buses)
    assert len(tabla) == len(gtfs)
    assert tabla["paradas_de_bus"].iloc[0] == 0
