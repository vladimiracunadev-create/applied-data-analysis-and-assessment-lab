# Cuándo conviene dejar Pandas

P07 resuelto como benchmark reproducible: la misma agregación —filas de horario por
parada— se ejecuta con Pandas completo, Pandas por bloques, DuckDB y Polars lazy sobre
el mismo CSV.

## Resultado de referencia

En el equipo de ejecución, para 1 098 717 filas:

| Método | Tiempo aproximado | Memoria de datos visible en Python |
| --- | ---: | ---: |
| Pandas completo | 0,96 s | 60,25 MB |
| Pandas por bloques | 1,66 s | 11,31 MB máximo por bloque |
| DuckDB, consulta | 1,12 s | administrada fuera del DataFrame |
| Polars lazy, consulta | 0,20 s | administrada fuera del DataFrame |

Los cuatro producen exactamente 12 495 grupos y cero diferencias. Los tiempos se vuelven
a medir en cada máquina; no son una promesa de rendimiento. En este volumen Pandas
completo cabe y es simple. Los bloques reducen aproximadamente 81 % la memoria de datos
a cambio de más tiempo. DuckDB y Polars necesitan extraer el miembro del ZIP; esa
preparación se informa aparte. En esta corrida Polars fue el más rápido en la consulta,
pero una medición no autoriza extrapolar a otros volúmenes u operaciones.

## Reproducir

```powershell
python -m cases.rendimiento_gtfs.solution
```

DuckDB y Polars son opcionales: `uv sync --extra sql --extra polars`. Sin ellos, el caso
ejecuta y valida los dos caminos de Pandas y marca las mediciones opcionales como no
ejecutadas.
