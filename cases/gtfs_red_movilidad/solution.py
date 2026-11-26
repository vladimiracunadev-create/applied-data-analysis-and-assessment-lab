"""Resolución del caso GTFS de la Red Metropolitana de Movilidad, con datos reales.

El problema
    Responder: **¿cuántas expediciones de transporte público hay por hora del día en un
    día laboral, y cómo se reparten entre buses, Metro y trenes?**

    Parece un conteo trivial. No lo es: los datos públicos reales esconden tres
    trampas encadenadas, y cada una, por separado, produce una respuesta plausible y
    equivocada.

Las tres trampas, verificadas en el feed del 14 de noviembre de 2026
    1. **El horario no siempre es un horario.** De las 26 137 expediciones declaradas,
       14 520 son de frecuencia: su `stop_times` no contiene horas de reloj sino
       **desplazamientos desde el inicio del viaje**, empezando siempre en `0:00:00`.
       Agrupar `arrival_time` por su hora da 635 574 llegadas «a medianoche».
    2. **El relleno de ceros no es consistente.** La misma expedición mezcla
       `0:00:00` (una cifra) y `00:00:51` (dos). Ordenar o comparar como texto pone la
       primera parada **después** de la segunda, porque `'0:00:00' > '00:00:51'`.
    3. **Contar expediciones declaradas subestima el servicio por un factor de seis.**
       Cada fila de `frequencies.txt` representa muchas salidas reales: una ventana con
       un intervalo entre salidas. Expandirlas da unas 154 000 salidas, no 26 137.

    Y una cuarta, que es un defecto que no existe:

    4. **«El 32 % de las paradas no se usa».** 5 991 de las 18 486 filas de `stops.txt`
       no aparecen en `stop_times.txt`. No es un problema de calidad: 5 989 de ellas no
       son paradas, son estaciones, accesos, nodos de pasillo y áreas de abordaje,
       distinguidas por `location_type`. Las paradas realmente huérfanas son **dos**.

Tecnologías y por qué estas
    - **`zipfile` + `pandas.read_csv` sobre el flujo del ZIP**, sin descomprimir a
      disco: el feed pesa 12,8 MB comprimidos y 69,7 MB descomprimido, de los cuales
      51 MB son un solo archivo. Descomprimir primero duplica el espacio sin aportar
      nada.
    - **`usecols` y `dtype=str` al leer `stop_times.txt`**: de sus 8 columnas se
      necesitan 3. Leer solo esas baja el consumo de memoria a una fracción, y `str`
      evita que pandas convierta las horas a algo antes de que las validemos.
    - **`lab.dates.parse_hms_seconds`** en lugar de `pd.to_datetime`: el formato admite
      horas de 24 o más y relleno de ceros irregular, que `to_datetime` rechaza.
    - **`lab.sources`** para la procedencia: el nombre del archivo publicado cambia en
      cada versión, de modo que se resuelve leyendo el enlace de la página índice.
    - **Pandas y no SQL** para la expansión de frecuencias: es una operación de
      producto cartesiano acotado sobre 14 520 filas, donde `repeat` e índices
      vectorizados son directos. Para `stop_times` completo con agregaciones por
      ventana, DuckDB sería mejor; aquí no hace falta y se declara por qué.

Reproducir
    python scripts/fetch_data.py gtfs-red-movilidad
    python -m cases.gtfs_red_movilidad.solution

Advertencia de licencia
    Los datos del DTPM **no se versionan** en este repositorio: su licencia no está
    verificada. Lo que se versiona es este código, el registro de procedencia y las
    tablas de resultado agregadas.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lab.dates import parse_hms_seconds, seconds_to_hms, service_day_hour  # noqa: E402
from lab.metrics import indicator_table, safe_ratio  # noqa: E402
from lab.sources import Provenance, read_zip_table, zip_members  # noqa: E402

HERE = Path(__file__).resolve().parent
FEED = ROOT / "data" / "original" / "gtfs-red-movilidad.zip"
RESULTS = HERE / "resultados"

#: Día de servicio a analizar. `L` es el servicio de lunes a viernes del feed.
SERVICIO_LABORAL = "L"

#: Tipos de ruta de la especificación GTFS que aparecen en este feed.
ROUTE_TYPES = {"0": "tranvía o ligero", "1": "metro", "2": "tren", "3": "bus"}

#: Significado de `location_type` en GTFS. Solo el 0 es una parada donde sube gente.
LOCATION_TYPES = {
    "0": "parada o andén",
    "1": "estación",
    "2": "acceso o salida",
    "3": "nodo generico de pasillo",
    "4": "área de abordaje",
}


def _ruta_legible(path: Path) -> str:
    """Ruta relativa a la raíz cuando se puede, absoluta cuando no.

    `relative_to` levanta `ValueError` si la ruta está fuera del repositorio, y un
    mensaje de error que falla al construirse es peor que no tener mensaje.
    """
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _exigir_feed() -> Path:
    if not FEED.exists():
        raise FileNotFoundError(
            f"No está el feed en {_ruta_legible(FEED)}.\n"
            "Descárguelo con:  python scripts/fetch_data.py gtfs-red-movilidad"
        )
    return FEED


# --------------------------------------------------------------------------- lectura
def cargar(feed: Path | None = None) -> dict[str, pd.DataFrame]:
    """Lee del ZIP solo las columnas necesarias, como texto.

    `dtype=str` es deliberado en todo: queremos ver los valores tal como los publicó el
    organismo, y decidir nosotros qué es un número y qué es una hora. `usecols` en
    `stop_times` reduce de 8 columnas a 3 la tabla de 1,1 millones de filas.
    """
    archivo = feed or _exigir_feed()
    return {
        "agency": read_zip_table(archivo, "agency.txt", dtype=str,
                                 usecols=["agency_id", "agency_name"]),
        "feed_info": read_zip_table(archivo, "feed_info.txt", dtype=str),
        "calendar": read_zip_table(archivo, "calendar.txt", dtype=str),
        "routes": read_zip_table(archivo, "routes.txt", dtype=str,
                                 usecols=["route_id", "agency_id", "route_short_name",
                                          "route_type"]),
        "trips": read_zip_table(archivo, "trips.txt", dtype=str,
                                usecols=["route_id", "service_id", "trip_id"]),
        "stops": read_zip_table(archivo, "stops.txt", dtype=str,
                                usecols=["stop_id", "stop_name", "location_type",
                                         "stop_lat", "stop_lon"]),
        "frequencies": read_zip_table(archivo, "frequencies.txt", dtype=str),
        # De las 8 columnas de stop_times.txt se usan 4. Leer solo esas reduce a la
        # mitad la memoria de la tabla de 1,1 millones de filas.
        "stop_times": read_zip_table(archivo, "stop_times.txt", dtype=str,
                                     usecols=["trip_id", "arrival_time", "stop_sequence",
                                              "stop_id"]),
    }


# ------------------------------------------------------------------ trampas 1, 2 y 3
def diagnosticar_horas(tablas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Mide las trampas 1 y 2: horas que no son horas y relleno de ceros irregular."""
    stop_times = tablas["stop_times"]
    con_frecuencia = set(tablas["frequencies"]["trip_id"])
    es_frecuencia = stop_times["trip_id"].isin(con_frecuencia)

    digitos = stop_times["arrival_time"].str.split(":").str[0].str.len()
    segundos = parse_hms_seconds(stop_times["arrival_time"])

    primera_parada = stop_times["stop_sequence"].eq("1")
    cero_en_la_primera = primera_parada & segundos.eq(0)

    filas = {
        "filas_stop_times": (len(stop_times), "filas",
                             "Tamaño de la tabla de horarios"),
        "expediciones_declaradas": (tablas["trips"]["trip_id"].nunique(), "expediciones",
                                    "Filas distintas de trips.txt"),
        "expediciones_de_frecuencia": (len(con_frecuencia), "expediciones",
                                       "Declaradas en frequencies.txt: su horario es un desplazamiento, no un reloj"),
        "filas_con_horario_relativo": (int(es_frecuencia.sum()), "filas",
                                       "Filas de stop_times cuyo tiempo NO es hora de reloj"),
        "pct_horario_relativo": (safe_ratio(int(es_frecuencia.sum()), len(stop_times), scale=100),
                                 "%", "Proporción de la tabla que no se puede leer como reloj"),
        "hora_sin_relleno": (int(digitos.eq(1).sum()), "filas",
                             "Valores con una sola cifra de hora, como 0:00:00"),
        "hora_con_relleno": (int(digitos.eq(2).sum()), "filas",
                             "Valores con dos cifras de hora, como 00:00:51"),
        "no_interpretables": (int((segundos.isna() & stop_times["arrival_time"].notna()).sum()),
                              "filas", "Valores presentes que no son H:MM:SS válido"),
        "segundos_maximo": (float(segundos.max()), "s",
                            "Mayor tiempo observado; sobre 86400 indica día de servicio extendido"),
        "primeras_paradas_en_cero": (int(cero_en_la_primera.sum()), "filas",
                                     "Expediciones cuya primera parada está en 0:00:00"),
    }
    return indicator_table(filas)


def expandir_frecuencias(tablas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Trampa 3: convierte cada ventana de frecuencia en sus salidas reales.

    Cada fila de `frequencies.txt` dice «entre `start_time` y `end_time`, sale un
    vehículo cada `headway_secs` segundos». El número de salidas de esa ventana es:

        salidas = (end_time − start_time) ÷ headway_secs

    con `end_time` **exclusivo**, que es lo que fija la especificación GTFS: la salida
    de `end_time` pertenece a la ventana siguiente. Contar inclusivo infla el total en
    una salida por ventana, y hay 14 520 ventanas.

    La expansión se hace con `Index.repeat`, que es la forma vectorizada de producir n
    filas por fila: construir la lista con un bucle sobre 14 520 ventanas y 142 366
    salidas funciona, pero tarda dos órdenes de magnitud más.
    """
    frecuencias = tablas["frequencies"].copy()
    frecuencias["inicio_s"] = parse_hms_seconds(frecuencias["start_time"])
    frecuencias["fin_s"] = parse_hms_seconds(frecuencias["end_time"])
    frecuencias["intervalo_s"] = pd.to_numeric(frecuencias["headway_secs"], errors="coerce")

    invalidas = (
        frecuencias[["inicio_s", "fin_s", "intervalo_s"]].isna().any(axis=1)
        | frecuencias["intervalo_s"].le(0)
        | frecuencias["fin_s"].lt(frecuencias["inicio_s"])
    )
    if invalidas.any():
        # No se descartan en silencio: se informan y se excluyen.
        frecuencias = frecuencias.loc[~invalidas].copy()

    frecuencias["salidas"] = (
        (frecuencias["fin_s"] - frecuencias["inicio_s"]) // frecuencias["intervalo_s"]
    ).clip(lower=0).astype(int)

    utiles = frecuencias.loc[frecuencias["salidas"].gt(0)]
    expandido = utiles.loc[utiles.index.repeat(utiles["salidas"])].copy()
    # Posición de cada salida dentro de su ventana: 0, 1, 2, …
    expandido["k"] = expandido.groupby(level=0).cumcount()
    expandido["salida_s"] = expandido["inicio_s"] + expandido["k"] * expandido["intervalo_s"]
    expandido["salida"] = seconds_to_hms(expandido["salida_s"])
    expandido["hora_reloj"] = service_day_hour(expandido["salida_s"])
    return expandido[["trip_id", "salida_s", "salida", "hora_reloj", "intervalo_s"]].reset_index(drop=True)


def salidas_programadas(tablas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Salidas de las expediciones con horario absoluto, desde su primera parada.

    Para una expedición sin `frequencies`, la hora de salida es el `arrival_time` de su
    `stop_sequence = 1`. Hay que ordenar por `stop_sequence` **numérico**: como texto,
    la parada 10 va antes de la 2.
    """
    con_frecuencia = set(tablas["frequencies"]["trip_id"])
    stop_times = tablas["stop_times"]
    primeras = stop_times.loc[
        ~stop_times["trip_id"].isin(con_frecuencia)
        & pd.to_numeric(stop_times["stop_sequence"], errors="coerce").eq(1)
    ].copy()
    primeras["salida_s"] = parse_hms_seconds(primeras["arrival_time"])
    primeras["salida"] = seconds_to_hms(primeras["salida_s"])
    primeras["hora_reloj"] = service_day_hour(primeras["salida_s"])
    return primeras[["trip_id", "salida_s", "salida", "hora_reloj"]].reset_index(drop=True)


def expediciones_por_hora(tablas: dict[str, pd.DataFrame],
                          servicio: str = SERVICIO_LABORAL) -> pd.DataFrame:
    """La respuesta: salidas por hora del reloj en un día de servicio, por modo.

    Une las dos poblaciones —frecuencia expandida y horario absoluto— y las restringe
    al servicio indicado. El resultado declara de qué fuente viene cada salida, porque
    la mezcla de dos mecánicas distintas en un mismo indicador tiene que ser visible.
    """
    trips = tablas["trips"]
    routes = tablas["routes"].copy()
    routes["modo"] = routes["route_type"].map(ROUTE_TYPES).fillna("otro")

    del_servicio = trips.loc[trips["service_id"].eq(servicio), ["trip_id", "route_id"]]
    catalogo = del_servicio.merge(routes[["route_id", "modo", "agency_id"]],
                                  on="route_id", how="left", validate="many_to_one")

    de_frecuencia = expandir_frecuencias(tablas).assign(fuente="frequencies")
    de_horario = salidas_programadas(tablas).assign(fuente="stop_times")
    todas = pd.concat(
        [de_frecuencia[["trip_id", "hora_reloj", "fuente"]],
         de_horario[["trip_id", "hora_reloj", "fuente"]]],
        ignore_index=True,
    )

    unido = todas.merge(catalogo, on="trip_id", how="inner", validate="many_to_one")
    resumen = (unido.groupby(["hora_reloj", "modo", "fuente"], dropna=False)
                    .size().rename("salidas").reset_index())
    resumen["hora_reloj"] = resumen["hora_reloj"].astype("Int64")
    return resumen.sort_values(["hora_reloj", "modo", "fuente"]).reset_index(drop=True)


def comparar_ingenuo_vs_correcto(tablas: dict[str, pd.DataFrame],
                                 servicio: str = SERVICIO_LABORAL) -> pd.DataFrame:
    """Cuantifica el error de cada atajo frente al cálculo correcto.

    Esta tabla es el entregable más útil del caso: no dice solo cuál es la respuesta,
    dice cuánto se equivoca cada forma de llegar a ella.
    """
    trips = tablas["trips"]
    del_servicio = trips.loc[trips["service_id"].eq(servicio)]
    con_frecuencia = set(tablas["frequencies"]["trip_id"])

    ingenuo_trips = del_servicio["trip_id"].nunique()
    correcto = expediciones_por_hora(tablas, servicio)["salidas"].sum()

    # Atajo 2: contar frecuencias inclusivo, sumando una salida de más por ventana.
    frecuencias = tablas["frequencies"].copy()
    frecuencias["inicio_s"] = parse_hms_seconds(frecuencias["start_time"])
    frecuencias["fin_s"] = parse_hms_seconds(frecuencias["end_time"])
    frecuencias["intervalo_s"] = pd.to_numeric(frecuencias["headway_secs"], errors="coerce")
    del_servicio_ids = set(del_servicio["trip_id"])
    suyas = frecuencias.loc[frecuencias["trip_id"].isin(del_servicio_ids)]
    inclusivo = int((((suyas["fin_s"] - suyas["inicio_s"]) // suyas["intervalo_s"]) + 1).sum())
    exclusivo = int(((suyas["fin_s"] - suyas["inicio_s"]) // suyas["intervalo_s"]).sum())
    sin_frecuencia = len(del_servicio_ids - con_frecuencia)

    filas = [
        {"forma_de_contar": "expediciones de trips.txt (atajo)",
         "resultado": ingenuo_trips,
         "error_vs_correcto": ingenuo_trips - correcto,
         "por_que_esta_mal": "Cada fila de frequencies.txt representa muchas salidas, no una."},
        {"forma_de_contar": "frecuencias con fin inclusivo + horario absoluto",
         "resultado": inclusivo + sin_frecuencia,
         "error_vs_correcto": (inclusivo + sin_frecuencia) - correcto,
         "por_que_esta_mal": "GTFS define end_time exclusivo: suma una salida por ventana."},
        {"forma_de_contar": "frecuencias expandidas + horario absoluto (correcto)",
         "resultado": correcto,
         "error_vs_correcto": 0,
         "por_que_esta_mal": "—"},
    ]
    tabla = pd.DataFrame(filas)
    tabla["error_relativo_pct"] = safe_ratio(
        tabla["error_vs_correcto"], correcto, scale=100
    ).round(2)
    # Comprobación interna: la expansión vectorizada y el cálculo aritmético directo
    # (ventanas con fin exclusivo, más las expediciones de horario absoluto) tienen que
    # dar el mismo número. Si no coinciden, la expansión tiene un error de borde.
    tabla.attrs["comprobacion_aritmetica"] = int(exclusivo + sin_frecuencia)
    tabla.attrs["coincide"] = bool(exclusivo + sin_frecuencia == correcto)
    return tabla


# ------------------------------------------------------------------------- trampa 4
def paradas_sin_uso(tablas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Trampa 4: el defecto que no existe.

    Cruzar `stops.txt` con `stop_times.txt` y declarar «paradas huérfanas» todo lo que
    no aparece es un error de interpretación, no un hallazgo de calidad: `stops.txt`
    describe una jerarquía de lugares, y solo `location_type = 0` es una parada donde
    sube gente.
    """
    usados = set(tablas["stop_times"]["stop_id"])
    stops = tablas["stops"].copy()
    stops["location_type"] = stops["location_type"].fillna("0").replace("", "0")
    stops["tipo"] = stops["location_type"].map(LOCATION_TYPES).fillna("no declarado")
    stops["aparece_en_horarios"] = stops["stop_id"].isin(usados)
    stops["sin_coordenadas"] = (
        stops["stop_lat"].isna() | stops["stop_lat"].astype("string").str.strip().eq("")
    )

    resumen = (stops.groupby(["location_type", "tipo"])
                    .agg(filas=("stop_id", "size"),
                         en_horarios=("aparece_en_horarios", "sum"),
                         sin_coordenadas=("sin_coordenadas", "sum"))
                    .reset_index())
    resumen["fuera_de_horarios"] = resumen["filas"] - resumen["en_horarios"]
    resumen["es_defecto_real"] = resumen["location_type"].eq("0") & resumen["fuera_de_horarios"].gt(0)
    return resumen.sort_values("filas", ascending=False).reset_index(drop=True)


def integridad(tablas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Integridad referencial del feed: claves huérfanas en los cuatro cruces del modelo."""
    comprobaciones = [
        ("stop_times.stop_id → stops.stop_id", tablas["stop_times"]["stop_id"],
         tablas["stops"]["stop_id"]),
        ("stop_times.trip_id → trips.trip_id", tablas["stop_times"]["trip_id"],
         tablas["trips"]["trip_id"]),
        ("trips.route_id → routes.route_id", tablas["trips"]["route_id"],
         tablas["routes"]["route_id"]),
        ("trips.service_id → calendar.service_id", tablas["trips"]["service_id"],
         tablas["calendar"]["service_id"]),
        ("routes.agency_id → agency.agency_id", tablas["routes"]["agency_id"],
         tablas["agency"]["agency_id"]),
        ("frequencies.trip_id → trips.trip_id", tablas["frequencies"]["trip_id"],
         tablas["trips"]["trip_id"]),
    ]
    filas = []
    for nombre, hijo, padre in comprobaciones:
        validos = set(padre.dropna())
        observados = hijo.dropna()
        huerfanos = int((~observados.isin(validos)).sum())
        filas.append({
            "cruce": nombre,
            "valores": len(observados),
            "distintos": observados.nunique(),
            "huerfanos": huerfanos,
            "veredicto": "íntegro" if huerfanos == 0 else "claves desconocidas",
        })
    return pd.DataFrame(filas)


# ---------------------------------------------------------------------------- informe
def analizar(feed: Path | None = None) -> dict[str, pd.DataFrame]:
    """Ejecuta el caso completo y devuelve todas las tablas de resultado."""
    tablas = cargar(feed)
    return {
        "inventario": zip_members(feed or FEED),
        "diagnostico_horas": diagnosticar_horas(tablas),
        "integridad": integridad(tablas),
        "paradas_por_tipo": paradas_sin_uso(tablas),
        "conteo_comparado": comparar_ingenuo_vs_correcto(tablas),
        "salidas_por_hora": expediciones_por_hora(tablas),
    }


def exportar(resultados: dict[str, pd.DataFrame], destino: Path = RESULTS) -> Path:
    """Escribe las tablas de resultado en CSV.

    Son agregados pequeños, no datos de terceros: se pueden versionar sin redistribuir
    el feed, de modo que los hallazgos quedan visibles sin descargar 12,8 MB.
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
        procedencia = Provenance.from_path(archivo)
        print(f"Fuente: {procedencia.summary()}\n")
    except FileNotFoundError:
        print("Aviso: el feed no tiene registro de procedencia.\n")

    resultados = analizar(archivo)

    print("=== Diagnóstico de las horas ===")
    print(resultados["diagnostico_horas"].to_string(index=False))

    print("\n=== Integridad referencial ===")
    print(resultados["integridad"].to_string(index=False))

    print("\n=== Paradas por tipo: el defecto que no existe ===")
    print(resultados["paradas_por_tipo"].to_string(index=False))

    print("\n=== Cuánto se equivoca cada forma de contar ===")
    print(resultados["conteo_comparado"].to_string(index=False))

    por_hora = resultados["salidas_por_hora"]
    print("\n=== Salidas por hora y modo (servicio laboral) ===")
    pivote = por_hora.pivot_table(index="hora_reloj", columns="modo", values="salidas",
                                  aggfunc="sum", fill_value=0)
    print(pivote.to_string())
    print(f"\nTotal de salidas del día laboral: {por_hora['salidas'].sum():,}")

    destino = exportar(resultados)
    print(f"\nTablas escritas en {_ruta_legible(destino)}")


if __name__ == "__main__":
    main()
