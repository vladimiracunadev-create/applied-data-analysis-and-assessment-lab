"""Genera los cuadernos de trabajo de los casos que declaran uno.

Un cuaderno es el caso resuelto **paso a paso**: para cada paso, el código de Pandas,
la salida que devuelve de verdad, y cómo se hace lo mismo en Excel. Se lee de arriba
abajo sin abrir ningún otro archivo.

Qué hace
    Busca en `cases/*/cuaderno.py` una función `construir()` que devuelva un
    `lab.cuaderno.Cuaderno`, lo ejecuta, y escribe `CUADERNO.md` junto al caso.

Por qué se genera y no se escribe
    Porque el código que aparece es el que se ejecutó y la salida es la que devolvió.
    Un apunte con salidas copiadas a mano envejece sin avisar, y el día que se estudia
    ya no describe lo que pasa. Si el código deja de funcionar, el cuaderno no se
    genera: no hay forma de que el documento mienta y siga publicado.

Necesita los datos descargados
    A diferencia de `build_docs.py`, este script **ejecuta el caso**, de modo que
    necesita los archivos públicos en `data/original/`. No corre en integración
    continua por eso, y el `CUADERNO.md` resultante se versiona —es texto y salidas
    agregadas, no datos de terceros—, igual que las tablas de `resultados/`.

Uso
    python scripts/build_cuadernos.py                # todos los declarados
    python scripts/build_cuadernos.py bip_lugares_carga
    python scripts/build_cuadernos.py --check       # falla si alguno quedó desfasado
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lab.console import enable_utf8  # noqa: E402
from lab.cuaderno import render  # noqa: E402

NOMBRE_SALIDA = "CUADERNO.md"


def casos_con_cuaderno() -> list[str]:
    """Los casos que declaran un cuaderno, en orden alfabético."""
    return sorted(
        ruta.parent.name
        for ruta in (ROOT / "cases").glob("*/cuaderno.py")
    )


def construir(slug: str) -> tuple[Path, str]:
    """Genera el cuaderno de un caso y devuelve su ruta y su contenido."""
    modulo = importlib.import_module(f"cases.{slug}.cuaderno")
    if not hasattr(modulo, "construir"):
        raise AttributeError(
            f"cases/{slug}/cuaderno.py no define construir(); "
            "tiene que devolver un lab.cuaderno.Cuaderno"
        )
    documento = render(modulo.construir())
    return ROOT / "cases" / slug / NOMBRE_SALIDA, documento


def main() -> int:
    enable_utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("casos", nargs="*", help="slugs a generar; por defecto, todos")
    parser.add_argument(
        "--check", action="store_true",
        help="no escribe: falla si algún cuaderno quedó desfasado del código",
    )
    argumentos = parser.parse_args()

    seleccion = argumentos.casos or casos_con_cuaderno()
    if not seleccion:
        print("Ningún caso declara un cuaderno todavía.")
        return 0

    desfasados: list[str] = []
    for slug in seleccion:
        destino, documento = construir(slug)
        relativo = destino.relative_to(ROOT).as_posix()
        if argumentos.check:
            actual = destino.read_text(encoding="utf-8") if destino.exists() else ""
            if actual != documento:
                desfasados.append(relativo)
                print(f"desfasado {relativo}")
            else:
                print(f"al día    {relativo}")
            continue
        destino.write_text(documento, encoding="utf-8")
        pasos = documento.count("\n## Paso ")
        print(f"escrito {relativo}  ({pasos} pasos, {len(documento):,} caracteres)")

    if desfasados:
        print(
            f"\n{len(desfasados)} cuaderno(s) desfasado(s). "
            "Ejecute: python scripts/build_cuadernos.py"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
