# Evolución entre publicaciones GTFS

Caso resuelto de P14 y P15 sobre tres publicaciones oficiales reales: 24 de noviembre
de 2024, 20 de diciembre de 2025 y 14 de noviembre de 2026.

## Resultado

| Medida | 2024-11-24 | 2025-12-20 | 2026-11-14 |
| --- | ---: | ---: | ---: |
| Rutas | 419 | 428 | 425 |
| Paradas de embarque | 12 201 | 12 336 | 12 497 |
| Viajes declarados | 19 983 | 14 149 | 26 137 |
| Ventanas de frecuencia | 19 863 | 14 060 | 14 520 |
| Salidas programadas en día laboral | 68 533 | 68 011 | 64 011 |

Entre 2024 y 2026 persisten 400 identificadores de ruta; aparecen 25 y desaparecen 19.
La oferta calculada con la misma definición cambia −0,76 % en 2025 y −5,88 % en 2026.

## Reproducir

```powershell
python scripts/fetch_data.py gtfs-historicos-2024
python scripts/fetch_data.py gtfs-historicos-2025
python scripts/fetch_data.py gtfs-red-movilidad
python -m cases.evolucion_gtfs.solution
```

## Interpretación y límite

La comparación detecta diferencias publicadas, no sus causas. Un alta o baja de ID
puede ser una modificación real o una decisión de identificación. La serie ejecutada
tiene tres puntos: describe una trayectoria reciente, no todo 2014–2026. El código
acepta más publicaciones sin cambiar la definición.

## Cuaderno, motores y gráfico

- [Resolución profesional paso a paso](CUADERNO.md).
- [Polars + Matplotlib](cuaderno/solucion_polars.py): evolución de salidas comparables.
- [R + ggplot2](cuaderno/solucion.R): contraste y gráfico equivalente.
- [Figura publicada](cuaderno/svg/paso-06.svg).
