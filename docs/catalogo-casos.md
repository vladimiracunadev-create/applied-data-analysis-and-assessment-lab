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
| [`education`](../cases/education/README.md) | Asistencia ponderada por establecimiento | analisis-de-datos | educacion | introductorio | implementado | 90 min | sí |
| [`gtfs_red_movilidad`](../cases/gtfs_red_movilidad/README.md) | Expediciones por hora en la Red Metropolitana de Movilidad (datos públicos reales) | ingenieria-de-datos | transporte | especializado | implementado | 180 min | sí |
| [`retail`](../cases/retail/README.md) | Ventas netas, margen y devoluciones por producto | analisis-de-negocios | comercio | intermedio | implementado | 90 min | sí |
| [`transport`](../cases/transport/README.md) | Indicadores operacionales de transporte público | analisis-de-datos | transporte | avanzado | implementado | 240 min | sí |

## Cobertura de competencias

Cuántos casos entrenan cada competencia. Las competencias con cero casos están
declaradas en la hoja de ruta como brechas conocidas.

| competencia | casos | cantidad |
| --- | --- | --- |
| agregacion-indicadores | bip_lugares_carga, education, gtfs_red_movilidad, retail, transport | 5 |
| calidad-datos | bip_lugares_carga, education, gtfs_red_movilidad, retail, transport | 5 |
| lectura-escritura-datos | bip_lugares_carga, education, gtfs_red_movilidad, retail, transport | 5 |
| comunicacion-resultados | bip_lugares_carga, education, gtfs_red_movilidad, retail | 4 |
| hojas-de-calculo | bip_lugares_carga, education, retail, transport | 4 |
| limpieza-normalizacion | bip_lugares_carga, gtfs_red_movilidad, retail, transport | 4 |
| cruce-consolidacion | bip_lugares_carga, gtfs_red_movilidad, transport | 3 |
| reproducibilidad | bip_lugares_carga, gtfs_red_movilidad, transport | 3 |
| validacion-independiente | bip_lugares_carga, gtfs_red_movilidad, transport | 3 |
| estadistica-descriptiva | education, transport | 2 |
| fechas-horarios | gtfs_red_movilidad, transport | 2 |
| gobernanza-datos | bip_lugares_carga | 1 |
| ingenieria-datos | gtfs_red_movilidad | 1 |
| sql | transport | 1 |
| visualizacion | transport | 1 |

## Cómo agregar un caso

```powershell
uv run python scripts/new_case.py mi-caso
```

Luego complete `cases/mi-caso/case.json` con los 26 campos obligatorios y
`uv run python -m pytest tests/test_catalog.py` para validarlo.
