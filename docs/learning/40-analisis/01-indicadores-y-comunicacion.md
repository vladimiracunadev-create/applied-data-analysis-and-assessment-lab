# Indicadores, visualización y comunicación de resultados

## Objetivos de aprendizaje

1. Definir un indicador de forma completa: fórmula, unidad, grano, denominador,
   período, cobertura y criterio de exclusión.
2. Construir gráficos que no distorsionen la magnitud ni dependan solo del color.
3. Redactar hallazgos distinguiendo hecho, evidencia, inferencia, interpretación e
   hipótesis.
4. Formular recomendaciones proporcionales a la evidencia disponible.
5. Entregar un informe con las secciones obligatorias del método del laboratorio.

## Prerrequisitos

Bloques de fundamentos y matemáticas. Clase `20-programacion/01` para el cálculo.

## Definiciones simples y formales

**Indicador.** *Simple:* un número que describe algo que importa. *Formal:* función de
los datos, con unidad y grano declarados, construida para apoyar una decisión
específica. Un número sin decisión asociada es una curiosidad, no un indicador.

**Métrica frente a indicador.** Una métrica mide; un indicador mide **y** tiene un
valor de referencia o una decisión asociada. «Duración media 52 min» es una métrica;
«duración media 52 min frente a meta 45 min» es un indicador.

**Grano del indicador.** El nivel al que está calculado: por viaje, por recorrido, por
operador, por día. El mismo nombre a distinto grano da números distintos.

**Denominador.** Lo que define sobre qué se calcula la razón. Es la parte del
indicador que más errores produce y la que menos se escribe.

**Escala honesta.** Representación en la que la razón entre las longitudes
gráficas es igual a la razón entre los valores. Truncar el eje de magnitudes la rompe.

**Proporcionalidad de la recomendación.** Correspondencia entre la fuerza de lo que se
recomienda y la fuerza de la evidencia que lo sostiene.

## Explicación conceptual

Un indicador mal definido no se arregla con una visualización mejor. El orden del
trabajo es: definir, calcular, verificar, mostrar, interpretar y recomendar; y la
definición es la parte difícil.

Definir un indicador exige responder siete preguntas, y el entregable debe contener
las siete respuestas:

| Pregunta | Ejemplo |
| --- | --- |
| ¿Qué mide? | Cumplimiento de la programación |
| ¿Con qué fórmula? | `100 · realizados / programados` |
| ¿A qué grano? | Recorrido × día |
| ¿Sobre qué denominador? | Viajes programados mayores que cero |
| ¿En qué unidad? | Porcentaje |
| ¿En qué período? | Octubre de 2026 |
| ¿Con qué cobertura y exclusiones? | 100 % de los días programados; se excluyen las claves desconocidas (3 viajes) |

Sin la séptima, el número no se puede auditar. Sin la cuarta, dos personas calculan
valores distintos y las dos creen tener razón.

La segunda mitad de la clase es sobre la comunicación, y el principio es uno: **la
fuerza de la afirmación no puede exceder la fuerza de la evidencia.** Un gráfico que
muestra que el operador A cumple menos que el B es evidencia de una brecha, no de una
causa. Escribir «el operador A incumple por falta de flota» cuando el dato no incluye
flota es inventar. Escribir «el operador A presenta una brecha de 7 pp; los datos no
incluyen flota disponible ni incidentes, de modo que la causa no puede establecerse
con esta información» es un hallazgo defendible, y además señala qué dato pedir.

## Desarrollo de fundamentos

### Qué hace honesto a un gráfico

| Elemento | Por qué |
| --- | --- |
| Título informativo | Dice qué se ve, no cómo se llama el gráfico |
| Eje rotulado con unidad | Un número sin unidad no se interpreta |
| Período | Un indicador sin período no es comparable |
| Fuente | Permite rastrear el dato |
| Eje de magnitudes desde cero | Mantiene la proporcionalidad visual |
| Orden intencionado | Descendente por valor, o cronológico; no alfabético por azar |
| Redundancia del color | Forma, posición o rótulo además del color |

El eje desde cero aplica a barras y áreas, donde la longitud **es** la codificación del
valor. En una serie temporal donde interesa la variación, un eje truncado puede ser
legítimo, pero entonces hay que declararlo en el título o en la nota. La regla no es
«nunca truncar»: es «nunca truncar en silencio».

La redundancia del color no es un detalle de accesibilidad opcional: alrededor del 8 %
de los hombres tiene alguna forma de daltonismo, y buena parte de los informes se
imprime en blanco y negro.

### Elegir la forma según la pregunta

| Pregunta | Forma |
| --- | --- |
| Comparar categorías | Barras, ordenadas por valor |
| Evolución en el tiempo | Línea |
| Distribución de una variable | Histograma o diagrama de caja |
| Relación entre dos variables | Dispersión |
| Composición de un total | Barras apiladas; evitar el gráfico circular con más de 3 partes |
| Un solo número relevante | Texto grande, no un gráfico |

El gráfico circular con muchas porciones obliga a comparar ángulos, que las personas
estiman peor que longitudes. Con dos o tres categorías es aceptable; con ocho, una
barra ordenada es siempre mejor.

### Estructura de un hallazgo

Un hallazgo bien escrito tiene cuatro partes en este orden:

1. **El dato**, con su magnitud y unidad.
2. **El contraste** que lo hace relevante (meta, período anterior, otra unidad).
3. **La clasificación**: hecho, evidencia, inferencia, interpretación o hipótesis.
4. **La limitación** que acota la lectura.

Ejemplo: «El recorrido R09 tiene una duración mediana de 64,9 minutos frente a una
meta de 67 (evidencia, n = 44 viajes). La puntualidad resultante es del 54,5 %. No hay
información de congestión ni de incidentes, de modo que no es posible determinar si la
diferencia es estructural o del período observado.»

Ver [[hecho-inferencia-hipotesis]].

### Proporcionalidad de la recomendación

| Evidencia disponible | Recomendación admisible |
| --- | --- |
| Un indicador descriptivo de un período | Observar, monitorear, pedir más datos |
| Patrón consistente en varios períodos | Priorizar revisión de los casos señalados |
| Diferencia con prueba estadística y tamaño de efecto | Proponer intervención acotada y medible |
| Diseño que permite inferencia causal | Proponer intervención con efecto esperado |

Saltarse un nivel es el error más frecuente de los informes técnicos, y el que más
daño hace a la credibilidad de quien los firma.

## Fórmulas matemáticas explicadas

```
Demanda           D = Σ pasajeros sobre viajes válidos                 [personas]
Cumplimiento      C = 100 · realizados / programados                   [%]
Puntualidad       P = 100 · puntuales / evaluados                      [%]
Duración media    T̄ = (1/n) Σ duraciónᵢ                                [min]
Percentil 90      T₉₀ = percentil(duración; 0,90)                      [min]
Cobertura         K = 100 · usados / objetivo                          [%]
Brecha            Δ = indicador_A − indicador_B                        [pp si son %]
Variación         V = 100 · (actual − anterior) / anterior             [%]
```

`Δ` y `V` responden preguntas distintas y se expresan en unidades distintas. Ver
[[puntos-porcentuales-vs-porcentaje]].

**Indicador compuesto de priorización.** Cuando hay que ordenar casos por varios
criterios:

```
Sᵣ = Σⱼ wⱼ · zⱼᵣ ,   con  zⱼᵣ = (xⱼᵣ − x̄ⱼ) / sⱼ   y   Σ wⱼ = 1
```

La estandarización `z` es necesaria porque los criterios tienen unidades distintas:
sumar minutos con porcentajes sin estandarizar hace que el criterio de mayor escala
numérica domine el resultado. Los pesos `wⱼ` son una decisión de política, no un
resultado técnico, y deben declararse como tal.

## Significado de variables, símbolos y unidades

| Símbolo | Significado | Unidad |
| --- | --- | --- |
| `D` | Demanda agregada | personas |
| `C`, `P`, `K` | Cumplimiento, puntualidad, cobertura | % |
| `T̄`, `T₉₀` | Duración media y percentil 90 | min |
| `n` | Observaciones usadas | viajes |
| `Δ` | Brecha entre dos indicadores | pp si son porcentajes |
| `V` | Variación relativa | % |
| `zⱼᵣ` | Valor estandarizado del criterio *j* en el caso *r* | adimensional |
| `wⱼ` | Peso del criterio *j*; decisión de política | adimensional, suma 1 |
| `sⱼ` | Desviación estándar del criterio *j* | unidad del criterio |

## Ejemplos, de simple a complejo

### Ejemplo 1 — definición completa de un indicador

> **Cumplimiento de la programación.** Porcentaje de viajes programados que se
> realizaron. Fórmula: `100 × realizados / programados`. Grano: recorrido × día.
> Denominador: viajes programados mayores que cero; los días con cero programados no
> generan indicador. Unidad: porcentaje, sin recorte a 100. Período: octubre de 2026.
> Exclusiones: 3 viajes con recorrido inexistente (0,09 % del total). Cobertura: 100 %
> de los pares recorrido-día de la programación.

### Ejemplo 2 — el mismo gráfico, honesto y engañoso

Cumplimiento por operador: 88,1 %, 90,3 % y 91,7 %.

Con el eje de 0 a 100, las tres barras se ven casi iguales: la conclusión visual es
«los tres operadores cumplen de forma similar», que es lo que dicen los datos.

Con el eje de 87 a 92, la primera barra se ve tres veces más corta que la tercera: la
conclusión visual es «un operador cumple mucho peor», que los datos no sostienen.

Las dos imágenes contienen los mismos números. La diferencia entre informar y
manipular está en el eje.

### Ejemplo 3 — hallazgo con su limitación

> **Hallazgo 2.** La demanda se concentra entre las 6 y las 9 horas, con 3 531
> pasajeros registrados frente a 2 100 en la banda de 9 a 12 (evidencia; cobertura del
> conteo: 99,8 %). *Limitación:* la demanda se asigna a la hora de **inicio del
> viaje**, no a la hora de validación de cada pasajero, de modo que la concentración
> real puede estar desplazada hasta la duración de un viaje.

### Ejemplo 4 — priorización declarada

Para ordenar los recorridos que requieren atención:

```python
criterios = {"cumplimiento_pct": -0.5, "duracion_p90": 0.3, "puntualidad_pct": -0.2}
```

Los signos expresan la dirección: un cumplimiento alto **reduce** la prioridad, un P90
alto la **aumenta**. Los pesos (0,5 / 0,3 / 0,2) son una decisión de política que debe
aparecer en el informe, no quedar escondida en el código. Cambiar los pesos cambia el
orden, y eso es legítimo siempre que sea visible.

## Aplicaciones profesionales

- **Transporte.** Tablero de cumplimiento, demanda y puntualidad por operador y
  recorrido, con las definiciones visibles en el propio tablero.
- **Salud.** Tiempos de espera por prestación, informados con mediana y P90 y no con
  media.
- **Banca.** Indicadores de mora con el denominador y la fecha de corte declarados; sin
  ellos, dos áreas reportan cifras distintas del mismo mes.
- **Administración pública.** Indicadores publicados: la cobertura y las exclusiones
  son parte del requisito de transparencia.
- **Emprendimiento.** Pocos indicadores bien definidos superan a un tablero con
  cuarenta métricas sin denominador.

## Código fuente comentado

```python
import pandas as pd

from lab.metrics import compare_rates, indicator_table, safe_ratio
from lab.report import case_report, table_markdown
from lab.viz import bar_chart, line_chart
from solutions.reference import analyze

resultado = analyze(1)
PERIODO = "octubre 2026 (datos sintéticos)"
FUENTE = "scripts/generate_data.py, semilla fija"

# 1. Tabla de indicadores: indicator_table obliga a declarar unidad y definición.
#    Un indicador sin ambas no es auditable.
op = resultado["cumplimiento_operador"]
comparacion = compare_rates(op["realizados"], op["viajes_programados"])
indicadores = indicator_table({
    "demanda_total": (resultado["demanda"]["pasajeros"].sum(), "personas",
                      "Suma de pasajeros en viajes realizados con conteo válido"),
    "cumplimiento_global": (comparacion.weighted, "%",
                            "100 × suma de realizados / suma de programados"),
    "cumplimiento_promedio_simple": (comparacion.simple, "%",
                                     "Promedio de los cumplimientos por operador"),
    "brecha_entre_ambos": (comparacion.difference, "pp",
                           "Ponderado menos promedio simple, en puntos porcentuales"),
    "duracion_mediana_max": (resultado["duracion"]["mediana_min"].max(), "min",
                             "Mayor duración mediana entre los recorridos"),
})
print(indicadores.to_string(index=False))

# 2. Gráficos con los cinco elementos obligatorios. bar_chart rechaza un gráfico sin
#    título o sin rótulo de magnitud: la validación es parte de la herramienta.
bar_chart(resultado["demanda"], "operador", "pasajeros",
          "reference_outputs/demanda_operador.png",
          title="Demanda de pasajeros por operador",
          ylabel="Pasajeros registrados (personas)",
          period=PERIODO, source=FUENTE)

line_chart(resultado["demanda_hora"], "hora", "pasajeros",
           "reference_outputs/demanda_hora.png",
           title="Demanda de pasajeros por hora de inicio del viaje",
           ylabel="Pasajeros registrados (personas)",
           xlabel="Hora de inicio (0–23)", period=PERIODO, source=FUENTE)

# 3. Informe con secciones obligatorias. to_markdown() se niega a exportar si falta
#    alguna: es preferible un error a un informe sin limitaciones.
informe = case_report("Indicadores operacionales — caso 1", author="Laboratorio")
(informe
 .add("contexto", "Cuatro archivos de operación de un sistema de transporte sintético.")
 .add("problema", "Informar demanda, duración y cumplimiento con exclusiones declaradas.")
 .add("objetivos", "Medir calidad, consolidar fuentes y calcular indicadores verificables.")
 .add("datos", "data/case_1; diccionario en docs/diccionario.md.")
 .add("metodologia", "Perfilado, conversión defensiva, cruce auditado y agregación por grano.")
 .add("supuestos", "Ver cases/transport/case.json, sección de supuestos.")
 .add_table("resultados", indicadores, intro="Indicadores con unidad y definición:")
 .add("validacion", "Recálculo independiente en SQL; diferencias nulas con τ = 1e-9.")
 .add("interpretacion", "La brecha de cumplimiento describe, no explica: falta flota e incidentes.")
 .add("limitaciones", "Datos sintéticos; la hora de inicio no es la hora de validación.")
 .add("conclusiones", "Los indicadores son reproducibles y están verificados por dos vías.")
 .add("reproducibilidad", "python solutions/reference.py 1 y python -m pytest."))

informe.claim("hecho", "El archivo tiene 454 filas y 4 duplicados exactos.",
              "Recuento directo sobre data/case_1/viajes.csv")
informe.claim("evidencia", f"El cumplimiento global es {comparacion.weighted:.1f} %.",
              "100 × suma de realizados / suma de programados")
informe.claim("inferencia", "La diferencia entre operadores no es atribuible al tamaño.",
              "Ambos indicadores se calculan sobre denominadores propios")
informe.claim("hipotesis", "La brecha podría relacionarse con disponibilidad de flota.",
              "No contrastable: el dataset no incluye flota")

print(informe.to_markdown()[:800])
```

## Ejercicios prácticos

1. Escriba la definición completa, con las siete preguntas respondidas, de la
   puntualidad del caso 2.
2. Construya el gráfico de cumplimiento por operador con eje desde cero y con eje
   truncado. Describa en una frase la conclusión que sugiere cada uno.
3. Redacte tres hallazgos del caso 3 con las cuatro partes de la estructura, y
   clasifique cada uno.
4. Para cada hallazgo del ejercicio anterior, escriba la recomendación más fuerte que
   la evidencia admite. Justifique por qué no se puede ir más allá.
5. Construya un índice de priorización con tres criterios estandarizados y pesos
   declarados. Muestre cómo cambia el orden al cambiar un peso.
6. Produzca el informe completo del caso 2 con `lab.report`. Quite una sección y
   compruebe qué ocurre al exportar.
7. Revise un gráfico de un informe público real y liste qué elementos obligatorios le
   faltan.

## Soluciones explicadas

1. «Porcentaje de viajes realizados cuya duración no supera la meta del recorrido.
   Fórmula: `100 × puntuales / evaluados`. Grano: recorrido. Denominador: viajes
   realizados con clave conocida y duración válida (`fin ≥ inicio`). Unidad:
   porcentaje. Período: octubre de 2026. Exclusiones y cobertura: se excluyen los
   cancelados, las claves desconocidas (2 viajes) y las duraciones inválidas;
   cobertura declarada por recorrido. **Advertencia:** esta definición es pedagógica y
   no corresponde al indicador oficial de ningún sistema de transporte.»

2. Con eje desde cero: «los tres operadores presentan cumplimientos similares». Con
   eje truncado: «hay una diferencia marcada entre operadores». El dato es el mismo;
   la segunda conclusión no está sostenida.

3. Cada hallazgo debe tener magnitud con unidad, contraste, clasificación y
   limitación. El error más común es omitir el contraste: «la duración media es 52
   minutos» no es un hallazgo hasta que se compara con algo.

4. Con un solo período descriptivo, la recomendación admisible es observar o pedir más
   datos. Proponer una intervención requiere al menos un patrón consistente, y
   estimar su efecto requiere un diseño que permita inferencia causal.

5. Al pasar el peso del cumplimiento de 0,5 a 0,2 y el del P90 de 0,3 a 0,6, el orden
   cambia: pasan al frente los recorridos lentos aunque cumplan bien. Esto demuestra
   que la priorización es una decisión de política expresada en números, y por eso los
   pesos van en el informe.

6. `to_markdown()` levanta `ValueError` nombrando las secciones faltantes. Con
   `allow_incomplete=True` exporta, pero añade un aviso visible de informe incompleto
   al inicio. Nunca produce un documento que parezca completo sin serlo.

7. Lo que falta con más frecuencia, en este orden: el período, la fuente y la
   cobertura. Es habitual encontrar gráficos con título y unidad pero sin período, lo
   que los hace no comparables con cualquier otra publicación.

## Errores frecuentes

- **Indicador sin denominador escrito.** Dos áreas reportan cifras distintas del mismo
  mes.
- **Eje truncado sin declararlo.**
- **Gráfico circular con muchas porciones**, que obliga a comparar ángulos.
- **Color como único portador de información.**
- **Promediar porcentajes** en la fila de totales.
- **Confundir pp con %** al informar una diferencia.
- **Recomendación desproporcionada**: proponer una intervención a partir de un
  descriptivo de un período.
- **Atribuir causa** a partir de una diferencia observada.
- **Omitir la cobertura** cuando es baja, que es justo cuando más importa.
- **Tablero con cuarenta métricas** y ninguna definición visible.

## Criterios de validación

1. Cada indicador responde las siete preguntas de la definición.
2. Cada gráfico lleva título, unidad, período, fuente y escala honesta.
3. Cada hallazgo está clasificado y acompañado de su limitación.
4. Las recomendaciones son proporcionales al nivel de evidencia.
5. Las diferencias entre porcentajes se expresan en puntos porcentuales.
6. El informe contiene las doce secciones obligatorias de `lab.report.CASE_SECTIONS`.
7. Los indicadores del informe coinciden con los del cálculo y con la validación
   independiente.

## Preguntas de evaluación

1. ¿Cuáles son las siete preguntas que definen un indicador?
2. ¿Por qué el eje de magnitudes de un gráfico de barras debe partir en cero?
3. Un informe dice «el cumplimiento subió 5 %». ¿Qué información falta para saber qué
   significa?
4. ¿Qué distingue una inferencia de una hipótesis en un hallazgo?
5. ¿Qué recomendación admite un indicador descriptivo de un solo período?
6. ¿Por qué hay que estandarizar los criterios de un índice de priorización?
7. ¿Por qué los pesos de un índice compuesto son una decisión de política y no un
   resultado técnico?

## Referencias verificables

- Tufte, E. R. *The Visual Display of Quantitative Information*, 2.ª edición, Graphics
  Press, 2001.
- Cleveland, W. S. y McGill, R. «Graphical Perception: Theory, Experimentation, and
  Application to the Development of Graphical Methods». *Journal of the American
  Statistical Association*, 79(387), 1984, pp. 531-554.
  doi:10.1080/01621459.1984.10478080
- Cairo, A. *How Charts Lie: Getting Smarter about Visual Information*. W. W. Norton,
  2019.
- Few, S. *Information Dashboard Design*, 2.ª edición, Analytics Press, 2013.
- Documentación de Matplotlib, guía de usuario.
  <https://matplotlib.org/stable/users/index.html>
- Web Content Accessibility Guidelines (WCAG) 2.2, criterio 1.4.1 «Use of Color».
  <https://www.w3.org/TR/WCAG22/#use-of-color>

## Glosario técnico

| Término | Definición |
| --- | --- |
| Cobertura | Proporción de la población objetivo incluida en el cálculo. |
| Denominador | Base sobre la que se calcula una razón. |
| Escala honesta | Proporcionalidad entre longitud gráfica y valor. |
| Grano del indicador | Nivel al que está calculado el indicador. |
| Indicador | Medición con unidad, grano y decisión asociada. |
| Métrica | Medición sin referencia ni decisión asociada. |
| Puntos porcentuales | Unidad de la diferencia entre dos porcentajes. |
| Proporcionalidad | Correspondencia entre fuerza de la recomendación y de la evidencia. |
| Redundancia del color | Codificar la información también sin color. |
| Estandarización z | `(x − x̄)/s`, para comparar criterios de distinta unidad. |
