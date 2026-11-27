"""Contraste Polars y visualización Matplotlib del caso carga_nocturna."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[3] if "__file__" in globals() else Path.cwd()
SOURCE = ROOT / "cases" / "carga_nocturna" / "resultados" / "respuesta.csv"


def analizar() -> pl.DataFrame:
    datos = pl.read_csv(SOURCE)
    return datos.filter(pl.col("situacion") != "TOTAL con servicio nocturno").sort("porcentaje", descending=True).select(["situacion", "porcentaje"])


def graficar(resultado: pl.DataFrame, destino: Path) -> Path:
    x = resultado["situacion"].to_list()
    y = resultado["porcentaje"].to_list()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh([str(value) for value in x], y, color="#11253B")
    ax.set_xlabel("Paradas con servicio nocturno (%)")
    ax.set_ylabel("Situación")
    ax.set_xlim(left=0)
    ax.set_title("La mitad de las paradas queda indeterminada por falta de horario")
    ax.grid(axis="y", alpha=0.25)
    fig.text(
        0.01,
        0.01,
        "Fuente: Resultados reproducibles del caso P05/P09 · Período: corte publicado",
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
