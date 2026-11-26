"""Libros de Excel profesionales: encabezados, filtros, unidades y fórmulas vivas.

Qué hace
    Construye libros `.xlsx` con una presentación consistente (paleta del estándar
    visual, encabezado congelado, autofiltro, anchos calculados, formatos numéricos
    por columna, fila de unidades) y con separación explícita entre hojas de
    **entradas**, **cálculos** y **resultados**. También permite escribir fórmulas
    reales de Excel, de modo que el libro se pueda auditar abriendo las celdas.

Por qué existe
    En una evaluación técnica no basta con que el número sea correcto: hay que poder
    demostrar cómo se obtuvo. Un libro con valores pegados no demuestra nada; un
    libro con `=SUMAR.SI.CONJUNTO(...)` sí. Este módulo produce lo segundo.

Nota sobre el idioma de las fórmulas
    El formato de archivo almacena las fórmulas con nombres en inglés
    (`SUMIFS`, `XLOOKUP`); Excel las muestra traducidas según la configuración
    regional. Por eso aquí se escriben en inglés y la documentación indica el
    equivalente en español. El separador de argumentos en el archivo es siempre la
    coma, aunque Excel muestre punto y coma.

Cómo se valida
    `tests/test_excel.py` abre los libros generados con openpyxl y comprueba hojas,
    encabezados, congelado, autofiltro y que las fórmulas quedaron escritas como
    fórmulas y no como texto.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import pandas as pd

#: Paleta del estándar visual del laboratorio (docs/visual-standard.md).
INK = "#11253B"       # azul profundo: encabezados
ACCENT = "#55D6BE"    # verde acento: destacados y totales
TEXT = "#17283A"      # texto
MUTED = "#5C6B7A"     # texto secundario
BORDER = "#D5DDE5"

SectionKind = Literal["entradas", "calculos", "resultados", "documentacion"]

#: Formatos numéricos por tipo de contenido. Se aplican por nombre de columna.
NUMBER_FORMATS: dict[str, str] = {
    "entero": "#,##0",
    "decimal": "#,##0.00",
    "porcentaje": '0.0"%"',
    "minutos": '#,##0.0" min"',
    "fecha_hora": "yyyy-mm-dd hh:mm",
    "fecha": "yyyy-mm-dd",
    "texto": "@",
}


@dataclass
class Sheet:
    """Una hoja a escribir.

    Args:
        name: nombre de la hoja (máximo 31 caracteres, sin `[]:*?/\\`).
        frame: datos.
        kind: sección a la que pertenece; determina el color del encabezado y el
            orden en la hoja índice.
        units: unidad por columna, mostrada bajo el encabezado.
        formats: clave de `NUMBER_FORMATS` por columna.
        notes: texto explicativo que se escribe sobre la tabla.
        formulas: fórmulas a escribir, `{celda: formula}`, con la fórmula en inglés
            y empezando por `=`.
    """

    name: str
    frame: pd.DataFrame
    kind: SectionKind = "resultados"
    units: Mapping[str, str] = field(default_factory=dict)
    formats: Mapping[str, str] = field(default_factory=dict)
    notes: str = ""
    formulas: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        invalid = set(self.name) & set("[]:*?/\\")
        if invalid or not self.name or len(self.name) > 31:
            raise ValueError(
                f"Nombre de hoja inválido: {self.name!r}. Máximo 31 caracteres sin []:*?/\\."
            )
        unknown = {v for v in self.formats.values() if v not in NUMBER_FORMATS}
        if unknown:
            raise ValueError(f"Formatos desconocidos: {sorted(unknown)}. Use {sorted(NUMBER_FORMATS)}.")
        for cell, formula in self.formulas.items():
            if not str(formula).startswith("="):
                raise ValueError(f"La fórmula de {cell} debe comenzar con '='.")


#: Color de encabezado por sección: el lector distingue de un golpe qué está mirando.
_SECTION_COLOR: dict[SectionKind, str] = {
    "entradas": MUTED,
    "calculos": INK,
    "resultados": INK,
    "documentacion": MUTED,
}

_SECTION_ORDER: dict[SectionKind, int] = {
    "documentacion": 0,
    "entradas": 1,
    "calculos": 2,
    "resultados": 3,
}


def write_workbook(
    path: str | Path,
    sheets: Sequence[Sheet],
    title: str = "",
    source: str = "",
    include_index: bool = True,
) -> Path:
    """Escribe un libro con presentación profesional y hoja índice.

    Args:
        path: destino `.xlsx`; los directorios se crean si faltan.
        sheets: hojas a escribir, en el orden deseado.
        title: título del trabajo, mostrado en el índice.
        source: procedencia de los datos, mostrada en el índice.
        include_index: si se agrega la hoja `00_indice`.

    Returns:
        La ruta escrita.

    Raises:
        ValueError: si no hay hojas o si hay nombres repetidos.
    """
    if not sheets:
        raise ValueError("Un libro necesita al menos una hoja.")
    names = [s.name for s in sheets]
    if len(set(names)) != len(names):
        raise ValueError(f"Nombres de hoja repetidos: {names}.")

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(destination, engine="xlsxwriter",
                        datetime_format=NUMBER_FORMATS["fecha_hora"]) as writer:
        book = writer.book
        styles = _build_styles(book)
        if include_index:
            _write_index(book, styles, sheets, title=title, source=source)
        for sheet in sheets:
            _write_sheet(writer, book, styles, sheet)
    return destination


def _build_styles(book) -> dict[str, Any]:
    base = {"font_name": "Calibri", "font_size": 11, "font_color": TEXT}
    styles = {
        "title": book.add_format({**base, "bold": True, "font_size": 16, "font_color": INK}),
        "subtitle": book.add_format({**base, "font_color": MUTED, "italic": True}),
        "note": book.add_format({**base, "font_color": MUTED, "text_wrap": True, "valign": "top"}),
        "cell": book.add_format({**base, "border": 1, "border_color": BORDER}),
        "unit": book.add_format({**base, "italic": True, "font_color": MUTED, "align": "center",
                                 "border": 1, "border_color": BORDER, "bg_color": "#F4F7FA"}),
        "accent": book.add_format({**base, "bold": True, "bg_color": ACCENT, "border": 1,
                                   "border_color": BORDER}),
        "link": book.add_format({**base, "font_color": "#1A6FB5", "underline": 1}),
    }
    for kind, colour in _SECTION_COLOR.items():
        styles[f"header_{kind}"] = book.add_format(
            {**base, "bold": True, "bg_color": colour, "font_color": "#FFFFFF",
             "border": 1, "border_color": colour, "text_wrap": True, "valign": "vcenter"}
        )
    for key, fmt in NUMBER_FORMATS.items():
        styles[f"num_{key}"] = book.add_format(
            {**base, "num_format": fmt, "border": 1, "border_color": BORDER}
        )
    return styles


def _write_index(book, styles, sheets: Sequence[Sheet], title: str, source: str) -> None:
    ws = book.add_worksheet("00_indice")
    ws.hide_gridlines(2)
    ws.set_column(0, 0, 26)
    ws.set_column(1, 1, 16)
    ws.set_column(2, 2, 64)
    ws.write(0, 0, title or "Resultados del análisis", styles["title"])
    ws.write(1, 0, "Libro generado por el laboratorio; revise cada hoja antes de usarla.",
             styles["subtitle"])
    if source:
        ws.write(2, 0, f"Procedencia de los datos: {source}", styles["subtitle"])
    row = 4
    for column, label in enumerate(("Hoja", "Sección", "Contenido")):
        ws.write(row, column, label, styles["header_documentacion"])
    row += 1
    for sheet in sorted(sheets, key=lambda s: (_SECTION_ORDER[s.kind], s.name)):
        ws.write_url(row, 0, f"internal:'{sheet.name}'!A1", styles["link"], string=sheet.name)
        ws.write(row, 1, sheet.kind, styles["cell"])
        ws.write(row, 2, sheet.notes or f"{len(sheet.frame)} filas × {len(sheet.frame.columns)} columnas",
                 styles["cell"])
        row += 1
    row += 1
    ws.write(row, 0, "Convención de secciones", styles["header_documentacion"])
    for text in (
        "entradas: datos tal como llegaron. No se modifican.",
        "calculos: transformaciones intermedias y columnas auxiliares.",
        "resultados: indicadores finales que respaldan las conclusiones.",
        "documentacion: diccionario, supuestos y control de validación.",
    ):
        row += 1
        ws.write(row, 0, text, styles["note"])


def data_start_row(has_notes: bool = True) -> int:
    """Primera fila de datos (1-based, como la numera Excel) que escribe `write_workbook`.

    El diseño de cada hoja es: título, subtítulo, nota opcional, encabezado, fila de
    unidades y luego los datos. Quien escriba fórmulas que apunten a otra hoja
    necesita este número; calcularlo a mano es la forma más rápida de desalinear un
    rango en una celda.
    """
    start = 3 if has_notes else 2
    return start + 3


def column_letter(index: int) -> str:
    """Letra de columna de Excel a partir de un índice base cero (0 → A, 27 → AB)."""
    if index < 0:
        raise ValueError("El índice de columna no puede ser negativo.")
    letters = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def range_ref(sheet_name: str, column_index: int, first_row: int, last_row: int) -> str:
    """Referencia absoluta a una columna de otra hoja, con el nombre entre comillas.

    Las comillas son obligatorias cuando el nombre de la hoja empieza por un dígito
    o contiene espacios, que es el caso de la convención `10_calculos` del laboratorio.
    """
    if last_row < first_row:
        raise ValueError(f"Rango vacío: filas {first_row} a {last_row}.")
    letter = column_letter(column_index)
    return f"'{sheet_name}'!${letter}${first_row}:${letter}${last_row}"


def _write_sheet(writer, book, styles, sheet: Sheet) -> None:
    frame = sheet.frame.copy()
    # La fila de unidades va ENCIMA del encabezado, no debajo. Un autofiltro de Excel
    # exige que los datos empiecen inmediatamente bajo el encabezado; con la fila de
    # unidades en medio, el filtro la trataría como un registro más.
    start_row = 3 if sheet.notes else 2
    unit_row = start_row
    header_row = unit_row + 1
    data_row = header_row + 1

    frame.to_excel(writer, sheet_name=sheet.name, index=False,
                   startrow=data_row, header=False)
    ws = writer.sheets[sheet.name]
    ws.hide_gridlines(2)
    ws.write(0, 0, sheet.name.replace("_", " ").title(), styles["title"])
    ws.write(1, 0, f"Sección: {sheet.kind} · {len(frame)} filas", styles["subtitle"])
    if sheet.notes:
        ws.write(2, 0, sheet.notes, styles["note"])

    header_style = styles[f"header_{sheet.kind}"]
    for column, name in enumerate(frame.columns):
        ws.write(header_row, column, str(name), header_style)
        ws.write(unit_row, column, sheet.units.get(str(name), "—"), styles["unit"])
        width = max(len(str(name)) + 2, 12)
        if len(frame):
            sample = frame[name].astype("string").fillna("").str.len().max()
            width = max(width, min(int(sample) + 4, 48))
        fmt_key = sheet.formats.get(str(name))
        ws.set_column(column, column, width, styles[f"num_{fmt_key}"] if fmt_key else styles["cell"])

    if len(frame):
        last_row = data_row + len(frame) - 1
        ws.autofilter(header_row, 0, last_row, len(frame.columns) - 1)
    ws.freeze_panes(data_row, 0)

    for cell, formula in sheet.formulas.items():
        ws.write_formula(cell, formula, styles["accent"])


# ------------------------------------------------------------------ fórmulas auxiliares
def sumifs(sum_range: str, criteria: Iterable[tuple[str, str]]) -> str:
    """Construye `SUMIFS` (en español: SUMAR.SI.CONJUNTO).

    Args:
        sum_range: rango a sumar, por ejemplo `"Viajes[pasajeros]"`.
        criteria: pares `(rango_criterio, criterio)`; el criterio puede ser una
            referencia de celda o un literal entre comillas dobles.

    Example:
        >>> sumifs("Viajes[pasajeros]", [("Viajes[operador]", "$A2")])
        '=SUMIFS(Viajes[pasajeros],Viajes[operador],$A2)'
    """
    parts = [sum_range]
    for rng, crit in criteria:
        parts += [rng, crit]
    if len(parts) < 3:
        raise ValueError("SUMIFS necesita al menos un par rango/criterio.")
    return "=SUMIFS(" + ",".join(parts) + ")"


def countifs(criteria: Iterable[tuple[str, str]]) -> str:
    """Construye `COUNTIFS` (en español: CONTAR.SI.CONJUNTO)."""
    parts: list[str] = []
    for rng, crit in criteria:
        parts += [rng, crit]
    if not parts:
        raise ValueError("COUNTIFS necesita al menos un par rango/criterio.")
    return "=COUNTIFS(" + ",".join(parts) + ")"


def xlookup(lookup: str, lookup_array: str, return_array: str, if_not_found: str = '"SIN CLAVE"') -> str:
    """Construye `XLOOKUP` (en español: BUSCARX), con valor por defecto explícito.

    Declarar `if_not_found` es obligatorio en la práctica del laboratorio: una
    búsqueda que falla en silencio produce un cruce incompleto que nadie detecta.
    """
    return f"=XLOOKUP({lookup},{lookup_array},{return_array},{if_not_found})"


def safe_divide(numerator: str, denominator: str, scale: int = 1) -> str:
    """Construye una división protegida contra denominador cero o vacío.

    Equivale a `safe_ratio` de `lab.metrics`: devuelve texto vacío en lugar de
    `#¡DIV/0!`, para que la planilla no propague errores a las tablas dinámicas.
    """
    factor = f"{scale}*" if scale != 1 else ""
    return f"=IF(N({denominator})=0,\"\",{factor}{numerator}/{denominator})"


def duration_minutes_formula(start_cell: str, end_cell: str) -> str:
    """Duración en minutos en Excel: `(fin − inicio) × 1440`, protegida ante vacíos."""
    return f'=IF(OR({start_cell}="",{end_cell}=""),"",({end_cell}-{start_cell})*1440)'
