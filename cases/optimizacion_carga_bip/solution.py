"""P20: seleccionar una cartera diversa de zonas para estudiar carga bip!.

El modelo amplía P16 sin inventar demanda, costos ni predios. Enumera todas las
combinaciones posibles de sus diez celdas candidatas, maximiza el puntaje exploratorio
heredado y exige diversidad territorial. Por tanto, la salida prioriza *estudios*; no
autoriza infraestructura ni identifica una localización óptima para operar.
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "cases" / "informe_decision_carga" / "resultados" / "prioridades.csv"
RESULTS = Path(__file__).resolve().parent / "resultados"
REQUIRED = {
    "celda_lat",
    "celda_lon",
    "paradas",
    "paradas_sin_cobertura",
    "cobertura_pct",
    "prioridad_exploratoria",
}
MAX_BUDGET = 5
RECOMMENDED_BUDGET = 4


def cargar(path: Path = SOURCE) -> pd.DataFrame:
    """Carga el resultado P16 y valida su contrato antes de optimizar."""
    frame = pd.read_csv(path)
    missing = sorted(REQUIRED - set(frame.columns))
    if missing:
        raise ValueError(f"Faltan columnas requeridas de P16: {missing}")
    if frame.empty:
        raise ValueError("P16 no contiene celdas candidatas")
    if frame[["celda_lat", "celda_lon"]].duplicated().any():
        raise ValueError("Cada celda candidata debe tener coordenadas únicas")
    if (frame["prioridad_exploratoria"] < 0).any():
        raise ValueError("El puntaje exploratorio no puede ser negativo")
    return frame.copy()


def preparar_candidatos(frame: pd.DataFrame) -> pd.DataFrame:
    """Asigna ID y banda territorial reproducible sin cambiar el puntaje de P16.

    Las bandas son terciles de latitud dentro de esta lista corta. Son una restricción
    pedagógica de diversidad, no divisiones administrativas ni áreas oficiales DTPM.
    """
    candidates = frame.sort_values(
        ["prioridad_exploratoria", "celda_lat", "celda_lon"],
        ascending=[False, True, True],
    ).reset_index(drop=True)
    candidates.insert(0, "candidato_id", [f"C{i:02d}" for i in range(1, len(candidates) + 1)])
    # rank(method='first') resuelve empates de latitud de manera estable; qcut reparte
    # la lista en tres grupos comparables sin fingir que son comunas o zonas oficiales.
    candidates["banda_territorial"] = pd.qcut(
        candidates["celda_lat"].rank(method="first"),
        q=3,
        labels=["sur", "centro", "norte"],
    ).astype(str)
    return candidates


def _evaluar(combination: tuple[int, ...], candidates: pd.DataFrame) -> dict[str, object]:
    selected = candidates.iloc[list(combination)]
    return {
        "candidatos": ";".join(sorted(selected["candidato_id"])),
        "puntaje_total": float(selected["prioridad_exploratoria"].sum()),
        "zonas_representadas": int(selected["banda_territorial"].nunique()),
        "paradas_sin_cobertura_referenciales": int(selected["paradas_sin_cobertura"].sum()),
    }


def optimizar(candidates: pd.DataFrame, max_budget: int = MAX_BUDGET) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Enumera combinaciones y devuelve frontera óptima y alternativas auditables.

    Para un presupuesto k se requieren min(k, 3) bandas. La enumeración exhaustiva es
    adecuada para diez candidatos (hasta 252 combinaciones por presupuesto) y hace la
    regla verificable sin instalar un solver externo.
    """
    if not 1 <= max_budget <= min(MAX_BUDGET, len(candidates)):
        raise ValueError(f"max_budget debe estar entre 1 y {min(MAX_BUDGET, len(candidates))}")
    frontier: list[dict[str, object]] = []
    alternatives: list[dict[str, object]] = []
    for budget in range(1, max_budget + 1):
        minimum_zones = min(budget, 3)
        feasible: list[dict[str, object]] = []
        for combination in combinations(range(len(candidates)), budget):
            evaluated = _evaluar(combination, candidates)
            if evaluated["zonas_representadas"] >= minimum_zones:
                feasible.append(evaluated)
        if not feasible:
            raise ValueError(f"No hay cartera factible para presupuesto {budget}")
        ranked = sorted(feasible, key=lambda row: (-float(row["puntaje_total"]), str(row["candidatos"])))
        for position, row in enumerate(ranked[:3], start=1):
            alternatives.append({"presupuesto": budget, "posicion": position, **row})
        frontier.append({"presupuesto": budget, "zonas_minimas": minimum_zones, **ranked[0]})
    return pd.DataFrame(frontier), pd.DataFrame(alternatives)


def analizar() -> dict[str, pd.DataFrame]:
    candidates = preparar_candidatos(cargar())
    frontier, alternatives = optimizar(candidates)
    chosen_ids = set(
        frontier.loc[frontier["presupuesto"] == RECOMMENDED_BUDGET, "candidatos"].iloc[0].split(";")
    )
    selection = candidates.loc[candidates["candidato_id"].isin(chosen_ids)].copy()
    selection.insert(1, "presupuesto_escenario", RECOMMENDED_BUDGET)
    summary = pd.DataFrame([
        {"indicador": "candidatos evaluados", "valor": len(candidates), "unidad": "celdas"},
        {"indicador": "combinaciones factibles", "valor": len(alternatives), "unidad": "top 3 por presupuesto"},
        {"indicador": "presupuesto ilustrativo", "valor": RECOMMENDED_BUDGET, "unidad": "estudios"},
        {"indicador": "bandas en escenario", "valor": selection["banda_territorial"].nunique(), "unidad": "bandas relativas"},
    ])
    return {
        "candidatos": candidates,
        "frontera_presupuesto": frontier,
        "alternativas": alternatives,
        "seleccion_presupuesto_4": selection,
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
        print(frame.to_string(index=False))
    exportar(results)


if __name__ == "__main__":
    main()

