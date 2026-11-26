"""Crea la carpeta de un caso nuevo a partir de la plantilla.

Qué hace
    Copia `templates/case/` a `cases/<nombre>/` y escribe un `case.json` con los 26
    campos obligatorios en blanco, listos para completar.

Por qué el `case.json` se crea vacío y no se omite
    Un caso sin metadatos aparece en el catálogo marcado como incompleto, lo que es
    exactamente lo que debe ocurrir mientras se está escribiendo. Omitir el archivo
    haría que el caso no apareciera en absoluto, y un caso invisible se olvida.

Uso
    python scripts/new_case.py mi-caso
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Nombres admitidos: minúsculas, dígitos, guion y guion bajo. El nombre se usa como
#: slug en los metadatos, como nombre de carpeta y como identificador en el catálogo.
PATRON_NOMBRE = re.compile(r"[a-z][a-z0-9_-]*")

VOCABULARIO = (
    "Dificultad: introductorio | intermedio | avanzado | especializado. "
    "Estado: implementado | parcial | proyectado. "
    "Competencias: use los valores de lab.profiles.COMPETENCIES."
)


def plantilla_metadatos(slug: str) -> dict[str, object]:
    """Esqueleto de `case.json` con los 26 campos obligatorios."""
    from lab.catalog import CONTENT_FIELDS

    datos: dict[str, object] = {
        "slug": slug,
        "titulo": "",
        "disciplina": "",
        "industria": "",
        "dificultad": "intermedio",
        "metodologia": "",
        "competencias": [],
        "estado": "proyectado",
        "tiempo_sugerido_min": 90,
        "_vocabulario": VOCABULARIO,
    }
    for campo in CONTENT_FIELDS:
        datos[campo] = []
    return datos


def create(nombre: str, root: Path = ROOT) -> Path:
    """Crea el caso y devuelve su carpeta.

    Raises:
        ValueError: si el nombre no sigue la convención.
        FileExistsError: si el caso ya existe. No se sobrescribe nada.
    """
    if not PATRON_NOMBRE.fullmatch(nombre):
        raise ValueError(
            f"Nombre inválido: {nombre!r}. Use minúsculas, dígitos, guion y guion bajo, "
            "empezando por una letra."
        )
    destino = root / "cases" / nombre
    if destino.exists():
        raise FileExistsError(f"El caso {nombre!r} ya existe en {destino}.")
    shutil.copytree(root / "templates" / "case", destino)
    (destino / "case.json").write_text(
        json.dumps(plantilla_metadatos(nombre), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return destino


def main() -> None:
    import sys

    sys.path.insert(0, str(ROOT))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="slug del caso, en minúsculas")
    args = parser.parse_args()
    try:
        destino = create(args.name)
    except (ValueError, FileExistsError) as error:
        parser.error(str(error))
    print(destino)
    print("\nComplete case.json y luego valide con:")
    print("  python -m pytest tests/test_catalog.py")


if __name__ == "__main__":
    main()
