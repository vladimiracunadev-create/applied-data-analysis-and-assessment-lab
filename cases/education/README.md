# Caso education
Datos sintéticos, semilla fija. Cada fila representa un registro agregado o transacción ficticia.

## Enunciado
Calcule asistencia ponderada por establecimiento (suma de días asistidos / suma de días programados), identifique registros inválidos y compare con el promedio simple de porcentajes. Reproduzca los indicadores en Excel y explique la diferencia.

## Entrega
Excel con datos limpios e indicadores, código reproducible y nota de supuestos. Tiempo sugerido: 90 minutos.

## Rúbrica
Calidad 25; cálculo 35; comprobación Excel 20; interpretación 20 puntos.

## Soluciones comparables

| Tecnología | Comando |
| --- | --- |
| Pandas | `uv run python -m cases.education.solution` |
| Polars | `uv run --extra polars python solutions/polars_reference.py education` |
| R base | `Rscript solutions/r_reference.R education 1 reference_outputs/r/education` |

Las tres parten de `input.csv`; `tests/test_multiengine.py` confronta ambas tasas con
tolerancia 10⁻⁹. No consulte las soluciones antes de resolver.
