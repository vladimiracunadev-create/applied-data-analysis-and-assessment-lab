"""Análisis de claves: qué identifica una fila, y qué hacer cuando nada lo hace.

Qué hace
    Busca de forma exhaustiva las combinaciones mínimas de columnas que identifican una
    fila, informa por qué cada columna candidata falla, y construye una clave subrogada
    determinista a partir de los campos que se declaren como identificadores.

Por qué existe
    «¿Cuál es la clave de esta tabla?» es la primera pregunta de cualquier cruce y casi
    nunca tiene respuesta escrita. La respuesta habitual —«el campo que se llama
    `codigo`»— es una suposición, y cuando es falsa no falla al cruzar: multiplica filas
    o colapsa diferencias. Ver el registro `clave-que-no-es-clave`.

    Medirlo cuesta poco y hay que hacerlo **antes** de usar la columna, no cuando los
    totales no cuadran.

Las tres cosas que distingue, y que suelen confundirse
    1. **Una columna sin repetidos** no es una clave si admite nulos: dos filas con el
       valor ausente no se distinguen entre sí.
    2. **Una clave candidata** es un conjunto de columnas sin nulos y sin repetidos.
       Puede haber varias, y las interesantes son las **mínimas**: las que dejan de ser
       únicas si se les quita cualquier columna.
    3. **Una clave candidata no es necesariamente una buena clave.** Que una
       combinación resulte única en los datos de hoy no la vuelve un identificador:
       depende de si los campos que la componen son estables. Una clave que incluye una
       coordenada medida o una dirección escrita a mano cambia cuando alguien vuelve a
       medir o corrige una falta de ortografía.

    La tercera es la que este módulo insiste en no esconder: `candidate_keys` devuelve
    hechos sobre los datos, y la decisión de cuál usar —o de no usar ninguna— sigue
    siendo de quien conoce el dominio.

Sobre la clave subrogada
    Cuando no hay clave natural sólida, la salida es una clave subrogada: un
    identificador derivado de forma determinista de los campos que se **declaren** como
    identificadores. Tiene dos propiedades que importan y una limitación que hay que
    decir:

    - es **determinista**: el mismo contenido produce el mismo identificador en
      cualquier máquina y en cualquier ejecución, a diferencia de un número de fila;
    - **verifica sus propias colisiones**: si dos filas distintas producen el mismo
      identificador, `surrogate_key` levanta un error en lugar de devolver duplicados;
    - **hereda la inestabilidad de sus campos**. Si uno de los campos declarados
       cambia entre dos publicaciones, el identificador cambia y la fila parece nueva.
       No hay forma de evitarlo sin un identificador provisto por la fuente.

Cómo se valida
    `tests/test_keys.py` prueba la búsqueda exhaustiva contra tablas con la respuesta
    conocida, la minimalidad de las claves devueltas, el rechazo de columnas con nulos,
    el determinismo de la clave subrogada entre ejecuciones y la detección de colisiones.
"""

from __future__ import annotations

import hashlib
from itertools import combinations

import pandas as pd

#: Largo del identificador subrogado, en caracteres hexadecimales. 16 caracteres son
#: 64 bits: con un millón de filas la probabilidad de colisión accidental es del orden
#: de 10⁻⁸. Y de todos modos se comprueba, de modo que el largo es una cuestión de
#: comodidad y no de corrección.
LARGO_ID = 16

#: Máximo de columnas que `candidate_keys` combina. Crece como el binomio, de modo que
#: subirlo tiene costo: con 12 columnas, tamaño 4 son 495 combinaciones y tamaño 6 son
#: 924. El tope existe para que una llamada distraída no se cuelgue.
MAX_COMBINACION = 4

#: Separador entre los valores que forman la clave subrogada. Se elige un carácter que
#: no aparece en datos de texto para que `A|B` y `AB|` no produzcan el mismo digesto:
#: sin separador seguro, dos filas distintas pueden generar la misma cadena.
SEPARADOR = "\x1f"


def key_report(frame: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """Diagnóstico por columna: nulos, distintos, repetidos, y si sirve de clave.

    Args:
        frame: la tabla a evaluar.
        columns: columnas a evaluar. Por defecto, todas.

    Returns:
        Una fila por columna, ordenada de la más cercana a ser clave a la más lejana,
        con la columna `por_que_no` que dice qué le falta.

    Raises:
        ValueError: si alguna columna pedida no existe.

    Se informa `por_que_no` y no solo un booleano porque las dos causas piden acciones
    distintas: una columna con nulos necesita que se complete o que se decida qué
    significa el vacío; una con repetidos necesita que se averigüe **qué** identifica.
    """
    columnas = list(columns) if columns is not None else list(frame.columns)
    faltantes = [c for c in columnas if c not in frame.columns]
    if faltantes:
        raise ValueError(f"No existen estas columnas: {faltantes}")

    filas = []
    for columna in columnas:
        serie = frame[columna]
        nulos = int(serie.isna().sum())
        distintos = int(serie.nunique(dropna=True))
        repetidos = int(serie.dropna().duplicated().sum())
        if nulos and repetidos:
            motivo = "tiene nulos y repetidos"
        elif nulos:
            motivo = "tiene nulos: dos ausencias no se distinguen entre sí"
        elif repetidos:
            motivo = "tiene valores repetidos"
        else:
            motivo = ""
        filas.append({
            "columna": columna,
            "filas": int(len(frame)),
            "nulos": nulos,
            "distintos": distintos,
            "repetidos": repetidos,
            "es_clave": "sí" if not motivo else "no",
            "por_que_no": motivo,
        })
    tabla = pd.DataFrame(filas)
    return tabla.sort_values(
        ["es_clave", "nulos", "repetidos"], ascending=[False, True, True]
    ).reset_index(drop=True)


def candidate_keys(
    frame: pd.DataFrame,
    columns: list[str] | None = None,
    max_size: int = MAX_COMBINACION,
) -> pd.DataFrame:
    """Las combinaciones **mínimas** de columnas que identifican una fila.

    Args:
        frame: la tabla a evaluar.
        columns: columnas candidatas. Por defecto, todas.
        max_size: máximo de columnas por combinación.

    Returns:
        Una fila por clave candidata mínima, con sus columnas y su tamaño. Vacía si
        ninguna combinación de hasta `max_size` columnas identifica una fila, que es un
        resultado y no un fallo.

    Raises:
        ValueError: si `max_size` es menor que 1 o alguna columna no existe.

    Sobre la minimalidad: si `A + B` es clave, entonces `A + B + C` también lo es, y
    devolver las dos no aporta nada. Se devuelven solo las mínimas, de modo que la tabla
    se puede leer. Una combinación con nulos se descarta de entrada: no identifica.
    """
    if max_size < 1:
        raise ValueError(f"max_size debe ser al menos 1; recibió {max_size}.")
    columnas = list(columns) if columns is not None else list(frame.columns)
    faltantes = [c for c in columnas if c not in frame.columns]
    if faltantes:
        raise ValueError(f"No existen estas columnas: {faltantes}")

    # Una columna con nulos no puede formar parte de una clave, de modo que se descarta
    # antes de combinar: ahorra la mayor parte del trabajo.
    utilizables = [c for c in columnas if not frame[c].isna().any()]

    minimas: list[tuple[str, ...]] = []
    for tamano in range(1, max_size + 1):
        for combo in combinations(utilizables, tamano):
            # Si ya contiene una clave mínima, no es mínima.
            if any(set(previa).issubset(combo) for previa in minimas):
                continue
            if not frame[list(combo)].duplicated().any():
                minimas.append(combo)

    if not minimas:
        return pd.DataFrame(columns=["columnas", "tamano", "combinaciones_evaluadas"])
    return pd.DataFrame([
        {
            "columnas": " + ".join(combo),
            "tamano": len(combo),
            "combinaciones_evaluadas": len(utilizables),
        }
        for combo in sorted(minimas, key=lambda c: (len(c), c))
    ])


def surrogate_key(
    frame: pd.DataFrame,
    columns: list[str],
    prefix: str = "",
    length: int = LARGO_ID,
) -> pd.Series:
    """Identificador determinista derivado de los campos declarados como identidad.

    Args:
        frame: la tabla.
        columns: los campos que **se declaran** como identificadores. El orden no altera
            el resultado: se ordenan para que dos llamadas con las mismas columnas en
            distinto orden produzcan el mismo identificador.
        prefix: prefijo legible, por ejemplo `"bip-"`.
        length: caracteres hexadecimales del digesto.

    Returns:
        Serie de identificadores alineada con el índice de `frame`.

    Raises:
        ValueError: si falta una columna, si `length` está fuera de 4 a 64, o si dos
            filas con **contenido distinto** producen el mismo identificador.

    Sobre el error por colisión: no se devuelve una clave con duplicados. Si los campos
    declarados no distinguen dos filas, el problema es la declaración, no el hash, y hay
    que resolverlo antes de seguir. El mensaje dice cuántas filas colisionan.

    Las filas con **contenido idéntico** en los campos declarados reciben el mismo
    identificador y eso no es una colisión: son el mismo registro repetido, y el
    identificador lo delata.

    Example:
        >>> frame = pd.DataFrame({"a": ["x", "y"], "b": [1, 2]})
        >>> surrogate_key(frame, ["a", "b"], prefix="id-").str.len().tolist()
        [19, 19]
    """
    faltantes = [c for c in columns if c not in frame.columns]
    if faltantes:
        raise ValueError(f"No existen estas columnas: {faltantes}")
    if not 4 <= length <= 64:
        raise ValueError(f"length debe estar entre 4 y 64; recibió {length}.")
    if not columns:
        raise ValueError("Hay que declarar al menos una columna de identidad.")

    ordenadas = sorted(columns)
    partes = [
        frame[columna].astype("string").fillna("\x00").astype(str)
        for columna in ordenadas
    ]
    contenido = partes[0]
    for parte in partes[1:]:
        contenido = contenido + SEPARADOR + parte

    identificadores = contenido.map(
        lambda texto: prefix + hashlib.sha256(texto.encode("utf-8")).hexdigest()[:length]
    )

    # Una colisión real es dos contenidos distintos con el mismo identificador. Dos
    # filas con el mismo contenido comparten identificador legítimamente.
    por_id = pd.DataFrame({"id": identificadores, "contenido": contenido})
    contenidos_por_id = por_id.groupby("id")["contenido"].nunique()
    colisiones = contenidos_por_id[contenidos_por_id > 1]
    if len(colisiones):
        raise ValueError(
            f"La clave subrogada tiene {len(colisiones)} colisión(es) con contenido "
            f"distinto sobre {len(frame)} filas. Suba `length` o revise los campos "
            f"declarados: {ordenadas}"
        )
    return identificadores.rename("id")


def surrogate_report(
    frame: pd.DataFrame, columns: list[str], prefix: str = ""
) -> pd.DataFrame:
    """Qué consigue la clave subrogada: unicidad, repetidos de contenido y estabilidad.

    Devuelve la cuenta de identificadores distintos y, sobre todo, cuántas filas
    comparten identificador por tener **contenido idéntico** en los campos declarados.
    Esas filas son duplicados exactos respecto de la definición de identidad elegida, y
    descubrirlo es parte del valor de construir la clave.
    """
    identificadores = surrogate_key(frame, columns, prefix=prefix)
    repetidos = int(identificadores.duplicated().sum())
    return pd.DataFrame(
        [
            ("campos_declarados", " + ".join(sorted(columns)), ""),
            ("filas", len(frame), "filas"),
            ("identificadores_distintos", int(identificadores.nunique()), "ids"),
            ("filas_con_identidad_repetida", repetidos, "filas"),
            (
                "es_clave",
                "sí" if repetidos == 0 else "no",
                "sí significa que los campos declarados distinguen cada fila",
            ),
        ],
        columns=["indicador", "valor", "unidad"],
    )
