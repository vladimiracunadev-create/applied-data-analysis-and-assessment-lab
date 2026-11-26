"""Metodología universal de resolución de problemas: 18 etapas ejecutables y auditables.

Qué hace
    Convierte la metodología del laboratorio en un objeto de seguimiento (`MethodRun`)
    que registra, por cada etapa, su estado, la evidencia producida y las decisiones
    tomadas. El resultado se exporta a Markdown o a un diccionario serializable.

Por qué existe
    Una metodología escrita en un documento no se puede auditar ni probar. Representada
    como datos, se puede validar (¿quedaron etapas sin evidencia?), comparar entre casos
    y exigir en las pruebas automáticas.

Cómo se valida
    `tests/test_method.py` comprueba el orden de las etapas, el rechazo de etapas
    desconocidas, el cálculo de cobertura y la exportación.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

Status = Literal["pendiente", "en_curso", "completada", "no_aplica"]

VALID_STATUS: tuple[Status, ...] = ("pendiente", "en_curso", "completada", "no_aplica")


@dataclass(frozen=True)
class Stage:
    """Una etapa de la metodología.

    Attributes:
        number: posición en la secuencia (1..18).
        key: identificador estable, en minúsculas y sin espacios.
        name: nombre legible en español.
        question: pregunta que la etapa debe responder.
        output: entregable mínimo esperado para considerarla completada.
    """

    number: int
    key: str
    name: str
    question: str
    output: str


#: Secuencia canónica de la metodología. El orden es parte del contrato público.
STAGES: tuple[Stage, ...] = (
    Stage(1, "recepcion", "Recepción y comprensión del problema",
          "¿Qué se está pidiendo exactamente y con qué palabras lo pide quien consulta?",
          "Enunciado reformulado y lista de ambigüedades detectadas."),
    Stage(2, "contexto", "Identificación del contexto",
          "¿En qué dominio, organización, marco legal y momento ocurre el problema?",
          "Descripción del contexto y de los actores afectados."),
    Stage(3, "objetivos", "Determinación de objetivos y restricciones",
          "¿Qué resultado se busca, con qué límites de tiempo, datos, herramientas y ética?",
          "Objetivo general, objetivos específicos y restricciones explícitas."),
    Stage(4, "descomposicion", "Descomposición del problema",
          "¿En qué subproblemas independientes se puede partir?",
          "Árbol de subproblemas con dependencias."),
    Stage(5, "conocimiento_necesario", "Identificación del conocimiento necesario",
          "¿Qué hay que saber para resolverlo y qué parte de eso aún no se sabe?",
          "Lista de conocimientos requeridos, disponibles y faltantes."),
    Stage(6, "antecedentes", "Investigación de antecedentes",
          "¿Quién resolvió algo parecido y con qué resultado?",
          "Revisión de antecedentes con referencias verificables."),
    Stage(7, "fuentes_herramientas", "Selección de fuentes y herramientas",
          "¿Qué fuentes y tecnologías son apropiadas y por qué, frente a qué alternativas?",
          "Decisión justificada con alternativas descartadas."),
    Stage(8, "datos", "Adquisición y preparación de datos",
          "¿De dónde vienen los datos, con qué licencia y en qué estado llegan?",
          "Datos crudos inmutables, diccionario, contrato e informe de calidad."),
    Stage(9, "alternativas", "Diseño de alternativas",
          "¿Qué caminos de solución existen y cómo se comparan?",
          "Dos o más alternativas con criterios de comparación."),
    Stage(10, "experimentacion", "Experimentación",
          "¿Qué se prueba, con qué parámetros y qué se mide?",
          "Diseño experimental reproducible y registro de corridas."),
    Stage(11, "implementacion", "Implementación de soluciones",
          "¿Cómo queda construida la solución elegida?",
          "Código ejecutable, documentado y versionado."),
    Stage(12, "medicion", "Medición y evaluación",
          "¿Qué métricas describen el desempeño de la solución?",
          "Indicadores calculados con denominadores explícitos."),
    Stage(13, "validacion_independiente", "Validación independiente",
          "¿Un método distinto produce el mismo resultado?",
          "Comprobación cruzada con herramienta o implementación alternativa."),
    Stage(14, "interpretacion", "Interpretación de resultados",
          "¿Qué significan los números en el dominio del problema?",
          "Interpretación que separa hecho, inferencia e hipótesis."),
    Stage(15, "comunicacion", "Comunicación de conclusiones",
          "¿Cómo se explica a quien debe decidir?",
          "Informe o visualización con unidades, período y fuente."),
    Stage(16, "limitaciones", "Identificación de limitaciones",
          "¿Qué no permite concluir este trabajo?",
          "Limitaciones, sesgos e incertidumbre declarados."),
    Stage(17, "conocimiento_reutilizable", "Generación de conocimiento reutilizable",
          "¿Qué quedó aprendido y en qué forma se puede volver a usar?",
          "Registro en la base de conocimiento con patrón y lecciones."),
    Stage(18, "incorporacion", "Incorporación de capacidades al laboratorio",
          "¿Qué del núcleo, pruebas o documentación cambió gracias a este problema?",
          "Cambios integrados al repositorio y pruebas que los protegen."),
)

STAGE_BY_KEY: dict[str, Stage] = {s.key: s for s in STAGES}


@dataclass
class StageRecord:
    """Estado de una etapa dentro de una corrida concreta."""

    stage: Stage
    status: Status = "pendiente"
    evidence: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class MethodRun:
    """Aplicación de la metodología a un problema concreto.

    Args:
        problem: enunciado del problema en una línea.
        owner: persona o equipo responsable.
        started: fecha de inicio.
        stages: subconjunto de etapas a seguir; por defecto las 18.

    Example:
        >>> run = MethodRun(problem="Medir cumplimiento de programación")
        >>> _ = run.complete("recepcion", evidence="docs/enunciado.md")
        >>> run.coverage()
        0.05555555555555555
    """

    problem: str
    owner: str = ""
    started: date | None = None
    stages: Iterable[Stage] = STAGES
    records: dict[str, StageRecord] = field(init=False)

    def __post_init__(self) -> None:
        self.records = {s.key: StageRecord(stage=s) for s in self.stages}
        if not self.records:
            raise ValueError("Una corrida necesita al menos una etapa.")

    # ------------------------------------------------------------------ escritura
    def _record(self, key: str) -> StageRecord:
        try:
            return self.records[key]
        except KeyError as exc:  # pragma: no cover - mensaje de error explícito
            raise KeyError(
                f"Etapa desconocida: {key!r}. Etapas válidas: {sorted(self.records)}"
            ) from exc

    def set_status(self, key: str, status: Status) -> StageRecord:
        """Cambia el estado de una etapa. Rechaza estados fuera del vocabulario."""
        if status not in VALID_STATUS:
            raise ValueError(f"Estado inválido: {status!r}. Use uno de {VALID_STATUS}.")
        record = self._record(key)
        record.status = status
        return record

    def complete(
        self,
        key: str,
        evidence: str | Iterable[str] = (),
        decisions: str | Iterable[str] = (),
        notes: str = "",
    ) -> StageRecord:
        """Marca una etapa como completada exigiendo al menos una evidencia.

        Raises:
            ValueError: si no se entrega evidencia. Una etapa sin evidencia no es
                una etapa completada; el laboratorio no acepta avances declarativos.
        """
        items = [evidence] if isinstance(evidence, str) else list(evidence)
        items = [i for i in items if i]
        if not items:
            raise ValueError(
                f"La etapa {key!r} no puede completarse sin evidencia verificable."
            )
        record = self._record(key)
        record.status = "completada"
        record.evidence.extend(items)
        record.decisions.extend([decisions] if isinstance(decisions, str) else list(decisions))
        record.decisions = [d for d in record.decisions if d]
        if notes:
            record.notes = notes
        return record

    def skip(self, key: str, reason: str) -> StageRecord:
        """Declara una etapa como no aplicable, con motivo obligatorio."""
        if not reason.strip():
            raise ValueError("Declarar una etapa como no aplicable exige un motivo.")
        record = self._record(key)
        record.status = "no_aplica"
        record.notes = reason
        return record

    # -------------------------------------------------------------------- lectura
    def coverage(self) -> float:
        """Proporción de etapas completadas sobre las aplicables (0.0 a 1.0)."""
        applicable = [r for r in self.records.values() if r.status != "no_aplica"]
        if not applicable:
            return 1.0
        done = sum(1 for r in applicable if r.status == "completada")
        return done / len(applicable)

    def pending(self) -> list[Stage]:
        """Etapas que todavía no están completadas ni descartadas, en orden."""
        return [
            r.stage
            for r in sorted(self.records.values(), key=lambda r: r.stage.number)
            if r.status in ("pendiente", "en_curso")
        ]

    def to_dict(self) -> dict:
        """Representación serializable (JSON) de la corrida."""
        return {
            "problem": self.problem,
            "owner": self.owner,
            "started": self.started.isoformat() if self.started else None,
            "coverage": round(self.coverage(), 4),
            "stages": [
                {
                    "number": r.stage.number,
                    "key": r.stage.key,
                    "name": r.stage.name,
                    "status": r.status,
                    "evidence": list(r.evidence),
                    "decisions": list(r.decisions),
                    "notes": r.notes,
                }
                for r in sorted(self.records.values(), key=lambda r: r.stage.number)
            ],
        }

    def to_markdown(self) -> str:
        """Informe de seguimiento en Markdown, apto para adjuntar a un caso."""
        lines = [
            f"# Seguimiento metodológico — {self.problem}",
            "",
            f"- Responsable: {self.owner or 'sin asignar'}",
            f"- Inicio: {self.started.isoformat() if self.started else 'sin fecha'}",
            f"- Cobertura: {self.coverage() * 100:.1f} % de las etapas aplicables",
            "",
            "| # | Etapa | Estado | Evidencia |",
            "| --- | --- | --- | --- |",
        ]
        for record in sorted(self.records.values(), key=lambda r: r.stage.number):
            evidence = "; ".join(record.evidence) if record.evidence else "—"
            lines.append(
                f"| {record.stage.number} | {record.stage.name} | {record.status} | {evidence} |"
            )
        pending = self.pending()
        lines += ["", "## Pendientes", ""]
        lines += [f"- {s.number}. {s.name} — {s.output}" for s in pending] or ["- Ninguna."]
        return "\n".join(lines) + "\n"


def stages_markdown() -> str:
    """Tabla de referencia de las 18 etapas, usada para generar documentación."""
    lines = [
        "| # | Etapa | Pregunta que responde | Entregable mínimo |",
        "| --- | --- | --- | --- |",
    ]
    for s in STAGES:
        lines.append(f"| {s.number} | {s.name} | {s.question} | {s.output} |")
    return "\n".join(lines) + "\n"
