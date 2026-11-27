---
id: duracion-en-minutos-tres-herramientas
tipo: formula
titulo: Duración en minutos en Pandas, Polars, R, Excel y SQL
etiquetas: [fechas-horarios, pandas, polars, r, excel, sql, equivalencias]
fuente: lab/dates.py, lab/excel.py, solutions/polars_reference.py, solutions/r_reference.R, solutions/sql_reference.py
relacionados: [julianday-precision, vacio-no-es-cero]
---

La misma operación, cinco mecánicas distintas. El resultado debe coincidir hasta el
último decimal; si no coincide, hay un error de tipos o de precisión.

**Pandas.** Resta de `datetime64`, que produce un `timedelta64` exacto:

```python
(pd.to_datetime(fin) - pd.to_datetime(inicio)).dt.total_seconds() / 60
```

**Excel.** Las fechas se almacenan como días decimales desde 1899-12-30. Un día son
1440 minutos:

```excel
=SI(O(C2="";D2="");"";(D2-C2)*1440)
```

El factor 1440 = 24 × 60. Si la celda está formateada como fecha, el resultado se
muestra como fecha: hay que cambiar el formato de la celda a número.

**Polars.** La resta produce una duración y la unidad se solicita explícitamente:

```python
(pl.col("fin") - pl.col("inicio")).dt.total_seconds() / 60
```

**R base.** `difftime` obliga a declarar la unidad:

```r
as.numeric(difftime(fin, inicio, units = "mins"))
```

**SQL (SQLite).** Con segundos enteros, no con `julianday`:

```sql
(CAST(strftime('%s', fin) AS INTEGER) - CAST(strftime('%s', inicio) AS INTEGER)) / 60.0
```

En PostgreSQL: `EXTRACT(EPOCH FROM (fin - inicio)) / 60`. En SQL Server:
`DATEDIFF(SECOND, inicio, fin) / 60.0`.

**Tres condiciones para que las cinco coincidan.**

1. Las cinco herramientas deben interpretar la fecha con el mismo orden de día y mes.
2. Ninguna debe convertir el extremo ausente en cero; el resultado debe ser nulo.
3. La división final se hace en punto flotante, pero la resta se hace en la unidad
   entera (segundos o milisegundos). Ver [[julianday-precision]].
