"""Diagramas en SVG: el flujo de un problema y el mapa mental de su solución.

Por qué existe
    Un cuaderno de trabajo empieza con dos cosas que no se explican bien en prosa:
    **cuál es el problema** y **qué se va a hacer**. Un párrafo de ocho líneas describe
    un flujo de datos peor que cinco cajas con flechas, y la estructura de un recorrido
    de doce pasos no se retiene leyéndola en vertical.

    Los dos diagramas de este módulo cubren esos dos huecos:

    - `render_flujo` dibuja **el problema**: de dónde vienen los datos, por dónde pasan
      y qué sale. Cajas y flechas, de izquierda a derecha.
    - `render_mapa` dibuja **la solución**: el recorrido agrupado por bloques, con lo
      que se resuelve en cada uno. Un mapa mental con el centro a la izquierda y las
      ramas a la derecha.

Por qué la rama no es radial
    Un mapa radial se ve bien con cuatro ramas de dos palabras y se vuelve ilegible con
    seis ramas de cuatro elementos, que es el caso real: el texto se solapa o hay que
    rotarlo. Con el centro a la izquierda y las ramas apiladas a la derecha, el texto
    va siempre horizontal y el diagrama crece hacia abajo sin pisarse.

Por qué SVG escrito a mano
    Son interfaces y esquemas, no datos. Unas pocas etiquetas `<rect>`, `<path>` y
    `<text>` dan un resultado más limpio y liviano que cualquier biblioteca de
    diagramas, el texto queda seleccionable, y no agrega una dependencia al entorno
    mínimo. Los colores son los del estándar visual (`lab.viz`), para que un cuaderno
    no mezcle dos paletas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape

#: Paleta, del estándar visual del laboratorio.
TINTA = "#11253B"
AZUL = "#1A6FB5"
ACENTO = "#55D6BE"
OCRE = "#B08A3E"
TEXTO = "#17283A"
APAGADO = "#5C6B7A"
REJILLA = "#D5DDE5"
SUAVE = "#F4F7FA"

#: Geometría de `render_flujo`.
CAJA_ANCHO = 186
CAJA_SEPARACION = 46
ALTO_LINEA = 17
MARGEN = 16

#: Geometría de `render_mapa`.
CENTRO_ANCHO = 168
RAMA_ANCHO = 300
RAMA_SEPARACION = 14

_FAMILIA = "system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
_MONO = "ui-monospace, SFMono-Regular, Consolas, monospace"


@dataclass
class Etapa:
    """Una caja del flujo.

    Attributes:
        titulo: el nombre de la etapa.
        lineas: qué pasa dentro. Tres o cuatro como máximo: una caja no es un párrafo.
        nota: una línea bajo la caja, para una cifra o una advertencia.
        color: color del borde y del título. Por defecto, tinta.
    """

    titulo: str
    lineas: list[str] = field(default_factory=list)
    nota: str = ""
    color: str = TINTA


@dataclass
class Flujo:
    """Un flujo de etapas conectadas por flechas."""

    etapas: list[Etapa]
    titulo: str = ""


@dataclass
class Rama:
    """Una rama del mapa mental.

    Attributes:
        titulo: el nombre del bloque.
        hojas: los elementos del bloque, uno por línea.
        color: color de la rama y de su conector.
    """

    titulo: str
    hojas: list[str] = field(default_factory=list)
    color: str = AZUL


@dataclass
class Mapa:
    """Un mapa mental: un centro y sus ramas."""

    centro: str
    ramas: list[Rama]
    subtitulo: str = ""


def _texto(x: float, y: float, contenido: str, *, color: str = TEXTO,
           tamano: float = 12, peso: str = "normal", ancla: str = "start",
           mono: bool = False) -> str:
    familia = _MONO if mono else _FAMILIA
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" fill="{color}" font-size="{tamano}" '
        f'font-weight="{peso}" text-anchor="{ancla}" font-family="{familia}">'
        f"{escape(contenido)}</text>"
    )


def _caja(x: float, y: float, ancho: float, alto: float, *, relleno: str,
          borde: str, grosor: float = 1.6, radio: float = 8) -> str:
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{ancho:.1f}" height="{alto:.1f}" '
        f'rx="{radio}" fill="{relleno}" stroke="{borde}" stroke-width="{grosor}"/>'
    )


def _flecha(x1: float, y: float, x2: float, color: str = APAGADO) -> str:
    """Una flecha horizontal de `x1` a `x2`."""
    punta = (
        f'<path d="M {x2:.1f} {y:.1f} l -7 -4.5 l 0 9 z" fill="{color}"/>'
    )
    return (
        f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2 - 6:.1f}" y2="{y:.1f}" '
        f'stroke="{color}" stroke-width="1.6"/>{punta}'
    )


def _envolver(texto: str, ancho_caracteres: int) -> list[str]:
    """Parte un texto en líneas de hasta `ancho_caracteres`, sin cortar palabras."""
    lineas: list[str] = []
    actual = ""
    for palabra in texto.split():
        if actual and len(actual) + 1 + len(palabra) > ancho_caracteres:
            lineas.append(actual)
            actual = palabra
        else:
            actual = f"{actual} {palabra}".strip()
    if actual:
        lineas.append(actual)
    return lineas


def render_flujo(flujo: Flujo) -> str:
    """El flujo como documento SVG: cajas de izquierda a derecha, con flechas.

    Raises:
        ValueError: si no hay etapas.
    """
    if not flujo.etapas:
        raise ValueError("Un flujo necesita al menos una etapa.")

    envueltas = [
        [linea for texto in etapa.lineas for linea in _envolver(texto, 26)]
        for etapa in flujo.etapas
    ]
    alto_caja = max(
        56 + ALTO_LINEA * len(lineas) for lineas in envueltas
    )
    alto_titulo = 30 if flujo.titulo else 0
    alto_nota = 20 if any(e.nota for e in flujo.etapas) else 0
    ancho = (
        MARGEN * 2 + CAJA_ANCHO * len(flujo.etapas)
        + CAJA_SEPARACION * (len(flujo.etapas) - 1)
    )
    alto = MARGEN * 2 + alto_titulo + alto_caja + alto_nota

    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" '
        f'viewBox="0 0 {ancho} {alto}" role="img">',
        f'<rect width="{ancho}" height="{alto}" fill="#FFFFFF"/>',
    ]
    if flujo.titulo:
        partes.append(
            _texto(MARGEN, MARGEN + 14, flujo.titulo, color=TINTA, tamano=13.5,
                   peso="700")
        )

    y = MARGEN + alto_titulo
    x = MARGEN
    for indice, (etapa, lineas) in enumerate(zip(flujo.etapas, envueltas, strict=True)):
        partes.append(_caja(x, y, CAJA_ANCHO, alto_caja, relleno=SUAVE,
                            borde=etapa.color))
        partes.append(
            _texto(x + 12, y + 24, etapa.titulo, color=etapa.color, tamano=12.5,
                   peso="700")
        )
        for numero, linea in enumerate(lineas):
            partes.append(
                _texto(x + 12, y + 46 + numero * ALTO_LINEA, linea, color=TEXTO,
                       tamano=11.5)
            )
        if etapa.nota:
            partes.append(
                _texto(x + 12, y + alto_caja + 15, etapa.nota, color=APAGADO,
                       tamano=11)
            )
        if indice < len(flujo.etapas) - 1:
            partes.append(
                _flecha(x + CAJA_ANCHO + 8, y + alto_caja / 2,
                        x + CAJA_ANCHO + CAJA_SEPARACION - 8)
            )
        x += CAJA_ANCHO + CAJA_SEPARACION

    partes.append("</svg>")
    return "\n".join(partes) + "\n"


def render_mapa(mapa: Mapa) -> str:
    """El mapa mental como documento SVG: centro a la izquierda, ramas a la derecha.

    Raises:
        ValueError: si no hay ramas.
    """
    if not mapa.ramas:
        raise ValueError("Un mapa necesita al menos una rama.")

    envueltas = [
        [linea for hoja in rama.hojas for linea in _envolver(hoja, 44)]
        for rama in mapa.ramas
    ]
    altos = [34 + ALTO_LINEA * len(lineas) for lineas in envueltas]
    alto_ramas = sum(altos) + RAMA_SEPARACION * (len(mapa.ramas) - 1)

    alto_centro = 54 + (18 if mapa.subtitulo else 0)
    alto = MARGEN * 2 + max(alto_ramas, alto_centro)
    ancho = MARGEN * 2 + CENTRO_ANCHO + 54 + RAMA_ANCHO

    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" '
        f'viewBox="0 0 {ancho} {alto}" role="img">',
        f'<rect width="{ancho}" height="{alto}" fill="#FFFFFF"/>',
    ]

    centro_x = MARGEN
    centro_y = (alto - alto_centro) / 2
    partes.append(
        _caja(centro_x, centro_y, CENTRO_ANCHO, alto_centro, relleno=TINTA,
              borde=TINTA, radio=10)
    )
    for numero, linea in enumerate(_envolver(mapa.centro, 22)):
        partes.append(
            _texto(centro_x + CENTRO_ANCHO / 2, centro_y + 24 + numero * 16, linea,
                   color="#FFFFFF", tamano=13, peso="700", ancla="middle")
        )
    if mapa.subtitulo:
        partes.append(
            _texto(centro_x + CENTRO_ANCHO / 2, centro_y + alto_centro - 12,
                   mapa.subtitulo, color=ACENTO, tamano=11, ancla="middle")
        )

    salida_x = centro_x + CENTRO_ANCHO
    salida_y = centro_y + alto_centro / 2
    rama_x = salida_x + 54
    y = MARGEN + max(0, (alto_centro - alto_ramas) / 2)

    for rama, lineas, alto_rama in zip(mapa.ramas, envueltas, altos, strict=True):
        destino_y = y + alto_rama / 2
        medio = (salida_x + rama_x) / 2
        partes.append(
            f'<path d="M {salida_x:.1f} {salida_y:.1f} '
            f'C {medio:.1f} {salida_y:.1f} {medio:.1f} {destino_y:.1f} '
            f'{rama_x:.1f} {destino_y:.1f}" fill="none" stroke="{rama.color}" '
            f'stroke-width="2" opacity="0.85"/>'
        )
        partes.append(
            _caja(rama_x, y, RAMA_ANCHO, alto_rama, relleno="#FFFFFF",
                  borde=rama.color, grosor=1.6)
        )
        partes.append(
            f'<rect x="{rama_x:.1f}" y="{y:.1f}" width="4" height="{alto_rama:.1f}" '
            f'rx="2" fill="{rama.color}"/>'
        )
        partes.append(
            _texto(rama_x + 14, y + 21, rama.titulo, color=rama.color, tamano=12.5,
                   peso="700")
        )
        for numero, linea in enumerate(lineas):
            partes.append(
                _texto(rama_x + 14, y + 38 + numero * ALTO_LINEA, linea, color=TEXTO,
                       tamano=11.5)
            )
        y += alto_rama + RAMA_SEPARACION

    partes.append("</svg>")
    return "\n".join(partes) + "\n"
