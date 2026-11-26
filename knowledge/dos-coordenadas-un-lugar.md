---
id: dos-coordenadas-un-lugar
tipo: leccion
titulo: Un dato redundante permite validar el archivo contra sí mismo
etiquetas: [validacion-independiente, calidad-datos, gobernanza-datos, datos-reales, geoespacial]
fuente: lab/geo.py, cases/bip_lugares_carga/solution.py
relacionados: [defecto-que-no-existe, clave-que-no-es-clave, cobertura-de-un-indicador]
---

**La situación.** Un archivo público trae la ubicación de cada local **dos veces**: en
coordenadas UTM (`ESTE`, `NORTE`) y en geográficas (`LATITUD`, `LONGITUD`). La lectura
perezosa es «hay columnas de sobra». La lectura útil es: **tengo una validación gratis
que no necesita ninguna fuente externa**.

Se convierte una representación a la otra y se mide la distancia. Sobre 1 928 filas:

| Desvío | Filas | Proporción | Qué es |
| --- | --- | --- | --- |
| menos de 5 m | 109 | 5,7 % | las dos columnas coinciden |
| 5 a 50 m | 37 | 1,9 % | zona intermedia |
| **50 a 80 m** | **1 779** | **92,3 %** | desplazamiento sistemático |
| 80 a 200 m | 0 | 0 % | — |
| **más de 200 m** | **3** | 0,16 % | **errores de registro** |

**La distribución es bimodal, y eso es la clave de la interpretación.** Dos grupos
nítidos —uno en torno a 0 m y otro en torno a 61 m— con **nada en medio**, más tres
valores sueltos a kilómetros de distancia. En uno de los archivos el desplazamiento es
de 60,99 m con desviación típica de **0,28 m**: constante.

### Tres conclusiones distintas, que no hay que mezclar

**1. El desplazamiento constante no es un error de registro.** Un desvío idéntico en
miles de filas es una **diferencia de datum geodésico** entre las dos columnas: se
calcularon sobre elipsoides o marcos de referencia distintos. Reportar 1 779 errores de
coordenada sería un falso positivo masivo.

**2. Que haya 109 filas sin desplazamiento es el hallazgo incómodo.** Si el desvío
fuera solo un datum, sería uniforme. Que el 5,7 % coincida significa que **las dos
columnas no se produjeron con un único proceso consistente**: el archivo mezcla al
menos dos procedencias para el mismo campo. Eso es gobernanza de datos, no limpieza. No
se arregla; se reporta y se pregunta al publicador.

**3. Tres filas son errores reales.** Desvíos de 4 623 m, 10 087 m y 10 272 m: las dos
coordenadas apuntan a lugares distintos de la ciudad. La validación cruzada es **lo
único que los encuentra**.

### Por qué el umbral no es arbitrario

El grupo sistemático termina en 80 m y los errores empiezan en 4 623 m: hay un orden de
magnitud de separación y el tramo intermedio está vacío. Cualquier umbral entre 100 y
1 000 m da el mismo resultado. **Que el resultado no dependa del umbral es la señal de
que el criterio es correcto**; si moverlo un 20 % cambiara el número de hallazgos, el
criterio estaría mal elegido y habría que decirlo.

### El patrón, más allá de la geografía

La redundancia dentro de una sola fuente permite validarla sin salir de ella. Aparece
en todas partes:

| Dato redundante | Validación |
| --- | --- |
| Un total y sus partes | la suma de las partes debe dar el total |
| Un monto en dos monedas | el cociente debe ser el tipo de cambio de la fecha |
| Una fecha y su número de semana | deben corresponder |
| Un RUT y su dígito verificador | el dígito se recalcula |
| Un código postal y una comuna | deben ser compatibles |
| Un porcentaje y su numerador y denominador | el cociente debe reproducirlo |

**La pregunta que hay que hacerse ante cualquier fuente nueva:** ¿hay algo aquí que
esté dicho dos veces? Si lo hay, eso es una prueba gratis. Y conviene hacerla antes de
calcular nada, porque es la más barata de todas las validaciones disponibles.
