---
id: acuerdo-multimotor-no-es-verdad
tipo: leccion
titulo: El acuerdo entre motores descarta errores compartidos, no demuestra la verdad
etiquetas: [validacion-independiente, pandas, polars, r, sql, reproducibilidad]
fuente: tests/test_multiengine.py, solutions/polars_reference.py, solutions/r_reference.R
relacionados: [julianday-precision, punto-ciego-del-control]
---

**Hallazgo.** Pandas, Polars, R base y SQL pueden producir las mismas siete tablas a
partir de los mismos CSV aunque resuelvan tipos, cruces, fechas y agregaciones con APIs
y runtimes distintos. Ese acuerdo elimina muchas causas probables de error de
implementación; no demuestra que la regla de negocio sea correcta.

**Condición para que el acuerdo sea informativo.** Cada vía debe partir de los datos
crudos y aplicar las reglas por su cuenta. Convertir un DataFrame de Pandas a Polars o
leer en R un CSV ya agregado solo verifica transporte de datos: hereda los mismos
filtros, denominadores y errores conceptuales.

**Lo que todavía puede estar mal.** Las cuatro implementaciones pueden compartir una
especificación equivocada: excluir el grupo incorrecto, usar un denominador que no
representa la pregunta o confundir programa con observación. Por eso las pruebas de
acuerdo complementan —no reemplazan— el diccionario, los casos mínimos calculados a
mano y la revisión de los límites del dato.

**Regla reutilizable.** Una nueva implementación aporta evidencia cuando cambia al
menos una semántica relevante —runtime, sistema de tipos, motor de cruce o modelo de
ejecución— y cuando el contrato comparado fija claves, columnas, unidades, nulos y
tolerancia. Más motores con el mismo malentendido no producen más verdad.
