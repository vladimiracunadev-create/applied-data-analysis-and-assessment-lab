"""P19: modelar como grafo bipartito las correspondencias Metro–bus de P03/P10."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "cases" / "correspondencia_metro" / "resultados" / "por_estacion.csv"
RESULTS = Path(__file__).resolve().parent / "resultados"
REQUIRED = {"stop_id", "stop_name", "servicios_distintos", "lista_de_servicios"}


def cargar(path: Path = SOURCE) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = sorted(REQUIRED - set(frame.columns))
    if missing:
        raise ValueError(f"Faltan columnas de correspondencia: {missing}")
    if frame["stop_id"].duplicated().any():
        raise ValueError("stop_id debe identificar una estación")
    return frame


def aristas(frame: pd.DataFrame) -> pd.DataFrame:
    """Convierte listas separadas por coma en una arista estación–servicio por fila."""
    edges = (
        frame[["stop_id", "stop_name", "lista_de_servicios"]]
        .assign(servicio=lambda x: x["lista_de_servicios"].fillna("").str.split(","))
        .explode("servicio")
        .drop(columns="lista_de_servicios")
    )
    edges["servicio"] = edges["servicio"].str.strip()
    edges = edges.loc[edges["servicio"].ne("")].drop_duplicates(["stop_id", "servicio"])
    return edges.sort_values(["stop_id", "servicio"]).reset_index(drop=True)


def analizar() -> dict[str, pd.DataFrame]:
    stations = cargar()
    edges = aristas(stations)
    degree_service = (
        edges.groupby("servicio", as_index=False)["stop_id"].nunique()
        .rename(columns={"stop_id": "estaciones_conectadas"})
        .sort_values(["estaciones_conectadas", "servicio"], ascending=[False, True])
        .reset_index(drop=True)
    )
    degree_station = (
        edges.groupby(["stop_id", "stop_name"], as_index=False)["servicio"].nunique()
        .rename(columns={"servicio": "servicios_conectados"})
        .sort_values(["servicios_conectados", "stop_name"], ascending=[False, True])
        .reset_index(drop=True)
    )
    top = degree_service.head(15).copy()
    top["participacion_estaciones_pct"] = 100 * top["estaciones_conectadas"] / stations["stop_id"].nunique()

    scenarios = []
    ordered = degree_service["servicio"].tolist()
    total_edges = len(edges)
    for count in (0, 1, 3, 5, 10):
        removed = set(ordered[:count])
        remaining = edges.loc[~edges["servicio"].isin(removed)]
        connected = remaining["stop_id"].nunique()
        scenarios.append({
            "servicios_retirados": count,
            "aristas_restantes": len(remaining),
            "aristas_perdidas_pct": 100 * (total_edges - len(remaining)) / total_edges,
            "estaciones_con_alternativa": connected,
            "estaciones_sin_alternativa": stations["stop_id"].nunique() - connected,
        })
    summary = pd.DataFrame([
        {"indicador": "estaciones", "valor": stations["stop_id"].nunique()},
        {"indicador": "servicios", "valor": edges["servicio"].nunique()},
        {"indicador": "aristas estación-servicio", "valor": len(edges)},
        {"indicador": "servicios medianos por estación", "valor": degree_station["servicios_conectados"].median()},
    ])
    return {
        "aristas": edges,
        "servicios_centrales": top,
        "grado_por_estacion": degree_station,
        "escenarios": pd.DataFrame(scenarios),
        "resumen": summary,
    }


def exportar(results: dict[str, pd.DataFrame], destination: Path = RESULTS) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    for name, frame in results.items():
        frame.to_csv(destination / f"{name}.csv", index=False, encoding="utf-8")
    return destination


def main() -> None:
    results = analizar()
    for name, frame in results.items():
        print(f"\n=== {name.replace('_', ' ').title()} ===")
        print(frame.head(20).to_string(index=False))
    exportar(results)


if __name__ == "__main__":
    main()
