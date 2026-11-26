"""Dibuja un fragmento de hoja de cálculo como SVG: las celdas, la fórmula y su resultado.

Por qué existe
    Una fórmula en prosa no se relaciona con la hoja. `=CONTAR.SI($A$2:$A$1929;A2)>1`
    es correcto y no dice **dónde va**, **sobre qué rango** opera ni **qué devuelve**, y
    copiarla de un párrafo de Markdown arrastra la tipografía y las comillas curvas.

    Dibujar el fragmento resuelve las tres cosas a la vez: se ve la columna donde va, se
    ven las filas sobre las que actúa, y se ve el resultado. Y el archivo descargable
    queda para copiar de verdad, que es lo único que se copia bien.

Por qué SVG escrito a mano y no matplotlib
    Matplotlib dibuja datos. Esto no son datos: es una **interfaz**, con sus letras de
    columna, sus números de fila y su barra de fórmulas. Sale más limpio y más liviano
    con unas pocas etiquetas `<rect>` y `<text>`, y el texto queda seleccionable en el
    navegador.

Colores
    Los del estándar visual del laboratorio (`lab.viz`), para que un cuaderno no mezcle
    dos paletas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape

#: Paleta, tomada del estándar visual.
TINTA = "#11253B"
ACENTO = "#55D6BE"
TEXTO = "#17283A"
APAGADO = "#5C6B7A"
REJILLA = "#D5DDE5"
CABECERA = "#EEF2F6"
RESALTE = "#FFF6E5"
BORDE_RESALTE = "#B08A3E"

#: Geometría, en píxeles de usuario.
ALTO_FILA = 26
ANCHO_NUMERO = 34
MARGEN = 12
ALTO_BARRA = 34


@dataclass
class Columna:
    """Una columna del fragmento.

    Attributes:
        letra: la letra de Excel, `A`, `B`, `K`…
        nombre: el encabezado de la fila 1. Vacío para una columna de trabajo.
        ancho: ancho en píxeles.
    """

    letra: str
    nombre: str = ""
    ancho: int = 96


@dataclass
class Hoja:
    """Un fragmento de hoja listo para dibujar.

    Attributes:
        columnas: las columnas visibles, en orden.
        filas: filas de muestra. Cada una es la lista de celdas, alineada con
            `columnas`. El número de fila se dibuja a partir de `primera_fila`.
        primera_fila: número de la primera fila de datos. 2, normalmente.
        formula: la fórmula, tal como se escribe en la celda.
        celda: dónde va, por ejemplo `K2`.
        resultado: qué devuelve. Se dibuja en la celda resaltada.
        nota: una línea bajo el dibujo.
        corte: si se dibuja la fila de puntos que indica que la hoja sigue.
    """

    columnas: list[Columna]
    filas: list[list[str]] = field(default_factory=list)
    primera_fila: int = 2
    formula: str = ""
    celda: str = ""
    resultado: str = ""
    nota: str = ""
    corte: bool = True


def _texto(x: float, y: float, contenido: str, *, color: str = TEXTO,
           tamano: int = 12, peso: str = "normal", ancla: str = "start",
           mono: bool = False) -> str:
    familia = (
        "ui-monospace, SFMono-Regular, Consolas, monospace" if mono
        else "system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
    )
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" fill="{color}" font-size="{tamano}" '
        f'font-weight="{peso}" text-anchor="{ancla}" '
        f'font-family="{familia}">{escape(contenido)}</text>'
    )


def _rect(x: float, y: float, ancho: float, alto: float, *, relleno: str,
          borde: str = REJILLA, grosor: float = 1) -> str:
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{ancho:.1f}" height="{alto:.1f}" '
        f'fill="{relleno}" stroke="{borde}" stroke-width="{grosor}"/>'
    )


def render_hoja(hoja: Hoja) -> str:
    """El fragmento de hoja como documento SVG completo.

    Raises:
        ValueError: si una fila no tiene tantas celdas como columnas, o si la celda de
            la fórmula nombra una columna que no está dibujada.
    """
    if not hoja.columnas:
        raise ValueError("Un fragmento de hoja necesita al menos una columna.")
    for numero, fila in enumerate(hoja.filas, start=1):
        if len(fila) != len(hoja.columnas):
            raise ValueError(
                f"La fila {numero} tiene {len(fila)} celdas y hay "
                f"{len(hoja.columnas)} columnas."
            )

    letras = [c.letra for c in hoja.columnas]
    columna_resaltada = -1
    fila_resaltada = -1
    if hoja.celda:
        letra = "".join(ch for ch in hoja.celda if ch.isalpha()).upper()
        digitos = "".join(ch for ch in hoja.celda if ch.isdigit())
        if letra not in letras:
            raise ValueError(
                f"La celda {hoja.celda} nombra la columna {letra}, que no está entre "
                f"las dibujadas: {letras}."
            )
        columna_resaltada = letras.index(letra)
        if digitos:
            fila_resaltada = int(digitos) - hoja.primera_fila

    anchos = [c.ancho for c in hoja.columnas]
    ancho_tabla = ANCHO_NUMERO + sum(anchos)
    filas_dibujadas = len(hoja.filas) + (1 if hoja.corte else 0)
    alto_barra = ALTO_BARRA + 10 if hoja.formula else 0
    alto_nota = 24 if hoja.nota else 0
    ancho = ancho_tabla + 2 * MARGEN
    alto = (
        MARGEN + alto_barra + ALTO_FILA * 2 + ALTO_FILA * filas_dibujadas
        + alto_nota + MARGEN
    )

    partes: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" '
        f'viewBox="0 0 {ancho} {alto}" role="img">',
        f'<rect width="{ancho}" height="{alto}" fill="#FFFFFF"/>',
    ]

    y = MARGEN

    # --- barra de fórmulas
    if hoja.formula:
        partes.append(_rect(MARGEN, y, 46, ALTO_BARRA, relleno=CABECERA))
        partes.append(_texto(MARGEN + 23, y + 22, hoja.celda or "fx",
                             color=APAGADO, tamano=12, ancla="middle", peso="600"))
        partes.append(
            _rect(MARGEN + 46, y, ancho_tabla - 46, ALTO_BARRA, relleno="#FFFFFF")
        )
        partes.append(
            _texto(MARGEN + 56, y + 22, hoja.formula, color=TINTA, tamano=12.5,
                   mono=True)
        )
        y += alto_barra

    # --- letras de columna
    partes.append(_rect(MARGEN, y, ANCHO_NUMERO, ALTO_FILA, relleno=CABECERA))
    x = MARGEN + ANCHO_NUMERO
    for indice, columna in enumerate(hoja.columnas):
        relleno = ACENTO if indice == columna_resaltada else CABECERA
        partes.append(_rect(x, y, columna.ancho, ALTO_FILA, relleno=relleno))
        partes.append(
            _texto(x + columna.ancho / 2, y + 18, columna.letra, color=TINTA,
                   tamano=12, peso="700", ancla="middle")
        )
        x += columna.ancho
    y += ALTO_FILA

    # --- fila 1: los encabezados del dato
    partes.append(_rect(MARGEN, y, ANCHO_NUMERO, ALTO_FILA, relleno=CABECERA))
    partes.append(_texto(MARGEN + ANCHO_NUMERO / 2, y + 18, "1", color=APAGADO,
                         tamano=11, ancla="middle"))
    x = MARGEN + ANCHO_NUMERO
    for columna in hoja.columnas:
        partes.append(_rect(x, y, columna.ancho, ALTO_FILA, relleno=TINTA,
                            borde=TINTA))
        if columna.nombre:
            partes.append(
                _texto(x + 6, y + 18, columna.nombre, color="#FFFFFF", tamano=11.5,
                       peso="600")
            )
        x += columna.ancho
    y += ALTO_FILA

    # --- filas de datos
    for indice, fila in enumerate(hoja.filas):
        numero = hoja.primera_fila + indice
        partes.append(_rect(MARGEN, y, ANCHO_NUMERO, ALTO_FILA, relleno=CABECERA))
        partes.append(_texto(MARGEN + ANCHO_NUMERO / 2, y + 18, str(numero),
                             color=APAGADO, tamano=11, ancla="middle"))
        x = MARGEN + ANCHO_NUMERO
        for posicion, (columna, celda) in enumerate(zip(hoja.columnas, fila,
                                                        strict=True)):
            resaltada = posicion == columna_resaltada and indice == fila_resaltada
            partes.append(
                _rect(x, y, columna.ancho, ALTO_FILA,
                      relleno=RESALTE if resaltada else "#FFFFFF",
                      borde=BORDE_RESALTE if resaltada else REJILLA,
                      grosor=1.8 if resaltada else 1)
            )
            contenido = hoja.resultado if resaltada and hoja.resultado else celda
            if contenido:
                partes.append(
                    _texto(x + 6, y + 18, contenido, tamano=11.5,
                           color=TINTA if resaltada else TEXTO,
                           peso="700" if resaltada else "normal",
                           mono=resaltada)
                )
            x += columna.ancho
        y += ALTO_FILA

    # --- corte: la hoja sigue
    if hoja.corte:
        partes.append(_rect(MARGEN, y, ANCHO_NUMERO, ALTO_FILA, relleno=CABECERA))
        partes.append(_texto(MARGEN + ANCHO_NUMERO / 2, y + 18, "⋮", color=APAGADO,
                             tamano=13, ancla="middle"))
        x = MARGEN + ANCHO_NUMERO
        for columna in hoja.columnas:
            partes.append(_rect(x, y, columna.ancho, ALTO_FILA, relleno="#FFFFFF"))
            partes.append(_texto(x + columna.ancho / 2, y + 18, "⋮", color=REJILLA,
                                 tamano=13, ancla="middle"))
            x += columna.ancho
        y += ALTO_FILA

    if hoja.nota:
        partes.append(_texto(MARGEN, y + 16, hoja.nota, color=APAGADO, tamano=11.5))

    partes.append("</svg>")
    return "\n".join(partes) + "\n"
