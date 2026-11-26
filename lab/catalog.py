"""Catálogo de casos: metadatos obligatorios, clasificación y control de completitud.

Qué hace
    Lee el archivo `case.json` de cada caso, valida que estén presentes las secciones
    obligatorias y produce el catálogo navegable del laboratorio. Un caso incompleto
    aparece en el catálogo marcado como incompleto, no se oculta.

Por qué existe
    El laboratorio crece caso a caso. Sin metadatos declarados, al cabo de treinta
    casos nadie sabe qué cubre cada uno, qué competencias entrena ni si su solución
    está validada. El catálogo es la única fuente de verdad sobre el estado real.

Cómo se valida
    `tests/test_catalog.py` comprueba el descubrimiento de casos, el rechazo de
    metadatos incompletos o con valores fuera de vocabulario, y que todos los casos
    del repositorio pasen su propia validación.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

#: Nombre del archivo de metadatos dentro de cada carpeta de caso.
METADATA_FILE = "case.json"

#: Campos de identificación y clasificación. Todos obligatorios.
IDENTITY_FIELDS: tuple[str, ...] = (
    "slug", "titulo", "disciplina", "industria", "dificultad",
    "metodologia", "competencias", "estado", "tiempo_sugerido_min",
)

#: Secciones de contenido exigidas a todo caso del laboratorio.
CONTENT_FIELDS: tuple[str, ...] = (
    "contexto", "problema", "objetivos", "restricciones", "fuentes", "datasets",
    "diccionario", "supuestos", "metodologias_alternativas", "implementaciones",
    "soluciones", "resultados", "validaciones", "interpretacion", "limitaciones",
    "conocimiento_adquirido", "capacidades_reutilizables",
)

REQUIRED_FIELDS: tuple[str, ...] = IDENTITY_FIELDS + CONTENT_FIELDS

#: Vocabularios cerrados. Mantenerlos cerrados permite filtrar y comparar casos.
DIFFICULTIES: tuple[str, ...] = ("introductorio", "intermedio", "avanzado", "especializado")
STATES: tuple[str, ...] = ("implementado", "parcial", "proyectado")


@dataclass
class CaseMetadata:
    """Metadatos de un caso, ya validados."""

    path: Path
    data: dict[str, Any]
    issues: list[str] = field(default_factory=list)

    @property
    def slug(self) -> str:
        return str(self.data.get("slug", self.path.name))

    @property
    def ok(self) -> bool:
        return not self.issues

    def get(self, key: str, default: Any = "") -> Any:
        return self.data.get(key, default)

    def as_row(self) -> dict[str, Any]:
        competencias = self.get("competencias", [])
        return {
            "caso": self.slug,
            "titulo": self.get("titulo"),
            "disciplina": self.get("disciplina"),
            "industria": self.get("industria"),
            "dificultad": self.get("dificultad"),
            "estado": self.get("estado"),
            "tiempo_min": self.get("tiempo_sugerido_min"),
            "competencias": ", ".join(competencias) if isinstance(competencias, list) else competencias,
            "metadatos_completos": "sí" if self.ok else "no",
        }


def validate_metadata(data: dict[str, Any], path: Path) -> list[str]:
    """Devuelve la lista de problemas de un diccionario de metadatos.

    Una lista vacía significa que el caso declara todo lo que el laboratorio exige.
    """
    issues: list[str] = []
    for field_name in REQUIRED_FIELDS:
        if field_name not in data:
            issues.append(f"falta el campo obligatorio '{field_name}'")
            continue
        value = data[field_name]
        if value is None or (isinstance(value, (str, list, dict)) and len(value) == 0):
            issues.append(f"el campo '{field_name}' está vacío")

    if data.get("dificultad") not in DIFFICULTIES and "dificultad" in data:
        issues.append(f"dificultad '{data.get('dificultad')}' fuera de {DIFFICULTIES}")
    if data.get("estado") not in STATES and "estado" in data:
        issues.append(f"estado '{data.get('estado')}' fuera de {STATES}")

    competencias = data.get("competencias")
    if competencias is not None and not isinstance(competencias, list):
        issues.append("'competencias' debe ser una lista")

    tiempo = data.get("tiempo_sugerido_min")
    if tiempo is not None and (not isinstance(tiempo, int) or tiempo <= 0):
        issues.append("'tiempo_sugerido_min' debe ser un entero de minutos mayor que cero")

    slug = data.get("slug")
    if slug and slug != path.parent.name:
        issues.append(f"el slug '{slug}' no coincide con la carpeta '{path.parent.name}'")

    return issues


def load_case(metadata_path: str | Path) -> CaseMetadata:
    """Carga y valida los metadatos de un caso.

    Raises:
        FileNotFoundError: si el archivo no existe.
        ValueError: si el JSON está mal formado. Un `case.json` ilegible es un error
            del repositorio, no un caso incompleto.
    """
    path = Path(metadata_path)
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} no es JSON válido: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path} debe contener un objeto JSON en su raíz.")
    return CaseMetadata(path=path, data=data, issues=validate_metadata(data, path))


def discover_cases(root: str | Path = ROOT) -> list[CaseMetadata]:
    """Encuentra todos los casos con metadatos bajo `cases/`, ordenados por slug."""
    base = Path(root) / "cases"
    if not base.exists():
        return []
    found = [load_case(p) for p in sorted(base.glob(f"*/{METADATA_FILE}"))]
    return sorted(found, key=lambda c: c.slug)


def catalog_frame(cases: Iterable[CaseMetadata]) -> pd.DataFrame:
    """Catálogo como tabla, apto para exportar o filtrar."""
    rows = [c.as_row() for c in cases]
    columns = ["caso", "titulo", "disciplina", "industria", "dificultad", "estado",
               "tiempo_min", "competencias", "metadatos_completos"]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows, columns=columns)


def catalog_markdown(cases: Iterable[CaseMetadata]) -> str:
    """Catálogo navegable en Markdown, con enlaces relativos a cada caso."""
    cases = list(cases)
    lines = [
        "| Caso | Título | Disciplina | Industria | Dificultad | Estado | Tiempo | Metadatos |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case in cases:
        row = case.as_row()
        link = f"[`{row['caso']}`](../cases/{row['caso']}/README.md)"
        lines.append(
            f"| {link} | {row['titulo']} | {row['disciplina']} | {row['industria']} | "
            f"{row['dificultad']} | {row['estado']} | {row['tiempo_min']} min | "
            f"{row['metadatos_completos']} |"
        )
    if not cases:
        lines.append("| — | Sin casos registrados | — | — | — | — | — | — |")
    return "\n".join(lines) + "\n"


def competency_matrix(cases: Iterable[CaseMetadata]) -> pd.DataFrame:
    """Matriz competencia × caso, para ver qué queda sin cubrir.

    Returns:
        Tabla con una fila por competencia y columnas `casos` y `cantidad`.
    """
    counter: dict[str, list[str]] = {}
    for case in cases:
        competencias = case.get("competencias", [])
        if not isinstance(competencias, list):
            continue
        for competencia in competencias:
            counter.setdefault(str(competencia), []).append(case.slug)
    rows = [
        {"competencia": name, "casos": ", ".join(sorted(slugs)), "cantidad": len(slugs)}
        for name, slugs in sorted(counter.items())
    ]
    if not rows:
        return pd.DataFrame(columns=["competencia", "casos", "cantidad"])
    return pd.DataFrame(rows).sort_values(["cantidad", "competencia"], ascending=[False, True])
