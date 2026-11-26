# Estadística descriptiva: resumir sin engañar

## Objetivos de aprendizaje

1. Elegir la medida de tendencia central adecuada según la forma de la distribución.
2. Calcular e interpretar dispersión, percentiles y rango intercuartílico.
3. Declarar el método de interpolación de un percentil y entender por qué dos
   herramientas pueden dar valores distintos para el mismo percentil.
4. Detectar valores atípicos con un criterio reproducible y decidir qué hacer con
   ellos.
5. Distinguir una tasa ponderada de un promedio de tasas, y puntos porcentuales de
   variación porcentual.

## Prerrequisitos

Bloque de fundamentos completo. Aritmética básica y noción de fracción. No se requiere
cálculo diferencial.

## Definiciones simples y formales

**Media aritmética.** *Simple:* el total repartido en partes iguales. *Formal:* el
primer momento de la distribución empírica,
`x̄ = (1/n) Σ xᵢ`. Minimiza la suma de desviaciones al cuadrado.

**Mediana.** *Simple:* el valor del medio. *Formal:* el valor `m` tal que al menos la
mitad de las observaciones son ≤ `m` y al menos la mitad son ≥ `m`. Minimiza la suma
de desviaciones absolutas.

**Moda.** El valor más frecuente. Única medida de centro aplicable a variables
categóricas.

**Desviación estándar muestral.** *Simple:* cuánto se alejan los valores del promedio.
*Formal:* `s = √[ Σ(xᵢ − x̄)² / (n − 1) ]`. El divisor `n − 1` (corrección de Bessel)
hace que `s²` sea un estimador no sesgado de la varianza poblacional.

**Percentil `p`.** Valor por debajo del cual se encuentra aproximadamente el `p` por
ciento de las observaciones. El «aproximadamente» es la razón de que existan varios
métodos de cálculo.

**Rango intercuartílico (IQR).** `IQR = P75 − P25`. Dispersión de la mitad central,
inmune a los extremos.

**Valor atípico.** Observación alejada del resto según un criterio declarado. No es
sinónimo de error: puede ser el dato más informativo del conjunto.

**Robustez.** Propiedad de un estadístico que apenas cambia ante una observación
extrema. La mediana es robusta; la media no lo es.

## Explicación conceptual

Resumir es perder información a propósito. La pregunta no es si se pierde, sino si lo
que queda responde la pregunta que se hizo.

Con duraciones de viaje, la media y la mediana cuentan historias distintas. Si un
recorrido tiene duración mediana de 43 minutos y media de 52, hay una cola de viajes
muy largos tirando la media hacia arriba. Informar solo la media sugiere que el viaje
típico dura 52 minutos, lo que no le ocurre a la mayoría. Informar solo la mediana
oculta que existe esa cola, que es justamente el problema operacional.

La regla práctica: **con distribuciones asimétricas se informan las dos, y además un
percentil alto.** El P90 responde «¿cuánto dura el viaje en el 10 % de los peores
casos?», que es la pregunta que hace quien debe planificar una frecuencia.

El segundo riesgo del resumen es el denominador. Una tasa de cumplimiento del 95 %
puede ser el cociente de las sumas o el promedio de los cocientes. Son dos números
distintos y ambos se llaman «cumplimiento». Ver
[[tasa-ponderada-vs-promedio-simple]].

## Desarrollo de fundamentos

### Por qué los percentiles no son únicos

Con `n = 4` valores `[1, 2, 3, 4]`, ¿cuál es el percentil 90? No hay una observación
en esa posición: el percentil cae entre la tercera y la cuarta. Hay que **interpolar**,
y existen varios criterios. Con el método lineal (el que usan NumPy y Excel en
`PERCENTIL.INC`), la posición es:

```
h = (n − 1) · q = 3 · 0,9 = 2,7     (índice base cero)
P90 = x₂ + 0,7 · (x₃ − x₂) = 3 + 0,7 · 1 = 3,7
```

Con el método `lower` el resultado es 3; con `higher`, 4. Ninguno está mal; son
definiciones distintas. Hyndman y Fan catalogaron nueve métodos usados en paquetes
estadísticos. Excel tiene dos funciones distintas: `PERCENTIL.INC` (inclusivo, como
NumPy lineal) y `PERCENTIL.EXC` (exclusivo), que dan valores diferentes.

**Consecuencia práctica.** Si el P90 de Excel y el de Python no coinciden, lo primero
que hay que comprobar no es el filtro de los datos: es qué método usa cada
herramienta. `lab.metrics.percentile` obliga a nombrarlo.

### Por qué `n − 1` y no `n`

La varianza poblacional divide por `n`, pero cuando se estima usando la media muestral
`x̄` —calculada de los mismos datos— los residuos tienen un grado de libertad menos.
Dividir por `n − 1` corrige el sesgo hacia abajo que tendría dividir por `n`. Con
`n = 100` la diferencia es del 1 %; con `n = 5`, del 25 %.

En pandas, `Series.std()` usa `ddof=1` por defecto; en NumPy, `np.std()` usa `ddof=0`.
Es una fuente habitual de discrepancias entre dos cálculos del «mismo» indicador.

### Criterio de Tukey para atípicos

```
límite inferior = P25 − k · IQR
límite superior = P75 + k · IQR
```

Con `k = 1,5` se señalan atípicos; con `k = 3`, atípicos extremos. El criterio es
convencional, no una prueba estadística: no dice que el valor sea un error, dice que
está lejos. La decisión posterior —investigar, excluir, conservar— es del análisis y
debe declararse.

Un atípico nunca se elimina «porque distorsiona el promedio». Si distorsiona el
promedio y es un dato real, el problema es el promedio, no el dato: use la mediana.

## Fórmulas matemáticas explicadas

```
Media:              x̄ = (1/n) · Σᵢ₌₁ⁿ xᵢ
Varianza muestral:  s² = Σ (xᵢ − x̄)² / (n − 1)
Desviación:         s  = √s²
Coef. de variación: CV = 100 · s / x̄                    [%]  (requiere x̄ ≠ 0 y x > 0)
Percentil lineal:   h = (n − 1) · q ;  P = x_⌊h⌋ + (h − ⌊h⌋)(x_⌈h⌉ − x_⌊h⌋)
IQR:                IQR = P75 − P25
Atípicos (Tukey):   x < P25 − k·IQR   o   x > P75 + k·IQR
Tasa ponderada:     r = 100 · Σaᵢ / Σbᵢ                  [%]
Promedio de tasas:  r̄ = (1/n) · Σ (100 · aᵢ / bᵢ)        [%]
Diferencia:         r − r̄                                [pp]
```

El **coeficiente de variación** permite comparar dispersión entre variables de
distinta unidad, porque es adimensional. No tiene sentido si la media está cerca de
cero o si la variable admite valores negativos.

## Significado de variables, símbolos y unidades

| Símbolo | Significado | Unidad |
| --- | --- | --- |
| `n` | Número de observaciones usables | observaciones |
| `xᵢ` | Valor de la observación *i* | unidad de la variable (min, personas) |
| `x̄` | Media aritmética | igual que `x` |
| `s` | Desviación estándar muestral | igual que `x` |
| `s²` | Varianza muestral | unidad de `x` al cuadrado |
| `CV` | Coeficiente de variación | % |
| `q` | Cuantil pedido | adimensional, en [0, 1] |
| `h` | Posición interpolada (base cero) | índice |
| `k` | Multiplicador del IQR | adimensional |
| `aᵢ`, `bᵢ` | Numerador y denominador de la unidad *i* | según el indicador |
| `pp` | Puntos porcentuales: diferencia entre dos porcentajes | pp |

## Ejemplos, de simple a complejo

### Ejemplo 1 — media y mediana sobre ocho valores

`x = [2, 4, 4, 4, 5, 5, 7, 9]`, `n = 8`.

```
Σx = 40            →  x̄ = 40/8 = 5
Σ(x − 5)² = 9+1+1+1+0+0+4+16 = 32
s² = 32/7 ≈ 4,571  →  s ≈ 2,138
Mediana: media de los dos centrales = (4 + 5)/2 = 4,5
```

La media supera a la mediana: hay asimetría a la derecha, producida por el 9.

### Ejemplo 2 — el mismo percentil, tres valores

`x = [1, 2, 3, 4]`, `q = 0,9`:

| Método | Resultado |
| --- | --- |
| linear | 3,7 |
| lower | 3 |
| higher | 4 |
| midpoint | 3,5 |

Con `n` grande las diferencias se diluyen; con `n` pequeño son del tamaño del efecto
que se busca medir.

### Ejemplo 3 — tasa ponderada y promedio simple

Dos establecimientos:

| Unidad | Asistidos | Programados | Tasa |
| --- | --- | --- | --- |
| A | 1 | 2 | 50,0 % |
| B | 90 | 100 | 90,0 % |

```
Ponderada:        100 · 91/102 = 89,2 %
Promedio simple:  (50 + 90)/2  = 70,0 %
Diferencia:       89,2 − 70,0  = 19,2 pp
```

La ponderada describe al conjunto de estudiantes; el promedio simple describe al
establecimiento típico. Informar «la asistencia es del 70 %» cuando 91 de 102 días se
asistió es una distorsión seria, aunque el cálculo esté bien hecho.

### Ejemplo 4 — asimetría y atípicos juntos

Duraciones `[38, 40, 41, 42, 43, 43, 44, 45, 120]`:

```
P25 = 40,5   P75 = 44,5   IQR = 4,0
Límite superior = 44,5 + 1,5 · 4 = 50,5   →  120 es atípico
Mediana = 43        Media ≈ 50,7
```

La media (50,7) es mayor que ocho de las nueve observaciones. Informar la media aquí
describe un viaje que no existe.

## Aplicaciones profesionales

- **Transporte.** El P90 de duración define el margen de la programación; la mediana
  describe el servicio habitual; la media sirve para calcular horas-vehículo totales,
  donde el total sí importa.
- **Salud.** Los tiempos de espera son fuertemente asimétricos: la mediana y el P90
  son los indicadores estándar, no la media.
- **Banca.** La distribución de montos de transacción tiene colas largas; un atípico
  puede ser fraude o un cliente corporativo. El criterio de Tukey marca candidatos a
  revisar, no culpables.
- **Manufactura.** El CV compara la estabilidad de dos procesos con unidades
  distintas.
- **Recursos humanos.** La mediana salarial es el indicador habitual precisamente por
  su robustez frente a las remuneraciones más altas.

## Código fuente comentado

```python
import pandas as pd

from lab.metrics import compare_rates, describe_numeric, outliers_iqr, percentile
from lab.viz import histogram
from solutions.reference import analyze

resultado = analyze(1)

# 1. Descripción completa de un indicador, con cobertura incluida. describe_numeric
#    informa filas, valores usables y cobertura antes de cualquier estadístico: una
#    media sin cobertura no se puede interpretar.
duracion = resultado["duracion"]["media_min"]
print(describe_numeric(duracion, unit="min").to_string(index=False))

# 2. El método del percentil se declara explícitamente. Con "lower" o "higher" el
#    resultado cambia, y la comparación con Excel exige saber cuál se usó.
for metodo in ("linear", "lower", "higher"):
    print(f"P90 ({metodo}) = {percentile(duracion, 0.90, metodo):.3f} min")

# 3. Media frente a mediana: si difieren mucho, la distribución es asimétrica y hay
#    que informar ambas.
media, mediana = duracion.mean(), percentile(duracion, 0.50)
print(f"media={media:.2f} mediana={mediana:.2f} diferencia={media - mediana:+.2f} min")

# 4. Atípicos con criterio reproducible. No se eliminan: se marcan y se cuentan.
marcados = outliers_iqr(duracion, k=1.5)
print(f"recorridos con duración atípica: {int(marcados.sum())} de {len(duracion)}")

# 5. Tasa ponderada frente a promedio simple, sobre el cumplimiento por operador.
op = resultado["cumplimiento_operador"]
comparacion = compare_rates(op["realizados"], op["viajes_programados"])
print(f"ponderada={comparacion.weighted:.2f}% simple={comparacion.simple:.2f}% "
      f"diferencia={comparacion.difference:+.2f} pp")

# 6. El histograma marca la mediana, no la media, porque con asimetría la mediana
#    describe mejor el caso típico.
histogram(duracion, "reference_outputs/duracion.png",
          title="Distribución de la duración media por recorrido",
          xlabel="Duración media (min)", bins=12, period="octubre 2026")
```

## Ejercicios prácticos

1. Para `data/case_2`, calcule media, mediana, P90 e IQR de la duración por recorrido.
   Indique si la distribución es simétrica y qué indicador informaría.
2. Calcule el P90 de la misma serie con los cinco métodos disponibles. Construya una
   tabla con los resultados y explique la dispersión entre ellos.
3. Reproduzca el P90 en Excel con `PERCENTIL.INC` y con `PERCENTIL.EXC`. ¿Cuál
   coincide con el método lineal de Python?
4. Marque los recorridos con duración atípica según Tukey con `k = 1,5` y `k = 3`.
   Para cada uno, decida y justifique si lo excluiría.
5. Calcule el cumplimiento global del caso 3 de las dos formas y exprese la diferencia
   en puntos porcentuales. Redacte en una frase cuál informaría a una jefatura.
6. El cumplimiento de un recorrido pasa de 80 % a 88 %. Escriba las dos formas
   correctas de comunicarlo y explique por qué «subió 8 %» es ambiguo.

## Soluciones explicadas

1. En los datos del laboratorio las duraciones se generan con una distribución normal
   alrededor de una meta por recorrido, de modo que media y mediana resultan próximas
   y la asimetría es leve. Con datos reales de transporte lo habitual es asimetría a
   la derecha: en ese caso se informa mediana y P90.

2. Los cinco métodos difieren más cuanto menor es `n`. Con nueve recorridos (caso 1)
   la diferencia entre `lower` y `higher` puede ser de varios minutos; con los 3 500
   viajes del caso 3 agregados por recorrido, sigue habiendo solo nueve valores, así
   que la diferencia persiste. Es un recordatorio: el `n` que importa es el de la serie
   que se resume, no el del archivo original.

3. `PERCENTIL.INC` corresponde al método lineal de NumPy —ambos usan `h = (n−1)·q`—.
   `PERCENTIL.EXC` usa `h = (n+1)·q − 1` y no está definido para `q` muy cerca de los
   extremos con `n` pequeño.

4. Con `k = 1,5` se marcan más recorridos que con `k = 3`. La decisión depende del
   origen: una duración de 300 minutos en un recorrido de 45 de meta es probablemente
   un error de registro (candidato a excluir, contando); una de 70 minutos es
   plausible y debe conservarse, aunque esté marcada.

5. Hay que dividir la suma de realizados por la suma de programados. La redacción:
   «El cumplimiento global de octubre fue de X % (realizados/programados agregados).
   El promedio de los cumplimientos diarios es Y %, Z pp distinto, porque los días con
   menos viajes programados pesan igual que los de mayor operación.»

6. Correcto: «subió 8 puntos porcentuales» o «subió 10 %» (`8/80`). «Subió 8 %» hace
   pensar en `80 × 1,08 = 86,4 %`, que no es el dato. Ver
   [[puntos-porcentuales-vs-porcentaje]].

## Errores frecuentes

- **Informar la media en distribuciones asimétricas** sin la mediana al lado.
- **Promediar porcentajes** cuando se quería la tasa del conjunto.
- **Comparar percentiles calculados con métodos distintos** y atribuir la diferencia a
  los datos.
- **Usar `ddof` distinto** en dos cálculos del mismo indicador (pandas usa 1, NumPy 0).
- **Eliminar atípicos para «mejorar» el promedio.** Si el atípico es real, el problema
  es la elección del estadístico.
- **Reportar un CV sobre una variable que puede ser negativa o con media cerca de
  cero**, donde el indicador no tiene sentido.
- **Omitir `n`.** Una media de 3 observaciones y una de 30 000 no merecen la misma
  confianza.

## Criterios de validación

1. Cada estadístico se informa con unidad y con `n`.
2. El método de percentil está declarado en el entregable.
3. Media y mediana se informan juntas cuando difieren de forma apreciable.
4. Las tasas declaran su numerador y su denominador.
5. Las diferencias de tasas se expresan en puntos porcentuales.
6. Los atípicos se marcan con criterio reproducible y su tratamiento está declarado.

## Preguntas de evaluación

1. ¿Por qué la varianza muestral divide por `n − 1`?
2. Una serie tiene media 52 y mediana 43. ¿Qué forma tiene la distribución y qué
   indicador informaría?
3. ¿Por qué el P90 de Excel puede diferir del de Python sobre los mismos datos?
4. ¿Qué significa que la mediana sea robusta y la media no?
5. Con 1 de 2 y 90 de 100, ¿cuánto vale la tasa ponderada y cuánto el promedio simple?
   ¿Cuál informaría y por qué?
6. ¿En qué caso un valor atípico es la observación más importante del conjunto?

## Referencias verificables

- Hyndman, R. J. y Fan, Y. «Sample Quantiles in Statistical Packages». *The American
  Statistician*, 50(4), 1996, pp. 361-365. doi:10.1080/00031305.1996.10473566
- Tukey, J. W. *Exploratory Data Analysis*. Addison-Wesley, 1977.
- NIST/SEMATECH. *e-Handbook of Statistical Methods*, sección 1 (EDA).
  <https://www.itl.nist.gov/div898/handbook/>
- Documentación de NumPy, `numpy.quantile` y sus métodos de interpolación.
  <https://numpy.org/doc/stable/reference/generated/numpy.quantile.html>
- Documentación de pandas, estadística descriptiva.
  <https://pandas.pydata.org/docs/user_guide/computation.html>
- Microsoft. «Función PERCENTIL.INC».
  <https://support.microsoft.com/es-es/office/percentil-inc-funci%C3%B3n-percentil-inc-680f9539-45eb-410b-9a5e-c1355e5fe2ed>

## Glosario técnico

| Término | Definición |
| --- | --- |
| Asimetría | Falta de simetría de la distribución respecto de su centro. |
| Atípico | Observación alejada del resto según un criterio declarado. |
| Coeficiente de variación | `s/x̄`, dispersión relativa adimensional. |
| Corrección de Bessel | Divisor `n − 1` que hace no sesgada la varianza muestral. |
| Cuantil | Valor que divide la distribución en proporciones dadas. |
| ddof | Grados de libertad que se restan al calcular la varianza. |
| IQR | Rango intercuartílico, `P75 − P25`. |
| Mediana | Valor central de la distribución ordenada. |
| Percentil | Cuantil expresado en porcentaje. |
| Puntos porcentuales | Unidad de la diferencia entre dos porcentajes. |
| Robustez | Insensibilidad de un estadístico a observaciones extremas. |
| Tasa ponderada | Cociente de sumas; tasa del conjunto. |
