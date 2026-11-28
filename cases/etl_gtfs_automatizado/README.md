# P18 · ETL histórico y control automatizado GTFS

P18 reutiliza el inventario reproducible de P14/P15 y lo convierte en una entrada
contractual e incremental. No sustituye la adquisición: enseña qué ocurre después de
obtener una publicación GTFS y antes de incorporarla a una serie histórica.

El caso valida identidad, fechas y volúmenes; produce una partición por publicación y
distingue explícitamente el CSV ejecutado de una exportación Parquet opcional. Si no hay
motor columnar instalado, el resultado dice **no ejecutado**.

- [Cuaderno resuelto](CUADERNO.md)
- [Abrir en Colab](https://colab.research.google.com/github/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/blob/main/cases/etl_gtfs_automatizado/cuaderno/colab.ipynb)

```powershell
python -m cases.etl_gtfs_automatizado.solution
```
