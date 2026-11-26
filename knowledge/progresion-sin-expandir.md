---
id: progresion-sin-expandir
tipo: formula
titulo: Contar eventos periódicos en una ventana no necesita generar los eventos
etiquetas: [pandas, fechas-horarios, ingenieria-datos, formulas, gtfs]
fuente: cases/carga_nocturna/solution.py
relacionados: [expandir-frecuencias, atajo-verosimil, horario-relativo-vs-absoluto]
---

**El problema.** Un evento se repite con período fijo: «entre las 06:00 y las 09:00
sale un bus cada 10 minutos». Hay 14 520 declaraciones así, que suman 142 366 salidas,
y cada salida llega a las paradas de su recorrido con un desplazamiento propio. La
pregunta es cuántas llegadas caen entre las 00:00 y las 05:00, por parada.

**El camino natural, y por qué no cabe.** Expandir: generar las 142 366 salidas y
unirlas a las 1 098 717 filas de paradas por recorrido. El producto son cientos de
millones de filas, para responder una pregunta de sí o no por parada.

Expandir es correcto, y en [[expandir-frecuencias]] es lo que hay que hacer, porque
allí el resultado **son** las salidas. Aquí el resultado es un conteo, y el conteo tiene
fórmula.

**La fórmula.** Las llegadas de una ventana a una parada son una progresión aritmética:

```
llegada(k) = inicio_de_ventana + k · intervalo + desplazamiento_de_la_parada
           = primero + k · intervalo,     con k en [0, salidas)
```

Cuántos términos caen en `[a, b)`:

```
k_desde = ceil((a − primero) / intervalo)        acotado a [0, salidas]
k_hasta = ceil((b − primero) / intervalo)        acotado a [0, salidas]
cuenta  = max(k_hasta − k_desde, 0)
```

```python
def llegadas_en(primero, intervalo, salidas, desde, hasta):
    k_desde = np.clip(np.ceil((desde - primero) / intervalo), 0, salidas)
    k_hasta = np.clip(np.ceil((hasta - primero) / intervalo), 0, salidas)
    return np.maximum(k_hasta - k_desde, 0)
```

Vectorizado sobre las columnas, es exacto y no materializa nada.

**Los detalles que hay que acertar.**

- **`ceil` y no `floor`.** El primer `k` que alcanza `a` es `ceil((a − primero)/h)`;
  con `floor` se incluye un término anterior a la ventana.
- **El acotado a `[0, salidas]`**, no a `[0, salidas − 1]`. `k_hasta` es un límite
  superior exclusivo, de modo que puede valer `salidas`.
- **`max(…, 0)`** para el caso en que la ventana queda entera fuera: sin él aparecen
  conteos negativos que luego suman mal.
- **El fin de la ventana es exclusivo**, igual que el `end_time` de GTFS.

**Cómo se verifica.** Con casos que se cuentan a mano, y los bordes son obligatorios:

| primero | intervalo | salidas | ventana | esperado |
| --- | --- | --- | --- | --- |
| 0 | 1800 | 2 | `[0, 18000)` | 2 |
| 0 | 1800 | 2 | `[0, 1800)` | 1 |
| 0 | 1800 | 2 | `[1800, 18000)` | 1 |
| 85 200 | 1800 | 2 | `[0, 18000)` | 0 |
| 85 200 | 1800 | 2 | `[86400, 104400)` | 1 |

La cuarta y la quinta fila son el mismo bus —sale 23:40, llega 00:10— visto desde los
dos intervalos de segundos de servicio que son la misma hora de reloj.

**Dónde más sirve.** Turnos rotativos, ciclos de facturación, mantenimientos
programados, ventanas de despliegue, intereses devengados, vencimientos periódicos:
cualquier serie con período fijo donde la pregunta sea «cuántos» o «hay alguno» y no
«cuáles».

**La regla.** Antes de expandir una serie periódica, preguntarse si el resultado son
los eventos o una propiedad de ellos. Si es una propiedad, hay fórmula.
