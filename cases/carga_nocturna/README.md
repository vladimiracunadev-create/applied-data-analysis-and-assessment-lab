# P09 · Cobertura de carga en el servicio nocturno

El caso donde la respuesta correcta no es un número. Es un intervalo de **52,6 puntos
de ancho**, y ese ancho no lo produce la red ni la geografía: lo produce una columna
vacía en uno de los cinco archivos.

Metadatos: [`case.json`](case.json) · Núcleo nuevo:
[`lab/schedules.py`](../../lab/schedules.py) · Hereda de
[P08](../cobertura_de_carga/README.md) y [P06](../gtfs_red_movilidad/README.md)

---

## 1. El problema, en palabras

Entre las 00:00 y las 05:00 la Red Metropolitana de Movilidad tiene servicio real:

- **367 251 llegadas** de bus
- en **10 520 paradas**, que son el **84,2 %** de las paradas de embarque de la red
- con una mediana de **23 llegadas por parada** en esas cinco horas, una cada trece
  minutos

No es un servicio marginal. Para subir hay que llevar saldo en la tarjeta bip!, y el
saldo se carga en locales físicos.

La pregunta: **donde hay servicio de madrugada, ¿hay dónde cargar?**

Es un cruce de **dos dimensiones a la vez**. No alcanza con que haya un local cerca
(espacio): tiene que estar abierto a esa hora (tiempo). Y la segunda dimensión vive en
un campo de texto libre que está presente en el 18,06 % de los locales.

---

## 2. Descomposición

| # | Subproblema | Por qué no es trivial |
| --- | --- | --- |
| 1 | Qué paradas tienen servicio nocturno | El `arrival_time` de las expediciones de frecuencia no es una hora |
| 2 | Las llegadas de después de medianoche | Las 00:00–05:00 son **dos** intervalos de segundos de servicio |
| 3 | Sin expandir 142 366 salidas | La unión con 1,1 M de filas no cabe |
| 4 | Interpretar el horario en texto libre | Diez formatos distintos, uno con saltos de línea |
| 5 | Qué hacer con los 1 579 locales sin horario | La decisión que determina todo el resultado |
| 6 | Cómo publicar un indicador con huecos | Un número con nota al pie no sirve |

---

## 3. La trampa que da una cifra plausible y falsa

El atajo natural: filtrar `arrival_time` entre `00:00:00` y `04:59:59`.

```
      filas_que_el_atajo_toma   851 773   filas
de_ellas_con_horario_relativo   851 773   filas
         proporcion_relativas       100   %
       paradas_segun_el_atajo    12 201   paradas
            paradas_correctas    10 520   paradas
              sobreestimacion     15,98   %
```

El **100 %** de lo que el atajo toma son filas de expediciones de frecuencia, cuyo
`stop_times` no contiene horas de reloj sino **desplazamientos desde el inicio del
viaje**, que empiezan todos en `0:00:00`. El atajo no está midiendo horas en absoluto.

Y aquí está lo peligroso: **12 201 no es un número absurdo.** El valor correcto es
10 520. Sobreestima apenas un 16 %, de modo que nada en el resultado grita que está
mal.

> El atajo peligroso no es el que da una cifra absurda. Es el que da una cifra
> verosímil. El primero se corrige; el segundo se publica.

### Las 00:00–05:00 son dos intervalos, no uno

El cálculo correcto tiene una segunda parte que el atajo tampoco tiene. La llegada real
de la salida `k` de una ventana a una parada es:

```
llegada = inicio_de_ventana + k · intervalo + desplazamiento_de_la_parada
```

Un bus que sale a las **23:30** y tarda **40 minutos** llega a su parada final a las
**00:10**, que en segundos de servicio son `86 400 + 600`. Está en la madrugada del
reloj y **no** está en `[0, 18 000)`.

De modo que hay que mirar dos intervalos: `[0 s, 18 000 s)` y `[86 400 s, 104 400 s)`.
**1 490 paradas** tienen servicio nocturno únicamente por esa segunda vía.

### Cómo se cuenta sin expandir nada

Expandir sería lo natural: 142 366 salidas unidas a las paradas de su recorrido. Son
cientos de millones de filas para responder una pregunta de sí o no por parada.

No hace falta. Las llegadas de una ventana a una parada forman una **progresión
aritmética** `primero + k·intervalo`, con `k` en `[0, salidas)`. Contar cuántas caen en
`[a, b)` son dos techos acotados y una resta:

```python
k_desde = clip(ceil((a - primero) / intervalo), 0, salidas)
k_hasta = clip(ceil((b - primero) / intervalo), 0, salidas)
llegadas = max(k_hasta - k_desde, 0)
```

Exacto, vectorizado, y sin materializar nada.

---

## 4. El intérprete de horarios, y la decisión que lo gobierna

Los 348 locales que declaran horario usan **diez textos distintos**:

| Texto | Locales |
| --- | --- |
| `Lun-Dom 08:00-21:00` | 168 |
| `Lunes a Viernes: 6:00 a 23:00 horas, Sábados: 6:30 a 23:00 horas, Domingos y festivos: 8:00 a 22:30 horas.` | 143 |
| `Lun a Sab 08:00 a 21:00 Dom y Festivos 09:00 a 14:00` | 15 |
| … otros siete, entre 1 y 9 locales cada uno | 22 |
| *(vacío)* | **1 579** |

Los diez se interpretan, incluido uno que trae **saltos de línea dentro de la celda**.
Eso está en [`lab/schedules.py`](../../lab/schedules.py), que es núcleo y no caso: un
campo de horario de atención escrito por personas aparece en cualquier catastro de
locales, directorio de sucursales o registro de atención de público.

### La regla que determina todo el resultado

> **Lo que no se entiende es desconocido, nunca «cerrado».**

Por eso `is_open` tiene **tres** respuestas: `True`, `False` y `None`.

Es la decisión que separa un intérprete honesto de uno que produce cifras cómodas.
Tratar el silencio como un cierre convierte un vacío de datos en una afirmación sobre
el mundo, y lo hace en la dirección que infla el problema: serían 1 579 locales
declarados cerrados de madrugada sin que nadie lo haya dicho.

La misma regla se aplica a los días: un texto que dice «Lun a Vie» no dice nada del
sábado. El sábado queda desconocido, no cerrado.

### Un detalle que limita todo lo que sigue

Diez textos para 348 locales, y **311 de ellos usan solo dos**. Los 143 que comparten
la frase larga son todas las estaciones de Metro; los 168 que comparten la corta, una
cadena de retail.

El campo no describe un local: describe **la política de una cadena**. Interpretarlo
correctamente no arregla ese problema, solo lo deja a la vista. Y el archivo lo llama
`horario referencial`, que es una advertencia del propio publicador.

---

## 5. Las cuatro clases, y por qué son cuatro

Cada parada con servicio nocturno cae en una de cuatro situaciones excluyentes:

| Situación | Qué significa | ¿Permite afirmar? |
| --- | --- | --- |
| **Con carga abierta verificada** | Hay un local a 300 m que declara abrir de noche | sí |
| **Sin local a 300 m** | No hay nada cerca; el horario es irrelevante | sí |
| **Sin carga abierta (verificado)** | Hay locales cerca, **todos** con horario conocido, ninguno abre | sí |
| **Indeterminado** | Hay locales cerca y al menos uno no declara horario | **no** |

La cuarta clase es el resultado del caso. Fundirla con la tercera —tratar el silencio
como un cierre— daría un titular de «59,8 % sin cobertura verificada» que suena a
medición y es una invención.

Y basta **un** local sin horario para volver indeterminada una parada, aunque sus
vecinos sí lo declaren. Es la decisión conservadora correcta: con un local cercano del
que no se sabe nada, no se puede afirmar que no hay cobertura.

---

## 6. El resultado

```
                               situacion  paradas  porcentaje permite_afirmar
            con carga abierta verificada        0         0.0              sí
                       sin local a 300 m     4225        40.2              sí
          sin carga abierta (verificado)      759         7.2              sí
indeterminado: local cercano sin horario     5536        52.6              no
             TOTAL con servicio nocturno    10520       100.0               —
```

**Cero.** Ninguna de las 10 520 paradas con servicio nocturno tiene, a 300 m o menos,
un lugar de carga que declare estar abierto en esa ventana. Y no por falta de locales
en la ciudad: **ninguno de los 1 927 locales abiertos** declara abrir de madrugada. El
más tardío cierra a las 23:00.

### La respuesta es un intervalo

```
paradas_con_servicio_nocturno   10 520   paradas
         cobertura_verificada        0   paradas
         cobertura_minima_pct     0,00   %
         cobertura_maxima_pct    52,62   %
       ancho_del_intervalo_pp    52,62   puntos
```

El piso es lo verificado. El techo supone que **todos** los locales sin horario abren de
madrugada —falso casi con certeza, dado que ninguno de los 348 que sí declaran lo
hace— pero es la cota que el dato permite.

El ancho del intervalo es un indicador por derecho propio: mide **cuánto de la pregunta
sigue abierto**.

### Lo mismo cualquier día de la semana

```
service_id  dias  paradas_nocturnas  llegadas  abierta  sin_local  cerrado  indeterminado  %
         D     1               9681    108291        0       3803      709           5169  53.4
         L     5              10465    140424        0       4185      759           5521  52.8
         S     1               9960    118536        0       3922      730           5308  53.3
```

La noche del sábado es la de mayor demanda y sale igual que las otras. Que salga igual
**es** el resultado: no hay un día en que la cobertura nocturna exista.

### El servicio nocturno no es uniforme

```
                     estadistico  llegadas
                             P10       3.0
                             P25       7.0
                             P50      23.0
                             P75      48.0
                             P90      80.0
                          máximo     459.0
         una sola llegada en 5 h     242.0
         5 o menos (testimonial)    1867.0
solo por llegadas tras las 24:00    1490.0
```

«Tiene servicio nocturno» es un sí o no que esconde todo. Hay paradas con un bus cada
trece minutos y **242 con una sola llegada** en cinco horas. Tratarlas igual pierde la
mitad de lo que el dato dice.

---

## 7. El hallazgo que vale: una columna, un archivo, una decisión

```
               tipo_local  locales  con_horario  abren_de_noche  cobertura_pct
Centro bip! alto estándar        7            7               0          100.0
     Centro bip! estándar       29           29               0          100.0
        Estación de Metro      143          143               0          100.0
               Punto bip!     1579            0               0            0.0
                   Retail      169          169               0          100.0
                    TOTAL     1927          348               0           18.1
```

Cuatro archivos al **100 %** y uno al **0 %** — y es el que tiene 1 579 de los 1 927
locales.

> Un vacío **uniforme** en un campo es un problema de captura. Un vacío **concentrado
> en un archivo** es una decisión de publicación. La diferencia cambia a quién se le
> reporta y qué se le pide.

Y la consecuencia está medida:

```
tipo_local  locales_por_completar  del_total_sin_horario_pct  paradas_que_desbloquean
Punto bip!                   1546                       97.9                     5536
```

**1 546 de los 1 579 locales sin horario están a menos de 300 m de una parada con
servicio nocturno.** Completar esos registros —el 97,9 % de los que faltan— vuelve
contestable el 52,6 % de la red nocturna.

Eso es lo que este caso entrega. No la cobertura, que no se puede establecer, sino el
pedido concreto que hay que hacerle al publicador y la cifra que lo justifica.

> No «faltan horarios». Sino: «estos 1 546 registros desbloquean el 52,6 % de la red
> nocturna». La primera frase es una queja; la segunda, una solicitud priorizada.

### Lo que sí se puede afirmar, sin intervalos

- Ninguno de los 348 locales que declaran horario abre de madrugada. El más tardío
  cierra a las **23:00**.
- **4 225 paradas** con servicio nocturno no tienen local alguno en trescientos metros.
  Esta conclusión es firme porque **no depende de ningún horario**.

Las quince peores, mucho servicio y nada cerca:

```
stop_id                                  stop_name  llegadas_noche  tras_medianoche
  PI253               PI253-Parada 3 / (M) Del Sol             254               97
  PC196    PC196-Parada 2 / Museo de Los Tajamares             253               54
  PC195          PC195-Parada 2 / Parque Balmaceda             252               52
  PI339                    PI339-Parada 3 / Concón             235               35
  PI217     PI217-Parada 1 / Paradero 14 Pajaritos             224              100
```

---

## 8. Lo que estos números **no** permiten concluir

- **No se puede responder la pregunta para el 52,6 % de las paradas nocturnas.** Es el
  resultado principal, no una limitación lateral.
- **La ventana de 00:00 a 05:00 es una elección del caso.** No se encontró ninguna
  definición oficial de «servicio nocturno» para la red, de modo que el denominador es
  discutible y queda declarado.
- **El horario, donde existe, es de cadena y no de local.** Diez textos para 348
  registros.
- **Las llegadas son oferta programada.** No hay datos de operación real.
- **No se pondera demanda.** Una parada con 459 llegadas nocturnas cuenta igual que una
  con una sola.
- **El pliegue de día no se resuelve.** Una llegada a las 24:30 de un viernes de
  servicio ocurre un sábado; el caso lo evita preguntando por el día más favorable de
  los siete, lo que da una cota superior. Como ningún local abre ningún día, el pliegue
  no cambia nada aquí — pero cambiaría con otros datos, y queda dicho.

---

## 9. Qué quedó aprendido

1. **Un indicador que cruza dos dimensiones necesita tres respuestas, no dos.** Fundir
   «no hay» con «no se sabe» fabrica una medición.
2. **La respuesta honesta a una pregunta con huecos es un intervalo**, y su ancho es un
   indicador: mide cuánto sigue abierto y a quién hay que pedírselo.
3. **Un vacío concentrado en un archivo es una decisión, no un accidente.**
4. **El atajo peligroso es el que da una cifra verosímil.** 12 201 contra 10 520.
5. **Las 00:00–05:00 de reloj son dos intervalos en GTFS.** 1 490 paradas dependen del
   segundo.
6. **Una pregunta de sí o no sobre una progresión aritmética no necesita la
   progresión.** Dos techos y una resta.
7. **Diez valores distintos en 348 registros no describen los registros**, describen a
   quien los agrupa.
8. **Cuantificar el dato que falta convierte una queja en una solicitud priorizada.**

Registros en la base de conocimiento:
[`tres-respuestas-no-dos`](../../knowledge/tres-respuestas-no-dos.md) ·
[`intervalo-en-vez-de-cifra`](../../knowledge/intervalo-en-vez-de-cifra.md) ·
[`vacio-concentrado`](../../knowledge/vacio-concentrado.md) ·
[`atajo-verosimil`](../../knowledge/atajo-verosimil.md) ·
[`progresion-sin-expandir`](../../knowledge/progresion-sin-expandir.md)

---

## Reproducir

```powershell
python scripts/fetch_data.py gtfs-red-movilidad bip-metro bip-puntos bip-centros-alto-estandar bip-centros-estandar bip-retail
python -m cases.carga_nocturna.solution
```

Las pruebas no necesitan los datos: construyen un feed con aritmética temporal
calculable a mano.

```powershell
python -m pytest tests/test_carga_nocturna.py tests/test_schedules.py -v
```
