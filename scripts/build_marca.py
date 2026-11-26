"""Genera la marca del repositorio: el logotipo y la imagen de vista previa social.

Qué escribe

    assets/logo.svg              el logotipo, para la cabecera del README
    assets/social-preview.png    1280 × 640, para Ajustes ▸ General ▸ Social preview

Por qué se genera y no se sube como binario
    Un PNG subido a mano no tiene origen: nadie sabe con qué se hizo ni puede
    cambiarle una palabra. Generado desde este script, la marca es reproducible y usa
    los colores del estándar visual (`lab.viz`), de modo que no hay una segunda paleta
    conviviendo con la del laboratorio.

Sobre la vista previa social
    GitHub **no tiene API pública** para subirla: hay que cargarla una vez a mano en
    Ajustes ▸ General ▸ Social preview. Es la imagen que aparece al compartir el
    enlace en Slack, LinkedIn o WhatsApp, y sin ella se muestra un mosaico genérico.

El logotipo
    Cinco barras de alturas distintas que se ordenan: las cinco planillas heterogéneas
    del primer caso volviéndose una tabla. No es un gráfico de datos reales y no
    pretende serlo; es una marca.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

from lab.console import enable_utf8  # noqa: E402
from lab.viz import ACCENT, CATEGORICAL, INK, MUTED  # noqa: E402

CARPETA = ROOT / "assets"

#: Alturas de las cinco barras del logotipo, en fracción de la altura útil. Van de
#: desordenadas a ordenadas: es la idea del repositorio en cinco trazos.
BARRAS = (0.42, 0.74, 0.30, 0.58, 1.00)


def logo_svg() -> str:
    """El logotipo como SVG, escrito a mano para que pese poco y escale bien."""
    ancho, alto = 128, 128
    radio = 18
    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" '
        f'viewBox="0 0 {ancho} {alto}" role="img" '
        'aria-label="Applied Data Analysis and Assessment Lab">',
        f'<rect width="{ancho}" height="{alto}" rx="{radio}" fill="{INK}"/>',
    ]
    margen, base, util = 22, 100, 62
    paso = (ancho - 2 * margen) / len(BARRAS)
    grosor = paso * 0.56
    for indice, fraccion in enumerate(BARRAS):
        altura = util * fraccion
        x = margen + indice * paso + (paso - grosor) / 2
        color = ACCENT if indice == len(BARRAS) - 1 else "#8FB4D4"
        partes.append(
            f'<rect x="{x:.1f}" y="{base - altura:.1f}" width="{grosor:.1f}" '
            f'height="{altura:.1f}" rx="2.5" fill="{color}"/>'
        )
    # La línea de base: la tabla que resulta.
    partes.append(
        f'<rect x="{margen - 4}" y="{base + 4}" width="{ancho - 2 * margen + 8}" '
        f'height="4" rx="2" fill="{ACCENT}"/>'
    )
    partes.append("</svg>")
    return "\n".join(partes) + "\n"


def social_preview(destino: Path) -> Path:
    """La imagen de vista previa, 1280 × 640, con matplotlib."""
    figura = plt.figure(figsize=(12.8, 6.4), dpi=100)
    figura.patch.set_facecolor(INK)
    eje = figura.add_axes((0, 0, 1, 1))
    eje.set_xlim(0, 1280)
    eje.set_ylim(0, 640)
    eje.axis("off")

    # La marca, arriba a la izquierda.
    eje.add_patch(FancyBboxPatch(
        (76, 452), 108, 108, boxstyle="round,pad=0,rounding_size=16",
        facecolor="#1B3A5C", edgecolor="none",
    ))
    for indice, fraccion in enumerate(BARRAS):
        altura = 54 * fraccion
        color = ACCENT if indice == len(BARRAS) - 1 else "#8FB4D4"
        eje.add_patch(Rectangle(
            (94 + indice * 17.5, 478), 11, altura, facecolor=color, edgecolor="none",
        ))
    eje.add_patch(Rectangle((92, 470), 78, 4, facecolor=ACCENT, edgecolor="none"))

    eje.text(212, 522, "Applied Data Analysis", color="#FFFFFF", fontsize=30,
             fontweight="bold", va="center")
    eje.text(212, 486, "& Assessment Lab", color=ACCENT, fontsize=30,
             fontweight="bold", va="center")

    eje.text(76, 392, "Datos reales, problemas reales,", color="#FFFFFF", fontsize=37,
             fontweight="bold", va="center")
    eje.text(76, 340, "resueltos paso a paso.", color="#FFFFFF", fontsize=37,
             fontweight="bold", va="center")

    eje.text(
        76, 282,
        "Cada caso trae el código de Python con su salida real, la fórmula de Excel "
        "dibujada en su hoja,",
        color="#C7D6E4", fontsize=17, va="center",
    )
    eje.text(
        76, 252,
        "las trampas de hacerlo de la forma obvia, y lo que los datos NO permiten "
        "concluir.",
        color="#C7D6E4", fontsize=17, va="center",
    )

    etiquetas = (
        "Python · Pandas", "Excel · Sheets", "Google Colab",
        "Datos abiertos", "16 casos",
    )
    x = 76
    for indice, etiqueta in enumerate(etiquetas):
        ancho = 34 + len(etiqueta) * 10.4
        eje.add_patch(FancyBboxPatch(
            (x, 140), ancho, 46, boxstyle="round,pad=0,rounding_size=10",
            facecolor="#1B3A5C", edgecolor=CATEGORICAL[indice % len(CATEGORICAL)],
            linewidth=2,
        ))
        eje.text(x + ancho / 2, 163, etiqueta, color="#FFFFFF", fontsize=15,
                 ha="center", va="center")
        x += ancho + 16

    eje.text(76, 74, "Instancia actual: transporte público de Santiago · DTPM",
             color=MUTED, fontsize=16, va="center")
    eje.text(1204, 74, "github.com/vladimiracunadev-create", color=MUTED, fontsize=15,
             ha="right", va="center")

    destino.parent.mkdir(parents=True, exist_ok=True)
    figura.savefig(destino, facecolor=INK, dpi=100)
    plt.close(figura)
    return destino


def main() -> int:
    enable_utf8()
    CARPETA.mkdir(parents=True, exist_ok=True)

    logo = CARPETA / "logo.svg"
    logo.write_text(logo_svg(), encoding="utf-8")
    print(f"escrito {logo.relative_to(ROOT).as_posix()}")

    preview = social_preview(CARPETA / "social-preview.png")
    print(f"escrito {preview.relative_to(ROOT).as_posix()}  (1280 × 640)")
    print(
        "\nLa vista previa social se carga a mano una vez: GitHub no tiene API para\n"
        "ella. Ajustes ▸ General ▸ Social preview ▸ Edit ▸ Upload an image."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
