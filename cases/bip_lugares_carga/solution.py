"""P01: consolidar cinco Excel públicos heterogéneos en una sola tabla utilizable.

El problema
    La Subsecretaría de Transporte publica los lugares donde se puede cargar la tarjeta
    bip! en **cinco archivos Excel distintos**, uno por tipo de local. La pregunta es
    simple: **¿cuántos lugares de carga hay, de qué tipo, en qué comuna y de qué
    entidad?**

    Para contestarla hay que consolidar los cinco archivos. Y los cinco están
    maquetados para que una persona los lea, no para que un programa los procese.

Los nueve defectos, verificados archivo por archivo
    1. El encabezado está en una **fila distinta en cada archivo**: 7, 9, 13, 10 y 9.
       `pd.read_excel` sin `header=` devuelve diez columnas `Unnamed: 0`…`Unnamed: 9`.
    2. Los esquemas tienen **9 o 10 columnas** según el archivo.
    3. Los nombres de columna varían: `NOMBRE FANTASIA`, `NOMBRE DE FANTASIA ` —con un
       espacio al final— o ausente; `DIRECCION` o `DIRECCIÓN`; `HORARIO REFERENCIAL`,
       `HORARIO` o ausente.
    4. Los nombres de hoja varían: `Abiertos`, `Abierto`, `PCMA`.
    5. Un archivo trae una hoja **`Cerrados`**, que no debe entrar en un indicador de
       cobertura.
    6. Hay **dos sistemas de coordenadas a la vez**: UTM (`ESTE`, `NORTE`) y geográficas
       (`LATITUD`, `LONGITUD`).
    7. La entidad viene con mayúsculas inconsistentes: `FULLCARGA` y `Fullcarga`.
    8. La comuna viene en mayúsculas y sin tildes: `CONCHALI`, `ESTACION CENTRAL`.
    9. El contenido incluye el carácter `∙`, que aborta un comando en una consola de
       Windows con página de códigos cp1252.

Lo que la consolidación encontró
    El defecto 6 es una oportunidad: dos representaciones de la misma coordenada
    permiten **validar una contra la otra sin ninguna fuente externa**. Al hacerlo
    aparecen dos cosas distintas:

    - Un **desvío sistemático de unos 61 metros** en casi todos los registros. En el
      archivo de centros de alto estándar es de 61,07 m con una desviación de 0,28 m:
      prácticamente constante. Un desplazamiento constante no es un error de cálculo,
      es una **diferencia de datum geodésico** entre las dos columnas.
    - **Tres registros con discrepancias de 4,6 km, 10,1 km y 10,3 km.** Ahí las dos
      coordenadas apuntan a lugares distintos de la ciudad: son errores de dato reales,
      y la validación cruzada es lo único que los encuentra.

Tecnologías y por qué estas
    - **`lab.excel.detect_header_row`** en lugar de fijar la fila a mano. Con cinco
      archivos del mismo organismo y cinco filas distintas, fijar el número funciona
      hasta la próxima publicación.
    - **`dtype=str` en todo.** Los códigos del archivo de Metro son `L1`, `L2`: leerlos
      como número los destruye.
    - **`lab.textual.normalize_key`** para las claves de agrupación, conservando
      además la etiqueta legible. Agrupar sobre texto crudo crea grupos espurios.
    - **`lab.geo.utm_to_latlon`** para la validación cruzada. Se implementa la fórmula
      en lugar de usar `pyproj` para no agregar dependencias al entorno mínimo y para
      que la conversión sea explicable; para trabajo geoespacial serio, use la
      biblioteca.
    - **Pandas y no Excel** para consolidar. En Excel esto se hace con Power Query, que
      es la respuesta correcta si el entregable tiene que ser un libro; aquí el
      entregable es una tabla reutilizable y un informe de calidad.

Reproducir
    python scripts/fetch_data.py bip-metro
    python scripts/fetch_data.py bip-puntos
    python scripts/fetch_data.py bip-centros-alto-estandar
    python scripts/fetch_data.py bip-centros-estandar
    python scripts/fetch_data.py bip-retail
    python -m cases.bip_lugares_carga.solution

Licencia de los datos
    Creative Commons Atribución-NoComercial 2.0, **verificada** en los metadatos del
    portal de datos abiertos. A diferencia del GTFS, aquí la licencia está declarada.
    Los archivos de origen no se versionan igualmente, por tamaño y por no
    redistribuir; sí se versionan las tablas de resultado agregadas.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lab.excel import SheetReport, read_all_sheets  # noqa: E402
from lab.geo import haversine_km, utm_to_latlon  # noqa: E402
from lab.metrics import indicator_table, safe_ratio  # noqa: E402
from lab.sources import BIP_SOURCES, Provenance  # noqa: E402
from lab.textual import normalize_key, normalize_label, normalize_series  # noqa: E402

HERE = Path(__file__).resolve().parent
ORIGINAL = ROOT / "data" / "original"
RESULTS = HERE / "resultados"

#: Tipo de local por archivo. El tipo no está dentro de los datos: está en el nombre
#: del archivo, de modo que hay que declararlo al consolidar o se pierde.
TIPOS: dict[str, str] = {
    "bip-metro": "Estación de Metro",
    "bip-puntos": "Punto bip!",
    "bip-centros-alto-estandar": "Centro bip! alto estándar",
    "bip-centros-estandar": "Centro bip! estándar",
    "bip-retail": "Retail",
}

#: Esquema común. Las columnas que algún archivo no trae quedan nulas, y la cobertura
#: se informa: un campo ausente en 1 579 de 1 928 filas no es un detalle.
ESQUEMA: tuple[str, ...] = (
    "codigo", "entidad", "nombre", "direccion", "comuna", "horario",
    "este", "norte", "latitud", "longitud",
)

#: Alias admitidos por columna, ya normalizados. La correspondencia se declara; no se
#: adivina por parecido, porque un acierto por casualidad hoy es un error mañana.
ALIAS: dict[str, tuple[str, ...]] = {
    "codigo": ("CODIGO",),
    "entidad": ("ENTIDAD",),
    "nombre": ("NOMBRE FANTASIA", "NOMBRE DE FANTASIA"),
    "direccion": ("DIRECCION",),
    "comuna": ("COMUNA",),
    "horario": ("HORARIO REFERENCIAL", "HORARIO"),
    "este": ("ESTE",),
    "norte": ("NORTE",),
    "latitud": ("LATITUD",),
    "longitud": ("LONGITUD",),
}

#: Nombres de hoja que indican locales fuera de servicio.
HOJAS_CERRADAS: tuple[str, ...] = ("CERRADOS", "CERRADAS", "CERRADO")

#: Desvío sobre el cual se considera que las dos coordenadas no describen el mismo
#: lugar. 200 m es holgado frente al desvío sistemático de ~61 m observado y estricto
#: frente a los errores reales, que son de kilómetros.
UMBRAL_COORDENADA_M = 200.0

#: Zona UTM de Santiago de Chile.
ZONA_UTM = 19


def _exigir_archivos() -> list[Path]:
    rutas = [ORIGINAL / f"{nombre}.xlsx" for nombre in BIP_SOURCES]
    faltan = [r for r in rutas if not r.exists()]
    if faltan:
        comandos = "\n".join(
            f"  python scripts/fetch_data.py {r.stem}" for r in faltan
        )
        raise FileNotFoundError(
            f"Faltan {len(faltan)} de los {len(rutas)} archivos. Descárguelos con:\n"
            f"{comandos}"
        )
    return rutas


# ------------------------------------------------------------------------- lectura
def cargar() -> dict[tuple[str, str], tuple[pd.DataFrame, SheetReport]]:
    """Lee las seis hojas de los cinco archivos, con el encabezado detectado.

    Returns:
        `{(fuente, hoja): (tabla, informe)}`. Se devuelven **todas** las hojas,
        incluida `Cerrados`: la decisión de excluirla pertenece al indicador, no a la
        lectura, y para excluirla hay que haberla contado.
    """
    _exigir_archivos()
    salida: dict[tuple[str, str], tuple[pd.DataFrame, SheetReport]] = {}
    for fuente in BIP_SOURCES:
        ruta = ORIGINAL / f"{fuente}.xlsx"
        for hoja, (tabla, informe) in read_all_sheets(ruta).items():
            salida[(fuente, hoja)] = (tabla, informe)
    return salida


def informe_de_lectura(hojas: dict[tuple[str, str], tuple[pd.DataFrame, SheetReport]]) -> pd.DataFrame:
    """Qué hubo que hacer para leer cada hoja. Es parte del entregable de calidad."""
    filas = []
    for (fuente, hoja), (_, informe) in hojas.items():
        fila = informe.as_row()
        fila["fuente"] = fuente
        fila["hoja"] = hoja
        fila["tipo_local"] = TIPOS[fuente]
        fila["abierto"] = "no" if normalize_key(hoja) in HOJAS_CERRADAS else "sí"
        filas.append(fila)
    columnas = ["fuente", "hoja", "tipo_local", "abierto", "encabezado_en_fila",
                "filas_de_titulo_descartadas", "filas", "columnas",
                "filas_vacias_descartadas", "columnas_vacias_descartadas"]
    return pd.DataFrame(filas)[columnas].sort_values(["fuente", "hoja"]).reset_index(drop=True)


def informe_de_esquemas(hojas) -> pd.DataFrame:
    """Qué campo del esquema común aporta cada hoja y cuál no trae.

    Es la tabla que justifica la correspondencia de columnas. Sin ella, el renombrado
    queda como una decisión escondida en el código.
    """
    filas = []
    for (fuente, hoja), (tabla, _) in hojas.items():
        presentes = {normalize_key(c) for c in tabla.columns}
        fila = {"fuente": fuente, "hoja": hoja}
        for campo, alias in ALIAS.items():
            encontrado = next((a for a in alias if a in presentes), None)
            fila[campo] = encontrado or "—"
        filas.append(fila)
    return pd.DataFrame(filas).sort_values(["fuente", "hoja"]).reset_index(drop=True)


# -------------------------------------------------------------------- armonización
def _armonizar(tabla: pd.DataFrame) -> pd.DataFrame:
    """Lleva una hoja al esquema común, dejando nulas las columnas que no trae."""
    por_clave = {normalize_key(c): c for c in tabla.columns}
    salida = pd.DataFrame(index=tabla.index)
    for campo, alias in ALIAS.items():
        origen = next((por_clave[a] for a in alias if a in por_clave), None)
        salida[campo] = tabla[origen].astype("string") if origen else pd.Series(
            pd.NA, index=tabla.index, dtype="string"
        )
    return salida


def consolidar(hojas=None) -> pd.DataFrame:
    """Una sola tabla con los lugares de carga de los cinco archivos.

    Agrega, además del esquema común:

    - `tipo_local` y `fuente`, que viven en el nombre del archivo y se perderían;
    - `abierto`, derivado del nombre de la hoja;
    - `entidad_clave` y `comuna_clave`, normalizadas para agrupar, junto con
      `comuna_etiqueta` legible para el informe;
    - las coordenadas convertidas desde UTM y el desvío respecto de las publicadas.
    """
    hojas = hojas if hojas is not None else cargar()
    partes = []
    for (fuente, hoja), (tabla, _) in hojas.items():
        parte = _armonizar(tabla)
        parte["fuente"] = fuente
        parte["hoja"] = hoja
        parte["tipo_local"] = TIPOS[fuente]
        parte["abierto"] = normalize_key(hoja) not in HOJAS_CERRADAS
        partes.append(parte)

    todo = pd.concat(partes, ignore_index=True)

    # Claves para agrupar, y etiqueta para mostrar. Las tres cosas a la vez, porque
    # guardar solo la clave empobrece el informe final.
    todo["entidad_clave"] = normalize_series(todo["entidad"])
    todo["comuna_clave"] = normalize_series(todo["comuna"])
    todo["comuna_etiqueta"] = todo["comuna"].map(normalize_label).astype("string")
    todo["direccion_clave"] = normalize_series(todo["direccion"], expand_abbreviations=True)

    # Numéricos, con los no convertibles en nulo y no en cero.
    for columna in ("este", "norte", "latitud", "longitud"):
        todo[columna] = pd.to_numeric(todo[columna], errors="coerce")

    lat_utm, lon_utm = utm_to_latlon(todo["este"], todo["norte"], zona=ZONA_UTM)
    todo["latitud_utm"] = lat_utm
    todo["longitud_utm"] = lon_utm
    todo["desvio_m"] = haversine_km(
        lat_utm, lon_utm, todo["latitud"], todo["longitud"]
    ) * 1000
    todo["coordenada_sospechosa"] = todo["desvio_m"].gt(UMBRAL_COORDENADA_M).fillna(False)

    return todo.reset_index(drop=True)


# ----------------------------------------------------------------------- validación
def validar_coordenadas(consolidado: pd.DataFrame) -> pd.DataFrame:
    """Compara las dos representaciones de la coordenada de cada fila.

    Distingue dos cosas que no hay que mezclar:

    - el **desvío sistemático**, visible en la mediana y en una desviación típica
      pequeña dentro de cada archivo, que indica una diferencia de datum geodésico
      entre las columnas y **no** es un error de registro;
    - los **errores de dato**, filas donde las dos coordenadas apuntan a lugares
      distintos de la ciudad.

    Informar el primero como si fueran mil errores sería un falso positivo masivo;
    callar los segundos, una omisión.
    """
    filas = []
    for fuente, grupo in consolidado.groupby("fuente", sort=True):
        desvio = grupo["desvio_m"].dropna()
        normales = desvio[desvio.le(UMBRAL_COORDENADA_M)]
        filas.append({
            "fuente": fuente,
            "filas": len(grupo),
            "con_ambas_coordenadas": int(desvio.notna().sum()),
            "desvio_mediano_m": round(float(normales.median()), 2) if len(normales) else np.nan,
            "desvio_desv_tipica_m": round(float(normales.std()), 2) if len(normales) > 1 else np.nan,
            "sospechosas": int(grupo["coordenada_sospechosa"].sum()),
        })
    tabla = pd.DataFrame(filas)
    tabla["veredicto"] = np.where(
        tabla["sospechosas"].gt(0),
        "revisar las filas marcadas",
        "desvío sistemático, sin errores de registro",
    )
    return tabla


def coordenadas_sospechosas(consolidado: pd.DataFrame) -> pd.DataFrame:
    """Las filas donde las dos coordenadas no describen el mismo lugar."""
    columnas = ["fuente", "codigo", "entidad", "comuna", "direccion",
                "este", "norte", "latitud", "longitud",
                "latitud_utm", "longitud_utm", "desvio_m"]
    sospechosas = consolidado.loc[consolidado["coordenada_sospechosa"], columnas]
    return sospechosas.sort_values("desvio_m", ascending=False).round(6).reset_index(drop=True)


def validar_clave(consolidado: pd.DataFrame) -> pd.DataFrame:
    """¿`codigo` identifica un lugar de carga de forma única?

    La respuesta es que no, y el motivo es instructivo: en el archivo de Metro el
    código es la **línea** (`L1`, `L2`), no el local. Al consolidar hace falta una clave
    compuesta con el archivo de origen.
    """
    filas = []
    for ambito, grupo in (
        ("consolidado", consolidado),
        *[(f"solo {fuente}", g) for fuente, g in consolidado.groupby("fuente", sort=True)],
    ):
        codigos = grupo["codigo"].dropna()
        filas.append({
            "ambito": ambito,
            "filas": len(grupo),
            "codigos_distintos": int(codigos.nunique()),
            "codigos_repetidos": int(codigos.duplicated().sum()),
            "es_clave": "sí" if len(codigos) == codigos.nunique() and len(codigos) == len(grupo)
                        else "no",
        })
    tabla = pd.DataFrame(filas)
    compuesta = consolidado[["fuente", "codigo"]].dropna()
    tabla.loc[len(tabla)] = {
        "ambito": "clave compuesta (fuente + codigo)",
        "filas": len(compuesta),
        "codigos_distintos": int(compuesta.drop_duplicates().shape[0]),
        "codigos_repetidos": int(compuesta.duplicated().sum()),
        "es_clave": "sí" if not compuesta.duplicated().any() else "no",
    }
    return tabla


def cobertura_de_campos(consolidado: pd.DataFrame) -> pd.DataFrame:
    """Qué proporción de las filas trae cada campo del esquema común.

    Un campo que un archivo no publica no es un campo con nulos: es un campo que esa
    población no tiene. La diferencia importa al interpretar cualquier indicador que
    lo use.
    """
    filas = []
    for campo in ESQUEMA:
        serie = consolidado[campo]
        presentes = serie.notna() & serie.astype("string").str.strip().ne("")
        por_fuente = consolidado.groupby("fuente")[campo].apply(
            lambda s: int((s.notna() & s.astype("string").str.strip().ne("")).sum())
        )
        filas.append({
            "campo": campo,
            "presentes": int(presentes.sum()),
            "ausentes": int((~presentes).sum()),
            "cobertura_pct": round(float(safe_ratio(presentes.sum(), len(consolidado),
                                                    scale=100)), 2),
            "fuentes_sin_el_campo": ", ".join(
                sorted(f for f, n in por_fuente.items() if n == 0)
            ) or "—",
        })
    return pd.DataFrame(filas)


# ------------------------------------------------------------------------ resultados
def resumen(consolidado: pd.DataFrame) -> pd.DataFrame:
    """Indicadores del conjunto, con su unidad y su definición."""
    abiertos = consolidado.loc[consolidado["abierto"]]
    return indicator_table({
        "lugares_totales": (len(consolidado), "locales",
                            "Filas consolidadas de los cinco archivos, todas las hojas"),
        "lugares_abiertos": (len(abiertos), "locales",
                             "Excluye las hojas de locales cerrados"),
        "lugares_cerrados": (len(consolidado) - len(abiertos), "locales",
                             "Filas provenientes de una hoja de cerrados"),
        "tipos_de_local": (consolidado["tipo_local"].nunique(), "tipos",
                           "Declarados por el archivo de origen"),
        "comunas_distintas": (abiertos["comuna_clave"].replace("", pd.NA).nunique(),
                              "comunas", "Sobre la comuna normalizada, solo abiertos"),
        "entidades_distintas": (abiertos["entidad_clave"].replace("", pd.NA).nunique(),
                                "entidades", "Sobre la entidad normalizada, solo abiertos"),
        "con_horario_declarado": (
            int(abiertos["horario"].notna().sum()), "locales",
            "El archivo de Puntos bip! no publica horario"),
        "cobertura_horario_pct": (
            float(safe_ratio(abiertos["horario"].notna().sum(), len(abiertos), scale=100)),
            "%", "Proporción de locales abiertos con horario publicado"),
        "coordenadas_sospechosas": (int(consolidado["coordenada_sospechosa"].sum()),
                                    "locales",
                                    f"Desvío entre UTM y lat/lon mayor que {UMBRAL_COORDENADA_M:.0f} m"),
    })


def por_comuna(consolidado: pd.DataFrame) -> pd.DataFrame:
    """Lugares de carga abiertos por comuna, con el desglose por tipo."""
    abiertos = consolidado.loc[consolidado["abierto"]].copy()
    tabla = (abiertos.groupby(["comuna_clave", "tipo_local"], dropna=False)
                     .size().rename("locales").reset_index()
                     .pivot(index="comuna_clave", columns="tipo_local", values="locales")
                     .fillna(0).astype(int))
    tabla["total"] = tabla.sum(axis=1)
    etiquetas = (abiertos.drop_duplicates("comuna_clave")
                         .set_index("comuna_clave")["comuna_etiqueta"])
    tabla.insert(0, "comuna", etiquetas.reindex(tabla.index).to_numpy())
    return tabla.sort_values("total", ascending=False).reset_index()


def por_entidad(consolidado: pd.DataFrame) -> pd.DataFrame:
    """Lugares de carga abiertos por entidad, y en cuántas comunas está cada una."""
    abiertos = consolidado.loc[consolidado["abierto"]]
    tabla = (abiertos.groupby("entidad_clave", dropna=False)
                     .agg(locales=("codigo", "size"),
                          comunas=("comuna_clave", "nunique"),
                          tipos=("tipo_local", "nunique"))
                     .reset_index())
    tabla["locales_por_comuna"] = (
        safe_ratio(tabla["locales"], tabla["comunas"]).round(2)
    )
    return tabla.sort_values("locales", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------- informe
def analizar() -> dict[str, pd.DataFrame]:
    """Ejecuta el caso completo y devuelve todas las tablas de resultado."""
    hojas = cargar()
    consolidado = consolidar(hojas)
    return {
        "lectura": informe_de_lectura(hojas),
        "esquemas": informe_de_esquemas(hojas),
        "cobertura_campos": cobertura_de_campos(consolidado),
        "clave": validar_clave(consolidado),
        "validacion_coordenadas": validar_coordenadas(consolidado),
        "coordenadas_sospechosas": coordenadas_sospechosas(consolidado),
        "resumen": resumen(consolidado),
        "por_comuna": por_comuna(consolidado),
        "por_entidad": por_entidad(consolidado),
    }


def exportar(resultados: dict[str, pd.DataFrame], destino: Path = RESULTS) -> Path:
    """Escribe las tablas de resultado en CSV.

    Son agregados propios, no los datos de terceros: se versionan para que los
    hallazgos estén visibles sin descargar los archivos de origen.
    """
    destino.mkdir(parents=True, exist_ok=True)
    for nombre, tabla in resultados.items():
        tabla.to_csv(destino / f"{nombre}.csv", index=False, encoding="utf-8")
    return destino


def main() -> None:
    from lab.console import enable_utf8

    enable_utf8()
    _exigir_archivos()

    print("=== Fuentes ===")
    for fuente in BIP_SOURCES:
        try:
            procedencia = Provenance.from_path(ORIGINAL / f"{fuente}.xlsx")
            print(f"  {procedencia.summary()}")
        except FileNotFoundError:
            print(f"  {fuente}: sin registro de procedencia")

    resultados = analizar()

    print("\n=== Lo que hubo que hacer para leer cada hoja ===")
    print(resultados["lectura"].to_string(index=False))

    print("\n=== Qué campo aporta cada hoja ===")
    print(resultados["esquemas"].to_string(index=False))

    print("\n=== Cobertura de los campos tras consolidar ===")
    print(resultados["cobertura_campos"].to_string(index=False))

    print("\n=== ¿El código es una clave? ===")
    print(resultados["clave"].to_string(index=False))

    print("\n=== Validación cruzada de las dos coordenadas ===")
    print(resultados["validacion_coordenadas"].to_string(index=False))

    sospechosas = resultados["coordenadas_sospechosas"]
    print(f"\n=== Filas donde las dos coordenadas no coinciden ({len(sospechosas)}) ===")
    if len(sospechosas):
        print(sospechosas[["fuente", "codigo", "comuna", "latitud", "longitud",
                           "latitud_utm", "longitud_utm", "desvio_m"]].to_string(index=False))

    print("\n=== Resumen ===")
    print(resultados["resumen"].to_string(index=False))

    print("\n=== Diez comunas con más lugares de carga ===")
    print(resultados["por_comuna"].head(10).to_string(index=False))

    print("\n=== Entidades ===")
    print(resultados["por_entidad"].head(10).to_string(index=False))

    destino = exportar(resultados)
    try:
        legible = destino.relative_to(ROOT).as_posix()
    except ValueError:
        legible = destino.as_posix()
    print(f"\nTablas escritas en {legible}")


if __name__ == "__main__":
    main()
