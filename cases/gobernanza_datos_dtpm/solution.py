"""P17: auditar la gobernanza de los activos de datos usados en la instancia DTPM.

El archivo ``input.csv`` es un catálogo pedagógico construido desde la procedencia ya
documentada en el repositorio. No es un catálogo oficial del DTPM. Su propósito es
convertir ausencias documentales en brechas medibles sin inventar responsables,
licencias, frecuencias de actualización o políticas de retención.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

CASE_DIR = Path(__file__).resolve().parent
INPUT = CASE_DIR / "input.csv"
RESULTS = CASE_DIR / "resultados"
REQUIRED = {
    "activo_id", "nombre", "publicador", "responsable_operativo", "retencion_meses",
    "licencia_estado", "esquema_estado", "actualizacion_declarada", "criticidad",
}
WEIGHTS = {"baja": 1, "media": 2, "alta": 3}


def cargar(path: Path = INPUT) -> pd.DataFrame:
    """Carga el catálogo y falla con un mensaje útil si rompe su contrato mínimo."""
    frame = pd.read_csv(path)
    missing = sorted(REQUIRED - set(frame.columns))
    if missing:
        raise ValueError(f"El catálogo no contiene las columnas requeridas: {missing}")
    if frame["activo_id"].isna().any() or frame["activo_id"].duplicated().any():
        raise ValueError("activo_id debe ser completo y único")
    unknown = sorted(set(frame["criticidad"]) - set(WEIGHTS))
    if unknown:
        raise ValueError(f"Criticidades desconocidas: {unknown}")
    return frame


def evaluar(frame: pd.DataFrame) -> pd.DataFrame:
    """Calcula cinco brechas explícitas y un riesgo de priorización reproducible.

    El puntaje de brecha suma: licencia no verificada (3), esquema no completo (2),
    actualización no declarada (2), responsable operativo ausente (2) y retención
    ausente (1). Luego se multiplica por el peso de criticidad 1/2/3. No estima la
    probabilidad de un incidente: sólo ordena trabajo documental pendiente.
    """
    audit = frame.copy()
    audit["brecha_licencia"] = (~audit["licencia_estado"].isin(["verificada", "pública"])).astype(int)
    audit["brecha_esquema"] = audit["esquema_estado"].ne("completo").astype(int)
    audit["brecha_actualizacion"] = audit["actualizacion_declarada"].ne("sí").astype(int)
    audit["brecha_responsable"] = audit["responsable_operativo"].eq("no_declarado").astype(int)
    audit["brecha_retencion"] = audit["retencion_meses"].isna().astype(int)
    audit["puntaje_brecha"] = (
        3 * audit["brecha_licencia"]
        + 2 * audit["brecha_esquema"]
        + 2 * audit["brecha_actualizacion"]
        + 2 * audit["brecha_responsable"]
        + audit["brecha_retencion"]
    )
    audit["peso_criticidad"] = audit["criticidad"].map(WEIGHTS)
    audit["puntaje_riesgo"] = audit["puntaje_brecha"] * audit["peso_criticidad"]
    return audit


def analizar(frame: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    """Produce las tablas que sostienen el diagnóstico y su recomendación."""
    audit = evaluar(cargar() if frame is None else frame)
    gaps = [
        "brecha_licencia", "brecha_esquema", "brecha_actualizacion",
        "brecha_responsable", "brecha_retencion",
    ]
    risk = (
        audit[["activo_id", "nombre", "criticidad", "puntaje_brecha", "puntaje_riesgo"]]
        .sort_values(["puntaje_riesgo", "activo_id"], ascending=[False, True])
        .reset_index(drop=True)
    )
    summary = pd.DataFrame({
        "brecha": [column.removeprefix("brecha_") for column in gaps],
        "activos_afectados": [int(audit[column].sum()) for column in gaps],
    }).sort_values(["activos_afectados", "brecha"], ascending=[False, True]).reset_index(drop=True)
    status = pd.DataFrame([
        {"indicador": "activos catalogados", "valor": len(audit), "unidad": "activos"},
        {"indicador": "activos sin responsable operativo declarado",
         "valor": int(audit["brecha_responsable"].sum()), "unidad": "activos"},
        {"indicador": "activos sin retención declarada",
         "valor": int(audit["brecha_retencion"].sum()), "unidad": "activos"},
        {"indicador": "activos con licencia no verificada",
         "valor": int(audit["brecha_licencia"].sum()), "unidad": "activos"},
    ])
    return {"auditoria": audit, "riesgo_por_activo": risk, "brechas": summary, "resumen": status}


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
