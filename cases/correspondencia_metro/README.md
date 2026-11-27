# P10 · Conciliar dos inventarios de la misma realidad

La pregunta de P10 tiene una respuesta cómoda: el **100 %** de las estaciones de Metro
tiene paradas de bus a 200 m. Lo que el caso enseña es otra cosa, y la encontró por el
camino: **toda comprobación de calidad tiene un punto ciego, y el punto ciego es
medible**.

Metadatos: [`case.json`](case.json) · Audita a
[P01](../bip_lugares_carga/README.md) · Hereda el método de
[P08](../cobertura_de_carga/README.md)

---

## 1. El problema, en palabras

Dos archivos públicos describen **la misma realidad** —las estaciones de Metro de
Santiago— con identificadores distintos y sin ningún campo en común:

- el feed GTFS del DTPM trae **126 estaciones** (`location_type = 1`);
- el Excel de bip! trae **143 filas**.

La pregunta: **¿qué estaciones tienen paradas de bus a menos de 200 m, y cuántos
servicios distintos las sirven?**

Para contestarla hay que conciliar los dos inventarios. Y hay que decidir algo que casi
nadie declara, porque las dos fuentes son oficiales y ninguna se presenta como
aproximada: **cuál de las dos provee la coordenada de cada estación**.

---

## 2. El grano, que es lo primero y casi nunca está escrito

126 contra 143 no es un problema de completitud. Son **granos distintos**:

| Fuente | Grano | Cómo lo delata |
| --- | --- | --- |
| GTFS | una fila por **estación** | las 17 estaciones de combinación llevan un id compuesto: `AN-NA`, `BA-BQ`, `CH-UCH` |
| bip! | una fila por **estación y línea** | sus 34 filas de combinación llevan la línea pegada al **nombre**: `SAN PABLO L1`, `SAN PABLO L5` |

Y la identidad cierra:

```
126 estaciones − 17 combinaciones + 34 filas con sufijo = 143 filas
```

El grano cuadra, pero solo después de haberlo nombrado. Sin esta tabla, la diferencia de
17 filas parece un hueco y se «arregla» descartando, que es la forma habitual de perder
precisamente las estaciones de combinación — las más importantes de la red.

Un detalle que no es menor: la línea va **pegada al texto del nombre** porque el campo
`codigo` vale la línea y no identifica nada. Es el hallazgo de P01
([`clave-que-no-es-clave`](../../knowledge/clave-que-no-es-clave.md)) reapareciendo como
la causa de que el publicador tuviera que desambiguar en otro campo.

Quitado el sufijo —con un patrón **declarado**, no deducido por parecido— quedan
**126 estaciones distintas**, exactamente las del GTFS.

---

## 3. Dos criterios, porque uno solo no tiene con qué equivocarse a la vista

```
     estaciones_a_conciliar   126
          cruzan_por_nombre   125   (99,21 %)
         sin_par_por_nombre     1
los_dos_criterios_coinciden   113
    los_criterios_discrepan    13
```

**Por nombre normalizado** coinciden 125 de 126. La única excepción:
`Presidente Pedro Aguirre Cerda` en el GTFS contra `PEDRO AGUIRRE CERDA` en bip!. Un
cruce solo por nombre la perdería **sin avisar**.

**Por proximidad** se resuelve esa: están a **1,4 m**. Pero la proximidad, sola,
aceptaría en silencio un par equivocado donde dos estaciones son vecinas.

Los dos criterios juntos convierten el cruce en una medición. Donde discrepan es donde
hay algo que explicar:

```
stop_id                      stop_name    clave_mas_cercana  distancia_m  desvio_m
 PZ-PZA                 Plaza de Armas   PUENTE CAL Y CANTO        489.1   13147.7
     SL                    Santa Lucía UNIVERSIDAD DE CHILE        519.8   12736.4
     PQ               Parque O'Higgins           RONDIZZONI       1076.7   11630.1
    LIB               Los Libertadores        CARDENAL CARO        959.1    6597.5
    PDG              Príncipe de Gales     FRANCISCO BILBAO       1330.6    3530.4
     DS                        Del Sol      SANTIAGO BUERAS        876.1    2583.9
    PAC Presidente Pedro Aguirre Cerda  PEDRO AGUIRRE CERDA          1.4       NaN
```

Trece estaciones cuyo par por nombre **no** es su vecino más cercano. En doce de ellas
la causa es la misma: la coordenada de bip! está mal.

---

## 4. Lo que el agregado escondía

Para comparar con el GTFS hay que reducir las filas de bip! al grano de estación. Lo
natural es tomar la mediana de las coordenadas. Y eso **suaviza un error en lugar de
mostrarlo**:

```
          desvio_maximo_m   13 147,7   m    ← usando la mediana de las filas
desvio_maximo_peor_fila_m   26 243,3   m    ← usando la peor de sus filas
```

Las dos filas de Plaza de Armas están separadas **26,2 km**. Su mediana cae a 13,1 km de
cada una: **un punto donde no hay ninguna estación**, y que reduce el desvío aparente a
la mitad exacta.

De modo que el caso publica las dos cifras y la dispersión interna de cada estación. La
regla que queda:

> Cualquier promedio, mediana o primer valor que reduzca varias filas a una debería
> venir acompañado de la dispersión de lo que reemplazó.

---

## 5. El hallazgo: cuatro detectores y cuatro puntos ciegos

P01 validó las coordenadas del Excel comparando sus **dos representaciones** —UTM contra
latitud/longitud— y encontró tres errores en 1 928 filas. Es una comprobación correcta.

Y tiene un punto ciego del tamaño exacto del problema siguiente: **no ve un error que
afecte a las dos representaciones por igual**.

De las 143 filas de Metro, **ninguna** quedó marcada como sospechosa por P01. Y once
estaciones están a más de 500 m de donde el GTFS las pone:

| Detector | Qué compara | ¿Fuente externa? | Encuentra | Ciego a |
| --- | --- | --- | --- | --- |
| **1.** Dos representaciones de una fila | UTM contra lat/lon, dentro de la fila | no | **0** filas de Metro | un error que afecte a las dos por igual |
| **2.** Filas hermanas | fila contra fila que nombra lo mismo | no | **4** estaciones | la estación que tiene una sola fila |
| **3.** Coordenada contra comuna declarada | fila contra la mediana de sus pares | no | **3** estaciones | un error dentro de la propia comuna |
| **4.** Contra otra fuente | bip! contra el feed GTFS | **sí** | **11** estaciones | un error que las dos fuentes compartan |

Lo que importa de esa tabla: **tres de los cuatro no necesitan ninguna fuente externa**,
y P01 solo corrió el primero. El archivo podía delatar sus propios errores y nadie le
hizo las preguntas.

### Los dos casos, para que no quede en abstracto

**Plaza de Armas** — la atrapa el detector 2, sin salir del archivo.

| Fila | Dirección | Latitud | |
| --- | --- | --- | --- |
| `PLAZA DE ARMAS L3` | Bandera 530 | −33,4371 | correcto |
| `PLAZA DE ARMAS L5` | 21 De Mayo 543 | −33,2018 | **26 km al norte** |

Las dos direcciones están a una cuadra una de la otra, en el centro de Santiago. La
dirección es correcta y la coordenada no. Bastaba comparar dos filas que nombran la
misma estación.

**Santa Lucía** — tiene una sola fila, de modo que no hay hermana que la contradiga.

```
nombre: SANTA LUCIA
direccion: Av. Libertador Bernardo O´Higgins N°511   ← el centro de Santiago
coordenada: -33.501205, -70.762993                   ← 12,7 km al suroeste
```

Su UTM está igual de mal, así que P01 no la vio. La atrapa el **detector 3**: está a
12,0 km de la mediana de los 148 locales de la comuna `Santiago` que ella misma declara.

Y es, con las coordenadas del GTFS, **la estación con más correspondencia de bus de toda
la red**: 55 servicios.

### El detector 3 es una señal, no un veredicto

```
 umbral_km  locales_marcados  estaciones_de_metro  puntos_bip  otros
       3.0               227                   13         189     25
       5.0                63                    5          52      6
      10.0                 8                    3           4      1
      15.0                 2                    1           1      0
```

A 3 km marca 227 locales, que son demasiados para ser todos errores en comunas extensas.
A 10 km marca 8, y los tres de Metro son errores verificados contra el GTFS. La curva se
publica para que la elección del umbral quede a la vista en lugar de esconderse en una
constante.

Una nota de método: la referencia de comuna es la **mediana** y no el promedio. Con una
fila a 26 km, un promedio arrastra la referencia hacia el error y el detector se ciega
contra sí mismo.

---

## 6. La respuesta a P10

```
   estaciones_evaluadas   126
con_parada_de_bus_cerca   126   (100,0 %)
            sin_ninguna     0
      servicios_mediana    13
          servicios_p90    33,5
       servicios_maximo    55
        paradas_mediana     5
```

Las 126 estaciones tienen al menos una parada de bus a 200 m. No hay ninguna sin
correspondencia. Mediana de **13 servicios distintos** por estación, máximo de 55.

| Estación | Paradas de bus | Servicios |
| --- | --- | --- |
| Santa Lucía | 9 | **55** |
| La Moneda | 7 | 50 |
| Estación Central | 11 | 47 |
| Los Héroes | 13 | 44 |
| Universidad de Chile | 7 | 43 |
| Plaza de Maipú | 10 | 38 |

### Y la advertencia que vale tanto como el resultado

```
       estaciones_comparables    125
cambia_el_conteo_de_servicios     48   (38,4 %)
          aparecerian_sin_bus      3
   servicios_totales_con_gtfs   2014
    servicios_totales_con_bip   1834
```

Calculada con las coordenadas de bip! en lugar de las del GTFS, la respuesta cambia en
**48 de 125 estaciones**, el total de servicios baja un 9 %, y **tres estaciones
aparecerían sin ninguna parada de bus cerca** cuando sí la tienen.

La elección de qué fuente provee la coordenada decide el **38,4 %** de las filas del
informe. Y es una decisión que no suele aparecer en ninguna parte, porque las dos
fuentes son oficiales.

---

## 7. Lo que este caso **no** establece

- **No demuestra que el GTFS tenga razón.** Sostiene algo más modesto y suficiente: las
  dos fuentes discrepan, y en los dos casos inspeccionados a mano la **dirección postal
  que trae el propio Excel** coincide con la posición del GTFS y no con su propia
  coordenada. Eso es evidencia, no prueba.
- **La correspondencia es geométrica.** No considera si el acceso está del lado correcto
  de la avenida, si hay cruce semaforizado, ni si la combinación está habilitada
  tarifariamente.
- **Los servicios son oferta programada.** Que un recorrido pase por la parada no
  implica que el pasajero pueda usarlo en ese sentido ni a cualquier hora.
- **El radio de 200 m lo fija el enunciado del problema**, no una norma publicada.
- **Faltan estaciones en las dos fuentes**: la Línea 7 y las extensiones en construcción
  no aparecen en ninguna.

---

## 8. Qué quedó aprendido

1. **Antes de cruzar, nombrar el grano.** 126 − 17 + 34 = 143. Sin esa identidad, la
   diferencia parece un hueco y se arregla descartando combinaciones.
2. **Cuando el grano difiere, la fuente lo delata en un campo inesperado**: un id con
   guion, o la línea pegada al texto del nombre.
3. **Un solo criterio de emparejamiento no tiene con qué equivocarse a la vista.** Dos
   criterios independientes convierten un cruce en una medición.
4. **Reducir el grano promediando coordenadas suaviza el error en lugar de mostrarlo**, y
   lo reduce exactamente a la mitad.
5. **Toda comprobación de calidad tiene un punto ciego, y es medible.** La de P01 no
   puede ver un error que afecte a las dos representaciones por igual, y hay once así.
6. **Antes de pedir otra fuente, preguntarle al archivo si se contradice consigo mismo.**
   Tres de los cuatro detectores no necesitan nada externo.
7. **La dirección y la coordenada son dos afirmaciones independientes.** Cuando se
   contradicen, una de las dos está mal, y eso es comprobable sin salir de la fila.
8. **Qué fuente provee cada campo es una decisión metodológica**, y aquí decide el 38,4 %
   del informe.

Registros en la base de conocimiento:
[`grano-antes-de-cruzar`](../../knowledge/grano-antes-de-cruzar.md) ·
[`punto-ciego-del-control`](../../knowledge/punto-ciego-del-control.md) ·
[`agregado-que-suaviza`](../../knowledge/agregado-que-suaviza.md) ·
[`dos-afirmaciones-de-la-misma-fila`](../../knowledge/dos-afirmaciones-de-la-misma-fila.md) ·
[`que-fuente-provee-el-campo`](../../knowledge/que-fuente-provee-el-campo.md)

---

## Reproducir

```powershell
python scripts/fetch_data.py gtfs-red-movilidad bip-metro bip-puntos bip-centros-alto-estandar bip-centros-estandar bip-retail
python -m cases.correspondencia_metro.solution
```

Las pruebas no necesitan los datos: construyen un inventario sintético de cuatro
estaciones con todas las distancias calculables a mano.

```powershell
python -m pytest tests/test_correspondencia_metro.py -v
```

## Cuaderno, motores y gráfico

- [Resolución profesional paso a paso](CUADERNO.md), ahora en una navegación lineal.
- [Polars + Matplotlib](cuaderno/solucion_polars.py): hallazgos por detector.
- [R + ggplot2](cuaderno/solucion.R): contraste y gráfico equivalente.
- [Figura publicada](cuaderno/svg/paso-04.svg).
