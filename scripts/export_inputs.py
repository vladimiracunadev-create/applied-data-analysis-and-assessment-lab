"""Exporta los CSV de cada caso a un único libro de Excel de entradas.

Qué produce
    `data/case_<n>/entradas.xlsx`, con una hoja por archivo CSV del caso, encabezado
    congelado, autofiltro y anchos de columna legibles.

Por qué existe
    Quien resuelve el caso en Excel necesita los cuatro archivos en un solo libro, sin
    pasar por el asistente de importación cuatro veces y sin riesgo de elegir mal la
    codificación. Este libro es la **zona de entradas**: no se edita. Los cálculos y
    los resultados van en hojas aparte, como explica `docs/learning/20-programacion/02`.

Diferencia con los libros resueltos
    Este script solo copia los datos. `scripts/build_excel_solutions.py` construye el
    libro **resuelto**, con fórmulas vivas y hoja de control.

Uso
    python scripts/export_inputs.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

#: Ancho de columna en caracteres. Suficiente para una fecha-hora completa.
ANCHO_COLUMNA = 22


def export(folder: Path) -> Path:
    """Escribe el libro de entradas de una carpeta de caso y devuelve su ruta."""
    destino = folder / "entradas.xlsx"
    archivos = sorted(folder.glob("*.csv"))
    if not archivos:
        raise FileNotFoundError(
            f"No hay CSV en {folder}. Genere los datos con 'python scripts/generate_data.py'."
        )
    with pd.ExcelWriter(destino, engine="xlsxwriter") as writer:
        for archivo in archivos:
            frame = pd.read_csv(archivo)
            frame.to_excel(writer, sheet_name=archivo.stem, index=False)
            hoja = writer.sheets[archivo.stem]
            hoja.freeze_panes(1, 0)
            hoja.autofilter(0, 0, len(frame), len(frame.columns) - 1)
            hoja.set_column(0, len(frame.columns) - 1, ANCHO_COLUMNA)
    return destino


def main() -> None:
    carpetas = sorted((ROOT / "data").glob("case_*"))
    if not carpetas:
        raise SystemExit(
            "No hay casos en data/. Ejecute primero: python scripts/generate_data.py"
        )
    for carpeta in carpetas:
        destino = export(carpeta)
        print(f"escrito {destino.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
