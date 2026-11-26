# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Este proyecto usa [versionado semántico](https://semver.org/lang/es/).

La **primera versión oficial es la 0.1.0**. Los prototipos anteriores no se consideran
releases y no se publican como tales.

## [0.5.0] — 2026-11-26

Resuelve el problema **P11**: reconstruir el calendario de medición de un indicador
oficial y auditar sus reglas. Es el caso que más se parece al trabajo real de un gestor
de datos del sector público.

### Agregado

- **Instancia `cases/calendario_medicion`.** Toma las ocho reglas de exclusión del
  índice de variación de tiempos de viaje, publicadas en un documento de DIPRES, y
  reconstruye el denominador del indicador. Resultado para 2026: de **261** días
  laborales quedan **164** elegibles (62,84 %) y **78 medibles** tras cruzar con los
  meses de medición.
- **`lab.calendars`: calendarios por reglas.** Cada regla es un objeto con su fuente
  citada. Mide la **exclusión exclusiva** de cada una —cuántos días solo ella
  excluye— y la matriz de solapamiento. Incluye el cálculo del Domingo de Pascua con
  el algoritmo gregoriano anónimo, validado en las pruebas contra diez fechas
  publicadas entre 1900 y 2027 y contra sus propiedades en doscientos años.
- **Fuente de feriados en el catálogo**, declarada explícitamente como **tercero, no
  oficial**: la API del gobierno no resolvía. El listado se descarga una vez, se
  valida y se **versiona** dentro del caso, porque depender de un servicio de tercero
  en cada ejecución haría el caso irreproducible.
- Tres registros de conocimiento: `denominador-es-una-decision`, `regla-redundante` y
  `supuesto-medido`.

### Los tres hallazgos

**1. La mitad de las reglas no cambia el denominador.** Al medir cuántos días medibles
recuperaría el quitar cada regla:

| Regla | Días medibles que quita |
| --- | --- |
| fin de semana | 25 |
| semana de fiestas patrias | 4 |
| días 28 y 29 | 2 |
| 11 de septiembre | 1 |
| vacaciones de invierno | **0** |
| meses completos (enero, febrero, diciembre) | **0** |
| feriados | **0** |
| día del joven combatiente | **0** |

Excluir enero, febrero y diciembre descarta 90 días del año y **ninguno** de los que se
miden, porque la medición ocurre en marzo, junio, septiembre y noviembre.

**2. Hay dos clases de redundancia, y confundirlas cuesta.** Comparando 2024 a 2027:

| Clasificación | Reglas |
| --- | --- |
| Efectiva (quita días todos los años) | fin de semana, días 28 y 29, semana de fiestas patrias |
| **Redundante accidental** | feriados (cero en 2026, tres en 2027), 11 de septiembre (cero en 2027) |
| **Redundante estructural** | meses completos, vacaciones de invierno, día del joven combatiente |

Quitar una estructuralmente redundante no cambia nada nunca; quitar una accidental
funciona este año y falla el siguiente. El «Día del joven combatiente» es el 29 de
marzo y la regla de los días 28 y 29 ya lo descarta: exclusión exclusiva cero.

**3. El denominador cambia entre años.** 70, 74, 78 y 75 días medibles para 2024, 2025,
2026 y 2027: una variación del **11 %** producida solo por cómo cae el calendario. El
valor anual del indicador es el promedio de cuatro mediciones trimestrales, de modo que
comparar dos años compara promedios calculados sobre cantidades distintas de días.

### El supuesto que no se pudo resolver, medido

La metodología dice «vacaciones de invierno (dos semanas, considerando los calendarios
escolares)» **sin fechas**, y el calendario escolar no se obtuvo. En lugar de elegir
unas fechas en silencio, el caso declara el supuesto y mide su efecto: moverlo dentro
de julio no cambia nada, y moverlo a la segunda mitad de junio —que sí es mes de
medición— baja el denominador de 78 a 72 días. Eso convierte una incertidumbre en un
riesgo acotado: hay que conseguir el calendario escolar **solo si** el receso empieza
antes del 1 de julio.

### Validación

- El listado de feriados **no se guarda** si no contiene el Viernes Santo calculado: un
  dato de entrada que no pasa su propia validación no entra.
- La identidad `suma_de_exclusiones − solapamiento = días_excluidos` se comprueba en
  las pruebas.
- El aporte de cada regla se calcula **quitándola y reconstruyendo** el calendario, no
  por diferencia algebraica, que se equivoca con los solapamientos.
- Las pruebas del caso corren **sin red**, y la descarga desde la API de tercero se
  ejerce contra un servidor falso para comprobar que valida antes de guardar.

## [0.4.0] — 2026-11-26

Resuelve el problema **P01** del mapa: consolidar cinco Excel públicos heterogéneos.
Es el primer caso del laboratorio con datos reales **de licencia verificada**, y el que
más se parece a lo que pide una evaluación técnica de cuatro horas con Excel y Pandas.

### Agregado

- **Instancia `cases/bip_lugares_carga`.** Consolida los cinco archivos de lugares de
  carga de la tarjeta bip! publicados por la Subsecretaría de Transporte: 1 928 filas
  en seis hojas, licencia Creative Commons Atribución-NoComercial 2.0 verificada.
  Responde cuántos lugares hay, de qué tipo, en qué comuna y de qué entidad: 1 927
  abiertos, 5 tipos, 46 comunas, 3 entidades, y solo el **18,06 %** con horario
  publicado.
- **`lab.excel`: lectura de planillas desordenadas.** `detect_header_row`,
  `read_messy_sheet`, `read_all_sheets`, `sheet_names` y el informe `SheetReport`. En
  los cinco archivos el encabezado estaba en las filas **7, 9, 13, 10 y 9**: detectarlo
  es más robusto que fijarlo, y si la detección falla el módulo falla en lugar de
  adivinar.
- **`lab.textual`: normalización de texto.** `normalize_key` para agrupar y
  `normalize_label` para mostrar, porque guardar solo la clave convierte `Ñuñoa` en
  `NUNOA` en el informe final. Más `similarity`, `duplicate_candidates` —que propone
  pares para revisión humana, nunca fusiona— y `normalization_report`, que cuantifica
  los grupos espurios que la normalización evita.
- **`lab.geo`: geografía mínima sin dependencias.** `haversine_km`, `utm_to_latlon`
  (transversa de Mercator inversa sobre WGS84), `grados_por_km` y `nearest_point` con
  búsqueda por bloques. Habilita el problema P08 del mapa.
- Cuatro registros de conocimiento: `encabezado-no-esta-en-la-primera-fila`,
  `clave-que-no-es-clave`, `normalizar-antes-de-agrupar` y `dos-coordenadas-un-lugar`.

### Lo que la validación cruzada encontró

El archivo trae la ubicación **dos veces** —UTM y geográficas—, lo que permite validarlo
contra sí mismo sin ninguna fuente externa. La distribución de los 1 928 desvíos es
**bimodal**:

| Desvío | Filas | Qué es |
| --- | --- | --- |
| menos de 5 m | 109 | las dos columnas coinciden |
| 50 a 80 m | 1 779 | desplazamiento sistemático (diferencia de datum) |
| más de 200 m | **3** | **errores de registro: 4 623 m, 10 087 m y 10 272 m** |

Y entre 80 y 200 m, **nada**. Que los dos grupos estén separados por un orden de
magnitud es lo que permite distinguir el problema sistemático del error puntual:
reportar los 1 779 como errores sería un falso positivo masivo, callar los tres una
omisión.

Que 109 filas **no** tengan el desplazamiento es el hallazgo de fondo: si fuera solo
una diferencia de datum, sería uniforme. Las dos columnas no se produjeron con un único
proceso consistente. Es gobernanza de datos, no limpieza: se reporta al publicador.

### Otros hallazgos del caso

- **`CODIGO` no es una clave**, y ni la clave compuesta `archivo + código` lo es: en el
  archivo de Metro el código es la **línea**, de modo que 143 estaciones comparten 7
  códigos.
- **El `horario` cubre el 18,06 %** porque 1 579 locales vienen de un archivo que no
  publica esa columna. No es un campo con nulos: es un campo que esa población no tiene.
- **`FULLCARGA` y `Fullcarga`** convivían en el mismo archivo, creando grupos espurios
  en cualquier `groupby` sobre el texto crudo.

### Corregido

- **`lab.geo.haversine_km` no aceptaba arreglos de NumPy difundidos entre sí**, que es
  justo lo que necesita una búsqueda del punto más cercano por bloques. Lo encontró la
  prueba de `nearest_point`.
- **`scripts/fetch_data.py` guardaba todo con extensión `.zip`.** Un `.xlsx` guardado
  como `.zip` funciona —un xlsx es un zip— pero nadie lo reconoce al abrir la carpeta.
  Ahora la extensión se deriva del tipo de contenido declarado.

### Cambiado

- `docs/roadmap.md` da por cubierta la competencia `gobernanza-datos`, cuyo hallazgo
  central aporta esta instancia, y mantiene pendiente el caso de gobernanza explícita
  (catálogo, propiedad del dato, retención), que este caso no toca.

## [0.3.0] — 2026-11-26

Inventario de lo que **sí se puede resolver** con datos públicos verificados, y las
definiciones oficiales de los indicadores del sector.

### Agregado

- **`docs/problemas-de-la-instancia.md`**: dieciséis problemas con su pregunta exacta,
  los datos que usa cada uno, la tecnología que exige, la trampa que enseña y su
  estado —resuelto, disponible o no se puede—. Incluye una sección de **siete
  preguntas que estos datos no permiten contestar**, con el motivo: no hay demanda, no
  hay GPS, no hay transacciones, no hay límites comunales.
- **`docs/indicadores-oficiales-transporte.md`**: las definiciones oficiales del índice
  de cumplimiento de regularidad (ICR), del de frecuencia (ICF) y del índice de
  variación de tiempos de viaje, con fórmula, grano, fuente y reglas de exclusión,
  citadas textualmente de un documento público de DIPRES (Partida 19, Ministerio de
  Transporte y Telecomunicaciones). Lo relevante: el grano del ICR y del ICF es
  **servicio × sentido × mes**, el denominador son **mediciones** —más de veinte
  millones al año—, el plan de referencia cambia dos veces al año de modo que la serie
  no es comparable sin advertirlo, y el índice de tiempos de viaje declara **siete
  reglas de exclusión** encadenadas, entre ellas descartar enero, febrero y diciembre
  completos y los días 28 y 29 de cada mes.
- **Cinco fuentes nuevas en `lab.sources.CATALOG`**: los lugares de carga de la tarjeta
  bip! publicados por la Subsecretaría de Transporte en el portal de datos abiertos,
  con licencia **Creative Commons Atribución-NoComercial 2.0 verificada**. El catálogo
  ahora distingue fuentes con licencia comprobada de fuentes sin comprobar, y una
  prueba exige que esa distinción exista.

### Por qué esos Excel son mejor material que un dataset sintético

Verificado archivo por archivo: el encabezado está en una fila distinta en cada uno
(7, 9, 13, 10 y 9), los esquemas tienen 9 o 10 columnas, los nombres de columna varían
(`NOMBRE FANTASIA` / `NOMBRE DE FANTASIA ` con espacio final / ausente;
`DIRECCION` / `DIRECCIÓN`), los nombres de hoja varían (`Abiertos`, `Abierto`, `PCMA`),
uno trae una hoja `Cerrados` que no debe entrar en un indicador de cobertura, hay dos
sistemas de coordenadas a la vez, la entidad viene con mayúsculas inconsistentes, los
horarios son texto libre en tres formatos distintos, y el contenido incluye un carácter
que rompe una consola de Windows en cp1252.

### Verificado y no encontrado

Se buscó el documento de la convocatoria del cargo en el sitio del DTPM, en el del
Ministerio de Transportes, en el portal de datos abiertos del Estado y en buscadores.
**No se encontró**, y el sitio del DTPM no tiene sección de concursos. Queda declarado
en `docs/problemas-de-la-instancia.md` para que nadie suponga que el material está
modelado sobre la prueba real.

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
