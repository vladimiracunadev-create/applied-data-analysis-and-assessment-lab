"""Salida de consola legible en cualquier sistema operativo.

Por qué existe
    En Windows la consola usa por defecto la página de códigos cp1252, que no puede
    representar caracteres como Σ, ≤ o ×. Imprimir una fórmula del laboratorio en esa
    consola levanta `UnicodeEncodeError` y aborta el comando, aunque el cálculo esté
    correcto. Centralizar el ajuste evita repetirlo en cada script y evita el remedio
    peor: quitar los símbolos de la documentación.

Cómo se usa
    Llame `enable_utf8()` como primera línea del bloque `__main__` de cualquier
    utilidad de consola.
"""

from __future__ import annotations

import sys
from contextlib import suppress


def enable_utf8() -> None:
    """Fuerza UTF-8 en la salida estándar, sustituyendo lo que no se pueda mostrar.

    Usa `errors="replace"` en lugar de `strict`: es preferible que un carácter
    aparezca como «?» a que el comando falle. No altera nada si la salida ya está en
    UTF-8 o si el flujo no admite reconfiguración (por ejemplo, al estar redirigido
    por una herramienta que no expone `reconfigure`).
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        # Si el flujo no admite la reconfiguración, se deja como está: la salida
        # puede perder un símbolo, pero el comando no debe fallar por eso.
        with suppress(ValueError, OSError):
            reconfigure(encoding="utf-8", errors="replace")
