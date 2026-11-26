"""Geografía mínima: distancias sobre la esfera y conversión de UTM a latitud/longitud.

Qué hace
    Calcula distancias con la fórmula de haversine, convierte coordenadas UTM a
    geográficas con la proyección transversa de Mercator inversa, y busca el punto más
    cercano entre dos conjuntos.

Por qué existe
    Dos razones concretas.

    La primera: un grado de longitud **no mide lo mismo** que un grado de latitud. En
    Santiago, a −33,45° de latitud, un grado de latitud son unos 110,9 km y uno de
    longitud unos 92,8 km. Calcular una distancia euclídea sobre grados produce un
    error sistemático del orden del 20 % en la componente este-oeste, y el error no se
    nota porque el número resultante es plausible.

    La segunda: hay archivos públicos que traen **las dos** representaciones de la
    misma coordenada —UTM y latitud/longitud—. Convertir una y compararla con la otra
    es una validación independiente que no necesita ninguna fuente externa.

Por qué sin dependencias
    `pyproj` o `GeoPandas` hacen esto mejor y con más generalidad. Se implementa aquí
    para mantener el entorno mínimo y, sobre todo, porque las fórmulas explicadas sirven
    al programa de aprendizaje: una conversión de coordenadas tratada como caja negra no
    enseña nada. Para trabajo geoespacial serio, use las bibliotecas.

Fórmulas
    Haversine, distancia sobre la esfera entre (φ₁, λ₁) y (φ₂, λ₂):

        a = sin²(Δφ/2) + cos φ₁ · cos φ₂ · sin²(Δλ/2)
        d = 2 · R · arcsin(√a)                            [km, con R = 6371,0088 km]

    Transversa de Mercator inversa (UTM → geográficas), elipsoide WGS84:

        a = 6378137 m,  f = 1/298,257223563,  k₀ = 0,9996
        E₀ = 500000 m (falso este),  N₀ = 10000000 m en el hemisferio sur

Cómo se valida
    `tests/test_geo.py` compara haversine contra distancias conocidas entre ciudades,
    comprueba las propiedades de la métrica (cero, simetría, desigualdad triangular) y
    valida la conversión UTM con los datos reales de un archivo público que trae ambas
    representaciones.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

#: Radio medio de la Tierra según la IUGG, en kilómetros.
RADIO_TIERRA_KM = 6371.0088

#: Parámetros del elipsoide WGS84 y de la proyección UTM.
WGS84_A = 6378137.0
WGS84_F = 1 / 298.257223563
UTM_K0 = 0.9996
UTM_FALSO_ESTE = 500000.0
UTM_FALSO_NORTE_SUR = 10000000.0


def haversine_km(
    lat1: float | pd.Series | np.ndarray, lon1: float | pd.Series | np.ndarray,
    lat2: float | pd.Series | np.ndarray, lon2: float | pd.Series | np.ndarray,
) -> float | pd.Series | np.ndarray:
    """Distancia sobre la esfera, en kilómetros.

    Acepta escalares, series de pandas y arreglos de NumPy, incluidos arreglos que se
    difunden entre sí: `haversine_km(lat[:, None], lon[:, None], lat2, lon2)` devuelve
    la matriz de todas las distancias, que es lo que necesita una búsqueda del punto
    más cercano.

    Es exacta a efectos prácticos para distancias urbanas: el error por tratar la
    Tierra como esfera en lugar de elipsoide es del orden del 0,3 %, muy por debajo de
    la precisión con que se registran las coordenadas de una parada.

    Example:
        >>> round(haversine_km(-33.45, -70.67, -33.46, -70.67), 3)
        1.112
    """
    lat1_rad, lon1_rad = np.radians(lat1), np.radians(lon1)
    lat2_rad, lon2_rad = np.radians(lat2), np.radians(lon2)
    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad
    a = (np.sin(delta_lat / 2) ** 2
         + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon / 2) ** 2)
    distancia = 2 * RADIO_TIERRA_KM * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))

    series = [v for v in (lat1, lon1, lat2, lon2) if isinstance(v, pd.Series)]
    if series:
        return pd.Series(np.asarray(distancia).reshape(-1), index=series[0].index)
    arreglo = np.asarray(distancia)
    return float(arreglo) if arreglo.ndim == 0 else arreglo


def utm_to_latlon(
    este: float | pd.Series,
    norte: float | pd.Series,
    zona: int = 19,
    hemisferio_sur: bool = True,
) -> tuple[pd.Series, pd.Series] | tuple[float, float]:
    """Convierte coordenadas UTM a latitud y longitud geográficas (WGS84).

    Args:
        este: coordenada este en metros.
        norte: coordenada norte en metros.
        zona: zona UTM. Santiago de Chile está en la 19.
        hemisferio_sur: si True, se resta el falso norte de 10 000 000 m.

    Returns:
        Par (latitud, longitud) en grados decimales, del mismo tipo que la entrada.

    Raises:
        ValueError: si la zona está fuera de 1 a 60.

    Implementa la serie inversa de la transversa de Mercator. Los nombres de las
    variables intermedias siguen la notación habitual de la literatura geodésica
    (`e`, `e1`, `M`, `mu`, `phi1`, `C1`, `T1`, `N1`, `R1`, `D`) para que la fórmula se
    pueda contrastar con cualquier referencia.
    """
    if not 1 <= zona <= 60:
        raise ValueError(f"Zona UTM inválida: {zona}. Debe estar entre 1 y 60.")

    es_serie = isinstance(este, pd.Series) or isinstance(norte, pd.Series)
    x = np.asarray(pd.to_numeric(este, errors="coerce"), dtype=float) - UTM_FALSO_ESTE
    y = np.asarray(pd.to_numeric(norte, errors="coerce"), dtype=float)
    if hemisferio_sur:
        y = y - UTM_FALSO_NORTE_SUR

    a = WGS84_A
    e2 = 2 * WGS84_F - WGS84_F**2          # primera excentricidad al cuadrado
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    ep2 = e2 / (1 - e2)                     # segunda excentricidad al cuadrado

    M = y / UTM_K0                          # distancia meridional
    mu = M / (a * (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256))

    phi1 = (mu
            + (3 * e1 / 2 - 27 * e1**3 / 32) * np.sin(2 * mu)
            + (21 * e1**2 / 16 - 55 * e1**4 / 32) * np.sin(4 * mu)
            + (151 * e1**3 / 96) * np.sin(6 * mu)
            + (1097 * e1**4 / 512) * np.sin(8 * mu))

    C1 = ep2 * np.cos(phi1) ** 2
    T1 = np.tan(phi1) ** 2
    N1 = a / np.sqrt(1 - e2 * np.sin(phi1) ** 2)
    R1 = a * (1 - e2) / (1 - e2 * np.sin(phi1) ** 2) ** 1.5
    D = x / (N1 * UTM_K0)

    latitud = phi1 - (N1 * np.tan(phi1) / R1) * (
        D**2 / 2
        - (5 + 3 * T1 + 10 * C1 - 4 * C1**2 - 9 * ep2) * D**4 / 24
        + (61 + 90 * T1 + 298 * C1 + 45 * T1**2 - 252 * ep2 - 3 * C1**2) * D**6 / 720
    )
    longitud = (
        D
        - (1 + 2 * T1 + C1) * D**3 / 6
        + (5 - 2 * C1 + 28 * T1 - 3 * C1**2 + 8 * ep2 + 24 * T1**2) * D**5 / 120
    ) / np.cos(phi1)

    lat_grados = np.degrees(latitud)
    lon_grados = (zona * 6 - 183) + np.degrees(longitud)

    if es_serie:
        indice = (este if isinstance(este, pd.Series) else norte).index
        return pd.Series(lat_grados, index=indice), pd.Series(lon_grados, index=indice)
    return float(lat_grados), float(lon_grados)


def grados_por_km(latitud: float) -> tuple[float, float]:
    """Cuántos grados de latitud y de longitud equivalen a un kilómetro, a esa latitud.

    Sirve para dimensionar una rejilla o un margen de búsqueda. La asimetría es el
    punto: en Santiago un kilómetro son 0,0090° de latitud y 0,0108° de longitud.
    """
    km_por_grado_lat = haversine_km(latitud - 0.5, 0.0, latitud + 0.5, 0.0)
    km_por_grado_lon = haversine_km(latitud, -0.5, latitud, 0.5)
    return 1.0 / float(km_por_grado_lat), 1.0 / float(km_por_grado_lon)


def nearest_point(
    origen: pd.DataFrame,
    destino: pd.DataFrame,
    lat_origen: str = "lat",
    lon_origen: str = "lon",
    lat_destino: str = "lat",
    lon_destino: str = "lon",
    id_destino: str | None = None,
    bloque: int = 500,
) -> pd.DataFrame:
    """Para cada fila de `origen`, el punto más cercano de `destino` y su distancia.

    Args:
        origen: puntos desde los que se mide.
        destino: puntos candidatos.
        lat_origen, lon_origen: nombres de columna en `origen`.
        lat_destino, lon_destino: nombres de columna en `destino`.
        id_destino: columna de `destino` cuyo valor se devuelve como identificador del
            punto más cercano.
        bloque: filas de `origen` procesadas por iteración. Controla la memoria: el
            cálculo es una matriz de `bloque × len(destino)` distancias.

    Returns:
        Tabla alineada con el índice de `origen`, con la distancia en kilómetros y el
        identificador del destino más cercano.

    Raises:
        ValueError: si alguna tabla está vacía o falta una columna.

    Sobre el método: es fuerza bruta por bloques, de coste `O(n·m)`. Con 12 495 paradas
    y 1 927 locales son 24 millones de distancias, que se calculan en segundos con
    NumPy. Si cualquiera de los dos conjuntos creciera un orden de magnitud, el camino
    es un índice espacial (`scipy.spatial.cKDTree` sobre coordenadas proyectadas, o
    `GeoPandas.sjoin_nearest`); se declara aquí para que la decisión quede explícita en
    lugar de descubrirse cuando el proceso no termina.
    """
    for tabla, nombre, columnas in (
        (origen, "origen", (lat_origen, lon_origen)),
        (destino, "destino", (lat_destino, lon_destino)),
    ):
        if tabla.empty:
            raise ValueError(f"La tabla de {nombre} está vacía.")
        faltantes = [c for c in columnas if c not in tabla.columns]
        if faltantes:
            raise ValueError(f"Faltan columnas en {nombre}: {faltantes}")
    if bloque < 1:
        raise ValueError("El tamaño de bloque debe ser al menos 1.")

    lat_d = pd.to_numeric(destino[lat_destino], errors="coerce").to_numpy(dtype=float)
    lon_d = pd.to_numeric(destino[lon_destino], errors="coerce").to_numpy(dtype=float)
    validos = ~(np.isnan(lat_d) | np.isnan(lon_d))
    if not validos.any():
        raise ValueError("Ningún punto de destino tiene coordenadas utilizables.")
    lat_d, lon_d = lat_d[validos], lon_d[validos]
    etiquetas = (
        destino.loc[validos, id_destino].to_numpy() if id_destino
        else destino.index[validos].to_numpy()
    )

    lat_o = pd.to_numeric(origen[lat_origen], errors="coerce").to_numpy(dtype=float)
    lon_o = pd.to_numeric(origen[lon_origen], errors="coerce").to_numpy(dtype=float)

    distancias = np.full(len(origen), np.nan)
    cercanos: list = [None] * len(origen)
    for inicio in range(0, len(origen), bloque):
        fin = min(inicio + bloque, len(origen))
        la = lat_o[inicio:fin, None]
        lo = lon_o[inicio:fin, None]
        matriz = np.asarray(haversine_km(la, lo, lat_d[None, :], lon_d[None, :]))
        with np.errstate(invalid="ignore"):
            indice = np.nanargmin(np.where(np.isnan(matriz), np.inf, matriz), axis=1)
        minimos = matriz[np.arange(fin - inicio), indice]
        distancias[inicio:fin] = minimos
        for posicion, idx in enumerate(indice):
            if not np.isnan(minimos[posicion]):
                cercanos[inicio + posicion] = etiquetas[idx]

    return pd.DataFrame(
        {"distancia_km": distancias, "destino_mas_cercano": cercanos},
        index=origen.index,
    )
