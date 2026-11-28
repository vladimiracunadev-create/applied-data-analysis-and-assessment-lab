<!-- Archivo generado por scripts/build_docs.py. No lo edite a mano: modifique el código fuente y vuelva a ejecutar el script. -->

# Perfiles y rutas profesionales

El laboratorio describe **11 perfiles** sobre un vocabulario de
**20 competencias**. Cada perfil declara sus competencias
núcleo, su ruta por los bloques del programa y las evidencias que lo demuestran.

## Cobertura real por perfil

Qué parte del núcleo de cada perfil está cubierta por los casos **implementados**.
No se aspira a 100 % en todos: la columna de faltantes es la lista de trabajo, y
`docs/roadmap.md` declara cada brecha.

| perfil | nucleo | cubiertas | cobertura_pct | faltantes |
| --- | --- | --- | --- | --- |
| Analista de datos | 7 | 7 | 100.0 | — |
| Gestor de datos | 8 | 8 | 100.0 | — |
| Ingeniero de datos | 6 | 6 | 100.0 | — |
| Científico de datos | 6 | 5 | 83.3 | inferencia-estadistica |
| Analista de negocios | 4 | 4 | 100.0 | — |
| Especialista en inteligencia de negocios | 4 | 4 | 100.0 | — |
| Investigador aplicado | 4 | 3 | 75.0 | inferencia-estadistica |
| Especialista en calidad de datos | 4 | 4 | 100.0 | — |
| Especialista en visualización | 2 | 2 | 100.0 | — |
| Arquitecto de soluciones de datos | 4 | 4 | 100.0 | — |
| Especialista en investigación de operaciones | 3 | 3 | 100.0 | — |

## Perfiles

### Analista de datos (`analista-de-datos`)

Responder preguntas de negocio con datos existentes y comunicarlas.

- **Ruta de aprendizaje:** Fundamentos de datos → Matemáticas y estadística aplicadas → Programación aplicada a datos → Análisis y comunicación
- **Herramientas:** Python, Pandas, Polars, R, Excel, SQL, Power BI
- **Competencias núcleo:** `lectura-escritura-datos`, `limpieza-normalizacion`, `agregacion-indicadores`, `estadistica-descriptiva`, `visualizacion`, `hojas-de-calculo`, `comunicacion-resultados`
- **Competencias de apoyo:** `sql`, `calidad-datos`, `apoyo-decision`
- **Evidencias que demuestran el perfil:**
  - un caso resuelto con informe e indicadores validados
  - un libro de Excel con fórmulas auditables
  - una simulación cronometrada corregida con rúbrica

### Gestor de datos (`gestor-de-datos`)

Asegurar que los datos de una organización sean correctos, trazables y utilizables.

- **Ruta de aprendizaje:** Fundamentos de datos → Programación aplicada a datos → Ingeniería y calidad de datos → Análisis y comunicación
- **Herramientas:** Python, Pandas, Polars, R, Excel, SQL, Power Query
- **Competencias núcleo:** `calidad-datos`, `limpieza-normalizacion`, `cruce-consolidacion`, `fechas-horarios`, `agregacion-indicadores`, `gobernanza-datos`, `validacion-independiente`, `hojas-de-calculo`
- **Competencias de apoyo:** `sql`, `automatizacion`, `comunicacion-resultados`, `reproducibilidad`
- **Evidencias que demuestran el perfil:**
  - informe de calidad con hallazgos por regla y columna
  - cruce auditado con control de cardinalidad
  - validación cruzada entre Pandas, Polars, R, SQL y hoja de cálculo

### Ingeniero de datos (`ingeniero-de-datos`)

Construir los procesos que llevan datos desde el origen hasta el consumo.

- **Ruta de aprendizaje:** Fundamentos de datos → Programación aplicada a datos → Ingeniería y calidad de datos
- **Herramientas:** Python, Polars, SQL, DuckDB, Parquet, Docker, GitHub Actions
- **Competencias núcleo:** `ingenieria-datos`, `automatizacion`, `calidad-datos`, `sql`, `reproducibilidad`, `lectura-escritura-datos`
- **Competencias de apoyo:** `gobernanza-datos`, `cruce-consolidacion`, `modelamiento`
- **Evidencias que demuestran el perfil:**
  - proceso ETL reproducible con pruebas
  - contrato de datos aplicado en integración continua

### Científico de datos (`cientifico-de-datos`)

Modelar fenómenos y cuantificar incertidumbre para anticipar o explicar.

- **Ruta de aprendizaje:** Matemáticas y estadística aplicadas → Programación aplicada a datos → Investigación aplicada → Temas avanzados
- **Herramientas:** Python, Pandas, Polars, NumPy, scikit-learn, Statsmodels, R
- **Competencias núcleo:** `estadistica-descriptiva`, `inferencia-estadistica`, `modelamiento`, `visualizacion`, `investigacion-aplicada`, `reproducibilidad`
- **Competencias de apoyo:** `limpieza-normalizacion`, `sql`, `comunicacion-resultados`
- **Evidencias que demuestran el perfil:**
  - investigación con hipótesis, prueba y limitaciones declaradas
  - modelo con validación fuera de muestra

### Analista de negocios (`analista-de-negocios`)

Traducir un problema de negocio en requisitos, métricas y decisiones.

- **Ruta de aprendizaje:** Fundamentos de datos → Análisis y comunicación
- **Herramientas:** Excel, Power BI, SQL
- **Competencias núcleo:** `agregacion-indicadores`, `apoyo-decision`, `comunicacion-resultados`, `hojas-de-calculo`
- **Competencias de apoyo:** `estadistica-descriptiva`, `visualizacion`, `calidad-datos`
- **Evidencias que demuestran el perfil:**
  - definición de indicadores con fórmula, unidad y denominador
  - informe con recomendación proporcional a la evidencia

### Especialista en inteligencia de negocios (`especialista-bi`)

Industrializar indicadores en modelos y tableros confiables.

- **Ruta de aprendizaje:** Programación aplicada a datos → Ingeniería y calidad de datos → Análisis y comunicación
- **Herramientas:** Power BI, Tableau, Metabase, SQL, Power Query
- **Competencias núcleo:** `agregacion-indicadores`, `visualizacion`, `sql`, `gobernanza-datos`
- **Competencias de apoyo:** `ingenieria-datos`, `automatizacion`, `apoyo-decision`
- **Evidencias que demuestran el perfil:**
  - modelo de datos documentado con su grano
  - tablero con definiciones de métrica visibles

### Investigador aplicado (`investigador-aplicado`)

Producir evidencia reproducible sobre preguntas abiertas.

- **Ruta de aprendizaje:** Matemáticas y estadística aplicadas → Investigación aplicada
- **Herramientas:** Python, R, JupyterLab, LaTeX o Markdown
- **Competencias núcleo:** `investigacion-aplicada`, `inferencia-estadistica`, `reproducibilidad`, `comunicacion-resultados`
- **Competencias de apoyo:** `calidad-datos`, `visualizacion`, `validacion-independiente`
- **Evidencias que demuestran el perfil:**
  - informe de investigación completo con sesgos e incertidumbre
  - material reproducible con semilla y dependencias

### Especialista en calidad de datos (`especialista-calidad-datos`)

Definir, medir y mejorar la aptitud de los datos para su uso.

- **Ruta de aprendizaje:** Fundamentos de datos → Ingeniería y calidad de datos
- **Herramientas:** Python, Pandera, SQL, Excel
- **Competencias núcleo:** `calidad-datos`, `gobernanza-datos`, `validacion-independiente`, `limpieza-normalizacion`
- **Competencias de apoyo:** `automatizacion`, `cruce-consolidacion`, `reproducibilidad`
- **Evidencias que demuestran el perfil:**
  - contrato de datos con reglas y severidades
  - tablero de defectos con evolución en el tiempo

### Especialista en visualización (`especialista-visualizacion`)

Hacer que el resultado se entienda sin distorsionarlo.

- **Ruta de aprendizaje:** Análisis y comunicación
- **Herramientas:** Matplotlib, Plotly, Power BI, D3
- **Competencias núcleo:** `visualizacion`, `comunicacion-resultados`
- **Competencias de apoyo:** `agregacion-indicadores`, `apoyo-decision`
- **Evidencias que demuestran el perfil:**
  - conjunto de gráficos con escalas honestas y accesibilidad verificada

### Arquitecto de soluciones de datos (`arquitecto-soluciones-datos`)

Decidir la estructura técnica que sostiene el análisis en el tiempo.

- **Ruta de aprendizaje:** Programación aplicada a datos → Ingeniería y calidad de datos → Temas avanzados
- **Herramientas:** Python, SQL, Docker, Arrow/Parquet, servicios cloud
- **Competencias núcleo:** `ingenieria-datos`, `gobernanza-datos`, `reproducibilidad`, `modelamiento`
- **Competencias de apoyo:** `automatizacion`, `sql`, `calidad-datos`, `apoyo-decision`
- **Evidencias que demuestran el perfil:**
  - decisión de arquitectura documentada con alternativas descartadas
  - contratos entre componentes verificados por pruebas

### Especialista en investigación de operaciones (`especialista-investigacion-operaciones`)

Optimizar decisiones bajo restricciones y simular escenarios.

- **Ruta de aprendizaje:** Matemáticas y estadística aplicadas → Temas avanzados
- **Herramientas:** Python, SciPy, solvers de programación lineal, simulación
- **Competencias núcleo:** `modelamiento`, `investigacion-aplicada`, `apoyo-decision`
- **Competencias de apoyo:** `estadistica-descriptiva`, `visualizacion`, `reproducibilidad`
- **Evidencias que demuestran el perfil:**
  - modelo de optimización con función objetivo y restricciones explícitas
  - simulación con análisis de sensibilidad

## Vocabulario de competencias

Los casos y los ítems de evaluación declaran competencias de esta lista, de modo
que todo quede cruzable:

- `lectura-escritura-datos`
- `calidad-datos`
- `limpieza-normalizacion`
- `cruce-consolidacion`
- `fechas-horarios`
- `agregacion-indicadores`
- `estadistica-descriptiva`
- `inferencia-estadistica`
- `modelamiento`
- `visualizacion`
- `hojas-de-calculo`
- `sql`
- `automatizacion`
- `ingenieria-datos`
- `gobernanza-datos`
- `investigacion-aplicada`
- `comunicacion-resultados`
- `apoyo-decision`
- `validacion-independiente`
- `reproducibilidad`
