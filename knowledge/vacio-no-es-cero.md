---
id: vacio-no-es-cero
tipo: concepto
titulo: Ausente, cero e inválido son tres estados distintos
etiquetas: [calidad-datos, limpieza-normalizacion, pandas, sql, excel]
fuente: lab/contracts.py, docs/diccionario.md
relacionados: [denominador-cero, cobertura-de-un-indicador, countifs-cadena-vacia]
---

Un conteo de pasajeros puede estar en cuatro estados, y confundirlos cambia el
resultado:

| Estado | Significado | Tratamiento |
| --- | --- | --- |
| `0` | El viaje ocurrió y nadie subió | Entra en la suma y en el promedio |
| vacío / nulo | El viaje ocurrió y no se registró el conteo | Sale de la suma; se cuenta como falta de cobertura |
| `-5` | Valor imposible: hay un error de registro | Sale de la suma; se reporta como defecto |
| fila ausente | El viaje no está en el archivo | Problema de completitud, distinto de los anteriores |

**Consecuencia práctica.** Un viaje realizado con pasajeros nulo sigue siendo un
viaje realizado: cuenta para el cumplimiento de la programación y para la duración,
pero no para la demanda. Eliminar la fila completa por tener un campo nulo degrada
dos indicadores correctos para proteger uno.

**Cómo se materializa en cada herramienta.**

- **Pandas.** `pd.to_numeric(serie, errors="coerce")` convierte lo no numérico en
  `NaN`, que es distinto de `0`. `read_csv` ya entrega `NaN` para el campo vacío.
- **SQL.** `CAST('' AS REAL)` devuelve `0.0` en SQLite, no `NULL`. Hay que escribir
  `CAST(NULLIF(TRIM(col), '') AS REAL)` para no convertir la ausencia en cero.
- **Excel.** Una celda vacía se trata como cero en una suma, pero `PROMEDIO` la
  ignora; `CONTARA` la distingue de una celda con cadena vacía.

**Regla del laboratorio.** Antes de calcular, informar la cobertura: cuántos
registros aportaron dato sobre el total. Una media sin cobertura es un número sin
interpretación.
