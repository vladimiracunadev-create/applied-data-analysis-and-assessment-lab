---
id: count-asterisco-vs-columna
tipo: definicion
titulo: COUNT(*) frente a COUNT(columna) en cinco tecnologías
etiquetas: [sql, pandas, polars, r, excel, equivalencias, calidad-datos]
fuente: lab/sqlbridge.py, docs/equivalencias.md
relacionados: [cruce-con-cardinalidad, vacio-no-es-cero]
---

Dos funciones con nombre casi idéntico y semántica distinta. La diferencia entre
ambas es exactamente el número de nulos, lo que las convierte en una herramienta de
diagnóstico y no solo de conteo.

| Operación | SQL | Pandas | Polars | R base | Excel |
| --- | --- | --- | --- | --- | --- |
| Filas del grupo | `COUNT(*)` | `.size()` | `pl.len()` | `nrow(df)` | `CONTAR.SI.CONJUNTO` sobre la clave |
| Valores no nulos | `COUNT(col)` | `.count()` | `.count()` | `sum(!is.na(x))` | `CONTAR(rango)` |
| Valores distintos | `COUNT(DISTINCT col)` | `.nunique()` | `.n_unique()` | `length(unique(na.omit(x)))` | `CONTARA(UNICOS(rango))` |
| Celdas no vacías | — | `.notna().sum()` | `.is_not_null().sum()` | `sum(!is.na(x))` | `CONTARA(rango)` |

**Uso diagnóstico.** Después de un cruce por la izquierda:

```sql
SELECT COUNT(*) AS filas, COUNT(operador_id) AS con_clave FROM base
```

`filas - con_clave` es el número de claves desconocidas. El mismo cálculo en Pandas:
`len(df) - df.operador_id.count()`, o `df.operador_id.isna().sum()`.
En Polars es `df.height - df["operador_id"].count()`; en R base,
`nrow(df) - sum(!is.na(df$operador_id))`.

**Trampa frecuente.** `GROUP BY` con `COUNT(*)` para contar «viajes con dato de
pasajeros». `COUNT(*)` cuenta también los viajes sin dato, y la cobertura del
indicador queda sobreestimada. El conteo correcto es `COUNT(pasajeros)`.

**Trampa adicional en Pandas.** `groupby().count()` cuenta no nulos **por columna**,
de modo que distintas columnas pueden devolver distintos números en el mismo grupo.
`groupby().size()` devuelve un único número por grupo: las filas. Elegir mal produce
una tabla cuyos totales no cuadran entre sí.
