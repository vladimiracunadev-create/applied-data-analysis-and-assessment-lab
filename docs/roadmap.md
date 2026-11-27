# Hoja de ruta

> Este documento separa de forma estricta **lo implementado y verificado** de **lo
> proyectado**. Nada de la segunda lista debe citarse como una capacidad existente del
> laboratorio.

## 1. Estado actual verificado (v0.11.0)

Todo lo de esta sección se ejecuta y está cubierto por pruebas automáticas.
Los recuentos se obtienen con los comandos indicados, no de memoria.

| Componente | Estado | Cómo comprobarlo |
| --- | --- | --- |
| Núcleo (`lab/`): 26 módulos | implementado | `python -m pytest` |
| Casos de estudio (13): 10 con datos públicos reales o resultados reproducibles, 3 sintéticos | implementado | `python -m pytest tests/test_catalog.py` |
| Cruce espacial por proximidad sin dependencias geoespaciales | implementado | `python -m pytest tests/test_cobertura_de_carga.py` |
| Intérprete de horarios en texto libre, con lo ilegible como desconocido | implementado | `python -m pytest tests/test_schedules.py` |
| Conciliación de inventarios con grano distinto y dos criterios | implementado | `python -m pytest tests/test_correspondencia_metro.py` |
| Análisis de claves: candidatas mínimas y clave subrogada determinista | implementado | `python -m pytest tests/test_keys.py` |
| Cuadernos de trabajo: 10 cuadernos cubren los 16 problemas | implementado | `python scripts/build_cuadernos.py --check` |
| Simulaciones de cuatro horas (3) | implementado | `simulations/0{1,2,3}_enunciado.md` |
| Solución de referencia en Pandas | implementado | `python solutions/reference.py 1` |
| Segunda implementación en SQL | implementado | `python solutions/sql_reference.py 1` |
| Validación cruzada Pandas ↔ SQL, τ = 1e-9 | implementado | `python -m pytest tests/test_cross_validation.py` |
| Libros de Excel resueltos con fórmulas vivas | implementado | `python scripts/build_excel_solutions.py` |
| Motor de evaluaciones con banco de ítems y rúbricas | implementado | `python scripts/build_assessment.py --list` |
| Programa de aprendizaje: 8 clases con 17 secciones | implementado | `python -m lab.learning` |
| Base de conocimiento (42 registros) con búsqueda léxica | implementado | `python -m lab.knowledge` |
| Contratos de 20 agentes y arnés de verificación | implementado | `python -m lab.agents` |
| Perfiles profesionales (11) con cobertura medida | implementado | `python -m pytest tests/test_profiles.py` |
| Inferencia estadística sin dependencias externas | implementado | `python -m pytest tests/test_stats.py` |
| Antecedentes públicos del DTPM verificados | implementado | `docs/dtpm-antecedentes.md` |

## 2. Brechas conocidas del estado actual

Estas brechas están **medidas**, no estimadas. Una prueba automática falla si alguna
deja de estar declarada aquí.

### 2.1 Competencias sin caso que las cubra

- **`gobernanza-datos`** quedó cubierta en la versión 0.4.0 por la instancia
  `bip_lugares_carga`, cuyo hallazgo central es de gobernanza y no de limpieza: la
  distribución bimodal de los desvíos de coordenada muestra que las dos columnas de
  ubicación del archivo no se produjeron con un único proceso consistente, y eso se
  reporta al publicador en lugar de corregirse. El caso previsto `cases/governance`
  sigue en pie para cubrir catálogo, propiedad del dato y políticas de retención, que
  esta instancia no toca.

- **El caso de gobernanza explícita, todavía pendiente.** Era una competencia
  **núcleo** del perfil `gestor-de-datos` y del perfil `especialista-calidad-datos`. El laboratorio tiene las piezas técnicas
  (contratos de datos, diccionarios, trazabilidad de decisiones) pero no un caso cuyo
  objeto sea la gobernanza: catálogo de datos, propiedad y responsabilidad
  (*stewardship*), ciclo de vida, políticas de retención y clasificación de
  sensibilidad. Hasta que exista ese caso, la cobertura de esos dos perfiles es
  parcial y así se informa.
  *Caso previsto:* `cases/governance`, sobre un catálogo de datos de una organización
  ficticia con responsables, clasificación y reglas de retención.

- **`inferencia-estadistica`.** El núcleo (`lab.stats`) está implementado y probado
  contra tablas publicadas, pero ningún caso de estudio la declara entre sus
  competencias: se usa en el material de aprendizaje, no en un caso resuelto.
  *Caso previsto:* una investigación aplicada completa con hipótesis, prueba y
  limitaciones, bajo `research/`.

- **`modelamiento` y `automatizacion`.** Aparecen en los perfiles y están proyectadas;
  no hay caso que las cubra. `apoyo-decision` quedó cubierta por
  `cases/informe_decision_carga`.

- **`ingenieria-datos`** quedó cubierta en la versión 0.2.0 por la instancia
  `gtfs_red_movilidad`: adquisición con procedencia, lectura selectiva de un archivo de
  1,1 millones de filas desde un ZIP y expansión vectorizada de ventanas.

### 2.2 Cuadernos de trabajo — brecha cerrada

Diez cuadernos generados y ejecutables cubren los dieciséis problemas. P02 y P04 están
integrados en P01; P09 en P05; P10 en P03; P13 en P12; y P15 en P14. Cada uno trae
Markdown con salidas reales, script, Colab, libro de práctica, diagramas SVG y ZIP.

P14/P15 se ejecuta sobre las últimas publicaciones oficiales de 2024 y 2025 y el feed
vigente de 2026. Es una trayectoria reciente de tres puntos; ampliar hasta 2014 sigue
siendo una extensión posible, no una condición para reproducir la comparación actual.

### 2.3 Sin corrección de la práctica propia

Un cuaderno muestra cómo se hace; no dice si quien practica lo hizo bien. No hay ninguna
pieza que tome el intento de alguien y le diga **qué** difiere del resultado de
referencia. `lab.assessment` tiene rúbricas y banco de ítems, y no está conectado a los
casos con datos reales: sus tres simulaciones corren sobre los datos sintéticos.

### 2.4 Bloque del programa sin clases publicadas

- **`60-avanzado` (Temas avanzados).** Declarado en la estructura del programa, sin
  clases publicadas. `python -m lab.learning` lo informa como `proyectado`.
- Matiz sobre el **análisis geoespacial**, que era una de las clases previstas de ese
  bloque: desde la versión 0.6.0 hay un caso resuelto con cruce por proximidad,
  haversine y conversión de UTM (`cases/cobertura_de_carga`, `lab.geo`). Lo que falta
  es la **clase**, no la capacidad. Y sigue faltando todo lo que exige una capa de
  polígonos: cruces con límites administrativos, densidades por superficie y
  cartografía.

### 2.5 Lo que las pruebas no cubren

- **Evaluación numérica de las fórmulas de Excel.** Las pruebas verifican que las
  fórmulas existan, sean fórmulas y apunten a los rangos correctos; **no** calculan su
  resultado, porque eso exige Excel o LibreOffice y no están disponibles en
  integración continua. La hoja `30_control` de cada libro hace esa comprobación al
  abrirlo, y el acuerdo numérico entre implementaciones está cubierto por la validación
  Pandas ↔ SQL, que sí se ejecuta.
- **Mediana y P90 en SQL.** No se calculan en SQLite por falta de una función de
  percentil con interpolación lineal. Se validan contra una implementación en Python
  puro escrita en la propia suite de pruebas.

### 2.6 Dependencias y entornos no implementados

Declarados en el ecosistema objetivo y **no** presentes en el entorno mínimo:
Polars, DuckDB, R/RStudio, Power BI, Tableau, Metabase, GeoPandas, QGIS, Arrow/Parquet,
SciPy, Statsmodels, scikit-learn, Docker, n8n, bases vectoriales y búsqueda semántica
con embeddings. `lab.sqlbridge.duckdb_available()` detecta DuckDB si alguien lo
instala; el resto no tiene integración escrita.

## 3. Próximos pasos, en orden de prioridad

### Fase 1 — cerrar la preparación DTPM (antes del 30 de noviembre de 2026)

1. Resolver las tres simulaciones de cuatro horas con reloj, sin consultar soluciones.
2. Corregir cada intento con la rúbrica y registrar el resultado con
   `lab.assessment.progress_frame`.
3. Repasar los registros de la base de conocimiento marcados como `error`, que son los
   defectos que más puntos cuestan en una corrección.
4. Verificar el entorno alternativo: Colab y Google Sheets con los CSV cargados.

### Fase 2 — cerrar las brechas medidas

5. `cases/governance`: el caso que cubre `gobernanza-datos`.
6. Primera investigación aplicada completa bajo `research/`, con las 20 secciones.
7. Dos clases del bloque `60-avanzado`: series temporales y análisis geoespacial.
   La de geoespacial ya tiene de dónde sacar el material: `cases/cobertura_de_carga`
   y los registros `sesgo-con-eje` y `cruce-sin-clave`.

### Fase 3 — ampliar dominios

8. Casos de salud agregada, finanzas y riesgo, logística y energía. Cada uno debe
   aportar al menos una capacidad nueva al núcleo, no solo un dataset más.
9. Resolver un mismo problema con dos tecnologías y comparar rendimiento y
   complejidad, además de resultados.

### Fase 4 — infraestructura opcional

10. DuckDB y Parquet como motor alternativo en `lab.sqlbridge`.
11. Integración de R como tercera implementación de referencia.
12. Evaluar la búsqueda semántica sobre la base de conocimiento, midiendo si mejora
    la recuperación frente a TF-IDF antes de incorporarla. Si no mejora de forma
    medible, no se incorpora.

## 4. Criterio para incorporar algo al laboratorio

Toda incorporación debe responder estas preguntas antes de escribirse:

1. ¿Qué conocimiento nuevo aporta que no esté ya en la base?
2. ¿Qué capacidades existentes del núcleo reutiliza?
3. ¿Qué capacidad nueva exige, y a quién más le servirá?
4. ¿Qué perfil profesional complementa?
5. ¿Cómo se valida de forma independiente?
6. ¿Qué prueba automática impide que se rompa?

Una incorporación que no responde la 5 y la 6 no entra.

## 5. Qué no se hará

- Convertir el repositorio en material exclusivo de una institución o de una
  evaluación.
- Reproducir instrumentos reales de selección.
- Publicar datos personales, credenciales o material de terceros.
- Declarar implementado lo proyectado, ni probado lo no ejecutado.
