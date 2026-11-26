<!-- Archivo generado por scripts/build_docs.py. No lo edite a mano: modifique el código fuente y vuelva a ejecutar el script. -->

# Catálogo de casos de estudio

Casos independientes del laboratorio. Cada uno declara sus metadatos en
`cases/<slug>/case.json`, y `tests/test_catalog.py` exige que las 26 secciones
obligatorias estén presentes: un caso con metadatos incompletos aparece aquí
marcado como tal, no se oculta.

## Casos

| Caso | Título | Disciplina | Industria | Dificultad | Estado | Tiempo | Metadatos |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [`bip_lugares_carga`](../cases/bip_lugares_carga/README.md) | Consolidar cinco Excel públicos heterogéneos: lugares de carga de la tarjeta bip! | gestion-de-datos | transporte | intermedio | implementado | 120 min | sí |
| [`calendario_medicion`](../cases/calendario_medicion/README.md) | Reconstruir el calendario de medición de un indicador oficial y auditar sus reglas | gobernanza-de-datos | administracion-publica | avanzado | implementado | 150 min | sí |
| [`carga_nocturna`](../cases/carga_nocturna/README.md) | Cobertura de carga en el servicio nocturno: cuando la respuesta es un intervalo porque falta una columna | gobernanza-de-datos | transporte | avanzado | implementado | 180 min | sí |
| [`cobertura_de_carga`](../cases/cobertura_de_carga/README.md) | Cruzar dos fuentes que no comparten ninguna clave: distancia de cada parada al lugar de carga más cercano | analisis-de-datos | transporte | intermedio | implementado | 120 min | sí |
| [`correspondencia_metro`](../cases/correspondencia_metro/README.md) | Conciliar dos inventarios de la misma realidad, y descubrir que cada comprobación tiene su punto ciego | gestion-de-datos | transporte | avanzado | implementado | 150 min | sí |
| [`education`](../cases/education/README.md) | Asistencia ponderada por establecimiento | analisis-de-datos | educacion | introductorio | implementado | 90 min | sí |
| [`gtfs_red_movilidad`](../cases/gtfs_red_movilidad/README.md) | Expediciones por hora en la Red Metropolitana de Movilidad (datos públicos reales) | ingenieria-de-datos | transporte | especializado | implementado | 180 min | sí |
| [`retail`](../cases/retail/README.md) | Ventas netas, margen y devoluciones por producto | analisis-de-negocios | comercio | intermedio | implementado | 90 min | sí |
| [`transport`](../cases/transport/README.md) | Indicadores operacionales de transporte público | analisis-de-datos | transporte | avanzado | implementado | 240 min | sí |

## Cobertura de competencias

Cuántos casos entrenan cada competencia. Las competencias con cero casos están
declaradas en la hoja de ruta como brechas conocidas.

| competencia | casos | cantidad |
| --- | --- | --- |
| agregacion-indicadores | bip_lugares_carga, calendario_medicion, carga_nocturna, cobertura_de_carga, correspondencia_metro, education, gtfs_red_movilidad, retail, transport | 9 |
| calidad-datos | bip_lugares_carga, calendario_medicion, carga_nocturna, cobertura_de_carga, correspondencia_metro, education, gtfs_red_movilidad, retail, transport | 9 |
| comunicacion-resultados | bip_lugares_carga, calendario_medicion, carga_nocturna, cobertura_de_carga, correspondencia_metro, education, gtfs_red_movilidad, retail | 8 |
| reproducibilidad | bip_lugares_carga, calendario_medicion, carga_nocturna, cobertura_de_carga, correspondencia_metro, gtfs_red_movilidad, transport | 7 |
| validacion-independiente | bip_lugares_carga, calendario_medicion, carga_nocturna, cobertura_de_carga, correspondencia_metro, gtfs_red_movilidad, transport | 7 |
| cruce-consolidacion | bip_lugares_carga, carga_nocturna, cobertura_de_carga, correspondencia_metro, gtfs_red_movilidad, transport | 6 |
| limpieza-normalizacion | bip_lugares_carga, carga_nocturna, correspondencia_metro, gtfs_red_movilidad, retail, transport | 6 |
| lectura-escritura-datos | bip_lugares_carga, education, gtfs_red_movilidad, retail, transport | 5 |
| apoyo-decision | calendario_medicion, carga_nocturna, cobertura_de_carga, correspondencia_metro | 4 |
| fechas-horarios | calendario_medicion, carga_nocturna, gtfs_red_movilidad, transport | 4 |
| gobernanza-datos | bip_lugares_carga, calendario_medicion, carga_nocturna, correspondencia_metro | 4 |
| hojas-de-calculo | bip_lugares_carga, education, retail, transport | 4 |
| estadistica-descriptiva | cobertura_de_carga, education, transport | 3 |
| ingenieria-datos | gtfs_red_movilidad | 1 |
| sql | transport | 1 |
| visualizacion | transport | 1 |

## Cómo agregar un caso

```powershell
uv run python scripts/new_case.py mi-caso
```

Luego complete `cases/mi-caso/case.json` con los 26 campos obligatorios y
`uv run python -m pytest tests/test_catalog.py` para validarlo.
