"""Puente SQL: ejecutar SQL real sobre DataFrames para validar de forma independiente.

Qué hace
    Carga un conjunto de DataFrames en una base SQLite en memoria (módulo `sqlite3`
    de la biblioteca estándar, sin dependencias nuevas) y permite consultarlos con
    SQL. Si DuckDB está instalado, se puede usar como motor alternativo.

Por qué existe
    La forma más honesta de validar un indicador calculado en Pandas es recalcularlo
    con otra tecnología y comparar. SQL es la segunda implementación natural: su
    semántica de `JOIN`, `GROUP BY` y `COUNT(col)` frente a `COUNT(*)` es distinta de
    la de Pandas, de modo que un acuerdo entre ambas es evidencia real, no una
    tautología.

Cómo se valida
    `tests/test_sqlbridge.py` compara agregaciones SQL contra las de Pandas sobre los
    datos sintéticos del laboratorio, incluido el caso de claves desconocidas.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager

import pandas as pd

#: Nombre de tabla admitido en SQLite sin necesidad de comillas.
_SAFE_NAME = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")


def _check_name(name: str) -> str:
    if not name or name[0].isdigit() or not set(name) <= _SAFE_NAME:
        raise ValueError(
            f"Nombre de tabla inválido: {name!r}. Use letras, dígitos y guion bajo."
        )
    return name


@contextmanager
def sqlite_tables(tables: Mapping[str, pd.DataFrame]) -> Iterator[sqlite3.Connection]:
    """Contexto con una base SQLite en memoria que contiene las tablas indicadas.

    Args:
        tables: `{nombre_tabla: DataFrame}`. Los nombres se validan para evitar
            inyección por identificador.

    Yields:
        Conexión abierta. Se cierra al salir del contexto.

    Example:
        >>> import pandas as pd
        >>> with sqlite_tables({"t": pd.DataFrame({"a": [1, 2]})}) as con:
        ...     pd.read_sql_query("SELECT SUM(a) AS s FROM t", con).s.iloc[0]
        3
    """
    con = sqlite3.connect(":memory:")
    try:
        for name, df in tables.items():
            frame = df.copy()
            for column in frame.columns:
                if pd.api.types.is_datetime64_any_dtype(frame[column]):
                    # SQLite no tiene tipo fecha: se almacena ISO-8601, que ordena
                    # y compara correctamente como texto.
                    frame[column] = frame[column].dt.strftime("%Y-%m-%d %H:%M:%S")
            frame.to_sql(_check_name(name), con, index=False)
        yield con
    finally:
        con.close()


def query(tables: Mapping[str, pd.DataFrame], sql: str) -> pd.DataFrame:
    """Ejecuta una consulta SQL sobre los DataFrames entregados.

    Args:
        tables: tablas disponibles para la consulta.
        sql: consulta `SELECT`. Se rechazan sentencias de modificación porque este
            puente existe para validar, no para transformar el estado.

    Returns:
        Resultado como DataFrame.

    Raises:
        ValueError: si la consulta no es de solo lectura.
    """
    stripped = sql.strip().lstrip("(").lstrip().lower()
    if not (stripped.startswith("select") or stripped.startswith("with")):
        raise ValueError("Solo se admiten consultas SELECT o WITH … SELECT.")
    forbidden = (" insert ", " update ", " delete ", " drop ", " alter ", " attach ")
    padded = f" {sql.lower().replace(chr(10), ' ')} "
    for token in forbidden:
        if token in padded:
            raise ValueError(f"Sentencia no permitida en el puente de validación: {token.strip()}")
    with sqlite_tables(tables) as con:
        return pd.read_sql_query(sql, con)


def cross_check(
    expected: pd.DataFrame,
    actual: pd.DataFrame,
    keys: list[str],
    value_columns: list[str],
    tolerance: float = 1e-9,
) -> pd.DataFrame:
    """Compara dos resultados fila a fila y devuelve solo las diferencias.

    Args:
        expected: resultado de referencia (por ejemplo, el de Pandas).
        actual: resultado a comprobar (por ejemplo, el de SQL).
        keys: columnas que identifican la fila en ambos resultados.
        value_columns: columnas numéricas a comparar.
        tolerance: diferencia absoluta máxima tolerada. Existe porque una suma de
            flotantes en distinto orden puede diferir en el último bit; una
            diferencia mayor es un error real, no ruido de punto flotante.

    Returns:
        Tabla con las filas discrepantes y la diferencia por columna. Vacía si
        ambos resultados coinciden.
    """
    merged = expected.merge(actual, on=keys, how="outer", suffixes=("_esperado", "_obtenido"))
    problems = []
    for column in value_columns:
        left, right = f"{column}_esperado", f"{column}_obtenido"
        if left not in merged or right not in merged:
            raise KeyError(f"La columna {column!r} no está en ambos resultados.")
        diff = pd.to_numeric(merged[left], errors="coerce") - pd.to_numeric(
            merged[right], errors="coerce"
        )
        bad = merged.loc[diff.abs().gt(tolerance) | diff.isna()].copy()
        if not bad.empty:
            bad["columna"] = column
            bad["diferencia"] = diff.loc[bad.index]
            problems.append(bad[keys + ["columna", left, right, "diferencia"]].rename(
                columns={left: "esperado", right: "obtenido"}
            ))
    if not problems:
        return pd.DataFrame(columns=keys + ["columna", "esperado", "obtenido", "diferencia"])
    return pd.concat(problems, ignore_index=True)


def duckdb_available() -> bool:
    """Indica si DuckDB está instalado, para decidir si se usa el motor alternativo."""
    try:  # pragma: no cover - depende del entorno
        import duckdb  # noqa: F401
    except ImportError:
        return False
    return True
