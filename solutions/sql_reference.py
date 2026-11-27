"""Implementación independiente de los indicadores de transporte, en SQL.

Qué hace
    Calcula los mismos indicadores que `solutions/reference.py`, pero cargando los
    CSV **como texto** en SQLite y haciendo toda la limpieza, el casteo y la
    agregación en SQL. Es la implementación independiente que permite validar la de
    Pandas.

Por qué esta implementación es realmente independiente
    No reutiliza una sola línea de `reference.py`. Parte de los mismos archivos
    crudos y aplica las reglas del diccionario de datos con otra semántica: el casteo
    es `CAST` en lugar de `pd.to_numeric`, el cruce es `LEFT JOIN` en lugar de
    `merge`, la fecha se interpreta con `strftime`/`julianday` en lugar de
    `pd.to_datetime`, y los nulos se tratan con `NULLIF`/`IS NULL` en lugar de
    `isna`. Si ambas coinciden, el acuerdo es informativo; si difieren, hay un error
    real en alguna de las dos.

Decisiones explícitas que replican el diccionario de datos
    1. Se eliminan duplicados exactos antes de contar (`SELECT DISTINCT`).
    2. Las claves desconocidas se excluyen de los indicadores por recorrido y se
       reportan aparte.
    3. Un viaje realizado con pasajeros nulo o negativo se conserva para indicadores
       operacionales y se excluye de las sumas de pasajeros.
    4. Los cancelados se excluyen de duración y demanda.
    5. Cumplimiento = realizados / programados, sin recortar a 100 %.

Mediana y percentil 90
    No se calculan aquí. SQLite no tiene una función de percentil con interpolación
    lineal, y reimplementarla en SQL produciría una tercera convención distinta. Esos
    dos indicadores se validan con `lab.metrics.percentile` contra una
    implementación en Python puro dentro de `tests/test_cross_validation.py`.

Uso
    python solutions/sql_reference.py 1
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lab.console import enable_utf8  # noqa: E402
from lab.sqlbridge import query  # noqa: E402

#: Tablas crudas leídas como texto. `dtype=str` es deliberado: así SQL recibe los
#: datos tal como están en el archivo y debe resolver él mismo los vacíos y los
#: valores no numéricos, igual que haría un gestor de datos frente al CSV original.
RAW_TABLES = ("viajes", "recorridos", "operadores", "programacion")

#: Viajes sin duplicados exactos, con tipos ya resueltos y banderas de validez.
#: Se usa como expresión común en todas las consultas siguientes.
_BASE_CTE = """
WITH viajes_unicos AS (
    SELECT DISTINCT viaje_id, recorrido_id, inicio, fin, pasajeros, estado
    FROM viajes
),
viajes_tipadas AS (
    SELECT
        v.viaje_id,
        v.recorrido_id,
        NULLIF(TRIM(v.inicio), '')                       AS inicio,
        NULLIF(TRIM(v.fin), '')                          AS fin,
        CAST(NULLIF(TRIM(v.pasajeros), '') AS REAL)      AS pasajeros,
        v.estado,
        r.operador_id                                    AS operador_id,
        o.operador                                       AS operador,
        CAST(r.meta_min AS REAL)                         AS meta_min,
        CASE WHEN v.estado = 'REALIZADO' THEN 1 ELSE 0 END AS realizado,
        -- Duración en minutos a partir de SEGUNDOS ENTEROS, no de julianday.
        -- julianday devuelve días en punto flotante: (fin - inicio) * 1440 produce
        -- 42.999999971 donde el valor real es 43, y la comparación 'duración <= meta'
        -- se invierte justo en los empates. Con strftime('%s') la resta es exacta.
        CASE
            WHEN NULLIF(TRIM(v.inicio), '') IS NULL OR NULLIF(TRIM(v.fin), '') IS NULL
                THEN NULL
            ELSE (CAST(strftime('%s', NULLIF(TRIM(v.fin), '')) AS INTEGER)
                  - CAST(strftime('%s', NULLIF(TRIM(v.inicio), '')) AS INTEGER)) / 60.0
        END                                              AS duracion_min
    FROM viajes_unicos v
    LEFT JOIN recorridos r ON r.recorrido_id = v.recorrido_id
    LEFT JOIN operadores o ON o.operador_id  = r.operador_id
),
viajes_marcadas AS (
    SELECT
        *,
        CASE WHEN pasajeros IS NULL OR pasajeros < 0 THEN 1 ELSE 0 END      AS pasajeros_invalido,
        CASE WHEN duracion_min IS NULL OR duracion_min < 0 THEN 1 ELSE 0 END AS duracion_invalida,
        CASE WHEN operador_id IS NULL THEN 1 ELSE 0 END                      AS clave_desconocida
    FROM viajes_tipadas
),
-- Base operacional: realizados con clave conocida. Conserva los viajes con
-- pasajeros inválidos, porque el viaje ocurrió aunque el conteo falte.
base AS (
    SELECT * FROM viajes_marcadas
    WHERE realizado = 1 AND clave_desconocida = 0
)
"""

QUERIES: dict[str, str] = {
    # ------------------------------------------------------------------ calidad
    "calidad": _BASE_CTE + """
    SELECT 'filas_originales' AS indicador, (SELECT COUNT(*) FROM viajes) AS valor
    UNION ALL
    SELECT 'duplicados_exactos',
           (SELECT COUNT(*) FROM viajes) - (SELECT COUNT(*) FROM viajes_unicos)
    UNION ALL
    SELECT 'claves_desconocidas', (SELECT SUM(clave_desconocida) FROM viajes_marcadas)
    UNION ALL
    SELECT 'pasajeros_invalidos_realizados',
           (SELECT SUM(pasajeros_invalido) FROM viajes_marcadas WHERE realizado = 1)
    UNION ALL
    SELECT 'duracion_invalida_realizados',
           (SELECT SUM(duracion_invalida) FROM viajes_marcadas WHERE realizado = 1)
    """,
    # ------------------------------------------------------------------ demanda
    "demanda": _BASE_CTE + """
    SELECT operador,
           SUM(pasajeros)    AS pasajeros,
           COUNT(viaje_id)   AS viajes_con_dato
    FROM base
    WHERE pasajeros_invalido = 0
    GROUP BY operador
    ORDER BY operador
    """,
    "demanda_hora": _BASE_CTE + """
    SELECT CAST(strftime('%H', inicio) AS INTEGER) AS hora,
           SUM(pasajeros)                          AS pasajeros
    FROM base
    WHERE pasajeros_invalido = 0
    GROUP BY hora
    ORDER BY hora
    """,
    # ----------------------------------------------------------------- duración
    "duracion": _BASE_CTE + """
    SELECT recorrido_id,
           AVG(duracion_min)                                                AS media_min,
           100.0 * SUM(CASE WHEN duracion_min <= meta_min THEN 1 ELSE 0 END)
                 / COUNT(*)                                                 AS puntualidad_pct,
           COUNT(*)                                                         AS viajes
    FROM base
    WHERE duracion_invalida = 0
    GROUP BY recorrido_id
    ORDER BY recorrido_id
    """,
    # -------------------------------------------------------------- cumplimiento
    # FULL OUTER JOIN emulado con UNION de dos LEFT JOIN: conserva días programados
    # sin viajes y viajes en días no programados, que son dos defectos distintos.
    "cumplimiento": _BASE_CTE + """
    , realizados_dia AS (
        SELECT recorrido_id,
               CAST(strftime('%d', inicio) AS INTEGER) AS dia_octubre,
               COUNT(*)                                AS realizados
        FROM base
        GROUP BY recorrido_id, dia_octubre
    ),
    prog AS (
        SELECT recorrido_id,
               CAST(dia_octubre AS INTEGER)       AS dia_octubre,
               CAST(viajes_programados AS INTEGER) AS viajes_programados
        FROM programacion
    )
    SELECT p.recorrido_id AS recorrido_id, p.dia_octubre AS dia_octubre,
           p.viajes_programados AS viajes_programados,
           COALESCE(d.realizados, 0) AS realizados,
           CASE WHEN p.viajes_programados > 0
                THEN 100.0 * COALESCE(d.realizados, 0) / p.viajes_programados END AS cumplimiento_pct
    FROM prog p LEFT JOIN realizados_dia d
        ON d.recorrido_id = p.recorrido_id AND d.dia_octubre = p.dia_octubre
    UNION ALL
    SELECT d.recorrido_id AS recorrido_id, d.dia_octubre AS dia_octubre,
           NULL AS viajes_programados, d.realizados AS realizados,
           NULL AS cumplimiento_pct
    FROM realizados_dia d LEFT JOIN prog p
        ON d.recorrido_id = p.recorrido_id AND d.dia_octubre = p.dia_octubre
    WHERE p.recorrido_id IS NULL
    ORDER BY recorrido_id, dia_octubre
    """,
    "cumplimiento_operador": _BASE_CTE + """
    , realizados_dia AS (
        SELECT recorrido_id,
               CAST(strftime('%d', inicio) AS INTEGER) AS dia_octubre,
               COUNT(*)                                AS realizados
        FROM base
        GROUP BY recorrido_id, dia_octubre
    ),
    prog AS (
        SELECT recorrido_id,
               CAST(dia_octubre AS INTEGER)        AS dia_octubre,
               CAST(viajes_programados AS INTEGER) AS viajes_programados
        FROM programacion
    )
    SELECT o.operador,
           SUM(COALESCE(d.realizados, 0)) AS realizados,
           SUM(p.viajes_programados)      AS viajes_programados,
           100.0 * SUM(COALESCE(d.realizados, 0)) / SUM(p.viajes_programados) AS cumplimiento_pct
    FROM prog p
    JOIN recorridos r ON r.recorrido_id = p.recorrido_id
    JOIN operadores o ON o.operador_id  = r.operador_id
    LEFT JOIN realizados_dia d
        ON d.recorrido_id = p.recorrido_id AND d.dia_octubre = p.dia_octubre
    GROUP BY o.operador
    ORDER BY o.operador
    """,
    "realizados_recorrido": _BASE_CTE + """
    SELECT recorrido_id, COUNT(*) AS realizados
    FROM base
    GROUP BY recorrido_id
    ORDER BY recorrido_id
    """,
}


def load_raw(case: int, root: Path = ROOT) -> dict[str, pd.DataFrame]:
    """Carga los CSV del caso como texto, sin inferir tipos.

    Raises:
        FileNotFoundError: si falta algún archivo del caso. Ejecute primero
            `python scripts/generate_data.py`.
    """
    folder = root / "data" / f"case_{case}"
    tables: dict[str, pd.DataFrame] = {}
    for name in RAW_TABLES:
        path = folder / f"{name}.csv"
        if not path.exists():
            raise FileNotFoundError(
                f"No existe {path}. Genere los datos con 'python scripts/generate_data.py'."
            )
        tables[name] = pd.read_csv(path, dtype=str, keep_default_na=False)
    return tables


def analyze(case: int, root: Path = ROOT) -> dict[str, pd.DataFrame]:
    """Calcula todos los indicadores del caso usando exclusivamente SQL.

    Args:
        case: número de caso (1, 2 o 3).
        root: raíz del repositorio.

    Returns:
        Un diccionario con las mismas claves que `solutions.reference.analyze`,
        excepto `demanda` y `duracion`, que no incluyen mediana ni P90 (ver el
        encabezado del módulo).
    """
    if case not in (1, 2, 3):
        raise ValueError(f"Caso inválido: {case!r}. Use 1, 2 o 3.")
    tables = load_raw(case, root=root)
    return {name: query(tables, sql) for name, sql in QUERIES.items()}


if __name__ == "__main__":  # pragma: no cover - utilidad de consola
    enable_utf8()
    if len(sys.argv) < 2:
        print("Uso: python solutions/sql_reference.py <1|2|3>")
        raise SystemExit(2)
    results = analyze(int(sys.argv[1]))
    for table_name, frame in results.items():
        print(f"\n== {table_name} ==")
        print(frame.head(12).to_string(index=False))
