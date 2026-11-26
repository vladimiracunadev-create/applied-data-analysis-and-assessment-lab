"""Configuración común de las pruebas.

Agrega la raíz del repositorio a `sys.path` para que `lab`, `cases` y `solutions`
sean importables sin instalar el proyecto como paquete, y expone los datos
sintéticos como fixture. Si los datos no existen, se generan: así `pytest` funciona
en una copia recién clonada sin pasos previos.

Y hace algo más, que es la razón de que este archivo valga la pena leerlo: **esconde
los datos públicos descargados durante toda la sesión de pruebas**.

Por qué
    La suite tiene que pasar sin los archivos descargados, porque así corre en
    integración continua: `data/original/` está en `.gitignore` y nadie la descarga allí.
    Una prueba que llama sin darse cuenta a una función que lee esa carpeta pasa en la
    máquina de quien la escribió y falla en CI.

    Eso ocurrió de verdad. `tabla_de_detectores` del caso P10 llamaba por dentro a una
    función que lee los cinco Excel: una función de informe con una lectura de disco
    escondida. Pasó en la máquina de desarrollo, falló en los tres Python de la matriz,
    y estuvo **dos versiones** sin corregir porque el síntoma solo aparecía en CI.

    Documentarlo en `CONTRIBUTING.md` no bastó: pedía acordarse de correr un comando
    extra. De modo que el laboratorio hace lo contrario de pedir disciplina y cambia el
    entorno: con `apartar_datos_descargados` activo, **local y CI son el mismo entorno**
    y el defecto es imposible de no ver.

Qué significa para quien escribe una prueba
    Una prueba **no puede** depender de los datos descargados. Si necesita datos, los
    construye: `tests/test_bip.py` arma libros de Excel mínimos, `tests/test_gtfs.py` y
    los demás arman un ZIP con los formatos problemáticos del feed real.

    Si una prueba falla con `FileNotFoundError: Faltan N de los N archivos`, la causa
    es una lectura de disco escondida en una función de informe. La corrección es
    **recibir** la tabla como argumento en lugar de calcularla dentro. No marcar la
    prueba como omitida.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

#: Constantes de los módulos de caso que apuntan a los datos públicos descargados. Se
#: redirigen a una carpeta vacía durante las pruebas. La lista se recorre contra los
#: módulos que existan: un caso nuevo queda cubierto por el solo hecho de usar los
#: mismos nombres, que son los que ya usa todo el repositorio.
CONSTANTES_DE_DATOS: tuple[str, ...] = ("ORIGINAL", "FEED")


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


@pytest.fixture(scope="session", autouse=True)
def apartar_datos_descargados(tmp_path_factory) -> Path:
    """Durante las pruebas, los datos descargados no existen.

    Redirige a una carpeta vacía las constantes de los módulos de caso que apuntan a
    `data/original/`. No mueve ni borra nada en el disco: cambia a dónde mira el código
    mientras corre la sesión, y pytest restituye los valores al terminar.

    El efecto es que local y CI son el mismo entorno, y una lectura de disco escondida
    en una función de informe falla en el acto en lugar de dos versiones más tarde.
    """
    vacia = tmp_path_factory.mktemp("sin-datos-descargados")
    monkeypatch = pytest.MonkeyPatch()
    paquetes = sorted(
        ruta.name for ruta in (ROOT / "cases").iterdir()
        if (ruta / "solution.py").exists()
    )
    for paquete in paquetes:
        modulo = importlib.import_module(f"cases.{paquete}.solution")
        for constante in CONSTANTES_DE_DATOS:
            if not hasattr(modulo, constante):
                continue
            actual = getattr(modulo, constante)
            # Una constante que apunta a un archivo se redirige a un archivo
            # inexistente dentro de la carpeta vacía; una que apunta a una carpeta, a
            # la carpeta vacía.
            destino = vacia / actual.name if actual.suffix else vacia
            monkeypatch.setattr(modulo, constante, destino, raising=True)
    yield vacia
    monkeypatch.undo()


@pytest.fixture(scope="session")
def tmp_outputs(tmp_path_factory) -> Path:
    """Directorio temporal compartido para artefactos generados en las pruebas."""
    return tmp_path_factory.mktemp("outputs")
