# Fuentes y contratos de datos de los cuadernos

Este índice centraliza cómo se obtiene cada fuente sin reemplazar la ficha específica
de `cases/<caso>/case.json`. Las URLs técnicas, publicador, descripción, tipo de medio y
licencia viven en `lab/sources.py`; las descargas dejan URL resuelta, fecha, tamaño y
SHA-256 en un archivo `*.procedencia.json`.

| Caso / problemas | Fuente primaria | Formato | Obtención reproducible | Licencia / condición | Contrato comparable y alternativa |
| --- | --- | --- | --- | --- | --- |
| `bip_lugares_carga` · P01/P02/P04 | cinco archivos de lugares bip!, Subsecretaría de Transporte | XLSX, seis hojas | `fetch_data.py bip-metro ... bip-retail` | CC BY-NC 2.0 verificada | `resultados/por_comuna.csv` |
| `correspondencia_metro` · P03/P10 | lugares bip! + GTFS vigente DTPM | XLSX + ZIP/CSV | cinco fuentes bip! + `gtfs-red-movilidad` | bip! verificada; GTFS no verificada | `resultados/detectores.csv` |
| `carga_nocturna` · P05/P09 | lugares bip! + GTFS vigente DTPM | XLSX + ZIP/CSV | cinco fuentes bip! + `gtfs-red-movilidad` | bip! verificada; GTFS no verificada | `resultados/respuesta.csv` |
| `gtfs_red_movilidad` · P06 | GTFS vigente DTPM | ZIP con CSV/TXT | `fetch_data.py gtfs-red-movilidad` | licencia no verificada; no redistribuir | `resultados/salidas_por_hora.csv` |
| `rendimiento_gtfs` · P07 | mismo GTFS vigente | ZIP con CSV/TXT | `fetch_data.py gtfs-red-movilidad` | licencia no verificada | `resultados/benchmark.csv` |
| `cobertura_de_carga` · P08 | lugares bip! + GTFS vigente | XLSX + ZIP/CSV | cinco fuentes bip! + `gtfs-red-movilidad` | condiciones combinadas anteriores | `resultados/cobertura_por_umbral.csv` |
| `calendario_medicion` · P11 | metodología pública + lista de feriados de tercero declarada | CSV versionado | `cases/calendario_medicion/feriados.csv` | fuente de feriados no oficial y licencia no verificada | `resultados/comparacion_anios.csv` |
| `frecuencia_programada` · P12/P13 | GTFS vigente + definición pública del indicador | ZIP/CSV + documento | `fetch_data.py gtfs-red-movilidad` | GTFS no verificada; documento se cita | `resultados/distribucion.csv` |
| `evolucion_gtfs` · P14/P15 | GTFS históricos 2024/2025 y vigente | ZIP con publicaciones anidadas | `fetch_data.py gtfs-historicos-2024`, `...2025`, `gtfs-red-movilidad` | licencia no verificada | `resultados/oferta_total.csv` |
| `informe_decision_carga` · P16 | resultados reproducibles de P06 y P08 | CSV versionados | incluidos en el repositorio | heredan la trazabilidad de los casos fuente | `resultados/resumen.csv` |
| `gobernanza_datos_dtpm` · P17 | procedencia documentada por P01–P16 | catálogo pedagógico CSV | incluido y versionado en el repositorio | no es catálogo oficial; conserva estados no declarados | `resultados/riesgo_por_activo.csv` |
| `etl_gtfs_automatizado` · P18 | inventario reproducible de P14/P15 | CSV; Parquet opcional | incluido en el repositorio | hereda licencia GTFS no verificada; Parquet declara estado real | `resultados/volumen_por_publicacion.csv` |
| `red_correspondencias_dtpm` · P19 | correspondencias P03/P10 | CSV versionado | incluido en el repositorio | hereda fuentes públicas GTFS/bip! y sus condiciones | `resultados/servicios_centrales.csv` |
| `optimizacion_carga_bip` · P20 | lista corta de P16 | CSV versionado | incluido en el repositorio | hereda la trazabilidad P16; bandas relativas no oficiales | `resultados/frontera_presupuesto.csv` |

## Estructura y diccionario

Cada `CUADERNO.md` genera un diccionario de las columnas que realmente leen Pandas,
Polars y R, con tipo observado y función (eje X, medida Y o campo auxiliar). El
diccionario completo del caso, sus supuestos y reglas de limpieza están en `case.json` y
en las constantes documentadas de `solution.py`. Para GTFS se conservan los nombres del
estándar (`trips`, `stop_times`, `frequencies`, `calendar`, `stops`) y el cuaderno
explica las horas de día de servicio mayores que 24.

## Validación y recuperación

1. Liste antes de descargar: `python scripts/fetch_data.py --listar`.
2. Descargue por el nombre estable del catálogo, no pegando una URL temporal.
3. Si dispone de una copia conocida, compare SHA-256 con `procedencia.json` antes de
   usarla. `fetch_data.py --sha256 <huella>` rechaza una descarga diferente.
4. Valide extensión, tipo de medio, columnas y tamaños antes de analizar.
5. Si la fuente cambia, conserve la fecha y la huella nuevas y regenere resultados; no
   mezcle publicaciones bajo un mismo rótulo.
6. Si la fuente no está disponible, los CSV de `resultados/` permiten estudiar el
   indicador comparable. No permiten afirmar que se reejecutó la adquisición completa.

Los datos sintéticos de `transport`, `retail` y `education` están identificados como
sintéticos y usan semilla fija. Ningún cuaderno presenta esos datos como oficiales.
