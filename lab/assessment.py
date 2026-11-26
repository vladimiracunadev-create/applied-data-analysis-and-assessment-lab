"""Motor genérico de evaluaciones técnicas: configurar, generar, cronometrar, corregir.

Qué hace
    Permite describir una evaluación (cargo, especialidad, industria, herramientas,
    competencias, dificultad, tiempo, entregables y criterios), generar una instancia
    reproducible a partir de un banco de ítems y una semilla, y corregirla con una
    rúbrica ponderada.

Por qué existe
    La preparación para una evaluación técnica suele consistir en ejercicios sueltos.
    Una evaluación real tiene restricciones de tiempo, cobertura de competencias y
    criterios de corrección. Modelarlas permite repetir la práctica con variantes
    equivalentes en dificultad y comparar resultados entre intentos.

Diferencia entre simulación y evaluación oficial
    Este módulo produce **simulaciones de entrenamiento**. Ninguna instancia generada
    aquí es una prueba oficial de ninguna institución, y cada instancia lo declara en
    su encabezado.

Cómo se valida
    `tests/test_assessment.py` comprueba la reproducibilidad por semilla, el respeto
    del presupuesto de tiempo, la cobertura obligatoria de competencias, el rechazo
    de rúbricas que no suman 100 y el cálculo de la nota.
"""

from __future__ import annotations

import json
import random
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ITEM_BANK_DIR = ROOT / "assessments" / "items"

DIFFICULTIES: tuple[str, ...] = ("introductorio", "intermedio", "avanzado", "especializado")

#: Peso relativo de cada nivel, usado para comprobar que una instancia tiene el
#: nivel declarado y no una mezcla arbitraria.
DIFFICULTY_WEIGHT: dict[str, int] = {
    "introductorio": 1, "intermedio": 2, "avanzado": 3, "especializado": 4,
}


@dataclass(frozen=True)
class Item:
    """Un ítem del banco de ejercicios.

    Args:
        id: identificador estable.
        enunciado: lo que se pide, en una o varias frases.
        competencias: competencias que el ítem evalúa.
        herramientas: herramientas admitidas para resolverlo.
        dificultad: nivel del ítem.
        minutos: tiempo estimado de resolución.
        entregable: qué debe entregar la persona.
        criterios: qué se corrige, en forma de lista verificable.
        datos: ruta relativa del dataset asociado, si aplica.
        trampas: errores que el ítem busca detectar de forma deliberada.
    """

    id: str
    enunciado: str
    competencias: tuple[str, ...]
    herramientas: tuple[str, ...]
    dificultad: str
    minutos: int
    entregable: str
    criterios: tuple[str, ...]
    datos: str = ""
    trampas: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.dificultad not in DIFFICULTIES:
            raise ValueError(f"Dificultad inválida en {self.id!r}: {self.dificultad!r}.")
        if self.minutos <= 0:
            raise ValueError(f"El ítem {self.id!r} debe declarar minutos positivos.")
        if not self.competencias:
            raise ValueError(f"El ítem {self.id!r} no declara competencias.")
        if not self.criterios:
            raise ValueError(f"El ítem {self.id!r} no declara criterios de corrección.")


@dataclass(frozen=True)
class RubricCriterion:
    """Un criterio de la rúbrica, con su peso y sus niveles de logro."""

    nombre: str
    puntos: int
    descripcion: str
    niveles: tuple[tuple[str, float], ...] = (
        ("logrado", 1.0), ("parcial", 0.5), ("no_logrado", 0.0),
    )

    def nivel(self, nombre: str) -> float:
        for label, factor in self.niveles:
            if label == nombre:
                return factor
        raise KeyError(f"Nivel {nombre!r} no definido en el criterio {self.nombre!r}.")


@dataclass(frozen=True)
class Rubric:
    """Rúbrica de corrección. Los puntos de los criterios deben sumar 100."""

    criterios: tuple[RubricCriterion, ...]

    def __post_init__(self) -> None:
        if not self.criterios:
            raise ValueError("Una rúbrica necesita al menos un criterio.")
        total = sum(c.puntos for c in self.criterios)
        if total != 100:
            raise ValueError(f"Los criterios suman {total} puntos; deben sumar 100.")
        names = [c.nombre for c in self.criterios]
        if len(set(names)) != len(names):
            raise ValueError(f"Criterios repetidos en la rúbrica: {names}.")

    def score(self, levels: dict[str, str]) -> float:
        """Nota de 0 a 100 a partir del nivel alcanzado en cada criterio.

        Raises:
            ValueError: si falta algún criterio. Corregir con criterios sin evaluar
                produce una nota que no significa nada.
        """
        missing = [c.nombre for c in self.criterios if c.nombre not in levels]
        if missing:
            raise ValueError(f"Faltan criterios por evaluar: {missing}.")
        return round(sum(c.puntos * c.nivel(levels[c.nombre]) for c in self.criterios), 2)

    def to_markdown(self) -> str:
        lines = ["| Criterio | Puntos | Qué se evalúa |", "| --- | --- | --- |"]
        for c in self.criterios:
            lines.append(f"| {c.nombre} | {c.puntos} | {c.descripcion} |")
        lines.append("| **Total** | **100** | |")
        return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class Blueprint:
    """Configuración de una evaluación.

    Args:
        nombre: nombre de la simulación.
        cargo: cargo o rol al que apunta.
        especialidad: especialidad técnica.
        industria: sector de aplicación.
        herramientas: herramientas admitidas.
        competencias_obligatorias: competencias que la instancia debe cubrir sí o sí.
        dificultad: nivel objetivo.
        minutos: presupuesto total de tiempo.
        entregables: lista de entregables exigidos.
        rubrica: rúbrica de corrección.
        permite_ia: si la evaluación simulada admite asistentes de IA. Se declara
            de forma explícita porque cada proceso de selección fija su propia regla
            y el laboratorio no la decide por nadie.
    """

    nombre: str
    cargo: str
    especialidad: str
    industria: str
    herramientas: tuple[str, ...]
    competencias_obligatorias: tuple[str, ...]
    dificultad: str
    minutos: int
    entregables: tuple[str, ...]
    rubrica: Rubric
    permite_ia: bool = False

    def __post_init__(self) -> None:
        if self.dificultad not in DIFFICULTIES:
            raise ValueError(f"Dificultad inválida: {self.dificultad!r}.")
        if self.minutos <= 0:
            raise ValueError("El presupuesto de minutos debe ser positivo.")
        if not self.competencias_obligatorias:
            raise ValueError("Declare al menos una competencia obligatoria.")
        if not self.entregables:
            raise ValueError("Declare al menos un entregable.")


@dataclass
class Assessment:
    """Instancia generada de una evaluación."""

    blueprint: Blueprint
    items: tuple[Item, ...]
    seed: int
    uncovered: tuple[str, ...] = field(default_factory=tuple)

    @property
    def minutos(self) -> int:
        return sum(i.minutos for i in self.items)

    @property
    def nivel_promedio(self) -> float:
        if not self.items:
            return float("nan")
        return sum(DIFFICULTY_WEIGHT[i.dificultad] for i in self.items) / len(self.items)

    def competencias(self) -> tuple[str, ...]:
        return tuple(sorted({c for i in self.items for c in i.competencias}))

    def to_frame(self) -> pd.DataFrame:
        rows = [
            {
                "item": i.id,
                "dificultad": i.dificultad,
                "minutos": i.minutos,
                "competencias": ", ".join(i.competencias),
                "herramientas": ", ".join(i.herramientas),
                "entregable": i.entregable,
            }
            for i in self.items
        ]
        columns = ["item", "dificultad", "minutos", "competencias", "herramientas", "entregable"]
        return pd.DataFrame(rows, columns=columns)

    def to_markdown(self) -> str:
        """Enunciado completo de la simulación, apto para entregar a quien practica."""
        bp = self.blueprint
        lines = [
            f"# {bp.nombre}",
            "",
            "> **Simulación de entrenamiento.** No es una prueba oficial de ninguna "
            "institución ni reproduce instrumentos reales de selección.",
            "",
            f"- Cargo de referencia: {bp.cargo}",
            f"- Especialidad: {bp.especialidad} · Industria: {bp.industria}",
            f"- Nivel declarado: {bp.dificultad}",
            f"- Tiempo: {self.minutos} de {bp.minutos} minutos presupuestados",
            f"- Herramientas admitidas: {', '.join(bp.herramientas)}",
            f"- Uso de asistentes de IA: {'permitido' if bp.permite_ia else 'no permitido'}",
            f"- Semilla de generación: {self.seed} (reproducible)",
            "",
            "## Entregables",
            "",
        ]
        lines += [f"{n}. {e}" for n, e in enumerate(bp.entregables, start=1)]
        lines += ["", "## Ítems", ""]
        for position, item in enumerate(self.items, start=1):
            lines += [
                f"### Ítem {position} · {item.id} ({item.minutos} min, {item.dificultad})",
                "",
                item.enunciado,
                "",
                f"- Entregable: {item.entregable}",
                f"- Competencias: {', '.join(item.competencias)}",
            ]
            if item.datos:
                lines.append(f"- Datos: `{item.datos}`")
            lines += ["- Se corrige:"]
            lines += [f"  - {c}" for c in item.criterios]
            lines.append("")
        lines += ["## Rúbrica", "", self.blueprint.rubrica.to_markdown()]
        if self.uncovered:
            lines += [
                "## Cobertura declarada",
                "",
                "Competencias obligatorias que el banco de ítems todavía no cubre: "
                + ", ".join(self.uncovered)
                + ". Se informan aquí en lugar de ocultarse.",
                "",
            ]
        return "\n".join(lines)


# ----------------------------------------------------------------------- banco de ítems
def load_items(directory: str | Path = ITEM_BANK_DIR) -> list[Item]:
    """Carga el banco de ítems desde archivos JSON.

    Cada archivo contiene una lista de objetos. Los identificadores repetidos son un
    error: impiden saber qué ítem se respondió.
    """
    path = Path(directory)
    items: list[Item] = []
    seen: set[str] = set()
    if not path.exists():
        return items
    for file_path in sorted(path.glob("*.json")):
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"{file_path} debe contener una lista de ítems.")
        for raw in payload:
            item = Item(
                id=raw["id"],
                enunciado=raw["enunciado"],
                competencias=tuple(raw["competencias"]),
                herramientas=tuple(raw["herramientas"]),
                dificultad=raw["dificultad"],
                minutos=int(raw["minutos"]),
                entregable=raw["entregable"],
                criterios=tuple(raw["criterios"]),
                datos=raw.get("datos", ""),
                trampas=tuple(raw.get("trampas", [])),
            )
            if item.id in seen:
                raise ValueError(f"Ítem repetido en el banco: {item.id!r}")
            seen.add(item.id)
            items.append(item)
    return items


def generate(
    blueprint: Blueprint,
    bank: Sequence[Item],
    seed: int = 0,
    tolerance_pct: float = 10.0,
) -> Assessment:
    """Genera una instancia reproducible de la evaluación.

    Algoritmo, en dos fases y determinista para una semilla dada:

    1. **Cobertura**: para cada competencia obligatoria se elige un ítem compatible
       (dificultad igual o inferior a la declarada, herramientas dentro de las
       admitidas) que quepa en el tiempo restante.
    2. **Relleno**: se agregan ítems compatibles hasta acercarse al presupuesto de
       tiempo sin excederlo más allá de `tolerance_pct`.

    Args:
        blueprint: configuración de la evaluación.
        bank: banco de ítems disponible.
        seed: semilla; la misma semilla y el mismo banco producen la misma instancia.
        tolerance_pct: cuánto puede exceder el tiempo total al presupuesto.

    Returns:
        La instancia generada, incluida la lista de competencias obligatorias que el
        banco no pudo cubrir.

    Raises:
        ValueError: si el banco está vacío o no hay ningún ítem compatible.
    """
    if not bank:
        raise ValueError("El banco de ítems está vacío.")
    max_weight = DIFFICULTY_WEIGHT[blueprint.dificultad]
    allowed = set(blueprint.herramientas)
    compatible = [
        i for i in bank
        if DIFFICULTY_WEIGHT[i.dificultad] <= max_weight
        and (not allowed or set(i.herramientas) & allowed)
    ]
    if not compatible:
        raise ValueError(
            "Ningún ítem del banco es compatible con el nivel y las herramientas declaradas."
        )

    rng = random.Random(seed)
    budget = blueprint.minutos * (1 + tolerance_pct / 100.0)
    chosen: list[Item] = []
    used: set[str] = set()
    uncovered: list[str] = []

    def fits(item: Item) -> bool:
        return sum(i.minutos for i in chosen) + item.minutos <= budget

    for competency in blueprint.competencias_obligatorias:
        candidates = sorted(
            (i for i in compatible if competency in i.competencias and i.id not in used and fits(i)),
            key=lambda i: i.id,
        )
        if not candidates:
            uncovered.append(competency)
            continue
        pick = rng.choice(candidates)
        chosen.append(pick)
        used.add(pick.id)

    remaining = sorted((i for i in compatible if i.id not in used), key=lambda i: i.id)
    rng.shuffle(remaining)
    for item in remaining:
        if fits(item):
            chosen.append(item)
            used.add(item.id)

    chosen.sort(key=lambda i: (DIFFICULTY_WEIGHT[i.dificultad], i.id))
    return Assessment(blueprint=blueprint, items=tuple(chosen), seed=seed,
                      uncovered=tuple(uncovered))


def progress_frame(attempts: Iterable[dict[str, Any]]) -> pd.DataFrame:
    """Seguimiento del aprendizaje a partir de intentos registrados.

    Args:
        attempts: cada intento como `{"fecha": ..., "simulacion": ..., "nota": ...,
            "minutos": ..., "criterios": {nombre: nivel}}`.

    Returns:
        Tabla con una fila por intento y la variación de nota respecto del anterior,
        que es la información útil: la tendencia, no la nota aislada.
    """
    rows = list(attempts)
    columns = ["fecha", "simulacion", "nota", "minutos", "variacion"]
    if not rows:
        return pd.DataFrame(columns=columns)
    frame = pd.DataFrame(rows)
    for column in ("fecha", "simulacion", "nota", "minutos"):
        if column not in frame:
            raise KeyError(f"Falta la columna {column!r} en el registro de intentos.")
    frame = frame.sort_values("fecha").reset_index(drop=True)
    frame["variacion"] = frame["nota"].diff()
    return frame[columns]
