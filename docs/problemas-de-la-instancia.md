# Qué problemas se pueden resolver con los datos de esta instancia

Inventario honesto: qué datos hay, qué pregunta se puede contestar con ellos, qué
tecnología hace falta, qué trampa enseña cada uno, y —la parte que suele faltar— **qué
no se puede contestar**.

Cada problema indica su estado: **resuelto** (hay código y resultado en el
repositorio), **resuelto en parte** (una mitad de la pregunta se contestó y la otra no
se puede, con la medición que lo demuestra), **disponible** (los datos alcanzan, falta
escribirlo) o **no se puede** (los datos no lo permiten, y se explica por qué).

---

## Los datos que hay, verificados

| Fuente | Qué contiene | Volumen | Licencia |
| --- | --- | --- | --- |
| **GTFS Red Movilidad** (DTPM) | 12 archivos: recorridos, paradas, expediciones, horarios, frecuencias, calendario, trazados, pasillos, niveles | 1 098 717 filas de horario, 26 137 expediciones, 18 486 lugares, 425 recorridos, 4 operadores | **no verificada** |
| **GTFS históricos** (DTPM) | Versiones por año | 2014 a 2026 | **no verificada** |
| **Lugares de carga bip!** (Subsecretaría de Transporte) | 5 archivos Excel: Metro, Puntos bip!, Centros alto estándar, Centros estándar, Retail | 1 927 locales abiertos + 1 cerrado | **CC BY-NC 2.0, verificada** |
| **Indicadores oficiales** (DIPRES, Partida 19) | Fórmulas, fuentes y reglas de exclusión del ICR, el ICF y el índice de tiempos de viaje | documento | pública |

### El desorden real de los Excel de bip!

Verificado archivo por archivo. Esto no es un dataset de práctica: es lo que publica
el organismo.

| Archivo | Hoja | Encabezado en fila | Filas útiles | Columnas |
| --- | --- | --- | --- | --- |
| Metro | `Abiertos` | **7** | 143 | 10 |
| Puntos bip! | `PCMA` | **9** | 1 579 | 9 — **sin horario** |
| Centros alto estándar | `Abiertos` | **13** | 7 | 9 — **sin nombre de fantasía** |
| Centros estándar | `Abierto` | **10** | 29 | 9 |
| Retail | `Abiertos` | **9** | 169 | 10 |
| Retail | **`Cerrados`** | **9** | 1 | 10 |

Nueve defectos, todos verificados:

1. El encabezado está en una **fila distinta en cada archivo**. `pd.read_excel` sin
   `header=` devuelve diez columnas `Unnamed: 0`…`Unnamed: 9`.
2. Los **esquemas no coinciden**: 9 o 10 columnas según el archivo.
3. Los **nombres de columna varían**: `NOMBRE FANTASIA` / `NOMBRE DE FANTASIA ` (con
   espacio al final) / ausente; `HORARIO REFERENCIAL` / `HORARIO` / ausente;
   `DIRECCION` / `DIRECCIÓN` (con tilde).
4. Los **nombres de hoja varían**: `Abiertos`, `Abierto`, `PCMA`.
5. Un archivo trae una **hoja `Cerrados`**. Consolidar todas las hojas sin mirar mete
   locales cerrados en un indicador de cobertura.
6. Hay **dos sistemas de coordenadas a la vez**: `ESTE`/`NORTE` (UTM) y
   `LONGITUD`/`LATITUD`.
7. La **entidad** viene con mayúsculas inconsistentes: `FULLCARGA` y `Fullcarga`.
8. La **comuna** viene en mayúsculas y sin tildes: `CONCHALI`, `ESTACION CENTRAL`.
9. Los **horarios son texto libre en tres formatos**: `Lunes a Viernes: …`,
   `Lun a Vie 07:00 …`, `Lun-Dom 08:00-21:00`. Y el archivo contiene el carácter `∙`,
   que rompe una consola de Windows en cp1252.

---

## Bloque 1 — Leer y consolidar fuentes heterogéneas

### P01. Consolidar los cinco archivos de lugares de carga en una sola tabla

**La pregunta.** ¿Cuántos lugares de carga hay, de qué tipo, y en qué comuna?

**Datos.** Los cinco Excel de bip!.

**Tecnología.** Pandas con `header=` detectado por archivo, o Power Query si se quiere
hacer en Excel. `openpyxl` para leer el `.xlsx`.

**Qué enseña.** Los nueve defectos de arriba. En particular: detectar la fila de
encabezado en lugar de fijarla a mano —porque en el próximo mes el organismo puede
mover el título una fila—, y renombrar a un esquema común declarando la
correspondencia, no adivinándola.

**La trampa que cuesta puntos.** Consolidar la hoja `Cerrados` junto con las
`Abiertos`. Son 1 de 1 928 filas: no mueve el total, pero el revisor que la busca
sabe si se mira el nombre de las hojas o no.

**Estado:** **resuelto** — [`cases/bip_lugares_carga`](../cases/bip_lugares_carga/README.md).
Incluye P02 (la clave), P03 (validación cruzada de coordenadas, que encontró tres
errores de hasta 10,3 km) y P04 (normalización).

### P02. ¿El código es una clave?

**La pregunta.** ¿`CODIGO` identifica un lugar de carga de forma única en el conjunto?

**Datos.** Los cinco Excel.

**Tecnología.** Pandas, `duplicated`, `nunique`.

**Qué enseña.** Que una columna llamada «código» no es una clave hasta que se mide. En
el archivo de Metro los códigos son `L1`, `L2`… (la **línea**, no el local), mientras
en los otros son numéricos. Al consolidar, el código **no** es único: hace falta una
clave compuesta, o una clave nueva con el origen del archivo.

**Estado:** disponible.

### P03. Validación cruzada de coordenadas: UTM contra latitud y longitud

**La pregunta.** ¿Las dos coordenadas de cada fila describen el mismo punto?

**Datos.** Los cinco Excel (columnas `ESTE`, `NORTE`, `LONGITUD`, `LATITUD`).

**Tecnología.** Conversión UTM 19S → WGS84. Sin dependencias se puede implementar la
fórmula inversa de Transverse Mercator; con `pyproj` es una línea. **La decisión y su
motivo son parte del entregable.**

**Qué enseña.** Validación independiente dentro del propio archivo: el dato trae dos
representaciones de la misma cosa, y compararlas detecta filas corruptas sin
necesidad de ninguna fuente externa. Es el mismo principio de la validación
Pandas ↔ SQL, aplicado a geometría.

**Estado:** **resuelto** como parte de
[`cases/correspondencia_metro`](../cases/correspondencia_metro/README.md), que lo
necesitaba para conciliar los dos inventarios. La validación interna de P01 se
amplía allí a cuatro detectores, cada uno con su punto ciego medido.

### P04. Normalizar comuna y entidad para poder agrupar

**La pregunta.** ¿Cuántos lugares de carga hay por comuna y por entidad?

**Datos.** Los cinco Excel.

**Tecnología.** Normalización de texto: mayúsculas, tildes, espacios dobles, espacios
al final.

**Qué enseña.** Que `FULLCARGA` y `Fullcarga` son dos grupos para `groupby` y uno para
una persona. Y que `CONCHALI` no cruza con `Conchalí` de ninguna otra fuente hasta que
ambas se normalizan con la **misma** regla, declarada.

**Estado:** disponible.

### P05. Interpretar horarios escritos en texto libre

**La pregunta.** ¿Cuántos lugares de carga atienden un domingo a las 20:00?

**Datos.** Los cuatro archivos que traen horario (Puntos bip! no lo trae).

**Tecnología.** Expresiones regulares sobre tres formatos distintos, más
`lab.dates.parse_hms_seconds` para las horas.

**Qué enseña.** Que un campo de texto libre no es un dato estructurado, y que la
cobertura del indicador cae por dos vías a la vez: los horarios que no se pueden
interpretar **y** los 1 579 registros que no tienen la columna. Hay que informar las
dos.

**Estado:** **resuelto** como parte de [`cases/carga_nocturna`](../cases/carga_nocturna/README.md), que lo necesitaba para contestar P09. El intérprete está en
[`lab/schedules.py`](../lab/schedules.py) y los diez formatos del archivo quedan fijados como prueba.

---

## Bloque 2 — Volumen y lectura selectiva

### P06. ¿Cuántas expediciones salen por hora en un día laboral?

**La pregunta.** Exactamente esa.

**Datos.** GTFS.

**Tecnología.** Lectura desde el ZIP sin descomprimir, `usecols` con 4 de 8 columnas
en la tabla de 1,1 millones de filas, expansión vectorizada con `Index.repeat`.

**Qué enseña.** Las cuatro trampas del GTFS: horarios que no son horas, relleno de
ceros irregular, expansión de frecuencias con borde exclusivo, y el defecto que no
existe. El atajo se equivoca en **−87,65 %**.

**Estado:** **resuelto** — [`cases/gtfs_red_movilidad`](../cases/gtfs_red_movilidad/README.md).

### P07. ¿Cuándo conviene dejar Pandas?

**La pregunta.** ¿A partir de qué volumen deja de servir leer todo en memoria, y qué
se gana midiendo en lugar de suponiendo?

**Datos.** GTFS (`stop_times.txt`, 51 MB sin comprimir) y los históricos.

**Tecnología.** Comparar tres caminos sobre la **misma** agregación: Pandas completo,
Pandas por bloques (`iter_zip_table`), y DuckDB sobre el CSV. Medir tiempo y memoria.

**Qué enseña.** Que la decisión de tecnología se **mide**, no se argumenta. Y que la
agregación por bloques solo sirve para estadísticos que se pueden calcular de forma
incremental: una suma sí, una mediana exacta no.

**Estado:** disponible.

---

## Bloque 3 — Cruces y análisis geográfico

### P08. ¿A qué distancia está el lugar de carga más cercano de cada parada?

**La pregunta.** ¿Qué proporción de las paradas tiene un lugar de carga de bip! a
menos de 300 metros? ¿Qué comunas quedan peor?

**Datos.** GTFS (12 497 paradas de embarque con coordenadas) + los cinco Excel de bip!
(1 927 locales abiertos).

**Tecnología.** Cruce por proximidad. Con 12 497 × 1 927 ≈ 24 millones de pares, la
fuerza bruta por bloques con NumPy resuelve en 1,4 s y no necesita índice espacial
(`scipy.spatial.cKDTree`, `GeoPandas.sjoin_nearest`); la decisión queda declarada para
revisarla si los conjuntos crecen. Distancias con haversine, no euclídea sobre grados.

**Qué enseña.** El cruce que **no tiene clave**: hay que inventar el criterio de
emparejamiento y declararlo. Y que la euclídea sobre grados no es una aproximación
sino un sesgo **con eje**: a la latitud de Santiago sobreestima la componente
este-oeste un 20 %, con cero subestimaciones en 12 497 paradas.

**El resultado.** 59,29 % de las paradas tiene un local a 300 m o menos **en línea
recta**; con un factor de rodeo de 1,3, el 46,02 %. La mediana es 249,6 m. Las cuatro
decisiones del criterio —fórmula, coordenada, rodeo y denominador— mueven la respuesta
plausible entre 39 % y 81 % sin que ningún dato cambie.

**Estado:** **resuelto en parte** —
[`cases/cobertura_de_carga`](../cases/cobertura_de_carga/README.md). La primera mitad
de la pregunta está contestada. La segunda, **no se puede**: las paradas del GTFS no
traen comuna, y atribuirle a cada parada la comuna de su local más cercano produce un
proxy sesgado por construcción, que falla exactamente donde la cobertura es peor. El
caso lo mide en lugar de afirmarlo y publica una rejilla geográfica como sustituto.

### P09. Cobertura de carga en el servicio nocturno

**La pregunta.** Donde hay servicio de buses entre las 00:00 y las 05:00, ¿hay dónde
cargar la tarjeta?

**Datos.** GTFS (367 251 llegadas nocturnas en 10 520 paradas, verificado) + los
horarios de los Excel de bip!, presentes en el 18,06 % de los locales.

**Tecnología.** Intérprete de horarios en texto libre (`lab.schedules`, escrito para
este caso) + proximidad de P08 + expansión de frecuencias de P06. El conteo de llegadas
se hace por **intersección de progresión aritmética con intervalo**, sin expandir las
142 366 salidas contra 1,1 millones de filas.

**Qué enseña.** Que un indicador de cobertura que cruza espacio y tiempo necesita
**tres respuestas y no dos**, y que cuando el denominador tiene huecos la respuesta
honesta es un **intervalo** cuyo ancho es otro indicador. Y la trampa: filtrar la hora
como texto da 12 201 paradas donde hay 10 520 —una sobreestimación del 16 %, lo
bastante pequeña para que nada parezca roto—, porque el 100 % de lo que toma el filtro
son desplazamientos relativos y no horas.

**El resultado.** **Cero** de las 10 520 paradas con servicio nocturno tiene un local
que declare abrir en esa ventana; ninguno de los 1 927 locales abiertos lo declara.
4 225 paradas (40,2 %) no tienen local alguno a 300 m, que es la conclusión más firme
porque no depende de ningún horario. Y 5 536 (52,6 %) quedan **indeterminadas**: la
cobertura nocturna está entre 0,0 % y 52,6 %.

**Estado:** **resuelto** —
[`cases/carga_nocturna`](../cases/carga_nocturna/README.md). Resuelve además P05, que
pedía interpretar los horarios escritos en texto libre: los diez formatos del archivo
se interpretan y quedan fijados como prueba.

### P10. Correspondencia entre buses y Metro

**La pregunta.** ¿Qué estaciones de Metro tienen paradas de bus a menos de 200 metros,
y cuántos servicios distintos las sirven?

**Datos.** GTFS (`route_type = 1` son las 7 líneas de Metro, `location_type = 1` sus
126 estaciones) + el archivo de Metro de bip! (143 filas con coordenadas).

**Tecnología.** Conciliación de inventarios con grano distinto, dos criterios de
emparejamiento independientes —nombre normalizado y proximidad— y auditoría de la
cobertura de los propios detectores de error.

**Qué enseña.** Que **toda comprobación de calidad tiene un punto ciego y el punto
ciego es medible**. La validación de coordenadas de P01 compara las dos
representaciones de cada fila y no puede ver un error que afecte a las dos por igual:
once estaciones están a más de 500 m de donde el GTFS las pone y ninguna quedó
marcada. Y que **tres de los cuatro detectores no necesitan ninguna fuente externa**:
el archivo podía delatar sus propios errores.

**El resultado.** Las **126** estaciones tienen al menos una parada de bus a 200 m —el
100 %—, con una mediana de **13 servicios** distintos y un máximo de 55 en Santa Lucía.
El grano cuadra con una identidad que hay que escribir: 126 − 17 combinaciones + 34
filas de desdoble = 143. Y la advertencia: calculada con las coordenadas de bip! en
lugar de las del GTFS, la respuesta cambia en **48 de 125 estaciones**.

**Estado:** **resuelto** —
[`cases/correspondencia_metro`](../cases/correspondencia_metro/README.md). Resuelve
además P03, que pedía la validación cruzada de coordenadas: la amplía de la validación
interna de P01 a cuatro detectores con su punto ciego declarado.

---

## Bloque 4 — Indicadores con la definición oficial

### P11. Construir el calendario de medición con las reglas de exclusión oficiales

**La pregunta.** Para un año dado, ¿qué días entran en la medición del índice de
tiempos de viaje según la metodología declarada?

**Datos.** Las reglas publicadas en el documento de DIPRES. Están enumeradas, y son
más de las que cualquiera supondría: solo días laborales, descartando feriados,
**todos** los días de enero, febrero y diciembre, dos semanas de vacaciones de
invierno, la semana de fiestas patrias, el 11 de septiembre, el día del joven
combatiente, y además los días 28 y 29 de cada mes porque algunos incidentes empiezan
la tarde anterior.

**Tecnología.** Construcción de calendario con Pandas, más una lista de feriados.

**Qué enseña.** Que el denominador de un indicador oficial es una **decisión
documentada**, no una propiedad de los datos. Y que reconstruirlo exige leer la nota al
pie, que es donde vive la metodología. Ver
[`indicadores-oficiales-transporte.md`](indicadores-oficiales-transporte.md).

**Estado:** **resuelto** — [`cases/calendario_medicion`](../cases/calendario_medicion/README.md).
De 261 días laborales quedan 164 elegibles y **78 medibles**. Y el hallazgo: cuatro de
las ocho reglas no cambian el denominador en 2026, tres de ellas en ningún año
analizado.

### P12. Implementar el ICF sobre la oferta programada

**La pregunta.** Con la definición oficial del índice de cumplimiento de frecuencia,
¿qué parte se puede calcular con el GTFS y qué parte no?

**Datos.** GTFS (`frequencies.txt`: la frecuencia **programada**).

**Tecnología.** Pandas.

**Qué enseña.** La diferencia entre **oferta programada** y **operación observada**. El
ICF oficial compara las mediciones por GPS contra el programa de operación: el GTFS
aporta el programa, no las mediciones. Se puede construir el denominador y la
estructura del indicador, y hay que **declarar que el numerador no es calculable** con
estos datos.

**Estado:** disponible, con el alcance limitado declarado.

### P13. Distribución de la frecuencia programada por servicio y período

**La pregunta.** ¿Qué servicios tienen los intervalos programados más largos en punta
mañana, y cómo se distribuyen los intervalos en toda la red?

**Datos.** GTFS (`frequencies.txt`, 14 520 ventanas; intervalos verificados entre 186 y
19 800 segundos, mediana 900).

**Tecnología.** Pandas, percentiles con método declarado, histograma.

**Qué enseña.** Estadística descriptiva sobre una distribución muy asimétrica: con
mínimo 3 minutos y máximo 5,5 horas, la media no describe a ningún servicio. Y la
ponderación importa: ¿el intervalo típico por servicio o por ventana de tiempo?

**Estado:** disponible.

---

## Bloque 5 — Series de tiempo sobre la red

### P14. ¿Cómo cambió la red entre dos versiones del feed?

**La pregunta.** Entre dos publicaciones del GTFS, ¿qué recorridos se crearon, se
eliminaron o cambiaron de trazado? ¿Qué paradas aparecieron y desaparecieron?

**Datos.** GTFS vigente + GTFS históricos (hay versiones desde 2014).

**Tecnología.** Comparación de conjuntos, cruce externo, y `lab.sources` para traer
cada versión con su procedencia.

**Qué enseña.** Comparar dos cargas del mismo sistema, que es el trabajo cotidiano de
un gestor de datos. Y el problema de identidad en el tiempo: si un `route_id` se
reutiliza para otro recorrido, la comparación por clave miente.

**Estado:** disponible.

### P15. Evolución de la oferta programada por año

**La pregunta.** ¿Cómo cambió el número de salidas programadas por hora en los últimos
años?

**Datos.** GTFS históricos, 2014 a 2026.

**Tecnología.** P06 aplicado a cada versión, más una serie temporal.

**Qué enseña.** Que comparar entre años exige que la **definición** sea idéntica en
todos: si una versión usa frecuencias donde otra usa horarios absolutos, la serie
compara dos cosas distintas. La comparabilidad se comprueba, no se supone.

**Estado:** disponible.

---

## Bloque 6 — Comunicación

### P16. Informe de una página para quien decide

**La pregunta.** Con el resultado de P06 y P08, ¿qué se le dice a quien tiene que
decidir dónde instalar el próximo centro de carga?

**Datos.** Los resultados de los problemas anteriores.

**Tecnología.** `lab.report` (secciones obligatorias y clasificación de afirmaciones),
`lab.viz` (gráficos con unidad, período y fuente).

**Qué enseña.** Que la recomendación tiene que ser proporcional a la evidencia. Con
oferta programada y ubicación de locales se puede decir dónde hay menos cobertura; no
se puede decir dónde hay más **necesidad**, porque eso exige demanda, y no la hay.

**Estado:** disponible.

---

## Lo que NO se puede contestar con estos datos

La parte más importante del inventario. Prometer cualquiera de estas sería inventar.

| Pregunta | Por qué no |
| --- | --- |
| ¿Cuántos pasajeros viajan? | **No hay datos de demanda.** Ninguna de las fuentes verificadas contiene transacciones de la tarjeta bip! ni subidas por parada. El GTFS describe la **oferta programada**. |
| ¿Se cumplió la frecuencia realmente? | **No hay datos de GPS.** El ICF y el ICR oficiales se calculan con mediciones del Centro de Monitoreo de Buses, que no son públicas. Solo se puede construir el lado programado. |
| ¿Cuánto demoró un viaje? | **No hay tiempos observados.** El GTFS da el horario programado, no el real. |
| ¿Cuántas validaciones hay por lugar de carga? | **No hay transacciones.** Los Excel dan ubicación y horario, no uso. |
| ¿Cuál es la cobertura territorial por superficie? | **No hay límites comunales.** La comuna viene como texto, de modo que se puede agrupar por comuna pero no calcular densidad por kilómetro cuadrado sin una capa geográfica que no está en estas fuentes. |
| ¿Qué comuna tiene peor cobertura de carga? | **Las paradas del GTFS no traen comuna.** El único proxy disponible es la comuna del local más cercano, sesgado por construcción: a la parada sin cobertura le asigna la comuna del local lejano. Medido en [P08](../cases/cobertura_de_carga/README.md): Paine recibe cinco paradas con una mediana de 18,9 km. El sustituto es una rejilla geográfica. |
| ¿Está abierto el local cuando pasa el pasajero? | **El horario está en el 18,06 % de los locales**, y el vacío está concentrado: cuatro archivos lo traen al 100 % y el quinto —con 1 579 de los 1 927 locales— al 0 %. Medido en [P09](../cases/carga_nocturna/README.md): la cobertura nocturna queda entre 0,0 % y 52,6 %, y completar 1 546 registros cerraría ese intervalo. |
| ¿Cuánto se camina de verdad hasta el local? | **No hay red peatonal.** Las distancias son en línea recta: no se consideran ríos, autopistas, cierres, pasarelas ni pendientes. P08 lo trata con un factor de rodeo declarado y su curva de sensibilidad, que es acotar la incertidumbre, no resolverla. |
| ¿Cómo evolucionó la satisfacción de usuarios? | **No hay encuestas** entre las fuentes verificadas. |
| ¿Qué pide la evaluación técnica del cargo? | **No se verificó.** Busqué el documento de la convocatoria en el sitio del DTPM, en el del ministerio, en el portal de datos abiertos y en buscadores, y no lo encontré. El sitio del DTPM no tiene sección de concursos. |

---

## Orden recomendado

Si el objetivo es prepararse para una evaluación de cuatro horas en Excel y Pandas, el
orden por rendimiento es:

1. **P01** (consolidar los cinco Excel) — **resuelto**: léalo y rehágalo sin mirar. Es
   el ejercicio más parecido a lo que se pide y concentra nueve defectos reales.
2. **P11** (calendario con reglas de exclusión oficiales) — **resuelto**: léalo. Es el
   que más se parece al trabajo real del cargo.
3. **P06** (ya resuelto: leerlo y rehacerlo) — volumen, fechas y el error del atajo.
4. **P04** y **P02** (normalización y claves) — rápidos, y aparecen siempre.
5. **P08** (proximidad) — **resuelto en parte**: léalo. Es el cruce sin clave, y el
   que mejor muestra cuánto del resultado lo pone el analista.
6. **P09** (cobertura nocturna) — **resuelto**: léalo al final. Es el más difícil de
   los resueltos y el único cuya respuesta es un intervalo en lugar de una cifra. Si
   en una evaluación le toca un indicador con datos faltantes, este es el patrón.
7. **P10** (conciliación de inventarios) — **resuelto**: léalo si el ejercicio incluye
   dos archivos que describen lo mismo. Enseña a nombrar el grano antes de cruzar, y a
   preguntarle a un control de calidad qué no mira.
8. **P16** (informe) — porque la interpretación se corrige aparte del cálculo.

El resto amplía, no prepara.
