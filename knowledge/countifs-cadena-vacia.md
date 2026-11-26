---
id: countifs-cadena-vacia
tipo: error
titulo: CONTAR.SI.CONJUNTO con "<>" cuenta las celdas que devuelven cadena vacía
etiquetas: [excel, hojas-de-calculo, indicadores, errores-frecuentes]
fuente: scripts/build_excel_solutions.py
relacionados: [denominador-cero, vacio-no-es-cero]
---

**Situación.** Una columna auxiliar marca con 1 o 0 los viajes puntuales y devuelve
`""` cuando el indicador no aplica:

```excel
=SI(O(K6=0;J6="";J6<0);"";SI(J6<=I6;1;0))
```

Para la tasa de puntualidad se necesita el denominador «viajes donde el indicador
aplica». La fórmula intuitiva es incorrecta:

```excel
=CONTAR.SI.CONJUNTO(Recorrido;$A6;Puntual;"<>")     ← mal
```

**Por qué falla.** El criterio `"<>"` significa «distinto de vacío», y Excel
considera no vacía toda celda que contenga algo, incluida una fórmula que devuelve
cadena vacía. Una celda con `=""` no está vacía: contiene una cadena de longitud
cero. El denominador queda inflado con todas las filas donde el indicador no aplica,
y la tasa baja sin motivo.

**Corrección.** Contar solo los valores numéricos, que son exactamente las filas
donde el indicador aplica:

```excel
=CONTAR.SI.CONJUNTO(Recorrido;$A6;Puntual;">=0")    ← bien
```

**Regla práctica.** En Excel hay tres estados distintos que conviene no confundir:
celda realmente vacía, celda con cadena vacía producida por fórmula y celda con cero.
`CONTARA` cuenta las dos primeras; `CONTAR` solo los números; `CONTAR.BLANCO` cuenta
las vacías reales **y** las de cadena vacía. Cuando el denominador de una tasa sale de
un `CONTAR.SI.CONJUNTO`, hay que preguntarse cuál de los tres estados se está
contando.
