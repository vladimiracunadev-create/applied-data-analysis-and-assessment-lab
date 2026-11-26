# Applied Data Analysis and Assessment Lab

![Applied Data Analysis and Assessment Lab](assets/banner.svg)

[![Tests](https://github.com/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/actions/workflows/ci.yml)
![Versión 0.1.0](https://img.shields.io/badge/versi%C3%B3n-0.1.0-11253B)
![Python 3.11–3.14](https://img.shields.io/badge/Python-3.11%E2%80%933.14-3776AB)
![Licencia MIT](https://img.shields.io/badge/licencia-MIT-147D70)
![Datos sintéticos](https://img.shields.io/badge/datos-sint%C3%A9ticos-5C6B7A)

Laboratorio profesional, genérico y evolutivo para **resolver problemas de datos,
investigar, experimentar y preparar evaluaciones técnicas** en cualquier sector.

Su principio rector: **resolver los problemas de hoy y convertir el conocimiento
adquirido en capacidades reutilizables para los problemas de mañana.**

🇬🇧 [English version](README.en.md)

---

## Navegación

| | |
| --- | --- |
| **Empezar** | [Inicio rápido](#inicio-rápido) · [Manual](docs/manual.md) · [Arquitectura](docs/arquitectura.md) |
| **Aprender** | [Programa de aprendizaje](docs/programa.md) · [Perfiles profesionales](docs/perfiles.md) · [Equivalencias SQL/Pandas/Excel/R](docs/equivalencias.md) |
| **Resolver** | [Catálogo de casos](docs/catalogo-casos.md) · [Metodología de 18 etapas](docs/metodologia.md) · [Método de investigación](docs/research-method.md) |
| **Evaluarse** | [Simulaciones de 4 horas](simulations/) · [Preparación DTPM](cases/transport/README.md) · [Antecedentes verificados](docs/dtpm-antecedentes.md) |
| **Consultar** | [Base de conocimiento](docs/conocimiento.md) · [Diccionario de datos](docs/diccionario.md) · [Contratos de agentes](docs/agentes.md) |
| **Gobernanza** | [Hoja de ruta](docs/roadmap.md) · [Cambios](CHANGELOG.md) · [Contribuir](CONTRIBUTING.md) · [Seguridad](SECURITY.md) · [Estándar visual](docs/visual-standard.md) · [Prompt maestro](PROMPT_MAESTRO.md) |

---

## Qué es esto

```mermaid
flowchart LR
    A[Problema nuevo] --> B[Metodología<br/>18 etapas]
    B --> C[Contrato y<br/>calidad de datos]
    C --> D[Análisis con<br/>el núcleo]
    D --> E[Validación<br/>independiente]
    E --> F[Informe con<br/>supuestos y límites]
    F --> G[Conocimiento<br/>reutilizable]
    G --> H[Capacidad nueva<br/>en el núcleo]
    H --> A
```

El laboratorio tiene tres piezas que no se mezclan:

- **Un núcleo transversal** (`lab/`, 17 módulos) que no sabe nada de ningún dominio:
  contratos de datos, indicadores, fechas, inferencia estadística, puente SQL, libros
  de Excel auditables, informes, metodología, base de conocimiento.
- **Casos de estudio independientes** (`cases/`) que resuelven problemas reales de un
  sector y no se conocen entre sí.
- **Un laboratorio de evaluaciones** (`assessments/`) que genera simulaciones
  reproducibles con rúbrica, para prepararse ante cualquier proceso técnico.

Cada problema resuelto deja registro en la base de conocimiento y, cuando hace falta
algo nuevo, el núcleo crece con su prueba automática.

---

## Inicio rápido

```powershell
uv sync
```

```powershell
uv run python scripts/generate_data.py
```

```powershell
uv run python -m pytest
```

Sin `uv`, el equivalente con pip:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -e .
```

### Qué hacer a continuación

```powershell
uv run python solutions/reference.py 1
```

```powershell
uv run python scripts/build_excel_solutions.py
```

```powershell
uv run python -m lab.knowledge "denominador cero"
```

```powershell
uv run jupyter lab
```

---

## Prioridad inmediata: evaluación técnica de gestor de datos (30 de noviembre de 2026)

El primer caso aplicado del laboratorio es la preparación para una evaluación técnica
de cuatro horas en Excel y Python con Pandas (o RStudio como alternativa), en el
dominio del transporte público.

**Qué hay implementado y verificado para eso:**

| Recurso | Dónde | Cómo se verifica |
| --- | --- | --- |
| 3 simulaciones de 4 horas con rúbrica | [`simulations/`](simulations/) | enunciados versionados |
| 3 datasets sintéticos con defectos controlados | `data/case_1..3` | `scripts/generate_data.py`, semilla fija |
| Solución de referencia en Pandas | `solutions/reference.py` | `tests/test_reference.py` |
| **Segunda implementación en SQL** | `solutions/sql_reference.py` | `tests/test_cross_validation.py` |
| **Libros de Excel resueltos con fórmulas vivas** | `solutions/excel/` | `tests/test_excel_solutions.py` |
| Equivalencias SQL ↔ Pandas ↔ Excel ↔ R | [`docs/equivalencias.md`](docs/equivalencias.md) | — |
| Banco de 15 ítems con criterios y trampas | `assessments/items/` | `tests/test_assessment.py` |
| Ruta de estudio y antecedentes públicos | [`docs/dtpm-antecedentes.md`](docs/dtpm-antecedentes.md) | fuentes abiertas y citadas |

**La validación cruzada es la pieza central.** `solutions/reference.py` (Pandas) y
`solutions/sql_reference.py` (SQL sobre los CSV cargados como texto) resuelven el mismo
problema sin compartir una línea de código, y las pruebas los confrontan indicador por
indicador con tolerancia 10⁻⁹. Esa confrontación **encontró un defecto real**: la
duración calculada con `julianday` difería en el séptimo decimal e invertía la
comparación «duración ≤ meta» justo en los empates, moviendo la puntualidad varios
puntos porcentuales. Con una sola implementación el número habría pasado por correcto.
Está documentado en [`knowledge/julianday-precision.md`](knowledge/julianday-precision.md).

Para generar una simulación nueva y reproducible:

```powershell
uv run python scripts/build_assessment.py --blueprint gestor-datos-transporte --seed 1
```

> Las simulaciones son **material de entrenamiento** propio del laboratorio. No son
> pruebas oficiales de ninguna institución ni reproducen instrumentos reales de
> selección. Cada proceso fija sus propias reglas sobre el uso de asistentes de IA;
> este repositorio no autoriza su uso durante una evaluación.

---

## El núcleo

| Módulo | Para qué sirve |
| --- | --- |
`lab.method` | Metodología de 18 etapas como objeto auditable: una etapa no se completa sin evidencia
`lab.contracts` | Contratos de datos: tipos, dominios, claves y severidad de cada hallazgo
`lab.core` | Lectura, perfil de calidad y cruce auditado con control de cardinalidad
`lab.dates` | Fechas, duraciones y bandas horarias, informando qué no se pudo interpretar
`lab.metrics` | Razones seguras, percentiles con método declarado, tasa ponderada frente a promedio simple
`lab.stats` | Intervalos de confianza, Welch, Pearson y chi-cuadrado **sin SciPy**, validados contra tablas publicadas
`lab.sqlbridge` | Ejecutar SQL real sobre DataFrames para validar de forma independiente
`lab.excel` | Libros con fórmulas vivas, unidades y separación entradas / cálculos / resultados
`lab.viz` | Gráficos con título, unidad, período, fuente y escala honesta obligatorios
`lab.report` | Informes que se niegan a exportarse sin sus secciones obligatorias
`lab.catalog` | Estado real de cada caso: 26 campos de metadatos exigidos
`lab.knowledge` | Base de conocimiento con búsqueda TF-IDF, sin modelos ni red
`lab.learning` | Validador del estándar pedagógico: 17 secciones por clase
`lab.assessment` | Motor de evaluaciones: configuración, generación reproducible y rúbricas
`lab.agents` | 20 contratos de capacidades especializadas y un arnés que los verifica
`lab.profiles` | 11 perfiles profesionales con su cobertura real medida
`lab.console` | Salida UTF-8 legible también en consolas de Windows

Ejemplo mínimo de dos cosas que el laboratorio hace cumplir siempre:

```python
from lab.metrics import compare_rates, safe_ratio

safe_ratio(1, 0)                      # nan, no una excepción ni un cero
compare_rates([1, 90], [2, 100])      # ponderada 89.2 %, simple 70.0 %, 19.2 pp de brecha
```

---

## Casos y evaluaciones disponibles

| Caso | Industria | Dificultad | Tiempo | Competencias |
| --- | --- | --- | --- | --- |
| [`transport`](cases/transport/README.md) | Transporte | avanzado | 240 min | 12 |
| [`retail`](cases/retail/README.md) | Comercio | intermedio | 90 min | 6 |
| [`education`](cases/education/README.md) | Educación | introductorio | 90 min | 6 |

El [catálogo completo](docs/catalogo-casos.md) se genera desde los metadatos y marca
los casos incompletos en lugar de ocultarlos. Para crear uno nuevo:

```powershell
uv run python scripts/new_case.py mi-caso
```

---

## Programa de aprendizaje

**8 clases publicadas** en 6 bloques, cada una con las 17 secciones del estándar:
objetivos, prerrequisitos, definiciones simples y formales, fundamentos, fórmulas con
variables y unidades, ejemplos progresivos, aplicaciones profesionales, código
comentado, ejercicios, soluciones explicadas, errores frecuentes, criterios de
validación, preguntas de evaluación, referencias verificables y glosario.

```mermaid
flowchart TD
    f["Fundamentos de datos<br/>2 clases"] --> m["Matemáticas y estadística<br/>1 clase"]
    m --> p["Programación aplicada<br/>2 clases"]
    p --> i["Ingeniería y calidad<br/>1 clase"]
    i --> a["Análisis y comunicación<br/>1 clase"]
    a --> inv["Investigación aplicada<br/>1 clase"]
    inv --> av["Temas avanzados<br/>proyectado"]
```

El validador mantiene vivo el estándar: una clase a la que le falte una sección hace
fallar la suite.

```powershell
uv run python -m lab.learning
```

Ver el [programa completo](docs/programa.md) y los
[perfiles profesionales](docs/perfiles.md) con su cobertura medida.

---

## Calidad y validación

```powershell
uv run python -m pytest
```

Lo que la suite protege, además de los cálculos:

- **Validación cruzada entre tecnologías**: Pandas contra SQL, indicador por indicador.
- **Estadística contra valores publicados**: la t de Student, la chi-cuadrado y el
  intervalo de Wilson se comparan con tablas y artículos, no consigo mismos.
- **Mediana y P90 contra una implementación en Python puro**, sin NumPy ni pandas.
- **Estructura de los libros de Excel**: que las fórmulas sean fórmulas y apunten al
  rango correcto.
- **Estándar pedagógico**: 17 secciones por clase.
- **Metadatos de los casos**: 26 campos por caso.
- **Arnés de agentes**: sin responsabilidades duplicadas ni referencias inexistentes.
- **Coherencia del repositorio**: versión única, enlaces relativos vivos, núcleo sin
  dependencias de dominio, documentación derivada al día, ausencia de secretos.

### Lo que la suite **no** cubre

Las pruebas verifican que las fórmulas de Excel existan, sean fórmulas y referencien
los rangos correctos; **no** evalúan su resultado numérico, porque eso exige Excel o
LibreOffice y no están disponibles en integración continua. Esa comprobación la hace la
hoja `30_control` de cada libro al abrirlo, y el acuerdo numérico entre
implementaciones queda cubierto por la validación Pandas ↔ SQL, que sí se ejecuta.
La distinción está declarada en [`docs/roadmap.md`](docs/roadmap.md).

Tras cualquier cambio en el código, regenere la documentación derivada:

```powershell
uv run python scripts/build_docs.py
```

---

## Ecosistema tecnológico

**Entorno mínimo** (siete paquetes): Python, pandas, NumPy, openpyxl, XlsxWriter,
Matplotlib, JupyterLab y pytest. Nada más es obligatorio.

**Integrado sin dependencias nuevas:** SQL mediante `sqlite3` de la biblioteca
estándar, e inferencia estadística implementada en `lab.stats`.

**Opcional y detectado en tiempo de ejecución:** DuckDB
(`lab.sqlbridge.duckdb_available()`).

**Declarado en la hoja de ruta, no implementado:** Polars, R/RStudio, Power BI,
Tableau, Metabase, GeoPandas, QGIS, Arrow/Parquet, SciPy, Statsmodels, scikit-learn,
Docker, n8n, bases vectoriales y búsqueda semántica. La
[hoja de ruta](docs/roadmap.md) distingue de forma estricta lo implementado de lo
proyectado, y declara cada brecha medida.

---

## Datos y privacidad

Los datos de este repositorio son **sintéticos, generados con semilla fija** y no
describen ningún sistema real. Los antecedentes públicos consultados están citados con
su fecha en [`docs/dtpm-antecedentes.md`](docs/dtpm-antecedentes.md), separando lo
verificado de lo pendiente.

No publique datos personales, credenciales ni material de terceros. Lea
[`SECURITY.md`](SECURITY.md) antes de incorporar cualquier dataset.

---

## Licencia

[MIT](LICENSE). El código y la documentación son reutilizables; los datos de terceros
que algún caso futuro incorpore mantendrán su propia licencia, declarada en el
`case.json` correspondiente.
