# P17 · Gobernanza y catálogo de datos DTPM

P17 convierte la procedencia ya documentada por el laboratorio en un catálogo de ocho
activos y pregunta algo distinto de P01–P16: **¿qué debe aclararse para que estos datos
sean gobernables, además de utilizables?**

El archivo [`input.csv`](input.csv) es una elaboración pedagógica versionada. Resume
evidencia del repositorio, pero **no es un catálogo oficial del DTPM** ni asigna
responsabilidades institucionales que no estén publicadas.

## Resultado

La solución valida la identidad del catálogo y mide cinco brechas: licencia, esquema,
actualización, responsable operativo y retención. El puntaje publicado es:

`brecha = 3·licencia + 2·esquema + 2·actualización + 2·responsable + retención`

`riesgo documental = brecha × peso de criticidad`

Sirve para ordenar aclaraciones; no estima incidentes ni califica el desempeño del
publicador.

## Ejecutar

```powershell
python -m cases.gobernanza_datos_dtpm.solution
```

- [Cuaderno resuelto](CUADERNO.md)
- [Abrir en Google Colab](https://colab.research.google.com/github/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/blob/main/cases/gobernanza_datos_dtpm/cuaderno/colab.ipynb)
- `cuaderno/solucion_pandas.py`
- `cuaderno/solucion_polars.py`
- `cuaderno/solucion.R`
- `cuaderno/solucion.Rmd`

Las tres implementaciones leen el mismo CSV reproducible, producen el mismo ranking y
generan visualizaciones comparables.
