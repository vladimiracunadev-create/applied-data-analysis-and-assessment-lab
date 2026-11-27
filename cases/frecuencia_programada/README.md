# Frecuencia programada e ICF

Caso resuelto de P12 y P13. Construye la referencia de frecuencia desde el GTFS y
separa con precisión lo que puede calcularse de lo que exige observaciones GPS.

## Resultado

- 14 520 ventanas válidas representan 142 366 salidas programadas.
- El intervalo mediano es 15 minutos por ventana y 13,03 minutos al ponderar por salida.
- El rango va de 3,10 a 330 minutos: la media de 21,17 no describe bien la distribución.
- El GTFS no contiene mediciones GPS, por lo que no permite calcular ni el numerador,
  ni el denominador observado, ni el ICF oficial.

## Reproducir

```powershell
python -m cases.frecuencia_programada.solution
```

Las tablas quedan en `resultados/`. El procedimiento completo, con equivalentes de
Excel, está en [CUADERNO.md](CUADERNO.md).

## Límites

El análisis describe oferta programada de la publicación GTFS del 14 de noviembre de
2026. No demuestra que esas salidas se hayan realizado ni mide regularidad, demanda o
cumplimiento operacional.

## Cuaderno, motores y gráfico

- [Resolución profesional paso a paso](CUADERNO.md).
- [Abrir en Google Colab](https://colab.research.google.com/github/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/blob/main/cases/frecuencia_programada/cuaderno/colab.ipynb).
- [Pandas + Matplotlib](cuaderno/solucion_pandas.py): referencia comparable de percentiles.
- [Polars + Matplotlib](cuaderno/solucion_polars.py): percentiles del intervalo programado.
- [R + dplyr/readr + ggplot2](cuaderno/solucion.R) y [R Markdown](cuaderno/solucion.Rmd): contraste y distribución portable.
- [Figura publicada](cuaderno/svg/paso-03.svg).
