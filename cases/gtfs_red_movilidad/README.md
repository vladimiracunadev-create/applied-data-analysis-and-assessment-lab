# Caso: expediciones por hora en la Red Metropolitana de Movilidad

**Datos públicos reales.** Es el único caso del laboratorio que no usa datos
sintéticos. Sirve para ver qué aparece cuando los datos no los generó nadie pensando
en enseñar.

> Los datos **no se versionan** en este repositorio: su licencia no está verificada.
> Se versiona el código, el registro de procedencia y las tablas de resultado
> agregadas. Descargue el feed con
> `python scripts/fetch_data.py gtfs-red-movilidad`.

---

## 1. El problema, en palabras

Una autoridad de transporte necesita saber **cuántas expediciones salen por hora del
día en un día laboral, y cómo se reparten entre buses, Metro y trenes.**

La decisión detrás: dimensionar la supervisión en terreno y responder cuántos
servicios hay disponibles en cada franja. El número tiene que poder defenderse ante
quien lo va a usar.

Parece un conteo. El feed tiene una tabla `trips.txt` con 26 137 filas, una por
expedición. La respuesta aparente es «26 137 expediciones, repartidas por hora según
`stop_times.txt`».

**Esa respuesta está mal por un factor de ocho**, y el error no se nota mirando el
resultado.

---

## 2. Descomposición

| # | Pregunta respondible | Qué hace falta para contestarla |
| --- | --- | --- |
| 1 | ¿Qué expediciones operan en un día laboral? | `trips.service_id` cruzado con `calendar.txt` |
| 2 | ¿A qué hora sale cada una? | Depende: unas tienen horario, otras frecuencia |
| 3 | ¿Cuántas salidas reales representa una frecuencia? | Expandir la ventana por su intervalo |
| 4 | ¿De qué modo es cada expedición? | `routes.route_type` |
| 5 | ¿Los datos son íntegros? | Seis cruces de clave foránea |

---

## 3. De dónde salen los datos

| Campo | Valor |
| --- | --- |
| Publica | Directorio de Transporte Público Metropolitano (DTPM) |
| Página índice | <https://www.dtpm.cl/index.php/gtfs-vigente> |
| Archivo | `GTFS_20261114_v2.zip` |
| Vigencia declarada | desde el 14 de noviembre de 2026 |
| Tamaño | 12 829 198 bytes comprimido, 69 728 607 descomprimido |
| SHA-256 | `ff0cda445cc4652013e159a133fcf863278ec55f6146e48c5a2416bf41c0b155` |
| Descargado | 26 de noviembre de 2026 |
| Licencia | **no verificada**: se abrió la página de descarga, no sus términos de uso |

El registro completo está en [`procedencia.json`](procedencia.json).

**Por qué el nombre del archivo no se escribe a mano.** Cambia en cada publicación
(`GTFS_<AAAAMMDD>[_vN].zip`). Un script que lo construya a partir de una fecha funciona
el día que se escribe y falla a la semana siguiente, sin aviso.
`lab.sources.discover_link` lee el enlace de la página índice con una expresión
regular sobre el `href`. Si la página cambia de estructura, el error es explícito.

### Las tablas que se usan

| Archivo | Filas | Para qué |
| --- | --- | --- |
| `stop_times.txt` | 1 098 717 | horas de paso por parada |
| `trips.txt` | 26 137 | expediciones y su servicio |
| `stops.txt` | 18 486 | paradas y su jerarquía |
| `frequencies.txt` | 14 520 | ventanas de frecuencia |
| `routes.txt` | 425 | recorridos y modo |
| `calendar.txt` | 6 | días de servicio |
| `agency.txt` | 4 | operadores |

---

## 4. Qué tecnología se usa y por qué

| Decisión | Alternativas | Por qué esta |
| --- | --- | --- |
| Leer del ZIP en memoria (`zipfile` + `read_csv` sobre el flujo) | Descomprimir a disco primero | 69,7 MB descomprimidos de los que 51 son un solo archivo. Descomprimir duplica el espacio y no aporta nada |
| `usecols` con 4 de las 8 columnas de `stop_times` | Leer la tabla completa | Reduce a la mitad la memoria de 1,1 millones de filas |
| `dtype=str` en todo | Dejar que pandas infiera | Queremos ver los valores tal como los publicó el organismo y decidir nosotros qué es una hora. Con inferencia, `0:00:00` se convierte en algo antes de validarlo |
| `lab.dates.parse_hms_seconds` | `pd.to_datetime`, `pd.to_timedelta` | `to_datetime` rechaza `25:10:00`; el formato admite horas de 24 o más y relleno de ceros irregular |
| Expansión con `Index.repeat` | Bucle sobre las ventanas | 14 520 ventanas y 142 366 salidas: la versión vectorizada es dos órdenes de magnitud más rápida |
| Pandas, no SQL ni DuckDB | DuckDB sobre el CSV | La operación pesada es un producto cartesiano acotado sobre 14 520 filas, no una agregación sobre el millón. DuckDB sería mejor si hubiera que agregar `stop_times` completo por ventanas; aquí no hace falta y se dice por qué |
| `sqlite3` para la validación | Confiar en el resultado | El acuerdo entre dos implementaciones es la única evidencia real |

---

## 5. Las cuatro trampas, resueltas

### Trampa 1 — el horario no siempre es un horario

De las 26 137 expediciones, **14 520 son de frecuencia**. Para ellas,
`stop_times.arrival_time` no es una hora de reloj: es el **desplazamiento desde el
inicio del viaje**, y la primera parada vale siempre `0:00:00`.

```
trip C05-I-D-B25, frequencies: 13:00:00 a 18:00:00, cada 900 s
  parada 1  llegada  0:00:00
  parada 2  llegada 00:00:51
  parada 3  llegada 00:01:22
```

Agrupar `arrival_time` por su hora produce **635 574 llegadas «a medianoche»**. Son
**851 773 filas**, el **77,5 %** de la tabla, las que no se pueden leer como reloj.

**Cómo se detecta sin saberlo de antes:** la distribución horaria es imposible. Un
sistema de transporte no concentra el 58 % de sus pasos entre las 00:00 y las 00:59.
Una distribución que no puede ser cierta es la señal.

### Trampa 2 — el relleno de ceros no es consistente

La misma expedición mezcla `0:00:00` (13 570 filas en el feed) y `00:00:51`
(1 085 147). Y entonces:

```python
'0:00:00' < '00:00:51'   # False
```

Comparando como texto, la parada 1 va **después** de la 2: el carácter `:` (58) es
mayor que `0` (48). Cualquier `sort_values("arrival_time")`, `min()`, `max()` o
`groupby` sobre el texto queda mal.

La solución es convertir a segundos antes de comparar. `lab.dates.parse_hms_seconds`
lo hace con una expresión regular que acepta de una a tres cifras de hora, y devuelve
NaN —no cero— ante lo no interpretable.

### Trampa 3 — contar expediciones subestima el servicio

Cada fila de `frequencies.txt` dice «entre `start_time` y `end_time` sale un vehículo
cada `headway_secs` segundos». El número de salidas es:

```
salidas = (end_time − start_time) ÷ headway_secs       con end_time EXCLUSIVO
```

El `end_time` exclusivo lo fija la especificación: la salida de `end_time` pertenece a
la ventana siguiente. Contarlo inclusivo suma **una salida por ventana**, y hay 14 520
ventanas.

Resultado real, para el servicio laboral:

| Forma de contar | Resultado | Error | Error relativo |
| --- | --- | --- | --- |
| Expediciones de `trips.txt` | 7 905 | −56 106 | **−87,65 %** |
| Frecuencias con fin inclusivo | 70 652 | +6 641 | **+10,37 %** |
| **Frecuencias expandidas (correcto)** | **64 011** | 0 | 0 % |

El atajo da **ocho veces menos** servicio del que hay.

**Validación independiente:** el total se calcula por dos caminos. Uno expande fila a
fila con `Index.repeat` y agrupa; el otro suma aritméticamente
`(fin − inicio) ÷ intervalo` por ventana y le añade las expediciones de horario
absoluto. Ambos dan 64 011. La comprobación queda en
`tabla.attrs["coincide"]` y la verifica una prueba automática.

### Trampa 4 — el defecto que no existe

5 991 de las 18 486 filas de `stops.txt` **no aparecen** en `stop_times.txt`. El 32 %.
La conclusión tentadora: «un tercio de las paradas está huérfano, hay un problema de
calidad».

Es falso. `stops.txt` no es una lista de paradas: es una **jerarquía de lugares**,
distinguida por `location_type`.

| `location_type` | Significado | Filas | En horarios | Huérfanas |
| --- | --- | --- | --- | --- |
| 0 | parada o andén | 12 497 | 12 495 | **2** |
| 3 | nodo genérico de pasillo | 5 031 | 0 | 0 |
| 4 | área de abordaje | 534 | 0 | 0 |
| 2 | acceso o salida | 298 | 0 | 0 |
| 1 | estación | 126 | 0 | 0 |

Solo `location_type = 0` es una parada donde sube gente. Las 5 989 restantes son
estaciones, accesos, nodos de pasillo y áreas de abordaje: **no deben** aparecer en
`stop_times`. Las paradas realmente huérfanas son **dos**, el 0,016 %.

**La lección:** antes de declarar un defecto hay que entender el modelo de datos. Un
cruce que «falla» puede estar diciendo que el cruce no correspondía. Reportar ese 32 %
como hallazgo de calidad en una evaluación cuesta más puntos que no reportar nada,
porque demuestra que no se leyó la especificación.

---

## 6. El resultado y cómo se comprueba

Total del día laboral: **64 011 salidas**. Perfil horario con dos puntas, mañana
(07:00, 4 444 buses) y tarde (17:00, 4 014 buses), y servicio nocturno reducido pero
continuo.

### Integridad referencial: los seis cruces

| Cruce | Valores | Distintos | Huérfanos |
| --- | --- | --- | --- |
| `stop_times.stop_id → stops.stop_id` | 1 098 717 | 12 495 | 0 |
| `stop_times.trip_id → trips.trip_id` | 1 098 717 | 26 137 | 0 |
| `trips.route_id → routes.route_id` | 26 137 | 425 | 0 |
| `trips.service_id → calendar.service_id` | 26 137 | 6 | 0 |
| `routes.agency_id → agency.agency_id` | 425 | 4 | 0 |
| `frequencies.trip_id → trips.trip_id` | 14 520 | 14 520 | 0 |

**Cero huérfanos en los seis.** Es un feed bien formado: el problema nunca estuvo en
la integridad, estuvo en la **semántica**. Vale la pena señalarlo, porque la intuición
dice que los datos públicos vienen sucios y aquí no es el caso. Lo que viene es
complejo, que no es lo mismo.

Las tablas completas están en [`resultados/`](resultados/), versionadas: son agregados
propios, no datos de terceros.

---

## 7. Qué quedó aprendido

Registros nuevos en la base de conocimiento:

- [`horario-relativo-vs-absoluto`](../../knowledge/horario-relativo-vs-absoluto.md) —
  cuándo una columna de hora no es una hora.
- [`relleno-de-ceros-y-orden`](../../knowledge/relleno-de-ceros-y-orden.md) — por qué
  el orden como texto rompe con relleno irregular.
- [`expandir-frecuencias`](../../knowledge/expandir-frecuencias.md) — el patrón de
  expansión y el borde inclusivo/exclusivo.
- [`defecto-que-no-existe`](../../knowledge/defecto-que-no-existe.md) — cómo
  distinguir un problema de calidad de un malentendido del modelo.

Capacidades nuevas en el núcleo, reutilizables en cualquier dominio:

- `lab.sources` — adquirir datos públicos con procedencia verificable.
- `lab.dates.parse_hms_seconds` / `seconds_to_hms` / `service_day_hour` — horarios que
  exceden el día, con relleno irregular.

Y un defecto corregido en el núcleo: `lab.metrics.safe_ratio` no difundía un escalar
sobre el índice de una serie, de modo que devolvía NaN en todas las filas salvo la
primera. Se detectó calculando los errores relativos de la tabla comparativa de este
caso.

---

## Reproducir

```powershell
uv run python scripts/fetch_data.py gtfs-red-movilidad
```

```powershell
uv run python -m cases.gtfs_red_movilidad.solution
```

El feed vigente cambia cada pocas semanas. Los números de este documento corresponden
a `GTFS_20261114_v2.zip`; con un feed posterior cambiarán las magnitudes, no las cuatro
trampas.

## Cuaderno, motores y gráfico

- [Resolución profesional paso a paso](CUADERNO.md).
- [Polars + Matplotlib](cuaderno/solucion_polars.py): perfil horario agregado.
- [R + ggplot2](cuaderno/solucion.R): contraste y gráfico equivalente.
- [Figura publicada](cuaderno/svg/paso-09.svg).
