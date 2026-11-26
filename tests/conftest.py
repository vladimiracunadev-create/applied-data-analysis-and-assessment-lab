"""Configuración común de las pruebas.

Agrega la raíz del repositorio a `sys.path` para que `lab`, `cases` y `solutions`
sean importables sin instalar el proyecto como paquete, y expone los datos
sintéticos como fixture. Si los datos no existen, se generan: así `pytest` funciona
en una copia recién clonada sin pasos previos.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Raíz del repositorio."""
    return ROOT


@pytest.fixture(scope="session", autouse=True)
def synthetic_data() -> Path:
    """Garantiza que los datos sintéticos de los tres casos existan."""
    data_dir = ROOT / "data"
    expected = [data_dir / f"case_{case}" / "viajes.csv" for case in (1, 2, 3)]
    if not all(p.exists() for p in expected):
        sys.path.insert(0, str(ROOT / "scripts"))
        from generate_data import generate  # type: ignore[import-not-found]

        for case in (1, 2, 3):
            generate(case)
    return data_dir


@pytest.fixture(scope="session")
def tmp_outputs(tmp_path_factory) -> Path:
    """Directorio temporal compartido para artefactos generados en las pruebas."""
    return tmp_path_factory.mktemp("outputs")
