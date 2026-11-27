"""Construye un ZIP determinista con todos los casos y sus soluciones publicables.

El paquete incluye los trece casos, sus cuadernos y resultados versionados, las cuatro
implementaciones ejecutables de referencia (Pandas, Polars, R y SQL), los datos
sintéticos y la documentación necesaria para orientarse. Nunca incluye descargas de
terceros desde ``data/original``.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "dist" / "todos-los-casos.zip"
ARCHIVE_ROOT = "applied-data-analysis-and-assessment-lab-casos"
FIXED_TIME = (2026, 11, 27, 0, 0, 0)

TOP_LEVEL_FILES = (
    "README.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "PROMPT_MAESTRO.md",
    "SECURITY.md",
    "pyproject.toml",
    "uv.lock",
)
PACKAGE_DIRS = (
    "assessments",
    "cases",
    "docs",
    "knowledge",
    "lab",
    "scripts",
    "simulations",
    "solutions",
    "templates",
    "tests",
)


def files_to_package(root: Path = ROOT) -> list[Path]:
    """Enumera solo contenido versionable y reproducible del paquete general."""
    paths = [root / item for item in TOP_LEVEL_FILES]
    for name in PACKAGE_DIRS:
        folder = root / name
        if folder.exists():
            paths.extend(path for path in folder.rglob("*") if path.is_file())
    for folder in sorted((root / "data").glob("case_*")):
        paths.extend(path for path in folder.rglob("*") if path.is_file())
    return sorted({path for path in paths if "__pycache__" not in path.parts})


def _entry(name: str, data: bytes) -> tuple[zipfile.ZipInfo, bytes]:
    info = zipfile.ZipInfo(f"{ARCHIVE_ROOT}/{name}", date_time=FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    info.create_system = 3
    return info, data


def build_bytes(root: Path = ROOT) -> bytes:
    """Devuelve el ZIP completo en memoria para permitir una comprobación exacta."""
    payload: list[tuple[str, bytes]] = []
    manifest_files: list[dict[str, object]] = []
    for path in files_to_package(root):
        relative = path.relative_to(root).as_posix()
        data = path.read_bytes()
        payload.append((relative, data))
        manifest_files.append({
            "path": relative,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    manifest = json.dumps(
        {
            "schema": 1,
            "cases": len(list((root / "cases").glob("*/case.json"))),
            "notebooks": len(list((root / "cases").glob("*/CUADERNO.md"))),
            "engines": ["Pandas", "Polars", "R base", "SQL", "Excel"],
            "third_party_data_included": False,
            "files": manifest_files,
        },
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8") + b"\n"
    payload.append(("MANIFEST.json", manifest))

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payload):
            info, content = _entry(name, data)
            archive.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return buffer.getvalue()


def write(destination: Path = DESTINATION) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(build_bytes())
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="falla si el ZIP publicado está desfasado")
    args = parser.parse_args()
    expected = build_bytes()
    if args.check:
        if not DESTINATION.exists() or DESTINATION.read_bytes() != expected:
            raise SystemExit(f"desfasado: {DESTINATION.relative_to(ROOT)}")
        print(f"al día: {DESTINATION.relative_to(ROOT)}")
        return
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    DESTINATION.write_bytes(expected)
    print(f"escrito {DESTINATION.relative_to(ROOT)} ({len(expected):,} bytes)")


if __name__ == "__main__":
    main()
