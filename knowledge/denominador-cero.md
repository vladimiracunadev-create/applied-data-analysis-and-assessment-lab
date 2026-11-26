---
id: denominador-cero
tipo: patron
titulo: Razones con denominador cero o ausente
etiquetas: [indicadores, calidad-datos, excel, pandas, errores-frecuentes]
fuente: lab/metrics.py, lab/excel.py
relacionados: [tasa-ponderada-vs-promedio-simple, vacio-no-es-cero]
---

Toda razón `a / b` necesita una decisión declarada para el caso `b = 0` o `b`
ausente. Las tres salidas posibles no son equivalentes:

| Decisión | Qué comunica | Cuándo corresponde |
| --- | --- | --- |
| Nulo (NaN, celda vacía) | «No hay indicador para esta unidad» | Casi siempre |
| Cero | «El indicador vale cero» | Nunca, salvo que el dominio lo justifique |
| Error visible (`#¡DIV/0!`) | «Hay que mirar esto» | En exploración, no en un entregable |

Devolver cero es el error más costoso: un cero se promedia, se grafica y se suma con
los demás, y arrastra el resultado del conjunto hacia abajo sin que nadie lo note.

**En Python.** `lab.metrics.safe_ratio` devuelve NaN cuando el denominador es cero o
nulo, tanto para escalares como para series.

**En Excel.** `=IF(N(C2)=0,"",D2/C2)` — en español, `=SI(N(C2)=0;"";D2/C2)`. Se usa
`N()` y no `C2=0` porque `N()` convierte el texto a cero y así una celda con texto o
vacía también queda cubierta. `SI.ERROR` no sirve aquí: oculta cualquier error, no
solo la división por cero, y puede tapar un `#¡REF!` real.

**En SQL.** `CASE WHEN b > 0 THEN 1.0 * a / b END` — sin cláusula `ELSE`, de modo que
el resultado sea `NULL`. `NULLIF(b, 0)` también funciona: `1.0 * a / NULLIF(b, 0)`.
