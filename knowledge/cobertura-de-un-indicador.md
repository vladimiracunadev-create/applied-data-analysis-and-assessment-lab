---
id: cobertura-de-un-indicador
tipo: metodologia
titulo: Informar la cobertura junto con el indicador
etiquetas: [calidad-datos, indicadores, comunicacion-resultados, metodologia]
fuente: lab/metrics.py, lab/dates.py
relacionados: [vacio-no-es-cero, denominador-cero, hecho-inferencia-hipotesis]
---

La **cobertura** de un indicador es la proporción de la población objetivo que
realmente aportó dato al cálculo:

```
cobertura = 100 · registros usados / registros que debían usarse     [%]
```

Dos indicadores con el mismo valor y distinta cobertura no son comparables. «Duración
media 52,1 minutos» con cobertura del 99 % describe el servicio; el mismo número con
cobertura del 41 % describe la mitad del servicio que sí se registró, y nada más.

**Qué informar en un entregable.** Por cada indicador: valor, unidad, denominador,
período, cobertura y qué quedó excluido con su recuento. Es la diferencia entre un
número y un resultado auditable.

**Cómo obtenerla.**

- `lab.metrics.describe_numeric` incluye `valores_usables` y `cobertura_pct`.
- `lab.metrics.coverage` la calcula para una serie suelta.
- `lab.dates.date_quality` hace lo mismo para una columna de fecha-hora, separando
  vacíos de valores no interpretables.

**Antipatrón.** Reportar la cobertura solo cuando es alta. Si la cobertura es baja,
esa es precisamente la información que quien decide necesita conocer antes de usar
el número.
