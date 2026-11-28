# P19 · Red programada de correspondencias Metro–bus

P19 convierte el resultado de P03/P10 en un grafo bipartito: 126 estaciones por un
lado y los servicios de bus programados que pasan a menos de 200 metros por el otro.

El caso calcula grados y escenarios de retiro. Una conexión perdida es una relación
programada menos; **no equivale a pasajeros afectados**, porque no hay demanda ni GPS.

- [Cuaderno resuelto](CUADERNO.md)
- [Abrir en Colab](https://colab.research.google.com/github/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/blob/main/cases/red_correspondencias_dtpm/cuaderno/colab.ipynb)

```powershell
python -m cases.red_correspondencias_dtpm.solution
```
