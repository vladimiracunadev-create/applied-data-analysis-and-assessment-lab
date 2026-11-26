---
id: sesgo-con-eje
tipo: error
titulo: La distancia euclídea sobre grados no es una aproximación: es un sesgo con eje
etiquetas: [geoespacial, errores-frecuentes, estadistica, pandas, datos-reales]
fuente: lab/geo.py
relacionados: [cruce-sin-clave, unidad-de-la-decision, dos-coordenadas-un-lugar]
---

**El atajo.** Tratar las coordenadas como un plano: distancia euclídea entre pares de
grados, multiplicada por los 111,32 km que mide un grado de meridiano.

```python
# El atajo que parece inofensivo
distancia_km = np.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) * 111.32
```

**Por qué está mal.** Un grado de latitud mide lo mismo en todas partes. Un grado de
longitud mide 111,3 km en el ecuador y **cero** en el polo: los meridianos convergen. A
la latitud de Santiago (−33,45°) mide 92,8 km, de modo que el atajo estira la
componente este-oeste un 20 %.

| Desplazamiento real | Distancia verdadera | El atajo |
| --- | --- | --- |
| 1 km al **este** | 1 000 m | **1 200 m** |
| 1 km al **norte** | 1 000 m | 1 001 m |

**Lo que hace que sea un sesgo y no un ruido.** El error **tiene eje**. No es una
imprecisión que fluctúe: toda componente este-oeste sale de más, siempre, en la misma
proporción. Sobre 12 497 paradas reales hubo **cero subestimaciones**. Un error con eje
no se cancela al promediar, de modo que el agregado hereda el sesgo completo.

**La comprobación, en dos líneas:**

```python
from lab.geo import grados_por_km
grados_lat, grados_lon = grados_por_km(-33.45)   # (0.008993, 0.010779)
# Si los dos valores difieren, la euclídea sobre grados mide mal en ese lugar.
```

La razón entre los dos es el factor de error en el eje este-oeste: 1,199 en Santiago,
alrededor de 1,4 en Londres, 1,00 en Quito. Cerca del ecuador el atajo es casi inocuo,
y de ahí que sobreviva en ejemplos y tutoriales escritos en otras latitudes.

**La corrección.** Haversine, que son cuatro líneas y no necesita dependencias:

```
a = sin²(Δφ/2) + cos φ₁ · cos φ₂ · sin²(Δλ/2)
d = 2 · R · arcsin(√a)
```

**Dos errores emparentados, por si aparecen.**

- **Promediar coordenadas** para obtener un centroide tiene el mismo problema, y además
  falla cruzando el antimeridiano.
- **Un índice espacial sobre grados** hereda el sesgo entero: el índice es correcto, la
  métrica no. Hay que proyectar antes de indexar.

**Regla general.** Antes de medir una distancia, preguntar en qué unidades está el
espacio. Los grados no son metros, y no son metros de forma **distinta según la
dirección**. Ver [[unidad-de-la-decision]] para por qué 17 metros de error mediano no
describen la gravedad de este defecto.
