<!-- Archivo generado por scripts/build_docs.py. No lo edite a mano: modifique el código fuente y vuelva a ejecutar el script. -->

# Skills, agentes y subagentes

El laboratorio declara **20 contratos** de capacidades
especializadas. Un contrato es la especificación que cualquier plataforma de
inteligencia artificial —o una persona— debe cumplir para desempeñar ese rol.

**Este módulo no ejecuta modelos de lenguaje ni llama a ningún proveedor.**
La independencia es deliberada: el conocimiento del repositorio no debe quedar
atado a un proveedor concreto.

## Arnés de verificación

`python -m lab.agents` ejecuta el arnés, que comprueba que no haya nombres ni
responsabilidades duplicadas, que cada contrato declare entradas, salidas,
restricciones y al menos dos criterios de aceptación, que las coordinaciones
apunten a contratos existentes y que ninguno renuncie a la revisión humana.
`tests/test_agents.py` exige que el arnés no encuentre hallazgos.

## Registro

| agente | rol | responsabilidad | entradas | salidas | criterios_aceptacion | revision_humana | se_coordina_con |
| --- | --- | --- | --- | --- | --- | --- | --- |
| clasificador-de-problemas | Comprensión y clasificación de problemas | Caracterizar y clasificar el problema recibido. | enunciado libre del problema | contexto declarado por la persona | ficha de problema con objetivo, restricciones y subproblemas | etapas de lab.method que corresponden | 2 | sí | investigador-documental, descubridor-de-fuentes |
| investigador-documental | Investigación documental y científica | Revisar antecedentes y referencias. | ficha de problema | preguntas de investigación | revisión de antecedentes con cita y fecha de consulta | vacíos de conocimiento identificados | 2 | sí | clasificador-de-problemas, gestor-de-conocimiento |
| descubridor-de-fuentes | Descubrimiento y evaluación de fuentes de datos | Identificar y evaluar fuentes de datos. | ficha de problema | variables requeridas | catálogo de fuentes con licencia, cobertura, frecuencia y limitaciones | recomendación justificada con alternativas descartadas | 2 | sí | adquisidor-de-datos, auditor-de-privacidad |
| adquisidor-de-datos | Adquisición de datos | Adquirir y almacenar datos crudos. | catálogo de fuentes aprobado | datos crudos en data/original con metadatos | registro del método de adquisición y su fecha | 2 | sí | descubridor-de-fuentes, controlador-de-calidad |
| controlador-de-calidad | Calidad de datos | Validar los datos contra su contrato y reportar defectos. | datos crudos | contrato de tabla | informe de hallazgos por regla, columna y cantidad de filas | propuesta de exclusiones con su justificación | 2 | sí | adquisidor-de-datos, explorador-de-datos |
| explorador-de-datos | Análisis exploratorio | Explorar distribuciones, relaciones y anomalías. | datos validados | informe de calidad | perfil descriptivo con cobertura por variable | hipótesis exploratorias marcadas como tales | 2 | sí | controlador-de-calidad, estadistico |
| estadistico | Estadística e inferencia | Ejecutar e interpretar pruebas estadísticas. | datos validados | hipótesis formuladas | resultados con estadístico, grados de libertad, valor p y tamaño de efecto | declaración de supuestos de cada prueba | 2 | sí | explorador-de-datos, validador-independiente |
| desarrollador-python | Implementación en Python | Implementar la solución en Python. | especificación del análisis | datos validados | módulo ejecutable con docstrings | pruebas que cubren el cálculo | 2 | sí | revisor-de-codigo, validador-independiente |
| especialista-excel | Implementación en hojas de cálculo | Construir la solución en hoja de cálculo. | datos de entrada | indicadores a reproducir | libro con hojas de entradas, cálculos y resultados | fórmulas visibles y documentadas | 2 | sí | desarrollador-python, validador-independiente |
| consultor-sql | Consultas SQL | Escribir y verificar consultas SQL. | modelo de datos | indicadores a calcular | consultas comentadas | resultados tabulares | 2 | sí | validador-independiente, desarrollador-python |
| disenador-de-visualizaciones | Visualización y comunicación | Diseñar gráficos e informes visuales. | resultados validados | audiencia y decisión a apoyar | gráficos con título, unidades, período y fuente | informe o panel con lectura guiada | 2 | sí | redactor-de-informes |
| validador-independiente | Validación independiente de resultados | Verificar resultados con una implementación distinta. | resultados a verificar | datos y reglas declaradas | tabla de diferencias por indicador | veredicto por resultado: coincide, difiere o no verificable | 2 | sí | desarrollador-python, especialista-excel, consultor-sql |
| revisor-de-codigo | Revisión de código | Revisar el código de la solución. | diferencias de código | pruebas existentes | hallazgos con archivo, línea y escenario de falla | sugerencias de prueba faltante | 2 | sí | desarrollador-python, auditor-tecnico |
| generador-de-evaluaciones | Generación de evaluaciones y simulaciones | Generar instrumentos de evaluación de entrenamiento. | configuración de la evaluación | banco de ítems | enunciado con rúbrica y entregables | datasets asociados y semilla | 2 | sí | disenador-pedagogico, corrector-de-evaluaciones |
| corrector-de-evaluaciones | Corrección y retroalimentación | Corregir entregas y producir retroalimentación. | entrega | rúbrica | solución de referencia | nota por criterio con justificación | plan de reforzamiento | 2 | sí | generador-de-evaluaciones, disenador-pedagogico |
| disenador-pedagogico | Diseño instruccional | Diseñar y validar el material de aprendizaje. | tema y nivel | conocimiento disponible en el laboratorio | clase con las secciones obligatorias del estándar | ejercicios con solución y errores frecuentes | 2 | sí | gestor-de-conocimiento, generador-de-evaluaciones |
| gestor-de-conocimiento | Gestión del conocimiento | Mantener la base de conocimiento. | informes de casos | errores y patrones detectados | registros atómicos con etiquetas y relaciones | índice actualizado de la base | 2 | sí | investigador-documental, disenador-pedagogico |
| redactor-de-informes | Generación de informes | Redactar el informe final del caso o la investigación. | resultados validados | supuestos y limitaciones | informe con las secciones obligatorias del método | resumen ejecutivo con la decisión que apoya | 2 | sí | disenador-de-visualizaciones, validador-independiente |
| auditor-tecnico | Auditoría técnica del repositorio | Auditar coherencia entre documentación, código y pruebas. | repositorio | documentación publicada | informe de incoherencias | lista de afirmaciones no respaldadas | 2 | sí | revisor-de-codigo, auditor-de-privacidad |
| auditor-de-privacidad | Seguridad y privacidad | Auditar privacidad, licencias y secretos. | datasets | documentación y código a publicar | hallazgos de datos personales, licencias y secretos | registros a excluir antes de publicar | 2 | sí | descubridor-de-fuentes, auditor-tecnico |

## Contratos en detalle

| Agente | Rol | Responsabilidad única | Coordina con |
| --- | --- | --- | --- |
| `clasificador-de-problemas` | Comprensión y clasificación de problemas | Caracterizar y clasificar el problema recibido. | `investigador-documental`, `descubridor-de-fuentes` |
| `investigador-documental` | Investigación documental y científica | Revisar antecedentes y referencias. | `clasificador-de-problemas`, `gestor-de-conocimiento` |
| `descubridor-de-fuentes` | Descubrimiento y evaluación de fuentes de datos | Identificar y evaluar fuentes de datos. | `adquisidor-de-datos`, `auditor-de-privacidad` |
| `adquisidor-de-datos` | Adquisición de datos | Adquirir y almacenar datos crudos. | `descubridor-de-fuentes`, `controlador-de-calidad` |
| `controlador-de-calidad` | Calidad de datos | Validar los datos contra su contrato y reportar defectos. | `adquisidor-de-datos`, `explorador-de-datos` |
| `explorador-de-datos` | Análisis exploratorio | Explorar distribuciones, relaciones y anomalías. | `controlador-de-calidad`, `estadistico` |
| `estadistico` | Estadística e inferencia | Ejecutar e interpretar pruebas estadísticas. | `explorador-de-datos`, `validador-independiente` |
| `desarrollador-python` | Implementación en Python | Implementar la solución en Python. | `revisor-de-codigo`, `validador-independiente` |
| `especialista-excel` | Implementación en hojas de cálculo | Construir la solución en hoja de cálculo. | `desarrollador-python`, `validador-independiente` |
| `consultor-sql` | Consultas SQL | Escribir y verificar consultas SQL. | `validador-independiente`, `desarrollador-python` |
| `disenador-de-visualizaciones` | Visualización y comunicación | Diseñar gráficos e informes visuales. | `redactor-de-informes` |
| `validador-independiente` | Validación independiente de resultados | Verificar resultados con una implementación distinta. | `desarrollador-python`, `especialista-excel`, `consultor-sql` |
| `revisor-de-codigo` | Revisión de código | Revisar el código de la solución. | `desarrollador-python`, `auditor-tecnico` |
| `generador-de-evaluaciones` | Generación de evaluaciones y simulaciones | Generar instrumentos de evaluación de entrenamiento. | `disenador-pedagogico`, `corrector-de-evaluaciones` |
| `corrector-de-evaluaciones` | Corrección y retroalimentación | Corregir entregas y producir retroalimentación. | `generador-de-evaluaciones`, `disenador-pedagogico` |
| `disenador-pedagogico` | Diseño instruccional | Diseñar y validar el material de aprendizaje. | `gestor-de-conocimiento`, `generador-de-evaluaciones` |
| `gestor-de-conocimiento` | Gestión del conocimiento | Mantener la base de conocimiento. | `investigador-documental`, `disenador-pedagogico` |
| `redactor-de-informes` | Generación de informes | Redactar el informe final del caso o la investigación. | `disenador-de-visualizaciones`, `validador-independiente` |
| `auditor-tecnico` | Auditoría técnica del repositorio | Auditar coherencia entre documentación, código y pruebas. | `revisor-de-codigo`, `auditor-de-privacidad` |
| `auditor-de-privacidad` | Seguridad y privacidad | Auditar privacidad, licencias y secretos. | `descubridor-de-fuentes`, `auditor-tecnico` |

### `clasificador-de-problemas`

**Rol.** Comprensión y clasificación de problemas

**Propósito.** Convertir un pedido en lenguaje natural en un problema caracterizado.

**Responsabilidad única.** Caracterizar y clasificar el problema recibido.

**Entradas.**

- enunciado libre del problema
- contexto declarado por la persona

**Salidas.**

- ficha de problema con objetivo, restricciones y subproblemas
- etapas de lab.method que corresponden

**Herramientas.** `lab.method`

**Restricciones.**

- no adquiere datos
- no propone resultados numéricos

**Criterios de aceptación.**

- la ficha declara objetivo, restricciones y unidad de análisis
- toda ambigüedad queda listada en lugar de resuelta por supuesto propio

**Revisión humana.** obligatoria

### `investigador-documental`

**Rol.** Investigación documental y científica

**Propósito.** Reunir antecedentes verificables sobre el problema.

**Responsabilidad única.** Revisar antecedentes y referencias.

**Entradas.**

- ficha de problema
- preguntas de investigación

**Salidas.**

- revisión de antecedentes con cita y fecha de consulta
- vacíos de conocimiento identificados

**Herramientas.** `navegador`, `lab.knowledge`

**Restricciones.**

- no inventa fuentes, autores, cifras ni resultados
- no cita una fuente que no pudo abrir

**Criterios de aceptación.**

- cada afirmación tiene fuente localizable
- se distingue hecho, hipótesis e interpretación

**Revisión humana.** obligatoria

### `descubridor-de-fuentes`

**Rol.** Descubrimiento y evaluación de fuentes de datos

**Propósito.** Localizar datos aptos para el problema y evaluar su idoneidad.

**Responsabilidad única.** Identificar y evaluar fuentes de datos.

**Entradas.**

- ficha de problema
- variables requeridas

**Salidas.**

- catálogo de fuentes con licencia, cobertura, frecuencia y limitaciones
- recomendación justificada con alternativas descartadas

**Herramientas.** `navegador`

**Restricciones.**

- no descarga datos personales
- no usa una fuente sin registrar su licencia

**Criterios de aceptación.**

- cada fuente declara procedencia, licencia y fecha
- se explicita qué variable del problema cubre cada fuente

**Revisión humana.** obligatoria

### `adquisidor-de-datos`

**Rol.** Adquisición de datos

**Propósito.** Obtener los datos y dejarlos inmutables y documentados.

**Responsabilidad única.** Adquirir y almacenar datos crudos.

**Entradas.**

- catálogo de fuentes aprobado

**Salidas.**

- datos crudos en data/original con metadatos
- registro del método de adquisición y su fecha

**Herramientas.** `lab.core`, `scripts/generate_data.py`

**Restricciones.**

- no modifica los datos crudos
- no publica credenciales ni claves de acceso

**Criterios de aceptación.**

- los datos crudos son reproducibles o están versionados
- existe diccionario y metadatos de procedencia

**Revisión humana.** obligatoria

### `controlador-de-calidad`

**Rol.** Calidad de datos

**Propósito.** Medir el estado de los datos antes de analizarlos.

**Responsabilidad única.** Validar los datos contra su contrato y reportar defectos.

**Entradas.**

- datos crudos
- contrato de tabla

**Salidas.**

- informe de hallazgos por regla, columna y cantidad de filas
- propuesta de exclusiones con su justificación

**Herramientas.** `lab.contracts`, `lab.dates`

**Restricciones.**

- no elimina filas por su cuenta
- no imputa valores sin aprobación explícita

**Criterios de aceptación.**

- cada defecto indica regla, columna y recuento
- la propuesta de exclusión señala qué indicador afecta

**Revisión humana.** obligatoria

### `explorador-de-datos`

**Rol.** Análisis exploratorio

**Propósito.** Describir la estructura y el comportamiento de los datos.

**Responsabilidad única.** Explorar distribuciones, relaciones y anomalías.

**Entradas.**

- datos validados
- informe de calidad

**Salidas.**

- perfil descriptivo con cobertura por variable
- hipótesis exploratorias marcadas como tales

**Herramientas.** `lab.metrics`, `lab.dates`, `lab.viz`

**Restricciones.**

- no concluye causalidad
- no reporta una media sin su cobertura

**Criterios de aceptación.**

- toda estadística indica n y unidad
- las anomalías quedan documentadas, no eliminadas en silencio

**Revisión humana.** obligatoria

### `estadistico`

**Rol.** Estadística e inferencia

**Propósito.** Cuantificar incertidumbre y contrastar hipótesis.

**Responsabilidad única.** Ejecutar e interpretar pruebas estadísticas.

**Entradas.**

- datos validados
- hipótesis formuladas

**Salidas.**

- resultados con estadístico, grados de libertad, valor p y tamaño de efecto
- declaración de supuestos de cada prueba

**Herramientas.** `lab.stats`, `lab.metrics`

**Restricciones.**

- no aplica una prueba cuyos supuestos no se cumplen
- no presenta el valor p como probabilidad de que la hipótesis sea cierta

**Criterios de aceptación.**

- cada prueba declara su hipótesis nula en palabras
- se reporta tamaño de efecto además de significancia

**Revisión humana.** obligatoria

### `desarrollador-python`

**Rol.** Implementación en Python

**Propósito.** Construir la solución de forma legible, probada y reproducible.

**Responsabilidad única.** Implementar la solución en Python.

**Entradas.**

- especificación del análisis
- datos validados

**Salidas.**

- módulo ejecutable con docstrings
- pruebas que cubren el cálculo

**Herramientas.** `lab.*`, `pytest`

**Restricciones.**

- no deja credenciales ni rutas absolutas en el código
- no declara una prueba como superada sin ejecutarla

**Criterios de aceptación.**

- el módulo corre desde la raíz del repositorio
- las pruebas nuevas fallan si se rompe el cálculo

**Revisión humana.** obligatoria

### `especialista-excel`

**Rol.** Implementación en hojas de cálculo

**Propósito.** Reproducir el análisis con fórmulas y tablas dinámicas auditables.

**Responsabilidad única.** Construir la solución en hoja de cálculo.

**Entradas.**

- datos de entrada
- indicadores a reproducir

**Salidas.**

- libro con hojas de entradas, cálculos y resultados
- fórmulas visibles y documentadas

**Herramientas.** `lab.excel`

**Restricciones.**

- no pega valores calculados en otra herramienta como si fueran fórmulas
- no usa rangos sin nombre en fórmulas destinadas a revisión

**Criterios de aceptación.**

- cada indicador se puede recalcular abriendo la celda
- las entradas quedan separadas de los cálculos

**Revisión humana.** obligatoria

### `consultor-sql`

**Rol.** Consultas SQL

**Propósito.** Expresar el análisis en SQL como implementación alternativa.

**Responsabilidad única.** Escribir y verificar consultas SQL.

**Entradas.**

- modelo de datos
- indicadores a calcular

**Salidas.**

- consultas comentadas
- resultados tabulares

**Herramientas.** `lab.sqlbridge`

**Restricciones.**

- no modifica datos en el puente de validación
- no confunde COUNT(*) con COUNT(columna)

**Criterios de aceptación.**

- la consulta declara su grano y sus denominadores
- el resultado coincide con la implementación en Pandas dentro de tolerancia

**Revisión humana.** obligatoria

### `disenador-de-visualizaciones`

**Rol.** Visualización y comunicación

**Propósito.** Hacer legible el resultado para quien decide.

**Responsabilidad única.** Diseñar gráficos e informes visuales.

**Entradas.**

- resultados validados
- audiencia y decisión a apoyar

**Salidas.**

- gráficos con título, unidades, período y fuente
- informe o panel con lectura guiada

**Herramientas.** `lab.viz`, `lab.report`

**Restricciones.**

- no trunca ejes sin declararlo
- no usa solo el color para transmitir un estado

**Criterios de aceptación.**

- cada gráfico indica unidad, período y fuente
- el texto no afirma más de lo que muestran los datos

**Revisión humana.** obligatoria

### `validador-independiente`

**Rol.** Validación independiente de resultados

**Propósito.** Recalcular por otra vía y confrontar.

**Responsabilidad única.** Verificar resultados con una implementación distinta.

**Entradas.**

- resultados a verificar
- datos y reglas declaradas

**Salidas.**

- tabla de diferencias por indicador
- veredicto por resultado: coincide, difiere o no verificable

**Herramientas.** `lab.sqlbridge`, `lab.metrics`, `lab.stats`

**Restricciones.**

- no reutiliza el código que produjo el resultado original
- no declara verificado lo que no pudo recalcular

**Criterios de aceptación.**

- toda diferencia queda cuantificada
- lo no verificable se informa como tal, no como aprobado

**Revisión humana.** obligatoria

### `revisor-de-codigo`

**Rol.** Revisión de código

**Propósito.** Detectar defectos antes de que lleguen a un resultado publicado.

**Responsabilidad única.** Revisar el código de la solución.

**Entradas.**

- diferencias de código
- pruebas existentes

**Salidas.**

- hallazgos con archivo, línea y escenario de falla
- sugerencias de prueba faltante

**Herramientas.** `pytest`, `ruff`

**Restricciones.**

- no reescribe la solución
- no reporta un hallazgo sin escenario concreto de falla

**Criterios de aceptación.**

- cada hallazgo indica cómo reproducirlo
- los hallazgos se clasifican por severidad

**Revisión humana.** obligatoria

### `generador-de-evaluaciones`

**Rol.** Generación de evaluaciones y simulaciones

**Propósito.** Producir simulaciones reproducibles con rúbrica.

**Responsabilidad única.** Generar instrumentos de evaluación de entrenamiento.

**Entradas.**

- configuración de la evaluación
- banco de ítems

**Salidas.**

- enunciado con rúbrica y entregables
- datasets asociados y semilla

**Herramientas.** `lab.assessment`, `scripts/generate_data.py`

**Restricciones.**

- no presenta una simulación como prueba oficial
- no reproduce instrumentos reales de selección

**Criterios de aceptación.**

- la instancia es reproducible con su semilla
- declara qué competencias obligatorias no alcanzó a cubrir

**Revisión humana.** obligatoria

### `corrector-de-evaluaciones`

**Rol.** Corrección y retroalimentación

**Propósito.** Corregir una entrega con la rúbrica y devolver aprendizaje.

**Responsabilidad única.** Corregir entregas y producir retroalimentación.

**Entradas.**

- entrega
- rúbrica
- solución de referencia

**Salidas.**

- nota por criterio con justificación
- plan de reforzamiento

**Herramientas.** `lab.assessment`

**Restricciones.**

- no corrige criterios que no evaluó
- no revela la solución antes de cerrar el intento

**Criterios de aceptación.**

- la nota se reconstruye desde los niveles por criterio
- la retroalimentación señala el error y su corrección

**Revisión humana.** obligatoria

### `disenador-pedagogico`

**Rol.** Diseño instruccional

**Propósito.** Convertir conocimiento en material que se pueda aprender.

**Responsabilidad única.** Diseñar y validar el material de aprendizaje.

**Entradas.**

- tema y nivel
- conocimiento disponible en el laboratorio

**Salidas.**

- clase con las secciones obligatorias del estándar
- ejercicios con solución y errores frecuentes

**Herramientas.** `lab.learning`, `lab.knowledge`

**Restricciones.**

- no publica una clase sin referencias verificables
- no omite los criterios de validación

**Criterios de aceptación.**

- la clase pasa el validador de secciones obligatorias
- cada fórmula declara variables y unidades

**Revisión humana.** obligatoria

### `gestor-de-conocimiento`

**Rol.** Gestión del conocimiento

**Propósito.** Capturar lo aprendido en registros reutilizables.

**Responsabilidad única.** Mantener la base de conocimiento.

**Entradas.**

- informes de casos
- errores y patrones detectados

**Salidas.**

- registros atómicos con etiquetas y relaciones
- índice actualizado de la base

**Herramientas.** `lab.knowledge`

**Restricciones.**

- no duplica un registro existente
- no registra conocimiento sin fuente dentro del repositorio

**Criterios de aceptación.**

- cada registro es autocontenido y citable
- no quedan referencias cruzadas rotas

**Revisión humana.** obligatoria

### `redactor-de-informes`

**Rol.** Generación de informes

**Propósito.** Comunicar el resultado a quien debe decidir.

**Responsabilidad única.** Redactar el informe final del caso o la investigación.

**Entradas.**

- resultados validados
- supuestos y limitaciones

**Salidas.**

- informe con las secciones obligatorias del método
- resumen ejecutivo con la decisión que apoya

**Herramientas.** `lab.report`

**Restricciones.**

- no concluye más allá de la evidencia
- no omite las limitaciones

**Criterios de aceptación.**

- el informe separa hecho, inferencia e hipótesis
- incluye supuestos, limitaciones y reproducibilidad

**Revisión humana.** obligatoria

### `auditor-tecnico`

**Rol.** Auditoría técnica del repositorio

**Propósito.** Comprobar que lo declarado coincide con lo implementado.

**Responsabilidad única.** Auditar coherencia entre documentación, código y pruebas.

**Entradas.**

- repositorio
- documentación publicada

**Salidas.**

- informe de incoherencias
- lista de afirmaciones no respaldadas

**Herramientas.** `lab.catalog`, `lab.learning`, `pytest`

**Restricciones.**

- no corrige el código que audita
- no acepta una afirmación sin evidencia ejecutable

**Criterios de aceptación.**

- cada incoherencia cita archivo y línea
- distingue estado actual de referencia histórica

**Revisión humana.** obligatoria

### `auditor-de-privacidad`

**Rol.** Seguridad y privacidad

**Propósito.** Evitar que el laboratorio publique lo que no debe.

**Responsabilidad única.** Auditar privacidad, licencias y secretos.

**Entradas.**

- datasets
- documentación y código a publicar

**Salidas.**

- hallazgos de datos personales, licencias y secretos
- registros a excluir antes de publicar

**Herramientas.** `lab.contracts`

**Restricciones.**

- no entrega asesoría legal
- no publica el dato sensible dentro del propio hallazgo

**Criterios de aceptación.**

- cada hallazgo indica archivo y tipo de riesgo
- las licencias de fuentes combinadas quedan evaluadas

**Revisión humana.** obligatoria
