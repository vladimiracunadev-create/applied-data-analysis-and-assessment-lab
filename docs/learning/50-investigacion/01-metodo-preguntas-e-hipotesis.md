# Método, preguntas, hipótesis y validez

## Objetivos de aprendizaje

1. Convertir una inquietud difusa en una pregunta de investigación respondible.
2. Formular hipótesis contrastables y declarar qué evidencia las refutaría.
3. Distinguir población, marco muestral y muestra, y reconocer los sesgos de cada
   paso.
4. Identificar las amenazas a la validez interna y externa de un estudio.
5. Diseñar una investigación reproducible y escribir su informe con las veinte
   secciones obligatorias.

## Prerrequisitos

Bloques de fundamentos y matemáticas. Clase `10-matematicas/01` para estadística
descriptiva. Es útil, no obligatorio, haber completado un caso aplicado.

## Definiciones simples y formales

**Pregunta de investigación.** *Simple:* lo que se quiere averiguar, escrito de modo
que se pueda saber si se averiguó. *Formal:* enunciado interrogativo que especifica
población, variables, relación esperada y ventana temporal, y cuya respuesta es
verificable con datos obtenibles.

**Hipótesis.** *Simple:* una respuesta provisional que se puede poner a prueba.
*Formal:* proposición sobre la relación entre variables, enunciada de modo que exista
evidencia capaz de contradecirla.

**Hipótesis nula (H₀).** La afirmación de ausencia de efecto o de diferencia. Es la
que se contrasta, no la que se cree.

**Población.** Conjunto completo de unidades sobre las que se quiere concluir.

**Marco muestral.** Lista concreta desde la que se selecciona. La diferencia entre
población y marco es la primera fuente de sesgo: se concluye sobre la población, pero
se observa solo el marco.

**Muestra.** Unidades efectivamente observadas.

**Validez interna.** Grado en que la conclusión sobre la relación estudiada es
correcta **dentro** del estudio.

**Validez externa.** Grado en que la conclusión se puede extender a otras poblaciones,
períodos o contextos.

**Confiabilidad.** Consistencia de la medición al repetirla.

**Sesgo.** Error sistemático, que no se reduce aumentando el tamaño de la muestra.

**Reproducibilidad.** Posibilidad de obtener el mismo resultado con los mismos datos y
el mismo código. **Replicabilidad** es lo más exigente: obtener la misma conclusión con
datos nuevos.

## Explicación conceptual

Toda investigación aplicada empieza con una inquietud mal formulada, y el primer
trabajo técnico es formularla bien. «¿Por qué el servicio funciona mal?» no es una
pregunta de investigación: no dice qué es «mal», sobre qué unidades, en qué período ni
con qué comparación.

Una pregunta respondible tiene cuatro componentes:

| Componente | Ejemplo |
| --- | --- |
| Población / unidades | Los 9 recorridos del sistema |
| Variables | Duración de viaje y cumplimiento de la programación |
| Relación esperada | ¿Los recorridos con mayor duración cumplen menos? |
| Ventana temporal | Octubre de 2026 |

Con los cuatro, la pregunta se puede responder o declarar no respondible con los datos
disponibles, que también es un resultado. Sin ellos, cualquier número parece una
respuesta.

El segundo punto, el más incómodo, es la **refutabilidad**. Una hipótesis que ningún
dato podría contradecir no es una hipótesis: es una creencia. Al formularla hay que
escribir, en la misma frase, qué observación la dejaría sin sostén. Esa frase es la
que impide, meses después, reinterpretar cualquier resultado como confirmación.

El tercer punto es que **el diseño manda sobre la técnica**. Ninguna prueba
estadística convierte un estudio observacional en causal. Si el diseño no permite
inferir causa, el informe no puede afirmarla, por sofisticado que sea el método. Ver
[[correlacion-no-es-causalidad]].

## Desarrollo de fundamentos

### Tipos de investigación y qué permite concluir cada uno

| Tipo | Pregunta típica | Permite concluir |
| --- | --- | --- |
| Exploratoria | ¿Qué hay aquí? | Patrones a investigar; nada definitivo |
| Descriptiva | ¿Cuánto, cuándo, dónde? | Magnitudes, con cobertura declarada |
| Correlacional | ¿Van juntas? | Asociación; **no** dirección ni causa |
| Explicativa / causal | ¿Por qué? | Causa, **si** el diseño lo sostiene |
| Experimental | ¿Qué pasa si intervengo? | Efecto causal del tratamiento |
| Documental | ¿Qué se sabe ya? | Estado del conocimiento, con referencias |

La mayoría de los estudios con datos operacionales es descriptiva o correlacional, y la
mayoría de los informes redacta como si fuera causal. Esa brecha entre lo que el
diseño permite y lo que el texto afirma es el defecto más común de la investigación
aplicada.

### De población a muestra: dónde entra el sesgo

```
Población  →  Marco muestral  →  Muestra seleccionada  →  Muestra observada
```

En cada flecha se pierde algo y el sesgo tiene nombre:

- **Población → marco:** sesgo de cobertura. El marco no incluye a toda la población
  (un registro de viajes solo tiene los viajes que el sistema registró).
- **Marco → seleccionada:** sesgo de selección. El criterio de selección se relaciona
  con la variable de interés.
- **Seleccionada → observada:** sesgo de no respuesta o de pérdida. Los que faltan no
  faltan al azar.

Aumentar el tamaño de la muestra reduce la **varianza**, no el **sesgo**. Un estudio
sesgado con un millón de observaciones da una respuesta muy precisa y equivocada.

### Amenazas a la validez

**Validez interna:**

- **Variable de confusión:** una tercera variable explica la relación observada.
- **Causalidad inversa:** el efecto supuesto es en realidad la causa.
- **Sesgo de selección:** las unidades comparadas difieren en algo relevante.
- **Error de medición:** el instrumento mide algo distinto de lo que se quería.
- **Regresión a la media:** los casos extremos se moderan solos, lo que puede
  confundirse con el efecto de una intervención.

**Validez externa:**

- **Período particular:** un mes atípico no representa el año.
- **Contexto particular:** lo que vale para un sistema no vale para otro.
- **Marco incompleto:** la muestra representa al marco, no a la población.

Declarar estas amenazas no debilita el informe: lo hace defendible. Un informe sin
sección de limitaciones es un informe cuyas limitaciones encontrará otra persona.

### Reproducibilidad: los cinco requisitos

1. **Datos** accesibles, o reproducibles con una semilla declarada.
2. **Código** versionado, que corre de principio a fin sin pasos manuales.
3. **Dependencias** fijadas, con versiones.
4. **Semillas** de cualquier proceso aleatorio.
5. **Decisiones** documentadas: qué se excluyó y por qué.

El quinto suele faltar, y es el que hace la diferencia. Dos personas con el mismo
código y los mismos datos obtienen resultados distintos si cada una excluyó registros
distintos.

## Fórmulas matemáticas explicadas

**Tamaño de muestra para estimar una media** con margen de error `E` y confianza
`1 − α`:

```
n = (z_{1−α/2} · σ / E)²
```

`σ` es la desviación poblacional, que no se conoce: se usa una estimación previa o un
estudio piloto. Con `σ = 12` min, `E = 2` min y 95 % de confianza:
`n = (1,96 · 12 / 2)² ≈ 138,3 → 139`.

**Tamaño de muestra para una proporción:**

```
n = z²_{1−α/2} · p(1 − p) / E²
```

`p(1 − p)` es máximo en `p = 0,5`, de modo que usar `p = 0,5` da el tamaño más
conservador. Con `E = 0,05` y 95 %: `n = 1,96² · 0,25 / 0,0025 ≈ 384,2 → 385`.

**Corrección para población finita**, cuando la muestra es una fracción apreciable de
la población:

```
n_ajustado = n / (1 + (n − 1)/N)
```

**Potencia estadística.** Probabilidad de detectar un efecto que existe:

```
potencia = 1 − β
```

donde `β` es la probabilidad de error de tipo II (no detectar un efecto real). Por
convención se busca potencia ≥ 0,80. Un estudio con potencia baja que no encuentra
efecto **no** ha demostrado que no haya efecto: no tenía capacidad de encontrarlo.

**Tamaño de efecto (d de Cohen):**

```
d = (x̄₁ − x̄₂) / s_agrupada
```

Interpretación convencional: 0,2 pequeño, 0,5 medio, 0,8 grande. Es una convención
sobre magnitudes, no una ley.

## Significado de variables, símbolos y unidades

| Símbolo | Significado | Unidad |
| --- | --- | --- |
| `N` | Tamaño de la población | unidades |
| `n` | Tamaño de la muestra | unidades |
| `σ` | Desviación estándar poblacional | unidad de la variable |
| `s` | Desviación estándar muestral | unidad de la variable |
| `E` | Margen de error admitido | unidad de la variable (o proporción) |
| `α` | Nivel de significancia; probabilidad de error de tipo I | adimensional |
| `β` | Probabilidad de error de tipo II | adimensional |
| `1 − β` | Potencia estadística | adimensional, objetivo ≥ 0,80 |
| `z_{1−α/2}` | Cuantil normal; 1,96 para 95 % | adimensional |
| `p` | Proporción poblacional supuesta | adimensional, en [0, 1] |
| `d` | Tamaño de efecto estandarizado | adimensional |

## Ejemplos, de simple a complejo

### Ejemplo 1 — de la inquietud a la pregunta

**Inquietud.** «El servicio de la mañana funciona mal.»

**Preguntas respondibles que se derivan:**

1. ¿Cuál es la duración mediana y el P90 de los viajes iniciados entre las 6 y las 9
   horas, frente a los iniciados entre las 9 y las 12, en octubre de 2026, por
   recorrido? *(descriptiva)*
2. ¿El cumplimiento de la programación en la banda de 6 a 9 difiere del de la banda de
   9 a 12? *(correlacional; con prueba de hipótesis)*
3. ¿La diferencia observada se explica por el recorrido o por la banda horaria?
   *(requiere control de confusión; límite de lo que estos datos permiten)*

La tercera muestra el borde: con el dataset disponible se puede estratificar por
recorrido, pero no controlar congestión, incidentes ni flota, de modo que la respuesta
será parcial y hay que decirlo.

### Ejemplo 2 — hipótesis con su condición de refutación

> **H₁.** Los recorridos con duración mediana superior a su meta presentan menor
> puntualidad que los que no la superan.
>
> **H₀.** No hay diferencia de puntualidad entre ambos grupos.
>
> **Refutación.** Si la puntualidad media de ambos grupos difiere en menos de 5 puntos
> porcentuales y el intervalo de confianza del 95 % de la diferencia incluye el cero,
> H₁ queda sin sostén en estos datos.
>
> **Advertencia de diseño.** La puntualidad se define como duración ≤ meta, de modo que
> está matemáticamente relacionada con la duración. La hipótesis es, en parte, una
> tautología. Un diseño honesto la reformularía con un indicador de puntualidad
> independiente de la duración, por ejemplo la desviación respecto del horario
> programado de cada salida.

Ese último párrafo es la parte más valiosa del ejemplo: detectar que las dos variables
no son independientes **antes** de hacer la prueba evita publicar un resultado vacío.

### Ejemplo 3 — tamaño de muestra y potencia

Se quiere detectar una diferencia de 3 minutos en la duración media entre dos
operadores, con `σ ≈ 12` minutos, `α = 0,05` y potencia 0,80. Para dos grupos de igual
tamaño:

```
n por grupo ≈ 2 · (z_{0,975} + z_{0,80})² · σ² / Δ²
            = 2 · (1,96 + 0,84)² · 144 / 9
            ≈ 251
```

Con 100 viajes por operador, el estudio no tendría potencia suficiente: si no encuentra
diferencia, no habrá demostrado que no la hay.

### Ejemplo 4 — investigación completa sobre los datos del laboratorio

**Pregunta.** ¿La duración media de los viajes difiere entre bandas horarias, por
recorrido, en el caso 3?

**Diseño.** Observacional, descriptivo-correlacional. Unidad: el viaje. Población: los
viajes del período. Marco: los viajes registrados. No hay muestreo: se observa el
marco completo, de modo que no hay error de muestreo, pero sí sesgo de cobertura si el
registro es incompleto.

**Método.** Estratificar por recorrido para controlar la confusión obvia (los
recorridos tienen metas distintas); comparar bandas con la prueba de Welch; reportar
tamaño de efecto e intervalo.

**Lo que no se podrá concluir.** Que la banda horaria *cause* la diferencia. Falta
información de congestión, demanda y flota, que varía con la hora y puede explicar
ambas cosas.

## Aplicaciones profesionales

- **Transporte.** Evaluar si un cambio de frecuencia modificó los tiempos de viaje
  exige un diseño antes-después con grupo de comparación; sin él, la variación puede
  ser estacional.
- **Salud pública.** La diferencia entre estudio observacional y ensayo controlado
  determina qué se puede afirmar sobre una intervención.
- **Banca.** Validar un modelo de riesgo exige muestra fuera de tiempo, no solo fuera
  de muestra: la validez externa temporal es el problema real.
- **Educación.** Comparar establecimientos sin ajustar por composición de la matrícula
  produce rankings que miden el contexto, no el efecto de la escuela.
- **Manufactura.** Un experimento factorial permite atribuir el efecto a cada factor;
  variar dos cosas a la vez sin diseño no lo permite.

## Código fuente comentado

```python
from datetime import date

import pandas as pd

from lab.dates import calendar_features
from lab.method import MethodRun
from lab.report import research_report, table_markdown
from lab.stats import mean_ci, results_frame, welch_t_test
from solutions.reference import analyze

# 1. La metodología se instrumenta: MethodRun exige evidencia para cerrar cada etapa,
#    de modo que no se puede declarar una etapa completada sin un archivo que la
#    respalde.
corrida = MethodRun(
    problem="¿La duración media difiere entre bandas horarias, por recorrido?",
    owner="Laboratorio",
    started=date(2026, 11, 26),
)
corrida.complete("recepcion", evidence="docs/learning/50-investigacion/01-...md")
corrida.complete("objetivos",
                 evidence="Pregunta con población, variables, relación y ventana",
                 decisions="Diseño observacional: no se afirmará causalidad")

# 2. Datos y estratificación. Se estratifica por recorrido porque las metas difieren:
#    comparar bandas sin estratificar confundiría banda con recorrido.
resultado = analyze(3)
duracion = resultado["duracion"]

# 3. Para la comparación por banda se necesita el detalle por viaje, no el agregado.
viajes = pd.read_csv("data/case_3/viajes.csv").drop_duplicates()
viajes = viajes.loc[viajes["estado"].eq("REALIZADO")].copy()
viajes["inicio"] = pd.to_datetime(viajes["inicio"], errors="coerce")
viajes["fin"] = pd.to_datetime(viajes["fin"], errors="coerce")
viajes["duracion_min"] = (viajes["fin"] - viajes["inicio"]).dt.total_seconds() / 60
viajes = viajes.loc[viajes["duracion_min"].ge(0)]
viajes = viajes.join(calendar_features(viajes["inicio"])[["banda"]])

# 4. Prueba por recorrido, no global: la comparación global mezclaría recorridos con
#    metas distintas y produciría una diferencia que refleja composición, no horario.
pruebas, estimaciones = [], []
for recorrido, grupo in viajes.groupby("recorrido_id"):
    punta = grupo.loc[grupo["banda"].eq("punta_manana"), "duracion_min"]
    valle = grupo.loc[grupo["banda"].eq("valle_tarde"), "duracion_min"]
    if len(punta) < 2 or len(valle) < 2:
        continue        # se declara, no se omite en silencio
    prueba = welch_t_test(punta, valle)
    pruebas.append(prueba)
    estimaciones.append({
        "recorrido": recorrido,
        "n_punta": len(punta), "n_valle": len(valle),
        "media_punta": mean_ci(punta).value,
        "media_valle": mean_ci(valle).value,
        "diferencia_min": mean_ci(punta).value - mean_ci(valle).value,
        "valor_p": prueba.p_value,
        "d_cohen": prueba.effect,
    })

tabla = pd.DataFrame(estimaciones)
print(tabla.to_string(index=False))
print(results_frame(pruebas).to_string(index=False))

# 5. El informe de investigación exige las 20 secciones: to_markdown() se niega a
#    exportar si falta alguna, incluidas sesgos, incertidumbre y limitaciones.
informe = research_report("Duración de viaje por banda horaria", author="Laboratorio",
                          report_date=date(2026, 11, 26),
                          disclaimer="Datos sintéticos. No describe ningún sistema real.")
print(f"secciones pendientes: {len(informe.missing())} de {len(informe.required)}")
```

## Ejercicios prácticos

1. Tome la inquietud «los operadores no cumplen» y escriba tres preguntas de
   investigación respondibles con sus cuatro componentes.
2. Formule una hipótesis para la segunda y escriba explícitamente qué observación la
   refutaría.
3. Identifique población, marco muestral y muestra en el caso 3, y nombre un sesgo
   plausible en cada transición.
4. Calcule el tamaño de muestra necesario para detectar una diferencia de 2 minutos
   con `σ = 12`, `α = 0,05` y potencia 0,80. Compare con los datos disponibles.
5. Liste tres amenazas a la validez interna y dos a la externa de la investigación del
   código comentado.
6. Complete una corrida de `MethodRun` para esa investigación. ¿Qué cobertura alcanza y
   qué etapas quedan pendientes?
7. Redacte las secciones de sesgos, incertidumbre y limitaciones del informe.
8. Explique por qué la hipótesis del ejemplo 2 es parcialmente tautológica y propóngale
   una reformulación.

## Soluciones explicadas

1. Por ejemplo: «¿Cuál fue el cumplimiento de la programación de cada operador en
   octubre de 2026, medido como realizados sobre programados por recorrido y día?»
   (descriptiva). «¿El cumplimiento difiere entre operadores más allá de la variación
   diaria esperada?» (correlacional con prueba). «¿La diferencia entre operadores
   persiste al estratificar por recorrido?» (control de confusión).

2. H₁: el cumplimiento del operador A difiere del del operador B. H₀: no difieren.
   Refutación: si el intervalo de confianza del 95 % de la diferencia incluye el cero y
   la diferencia puntual es menor que 2 pp, H₁ queda sin sostén.

3. Población: todos los viajes efectivamente realizados. Marco: los viajes
   **registrados** en el archivo; sesgo de cobertura si el registro falla
   sistemáticamente en alguna condición (por ejemplo, de noche). Muestra: el marco
   completo menos los excluidos por calidad; sesgo de pérdida si los excluidos se
   concentran en un operador o en una banda horaria. Comprobarlo es parte del análisis.

4. `n = (1,96 · 12 / 2)² ≈ 139` por grupo para estimar una media con ese margen; para
   **detectar** una diferencia de 2 minutos entre dos grupos con potencia 0,80 se
   necesitan unos 565 por grupo. El caso 3 tiene unos 3 500 viajes repartidos en 9
   recorridos y 6 bandas, de modo que por celda quedan unas decenas: potencia
   insuficiente para esa diferencia. La conclusión honesta es que el estudio no puede
   descartar un efecto de ese tamaño.

5. Internas: confusión por recorrido (metas distintas), confusión por día de la semana,
   error de medición en las marcas de tiempo. Externas: un solo período (octubre) y un
   sistema sintético que no representa ningún sistema real.

6. Una corrida completa cubre las 18 etapas. Si no se hizo revisión de antecedentes ni
   se incorporó el conocimiento a la base, la cobertura queda alrededor de 16/18 ≈
   88,9 %, y `pending()` nombra exactamente las dos que faltan.

7. Sesgos: cobertura del registro, pérdida por exclusiones de calidad, posible
   confusión por día de la semana. Incertidumbre: intervalos de confianza por
   recorrido, con la advertencia de que los viajes del mismo recorrido y día no son
   independientes, de modo que los intervalos son más estrechos de lo correcto.
   Limitaciones: datos sintéticos, período único, sin información de congestión,
   demanda ni flota.

8. Porque la puntualidad se define como `duración ≤ meta`: preguntar si los recorridos
   de mayor duración son menos puntuales es preguntar si los que superan el umbral lo
   superan. Reformulación: usar la desviación respecto del **horario programado de
   salida** como indicador de puntualidad, que es conceptualmente independiente de la
   duración del recorrido.

## Errores frecuentes

- **Pregunta sin población, variables, relación o ventana temporal.**
- **Hipótesis irrefutable**, que ninguna observación podría contradecir.
- **Hipótesis tautológica**, donde las dos variables están ligadas por definición.
- **Confundir población con marco muestral** y concluir sobre quien no se observó.
- **Creer que más datos corrigen el sesgo.** Reducen la varianza, no el sesgo.
- **Interpretar un resultado no significativo como ausencia de efecto**, sin reportar
  la potencia.
- **Afirmar causalidad desde un diseño observacional.**
- **Buscar en los datos hasta encontrar un `p < 0,05`** y reportar solo esa prueba.
- **Omitir las limitaciones** porque «debilitan» el informe.
- **No declarar la semilla** de un proceso aleatorio, haciendo irreproducible el
  resultado.

## Criterios de validación

1. La pregunta declara población, variables, relación y ventana temporal.
2. Cada hipótesis tiene su H₀ y su condición explícita de refutación.
3. Población, marco y muestra están distinguidos, con un sesgo nombrado por
   transición.
4. El tipo de diseño está declarado y el informe no afirma más de lo que permite.
5. Se reportan tamaño de efecto e incertidumbre, no solo el valor p.
6. Las amenazas a la validez interna y externa están enumeradas.
7. El informe contiene las veinte secciones de `lab.report.RESEARCH_SECTIONS`.
8. Los cinco requisitos de reproducibilidad están satisfechos, incluida la semilla y la
   lista de decisiones de exclusión.

## Preguntas de evaluación

1. ¿Qué cuatro componentes hacen respondible una pregunta de investigación?
2. ¿Por qué una hipótesis debe venir con su condición de refutación?
3. ¿Cuál es la diferencia entre población y marco muestral, y qué sesgo introduce la
   brecha?
4. ¿Por qué aumentar `n` no corrige el sesgo?
5. Un estudio no encuentra diferencia significativa. ¿Qué hay que reportar antes de
   concluir que no hay efecto?
6. ¿Qué distingue la validez interna de la externa? Dé una amenaza de cada una.
7. ¿Por qué la reproducibilidad exige documentar las decisiones de exclusión y no solo
   el código?
8. ¿En qué se diferencia reproducibilidad de replicabilidad?

## Referencias verificables

- Shadish, W. R., Cook, T. D. y Campbell, D. T. *Experimental and Quasi-Experimental
  Designs for Generalized Causal Inference*. Houghton Mifflin, 2002.
- Cohen, J. *Statistical Power Analysis for the Behavioral Sciences*, 2.ª edición,
  Lawrence Erlbaum, 1988.
- Wasserstein, R. L. y Lazar, N. A. «The ASA Statement on p-Values: Context, Process,
  and Purpose». *The American Statistician*, 70(2), 2016, pp. 129-133.
  doi:10.1080/00031305.2016.1154108
- Welch, B. L. «The Generalization of "Student's" Problem when Several Different
  Population Variances are Involved». *Biometrika*, 34(1-2), 1947, pp. 28-35.
  doi:10.1093/biomet/34.1-2.28
- Wilson, E. B. «Probable Inference, the Law of Succession, and Statistical Inference».
  *Journal of the American Statistical Association*, 22(158), 1927, pp. 209-212.
  doi:10.1080/01621459.1927.10502953
- Peng, R. D. «Reproducible Research in Computational Science». *Science*, 334(6060),
  2011, pp. 1226-1227. doi:10.1126/science.1213847
- NIST/SEMATECH. *e-Handbook of Statistical Methods*, capítulo sobre diseño de
  experimentos. <https://www.itl.nist.gov/div898/handbook/>

## Glosario técnico

| Término | Definición |
| --- | --- |
| Confusión | Tercera variable que explica la relación observada. |
| Error de tipo I (α) | Rechazar H₀ siendo cierta. |
| Error de tipo II (β) | No rechazar H₀ siendo falsa. |
| Hipótesis nula | Afirmación de ausencia de efecto que se contrasta. |
| Marco muestral | Lista concreta desde la que se selecciona la muestra. |
| Población | Conjunto completo sobre el que se quiere concluir. |
| Potencia | `1 − β`: capacidad de detectar un efecto existente. |
| Replicabilidad | Misma conclusión con datos nuevos. |
| Reproducibilidad | Mismo resultado con los mismos datos y código. |
| Sesgo | Error sistemático; no se reduce con más datos. |
| Tamaño de efecto | Magnitud estandarizada de la diferencia observada. |
| Validez externa | Grado de generalización a otros contextos. |
| Validez interna | Corrección de la conclusión dentro del estudio. |
