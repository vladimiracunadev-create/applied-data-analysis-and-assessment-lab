# Calidad de datos: medir antes de limpiar

## Objetivos de aprendizaje

1. Enumerar las dimensiones de calidad de datos y traducir cada una en una medición
   concreta.
2. Construir un informe de calidad que cuantifique cada defecto y declare su efecto
   sobre cada indicador.
3. Decidir, con criterio explícito, entre conservar, excluir, corregir o rechazar un
   registro defectuoso.
4. Expresar las reglas de calidad como un contrato ejecutable.

## Prerrequisitos

Clase `01-datos-tablas-y-tipos` de este bloque: unidad de análisis, grano, clave y
tipos.

## Definiciones simples y formales

**Calidad de datos.** *Simple:* si los datos sirven para lo que se quiere hacer con
ellos. *Formal:* grado en que un conjunto de datos satisface los requisitos de un uso
determinado. La calidad no es una propiedad absoluta del archivo: es una relación
entre el archivo y el uso. Los mismos datos pueden ser aptos para un indicador
agregado e inaptos para uno individual.

**Dimensión de calidad.** Aspecto medible de esa aptitud. Las seis que usa el
laboratorio:

| Dimensión | Pregunta que responde | Medición |
| --- | --- | --- |
| Completitud | ¿Falta información? | % de valores presentes y convertibles |
| Unicidad | ¿Hay registros repetidos? | duplicados exactos y de clave |
| Validez | ¿Los valores son posibles? | % fuera de tipo, rango o dominio |
| Consistencia | ¿Las reglas entre campos se cumplen? | nº de violaciones (`fin ≥ inicio`) |
| Integridad referencial | ¿Las claves existen? | nº de claves huérfanas |
| Exactitud | ¿El valor corresponde a la realidad? | requiere una fuente de verdad externa |

**Exactitud.** Es la única dimensión que **no** se puede medir dentro del archivo:
necesita una fuente independiente contra la que comparar. Declararla «correcta» sin
esa fuente es una afirmación sin respaldo.

**Severidad.** Clasificación del hallazgo. En el laboratorio: `error` impide usar los
datos para el indicador afectado; `aviso` exige decisión documentada pero no bloquea.

## Explicación conceptual

El impulso natural frente a un archivo sucio es limpiarlo. El orden correcto es el
inverso: **medir, decidir, documentar y solo entonces transformar.**

La razón es que la limpieza destruye evidencia. Si se eliminan las filas con
`pasajeros` vacío antes de contarlas, el informe ya no puede decir cuánta demanda
quedó sin registrar, y quien lea el resultado no tiene cómo juzgar su cobertura. El
recuento del defecto es parte del resultado, no un paso previo descartable.

La segunda razón es que la decisión depende del indicador, no del registro. Un viaje
realizado con `pasajeros` nulo:

- **sirve** para el cumplimiento de la programación (el viaje ocurrió);
- **sirve** para la duración (hay inicio y fin);
- **no sirve** para la demanda (no hay conteo).

Eliminar la fila degrada dos indicadores correctos para proteger uno. Marcarla con
banderas por indicador conserva los tres. Esa es la diferencia entre limpiar una tabla
y calificar cada registro para cada uso.

## Desarrollo de fundamentos

### Las cuatro decisiones posibles ante un defecto

| Decisión | Cuándo | Qué hay que documentar |
| --- | --- | --- |
| **Conservar** | El defecto no afecta al indicador en cuestión | Qué indicadores lo usan y cuáles no |
| **Excluir** | El valor es imposible o falta | Recuento excluido y cobertura resultante |
| **Corregir** | Existe una regla determinista y verificable | La regla y su justificación |
| **Rechazar la carga** | El archivo incumple su contrato en lo esencial | El hallazgo bloqueante |

**Imputar** —rellenar con la media, con el valor anterior o con cero— no aparece en
esta tabla. Es una técnica legítima en modelamiento, pero en un informe operacional
convierte una ausencia medida en un número inventado. Si se usa, debe declararse en el
informe, no esconderse en el código.

### Severidad: por qué un duplicado exacto es aviso y un nulo en la clave es error

Un duplicado exacto no destruye información: la fila original sigue ahí, y el
tratamiento (eliminar, contando) es inequívoco. Una clave primaria nula sí destruye
información: ese registro no se puede relacionar con nada y no hay regla que lo
recupere. De ahí la diferencia de severidad en `lab.contracts`.

### La cobertura cierra el informe

Después de excluir, hay que informar qué proporción de la población objetivo quedó
representada. Sin cobertura, un indicador correcto se lee como si describiera el
total. Ver [[cobertura-de-un-indicador]].

## Fórmulas matemáticas explicadas

**Completitud de una columna.**

```
C = 100 · n_presentes / n_filas              [%]
```

`n_presentes` cuenta los valores no nulos **y** convertibles al tipo declarado.

**Tasa de defecto.**

```
D = 100 · n_defectuosos / n_evaluados        [%]
```

El denominador es el número de filas donde la regla **aplica**, no el total. Una regla
de consistencia entre `inicio` y `fin` no aplica a los viajes cancelados, que no
tienen `fin`. Usar el total como denominador diluye el defecto y lo hace parecer menor.

**Cobertura de un indicador.**

```
K = 100 · n_usados / n_objetivo              [%]
```

**Índice compuesto de calidad** (opcional, y con advertencia):

```
Q = Σ wᵢ · qᵢ ,   con Σ wᵢ = 1
```

donde `qᵢ` es la puntuación de la dimensión *i* en [0, 1] y `wᵢ` su peso. Un índice
compuesto resume bien para un tablero y oculta bien el problema concreto: `Q = 0,94`
no dice qué hay que arreglar. Úselo junto al detalle, nunca en su lugar.

## Significado de variables, símbolos y unidades

| Símbolo | Significado | Unidad |
| --- | --- | --- |
| `n_filas` | Filas del archivo | filas |
| `n_presentes` | Valores no nulos y del tipo correcto | valores |
| `n_evaluados` | Filas donde la regla aplica | filas |
| `n_defectuosos` | Filas que incumplen la regla | filas |
| `n_usados` | Registros que entraron al cálculo del indicador | registros |
| `n_objetivo` | Registros que debían entrar | registros |
| `C`, `D`, `K` | Completitud, tasa de defecto, cobertura | % |
| `wᵢ` | Peso de la dimensión *i* | adimensional, suma 1 |

## Ejemplos, de simple a complejo

### Ejemplo 1 — completitud con denominador correcto

Columna `fin` con 100 filas: 94 tienen valor, 6 están vacías. Pero las 6 vacías
corresponden a viajes cancelados, donde `fin` **no debe** existir.

- Completitud bruta: `94/100 = 94 %`.
- Completitud sobre las filas donde aplica: `94/94 = 100 %`.

El primer número sugiere un problema de registro; el segundo muestra que no hay
ninguno. Declarar el denominador es lo que distingue un informe útil de una alarma
falsa.

### Ejemplo 2 — consistencia entre campos

Regla: `fin ≥ inicio`. Sobre 94 viajes realizados, 2 tienen `fin < inicio`. Tasa de
defecto: `2/94 ≈ 2,1 %`. Esos 2 viajes se excluyen de duración (donde el valor es
imposible) y se conservan para cumplimiento (el viaje ocurrió). La duración queda con
cobertura `92/94 ≈ 97,9 %`.

### Ejemplo 3 — el informe completo de un caso

| Indicador de calidad | Valor | Severidad | Efecto declarado |
| --- | --- | --- | --- |
| filas_originales | 454 | — | referencia |
| duplicados_exactos | 4 | aviso | se eliminan; todos los indicadores |
| claves_desconocidas | 1 | error | excluida de indicadores por recorrido |
| pasajeros_invalidos_realizados | 1 | error | excluido solo de demanda |
| duracion_invalida_realizados | 0 | — | sin efecto |

Esta tabla es el entregable mínimo de calidad: cada fila dice **qué** pasa, **cuánto**
y **a qué indicador afecta**.

## Aplicaciones profesionales

- **Transporte.** La cobertura del conteo de pasajeros determina si la demanda
  informada es comparable entre operadores o si refleja diferencias de registro.
- **Salud.** Un diagnóstico ausente no es un diagnóstico negativo. Tratarlos igual
  subestima la prevalencia.
- **Banca y seguros.** La integridad referencial entre movimientos y titulares es
  requisito regulatorio, no una buena práctica opcional.
- **Administración pública.** Un indicador publicado sin cobertura es un indicador
  que no se puede auditar, y en un organismo público eso es un problema de
  transparencia además de uno técnico.
- **Manufactura.** Una lectura de sensor fuera de rango físico es un fallo del
  sensor: imputarla con la media borra la señal de falla.

## Código fuente comentado

```python
import pandas as pd

from lab.contracts import Column, ForeignKey, TableContract, findings_frame, validate_dataset
from lab.dates import date_quality, duration_minutes, parse_datetime
from lab.metrics import coverage, indicator_table, safe_ratio

crudos = {
    "viajes": pd.read_csv("data/case_1/viajes.csv", dtype=str, keep_default_na=False),
    "recorridos": pd.read_csv("data/case_1/recorridos.csv", dtype=str, keep_default_na=False),
}

# 1. Contrato: las expectativas quedan escritas una vez y se comprueban siempre.
#    allow_missing=False en la clave foránea porque una clave desconocida impide
#    calcular indicadores por recorrido: es un error, no un aviso.
viajes = TableContract(
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
    foreign_keys=(ForeignKey("recorrido_id", "recorridos", "recorrido_id"),),
)
recorridos = TableContract(
    name="recorridos",
    columns=(
        Column("recorrido_id", "texto", nullable=False, unique=True),
        Column("operador_id", "texto", nullable=False),
        Column("meta_min", "decimal", minimum=0, unit="min"),
    ),
    primary_key=("recorrido_id",),
)

# 2. Validación conjunta: resuelve las claves foráneas entre tablas.
informes = validate_dataset([viajes, recorridos], crudos)
print(findings_frame(informes.values()).to_string(index=False))

# 3. Calidad específica de las columnas de fecha: separa vacío de no interpretable.
print(date_quality(crudos["viajes"]["inicio"]).to_string(index=False))

# 4. Consistencia entre campos. El denominador son los viajes REALIZADOS, no el
#    total: en un cancelado la regla fin >= inicio no aplica.
viajes_df = crudos["viajes"].drop_duplicates().copy()
realizado = viajes_df["estado"].eq("REALIZADO")
inicio = parse_datetime(viajes_df["inicio"]).values
fin = parse_datetime(viajes_df["fin"]).values
duracion = duration_minutes(inicio, fin)
evaluados = int(realizado.sum())
defectuosos = int((realizado & (duracion.isna() | duracion.lt(0))).sum())

# 5. Informe final: valor, unidad y definición por indicador. indicator_table
#    obliga a declarar las dos últimas, que es lo que lo hace auditable.
print(indicator_table({
    "filas_originales": (len(crudos["viajes"]), "filas", "Registros del archivo original"),
    "duplicados_exactos": (len(crudos["viajes"]) - len(viajes_df), "filas",
                           "Filas idénticas en todas sus columnas"),
    "duracion_invalida_pct": (safe_ratio(defectuosos, evaluados, scale=100), "%",
                              "Realizados con fin ausente o anterior al inicio"),
    "cobertura_pasajeros_pct": (coverage(viajes_df["pasajeros"]), "%",
                                "Valores convertibles a número sobre el total de filas"),
}).to_string(index=False))
```

## Ejercicios prácticos

1. Construya el contrato de `programacion.csv` (clave compuesta) y valídelo contra
   `recorridos.csv`. Informe los hallazgos por severidad.
2. Calcule la completitud de `fin` con dos denominadores: todas las filas y solo los
   viajes realizados. Explique cuál informaría y por qué.
3. Para cada defecto del caso 1, escriba la decisión tomada (conservar, excluir,
   corregir, rechazar) y los indicadores afectados.
4. Añada al contrato una regla que detecte `fin` presente en un viaje cancelado.
   ¿Debería ser error o aviso? Justifique.
5. Construya un índice compuesto de calidad con pesos propios y explique qué
   información se pierde al resumirlo en un solo número.
6. Repita el ejercicio 1 sobre `data/case_3`. ¿Las tasas de defecto cambian o solo
   los recuentos absolutos? ¿Qué implica eso sobre el generador de datos?

## Soluciones explicadas

1. El contrato lleva `primary_key=("recorrido_id", "dia_octubre")` y una clave foránea
   a `recorridos`. Sobre los datos del laboratorio no debe arrojar errores: la
   programación está completa y sus claves existen.

2. Sobre todas las filas, la completitud de `fin` ronda el 94 %. Sobre los realizados
   es 100 %. Se informa la segunda, declarando el denominador: «`fin` está presente en
   el 100 % de los viajes realizados; está vacío por diseño en los cancelados».

3. Duplicados exactos → **excluir** (eliminar contando), afecta a todos los
   indicadores. Clave desconocida → **excluir** de indicadores por recorrido,
   **conservar** en los recuentos globales de calidad. `pasajeros` nulo o negativo →
   **conservar** para cumplimiento y duración, **excluir** de demanda. `fin < inicio`
   → **excluir** de duración, conservar en cumplimiento.

4. Debería ser **aviso**. Un `fin` en un viaje cancelado es inconsistente con la
   semántica declarada, pero no impide calcular ningún indicador: los cancelados ya
   están fuera de duración y demanda. Lo que exige es una pregunta al origen de los
   datos, no un bloqueo de la carga.

5. Con pesos iguales sobre cinco dimensiones medibles, `Q` resume la situación en un
   número comparable entre cargas. Lo que se pierde es la acción: `Q = 0,94` no
   indica si el 6 % faltante son claves huérfanas (bloqueantes) o duplicados exactos
   (triviales). El índice sirve para seguir la tendencia, no para decidir.

6. Los recuentos crecen (4, 8 y 12 duplicados en los casos 1, 2 y 3) mientras el
   volumen crece más rápido (450, 1 400 y 3 500 viajes). Las **tasas** por lo tanto
   bajan. Implica que el generador introduce un número fijo de defectos por caso y no
   una proporción, lo que conviene saber antes de comparar casos entre sí.

## Errores frecuentes

- **Limpiar antes de medir**, y perder así el recuento del defecto.
- **Usar el total como denominador** de una regla que no aplica a todas las filas.
- **Imputar en silencio.** Rellenar con cero o con la media sin declararlo convierte
  una ausencia en un dato.
- **Una sola decisión para toda la fila**, en lugar de una decisión por indicador.
- **Declarar exactitud sin fuente externa.** Lo que se mide dentro del archivo es
  validez y consistencia, no exactitud.
- **Resumir la calidad en un índice** y perder la acción concreta.

## Criterios de validación

1. Existe un informe con un hallazgo por regla, con recuento y severidad.
2. Cada defecto declara los indicadores que afecta.
3. Los denominadores de las tasas de defecto son las filas donde la regla aplica.
4. Toda exclusión está contada y toda corrección tiene regla escrita.
5. Cada indicador final informa su cobertura.
6. El contrato es ejecutable y la próxima carga se valida sin intervención manual.

## Preguntas de evaluación

1. ¿Por qué la exactitud no se puede medir dentro del propio archivo?
2. Un archivo tiene 5 % de `pasajeros` nulos. ¿Qué indicadores puede calcular y
   cuáles no?
3. ¿Qué distingue excluir de imputar, y por qué el laboratorio prefiere lo primero en
   un informe operacional?
4. Una regla de consistencia tiene 2 violaciones en 500 filas, pero solo aplica a 94.
   ¿Cuál es la tasa de defecto y por qué importa la diferencia?
5. ¿Cuándo un duplicado exacto no se puede eliminar sin perder información?
6. ¿Qué información debe acompañar a todo indicador para que sea auditable?

## Referencias verificables

- ISO/IEC 25012:2008, *Software engineering — Software product Quality Requirements
  and Evaluation (SQuaRE) — Data quality model*.
- ISO 8000, serie de normas sobre calidad de datos.
- DAMA International. *DAMA-DMBOK*, 2.ª edición, 2017. Capítulo 13, «Data Quality».
- Documentación de pandas, «Working with missing data».
  <https://pandas.pydata.org/docs/user_guide/missing_data.html>
- Pandera, biblioteca de validación de esquemas para DataFrames.
  <https://pandera.readthedocs.io/>
- Rahm, E. y Do, H. H. «Data Cleaning: Problems and Current Approaches». *IEEE Data
  Engineering Bulletin*, 23(4), 2000, pp. 3-13.

## Glosario técnico

| Término | Definición |
| --- | --- |
| Cobertura | Proporción de la población objetivo representada en el cálculo. |
| Completitud | Proporción de valores presentes y del tipo correcto. |
| Consistencia | Cumplimiento de reglas que relacionan varios campos. |
| Contrato de datos | Declaración ejecutable de las expectativas sobre una tabla. |
| Exactitud | Correspondencia con la realidad; exige fuente externa. |
| Imputación | Reemplazo de un valor ausente por uno estimado. |
| Integridad referencial | Toda clave foránea existe en su tabla destino. |
| Severidad | Gravedad del hallazgo: error o aviso. |
| Tasa de defecto | Filas que incumplen una regla sobre las filas donde aplica. |
| Unicidad | Ausencia de registros repetidos según la clave. |
| Validez | Conformidad con el tipo, el rango y el dominio declarados. |
