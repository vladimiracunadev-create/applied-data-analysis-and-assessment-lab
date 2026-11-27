"""Regresiones de los casos que cerraron P07 y P12–P16."""

from __future__ import annotations

import zipfile

import pandas as pd

from cases.evolucion_gtfs import solution as evolucion
from cases.frecuencia_programada import solution as frecuencia
from cases.informe_decision_carga import solution as decision
from cases.rendimiento_gtfs import solution as rendimiento


def _zip_csv(path, nombre: str, contenido: str) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(nombre, contenido)


def test_benchmark_completo_y_bloques_coinciden_en_cada_clave(tmp_path):
    feed = tmp_path / "feed.zip"
    _zip_csv(feed, "stop_times.txt", "trip_id,stop_id\nT1,A\nT1,B\nT2,A\n")

    completo, _ = rendimiento.pandas_completo(feed)
    bloques, meta = rendimiento.pandas_bloques(feed, chunksize=2)

    pd.testing.assert_series_equal(completo, bloques)
    assert meta["bloques"] == 2
    assert completo.to_dict() == {"A": 2, "B": 1}


def test_frecuencia_separa_programa_de_icf_observado():
    tablas = {
        "frequencies": pd.DataFrame({
            "trip_id": ["T1", "T2"], "start_time": ["08:00:00", "08:30:00"],
            "end_time": ["09:00:00", "09:30:00"], "headway_secs": ["600", "0"],
        }),
        "trips": pd.DataFrame({
            "route_id": ["R1", "R2"], "service_id": ["L", "L"],
            "trip_id": ["T1", "T2"], "direction_id": ["0", "1"],
        }),
        "routes": pd.DataFrame({
            "route_id": ["R1", "R2"], "route_short_name": ["1", "2"],
            "route_type": ["3", "3"],
        }),
    }
    ventanas = frecuencia.ventanas_programadas(tablas)
    alcance = frecuencia.alcance_icf(ventanas).set_index("componente")

    assert ventanas["valida"].tolist() == [True, False]
    assert alcance.loc["salidas programadas", "valor"] == 6
    assert alcance.loc["ICF oficial", "calculable_con_gtfs"] == "NO"
    assert pd.isna(alcance.loc["ICF oficial", "valor"])


def test_comparacion_historica_filtra_solo_paradas_de_embarque():
    a = {
        "routes": pd.DataFrame({"route_id": ["R1", "R2"]}),
        "stops": pd.DataFrame({"stop_id": ["A", "X"], "location_type": ["0", "1"]}),
    }
    b = {
        "routes": pd.DataFrame({"route_id": ["R1", "R3"]}),
        "stops": pd.DataFrame({"stop_id": ["A", "B", "X"], "location_type": ["0", "0", "3"]}),
    }
    tabla = evolucion.comparar_identidades(a, b)
    paradas = tabla.loc[tabla["entidad"].eq("paradas de embarque")].set_index("cambio")

    assert paradas.loc["permanece", "cantidad"] == 1
    assert paradas.loc["aparece", "cantidad"] == 1
    assert paradas.loc["desaparece", "cantidad"] == 0


def test_informe_de_decision_esta_completo_y_no_convierte_brecha_en_demanda():
    tablas = decision.cargar()
    informe = decision.construir_informe(tablas)
    afirmaciones = decision.afirmaciones()

    assert informe.missing() == []
    assert "demanda" in informe.sections["limitaciones"]
    assert "no demostrable" in set(afirmaciones["tipo"])
    assert len(decision.prioridades(tablas)) == 10
