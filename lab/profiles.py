"""Perfiles y rutas profesionales que el laboratorio permite desarrollar.

Qué hace
    Declara perfiles profesionales con sus competencias, herramientas, bloques del
    programa que les corresponden y evidencias que demuestran la competencia.
    Permite cruzar perfiles con casos y con clases publicadas para ver qué parte de
    cada ruta está realmente cubierta.

Por qué existe
    «Aprender datos» no es una meta verificable. Un perfil con competencias y
    evidencias sí lo es: se puede comprobar si existe un caso resuelto, una clase y
    una simulación que respalden cada competencia declarada.

Cómo se valida
    `tests/test_profiles.py` comprueba la consistencia de los perfiles (bloques y
    competencias existentes, sin duplicados) y el cálculo de cobertura.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd

from lab.learning import BLOCK_TITLES

#: Competencias transversales del laboratorio. Los casos y los ítems de evaluación
#: declaran competencias de esta lista, de modo que todo quede cruzable.
COMPETENCIES: tuple[str, ...] = (
    "lectura-escritura-datos",
    "calidad-datos",
    "limpieza-normalizacion",
    "cruce-consolidacion",
    "fechas-horarios",
    "agregacion-indicadores",
    "estadistica-descriptiva",
    "inferencia-estadistica",
    "modelamiento",
    "visualizacion",
    "hojas-de-calculo",
    "sql",
    "automatizacion",
    "ingenieria-datos",
    "gobernanza-datos",
    "investigacion-aplicada",
    "comunicacion-resultados",
    "apoyo-decision",
    "validacion-independiente",
    "reproducibilidad",
)


@dataclass(frozen=True)
class Profile:
    """Un perfil profesional.

    Args:
        slug: identificador en kebab-case.
        name: nombre del perfil.
        focus: qué distingue a este perfil de los vecinos.
        core: competencias imprescindibles.
        supporting: competencias complementarias.
        tools: herramientas típicas del perfil.
        blocks: bloques del programa que componen su ruta.
        evidence: evidencias que demuestran la competencia del perfil.
    """

    slug: str
    name: str
    focus: str
    core: tuple[str, ...]
    supporting: tuple[str, ...]
    tools: tuple[str, ...]
    blocks: tuple[str, ...]
    evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        unknown = sorted(set(self.core + self.supporting) - set(COMPETENCIES))
        if unknown:
            raise ValueError(f"{self.slug}: competencias no declaradas {unknown}.")
        overlap = sorted(set(self.core) & set(self.supporting))
        if overlap:
            raise ValueError(f"{self.slug}: competencias en núcleo y apoyo a la vez {overlap}.")
        bad_blocks = sorted(set(self.blocks) - set(BLOCK_TITLES))
        if bad_blocks:
            raise ValueError(f"{self.slug}: bloques inexistentes {bad_blocks}.")
        if not self.evidence:
            raise ValueError(f"{self.slug}: un perfil sin evidencias no es verificable.")


PROFILES: tuple[Profile, ...] = (
    Profile(
        slug="analista-de-datos",
        name="Analista de datos",
        focus="Responder preguntas de negocio con datos existentes y comunicarlas.",
        core=("lectura-escritura-datos", "limpieza-normalizacion", "agregacion-indicadores",
              "estadistica-descriptiva", "visualizacion", "hojas-de-calculo",
              "comunicacion-resultados"),
        supporting=("sql", "calidad-datos", "apoyo-decision"),
        tools=("Python", "Pandas", "Polars", "R", "Excel", "SQL", "Power BI"),
        blocks=("00-fundamentos", "10-matematicas", "20-programacion", "40-analisis"),
        evidence=("un caso resuelto con informe e indicadores validados",
                  "un libro de Excel con fórmulas auditables",
                  "una simulación cronometrada corregida con rúbrica"),
    ),
    Profile(
        slug="gestor-de-datos",
        name="Gestor de datos",
        focus="Asegurar que los datos de una organización sean correctos, trazables y utilizables.",
        core=("calidad-datos", "limpieza-normalizacion", "cruce-consolidacion",
              "fechas-horarios", "agregacion-indicadores", "gobernanza-datos",
              "validacion-independiente", "hojas-de-calculo"),
        supporting=("sql", "automatizacion", "comunicacion-resultados", "reproducibilidad"),
        tools=("Python", "Pandas", "Polars", "R", "Excel", "SQL", "Power Query"),
        blocks=("00-fundamentos", "20-programacion", "30-ingenieria", "40-analisis"),
        evidence=("informe de calidad con hallazgos por regla y columna",
                  "cruce auditado con control de cardinalidad",
                  "validación cruzada entre Pandas, Polars, R, SQL y hoja de cálculo"),
    ),
    Profile(
        slug="ingeniero-de-datos",
        name="Ingeniero de datos",
        focus="Construir los procesos que llevan datos desde el origen hasta el consumo.",
        core=("ingenieria-datos", "automatizacion", "calidad-datos", "sql",
              "reproducibilidad", "lectura-escritura-datos"),
        supporting=("gobernanza-datos", "cruce-consolidacion", "modelamiento"),
        tools=("Python", "Polars", "SQL", "DuckDB", "Parquet", "Docker", "GitHub Actions"),
        blocks=("00-fundamentos", "20-programacion", "30-ingenieria"),
        evidence=("proceso ETL reproducible con pruebas",
                  "contrato de datos aplicado en integración continua"),
    ),
    Profile(
        slug="cientifico-de-datos",
        name="Científico de datos",
        focus="Modelar fenómenos y cuantificar incertidumbre para anticipar o explicar.",
        core=("estadistica-descriptiva", "inferencia-estadistica", "modelamiento",
              "visualizacion", "investigacion-aplicada", "reproducibilidad"),
        supporting=("limpieza-normalizacion", "sql", "comunicacion-resultados"),
        tools=("Python", "Pandas", "Polars", "NumPy", "scikit-learn", "Statsmodels", "R"),
        blocks=("10-matematicas", "20-programacion", "50-investigacion", "60-avanzado"),
        evidence=("investigación con hipótesis, prueba y limitaciones declaradas",
                  "modelo con validación fuera de muestra"),
    ),
    Profile(
        slug="analista-de-negocios",
        name="Analista de negocios",
        focus="Traducir un problema de negocio en requisitos, métricas y decisiones.",
        core=("agregacion-indicadores", "apoyo-decision", "comunicacion-resultados",
              "hojas-de-calculo"),
        supporting=("estadistica-descriptiva", "visualizacion", "calidad-datos"),
        tools=("Excel", "Power BI", "SQL"),
        blocks=("00-fundamentos", "40-analisis"),
        evidence=("definición de indicadores con fórmula, unidad y denominador",
                  "informe con recomendación proporcional a la evidencia"),
    ),
    Profile(
        slug="especialista-bi",
        name="Especialista en inteligencia de negocios",
        focus="Industrializar indicadores en modelos y tableros confiables.",
        core=("agregacion-indicadores", "visualizacion", "sql", "gobernanza-datos"),
        supporting=("ingenieria-datos", "automatizacion", "apoyo-decision"),
        tools=("Power BI", "Tableau", "Metabase", "SQL", "Power Query"),
        blocks=("20-programacion", "30-ingenieria", "40-analisis"),
        evidence=("modelo de datos documentado con su grano",
                  "tablero con definiciones de métrica visibles"),
    ),
    Profile(
        slug="investigador-aplicado",
        name="Investigador aplicado",
        focus="Producir evidencia reproducible sobre preguntas abiertas.",
        core=("investigacion-aplicada", "inferencia-estadistica", "reproducibilidad",
              "comunicacion-resultados"),
        supporting=("calidad-datos", "visualizacion", "validacion-independiente"),
        tools=("Python", "R", "JupyterLab", "LaTeX o Markdown"),
        blocks=("10-matematicas", "50-investigacion"),
        evidence=("informe de investigación completo con sesgos e incertidumbre",
                  "material reproducible con semilla y dependencias"),
    ),
    Profile(
        slug="especialista-calidad-datos",
        name="Especialista en calidad de datos",
        focus="Definir, medir y mejorar la aptitud de los datos para su uso.",
        core=("calidad-datos", "gobernanza-datos", "validacion-independiente",
              "limpieza-normalizacion"),
        supporting=("automatizacion", "cruce-consolidacion", "reproducibilidad"),
        tools=("Python", "Pandera", "SQL", "Excel"),
        blocks=("00-fundamentos", "30-ingenieria"),
        evidence=("contrato de datos con reglas y severidades",
                  "tablero de defectos con evolución en el tiempo"),
    ),
    Profile(
        slug="especialista-visualizacion",
        name="Especialista en visualización",
        focus="Hacer que el resultado se entienda sin distorsionarlo.",
        core=("visualizacion", "comunicacion-resultados"),
        supporting=("agregacion-indicadores", "apoyo-decision"),
        tools=("Matplotlib", "Plotly", "Power BI", "D3"),
        blocks=("40-analisis",),
        evidence=("conjunto de gráficos con escalas honestas y accesibilidad verificada",),
    ),
    Profile(
        slug="arquitecto-soluciones-datos",
        name="Arquitecto de soluciones de datos",
        focus="Decidir la estructura técnica que sostiene el análisis en el tiempo.",
        core=("ingenieria-datos", "gobernanza-datos", "reproducibilidad", "modelamiento"),
        supporting=("automatizacion", "sql", "calidad-datos", "apoyo-decision"),
        tools=("Python", "SQL", "Docker", "Arrow/Parquet", "servicios cloud"),
        blocks=("20-programacion", "30-ingenieria", "60-avanzado"),
        evidence=("decisión de arquitectura documentada con alternativas descartadas",
                  "contratos entre componentes verificados por pruebas"),
    ),
    Profile(
        slug="especialista-investigacion-operaciones",
        name="Especialista en investigación de operaciones",
        focus="Optimizar decisiones bajo restricciones y simular escenarios.",
        core=("modelamiento", "investigacion-aplicada", "apoyo-decision"),
        supporting=("estadistica-descriptiva", "visualizacion", "reproducibilidad"),
        tools=("Python", "SciPy", "solvers de programación lineal", "simulación"),
        blocks=("10-matematicas", "60-avanzado"),
        evidence=("modelo de optimización con función objetivo y restricciones explícitas",
                  "simulación con análisis de sensibilidad"),
    ),
)


def profiles_frame(profiles: Iterable[Profile] = PROFILES) -> pd.DataFrame:
    """Perfiles como tabla."""
    rows = [
        {
            "perfil": p.slug,
            "nombre": p.name,
            "foco": p.focus,
            "competencias_nucleo": len(p.core),
            "competencias_apoyo": len(p.supporting),
            "herramientas": ", ".join(p.tools),
            "ruta": " → ".join(BLOCK_TITLES[b] for b in p.blocks),
        }
        for p in profiles
    ]
    columns = ["perfil", "nombre", "foco", "competencias_nucleo", "competencias_apoyo",
               "herramientas", "ruta"]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows, columns=columns)


def competency_coverage(
    case_competencies: Iterable[str], profiles: Iterable[Profile] = PROFILES
) -> pd.DataFrame:
    """Qué parte del núcleo de cada perfil está cubierta por casos del laboratorio.

    Args:
        case_competencies: competencias declaradas por los casos implementados.
        profiles: perfiles a evaluar.

    Returns:
        Tabla con cobertura por perfil y las competencias que faltan. Esta tabla es
        el estado real: sirve para priorizar qué caso construir después.
    """
    available = set(case_competencies)
    rows = []
    for profile in profiles:
        covered = [c for c in profile.core if c in available]
        missing = [c for c in profile.core if c not in available]
        rows.append({
            "perfil": profile.name,
            "nucleo": len(profile.core),
            "cubiertas": len(covered),
            "cobertura_pct": round(100.0 * len(covered) / len(profile.core), 1),
            "faltantes": ", ".join(missing) or "—",
        })
    return pd.DataFrame(rows, columns=["perfil", "nucleo", "cubiertas", "cobertura_pct",
                                       "faltantes"])


def profiles_markdown(profiles: Iterable[Profile] = PROFILES) -> str:
    """Documentación de los perfiles, generada desde los datos."""
    lines: list[str] = []
    for profile in profiles:
        lines += [
            f"### {profile.name} (`{profile.slug}`)",
            "",
            profile.focus,
            "",
            f"- **Ruta de aprendizaje:** {' → '.join(BLOCK_TITLES[b] for b in profile.blocks)}",
            f"- **Herramientas:** {', '.join(profile.tools)}",
            f"- **Competencias núcleo:** {', '.join(f'`{c}`' for c in profile.core)}",
            f"- **Competencias de apoyo:** {', '.join(f'`{c}`' for c in profile.supporting) or '—'}",
            "- **Evidencias que demuestran el perfil:**",
        ]
        lines += [f"  - {e}" for e in profile.evidence]
        lines.append("")
    return "\n".join(lines)
