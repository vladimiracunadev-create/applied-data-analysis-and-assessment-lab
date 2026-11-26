"""Normalización de texto para poder agrupar y cruzar.

Qué hace
    Convierte texto escrito por personas en una clave comparable: sin tildes, sin
    mayúsculas inconsistentes, sin espacios dobles ni espacios al final, y con las
    abreviaturas habituales de direcciones unificadas.

Por qué existe
    `FULLCARGA` y `Fullcarga` son dos grupos para `groupby` y uno para una persona.
    `CONCHALI` no cruza con `Conchalí`, y `NOMBRE DE FANTASIA ` —con un espacio al
    final, como viene en un archivo público real— no es `NOMBRE DE FANTASIA`. Cada uno
    de esos tres casos rompe un cruce en silencio, sin error y sin aviso.

    Centralizar la normalización asegura que las dos partes de un cruce se normalicen
    con la **misma** regla. Dos reglas parecidas aplicadas a cada lado producen un
    cruce que falla justo en los casos límite, que son los que importan.

Qué NO hace
    No decide que dos registros son la misma entidad. Normalizar es un paso previo;
    la deduplicación es una decisión con criterio declarado, y este módulo solo
    ofrece la medida de parecido para sostenerla.

Cómo se valida
    `tests/test_textual.py` cubre tildes, mayúsculas, espacios, abreviaturas, valores
    nulos y la simetría de la medida de parecido.
"""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

import pandas as pd

#: Abreviaturas de dirección que aparecen escritas de varias formas en el mismo
#: archivo. La correspondencia es deliberadamente corta y explícita: una lista larga
#: de reemplazos automáticos acaba cambiando cosas que no debía.
ABREVIATURAS: dict[str, str] = {
    "AV": "AVENIDA",
    "AVDA": "AVENIDA",
    "AVE": "AVENIDA",
    "STA": "SANTA",
    "STO": "SANTO",
    "GRAL": "GENERAL",
    "PJE": "PASAJE",
    "PSJE": "PASAJE",
    "DEPTO": "DEPARTAMENTO",
    "LOC": "LOCAL",
    "N": "NUMERO",
    "NRO": "NUMERO",
    "S/N": "SIN NUMERO",
}

_ESPACIOS = re.compile(r"\s+")
_NO_ALFANUM = re.compile(r"[^A-Z0-9 ]")


def strip_accents(text: str) -> str:
    """Quita tildes y diéresis conservando la letra base.

    Usa descomposición canónica NFD y descarta las marcas combinantes, de modo que
    `á` queda en `a` y `ñ` en `n`. Es lo que se quiere para una clave de cruce; **no**
    es lo que se quiere para mostrar un nombre a una persona.

    Example:
        >>> strip_accents("Conchalí")
        'Conchali'
    """
    descompuesto = unicodedata.normalize("NFD", text)
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def normalize_key(
    value: object,
    expand_abbreviations: bool = False,
    keep_punctuation: bool = False,
) -> str:
    """Convierte un valor en una clave comparable.

    Pasos, en este orden: a texto, quitar tildes, mayúsculas, quitar puntuación
    (opcional), colapsar espacios, recortar extremos.

    Args:
        value: cualquier valor; los nulos devuelven cadena vacía.
        expand_abbreviations: si expande las abreviaturas de `ABREVIATURAS`. Úselo
            para direcciones, no para nombres de entidad: expandir `N` a `NUMERO` en
            un nombre comercial produce basura.
        keep_punctuation: si conserva los signos. Por defecto se quitan, porque
            `Av. Matta 1200` y `Av Matta 1200` deben dar la misma clave.

    Returns:
        La clave normalizada, o cadena vacía si el valor era nulo.

    Example:
        >>> normalize_key("  Av.  Providencia  1208 ")
        'AV PROVIDENCIA 1208'
        >>> normalize_key("Av. Providencia 1208", expand_abbreviations=True)
        'AVENIDA PROVIDENCIA 1208'
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    texto = str(value)
    if texto.strip().lower() in ("nan", "nat", "none", "<na>"):
        return ""
    texto = strip_accents(texto).upper()
    if not keep_punctuation:
        texto = _NO_ALFANUM.sub(" ", texto)
    texto = _ESPACIOS.sub(" ", texto).strip()
    if expand_abbreviations and texto:
        texto = " ".join(ABREVIATURAS.get(palabra, palabra) for palabra in texto.split(" "))
    return texto


def normalize_series(
    series: pd.Series, expand_abbreviations: bool = False
) -> pd.Series:
    """Aplica `normalize_key` a una serie completa, devolviendo texto."""
    return pd.Series(series).map(
        lambda v: normalize_key(v, expand_abbreviations=expand_abbreviations)
    ).astype("string")


def normalize_label(value: object) -> str:
    """Normaliza para **mostrar**, no para cruzar: conserva tildes y usa capitalización.

    La diferencia con `normalize_key` importa: la clave sirve para agrupar, la etiqueta
    para que una persona lea el resultado. Guardar solo la clave convierte `Conchalí`
    en `CONCHALI` en el informe final, que es un empobrecimiento gratuito.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    texto = _ESPACIOS.sub(" ", str(value)).strip()
    if not texto:
        return ""
    menores = {"de", "del", "la", "las", "los", "y", "el", "en", "a"}
    palabras = texto.lower().split(" ")
    return " ".join(
        p if i and p in menores else p.capitalize() for i, p in enumerate(palabras)
    )


def similarity(left: object, right: object) -> float:
    """Parecido entre dos textos, en el rango [0, 1], sobre sus claves normalizadas.

    Usa `difflib.SequenceMatcher`, que es parte de la biblioteca estándar. No es la
    mejor medida que existe —Jaro-Winkler o la distancia de Levenshtein normalizada
    suelen comportarse mejor con nombres propios— pero no agrega dependencias y es
    suficiente para **proponer** candidatos a revisión.

    Nunca para decidir solo: un umbral de parecido es una heurística, y fusionar dos
    registros es una decisión que alguien tiene que firmar.

    Example:
        >>> round(similarity("Fullcarga", "FULLCARGA"), 3)
        1.0
    """
    a, b = normalize_key(left), normalize_key(right)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def duplicate_candidates(
    frame: pd.DataFrame,
    columns: list[str],
    threshold: float = 0.90,
    max_rows: int = 2000,
) -> pd.DataFrame:
    """Pares de filas que podrían ser el mismo registro, para revisión humana.

    Compara la concatenación normalizada de `columns` entre todos los pares. Es
    cuadrático: con `max_rows` se corta antes de intentar algo que no termina. Para
    volúmenes mayores hay que bloquear por una clave (la comuna, por ejemplo) y
    comparar dentro de cada bloque.

    Args:
        frame: tabla a revisar.
        columns: columnas que definen la identidad del registro.
        threshold: parecido mínimo para proponer el par.
        max_rows: tope de filas; por encima se levanta un error en lugar de colgarse.

    Returns:
        Pares con su parecido, ordenados del más parecido al menos. **Son candidatos**,
        no duplicados confirmados.

    Raises:
        ValueError: si la tabla excede `max_rows` o si falta una columna.
    """
    faltantes = [c for c in columns if c not in frame.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas para comparar: {faltantes}")
    if len(frame) > max_rows:
        raise ValueError(
            f"La tabla tiene {len(frame)} filas y el tope es {max_rows}. La comparación "
            "es cuadrática: bloquee por una clave (por ejemplo la comuna) y compare "
            "dentro de cada bloque."
        )
    claves = frame[columns].astype("string").fillna("").agg(" ".join, axis=1).map(normalize_key)
    indices = list(claves.index)
    filas = []
    for posicion, i in enumerate(indices):
        for j in indices[posicion + 1:]:
            parecido = similarity(claves[i], claves[j])
            if parecido >= threshold:
                filas.append({"fila_a": i, "fila_b": j, "parecido": round(parecido, 4),
                              "texto_a": claves[i], "texto_b": claves[j]})
    columnas = ["fila_a", "fila_b", "parecido", "texto_a", "texto_b"]
    if not filas:
        return pd.DataFrame(columns=columnas)
    return pd.DataFrame(filas, columns=columnas).sort_values(
        "parecido", ascending=False
    ).reset_index(drop=True)


def normalization_report(series: pd.Series, name: str = "") -> pd.DataFrame:
    """Qué cambia al normalizar una columna: el argumento para hacerlo.

    Devuelve el recuento de valores distintos antes y después. Si baja, es porque
    había variantes del mismo valor; esa diferencia es exactamente el número de grupos
    espurios que `groupby` habría creado sobre el texto crudo.
    """
    cruda = pd.Series(series).astype("string")
    normalizada = normalize_series(cruda)
    distintos_antes = int(cruda.dropna().nunique())
    distintos_despues = int(normalizada.replace("", pd.NA).dropna().nunique())
    return pd.DataFrame(
        [
            ("columna", name or (series.name or "sin nombre"), ""),
            ("filas", len(cruda), "filas"),
            ("distintos_sin_normalizar", distintos_antes, "valores"),
            ("distintos_normalizados", distintos_despues, "valores"),
            ("grupos_espurios_evitados", distintos_antes - distintos_despues, "grupos"),
            ("vacios_tras_normalizar", int((normalizada == "").sum()), "filas"),
        ],
        columns=["indicador", "valor", "unidad"],
    )


def merge_audit(
    series: pd.Series,
    name: str = "",
    expand_abbreviations: bool = False,
) -> pd.DataFrame:
    """Qué fusionó la normalización, fusión por fusión, para poder verificarla.

    Args:
        series: la columna en su forma cruda.
        name: nombre para el informe.
        expand_abbreviations: si se expanden las abreviaturas declaradas.

    Returns:
        Una fila por clave normalizada que agrupa **más de una** forma cruda, con las
        formas que absorbió y cuántas filas aporta cada una. Vacía si la normalización
        no fusionó nada, que también es un resultado.

    Por qué hace falta
        `normalization_report` cuenta **cuántos** grupos espurios se evitaron, que es
        el argumento a favor de normalizar. Esta función responde la pregunta opuesta,
        que es la que nadie hace: **¿alguna de esas fusiones estaba mal?**

        Normalizar tiene dos direcciones de error y solo una se mide. Dejar separado lo
        que es igual —`FULLCARGA` y `Fullcarga`— infla el número de grupos, y se nota
        porque aparecen dos filas donde debería haber una. Juntar lo que es distinto no
        se nota de ninguna manera: produce un grupo menos, con un total mayor, y
        perfectamente verosímil.

        La expansión de abreviaturas es el caso de riesgo: `AV` por `AVENIDA` es
        inofensivo hasta que una entidad se llama literalmente `AV`. Por eso esta
        función existe y por eso devuelve las formas crudas en lugar de un recuento.

    Qué hacer con el resultado
        Leerlo. Cada fila es una afirmación de que dos textos distintos nombran la misma
        cosa, y es la única parte de la normalización que una persona tiene que
        confirmar. Son pocas filas: en datos reales la normalización suele fusionar
        mucho menos de lo que se teme.
    """
    cruda = pd.Series(series).astype("string")
    claves = cruda.map(lambda v: normalize_key(v, expand_abbreviations=expand_abbreviations))
    tabla = pd.DataFrame({"clave": claves, "cruda": cruda}).dropna(subset=["cruda"])
    tabla = tabla.loc[tabla["clave"] != ""]

    filas = []
    for clave, grupo in tabla.groupby("clave", observed=True):
        formas = grupo["cruda"].value_counts()
        if len(formas) < 2:
            continue
        filas.append({
            "columna": name or (series.name or "sin nombre"),
            "clave_normalizada": clave,
            "formas_crudas": int(len(formas)),
            "formas": " | ".join(f"{texto} ({cuenta})" for texto, cuenta in formas.items()),
            "filas_afectadas": int(formas.sum()),
        })

    columnas = ["columna", "clave_normalizada", "formas_crudas", "formas", "filas_afectadas"]
    if not filas:
        return pd.DataFrame(columns=columnas)
    return pd.DataFrame(filas, columns=columnas).sort_values(
        ["formas_crudas", "filas_afectadas"], ascending=[False, False]
    ).reset_index(drop=True)
