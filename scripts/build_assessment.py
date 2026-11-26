"""Genera una simulación de evaluación técnica reproducible.

Qué hace
    Combina una configuración de `assessments/blueprints.py` con el banco de ítems de
    `assessments/items/` y escribe el enunciado completo en Markdown, con rúbrica,
    entregables y la semilla que permite volver a generar exactamente la misma
    simulación.

Por qué la semilla importa
    Dos personas que practican con la misma semilla resuelven la misma prueba y
    pueden comparar resultados. Con semillas distintas obtienen variantes del mismo
    nivel. Sin semilla, nada de eso es posible.

Uso
    python scripts/build_assessment.py --blueprint gestor-datos-transporte --seed 1
    python scripts/build_assessment.py --list
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from assessments.blueprints import BLUEPRINTS, get  # noqa: E402
from lab.assessment import generate, load_items  # noqa: E402
from lab.console import enable_utf8  # noqa: E402

OUTPUT_DIR = ROOT / "assessments" / "generated"


def build(blueprint_name: str, seed: int, output_dir: Path = OUTPUT_DIR) -> Path:
    """Genera la simulación y devuelve la ruta del enunciado escrito."""
    blueprint = get(blueprint_name)
    bank = load_items()
    if not bank:
        raise RuntimeError(
            "El banco de ítems está vacío. Revise assessments/items/*.json."
        )
    assessment = generate(blueprint, bank, seed=seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{blueprint_name}-semilla-{seed}.md"
    destination.write_text(assessment.to_markdown(), encoding="utf-8")
    return destination


def main() -> None:
    enable_utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blueprint", default="gestor-datos-transporte",
                        help="nombre corto de la configuración")
    parser.add_argument("--seed", type=int, default=1, help="semilla de generación")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--list", action="store_true",
                        help="lista las configuraciones disponibles y termina")
    args = parser.parse_args()

    if args.list:
        for name, blueprint in sorted(BLUEPRINTS.items()):
            print(f"{name:26} {blueprint.minutos:>4} min  {blueprint.nombre}")
        return

    path = build(args.blueprint, args.seed, output_dir=args.output)
    bank = load_items()
    assessment = generate(get(args.blueprint), bank, seed=args.seed)
    print(f"Simulación escrita en {path.relative_to(ROOT)}")
    print(f"  ítems: {len(assessment.items)} · tiempo: {assessment.minutos} min "
          f"de {assessment.blueprint.minutos} presupuestados")
    print(f"  competencias cubiertas: {len(assessment.competencias())}")
    if assessment.uncovered:
        print(f"  competencias obligatorias sin ítem en el banco: "
              f"{', '.join(assessment.uncovered)}")


if __name__ == "__main__":
    main()
