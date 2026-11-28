"""Pruebas de P20: cartera exploratoria de estudios de carga bip!."""

from cases.optimizacion_carga_bip import solution


def test_candidatos_tienen_id_y_tres_bandas_relativas():
    candidates = solution.preparar_candidatos(solution.cargar())
    assert candidates["candidato_id"].is_unique
    assert set(candidates["banda_territorial"]) == {"sur", "centro", "norte"}


def test_frontera_respeta_presupuesto_y_diversidad():
    candidates = solution.preparar_candidatos(solution.cargar())
    frontier, _ = solution.optimizar(candidates)
    for row in frontier.itertuples(index=False):
        assert len(row.candidatos.split(";")) == row.presupuesto
        assert row.zonas_representadas >= min(row.presupuesto, 3)


def test_objetivo_crece_con_el_presupuesto():
    frontier = solution.analizar()["frontera_presupuesto"]
    assert frontier["puntaje_total"].is_monotonic_increasing


def test_resultado_no_inventa_demanda_ni_costos():
    results = solution.analizar()
    assert len(results["seleccion_presupuesto_4"]) == solution.RECOMMENDED_BUDGET
    assert "demanda" not in set(results["resumen"]["indicador"])
    assert "costo" not in set(results["resumen"]["indicador"])

