"""P10: correspondencia entre buses y Metro, y el precio de confiar en una sola fuente.

El problema
    Dos archivos públicos describen **la misma realidad** —las estaciones de Metro de
    Santiago— con identificadores distintos y sin ningún campo en común. El feed GTFS
    trae 126 estaciones; el Excel de bip!, 143 filas. La pregunta de P10 es cuántas
    estaciones tienen paradas de bus a menos de 200 m y cuántos servicios las sirven.

    Contestarla exige antes conciliar los dos inventarios. Y al conciliarlos aparece
    algo que ninguno de los dos archivos delata por su cuenta.

La respuesta a la pregunta
    Las **126** estaciones tienen al menos una parada de bus a 200 m: el 100 %. No hay
    ninguna estación sin correspondencia. La mediana es de **13 servicios distintos**
    por estación, el P90 de 34, y el máximo de **55** en Santa Lucía. Paradas de bus a
    200 m: mediana 5, máximo 19.

    Y una advertencia que vale tanto como el resultado: calculado con las coordenadas
    del Excel de bip! en lugar de las del GTFS, el conteo de servicios cambia en **48
    de 125 estaciones**, el total baja de 2 014 a 1 815 —un 10 %— y **dos estaciones
    aparecerían sin ninguna parada de bus cerca** cuando sí la tienen. La elección de
    qué fuente provee la coordenada, que nadie suele declarar, decide el 38 % de las
    filas del informe.

El grano, que es lo primero y casi nunca está escrito
    126 contra 143 no es un error: son **granos distintos**.

    - El GTFS tiene **una fila por estación**. Las 17 estaciones de combinación llevan
      un identificador compuesto —`AN-NA`, `BA-BQ`, `CH-UCH`— que delata la fusión de
      dos códigos de línea.
    - El Excel de bip! tiene **una fila por estación y línea**. Sus 34 filas de
      combinación llevan la línea pegada al **nombre** —`SAN PABLO L1`, `SAN PABLO L5`—
      porque el campo `codigo` vale la línea y no identifica nada.

    Y 126 − 17 + 34 = 143. El grano cuadra, pero solo después de haberlo nombrado.
    Quitar el sufijo del nombre deja **126 estaciones distintas**, exactamente las del
    GTFS, de las cuales **125 coinciden por nombre normalizado**. La única excepción es
    `Presidente Pedro Aguirre Cerda` contra `PEDRO AGUIRRE CERDA`, y la resuelve la
    proximidad: están a 1,4 m.

Lo que se encontró: cuatro detectores y cuatro puntos ciegos
    P01 validó las coordenadas del Excel comparando sus **dos representaciones** —UTM
    contra latitud/longitud— y encontró tres errores en 1 928 filas. Es una
    comprobación correcta y tiene un punto ciego del tamaño exacto del problema
    siguiente: **no ve un error que afecte a las dos representaciones por igual**.

    De las estaciones de Metro, **ninguna** está marcada como sospechosa por P01. Y
    doce están a más de 500 m de donde el GTFS las pone, hasta **26 km**:

    | Error | Qué compara el detector | ¿Fuente externa? | Encuentra |
    | --- | --- | --- | --- |
    | Las dos coordenadas de una fila discrepan | UTM contra latitud/longitud | no | 3 en 1 928 · **0 estaciones de Metro** |
    | Dos filas de la misma estación discrepan | fila contra fila hermana | no | 4 estaciones a más de 200 m, **una a 26 km** |
    | La coordenada contradice la comuna declarada | fila contra sus pares de comuna | no | 8 locales a más de 10 km, **3 estaciones** |
    | La fila es coherente consigo misma y está mal | bip! contra GTFS | **sí** | **12 estaciones a más de 500 m** |

    Lo que importa de esa tabla: **tres de los cuatro detectores no necesitan ninguna
    fuente externa**, y P01 solo corrió el primero. El archivo podía delatar sus
    propios errores y nadie le hizo las preguntas.

Dos casos concretos, para que no quede en abstracto
    **Plaza de Armas.** Dos filas en bip!, una por línea, separadas **26,2 km**. La de
    L3 dice `Bandera 530`, latitud −33,4371: correcto. La de L5 dice `21 De Mayo 543`
    —que está a una cuadra de la otra— y latitud −33,2018, veintiséis kilómetros al
    norte. La dirección es correcta y la coordenada no. Dos filas que nombran la misma
    estación bastaban para encontrarlo.

    **Santa Lucía.** Una sola fila, de modo que no hay hermana que la contradiga. Dice
    `Av. Libertador Bernardo O´Higgins N°511`, que es el centro de Santiago, y una
    coordenada 12,7 km al suroeste. Su UTM está igual de mal, de modo que P01 no la vio.
    La atrapa la comuna que ella misma declara: está a 12,0 km de la mediana de los 148
    locales de la comuna `Santiago`. Y es, con las coordenadas del GTFS, **la estación
    con más correspondencia de bus de toda la red**: 55 servicios.

Tecnologías y por qué estas
    - **`lab.textual.normalize_key`** para conciliar por nombre, y el sufijo de línea
      quitado con una expresión regular **declarada**, no por parecido de cadenas. El
      emparejamiento por similitud se evita a propósito: un acierto por casualidad no
      se distingue de un acierto.
    - **Dos criterios independientes** —nombre y proximidad— y la comparación entre
      ellos. Un solo criterio no tiene con qué equivocarse a la vista.
    - **La mediana y no el centroide** para la referencia de comuna: con una fila a 26
      km, un promedio arrastra la referencia y el detector se ciega a sí mismo.
    - **`lab.geo.haversine_km`** y el radio de 200 m que fija el enunciado de P10.
    - **Reutiliza `cases.bip_lugares_carga`**, declarado en `case.json`.

Reproducir
    python scripts/fetch_data.py gtfs-red-movilidad bip-metro bip-puntos \\
        bip-centros-alto-estandar bip-centros-estandar bip-retail
    python -m cases.correspondencia_metro.solution

Advertencia de licencia
    El feed del DTPM **no se versiona**: su licencia no está verificada. Los Excel de
    bip! son CC BY-NC 2.0 y tampoco se versionan. Lo que se versiona es este código,
    los registros de procedencia y las tablas de resultado agregadas.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.bip_lugares_carga import solution as bip  # noqa: E402
from lab.geo import haversine_km, nearest_point  # noqa: E402
from lab.metrics import indicator_table, safe_ratio  # noqa: E402
from lab.sources import Provenance, read_zip_table  # noqa: E402
from lab.textual import normalize_key  # noqa: E402

HERE = Path(__file__).resolve().parent
FEED = ROOT / "data" / "original" / "gtfs-red-movilidad.zip"
RESULTS = HERE / "resultados"

#: Radio de correspondencia, en metros. Lo fija el enunciado de P10. Es más estricto
#: que los 300 m de P08 porque aquí la caminata es dentro de una combinación, no un
#: trayecto hasta un local: el umbral describe otra cosa y se declara aparte.
RADIO_M = 200.0

#: `route_type` de la especificación GTFS. El 1 es metro y el 3, bus.
TIPO_METRO = "1"
TIPO_BUS = "3"

#: `location_type` 1 es una estación; 0 —o vacío— un lugar donde sube gente.
TIPO_ESTACION = "1"
TIPO_EMBARQUE = "0"

#: El sufijo de línea pegado al nombre en el Excel de bip!: `SAN PABLO L1`, `LA
#: CISTERNA L4A`. Se declara en lugar de deducirse por parecido, porque una estación
#: que legítimamente terminara en algo similar quedaría mutilada en silencio.
SUFIJO_DE_LINEA = re.compile(r"\s+L\d+A?$")

#: Desvío sobre el cual dos filas que nombran la misma estación no describen el mismo
#: lugar. 200 m es el mismo criterio de P01, por coherencia entre casos.
UMBRAL_ENTRE_FILAS_M = 200.0

#: Desvío contra la fuente externa sobre el cual la discrepancia no se explica por la
#: diferencia entre el acceso de una estación y su centro. Una estación de Metro grande
#: tiene accesos a 200 m del punto que la representa; a 500 m ya no es eso.
UMBRAL_CONTRA_GTFS_M = 500.0

#: Distancia a la mediana de la propia comuna declarada por encima de la cual la fila
#: se marca. 10 km es deliberadamente holgado: a 3 km hay 227 locales, que son
#: demasiados para ser todos errores en comunas grandes. El detector es una **señal**,
#: no un veredicto, y se informa la curva completa.
UMBRAL_CONTRA_COMUNA_KM = 10.0

#: Mínimo de locales para que la mediana de una comuna sea una referencia utilizable.
MINIMO_POR_COMUNA = 5

#: Bloque de estaciones por iteración al buscar paradas cercanas.
BLOQUE = 32


def _ruta_legible(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _exigir_feed(feed: Path | None = None) -> Path:
    archivo = feed or FEED
    if not archivo.exists():
        raise FileNotFoundError(
            f"No está el feed en {_ruta_legible(archivo)}.\n"
            "Descárguelo con:  python scripts/fetch_data.py gtfs-red-movilidad"
        )
    return archivo


# --------------------------------------------------------------------------- lectura
def cargar(feed: Path | None = None) -> dict[str, pd.DataFrame]:
    """Lee del ZIP las cinco tablas que el caso necesita."""
    archivo = _exigir_feed(feed)
    return {
        "stops": read_zip_table(archivo, "stops.txt", dtype=str,
                                usecols=["stop_id", "stop_name", "location_type",
                                         "parent_station", "stop_lat", "stop_lon"]),
        "routes": read_zip_table(archivo, "routes.txt", dtype=str,
                                 usecols=["route_id", "route_short_name", "route_type"]),
        "trips": read_zip_table(archivo, "trips.txt", dtype=str,
                                usecols=["route_id", "trip_id"]),
        "stop_times": read_zip_table(archivo, "stop_times.txt", dtype=str,
                                     usecols=["trip_id", "stop_id"]),
    }


def estaciones_gtfs(tablas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Las estaciones del feed: `location_type = 1`, una fila por estación.

    No se usan las paradas de andén (`location_type = 0` con `parent_station`): son dos
    por estación y por sentido, de modo que contarlas daría 286 «estaciones». La
    jerarquía de la especificación existe precisamente para no tener que adivinar esto.
    """
    stops = tablas["stops"]
    estaciones = stops.loc[stops["location_type"] == TIPO_ESTACION].copy()
    estaciones["lat"] = pd.to_numeric(estaciones["stop_lat"], errors="coerce")
    estaciones["lon"] = pd.to_numeric(estaciones["stop_lon"], errors="coerce")
    estaciones["clave"] = estaciones["stop_name"].map(normalize_key)
    estaciones["id_compuesto"] = estaciones["stop_id"].str.contains("-")
    columnas = ["stop_id", "stop_name", "clave", "lat", "lon", "id_compuesto"]
    return estaciones[columnas].sort_values("stop_id").reset_index(drop=True)


def estaciones_bip() -> pd.DataFrame:
    """Las filas de Metro del Excel de bip!, con el sufijo de línea separado del nombre.

    El sufijo se quita a una columna nueva y el nombre original se conserva: perder el
    dato de origen para quedarse con el derivado impide auditar la transformación.
    """
    consolidado = bip.consolidar()
    metro = consolidado.loc[
        (consolidado["tipo_local"] == bip.TIPOS["bip-metro"]) & consolidado["abierto"]
    ].copy()
    metro["nombre_estacion"] = metro["nombre"].astype("string").str.replace(
        SUFIJO_DE_LINEA, "", regex=True
    )
    metro["tiene_sufijo"] = metro["nombre"].astype("string").str.contains(
        SUFIJO_DE_LINEA, regex=True, na=False
    )
    metro["clave"] = metro["nombre_estacion"].map(normalize_key)
    metro["lat"] = metro["latitud"]
    metro["lon"] = metro["longitud"]
    return metro.reset_index(drop=True)


# ------------------------------------------------------------------------- el grano
def informe_de_grano(gtfs: pd.DataFrame, bip_metro: pd.DataFrame) -> pd.DataFrame:
    """Por qué 126 y 143 no se contradicen: el grano de cada fuente.

    Es la tabla que hay que construir **antes** de cualquier cruce. Sin ella, la
    diferencia de 17 filas parece un problema de completitud y se «arregla»
    descartando, que es la forma habitual de perder las estaciones de combinación.
    """
    combinaciones = int(gtfs["id_compuesto"].sum())
    con_sufijo = int(bip_metro["tiene_sufijo"].sum())
    return indicator_table({
        "estaciones_gtfs": (
            int(len(gtfs)), "filas",
            "Filas con location_type 1: una por estación"),
        "filas_bip": (
            int(len(bip_metro)), "filas",
            "Una por estación y línea: es otro grano, no un error"),
        "estaciones_de_combinacion_gtfs": (
            combinaciones, "estaciones",
            "Identificador compuesto con guion (AN-NA, BA-BQ): delata la fusión "
            "de dos códigos de línea"),
        "filas_con_sufijo_de_linea_bip": (
            con_sufijo, "filas",
            "Nombres como «SAN PABLO L1»: la línea va pegada al nombre porque "
            "el campo codigo vale la línea y no identifica nada"),
        "relacion_entre_los_dos_granos": (
            int(len(gtfs) - combinaciones + con_sufijo), "filas",
            "estaciones − combinaciones + filas con sufijo. Debe dar las filas de bip!"),
        "estaciones_bip_tras_quitar_el_sufijo": (
            int(bip_metro["clave"].nunique()), "estaciones",
            "Si coincide con las del GTFS, el grano quedó reducido correctamente"),
    })


# -------------------------------------------------------------------- la conciliación
def conciliar(gtfs: pd.DataFrame, bip_metro: pd.DataFrame) -> pd.DataFrame:
    """Une los dos inventarios por nombre y, en paralelo, por proximidad.

    Los dos criterios son independientes y eso es el punto: con uno solo no hay con qué
    detectar un emparejamiento equivocado. La tabla devuelve ambos resultados y la
    columna `coinciden_los_criterios`, que es donde hay que mirar.
    """
    por_estacion = bip_metro.groupby("clave", observed=True).agg(
        nombre_bip=("nombre_estacion", "first"),
        lat_bip=("lat", "median"),
        lon_bip=("lon", "median"),
        lineas=("codigo", lambda s: ",".join(sorted(set(s.dropna())))),
        filas_bip=("codigo", "size"),
    ).reset_index()

    # Reducir el grano por mediana **suaviza un error en lugar de mostrarlo**: la
    # mediana de dos filas separadas 26 km cae en un punto donde no hay ninguna
    # estación, y reduce a la mitad el desvío aparente contra la otra fuente. De modo
    # que se mide cuánto esconde, por estación, y la cifra viaja con el resultado.
    dispersion = []
    for clave, grupo in bip_metro.groupby("clave", observed=True):
        mediana_lat = float(grupo["lat"].median())
        mediana_lon = float(grupo["lon"].median())
        a_la_mediana = haversine_km(
            grupo["lat"], grupo["lon"], mediana_lat, mediana_lon
        ) * 1000
        dispersion.append({
            "clave": clave,
            "dispersion_interna_m": float(a_la_mediana.max()),
        })
    por_estacion = por_estacion.merge(pd.DataFrame(dispersion), on="clave", how="left")

    unido = gtfs.rename(columns={"lat": "lat_gtfs", "lon": "lon_gtfs"}).merge(
        por_estacion, on="clave", how="left"
    )
    cercano = nearest_point(
        unido, por_estacion,
        lat_origen="lat_gtfs", lon_origen="lon_gtfs",
        lat_destino="lat_bip", lon_destino="lon_bip",
    )
    unido["clave_mas_cercana"] = cercano["destino_mas_cercano"].map(por_estacion["clave"])
    unido["distancia_al_mas_cercano_m"] = cercano["distancia_km"] * 1000
    unido["cruza_por_nombre"] = unido["nombre_bip"].notna()
    unido["coinciden_los_criterios"] = unido["clave"] == unido["clave_mas_cercana"]
    unido["desvio_m"] = haversine_km(
        unido["lat_gtfs"], unido["lon_gtfs"], unido["lat_bip"], unido["lon_bip"]
    ) * 1000
    # El desvío que habría si se tomara la peor de las filas de la estación en lugar
    # de su mediana. La diferencia entre las dos columnas es lo que oculta el agregado.
    unido["desvio_peor_fila_m"] = unido["desvio_m"] + unido["dispersion_interna_m"].fillna(0.0)
    unido["filas_discrepantes"] = unido["dispersion_interna_m"].fillna(0.0).gt(
        UMBRAL_ENTRE_FILAS_M / 2
    )
    return unido


def informe_de_conciliacion(conciliado: pd.DataFrame) -> pd.DataFrame:
    """Cuánto coincide cada criterio y cuánto coinciden entre sí."""
    total = len(conciliado)
    por_nombre = int(conciliado["cruza_por_nombre"].sum())
    coinciden = int(conciliado["coinciden_los_criterios"].sum())
    return indicator_table({
        "estaciones_a_conciliar": (total, "estaciones", "Las del GTFS"),
        "cruzan_por_nombre": (
            por_nombre, "estaciones",
            "Con el sufijo de línea quitado y el nombre normalizado"),
        "cruzan_por_nombre_pct": (
            round(float(safe_ratio(por_nombre, total, scale=100)), 2), "%", ""),
        "sin_par_por_nombre": (
            total - por_nombre, "estaciones",
            "Un cruce solo por nombre las perdería en silencio"),
        "los_dos_criterios_coinciden": (
            coinciden, "estaciones",
            "El par por nombre es además el más cercano geográficamente"),
        "los_criterios_discrepan": (
            total - coinciden, "estaciones",
            "Donde hay que mirar: o el nombre o la coordenada está mal"),
        "desvio_mediano_m": (
            round(float(conciliado["desvio_m"].median()), 1), "m",
            "Entre las dos fuentes, donde cruzan por nombre"),
        "desvio_maximo_m": (
            round(float(conciliado["desvio_m"].max()), 1), "m",
            "El peor caso usando la MEDIANA de las filas de la estación"),
        "desvio_maximo_peor_fila_m": (
            round(float(conciliado["desvio_peor_fila_m"].max()), 1), "m",
            "El mismo caso usando la peor de sus filas. La diferencia con la "
            "cifra anterior es lo que el agregado por mediana esconde"),
        "estaciones_con_filas_discrepantes": (
            int(conciliado["filas_discrepantes"].sum()), "estaciones",
            "Sus filas de bip! no coinciden entre sí, de modo que cualquier "
            "agregado de sus coordenadas inventa un punto intermedio"),
    })


def criterios_discrepantes(conciliado: pd.DataFrame) -> pd.DataFrame:
    """Las estaciones donde el par por nombre no es el más cercano, una por fila.

    Se listan todas porque cada una tiene una causa distinta: un nombre que cambió, una
    coordenada equivocada, o dos estaciones genuinamente vecinas.
    """
    discrepan = conciliado.loc[~conciliado["coinciden_los_criterios"]].copy()
    columnas = ["stop_id", "stop_name", "nombre_bip", "clave_mas_cercana",
                "distancia_al_mas_cercano_m", "desvio_m", "dispersion_interna_m"]
    salida = discrepan[columnas].copy()
    for columna in ("distancia_al_mas_cercano_m", "desvio_m", "dispersion_interna_m"):
        salida[columna] = salida[columna].round(1)
    return salida.sort_values("desvio_m", ascending=False).reset_index(drop=True)


# --------------------------------------------------------- los cuatro detectores
def detectar_discrepancia_interna(bip_metro: pd.DataFrame) -> pd.DataFrame:
    """Detector 1, el de P01: las dos representaciones de una misma fila.

    Compara la coordenada publicada con la derivada del este y norte UTM. Encuentra
    errores de conversión y de digitación de **una** de las dos, y es ciego a un error
    que afecte a las dos por igual, que es justamente el que este caso destapa.
    """
    sospechosas = bip_metro.loc[bip_metro["coordenada_sospechosa"]]
    return indicator_table({
        "filas_evaluadas": (int(len(bip_metro)), "filas", "Las de Metro del Excel"),
        "marcadas_sospechosas": (
            int(len(sospechosas)), "filas",
            f"Las dos coordenadas de la fila difieren más de "
            f"{bip.UMBRAL_COORDENADA_M:.0f} m"),
        "desvio_interno_mediano_m": (
            round(float(bip_metro["desvio_m"].median()), 1), "m",
            "El desvío sistemático entre las dos representaciones"),
        "punto_ciego": (
            0, "filas",
            "Errores que este detector no puede ver: los que afectan a las dos "
            "representaciones por igual. Se cuentan con los detectores 2, 3 y 4"),
    })


def detectar_entre_filas(bip_metro: pd.DataFrame) -> pd.DataFrame:
    """Detector 2: dos filas que nombran la misma estación deben estar en el mismo sitio.

    No necesita ninguna fuente externa y encuentra el peor error del archivo: Plaza de
    Armas con sus dos filas separadas 26,2 km. Es ciego donde la estación tiene una
    sola fila, que es el caso de Santa Lucía.
    """
    filas = []
    for clave, grupo in bip_metro.groupby("clave", observed=True):
        if len(grupo) < 2:
            continue
        lat = grupo["lat"].to_numpy(dtype=float)
        lon = grupo["lon"].to_numpy(dtype=float)
        matriz = np.asarray(haversine_km(lat[:, None], lon[:, None],
                                         lat[None, :], lon[None, :])) * 1000
        filas.append({
            "estacion": clave,
            "filas": int(len(grupo)),
            "lineas": ",".join(sorted(grupo["codigo"].dropna())),
            "separacion_maxima_m": round(float(np.nanmax(matriz)), 1),
            "excede_el_umbral": "sí" if np.nanmax(matriz) > UMBRAL_ENTRE_FILAS_M else "no",
        })
    tabla = pd.DataFrame(filas)
    if tabla.empty:
        return tabla
    return tabla.sort_values("separacion_maxima_m", ascending=False).reset_index(drop=True)


def detectar_contra_comuna(
    umbral_km: float = UMBRAL_CONTRA_COMUNA_KM,
    minimo: int = MINIMO_POR_COMUNA,
) -> pd.DataFrame:
    """Detector 3: la coordenada contra la comuna que la propia fila declara.

    Para cada local se mide la distancia a la **mediana** de las coordenadas de los
    locales de su misma comuna declarada. Una fila muy lejos de sus pares tiene la
    coordenada o la comuna equivocadas, y en cualquiera de los dos casos hay que
    mirarla.

    Se usa la mediana y no el promedio a propósito: con una fila a 26 km, un promedio
    arrastra la referencia hacia el error y el detector se ciega a sí mismo.

    Opera sobre **todo** el archivo y no solo sobre Metro, porque el detector se
    descubrió aquí pero el hallazgo es del archivo completo.
    """
    consolidado = bip.consolidar()
    locales = consolidado.loc[
        consolidado["abierto"]
        & consolidado["latitud"].notna()
        & consolidado["longitud"].notna()
    ].copy()
    referencia = locales.groupby("comuna_clave", observed=True).agg(
        lat_comuna=("latitud", "median"),
        lon_comuna=("longitud", "median"),
        locales_en_la_comuna=("codigo", "size"),
    )
    locales = locales.join(referencia, on="comuna_clave")
    locales["km_a_su_comuna"] = haversine_km(
        locales["latitud"], locales["longitud"],
        locales["lat_comuna"], locales["lon_comuna"],
    )
    marcadas = locales.loc[
        locales["locales_en_la_comuna"].ge(minimo)
        & locales["km_a_su_comuna"].gt(umbral_km)
    ]
    columnas = ["tipo_local", "nombre", "direccion", "comuna_etiqueta",
                "locales_en_la_comuna", "km_a_su_comuna"]
    salida = marcadas[columnas].copy()
    salida["km_a_su_comuna"] = salida["km_a_su_comuna"].round(2)
    return salida.sort_values("km_a_su_comuna", ascending=False).reset_index(drop=True)


def sensibilidad_del_detector_de_comuna(
    umbrales_km: tuple[float, ...] = (3.0, 5.0, 10.0, 15.0),
) -> pd.DataFrame:
    """Cuántos locales marca el detector 3 según el umbral, y de qué tipo.

    Importa porque el detector es una **señal y no un veredicto**: a 3 km marca 227
    locales, que son demasiados para ser todos errores en comunas extensas. La curva
    deja la elección del umbral a la vista en lugar de esconderla en una constante.
    """
    filas = []
    for umbral in umbrales_km:
        marcadas = detectar_contra_comuna(umbral_km=umbral)
        por_tipo = marcadas["tipo_local"].value_counts()
        filas.append({
            "umbral_km": umbral,
            "locales_marcados": int(len(marcadas)),
            "estaciones_de_metro": int(por_tipo.get(bip.TIPOS["bip-metro"], 0)),
            "puntos_bip": int(por_tipo.get(bip.TIPOS["bip-puntos"], 0)),
            "otros": int(len(marcadas) - por_tipo.get(bip.TIPOS["bip-metro"], 0)
                         - por_tipo.get(bip.TIPOS["bip-puntos"], 0)),
        })
    return pd.DataFrame(filas)


def detectar_contra_gtfs(
    conciliado: pd.DataFrame, umbral_m: float = UMBRAL_CONTRA_GTFS_M
) -> pd.DataFrame:
    """Detector 4: la coordenada de bip! contra la del GTFS, que es la fuente externa.

    Es el único de los cuatro que necesita otra fuente, y el único que ve un error
    coherente consigo mismo en todas las comprobaciones internas.

    Ojo con lo que **no** se puede concluir: que el GTFS tenga razón no se demuestra
    aquí. Lo que se sostiene es más modesto y suficiente: las dos fuentes discrepan, y
    en los casos inspeccionados la **dirección** que trae el propio Excel coincide con
    la posición del GTFS y no con su propia coordenada.
    """
    lejanas = conciliado.loc[
        conciliado["cruza_por_nombre"] & conciliado["desvio_m"].gt(umbral_m)
    ].copy()
    columnas = ["stop_id", "stop_name", "nombre_bip", "lineas", "desvio_m"]
    salida = lejanas[columnas].copy()
    salida["desvio_m"] = salida["desvio_m"].round(1)
    return salida.sort_values("desvio_m", ascending=False).reset_index(drop=True)


def tabla_de_detectores(
    bip_metro: pd.DataFrame, conciliado: pd.DataFrame
) -> pd.DataFrame:
    """Los cuatro detectores, lo que cada uno encuentra y a qué es ciego.

    Es el entregable conceptual del caso. La lectura que importa: **tres de los cuatro
    no necesitan ninguna fuente externa**, y el caso P01 solo corrió el primero.
    """
    entre_filas = detectar_entre_filas(bip_metro)
    excede = (
        int((entre_filas["excede_el_umbral"] == "sí").sum())
        if not entre_filas.empty else 0
    )
    metro_por_comuna = detectar_contra_comuna()
    metro_marcado = int(
        (metro_por_comuna["tipo_local"] == bip.TIPOS["bip-metro"]).sum()
    )
    contra_gtfs = detectar_contra_gtfs(conciliado)
    return pd.DataFrame([
        {
            "detector": "1. Dos representaciones de una fila",
            "compara": "UTM contra latitud/longitud, dentro de la fila",
            "fuente_externa": "no",
            "hallazgos": int(bip_metro["coordenada_sospechosa"].sum()),
            "unidad": "filas de Metro",
            "ciego_a": "un error que afecte a las dos representaciones por igual",
        },
        {
            "detector": "2. Filas hermanas de la misma estación",
            "compara": "fila contra fila que nombra lo mismo",
            "fuente_externa": "no",
            "hallazgos": excede,
            "unidad": "estaciones",
            "ciego_a": "la estación que tiene una sola fila",
        },
        {
            "detector": "3. Coordenada contra comuna declarada",
            "compara": "fila contra la mediana de sus pares de comuna",
            "fuente_externa": "no",
            "hallazgos": metro_marcado,
            "unidad": "estaciones",
            "ciego_a": "un error dentro de la propia comuna",
        },
        {
            "detector": "4. Contra otra fuente",
            "compara": "bip! contra el feed GTFS",
            "fuente_externa": "sí",
            "hallazgos": int(len(contra_gtfs)),
            "unidad": "estaciones",
            "ciego_a": "un error que las dos fuentes compartan",
        },
    ])


# ------------------------------------------------------------------ la correspondencia
def paradas_de_bus(tablas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Paradas de embarque servidas por algún servicio de bus, con sus servicios.

    Se exige las dos condiciones: que la fila sea un lugar de embarque y que algún
    recorrido de `route_type = 3` pare ahí. Con la primera sola entran andenes de Metro;
    con la segunda sola, estaciones y nodos.
    """
    rutas_bus = tablas["routes"].loc[tablas["routes"]["route_type"] == TIPO_BUS]
    viajes = tablas["trips"].loc[
        tablas["trips"]["route_id"].isin(set(rutas_bus["route_id"]))
    ]
    servicios = (
        tablas["stop_times"]
        .merge(viajes, on="trip_id")[["stop_id", "route_id"]]
        .drop_duplicates()
        .merge(rutas_bus[["route_id", "route_short_name"]], on="route_id")
    )
    stops = tablas["stops"]
    embarque = stops.loc[stops["location_type"].fillna(TIPO_EMBARQUE) == TIPO_EMBARQUE].copy()
    embarque = embarque.loc[embarque["stop_id"].isin(set(servicios["stop_id"]))].copy()
    embarque["lat"] = pd.to_numeric(embarque["stop_lat"], errors="coerce")
    embarque["lon"] = pd.to_numeric(embarque["stop_lon"], errors="coerce")
    por_parada = servicios.groupby("stop_id", observed=True)["route_short_name"].agg(
        lambda s: frozenset(s)
    )
    embarque["servicios"] = embarque["stop_id"].map(por_parada)
    return embarque[["stop_id", "stop_name", "lat", "lon", "servicios"]].reset_index(drop=True)


def correspondencia(
    estaciones: pd.DataFrame,
    buses: pd.DataFrame,
    lat_columna: str = "lat",
    lon_columna: str = "lon",
    radio_m: float = RADIO_M,
) -> pd.DataFrame:
    """Paradas de bus y servicios distintos a `radio_m` de cada estación.

    `lat_columna` y `lon_columna` permiten repetir el cálculo con la coordenada de la
    otra fuente, que es lo que mide `sensibilidad_a_la_fuente`.
    """
    lat_bus = buses["lat"].to_numpy(dtype=float)
    lon_bus = buses["lon"].to_numpy(dtype=float)
    conjuntos = buses["servicios"].to_numpy()

    lat = estaciones[lat_columna].to_numpy(dtype=float)
    lon = estaciones[lon_columna].to_numpy(dtype=float)

    paradas: list[int] = []
    servicios: list[int] = []
    listas: list[str] = []
    for inicio in range(0, len(estaciones), BLOQUE):
        fin = min(inicio + BLOQUE, len(estaciones))
        matriz = np.asarray(haversine_km(
            lat[inicio:fin, None], lon[inicio:fin, None],
            lat_bus[None, :], lon_bus[None, :],
        )) * 1000
        for fila in range(fin - inicio):
            cerca = np.flatnonzero(matriz[fila] <= radio_m)
            union: set[str] = set()
            for k in cerca:
                valor = conjuntos[k]
                if isinstance(valor, (frozenset, set)):
                    union |= set(valor)
            paradas.append(len(cerca))
            servicios.append(len(union))
            listas.append(",".join(sorted(union)))

    salida = estaciones.copy()
    salida["paradas_de_bus"] = paradas
    salida["servicios_distintos"] = servicios
    salida["lista_de_servicios"] = listas
    return salida


def informe_de_correspondencia(tabla: pd.DataFrame) -> pd.DataFrame:
    """La respuesta a P10, resumida."""
    total = len(tabla)
    con_bus = int(tabla["paradas_de_bus"].gt(0).sum())
    return indicator_table({
        "estaciones_evaluadas": (total, "estaciones", "Las 126 del feed"),
        "con_parada_de_bus_cerca": (
            con_bus, "estaciones", f"Con al menos una parada a {RADIO_M:.0f} m"),
        "con_parada_de_bus_pct": (
            round(float(safe_ratio(con_bus, total, scale=100)), 1), "%", ""),
        "sin_ninguna": (
            total - con_bus, "estaciones", "Estaciones sin correspondencia de bus"),
        "servicios_mediana": (
            float(tabla["servicios_distintos"].median()), "servicios",
            "Servicios de bus distintos por estación"),
        "servicios_p90": (
            float(tabla["servicios_distintos"].quantile(0.90)), "servicios", ""),
        "servicios_maximo": (
            int(tabla["servicios_distintos"].max()), "servicios",
            "El máximo de la red"),
        "paradas_mediana": (
            float(tabla["paradas_de_bus"].median()), "paradas",
            f"Paradas de bus a {RADIO_M:.0f} m de la estación"),
    })


def mejores_correspondencias(tabla: pd.DataFrame, limite: int = 12) -> pd.DataFrame:
    """Las estaciones con más servicios de bus distintos a 200 m."""
    columnas = ["stop_id", "stop_name", "paradas_de_bus", "servicios_distintos"]
    return tabla.nlargest(limite, "servicios_distintos")[columnas].reset_index(drop=True)


def sensibilidad_a_la_fuente(
    conciliado: pd.DataFrame, buses: pd.DataFrame
) -> pd.DataFrame:
    """Cuánto cambia la respuesta según qué fuente provea la coordenada de la estación.

    Es la pregunta que casi nunca se hace, porque las dos fuentes son oficiales y
    ninguna se presenta como aproximada. La respuesta: cambia el 38 % de las filas del
    informe.
    """
    comparables = conciliado.loc[conciliado["cruza_por_nombre"]].reset_index(drop=True)
    con_gtfs = correspondencia(comparables, buses, "lat_gtfs", "lon_gtfs")
    con_bip = correspondencia(comparables, buses, "lat_bip", "lon_bip")

    cambia = con_gtfs["servicios_distintos"].to_numpy() != con_bip["servicios_distintos"].to_numpy()
    perderian = (con_gtfs["paradas_de_bus"].gt(0) & con_bip["paradas_de_bus"].eq(0)).sum()
    ganarian = (con_gtfs["paradas_de_bus"].eq(0) & con_bip["paradas_de_bus"].gt(0)).sum()
    return indicator_table({
        "estaciones_comparables": (
            int(len(comparables)), "estaciones", "Las que cruzan por nombre"),
        "cambia_el_conteo_de_servicios": (
            int(cambia.sum()), "estaciones",
            "Solo por elegir la otra coordenada de la misma estación"),
        "cambia_pct": (
            round(float(safe_ratio(cambia.sum(), len(comparables), scale=100)), 1), "%", ""),
        "aparecerian_sin_bus": (
            int(perderian), "estaciones",
            "Con la coordenada de bip! parecerían no tener ninguna parada cerca"),
        "aparecerian_con_bus": (
            int(ganarian), "estaciones", "El caso contrario"),
        "servicios_totales_con_gtfs": (
            int(con_gtfs["servicios_distintos"].sum()), "servicios",
            "Suma sobre las estaciones, con repetición entre estaciones"),
        "servicios_totales_con_bip": (
            int(con_bip["servicios_distintos"].sum()), "servicios", ""),
    })


def resumen(conciliado: pd.DataFrame, tabla: pd.DataFrame,
            bip_metro: pd.DataFrame) -> pd.DataFrame:
    """Las cifras del caso."""
    total = len(tabla)
    con_bus = int(tabla["paradas_de_bus"].gt(0).sum())
    contra_gtfs = detectar_contra_gtfs(conciliado)
    return indicator_table({
        "estaciones_gtfs": (int(len(conciliado)), "estaciones", "location_type 1"),
        "filas_bip": (
            int(len(bip_metro)), "filas", "Una por estación y línea: otro grano"),
        "concilian_por_nombre": (
            int(conciliado["cruza_por_nombre"].sum()), "estaciones",
            "Tras quitar el sufijo de línea y normalizar"),
        "correspondencia_de_bus_pct": (
            round(float(safe_ratio(con_bus, total, scale=100)), 1), "%",
            f"Estaciones con al menos una parada de bus a {RADIO_M:.0f} m"),
        "servicios_mediana": (
            float(tabla["servicios_distintos"].median()), "servicios",
            "Servicios de bus distintos por estación"),
        "estaciones_mal_ubicadas_en_bip": (
            int(len(contra_gtfs)), "estaciones",
            f"A más de {UMBRAL_CONTRA_GTFS_M:.0f} m de donde el GTFS las pone, "
            "ninguna detectada por la validación interna de P01"),
        "peor_desvio_m": (
            round(float(conciliado["desvio_peor_fila_m"].max()), 1), "m",
            "Plaza de Armas, tomando la peor de sus dos filas. Sus filas de L3 "
            "y L5 están separadas 26,2 km entre sí"),
    })


# ---------------------------------------------------------------------------- informe
def analizar(feed: Path | None = None) -> dict[str, pd.DataFrame]:
    """Ejecuta el caso completo y devuelve todas las tablas de resultado."""
    tablas = cargar(feed)
    gtfs = estaciones_gtfs(tablas)
    bip_metro = estaciones_bip()
    conciliado = conciliar(gtfs, bip_metro)
    buses = paradas_de_bus(tablas)
    tabla = correspondencia(gtfs, buses)

    return {
        "resumen": resumen(conciliado, tabla, bip_metro),
        "grano": informe_de_grano(gtfs, bip_metro),
        "conciliacion": informe_de_conciliacion(conciliado),
        "criterios_discrepantes": criterios_discrepantes(conciliado),
        "detectores": tabla_de_detectores(bip_metro, conciliado),
        "detector_1_interno": detectar_discrepancia_interna(bip_metro),
        "detector_2_entre_filas": detectar_entre_filas(bip_metro),
        "detector_3_contra_comuna": detectar_contra_comuna(),
        "detector_3_sensibilidad": sensibilidad_del_detector_de_comuna(),
        "detector_4_contra_gtfs": detectar_contra_gtfs(conciliado),
        "correspondencia": informe_de_correspondencia(tabla),
        "mejores_correspondencias": mejores_correspondencias(tabla),
        "sensibilidad_a_la_fuente": sensibilidad_a_la_fuente(conciliado, buses),
        "por_estacion": tabla[["stop_id", "stop_name", "paradas_de_bus",
                               "servicios_distintos", "lista_de_servicios"]],
    }


def exportar(resultados: dict[str, pd.DataFrame], destino: Path = RESULTS) -> Path:
    """Escribe las tablas de resultado en CSV. Son agregados, no datos de terceros."""
    destino.mkdir(parents=True, exist_ok=True)
    for nombre, tabla in resultados.items():
        tabla.to_csv(destino / f"{nombre}.csv", index=False, encoding="utf-8")
    return destino


def main() -> None:
    from lab.console import enable_utf8

    enable_utf8()
    archivo = _exigir_feed()
    try:
        print(f"Fuente del feed: {Provenance.from_path(archivo).summary()}\n")
    except FileNotFoundError:
        print("Aviso: el feed no tiene registro de procedencia.\n")

    resultados = analizar(archivo)

    print("=== Resumen ===")
    print(resultados["resumen"].to_string(index=False))

    print("\n=== El grano: por qué 126 y 143 no se contradicen ===")
    print(resultados["grano"].to_string(index=False))

    print("\n=== La conciliación, con los dos criterios ===")
    print(resultados["conciliacion"].to_string(index=False))

    print("\n=== Donde los dos criterios discrepan ===")
    print(resultados["criterios_discrepantes"].to_string(index=False))

    print("\n=== Los cuatro detectores y sus puntos ciegos ===")
    print(resultados["detectores"].to_string(index=False))

    print("\n=== Detector 2: filas hermanas que no están en el mismo sitio ===")
    print(resultados["detector_2_entre_filas"].head(8).to_string(index=False))

    print("\n=== Detector 3: la coordenada contra su propia comuna ===")
    print(resultados["detector_3_contra_comuna"].to_string(index=False))

    print("\n=== Detector 3: cuántos marca según el umbral ===")
    print(resultados["detector_3_sensibilidad"].to_string(index=False))

    print("\n=== Detector 4: contra el GTFS ===")
    print(resultados["detector_4_contra_gtfs"].to_string(index=False))

    print("\n=== LA RESPUESTA: correspondencia de bus por estación ===")
    print(resultados["correspondencia"].to_string(index=False))

    print("\n=== Las estaciones con más servicios de bus a 200 m ===")
    print(resultados["mejores_correspondencias"].to_string(index=False))

    print("\n=== Qué pasa si la coordenada la provee la otra fuente ===")
    print(resultados["sensibilidad_a_la_fuente"].to_string(index=False))

    destino = exportar(resultados)
    print(f"\nTablas escritas en {_ruta_legible(destino)}")


if __name__ == "__main__":
    main()
