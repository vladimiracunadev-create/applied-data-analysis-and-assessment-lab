# Cuándo conviene dejar Pandas

P07 resuelto como benchmark reproducible: la misma agregación —filas de horario por
parada— se ejecuta con Pandas completo, Pandas por bloques y DuckDB sobre CSV.

## Resultado de referencia

En el equipo de ejecución, para 1 098 717 filas:

| Método | Tiempo aproximado | Memoria de datos visible en Python |
| --- | ---: | ---: |
| Pandas completo | 0,43 s | 60,25 MB |
| Pandas por bloques | 0,65 s | 11,31 MB máximo por bloque |
| DuckDB, consulta | 0,30 s | administrada fuera del DataFrame |

Los tres producen exactamente 12 495 grupos y cero diferencias. Los tiempos se vuelven
a medir en cada máquina; no son una promesa de rendimiento. En este volumen Pandas
completo cabe y es simple. Los bloques reducen aproximadamente 81 % la memoria de datos
a cambio de más tiempo. DuckDB gana en la consulta, pero necesita extraer el miembro
del ZIP; esa preparación se informa aparte.

## Reproducir

```powershell
python -m cases.rendimiento_gtfs.solution
```

DuckDB es opcional: `pip install -e ".[sql]"`. Sin él, el caso ejecuta y valida los dos
caminos de Pandas y marca la tercera medición como no ejecutada.
