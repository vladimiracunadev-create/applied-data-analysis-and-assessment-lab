# Pandas para gestión de datos

## Objetivos de aprendizaje

1. Leer, inspeccionar y escribir archivos CSV y Excel controlando tipos y codificación.
2. Seleccionar, filtrar y crear columnas sin provocar el aviso de copia encadenada.
3. Agrupar y agregar con el grano correcto, distinguiendo `size` de `count`.
4. Convertir tipos de forma defensiva y medir qué se pierde en la conversión.
5. Escribir un análisis reproducible que se ejecute de principio a fin sin
   intervención manual.

## Prerrequisitos

Bloque de fundamentos completo. Python básico: variables, listas, diccionarios,
funciones, `for`. Entorno: `uv sync`.

## Definiciones simples y formales

**Series.** *Simple:* una columna. *Formal:* arreglo unidimensional con un índice
asociado y un `dtype` homogéneo.

**DataFrame.** *Simple:* una tabla. *Formal:* colección de Series que comparten un
índice de filas.

**Índice.** Etiquetas de las filas. No es una columna: es la estructura por la que
pandas alinea operaciones entre objetos. La **alineación por índice** es la causa de
la mitad de los resultados sorprendentes de pandas.

**dtype.** Tipo físico de una Series: `int64`, `float64`, `object`, `datetime64[ns]`,
`boolean`. `object` suele significar «texto o mezcla», es decir, «pandas no supo».

**Vectorización.** Aplicar una operación a toda la Series de una vez, en lugar de
recorrer filas. Es más rápido y, sobre todo, más legible.

**Máscara booleana.** Series de `True`/`False` usada para filtrar. Es la forma
idiomática de expresar una regla de negocio en pandas.

**Copia encadenada.** Asignar sobre el resultado de una selección previa
(`df[df.a > 0]["b"] = 1`). Puede modificar una copia temporal y perder el cambio.

## Explicación conceptual

Un análisis en pandas tiene siempre la misma forma, y conviene escribirla en ese orden:

1. **Leer sin interpretar.** Traer los datos como están, para poder medirlos.
2. **Perfilar.** Tipos, nulos, duplicados, dominios.
3. **Convertir con `errors="coerce"`.** Lo no convertible pasa a nulo, y se cuenta.
4. **Marcar, no borrar.** Crear columnas booleanas con las reglas de validez.
5. **Agregar con el grano declarado.** Un `groupby` por nivel de análisis.
6. **Exportar y validar.** Totales que cuadran entre tablas.

El paso 4 es el que distingue un análisis defendible de uno frágil. Si en lugar de
marcar se filtra y se reasigna `df`, a la mitad del script ya nadie sabe qué filas
quedaron ni por qué. Con banderas explícitas (`realizado`, `valido_demanda`,
`duracion_valida`) cada indicador declara su propio filtro en el momento de
calcularse, y el informe de calidad sale de contar esas mismas banderas.

## Desarrollo de fundamentos

### `.loc`, `.iloc` y por qué no usar corchetes para asignar

| Expresión | Qué hace |
| --- | --- |
| `df["col"]` | Selecciona una columna (Series) |
| `df[["a", "b"]]` | Selecciona columnas (DataFrame) |
| `df[mascara]` | Filtra filas |
| `df.loc[mascara, "col"]` | Selecciona por etiqueta; **es la forma de asignar** |
| `df.iloc[0:5, 0:2]` | Selecciona por posición entera |

Para asignar siempre `df.loc[filas, columna] = valor`. La variante
`df[mascara]["col"] = valor` puede operar sobre una copia: en pandas 2 emite
`SettingWithCopyWarning` y en pandas 3, con copy-on-write activo por defecto, el cambio
simplemente no se refleja. Es un error silencioso de los peores: el código corre, el
resultado está mal.

### `size` frente a `count`

```python
df.groupby("recorrido_id").size()                  # filas del grupo
df.groupby("recorrido_id")["pasajeros"].count()    # valores no nulos de pasajeros
```

La diferencia entre ambos es exactamente el número de nulos del grupo. Confundirlos
sobreestima la cobertura del indicador. Ver [[count-asterisco-vs-columna]].

### Conversión defensiva

```python
pd.to_numeric(serie, errors="coerce")      # no numérico → NaN
pd.to_datetime(serie, errors="coerce")     # no fecha   → NaT
```

`errors="coerce"` es la opción correcta en gestión de datos: `errors="raise"` detiene
el proceso en el primer valor malo, sin decir cuántos hay, y `errors="ignore"` (ya
retirado) dejaba la columna como texto, lo que hacía fallar operaciones posteriores
por un motivo aparentemente distinto.

Después de convertir hay que contar: `(convertida.isna() & original.notna()).sum()` es
el número de valores que se perdieron en la conversión.

### Agrupación con varias agregaciones nombradas

```python
resumen = (df.loc[valido]
             .groupby("recorrido_id")
             .agg(viajes=("viaje_id", "size"),
                  pasajeros=("pasajeros", "sum"),
                  duracion_media=("duracion_min", "mean"),
                  duracion_p90=("duracion_min", lambda s: s.quantile(0.9)))
             .reset_index())
```

La sintaxis de agregación nombrada produce columnas con nombre explícito en lugar de
un índice jerárquico, que es lo que hace que la tabla se pueda exportar a Excel
directamente.

## Fórmulas matemáticas explicadas

Las agregaciones de pandas implementan directamente las fórmulas del bloque de
matemáticas:

```
sum()      Σ xᵢ
mean()     x̄ = (1/n) Σ xᵢ
std()      s = √[ Σ(xᵢ − x̄)² / (n − 1) ]        (ddof = 1 por defecto)
median()   valor central
quantile(q) percentil con método lineal
size()     n de filas del grupo
count()    nº de valores no nulos
nunique()  nº de valores distintos
```

Cuidado con `std()`: pandas usa `ddof=1` y NumPy `ddof=0`. Sobre 5 observaciones la
diferencia es del 12 % en la desviación.

## Significado de variables, símbolos y unidades

| Elemento | Significado | Unidad / tipo |
| --- | --- | --- |
| `df` | DataFrame de trabajo | tabla |
| `n` | Filas del grupo (`size`) | filas |
| `NaN` | Valor numérico ausente | — |
| `NaT` | Fecha-hora ausente | — |
| `dtype` | Tipo físico de la columna | `int64`, `float64`, `object`, `datetime64[ns]` |
| `duracion_min` | Duración del viaje | minutos |
| `pasajeros` | Personas registradas en el viaje | personas |
| `cumplimiento_pct` | `100 · realizados / programados` | % |

## Ejemplos, de simple a complejo

### Ejemplo 1 — leer y perfilar

```python
import pandas as pd
from lab.core import profile

df = pd.read_csv("data/case_1/viajes.csv")
print(df.shape)                      # (454, 6)
print(profile(df).to_string(index=False))
```

`profile` devuelve, por columna, `dtype`, nulos, valores únicos, filas totales y
duplicados exactos. Es el primer comando de cualquier análisis.

### Ejemplo 2 — máscara booleana como regla de negocio

```python
realizado = df["estado"].eq("REALIZADO")
pasajeros = pd.to_numeric(df["pasajeros"], errors="coerce")
pax_valido = pasajeros.notna() & pasajeros.ge(0)

df = df.assign(realizado=realizado, pax_valido=pax_valido)
# La regla queda escrita una vez y se puede contar:
print(f"realizados con pasajeros válido: {int((realizado & pax_valido).sum())}")
```

### Ejemplo 3 — del CSV al indicador, completo

```python
import pandas as pd
from lab.dates import duration_minutes, parse_datetime
from lab.metrics import safe_ratio

viajes = pd.read_csv("data/case_1/viajes.csv")
recorridos = pd.read_csv("data/case_1/recorridos.csv")

# Duplicados: se cuentan antes de eliminar.
originales = len(viajes)
viajes = viajes.drop_duplicates().copy()
duplicados = originales - len(viajes)

# Conversión defensiva, contando lo perdido.
viajes["pasajeros"] = pd.to_numeric(viajes["pasajeros"], errors="coerce")
inicio = parse_datetime(viajes["inicio"])
fin = parse_datetime(viajes["fin"])
viajes["inicio"], viajes["fin"] = inicio.values, fin.values
viajes["duracion_min"] = duration_minutes(viajes["inicio"], viajes["fin"])

# Cruce con control de cardinalidad: validate falla si el catálogo no es único.
viajes = viajes.merge(recorridos, on="recorrido_id", how="left", validate="many_to_one")

# Banderas por indicador: cada cálculo declara su propio filtro.
viajes["realizado"] = viajes["estado"].eq("REALIZADO") & viajes["operador_id"].notna()
viajes["pax_valido"] = viajes["pasajeros"].notna() & viajes["pasajeros"].ge(0)
viajes["dur_valida"] = viajes["duracion_min"].notna() & viajes["duracion_min"].ge(0)

# Indicador con su cobertura al lado.
base = viajes.loc[viajes["realizado"]]
demanda = (base.loc[base["pax_valido"]]
               .groupby("operador_id")
               .agg(pasajeros=("pasajeros", "sum"), viajes_con_dato=("viaje_id", "size"))
               .reset_index())
demanda["cobertura_pct"] = safe_ratio(
    demanda["viajes_con_dato"],
    base.groupby("operador_id").size().reindex(demanda["operador_id"]).to_numpy(),
    scale=100,
)
print(f"duplicados eliminados: {duplicados}")
print(demanda.to_string(index=False))
```

## Aplicaciones profesionales

- **Transporte.** Consolidar archivos de varios operadores con formatos distintos y
  producir indicadores comparables.
- **Finanzas.** Conciliar movimientos contra extractos: el patrón es el mismo cruce
  auditado con control de cardinalidad.
- **Logística.** Calcular tiempos de tránsito desde pares de marcas de tiempo, con el
  mismo tratamiento de duraciones negativas.
- **Recursos humanos.** Agregar dotación por área y período declarando el grano.
- **Ciencias.** Limpiar series de mediciones instrumentales conservando el registro de
  los valores descartados.

## Código fuente comentado

El ejemplo 3 es el código comentado de la clase. Para la versión de producción, con
todos los indicadores del caso, vea `solutions/reference.py`, y para la validación
independiente del mismo cálculo, `solutions/sql_reference.py`.

Tres convenciones del laboratorio visibles en ese archivo:

```python
# 1. Rutas relativas a la raíz del repositorio, nunca absolutas: el script debe
#    correr en el equipo de otra persona sin editarlo.
ROOT = Path(__file__).resolve().parents[1]

# 2. Las reglas de validez son columnas, no filtros aplicados sobre df.
done = t.estado.eq("REALIZADO")
bad_pax = t.pasajeros.isna() | t.pasajeros.lt(0)

# 3. Cada indicador se calcula sobre la base que le corresponde, no sobre un df
#    global que fue filtrado paso a paso.
demand = valid.loc[~bad_pax.loc[valid.index]].groupby("operador").agg(...)
```

## Ejercicios prácticos

1. Lea `data/case_2/viajes.csv` y perfile la tabla. Informe `dtype`, nulos y
   duplicados por columna.
2. Convierta `pasajeros` a numérico y `inicio`/`fin` a fecha-hora. Informe cuántos
   valores se perdieron en cada conversión y por qué.
3. Calcule el número de viajes y la suma de pasajeros por operador usando `size` y
   `count`. Explique la diferencia entre ambos resultados.
4. Cruce `viajes` con `recorridos` usando `validate="many_to_one"`. Luego duplique
   deliberadamente una fila de `recorridos` y vuelva a cruzar. ¿Qué ocurre y por qué
   es preferible a que no ocurra nada?
5. Agrupe por hora del día y compruebe que la suma por hora coincide con el total
   general. Si no coincide, encuentre las filas faltantes.
6. Reescriba un filtro del tipo `df = df[df.a > 0]` usando una columna de bandera y
   explique qué información se gana.

## Soluciones explicadas

1. En el caso 2, `pasajeros` llega como `float64` (porque hay vacíos) e `inicio`/`fin`
   como `object` (texto). Hay 8 duplicados exactos. `profile` lo entrega en una tabla.

2. `pasajeros` pierde los valores vacíos (pasan a `NaN`), que son 4 en el caso 2;
   `fin` queda `NaT` en los viajes cancelados, que es correcto por diseño y no un
   defecto. La distinción entre «vacío esperado» y «vacío inesperado» viene del
   diccionario de datos, no de los datos.

3. `size` cuenta todos los viajes del operador; `count` sobre `pasajeros` cuenta solo
   los que tienen conteo registrado. La diferencia es el número de viajes sin dato de
   pasajeros, y es exactamente lo que hay que informar como cobertura.

4. Con el catálogo duplicado, `validate="many_to_one"` levanta `MergeError` y el
   proceso se detiene. Sin `validate`, el cruce duplica silenciosamente las filas de
   viajes y la suma de pasajeros se infla. Un error ruidoso es preferible a un número
   erróneo con apariencia correcta.

5. La suma por hora coincide con el total solo si todas las filas tienen `inicio`
   interpretable. Las que no lo tienen caen fuera de todos los grupos: `groupby`
   descarta los nulos de la clave de agrupación por defecto. Para encontrarlas:
   `df[df.inicio.isna()]`. Para incluirlas como grupo propio: `dropna=False`.

6. Con bandera se conserva el denominador. `df = df[df.a > 0]` hace imposible, tres
   líneas después, responder «¿sobre cuántas filas se calculó esto?». Con
   `df["a_valido"] = df.a > 0`, el informe de calidad y el indicador salen del mismo
   objeto.

## Errores frecuentes

- **Asignar sobre una selección** (`df[mask]["col"] = x`): el cambio se pierde.
- **`errors="raise"` en producción**: se detiene en el primer valor malo sin decir
  cuántos hay.
- **Confundir `size` con `count`** y sobreestimar la cobertura.
- **Cruzar sin `validate`** y duplicar filas sin notarlo.
- **Olvidar que `groupby` descarta nulos en la clave**, perdiendo filas en silencio.
- **Reasignar `df` paso a paso** hasta perder el rastro de qué filas quedaron.
- **`inplace=True`**: dificulta la lectura, no ahorra memoria de forma garantizada y
  está en desuso en la API moderna.
- **Suponer el `dtype`.** Una columna `object` que «parece» numérica no lo es.

## Criterios de validación

1. El script corre de principio a fin desde la raíz del repositorio, sin editar rutas.
2. Cada conversión de tipo informa cuántos valores no se pudieron convertir.
3. Cada cruce declara su cardinalidad esperada.
4. Cada indicador declara el filtro con el que se calculó y su cobertura.
5. Los totales cuadran entre tablas relacionadas (por hora frente a general).
6. No hay `SettingWithCopyWarning` ni avisos de deprecación en la ejecución.

## Preguntas de evaluación

1. ¿Por qué `df[df.a > 0]["b"] = 1` puede no modificar nada?
2. ¿Cuál es la diferencia numérica exacta entre `groupby().size()` y
   `groupby()["col"].count()`?
3. ¿Qué hace `errors="coerce"` y por qué es la opción correcta en gestión de datos?
4. ¿Qué garantiza `validate="many_to_one"` y qué problema previene?
5. Al agrupar por una columna con nulos, ¿qué ocurre con esas filas y cómo se las
   incluye?
6. ¿Por qué `std()` de pandas y `np.std()` dan resultados distintos sobre los mismos
   datos?

## Referencias verificables

- Documentación de pandas, guía de usuario completa.
  <https://pandas.pydata.org/docs/user_guide/index.html>
- pandas, «Indexing and selecting data» (incluye copia encadenada).
  <https://pandas.pydata.org/docs/user_guide/indexing.html>
- pandas, «Copy-on-Write», comportamiento por defecto desde pandas 3.
  <https://pandas.pydata.org/docs/user_guide/copy_on_write.html>
- pandas, «Group by: split-apply-combine».
  <https://pandas.pydata.org/docs/user_guide/groupby.html>
- pandas, «Merge, join, concatenate and compare».
  <https://pandas.pydata.org/docs/user_guide/merging.html>
- McKinney, W. *Python for Data Analysis*, 3.ª edición, O'Reilly, 2022.
  <https://wesmckinney.com/book/>

## Glosario técnico

| Término | Definición |
| --- | --- |
| Agregación nombrada | Sintaxis `nombre=(columna, función)` dentro de `agg`. |
| Alineación por índice | pandas empareja filas por etiqueta antes de operar. |
| Copia encadenada | Asignación sobre el resultado de una selección previa. |
| Copy-on-Write | Modelo de copia de pandas 3 que evita mutaciones indirectas. |
| DataFrame | Tabla con índice de filas y columnas con nombre. |
| dtype | Tipo físico de una columna. |
| Índice | Etiquetas de las filas de una Series o DataFrame. |
| Máscara booleana | Series de `True`/`False` usada para filtrar o marcar. |
| NaN / NaT | Valor numérico / de fecha ausente. |
| Series | Columna: arreglo unidimensional con índice. |
| Vectorización | Operar sobre toda la Series en lugar de fila por fila. |
