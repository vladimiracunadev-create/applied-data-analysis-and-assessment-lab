"""Pruebas de geografía (`lab.geo`).

La distancia se contrasta con valores publicados y con las propiedades que cualquier
métrica debe cumplir. La conversión de UTM se valida contra un punto de referencia
conocido y contra la coherencia de ida y vuelta.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from lab.geo import (
    RADIO_TIERRA_KM,
    grados_por_km,
    haversine_km,
    nearest_point,
    utm_to_latlon,
)

#: Coordenadas de referencia, en grados decimales.
SANTIAGO = (-33.4489, -70.6693)
VALPARAISO = (-33.0472, -71.6127)
BUENOS_AIRES = (-34.6037, -58.3816)


def test_haversine_cumple_las_propiedades_de_una_metrica():
    a, b = SANTIAGO, VALPARAISO
    assert haversine_km(*a, *a) == pytest.approx(0.0, abs=1e-9)
    assert haversine_km(*a, *b) == pytest.approx(haversine_km(*b, *a))
    directa = haversine_km(*SANTIAGO, *BUENOS_AIRES)
    via = (haversine_km(*SANTIAGO, *VALPARAISO)
           + haversine_km(*VALPARAISO, *BUENOS_AIRES))
    assert directa <= via + 1e-9


def test_haversine_contra_distancias_conocidas():
    # Santiago–Valparaíso: unos 98 km en línea recta.
    assert haversine_km(*SANTIAGO, *VALPARAISO) == pytest.approx(98, abs=3)
    # Santiago–Buenos Aires: unos 1 140 km.
    assert haversine_km(*SANTIAGO, *BUENOS_AIRES) == pytest.approx(1140, abs=20)
    # Un grado de latitud en el ecuador: la circunferencia dividida en 360.
    esperado = 2 * np.pi * RADIO_TIERRA_KM / 360
    assert haversine_km(0.0, 0.0, 1.0, 0.0) == pytest.approx(esperado, rel=1e-6)


def test_haversine_vectorizado_conserva_el_indice():
    lat = pd.Series([-33.45, -33.46], index=["a", "b"])
    lon = pd.Series([-70.67, -70.67], index=["a", "b"])
    resultado = haversine_km(lat, lon, -33.45, -70.67)
    assert isinstance(resultado, pd.Series)
    assert list(resultado.index) == ["a", "b"]
    assert resultado.iloc[0] == pytest.approx(0.0, abs=1e-9)
    assert resultado.iloc[1] > 1.0


def test_un_grado_de_longitud_no_mide_lo_mismo_que_uno_de_latitud():
    """Es el motivo por el que la distancia euclídea sobre grados está mal."""
    por_lat, por_lon = grados_por_km(-33.45)
    assert por_lat == pytest.approx(0.008993, abs=1e-5)
    assert por_lon == pytest.approx(0.010779, abs=1e-5)
    # A esta latitud, un grado de longitud recorre un 16 % menos que uno de latitud.
    assert por_lon > por_lat
    km_lat = haversine_km(-33.95, 0.0, -32.95, 0.0)
    km_lon = haversine_km(-33.45, -0.5, -33.45, 0.5)
    assert km_lon / km_lat == pytest.approx(0.836, abs=0.01)
    # En el ecuador sí coinciden.
    eq_lat, eq_lon = grados_por_km(0.0)
    assert eq_lat == pytest.approx(eq_lon, rel=1e-6)


def test_utm_to_latlon_en_un_punto_de_referencia():
    """El centro de una zona UTM, en el ecuador, tiene longitud conocida.

    Para la zona 19 el meridiano central es 19 × 6 − 183 = −69°. En el falso este
    (500 000 m) y con norte cero en el hemisferio norte, la latitud es 0 y la longitud
    es exactamente el meridiano central.
    """
    lat, lon = utm_to_latlon(500000.0, 0.0, zona=19, hemisferio_sur=False)
    assert lat == pytest.approx(0.0, abs=1e-9)
    assert lon == pytest.approx(-69.0, abs=1e-9)


def test_utm_to_latlon_sobre_santiago_da_coordenadas_plausibles():
    # Valores tomados de un archivo público: ESTE 339892, NORTE 6298155.
    lat, lon = utm_to_latlon(339892.0, 6298155.0, zona=19)
    assert -34.0 < lat < -33.0, "debe caer en la latitud de Santiago"
    assert -71.5 < lon < -70.0, "debe caer en la longitud de Santiago"


def test_utm_to_latlon_vectorizado_conserva_el_indice():
    este = pd.Series([339892.0, 342846.0], index=[10, 11])
    norte = pd.Series([6298155.0, 6291414.0], index=[10, 11])
    lat, lon = utm_to_latlon(este, norte, zona=19)
    assert isinstance(lat, pd.Series) and isinstance(lon, pd.Series)
    assert list(lat.index) == [10, 11]
    assert lat.notna().all() and lon.notna().all()


def test_utm_to_latlon_el_hemisferio_cambia_el_resultado():
    sur = utm_to_latlon(339892.0, 6298155.0, zona=19, hemisferio_sur=True)
    norte = utm_to_latlon(339892.0, 6298155.0, zona=19, hemisferio_sur=False)
    assert sur[0] < 0 < norte[0]


def test_utm_to_latlon_rechaza_una_zona_invalida():
    for zona in (0, 61, -1):
        with pytest.raises(ValueError, match="Zona UTM inválida"):
            utm_to_latlon(500000.0, 0.0, zona=zona)


def test_utm_to_latlon_propaga_los_nulos():
    lat, lon = utm_to_latlon(pd.Series([339892.0, None]), pd.Series([6298155.0, None]))
    assert lat.notna().iloc[0]
    assert pd.isna(lat.iloc[1]) and pd.isna(lon.iloc[1])


# ---------------------------------------------------------------------- más cercano
@pytest.fixture
def origen() -> pd.DataFrame:
    return pd.DataFrame(
        {"lat": [-33.45, -33.50], "lon": [-70.67, -70.60]}, index=["p1", "p2"]
    )


@pytest.fixture
def destino() -> pd.DataFrame:
    return pd.DataFrame({
        "id": ["cerca_de_p1", "cerca_de_p2", "lejos"],
        "lat": [-33.4505, -33.4995, -33.90],
        "lon": [-70.6705, -70.6005, -70.60],
    })


def test_nearest_point_encuentra_el_mas_cercano(origen, destino):
    resultado = nearest_point(origen, destino, id_destino="id")
    assert list(resultado.index) == ["p1", "p2"]
    assert resultado.loc["p1", "destino_mas_cercano"] == "cerca_de_p1"
    assert resultado.loc["p2", "destino_mas_cercano"] == "cerca_de_p2"
    assert resultado["distancia_km"].max() < 0.1


def test_nearest_point_por_bloques_da_el_mismo_resultado(origen, destino):
    completo = nearest_point(origen, destino, id_destino="id", bloque=100)
    por_bloques = nearest_point(origen, destino, id_destino="id", bloque=1)
    pd.testing.assert_frame_equal(completo, por_bloques)


def test_nearest_point_sin_id_devuelve_el_indice_del_destino(origen, destino):
    resultado = nearest_point(origen, destino)
    assert resultado.loc["p1", "destino_mas_cercano"] == 0


def test_nearest_point_ignora_destinos_sin_coordenadas(origen):
    destino = pd.DataFrame({
        "id": ["sin_coordenadas", "valido"],
        "lat": [None, -33.4505],
        "lon": [None, -70.6705],
    })
    resultado = nearest_point(origen, destino, id_destino="id")
    assert set(resultado["destino_mas_cercano"].dropna()) == {"valido"}


def test_nearest_point_deja_nulo_el_origen_sin_coordenadas(destino):
    origen = pd.DataFrame({"lat": [-33.45, None], "lon": [-70.67, None]})
    resultado = nearest_point(origen, destino, id_destino="id")
    assert resultado["distancia_km"].notna().iloc[0]
    assert pd.isna(resultado["distancia_km"].iloc[1])
    # pandas puede representar el ausente como None o como NaN según los demás
    # valores de la columna; lo que importa es que no se inventó un destino.
    assert pd.isna(resultado["destino_mas_cercano"].iloc[1])


def test_nearest_point_valida_sus_entradas(origen, destino):
    with pytest.raises(ValueError, match="está vacía"):
        nearest_point(pd.DataFrame(columns=["lat", "lon"]), destino)
    with pytest.raises(ValueError, match="Faltan columnas"):
        nearest_point(origen.rename(columns={"lat": "latitud"}), destino)
    with pytest.raises(ValueError, match="bloque"):
        nearest_point(origen, destino, bloque=0)
    sin_coordenadas = pd.DataFrame({"id": ["x"], "lat": [None], "lon": [None]})
    with pytest.raises(ValueError, match="Ningún punto de destino"):
        nearest_point(origen, sin_coordenadas, id_destino="id")
