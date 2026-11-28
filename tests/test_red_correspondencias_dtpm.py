"""Pruebas de P19: red programada de correspondencias."""

from cases.red_correspondencias_dtpm import solution


def test_aristas_son_unicas_y_reconstruyen_grados():
    edges = solution.aristas(solution.cargar())
    assert not edges.duplicated(["stop_id", "servicio"]).any()
    results = solution.analizar()
    expected = edges.groupby("servicio")["stop_id"].nunique()
    actual = results["servicios_centrales"].set_index("servicio")["estaciones_conectadas"]
    for service, value in actual.items():
        assert value == expected[service]


def test_escenarios_pierden_aristas_de_forma_monotona():
    scenarios = solution.analizar()["escenarios"]
    assert scenarios["aristas_restantes"].is_monotonic_decreasing
    assert scenarios["aristas_perdidas_pct"].is_monotonic_increasing


def test_resumen_no_inventa_demanda():
    results = solution.analizar()
    assert len(results["aristas"]) > 0
    assert "pasajeros" not in set(results["resumen"]["indicador"])
