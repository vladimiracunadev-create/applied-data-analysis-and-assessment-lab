---
id: unidad-de-la-decision
tipo: patron
titulo: El error de un método se mide en la unidad de la decisión, no en la del cálculo
etiquetas: [pensamiento-critico, comunicacion-resultados, calidad-datos, estadistica, indicadores]
fuente: cases/cobertura_de_carga/solution.py
relacionados: [sesgo-con-eje, cruce-sin-clave, julianday-precision, denominador-es-una-decision]
---

**El patrón.** Un método aproximado se evalúa contra el correcto. La forma habitual de
reportar la diferencia es en la unidad del cálculo: metros, segundos, pesos, puntos
porcentuales. Esa cifra casi siempre **subestima la gravedad**, porque el usuario del
resultado no consume metros: consume una decisión.

**Los dos informes del mismo defecto.**

| En la unidad del cálculo | En la unidad de la decisión |
| --- | --- |
| Error mediano de 17,2 m | **574 paradas** cambian de clase |
| Error mediano del 9,4 % | **814 paradas** reciben otro local como el más cercano |

Diecisiete metros suenan a redondeo. Quinientas setenta y cuatro paradas que pasan de
«tiene dónde cargar cerca» a «no tiene» es un informe distinto, y es el mismo defecto.

**Por qué la diferencia es tan grande.** Porque entre el cálculo y la decisión hay
siempre un **umbral**, y un umbral amplifica los errores de los valores que caen cerca
de él. El error mediano describe toda la distribución; lo que importa es el error de
los casos que estaban al borde. La proporción de casos al borde no se deduce del error
medio: hay que contarla.

**Dos ejemplos del mismo laboratorio.**

- Una diferencia de precisión de punto flotante de 0,000000029 minutos en el cálculo de
  una duración movió un indicador de puntualidad **varios puntos porcentuales**, porque
  invertía la comparación en los empates exactos contra la meta. La media coincidía
  hasta el octavo decimal. Ver [[julianday-precision]].
- Un error de cobertura del 9,4 % en una distancia movió 4,6 puntos de un indicador y
  cambió de clase a 574 de 12 497 registros.

**La regla práctica.** Al comparar dos métodos, reportar tres cosas y no una:

1. el error en la unidad del cálculo —sirve para diagnosticar;
2. **cuántos registros cambian de clase** respecto de la decisión que el indicador
   alimenta;
3. **el signo del error**, porque un error con signo constante es un sesgo y no se
   cancela al agregar. Ver [[sesgo-con-eje]].

**El corolario para comunicar.** Si no se sabe qué decisión alimenta el número, no se
sabe en qué unidad reportar el error. Preguntar por la decisión es parte de medir la
calidad, no un paso posterior.
