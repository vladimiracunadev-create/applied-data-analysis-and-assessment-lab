# Datos, tablas, tipos y claves

Primera clase del bloque de fundamentos. Todo lo que viene después —limpieza,
cruces, indicadores, modelos— depende de que estas cuatro ideas estén firmes.

## Objetivos de aprendizaje

Al terminar esta clase podrá:

1. Describir un conjunto de datos en términos de **unidad de análisis**, **grano**,
   **atributos** y **clave**.
2. Distinguir los tipos de dato lógicos y reconocer el daño que produce un tipo
   equivocado.
3. Identificar la clave primaria de una tabla y comprobar que efectivamente
   identifica cada fila.
4. Leer un archivo CSV y un libro de Excel declarando codificación y separador, y
   explicar qué se pierde en cada formato.
5. Escribir un diccionario de datos mínimo para una tabla cualquiera.

## Prerrequisitos

Ninguno de contenido. Se necesita un equipo con Python 3.11 o superior y una hoja de
cálculo (Excel, LibreOffice Calc o Google Sheets). Si va a usar el entorno del
laboratorio: `uv sync`.

## Definiciones simples y formales

**Dato.** *Simple:* un valor registrado sobre algo. *Formal:* la realización de una
variable para una unidad de observación en un momento determinado.

**Tabla.** *Simple:* filas y columnas. *Formal:* conjunto de tuplas que comparten un
esquema; cada columna es un atributo con un dominio y cada fila es una observación.
Una tabla está en forma **ordenada** (*tidy*) cuando cada variable es una columna,
cada observación es una fila y cada tipo de unidad ocupa su propia tabla.

**Unidad de análisis.** *Simple:* qué representa una fila. *Formal:* el objeto sobre
el que se mide. En `viajes.csv` la unidad es el viaje, no el vehículo ni el pasajero.

**Grano.** *Simple:* el nivel de detalle de la tabla. *Formal:* la combinación mínima
de atributos que identifica una fila de manera única. En `programacion.csv` el grano
es `recorrido_id` × `dia_octubre`.

**Clave primaria.** *Simple:* la columna (o columnas) que no se repiten. *Formal:*
subconjunto mínimo de atributos cuyos valores son únicos y no nulos en toda la tabla.

**Clave foránea.** Atributo que debe existir como clave primaria en otra tabla.
`viajes.recorrido_id` apunta a `recorridos.recorrido_id`.

**Tipo de dato.** *Simple:* qué clase de valor admite la columna. *Formal:* el dominio
de valores y el conjunto de operaciones válidas sobre ellos. Si `inicio` es texto, la
resta no está definida, aunque el valor «parezca» una fecha.

## Explicación conceptual

Un archivo de datos llega siempre con tres capas superpuestas y conviene separarlas
mentalmente antes de tocar nada.

La **capa física** es cómo están guardados los bytes: CSV con coma o punto y coma,
codificación UTF-8 o Latin-1, Excel con una hoja por tabla. Determina si el archivo se
abre bien, nada más.

La **capa lógica** es el esquema: qué columnas hay, de qué tipo, con qué dominio, qué
identifica una fila y qué apunta a otra tabla. Es la capa donde se decide si el
archivo es usable.

La **capa semántica** es qué significan los valores en el dominio del problema. Que
`pasajeros = 0` sea «nadie subió» y no «no se midió» es información semántica: no está
en el archivo, está en el diccionario de datos. Sin esa capa, dos analistas calculan
indicadores distintos con el mismo archivo y ambos creen tener razón.

El error más costoso de esta clase es confundir capas: tratar un problema semántico
(«¿el cero significa ausencia?») como un problema físico («el CSV viene mal») y
resolverlo con un reemplazo silencioso.

## Desarrollo de fundamentos

### Por qué el tipo decide el resultado

Una columna de texto que contiene `"43"` y una columna entera que contiene `43` se ven
igual al imprimirlas, pero se comportan distinto en tres operaciones críticas:

| Operación | Texto | Número |
| --- | --- | --- |
| Orden | `"10" < "9"` (lexicográfico) | `9 < 10` |
| Suma | concatena o falla | suma aritmética |
| Comparación con umbral | compara carácter a carácter | compara magnitudes |

El caso del orden es el que pasa más desapercibido: una tabla ordenada por un
identificador numérico almacenado como texto queda con `R1, R10, R2`, y quien revisa
asume que faltan filas.

### Por qué la clave hay que comprobarla y no suponerla

Un identificador llamado `viaje_id` no es una clave primaria por llamarse así. Lo es
si y solo si sus valores son únicos y no nulos **en los datos que usted recibió**. Las
dos formas en que falla:

- **Repetición por duplicado exacto.** Toda la fila está repetida. Se puede eliminar
  sin perder información, dejando constancia del recuento.
- **Repetición con contenido distinto.** El mismo identificador con valores
  diferentes. Aquí no se puede elegir una fila al azar: hay que decidir una regla
  (la más reciente, la que tiene más campos completos) y declararla.

### Codificación: el problema que se ve y el que no

Un CSV es texto, y el texto necesita una codificación para interpretar los bytes.
UTF-8 representa todos los caracteres; Latin-1 (cp1252 en Windows) solo un subconjunto.
Abrir un UTF-8 como Latin-1 convierte `operación` en `operaciÃ³n`: el daño es visible.
El caso peligroso es el inverso en archivos sin tildes: el archivo se abre «bien» y el
problema aparece meses después, con el primer nombre acentuado.

Excel en Windows asume la codificación del sistema al hacer doble clic sobre un CSV.
Para controlar la lectura se usa **Datos → Obtener datos → Desde texto/CSV**, donde la
codificación y el separador se eligen explícitamente. Por eso los CSV del laboratorio
se escriben con `utf-8-sig`: el marcador inicial (BOM) le indica a Excel que el
archivo es UTF-8.

## Fórmulas matemáticas explicadas

Esta clase usa dos razones elementales que se repetirán en todo el programa.

**Unicidad de una clave.**

```
unicidad = filas_distintas_en_la_clave / filas_totales
```

Si `unicidad = 1`, la clave identifica cada fila. Si `unicidad < 1`, la diferencia
`filas_totales − filas_distintas` es exactamente el número de filas sobrantes.

**Completitud de una columna.**

```
completitud = 100 · valores_presentes / filas_totales        [%]
```

«Presente» significa no nulo **y** convertible al tipo declarado. Una columna con
texto en una columna numérica tiene valores presentes físicamente pero ausentes
lógicamente, y es la segunda cuenta la que importa.

## Significado de variables, símbolos y unidades

| Símbolo | Significado | Unidad |
| --- | --- | --- |
| `filas_totales` | Número de registros del archivo | filas |
| `filas_distintas_en_la_clave` | Valores diferentes de la clave | filas |
| `valores_presentes` | Valores no nulos y del tipo correcto | valores |
| `completitud` | Proporción de la columna utilizable | % |
| `unicidad` | Proporción en [0, 1]; 1 es una clave válida | adimensional |

Convención del laboratorio: las proporciones se expresan en el rango [0, 1] y los
porcentajes en [0, 100]. Mezclarlas produce indicadores con un factor 100 de error,
que es el error más frecuente y el más fácil de detectar si se declara la unidad.

## Ejemplos, de simple a complejo

### Ejemplo 1 — una tabla de cuatro filas

| id | producto | cantidad |
| --- | --- | --- |
| 1 | A | 2 |
| 2 | B | 1 |
| 3 | A | 5 |
| 3 | A | 5 |

Unidad de análisis: la transacción. Grano: `id`. Clave candidata: `id`, con unicidad
`3/4 = 0,75`, de modo que **no** es clave en estos datos. El duplicado es exacto:
eliminarlo deja `unicidad = 1` sin perder información.

### Ejemplo 2 — el mismo identificador con contenido distinto

| id | producto | cantidad |
| --- | --- | --- |
| 7 | A | 2 |
| 7 | A | 9 |

Aquí no hay duplicado exacto. Hay un conflicto: dos versiones de la misma
transacción. Eliminar «el duplicado» significa elegir entre 2 y 9 unidades, y la
elección cambia el resultado. Esto se resuelve con una regla declarada, no con
`drop_duplicates()`.

### Ejemplo 3 — grano compuesto

`programacion.csv` tiene `recorrido_id`, `dia_octubre` y `viajes_programados`. Ninguna
columna sola es clave: `R01` aparece una vez por día. El grano es la pareja. Comprobar
la clave compuesta es lo que impide, más adelante, que un cruce multiplique filas.

## Aplicaciones profesionales

- **Transporte.** Antes de informar demanda hay que saber si una fila es un viaje, un
  vehículo o una validación de tarjeta. Los tres dan números distintos y los tres se
  llaman «demanda» en alguna conversación.
- **Salud.** La unidad puede ser el paciente, el episodio de atención o la
  prestación. Un indicador «por paciente» calculado sobre prestaciones cuenta de más
  a quien se atendió varias veces.
- **Banca.** El grano de una tabla de movimientos es la transacción; el de un estado
  de cuenta, el día. Sumar saldos diarios como si fueran movimientos duplica el monto.
- **Recursos humanos.** Una tabla de dotación con grano mensual y otra de
  remuneraciones con grano de liquidación no se cruzan directamente sin definir el
  grano común.

## Código fuente comentado

```python
from pathlib import Path
import pandas as pd

from lab.contracts import Column, TableContract, contract_markdown
from lab.core import profile

RUTA = Path("data/case_1/viajes.csv")

# 1. Lectura explícita. Se declaran separador y codificación en lugar de confiar en
#    la detección automática: un archivo que hoy se detecta bien puede cambiar.
#    dtype=str mantiene todo como texto para ver los datos como realmente llegan,
#    sin que pandas adivine tipos y oculte los valores problemáticos.
crudo = pd.read_csv(RUTA, sep=",", encoding="utf-8-sig", dtype=str, keep_default_na=False)

# 2. Perfil rápido: tipos, nulos, valores únicos y duplicados exactos por columna.
print(profile(crudo).to_string(index=False))

# 3. Comprobación de la clave candidata. No se supone: se mide.
unicidad = crudo["viaje_id"].nunique() / len(crudo)
duplicados_exactos = int(crudo.duplicated().sum())
duplicados_de_clave = int(crudo["viaje_id"].duplicated().sum())
print(f"unicidad={unicidad:.4f} exactos={duplicados_exactos} "
      f"clave_repetida={duplicados_de_clave}")

# 4. Si ambos recuentos coinciden, toda repetición de la clave viene de filas
#    idénticas y se puede eliminar. Si clave_repetida > exactos, hay conflictos
#    reales que exigen una regla de resolución declarada.

# 5. El contrato convierte las expectativas en código ejecutable, de modo que la
#    próxima entrega del archivo se valide sola.
contrato = TableContract(
    name="viajes",
    columns=(
        Column("viaje_id", "texto", nullable=False, unique=True),
        Column("recorrido_id", "texto", nullable=False),
        Column("inicio", "fecha_hora"),
        Column("fin", "fecha_hora"),
        Column("pasajeros", "entero", minimum=0, unit="personas"),
        Column("estado", "texto", allowed=("REALIZADO", "CANCELADO")),
    ),
    primary_key=("viaje_id",),
)
informe = contrato.validate(crudo)
print(informe.to_frame().to_string(index=False))

# 6. El diccionario de datos se genera desde el contrato: una sola fuente de verdad,
#    imposible que la documentación quede desincronizada del código.
print(contract_markdown(contrato))
```

## Ejercicios prácticos

1. Lea `data/case_1/viajes.csv` y determine la unidad de análisis, el grano y la
   clave primaria. Justifique con números, no con la intuición.
2. Calcule la completitud de cada columna. Para `pasajeros`, informe por separado las
   celdas vacías y los valores que no son números.
3. Separe los duplicados exactos de los duplicados de clave con contenido distinto.
   Informe ambos recuentos.
4. Abra el mismo CSV en Excel usando **Datos → Desde texto/CSV** con UTF-8, y después
   con Latin-1. Describa la diferencia observada.
5. Escriba el contrato de `programacion.csv` con clave primaria compuesta y valídelo.
   ¿Qué hallazgos aparecen?
6. Una tabla tiene `unicidad = 0,98` y cero duplicados exactos. ¿Qué está ocurriendo y
   qué información necesita para resolverlo?

## Soluciones explicadas

1. **Unidad:** el viaje. **Grano:** `viaje_id`. **Clave:** `viaje_id` tras eliminar
   duplicados exactos; antes de eliminarlos, la unicidad es menor que 1. En el caso 1
   hay 454 filas y 4 duplicados exactos, de modo que `unicidad = 450/454 ≈ 0,9912`.

2. `pasajeros` tiene celdas vacías (valor no registrado) y un valor negativo (valor
   imposible). Con `dtype=str` ambos se ven como texto; con `pd.to_numeric(...,
   errors="coerce")` el vacío pasa a `NaN` y el `-5` sigue siendo numérico pero
   inválido por dominio. Son dos defectos distintos que se cuentan por separado:

   ```python
   vacios = (crudo.pasajeros.str.strip() == "").sum()
   numerico = pd.to_numeric(crudo.pasajeros, errors="coerce")
   negativos = int((numerico < 0).sum())
   ```

3. `crudo.duplicated().sum()` da los exactos; `crudo.viaje_id.duplicated().sum()` da
   las repeticiones de clave. En los datos del laboratorio ambos coinciden, de modo
   que no hay conflictos de contenido. Si no coincidieran, la diferencia sería el
   número de conflictos reales.

4. Con Latin-1 los acentos aparecen como caracteres extraños. Con UTF-8 se leen
   correctamente. Los CSV del laboratorio llevan BOM (`utf-8-sig`) para que Excel
   acierte sin intervención.

5. El contrato de `programacion.csv` declara `primary_key=("recorrido_id",
   "dia_octubre")`. Si se declarara solo `recorrido_id`, la validación reportaría
   `clave_primaria_repetida` con tantas filas sobrantes como días tenga cada
   recorrido. Es el mecanismo que detecta un grano mal entendido.

6. Hay repeticiones de clave con contenido distinto: el 2 % de las filas son versiones
   en conflicto. Se necesita saber qué significa la repetición en el sistema de
   origen: ¿correcciones sucesivas, cargas duplicadas parciales, dos sistemas que
   usan el mismo identificador? Sin esa respuesta, cualquier regla de resolución es
   una invención.

## Errores frecuentes

- **Dejar que la herramienta adivine el tipo** y descubrir después que una columna
  de identificadores quedó como número, perdiendo los ceros a la izquierda.
- **Llamar «clave» a una columna por su nombre** sin medir la unicidad.
- **Eliminar duplicados sin contar** cuántos se eliminaron: el recuento es parte del
  informe de calidad, no un detalle de implementación.
- **Confundir celda vacía con cero.** Ver [[vacio-no-es-cero]] en la base de
  conocimiento.
- **Mezclar granos al cruzar**, que multiplica filas y produce sumas infladas con
  apariencia razonable.
- **Guardar un CSV desde Excel sin elegir codificación** y romper los acentos para
  todos los consumidores siguientes.

## Criterios de validación

Una entrega de esta clase se considera correcta si:

1. La unidad de análisis y el grano están escritos en una frase cada uno.
2. La unicidad de la clave está calculada, no afirmada.
3. Los recuentos de duplicados exactos y de clave aparecen por separado.
4. La completitud distingue valores ausentes de valores del tipo equivocado.
5. Existe un contrato ejecutable y su informe de hallazgos está adjunto.
6. El diccionario de datos declara, por columna, tipo, unidad y dominio.

## Preguntas de evaluación

1. Una tabla tiene 1 000 filas y su columna `id` tiene 998 valores distintos, con cero
   duplicados exactos. ¿Es `id` una clave primaria? ¿Qué haría a continuación?
2. ¿Por qué `"10" < "9"` es verdadero en una comparación de texto y falso en una
   comparación numérica? ¿Qué consecuencia práctica tiene al ordenar un informe?
3. Explique la diferencia entre grano y unidad de análisis con un ejemplo donde no
   coincidan.
4. Un CSV abre con los acentos rotos. ¿Qué capa del problema está afectada y qué
   información necesita para resolverlo?
5. ¿En qué situación es correcto eliminar filas duplicadas y en qué situación no?
6. Al cruzar `viajes` con `recorridos`, el resultado tiene más filas que `viajes`.
   ¿Qué ocurrió y cómo se previene?

## Referencias verificables

- Wickham, H. y Grolemund, G. *R for Data Science*, 2.ª edición, O'Reilly, 2023.
  Capítulos sobre importación de datos y datos ordenados. <https://r4ds.hadley.nz/>
- Wickham, H. «Tidy Data». *Journal of Statistical Software*, 59(10), 2014.
  doi:10.18637/jss.v059.i10
- Documentación de pandas, guía de entrada y salida de datos.
  <https://pandas.pydata.org/docs/user_guide/io.html>
- Microsoft. «Importar o exportar archivos de texto (.txt o .csv)».
  <https://support.microsoft.com/es-es/office/importar-o-exportar-archivos-de-texto-txt-o-csv-5250ac4c-663c-47ce-937b-339e391393ba>
- ISO/IEC 25012:2008, *Data quality model*. Define las características de calidad de
  datos que esta clase mide de forma elemental.
- DAMA International. *DAMA-DMBOK: Data Management Body of Knowledge*, 2.ª edición,
  2017. Capítulo de metadatos y calidad de datos.

## Glosario técnico

| Término | Definición |
| --- | --- |
| Atributo | Columna de una tabla; una variable medida sobre la unidad. |
| BOM | Marca inicial de un archivo de texto que declara su codificación. |
| Clave candidata | Conjunto de columnas que podría ser clave primaria. |
| Clave foránea | Atributo que referencia la clave primaria de otra tabla. |
| Clave primaria | Conjunto mínimo de columnas únicas y no nulas. |
| Codificación | Correspondencia entre bytes y caracteres (UTF-8, Latin-1). |
| Completitud | Proporción de valores presentes y del tipo correcto. |
| Dominio | Conjunto de valores admitidos por una columna. |
| Esquema | Declaración de columnas, tipos y restricciones de una tabla. |
| Grano | Nivel de detalle: lo que identifica una fila de forma única. |
| Tidy data | Forma ordenada: una variable por columna, una observación por fila. |
| Unidad de análisis | Objeto sobre el que se mide cada fila. |
| Unicidad | Proporción de valores distintos sobre el total de filas. |
