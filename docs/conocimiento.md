<!-- Archivo generado por scripts/build_docs.py. No lo edite a mano: modifique el código fuente y vuelva a ejecutar el script. -->

# Índice de la base de conocimiento

**40 registros**. Búsqueda: `python -m lab.knowledge "consulta"`.

## Por tipo

| Tipo | Registros |
| --- | --- |
| concepto | 3 |
| definicion | 3 |
| error | 8 |
| formula | 3 |
| leccion | 7 |
| metodologia | 5 |
| patron | 11 |

## Registros

| Tipo | Registro | Título | Etiquetas |
| --- | --- | --- | --- |
| concepto | [`correlacion-no-es-causalidad`](../knowledge/correlacion-no-es-causalidad.md) | Qué permite y qué no permite concluir una correlación | estadistica, inferencia-estadistica, pensamiento-critico, errores-frecuentes |
| concepto | [`tasa-ponderada-vs-promedio-simple`](../knowledge/tasa-ponderada-vs-promedio-simple.md) | Tasa ponderada frente a promedio simple de porcentajes | estadistica, indicadores, denominadores, errores-frecuentes |
| concepto | [`vacio-no-es-cero`](../knowledge/vacio-no-es-cero.md) | Ausente, cero e inválido son tres estados distintos | calidad-datos, limpieza-normalizacion, pandas, sql, excel |
| definicion | [`count-asterisco-vs-columna`](../knowledge/count-asterisco-vs-columna.md) | COUNT(*) frente a COUNT(columna) y su equivalente en Pandas y Excel | sql, pandas, excel, equivalencias, calidad-datos |
| definicion | [`puntos-porcentuales-vs-porcentaje`](../knowledge/puntos-porcentuales-vs-porcentaje.md) | Puntos porcentuales frente a variación porcentual | indicadores, comunicacion-resultados, errores-frecuentes |
| definicion | [`valor-p-que-significa`](../knowledge/valor-p-que-significa.md) | Qué es y qué no es un valor p | estadistica, inferencia-estadistica, errores-frecuentes |
| error | [`agregado-que-suaviza`](../knowledge/agregado-que-suaviza.md) | Un agregado que reduce varias filas a una suaviza el error en lugar de mostrarlo | errores-frecuentes, calidad-datos, pandas, geoespacial, indicadores |
| error | [`clave-falla-al-volver`](../knowledge/clave-falla-al-volver.md) | Una clave que no es única no falla al cruzar: falla al volver, y a veces no falla | calidad-datos, cruce-consolidacion, errores-frecuentes, pandas, datos-reales |
| error | [`clave-que-no-es-clave`](../knowledge/clave-que-no-es-clave.md) | Una columna llamada «código» no es una clave hasta que se mide | calidad-datos, cruce-consolidacion, datos-reales, errores-frecuentes |
| error | [`countifs-cadena-vacia`](../knowledge/countifs-cadena-vacia.md) | CONTAR.SI.CONJUNTO con "<>" cuenta las celdas que devuelven cadena vacía | excel, hojas-de-calculo, indicadores, errores-frecuentes |
| error | [`horario-relativo-vs-absoluto`](../knowledge/horario-relativo-vs-absoluto.md) | Una columna de hora que no contiene horas | fechas-horarios, calidad-datos, gtfs, errores-frecuentes, datos-reales |
| error | [`julianday-precision`](../knowledge/julianday-precision.md) | julianday en SQLite invierte las comparaciones de duración en los empates | sql, sqlite, fechas-horarios, punto-flotante, validacion-independiente |
| error | [`relleno-de-ceros-y-orden`](../knowledge/relleno-de-ceros-y-orden.md) | El relleno de ceros irregular invierte el orden como texto | fechas-horarios, calidad-datos, pandas, excel, sql, errores-frecuentes, datos-reales |
| error | [`sesgo-con-eje`](../knowledge/sesgo-con-eje.md) | La distancia euclídea sobre grados no es una aproximación: es un sesgo con eje | geoespacial, errores-frecuentes, estadistica, pandas, datos-reales |
| formula | [`duracion-en-minutos-tres-herramientas`](../knowledge/duracion-en-minutos-tres-herramientas.md) | Duración en minutos en Pandas, Excel y SQL | fechas-horarios, pandas, excel, sql, equivalencias |
| formula | [`intervalo-de-confianza`](../knowledge/intervalo-de-confianza.md) | Intervalo de confianza de una media y de una proporción | estadistica, inferencia-estadistica, formulas, incertidumbre |
| formula | [`progresion-sin-expandir`](../knowledge/progresion-sin-expandir.md) | Contar eventos periódicos en una ventana no necesita generar los eventos | pandas, fechas-horarios, ingenieria-datos, formulas, gtfs |
| leccion | [`atajo-verosimil`](../knowledge/atajo-verosimil.md) | El atajo peligroso no es el que da una cifra absurda, es el que da una cifra verosímil | errores-frecuentes, pensamiento-critico, calidad-datos, gtfs, fechas-horarios |
| leccion | [`cambiar-la-pregunta`](../knowledge/cambiar-la-pregunta.md) | Cuando el dato no está, a veces lo honesto es cambiar la pregunta y no el dato | pensamiento-critico, gobernanza-datos, comunicacion-resultados, metodologia, incertidumbre |
| leccion | [`defecto-que-no-existe`](../knowledge/defecto-que-no-existe.md) | Un cruce que falla puede estar diciendo que el cruce no correspondía | calidad-datos, cruce-consolidacion, pensamiento-critico, datos-reales, errores-frecuentes |
| leccion | [`dos-coordenadas-un-lugar`](../knowledge/dos-coordenadas-un-lugar.md) | Un dato redundante permite validar el archivo contra sí mismo | validacion-independiente, calidad-datos, gobernanza-datos, datos-reales, geoespacial |
| leccion | [`punto-ciego-del-control`](../knowledge/punto-ciego-del-control.md) | Toda comprobación de calidad tiene un punto ciego, y el punto ciego es medible | calidad-datos, gobernanza-datos, validacion-independiente, pensamiento-critico, errores-frecuentes |
| leccion | [`que-fuente-provee-el-campo`](../knowledge/que-fuente-provee-el-campo.md) | Qué fuente provee cada campo es una decisión metodológica, y casi nunca se declara | gobernanza-datos, metodologia, comunicacion-resultados, calidad-datos, indicadores |
| leccion | [`vacio-concentrado`](../knowledge/vacio-concentrado.md) | Un vacío uniforme es un problema de captura; concentrado en un archivo, es una decisión | gobernanza-datos, calidad-datos, datos-reales, pensamiento-critico, comunicacion-resultados |
| metodologia | [`cobertura-de-un-indicador`](../knowledge/cobertura-de-un-indicador.md) | Informar la cobertura junto con el indicador | calidad-datos, indicadores, comunicacion-resultados, metodologia |
| metodologia | [`cruce-sin-clave`](../knowledge/cruce-sin-clave.md) | Cuando no hay clave compartida, el criterio de emparejamiento es la mitad del resultado | cruce-consolidacion, metodologia, geoespacial, pensamiento-critico, datos-reales |
| metodologia | [`denominador-es-una-decision`](../knowledge/denominador-es-una-decision.md) | El denominador de un indicador oficial es una decisión, no un dato | indicadores, gobernanza-datos, denominadores, metodologia, datos-reales |
| metodologia | [`hecho-inferencia-hipotesis`](../knowledge/hecho-inferencia-hipotesis.md) | Distinguir hecho, evidencia, inferencia, interpretación e hipótesis | metodologia, investigacion-aplicada, comunicacion-resultados, pensamiento-critico |
| metodologia | [`supuesto-medido`](../knowledge/supuesto-medido.md) | Un supuesto que no se puede resolver se mide | metodologia, incertidumbre, comunicacion-resultados, gobernanza-datos, datos-reales |
| patron | [`cruce-con-cardinalidad`](../knowledge/cruce-con-cardinalidad.md) | Cruzar tablas controlando la cardinalidad | cruce-consolidacion, calidad-datos, pandas, sql, excel, equivalencias |
| patron | [`denominador-cero`](../knowledge/denominador-cero.md) | Razones con denominador cero o ausente | indicadores, calidad-datos, excel, pandas, errores-frecuentes |
| patron | [`dos-afirmaciones-de-la-misma-fila`](../knowledge/dos-afirmaciones-de-la-misma-fila.md) | Dos campos que describen lo mismo son dos afirmaciones independientes, y se pueden contrastar | calidad-datos, validacion-independiente, geoespacial, datos-reales, pensamiento-critico |
| patron | [`encabezado-no-esta-en-la-primera-fila`](../knowledge/encabezado-no-esta-en-la-primera-fila.md) | Detectar la fila del encabezado en una planilla maquetada para imprimir | excel, hojas-de-calculo, lectura-escritura-datos, datos-reales, calidad-datos |
| patron | [`expandir-frecuencias`](../knowledge/expandir-frecuencias.md) | Expandir una ventana con cadencia a sus eventos reales | agregacion-indicadores, pandas, gtfs, datos-reales, denominadores |
| patron | [`grano-antes-de-cruzar`](../knowledge/grano-antes-de-cruzar.md) | Antes de cruzar dos inventarios, nombrar el grano de cada uno y cerrar la identidad | cruce-consolidacion, calidad-datos, metodologia, datos-reales, gobernanza-datos |
| patron | [`intervalo-en-vez-de-cifra`](../knowledge/intervalo-en-vez-de-cifra.md) | Cuando el denominador tiene huecos, el indicador es un intervalo y su ancho es otro indicador | indicadores, incertidumbre, comunicacion-resultados, gobernanza-datos, denominadores |
| patron | [`normalizar-antes-de-agrupar`](../knowledge/normalizar-antes-de-agrupar.md) | Normalizar para agrupar y conservar la etiqueta para informar | limpieza-normalizacion, cruce-consolidacion, pandas, datos-reales, comunicacion-resultados |
| patron | [`regla-redundante`](../knowledge/regla-redundante.md) | Distinguir una regla redundante por construcción de una redundante por azar | indicadores, gobernanza-datos, metodologia, datos-reales, pensamiento-critico |
| patron | [`tres-respuestas-no-dos`](../knowledge/tres-respuestas-no-dos.md) | Un indicador construido sobre datos incompletos necesita tres respuestas, no dos | calidad-datos, gobernanza-datos, indicadores, incertidumbre, comunicacion-resultados |
| patron | [`unidad-de-la-decision`](../knowledge/unidad-de-la-decision.md) | El error de un método se mide en la unidad de la decisión, no en la del cálculo | pensamiento-critico, comunicacion-resultados, calidad-datos, estadistica, indicadores |
