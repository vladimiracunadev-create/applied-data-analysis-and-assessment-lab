# Caso retail
Datos sintéticos, semilla fija. Cada fila representa un registro agregado o transacción ficticia.

## Enunciado
Calcule ventas netas, margen y unidades por producto, descontando devoluciones. Excluya cantidades negativas y duplicados; explique el tratamiento y compare los resultados en Excel mediante SUMAR.SI.CONJUNTO o tabla dinámica.

## Entrega
Excel con datos limpios e indicadores, código reproducible y nota de supuestos. Tiempo sugerido: 90 minutos.

## Rúbrica
Calidad 25; cálculo 35; comprobación Excel 20; interpretación 20 puntos.

## Soluciones comparables

| Tecnología | Comando |
| --- | --- |
| Pandas | `uv run python -m cases.retail.solution` |
| Polars | `uv run --extra polars python solutions/polars_reference.py retail` |
| R base | `Rscript solutions/r_reference.R retail 1 reference_outputs/r/retail` |

Las tres parten de `input.csv`; `tests/test_multiengine.py` confronta las métricas con
tolerancia 10⁻⁹. No consulte las soluciones antes de resolver.
