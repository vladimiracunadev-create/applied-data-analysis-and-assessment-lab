# Cuadernos de trabajo

Un **cuaderno** es el problema resuelto paso a paso: el problema explicado como
problema, el plan de la solución antes de ejecutarla, y para cada paso el
código de Python, la salida que devuelve de verdad, la fórmula de Excel y
contrastes ejecutables en Polars y R. Cada caso incluye al menos un gráfico
estadístico con unidades, período y fuente. Se lee de arriba abajo y trae
sus descargables al lado, incluido un ZIP con todo el caso.

No es lo mismo que el `README.md` de un caso, que cuenta **qué se encontró** y
sirve para auditar el resultado.

> Archivo generado por `scripts/build_cuadernos.py`. No lo edite a mano.

## Ruta lineal de los cuadernos

La navegación anterior/siguiente sigue este orden, sin saltar del P01 al P08:

1. [P01/P02/P04 · Consolidación y calidad](../cases/bip_lugares_carga/CUADERNO.md) · [Abrir en Colab](https://colab.research.google.com/github/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/blob/main/cases/bip_lugares_carga/cuaderno/colab.ipynb)
2. [P03/P10 · Coordenadas y correspondencia](../cases/correspondencia_metro/CUADERNO.md) · [Abrir en Colab](https://colab.research.google.com/github/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/blob/main/cases/correspondencia_metro/cuaderno/colab.ipynb)
3. [P05/P09 · Horarios y cobertura nocturna](../cases/carga_nocturna/CUADERNO.md) · [Abrir en Colab](https://colab.research.google.com/github/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/blob/main/cases/carga_nocturna/cuaderno/colab.ipynb)
4. [P06 · Expediciones por hora](../cases/gtfs_red_movilidad/CUADERNO.md) · [Abrir en Colab](https://colab.research.google.com/github/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/blob/main/cases/gtfs_red_movilidad/cuaderno/colab.ipynb)
5. [P07 · Rendimiento GTFS](../cases/rendimiento_gtfs/CUADERNO.md) · [Abrir en Colab](https://colab.research.google.com/github/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/blob/main/cases/rendimiento_gtfs/cuaderno/colab.ipynb)
6. [P08 · Cobertura espacial](../cases/cobertura_de_carga/CUADERNO.md) · [Abrir en Colab](https://colab.research.google.com/github/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/blob/main/cases/cobertura_de_carga/cuaderno/colab.ipynb)
7. [P11 · Calendario de medición](../cases/calendario_medicion/CUADERNO.md) · [Abrir en Colab](https://colab.research.google.com/github/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/blob/main/cases/calendario_medicion/cuaderno/colab.ipynb)
8. [P12/P13 · Frecuencia programada](../cases/frecuencia_programada/CUADERNO.md) · [Abrir en Colab](https://colab.research.google.com/github/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/blob/main/cases/frecuencia_programada/cuaderno/colab.ipynb)
9. [P14/P15 · Evolución GTFS](../cases/evolucion_gtfs/CUADERNO.md) · [Abrir en Colab](https://colab.research.google.com/github/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/blob/main/cases/evolucion_gtfs/cuaderno/colab.ipynb)
10. [P16 · Informe de decisión](../cases/informe_decision_carga/CUADERNO.md) · [Abrir en Colab](https://colab.research.google.com/github/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/blob/main/cases/informe_decision_carga/cuaderno/colab.ipynb)
11. [P17 · Gobernanza de datos DTPM](../cases/gobernanza_datos_dtpm/CUADERNO.md) · [Abrir en Colab](https://colab.research.google.com/github/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/blob/main/cases/gobernanza_datos_dtpm/cuaderno/colab.ipynb)

## Los 17 problemas de la instancia DTPM

| Problema | Cuaderno | Caso |
| --- | --- | --- |
| P01 · Consolidar los cinco Excel de lugares de carga | [**abrir**](../cases/bip_lugares_carga/CUADERNO.md) | [`bip_lugares_carga`](../cases/bip_lugares_carga/README.md) |
| P02 · ¿El código es una clave? | [dentro del de P01, pasos 7 a 9](../cases/bip_lugares_carga/CUADERNO.md) | [`bip_lugares_carga`](../cases/bip_lugares_carga/README.md) |
| P03 · Validación cruzada de coordenadas | [**abrir**](../cases/correspondencia_metro/CUADERNO.md) | [`correspondencia_metro`](../cases/correspondencia_metro/README.md) |
| P04 · Normalizar comuna y entidad para agrupar | [dentro del de P01, pasos 10 a 12](../cases/bip_lugares_carga/CUADERNO.md) | [`bip_lugares_carga`](../cases/bip_lugares_carga/README.md) |
| P05 · Interpretar horarios escritos en texto libre | [**abrir**](../cases/carga_nocturna/CUADERNO.md) | [`carga_nocturna`](../cases/carga_nocturna/README.md) |
| P06 · Expediciones por hora en un día laboral | [**abrir**](../cases/gtfs_red_movilidad/CUADERNO.md) | [`gtfs_red_movilidad`](../cases/gtfs_red_movilidad/README.md) |
| P07 · ¿Cuándo conviene dejar Pandas? | [**abrir**](../cases/rendimiento_gtfs/CUADERNO.md) | [`rendimiento_gtfs`](../cases/rendimiento_gtfs/README.md) |
| P08 · Distancia de cada parada al lugar de carga | [**abrir**](../cases/cobertura_de_carga/CUADERNO.md) | [`cobertura_de_carga`](../cases/cobertura_de_carga/README.md) |
| P09 · Cobertura de carga en el servicio nocturno | [mismo cuaderno que P05](../cases/carga_nocturna/CUADERNO.md) | [`carga_nocturna`](../cases/carga_nocturna/README.md) |
| P10 · Correspondencia entre buses y Metro | [mismo cuaderno que P03](../cases/correspondencia_metro/CUADERNO.md) | [`correspondencia_metro`](../cases/correspondencia_metro/README.md) |
| P11 · El calendario de medición de un indicador oficial | [**abrir**](../cases/calendario_medicion/CUADERNO.md) | [`calendario_medicion`](../cases/calendario_medicion/README.md) |
| P12 · El ICF sobre la oferta programada | [**abrir**](../cases/frecuencia_programada/CUADERNO.md) | [`frecuencia_programada`](../cases/frecuencia_programada/README.md) |
| P13 · Distribución de la frecuencia programada | [mismo cuaderno que P12](../cases/frecuencia_programada/CUADERNO.md) | [`frecuencia_programada`](../cases/frecuencia_programada/README.md) |
| P14 · Qué cambió entre dos versiones del feed | [**abrir**](../cases/evolucion_gtfs/CUADERNO.md) | [`evolucion_gtfs`](../cases/evolucion_gtfs/README.md) |
| P15 · Evolución de la oferta programada por año | [mismo cuaderno que P14](../cases/evolucion_gtfs/CUADERNO.md) | [`evolucion_gtfs`](../cases/evolucion_gtfs/README.md) |
| P16 · Informe de una página para quien decide | [**abrir**](../cases/informe_decision_carga/CUADERNO.md) | [`informe_decision_carga`](../cases/informe_decision_carga/README.md) |
| P17 · Gobernanza y catálogo de activos de datos | [**abrir**](../cases/gobernanza_datos_dtpm/CUADERNO.md) | [`gobernanza_datos_dtpm`](../cases/gobernanza_datos_dtpm/README.md) |

**11 cuadernos distintos cubren 17 de 17 problemas**:
6 están integrados en el cuaderno de un problema relacionado.
El estado detallado de cada uno, con lo que enseña y lo que no se puede
contestar, está en el [mapa de problemas](problemas-de-la-instancia.md).

## Regenerar

```powershell
python scripts/build_cuadernos.py
```

Necesita los datos descargados: un cuaderno se genera **ejecutando el caso**,
de modo que el código que aparece es el que corrió y la salida es la que
devolvió.
