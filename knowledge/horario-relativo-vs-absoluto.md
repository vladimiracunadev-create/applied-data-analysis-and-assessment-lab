---
id: horario-relativo-vs-absoluto
tipo: error
titulo: Una columna de hora que no contiene horas
etiquetas: [fechas-horarios, calidad-datos, gtfs, errores-frecuentes, datos-reales]
fuente: cases/gtfs_red_movilidad/solution.py
relacionados: [relleno-de-ceros-y-orden, expandir-frecuencias, duracion-en-minutos-tres-herramientas]
---

**Síntoma.** Al agrupar la hora de paso de 1 098 717 registros de horarios de
transporte, 635 574 caían «entre las 00:00 y las 00:59». El 58 % del servicio de una
ciudad a medianoche.

**Causa.** La tabla mezcla dos poblaciones con la misma columna y semántica distinta:

| Población | Qué contiene `arrival_time` | Cuántas |
| --- | --- | --- |
| Expediciones con horario | hora de reloj: `07:16:40` | 11 617 |
| Expediciones por frecuencia | **desplazamiento desde el inicio del viaje**: `0:00:00`, `00:00:51` | 14 520 |

Para una expedición de frecuencia, el horario dice «la segunda parada está a 51
segundos de la primera», no «pasa a las 00:00:51». La hora real de salida vive en otra
tabla, con una ventana y una cadencia.

En este feed, **851 773 filas, el 77,5 % de la tabla**, no se pueden leer como reloj.

**Cómo se detecta sin conocer el formato de antes.** Por la distribución. Un sistema de
transporte no concentra el 58 % de sus pasos en una hora, y menos a medianoche. *Una
distribución que no puede ser cierta es la señal*: antes de explicar un patrón
sorprendente hay que descartar que la columna signifique otra cosa.

**Cómo se resuelve.** Separar las dos poblaciones antes de cualquier agregación, por la
presencia de la expedición en la tabla de frecuencias:

```python
con_frecuencia = set(frequencies["trip_id"])
relativo = stop_times["trip_id"].isin(con_frecuencia)
```

Después, cada población se trata con su propia mecánica: la de horario absoluto se
agrupa por su hora; la de frecuencia se expande desde su ventana. Ver
[[expandir-frecuencias]].

**Dónde más aparece el mismo patrón.** Cualquier dato que mezcle marcas de tiempo
absolutas con desplazamientos relativos en una sola columna: tiempos de proceso
industrial medidos desde el inicio del lote, cronómetros de atención medidos desde la
llegada, duraciones de llamada guardadas con formato de hora. La pregunta que lo
destapa siempre es la misma: **¿esta columna es un instante o es un intervalo?**
