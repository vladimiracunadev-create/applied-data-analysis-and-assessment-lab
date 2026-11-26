"""Informes con las secciones que el método exige, y nada declarado sin respaldo.

Qué hace
    Construye informes de caso y de investigación en Markdown a partir de secciones
    nombradas, validando que estén todas las obligatorias antes de permitir la
    exportación. Incluye utilidades para insertar tablas y para separar
    explícitamente hechos, inferencias e hipótesis.

Por qué existe
    Un informe al que le falta la sección de limitaciones o la de supuestos induce a
    conclusiones más fuertes de lo que los datos permiten. Que el validador se niegue
    a exportar un informe incompleto es parte del control de calidad.

Cómo se valida
    `tests/test_report.py` comprueba el rechazo de informes incompletos, el orden de
    las secciones, la clasificación de afirmaciones y la conversión de tablas.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Literal

import pandas as pd

#: Secciones obligatorias de un informe de caso aplicado.
CASE_SECTIONS: tuple[str, ...] = (
    "contexto", "problema", "objetivos", "datos", "metodologia", "supuestos",
    "resultados", "validacion", "interpretacion", "limitaciones", "conclusiones",
    "reproducibilidad",
)

#: Secciones obligatorias de un informe de investigación.
RESEARCH_SECTIONS: tuple[str, ...] = (
    "problema", "preguntas", "objetivos", "hipotesis", "revision_bibliografica",
    "fuentes", "poblacion_muestra", "variables", "calidad_datos", "metodologia",
    "experimentacion", "analisis", "resultados", "validacion", "incertidumbre",
    "sesgos", "limitaciones", "conclusiones", "recomendaciones", "reproducibilidad",
)

ClaimKind = Literal["hecho", "evidencia", "hipotesis", "inferencia", "interpretacion"]

#: Cómo se debe leer cada tipo de afirmación. Se imprime en el informe.
CLAIM_LEGEND: dict[ClaimKind, str] = {
    "hecho": "Verificable directamente en los datos entregados.",
    "evidencia": "Resultado de un cálculo sobre los datos, con método declarado.",
    "hipotesis": "Explicación posible, todavía no contrastada.",
    "inferencia": "Conclusión derivada de la evidencia, con el supuesto que la sostiene.",
    "interpretacion": "Lectura del resultado en el dominio del problema.",
}

#: Títulos legibles de las secciones.
TITLES: dict[str, str] = {
    "contexto": "Contexto",
    "problema": "Definición del problema",
    "preguntas": "Preguntas de investigación",
    "objetivos": "Objetivos",
    "hipotesis": "Hipótesis",
    "revision_bibliografica": "Revisión bibliográfica",
    "restricciones": "Restricciones",
    "fuentes": "Fuentes",
    "datos": "Datos y diccionario",
    "poblacion_muestra": "Población y muestra",
    "variables": "Variables e instrumentos",
    "calidad_datos": "Calidad de los datos",
    "metodologia": "Metodología",
    "experimentacion": "Experimentación",
    "analisis": "Análisis",
    "supuestos": "Supuestos",
    "resultados": "Resultados",
    "validacion": "Validación independiente",
    "incertidumbre": "Incertidumbre",
    "sesgos": "Sesgos",
    "interpretacion": "Interpretación",
    "limitaciones": "Limitaciones",
    "conclusiones": "Conclusiones",
    "recomendaciones": "Recomendaciones",
    "reproducibilidad": "Reproducibilidad",
}


@dataclass(frozen=True)
class Claim:
    """Una afirmación del informe, con su tipo y su respaldo."""

    kind: ClaimKind
    text: str
    support: str

    def __post_init__(self) -> None:
        if self.kind not in CLAIM_LEGEND:
            raise ValueError(f"Tipo de afirmación inválido: {self.kind!r}.")
        if not self.support.strip():
            raise ValueError(
                f"La afirmación {self.text!r} no declara respaldo. Toda afirmación del "
                "informe debe indicar de dónde sale."
            )


def table_markdown(frame: pd.DataFrame, max_rows: int = 30, floatfmt: str = "{:,.2f}") -> str:
    """Convierte un DataFrame en tabla Markdown, truncando con aviso explícito."""
    if frame.empty:
        return "_Sin filas._\n"
    shown = frame.head(max_rows).copy()
    for column in shown.columns:
        if pd.api.types.is_float_dtype(shown[column]):
            shown[column] = shown[column].map(
                lambda v: "" if pd.isna(v) else floatfmt.format(v)
            )
        else:
            shown[column] = shown[column].astype("string").fillna("")
    header = "| " + " | ".join(str(c) for c in shown.columns) + " |"
    divider = "| " + " | ".join("---" for _ in shown.columns) + " |"
    rows = ["| " + " | ".join(row) + " |" for row in shown.astype(str).to_numpy()]
    out = [header, divider, *rows]
    if len(frame) > max_rows:
        out.append("")
        out.append(f"_Se muestran {max_rows} de {len(frame)} filas._")
    return "\n".join(out) + "\n"


@dataclass
class Report:
    """Informe con secciones nombradas y validación de completitud.

    Args:
        title: título del informe.
        required: secciones obligatorias; use `CASE_SECTIONS` o `RESEARCH_SECTIONS`.
        author: autoría.
        report_date: fecha del informe.
        disclaimer: advertencia que encabeza el documento.
    """

    title: str
    required: tuple[str, ...] = CASE_SECTIONS
    author: str = ""
    report_date: date | None = None
    disclaimer: str = ""
    sections: dict[str, str] = field(default_factory=dict)
    claims: list[Claim] = field(default_factory=list)

    def add(self, section: str, body: str) -> Report:
        """Agrega o reemplaza el contenido de una sección. Devuelve `self` para encadenar."""
        if not body.strip():
            raise ValueError(f"La sección {section!r} no puede quedar vacía.")
        self.sections[section] = body.strip()
        return self

    def add_table(self, section: str, frame: pd.DataFrame, intro: str = "") -> Report:
        """Agrega una sección cuyo contenido es una tabla, con introducción opcional."""
        body = f"{intro.strip()}\n\n{table_markdown(frame)}" if intro else table_markdown(frame)
        return self.add(section, body)

    def claim(self, kind: ClaimKind, text: str, support: str) -> Report:
        """Registra una afirmación clasificada."""
        self.claims.append(Claim(kind, text, support))
        return self

    def missing(self) -> list[str]:
        """Secciones obligatorias todavía sin contenido, en el orden declarado."""
        return [s for s in self.required if s not in self.sections]

    def to_markdown(self, allow_incomplete: bool = False) -> str:
        """Renderiza el informe.

        Args:
            allow_incomplete: si es False (por defecto) y faltan secciones
                obligatorias, se levanta un error en lugar de producir un informe
                que parece completo.

        Raises:
            ValueError: si faltan secciones obligatorias.
        """
        pending = self.missing()
        if pending and not allow_incomplete:
            raise ValueError(
                f"El informe {self.title!r} no está completo. Faltan: {', '.join(pending)}."
            )
        lines = [f"# {self.title}", ""]
        meta = []
        if self.author:
            meta.append(f"Autoría: {self.author}")
        if self.report_date:
            meta.append(f"Fecha: {self.report_date.isoformat()}")
        if meta:
            lines += ["· ".join(meta), ""]
        if self.disclaimer:
            lines += [f"> {self.disclaimer}", ""]
        if pending:
            lines += [
                "> **Informe incompleto.** Secciones obligatorias sin redactar: "
                + ", ".join(pending)
                + ".",
                "",
            ]
        order = list(self.required) + [s for s in self.sections if s not in self.required]
        for section in order:
            if section not in self.sections:
                continue
            lines += [f"## {TITLES.get(section, section.replace('_', ' ').capitalize())}", "",
                      self.sections[section], ""]
        if self.claims:
            lines += ["## Clasificación de afirmaciones", "",
                      "| Tipo | Afirmación | Respaldo |", "| --- | --- | --- |"]
            for claim in self.claims:
                lines.append(f"| {claim.kind} | {claim.text} | {claim.support} |")
            lines += ["", "Cómo leer esta tabla:", ""]
            used = {c.kind for c in self.claims}
            lines += [f"- **{kind}**: {CLAIM_LEGEND[kind]}" for kind in CLAIM_LEGEND if kind in used]
            lines.append("")
        return "\n".join(lines)

    def write(self, path: str | Path, allow_incomplete: bool = False) -> Path:
        """Escribe el informe en disco creando los directorios necesarios."""
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.to_markdown(allow_incomplete=allow_incomplete),
                               encoding="utf-8")
        return destination


def case_report(title: str, **kwargs) -> Report:
    """Informe de caso aplicado con las secciones obligatorias ya configuradas."""
    return Report(title=title, required=CASE_SECTIONS, **kwargs)


def research_report(title: str, **kwargs) -> Report:
    """Informe de investigación con las secciones obligatorias ya configuradas."""
    return Report(title=title, required=RESEARCH_SECTIONS, **kwargs)


def checklist(required: Sequence[str], present: Sequence[str]) -> pd.DataFrame:
    """Lista de verificación de secciones, para adjuntar al entregable."""
    return pd.DataFrame(
        [{"seccion": TITLES.get(s, s), "clave": s, "presente": "sí" if s in present else "no"}
         for s in required]
    )
