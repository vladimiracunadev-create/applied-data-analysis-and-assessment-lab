"""Visualización con el estándar visual del laboratorio.

Qué hace
    Produce gráficos de barras, líneas e histogramas con título informativo, ejes
    rotulados con unidad, período, nota de fuente y escala honesta (el eje de
    magnitudes empieza en cero salvo declaración explícita).

Por qué existe
    Un gráfico sin unidades, sin período y con eje truncado comunica una conclusión
    distinta de la que respaldan los datos. Centralizar el estilo evita repetir esa
    decisión en cada caso y mantiene la coherencia visual exigida por el estándar.

Cómo se valida
    `tests/test_viz.py` genera los gráficos sobre un backend sin pantalla y verifica
    que el archivo exista, no esté vacío y que el título, los ejes y la nota de
    fuente quedaron escritos en la figura.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # backend sin pantalla: imprescindible en integración continua
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

INK = "#11253B"
ACCENT = "#55D6BE"
TEXT = "#17283A"
MUTED = "#5C6B7A"
GRID = "#D5DDE5"

#: Secuencia categórica accesible: diferencias de luminosidad suficientes para
#: distinguir las series también en escala de grises o con daltonismo.
CATEGORICAL = ("#11253B", "#1A6FB5", "#55D6BE", "#B08A3E", "#7A4E9C", "#2E7D5B")


def apply_style() -> None:
    """Aplica el estilo del laboratorio a la sesión de matplotlib."""
    plt.rcParams.update({
        "figure.figsize": (9, 5),
        "figure.dpi": 130,
        "font.size": 11,
        "text.color": TEXT,
        "axes.edgecolor": GRID,
        "axes.labelcolor": TEXT,
        "axes.titlecolor": INK,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.7,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "legend.frameon": False,
        "savefig.bbox": "tight",
    })


def _finish(ax, title: str, xlabel: str, ylabel: str, period: str, source: str,
            path: str | Path) -> Path:
    if not title.strip():
        raise ValueError("Un gráfico sin título no es publicable.")
    if not ylabel.strip():
        raise ValueError("El eje de magnitudes necesita rótulo con unidad.")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    footer = " · ".join(part for part in (f"Período: {period}" if period else "",
                                          f"Fuente: {source}" if source else "") if part)
    if footer:
        ax.figure.text(0.01, -0.02, footer, fontsize=9, color=MUTED, ha="left")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    ax.figure.savefig(destination)
    plt.close(ax.figure)
    return destination


def bar_chart(
    data: pd.DataFrame,
    category: str,
    value: str,
    path: str | Path,
    title: str,
    ylabel: str,
    xlabel: str = "",
    period: str = "",
    source: str = "Datos sintéticos del laboratorio",
    sort: bool = True,
) -> Path:
    """Gráfico de barras verticales, ordenado de mayor a menor por defecto.

    El eje de magnitudes empieza en cero: truncarlo exagera visualmente las
    diferencias relativas entre categorías.
    """
    apply_style()
    frame = data[[category, value]].dropna()
    if frame.empty:
        raise ValueError("No hay datos que graficar.")
    if sort:
        frame = frame.sort_values(value, ascending=False)
    fig, ax = plt.subplots()
    ax.bar(frame[category].astype(str), frame[value], color=INK, edgecolor="none")
    ax.set_ylim(bottom=0)
    if len(frame) > 6:
        ax.tick_params(axis="x", rotation=45)
        for label in ax.get_xticklabels():
            label.set_horizontalalignment("right")
    return _finish(ax, title, xlabel or category, ylabel, period, source, path)


def line_chart(
    data: pd.DataFrame,
    x: str,
    y: str | Sequence[str],
    path: str | Path,
    title: str,
    ylabel: str,
    xlabel: str = "",
    period: str = "",
    source: str = "Datos sintéticos del laboratorio",
    start_at_zero: bool = True,
) -> Path:
    """Gráfico de líneas para una o varias series.

    Args:
        start_at_zero: déjelo en True salvo que la variación relativa sea el objeto
            del análisis; en ese caso, decláralo en el título o en la nota.
    """
    apply_style()
    columns = [y] if isinstance(y, str) else list(y)
    frame = data[[x, *columns]].dropna(subset=[x]).sort_values(x)
    if frame.empty:
        raise ValueError("No hay datos que graficar.")
    fig, ax = plt.subplots()
    for index, column in enumerate(columns):
        ax.plot(frame[x], frame[column], marker="o", linewidth=2,
                color=CATEGORICAL[index % len(CATEGORICAL)], label=str(column))
    if start_at_zero:
        ax.set_ylim(bottom=0)
    if len(columns) > 1:
        ax.legend()
    return _finish(ax, title, xlabel or x, ylabel, period, source, path)


def histogram(
    values: pd.Series,
    path: str | Path,
    title: str,
    xlabel: str,
    bins: int = 20,
    period: str = "",
    source: str = "Datos sintéticos del laboratorio",
) -> Path:
    """Histograma con línea de mediana señalada.

    Se marca la mediana y no la media porque, ante distribuciones asimétricas
    (duraciones, tiempos de espera), la mediana describe mejor el caso típico.
    """
    apply_style()
    series = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
    if series.empty:
        raise ValueError("No hay datos que graficar.")
    if bins < 1:
        raise ValueError("El número de intervalos debe ser al menos 1.")
    fig, ax = plt.subplots()
    ax.hist(series, bins=bins, color=INK, edgecolor="white")
    median = float(series.median())
    ax.axvline(median, color=ACCENT, linewidth=2.5)
    ax.annotate(f"mediana = {median:,.1f}", xy=(median, ax.get_ylim()[1] * 0.92),
                xytext=(6, 0), textcoords="offset points", color=INK, fontsize=10)
    return _finish(ax, title, xlabel, "Frecuencia (recuento)", period, source, path)
