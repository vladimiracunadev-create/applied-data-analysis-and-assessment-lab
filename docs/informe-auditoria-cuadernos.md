# Informe de auditoría de cuadernos

Fecha: **27 de noviembre de 2026**.

## Hallazgos de la línea base

1. Los pasos Pandas no habían sido eliminados: seguían en `CUADERNO.md`, `pasos.py` y
   los módulos `cuaderno.py`. Sin embargo, no existía un `solucion_pandas.py` simétrico
   para comparar el indicador aislado con Polars y R.
2. Los cuadernos Colab mostraban Polars y R como bloques Markdown, pero no ejecutaban
   Polars ni instalaban su dependencia.
3. Las implementaciones alternativas transformaban tablas reales, pero carecían de un
   contrato pedagógico común, validación de columnas, exportación comparable y
   comentarios suficientes.
4. Las pruebas comprobaban que Polars y R producían un PNG, pero no confrontaban sus
   resultados contra Pandas para cada uno de los diez cuadernos.
5. P02 y P04 estaban cubiertos por el caso de P01 e incluidos en algunos índices, pero
   la identidad visible del cuaderno y varios accesos seguían nombrándolo sólo P01.
6. R carecía de un formato natural para RStudio/Posit Cloud y de instrucciones claras
   para IRkernel; Colab tampoco distinguía lo ejecutado de lo sólo compatible.

## Correcciones implementadas

- Se conservó el recorrido Pandas completo y se añadió un laboratorio paralelo con
  Pandas + Matplotlib, Polars + Matplotlib y R + `readr`/`dplyr`/ggplot2.
- Los tres scripts leen el mismo CSV, validan su esquema, aplican la misma regla,
  aceptan `--salida` y `--grafico`, y evitan rutas absolutas.
- Cada cuaderno explica objetivo, origen, diccionario, fórmula, alcance, interpretación,
  error frecuente, diferencias de semántica y límites de cada motor.
- Se añadió `solucion.Rmd` sin duplicar lógica: reutiliza `solucion.R`.
- Colab ahora detecta el entorno, clona de forma idempotente, instala Pandas/Polars y
  dependencias, registra versiones, obtiene datos con errores explícitos y ejecuta las
  dos implementaciones Python comparables mostrando sus gráficos.
- Se incorporaron accesos Colab en el índice, una guía portable y esta matriz de
  validación con estados honestos.
- Se reforzaron las pruebas para comparar Pandas ↔ Polars ↔ R con tolerancia `1e-9` y
  comprobar los artefactos Python, R, R Markdown, Colab y ZIP.

## Decisiones y límites

El laboratorio de tres motores usa una tabla de resultado versionada porque es la única
forma de aislar el efecto del motor sin triplicar cientos de líneas de adquisición y
limpieza ni redistribuir datos de terceros. La resolución completa y progresiva sigue
en los pasos Pandas; el contraste no se presenta como reemplazo. Esta separación queda
declarada en cada cuaderno para evitar confundir equivalencia del indicador con una
reescritura total del pipeline.

Las validaciones de servicios interactivos no se inventan: véase la
[matriz](matriz-validacion-cuadernos.md). La fuente de verdad de los conteos finales es
`pytest --collect-only`; la documentación se sincroniza después de ejecutar la suite.

## Ampliación P17 · 28 de noviembre de 2026

P17 agrega gobernanza explícita sin alterar P01–P16. Su catálogo es una elaboración
pedagógica basada en la procedencia documentada del repositorio y se identifica como tal;
no se presenta como catálogo oficial del DTPM. Las tres implementaciones confrontan el
mismo ranking de brechas y las pruebas verifican identidad, fórmula y artefactos.
