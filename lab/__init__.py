"""Núcleo del Applied Data Analysis and Assessment Lab.

Componentes
    `core`        utilidades de lectura, perfilado, cruce auditado y exportación.
    `contracts`   contratos de datos y validación con informe de hallazgos.
    `metrics`     indicadores, estadística descriptiva y razones seguras.
    `dates`       fechas, duraciones y bandas horarias.
    `stats`       inferencia estadística sin dependencias externas.
    `sqlbridge`   ejecución de SQL sobre DataFrames para validación independiente.
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

__version__ = "0.1.0"

__all__ = [
    "agents",
    "assessment",
    "catalog",
    "console",
    "contracts",
    "core",
    "dates",
    "excel",
    "knowledge",
    "learning",
    "method",
    "metrics",
    "profiles",
    "report",
    "sqlbridge",
    "stats",
    "viz",
]
