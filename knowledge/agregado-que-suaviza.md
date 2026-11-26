---
id: agregado-que-suaviza
tipo: error
titulo: Un agregado que reduce varias filas a una suaviza el error en lugar de mostrarlo
etiquetas: [errores-frecuentes, calidad-datos, pandas, geoespacial, indicadores]
fuente: cases/correspondencia_metro/solution.py
relacionados: [grano-antes-de-cruzar, punto-ciego-del-control, unidad-de-la-decision, normalizar-antes-de-agrupar]
---

**El caso.** Para comparar dos inventarios hay que llevar el más fino al grano del otro.
Un archivo tiene dos filas por estación —una por línea— y el otro una sola. Lo natural:

```python
por_estacion = filas.groupby("estacion").agg(lat=("lat","median"), lon=("lon","median"))
```

Las dos filas de Plaza de Armas están separadas **26,2 km**: una correcta y la otra con
la latitud equivocada. Su mediana cae a **13,1 km de cada una**, en un punto donde no hay
ninguna estación. Y el desvío contra la otra fuente pasa de 26,2 km a 13,1: **la mitad
exacta**.

El agregado no corrigió nada. Dividió el error por dos y lo hizo ver más plausible.

**Por qué la mediana no salva.** La mediana es robusta a valores atípicos **cuando hay
suficientes observaciones**. Con dos, la mediana es el promedio, y con tres es la del
medio: en grupos pequeños ninguna medida de centro resiste un error grande. Y los grupos
de una conciliación son casi siempre de dos o tres filas.

```python
np.median([-33.4371, -33.2018])   # -33.31945: ni una ni otra
```

**Lo que hay que hacer.** No es dejar de agregar: es **publicar la dispersión de lo que
se reemplazó**.

```python
a_la_mediana = haversine_km(grupo["lat"], grupo["lon"], mediana_lat, mediana_lon) * 1000
dispersion_interna_m = float(a_la_mediana.max())
```

Y con eso, tres columnas en lugar de una:

| Columna | Qué dice |
| --- | --- |
| `desvio_m` | el desvío usando el agregado · 13 147,7 m |
| `desvio_peor_fila_m` | el desvío usando la peor fila · 26 243,3 m |
| `dispersion_interna_m` | lo que el agregado esconde · 13 095,6 m |

La tercera columna es la que importa, y es la que nadie calcula.

**La regla general.** Todo `mean`, `median`, `first`, `last` o `mode` que reduzca varias
filas a una está afirmando que las filas eran intercambiables. Esa afirmación es
comprobable y casi nunca se comprueba:

```python
tabla = datos.groupby(clave).agg(
    valor=("valor", "median"),
    dispersion=("valor", lambda s: s.max() - s.min()),   # la columna que falta
    filas=("valor", "size"),
)
```

Si la dispersión es grande, el agregado no representa al grupo: **el grupo está mal
formado o los datos se contradicen**, y las dos cosas son hallazgos.

**El caso peor, el de `first`.** `first` no suaviza: elige al azar según el orden de las
filas. Con las dos filas de Plaza de Armas, `first` devuelve la correcta o la equivocada
según cómo se haya ordenado antes, de modo que el resultado cambia sin que nada en el
código haya cambiado. Es peor que la mediana porque no es reproducible.

**Dónde más aparece.** Precios de un producto en varias sucursales, fechas de un mismo
trámite en varios sistemas, montos de un contrato en varias versiones, edades de una
persona en varios registros. Cada vez que el `groupby` reduce, hay una afirmación de
intercambiabilidad esperando que alguien la mida.
