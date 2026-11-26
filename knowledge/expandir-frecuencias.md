---
id: expandir-frecuencias
tipo: patron
titulo: Expandir una ventana con cadencia a sus eventos reales
etiquetas: [agregacion-indicadores, pandas, gtfs, datos-reales, denominadores]
fuente: cases/gtfs_red_movilidad/solution.py
relacionados: [horario-relativo-vs-absoluto, defecto-que-no-existe, cobertura-de-un-indicador]
---

**El problema.** Un dato declara «entre las 13:00 y las 18:00 sale un vehículo cada 15
minutos» en **una sola fila**. Contar filas da 1; la realidad son 20 salidas.

Cuando parte del dato viene así y parte como eventos individuales, contar filas
subestima el total. En el feed de transporte de Santiago, el conteo ingenuo de
expediciones daba 7 905 para un día laboral y el valor correcto es **64 011**: un
error del **−87,65 %**, un factor de ocho.

**La fórmula y su borde.**

```
salidas = (fin − inicio) ÷ cadencia          con fin EXCLUSIVO
```

El borde decide más de lo que parece. Con `fin` inclusivo se suma **una salida por
ventana**; sobre 14 520 ventanas eso son 6 641 salidas de más, un **+10,37 %**. La
especificación GTFS fija `end_time` exclusivo: la salida de esa hora pertenece a la
ventana siguiente. Si el dato no lo declara, hay que preguntarlo, no suponerlo.

**La implementación vectorizada.** `Index.repeat` es la forma de producir n filas por
fila sin bucle:

```python
v["salidas"] = ((v["fin_s"] - v["inicio_s"]) // v["cadencia_s"]).clip(lower=0).astype(int)
utiles = v.loc[v["salidas"].gt(0)]
exp = utiles.loc[utiles.index.repeat(utiles["salidas"])].copy()
exp["k"] = exp.groupby(level=0).cumcount()          # 0, 1, 2, … dentro de su ventana
exp["evento_s"] = exp["inicio_s"] + exp["k"] * exp["cadencia_s"]
```

`groupby(level=0).cumcount()` numera las repeticiones de cada fila original, que es
justo la posición del evento dentro de su ventana. Con 14 520 ventanas y 142 366
eventos, la versión vectorizada es dos órdenes de magnitud más rápida que el bucle, y
—más importante— cabe en seis líneas legibles.

**La validación que hay que hacer siempre.** La expansión se comprueba contra la
aritmética directa, que no comparte código con ella:

```python
assert exp.groupby("ventana").size().sum() == v["salidas"].sum()
```

Si no coinciden, el error está en el borde: ventanas con cadencia cero, fin anterior al
inicio, o un `clip` mal puesto. Esas filas se **excluyen y se informan**, nunca se
descartan en silencio.

**Dónde más aparece.** Cualquier dato que declare una regla en lugar de sus
instancias: turnos («lunes a viernes, cada 8 horas»), cuotas de pago («12 cuotas
mensuales desde marzo»), mantenimientos programados («cada 5 000 km»), reservas
periódicas. El patrón es siempre el mismo: **una fila de regla, n filas de realidad**,
y el conteo de filas de regla no es un indicador de volumen.
