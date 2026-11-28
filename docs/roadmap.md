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
| Casos de estudio (15): 12 con datos públicos reales, metadatos o resultados reproducibles, 3 sintéticos | implementado | `python -m pytest tests/test_catalog.py` |
| Cruce espacial por proximidad sin dependencias geoespaciales | implementado | `python -m pytest tests/test_cobertura_de_carga.py` |
| Intérprete de horarios en texto libre, con lo ilegible como desconocido | implementado | `python -m pytest tests/test_schedules.py` |
| Conciliación de inventarios con grano distinto y dos criterios | implementado | `python -m pytest tests/test_correspondencia_metro.py` |
| Análisis de claves: candidatas mínimas y clave subrogada determinista | implementado | `python -m pytest tests/test_keys.py` |
| Cuadernos multiengine: 12 cuadernos cubren los 18 problemas con Pandas, Polars, R, Excel y gráficos | implementado | `python scripts/build_cuadernos.py --check` |
| Simulaciones de cuatro horas (3) | implementado | `simulations/0{1,2,3}_enunciado.md` |
| Solución de referencia en Pandas | implementado | `python solutions/reference.py 1` |
| Implementación columnar en Polars | implementado | `python solutions/polars_reference.py transport 1` |
| Implementación independiente en R base | implementado | `Rscript solutions/r_reference.R transport 1 reference_outputs/r/transport` |
| Segunda implementación en SQL | implementado | `python solutions/sql_reference.py 1` |
| Validación cruzada Pandas ↔ Polars ↔ R ↔ SQL, τ = 1e-9 | implementado | `python -m pytest tests/test_cross_validation.py tests/test_multiengine.py` |
| Paquete general de los quince casos | implementado | `python scripts/build_all_cases.py --check` |
| Libros de Excel resueltos con fórmulas vivas | implementado | `python scripts/build_excel_solutions.py` |
| Motor de evaluaciones con banco de ítems y rúbricas | implementado | `python scripts/build_assessment.py --list` |
| Programa de aprendizaje: 8 clases con 17 secciones | implementado | `python -m lab.learning` |
| Base de conocimiento (43 registros) con búsqueda léxica | implementado | `python -m lab.knowledge` |
| Contratos de 20 agentes y arnés de verificación | implementado | `python -m lab.agents` |
| Perfiles profesionales (11) con cobertura medida | implementado | `python -m pytest tests/test_profiles.py` |
| Inferencia estadística sin dependencias externas | implementado | `python -m pytest tests/test_stats.py` |
| Antecedentes públicos del DTPM verificados | implementado | `docs/dtpm-antecedentes.md` |

## 2. Brechas conocidas del estado actual

Estas brechas están **medidas**, no estimadas. Una prueba automática falla si alguna
deja de estar declarada aquí.

### 2.1 Cobertura y competencias todavía sin caso

- **`gobernanza-datos`**, brecha cerrada por P17. `cases/gobernanza_datos_dtpm`
  convierte la procedencia de la instancia en un catálogo pedagógico, conserva lo no
  declarado y prioriza licencia, esquema, actualización, responsable operativo y
  retención. Validar responsables reales con los publicadores sigue fuera del alcance;
  el repositorio no los inventa.

- **`inferencia-estadistica`.** El núcleo (`lab.stats`) está implementado y probado
  contra tablas publicadas, pero ningún caso de estudio la declara entre sus
  competencias: se usa en el material de aprendizaje, no en un caso resuelto.
  *Caso previsto:* una investigación aplicada completa con hipótesis, prueba y
  limitaciones, bajo `research/`.

- **`automatizacion`**, brecha cerrada por P18 mediante contrato, controles y
  particiones incrementales. **`modelamiento`** sigue sin caso que lo cubra.

- **`ingenieria-datos`** quedó cubierta en la versión 0.2.0 por la instancia
  `gtfs_red_movilidad`: adquisición con procedencia, lectura selectiva de un archivo de
  1,1 millones de filas desde un ZIP y expansión vectorizada de ventanas.

### 2.2 Cuadernos de trabajo — brecha cerrada

Doce cuadernos generados y ejecutables cubren los dieciocho problemas. P02 y P04 están
integrados en P01; P09 en P05; P10 en P03; P13 en P12; y P15 en P14. Cada uno trae
Markdown con salidas reales, pasos Pandas y laboratorio comparable Pandas/Polars/R,
Colab, R Markdown, libro de
práctica, al menos un gráfico estadístico, diagramas SVG y ZIP. La navegación recorre
los doce cuadernos en orden y ya no salta de P01 a P08.

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
  Pandas ↔ Polars ↔ R ↔ SQL, que sí se ejecuta.
- **Mediana y P90 en SQL.** No se calculan en SQLite por falta de una función de
  percentil con interpolación lineal. Se validan contra una implementación en Python
  puro escrita en la propia suite de pruebas.

### 2.6 Dependencias y entornos opcionales

Polars está implementado como extra `polars`; DuckDB como extra `sql` y benchmark de
P07; R base sostiene la referencia canónica y ggplot2 las visualizaciones de los diez
cuadernos reales, todo verificado en CI. Ninguno infla el
entorno mínimo. Siguen sin integración ejecutable Power BI, Tableau, Metabase,
GeoPandas, QGIS, Arrow/Parquet, Docker, n8n, bases vectoriales y búsqueda semántica con
embeddings. SciPy, Statsmodels y herramientas de visualización permanecen como extras
de contraste, no como requisitos del núcleo.

## 3. Próximos pasos, en orden de prioridad

### Fase 1 — cerrar la preparación DTPM (antes del 30 de noviembre de 2026)

1. Resolver las tres simulaciones de cuatro horas con reloj, sin consultar soluciones.
2. Corregir cada intento con la rúbrica y registrar el resultado con
   `lab.assessment.progress_frame`.
3. Repasar los registros de la base de conocimiento marcados como `error`, que son los
   defectos que más puntos cuestan en una corrección.
4. Verificar el entorno alternativo: Colab y Google Sheets con los CSV cargados.

### Fase 2 — cerrar las brechas medidas

5. Profundizar P17 con validación institucional del catálogo y responsables reales.
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

10. Parquet como formato columnar reproducible para los casos cuyo volumen lo justifique.
11. Profundizar los contrastes Polars/R cuando una diferencia de motor aporte evidencia
    nueva, no como traducción mecánica.
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
