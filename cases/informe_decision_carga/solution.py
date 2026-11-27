"""Construye un informe ejecutivo desde resultados versionados de P06 y P08."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from lab.report import case_report, checklist

ROOT = Path(__file__).resolve().parents[2]
P06 = ROOT / "cases" / "gtfs_red_movilidad" / "resultados"
P08 = ROOT / "cases" / "cobertura_de_carga" / "resultados"
RESULTS = Path(__file__).resolve().parent / "resultados"


def cargar() -> dict[str, pd.DataFrame]:
    rutas = {
        "salidas_por_hora": P06 / "salidas_por_hora.csv",
        "cobertura_por_umbral": P08 / "cobertura_por_umbral.csv",
        "sensibilidad_rodeo": P08 / "sensibilidad_rodeo.csv",
        "por_rejilla": P08 / "por_rejilla.csv",
    }
    faltantes = [str(path) for path in rutas.values() if not path.exists()]
    if faltantes:
        raise FileNotFoundError("Faltan resultados de entrada: " + ", ".join(faltantes))
    return {nombre: pd.read_csv(path) for nombre, path in rutas.items()}


def resumen_ejecutivo(tablas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    horas = tablas["salidas_por_hora"].groupby("hora_reloj", as_index=False)["salidas"].sum()
    punta = horas.loc[horas["salidas"].idxmax()]
    cobertura = tablas["cobertura_por_umbral"].loc[
        tablas["cobertura_por_umbral"]["umbral_m"].eq(300)
    ].iloc[0]
    rodeo = tablas["sensibilidad_rodeo"].loc[
        tablas["sensibilidad_rodeo"]["factor_rodeo"].eq(1.3)
    ].iloc[0]
    return pd.DataFrame([
        {"indicador": "salidas programadas en día laboral", "valor": int(horas["salidas"].sum()),
         "unidad": "salidas", "lectura": "oferta programada, no demanda"},
        {"indicador": "hora de mayor oferta", "valor": int(punta["hora_reloj"]),
         "unidad": "hora", "lectura": f"{int(punta['salidas'])} salidas programadas"},
        {"indicador": "paradas con carga a 300 m en línea recta", "valor": float(cobertura["cobertura_pct"]),
         "unidad": "%", "lectura": "referencia espacial"},
        {"indicador": "paradas con factor de rodeo 1,3", "valor": float(rodeo["cobertura_pct"]),
         "unidad": "%", "lectura": "supuesto, no ruta peatonal observada"},
    ])


def prioridades(tablas: dict[str, pd.DataFrame], limite: int = 10) -> pd.DataFrame:
    """Celdas para estudio de factibilidad, no sitios recomendados automáticamente."""
    rejilla = tablas["por_rejilla"].copy()
    rejilla["paradas_sin_cobertura"] = rejilla["paradas"] - rejilla["cubiertas"]
    rejilla["prioridad_exploratoria"] = (
        rejilla["paradas_sin_cobertura"] * rejilla["mediana_m"]
    ).round(1)
    return (rejilla.sort_values(["prioridad_exploratoria", "paradas_sin_cobertura"],
                                ascending=False)
            .head(limite)[["celda_lat", "celda_lon", "paradas", "cubiertas",
                           "paradas_sin_cobertura", "mediana_m", "cobertura_pct",
                           "parada_mas_lejana", "prioridad_exploratoria"]]
            .reset_index(drop=True))


def afirmaciones() -> pd.DataFrame:
    return pd.DataFrame([
        {"tipo": "evidencia", "afirmacion": "59,29 % de las paradas está a 300 m en línea recta.",
         "respaldo": "P08, 7 409 de 12 497 paradas."},
        {"tipo": "inferencia", "afirmacion": "Las celdas con muchas paradas descubiertas ameritan estudio de factibilidad.",
         "respaldo": "Supuesto: cobertura espacial es criterio de cribado, no decisión final."},
        {"tipo": "hipotesis", "afirmacion": "Un nuevo centro en esas zonas podría reducir la brecha.",
         "respaldo": "Requiere demanda, predios, seguridad, costo y red peatonal."},
        {"tipo": "no demostrable", "afirmacion": "Esas zonas tienen mayor necesidad de carga.",
         "respaldo": "No hay transacciones, saldo, demanda ni origen-destino."},
    ])


def construir_informe(tablas: dict[str, pd.DataFrame]):
    resumen = resumen_ejecutivo(tablas)
    focos = prioridades(tablas, 5)
    informe = case_report(
        "Dónde estudiar el próximo centro de carga bip!",
        report_date=date(2026, 11, 26),
        disclaimer="Cribado territorial con oferta programada y proximidad; no es una decisión de inversión.",
    )
    informe.add("contexto", "La red tiene 12 497 paradas de embarque y 1 927 lugares de carga abiertos publicados.")
    informe.add("problema", "Priorizar zonas para estudiar un nuevo centro sin confundir baja cobertura con demanda demostrada.")
    informe.add("objetivos", "Resumir oferta, medir cobertura y producir una lista corta de celdas para factibilidad.")
    informe.add("datos", "Resultados reproducibles de P06 y P08; GTFS vigente y lugares bip! públicos.")
    informe.add("metodologia", "Cobertura haversine a 300 m; rejilla de 0,01°; prioridad exploratoria = paradas descubiertas × distancia mediana.")
    informe.add("supuestos", "300 m es referencia; factor de rodeo 1,3 es sensibilidad; una celda no es un predio.")
    informe.add_table("resultados", resumen, "Cuatro cifras para la decisión:")
    informe.add("validacion", "P06 valida el total por dos caminos; P08 confronta fórmulas y representaciones de coordenadas.")
    informe.add("interpretacion", "Las celdas superiores son zonas para estudiar, no ubicaciones aprobadas.")
    informe.add("limitaciones", "Faltan demanda, transacciones, red peatonal, seguridad, disponibilidad de predios, costos y horarios completos.")
    informe.add_table("conclusiones", focos, "Lista corta para estudio de factibilidad:")
    informe.add("reproducibilidad", "python -m cases.informe_decision_carga.solution")
    informe.claim("evidencia", "La cobertura en línea recta a 300 m es 59,29 %.", "P08: 7 409/12 497.")
    informe.claim("inferencia", "Las celdas priorizadas ameritan revisión.", "Regla declarada de cribado territorial.")
    informe.claim("hipotesis", "Un nuevo centro podría reducir la brecha.", "Debe contrastarse con demanda y factibilidad.")
    return informe


def analizar() -> dict[str, pd.DataFrame]:
    tablas = cargar()
    informe = construir_informe(tablas)
    return {"resumen": resumen_ejecutivo(tablas), "prioridades": prioridades(tablas),
            "afirmaciones": afirmaciones(),
            "completitud": checklist(informe.required, informe.sections)}


def exportar(resultados: dict[str, pd.DataFrame], destino: Path = RESULTS) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    tablas = cargar()
    construir_informe(tablas).write(destino / "informe.md")
    for nombre, tabla in resultados.items():
        tabla.to_csv(destino / f"{nombre}.csv", index=False, encoding="utf-8")
    return destino


def main() -> None:
    resultados = analizar()
    for nombre, tabla in resultados.items():
        print(f"\n=== {nombre.title()} ===")
        print(tabla.to_string(index=False))
    exportar(resultados)


if __name__ == "__main__":
    main()
