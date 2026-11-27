"""Enriquece todos los cuadernos con navegación, motores y gráficos comparables.

La configuración vive en un solo lugar para impedir tres derivas: cuadernos sin una
implementación prometida, navegación que salta problemas y gráficos decorativos que no
responden la pregunta del caso. Cada contraste parte de una tabla de resultados
versionada, recalcula el indicador principal con Polars o R y puede producir la misma
visualización con Matplotlib o ggplot2.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import pandas as pd

from lab.cuaderno import Cuaderno, Implementacion
from lab.viz import bar_chart, horizontal_bar_chart, line_chart

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class CaseSpec:
    """Contrato del indicador y del gráfico comparable de un cuaderno."""

    csv: str
    x: str
    y: str
    chart: str
    title: str
    xlabel: str
    ylabel: str
    period: str
    source: str
    scope: str
    polars_query: str
    r_query: str
    figure_step: int


SPECS: dict[str, CaseSpec] = {
    "bip_lugares_carga": CaseSpec(
        "por_comuna.csv", "comuna", "total", "barh",
        "Lugares de carga en las diez comunas con mayor oferta",
        "Lugares de carga (recuento)", "Comuna", "corte publicado",
        "Resultados reproducibles del caso P01", "ranking comunal y total por comuna",
        '.sort("total", descending=True).head(10).select(["comuna", "total"])',
        'head(datos[order(-datos$total), c("comuna", "total")], 10)', 11,
    ),
    "correspondencia_metro": CaseSpec(
        "detectores.csv", "detector", "hallazgos", "barh",
        "Cada detector encuentra un punto ciego distinto",
        "Hallazgos (recuento)", "Detector", "corte publicado",
        "Resultados reproducibles del caso P03/P10", "hallazgos por detector independiente",
        '.sort("hallazgos", descending=True).select(["detector", "hallazgos"])',
        'datos[order(-datos$hallazgos), c("detector", "hallazgos")]', 4,
    ),
    "carga_nocturna": CaseSpec(
        "respuesta.csv", "situacion", "porcentaje", "barh",
        "La mitad de las paradas queda indeterminada por falta de horario",
        "Paradas con servicio nocturno (%)", "Situación", "corte publicado",
        "Resultados reproducibles del caso P05/P09", "distribución de la respuesta nocturna",
        '.filter(pl.col("situacion") != "TOTAL con servicio nocturno").sort("porcentaje", descending=True).select(["situacion", "porcentaje"])',
        'subset(datos, situacion != "TOTAL con servicio nocturno", select = c("situacion", "porcentaje"))[order(-subset(datos, situacion != "TOTAL con servicio nocturno")$porcentaje), ]', 6,
    ),
    "gtfs_red_movilidad": CaseSpec(
        "salidas_por_hora.csv", "hora_reloj", "salidas", "line",
        "Oferta programada por hora del día",
        "Hora del reloj", "Salidas programadas (recuento)", "publicación GTFS analizada",
        "Resultados reproducibles del caso P06", "perfil horario agregado de salidas",
        '.group_by("hora_reloj").agg(pl.col("salidas").sum()).sort("hora_reloj")',
        'aggregate(salidas ~ hora_reloj, datos, sum)', 9,
    ),
    "rendimiento_gtfs": CaseSpec(
        "benchmark.csv", "metodo", "segundos", "barh",
        "Tiempo observado para la misma agregación",
        "Tiempo (segundos; menor es mejor)", "Método", "ejecución de referencia",
        "Benchmark P07; tiempos dependientes del equipo", "tiempo por implementación ejecutada",
        '.filter(pl.col("segundos").is_not_null()).sort("segundos").select(["metodo", "segundos"])',
        'subset(datos, !is.na(segundos), select = c("metodo", "segundos"))[order(subset(datos, !is.na(segundos))$segundos), ]', 7,
    ),
    "cobertura_de_carga": CaseSpec(
        "cobertura_por_umbral.csv", "umbral_m", "cobertura_pct", "line",
        "La cobertura depende del umbral declarado",
        "Umbral de cercanía (m)", "Paradas cubiertas (%)", "corte publicado",
        "Resultados reproducibles del caso P08", "curva de sensibilidad al umbral",
        '.sort("umbral_m").select(["umbral_m", "cobertura_pct"])',
        'datos[order(datos$umbral_m), c("umbral_m", "cobertura_pct")]', 5,
    ),
    "calendario_medicion": CaseSpec(
        "comparacion_anios.csv", "anio", "dias_medibles", "line",
        "El denominador cambia con el calendario anual",
        "Año", "Días medibles (recuento)", "2024–2027",
        "Resultados reproducibles del caso P11", "días medibles por año",
        '.sort("anio").select(["anio", "dias_medibles"])',
        'datos[order(datos$anio), c("anio", "dias_medibles")]', 7,
    ),
    "frecuencia_programada": CaseSpec(
        "distribucion.csv", "estadistico", "intervalo_min", "bar",
        "La distribución revela más que un promedio",
        "Estadístico", "Intervalo entre salidas (minutos)", "publicación GTFS analizada",
        "Resultados reproducibles del caso P12/P13", "percentiles del intervalo programado",
        '.select(["estadistico", "intervalo_min"])',
        'datos[, c("estadistico", "intervalo_min")]', 3,
    ),
    "evolucion_gtfs": CaseSpec(
        "oferta_total.csv", "publicacion", "salidas", "line",
        "La oferta programada cae en la publicación más reciente",
        "Publicación GTFS", "Salidas laborales (recuento)", "2024–2026",
        "Resultados reproducibles del caso P14/P15", "evolución de salidas comparables",
        '.sort("publicacion").select(["publicacion", "salidas"])',
        'datos[order(datos$publicacion), c("publicacion", "salidas")]', 6,
    ),
    "informe_decision_carga": CaseSpec(
        "resumen.csv", "indicador", "valor", "barh",
        "Dos supuestos espaciales producen coberturas distintas",
        "Cobertura de paradas (%)", "Indicador", "corte publicado",
        "Resultados reproducibles del caso P16", "indicadores porcentuales de cobertura",
        '.filter(pl.col("unidad") == "%").select(["indicador", "valor"])',
        'subset(datos, unidad == "%", select = c("indicador", "valor"))', 1,
    ),
}


NAVIGATION: tuple[tuple[str, str], ...] = (
    ("bip_lugares_carga", "P01/P02/P04 · Consolidación y calidad"),
    ("correspondencia_metro", "P03/P10 · Coordenadas y correspondencia"),
    ("carga_nocturna", "P05/P09 · Horarios y cobertura nocturna"),
    ("gtfs_red_movilidad", "P06 · Expediciones por hora"),
    ("rendimiento_gtfs", "P07 · Rendimiento GTFS"),
    ("cobertura_de_carga", "P08 · Cobertura espacial"),
    ("calendario_medicion", "P11 · Calendario de medición"),
    ("frecuencia_programada", "P12/P13 · Frecuencia programada"),
    ("evolucion_gtfs", "P14/P15 · Evolución GTFS"),
    ("informe_decision_carga", "P16 · Informe de decisión"),
)


def _polars_code(slug: str, spec: CaseSpec) -> str:
    if spec.chart == "line":
        plot_body = f'''ax.plot(x, y, marker="o", linewidth=2, color="#11253B")
    ax.set_xlabel("{spec.xlabel}")
    ax.set_ylabel("{spec.ylabel}")
    ax.set_ylim(bottom=0)'''
    elif spec.chart == "barh":
        plot_body = f'''ax.barh([str(value) for value in x], y, color="#11253B")
    ax.set_xlabel("{spec.xlabel}")
    ax.set_ylabel("{spec.ylabel}")
    ax.set_xlim(left=0)'''
    else:
        plot_body = f'''ax.bar([str(value) for value in x], y, color="#11253B")
    ax.set_xlabel("{spec.xlabel}")
    ax.set_ylabel("{spec.ylabel}")
    ax.set_ylim(bottom=0)'''
    return f'''"""Contraste Polars y visualización Matplotlib del caso {slug}."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[3] if "__file__" in globals() else Path.cwd()
SOURCE = ROOT / "cases" / "{slug}" / "resultados" / "{spec.csv}"


def analizar() -> pl.DataFrame:
    datos = pl.read_csv(SOURCE)
    return datos{spec.polars_query}


def graficar(resultado: pl.DataFrame, destino: Path) -> Path:
    x = resultado["{spec.x}"].to_list()
    y = resultado["{spec.y}"].to_list()
    fig, ax = plt.subplots(figsize=(9, 5))
    {plot_body}
    ax.set_title("{spec.title}")
    ax.grid(axis="y", alpha=0.25)
    fig.text(
        0.01,
        0.01,
        "Fuente: {spec.source} · Período: {spec.period}",
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
'''


def _r_code(slug: str, spec: CaseSpec) -> str:
    chart_layer = (
        'ggplot2::geom_line(ggplot2::aes(group = 1), linewidth = 1, colour = "#11253B") +\n'
        '    ggplot2::geom_point(size = 2.5, colour = "#55D6BE")'
        if spec.chart == "line"
        else (
            'ggplot2::geom_col(fill = "#11253B") +\n    ggplot2::coord_flip()'
            if spec.chart == "barh"
            else 'ggplot2::geom_col(fill = "#11253B")'
        )
    )
    return f'''#!/usr/bin/env Rscript
# Contraste R + ggplot2 del caso {slug}.
script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
script_path <- if (length(script_arg)) sub("^--file=", "", script_arg[1]) else "cuaderno/solucion.R"
root <- normalizePath(file.path(dirname(script_path), "../../.."), mustWork = TRUE)
source_csv <- file.path(root, "cases", "{slug}", "resultados", "{spec.csv}")

datos <- read.csv(source_csv, check.names = FALSE, fileEncoding = "UTF-8")
resultado <- {spec.r_query}
print(resultado, row.names = FALSE)

args <- commandArgs(trailingOnly = TRUE)
plot_pos <- match("--grafico", args)
if (!is.na(plot_pos)) {{
  if (plot_pos == length(args)) stop("--grafico necesita una ruta de salida")
  if (!requireNamespace("ggplot2", quietly = TRUE)) {{
    stop("Instale ggplot2 para generar el gráfico: install.packages('ggplot2')")
  }}
  destino <- args[plot_pos + 1]
  grafico <- ggplot2::ggplot(
    resultado,
    ggplot2::aes(x = .data[["{spec.x}"]], y = .data[["{spec.y}"]])
  ) +
    {chart_layer} +
    ggplot2::labs(
      title = "{spec.title}",
      x = "{spec.xlabel}", y = "{spec.ylabel}",
      caption = "Fuente: {spec.source} · Período: {spec.period}"
    ) +
    ggplot2::theme_minimal(base_size = 11)
  ggplot2::ggsave(destino, grafico, width = 9, height = 5, dpi = 150)
  cat(destino, "\\n")
}}
'''


def _implementaciones(slug: str, spec: CaseSpec) -> tuple[Implementacion, ...]:
    return (
        Implementacion(
            motor="Polars + Matplotlib",
            lenguaje="python",
            archivo="solucion_polars.py",
            comando=f"uv run --extra polars python cases/{slug}/cuaderno/solucion_polars.py",
            alcance=spec.scope,
            codigo=_polars_code(slug, spec),
        ),
        Implementacion(
            motor="R + ggplot2",
            lenguaje="r",
            archivo="solucion.R",
            comando=f"Rscript cases/{slug}/cuaderno/solucion.R",
            alcance=spec.scope,
            codigo=_r_code(slug, spec),
        ),
    )


def _navigation(slug: str) -> tuple[tuple[str, str] | None, tuple[str, str] | None]:
    slugs = [item[0] for item in NAVIGATION]
    index = slugs.index(slug)

    def link(position: int) -> tuple[str, str]:
        target, label = NAVIGATION[position]
        return label, f"../{target}/CUADERNO.md"

    previous = link(index - 1) if index > 0 else None
    following = link(index + 1) if index + 1 < len(NAVIGATION) else None
    return previous, following


def enriquecer_cuaderno(slug: str, cuaderno: Cuaderno) -> Cuaderno:
    """Aplica a un cuaderno el contrato común sin ocultar la configuración del caso."""
    spec = SPECS[slug]
    previous, following = _navigation(slug)
    cuaderno.anterior = previous
    cuaderno.siguiente = following
    cuaderno.implementaciones = _implementaciones(slug, spec)
    cuaderno.contexto["render_case_chart"] = render_case_chart

    # Los dos primeros cuadernos que ya tenían gráficos conservan sus figuras y
    # reciben además la visualización comparable solo si el paso elegido carece de una.
    index = spec.figure_step - 1
    selected = cuaderno.pasos[index]
    if not selected.figura:
        cuaderno.pasos[index] = replace(
            selected,
            figura=f"render_case_chart('{slug}', SVG_DESTINO)",
            pie_figura=(
                f"{spec.title}. Ejes con unidad, período y fuente; el código "
                "Polars y R genera la misma vista."
            ),
        )
    return cuaderno


def _prepare_frame(slug: str, frame: pd.DataFrame) -> pd.DataFrame:
    if slug == "bip_lugares_carga":
        return frame.nlargest(10, "total")[["comuna", "total"]]
    if slug == "correspondencia_metro":
        return frame.sort_values("hallazgos", ascending=False)[["detector", "hallazgos"]]
    if slug == "carga_nocturna":
        return frame.loc[frame.situacion != "TOTAL con servicio nocturno", ["situacion", "porcentaje"]]
    if slug == "gtfs_red_movilidad":
        return frame.groupby("hora_reloj", as_index=False).salidas.sum()
    if slug == "rendimiento_gtfs":
        return frame.dropna(subset=["segundos"]).sort_values("segundos")[["metodo", "segundos"]]
    if slug == "cobertura_de_carga":
        return frame.sort_values("umbral_m")[["umbral_m", "cobertura_pct"]]
    if slug == "calendario_medicion":
        return frame.sort_values("anio")[["anio", "dias_medibles"]]
    if slug == "frecuencia_programada":
        return frame[["estadistico", "intervalo_min"]]
    if slug == "evolucion_gtfs":
        return frame.sort_values("publicacion")[["publicacion", "salidas"]]
    if slug == "informe_decision_carga":
        return frame.loc[frame.unidad == "%", ["indicador", "valor"]]
    raise KeyError(slug)


def render_case_chart(slug: str, destination: str | Path) -> Path:
    """Genera el gráfico estadístico visible de un caso con el estilo del laboratorio."""
    spec = SPECS[slug]
    source = ROOT / "cases" / slug / "resultados" / spec.csv
    frame = _prepare_frame(slug, pd.read_csv(source))
    common = {
        "data": frame,
        "path": destination,
        "title": spec.title,
        "period": spec.period,
        "source": spec.source,
    }
    if spec.chart == "line":
        return line_chart(
            x=spec.x, y=spec.y, xlabel=spec.xlabel, ylabel=spec.ylabel,
            **common,
        )
    if spec.chart == "barh":
        return horizontal_bar_chart(
            category=spec.x, value=spec.y, xlabel=spec.xlabel, ylabel=spec.ylabel,
            **common,
        )
    return bar_chart(
        category=spec.x, value=spec.y, xlabel=spec.xlabel, ylabel=spec.ylabel,
        sort=False, **common,
    )
