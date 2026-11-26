---
id: puntos-porcentuales-vs-porcentaje
tipo: definicion
titulo: Puntos porcentuales frente a variación porcentual
etiquetas: [indicadores, comunicacion-resultados, errores-frecuentes]
fuente: lab/metrics.py
relacionados: [tasa-ponderada-vs-promedio-simple, cobertura-de-un-indicador]
---

Si el cumplimiento pasa de 40 % a 50 %, hay dos formas correctas de decirlo y una
incorrecta.

- **Diferencia absoluta:** subió **10 puntos porcentuales** (`50 − 40`).
- **Variación relativa:** subió **25 %** (`100 × (50 − 40) / 40`).
- **Incorrecto:** «subió 10 %». Esa frase significa la variación relativa y conduce a
  49 % − 40 % · 1,10 = 44 %, que no es el dato.

**Regla de escritura.** La resta de dos porcentajes se expresa en **puntos
porcentuales** (pp). El cociente de dos porcentajes se expresa en **por ciento**.

**Por qué importa en un entregable.** Un informe que dice «el cumplimiento del
operador A es 10 % mayor que el del operador B» es ambiguo: con 40 % y 50 % puede
significar 10 pp o 25 %. Quien decide actúa sobre una magnitud equivocada.

**En el laboratorio.** `lab.metrics.compare_rates` devuelve `difference`, documentada
como diferencia en puntos porcentuales. Al construir tablas de indicadores con
`indicator_table`, la unidad de una diferencia de tasas se declara como `pp` y no
como `%`.
