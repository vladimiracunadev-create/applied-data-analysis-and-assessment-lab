# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Este proyecto usa [versionado semántico](https://semver.org/lang/es/).

La **primera versión oficial es la 0.1.0**. Los prototipos anteriores no se consideran
releases y no se publican como tales.

## [0.2.0] — 2026-11-26

Primera instancia con **datos públicos reales** y el módulo de adquisición que la hace
posible. Define el laboratorio como un recorrido reutilizable para leer datos de
cualquier dominio, no como un programa sobre transporte.

### Agregado

- **`lab.sources`: adquisición de datos con procedencia.** Descarga registrando URL,
  fecha, tamaño, tipo de contenido, huella SHA-256 y licencia en un registro que queda
  junto al dato. `discover_link` resuelve la URL de descarga **leyendo el enlace de la
  página índice**, porque el nombre del archivo publicado cambia en cada versión y un
  nombre construido a mano falla sin aviso. Incluye lectura de tablas desde dentro de
  un ZIP, con y sin bloques, e inventario de lo adquirido.
- **Instancia `cases/gtfs_red_movilidad` con datos reales.** GTFS vigente de la Red
  Metropolitana de Movilidad publicado por el DTPM: 12,8 MB comprimidos, 69,7 MB
  descomprimidos, 1 098 717 filas de horarios, 26 137 expediciones, 18 486 lugares y
  425 recorridos de cuatro operadores. Resuelve «¿cuántas expediciones salen por hora
  en un día laboral?» y documenta las cuatro trampas que contiene:
  - el **77,5 %** de la tabla de horarios no contiene horas de reloj, sino
    desplazamientos desde el inicio del viaje;
  - el relleno de ceros es irregular, de modo que `'0:00:00' > '00:00:51'` como texto y
    la primera parada queda ordenada después de la segunda;
  - contar expediciones en lugar de expandir sus ventanas de frecuencia subestima el
    servicio en un **87,65 %** (7 905 frente a 64 011), y tomar el fin de ventana como
    inclusivo lo sobreestima en un **10,37 %**;
  - el «32 % de paradas huérfanas» es **falso**: 5 989 de las 5 991 filas sin horarios
    no son paradas, sino estaciones, accesos, nodos de pasillo y áreas de abordaje. Las
    paradas realmente sin uso son **dos**.

  Los seis cruces de clave foránea del modelo tienen **cero** huérfanos: el feed está
  bien formado. El problema nunca fue la integridad, fue la semántica.
- **`lab.dates.parse_hms_seconds`, `seconds_to_hms` y `service_day_hour`** para
  horarios de día de servicio: admiten horas de 24 o más y relleno de ceros irregular,
  que `pd.to_datetime` rechaza. Sirven para cualquier horario operacional —turnos,
  guardias, jornadas de producción—, no solo para transporte.
- **`scripts/fetch_data.py`** para traer una fuente del catálogo desde la línea de
  comandos, declarando el estado de su licencia.
- **`docs/instancias.md`**: el recorrido de nueve etapas que se aplica a cualquier
  dominio, con lo que cada etapa evita, y una lista de instancias candidatas —banca,
  astronomía, clientes, empresa, salud, energía, logística, ciberseguridad— marcada
  explícitamente como trabajo pendiente y no como capacidad existente.
- Cuatro registros de conocimiento nuevos, todos con origen en datos reales:
  `horario-relativo-vs-absoluto`, `relleno-de-ceros-y-orden`, `expandir-frecuencias` y
  `defecto-que-no-existe`.

### Corregido

- **`lab.metrics.safe_ratio` no difundía un escalar sobre el índice de una serie.**
  Envolver el escalar con `pd.Series(escalar)` creaba una serie de un elemento con
  índice 0, y la división alineaba por índice: todas las filas salvo la primera
  quedaban en NaN sin que nada avisara. Se detectó calculando los errores relativos de
  la tabla comparativa de la instancia del GTFS, y tiene prueba de regresión.
- El mensaje de error que avisa que falta el feed fallaba al construirse cuando la
  ruta estaba fuera del repositorio: `Path.relative_to` levanta `ValueError`. Un
  mensaje de error que no se puede construir es peor que no tener mensaje.

### Cambiado

- **Toda la documentación queda en español.** Se eliminó `README.en.md` y las
  referencias a él. Los nombres técnicos se conservan en su forma original cuando es la
  que usa la herramienta (`groupby`, `SUMIFS`, `LEFT JOIN`), porque traducirlos
  impediría buscarlos.
- El README describe el laboratorio como un recorrido para leer datos de cualquier
  dominio, con las instancias como aplicaciones de ese recorrido.
- `docs/roadmap.md` da por cubierta la competencia `ingenieria-datos`, que la instancia
  real entrena.

## [0.1.0] — 2026-11-26

Primera versión oficial. Consolida el laboratorio como infraestructura genérica de
análisis, investigación, aprendizaje y evaluación, con la preparación para una
evaluación técnica de gestor de datos como primer caso aplicado.

### Núcleo transversal (`lab/`, 17 módulos)

- `method`: metodología universal de 18 etapas como objeto auditable. Una etapa no se
  puede completar sin evidencia verificable; declararla no aplicable exige un motivo.
- `contracts`: contratos de datos con tipos lógicos, dominios, rangos, claves
  primarias y foráneas, y severidad por hallazgo. No elimina filas: informa.
- `metrics`: razones con denominador seguro, estadística descriptiva con cobertura,
  percentiles con método declarado, comparación entre tasa ponderada y promedio simple,
  atípicos por el criterio de Tukey.
- `dates`: conversión defensiva de fecha-hora informando qué no se pudo interpretar,
  duraciones, bandas horarias validadas contra huecos y solapes, atributos de
  calendario.
- `stats`: intervalos de confianza de media y proporción (Wilson), prueba de Welch,
  correlación de Pearson y chi-cuadrado de independencia, con las distribuciones
  acumuladas implementadas en Python puro. **Sin SciPy.**
- `sqlbridge`: ejecución de SQL de solo lectura sobre DataFrames mediante `sqlite3`, y
  comparación formal de resultados entre implementaciones.
- `excel`: libros con paleta del estándar visual, fila de unidades sobre el encabezado,
  autofiltro, congelado, formatos numéricos, hoja índice y escritura de fórmulas reales.
- `viz`: gráficos que exigen título, rótulo con unidad, período y fuente, con escala
  honesta y paleta accesible.
- `report`: informes de caso (12 secciones) y de investigación (20 secciones) que se
  niegan a exportarse incompletos, con clasificación obligatoria de las afirmaciones.
- `catalog`: descubrimiento y validación de casos contra 26 campos de metadatos, con
  matriz de cobertura de competencias.
- `knowledge`: base de conocimiento con índice invertido y búsqueda TF-IDF, sin
  modelos ni red, con control de referencias cruzadas.
- `learning`: modelo del programa y validador del estándar de 17 secciones por clase.
- `assessment`: motor de evaluaciones con configuraciones, banco de ítems, generación
  reproducible por semilla, rúbricas ponderadas y seguimiento de intentos.
- `agents`: 20 contratos de capacidades especializadas y un arnés que detecta
  responsabilidades duplicadas, contratos incompletos y referencias inexistentes.
- `profiles`: 11 perfiles profesionales sobre un vocabulario de 20 competencias, con
  cobertura real medida contra los casos implementados.
- `core`: se conserva sin cambios de comportamiento (lectura, perfil, cruce auditado,
  exportación).
- `console`: salida UTF-8 legible en consolas de Windows.

### Caso prioritario: transporte

- `solutions/sql_reference.py`: **segunda implementación completa en SQL**, que parte
  de los CSV cargados como texto y hace su propio casteo, cruce y agregación. No
  comparte código con la implementación en Pandas.
- `scripts/build_excel_solutions.py`: libros `solutions/excel/case_N_resuelto.xlsx` con
  **fórmulas reales de Excel** (`XLOOKUP`, `SUMIFS`, `COUNTIFS`, `AVERAGEIFS`,
  duración por factor 1440), hojas separadas de entradas, cálculos, resultados,
  control y documentación, y una hoja de control que confronta Excel con Python al
  abrir el libro.
- `cases/transport/case.json`: metadatos completos, incluidos supuestos, metodologías
  alternativas, validaciones, limitaciones, conocimiento adquirido y capacidades
  reutilizables.
- `docs/dtpm-antecedentes.md`: antecedentes públicos **verificados** el 26 de noviembre
  de 2026 (GTFS vigente y GTFS históricos publicados por el DTPM, con sus URL y la
  fecha de vigencia leída en el sitio), con una sección explícita de lo que **no** se
  pudo verificar.
- `docs/equivalencias.md`: equivalencias entre SQL, Pandas, Excel y R, con una columna
  de trampas donde las versiones «equivalentes» dejan de serlo.

### Laboratorio de evaluaciones

- `assessments/items/gestion-de-datos.json`: banco de 15 ítems con enunciado,
  competencias, herramientas, tiempo, entregable, criterios de corrección y las
  trampas que cada ítem busca detectar.
- `assessments/blueprints.py`: tres configuraciones (simulación de cuatro horas para
  gestor de datos, diagnóstico rápido, análisis y comunicación) con rúbricas que suman
  100 puntos.
- `scripts/build_assessment.py`: generación reproducible por semilla, declarando las
  competencias obligatorias que el banco todavía no cubre.

### Programa de aprendizaje

Ocho clases publicadas, cada una con las 17 secciones del estándar:

- Fundamentos: datos, tablas, tipos y claves; calidad de datos.
- Matemáticas: estadística descriptiva.
- Programación: Pandas para gestión de datos; Excel con fórmulas y tablas dinámicas.
- Ingeniería: cruces, contratos y SQL equivalente.
- Análisis: indicadores, visualización y comunicación.
- Investigación: método, preguntas, hipótesis y validez.

### Base de conocimiento

Catorce registros atómicos con procedencia y referencias cruzadas, entre ellos los
defectos encontrados durante esta versión: la pérdida de precisión de `julianday`, el
denominador inflado por `CONTAR.SI.CONJUNTO` con criterio `"<>"`, la confusión entre
ausente, cero e inválido, y la diferencia entre puntos porcentuales y variación
porcentual.

### Documentación

- README en español, con navegación, diagramas Mermaid, insignias
  verificables y una sección explícita de lo que las pruebas **no** cubren.
- `docs/arquitectura.md`: vista de componentes, contratos entre módulos, flujo de un
  problema nuevo y decisiones de arquitectura con sus alternativas descartadas.
- `docs/roadmap.md`: separación estricta entre implementado y proyectado, con las
  brechas **medidas** (competencias sin caso, bloque sin clases, lo que las pruebas no
  cubren).
- `scripts/build_docs.py`: genera catálogo, agentes, perfiles, programa, metodología e
  índice de conocimiento **desde el código**, de modo que la documentación no pueda
  desincronizarse. `--check` lo verifica en integración continua.
- `LICENSE` (MIT), `CONTRIBUTING.md` y `SECURITY.md`.

### Calidad

- Suite de pruebas que cubre el núcleo módulo por módulo, la validación cruzada entre
  Pandas y SQL en los tres casos, la estructura de los libros de Excel, el estándar
  pedagógico, los metadatos de los casos, el arnés de agentes y la coherencia del
  repositorio (versión única, enlaces relativos vivos, núcleo sin dependencias de
  dominio, documentación derivada al día, ausencia de secretos y de rutas absolutas).
- Integración continua con `uv`, lockfile versionado, y comprobación de que la
  documentación generada está al día.

### Corregido

- **Precisión de la duración en SQL.** El cálculo con
  `(julianday(fin) − julianday(inicio)) × 1440` perdía dígitos significativos y
  devolvía `42.999999971` donde el valor exacto era `43`. La comparación
  `duración ≤ meta` se invertía en todos los empates, moviendo la puntualidad varios
  puntos porcentuales mientras la media coincidía hasta el octavo decimal. Se
  reemplazó por una resta de segundos enteros con `strftime('%s', …)`. Detectado por la
  validación cruzada con la implementación en Pandas.
- **Denominador de la puntualidad en Excel.** `COUNTIFS(rango, "<>")` cuenta como no
  vacías las celdas cuya fórmula devuelve cadena vacía, de modo que inflaba el
  denominador y bajaba la tasa. Se reemplazó por `">=0"`, que solo admite valores
  numéricos.
- **Fila de unidades dentro del autofiltro de Excel.** Estaba bajo el encabezado, de
  modo que el filtro la trataba como un registro más. Se movió encima del encabezado.
- **IDF que anulaba términos frecuentes.** Con `log(N/df)`, un término presente en
  todos los registros pesaba exactamente cero y una búsqueda legítima no devolvía
  nada. Se cambió a la IDF suavizada `log(1 + N/df)`.
- **`UnicodeEncodeError` en consolas de Windows.** Imprimir una fórmula con símbolos
  matemáticos abortaba el comando en consolas con página de códigos cp1252, aunque el
  cálculo fuera correcto. Resuelto en `lab.console`.
- **Fallo del validador de clases fuera del repositorio.** `Lesson.reference` levantaba
  `ValueError` al validar un directorio externo; ahora devuelve la ruta absoluta.
- **`ORDER BY` en consulta compuesta.** La emulación del `FULL OUTER JOIN` con `UNION
  ALL` fallaba porque el `ORDER BY` no encontraba las columnas; se agregaron alias
  explícitos en el primer `SELECT`.

### Conservado sin cambios de comportamiento

Las tres simulaciones de cuatro horas, los tres datasets sintéticos con sus semillas,
`solutions/reference.py`, `cases/retail`, `cases/education`, `lab/core.py`,
`scripts/generate_data.py`, `scripts/export_inputs.py`, `scripts/new_case.py`,
`docs/manual.md`, `docs/diccionario.md`, `docs/research-method.md`,
`docs/visual-standard.md`, `solutions/EXCEL.md`, la plantilla de caso y las pruebas
previas (`tests/test_generic.py`, `tests/test_reference.py`), que siguen pasando.
