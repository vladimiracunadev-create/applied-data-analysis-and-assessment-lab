# Cruces, contratos y SQL equivalente

## Objetivos de aprendizaje

1. Elegir el tipo de cruce correcto y comprobar la cardinalidad antes y después.
2. Detectar y cuantificar claves huérfanas y filas multiplicadas.
3. Expresar el mismo cruce y la misma agregación en Pandas, SQL y Excel.
4. Declarar un contrato de datos entre componentes y hacerlo cumplir en integración
   continua.
5. Validar un resultado recalculándolo con una tecnología distinta.

## Prerrequisitos

Clases `00-fundamentos/01`, `00-fundamentos/02` y `20-programacion/01`. Nociones de
SQL: `SELECT`, `WHERE`, `GROUP BY`.

## Definiciones simples y formales

**Cruce (join).** *Simple:* pegar columnas de otra tabla usando una clave. *Formal:*
operación que combina tuplas de dos relaciones según un predicado de igualdad sobre
atributos comunes.

**Cardinalidad de la relación.** Cuántas filas de una tabla pueden corresponder a una
fila de la otra: `uno a uno`, `muchos a uno`, `uno a muchos`, `muchos a muchos`. Es la
propiedad que determina si el cruce puede multiplicar filas.

**Clave huérfana.** Valor de clave foránea que no existe en la tabla destino.

**Grano del resultado.** Lo que identifica una fila después del cruce. Un cruce
`muchos a uno` conserva el grano de la tabla izquierda; un `uno a muchos` lo cambia, y
toda suma posterior queda inflada si nadie lo advirtió.

**Contrato de datos.** Acuerdo explícito y ejecutable sobre el esquema, los tipos, los
dominios y las claves que una tabla debe cumplir para ser consumida.

**Validación independiente.** Recalcular un resultado con una implementación que no
comparte código con la original, y comparar.

## Explicación conceptual

Un cruce falla de dos formas opuestas y ambas son silenciosas.

**Pierde filas.** Un cruce interno descarta los registros cuya clave no existe en el
catálogo. En el caso de transporte, los viajes con `recorrido_id = 'R99'`
desaparecerían: la demanda total baja, el informe no lo menciona y el número sigue
pareciendo razonable.

**Multiplica filas.** Si el catálogo tiene su clave repetida, cada fila de la
izquierda se duplica. La suma de pasajeros se infla en la proporción de la
duplicación. Nada en el resultado indica que ocurrió.

La defensa no es la pericia: es el procedimiento. Contar antes, declarar la
cardinalidad esperada, cruzar por la izquierda, contar después y cuantificar los
huérfanos. Cinco pasos que ocupan diez líneas y que convierten un error silencioso en
un número informado. Ver [[cruce-con-cardinalidad]].

Sobre eso se construye la segunda idea de la clase: si el cruce y la agregación se
pueden escribir en tres tecnologías, se pueden **confrontar**. Dos implementaciones
que coinciden no garantizan que el indicador sea el correcto —pueden compartir el
mismo malentendido sobre la regla de negocio— pero descartan toda una familia de
errores: tipos mal convertidos, filtros mal escritos, denominadores equivocados,
precisión numérica. Es la forma más económica de validación que existe.

## Desarrollo de fundamentos

### Los cuatro tipos de cruce

| Tipo | Pandas | SQL | Qué conserva |
| --- | --- | --- | --- |
| Interno | `how="inner"` | `INNER JOIN` | Solo las claves presentes en ambas |
| Izquierdo | `how="left"` | `LEFT JOIN` | Todas las de la izquierda |
| Derecho | `how="right"` | `RIGHT JOIN` | Todas las de la derecha |
| Externo | `how="outer"` | `FULL OUTER JOIN` | Todas las de ambas |

En gestión de datos el cruce por defecto es el **izquierdo**: conserva la tabla de
hechos completa y hace visible lo que no encontró par. El interno se usa cuando la
ausencia de clave es, por definición del problema, motivo de exclusión, y eso hay que
declararlo.

El **externo** es el correcto para el cumplimiento de la programación: hay que
conservar los días programados sin viajes (realizados = 0) **y** detectar los viajes en
días no programados (dos defectos distintos). SQLite no tiene `FULL OUTER JOIN` en
versiones antiguas; se emula con la unión de dos `LEFT JOIN`:

```sql
SELECT p.recorrido_id, p.dia, p.programados, COALESCE(d.realizados, 0) AS realizados
FROM prog p LEFT JOIN realizados_dia d
  ON d.recorrido_id = p.recorrido_id AND d.dia = p.dia
UNION ALL
SELECT d.recorrido_id, d.dia, NULL, d.realizados
FROM realizados_dia d LEFT JOIN prog p
  ON d.recorrido_id = p.recorrido_id AND d.dia = p.dia
WHERE p.recorrido_id IS NULL
```

En un `UNION`, el `ORDER BY` final debe referirse a los nombres de columna del primer
`SELECT`; conviene poner alias explícitos (`p.recorrido_id AS recorrido_id`) o la
consulta falla con un mensaje poco informativo.

### `validate` en pandas

```python
izquierda.merge(catalogo, on="clave", how="left", validate="many_to_one", indicator=True)
```

`validate="many_to_one"` comprueba que la clave del catálogo sea única y levanta
`MergeError` si no lo es. Es preferible un error ruidoso a un total inflado.
`indicator=True` agrega la columna `_merge` con `both` o `left_only`, cuyo recuento es
la auditoría del cruce. `lab.core.audited_join` devuelve ambas cosas.

### El contrato como frontera entre componentes

Un contrato (`lab.contracts.TableContract`) declara columnas, tipos, dominios, clave
primaria y claves foráneas. Su valor no está en validar una vez, sino en validar
**cada** carga: el contrato se ejecuta en integración continua y la próxima entrega del
archivo se rechaza antes de llegar a un informe.

La diferencia entre un contrato y una comprobación suelta es la **severidad
declarada**: el contrato distingue lo que impide usar los datos (`error`) de lo que
exige decisión documentada (`aviso`). Sin esa distinción, el equipo aprende a ignorar
las alertas.

### Trampas de SQL que no existen en Pandas (y al revés)

| Trampa | Dónde | Efecto |
| --- | --- | --- |
| `CAST('' AS REAL)` da `0.0` | SQLite | Convierte una ausencia en un cero |
| `COUNT(*)` frente a `COUNT(col)` | SQL | Sobreestima la cobertura |
| `NULL` en el predicado del `JOIN` | SQL | `NULL = NULL` es falso: nunca empareja |
| `julianday` en punto flotante | SQLite | Invierte comparaciones en los empates |
| `groupby` descarta nulos en la clave | Pandas | Pierde filas sin avisar |
| Alineación por índice | Pandas | Opera entre Series desalineadas sin error |
| `std()` con `ddof` distinto | Pandas / NumPy | Desviaciones distintas del mismo dato |

La tercera merece atención: en SQL, dos `NULL` no son iguales. Un `JOIN` por una
columna con nulos nunca los empareja, y esas filas desaparecen del `INNER JOIN` o
quedan sin par en el `LEFT JOIN`. En Pandas, `merge` **sí** empareja `NaN` con `NaN`,
que es el comportamiento opuesto. Dos implementaciones del mismo cruce pueden diferir
exactamente en esas filas.

## Fórmulas matemáticas explicadas

**Factor de multiplicación del cruce.**

```
factor = filas_despues / filas_antes
```

Debe ser exactamente 1 en un cruce `muchos a uno`. Un `factor > 1` indica duplicación
en el catálogo; un `factor < 1` indica que el cruce fue interno y se perdieron filas.

**Tasa de claves huérfanas.**

```
huerfanas = 100 · filas_sin_par / filas_antes       [%]
```

En SQL se obtiene como la diferencia entre `COUNT(*)` y `COUNT(columna_del_catalogo)`
después del `LEFT JOIN`.

**Criterio de acuerdo entre implementaciones.**

```
coinciden  si  |valor_A − valor_B| ≤ τ
```

La tolerancia `τ` existe porque una suma de números en coma flotante puede diferir en
el último bit según el orden de las operaciones. El laboratorio usa `τ = 10⁻⁹`. Una
diferencia mayor **no** es ruido numérico: es un error real en alguna de las dos
implementaciones.

## Significado de variables, símbolos y unidades

| Símbolo | Significado | Unidad |
| --- | --- | --- |
| `filas_antes` | Filas de la tabla izquierda antes del cruce | filas |
| `filas_despues` | Filas del resultado | filas |
| `factor` | Multiplicación producida por el cruce | adimensional, esperado 1 |
| `filas_sin_par` | Filas cuya clave no existe en el catálogo | filas |
| `huerfanas` | Proporción de claves huérfanas | % |
| `τ` | Tolerancia de comparación entre implementaciones | unidad del indicador |

## Ejemplos, de simple a complejo

### Ejemplo 1 — cruce que pierde filas

`viajes` tiene 3 filas con claves `R1`, `R1`, `R9`. `rutas` solo tiene `R1`.

```sql
SELECT COUNT(*) AS filas, COUNT(r.operador) AS con_operador
FROM viajes v LEFT JOIN rutas r ON r.ruta = v.ruta
```

Resultado: `filas = 3`, `con_operador = 2`. La diferencia, 1, es la clave huérfana.
Con `INNER JOIN` el resultado habría sido 2 filas y nadie sabría que faltaba una.

### Ejemplo 2 — cruce que multiplica filas

`rutas` con `R1` repetida dos veces (por un error de carga). El `LEFT JOIN` devuelve 5
filas en lugar de 3: `factor = 5/3 ≈ 1,67`. La suma de pasajeros queda inflada un 67 %
en las filas afectadas. `validate="many_to_one"` en pandas lo detecta antes.

### Ejemplo 3 — las tres implementaciones del mismo indicador

**Pandas.**

```python
demanda = (base.loc[base.pax_valido]
               .groupby("operador")
               .agg(pasajeros=("pasajeros", "sum"), viajes=("viaje_id", "size"))
               .reset_index())
```

**SQL.**

```sql
SELECT operador, SUM(pasajeros) AS pasajeros, COUNT(viaje_id) AS viajes
FROM base
WHERE pasajeros_invalido = 0
GROUP BY operador
ORDER BY operador
```

**Excel.**

```excel
=SUMAR.SI.CONJUNTO(Calc[pasajeros];Calc[operador];$A6;Calc[valido];1)
=CONTAR.SI.CONJUNTO(Calc[operador];$A6;Calc[valido];1)
```

Las tres deben dar el mismo número. Si no, el orden de diagnóstico es: ¿el filtro es
el mismo?, ¿la conversión de tipos es la misma?, ¿el denominador es el mismo?

### Ejemplo 4 — validación cruzada ejecutada

El laboratorio tiene dos implementaciones completas del caso de transporte:
`solutions/reference.py` en Pandas y `solutions/sql_reference.py` en SQL, que parte de
los CSV cargados como texto y hace su propio casteo. `tests/test_cross_validation.py`
las confronta indicador por indicador con `τ = 10⁻⁹` sobre los tres casos.

Esa confrontación detectó un error real: la duración calculada con `julianday`
difería del valor exacto en el séptimo decimal, lo que invertía la comparación
`duración ≤ meta` justo en los empates y cambiaba la puntualidad en varios puntos
porcentuales. La media coincidía hasta el octavo decimal; solo el porcentaje delataba
el problema. Con una sola implementación, el número habría sido plausible. Ver
[[julianday-precision]].

## Aplicaciones profesionales

- **Transporte.** Consolidar hechos de operación con catálogos de recorridos,
  operadores y programación.
- **Banca.** Conciliar movimientos con titulares y productos; la integridad
  referencial es requisito regulatorio.
- **Salud.** Unir episodios con prestaciones sin multiplicar el recuento de pacientes.
- **Retail.** Cruzar ventas con catálogo de productos y detectar SKU no catalogados.
- **Telecomunicaciones.** Unir registros de uso con planes vigentes por período, donde
  el cruce es por clave **y** por rango de fechas.

## Código fuente comentado

```python
import pandas as pd

from lab.core import audited_join
from lab.sqlbridge import cross_check, query

viajes = pd.read_csv("data/case_1/viajes.csv").drop_duplicates()
recorridos = pd.read_csv("data/case_1/recorridos.csv")

# 1. Procedimiento de cruce en cinco pasos.
antes = len(viajes)
assert recorridos["recorrido_id"].is_unique, "el catálogo no es único en su clave"
unido, auditoria = audited_join(viajes, recorridos, "recorrido_id", validate="many_to_one")
despues = len(unido)
huerfanas = int(unido["operador_id"].isna().sum())

print(f"antes={antes} despues={despues} factor={despues / antes:.4f} huerfanas={huerfanas}")
print(auditoria.to_string(index=False))   # recuento de both / left_only

# 2. El mismo recuento en SQL, como segunda opinión. Se carga como texto para que
#    SQL resuelva el casteo por su cuenta: así la validación es independiente.
crudos = {
    "viajes": pd.read_csv("data/case_1/viajes.csv", dtype=str, keep_default_na=False),
    "recorridos": pd.read_csv("data/case_1/recorridos.csv", dtype=str, keep_default_na=False),
}
sql = """
WITH unicos AS (SELECT DISTINCT * FROM viajes),
     base AS (
        SELECT u.viaje_id, r.operador_id
        FROM unicos u LEFT JOIN recorridos r ON r.recorrido_id = u.recorrido_id
     )
SELECT COUNT(*) AS filas, COUNT(operador_id) AS con_clave FROM base
"""
fila = query(crudos, sql).iloc[0]
print(f"SQL: filas={fila.filas} huerfanas={fila.filas - fila.con_clave}")

# 3. Confrontación formal de dos resultados: devuelve solo las filas discrepantes.
#    Un DataFrame vacío es el resultado deseado.
desde_pandas = (unido.loc[unido["estado"].eq("REALIZADO")]
                     .groupby("recorrido_id").size().rename("realizados").reset_index())
desde_sql = query(crudos, """
WITH unicos AS (SELECT DISTINCT * FROM viajes)
SELECT u.recorrido_id AS recorrido_id, COUNT(*) AS realizados
FROM unicos u JOIN recorridos r ON r.recorrido_id = u.recorrido_id
WHERE u.estado = 'REALIZADO'
GROUP BY u.recorrido_id ORDER BY u.recorrido_id
""")
diferencias = cross_check(desde_pandas, desde_sql, ["recorrido_id"], ["realizados"])
print("sin diferencias" if diferencias.empty else diferencias.to_string(index=False))
```

## Ejercicios prácticos

1. Cruce `viajes` con `recorridos` en `data/case_3` y calcule el factor de
   multiplicación y la tasa de claves huérfanas.
2. Duplique una fila de `recorridos` en memoria y repita el cruce con y sin
   `validate="many_to_one"`. Compare los dos comportamientos.
3. Escriba el `FULL OUTER JOIN` del cumplimiento emulado con dos `LEFT JOIN` en
   SQLite y verifique que conserva los días programados sin viajes.
4. Calcule la demanda por operador en Pandas y en SQL y confróntelas con
   `cross_check`. Si hay diferencias, diagnostíquelas.
5. Escriba el contrato de las cuatro tablas del caso y ejecútelo con
   `validate_dataset`. Clasifique cada hallazgo por severidad.
6. Introduzca un nulo en la columna de cruce de `viajes` y compare el comportamiento
   de `merge` en Pandas y de `JOIN` en SQL. Explique la diferencia.
7. Calcule la duración con `julianday` y con `strftime('%s')` sobre el caso 2 y cuente
   en cuántos viajes la comparación `duración ≤ meta` cambia de resultado.

## Soluciones explicadas

1. El factor debe ser exactamente 1 (cruce `muchos a uno` con catálogo único). Las
   huérfanas son 3 en el caso 3, correspondientes a `R99`.

2. Con `validate` se levanta `MergeError` inmediatamente. Sin `validate`, el resultado
   tiene más filas que la tabla izquierda y la suma de pasajeros se infla. El error
   ruidoso es preferible: el silencioso llega al informe.

3. La unión de dos `LEFT JOIN` conserva los 63 pares recorrido-día de la programación
   del caso 1 y agrega, si existieran, los días con viajes no programados. Recuerde
   los alias de columna en el primer `SELECT` para que el `ORDER BY` funcione.

4. Sobre los datos del laboratorio no debe haber diferencias. El orden de diagnóstico
   cuando las hay: filtro, casteo, denominador, precisión.

5. Los hallazgos esperados: `duplicados_exactos` (aviso) en `viajes`,
   `clave_desconocida` (error) en `viajes.recorrido_id`, `bajo_minimo` (error) en
   `pasajeros` por el valor negativo. `recorridos`, `operadores` y `programacion` deben
   salir limpias.

6. En Pandas, `merge` empareja `NaN` con `NaN` y produce una fila cruzada. En SQL,
   `NULL = NULL` es desconocido y la fila nunca empareja. Es una diferencia semántica
   real entre las dos tecnologías: al validar, las filas con clave nula son el primer
   lugar donde buscar discrepancias.

7. Cambia en todos los viajes cuya duración coincide exactamente con la meta del
   recorrido. En el caso 2 son varias decenas, suficientes para mover la puntualidad
   de un recorrido en más de dos puntos porcentuales.

## Errores frecuentes

- **Cruce interno por defecto**, que pierde las claves huérfanas en silencio.
- **No comprobar la unicidad del catálogo** antes de cruzar.
- **No contar las huérfanas**: el recuento es parte del informe de calidad.
- **Cambiar el grano sin advertirlo** y sumar sobre filas multiplicadas.
- **Cruzar por una columna con nulos** y suponer el mismo comportamiento en Pandas y
  en SQL.
- **`CAST` sobre cadena vacía en SQLite**, que convierte la ausencia en cero.
- **Validar reutilizando el mismo código**: no es validación, es repetición.
- **Declarar validado** lo que no se pudo recalcular.

## Criterios de validación

1. Cada cruce declara su cardinalidad esperada y la comprueba.
2. El factor de multiplicación se calcula y es 1 donde debe serlo.
3. Las claves huérfanas están contadas y reportadas.
4. Existe un contrato ejecutable por tabla, con severidades declaradas.
5. Al menos un indicador clave está recalculado con otra tecnología.
6. La tolerancia de comparación está declarada y toda diferencia mayor está explicada.
7. Lo que no se pudo validar aparece como «no verificado», nunca como aprobado.

## Preguntas de evaluación

1. ¿Qué garantiza `validate="many_to_one"` y qué error previene?
2. ¿Por qué un `LEFT JOIN` es el cruce por defecto en gestión de datos?
3. ¿Cómo se cuantifican las claves huérfanas en SQL con un solo `SELECT`?
4. ¿Por qué `NULL = NULL` es falso en SQL y qué consecuencia tiene al cruzar?
5. ¿Por qué `CAST('' AS REAL)` es peligroso en SQLite?
6. ¿Dos implementaciones que coinciden garantizan que el indicador es correcto? ¿Qué
   descartan y qué no?
7. ¿Por qué se declara una tolerancia al comparar dos implementaciones, y cuándo una
   diferencia deja de ser ruido numérico?

## Referencias verificables

- Documentación de pandas, «Merge, join, concatenate and compare».
  <https://pandas.pydata.org/docs/user_guide/merging.html>
- SQLite. «Query Language: SELECT» (incluye los tipos de `JOIN`).
  <https://www.sqlite.org/lang_select.html>
- SQLite. «Date And Time Functions».
  <https://www.sqlite.org/lang_datefunc.html>
- SQLite. «Datatypes In SQLite» (tipado dinámico y conversión por afinidad).
  <https://www.sqlite.org/datatype3.html>
- Date, C. J. *An Introduction to Database Systems*, 8.ª edición, Addison-Wesley,
  2003. Capítulos sobre álgebra relacional e integridad.
- DAMA International. *DAMA-DMBOK*, 2.ª edición, 2017. Capítulo 8, «Data Integration
  and Interoperability».
- Pandera, validación de esquemas de DataFrames. <https://pandera.readthedocs.io/>

## Glosario técnico

| Término | Definición |
| --- | --- |
| Cardinalidad | Relación entre filas de dos tablas al cruzar. |
| Clave huérfana | Clave foránea sin correspondencia en la tabla destino. |
| Contrato de datos | Declaración ejecutable del esquema y sus restricciones. |
| Cruce externo | Conserva las filas no emparejadas de ambas tablas. |
| Cruce interno | Conserva solo las claves presentes en ambas tablas. |
| Factor de multiplicación | Filas después del cruce sobre filas antes. |
| Grano del resultado | Lo que identifica una fila tras el cruce. |
| Integridad referencial | Toda clave foránea existe en su destino. |
| Tolerancia (τ) | Diferencia máxima admitida entre dos implementaciones. |
| Validación independiente | Recálculo con una implementación sin código común. |
