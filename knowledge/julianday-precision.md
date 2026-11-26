---
id: julianday-precision
tipo: error
titulo: julianday en SQLite invierte las comparaciones de duración en los empates
etiquetas: [sql, sqlite, fechas-horarios, punto-flotante, validacion-independiente]
fuente: solutions/sql_reference.py, cases/transport/case.json
relacionados: [duracion-en-minutos-tres-herramientas, vacio-no-es-cero]
---

**Síntoma.** La puntualidad calculada en SQL daba menos que la calculada en Pandas,
en recorridos distintos y por cantidades distintas: 43,6 % frente a 35,9 % en un
recorrido, idénticas en otro. Los recuentos de viajes coincidían exactamente, así
que el problema no estaba en el filtro ni en el cruce.

**Causa.** La duración se calculaba como
`(julianday(fin) - julianday(inicio)) * 1440`. `julianday` devuelve días en punto
flotante; la resta de dos números grandes y cercanos pierde dígitos significativos, y
el producto por 1440 entrega `42.999999971` donde el valor exacto es `43`. La
comparación del indicador era `duracion <= meta_min`, con `meta_min` entero. En todos
los viajes cuya duración coincidía exactamente con la meta, la comparación pasaba de
verdadera a falsa.

Que el error apareciera solo en los empates explica por qué afectaba a unos
recorridos y no a otros, y por qué la **media** de duración coincidía hasta el octavo
decimal mientras el **porcentaje** difería en varios puntos.

**Corrección.** Restar segundos enteros, que en SQLite son exactos:

```sql
(CAST(strftime('%s', fin) AS INTEGER) - CAST(strftime('%s', inicio) AS INTEGER)) / 60.0
```

**Lección general.** Un indicador que compara una magnitud calculada contra un umbral
es sensible al error de punto flotante justo en el umbral, que suele ser el caso más
frecuente del dataset. Antes de comparar, conviene calcular en la unidad entera más
fina disponible (segundos, centavos, unidades) y dividir al final.

**Por qué se detectó.** Solo porque existían dos implementaciones independientes del
mismo indicador. Con una sola, el número habría sido plausible y nadie lo habría
cuestionado.
