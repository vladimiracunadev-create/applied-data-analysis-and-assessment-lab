# Documentación

Mapa de la documentación, organizado por lo que vienes a hacer. Si es tu primera vez,
el [README principal](../README.md) explica en una pantalla qué problema resuelve el
repositorio.

---

## Vengo a prepararme para una evaluación técnica

En orden, de lo que más rinde a lo que menos:

| # | Documento | Qué te da |
| --- | --- | --- |
| 1 | [Mapa de problemas](problemas-de-la-instancia.md) | 16 problemas con su pregunta exacta, los datos que usa cada uno y su estado. Y **10 preguntas que estos datos no permiten contestar** |
| 2 | [`cases/bip_lugares_carga`](../cases/bip_lugares_carga/README.md) | **P01 resuelto**: consolidar cinco Excel reales con nueve defectos. Es lo más parecido a una prueba de cuatro horas |
| 3 | [`cases/calendario_medicion`](../cases/calendario_medicion/README.md) | **P11 resuelto**: reconstruir el denominador de un indicador oficial |
| 4 | [`cases/cobertura_de_carga`](../cases/cobertura_de_carga/README.md) | **P08 resuelto en parte**: el cruce que no tiene clave, y cuánto del resultado lo pone el analista |
| 5 | [Equivalencias SQL / Pandas / Excel / R](equivalencias.md) | La tabla de traducción, con una columna de **trampas** donde las versiones «equivalentes» dejan de serlo |
| 6 | [Indicadores oficiales del transporte](indicadores-oficiales-transporte.md) | Las fórmulas, el grano, las fuentes y las reglas de exclusión reales, citadas |
| 7 | [`cases/transport`](../cases/transport/README.md) | Las tres simulaciones de cuatro horas y qué se corrige en cada una |

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
| [Base de conocimiento](conocimiento.md) | 30 registros de cosas que costó descubrir. Búsqueda: `python -m lab.knowledge "consulta"` |
| [Catálogo de casos](catalogo-casos.md) | Los siete casos con sus metadatos y la cobertura de competencias |

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
