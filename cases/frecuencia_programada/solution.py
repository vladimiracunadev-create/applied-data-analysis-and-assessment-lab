"""Analiza la frecuencia programada y delimita qué parte del ICF es calculable.

El GTFS describe el programa de operación. El ICF oficial, en cambio, cuenta
mediciones GPS que cumplieron ese programa. Este caso construye la referencia
programada y deja el numerador y el denominador observados como no disponibles.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from lab.dates import parse_hms_seconds
from lab.sources import read_zip_table

ROOT = Path(__file__).resolve().parents[2]
FEED = ROOT / "data" / "original" / "gtfs-red-movilidad.zip"
RESULTS = Path(__file__).resolve().parent / "resultados"
PUNTA_MANANA = (8 * 3600, 9 * 3600)


def cargar(feed: Path = FEED) -> dict[str, pd.DataFrame]:
    """Lee las tres tablas necesarias, sin cargar `stop_times.txt`."""
    if not feed.exists():
        raise FileNotFoundError(f"Falta {feed}. Ejecute: python scripts/fetch_data.py gtfs-red-movilidad")
    return {
        "frequencies": read_zip_table(feed, "frequencies.txt", dtype=str),
        "trips": read_zip_table(feed, "trips.txt", dtype=str,
                                usecols=["route_id", "service_id", "trip_id", "direction_id"]),
        "routes": read_zip_table(feed, "routes.txt", dtype=str,
                                 usecols=["route_id", "route_short_name", "route_type"]),
    }


def ventanas_programadas(tablas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Ventanas tipadas, con duración, intervalo y salidas programadas."""
    frecuencias = tablas["frequencies"].copy()
    frecuencias["inicio_s"] = parse_hms_seconds(frecuencias["start_time"])
    frecuencias["fin_s"] = parse_hms_seconds(frecuencias["end_time"])
    frecuencias["intervalo_s"] = pd.to_numeric(frecuencias["headway_secs"], errors="coerce")
    frecuencias["duracion_s"] = frecuencias["fin_s"] - frecuencias["inicio_s"]
    frecuencias["valida"] = (
        frecuencias[["inicio_s", "fin_s", "intervalo_s"]].notna().all(axis=1)
        & frecuencias["intervalo_s"].gt(0)
        & frecuencias["duracion_s"].ge(0)
    )
    frecuencias["salidas_programadas"] = pd.NA
    validas = frecuencias["valida"]
    frecuencias.loc[validas, "salidas_programadas"] = (
        frecuencias.loc[validas, "duracion_s"]
        // frecuencias.loc[validas, "intervalo_s"]
    ).astype("Int64")

    catalogo = tablas["trips"].merge(tablas["routes"], on="route_id", how="left",
                                      validate="many_to_one")
    return frecuencias.merge(catalogo, on="trip_id", how="left", validate="many_to_one")


def alcance_icf(ventanas: pd.DataFrame) -> pd.DataFrame:
    """Matriz que separa lo calculable de lo que requiere mediciones GPS."""
    filas = [
        ("programa de frecuencia", "sí", len(ventanas), "ventanas GTFS"),
        ("intervalo objetivo", "sí", int(ventanas["intervalo_s"].notna().sum()), "ventanas"),
        ("salidas programadas", "sí", int(ventanas["salidas_programadas"].sum()), "salidas"),
        ("mediciones GPS realizadas", "NO", pd.NA, "mediciones"),
        ("mediciones que cumplen", "NO", pd.NA, "mediciones"),
        ("ICF oficial", "NO", pd.NA, "%"),
    ]
    return pd.DataFrame(filas, columns=["componente", "calculable_con_gtfs", "valor", "unidad"])


def distribucion(ventanas: pd.DataFrame) -> pd.DataFrame:
    """Distribución no ponderada de intervalos, con percentiles declarados."""
    segundos = ventanas.loc[ventanas["valida"], "intervalo_s"].astype(float)
    cuantiles = [("mínimo", segundos.min()), ("P10", segundos.quantile(0.10)),
                 ("P25", segundos.quantile(0.25)), ("P50", segundos.quantile(0.50)),
                 ("P75", segundos.quantile(0.75)), ("P90", segundos.quantile(0.90)),
                 ("P95", segundos.quantile(0.95)), ("máximo", segundos.max()),
                 ("media", segundos.mean())]
    return pd.DataFrame({
        "estadistico": [nombre for nombre, _ in cuantiles],
        "intervalo_min": [round(valor / 60, 2) for _, valor in cuantiles],
        "unidad": "minutos entre salidas",
    })


def punta_manana(ventanas: pd.DataFrame) -> pd.DataFrame:
    """Servicios con mayor intervalo programado que intersectan 08:00–09:00."""
    inicio, fin = PUNTA_MANANA
    seleccion = ventanas.loc[
        ventanas["valida"] & ventanas["inicio_s"].lt(fin) & ventanas["fin_s"].gt(inicio)
    ].copy()
    seleccion["intervalo_min"] = seleccion["intervalo_s"].astype(float) / 60
    grupos = (seleccion.groupby(["route_short_name", "direction_id"], dropna=False)
              .agg(ventanas=("trip_id", "size"),
                   intervalo_mediano_min=("intervalo_min", "median"),
                   intervalo_maximo_min=("intervalo_min", "max"),
                   salidas_programadas=("salidas_programadas", "sum"))
              .reset_index())
    return grupos.sort_values(["intervalo_mediano_min", "route_short_name"],
                              ascending=[False, True]).reset_index(drop=True)


def ponderaciones(ventanas: pd.DataFrame) -> pd.DataFrame:
    """Tres respuestas distintas a 'cuál es el intervalo típico'."""
    validas = ventanas.loc[ventanas["valida"]].copy()
    validas["intervalo_min"] = validas["intervalo_s"].astype(float) / 60
    por_servicio = validas.groupby("route_short_name")["intervalo_min"].median()
    por_salida = validas.loc[validas.index.repeat(validas["salidas_programadas"].astype(int)),
                             "intervalo_min"]
    return pd.DataFrame([
        {"unidad_de_analisis": "ventana publicada", "intervalo_tipico_min": validas["intervalo_min"].median(),
         "observaciones": len(validas)},
        {"unidad_de_analisis": "servicio (mediana de sus ventanas)",
         "intervalo_tipico_min": por_servicio.median(), "observaciones": len(por_servicio)},
        {"unidad_de_analisis": "salida programada", "intervalo_tipico_min": por_salida.median(),
         "observaciones": len(por_salida)},
    ]).round({"intervalo_tipico_min": 2})


def analizar(feed: Path = FEED) -> dict[str, pd.DataFrame]:
    tablas = cargar(feed)
    ventanas = ventanas_programadas(tablas)
    return {
        "alcance_icf": alcance_icf(ventanas),
        "distribucion": distribucion(ventanas),
        "punta_manana": punta_manana(ventanas),
        "ponderaciones": ponderaciones(ventanas),
        "ventanas_invalidas": ventanas.loc[~ventanas["valida"],
                                             ["trip_id", "start_time", "end_time", "headway_secs"]],
    }


def exportar(resultados: dict[str, pd.DataFrame], destino: Path = RESULTS) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    for nombre, tabla in resultados.items():
        tabla.to_csv(destino / f"{nombre}.csv", index=False, encoding="utf-8")
    return destino


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feed", type=Path, default=FEED)
    args = parser.parse_args()
    resultados = analizar(args.feed)
    for nombre, tabla in resultados.items():
        print(f"\n=== {nombre.replace('_', ' ').title()} ===")
        print(tabla.head(20).to_string(index=False))
    exportar(resultados)


if __name__ == "__main__":
    main()
