"""Mide tres caminos para la misma agregación sobre `stop_times.txt`."""

from __future__ import annotations

import argparse
import shutil
import tempfile
import time
import zipfile
from pathlib import Path

import pandas as pd

from lab.sources import iter_zip_table, read_zip_table

ROOT = Path(__file__).resolve().parents[2]
FEED = ROOT / "data" / "original" / "gtfs-red-movilidad.zip"
RESULTS = Path(__file__).resolve().parent / "resultados"
CHUNK_SIZE = 200_000


def _memoria_mb(frame: pd.DataFrame) -> float:
    return float(frame.memory_usage(deep=True).sum() / 1_000_000)


def pandas_completo(feed: Path = FEED) -> tuple[pd.Series, dict[str, object]]:
    inicio = time.perf_counter()
    tabla = read_zip_table(feed, "stop_times.txt", dtype=str, usecols=["stop_id"])
    lectura = time.perf_counter() - inicio
    memoria = _memoria_mb(tabla)
    inicio_agregacion = time.perf_counter()
    resultado = tabla.groupby("stop_id").size().sort_index()
    agregacion = time.perf_counter() - inicio_agregacion
    return resultado, {"metodo": "Pandas completo", "segundos": lectura + agregacion,
                       "lectura_s": lectura, "agregacion_s": agregacion,
                       "memoria_datos_mb": memoria, "bloques": 1}


def pandas_bloques(feed: Path = FEED, chunksize: int = CHUNK_SIZE) -> tuple[pd.Series, dict[str, object]]:
    inicio = time.perf_counter()
    resultado = pd.Series(dtype="int64")
    max_memoria = 0.0
    bloques = 0
    for bloque in iter_zip_table(feed, "stop_times.txt", chunksize=chunksize,
                                 dtype=str, usecols=["stop_id"]):
        bloques += 1
        max_memoria = max(max_memoria, _memoria_mb(bloque))
        parcial = bloque.groupby("stop_id").size()
        resultado = resultado.add(parcial, fill_value=0)
    resultado = resultado.fillna(0).astype("int64").sort_index()
    segundos = time.perf_counter() - inicio
    return resultado, {"metodo": "Pandas por bloques", "segundos": segundos,
                       "lectura_s": pd.NA, "agregacion_s": pd.NA,
                       "memoria_datos_mb": max_memoria, "bloques": bloques}


def duckdb_csv(feed: Path = FEED) -> tuple[pd.Series | None, dict[str, object]]:
    """Agrega con DuckDB; la extracción a CSV se mide aparte del motor."""
    try:
        import duckdb
    except ImportError:
        return None, {"metodo": "DuckDB sobre CSV", "segundos": pd.NA,
                      "lectura_s": pd.NA, "agregacion_s": pd.NA,
                      "memoria_datos_mb": pd.NA, "bloques": pd.NA,
                      "estado": "no ejecutado: instale el extra sql"}

    with tempfile.TemporaryDirectory(prefix="gtfs-benchmark-") as temporal:
        csv = Path(temporal) / "stop_times.txt"
        inicio = time.perf_counter()
        with zipfile.ZipFile(feed) as archive, archive.open("stop_times.txt") as source, csv.open("wb") as target:
            shutil.copyfileobj(source, target)
        preparacion = time.perf_counter() - inicio
        ruta = str(csv).replace("'", "''").replace("\\", "/")
        inicio = time.perf_counter()
        frame = duckdb.sql(
            f"SELECT stop_id, count(*) AS filas FROM read_csv_auto('{ruta}', header=true) "
            "GROUP BY stop_id ORDER BY stop_id"
        ).df()
        consulta = time.perf_counter() - inicio
    resultado = frame.set_index("stop_id")["filas"].astype("int64")
    return resultado, {"metodo": "DuckDB sobre CSV", "segundos": consulta,
                       "lectura_s": preparacion, "agregacion_s": consulta,
                       "memoria_datos_mb": pd.NA, "bloques": pd.NA,
                       "estado": "ejecutado; extracción informada por separado"}


def benchmark(feed: Path = FEED) -> dict[str, pd.DataFrame]:
    """Ejecuta los métodos y comprueba que produzcan exactamente el mismo resultado."""
    if not feed.exists():
        raise FileNotFoundError(f"Falta {feed}. Ejecute: python scripts/fetch_data.py gtfs-red-movilidad")
    completo, meta_completo = pandas_completo(feed)
    bloques, meta_bloques = pandas_bloques(feed)
    duck, meta_duck = duckdb_csv(feed)

    filas = [meta_completo, meta_bloques, meta_duck]
    referencia = completo.rename("completo").to_frame().join(
        bloques.rename("bloques"), how="outer")
    referencia["coincide_bloques"] = referencia["completo"].eq(referencia["bloques"])
    if duck is not None:
        referencia = referencia.join(duck.rename("duckdb"), how="outer")
        referencia["coincide_duckdb"] = referencia["completo"].eq(referencia["duckdb"])
    resumen = pd.DataFrame(filas)
    resumen["filas_resultado"] = len(completo)
    resumen["filas_entrada"] = int(completo.sum())
    return {"benchmark": resumen, "validacion": pd.DataFrame([
        {"comparacion": "completo vs bloques", "coinciden": bool(referencia["coincide_bloques"].all()),
         "diferencias": int((~referencia["coincide_bloques"]).sum())},
        {"comparacion": "completo vs DuckDB", "coinciden": (pd.NA if duck is None else bool(referencia["coincide_duckdb"].all())),
         "diferencias": (pd.NA if duck is None else int((~referencia["coincide_duckdb"]).sum()))},
    ]), "conteos": referencia.reset_index()}


def exportar(resultados: dict[str, pd.DataFrame], destino: Path = RESULTS) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    for nombre, tabla in resultados.items():
        tabla.to_csv(destino / f"{nombre}.csv", index=False, encoding="utf-8")
    return destino


def cargar_referencia(destino: Path = RESULTS) -> dict[str, pd.DataFrame]:
    """Lee la medición versionada que usa el cuaderno reproducible.

    Los tiempos vivos varían en cada ejecución. El comando principal los vuelve a
    medir y exporta; el cuaderno muestra esta referencia fija para que `--check` pueda
    detectar cambios reales en el contenido y no ruido del reloj.
    """
    nombres = ("benchmark", "validacion", "conteos")
    faltantes = [destino / f"{nombre}.csv" for nombre in nombres
                 if not (destino / f"{nombre}.csv").exists()]
    if faltantes:
        raise FileNotFoundError(
            "Falta la medición de referencia. Ejecute: "
            "python -m cases.rendimiento_gtfs.solution"
        )
    return {nombre: pd.read_csv(destino / f"{nombre}.csv") for nombre in nombres}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feed", type=Path, default=FEED)
    args = parser.parse_args()
    resultados = benchmark(args.feed)
    print(resultados["benchmark"].to_string(index=False))
    print("\nValidación:\n" + resultados["validacion"].to_string(index=False))
    exportar(resultados)


if __name__ == "__main__":
    main()
