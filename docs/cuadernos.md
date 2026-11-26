# Cuadernos de trabajo

Un **cuaderno** es el problema resuelto paso a paso: el problema explicado como
problema, el plan de la solución antes de ejecutarla, y para cada paso el
código de Python, la salida que devuelve de verdad, y la fórmula de Excel
dibujada en su hoja. Se lee de arriba abajo y trae sus descargables al lado,
incluido un ZIP con todo el caso.

No es lo mismo que el `README.md` de un caso, que cuenta **qué se encontró** y
sirve para auditar el resultado.

> Archivo generado por `scripts/build_cuadernos.py`. No lo edite a mano.

## Los dieciséis problemas de la instancia DTPM

| Problema | Cuaderno | Caso |
| --- | --- | --- |
| P01 · Consolidar los cinco Excel de lugares de carga | [**abrir**](../cases/bip_lugares_carga/CUADERNO.md) | [`bip_lugares_carga`](../cases/bip_lugares_carga/README.md) |
| P02 · ¿El código es una clave? | [dentro del de P01, pasos 7 y 8](../cases/bip_lugares_carga/CUADERNO.md) | [`bip_lugares_carga`](../cases/bip_lugares_carga/README.md) |
| P03 · Validación cruzada de coordenadas | pendiente | [`correspondencia_metro`](../cases/correspondencia_metro/README.md) |
| P04 · Normalizar comuna y entidad para agrupar | [dentro del de P01, paso 8](../cases/bip_lugares_carga/CUADERNO.md) | [`bip_lugares_carga`](../cases/bip_lugares_carga/README.md) |
| P05 · Interpretar horarios escritos en texto libre | pendiente | [`carga_nocturna`](../cases/carga_nocturna/README.md) |
| P06 · Expediciones por hora en un día laboral | pendiente | [`gtfs_red_movilidad`](../cases/gtfs_red_movilidad/README.md) |
| P07 · ¿Cuándo conviene dejar Pandas? | pendiente · falta el análisis | — |
| P08 · Distancia de cada parada al lugar de carga | pendiente | [`cobertura_de_carga`](../cases/cobertura_de_carga/README.md) |
| P09 · Cobertura de carga en el servicio nocturno | pendiente | [`carga_nocturna`](../cases/carga_nocturna/README.md) |
| P10 · Correspondencia entre buses y Metro | pendiente | [`correspondencia_metro`](../cases/correspondencia_metro/README.md) |
| P11 · El calendario de medición de un indicador oficial | pendiente | [`calendario_medicion`](../cases/calendario_medicion/README.md) |
| P12 · El ICF sobre la oferta programada | pendiente · falta el análisis | — |
| P13 · Distribución de la frecuencia programada | pendiente · falta el análisis | — |
| P14 · Qué cambió entre dos versiones del feed | pendiente · falta el análisis | — |
| P15 · Evolución de la oferta programada por año | pendiente · falta el análisis | — |
| P16 · Informe de una página para quien decide | pendiente · falta el análisis | — |

**1 de 16 cuadernos propios**, más 2 problemas
cubiertos dentro del cuaderno de otro. Los problemas sin caso necesitan el
análisis además del cuaderno. El estado detallado de cada uno, con lo que
enseña y lo que no se puede contestar, está en el
[mapa de problemas](problemas-de-la-instancia.md).

## Regenerar

```powershell
python scripts/build_cuadernos.py
```

Necesita los datos descargados: un cuaderno se genera **ejecutando el caso**,
de modo que el código que aparece es el que corrió y la salida es la que
devolvió.
