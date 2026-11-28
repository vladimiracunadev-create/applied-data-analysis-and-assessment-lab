# Documentación

Mapa de la documentación, organizado por lo que vienes a hacer. Si es tu primera vez,
el [README principal](../README.md) explica en una pantalla qué problema resuelve el
repositorio.

---

## Vengo a aprender a hacerlo, no a leer qué se encontró

**[Ruta de cuadernos](cuadernos.md)** — trece cuadernos en orden lineal para los
diecinueve problemas.

Los **cuadernos de trabajo** son el problema resuelto paso a paso, con Pandas y su
salida real, la fórmula de Excel equivalente y un laboratorio ejecutable equivalente
en Pandas, Polars y R con visualizaciones comparables.

Antes de ejecutar en otra plataforma consulte la [guía portable](ejecucion-portable.md)
y la [matriz de validación](matriz-validacion-cuadernos.md). El
[informe de auditoría](informe-auditoria-cuadernos.md) registra los defectos corregidos
y los límites que permanecen.

El [`paquete general`](paquete-general.md) permite descargar juntos los dieciséis casos,
los trece cuadernos y las implementaciones comparables en Pandas, Polars, R, SQL y
Excel, sin redistribuir datos de terceros.

| Cuaderno | Problemas | Pasos |
| --- | --- | ---: |
| [Consolidar cinco Excel](../cases/bip_lugares_carga/CUADERNO.md) | P01, P02, P04 | 16 |
| [Conciliar Metro y buses](../cases/correspondencia_metro/CUADERNO.md) | P03, P10 | 9 |
| [Horarios y cobertura nocturna](../cases/carga_nocturna/CUADERNO.md) | P05, P09 | 9 |
| [Expediciones por hora](../cases/gtfs_red_movilidad/CUADERNO.md) | P06 | 10 |
| [Cuándo dejar Pandas](../cases/rendimiento_gtfs/CUADERNO.md) | P07 | 8 |
| [Cobertura espacial](../cases/cobertura_de_carga/CUADERNO.md) | P08 | 9 |
| [Calendario oficial](../cases/calendario_medicion/CUADERNO.md) | P11 | 8 |
| [Frecuencia programada](../cases/frecuencia_programada/CUADERNO.md) | P12, P13 | 8 |
| [Evolución GTFS](../cases/evolucion_gtfs/CUADERNO.md) | P14, P15 | 8 |
| [Informe para decisión](../cases/informe_decision_carga/CUADERNO.md) | P16 | 8 |
| [Gobernanza de datos DTPM](../cases/gobernanza_datos_dtpm/CUADERNO.md) | P17 | 8 |
| [ETL histórico GTFS](../cases/etl_gtfs_automatizado/CUADERNO.md) | P18 | 8 |
| [Red de correspondencias](../cases/red_correspondencias_dtpm/CUADERNO.md) | P19 | 8 |

El Excel de cada paso va dibujado como hoja, con la fórmula en su celda y el resultado a
la vista.

Se generan ejecutando el caso, con `python scripts/build_cuadernos.py`. Los trece
cuadernos siguen una ruta sin saltos y cubren los diecinueve problemas; el alcance y
los límites de cada uno están en el
[mapa de problemas](problemas-de-la-instancia.md).

---

## Vengo a prepararme para una evaluación técnica

En orden, de lo que más rinde a lo que menos:

| # | Documento | Qué te da |
| --- | --- | --- |
| 1 | [Mapa de problemas](problemas-de-la-instancia.md) | 19 problemas resueltos con su pregunta exacta, método, resultado y límites; además, 10 preguntas que los datos no permiten contestar |
| 2 | [`cases/bip_lugares_carga`](../cases/bip_lugares_carga/README.md) | **P01, P02 y P04 resueltos**: consolidar cinco Excel reales con nueve defectos, y establecer qué identifica una fila cuando nada lo hace. Es lo más parecido a una prueba de cuatro horas |
| 3 | [`cases/calendario_medicion`](../cases/calendario_medicion/README.md) | **P11 resuelto**: reconstruir el denominador de un indicador oficial |
| 4 | [`cases/cobertura_de_carga`](../cases/cobertura_de_carga/README.md) | **P08 resuelto en parte**: el cruce que no tiene clave, y cuánto del resultado lo pone el analista |
| 5 | [`cases/carga_nocturna`](../cases/carga_nocturna/README.md) | **P09 y P05 resueltos**: un indicador con datos faltantes, publicado como intervalo en lugar de cifra |
| 6 | [`cases/correspondencia_metro`](../cases/correspondencia_metro/README.md) | **P10 y P03 resueltos**: conciliar dos inventarios de la misma realidad, y auditar qué no mira cada control de calidad |
| 7 | [`cases/rendimiento_gtfs`](../cases/rendimiento_gtfs/README.md) | **P07 resuelto**: benchmark comparable de Pandas, bloques, DuckDB y Polars |
| 8 | [`cases/frecuencia_programada`](../cases/frecuencia_programada/README.md) | **P12 y P13 resueltos**: frecuencia programada e ICF no observable sin GPS |
| 9 | [`cases/evolucion_gtfs`](../cases/evolucion_gtfs/README.md) | **P14 y P15 resueltos**: tres publicaciones oficiales comparadas con la misma definición |
| 10 | [`cases/informe_decision_carga`](../cases/informe_decision_carga/README.md) | **P16 resuelto**: informe ejecutivo con evidencia, inferencia y límites |
| 11 | [`cases/gobernanza_datos_dtpm`](../cases/gobernanza_datos_dtpm/README.md) | **P17 resuelto**: catálogo, brechas documentales y prioridad auditable |
| 12 | [`cases/etl_gtfs_automatizado`](../cases/etl_gtfs_automatizado/README.md) | **P18 resuelto**: ETL contractual, controles y particiones incrementales |
| 13 | [`cases/red_correspondencias_dtpm`](../cases/red_correspondencias_dtpm/README.md) | **P19 resuelto**: grafo bipartito y escenarios estructurales |
| 14 | [Equivalencias SQL / Pandas / Polars / Excel / R](equivalencias.md) | Traducción con las trampas donde las versiones dejan de ser equivalentes |
| 15 | [`cases/transport`](../cases/transport/README.md) | Las tres simulaciones de cuatro horas y qué se corrige en cada una |

Lo que **no** encontrarás: nada sobre el contenido de ninguna prueba real. No se
conoce, y queda dicho en el mapa de problemas.

---

## Vengo a resolver un problema de datos

| Documento | Qué te da |
| --- | --- |
| [El recorrido de nueve etapas](instancias.md) | Las nueve etapas, qué evita cada una, y cómo agregar tu propia instancia |
| [Metodología de 18 etapas](metodologia.md) | La versión completa y auditable, implementada en `lab.method` |
| [Método de investigación](research-method.md) | La versión corta, para un análisis acotado |
| [Arquitectura](arquitectura.md) | Los contratos entre módulos y las decisiones técnicas con sus alternativas descartadas |
| [Base de conocimiento](conocimiento.md) | 43 registros de cosas que costó descubrir. Búsqueda: `python -m lab.knowledge "consulta"` |
| [Catálogo de casos](catalogo-casos.md) | Los dieciséis casos con sus metadatos y la cobertura de competencias |
| [Paquete general](paquete-general.md) | Una descarga determinista con casos, cuadernos, resultados y cinco tecnologías |

---

## Vengo a aprender

| Documento | Qué te da |
| --- | --- |
| [Programa de aprendizaje](programa.md) | 8 clases en 6 bloques, cada una con las 17 secciones del estándar |
| [Perfiles profesionales](perfiles.md) | 11 perfiles con sus competencias y la cobertura **medida** de cada uno |
| [Manual](manual.md) | La guía corta: entorno, Pandas, Excel, SQL, calidad, cruces, indicadores |
| [Diccionario de datos](diccionario.md) | Los datos sintéticos de transporte y sus reglas de tratamiento |

Las clases están en [`learning/`](learning/), organizadas por bloque. El validador
exige que todas tengan sus 17 secciones:

```powershell
uv run python -m lab.learning
```

---

## Vengo a entender el estado real del repositorio

| Documento | Qué te da |
| --- | --- |
| [Hoja de ruta](roadmap.md) | Separación estricta entre **implementado** y **proyectado**, con las brechas medidas |
| [Contratos de agentes](agentes.md) | 20 capacidades especializadas con sus entradas, salidas y criterios de aceptación |
| [Registro de cambios](../CHANGELOG.md) | Qué cambió en cada versión, incluidos los defectos corregidos y cómo se encontraron |
| [Estándar visual](visual-standard.md) | Paleta, tipografía y reglas para gráficos y planillas |
| [Ejecución portable](ejecucion-portable.md) | Python local, Colab, RStudio, Posit Cloud e IRkernel sin rutas del autor |
| [Matriz de validación](matriz-validacion-cuadernos.md) | Estado por caso y entorno: ejecución real, CI o compatibilidad documentada |
| [Auditoría de cuadernos](informe-auditoria-cuadernos.md) | Hallazgos, correcciones, decisiones y pendientes verificables |
| [Fuentes de los cuadernos](fuentes-cuadernos.md) | Origen, formato, licencia, descarga, contrato comparable y recuperación |

---

## Documentos generados desde el código

Estos seis **no se editan a mano**: se generan con `python scripts/build_docs.py`, y la
integración continua comprueba que estén al día. Si cambias el código y no los
regeneras, la suite falla.

- [`catalogo-casos.md`](catalogo-casos.md) — desde los `case.json`
- [`agentes.md`](agentes.md) — desde `lab.agents.REGISTRY`
- [`perfiles.md`](perfiles.md) — desde `lab.profiles.PROFILES`
- [`programa.md`](programa.md) — desde los archivos de clase
- [`metodologia.md`](metodologia.md) — desde `lab.method.STAGES`
- [`conocimiento.md`](conocimiento.md) — desde `knowledge/`

El resto de los documentos de esta carpeta se escriben a mano.

---

## Fuentes y procedencia

Lo que se verificó y lo que no, por fuente:

| Documento | Contenido |
| --- | --- |
| [Antecedentes del DTPM](dtpm-antecedentes.md) | Lo que se **abrió y leyó** el 26 de noviembre de 2026, con una sección explícita de lo que **no** se pudo verificar |
| [Indicadores oficiales](indicadores-oficiales-transporte.md) | Fórmulas citadas textualmente de un documento público de DIPRES |

Cada caso con datos reales lleva además su propio `procedencia.json` con la URL, la
fecha, el tamaño y el SHA-256 del archivo usado.

---

## Convenciones de toda la documentación

Cuatro reglas que se aplican en todos los documentos de esta carpeta, y que explican
por qué algunos párrafos dicen «no se verificó» en lugar de callarlo:

1. **Lo implementado se separa de lo proyectado.** Una capacidad proyectada no se
   describe en presente.
2. **Lo que no se ejecutó no se declara probado.** Si una comprobación no corre en
   integración continua, el documento dice qué mecanismo la cubre en su lugar.
3. **Toda cifra es reproducible.** Cada número de estos documentos sale de un comando
   que se puede volver a ejecutar.
4. **Toda fuente lleva su estado.** Verificada, no verificada, o de tercero. Lo que no
   se comprobó se dice.
