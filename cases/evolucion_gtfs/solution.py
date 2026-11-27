"""Compara publicaciones GTFS y mide la oferta programada por hora.

La comparación ejecutada usa los últimos cortes anuales de 2024 y 2025, y el feed
vigente de 2026. El código acepta más referencias sin cambiar la definición.
"""

from __future__ import annotations

import argparse
import io
import zipfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from lab.dates import parse_hms_seconds, service_day_hour

ROOT = Path(__file__).resolve().parents[2]
HISTORICOS_2024 = ROOT / "data" / "original" / "gtfs-historicos-2024.zip"
HISTORICOS_2025 = ROOT / "data" / "original" / "gtfs-historicos-2025.zip"
VIGENTE = ROOT / "data" / "original" / "gtfs-red-movilidad.zip"
MIEMBRO_2024 = "2024/GTFS_20241124.zip"
MIEMBRO_2025 = "2025/GTFS_20251220.zip"
RESULTS = Path(__file__).resolve().parent / "resultados"


@dataclass(frozen=True)
class FeedRef:
    etiqueta: str
    ruta: Path
    miembro: str = ""


REFERENCIAS = (
    FeedRef("2024-11-24", HISTORICOS_2024, MIEMBRO_2024),
    FeedRef("2025-12-20", HISTORICOS_2025, MIEMBRO_2025),
    FeedRef("2026-11-14", VIGENTE),
)


def _inner_bytes(ref: FeedRef) -> bytes | None:
    if not ref.miembro:
        return None
    with zipfile.ZipFile(ref.ruta) as outer:
        return outer.read(ref.miembro)


def _members(ref: FeedRef) -> dict[str, zipfile.ZipInfo]:
    data = _inner_bytes(ref)
    source = io.BytesIO(data) if data is not None else ref.ruta
    with zipfile.ZipFile(source) as archive:
        return {item.filename: item for item in archive.infolist()}


def _read(ref: FeedRef, member: str, **kwargs) -> pd.DataFrame:
    data = _inner_bytes(ref)
    source = io.BytesIO(data) if data is not None else ref.ruta
    with zipfile.ZipFile(source) as archive, archive.open(member) as raw:
        return pd.read_csv(io.TextIOWrapper(raw, encoding="utf-8-sig"), **kwargs)


def cargar(ref: FeedRef) -> dict[str, pd.DataFrame]:
    """Tablas necesarias para identidad y oferta, leídas como texto."""
    if not ref.ruta.exists():
        if ref.miembro.startswith("2024/"):
            fuente = "gtfs-historicos-2024"
        elif ref.miembro:
            fuente = "gtfs-historicos-2025"
        else:
            fuente = "gtfs-red-movilidad"
        raise FileNotFoundError(f"Falta {ref.ruta}. Ejecute: python scripts/fetch_data.py {fuente}")
    return {
        "routes": _read(ref, "routes.txt", dtype=str,
                        usecols=["route_id", "route_short_name", "route_type"]),
        "stops": _read(ref, "stops.txt", dtype=str,
                       usecols=["stop_id", "stop_name", "location_type"]),
        "trips": _read(ref, "trips.txt", dtype=str,
                       usecols=["route_id", "service_id", "trip_id", "shape_id"]),
        "shapes": _read(ref, "shapes.txt", dtype=str,
                        usecols=["shape_id", "shape_pt_lat", "shape_pt_lon",
                                 "shape_pt_sequence"]),
        "frequencies": _read(ref, "frequencies.txt", dtype=str),
        "stop_times": _read(ref, "stop_times.txt", dtype=str,
                            usecols=["trip_id", "arrival_time", "stop_sequence"]),
    }


def inventario(ref: FeedRef, tablas: dict[str, pd.DataFrame]) -> dict[str, object]:
    miembros = _members(ref)
    paradas = tablas["stops"]["location_type"].fillna("0").eq("0")
    return {
        "publicacion": ref.etiqueta,
        "rutas": tablas["routes"]["route_id"].nunique(),
        "paradas_embarque": int(paradas.sum()),
        "viajes_declarados": tablas["trips"]["trip_id"].nunique(),
        "ventanas_frecuencia": len(tablas["frequencies"]),
        "filas_stop_times": len(tablas["stop_times"]),
        "bytes_stop_times": miembros["stop_times.txt"].file_size,
    }


def salidas_por_hora(tablas: dict[str, pd.DataFrame], servicio: str = "L") -> pd.DataFrame:
    """Salidas programadas por hora, combinando frecuencia y horario absoluto."""
    trips = tablas["trips"].loc[tablas["trips"]["service_id"].eq(servicio),
                                ["trip_id", "route_id"]]
    validos = set(trips["trip_id"])
    freq = tablas["frequencies"].loc[
        tablas["frequencies"]["trip_id"].isin(validos)
    ].copy()
    freq["inicio_s"] = parse_hms_seconds(freq["start_time"])
    freq["fin_s"] = parse_hms_seconds(freq["end_time"])
    freq["intervalo_s"] = pd.to_numeric(freq["headway_secs"], errors="coerce")
    ok = (freq[["inicio_s", "fin_s", "intervalo_s"]].notna().all(axis=1)
          & freq["intervalo_s"].gt(0) & freq["fin_s"].ge(freq["inicio_s"]))
    freq = freq.loc[ok]
    freq["salidas"] = ((freq["fin_s"] - freq["inicio_s"]) // freq["intervalo_s"]).astype(int)
    exp = freq.loc[freq.index.repeat(freq["salidas"])].copy()
    exp["orden"] = exp.groupby(level=0).cumcount()
    exp["salida_s"] = exp["inicio_s"] + exp["orden"] * exp["intervalo_s"]
    exp["hora"] = service_day_hour(exp["salida_s"])

    con_frecuencia = set(tablas["frequencies"]["trip_id"])
    absolutas = tablas["stop_times"].loc[
        tablas["stop_times"]["trip_id"].isin(validos - con_frecuencia)
    ].copy()
    absolutas["secuencia"] = pd.to_numeric(absolutas["stop_sequence"], errors="coerce")
    primeras = absolutas.loc[absolutas["secuencia"].eq(1)].drop_duplicates("trip_id")
    primeras["hora"] = service_day_hour(parse_hms_seconds(primeras["arrival_time"]))

    horas = pd.concat([exp["hora"], primeras["hora"]], ignore_index=True).dropna().astype(int)
    return (horas.value_counts().reindex(range(24), fill_value=0).sort_index()
            .rename_axis("hora").rename("salidas").reset_index())


def comparar_identidades(tablas_a: dict[str, pd.DataFrame],
                         tablas_b: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Altas, bajas y permanencias por identificador publicado."""
    filas = []
    for entidad, tabla, clave in (("rutas", "routes", "route_id"),
                                  ("paradas de embarque", "stops", "stop_id")):
        marco_a = tablas_a[tabla]
        marco_b = tablas_b[tabla]
        if tabla == "stops":
            marco_a = marco_a.loc[marco_a["location_type"].fillna("0").eq("0")]
            marco_b = marco_b.loc[marco_b["location_type"].fillna("0").eq("0")]
        a = set(marco_a[clave].dropna())
        b = set(marco_b[clave].dropna())
        filas.extend([
            {"entidad": entidad, "cambio": "permanece", "cantidad": len(a & b)},
            {"entidad": entidad, "cambio": "aparece", "cantidad": len(b - a)},
            {"entidad": entidad, "cambio": "desaparece", "cantidad": len(a - b)},
        ])
    return pd.DataFrame(filas)


def cambios_de_trazado(tablas_a: dict[str, pd.DataFrame],
                       tablas_b: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Rutas persistentes cuyo conjunto de geometrías cambió.

    No compara solo `shape_id`: el publicador puede conservar el identificador y
    cambiar sus puntos, o renombrar una geometría idéntica. Cada shape se firma con
    sus coordenadas y su secuencia antes de asociarlo a la ruta.
    """
    def formas(tablas):
        puntos = tablas["shapes"].copy()
        puntos["shape_pt_sequence"] = pd.to_numeric(puntos["shape_pt_sequence"], errors="coerce")
        puntos = puntos.sort_values(["shape_id", "shape_pt_sequence"])
        tokens = pd.util.hash_pandas_object(
            puntos[["shape_pt_sequence", "shape_pt_lat", "shape_pt_lon"]], index=False
        )
        firmas = tokens.groupby(puntos["shape_id"]).sum().astype(str)
        viajes = tablas["trips"].copy()
        viajes["firma"] = viajes["shape_id"].map(firmas)
        return viajes.groupby("route_id")["firma"].agg(lambda s: frozenset(s.dropna()))

    a, b = formas(tablas_a), formas(tablas_b)
    comunes = sorted(set(a.index) & set(b.index))
    filas = [{"route_id": route, "formas_inicial": len(a[route]), "formas_final": len(b[route]),
              "cambio_de_conjunto": a[route] != b[route]} for route in comunes]
    return pd.DataFrame(filas).sort_values(["cambio_de_conjunto", "route_id"],
                                          ascending=[False, True]).reset_index(drop=True)


def analizar(referencias: tuple[FeedRef, ...] = REFERENCIAS) -> dict[str, pd.DataFrame]:
    cargadas = [(ref, cargar(ref)) for ref in referencias]
    inventarios = pd.DataFrame([inventario(ref, tablas) for ref, tablas in cargadas])
    ofertas = []
    for ref, tablas in cargadas:
        por_hora = salidas_por_hora(tablas)
        por_hora["publicacion"] = ref.etiqueta
        ofertas.append(por_hora)
    serie = pd.concat(ofertas, ignore_index=True)
    totales = (serie.groupby("publicacion", as_index=False)["salidas"].sum()
               .sort_values("publicacion").reset_index(drop=True))
    totales["cambio_abs"] = totales["salidas"].diff()
    totales["cambio_pct"] = totales["salidas"].pct_change().mul(100).round(2)
    return {
        "inventario": inventarios,
        "identidades": comparar_identidades(cargadas[0][1], cargadas[-1][1]),
        "trazados": cambios_de_trazado(cargadas[0][1], cargadas[-1][1]),
        "oferta_por_hora": serie[["publicacion", "hora", "salidas"]],
        "oferta_total": totales,
    }


def exportar(resultados: dict[str, pd.DataFrame], destino: Path = RESULTS) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    for nombre, tabla in resultados.items():
        tabla.to_csv(destino / f"{nombre}.csv", index=False, encoding="utf-8")
    return destino


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    resultados = analizar()
    for nombre, tabla in resultados.items():
        print(f"\n=== {nombre.replace('_', ' ').title()} ===")
        print(tabla.head(30).to_string(index=False))
    exportar(resultados)


if __name__ == "__main__":
    main()
