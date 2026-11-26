"""Descarga una fuente pública del catálogo, registrando su procedencia.

Qué hace
    Resuelve el enlace de descarga, trae el archivo a `data/original/`, comprueba su
    huella si se conoce y deja al lado un registro con la URL, la fecha, el tamaño, el
    tipo de contenido y el SHA-256.

Por qué los datos descargados no se versionan
    Pesan decenas de megabytes y su licencia no está verificada. El repositorio
    publica el **código** que los procesa y el **registro de procedencia** que permite
    comprobar que se está mirando el mismo archivo, no los datos de terceros.

Uso
    python scripts/fetch_data.py --listar
    python scripts/fetch_data.py gtfs-red-movilidad
    python scripts/fetch_data.py gtfs-red-movilidad --sha256 ff0cda44...
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lab.console import enable_utf8  # noqa: E402
from lab.sources import CATALOG, fetch, get, manifest, zip_members  # noqa: E402

DESTINO = ROOT / "data" / "original"


def main() -> None:
    enable_utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fuente", nargs="?", help="nombre de la fuente del catálogo")
    parser.add_argument("--sha256", default="",
                        help="huella esperada; si no coincide, no se conserva el archivo")
    parser.add_argument("--forzar", action="store_true",
                        help="volver a descargar aunque ya exista")
    parser.add_argument("--listar", action="store_true",
                        help="listar el catálogo y lo ya descargado")
    args = parser.parse_args()

    if args.listar or not args.fuente:
        print("Fuentes declaradas:\n")
        for nombre, fuente in sorted(CATALOG.items()):
            marca = "verificada" if fuente.licence_verified else "NO verificada"
            print(f"  {nombre}")
            print(f"    publica:  {fuente.publisher}")
            print(f"    página:   {fuente.url}")
            print(f"    licencia: {fuente.licence} ({marca})")
            print(f"    contiene: {fuente.description}")
            print()
        inventario = manifest(DESTINO)
        if inventario.empty:
            print("Nada descargado todavía en data/original/.")
        else:
            print("Ya descargado:\n")
            print(inventario.to_string(index=False))
        return

    fuente = get(args.fuente)
    destino = DESTINO / f"{fuente.name}.zip"
    print(f"Fuente:   {fuente.name}")
    print(f"Publica:  {fuente.publisher}")
    print(f"Licencia: {fuente.licence}")
    if not fuente.licence_verified:
        print("          Revise los términos de uso antes de redistribuir estos datos.")
    print(f"Página:   {fuente.url}\n")

    ruta, procedencia = fetch(fuente, destino, expected_sha256=args.sha256, force=args.forzar)
    print(f"Archivo:  {ruta.relative_to(ROOT)}")
    print(f"Cita:     {procedencia.summary()}")
    for nota in procedencia.notes:
        print(f"Nota:     {nota}")

    if ruta.suffix.lower() == ".zip":
        print("\nContenido:")
        print(zip_members(ruta).to_string(index=False))


if __name__ == "__main__":
    main()
