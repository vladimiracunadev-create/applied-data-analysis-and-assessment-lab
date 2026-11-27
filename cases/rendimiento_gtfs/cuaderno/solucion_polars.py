"""Contraste Polars y visualización Matplotlib del caso rendimiento_gtfs."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[3] if "__file__" in globals() else Path.cwd()
SOURCE = ROOT / "cases" / "rendimiento_gtfs" / "resultados" / "benchmark.csv"


def analizar() -> pl.DataFrame:
    datos = pl.read_csv(SOURCE)
    return datos.filter(pl.col("segundos").is_not_null()).sort("segundos").select(["metodo", "segundos"])


def graficar(resultado: pl.DataFrame, destino: Path) -> Path:
    x = resultado["metodo"].to_list()
    y = resultado["segundos"].to_list()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh([str(value) for value in x], y, color="#11253B")
    ax.set_xlabel("Tiempo (segundos; menor es mejor)")
    ax.set_ylabel("Método")
    ax.set_xlim(left=0)
    ax.set_title("Tiempo observado para la misma agregación")
    ax.grid(axis="y", alpha=0.25)
    fig.text(
        0.01,
        0.01,
        "Fuente: Benchmark P07; tiempos dependientes del equipo · Período: ejecución de referencia",
        fontsize=8,
        color="#58677A",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(destino, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return destino


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grafico", type=Path)
    args = parser.parse_args()
    resultado = analizar()
    print(resultado)
    if args.grafico:
        print(graficar(resultado, args.grafico))


if __name__ == "__main__":
    main()
