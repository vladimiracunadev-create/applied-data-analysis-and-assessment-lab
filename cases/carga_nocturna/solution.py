"""P09: donde hay servicio de buses de madrugada, ¿hay dónde cargar la tarjeta?

El problema
    Entre las 00:00 y las 05:00 la Red Metropolitana de Movilidad tiene servicio real:
    **367 251 llegadas de bus** repartidas en **10 520 paradas**, que son el 84,2 % de
    las paradas de embarque de la red. La parada mediana recibe 23 llegadas en esas
    cinco horas, una cada trece minutos. No es un servicio marginal.

    Para subir hay que llevar saldo. La pregunta es si hay dónde cargarlo.

La respuesta
    **Cero.** Ninguna de las 10 520 paradas con servicio nocturno tiene, a 300 m o
    menos, un lugar de carga que **declare** estar abierto en esa ventana. Ni una.

    Pero esa cifra sola miente por omisión, y el reparto es lo que importa:

    | Situación de la parada | Paradas | % |
    | --- | --- | --- |
    | Con carga abierta verificada | **0** | 0,0 % |
    | Sin ningún local a 300 m | 4 225 | 40,2 % |
    | Con locales cerca, todos con horario conocido, ninguno abierto | 759 | 7,2 % |
    | **Indeterminado**: hay locales cerca sin horario declarado | **5 536** | **52,6 %** |

    De modo que la respuesta honesta no es un número, es un **intervalo**: la cobertura
    de carga nocturna está entre **0,0 % y 52,6 %**, y el ancho de ese intervalo —52,6
    puntos— no lo produce la red ni la geografía. Lo produce una columna vacía.

El hallazgo de gobernanza, que es el verdadero resultado
    El campo `horario referencial` está completo al 100 % en cuatro de los cinco
    archivos y al 0 % en el quinto:

    | Tipo de local | Locales | Con horario |
    | --- | --- | --- |
    | Estación de Metro | 143 | 100 % |
    | Retail | 169 | 100 % |
    | Centro bip! estándar | 29 | 100 % |
    | Centro bip! alto estándar | 7 | 100 % |
    | **Punto bip!** | **1 579** | **0 %** |

    Eso no es ruido de calidad de datos: es una **decisión de publicación** sobre un
    archivo, y tiene una consecuencia medible. De los 1 579 locales sin horario,
    **1 546 están a menos de 300 m de una parada con servicio nocturno**. Completar
    esos 1 546 registros —el 97,9 % de los que faltan— vuelve contestable el 52,6 % de
    la red nocturna. Es el pedido concreto que este caso le hace al publicador, con la
    cifra que lo justifica.

La trampa técnica, que habría dado una respuesta plausible y falsa
    Filtrar `arrival_time` entre `00:00:00` y `04:59:59` devuelve **851 773 filas** y
    **12 201 paradas**: casi toda la red. Y las 851 773 son, el 100 % de ellas, de
    expediciones de frecuencia, cuyo `stop_times` no contiene horas de reloj sino
    **desplazamientos desde el inicio del viaje**, que empiezan todos en `0:00:00`.

    Lo peligroso es que 12 201 no es un número absurdo: el valor correcto es 10 520.
    El atajo sobreestima apenas un 16 %, de modo que nada en el resultado grita que
    está mal. Un error que produce una cifra inverosímil se corrige; uno que produce
    una cifra verosímil se publica.

    El cálculo correcto tiene dos partes que el atajo no tiene:

    1. **Expandir las ventanas de frecuencia** y sumar el desplazamiento de cada parada:
       la llegada real es `inicio_de_ventana + k·intervalo + desplazamiento`.
    2. **Mirar dos intervalos de segundos de servicio, no uno.** Las 00:00–05:00 de
       reloj son `[0 s, 18 000 s)` y también `[86 400 s, 104 400 s)`, porque un bus que
       sale a las 23:40 llega a sus paradas finales pasada la medianoche. **1 490
       paradas** tienen servicio nocturno únicamente por esa segunda vía.

Tecnologías y por qué estas
    - **`lab.schedules`**, escrito para este caso: interpreta el horario en texto libre
      y respeta la regla que gobierna todo el resultado —lo que no se entiende es
      **desconocido**, nunca «cerrado»—. De ahí que `is_open` tenga tres respuestas.
      Sobre el archivo real interpreta los 348 valores con horario, que son solo **10
      textos distintos**.
    - **Intersección de progresión aritmética con intervalo**, en lugar de expandir las
      142 366 salidas y unirlas a 1,1 millones de filas de `stop_times`. Las llegadas
      de una ventana forman la progresión `primero + k·intervalo`; contar cuántas caen
      en `[a, b)` son dos techos y una resta. Es exacto y evita materializar una tabla
      de cientos de millones de filas.
    - **`lab.geo.haversine_km` por bloques** para el radio de 300 m, con el criterio y
      el umbral heredados de P08.
    - **Reutiliza `cases.cobertura_de_carga` y `cases.gtfs_red_movilidad`**, declarado
      en `case.json`. Este caso es la intersección de los dos: sin la consolidación de
      locales y sin la expansión de frecuencias no hay nada que cruzar.

Reproducir
    python scripts/fetch_data.py gtfs-red-movilidad bip-metro bip-puntos \\
        bip-centros-alto-estandar bip-centros-estandar bip-retail
    python -m cases.carga_nocturna.solution

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

from cases.cobertura_de_carga import solution as cobertura  # noqa: E402
from lab.dates import parse_hms_seconds  # noqa: E402
from lab.geo import haversine_km  # noqa: E402
from lab.metrics import indicator_table, safe_ratio  # noqa: E402
from lab.schedules import SEGUNDOS_POR_DIA, covers_window, parse_report, parse_series  # noqa: E402
from lab.sources import Provenance, read_zip_table  # noqa: E402

HERE = Path(__file__).resolve().parent
FEED = ROOT / "data" / "original" / "gtfs-red-movilidad.zip"
RESULTS = HERE / "resultados"

#: La ventana nocturna, en segundos desde la medianoche. `[00:00, 05:00)`.
#: El fin es exclusivo, igual que en el resto del laboratorio: una llegada a las
#: 05:00:00 en punto pertenece a la mañana.
NOCHE_INICIO = 0
NOCHE_FIN = 5 * 3600

#: Radio de cobertura, heredado de P08 con su misma advertencia: los 300 m vienen por
#: analogía del espaciamiento entre paradas del manual del DTPM, que no fija ningún
#: criterio de distancia a un lugar de carga.
RADIO_M = cobertura.UMBRAL_M

#: Llegadas nocturnas por debajo de las cuales el servicio es testimonial: una por hora
#: o menos en la ventana de cinco horas. No cambia ninguna cifra de cobertura; sirve
#: para no tratar igual una parada con un bus cada trece minutos y una con uno solo.
UMBRAL_SERVICIO_TESTIMONIAL = 5

#: Días de la semana que cubre cada `service_id` del feed, lunes 0 a domingo 6. El feed
#: declara seis servicios; solo estos tres traen ventanas de frecuencia, que es de
#: donde sale todo el servicio nocturno.
DIAS_POR_SERVICIO: dict[str, tuple[int, ...]] = {
    "L": (0, 1, 2, 3, 4),
    "S": (5,),
    "D": (6,),
    "LJ": (0, 1, 2, 3),
    "V": (4,),
    "F": (6,),
}

#: Bloque de paradas por iteración en la búsqueda de locales cercanos. Controla la
#: memoria: el cálculo es una matriz de `bloque × locales` distancias.
BLOQUE = 400

#: Las cuatro situaciones en que puede estar una parada nocturna. El orden es el del
#: informe: primero la que importa, última la que no se sabe.
CLASE_ABIERTA = "con carga abierta verificada"
CLASE_SIN_LOCAL = "sin local a 300 m"
CLASE_CERRADA = "sin carga abierta (verificado)"
CLASE_INDETERMINADA = "indeterminado: local cercano sin horario"
CLASES = (CLASE_ABIERTA, CLASE_SIN_LOCAL, CLASE_CERRADA, CLASE_INDETERMINADA)


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


# --------------------------------------------------------------- el lado del tiempo
def cargar_servicio(feed: Path | None = None) -> dict[str, pd.DataFrame]:
    """Lee del ZIP solo lo necesario para ubicar el servicio en el tiempo.

    No usa `cases.gtfs_red_movilidad.cargar` porque este caso necesita `service_id` en
    las ventanas y no necesita `routes` ni `agency`. Leer menos de una tabla de 1,1
    millones de filas es la diferencia entre segundos y decenas de segundos.
    """
    archivo = _exigir_feed(feed)
    return {
        "frequencies": read_zip_table(archivo, "frequencies.txt", dtype=str),
        "trips": read_zip_table(archivo, "trips.txt", dtype=str,
                                usecols=["trip_id", "service_id"]),
        "stop_times": read_zip_table(archivo, "stop_times.txt", dtype=str,
                                     usecols=["trip_id", "stop_id", "arrival_time"]),
    }


def ventanas_de_frecuencia(tablas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Las ventanas de `frequencies.txt` con su cuenta de salidas y su servicio.

    `end_time` es **exclusivo** según la especificación GTFS: la salida de `end_time`
    pertenece a la ventana siguiente. Las ventanas inválidas —sin intervalo, con fin
    antes del inicio— se excluyen, pero quedan contadas en `informe_de_ventanas`.
    """
    frecuencias = tablas["frequencies"].copy()
    frecuencias["inicio_s"] = parse_hms_seconds(frecuencias["start_time"])
    frecuencias["fin_s"] = parse_hms_seconds(frecuencias["end_time"])
    frecuencias["intervalo_s"] = pd.to_numeric(frecuencias["headway_secs"], errors="coerce")
    frecuencias["valida"] = (
        frecuencias[["inicio_s", "fin_s", "intervalo_s"]].notna().all(axis=1)
        & frecuencias["intervalo_s"].gt(0)
        & frecuencias["fin_s"].gt(frecuencias["inicio_s"])
    )
    utiles = frecuencias.loc[frecuencias["valida"]].copy()
    utiles["salidas"] = (
        (utiles["fin_s"] - utiles["inicio_s"]) // utiles["intervalo_s"]
    ).astype(int)
    utiles = utiles.loc[utiles["salidas"].gt(0)]
    return utiles.merge(tablas["trips"], on="trip_id", how="left")


def informe_de_ventanas(tablas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Qué servicios traen ventanas de frecuencia y cuáles alcanzan la madrugada.

    Es la tabla que muestra de dónde sale el servicio nocturno. Sin ella, el 10 520 de
    más abajo aparece sin explicación.
    """
    ventanas = ventanas_de_frecuencia(tablas)
    filas = []
    for servicio, grupo in ventanas.groupby("service_id", observed=True):
        nocturnas = grupo.loc[grupo["inicio_s"].lt(NOCHE_FIN)]
        filas.append({
            "service_id": servicio,
            "dias_de_la_semana": len(DIAS_POR_SERVICIO.get(servicio, ())),
            "ventanas": int(len(grupo)),
            "salidas": int(grupo["salidas"].sum()),
            "ventanas_que_empiezan_antes_de_las_5": int(len(nocturnas)),
            "ventanas_que_terminan_a_las_24": int(grupo["fin_s"].ge(SEGUNDOS_POR_DIA).sum()),
            "intervalo_mediano_nocturno_min": round(
                float(nocturnas["intervalo_s"].median() / 60), 1
            ) if len(nocturnas) else float("nan"),
        })
    return pd.DataFrame(filas).sort_values("service_id").reset_index(drop=True)


def _llegadas_en(primero: np.ndarray, intervalo: np.ndarray, salidas: np.ndarray,
                 desde: float, hasta: float) -> np.ndarray:
    """Cuántos términos de `primero + k·intervalo`, con `k` en `[0, salidas)`, caen en `[desde, hasta)`.

    Es la operación que permite no expandir nada. Las llegadas de una ventana a una
    parada forman una progresión aritmética; contar cuántas caen en un intervalo son
    dos techos acotados y una resta.

    Expandir sería lo natural y aquí no cabe: 142 366 salidas unidas a las paradas de
    su recorrido producen cientos de millones de filas para responder una pregunta de
    sí o no por parada.
    """
    k_desde = np.clip(np.ceil((desde - primero) / intervalo), 0, salidas)
    k_hasta = np.clip(np.ceil((hasta - primero) / intervalo), 0, salidas)
    return np.maximum(k_hasta - k_desde, 0)


def llegadas_nocturnas(tablas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Llegadas de bus en `[00:00, 05:00)` por parada y por servicio.

    La llegada real de la salida `k` de una ventana a una parada es
    `inicio_de_ventana + k·intervalo + desplazamiento_de_la_parada`.

    Se cuentan **dos** intervalos de segundos de servicio, porque los dos son las
    00:00–05:00 del reloj: `[0, 18 000)` y `[86 400, 104 400)`. El segundo recoge los
    buses que salen antes de medianoche y llegan después, que es servicio nocturno
    real y lo que un filtro por texto pierde.

    Returns:
        Una fila por `(stop_id, service_id)` con las llegadas, más la columna
        `tras_medianoche` que dice cuántas vienen del segundo intervalo.
    """
    ventanas = ventanas_de_frecuencia(tablas)
    paradas = tablas["stop_times"].copy()
    paradas["desplazamiento_s"] = parse_hms_seconds(paradas["arrival_time"])

    pares = paradas[["trip_id", "stop_id", "desplazamiento_s"]].merge(
        ventanas[["trip_id", "service_id", "inicio_s", "intervalo_s", "salidas"]],
        on="trip_id", how="inner",
    )
    primero = (pares["inicio_s"] + pares["desplazamiento_s"]).to_numpy(dtype=float)
    intervalo = pares["intervalo_s"].to_numpy(dtype=float)
    salidas = pares["salidas"].to_numpy(dtype=float)

    antes = _llegadas_en(primero, intervalo, salidas, NOCHE_INICIO, NOCHE_FIN)
    despues = _llegadas_en(
        primero, intervalo, salidas,
        SEGUNDOS_POR_DIA + NOCHE_INICIO, SEGUNDOS_POR_DIA + NOCHE_FIN,
    )
    pares["llegadas"] = antes + despues
    pares["tras_medianoche"] = despues

    agregado = pares.loc[pares["llegadas"].gt(0)].groupby(
        ["stop_id", "service_id"], observed=True
    ).agg(llegadas=("llegadas", "sum"), tras_medianoche=("tras_medianoche", "sum"))
    return agregado.astype(int).reset_index()


def comparar_con_el_atajo(tablas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """El filtro por texto contra el cálculo correcto.

    El atajo —quedarse con las filas cuyo `arrival_time` está entre `00:00:00` y
    `04:59:59`— es plausible, rápido y da 12 201 paradas donde hay 10 520. Sobreestima
    un 16 %: poco suficiente para que nada parezca roto.
    """
    paradas = tablas["stop_times"].copy()
    paradas["segundos"] = parse_hms_seconds(paradas["arrival_time"])
    con_frecuencia = set(tablas["frequencies"]["trip_id"])

    en_ventana = paradas["segundos"].between(NOCHE_INICIO, NOCHE_FIN, inclusive="left")
    atajo = paradas.loc[en_ventana]
    relativas = atajo["trip_id"].isin(con_frecuencia)

    correcto = llegadas_nocturnas(tablas)
    paradas_correctas = set(correcto["stop_id"])
    paradas_atajo = set(atajo["stop_id"])

    return indicator_table({
        "filas_que_el_atajo_toma": (
            int(len(atajo)), "filas",
            "Filas cuyo arrival_time cae entre 00:00:00 y 04:59:59 leído como reloj"),
        "de_ellas_con_horario_relativo": (
            int(relativas.sum()), "filas",
            "Filas de expediciones de frecuencia, cuyo arrival_time es un "
            "desplazamiento desde el inicio del viaje y no una hora"),
        "proporcion_relativas": (
            round(float(relativas.mean() * 100), 2), "%",
            "Si es 100, el atajo no está midiendo horas en absoluto"),
        "paradas_segun_el_atajo": (
            len(paradas_atajo), "paradas", "Paradas que el atajo reporta como nocturnas"),
        "paradas_correctas": (
            len(paradas_correctas), "paradas",
            "Paradas con al menos una llegada real en la ventana"),
        "sobreestimacion": (
            round(float(safe_ratio(len(paradas_atajo) - len(paradas_correctas),
                                   len(paradas_correctas), scale=100)), 2), "%",
            "Lo bastante pequeña para que el resultado parezca razonable"),
        "paradas_que_el_atajo_inventa": (
            len(paradas_atajo - paradas_correctas), "paradas",
            "Reportadas como nocturnas sin tener ninguna llegada nocturna"),
        "paradas_que_el_atajo_pierde": (
            len(paradas_correctas - paradas_atajo), "paradas",
            "Nocturnas que el atajo no reporta"),
    })


def servicio_por_parada(tablas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Llegadas nocturnas totales por parada, sumando los tres servicios.

    Se suma sobre los servicios porque la pregunta es «¿tiene esta parada servicio de
    madrugada?», que no distingue el día. La desagregación por día está en
    `cobertura_por_servicio`.
    """
    llegadas = llegadas_nocturnas(tablas)
    total = llegadas.groupby("stop_id", observed=True).agg(
        llegadas_noche=("llegadas", "sum"),
        tras_medianoche=("tras_medianoche", "sum"),
        servicios=("service_id", "nunique"),
    )
    return total.reset_index()


def intensidad_del_servicio(servicio: pd.DataFrame) -> pd.DataFrame:
    """Distribución de las llegadas nocturnas por parada.

    Importa porque «tiene servicio nocturno» es un sí o no que esconde todo. La parada
    mediana recibe 23 llegadas en cinco horas, una cada trece minutos; y hay 242 que
    reciben **una sola** en toda la ventana. Tratar las dos igual es perder la mitad de
    lo que el dato dice.
    """
    llegadas = servicio["llegadas_noche"]
    filas = [{"estadistico": "paradas con servicio nocturno", "llegadas": float(len(llegadas))}]
    for cuantil in (0.10, 0.25, 0.50, 0.75, 0.90, 0.99):
        filas.append({
            "estadistico": f"P{int(cuantil * 100)}",
            "llegadas": round(float(llegadas.quantile(cuantil)), 1),
        })
    filas.extend([
        {"estadistico": "máximo", "llegadas": float(llegadas.max())},
        {"estadistico": "una sola llegada en 5 h", "llegadas": float((llegadas == 1).sum())},
        {"estadistico": f"{UMBRAL_SERVICIO_TESTIMONIAL} o menos (testimonial)",
         "llegadas": float((llegadas <= UMBRAL_SERVICIO_TESTIMONIAL).sum())},
        {"estadistico": "solo por llegadas tras las 24:00",
         "llegadas": float(((servicio["tras_medianoche"] > 0)
                            & (servicio["llegadas_noche"] == servicio["tras_medianoche"])).sum())},
    ])
    return pd.DataFrame(filas)


# --------------------------------------------------------------- el lado del horario
def cargar_locales() -> pd.DataFrame:
    """Los lugares de carga abiertos, con su horario ya interpretado.

    Agrega tres columnas al consolidado de P01:

    - `horario_interpretado`: el objeto `Schedule`;
    - `horario_conocido`: si se pudo interpretar. **No** es lo mismo que «tiene texto»:
      un texto ilegible deja el horario desconocido;
    - `abre_de_noche`: `True`, `False` o `None`, y el `None` se propaga.
    """
    locales = cobertura.cargar_lugares().copy()
    horarios = parse_series(locales["horario"])
    locales["horario_interpretado"] = horarios
    locales["horario_conocido"] = [h.parsed for h in horarios]
    locales["abre_de_noche"] = [
        _abre_en_alguna_noche(h) for h in horarios
    ]
    return locales


def _abre_en_alguna_noche(horario) -> bool | None:
    """Si el local abre en `[00:00, 05:00)` **algún** día de la semana.

    Se pregunta por «algún día» y no por un día concreto a propósito. El mapeo entre el
    servicio del feed y el día del calendario tiene un pliegue —una llegada a las 24:30
    de un viernes de servicio ocurre un sábado— y resolverlo exigiría fechas, no días
    de servicio. Preguntando por el día más favorable, el resultado es una **cota
    superior**: si no abre ningún día, no abre, y el pliegue no cambia nada.

    Esa holgura es la que permite afirmar el cero sin resolver el pliegue, y queda
    dicha para que nadie reutilice el criterio donde sí importe.
    """
    respuestas = [
        covers_window(horario, dia, NOCHE_INICIO, NOCHE_FIN) for dia in range(7)
    ]
    if any(r is True for r in respuestas):
        return True
    if all(r is False for r in respuestas):
        return False
    return None


def informe_de_horarios(locales: pd.DataFrame) -> pd.DataFrame:
    """Cada texto de horario, cuántos locales lo usan y si se interpretó.

    Pone a la vista algo que no se espera: los 348 locales con horario usan **10 textos
    distintos**, y 311 de ellos usan solo dos. El campo no describe un local, describe
    la política de una cadena, y eso limita cualquier conclusión que se saque de él.
    """
    tabla = parse_report(locales["horario"])
    sin_dato = tabla.attrs.get("sin_dato", 0)
    tabla.attrs["sin_dato"] = sin_dato
    return tabla


def cobertura_del_campo_horario(locales: pd.DataFrame) -> pd.DataFrame:
    """Qué proporción de cada tipo de local declara horario.

    Es la tabla que convierte el problema de «faltan datos» en un hallazgo concreto:
    cuatro archivos al 100 % y uno al 0 %. Un vacío uniforme sería un problema de
    captura; un vacío concentrado en un archivo es una decisión de publicación.
    """
    tabla = locales.groupby("tipo_local", observed=True).agg(
        locales=("codigo", "size"),
        con_horario=("horario_conocido", "sum"),
        abren_de_noche=("abre_de_noche", lambda s: int(sum(x is True for x in s))),
    )
    tabla["cobertura_pct"] = (tabla["con_horario"] / tabla["locales"] * 100).round(1)
    total = pd.DataFrame([{
        "locales": int(len(locales)),
        "con_horario": int(locales["horario_conocido"].sum()),
        "abren_de_noche": int(sum(x is True for x in locales["abre_de_noche"])),
        "cobertura_pct": round(float(locales["horario_conocido"].mean() * 100), 1),
    }], index=pd.Index(["TOTAL"], name="tipo_local"))
    return pd.concat([tabla, total]).reset_index()


# ------------------------------------------------------------------------- el cruce
def clasificar(paradas_noche: pd.DataFrame, locales: pd.DataFrame) -> pd.DataFrame:
    """Para cada parada con servicio nocturno, en qué situación está.

    Las cuatro clases son excluyentes y se evalúan en este orden:

    1. **Con carga abierta verificada**: algún local a 300 m declara abrir de noche.
    2. **Sin local a 300 m**: no hay nada cerca, y el horario es irrelevante.
    3. **Sin carga abierta (verificado)**: hay locales cerca, **todos** con horario
       conocido, y ninguno abre. Es la única clase que permite afirmar que no hay
       cobertura.
    4. **Indeterminado**: hay locales cerca y al menos uno no declara horario.

    La cuarta clase es el resultado del caso. Fundirla con la tercera —tratar el
    silencio como un cerrado— produciría un «59,8 % sin cobertura verificada» que
    suena a medición y es una invención.
    """
    lat_locales = locales["lat"].to_numpy(dtype=float)
    lon_locales = locales["lon"].to_numpy(dtype=float)
    conocido = locales["horario_conocido"].to_numpy()
    abre = locales["abre_de_noche"].to_numpy()

    lat_paradas = paradas_noche["lat"].to_numpy(dtype=float)
    lon_paradas = paradas_noche["lon"].to_numpy(dtype=float)
    total = len(paradas_noche)

    clase: list[str] = [""] * total
    cercanos = np.zeros(total, dtype=int)
    con_horario = np.zeros(total, dtype=int)

    for inicio in range(0, total, BLOQUE):
        fin = min(inicio + BLOQUE, total)
        matriz = np.asarray(haversine_km(
            lat_paradas[inicio:fin, None], lon_paradas[inicio:fin, None],
            lat_locales[None, :], lon_locales[None, :],
        )) * 1000
        dentro = matriz <= RADIO_M
        for fila in range(fin - inicio):
            indices = np.flatnonzero(dentro[fila])
            posicion = inicio + fila
            cercanos[posicion] = len(indices)
            con_horario[posicion] = int(conocido[indices].sum())
            if len(indices) == 0:
                clase[posicion] = CLASE_SIN_LOCAL
            elif any(abre[k] is True for k in indices):
                clase[posicion] = CLASE_ABIERTA
            elif conocido[indices].all():
                clase[posicion] = CLASE_CERRADA
            else:
                clase[posicion] = CLASE_INDETERMINADA

    salida = paradas_noche.copy()
    salida["clase"] = clase
    salida["locales_a_300m"] = cercanos
    salida["locales_con_horario"] = con_horario
    return salida


def respuesta(clasificadas: pd.DataFrame) -> pd.DataFrame:
    """El reparto de las paradas nocturnas entre las cuatro clases."""
    total = len(clasificadas)
    cuenta = clasificadas["clase"].value_counts()
    filas = []
    for nombre in CLASES:
        valor = int(cuenta.get(nombre, 0))
        filas.append({
            "situacion": nombre,
            "paradas": valor,
            "porcentaje": round(float(safe_ratio(valor, total, scale=100)), 1),
            "permite_afirmar": "sí" if nombre != CLASE_INDETERMINADA else "no",
        })
    filas.append({
        "situacion": "TOTAL con servicio nocturno",
        "paradas": total,
        "porcentaje": 100.0,
        "permite_afirmar": "—",
    })
    return pd.DataFrame(filas)


def intervalo_de_la_respuesta(clasificadas: pd.DataFrame) -> pd.DataFrame:
    """El piso y el techo de la cobertura nocturna, con el ancho que los separa.

    El piso es lo verificado. El techo supone que **todos** los locales sin horario
    abren de madrugada, que es falso casi con certeza —ninguno de los 348 que sí
    declaran abre— pero es la cota que el dato permite. Entre los dos está la
    respuesta, y el ancho mide cuánto de la pregunta sigue abierto.
    """
    total = len(clasificadas)
    cuenta = clasificadas["clase"].value_counts()
    piso = int(cuenta.get(CLASE_ABIERTA, 0))
    indeterminadas = int(cuenta.get(CLASE_INDETERMINADA, 0))
    techo = piso + indeterminadas
    piso_pct = float(safe_ratio(piso, total, scale=100))
    techo_pct = float(safe_ratio(techo, total, scale=100))
    return indicator_table({
        "paradas_con_servicio_nocturno": (
            total, "paradas", "El denominador de este indicador"),
        "cobertura_verificada": (
            piso, "paradas", "Paradas con un local que declara abrir de madrugada"),
        "cobertura_minima_pct": (
            round(piso_pct, 2), "%", "El piso: lo que el dato permite afirmar"),
        "cobertura_maxima_pct": (
            round(techo_pct, 2), "%",
            "El techo: suponiendo que todos los locales sin horario abran"),
        "ancho_del_intervalo_pp": (
            round(techo_pct - piso_pct, 2), "puntos",
            "Cuánto de la pregunta sigue abierto. No lo produce la red ni la "
            "geografía: lo produce una columna vacía"),
    })


def lo_que_falta_para_contestar(clasificadas: pd.DataFrame, locales: pd.DataFrame) -> pd.DataFrame:
    """Qué locales habría que completar para cerrar el intervalo, y cuántos son.

    Convierte «faltan datos» en un pedido con número: estos registros, este efecto. Es
    la diferencia entre una queja y un hallazgo accionable.
    """
    indeterminadas = clasificadas.loc[clasificadas["clase"] == CLASE_INDETERMINADA]
    lat_locales = locales["lat"].to_numpy(dtype=float)
    lon_locales = locales["lon"].to_numpy(dtype=float)
    conocido = locales["horario_conocido"].to_numpy()

    pendientes: set[int] = set()
    lat = indeterminadas["lat"].to_numpy(dtype=float)
    lon = indeterminadas["lon"].to_numpy(dtype=float)
    for inicio in range(0, len(indeterminadas), BLOQUE):
        fin = min(inicio + BLOQUE, len(indeterminadas))
        matriz = np.asarray(haversine_km(
            lat[inicio:fin, None], lon[inicio:fin, None],
            lat_locales[None, :], lon_locales[None, :],
        )) * 1000
        for fila in range(fin - inicio):
            for k in np.flatnonzero((matriz[fila] <= RADIO_M) & ~conocido):
                pendientes.add(int(k))

    sin_horario_total = int((~conocido).sum())
    afectados = locales.iloc[sorted(pendientes)]
    tabla = afectados.groupby("tipo_local", observed=True).size().rename("locales_por_completar")
    salida = tabla.reset_index()
    salida["del_total_sin_horario_pct"] = (
        salida["locales_por_completar"] / max(sin_horario_total, 1) * 100
    ).round(1)
    salida["paradas_que_desbloquean"] = len(indeterminadas)
    return salida


def cobertura_por_servicio(tablas: dict[str, pd.DataFrame], locales: pd.DataFrame,
                           paradas: pd.DataFrame) -> pd.DataFrame:
    """La respuesta desagregada por servicio, que son los tipos de día.

    La noche del sábado es el caso de mayor demanda y el que más interesa. Sale igual
    que los otros dos, y que salga igual es el resultado: no hay un día en que la
    cobertura nocturna exista.
    """
    llegadas = llegadas_nocturnas(tablas)
    filas = []
    for servicio, grupo in llegadas.groupby("service_id", observed=True):
        del_servicio = paradas.loc[paradas["stop_id"].isin(set(grupo["stop_id"]))]
        if del_servicio.empty:
            continue
        clasificadas = clasificar(del_servicio.reset_index(drop=True), locales)
        cuenta = clasificadas["clase"].value_counts()
        total = len(clasificadas)
        filas.append({
            "service_id": servicio,
            "dias_de_la_semana": len(DIAS_POR_SERVICIO.get(servicio, ())),
            "paradas_nocturnas": total,
            "llegadas": int(grupo["llegadas"].sum()),
            "con_carga_abierta": int(cuenta.get(CLASE_ABIERTA, 0)),
            "sin_local_cerca": int(cuenta.get(CLASE_SIN_LOCAL, 0)),
            "cerrado_verificado": int(cuenta.get(CLASE_CERRADA, 0)),
            "indeterminado": int(cuenta.get(CLASE_INDETERMINADA, 0)),
            "indeterminado_pct": round(
                float(safe_ratio(cuenta.get(CLASE_INDETERMINADA, 0), total, scale=100)), 1),
        })
    return pd.DataFrame(filas).sort_values("service_id").reset_index(drop=True)


def peores_paradas(clasificadas: pd.DataFrame, limite: int = 15) -> pd.DataFrame:
    """Las paradas con más servicio nocturno y sin ningún local cerca.

    Es la lista que un equipo de operaciones podría usar: mucho servicio de madrugada,
    nada donde cargar en trescientos metros, y nada que averiguar porque la ausencia
    de local no depende de ningún horario.
    """
    sin_local = clasificadas.loc[clasificadas["clase"] == CLASE_SIN_LOCAL]
    columnas = ["stop_id", "stop_name", "llegadas_noche", "tras_medianoche", "servicios"]
    return sin_local.nlargest(limite, "llegadas_noche")[columnas].reset_index(drop=True)


def resumen(clasificadas: pd.DataFrame, locales: pd.DataFrame,
            paradas_totales: int) -> pd.DataFrame:
    """Las cifras del caso, cada una con su unidad y su definición."""
    cuenta = clasificadas["clase"].value_counts()
    total = len(clasificadas)
    return indicator_table({
        "paradas_de_embarque": (
            paradas_totales, "paradas", "Todas las paradas donde sube gente"),
        "con_servicio_nocturno": (
            total, "paradas", "Con al menos una llegada en [00:00, 05:00)"),
        "proporcion_nocturna_pct": (
            round(float(safe_ratio(total, paradas_totales, scale=100)), 1), "%",
            "El servicio de madrugada no es marginal"),
        "llegadas_nocturnas": (
            int(clasificadas["llegadas_noche"].sum()), "llegadas",
            "Sumadas sobre los tres servicios con ventanas de frecuencia"),
        "llegadas_medianas_por_parada": (
            float(clasificadas["llegadas_noche"].median()), "llegadas",
            "En las cinco horas de la ventana"),
        "locales_que_abren_de_noche": (
            int(sum(x is True for x in locales["abre_de_noche"])), "locales",
            "De los 1 927 abiertos, cuántos declaran abrir en la madrugada"),
        "cobertura_verificada_pct": (
            round(float(safe_ratio(cuenta.get(CLASE_ABIERTA, 0), total, scale=100)), 2), "%",
            "Paradas nocturnas con carga abierta a 300 m, verificada"),
        "indeterminadas_pct": (
            round(float(safe_ratio(cuenta.get(CLASE_INDETERMINADA, 0), total, scale=100)), 1), "%",
            "Paradas sobre las que el dato no permite concluir nada"),
    })


# ---------------------------------------------------------------------------- informe
def analizar(feed: Path | None = None) -> dict[str, pd.DataFrame]:
    """Ejecuta el caso completo y devuelve todas las tablas de resultado."""
    tablas = cargar_servicio(feed)
    locales = cargar_locales()
    todas = cobertura.cargar_paradas(feed)
    servicio = servicio_por_parada(tablas)

    paradas_noche = todas.merge(servicio, on="stop_id", how="inner").reset_index(drop=True)
    clasificadas = clasificar(paradas_noche, locales)

    return {
        "resumen": resumen(clasificadas, locales, len(todas)),
        "respuesta": respuesta(clasificadas),
        "intervalo": intervalo_de_la_respuesta(clasificadas),
        "lo_que_falta": lo_que_falta_para_contestar(clasificadas, locales),
        "ventanas_por_servicio": informe_de_ventanas(tablas),
        "atajo_comparado": comparar_con_el_atajo(tablas),
        "intensidad": intensidad_del_servicio(servicio),
        "horarios_interpretados": informe_de_horarios(locales),
        "cobertura_del_campo": cobertura_del_campo_horario(locales),
        "por_servicio": cobertura_por_servicio(tablas, locales, paradas_noche),
        "peores_paradas": peores_paradas(clasificadas),
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

    print("\n=== LA RESPUESTA: paradas con servicio nocturno, por situación ===")
    print(resultados["respuesta"].to_string(index=False))

    print("\n=== El intervalo honesto ===")
    print(resultados["intervalo"].to_string(index=False))

    print("\n=== Lo que falta para cerrarlo ===")
    print(resultados["lo_que_falta"].to_string(index=False))

    print("\n=== De dónde sale el servicio nocturno ===")
    print(resultados["ventanas_por_servicio"].to_string(index=False))

    print("\n=== El atajo que da una cifra plausible y falsa ===")
    print(resultados["atajo_comparado"].to_string(index=False))

    print("\n=== Intensidad del servicio nocturno ===")
    print(resultados["intensidad"].to_string(index=False))

    print("\n=== Los horarios, texto por texto ===")
    print(resultados["horarios_interpretados"].to_string(index=False))

    print("\n=== Cobertura del campo horario: cuatro archivos al 100 %, uno al 0 % ===")
    print(resultados["cobertura_del_campo"].to_string(index=False))

    print("\n=== Por servicio (tipo de día) ===")
    print(resultados["por_servicio"].to_string(index=False))

    print("\n=== Mucho servicio nocturno y ningún local a 300 m ===")
    print(resultados["peores_paradas"].to_string(index=False))

    destino = exportar(resultados)
    print(f"\nTablas escritas en {_ruta_legible(destino)}")


if __name__ == "__main__":
    main()
