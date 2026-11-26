---
id: valor-p-que-significa
tipo: definicion
titulo: Qué es y qué no es un valor p
etiquetas: [estadistica, inferencia-estadistica, errores-frecuentes]
fuente: lab/stats.py
relacionados: [correlacion-no-es-causalidad, intervalo-de-confianza]
---

**Definición.** El valor p es la probabilidad de observar un estadístico de prueba al
menos tan extremo como el observado, **suponiendo que la hipótesis nula es cierta**.

```
p = P( |T| ≥ |t_observado|  |  H₀ cierta )
```

**Lo que no es** —y son los cuatro errores más frecuentes:

1. **No** es la probabilidad de que la hipótesis nula sea cierta. Esa probabilidad
   requiere un marco bayesiano y una distribución previa.
2. **No** es la probabilidad de que el resultado se deba al azar.
3. **No** mide el tamaño del efecto. Con n grande, una diferencia irrelevante
   produce un p diminuto; con n pequeño, una diferencia importante puede no alcanzar
   significancia.
4. **No** convierte el umbral 0,05 en una verdad. Es una convención; `p = 0,049` y
   `p = 0,051` describen prácticamente la misma evidencia.

**Qué informar siempre junto al valor p.**

- La hipótesis nula enunciada en palabras.
- El estadístico y sus grados de libertad.
- El **tamaño del efecto** (d de Cohen, V de Cramér, r) y su intervalo.
- El tamaño de muestra.

`lab.stats.TestResult` obliga a lo primero y lo segundo, y reporta el tamaño de
efecto en las pruebas donde está definido. `results_frame` entrega todo en una tabla
lista para el informe.

**Formulación correcta.** «La diferencia de duración media entre operadores es de
6,2 minutos (t de Welch = 4,13; gl = 128; p = 0,00006; d = 0,73). La hipótesis nula
de igualdad de medias resulta poco compatible con los datos.»
