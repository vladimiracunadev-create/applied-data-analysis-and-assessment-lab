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
        "Resultados reproducibles de P01/P02/P04", "ranking comunal y total por comuna",
        '.sort("total", descending=True).head(10).select(["comuna", "total"])',
        'datos |> dplyr::arrange(dplyr::desc(.data$total)) |> dplyr::slice_head(n = 10) |> dplyr::select(.data$comuna, .data$total)', 13,
    ),
    "correspondencia_metro": CaseSpec(
        "detectores.csv", "detector", "hallazgos", "barh",
        "Cada detector encuentra un punto ciego distinto",
        "Hallazgos (recuento)", "Detector", "corte publicado",
        "Resultados reproducibles del caso P03/P10", "hallazgos por detector independiente",
        '.sort("hallazgos", descending=True).select(["detector", "hallazgos"])',
        'datos |> dplyr::arrange(dplyr::desc(.data$hallazgos)) |> dplyr::select(.data$detector, .data$hallazgos)', 4,
    ),
    "carga_nocturna": CaseSpec(
        "respuesta.csv", "situacion", "porcentaje", "barh",
        "La mitad de las paradas queda indeterminada por falta de horario",
        "Paradas con servicio nocturno (%)", "Situación", "corte publicado",
        "Resultados reproducibles del caso P05/P09", "distribución de la respuesta nocturna",
        '.filter(pl.col("situacion") != "TOTAL con servicio nocturno").sort("porcentaje", descending=True).select(["situacion", "porcentaje"])',
        'datos |> dplyr::filter(.data$situacion != "TOTAL con servicio nocturno") |> dplyr::arrange(dplyr::desc(.data$porcentaje)) |> dplyr::select(.data$situacion, .data$porcentaje)', 6,
    ),
    "gtfs_red_movilidad": CaseSpec(
        "salidas_por_hora.csv", "hora_reloj", "salidas", "line",
        "Oferta programada por hora del día",
        "Hora del reloj", "Salidas programadas (recuento)", "publicación GTFS analizada",
        "Resultados reproducibles del caso P06", "perfil horario agregado de salidas",
        '.group_by("hora_reloj").agg(pl.col("salidas").sum()).sort("hora_reloj")',
        'datos |> dplyr::group_by(.data$hora_reloj) |> dplyr::summarise(salidas = sum(.data$salidas), .groups = "drop") |> dplyr::arrange(.data$hora_reloj)', 9,
    ),
    "rendimiento_gtfs": CaseSpec(
        "benchmark.csv", "metodo", "segundos", "barh",
        "Tiempo observado para la misma agregación",
        "Tiempo (segundos; menor es mejor)", "Método", "ejecución de referencia",
        "Benchmark P07; tiempos dependientes del equipo", "tiempo por implementación ejecutada",
        '.filter(pl.col("segundos").is_not_null()).sort("segundos").select(["metodo", "segundos"])',
        'datos |> dplyr::filter(!is.na(.data$segundos)) |> dplyr::arrange(.data$segundos) |> dplyr::select(.data$metodo, .data$segundos)', 7,
    ),
    "cobertura_de_carga": CaseSpec(
        "cobertura_por_umbral.csv", "umbral_m", "cobertura_pct", "line",
        "La cobertura depende del umbral declarado",
        "Umbral de cercanía (m)", "Paradas cubiertas (%)", "corte publicado",
        "Resultados reproducibles del caso P08", "curva de sensibilidad al umbral",
        '.sort("umbral_m").select(["umbral_m", "cobertura_pct"])',
        'datos |> dplyr::arrange(.data$umbral_m) |> dplyr::select(.data$umbral_m, .data$cobertura_pct)', 5,
    ),
    "calendario_medicion": CaseSpec(
        "comparacion_anios.csv", "anio", "dias_medibles", "line",
        "El denominador cambia con el calendario anual",
        "Año", "Días medibles (recuento)", "2024–2027",
        "Resultados reproducibles del caso P11", "días medibles por año",
        '.sort("anio").select(["anio", "dias_medibles"])',
        'datos |> dplyr::arrange(.data$anio) |> dplyr::select(.data$anio, .data$dias_medibles)', 7,
    ),
    "frecuencia_programada": CaseSpec(
        "distribucion.csv", "estadistico", "intervalo_min", "bar",
        "La distribución revela más que un promedio",
        "Estadístico", "Intervalo entre salidas (minutos)", "publicación GTFS analizada",
        "Resultados reproducibles del caso P12/P13", "percentiles del intervalo programado",
        '.with_columns(pl.col("estadistico").replace_strict({"mínimo": 0, "P10": 1, "P25": 2, "P50": 3, "media": 4, "P75": 5, "P90": 6, "P95": 7, "máximo": 8}).alias("_orden")).sort("_orden").select(["estadistico", "intervalo_min"])',
        'datos |> dplyr::mutate(.orden = match(.data$estadistico, c("mínimo", "P10", "P25", "P50", "media", "P75", "P90", "P95", "máximo"))) |> dplyr::arrange(.data$.orden) |> dplyr::select(.data$estadistico, .data$intervalo_min)', 3,
    ),
    "evolucion_gtfs": CaseSpec(
        "oferta_total.csv", "publicacion", "salidas", "line",
        "La oferta programada cae en la publicación más reciente",
        "Publicación GTFS", "Salidas laborales (recuento)", "2024–2026",
        "Resultados reproducibles del caso P14/P15", "evolución de salidas comparables",
        '.sort("publicacion").select(["publicacion", "salidas"])',
        'datos |> dplyr::arrange(.data$publicacion) |> dplyr::select(.data$publicacion, .data$salidas)', 6,
    ),
    "informe_decision_carga": CaseSpec(
        "resumen.csv", "indicador", "valor", "barh",
        "Dos supuestos espaciales producen coberturas distintas",
        "Cobertura de paradas (%)", "Indicador", "corte publicado",
        "Resultados reproducibles del caso P16", "indicadores porcentuales de cobertura",
        '.filter(pl.col("unidad") == "%").select(["indicador", "valor"])',
        'datos |> dplyr::filter(.data$unidad == "%") |> dplyr::select(.data$indicador, .data$valor)', 1,
    ),
    "gobernanza_datos_dtpm": CaseSpec(
        "riesgo_por_activo.csv", "activo_id", "puntaje_riesgo", "barh",
        "Prioridad documental de los activos de la instancia DTPM",
        "Puntaje de riesgo documental", "Activo", "corte documental 2026-11-28",
        "Catálogo pedagógico P17; no es un registro oficial DTPM",
        "ranking de brechas ponderadas por criticidad",
        '.sort(["puntaje_riesgo", "activo_id"], descending=[True, False]).select(["activo_id", "puntaje_riesgo"])',
        'datos |> dplyr::arrange(dplyr::desc(.data$puntaje_riesgo), .data$activo_id) |> dplyr::select(.data$activo_id, .data$puntaje_riesgo)', 7,
    ),
    "etl_gtfs_automatizado": CaseSpec(
        "volumen_por_publicacion.csv", "publicacion", "mb_stop_times", "bar",
        "Volumen de stop_times por publicación GTFS",
        "Publicación", "Tamaño de stop_times (MB decimales)", "publicaciones 2024–2026",
        "Inventario reproducible P14/P15", "volumen por corte bajo el mismo contrato",
        '.sort("publicacion").select(["publicacion", "mb_stop_times"])',
        'datos |> dplyr::arrange(.data$publicacion) |> dplyr::select(.data$publicacion, .data$mb_stop_times)', 6,
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
    ("gobernanza_datos_dtpm", "P17 · Gobernanza de datos DTPM"),
    ("etl_gtfs_automatizado", "P18 · ETL histórico GTFS"),
)


# Objetivo, fórmula, interpretación y error frecuente del indicador comparable. Esta
# prosa es deliberadamente específica: explica el razonamiento que el código materializa
# y no vuelve a narrar cada instrucción con otras palabras.
PEDAGOGY: dict[str, tuple[str, str, str, str]] = {
    "bip_lugares_carga": (
        "Ordenar la oferta comunal y conservar las diez comunas con mayor número de lugares.",
        "Para cada comuna c: n_c = Σ 1(fila pertenece a c). El ranking usa n_c descendente; no suma códigos porque el código no es una clave (P02).",
        "Una barra representa lugares publicados, no demanda ni cobertura territorial. La normalización previa evita partir una comuna en dos etiquetas (P04).",
        "Contar códigos distintos subestima filas repetidas; agrupar el texto crudo puede separar variantes ortográficas.",
    ),
    "correspondencia_metro": (
        "Comparar cuántos hallazgos aporta cada detector independiente de coordenadas.",
        "hallazgos_d = Σ 1(detector d marca la fila). Los detectores no son mutuamente excluyentes, por lo que sus barras no deben sumarse como un total.",
        "La diferencia entre barras muestra puntos ciegos del control, no una competencia entre algoritmos.",
        "Sumar detectores duplica estaciones marcadas por más de una regla; use el identificador de estación para una unión.",
    ),
    "carga_nocturna": (
        "Mostrar la distribución de respuestas verificables e indeterminadas sobre servicio nocturno.",
        "porcentaje_s = 100 × n_s / N. Se excluye la fila TOTAL porque es un resumen, no una categoría adicional.",
        "La categoría indeterminada es evidencia de falta de datos; no equivale a ausencia de servicio.",
        "Convertir los faltantes en 'no' produce una cobertura falsamente baja y borra la incertidumbre.",
    ),
    "gtfs_red_movilidad": (
        "Agregar salidas programadas por hora de reloj para observar el perfil diario.",
        "salidas_h = Σ salidas_i para toda fila cuya hora_reloj = h. Las horas GTFS mayores que 24 se normalizan según día de servicio antes de este agregado.",
        "La curva representa oferta programada, no viajes efectivamente realizados ni pasajeros.",
        "Truncar 25:30 como hora inválida elimina servicio posterior a medianoche; GTFS permite horas mayores que 24.",
    ),
    "rendimiento_gtfs": (
        "Comparar el tiempo observado de métodos que resuelven la misma agregación.",
        "t = fin - inicio en segundos. Sólo se comparan filas con medición; menor es mejor bajo el mismo archivo y equipo.",
        "Una diferencia observada describe esta ejecución de referencia y no una ley universal de rendimiento.",
        "Comparar ejecuciones con caché, hardware o resultados distintos invalida el benchmark.",
    ),
    "cobertura_de_carga": (
        "Medir cómo cambia la cobertura al variar el umbral de cercanía.",
        "cobertura(u) = 100 × #{paradas con distancia ≤ u} / #{paradas evaluables}. El denominador se mantiene fijo entre umbrales.",
        "La pendiente revela sensibilidad a una decisión metodológica; no demuestra demanda de nuevos puntos.",
        "Cambiar simultáneamente umbral y denominador hace incomparables los puntos de la curva.",
    ),
    "calendario_medicion": (
        "Comparar el denominador de días medibles entre años bajo las mismas reglas.",
        "días_medibles_a = Σ 1(día laboral y no excluido por ninguna regla) para el año a.",
        "Las diferencias anuales pueden venir del calendario, aunque la metodología no cambie.",
        "Reutilizar la lista de feriados de un año en otro altera el denominador silenciosamente.",
    ),
    "frecuencia_programada": (
        "Contrastar estadísticos de la distribución de intervalos programados.",
        "El percentil p con interpolación lineal se ubica en h=(n−1)p; se interpola entre floor(h) y ceil(h). La convención debe declararse.",
        "La mediana y el P90 muestran asimetría que el promedio puede ocultar.",
        "Comparar percentiles calculados con métodos de interpolación distintos puede producir discrepancias legítimas.",
    ),
    "evolucion_gtfs": (
        "Comparar salidas laborales entre publicaciones GTFS equivalentes.",
        "oferta_p = Σ salidas_i de la publicación p después de aplicar el mismo filtro de día comparable.",
        "Una caída en oferta programada es una diferencia de programación, no evidencia directa de ejecución o demanda.",
        "Comparar archivos con ventanas temporales o reglas de servicio distintas confunde versión con estacionalidad.",
    ),
    "informe_decision_carga": (
        "Contrastar los indicadores porcentuales que sostienen la recomendación final.",
        "cobertura = 100 × paradas cubiertas / paradas evaluables. Se filtra unidad='%' para no mezclar magnitudes incompatibles.",
        "La brecha entre supuestos espaciales cuantifica sensibilidad y debe acompañar cualquier decisión.",
        "Poner porcentajes y recuentos en el mismo eje produce una comparación visual sin unidad común.",
    ),
    "gobernanza_datos_dtpm": (
        "Ordenar los activos según brechas documentales ponderadas por criticidad.",
        "riesgo = (3·licencia + 2·esquema + 2·actualización + 2·responsable + retención) × peso_criticidad; cada brecha vale 0 o 1.",
        "Una barra alta prioriza una aclaración; no demuestra mala calidad del dato ni estima la probabilidad de un incidente.",
        "Imputar un campo no declarado como conforme reduce artificialmente el puntaje y fabrica evidencia.",
    ),
    "etl_gtfs_automatizado": (
        "Comparar el volumen de stop_times entre cortes procesados con el mismo contrato.",
        "MB = bytes_stop_times / 1.000.000; se conserva una fila por publicación y se ordena por fecha.",
        "El cambio de volumen sirve como señal para inspección, pero no demuestra un cambio de servicio ni su causa.",
        "Comparar el ZIP completo de un corte con stop_times de otro mezcla unidades y vuelve engañosa la gráfica.",
    ),
}

PANDAS_QUERIES: dict[str, str] = {
    "bip_lugares_carga": 'datos.nlargest(10, "total")[["comuna", "total"]]',
    "correspondencia_metro": 'datos.sort_values("hallazgos", ascending=False)[["detector", "hallazgos"]]',
    "carga_nocturna": 'datos.loc[datos["situacion"] != "TOTAL con servicio nocturno", ["situacion", "porcentaje"]].sort_values("porcentaje", ascending=False)',
    "gtfs_red_movilidad": 'datos.groupby("hora_reloj", as_index=False)["salidas"].sum().sort_values("hora_reloj")',
    "rendimiento_gtfs": 'datos.dropna(subset=["segundos"]).sort_values("segundos")[["metodo", "segundos"]]',
    "cobertura_de_carga": 'datos.sort_values("umbral_m")[["umbral_m", "cobertura_pct"]]',
    "calendario_medicion": 'datos.sort_values("anio")[["anio", "dias_medibles"]]',
    "frecuencia_programada": 'datos.assign(_orden=datos["estadistico"].map({"mínimo": 0, "P10": 1, "P25": 2, "P50": 3, "media": 4, "P75": 5, "P90": 6, "P95": 7, "máximo": 8})).sort_values("_orden")[["estadistico", "intervalo_min"]]',
    "evolucion_gtfs": 'datos.sort_values("publicacion")[["publicacion", "salidas"]]',
    "informe_decision_carga": 'datos.loc[datos["unidad"] == "%", ["indicador", "valor"]]',
    "gobernanza_datos_dtpm": 'datos.sort_values(["puntaje_riesgo", "activo_id"], ascending=[False, True])[["activo_id", "puntaje_riesgo"]]',
    "etl_gtfs_automatizado": 'datos.sort_values("publicacion")[["publicacion", "mb_stop_times"]]',
}


def _pandas_code(slug: str, spec: CaseSpec) -> str:
    """Implementación Pandas explícita del mismo contrato usado por Polars y R."""
    if spec.chart == "line":
        plot_body = f'''ax.plot(x, y, marker="o", linewidth=2, color="#11253B")
    ax.set_xlabel("{spec.xlabel}")
    ax.set_ylabel("{spec.ylabel}")
    ax.set_ylim(bottom=0)'''
    elif spec.chart == "barh":
        plot_body = f'''ax.barh([str(value) for value in x], y, color="#11253B")
    ax.invert_yaxis()  # el primer puesto del ranking queda arriba, como se lee una tabla
    ax.set_xlabel("{spec.xlabel}")
    ax.set_ylabel("{spec.ylabel}")
    ax.set_xlim(left=0)'''
    else:
        plot_body = f'''ax.bar([str(value) for value in x], y, color="#11253B")
    ax.set_xlabel("{spec.xlabel}")
    ax.set_ylabel("{spec.ylabel}")
    ax.set_ylim(bottom=0)'''
    return f'''"""Laboratorio comparable Pandas + Matplotlib del caso {slug}.

Lee el mismo contrato CSV que las versiones Polars y R. La resolución completa del
caso permanece en ``solution.py`` y en los pasos del cuaderno; este archivo aísla el
indicador central para que la comparación entre motores sea controlada.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Buscar la raíz desde el propio archivo evita rutas C:\\... específicas del autor y
# funciona igual después de clonar el repositorio en Linux, Windows o Google Colab.
ROOT = Path(__file__).resolve().parents[3] if "__file__" in globals() else Path.cwd()
SOURCE = ROOT / "cases" / "{slug}" / "resultados" / "{spec.csv}"
REQUIRED = {{"{spec.x}", "{spec.y}"}}


def analizar() -> pd.DataFrame:
    """Carga, valida y transforma el indicador; no modifica el archivo de entrada."""
    datos = pd.read_csv(SOURCE)
    faltantes = REQUIRED.difference(datos.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas en {{SOURCE}}: {{sorted(faltantes)}}")
    # La expresión conserva explícitos filtro, agrupación, orden y selección para que
    # el estudiante pueda alinearlos con las expresiones de Polars y dplyr.
    resultado = {PANDAS_QUERIES[slug]}
    return resultado.reset_index(drop=True)


def graficar(resultado: pd.DataFrame, destino: Path) -> Path:
    """Representa exactamente las columnas comparadas y explicita sus unidades."""
    x = resultado["{spec.x}"].tolist()
    y = resultado["{spec.y}"].tolist()
    fig, ax = plt.subplots(figsize=(9, 5))
    {plot_body}
    ax.set_title("{spec.title}")
    ax.grid(axis="y", alpha=0.25)
    fig.text(0.01, 0.01, "Fuente: {spec.source} · Período: {spec.period}", fontsize=8, color="#58677A")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(destino, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return destino


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, help="CSV normalizado para comparar motores")
    parser.add_argument("--grafico", type=Path, help="PNG de la visualización comparable")
    args = parser.parse_args()
    resultado = analizar()
    print(resultado.to_string(index=False))
    if args.salida:
        resultado.to_csv(args.salida, index=False)
    if args.grafico:
        print(graficar(resultado, args.grafico))


if __name__ == "__main__":
    main()
'''


def _polars_code(slug: str, spec: CaseSpec) -> str:
    if spec.chart == "line":
        plot_body = f'''ax.plot(x, y, marker="o", linewidth=2, color="#11253B")
    ax.set_xlabel("{spec.xlabel}")
    ax.set_ylabel("{spec.ylabel}")
    ax.set_ylim(bottom=0)'''
    elif spec.chart == "barh":
        plot_body = f'''ax.barh([str(value) for value in x], y, color="#11253B")
    ax.invert_yaxis()  # el primer puesto del ranking queda arriba, como se lee una tabla
    ax.set_xlabel("{spec.xlabel}")
    ax.set_ylabel("{spec.ylabel}")
    ax.set_xlim(left=0)'''
    else:
        plot_body = f'''ax.bar([str(value) for value in x], y, color="#11253B")
    ax.set_xlabel("{spec.xlabel}")
    ax.set_ylabel("{spec.ylabel}")
    ax.set_ylim(bottom=0)'''
    return f'''"""Laboratorio comparable Polars + Matplotlib del caso {slug}.

Usa el mismo CSV, columnas, reglas y escala que Pandas y R. Polars expresa las
transformaciones como un plan de expresiones columnares; esa diferencia de método es
el objeto de aprendizaje, no una razón para cambiar la pregunta.
"""
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
REQUIRED = {{"{spec.x}", "{spec.y}"}}


def analizar() -> pl.DataFrame:
    """Carga y valida antes de transformar para producir un error explicativo."""
    datos = pl.read_csv(SOURCE)
    faltantes = REQUIRED.difference(datos.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas en {{SOURCE}}: {{sorted(faltantes)}}")
    # select al final fija el contrato de salida y evita comparar columnas auxiliares.
    return datos{spec.polars_query}


def graficar(resultado: pl.DataFrame, destino: Path) -> Path:
    """Convierte sólo las series del gráfico; el análisis permanece en Polars."""
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, help="CSV normalizado para comparar motores")
    parser.add_argument("--grafico", type=Path, help="PNG de la visualización comparable")
    args = parser.parse_args()
    resultado = analizar()
    print(resultado)
    if args.salida:
        resultado.write_csv(args.salida)
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
            'ggplot2::geom_col(fill = "#11253B") +\n    ggplot2::scale_x_discrete(limits = rev) +\n    ggplot2::coord_flip()'
            if spec.chart == "barh"
            else 'ggplot2::geom_col(fill = "#11253B")'
        )
    )
    return f'''#!/usr/bin/env Rscript
# Laboratorio comparable R + dplyr/readr + ggplot2 del caso {slug}.
#
# La resolución completa sigue en solution.py y en los pasos Pandas. Este script
# cambia el motor sobre el mismo contrato CSV para estudiar sintaxis y semántica sin
# cambiar datos, indicador ni escala gráfica.

required <- c("readr", "dplyr")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) {{
  stop(
    "Faltan paquetes: ", paste(missing, collapse = ", "),
    ". Instálelos con install.packages(c('readr', 'dplyr', 'ggplot2'))."
  )
}}

# Buscar pyproject.toml hacia arriba hace portable el script entre terminal, RStudio,
# Posit Cloud, IRkernel y un clon en Colab. LAB_ROOT permite una ruta explícita sin
# codificar la unidad o el directorio del desarrollador.
find_root <- function(start = getwd()) {{
  current <- normalizePath(start, mustWork = TRUE)
  repeat {{
    if (file.exists(file.path(current, "pyproject.toml"))) return(current)
    parent <- dirname(current)
    if (identical(parent, current)) stop("No se encontró la raíz del repositorio.")
    current <- parent
  }}
}}
root <- Sys.getenv("LAB_ROOT", unset = find_root())
source_csv <- file.path(root, "cases", "{slug}", "resultados", "{spec.csv}")

# readr conserva nombres y tipos previsibles. La validación temprana produce un error
# que explica el contrato roto, en vez de fallar más tarde dentro de una gráfica.
datos <- readr::read_csv(source_csv, show_col_types = FALSE, progress = FALSE)
required_columns <- c("{spec.x}", "{spec.y}")
missing_columns <- setdiff(required_columns, names(datos))
if (length(missing_columns)) stop("Faltan columnas: ", paste(missing_columns, collapse = ", "))

# dplyr expresa la misma selección, filtro, agrupación y orden que las otras vías.
resultado <- {spec.r_query}
print(resultado)

args <- commandArgs(trailingOnly = TRUE)
value_after <- function(flag) {{
  pos <- match(flag, args)
  if (is.na(pos)) return(NULL)
  if (pos == length(args)) stop(flag, " necesita una ruta de salida")
  args[pos + 1]
}}

csv_output <- value_after("--salida")
if (!is.null(csv_output)) readr::write_csv(resultado, csv_output)

plot_output <- value_after("--grafico")
if (!is.null(plot_output)) {{
  if (!requireNamespace("ggplot2", quietly = TRUE)) {{
    stop("Instale ggplot2 para generar el gráfico: install.packages('ggplot2')")
  }}
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
  ggplot2::ggsave(plot_output, grafico, width = 9, height = 5, dpi = 150)
  cat(plot_output, "\\n")
}}
'''


def _data_dictionary(slug: str, spec: CaseSpec) -> str:
    """Diccionario compacto del contrato realmente leído por los tres motores."""
    source = ROOT / "cases" / slug / "resultados" / spec.csv
    frame = pd.read_csv(source, nrows=50)
    rows = ["| Campo | Tipo observado | Función en el ejercicio |", "| --- | --- | --- |"]
    for column, dtype in frame.dtypes.items():
        role = "categoría/eje X" if column == spec.x else (
            "medida/eje Y" if column == spec.y else "campo auxiliar del contrato"
        )
        rows.append(f"| `{column}` | `{dtype}` | {role} |")
    return "\n".join(rows)


def _guide(slug: str, spec: CaseSpec) -> str:
    objective, formula, interpretation, pitfall = PEDAGOGY[slug]
    return f'''#### Contrato común del ejercicio

- **Objetivo.** {objective}
- **Fuente que leen las tres implementaciones.**
  [`resultados/{spec.csv}`](resultados/{spec.csv}), CSV UTF-8 versionado y producido
  por la resolución completa del caso. Los datos originales, su publicador, fecha,
  licencia, URL y huella se documentan en [`case.json`](case.json) y, cuando existe,
  `procedencia.json`. Este CSV es un **resultado reproducible**, no se presenta como
  una nueva fuente oficial.
- **Alcance.** {spec.scope}. Los tres scripts comparables no sustituyen la adquisición,
  limpieza ni controles completos de los pasos Pandas: aíslan el indicador para que
  una diferencia observada sea atribuible al motor.
- **Fórmula o regla.** {formula}
- **Interpretación.** {interpretation}
- **Error frecuente.** {pitfall}

{_data_dictionary(slug, spec)}

#### Qué cambia entre motores

| Dimensión | Pandas | Polars | R (`dplyr`/`readr`) |
| --- | --- | --- | --- |
| Modelo | DataFrame mutable por operaciones | expresiones columnares y plan optimizable | tubería declarativa sobre `tibble` |
| Nulos | `NaN`/`NA`; `groupby` exige decidir `dropna` | `null` separado de `NaN` | `NA`; muchas funciones exigen `na.rm` explícito |
| Orden | varias operaciones lo conservan, pero se ordena explícitamente | no se presupone tras agrupar | se fija con `arrange` |
| Gráfico | Matplotlib | Matplotlib tras extraer sólo X/Y | ggplot2 y su gramática de capas |
| Ventaja típica | ecosistema amplio y aprendizaje gradual | paralelismo, tipos y consultas grandes | estadística, comunicación y análisis reproducible |
| Límite aquí | el índice puede introducir alineaciones implícitas | añade una dependencia y otra semántica de tipos | requiere runtime y paquetes R independientes |

La equivalencia se valida sobre CSV normalizados con tolerancia numérica `1e-9`; no
se exige que la sintaxis ni los píxeles sean idénticos. Para ejecutar en un entorno
limpio consulte [`docs/ejecucion-portable.md`](../../docs/ejecucion-portable.md).'''


def _implementaciones(slug: str, spec: CaseSpec) -> tuple[Implementacion, ...]:
    return (
        Implementacion(
            motor="Pandas + Matplotlib",
            lenguaje="python",
            archivo="solucion_pandas.py",
            comando=f"python cases/{slug}/cuaderno/solucion_pandas.py",
            alcance=spec.scope,
            codigo=_pandas_code(slug, spec),
        ),
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
    cuaderno.guia_multimotor = _guide(slug, spec)
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
        order = {"mínimo": 0, "P10": 1, "P25": 2, "P50": 3, "media": 4,
                 "P75": 5, "P90": 6, "P95": 7, "máximo": 8}
        return frame.assign(_orden=frame["estadistico"].map(order)).sort_values(
            "_orden"
        )[["estadistico", "intervalo_min"]]
    if slug == "evolucion_gtfs":
        return frame.sort_values("publicacion")[["publicacion", "salidas"]]
    if slug == "informe_decision_carga":
        return frame.loc[frame.unidad == "%", ["indicador", "valor"]]
    if slug == "gobernanza_datos_dtpm":
        return frame.sort_values(
            ["puntaje_riesgo", "activo_id"], ascending=[False, True]
        )[["activo_id", "puntaje_riesgo"]]
    if slug == "etl_gtfs_automatizado":
        return frame.sort_values("publicacion")[["publicacion", "mb_stop_times"]]
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
