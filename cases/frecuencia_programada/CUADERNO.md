# P12-P13 · ICF y distribución de la frecuencia programada

◀ [P11 · Calendario](../calendario_medicion/CUADERNO.md) · [Todos los cuadernos](../../docs/cuadernos.md) · [P14-P15 · Evolución GTFS](../evolucion_gtfs/CUADERNO.md) ▶

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/blob/main/cases/frecuencia_programada/cuaderno/colab.ipynb) — corre los pasos sin instalar nada: el cuaderno clona el repositorio y descarga los datos del portal.

> **¿Qué parte del ICF se puede calcular con GTFS y cómo se distribuye la frecuencia programada?**

## 1 · El problema

El ICF oficial parece una razón simple, pero su numerador y denominador son mediciones
GPS. El GTFS solo contiene el programa. Confundir ambos convierte una promesa de oferta
en una medición de cumplimiento inexistente. El mismo archivo sí permite contestar P13:
cómo se distribuyen los intervalos programados y qué servicios tienen mayor espera.

**Los datos.** frequencies.txt, trips.txt y routes.txt del GTFS vigente, más la definición oficial del ICF.

![El flujo del problema](cuaderno/svg/flujo.svg)

## 2 · La solución que se va a aplicar

Se validan las ventanas, se calculan sus salidas con fin exclusivo y se construye una
matriz de alcance del ICF. La distribución se resume con percentiles y tres unidades de
análisis. La punta mañana se filtra por intersección temporal, no por hora de inicio.

![El recorrido](cuaderno/svg/mapa.svg)

8 pasos. Cada uno trae el código de **Python**, la salida que devuelve de verdad, y la **fórmula de Excel** equivalente dibujada en su hoja. 8 traen además la trampa de hacerlo de la forma obvia.

| # | Paso | Trampa |
| --- | --- | --- |
| 1 | [Leer solo tres tablas](#paso-1) | sí |
| 2 | [Validar las ventanas](#paso-2) | sí |
| 3 | [Separar programa de observación](#paso-3) | sí |
| 4 | [Conservar el ICF como no calculable](#paso-4) | sí |
| 5 | [Describir la distribución](#paso-5) | sí |
| 6 | [Cambiar la unidad de análisis](#paso-6) | sí |
| 7 | [Filtrar la punta por intersección](#paso-7) | sí |
| 8 | [Publicar una conclusión proporcional](#paso-8) | sí |

### Para trabajar

| Archivo | Qué es |
| --- | --- |
| [`P12-P13-caso-completo.zip`](cuaderno/P12-P13-caso-completo.zip) | **todo el caso en un ZIP**: el cuaderno, el script, el libro de Excel y las figuras |
| [`pasos.py`](cuaderno/pasos.py) | los 8 pasos seguidos. Se corre y muestra cada salida |
| [`practica.xlsx`](cuaderno/practica.xlsx) | las fórmulas y **el resultado que deben dar**, para corregirse solo. Se abre igual en Google Sheets |
| [`colab.ipynb`](cuaderno/colab.ipynb) | el cuaderno **ejecutable en Colab**: clona, descarga los datos del portal y corre los 8 pasos |

---

## 3 · Los pasos

<a id="paso-1"></a>

### Paso 1 · Leer solo tres tablas

El ICF programado no necesita el archivo de 1,1 millones de horarios.

#### Python

```python
tablas = frecuencia.cargar()
{k: v.shape for k, v in tablas.items()}
```

```
{'frequencies': (14520, 5), 'trips': (26137, 4), 'routes': (425, 3)}
```

#### Excel

Power Query: cargar `frequencies`, `trips` y `routes`; no importar `stop_times`.

> **La trampa.** Cargar por costumbre la tabla grande duplica memoria sin aportar una columna al cálculo.

[↑ volver al recorrido](#2--la-solución-que-se-va-a-aplicar)

---

<a id="paso-2"></a>

### Paso 2 · Validar las ventanas

Inicio, fin e intervalo se tipan antes de resumir.

#### Python

```python
ventanas = frecuencia.ventanas_programadas(tablas)
ventanas[['valida','salidas_programadas']].agg(['count','sum'])
```

| valida | salidas_programadas |
| --- | --- |
| 14520 | 14520 |
| 14520 | 142366 |
*2 filas × 2 columnas.*

#### Excel

Columnas auxiliares para segundos, duración, intervalo positivo y fin posterior al inicio.

> **La trampa.** Una ventana inválida no se descarta sin contarla.

[↑ volver al recorrido](#2--la-solución-que-se-va-a-aplicar)

---

<a id="paso-3"></a>

### Paso 3 · Separar programa de observación

La matriz impide presentar el programa como ICF.

#### Python

```python
resultados = frecuencia.analizar()
resultados['alcance_icf']
```

| componente | calculable_con_gtfs | valor | unidad |
| --- | --- | --- | --- |
| programa de frecuencia | sí | 14520 | ventanas GTFS |
| intervalo objetivo | sí | 14520 | ventanas |
| salidas programadas | sí | 142366 | salidas |
| mediciones GPS realizadas | NO |  | mediciones |
| mediciones que cumplen | NO |  | mediciones |
| ICF oficial | NO |  | % |
*6 filas × 4 columnas.*

#### Excel

Tabla de control con componente, disponibilidad, valor y unidad.

> **La trampa.** 142 366 salidas programadas no son 142 366 mediciones GPS.

[↑ volver al recorrido](#2--la-solución-que-se-va-a-aplicar)

---

<a id="paso-4"></a>

### Paso 4 · Conservar el ICF como no calculable

La ausencia de GPS es un resultado de alcance, no un error de ejecución.

#### Python

```python
resultados['alcance_icf'].query("calculable_con_gtfs == 'NO'")
```

| componente | calculable_con_gtfs | valor | unidad |
| --- | --- | --- | --- |
| mediciones GPS realizadas | NO |  | mediciones |
| mediciones que cumplen | NO |  | mediciones |
| ICF oficial | NO |  | % |
*3 filas × 4 columnas.*

#### Excel

Dejar numerador, denominador e ICF en blanco y acompañarlos con la causa.

> **La trampa.** Rellenar con cero produciría un ICF de 0 % que los datos jamás observaron.

[↑ volver al recorrido](#2--la-solución-que-se-va-a-aplicar)

---

<a id="paso-5"></a>

### Paso 5 · Describir la distribución

Percentiles muestran la asimetría entre 3,10 y 330 minutos.

#### Python

```python
resultados['distribucion']
```

| estadistico | intervalo_min | unidad |
| --- | --- | --- |
| mínimo | 3.1 | minutos entre salidas |
| P10 | 9.0 | minutos entre salidas |
| P25 | 12.0 | minutos entre salidas |
| P50 | 15.0 | minutos entre salidas |
| P75 | 20.0 | minutos entre salidas |
| P90 | 30.0 | minutos entre salidas |
| P95 | 42.85 | minutos entre salidas |
| máximo | 330.0 | minutos entre salidas |
| media | 21.17 | minutos entre salidas |
*9 filas × 3 columnas.*

#### Excel

![La hoja](cuaderno/svg/paso-05-excel.svg)

`PERCENTIL.INC` sobre `headway_secs/60`.

Debe dar: **15 minutos**

**En Google Sheets:** la misma fórmula, sin cambios.

> **La trampa.** La media de 21,17 minutos no representa la ventana típica de 15.

[↑ volver al recorrido](#2--la-solución-que-se-va-a-aplicar)

---

<a id="paso-6"></a>

### Paso 6 · Cambiar la unidad de análisis

Ventana, servicio y salida responden preguntas distintas.

#### Python

```python
resultados['ponderaciones']
```

| unidad_de_analisis | intervalo_tipico_min | observaciones |
| --- | --- | --- |
| ventana publicada | 15.0 | 14520 |
| servicio (mediana de sus ventanas) | 15.0 | 417 |
| salida programada | 13.03 | 142366 |
*3 filas × 3 columnas.*

#### Excel

Tres tablas dinámicas o tres ponderaciones explícitas.

> **La trampa.** Promediar servicios sin declarar peso da el mismo voto a uno diario y a uno intensivo.

[↑ volver al recorrido](#2--la-solución-que-se-va-a-aplicar)

---

<a id="paso-7"></a>

### Paso 7 · Filtrar la punta por intersección

Entra toda ventana que toca 08:00–09:00.

#### Python

```python
resultados['punta_manana'].head(15)
```

| route_short_name | direction_id | ventanas | intervalo_mediano_min | intervalo_maximo_min | salidas_programadas |
| --- | --- | --- | --- | --- | --- |
| B30n | 0 | 2 | 240.0 | 330.0 | 2 |
| B31n | 1 | 2 | 240.0 | 330.0 | 2 |
| F30n | 0 | 2 | 240.0 | 330.0 | 2 |
| G37 | 0 | 3 | 150.0 | 165.0 | 4 |
| F30n | 1 | 2 | 120.0 | 165.0 | 4 |
| G37 | 1 | 3 | 110.0 | 150.0 | 5 |
| J22 | 1 | 3 | 110.0 | 150.0 | 5 |
| 282 | 0 | 2 | 92.5 | 110.0 | 5 |
| 206c | 0 | 1 | 90.0 | 90.0 | 1 |
| 210e | 0 | 1 | 90.0 | 90.0 | 1 |
| 320c | 0 | 1 | 90.0 | 90.0 | 1 |
| 320c | 1 | 1 | 90.0 | 90.0 | 1 |
| J22 | 0 | 3 | 90.0 | 110.0 | 6 |
| 282 | 1 | 3 | 50.0 | 110.0 | 8 |
| G46 | 0 | 3 | 50.0 | 55.0 | 11 |
*15 filas × 6 columnas.*

#### Excel

Condición: inicio < 09:00 Y fin > 08:00; agrupar por servicio y sentido.

> **La trampa.** Filtrar solo `start_time` pierde ventanas que comenzaron antes de las 08:00.

[↑ volver al recorrido](#2--la-solución-que-se-va-a-aplicar)

---

<a id="paso-8"></a>

### Paso 8 · Publicar una conclusión proporcional

Se distingue frecuencia larga de incumplimiento.

#### Python

```python
resultados['ventanas_invalidas']
```

| trip_id | start_time | end_time | headway_secs |
| --- | --- | --- | --- |
*0 filas × 4 columnas.*

#### Excel

Mostrar el recuento de inválidas junto a la tabla final.

> **La trampa.** Un intervalo programado largo puede ser diseño de servicio; no demuestra falla operacional.

[↑ volver al recorrido](#2--la-solución-que-se-va-a-aplicar)

---

## 4 · El resultado

El GTFS permite construir 142 366 salidas programadas y describir sus intervalos. No contiene mediciones GPS: el ICF oficial permanece no calculable.

## 5 · Qué queda aprendido

1. Programa no es operación observada.
2. La unidad de análisis cambia el intervalo típico.
3. Las ventanas se filtran por intersección temporal.
4. Un vacío metodológico no se rellena con cero.

## Reproducir

```powershell
python -m cases.frecuencia_programada.solution
```

## Seguir

Lo que este caso toca y se trata a fondo en otro sitio:

- [Resultados auditables](README.md)
- [Definición oficial del ICF](../../docs/indicadores-oficiales-transporte.md)

◀ [P11 · Calendario](../calendario_medicion/CUADERNO.md) · [Todos los cuadernos](../../docs/cuadernos.md) · [P14-P15 · Evolución GTFS](../evolucion_gtfs/CUADERNO.md) ▶
