"""Programa de aprendizaje: estructura, estándar de clase y validador.

Qué hace
    Modela el programa (bloques → módulos → clases), define las secciones que toda
    clase del laboratorio debe contener y valida los archivos reales de
    `docs/learning/`. También construye el mapa de aprendizaje en Mermaid y el
    índice navegable.

Por qué existe
    El estándar pedagógico del laboratorio exige diecisiete secciones por clase. Un
    estándar que nadie comprueba se degrada en dos semanas. El validador convierte
    el estándar en una prueba automática: una clase a la que le falte «errores
    frecuentes» o «referencias» hace fallar la suite.

Convención de archivos
    `docs/learning/<bloque>/<NN>-<slug>.md`, con un encabezado `# Título` y las
    secciones como encabezados de nivel 2 cuyo texto contenga la palabra clave de la
    sección. El prefijo numérico fija el orden dentro del bloque.

Cómo se valida
    `tests/test_learning.py` verifica el descubrimiento de clases, el rechazo de una
    clase incompleta y que todas las clases publicadas cumplan el estándar.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LEARNING_DIR = ROOT / "docs" / "learning"

#: Secciones obligatorias de una clase. La clave es el identificador interno; el
#: valor es la expresión que debe aparecer en el encabezado de nivel 2.
REQUIRED_SECTIONS: tuple[tuple[str, str], ...] = (
    ("objetivos", "objetivos"),
    ("prerrequisitos", "prerrequisitos"),
    ("definiciones", "definiciones"),
    ("explicacion", "explicación"),
    ("fundamentos", "fundamentos"),
    ("formulas", "fórmulas"),
    ("variables", "variables"),
    ("ejemplos", "ejemplos"),
    ("aplicaciones", "aplicaciones"),
    ("codigo", "código"),
    ("ejercicios", "ejercicios"),
    ("soluciones", "soluciones"),
    ("errores", "errores frecuentes"),
    ("validacion", "validación"),
    ("evaluacion", "evaluación"),
    ("referencias", "referencias"),
    ("glosario", "glosario"),
)

#: Bloques del programa. El orden es la progresión recomendada.
BLOCKS: tuple[tuple[str, str, str], ...] = (
    ("00-fundamentos", "Fundamentos de datos",
     "Qué es un dato, un registro, una tabla, un tipo y una clave; cómo se lee y se escribe."),
    ("10-matematicas", "Matemáticas y estadística aplicadas",
     "Aritmética de indicadores, probabilidad, estadística descriptiva e inferencia básica."),
    ("20-programacion", "Programación aplicada a datos",
     "Python, Pandas y hojas de cálculo como herramientas equivalentes para el mismo problema."),
    ("30-ingenieria", "Ingeniería y calidad de datos",
     "Contratos, validación, cruces, ETL, trazabilidad y gobernanza."),
    ("40-analisis", "Análisis y comunicación",
     "Indicadores, visualización, informes y apoyo a la decisión."),
    ("50-investigacion", "Investigación aplicada",
     "Preguntas, hipótesis, diseño, sesgos, validez y reproducibilidad."),
    ("60-avanzado", "Temas avanzados",
     "Series temporales, geoespacial, optimización, simulación y aprendizaje automático."),
)

BLOCK_TITLES: dict[str, str] = {key: title for key, title, _ in BLOCKS}

_HEADING = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_TITLE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_FILENAME = re.compile(r"^(\d{2})-([a-z0-9][a-z0-9-]*)\.md$")

#: Normalización para comparar encabezados sin depender de tildes ni mayúsculas.
_FOLD = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")


def _fold(text: str) -> str:
    return text.translate(_FOLD).lower()


@dataclass
class Lesson:
    """Una clase del programa."""

    path: Path
    block: str
    order: int
    slug: str
    title: str
    headings: tuple[str, ...]
    word_count: int
    issues: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues

    @property
    def reference(self) -> str:
        """Ruta relativa a la raíz del repositorio, con separadores POSIX.

        Si la clase está fuera del repositorio —por ejemplo al validar un directorio
        de pruebas— se devuelve la ruta absoluta en lugar de fallar: el validador debe
        poder informar sobre cualquier archivo que se le entregue.
        """
        try:
            return self.path.relative_to(ROOT).as_posix()
        except ValueError:
            return self.path.as_posix()

    def as_row(self) -> dict[str, object]:
        return {
            "bloque": BLOCK_TITLES.get(self.block, self.block),
            "orden": self.order,
            "clase": self.slug,
            "titulo": self.title,
            "palabras": self.word_count,
            "secciones": len(self.headings),
            "cumple_estandar": "sí" if self.ok else "no",
            "ruta": self.reference,
        }


def check_sections(headings: Iterable[str]) -> list[str]:
    """Devuelve las secciones obligatorias ausentes entre los encabezados dados."""
    folded = [_fold(h) for h in headings]
    missing = []
    for key, needle in REQUIRED_SECTIONS:
        target = _fold(needle)
        if not any(target in heading for heading in folded):
            missing.append(key)
    return missing


def load_lesson(path: str | Path) -> Lesson:
    """Carga una clase y comprueba su cumplimiento del estándar.

    Raises:
        ValueError: si el nombre de archivo no sigue la convención `NN-slug.md` o si
            el archivo no tiene título de nivel 1.
    """
    file_path = Path(path)
    match = _FILENAME.match(file_path.name)
    if not match:
        raise ValueError(
            f"{file_path.name}: el nombre debe seguir la convención 'NN-slug.md'."
        )
    text = file_path.read_text(encoding="utf-8")
    title_match = _TITLE.search(text)
    if not title_match:
        raise ValueError(f"{file_path}: falta el título de nivel 1 ('# ...').")
    headings = tuple(m.group(1) for m in _HEADING.finditer(text))
    missing = check_sections(headings)
    issues = [f"falta la sección obligatoria '{m}'" for m in missing]
    return Lesson(
        path=file_path,
        block=file_path.parent.name,
        order=int(match.group(1)),
        slug=match.group(2),
        title=title_match.group(1),
        headings=headings,
        word_count=len(text.split()),
        issues=issues,
    )


def discover_lessons(directory: str | Path = LEARNING_DIR) -> list[Lesson]:
    """Encuentra todas las clases del programa, ordenadas por bloque y número."""
    base = Path(directory)
    if not base.exists():
        return []
    lessons = [
        load_lesson(p)
        for p in sorted(base.glob("*/*.md"))
        if _FILENAME.match(p.name)
    ]
    block_order = {key: index for index, (key, _, _) in enumerate(BLOCKS)}
    return sorted(lessons, key=lambda leccion: (block_order.get(leccion.block, 99), leccion.order, leccion.slug))


def program_frame(lessons: Iterable[Lesson]) -> pd.DataFrame:
    """Programa como tabla."""
    rows = [leccion.as_row() for leccion in lessons]
    columns = ["bloque", "orden", "clase", "titulo", "palabras", "secciones",
               "cumple_estandar", "ruta"]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows, columns=columns)


def program_markdown(lessons: Iterable[Lesson], base_from: str = "docs") -> str:
    """Índice navegable del programa, agrupado por bloque.

    Args:
        lessons: clases descubiertas.
        base_from: carpeta desde la cual se escriben los enlaces relativos.
    """
    lessons = list(lessons)
    by_block: dict[str, list[Lesson]] = {}
    for lesson in lessons:
        by_block.setdefault(lesson.block, []).append(lesson)
    lines: list[str] = []
    for key, title, description in BLOCKS:
        block_lessons = by_block.get(key, [])
        lines += [f"### {title}", "", description, ""]
        if not block_lessons:
            lines += ["_Bloque declarado en la hoja de ruta; sin clases publicadas todavía._", ""]
            continue
        for lesson in block_lessons:
            relative = lesson.reference
            if base_from and relative.startswith(f"{base_from}/"):
                relative = relative[len(base_from) + 1:]
            flag = "" if lesson.ok else " ⚠️ incompleta"
            lines.append(f"- [{lesson.order:02d}. {lesson.title}]({relative}){flag}")
        lines.append("")
    return "\n".join(lines)


def learning_map_mermaid() -> str:
    """Mapa de aprendizaje como diagrama Mermaid, derivado de `BLOCKS`."""
    lines = ["```mermaid", "flowchart TD"]
    for index, (key, title, _) in enumerate(BLOCKS):
        node = key.replace("-", "_")
        lines.append(f'    {node}["{title}"]')
        if index:
            previous = BLOCKS[index - 1][0].replace("-", "_")
            lines.append(f"    {previous} --> {node}")
    lines.append("```")
    return "\n".join(lines) + "\n"


def coverage_summary(lessons: Iterable[Lesson]) -> pd.DataFrame:
    """Cobertura real por bloque: cuántas clases hay y cuántas cumplen el estándar."""
    lessons = list(lessons)
    rows = []
    for key, title, _ in BLOCKS:
        block = [leccion for leccion in lessons if leccion.block == key]
        rows.append({
            "bloque": title,
            "clases": len(block),
            "cumplen_estandar": sum(1 for leccion in block if leccion.ok),
            "estado": "publicado" if block else "proyectado",
        })
    return pd.DataFrame(rows, columns=["bloque", "clases", "cumplen_estandar", "estado"])


if __name__ == "__main__":  # pragma: no cover - utilidad de consola
    from lab.console import enable_utf8

    enable_utf8()
    found = discover_lessons()
    print(coverage_summary(found).to_string(index=False))
    broken = [leccion for leccion in found if not leccion.ok]
    if broken:
        print("\nClases que no cumplen el estándar:")
        for lesson in broken:
            print(f"  {lesson.reference}: {'; '.join(lesson.issues)}")
        raise SystemExit(1)
    print(f"\n{len(found)} clase(s) cumplen las {len(REQUIRED_SECTIONS)} secciones obligatorias.")
