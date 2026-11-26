"""P08: ¿a qué distancia está el lugar de carga bip! más cercano de cada parada?

El problema
    Hay 12 497 paradas de embarque en el feed GTFS de la Red Metropolitana de
    Movilidad y 1 927 lugares de carga bip! abiertos en los cinco Excel del DTPM. La
    pregunta es cuántas paradas tienen dónde cargar la tarjeta cerca.

    Es un **cruce sin clave**: no hay ningún campo que relacione una parada con un
    lugar de carga. Hay que inventar el criterio de emparejamiento —la proximidad— y
    con él vienen cuatro decisiones que cambian la respuesta y que normalmente nadie
    declara. Ese es el caso: no el cálculo, sino las decisiones.

Las cuatro decisiones que mueven la respuesta
    1. **Qué fórmula de distancia.** La euclídea sobre grados, escalada con los
       111,32 km/grado del meridiano, es el atajo habitual. A la latitud de Santiago
       **sobreestima** cada distancia: la mediana del error es del +9,4 % y nunca es
       negativo. La cobertura a 300 m cae de 59,29 % a 54,69 % —4,6 puntos— y 574
       paradas cambian de clase. El error es sistemático y de un solo signo, que es
       justamente la firma que distingue un sesgo de un ruido.
    2. **Qué coordenada.** Los Excel traen la misma ubicación dos veces, en UTM y en
       latitud/longitud, y no coinciden: hay un desvío sistemático de ~61 m (hallazgo
       de P01). Usar una u otra deja la cobertura casi igual —59,29 % contra 59,17 %—
       pero cambia **cuál** es el lugar más cercano en 1 657 paradas. El indicador
       agregado es robusto; la asignación individual no lo es, y conviene saberlo
       antes de decirle a alguien a qué local caminar.
    3. **Línea recta o caminata.** Nadie camina en línea recta. Aplicar un factor de
       rodeo de 1,3 baja la cobertura de 59,29 % a 46,02 %: el titular pasa de «seis
       de cada diez paradas» a «menos de la mitad». No existe un valor canónico
       publicado para el factor peatonal, de modo que aquí **no se elige uno**: se
       informa la curva completa y el supuesto queda a la vista.
    4. **Qué paradas entran en el denominador.** El feed incluye el servicio de tren
       Santiago–Rancagua. La Estación Rancagua queda a 40,3 km del lugar de carga más
       cercano, no porque falte cobertura sino porque está fuera del área que
       describen los Excel. 61 paradas superan los 3 km.

Lo que se encontró, y lo que no se puede contestar
    - 59,29 % de las paradas tiene un lugar de carga a 300 m o menos **en línea
      recta**. Con un factor de rodeo de 1,3, el 46,02 %.
    - La mediana de la distancia es 249,6 m; el P90, 671,0 m.
    - El `codigo` de los Excel **no identifica** un lugar: 1 927 filas traen 1 791
      códigos distintos, porque en las estaciones de Metro el código es la línea
      (`L1`, `L5`) y no la estación. El punto más cercano hay que devolverlo por
      posición de fila, no por código.
    - **La segunda mitad de P08 no se puede contestar con estos datos.** Las paradas
      del GTFS no traen comuna, y atribuirle a cada parada la comuna de su lugar de
      carga más cercano falla exactamente donde importa: a las paradas sin cobertura
      les asigna la comuna del local lejano. El sustituto honesto es una rejilla
      geográfica, que no necesita límites administrativos.
    - **Tampoco se puede saber si el local está abierto cuando pasa el pasajero.** El
      `horario referencial` está presente en el 18,06 % de los locales (P01). Toda
      cifra de cobertura de este caso supone disponibilidad permanente, que los datos
      no respaldan.

De dónde sale el umbral de 300 m
    Del manual de diseño de paradas del DTPM (febrero de 2026), que dice textualmente:

        «La ubicación de un punto de parada responde a múltiples parámetros donde el
        distanciamiento entre puntos de parada promedio es de 300 m, que considera un
        tiempo de caminata de 3 a 5 minutos aproximadamente.»

    Es la distancia que el propio organismo asocia a una caminata de 3 a 5 minutos.
    Pero el manual la usa para el **espaciamiento entre paradas**, y no fija ningún
    criterio de distancia a un lugar de carga: el manual no menciona la carga de la
    tarjeta. El traslado es una analogía, declarada como tal, y por eso se informa la
    cobertura a seis umbrales en lugar de uno.

Tecnologías y por qué estas
    - **`lab.geo.nearest_point`**, fuerza bruta por bloques con NumPy: 24 081 719
      pares de distancias en 1,4 s. Con estos tamaños un índice espacial
      (`scipy.spatial.cKDTree`, `GeoPandas.sjoin_nearest`) no se amortiza, y añadir
      SciPy o GeoPandas al entorno por 1,4 s de cálculo no se justifica. Si cualquiera
      de los dos conjuntos creciera un orden de magnitud, la decisión cambia; queda
      declarada para que se revise entonces y no cuando el proceso no termine.
    - **`lab.geo.haversine_km`** y no distancia euclídea, por la razón medida arriba.
    - **Una rejilla de grados en lugar de polígonos de comuna**: responde «qué zonas
      quedan peor» sin incorporar una capa cartográfica nueva, cuya licencia habría
      que verificar y cuyo cruce espacial exigiría GeoPandas.
    - **Reutiliza `cases.bip_lugares_carga`** en lugar de volver a leer los Excel: la
      consolidación, la armonización de esquemas y la validación de coordenadas ya
      están resueltas y probadas en P01. Un caso que depende de otro caso es
      deliberado: así se ve que el trabajo de calidad se amortiza.

Reproducir
    python scripts/fetch_data.py gtfs-red-movilidad
    python scripts/fetch_data.py bip-metro bip-puntos bip-centros-alto-estandar \\
        bip-centros-estandar bip-retail
    python -m cases.cobertura_de_carga.solution

Advertencia de licencia
    El feed del DTPM **no se versiona**: su licencia no está verificada. Los Excel de
    bip! son CC BY-NC 2.0 y tampoco se versionan. Lo que se versiona es este código,
    los registros de procedencia y las tablas de resultado agregadas.
"""

from __future__ import annotations

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

HERE = Path(__file__).resolve().parent
FEED = ROOT / "data" / "original" / "gtfs-red-movilidad.zip"
RESULTS = HERE / "resultados"

#: Cita textual del manual que ancla el umbral. Se guarda en el código para que la
#: cifra no quede como una elección sin respaldo.
CITA_UMBRAL = (
    "«La ubicación de un punto de parada responde a múltiples parámetros donde el "
    "distanciamiento entre puntos de parada promedio es de 300 m, que considera un "
    "tiempo de caminata de 3 a 5 minutos aproximadamente.» "
    "— DTPM, Puntos de Parada: Manual de Diseño, febrero de 2026, p. 36."
)

#: Umbral de referencia, en metros. Es la distancia que el DTPM asocia a 3–5 minutos
#: de caminata. El manual la usa para el espaciamiento entre paradas, no para la
#: distancia a un lugar de carga: el traslado es una analogía.
UMBRAL_M = 300.0

#: Umbrales sobre los que se informa la cobertura. Son seis y no uno porque el umbral
#: es una decisión, y una decisión se audita mostrando la sensibilidad.
UMBRALES_M: tuple[float, ...] = (200.0, 300.0, 400.0, 500.0, 700.0, 1000.0)

#: Factores de rodeo (circuity) sobre los que se informa la sensibilidad. Es la razón
#: entre la distancia caminando y la línea recta. No se fija un valor: la literatura
#: no ofrece una cifra peatonal canónica, y los valores publicados varían por ciudad y
#: por método de medición. 1,0 es la línea recta pura, que es un piso, no una
#: estimación.
FACTORES_RODEO: tuple[float, ...] = (1.0, 1.2, 1.3, 1.4, 1.5)

#: Radio sobre el que se considera que una parada está fuera del área que describen
#: los Excel, y no simplemente mal cubierta. 3 km es diez veces el umbral: holgado
#: frente a una mala cobertura urbana y estricto frente a los 40 km de la Estación
#: Rancagua.
RADIO_DE_ALCANCE_M = 3000.0

#: Lado de la celda de la rejilla, en grados. 0,01° son unos 1,11 km de norte a sur y
#: 0,93 km de este a oeste a la latitud de Santiago: la celda no es cuadrada, y por eso
#: la rejilla sirve para localizar zonas y no para medir superficies.
PASO_REJILLA = 0.01

#: Mínimo de paradas para que una celda entre en el informe. Una celda con tres
#: paradas da porcentajes de 0 % o 100 % que no dicen nada.
MINIMO_POR_CELDA = 20

#: Mínimo de paradas atribuidas para que una fila del proxy de comuna se tome en
#: serio. Por debajo, el porcentaje describe el sesgo del proxy y no la comuna.
MINIMO_ATRIBUIDAS = 10

#: Kilómetros por grado en el meridiano. Es la constante del atajo euclídeo, que se
#: implementa aquí para medir su error, no para usarla.
KM_POR_GRADO = 111.32

#: `location_type` de GTFS que corresponde a un lugar donde sube gente. El campo vacío
#: equivale a 0 según la especificación.
TIPO_DE_EMBARQUE = "0"

#: Significado de `location_type`, tomado de la especificación GTFS estática. El caso
#: `gtfs_red_movilidad` declara el mismo diccionario: no es una duplicación de lógica,
#: son dos casos citando la misma especificación pública. Compartirlo exigiría o bien
#: meter vocabulario de transporte en el núcleo, o bien que un caso importara del otro
#: para leer una constante, y ninguna de las dos mejora nada.
LOCATION_TYPES: dict[str, str] = {
    "0": "parada o andén",
    "1": "estación",
    "2": "acceso o salida",
    "3": "nodo generico de pasillo",
    "4": "área de abordaje",
}


def _ruta_legible(path: Path) -> str:
    """Ruta relativa a la raíz cuando se puede, absoluta cuando no."""
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
def cargar_paradas(feed: Path | None = None) -> pd.DataFrame:
    """Las paradas de embarque del feed, con coordenadas numéricas.

    Filtra por `location_type`: de las 18 486 filas de `stops.txt`, 12 497 son lugares
    donde sube gente. Las otras 5 989 son estaciones, accesos, nodos de pasillo y
    áreas de abordaje. Incluirlas infla el denominador con filas que además no traen
    coordenadas —la especificación solo las exige para los tipos 0, 1 y 2—, de modo
    que aparecerían como paradas sin cobertura cuando no son paradas.

    Returns:
        Tabla con `stop_id`, `stop_name`, `lat` y `lon`, reindexada desde cero.
    """
    archivo = _exigir_feed(feed)
    stops = read_zip_table(
        archivo, "stops.txt", dtype=str,
        usecols=["stop_id", "stop_name", "location_type", "stop_lat", "stop_lon"],
    )
    tipo = stops["location_type"].fillna(TIPO_DE_EMBARQUE)
    paradas = stops[tipo == TIPO_DE_EMBARQUE].copy()
    paradas["lat"] = pd.to_numeric(paradas["stop_lat"], errors="coerce")
    paradas["lon"] = pd.to_numeric(paradas["stop_lon"], errors="coerce")
    return paradas[["stop_id", "stop_name", "lat", "lon"]].reset_index(drop=True)


def informe_de_paradas(feed: Path | None = None) -> pd.DataFrame:
    """Cuántas filas de `stops.txt` entran al denominador y cuántas no, por tipo.

    Es la tabla que justifica el filtro. Sin ella el 12 497 es un número que aparece
    sin explicación, y la diferencia con las 18 486 filas del archivo queda como una
    discrepancia inexplicada para quien revise.
    """
    archivo = _exigir_feed(feed)
    stops = read_zip_table(
        archivo, "stops.txt", dtype=str,
        usecols=["stop_id", "location_type", "stop_lat", "stop_lon"],
    )
    tipo = stops["location_type"].fillna(TIPO_DE_EMBARQUE)
    tiene_coordenada = stops["stop_lat"].notna() & stops["stop_lon"].notna()
    filas = []
    for valor, grupo in tiene_coordenada.groupby(tipo, observed=True):
        filas.append({
            "location_type": valor,
            "significado": LOCATION_TYPES.get(valor, "desconocido"),
            "filas": int(len(grupo)),
            "con_coordenada": int(grupo.sum()),
            "entra_al_denominador": "sí" if valor == TIPO_DE_EMBARQUE else "no",
        })
    return pd.DataFrame(filas).sort_values("location_type").reset_index(drop=True)


def cargar_lugares() -> pd.DataFrame:
    """Los lugares de carga abiertos, consolidados por P01.

    Se queda con `abierto`: la hoja `Cerrados` de los Excel describe un local fuera de
    servicio, que no da cobertura. Es una fila de 1 928, pero excluirla exige haberla
    contado, y contarla es lo que hace P01.

    Returns:
        Tabla con las dos representaciones de la coordenada y los campos descriptivos,
        reindexada desde cero para que la posición de fila sirva de identificador.
    """
    consolidado = bip.consolidar()
    abiertos = consolidado[consolidado["abierto"]].reset_index(drop=True)
    abiertos = abiertos.copy()
    abiertos["lat"] = abiertos["latitud"]
    abiertos["lon"] = abiertos["longitud"]
    return abiertos


def informe_de_identificador(lugares: pd.DataFrame) -> pd.DataFrame:
    """Por qué el punto más cercano se devuelve por posición y no por `codigo`.

    `codigo` parece una llave y no lo es: en las estaciones de Metro vale la línea
    (`L1`, `L5`), de modo que 143 estaciones comparten seis códigos. Pedirle a
    `nearest_point` que devuelva `codigo` produce un resultado que no se puede volver a
    unir con la tabla de lugares, y el error aparece recién al hacer el `map`.
    """
    filas = []
    for tipo, grupo in lugares.groupby("tipo_local", observed=True):
        filas.append({
            "tipo_local": tipo,
            "filas": int(len(grupo)),
            "codigos_distintos": int(grupo["codigo"].nunique(dropna=True)),
            "codigos_repetidos": int(grupo["codigo"].duplicated().sum()),
            "sirve_de_llave": "sí" if grupo["codigo"].is_unique else "no",
        })
    total = {
        "tipo_local": "TOTAL",
        "filas": int(len(lugares)),
        "codigos_distintos": int(lugares["codigo"].nunique(dropna=True)),
        "codigos_repetidos": int(lugares["codigo"].duplicated().sum()),
        "sirve_de_llave": "sí" if lugares["codigo"].is_unique else "no",
    }
    return pd.concat(
        [pd.DataFrame(filas).sort_values("tipo_local"), pd.DataFrame([total])],
        ignore_index=True,
    )


# ----------------------------------------------------------------------- la medición
def medir(
    paradas: pd.DataFrame,
    lugares: pd.DataFrame,
    columna_lat: str = "lat",
    columna_lon: str = "lon",
) -> pd.DataFrame:
    """Distancia en línea recta de cada parada a su lugar de carga más cercano.

    Args:
        paradas: salida de `cargar_paradas`.
        lugares: salida de `cargar_lugares`.
        columna_lat, columna_lon: qué representación de la coordenada del lugar usar.
            `lat`/`lon` son las publicadas; `latitud_utm`/`longitud_utm`, las derivadas
            de las coordenadas UTM del mismo archivo.

    Returns:
        Las paradas con `metros`, `lugar` (posición de fila en `lugares`) y los campos
        descriptivos del lugar más cercano.

    El identificador es la **posición de fila**, no `codigo`: ver
    `informe_de_identificador`.
    """
    cercano = nearest_point(
        paradas, lugares,
        lat_origen="lat", lon_origen="lon",
        lat_destino=columna_lat, lon_destino=columna_lon,
    )
    salida = paradas.copy()
    salida["metros"] = cercano["distancia_km"] * 1000
    salida["lugar"] = cercano["destino_mas_cercano"]
    for campo, destino in (
        ("tipo_local", "tipo_lugar"),
        ("nombre", "nombre_lugar"),
        ("comuna_etiqueta", "comuna_lugar"),
        ("horario", "horario_lugar"),
    ):
        salida[destino] = salida["lugar"].map(lugares[campo])
    return salida


def distribucion(medidas: pd.DataFrame) -> pd.DataFrame:
    """Percentiles de la distancia, en metros.

    Se informa la distribución y no solo la media porque la cola es larga: la media
    (363,5 m) está por encima del percentil 60, arrastrada por las paradas que están a
    kilómetros. Un promedio, aquí, describe mal a casi todas las paradas.
    """
    metros = medidas["metros"].dropna()
    filas = [{"estadistico": "paradas medidas", "metros": float(len(metros))}]
    for cuantil in (0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99):
        filas.append({
            "estadistico": f"P{int(cuantil * 100)}",
            "metros": round(float(metros.quantile(cuantil)), 1),
        })
    filas.append({"estadistico": "media", "metros": round(float(metros.mean()), 1)})
    filas.append({"estadistico": "máximo", "metros": round(float(metros.max()), 1)})
    return pd.DataFrame(filas)


def cobertura_por_umbral(
    medidas: pd.DataFrame, umbrales: tuple[float, ...] = UMBRALES_M
) -> pd.DataFrame:
    """Qué proporción de las paradas queda bajo cada umbral.

    La curva completa en lugar de una cifra: entre 200 m y 500 m la cobertura va de
    39,60 % a 81,84 %, de modo que el titular depende más del umbral elegido que de
    los datos.
    """
    metros = medidas["metros"]
    total = int(metros.notna().sum())
    filas = []
    for umbral in umbrales:
        bajo = int((metros <= umbral).sum())
        filas.append({
            "umbral_m": umbral,
            "paradas_cubiertas": bajo,
            "paradas_medidas": total,
            "cobertura_pct": round(float(safe_ratio(bajo, total) * 100), 2),
            "es_referencia": "sí" if umbral == UMBRAL_M else "no",
        })
    return pd.DataFrame(filas)


def sensibilidad_rodeo(
    medidas: pd.DataFrame,
    umbral: float = UMBRAL_M,
    factores: tuple[float, ...] = FACTORES_RODEO,
) -> pd.DataFrame:
    """Cobertura al umbral, para cada factor de rodeo.

    El factor de rodeo convierte la línea recta en una caminata estimada. No se elige
    un valor: se muestra la curva, porque el supuesto es de quien lee el indicador y
    no de quien lo calcula. El rango importa: entre 1,0 y 1,5 la cobertura a 300 m va
    de 59,29 % a 39,60 %, casi veinte puntos.
    """
    metros = medidas["metros"]
    total = int(metros.notna().sum())
    base = None
    filas = []
    for factor in factores:
        bajo = int((metros * factor <= umbral).sum())
        pct = float(safe_ratio(bajo, total) * 100)
        if base is None:
            base = pct
        filas.append({
            "factor_rodeo": factor,
            "umbral_m": umbral,
            "paradas_cubiertas": bajo,
            "cobertura_pct": round(pct, 2),
            "puntos_vs_linea_recta": round(pct - base, 2),
        })
    return pd.DataFrame(filas)


# ------------------------------------------------------- validación de las decisiones
def comparar_formulas(paradas: pd.DataFrame, lugares: pd.DataFrame) -> pd.DataFrame:
    """Haversine contra euclídea sobre grados: el sesgo del atajo.

    La euclídea sobre grados trata un grado de longitud y uno de latitud como la misma
    distancia. A −33,45° no lo son: un grado de latitud son 111,2 km y uno de longitud
    92,8 km. Escalar con los 111,32 km/grado del meridiano estira la componente
    este-oeste en un 20 %, de modo que toda distancia sale **de más**.

    Lo que se mide aquí no es el error medio —que es pequeño en metros— sino cuántas
    paradas **cambian de clase** y cuántas cambian de lugar más cercano, que es lo que
    le llega a quien usa el resultado.
    """
    lat_o = paradas["lat"].to_numpy()[:, None]
    lon_o = paradas["lon"].to_numpy()[:, None]
    lat_d = lugares["lat"].to_numpy()[None, :]
    lon_d = lugares["lon"].to_numpy()[None, :]

    haver = np.asarray(haversine_km(lat_o, lon_o, lat_d, lon_d)) * 1000
    euclid = np.sqrt((lat_o - lat_d) ** 2 + (lon_o - lon_d) ** 2) * KM_POR_GRADO * 1000

    m_haver, i_haver = haver.min(axis=1), haver.argmin(axis=1)
    m_euclid, i_euclid = euclid.min(axis=1), euclid.argmin(axis=1)
    error = m_euclid - m_haver
    total = len(paradas)
    cubierta_haver = m_haver <= UMBRAL_M
    cubierta_euclid = m_euclid <= UMBRAL_M

    return indicator_table({
        "paradas_medidas": (total, "paradas", "Paradas de embarque con coordenada"),
        "error_mediano_m": (
            round(float(np.median(error)), 1), "m",
            "Distancia euclídea menos haversine, mediana sobre las paradas"),
        "error_mediano_pct": (
            round(float(np.median(error / m_haver) * 100), 2), "%",
            "El mismo error, relativo a la distancia correcta"),
        "errores_negativos": (
            int((error < -1e-9).sum()), "paradas",
            "Paradas donde la euclídea subestima. Cero confirma que el sesgo "
            "es sistemático y de un solo signo, no ruido"),
        "cobertura_haversine_pct": (
            round(float(cubierta_haver.mean() * 100), 2), "%",
            f"Paradas a {UMBRAL_M:.0f} m o menos, con la fórmula correcta"),
        "cobertura_euclidea_pct": (
            round(float(cubierta_euclid.mean() * 100), 2), "%",
            f"Paradas a {UMBRAL_M:.0f} m o menos, con el atajo"),
        "cambian_de_clase": (
            int((cubierta_haver != cubierta_euclid).sum()), "paradas",
            "Paradas que pasan de cubiertas a no cubiertas, o al revés"),
        "cambian_de_lugar": (
            int((i_haver != i_euclid).sum()), "paradas",
            "Paradas a las que el atajo asigna otro local como el más cercano"),
    })


def comparar_representaciones(
    paradas: pd.DataFrame, lugares: pd.DataFrame
) -> pd.DataFrame:
    """La coordenada publicada contra la derivada de UTM: qué cambia al elegir.

    Los Excel traen la ubicación dos veces y no coinciden. P01 midió el desvío; aquí se
    mide su **consecuencia**: el indicador agregado casi no se mueve, pero la respuesta
    por parada sí. Es la distinción que decide para qué sirve el resultado: publicar la
    cobertura, sí; decirle a una persona a qué local caminar, no sin resolver antes
    cuál de las dos coordenadas es la buena.
    """
    publicada = medir(paradas, lugares, "lat", "lon")
    desde_utm = medir(paradas, lugares, "latitud_utm", "longitud_utm")
    diferencia = (desde_utm["metros"] - publicada["metros"]).abs()
    cubierta_pub = publicada["metros"] <= UMBRAL_M
    cubierta_utm = desde_utm["metros"] <= UMBRAL_M

    return indicator_table({
        "cobertura_publicada_pct": (
            round(float(cubierta_pub.mean() * 100), 2), "%",
            f"Paradas a {UMBRAL_M:.0f} m usando la latitud y longitud publicadas"),
        "cobertura_desde_utm_pct": (
            round(float(cubierta_utm.mean() * 100), 2), "%",
            "La misma cifra usando la coordenada derivada del este y norte UTM"),
        "cambian_de_clase": (
            int((cubierta_pub != cubierta_utm).sum()), "paradas",
            "Paradas que cambian de cubiertas a no cubiertas al cambiar de "
            "representación. El agregado se mueve poco; estas paradas, sí"),
        "cambian_de_lugar": (
            int((publicada["lugar"] != desde_utm["lugar"]).sum()), "paradas",
            "Paradas a las que la otra representación asigna otro local"),
        "diferencia_mediana_m": (
            round(float(diferencia.median()), 2), "m",
            "Diferencia absoluta entre las dos distancias, mediana"),
        "diferencia_maxima_m": (
            round(float(diferencia.max()), 1), "m",
            "El peor caso, que son los locales de coordenada contradictoria"),
        "locales_sospechosos": (
            int(lugares["coordenada_sospechosa"].sum()), "locales",
            f"Locales cuyas dos coordenadas difieren más de "
            f"{bip.UMBRAL_COORDENADA_M:.0f} m (hallazgo de P01)"),
    })


def paradas_fuera_de_alcance(
    medidas: pd.DataFrame, radio: float = RADIO_DE_ALCANCE_M
) -> pd.DataFrame:
    """Las paradas que superan el radio de alcance, nombradas una por una.

    No se descartan en silencio: se listan, porque la decisión de excluirlas pertenece
    a quien lee el indicador. Entre ellas están las estaciones del tren a Rancagua,
    que están lejos porque el feed cubre un territorio mayor que los Excel, y los
    niveles del aeropuerto, que están lejos porque un terminal aéreo no es un barrio.
    """
    lejanas = medidas[medidas["metros"] > radio].copy()
    lejanas = lejanas.sort_values("metros", ascending=False)
    columnas = ["stop_id", "stop_name", "metros", "nombre_lugar", "comuna_lugar"]
    salida = lejanas[columnas].copy()
    salida["metros"] = salida["metros"].round(1)
    return salida.reset_index(drop=True)


def resumen_con_y_sin_lejanas(
    medidas: pd.DataFrame,
    radio: float = RADIO_DE_ALCANCE_M,
    umbral: float = UMBRAL_M,
) -> pd.DataFrame:
    """La cobertura con el denominador completo y sin las paradas fuera de alcance.

    Las dos cifras, porque el denominador es una decisión. Aquí la decisión resulta ser
    casi inocua —las 61 paradas lejanas son el 0,49 % del total—, y eso también es un
    resultado: mostrar que una exclusión no cambia nada vale tanto como mostrar que sí.
    """
    metros = medidas["metros"]
    dentro = metros <= radio
    filas = []
    for etiqueta, seleccion in (
        ("denominador completo", pd.Series(True, index=metros.index)),
        (f"sin paradas a más de {radio / 1000:.0f} km", dentro),
    ):
        sub = metros[seleccion]
        filas.append({
            "denominador": etiqueta,
            "paradas": int(len(sub)),
            "cubiertas": int((sub <= umbral).sum()),
            "cobertura_pct": round(float(safe_ratio((sub <= umbral).sum(), len(sub)) * 100), 2),
        })
    return pd.DataFrame(filas)


# -------------------------------------------------------------------- desagregaciones
def por_tipo_de_lugar(medidas: pd.DataFrame, lugares: pd.DataFrame) -> pd.DataFrame:
    """Qué tipo de local provee la cobertura, y con qué calidad.

    Importa porque los tipos no son equivalentes. 143 estaciones de Metro son el local
    más cercano de 1 344 paradas con la mediana más baja (180,6 m), mientras 1 579
    puntos bip! cubren 9 710 paradas. Y el retail, que cubre 1 116, es el de peor
    mediana (289,8 m) y el que más depende del horario comercial, que es justamente el
    campo que los datos casi no traen.
    """
    por_tipo = medidas.groupby("tipo_lugar", observed=True)
    tabla = por_tipo.agg(
        paradas=("stop_id", "size"),
        cubiertas=("metros", lambda s: int((s <= UMBRAL_M).sum())),
        mediana_m=("metros", "median"),
        p90_m=("metros", lambda s: s.quantile(0.90)),
    )
    tabla["cobertura_pct"] = (tabla["cubiertas"] / tabla["paradas"] * 100).round(2)
    tabla["locales"] = lugares.groupby("tipo_local", observed=True).size()
    tabla["paradas_por_local"] = (tabla["paradas"] / tabla["locales"]).round(1)
    tabla["mediana_m"] = tabla["mediana_m"].round(1)
    tabla["p90_m"] = tabla["p90_m"].round(1)
    return tabla.reset_index().rename(columns={"tipo_lugar": "tipo_local"})


def por_rejilla(
    medidas: pd.DataFrame,
    paso: float = PASO_REJILLA,
    minimo: int = MINIMO_POR_CELDA,
) -> pd.DataFrame:
    """Cobertura por celda de rejilla, con las celdas peores primero.

    Es el sustituto de la desagregación por comuna, que estos datos no permiten. La
    rejilla no necesita límites administrativos: se deriva de las propias coordenadas.
    A cambio, una celda no es una unidad con la que nadie gobierne, de modo que la
    tabla sirve para localizar zonas y no para asignar responsabilidades.

    Se nombra la parada más lejana de cada celda para que la celda se pueda reconocer
    sin un mapa.
    """
    rejilla = medidas.dropna(subset=["metros", "lat", "lon"]).copy()
    rejilla["celda_lat"] = np.floor(rejilla["lat"] / paso) * paso
    rejilla["celda_lon"] = np.floor(rejilla["lon"] / paso) * paso
    grupos = rejilla.groupby(["celda_lat", "celda_lon"], observed=True)
    tabla = grupos.agg(
        paradas=("stop_id", "size"),
        cubiertas=("metros", lambda s: int((s <= UMBRAL_M).sum())),
        mediana_m=("metros", "median"),
    )
    tabla["parada_mas_lejana"] = rejilla.loc[
        grupos["metros"].idxmax(), "stop_name"
    ].to_numpy()
    tabla = tabla[tabla["paradas"] >= minimo].copy()
    tabla["cobertura_pct"] = (tabla["cubiertas"] / tabla["paradas"] * 100).round(1)
    tabla["mediana_m"] = tabla["mediana_m"].round(1)
    tabla = tabla.reset_index().round({"celda_lat": 2, "celda_lon": 2})
    return tabla.sort_values(["cobertura_pct", "mediana_m"], ascending=[True, False]).reset_index(drop=True)


def sesgo_del_proxy_de_comuna(medidas: pd.DataFrame, lugares: pd.DataFrame) -> pd.DataFrame:
    """Mide por qué **no** se publica la cobertura por comuna.

    La única comuna disponible para una parada es la del lugar de carga más cercano, y
    ese proxy está sesgado por construcción: a una parada sin cobertura se le atribuye
    la comuna del local lejano, que es precisamente la comuna equivocada. El sesgo es
    peor donde el indicador sería más interesante.

    La tabla lo cuantifica. Las comunas con tres o cinco paradas atribuidas y 0 % de
    cobertura son el artefacto: no son comunas con mala cobertura, son comunas que
    recibieron paradas que no les pertenecen.
    """
    proxy = medidas.groupby("comuna_lugar", observed=True).agg(
        paradas_atribuidas=("stop_id", "size"),
        cubiertas=("metros", lambda s: int((s <= UMBRAL_M).sum())),
        mediana_m=("metros", "median"),
    )
    proxy["cobertura_pct"] = (proxy["cubiertas"] / proxy["paradas_atribuidas"] * 100).round(1)
    proxy["mediana_m"] = proxy["mediana_m"].round(1)
    proxy["locales_en_la_comuna"] = lugares.groupby("comuna_etiqueta", observed=True).size()
    proxy["es_artefacto"] = np.where(
        proxy["paradas_atribuidas"] < MINIMO_ATRIBUIDAS, "probable", "no"
    )
    proxy = proxy.sort_values(["cobertura_pct", "paradas_atribuidas"])
    return proxy.reset_index().rename(
        columns={"comuna_lugar": "comuna_del_lugar_cercano"}
    )


def limite_por_horario(medidas: pd.DataFrame) -> pd.DataFrame:
    """Para cuántas paradas se sabe si el local más cercano está abierto.

    Toda cifra de cobertura de este caso supone que el local está disponible. El campo
    `horario referencial` está en el 18,06 % de los locales (P01), de modo que para la
    gran mayoría de las paradas el supuesto no se puede verificar. No es un detalle: un
    local de retail cerrado a las 23:00 no da cobertura a quien necesita cargar a esa
    hora, y el dato para distinguirlo no está.
    """
    con_horario = medidas["horario_lugar"].notna() & (
        medidas["horario_lugar"].astype("string").str.strip() != ""
    )
    cubiertas = medidas["metros"] <= UMBRAL_M
    return indicator_table({
        "paradas_medidas": (int(len(medidas)), "paradas", "Paradas de embarque"),
        "con_horario_conocido": (
            int(con_horario.sum()), "paradas",
            "Paradas cuyo local más cercano declara horario referencial"),
        "con_horario_conocido_pct": (
            round(float(safe_ratio(con_horario.sum(), len(medidas), scale=100)), 2), "%",
            "La misma cifra como proporción del total"),
        "cubiertas_con_horario": (
            int((cubiertas & con_horario).sum()), "paradas",
            f"Cubiertas a {UMBRAL_M:.0f} m y se sabe cuándo abre el local"),
        "cubiertas_sin_horario": (
            int((cubiertas & ~con_horario).sum()), "paradas",
            f"Cubiertas a {UMBRAL_M:.0f} m pero no se sabe si está abierto. "
            "La cobertura de estas paradas es un supuesto, no un dato"),
    })


def resumen(medidas: pd.DataFrame, lugares: pd.DataFrame) -> pd.DataFrame:
    """Las cifras del caso, con el supuesto declarado junto a cada una."""
    metros = medidas["metros"]
    return indicator_table({
        "paradas_de_embarque": (
            int(len(medidas)), "paradas",
            "Filas de stops.txt con location_type 0: donde sube gente"),
        "lugares_abiertos": (
            int(len(lugares)), "locales",
            "Lugares de carga bip! en servicio, consolidados por P01"),
        "pares_calculados": (
            int(len(medidas) * len(lugares)), "pares",
            "Distancias evaluadas por la búsqueda por fuerza bruta"),
        "mediana_m": (
            round(float(metros.median()), 1), "m",
            "Distancia en línea recta al local más cercano, mediana"),
        "p90_m": (
            round(float(metros.quantile(0.90)), 1), "m",
            "Nueve de cada diez paradas están a esta distancia o menos"),
        "cobertura_linea_recta_pct": (
            round(float((metros <= UMBRAL_M).mean() * 100), 2), "%",
            f"Paradas a {UMBRAL_M:.0f} m o menos en línea recta. Es un piso: "
            "nadie camina en línea recta"),
        "cobertura_rodeo_13_pct": (
            round(float((metros * 1.3 <= UMBRAL_M).mean() * 100), 2), "%",
            "La misma cifra suponiendo que caminar cuesta 1,3 veces la línea "
            "recta. El factor es un supuesto declarado, no un dato"),
        "paradas_fuera_de_alcance": (
            int((metros > RADIO_DE_ALCANCE_M).sum()), "paradas",
            f"Paradas a más de {RADIO_DE_ALCANCE_M / 1000:.0f} km, que están "
            "fuera del área que describen los Excel"),
    })


# ---------------------------------------------------------------------------- informe
def analizar(feed: Path | None = None) -> dict[str, pd.DataFrame]:
    """Ejecuta el caso completo y devuelve todas las tablas de resultado."""
    paradas = cargar_paradas(feed)
    lugares = cargar_lugares()
    medidas = medir(paradas, lugares)
    return {
        "resumen": resumen(medidas, lugares),
        "paradas_por_tipo": informe_de_paradas(feed),
        "identificador": informe_de_identificador(lugares),
        "distribucion": distribucion(medidas),
        "cobertura_por_umbral": cobertura_por_umbral(medidas),
        "sensibilidad_rodeo": sensibilidad_rodeo(medidas),
        "formulas_comparadas": comparar_formulas(paradas, lugares),
        "representaciones_comparadas": comparar_representaciones(paradas, lugares),
        "denominador": resumen_con_y_sin_lejanas(medidas),
        "fuera_de_alcance": paradas_fuera_de_alcance(medidas),
        "por_tipo_de_lugar": por_tipo_de_lugar(medidas, lugares),
        "por_rejilla": por_rejilla(medidas),
        "proxy_de_comuna": sesgo_del_proxy_de_comuna(medidas, lugares),
        "limite_por_horario": limite_por_horario(medidas),
    }


def exportar(resultados: dict[str, pd.DataFrame], destino: Path = RESULTS) -> Path:
    """Escribe las tablas de resultado en CSV.

    Son agregados, no datos de terceros: se versionan sin redistribuir ni el feed ni
    los Excel, de modo que los hallazgos quedan visibles sin descargar nada.
    """
    destino.mkdir(parents=True, exist_ok=True)
    for nombre, tabla in resultados.items():
        tabla.to_csv(destino / f"{nombre}.csv", index=False, encoding="utf-8")
    return destino


def main() -> None:
    from lab.console import enable_utf8

    enable_utf8()
    archivo = _exigir_feed()
    try:
        print(f"Fuente del feed: {Provenance.from_path(archivo).summary()}")
    except FileNotFoundError:
        print("Aviso: el feed no tiene registro de procedencia.")
    print(f"Umbral: {UMBRAL_M:.0f} m. {CITA_UMBRAL}\n")

    resultados = analizar(archivo)

    print("=== Resumen ===")
    print(resultados["resumen"].to_string(index=False))

    print("\n=== Qué filas de stops.txt entran al denominador ===")
    print(resultados["paradas_por_tipo"].to_string(index=False))

    print("\n=== El código no sirve de llave ===")
    print(resultados["identificador"].to_string(index=False))

    print("\n=== Distribución de la distancia ===")
    print(resultados["distribucion"].to_string(index=False))

    print("\n=== Cobertura por umbral ===")
    print(resultados["cobertura_por_umbral"].to_string(index=False))

    print("\n=== Sensibilidad al factor de rodeo ===")
    print(resultados["sensibilidad_rodeo"].to_string(index=False))

    print("\n=== Haversine contra euclídea sobre grados ===")
    print(resultados["formulas_comparadas"].to_string(index=False))

    print("\n=== Coordenada publicada contra derivada de UTM ===")
    print(resultados["representaciones_comparadas"].to_string(index=False))

    print("\n=== El denominador es una decisión ===")
    print(resultados["denominador"].to_string(index=False))

    print("\n=== Tipo de local que provee la cobertura ===")
    print(resultados["por_tipo_de_lugar"].to_string(index=False))

    print("\n=== Las diez celdas con peor cobertura ===")
    print(resultados["por_rejilla"].head(10).to_string(index=False))

    print("\n=== Por qué no se publica la cobertura por comuna ===")
    print(resultados["proxy_de_comuna"].head(8).to_string(index=False))

    print("\n=== Lo que no se puede saber: si el local está abierto ===")
    print(resultados["limite_por_horario"].to_string(index=False))

    destino = exportar(resultados)
    print(f"\nTablas escritas en {_ruta_legible(destino)}")


if __name__ == "__main__":
    main()
