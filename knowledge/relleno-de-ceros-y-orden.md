---
id: relleno-de-ceros-y-orden
tipo: error
titulo: El relleno de ceros irregular invierte el orden como texto
etiquetas: [fechas-horarios, calidad-datos, pandas, excel, sql, errores-frecuentes, datos-reales]
fuente: lab/dates.py, cases/gtfs_red_movilidad/solution.py
relacionados: [horario-relativo-vs-absoluto, duracion-en-minutos-tres-herramientas, vacio-no-es-cero]
---

**El hecho.** En datos públicos reales, la misma expedición de transporte trae sus
horas así:

```
parada 1   0:00:00     (una cifra de hora: 13 570 filas en el feed)
parada 2  00:00:51     (dos cifras:     1 085 147 filas)
parada 3  00:01:22
```

Y entonces:

```python
'0:00:00' < '00:00:51'   # False
```

Comparando carácter a carácter: el primero coincide (`0` = `0`); en el segundo, `:`
vale 58 en la tabla de caracteres y `0` vale 48. Como `58 > 48`, el texto `'0:00:00'`
es **mayor** que `'00:00:51'`. La primera parada del recorrido queda al final.

**Qué se rompe.** Todo lo que compare u ordene el texto sin convertirlo:

| Operación | Resultado erróneo |
| --- | --- |
| `sort_values("arrival_time")` | la parada 1 al final del recorrido |
| `min()` / `max()` | el primer paso no es el mínimo |
| `groupby(serie.str[:2])` | `0:` y `00` como grupos distintos |
| `WHERE hora BETWEEN '06:00:00' AND '09:00:00'` en SQL | excluye `6:30:00` |
| Filtro de Excel sobre texto | ordena 10 antes de 2 |

Es el mismo mecanismo que hace que `R1, R10, R2` parezca un orden correcto.

**Cómo se resuelve.** Convertir a una magnitud numérica **antes** de comparar. Para
horas que pueden exceder el día:

```python
from lab.dates import parse_hms_seconds, seconds_to_hms

segundos = parse_hms_seconds(serie)          # 0, 51, 82, …  NaN si no es válido
texto = seconds_to_hms(segundos)             # siempre HH:MM:SS, ordenable como texto
```

`parse_hms_seconds` acepta de una a tres cifras de hora y devuelve **NaN**, no cero,
ante lo no interpretable: una hora ausente no es la medianoche.

**Regla práctica.** Un identificador o una magnitud guardados como texto solo se
ordenan bien si el relleno es **fijo**. Si el ancho varía, hay que convertir o
normalizar. Antes de confiar en un orden de texto, la comprobación cuesta una línea:

```python
serie.str.len().value_counts()     # más de un valor = relleno irregular
```
