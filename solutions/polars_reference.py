"""Implementación independiente en Polars de los tres casos sintéticos canónicos.

No convierte DataFrames de Pandas ni reutiliza sus cálculos. Lee los CSV crudos,
resuelve tipos, filtros, cruces y agregaciones con expresiones de Polars y devuelve las
mismas tablas contractuales para poder confrontarlas indicador por indicador.

Uso:
    python solutions/polars_reference.py transport 1
    python solutions/polars_reference.py retail
    python solutions/polars_reference.py education
"""

from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
TRANSPORT_CASES = (1, 2, 3)


def _read_csv(path: Path, *, all_text: bool = False) -> pl.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}.")
    options = {"infer_schema_length": 0} if all_text else {}
    return pl.read_csv(path, null_values=["", "NA"], **options)


def _profile(frame: pl.DataFrame) -> pl.DataFrame:
    duplicates = frame.height - frame.unique().height
    return pl.DataFrame({
        "column": frame.columns,
        "dtype": [str(value) for value in frame.dtypes],
        "nulls": [frame[column].null_count() for column in frame.columns],
        "unique": [frame[column].n_unique() for column in frame.columns],
        "rows": [frame.height] * frame.width,
        "exact_duplicates": [duplicates] * frame.width,
    })


def analyze_transport(case: int, root: Path = ROOT) -> dict[str, pl.DataFrame]:
    """Calcula las siete tablas del caso de transporte exclusivamente con Polars."""
    if case not in TRANSPORT_CASES:
        raise ValueError(f"Caso inválido: {case!r}. Use 1, 2 o 3.")
    folder = root / "data" / f"case_{case}"
    trips = _read_csv(folder / "viajes.csv", all_text=True)
    routes = _read_csv(folder / "recorridos.csv", all_text=True)
    operators = _read_csv(folder / "operadores.csv", all_text=True)
    schedule = _read_csv(folder / "programacion.csv", all_text=True).with_columns(
        pl.col("dia_octubre").cast(pl.Int64, strict=False),
        pl.col("viajes_programados").cast(pl.Int64, strict=False),
    )

    original = trips.height
    t = trips.unique(maintain_order=True).with_columns(
        pl.col("pasajeros").cast(pl.Float64, strict=False),
        pl.col("inicio").str.to_datetime(strict=False),
        pl.col("fin").str.to_datetime(strict=False),
    )
    t = (
        t.join(routes, on="recorrido_id", how="left", validate="m:1")
        .join(operators, on="operador_id", how="left", validate="m:1")
        .with_columns(
            ((pl.col("fin") - pl.col("inicio")).dt.total_seconds() / 60)
            .alias("duracion_min")
        )
        .with_columns(
            pl.col("estado").eq("REALIZADO").alias("realizado"),
            (pl.col("pasajeros").is_null() | pl.col("pasajeros").lt(0))
            .alias("pasajeros_invalido"),
            (pl.col("duracion_min").is_null() | pl.col("duracion_min").lt(0))
            .alias("duracion_invalida"),
            pl.col("operador_id").is_null().alias("clave_desconocida"),
        )
    )

    quality = pl.DataFrame({
        "indicador": [
            "filas_originales",
            "duplicados_exactos",
            "claves_desconocidas",
            "pasajeros_invalidos_realizados",
            "duracion_invalida_realizados",
        ],
        "valor": [
            original,
            original - t.height,
            t.select(pl.col("clave_desconocida").sum()).item(),
            t.filter("realizado").select(pl.col("pasajeros_invalido").sum()).item(),
            t.filter("realizado").select(pl.col("duracion_invalida").sum()).item(),
        ],
    })

    valid = t.filter(pl.col("realizado") & ~pl.col("clave_desconocida")).with_columns(
        pl.col("inicio").dt.day().alias("dia_octubre"),
        pl.col("inicio").dt.hour().alias("hora"),
    )
    with_pax = valid.filter(~pl.col("pasajeros_invalido"))
    demand = (
        with_pax.group_by("operador")
        .agg(
            pl.col("pasajeros").sum(),
            pl.len().alias("viajes_con_dato"),
        )
        .sort("operador")
    )
    hour = with_pax.group_by("hora").agg(pl.col("pasajeros").sum()).sort("hora")

    duration = (
        valid.filter(~pl.col("duracion_invalida"))
        .with_columns(pl.col("duracion_min").le(pl.col("meta_min").cast(pl.Float64)).alias("puntual"))
        .group_by("recorrido_id")
        .agg(
            pl.col("duracion_min").mean().alias("media_min"),
            pl.col("duracion_min").median().alias("mediana_min"),
            pl.col("duracion_min").quantile(0.9, interpolation="linear").alias("p90_min"),
            (100 * pl.col("puntual").mean()).alias("puntualidad_pct"),
        )
        .sort("recorrido_id")
    )

    counts = (
        valid.group_by("recorrido_id", "dia_octubre")
        .len()
        .rename({"len": "realizados"})
    )
    compliance = (
        schedule.join(
            counts,
            on=["recorrido_id", "dia_octubre"],
            how="full",
            coalesce=True,
            validate="1:1",
        )
        .with_columns(pl.col("realizados").fill_null(0).cast(pl.Int64))
        .with_columns(
            pl.when(pl.col("viajes_programados").gt(0))
            .then(100 * pl.col("realizados") / pl.col("viajes_programados"))
            .otherwise(None)
            .alias("cumplimiento_pct")
        )
        .sort("recorrido_id", "dia_octubre")
    )
    by_operator = (
        compliance.join(routes, on="recorrido_id", how="inner", validate="m:1")
        .join(operators, on="operador_id", how="inner", validate="m:1")
        .group_by("operador")
        .agg(
            pl.col("realizados").sum(),
            pl.col("viajes_programados").sum(),
        )
        .with_columns(
            (100 * pl.col("realizados") / pl.col("viajes_programados"))
            .alias("cumplimiento_pct")
        )
        .sort("operador")
    )

    return {
        "calidad": quality,
        "demanda": demand,
        "demanda_hora": hour,
        "duracion": duration,
        "cumplimiento": compliance,
        "cumplimiento_operador": by_operator,
        "realizados_recorrido": (
            valid.group_by("recorrido_id").len().rename({"len": "realizados"})
            .sort("recorrido_id")
        ),
    }


def analyze_retail(path: Path | None = None) -> dict[str, pl.DataFrame]:
    """Resuelve ventas netas y margen del caso retail con Polars."""
    source = path or ROOT / "cases" / "retail" / "input.csv"
    raw = _read_csv(source)
    clean = raw.unique(maintain_order=True).filter(
        pl.col("quantity").gt(0)
        & pl.col("price").ge(0)
        & pl.col("cost").ge(0)
        & pl.col("status").is_in(["SALE", "RETURN"])
    )
    metrics = (
        clean.with_columns(
            pl.when(pl.col("status").eq("SALE"))
            .then(pl.col("quantity"))
            .otherwise(-pl.col("quantity"))
            .alias("units")
        )
        .with_columns(
            (pl.col("units") * pl.col("price")).alias("net_sales"),
            (pl.col("units") * (pl.col("price") - pl.col("cost"))).alias("margin"),
        )
        .group_by("product")
        .agg(pl.col("units", "net_sales", "margin").sum())
        .sort("product")
    )
    return {"quality": _profile(raw), "metrics": metrics}


def analyze_education(path: Path | None = None) -> dict[str, pl.DataFrame]:
    """Resuelve las dos tasas de asistencia del caso education con Polars."""
    source = path or ROOT / "cases" / "education" / "input.csv"
    raw = _read_csv(source)
    clean = (
        raw.unique(maintain_order=True)
        .filter(pl.col("scheduled").gt(0) & pl.col("attended").is_between(0, pl.col("scheduled")))
        .with_columns((100 * pl.col("attended") / pl.col("scheduled")).alias("rate"))
    )
    metrics = (
        clean.group_by("school")
        .agg(
            pl.col("attended").sum(),
            pl.col("scheduled").sum(),
            pl.col("rate").mean().alias("simple_pct"),
        )
        .with_columns((100 * pl.col("attended") / pl.col("scheduled")).alias("weighted_pct"))
        .sort("school")
    )
    return {"quality": _profile(raw), "metrics": metrics}


def export(tables: dict[str, pl.DataFrame], destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.write_csv(destination / f"{name}.csv")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=("transport", "retail", "education"))
    parser.add_argument("number", nargs="?", type=int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.case == "transport":
        tables = analyze_transport(args.number)
    elif args.case == "retail":
        tables = analyze_retail()
    else:
        tables = analyze_education()
    destination = args.output or ROOT / "reference_outputs" / "polars" / args.case
    export(tables, destination)
    print(f"{args.case}: {len(tables)} tablas escritas en {destination}")


if __name__ == "__main__":
    main()
