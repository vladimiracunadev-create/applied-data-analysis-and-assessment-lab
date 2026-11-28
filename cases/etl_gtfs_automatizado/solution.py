"""P18: convertir el inventario histórico GTFS en un ETL contractual e incremental.

El caso reutiliza el inventario ejecutado por P14/P15. No vuelve a descargar ni
redistribuye los ZIP del DTPM: valida el contrato de su resultado reproducible, produce
particiones lógicas y deja la exportación Parquet como capacidad opcional verificable.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "cases" / "evolucion_gtfs" / "resultados" / "inventario.csv"
RESULTS = Path(__file__).resolve().parent / "resultados"
REQUIRED = {
    "publicacion", "rutas", "paradas_embarque", "viajes_declarados",
    "ventanas_frecuencia", "filas_stop_times", "bytes_stop_times",
}


def cargar(path: Path = SOURCE) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = sorted(REQUIRED - set(frame.columns))
    if missing:
        raise ValueError(f"Inventario GTFS incompleto; faltan: {missing}")
    if frame["publicacion"].duplicated().any():
        raise ValueError("Cada publicación debe aparecer una sola vez")
    return frame


def transformar(frame: pd.DataFrame) -> pd.DataFrame:
    """Tipa fechas, valida magnitudes y calcula métricas sin alterar el origen."""
    result = frame.copy()
    result["publicacion"] = pd.to_datetime(result["publicacion"], errors="raise")
    numeric = sorted(REQUIRED - {"publicacion"})
    if (result[numeric] < 0).any().any():
        raise ValueError("Los conteos y tamaños GTFS no pueden ser negativos")
    result["anio"] = result["publicacion"].dt.year
    result["particion"] = result["publicacion"].dt.strftime("anio=%Y/publicacion=%Y-%m-%d")
    result["mb_stop_times"] = result["bytes_stop_times"] / 1_000_000
    result["filas_por_mb"] = result["filas_stop_times"] / result["mb_stop_times"]
    return result.sort_values("publicacion").reset_index(drop=True)


def controles(frame: pd.DataFrame) -> pd.DataFrame:
    """Devuelve evidencia por control; no reduce varias reglas a un único booleano."""
    checks = [
        ("publicacion_unica", frame["publicacion"].is_unique, "una fila por corte"),
        ("fechas_validas", frame["publicacion"].notna().all(), "fecha ISO interpretable"),
        ("volumen_positivo", (frame["filas_stop_times"] > 0).all(), "stop_times no vacío"),
        ("paradas_positivas", (frame["paradas_embarque"] > 0).all(), "paradas de embarque presentes"),
        ("particion_unica", frame["particion"].is_unique, "partición determinista por corte"),
    ]
    return pd.DataFrame([
        {"control": name, "cumple": bool(ok), "regla": rule} for name, ok, rule in checks
    ])


def parquet_disponible() -> bool:
    return any(importlib.util.find_spec(name) is not None for name in ("pyarrow", "fastparquet"))


def exportar_parquet(frame: pd.DataFrame, destination: Path) -> Path:
    """Exporta sólo si existe un motor; nunca etiqueta un CSV como Parquet."""
    if not parquet_disponible():
        raise RuntimeError("Parquet requiere el extra columnar: pip install '.[columnar]'")
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(destination, index=False)
    return destination


def analizar() -> dict[str, pd.DataFrame]:
    transformed = transformar(cargar())
    volume = transformed[["publicacion", "filas_stop_times", "mb_stop_times", "filas_por_mb"]].copy()
    volume["publicacion"] = volume["publicacion"].dt.strftime("%Y-%m-%d")
    partitions = transformed[["publicacion", "anio", "particion"]].copy()
    partitions["publicacion"] = partitions["publicacion"].dt.strftime("%Y-%m-%d")
    format_status = pd.DataFrame([
        {"formato": "CSV dentro de ZIP", "estado": "ejecutado", "portabilidad": "entorno mínimo"},
        {"formato": "Parquet", "estado": "disponible" if parquet_disponible() else "no ejecutado",
         "portabilidad": "requiere extra columnar"},
    ])
    return {
        "volumen_por_publicacion": volume,
        "controles": controles(transformed),
        "particiones": partitions,
        "formatos": format_status,
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
        print(frame.to_string(index=False))
    exportar(results)


if __name__ == "__main__":
    main()
