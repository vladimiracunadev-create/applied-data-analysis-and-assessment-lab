---
id: tasa-ponderada-vs-promedio-simple
tipo: concepto
titulo: Tasa ponderada frente a promedio simple de porcentajes
etiquetas: [estadistica, indicadores, denominadores, errores-frecuentes]
fuente: lab/metrics.py, cases/education/case.json
relacionados: [denominador-cero, puntos-porcentuales-vs-porcentaje]
---

Dos formas de resumir un conjunto de razones dan números distintos, y solo una
describe al conjunto.

**Tasa ponderada.** `r = 100 · Σaᵢ / Σbᵢ`. Suma los numeradores, suma los
denominadores y divide. Cada observación pesa según su tamaño. Es la tasa del
conjunto: si 91 de 102 viajes se realizaron, la tasa del conjunto es 89,2 %.

**Promedio simple de tasas.** `r̄ = (1/n) · Σ (100 · aᵢ / bᵢ)`. Calcula la tasa de
cada unidad y promedia. Cada unidad pesa igual, sin importar su tamaño. Un recorrido
con 2 viajes influye tanto como uno con 10 000.

Cuándo usar cada uno:

- La **ponderada** responde «¿cómo le fue al sistema?».
- El **promedio simple** responde «¿cómo le fue a la unidad típica?».

Ninguno es incorrecto; lo incorrecto es informar uno y describirlo como el otro. En
una evaluación técnica, calcular ambos y explicar la diferencia vale más que elegir
bien por azar. `lab.metrics.compare_rates` devuelve los dos y su diferencia.

**Error habitual.** Promediar los porcentajes diarios de cumplimiento para obtener
el cumplimiento del mes. El resultado da peso igual a un domingo con 3 viajes
programados y a un martes con 300.
