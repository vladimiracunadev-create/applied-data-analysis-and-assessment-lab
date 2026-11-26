# Indicadores oficiales del transporte público de Santiago

Definiciones **oficiales**, con su fórmula, su grano, su fuente de datos y sus reglas
de exclusión, tomadas de documentos públicos de la Dirección de Presupuestos (DIPRES).

> **Procedencia.** Documento «VERSIÓN LEY AÑO 2019», Partida 19 — Ministerio de
> Transporte y Telecomunicaciones, Capítulo 01 — Secretaría y Administración General
> de Transportes. Descargado de `https://www.dipres.gob.cl/597/articles-188560_doc_pdf.pdf`
> el 26 de noviembre de 2026. Las citas entre comillas son textuales del documento.
>
> Documento complementario: «FORMULACIÓN DEL PROGRAMA DE MEJORAMIENTO DE LA GESTIÓN
> AÑO 2020», misma partida y capítulo, de
> `https://www.dipres.gob.cl/597/articles-211164_doc_pdf.pdf`.
>
> **Lo que estos documentos no son.** No son el instrumento de ninguna evaluación de
> selección de personal, y no se usaron para inferir su contenido. Son la metodología
> con la que el ministerio mide su propio desempeño, que es información útil para
> entender qué trabajo de datos se hace en esa organización.

---

## Por qué este documento importa

La diferencia entre un indicador de ejercicio y un indicador real está en las **notas
al pie**. La fórmula del índice de cumplimiento de regularidad ocupa dos líneas; sus
reglas de cálculo, media página. Y es en esa media página donde está el trabajo de un
gestor de datos: el grano, la fuente, qué se excluye, qué pasa en una catástrofe, quién
aprueba un cambio.

Lo que sigue es la estructura completa de tres indicadores oficiales, con sus notas.

---

## 1. Índice de cumplimiento de regularidad (ICR)

**Nombre oficial.** «Porcentaje de cumplimiento de regularidad en los servicios de
buses de transporte público de Santiago».

**Tipo.** Eficacia / Resultado final.

### Fórmula

```
         Número de mediciones a buses que presentan cumplimiento de la
         regularidad según lo establecido en el Programa de Operación en año t
ICR = ──────────────────────────────────────────────────────────────────────── × 100
         Número total de mediciones a buses efectuadas en el año t
```

Textual: «(Número de mediciones a buses de Transantiago que presentan cumplimiento de
la regularidad según lo establecido en el Programa de Operación en año t / Número total
de mediciones a buses de Transantiago efectuadas en el año t)*100».

**Unidad:** porcentaje. **El denominador son mediciones, no viajes ni buses.**

### Valores publicados

| Período | Valor |
| --- | --- |
| 2015 | 95,22 % |
| 2016 | 95,21 % |
| 2017 | 95,36 % |
| a junio de 2018 | 95,40 % |
| meta 2019 | 95,50 % |

### Grano y fuente

> «El cálculo es desarrollado en base a las mediciones por **servicio-sentido-mes** que
> son obtenidas desde las bases de datos generados en la gerencia de Control de la
> Operación, los cuales son obtenidos a su vez, de las mediciones vía GPS de todos los
> buses que prestan servicio en la ciudad.»

El grano es **servicio × sentido × mes**. No es por bus ni por viaje. Un analista que
agregue por servicio sin separar el sentido produce otro número.

### Qué mide el numerador

> «El numerador de este indicador guarda relación con aquellas mediciones que cumplen
> con la **regularidad de los intervalos de tiempos entre buses** en un servicio, los
> cuales están determinados en el Anexo 8 "Itinerarios" del programa de operación
> vigente y por el Contrato de Concesión de Uso de Vías vigente a la fecha.»

La definición del cumplimiento **no está en los datos**: está en un anexo contractual.
El indicador no se puede reproducir sin ese anexo.

### Para qué existe

> «El resultado de esta medición busca resguardar que los tiempos de espera de los
> usuarios no se vean afectados, dado a un aumento de los tiempos de pasada entre
> buses o a la impuntualidad de los servicios.»

Y tiene consecuencia económica directa:

> «se determina el nivel de cumplimiento del servicio y los **descuentos** que
> corresponden».

Un indicador que determina descuentos contractuales es un indicador que alguien va a
auditar. Esa es la razón de fondo por la que un gestor de datos del sector público
declara sus supuestos.

### El plan de referencia cambia dos veces al año

> «En la actualidad, el plan de operaciones se actualiza de manera oficial, dos veces
> al año. La medición del ICR se **ajusta respecto del plan de operaciones que se
> encuentre vigente**.»

Consecuencia: comparar el ICR de dos períodos compara el desempeño contra **planes
distintos**. La serie no es directamente comparable, y hay que decirlo.

### Qué pasa con los eventos excepcionales

Para eventos de impacto mayor, el contrato obliga a un procedimiento que «identifique
tales eventos y establezca un sistema para **corregir el cálculo** de los índices de
calidad y desempeño, con el fin de reducir el efecto de dichos eventos en sus
resultados».

Y para catástrofes:

> «no se usará el procedimiento a que se refiere este apartado, sino que se abordará la
> situación mediante un procedimiento que refleje en forma global las dificultades de
> operación, **relajando las exigencias normales de cálculo**».

Es decir: el indicador tiene un mecanismo formal de excepción. Un valor del ICR no se
interpreta sin saber si el período tuvo correcciones aplicadas.

---

## 2. Índice de cumplimiento de frecuencia (ICF)

**Nombre oficial.** «Porcentaje de cumplimiento de la frecuencia en los servicios de
buses de transporte público de Santiago».

### Fórmula

```
         Número de mediciones a buses que presentan cumplimiento de la
         frecuencia según lo establecido en el Programa de Operación en año t
ICF = ──────────────────────────────────────────────────────────────────────── × 100
         Número total de mediciones a buses efectuadas en el año t
```

### Valores publicados, con sus denominadores

Lo valioso aquí es que el documento publica **numerador y denominador**, no solo el
porcentaje:

| Período | Numerador | Denominador | Valor |
| --- | --- | --- | --- |
| 2015 | 22 886 640 | 24 034 568 | 95,22 % |
| 2016 | 22 786 585 | 23 932 141 | 95,21 % |
| 2017 | 22 331 975 | 23 418 844 | 95,36 % |
| a junio de 2018 | 10 981 445 | 11 511 049 | 95,40 % |
| meta 2019 | 21 487 500 | 22 500 000 | 95,50 % |

Son **más de veinte millones de mediciones al año**. Ese orden de magnitud explica por
qué el trabajo es de ingeniería de datos y no de planilla.

### Diferencia con el ICR

La fórmula es casi idéntica; lo que cambia es qué se considera cumplimiento:

| Índice | El numerador mide |
| --- | --- |
| **ICR** | «la regularidad de los **intervalos de tiempos entre buses** en un servicio» |
| **ICF** | «la **frecuencia de salida** entre buses de un servicio» |

> «la frecuencia de los servicios impacta directamente en la regularidad de pasada de
> los servicios»

Dos indicadores con el mismo denominador, el mismo grano y la misma fuente, que miden
cosas distintas y se nombran parecido. Confundirlos en un informe es el error típico.

---

## 3. Índice de variación de tiempos de viaje

**Nombre oficial.** «Índice de variación de tiempos de viaje de las personas en ejes de
la red vial básica de la ciudad de Santiago».

### Fórmula

```
        Segundos promedio ponderado de viaje de las personas en ejes viales
        de Santiago en periodo t
I = ──────────────────────────────────────────────────────────────────────── × 100
        Segundos promedio ponderado de viaje en ejes viales de Santiago
        en periodo t-1
```

Es un índice **año contra año**: un valor de 98 significa que el tiempo de viaje bajó
un 2 % respecto del año anterior. Valores publicados: 103 (2015), 101 (2016), 103
(2017), 100 (junio 2018), meta 101 (2019).

### Fuentes de datos, por modo

| Modo | Fuente | Cita |
| --- | --- | --- |
| Transporte público | GPS de buses | «La medición se realiza a través del Centro de Monitoreo de Buses (CMB) … el que mide de forma continua velocidades de los buses a partir de las emisiones GPS de los mismos en ejes relevantes» |
| Transporte privado | Waze + Traffic UOCT | «se realiza utilizando los datos obtenidos a través de **Waze** que son respaldados a través de un sistema desarrollado por UOCT llamado Traffic UOCT» |
| Ocupación de buses | supuesto declarado | «se define una **tasa de ocupación promedio** de buses, medida en cantidad de pasajeros por bus» |
| Ocupación de autos | encuesta de 2012 | «se utiliza el dato arrojado por la encuesta **Origen Destino de Viajes de Santiago del año 2012 - SECTRA**» |

**Dos cosas que vale la pena notar.** La primera: el indicador se construye con una
fuente privada (Waze). La segunda: la tasa de ocupación de autos de un indicador de
2019 viene de una encuesta de **2012**. Está declarado, que es lo correcto, y es
exactamente el tipo de supuesto que un informe honesto pone en su sección de
limitaciones.

### Las reglas de exclusión, completas

Esta es la parte que convierte el indicador en un ejercicio de gestión de datos. Todas
textuales:

> «Con el objetivo de homologar la metodología de cálculo empleada por **DTPM** con la
> utilizada por la **UOCT**, se consideran sólo días laborales, descartando los
> siguientes casos: Días feriados; **Todos los días de los meses de enero, febrero y
> diciembre**; Vacaciones de invierno (dos semanas, considerando los calendarios
> escolares); Semana de fiestas patrias; 11 de septiembre; Día del joven combatiente.
> Dado que en algunas ocasiones los incidentes inician en la tarde del día anterior,
> **se descartan todos los datos de los días 28 y 29**.»

Siete reglas de exclusión encadenadas. La última —descartar los días 28 y 29 porque los
incidentes empiezan la tarde anterior— es el tipo de decisión que nadie adivina: hay
que leerla.

### Períodos de medición

| Período | Horario |
| --- | --- |
| Punta mañana | 8:00 a 8:59 |
| Punta tarde 1 | 18:00 a 18:59 |
| Punta tarde 2 | 19:00 a 19:59 |

Con una homologación explícita:

> «en la punta tarde los tiempos y los flujos de los períodos 18:00 a 18:59 hrs. y
> 19:00 a 19:59 hrs., se **promedia** para hacerlos comparables a los del período punta
> mañana»

### Cómo se agrega

> «se calcula el tiempo de viaje promedio (en min/km) y el flujo que circula por cada
> uno de los ejes para los períodos definidos … Una vez obtenidos estos valores para
> buses y autos, el tiempo de viaje global **se pondera por su flujo**.»

Y la ponderación es triple:

> «se trata de valores promedios **ponderados por el volumen del flujo, la longitud del
> tramo y la tasa de ocupación** para cada uno de los modos de transportes considerados»

### Frecuencia y cobertura

- 17 ejes representativos, enumerados en el documento con sus tramos exactos.
- «Las mediciones se efectúan **trimestralmente**, en los meses de marzo, junio,
  septiembre y noviembre.»
- «El valor anual del tiempo de viaje corresponde al **promedio de los valores
  resultantes de las cuatro mediciones trimestrales**.»
- Y una limitación declarada: «Por limitaciones tecnológicas, no todos los ejes se
  pueden medir exactamente en el mismo tramo definido inicialmente por UOCT, por lo que
  se buscó el eje equivalente más similar en su ubicación.»

---

## Lo que esto enseña, en cinco puntos

1. **Un indicador oficial se define por su denominador y su grano, no por su nombre.**
   ICR e ICF comparten denominador, grano (servicio-sentido-mes) y fuente (GPS), y
   miden cosas distintas.

2. **El denominador es una decisión documentada.** Siete reglas de exclusión en el
   índice de tiempos de viaje, ninguna derivable de los datos. Están en las notas.

3. **Los supuestos se declaran, incluso los incómodos.** Una tasa de ocupación de 2012
   usada en un indicador de 2019, y una fuente privada para el transporte particular.
   Declararlo es lo correcto; omitirlo sería el defecto.

4. **La comparabilidad se verifica.** El ICR se mide contra un plan de operaciones que
   cambia dos veces al año, de modo que la serie no es directamente comparable entre
   períodos.

5. **Hay un mecanismo formal de excepción.** Catástrofes y eventos mayores permiten
   «relajar las exigencias normales de cálculo». Un valor sin saber si tuvo corrección
   aplicada no se interpreta.

Los cinco puntos son transferibles a cualquier indicador de cualquier sector: una tasa
de mora bancaria, un tiempo de espera hospitalario o un cumplimiento de SLA tienen
exactamente la misma estructura.

---

## Problemas del laboratorio que usan este documento

- **P11** — construir el calendario de medición con las siete reglas de exclusión.
- **P12** — implementar el ICF sobre la oferta programada del GTFS, declarando qué
  parte no es calculable sin las mediciones de GPS.

Ver [`problemas-de-la-instancia.md`](problemas-de-la-instancia.md).

---

## Advertencia sobre las cifras

Los valores publicados corresponden a los años indicados en el documento de 2019. No
son cifras actuales del sistema. El sistema se llamaba Transantiago en ese documento y
hoy opera como Red Metropolitana de Movilidad. Citar estas cifras como estado presente
del transporte público de Santiago sería incorrecto.
