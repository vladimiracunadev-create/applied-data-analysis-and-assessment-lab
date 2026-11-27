# Manual de aprendizaje
## 1. Entorno
`uv sync`, `uv run python --version`, `uv run jupyter lab`. Compruebe Excel y pruebe exportar un archivo antes del examen.
## 2. Python
Practique listas, diccionarios, funciones, pathlib, excepciones. Ejercicio: función que reciba realizados y programados y devuelva None cuando el denominador sea cero.
## 3. Pandas
`pd.read_csv`, `head`, `info`, `describe`, `value_counts`, `loc`, `groupby`, `agg`. Ejercicio: contar viajes por estado y comprobar el total.
## 4. Polars, R y visualización
Polars es opcional: `uv sync --extra polars`. Ejecute la referencia canónica con
`uv run --extra polars python solutions/polars_reference.py transport 1`. La referencia
canónica de R usa solo la biblioteca base: `Rscript solutions/r_reference.R transport 1
reference_outputs/r/transport`. Ambos parten de los CSV crudos; no convierten la salida
de Pandas.

Los diez casos reales agregan dentro de `cases/<caso>/cuaderno/` una
`solucion_polars.py` con Matplotlib y una `solucion.R` con ggplot2. Por ejemplo:

```powershell
python cases/cobertura_de_carga/cuaderno/solucion_polars.py --grafico cobertura.png
Rscript cases/cobertura_de_carga/cuaderno/solucion.R --grafico cobertura-r.png
```

Ambas leen el mismo contrato de resultados del caso, muestran el resumen estadístico y
generan una figura comparable. Los enlaces están también dentro de cada `CUADERNO.md`.

## 5. Excel
Importe CSV como tabla; use filtros, tablas dinámicas, CONTAR.SI.CONJUNTO, SUMAR.SI.CONJUNTO, BUSCARX, SI.ERROR. Ejemplo con tablas nombradas Viajes y Recorridos: `=BUSCARX([@recorrido_id];Recorridos[recorrido_id];Recorridos[operador_id];"SIN CLAVE")`. Duración en minutos: `=SI(O([@inicio]="";[@fin]="");"";([@fin]-[@inicio])*1440)`. Convierta fechas de texto a fecha/hora primero. Los separadores dependen de la configuración regional.
## 6. SQL a Pandas
SELECT columnas -> df[[...]]; WHERE -> loc; GROUP BY -> groupby; JOIN -> merge; DISTINCT -> drop_duplicates. COUNT(*) -> size; COUNT(col) -> count. Verifique cardinalidad con validate='many_to_one'.
## 7. Calidad
`duplicated`, `isna`, `pd.to_numeric(errors='coerce')`, `pd.to_datetime(errors='coerce')`. No borre registros indiscriminadamente. Genere un informe de defectos y cobertura.
## 8. Cruces
Cruce viajes con recorridos y operadores. Use left join para detectar faltantes; compruebe que la cantidad de filas no aumente. Una programación sin viajes debe conservarse.
## 9. Indicadores
Media = suma/n; mediana = valor central; percentil 90 = umbral que deja aproximadamente 90% de observaciones por debajo. Diferencie porcentaje de puntos porcentuales. Ejercicio: compare promedio y mediana de duración.
## 10. Fechas
`pd.to_datetime`, `.dt.hour`, `.dt.date`, `.dt.day`. Agrupe por hora y día; explique que la hora de inicio no equivale a la hora de cada validación.
## 11. Transporte
Diferencie viajes de vehículos y pasajeros registrados. Calcule demanda, cancelaciones, duración, cumplimiento de programación y cobertura. No infiera causas a partir de correlaciones.
## 12. Visualización
Gráfico de barras por operador y línea por hora; rotule unidades y período. Exporte tablas con `to_excel`.
## 13. Validación
Compare totales de Excel y Python, documente reglas, denominadores, excepciones, diferencias de redondeo y limitaciones. Entregue código reproducible y archivos legibles.
## 14–16. Simulaciones
Use reloj de cuatro horas, sin consultar soluciones. Corrija con la rúbrica. Distribución sugerida: 15 lectura, 30 calidad, 80 Python, 55 Excel, 30 análisis, 20 validación, 10 envío.
