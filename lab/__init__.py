"""Núcleo del Applied Data Analysis and Assessment Lab.

Componentes
    `cuaderno`    cuadernos: Pandas, Excel, motores alternativos y salidas reales.
    `notebook_enrichment` Polars, R, gráficos y navegación de los diez cuadernos.
    `core`        utilidades de lectura, perfilado, cruce auditado y exportación.
    `contracts`   contratos de datos y validación con informe de hallazgos.
    `metrics`     indicadores, estadística descriptiva y razones seguras.
    `dates`       fechas, duraciones y bandas horarias.
    `textual`     normalización de texto para agrupar y cruzar.
    `calendars`   calendarios por reglas, con auditoría de exclusiones.
    `schedules`   horarios de atención en texto libre, con lo ilegible como desconocido.
    `geo`         distancias sobre la esfera y conversión de UTM.
    `hoja_svg`    dibuja un fragmento de hoja de cálculo, con su fórmula, en SVG.
    `keys`        qué identifica una fila, y qué hacer cuando nada lo hace.
    `stats`       inferencia estadística sin dependencias externas.
    `sources`     adquisición de datos públicos con registro de procedencia.
    `sqlbridge`   ejecución de SQL sobre DataFrames para validación independiente.
    `diagrama_svg` diagramas de flujo y mapas mentales en SVG.
    `excel`       libros de Excel profesionales con fórmulas vivas.
    `viz`         gráficos con el estándar visual del laboratorio.
    `report`      informes de caso y de investigación con secciones obligatorias.
    `method`      metodología universal de dieciocho etapas, auditable.
    `catalog`     catálogo de casos y control de metadatos.
    `knowledge`   base de conocimiento con búsqueda léxica.
    `learning`    programa de aprendizaje y validador del estándar de clase.
    `assessment`  motor de evaluaciones técnicas y rúbricas.
    `agents`      contratos de skills y agentes, con arnés de verificación.
    `profiles`    perfiles y rutas profesionales.
    `console`     salida UTF-8 legible también en consolas de Windows.

Los submódulos se importan de forma explícita (`from lab import metrics`) para que el
costo de importar matplotlib o pandas se pague solo cuando se usa.
"""

__version__ = "0.11.0"

__all__ = [
    "agents",
    "assessment",
    "calendars",
    "catalog",
    "console",
    "contracts",
    "cuaderno",
    "core",
    "dates",
    "diagrama_svg",
    "excel",
    "geo",
    "hoja_svg",
    "keys",
    "knowledge",
    "learning",
    "method",
    "metrics",
    "notebook_enrichment",
    "profiles",
    "report",
    "schedules",
    "sources",
    "sqlbridge",
    "stats",
    "textual",
    "viz",
]
