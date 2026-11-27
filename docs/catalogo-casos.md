<!-- Archivo generado por scripts/build_docs.py. No lo edite a mano: modifique el código fuente y vuelva a ejecutar el script. -->

# Catálogo de casos de estudio

Casos independientes del laboratorio. Cada uno declara sus metadatos en
`cases/<slug>/case.json`, y `tests/test_catalog.py` exige que las 26 secciones
obligatorias estén presentes: un caso con metadatos incompletos aparece aquí
marcado como tal, no se oculta.

## Casos

| Caso | Título | Disciplina | Industria | Dificultad | Estado | Tiempo | Metadatos |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [`bip_lugares_carga`](../cases/bip_lugares_carga/README.md) | Consolidar cinco Excel públicos heterogéneos, y establecer qué identifica una fila cuando nada lo hace | gestion-de-datos | transporte | intermedio | implementado | 180 min | sí |
| [`calendario_medicion`](../cases/calendario_medicion/README.md) | Reconstruir el calendario de medición de un indicador oficial y auditar sus reglas | gobernanza-de-datos | administracion-publica | avanzado | implementado | 150 min | sí |
| [`carga_nocturna`](../cases/carga_nocturna/README.md) | Cobertura de carga en el servicio nocturno: cuando la respuesta es un intervalo porque falta una columna | gobernanza-de-datos | transporte | avanzado | implementado | 180 min | sí |
| [`cobertura_de_carga`](../cases/cobertura_de_carga/README.md) | Cruzar dos fuentes que no comparten ninguna clave: distancia de cada parada al lugar de carga más cercano | analisis-de-datos | transporte | intermedio | implementado | 120 min | sí |
| [`correspondencia_metro`](../cases/correspondencia_metro/README.md) | Conciliar dos inventarios de la misma realidad, y descubrir que cada comprobación tiene su punto ciego | gestion-de-datos | transporte | avanzado | implementado | 150 min | sí |
| [`education`](../cases/education/README.md) | Asistencia ponderada por establecimiento | analisis-de-datos | educacion | introductorio | implementado | 90 min | sí |
| [`evolucion_gtfs`](../cases/evolucion_gtfs/README.md) | Cambios de red y oferta programada entre publicaciones GTFS | ingenieria-de-datos | transporte | especializado | implementado | 210 min | sí |
| [`frecuencia_programada`](../cases/frecuencia_programada/README.md) | Frecuencia programada y alcance calculable del ICF | analisis-de-datos | transporte | avanzado | implementado | 150 min | sí |
| [`gtfs_red_movilidad`](../cases/gtfs_red_movilidad/README.md) | Expediciones por hora en la Red Metropolitana de Movilidad (datos públicos reales) | ingenieria-de-datos | transporte | especializado | implementado | 180 min | sí |
| [`informe_decision_carga`](../cases/informe_decision_carga/README.md) | Informe ejecutivo para priorizar estudios de nuevos centros de carga | analisis-de-negocios | transporte | avanzado | implementado | 90 min | sí |
| [`rendimiento_gtfs`](../cases/rendimiento_gtfs/README.md) | Cuándo conviene dejar Pandas: benchmark de una agregación GTFS | ingenieria-de-datos | transporte | avanzado | implementado | 120 min | sí |
| [`retail`](../cases/retail/README.md) | Ventas netas, margen y devoluciones por producto | analisis-de-negocios | comercio | intermedio | implementado | 90 min | sí |
| [`transport`](../cases/transport/README.md) | Indicadores operacionales de transporte público | analisis-de-datos | transporte | avanzado | implementado | 240 min | sí |

## Cobertura de competencias

Cuántos casos entrenan cada competencia. Las competencias con cero casos están
declaradas en la hoja de ruta como brechas conocidas.

| competencia | casos | cantidad |
| --- | --- | --- |
| agregacion-indicadores | bip_lugares_carga, calendario_medicion, carga_nocturna, cobertura_de_carga, correspondencia_metro, education, evolucion_gtfs, frecuencia_programada, gtfs_red_movilidad, informe_decision_carga, rendimiento_gtfs, retail, transport | 13 |
| calidad-datos | bip_lugares_carga, calendario_medicion, carga_nocturna, cobertura_de_carga, correspondencia_metro, education, evolucion_gtfs, frecuencia_programada, gtfs_red_movilidad, informe_decision_carga, rendimiento_gtfs, retail, transport | 13 |
| comunicacion-resultados | bip_lugares_carga, calendario_medicion, carga_nocturna, cobertura_de_carga, correspondencia_metro, education, evolucion_gtfs, frecuencia_programada, gtfs_red_movilidad, informe_decision_carga, rendimiento_gtfs, retail | 12 |
| reproducibilidad | bip_lugares_carga, calendario_medicion, carga_nocturna, cobertura_de_carga, correspondencia_metro, evolucion_gtfs, frecuencia_programada, gtfs_red_movilidad, informe_decision_carga, rendimiento_gtfs, transport | 11 |
| validacion-independiente | bip_lugares_carga, calendario_medicion, carga_nocturna, cobertura_de_carga, correspondencia_metro, evolucion_gtfs, frecuencia_programada, gtfs_red_movilidad, informe_decision_carga, rendimiento_gtfs, transport | 11 |
| lectura-escritura-datos | bip_lugares_carga, education, evolucion_gtfs, frecuencia_programada, gtfs_red_movilidad, rendimiento_gtfs, retail, transport | 8 |
| cruce-consolidacion | bip_lugares_carga, carga_nocturna, cobertura_de_carga, correspondencia_metro, evolucion_gtfs, gtfs_red_movilidad, transport | 7 |
| gobernanza-datos | bip_lugares_carga, calendario_medicion, carga_nocturna, correspondencia_metro, evolucion_gtfs, frecuencia_programada, informe_decision_carga | 7 |
| fechas-horarios | calendario_medicion, carga_nocturna, evolucion_gtfs, frecuencia_programada, gtfs_red_movilidad, transport | 6 |
| limpieza-normalizacion | bip_lugares_carga, carga_nocturna, correspondencia_metro, gtfs_red_movilidad, retail, transport | 6 |
| apoyo-decision | calendario_medicion, carga_nocturna, cobertura_de_carga, correspondencia_metro, informe_decision_carga | 5 |
| estadistica-descriptiva | cobertura_de_carga, education, frecuencia_programada, transport | 4 |
| hojas-de-calculo | bip_lugares_carga, education, retail, transport | 4 |
| ingenieria-datos | evolucion_gtfs, gtfs_red_movilidad, rendimiento_gtfs | 3 |
| visualizacion | informe_decision_carga, transport | 2 |
| sql | transport | 1 |

## Cómo agregar un caso

```powershell
uv run python scripts/new_case.py mi-caso
```

Luego complete `cases/mi-caso/case.json` con los 26 campos obligatorios y
`uv run python -m pytest tests/test_catalog.py` para validarlo.
