# Matriz de validación de los cuadernos

Fecha de corte: **28 de noviembre de 2026**.

## Leyenda

- **ER**: validado mediante ejecución real en este entorno.
- **CI**: verificado mediante una prueba automatizada en un runner limpio.
- **CD**: compatibilidad documentada, pendiente de ejecución en la plataforma.
- **NC**: no compatible o no aplicable; se explica debajo.

Todos los cuadernos conservan los pasos Pandas originales y publican
`solucion_pandas.py`, `solucion_polars.py`, `solucion.R` y `solucion.Rmd`. Las pruebas
exportan el resultado de cada motor, comparan los valores con tolerancia `1e-9` y exigen
un PNG no vacío en los dos sistemas de visualización.

| Caso / problemas | Pandas + Matplotlib | Polars + Matplotlib | R + ggplot2 | Comentarios y pedagogía | Datos y trazabilidad | Equivalencia | Gráficas | Python local/CI | Colab | R CI | R local | RStudio | Posit | IRkernel | Dependencias | Referencias | Correcciones | Estado |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `bip_lugares_carga` · P01/P02/P04 | ER/CI | ER/CI | CI | CI | CI | ER/CI | ER/CI | ER/CI | CD | CI | CD | CD | CD | CD | CI | CI | sí, 4 pasos añadidos | conforme |
| `correspondencia_metro` · P03/P10 | ER/CI | ER/CI | CI | CI | CI | ER/CI | ER/CI | ER/CI | CD | CI | CD | CD | CD | CD | CI | CI | sí, fuente Colab | conforme |
| `carga_nocturna` · P05/P09 | ER/CI | ER/CI | CI | CI | CI | ER/CI | ER/CI | ER/CI | CD | CI | CD | CD | CD | CD | CI | CI | sí, fuente Colab | conforme |
| `gtfs_red_movilidad` · P06 | ER/CI | ER/CI | CI | CI | CI | ER/CI | ER/CI | ER/CI | CD | CI | CD | CD | CD | CD | CI | CI | sí, trío y guía | conforme |
| `rendimiento_gtfs` · P07 | ER/CI | ER/CI | CI | CI | CI | ER/CI | ER/CI | ER/CI | CD | CI | CD | CD | CD | CD | CI | CI | sí, trío y guía | conforme |
| `cobertura_de_carga` · P08 | ER/CI | ER/CI | CI | CI | CI | ER/CI | ER/CI | ER/CI | CD | CI | CD | CD | CD | CD | CI | CI | sí, fuente Colab | conforme |
| `calendario_medicion` · P11 | ER/CI | ER/CI | CI | CI | CI | ER/CI | ER/CI | ER/CI | CD | CI | CD | CD | CD | CD | CI | CI | sí, trío y guía | conforme |
| `frecuencia_programada` · P12/P13 | ER/CI | ER/CI | CI | CI | CI | ER/CI | ER/CI | ER/CI | CD | CI | CD | CD | CD | CD | CI | CI | sí, trío y guía | conforme |
| `evolucion_gtfs` · P14/P15 | ER/CI | ER/CI | CI | CI | CI | ER/CI | ER/CI | ER/CI | CD | CI | CD | CD | CD | CD | CI | CI | sí, trío y guía | conforme |
| `informe_decision_carga` · P16 | ER/CI | ER/CI | CI | CI | CI | ER/CI | ER/CI | ER/CI | CD | CI | CD | CD | CD | CD | CI | CI | sí, trío y guía | conforme |
| `gobernanza_datos_dtpm` · P17 | ER/CI | ER/CI | CI | CI | CI | ER/CI | ER/CI | ER/CI | CD | CI | CD | CD | CD | CD | CI | CI | caso nuevo completo | conforme |
| `etl_gtfs_automatizado` · P18 | ER/CI | ER/CI | CI | CI | CI | ER/CI | ER/CI | ER/CI | CD | CI | CD | CD | CD | CD | CI | CI | caso nuevo completo | conforme |
| `red_correspondencias_dtpm` · P19 | ER/CI | ER/CI | CI | CI | CI | ER/CI | ER/CI | ER/CI | CD | CI | CD | CD | CD | CD | CI | CI | caso nuevo completo | conforme |

## Qué cubre cada columna transversal

- **Comentarios y pedagogía:** problema, objetivo, fuente, diccionario observado,
  fórmula, decisión técnica, interpretación, gráfico, error frecuente y comparación de
  ventajas/límites están presentes y protegidos por pruebas estructurales.
- **Datos y trazabilidad:** los tres motores leen el mismo CSV versionado; `case.json`,
  `procedencia.json` y `lab.sources` conservan origen, formato, licencia, fecha y huella
  cuando están disponibles. Los datos sintéticos se identifican como tales.
- **Equivalencia:** ejecución de scripts con `--salida`, comparación de DataFrames con
  tolerancia `1e-9` y validación de archivos gráficos.
- **Dependencias:** Python se fija mediante `uv.lock`; Colab instala rangos compatibles;
  CI instala R, `readr`, `dplyr` y `ggplot2` en un runner nuevo.
- **Referencias:** el generador enumera P01–P19 y representa juntos P01/P02/P04 donde el
  contenido es transversal, sin renumerar los problemas.

## Límites declarados

- Colab, RStudio Desktop, Posit Cloud e IRkernel no se ejecutaron de forma interactiva
  en esta entrega; por eso figuran como **CD**, no como ER.
- R no estaba instalado en el equipo Windows local. Su ejecución real corresponde al
  job limpio `multitecnologia` de GitHub Actions (**CI**).
- R en Colab es condicional y no forma parte del runtime Python estándar; se documenta
  como alternativa, no como plataforma garantizada.
- La disponibilidad futura de una fuente externa no se puede prometer. El registro de
  procedencia, la huella y los resultados versionados permiten detectar cambios y
  conservar el laboratorio comparable sin presentar el resultado como dato oficial.
