"""Pruebas del puente SQL (`lab.sqlbridge`)."""

from __future__ import annotations

import sqlite3

import pandas as pd
import pytest

from lab.sqlbridge import cross_check, query, sqlite_tables


def test_query_ejecuta_agregaciones_sobre_dataframes():
    tablas = {"t": pd.DataFrame({"g": ["a", "a", "b"], "v": [1, 2, 10]})}
    resultado = query(tablas, "SELECT g, SUM(v) AS total FROM t GROUP BY g ORDER BY g")
    assert resultado.total.tolist() == [3, 10]


def test_query_admite_with_y_joins():
    tablas = {
        "viajes": pd.DataFrame({"id": [1, 2, 3], "ruta": ["R1", "R1", "R9"]}),
        "rutas": pd.DataFrame({"ruta": ["R1"], "operador": ["A"]}),
    }
    sql = """
    WITH base AS (SELECT v.id, r.operador FROM viajes v LEFT JOIN rutas r ON r.ruta = v.ruta)
    SELECT COUNT(*) AS filas, COUNT(operador) AS con_operador FROM base
    """
    fila = query(tablas, sql).iloc[0]
    # COUNT(*) cuenta filas; COUNT(columna) ignora los nulos. La diferencia es
    # exactamente el número de claves desconocidas.
    assert fila.filas == 3 and fila.con_operador == 2


def test_query_rechaza_sentencias_que_no_son_de_lectura():
    tablas = {"t": pd.DataFrame({"a": [1]})}
    for sql in ("DELETE FROM t", "DROP TABLE t", "UPDATE t SET a = 2"):
        with pytest.raises(ValueError):
            query(tablas, sql)


def test_query_rechaza_sentencias_encubiertas_tras_un_select():
    tablas = {"t": pd.DataFrame({"a": [1]})}
    with pytest.raises(ValueError, match="no permitida"):
        query(tablas, "SELECT 1; drop table t")


def test_nombre_de_tabla_invalido_se_rechaza():
    with pytest.raises(ValueError, match="Nombre de tabla inválido"):
        query({"t; drop table x": pd.DataFrame({"a": [1]})}, "SELECT 1 AS a")
    with pytest.raises(ValueError, match="Nombre de tabla inválido"):
        query({"1tabla": pd.DataFrame({"a": [1]})}, "SELECT 1 AS a")


def test_las_fechas_se_guardan_en_iso_y_siguen_ordenando_bien():
    frame = pd.DataFrame({"f": pd.to_datetime(["2026-10-02 10:00", "2026-01-05 09:00"])})
    resultado = query({"t": frame}, "SELECT MIN(f) AS primera, MAX(f) AS ultima FROM t")
    assert resultado.primera.iloc[0] == "2026-01-05 09:00:00"
    assert resultado.ultima.iloc[0] == "2026-10-02 10:00:00"


def test_sqlite_tables_abre_y_cierra_la_conexion():
    with sqlite_tables({"t": pd.DataFrame({"a": [1, 2]})}) as con:
        assert pd.read_sql_query("SELECT COUNT(*) AS n FROM t", con).n.iloc[0] == 2
    with pytest.raises(sqlite3.ProgrammingError):
        con.execute("SELECT 1")


def test_cross_check_vacio_cuando_los_resultados_coinciden():
    esperado = pd.DataFrame({"k": ["a", "b"], "v": [1.0, 2.0]})
    obtenido = pd.DataFrame({"k": ["b", "a"], "v": [2.0, 1.0]})
    assert cross_check(esperado, obtenido, ["k"], ["v"]).empty


def test_cross_check_reporta_la_diferencia_y_respeta_la_tolerancia():
    esperado = pd.DataFrame({"k": ["a"], "v": [1.0]})
    obtenido = pd.DataFrame({"k": ["a"], "v": [1.0 + 1e-12]})
    assert cross_check(esperado, obtenido, ["k"], ["v"], tolerance=1e-9).empty

    distinto = pd.DataFrame({"k": ["a"], "v": [1.5]})
    diferencias = cross_check(esperado, distinto, ["k"], ["v"])
    assert len(diferencias) == 1
    assert diferencias.diferencia.iloc[0] == pytest.approx(-0.5)
    assert diferencias.columna.iloc[0] == "v"


def test_cross_check_detecta_filas_que_faltan_en_un_lado():
    esperado = pd.DataFrame({"k": ["a", "b"], "v": [1.0, 2.0]})
    obtenido = pd.DataFrame({"k": ["a"], "v": [1.0]})
    diferencias = cross_check(esperado, obtenido, ["k"], ["v"])
    assert diferencias.k.tolist() == ["b"]


def test_cross_check_exige_que_la_columna_exista_en_ambos_resultados():
    esperado = pd.DataFrame({"k": ["a"], "v": [1.0]})
    with pytest.raises(KeyError, match="no está en ambos"):
        cross_check(esperado, esperado, ["k"], ["inexistente"])
