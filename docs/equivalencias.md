# Equivalencias entre SQL, Pandas, Polars, Excel y R

Tablas de traducción entre las herramientas del laboratorio. La columna **Trampa**
señala dónde las versiones «equivalentes» dejan de serlo: es la parte útil de esta
guía.

Convención de nombres: Excel almacena las funciones en inglés y las muestra traducidas
según la configuración regional. Aquí se dan ambas formas. El separador de argumentos
del archivo es la coma; Excel puede mostrar punto y coma.

## 1. Selección y filtrado

| Operación | SQL | Pandas | Polars | Excel | Trampa |
| --- | --- | --- | --- | --- | --- |
| Elegir columnas | `SELECT a, b` | `df[["a","b"]]` | `df.select("a", "b")` | Ocultar columnas o `ELEGIRCOLS` | `df["a"]` de Pandas devuelve Series; `select` de Polars conserva DataFrame |
| Filtrar filas | `WHERE a > 0` | `df.loc[df.a > 0]` | `df.filter(pl.col("a") > 0)` | Autofiltro o `FILTRAR` | Pandas alinea máscaras por índice; Polars evalúa expresiones por fila |
| Varias condiciones | `WHERE a > 0 AND b = 'X'` | `df.loc[(df.a > 0) & df.b.eq("X")]` | `df.filter((pl.col("a") > 0) & (pl.col("b") == "X"))` | `FILTRAR(rango;(a>0)*(b="X"))` | En Excel `*` es Y lógico, `+` es O lógico |
| Valores distintos | `SELECT DISTINCT a` | `df.a.drop_duplicates()` | `df.select("a").unique()` | `UNICOS(rango)` | Polars no garantiza el orden sin `maintain_order=True` |
| Primeras n filas | `LIMIT 10` | `df.head(10)` | `df.head(10)` | — | `head` no ordena: dé el orden explícito |
| Nulos | `WHERE a IS NULL` | `df.loc[df.a.isna()]` | `df.filter(pl.col("a").is_null())` | `ESBLANCO(A2)` | `NaN` flotante y `null` son estados distintos en Polars |
| Entre valores | `BETWEEN 1 AND 10` | `df.a.between(1, 10)` | `pl.col("a").is_between(1, 10)` | `Y(A2>=1;A2<=10)` | Los tres incluyen ambos extremos por defecto |
| En un conjunto | `IN ('A','B')` | `df.a.isin(["A","B"])` | `pl.col("a").is_in(["A","B"])` | `CONTAR.SI(rango;A2)>0` | `NOT IN` con nulos en SQL tiene semántica ternaria |

## 2. Conteos y agregación

| Operación | SQL | Pandas | Polars | Excel | Trampa |
| --- | --- | --- | --- | --- | --- |
| Filas | `COUNT(*)` | `len(df)` / `.size()` | `df.height` / `pl.len()` | `CONTARA(columna_clave)` | — |
| Valores no nulos | `COUNT(col)` | `df.col.count()` | `pl.col("col").count()` | `CONTAR(rango)` | La diferencia con el total es el número de nulos |
| Valores distintos | `COUNT(DISTINCT col)` | `df.col.nunique()` | `pl.col("col").n_unique()` | `CONTARA(UNICOS(rango))` | Declare si el nulo cuenta como categoría |
| Suma | `SUM(col)` | `df.col.sum()` | `pl.col("col").sum()` | `SUMA(rango)` | Pandas y Polars pueden diferir en una columna completamente nula |
| Promedio | `AVG(col)` | `df.col.mean()` | `pl.col("col").mean()` | `PROMEDIO(rango)` | Todos excluyen nulos: informe la cobertura |
| Mínimo / máximo | `MIN` / `MAX` | `.min()` / `.max()` | `.min()` / `.max()` | `MIN` / `MAX` | Sobre texto comparan lexicográficamente |
| Desviación | `STDDEV_SAMP` | `.std()` (ddof=1) | `.std(ddof=1)` | `DESVEST.M` | Fijar `ddof`; la población usa 0 |
| Mediana | `PERCENTILE_CONT(0.5)` | `.median()` | `.median()` | `MEDIANA` | SQLite no la trae de serie |
| Percentil | `PERCENTILE_CONT(0.9)` | `.quantile(0.9)` | `.quantile(0.9, interpolation="linear")` | `PERCENTIL.INC(rango;0,9)` | Declare interpolación; no todos los motores comparten el valor por defecto |
| Agrupar | `GROUP BY a` | `df.groupby("a", dropna=False)` | `df.group_by("a")` | Tabla dinámica | Pandas descarta claves nulas salvo que se indique; Polars las conserva |
| Filtrar grupos | `HAVING SUM(x) > 10` | `.groupby(...).filter(...)` | `.group_by(...).agg(...).filter(...)` | Filtro sobre la dinámica | `WHERE` filtra filas; `HAVING`, grupos |

## 3. Agregación condicional

| Operación | SQL | Pandas | Polars | Excel |
| --- | --- | --- | --- | --- |
| Sumar con condición | `SUM(CASE WHEN ok THEN x END)` | `df.loc[ok, "x"].sum()` | `pl.col("x").filter(pl.col("ok")).sum()` | `SUMAR.SI.CONJUNTO(x;ok;1)` / `SUMIFS` |
| Contar con condición | `COUNT(CASE WHEN ok THEN 1 END)` | `int(ok.sum())` | `pl.col("ok").sum()` | `CONTAR.SI.CONJUNTO(ok;1)` / `COUNTIFS` |
| Promediar con condición | `AVG(CASE WHEN ok THEN x END)` | `df.loc[ok, "x"].mean()` | `pl.col("x").filter(pl.col("ok")).mean()` | `PROMEDIO.SI.CONJUNTO(x;ok;1)` / `AVERAGEIFS` |

**Trampa del denominador.** Cuando la columna de bandera devuelve cadena vacía donde
el indicador no aplica, `CONTAR.SI.CONJUNTO(rango;"<>")` la cuenta como no vacía e
infla el denominador. Use `">=0"`, que solo admite números. Ver
`knowledge/countifs-cadena-vacia.md`.

**Orden de argumentos.** `SUMIFS` y `AVERAGEIFS` reciben primero el rango a agregar;
`COUNTIFS` empieza directamente por los pares rango/criterio.

## 4. Cruces

| Operación | SQL | Pandas | Polars | Excel |
| --- | --- | --- | --- | --- |
| Por la izquierda | `LEFT JOIN` | `merge(how="left")` | `join(how="left")` | `BUSCARX(...;"SIN CLAVE")` |
| Interno | `INNER JOIN` | `merge(how="inner")` | `join(how="inner")` | `BUSCARX` + filtrar los no encontrados |
| Externo completo | `FULL OUTER JOIN` | `merge(how="outer")` | `join(how="full", coalesce=True)` | Unir dos `BUSCARX` cruzados |
| Clave compuesta | `ON a.k1=b.k1 AND a.k2=b.k2` | `merge(on=["k1","k2"])` | `join(on=["k1","k2"])` | `BUSCARX` sobre una clave concatenada |
| Auditar el cruce | comparar `COUNT(*)` y `COUNT(col)` | `indicator=True` + `validate=` | `validate="m:1"` + recuento de nulos | `CONTAR.SI(rango;"SIN CLAVE")` |

**Trampas del cruce:**

- En SQL, `NULL = NULL` es desconocido: las filas con clave nula **nunca** emparejan.
  En Pandas, `merge` **sí** empareja `NaN` con `NaN`. Dos implementaciones del mismo
  cruce difieren exactamente en esas filas.
- `BUSCARV` cuenta columnas por número: insertar una columna rompe el resultado sin
  error visible. `BUSCARX` referencia rangos y no tiene ese problema.
- `merge` sin `validate` duplica filas en silencio si el catálogo no es único.
- `join` de Polars también debe declarar `validate`; `coalesce=True` en un cruce
  completo evita conservar dos columnas de clave que describen lo mismo.

## 5. Fechas y horas

| Operación | SQL (SQLite) | Pandas | Polars | Excel |
| --- | --- | --- | --- | --- |
| Texto a fecha | `date(col)` | `pd.to_datetime(col, errors="coerce")` | `str.to_datetime(strict=False)` | `VALOR.FECHA` / importación tipada |
| Hora del día | `strftime('%H', col)` | `.dt.hour` | `.dt.hour()` | `HORA(A2)` |
| Día del mes | `strftime('%d', col)` | `.dt.day` | `.dt.day()` | `DIA(A2)` |
| Día de la semana | `strftime('%w', col)` | `.dt.weekday` | `.dt.weekday()` | `DIASEM(A2;2)` |
| Duración en minutos | `(strftime('%s',fin)-strftime('%s',ini))/60.0` | `(fin-ini).dt.total_seconds()/60` | `(fin-inicio).dt.total_seconds()/60` | `(D2-C2)*1440` |
| Fecha de hoy | `date('now')` | `pd.Timestamp.today()` | `pl.lit(date.today())` | `HOY()` |

**Trampas de fechas:**

- En SQLite, `julianday` devuelve días en punto flotante: la resta pierde precisión e
  invierte las comparaciones justo en los empates. Use segundos enteros. Ver
  `knowledge/julianday-precision.md`.
- `strftime('%w')` de SQLite cuenta domingo = 0; `.dt.weekday` de Pandas cuenta
  lunes = 0; `DIASEM` de Excel depende de su segundo argumento. Tres convenciones
  distintas para la misma pregunta.
- Excel almacena la fecha como días decimales; el resultado de una resta hereda el
  formato de fecha y hay que cambiarlo a número.
- En GTFS, `stop_times.txt` admite horas mayores que 24 (`25:10:00`): ninguna de las
  tres conversiones lo acepta sin tratamiento previo.

## 6. Tipos y nulos

| Operación | SQL | Pandas | Polars | Excel | Trampa |
| --- | --- | --- | --- | --- | --- |
| A número | `CAST(col AS REAL)` | `pd.to_numeric(col, errors="coerce")` | `pl.col("col").cast(pl.Float64, strict=False)` | `VALOR(A2)` | `CAST('' AS REAL)` da **0.0** en SQLite, no nulo |
| Vacío a nulo | `NULLIF(TRIM(col),'')` | se configura al leer | `null_values=[""]` | — | Declare la política de lectura, no la deje implícita |
| Nulo a valor | `COALESCE(col, 0)` | `col.fillna(0)` | `pl.col("col").fill_null(0)` | `SI.ERROR(A2;0)` | Rellenar con cero convierte una ausencia en un dato |
| ¿Es número? | `typeof(col)='real'` | `col.notna()` tras `to_numeric` | `cast(strict=False).is_not_null()` | `ESNUMERO(A2)` | `NaN` no es `null` en Polars |
| División protegida | `x / NULLIF(y,0)` | `lab.metrics.safe_ratio` | `pl.when(y != 0).then(x/y)` | `SI(N(C2)=0;"";D2/C2)` | `SI.ERROR` oculta también errores estructurales |

## 7. Equivalencias con Polars y R

Para quien elija RStudio como alternativa:

| Operación | Pandas | Polars | R base | dplyr |
| --- | --- | --- | --- | --- |
| Leer CSV | `pd.read_csv(p)` | `pl.read_csv(p)` | `read.csv(p)` | `readr::read_csv(p)` |
| Filtrar | `df.loc[df.a > 0]` | `df.filter(pl.col("a") > 0)` | `df[df$a > 0, ]` | `filter(df, a > 0)` |
| Elegir columnas | `df[["a","b"]]` | `df.select("a", "b")` | `df[, c("a","b")]` | `select(df, a, b)` |
| Columna nueva | `df.assign(c=...)` | `df.with_columns(expr.alias("c"))` | `df$c <- ...` | `mutate(df, c = ...)` |
| Agrupar y agregar | `df.groupby("a").agg(...)` | `df.group_by("a").agg(...)` | `aggregate(...)` | `group_by(a) %>% summarise(...)` |
| Cruzar | `merge(how="left")` | `join(how="left")` | `merge(all.x=TRUE)` | `left_join(a, b, by="k")` |
| Quitar duplicados | `df.drop_duplicates()` | `df.unique()` | `unique(df)` | `distinct(df)` |
| Nulos | `df.a.isna()` | `pl.col("a").is_null()` | `is.na(df$a)` | `is.na(a)` |
| Percentil | `df.a.quantile(0.9)` | `pl.col("a").quantile(0.9, interpolation="linear")` | `quantile(df$a, 0.9)` | `quantile(a, 0.9)` |

**Trampa de R.** `quantile()` de R tiene nueve tipos de interpolación (`type = 1..9`);
el predeterminado es el 7, que coincide con el método lineal de NumPy y con
`PERCENTIL.INC` de Excel. Cambiar el tipo cambia el resultado.

## 8. Qué no es equivalente

Casos donde la traducción no existe y hay que decidir, no traducir:

| Concepto | Por qué no se traduce |
| --- | --- |
| Índice de Pandas | SQL no tiene equivalente: la alineación por índice es propia de Pandas |
| Plan lazy de Polars | Describe una consulta optimizable; no equivale a ejecutar un DataFrame eager |
| `NULL = NULL` | Falso en SQL, verdadero al cruzar en Pandas |
| Tipado de SQLite | Dinámico por afinidad: una columna admite texto y número a la vez |
| Celda con `""` de Excel | No es nula ni vacía: es texto de longitud cero |
| Orden de filas | No garantizado en SQL sin `ORDER BY`; sí en un DataFrame |
| Tabla dinámica | Es un `groupby` **más** una presentación; no hay equivalente directo |
