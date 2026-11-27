# P08 · Cruzar dos fuentes que no comparten ninguna clave

El cruce que no tiene `JOIN`. Dos archivos públicos describen cosas que están en el
mismo territorio y **no hay un solo campo que las relacione**. Hay que inventar el
criterio, y el criterio resulta ser la mitad de la respuesta.

Metadatos: [`case.json`](case.json) · Umbral:
[manual de paradas del DTPM](#de-dónde-sale-el-umbral-de-300-metros) · Reutiliza
[P01](../bip_lugares_carga/README.md)

---

## 1. El problema, en palabras

Para pagar un viaje en la Red Metropolitana de Movilidad hay que llevar saldo en la
tarjeta bip!, y el saldo se carga en locales físicos. El organismo publica las dos
cosas por separado:

- **dónde están las paradas**, en el feed GTFS: 12 497 paradas de embarque;
- **dónde están los locales de carga**, en cinco planillas Excel: 1 927 abiertos.

La pregunta: **¿a qué distancia está el lugar de carga más cercano de cada parada, y
qué proporción de las paradas lo tiene a una distancia caminable?**

Y aquí está lo que hace interesante el caso. En los otros problemas del laboratorio
hay una clave: un `trip_id`, un `código`, una fecha. Aquí **no hay ninguna**. Las
paradas no traen comuna, no traen dirección, no traen ningún identificador que
aparezca también en los Excel. Lo único que comparten las dos fuentes es estar en el
mismo territorio.

Eso significa que el criterio de emparejamiento no viene dado: **hay que construirlo**.
Y al construirlo aparecen cuatro decisiones que nadie declara y que mueven la
respuesta entre el 39 % y el 81 %.

---

## 2. Descomposición

| # | Subproblema | Por qué no es trivial |
| --- | --- | --- |
| 1 | Cuántas paradas hay | `stops.txt` trae 18 486 filas y no 18 486 paradas |
| 2 | Qué fórmula de distancia | La euclídea sobre grados tiene un sesgo con eje |
| 3 | Qué coordenada de los Excel | Traen dos y no coinciden (hallazgo de P01) |
| 4 | Cómo devolver el local más cercano | El `código` no es único |
| 5 | Línea recta o caminata | Nadie camina en línea recta, y no hay red peatonal |
| 6 | Qué paradas entran al denominador | El feed cubre más territorio que los Excel |
| 7 | Qué zonas quedan peor | Las paradas no traen comuna |

Los subproblemas 1, 3 y 4 son herencia directa de los otros dos casos del
laboratorio. Que reaparezcan no es casualidad: son las tres formas en que una fuente
pública contradice lo que uno supone de ella.

---

## 3. De dónde salen los datos

| Fuente | Qué aporta | Licencia |
| --- | --- | --- |
| [Feed GTFS del DTPM](https://www.dtpm.cl/index.php/gtfs-vigente) | 12 497 paradas con coordenadas | **NO VERIFICADA** |
| Cinco datasets bip! en [datos.gob.cl](https://datos.gob.cl/) | 1 927 locales abiertos | CC BY-NC 2.0, verificada |
| [Manual de paradas del DTPM](https://www.dtpm.cl/descargas/manuales/Manual%20de%20paradas%20DTPM%20(06-03-26)%20alta.pdf) | El umbral de 300 m | No verificada |

Ninguna de las tres se versiona en este repositorio. Lo que se versiona es el código,
el registro de procedencia con su SHA-256 y las catorce tablas de resultado.

### Las 18 486 filas que no son 18 486 paradas

```
location_type              significado  filas  con_coordenada entra
            0           parada o andén  12497           12497    sí
            1                 estación    126             126    no
            2          acceso o salida    298             298    no
            3 nodo generico de pasillo   5031               0    no
            4         área de abordaje    534               0    no
```

De las 18 486 filas, **12 497 son lugares donde sube gente**. Las otras 5 989 son
estaciones, accesos, nodos de pasillo y áreas de abordaje. Y 5 565 de ellas **no
traen coordenadas**, porque la especificación GTFS solo las exige para los tipos 0, 1
y 2. No es un defecto del feed: es la jerarquía de la especificación.

Si se cuentan todas las filas como paradas, aparecen 5 565 «paradas sin cobertura»
que no son paradas y que ni siquiera tienen posición. El denominador queda inflado un
48 % y el error se ve plausible.

### De dónde sale el umbral de 300 metros

El manual de diseño de paradas del DTPM, de febrero de 2026, dice textualmente:

> «La ubicación de un punto de parada responde a múltiples parámetros donde el
> distanciamiento entre puntos de parada promedio es de 300 m, que considera un tiempo
> de caminata de 3 a 5 minutos aproximadamente.»
>
> — DTPM, *Puntos de Parada: Manual de Diseño*, febrero de 2026, p. 36

Esa es la distancia que el propio organismo asocia a una caminata de 3 a 5 minutos.
Pero conviene leer qué dice exactamente: habla del **espaciamiento entre paradas**. El
manual **no fija ningún criterio de distancia a un lugar de carga** y no menciona la
carga de la tarjeta en ninguna de sus páginas.

Trasladar los 300 m de un contexto al otro es una **analogía**, no la aplicación de
una norma. Por eso la cita está en el código (`CITA_UMBRAL`) y por eso el caso informa
la cobertura a seis umbrales en lugar de uno.

---

## 4. Qué tecnología se usa y por qué

| Decisión | Alternativa descartada | Motivo |
| --- | --- | --- |
| `lab.geo.nearest_point`, fuerza bruta por bloques con NumPy | `scipy.spatial.cKDTree` | 24 081 719 pares en **1,4 s**. Añadir SciPy para ahorrar un segundo no se justifica. Y un KD-tree sobre grados mide mal: habría que proyectar primero |
| Haversine | Euclídea sobre grados | Es la decisión número 2, y se mide más abajo |
| Rejilla de grados | Capa de comunas + GeoPandas | No hay capa disponible con licencia verificada, y el cruce con polígonos exige una dependencia nueva |
| Reutilizar `cases.bip_lugares_carga` | Volver a leer los cinco Excel | La consolidación ya está resuelta y probada. Un caso que depende de otro es deliberado |

Sobre el tamaño: la fuerza bruta es `O(n·m)`. Con estos conjuntos es la opción
correcta. Si cualquiera de los dos creciera un orden de magnitud, la decisión cambia
—y queda declarada en el docstring para que se revise entonces, y no cuando el proceso
no termine.

---

## 5. La resolución, decisión por decisión

### 5.1 La fórmula: un sesgo con eje

El atajo habitual es tratar las coordenadas como un plano: calcular la distancia
euclídea entre pares de grados y multiplicar por los 111,32 km que mide un grado de
meridiano. Es rápido, es una línea, y está mal de una forma concreta.

A la latitud de Santiago (−33,45°) un grado de latitud mide 111,2 km y uno de longitud
**92,8 km**. La razón es 1,199. De modo que el atajo estira la componente este-oeste
un 20 %.

La prueba lo fija a mano:

| Parada | Distancia real | Euclídea sobre grados |
| --- | --- | --- |
| 1 km al **este** | 1 000 m | **1 200 m** |
| 1 km al **norte** | 1 000 m | 1 001 m |

Que el error tenga **eje** —y no magnitud aleatoria— es lo que lo convierte en un
sesgo. Un error con eje no se cancela al promediar.

Sobre las 12 497 paradas reales:

```
        error_mediano_m    17.20   m
      error_mediano_pct     9.41   %
      errores_negativos        0   paradas
cobertura_haversine_pct    59.29   %
 cobertura_euclidea_pct    54.69   %
       cambian_de_clase      574   paradas
       cambian_de_lugar      814   paradas
```

**Cero subestimaciones en 12 497 paradas.** Si el error fuera ruido habría errores de
los dos signos; que todos vayan en la misma dirección confirma que es sistemático.

Y hay algo que importa más que el error mediano: **17 metros suenan a nada, 574
paradas que cambian de clase no**. El error de un método no se mide en la unidad del
cálculo sino en la unidad de la decisión.

### 5.2 La coordenada: dos respuestas distintas, ninguna verificable

P01 encontró que los Excel traen la misma ubicación dos veces —en UTM y en
latitud/longitud— y que no coinciden: hay un desvío sistemático de unos 61 m, más tres
locales con una contradicción de kilómetros. Aquí se mide la **consecuencia** de esa
ambigüedad:

```
cobertura_publicada_pct   59.29   %
cobertura_desde_utm_pct   59.17   %
       cambian_de_clase     707   paradas
       cambian_de_lugar    1673   paradas
   diferencia_mediana_m   35.70   m
    diferencia_maxima_m   825.9   m
```

Esta tabla dice dos cosas opuestas a la vez, y las dos son útiles:

- **el indicador agregado es robusto**: 59,29 % contra 59,17 %, una diferencia de 0,12
  puntos que no cambia ninguna conclusión;
- **la respuesta por parada no lo es**: 1 673 paradas —el 13 %— tienen otro local como
  el más cercano según cuál de las dos coordenadas se use.

Y eso decide **para qué sirve el resultado**. Publicar la cobertura de la red, sí.
Decirle a una persona a qué local caminar, no: para eso hay que resolver primero cuál
de las dos coordenadas del archivo es la correcta, y el archivo no lo dice.

### 5.3 El identificador: la clave que no es clave, otra vez

P01 ya había establecido que el `código` de los Excel no identifica un local. Aquí ese
hallazgo dejó de ser una observación y se convirtió en un error:

```
               tipo_local  filas  codigos_distintos  codigos_repetidos  llave
        Estación de Metro    143                  7                136     no
               Punto bip!   1579               1579                  0     sí
                   Retail    169                169                  0     sí
                    TOTAL   1927               1791                136     no
```

En las estaciones de Metro el código es **la línea** (`L1`, `L5`), no la estación. 143
estaciones comparten siete códigos.

La primera versión de este caso pedía a `nearest_point` que devolviera el `código` del
local más cercano. El resultado fue:

1. `pandas` levantó `InvalidIndexError` al intentar unir el resultado con la tabla de
   locales, porque el índice no era único. Ese error, al menos, es ruidoso.
2. Peor: la comparación entre métodos **subestimó en silencio**. Contando por código,
   814 paradas que cambian de local aparecían como 807, y 1 673 aparecían como 1 657.
   Dos estaciones distintas de la misma línea se contaban como la misma.

> Una clave que no es única no falla al cruzar. Falla **al volver**. Y cuando falla al
> volver, a veces no falla: devuelve un número un poco menor.

El caso devuelve la **posición de fila**, y hay una prueba con dos locales que
comparten código para que no pueda volver a pasar.

### 5.4 La caminata: el supuesto que mueve el titular

Nadie camina en línea recta. La forma estándar de corregirlo sin una red de calles es
un **factor de rodeo**: la razón entre el recorrido real y la línea recta.

No se adopta un valor. Se buscó, y los valores publicados varían por ciudad y por
método de medición; no hay una cifra peatonal canónica que se pueda citar. De modo que
el caso informa la curva:

```
 factor_rodeo  cobertura_pct  puntos_vs_linea_recta
          1.0          59.29                   0.00
          1.2          50.06                  -9.23
          1.3          46.02                 -13.27
          1.4          42.33                 -16.96
          1.5          39.60                 -19.68
```

**El titular cambia de signo dentro de este rango.** «Seis de cada diez paradas tienen
dónde cargar a tres minutos caminando» y «menos de la mitad lo tiene» son la misma
medición con dos supuestos distintos, ambos defendibles. Y ninguno de los dos aparece
en el número si no se declara.

El 1,0 está en la tabla porque es un **piso**, no una estimación: la cobertura real no
puede ser mejor que eso.

### 5.5 El denominador: el feed cubre más territorio que los Excel

```
stop_id                  stop_name       metros
 PT0228          Estación Rancagua      40305.3
 PT0227          Estación Graneros      28670.5
 PT0226     Estación San Francisco      18924.7
 PT0225          Estación Hospital       6716.4
  PJ839  Colegio A. Merino Benítez       5208.0
```

La Estación Rancagua está a 40,3 km del lugar de carga más cercano. No es una falla de
cobertura: el feed incluye el servicio de tren a Rancagua, y los Excel describen el
área metropolitana. También aparecen los niveles del aeropuerto —un terminal aéreo no
es un barrio— y caminos industriales de Lampa y Noviciado.

61 paradas superan los 3 km. Se informan las dos cifras:

```
              denominador  paradas  cubiertas  cobertura_pct
     denominador completo    12497       7409          59.29
sin paradas a más de 3 km    12436       7409          59.58
```

Aquí la exclusión resulta **casi inocua**: 0,29 puntos. Y eso también es un resultado.
Mostrar que una decisión del denominador no cambia nada vale tanto como mostrar que
sí; la diferencia es que ahora se sabe, en lugar de suponerlo. Las 61 paradas se
listan una por una en `fuera_de_alcance.csv`: excluirlas es una decisión de quien lee
el indicador, no del cálculo.

### 5.6 Las zonas: cuando lo honesto es cambiar la pregunta

La segunda mitad de P08 preguntaba **qué comunas quedan peor**. No se puede contestar
con estos datos, y el caso lo demuestra en lugar de afirmarlo.

Las paradas del GTFS no traen comuna. La única comuna disponible es la del local más
cercano, y ese proxy está sesgado por construcción: **a la parada sin cobertura le
asigna la comuna del local lejano**, que es precisamente la comuna equivocada. El
sesgo es peor donde el indicador sería más interesante.

```
comuna_del_lugar_cercano  paradas_atribuidas  mediana_m  cobertura_pct  artefacto
                    Buin                   3     2480.9            0.0   probable
         Calera de Tango                   4     2564.7            0.0   probable
                   Paine                   5    18924.7            0.0   probable
           Padre Hurtado                  47      540.8           23.4         no
```

Paine recibe cinco paradas con una mediana de **18,9 km**. Paine no tiene mala
cobertura: tiene un local que quedó siendo el más cercano de unas paradas que están a
diecinueve kilómetros. Las tres primeras filas no miden comunas, miden el sesgo del
proxy. De 46 comunas con locales, solo 39 reciben paradas atribuidas.

El sustituto es una **rejilla de 0,01° de lado**, derivada de las propias coordenadas:

```
 celda_lat  celda_lon  paradas  mediana_m                      parada_mas_lejana  cob_pct
    -33.62     -70.57       20      745.6   Av. Circunvalación / esq. Nonato Coo      0.0
    -33.62     -70.70       29      663.8    Los Suspiros / esq. Avenida Central      0.0
    -33.51     -70.67       24      643.8   Av. J. J. Prieto Vial / esq. Vecinal      0.0
    -33.59     -70.62       21      413.5    Avenida Juanita / esq. Miguel Angel      0.0
```

Cuatro celdas con veinte o más paradas y **cero** cobertura a 300 m. Se nombra la
parada más lejana de cada celda para que la zona se reconozca sin un mapa. Las celdas
con menos de 20 paradas no entran: con tres paradas el porcentaje es 0 % o 100 % y no
informa de nada.

La rejilla tiene un costo que hay que declarar: **una celda no es una unidad con la que
nadie gobierne**. Localiza zonas, no asigna responsabilidades. Y no es cuadrada —1,11
km de norte a sur, 0,93 de este a oeste—, de modo que no sirve para medir superficies
ni densidades.

### 5.7 El límite que ningún supuesto arregla

Toda cifra de este caso supone que el local **está abierto** cuando pasa el pasajero.
Los datos no lo respaldan:

```
         paradas_medidas    12497   paradas
    con_horario_conocido     2787   paradas
con_horario_conocido_pct    22.30   %
   cubiertas_con_horario     1708   paradas
   cubiertas_sin_horario     5701   paradas
```

De las 7 409 paradas «cubiertas», **5 701 lo están por un local cuyo horario se
desconoce**. P01 ya había medido que el `horario referencial` está en el 18,06 % de los
locales; aquí se ve la consecuencia. Y no es un detalle menor: el retail es el tipo de
local con peor mediana (289,8 m) y el que más depende del horario comercial.

Un local cerrado a las 23:00 no da cobertura a quien necesita cargar a esa hora. El
dato para distinguirlo no está, y ningún supuesto lo reemplaza.

---

## 6. El resultado

```
      paradas_de_embarque    12497  paradas
         lugares_abiertos     1927  locales
         pares_calculados 24081719  pares
                mediana_m    249.6  m
                    p90_m    671.0  m
cobertura_linea_recta_pct    59.29  %
   cobertura_rodeo_13_pct    46.02  %
 paradas_fuera_de_alcance       61  paradas
```

Y la curva completa, que es el resultado de verdad:

| Umbral | Cobertura |
| --- | --- |
| 200 m | 39,60 % |
| **300 m** | **59,29 %** |
| 400 m | 73,11 % |
| 500 m | 81,84 % |
| 700 m | 90,83 % |
| 1 000 m | 95,22 % |

Qué tipo de local provee la cobertura:

| Tipo | Locales | Paradas | Mediana | Cobertura |
| --- | --- | --- | --- | --- |
| Estación de Metro | 143 | 1 344 | 180,6 m | 69,12 % |
| Centro bip! estándar | 29 | 262 | 224,7 m | 63,36 % |
| Punto bip! | 1 579 | 9 710 | 254,1 m | 58,71 % |
| Centro bip! alto estándar | 7 | 65 | 258,3 m | 58,46 % |
| Retail | 169 | 1 116 | 289,8 m | 51,52 % |

Las 143 estaciones de Metro son el local más cercano de 1 344 paradas con la mejor
mediana de todas: la red de Metro es, de hecho, la columna de la cobertura de carga.

### Lo que estos números **no** permiten concluir

- **No se puede concluir que el 59,29 % de los pasajeros tiene buena cobertura.** La
  cobertura no pondera demanda: una parada por la que pasan diez mil personas al día
  cuenta igual que una por la que pasan veinte. Los volúmenes por parada no son
  públicos.
- **No se puede concluir que una parada cubierta tiene servicio.** 5 701 de las 7 409
  están cubiertas por un local de horario desconocido.
- **No se puede afirmar nada por comuna.** El proxy disponible está sesgado y el caso
  lo mide.
- **No se puede decir cuánto se camina de verdad.** No hay red peatonal: no se
  consideran ríos, autopistas, cierres, pasarelas ni pendientes, que en Santiago
  cambian recorridos reales de forma sustancial.
- **No se puede extrapolar a otra fecha.** Es la foto del feed del 14 de noviembre de
  2026 y de los Excel del 26 de noviembre de 2026.

---

## 7. Qué quedó aprendido

1. **Un cruce sin clave obliga a inventar el criterio, y el criterio es la mitad del
   resultado.** Cuatro decisiones —fórmula, coordenada, rodeo y denominador— mueven la
   respuesta entre 39 % y 81 %. Ninguna es incorrecta; todas tienen que declararse.
2. **La euclídea sobre grados no es una aproximación: es un sesgo con eje.** Cero
   subestimaciones en 12 497 paradas. Un error con eje no se cancela al promediar.
3. **El error de un método se mide en la unidad de la decisión.** 17 metros de error
   mediano, 574 paradas que cambian de clase.
4. **Un agregado robusto puede esconder una asignación individual que no lo es.** Son
   dos propiedades distintas y hay que medirlas por separado antes de decidir para qué
   sirve el resultado.
5. **Una clave que no es única falla al volver, y a veces no falla: devuelve un número
   un poco menor.** 807 en lugar de 814.
6. **El número de filas no es el número de entidades.** 18 486 filas, 12 497 paradas.
7. **Cuando el dato no está, a veces lo honesto es cambiar la pregunta y no el dato.**
   La rejilla contesta «qué zonas quedan peor» sin incorporar una fuente nueva ni
   fingir una precisión administrativa que no se tiene.
8. **Un umbral con cita sigue siendo una decisión.** El manual asocia 300 m a 3–5
   minutos de caminata, pero para el espaciamiento entre paradas. La analogía se
   declara.

Registros en la base de conocimiento:
[`cruce-sin-clave`](../../knowledge/cruce-sin-clave.md) ·
[`sesgo-con-eje`](../../knowledge/sesgo-con-eje.md) ·
[`clave-falla-al-volver`](../../knowledge/clave-falla-al-volver.md) ·
[`unidad-de-la-decision`](../../knowledge/unidad-de-la-decision.md) ·
[`cambiar-la-pregunta`](../../knowledge/cambiar-la-pregunta.md)

---

## Reproducir

```powershell
python scripts/fetch_data.py gtfs-red-movilidad bip-metro bip-puntos bip-centros-alto-estandar bip-centros-estandar bip-retail
python -m cases.cobertura_de_carga.solution
```

Las pruebas no necesitan los datos: construyen una geometría sintética con distancias
exactas.

```powershell
python -m pytest tests/test_cobertura_de_carga.py -v
```

## Cuaderno, motores y gráfico

- [Resolución profesional paso a paso](CUADERNO.md).
- [Abrir en Google Colab](https://colab.research.google.com/github/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/blob/main/cases/cobertura_de_carga/cuaderno/colab.ipynb).
- [Pandas + Matplotlib](cuaderno/solucion_pandas.py): referencia comparable de sensibilidad al umbral.
- [Polars + Matplotlib](cuaderno/solucion_polars.py): curva de sensibilidad al umbral.
- [R + dplyr/readr + ggplot2](cuaderno/solucion.R) y [R Markdown](cuaderno/solucion.Rmd): contraste y distribución portable.
- [Figura publicada](cuaderno/svg/paso-05.svg).
