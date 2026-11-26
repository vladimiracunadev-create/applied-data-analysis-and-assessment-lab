"""Pruebas del caso del calendario de medición (`cases.calendario_medicion.solution`).

Corren **sin red**: el listado de feriados está versionado dentro del caso, que es
precisamente la decisión de diseño que hace el caso reproducible. La descarga desde la
API de tercero se ejerce aparte, contra un servidor falso, para comprobar que valida
antes de guardar.
"""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import pandas as pd
import pytest

from cases.calendario_medicion.solution import (
    MESES_DE_MEDICION,
    MESES_EXCLUIDOS,
    actualizar_feriados,
    analizar,
    aporte_sobre_medibles,
    cargar_feriados,
    clasificar_redundancias,
    comparar_anios,
    construir,
    dias_medibles,
    exportar,
    reglas_oficiales,
    resumen_medicion,
    sensibilidad_invierno,
    validar_feriados,
)
from lab.calendars import easter_sunday, exclusion_report

ANIO = 2026

#: Las ocho reglas de la metodología citada, en su orden.
REGLAS_ESPERADAS = (
    "fin_de_semana", "feriados", "meses_completos", "vacaciones_invierno",
    "semana_fiestas_patrias", "once_de_septiembre", "dia_joven_combatiente",
    "dias_28_y_29",
)


@pytest.fixture(scope="module")
def feriados() -> pd.DataFrame:
    return cargar_feriados()


# -------------------------------------------------------------------------- feriados
def test_el_listado_de_feriados_esta_versionado(feriados):
    assert not feriados.empty
    assert {"fecha", "nombre", "anio", "fuente"} <= set(feriados.columns)
    assert ANIO in set(feriados["anio"])


def test_el_listado_declara_que_su_fuente_no_es_oficial(feriados):
    fuentes = set(feriados["fuente"])
    assert fuentes, "cada fila debe declarar de dónde viene"
    assert any("NO es la fuente oficial" in f for f in fuentes), (
        "la fuente es un tercero y el listado tiene que decirlo"
    )


def test_la_validacion_comprueba_pascua_de_forma_independiente(feriados):
    tabla = validar_feriados(feriados, ANIO)
    pascua = easter_sunday(ANIO)
    viernes = tabla.loc[tabla.comprobacion.str.contains("Viernes Santo")].iloc[0]
    assert viernes.resultado == (pascua - timedelta(days=2)).isoformat()
    assert viernes.veredicto == "sí"
    sabado = tabla.loc[tabla.comprobacion.str.contains("Sábado Santo")].iloc[0]
    assert sabado.veredicto == "sí"


def test_la_validacion_comprueba_los_feriados_de_fecha_fija(feriados):
    tabla = validar_feriados(feriados, ANIO).set_index("comprobacion")
    fila = next(v for k, v in tabla.iterrows() if "fecha fija" in k)
    assert fila.veredicto == "sí", f"faltan feriados fijos: {fila.veredicto}"


def test_la_validacion_declara_lo_que_no_puede_verificar(feriados):
    tabla = validar_feriados(feriados, ANIO)
    movibles = tabla.loc[tabla.comprobacion.str.contains("movibles")].iloc[0]
    assert movibles.veredicto == "declarado"
    assert "no verificable" in movibles.resultado


def test_actualizar_feriados_rechaza_un_listado_que_no_pasa_su_validacion(monkeypatch,
                                                                          tmp_path):
    """Un listado sin el Viernes Santo calculado no se guarda."""
    import urllib.request

    class RespuestaFalsa:
        def __init__(self, payload):
            self._datos = json.dumps(payload).encode("utf-8")

        def read(self):
            return self._datos

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    malo = {"status": "success", "data": [
        {"date": f"{ANIO}-01-01", "title": "Año Nuevo", "inalienable": True},
    ]}
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: RespuestaFalsa(malo))
    destino = tmp_path / "feriados.csv"
    with pytest.raises(ValueError, match="Viernes Santo"):
        actualizar_feriados(ANIO, destino=destino)
    assert not destino.exists(), "un listado que no valida no debe quedar escrito"


def test_actualizar_feriados_guarda_un_listado_valido(monkeypatch, tmp_path):
    import urllib.request

    pascua = easter_sunday(ANIO)
    bueno = {"status": "success", "data": [
        {"date": f"{ANIO}-01-01", "title": "Año Nuevo", "inalienable": True},
        {"date": (pascua - timedelta(days=2)).isoformat(), "title": "Viernes Santo",
         "inalienable": False},
        {"date": (pascua - timedelta(days=1)).isoformat(), "title": "Sábado Santo",
         "inalienable": False},
    ]}

    class RespuestaFalsa:
        def read(self):
            return json.dumps(bueno).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: RespuestaFalsa())
    destino = tmp_path / "feriados.csv"
    ruta = actualizar_feriados(ANIO, destino=destino)
    guardado = pd.read_csv(ruta)
    assert len(guardado) == 3
    assert guardado["validado_contra_pascua"].sum() == 2


def test_un_servicio_sin_datos_se_rechaza(monkeypatch, tmp_path):
    import urllib.request

    class RespuestaFalsa:
        def read(self):
            return json.dumps({"status": "error", "data": []}).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: RespuestaFalsa())
    with pytest.raises(ValueError, match="no devolvió datos"):
        actualizar_feriados(ANIO, destino=tmp_path / "f.csv")


def test_cargar_feriados_explica_como_generarlo(tmp_path):
    with pytest.raises(FileNotFoundError, match="actualizar-feriados"):
        cargar_feriados(tmp_path / "no-existe.csv")


# ---------------------------------------------------------------------------- reglas
def test_las_ocho_reglas_estan_en_el_orden_de_la_metodologia(feriados):
    reglas = reglas_oficiales(ANIO, feriados=feriados)
    assert tuple(r.name for r in reglas) == REGLAS_ESPERADAS


def test_cada_regla_cita_su_fuente(feriados):
    for regla in reglas_oficiales(ANIO, feriados=feriados):
        assert regla.source, f"{regla.name} no declara de dónde sale"
        assert "DIPRES" in regla.source


def test_la_regla_de_invierno_declara_que_es_un_supuesto(feriados):
    invierno = next(r for r in reglas_oficiales(ANIO, feriados=feriados)
                    if r.name == "vacaciones_invierno")
    assert "SUPUESTO" in invierno.description
    assert "supuesto propio" in invierno.source


def test_el_supuesto_de_invierno_cae_en_julio(feriados):
    invierno = next(r for r in reglas_oficiales(ANIO, feriados=feriados)
                    if r.name == "vacaciones_invierno")
    excluidos = construir(ANIO, feriados=feriados).frame
    meses = set(excluidos.loc[excluidos["vacaciones_invierno"], "mes"])
    assert meses == {7}
    assert excluidos["vacaciones_invierno"].sum() == 14, "dos semanas"
    assert invierno.name == "vacaciones_invierno"


# ----------------------------------------------------------------------- calendario
def test_el_calendario_cubre_el_anio_completo(feriados):
    marco = construir(ANIO, feriados=feriados).frame
    assert len(marco) == 365
    assert set(marco["mes"]) == set(range(1, 13))


def test_los_meses_excluidos_quedan_sin_un_solo_dia(feriados):
    marco = construir(ANIO, feriados=feriados).frame
    for mes in MESES_EXCLUIDOS:
        assert marco.loc[marco["mes"].eq(mes), "incluido"].sum() == 0


def test_ningun_fin_de_semana_queda_incluido(feriados):
    incluidos = construir(ANIO, feriados=feriados).included
    assert not incluidos["dia_semana"].isin((5, 6)).any()


def test_ningun_dia_28_o_29_queda_incluido(feriados):
    incluidos = construir(ANIO, feriados=feriados).included
    assert not incluidos["dia"].isin((28, 29)).any()


def test_ningun_feriado_queda_incluido(feriados):
    incluidos = construir(ANIO, feriados=feriados).included
    delanio = set(feriados.loc[feriados["anio"].eq(ANIO), "fecha"])
    fechas = set(incluidos["fecha"].dt.strftime("%Y-%m-%d"))
    assert not (fechas & delanio)


# --------------------------------------------------- el hallazgo: reglas redundantes
def test_el_dia_del_joven_combatiente_es_redundante(feriados):
    """El 29 de marzo ya lo excluye la regla de los días 28 y 29."""
    reporte = exclusion_report(construir(ANIO, feriados=feriados)).set_index("regla")
    assert reporte.loc["dia_joven_combatiente", "excluye"] == 1
    assert reporte.loc["dia_joven_combatiente", "exclusiva"] == 0
    assert reporte.loc["dia_joven_combatiente", "aporte_pct"] == 0.0


def test_el_informe_lista_las_reglas_redundantes():
    redundantes = analizar(ANIO)["reglas_redundantes"]
    assert "dia_joven_combatiente" in set(redundantes["regla"])
    assert redundantes["motivo"].str.contains("ya excluye").all()


def test_el_aporte_al_denominador_real_es_distinto_del_aporte_al_anio(feriados):
    """Una regla puede excluir muchos días del año y ninguno de los que se miden."""
    sobre_el_anio = exclusion_report(
        construir(ANIO, feriados=feriados)
    ).set_index("regla")
    sobre_medibles = aporte_sobre_medibles(ANIO, feriados=feriados).set_index("regla")

    # Excluir enero, febrero y diciembre descarta decenas de días del año…
    assert sobre_el_anio.loc["meses_completos", "exclusiva"] > 40
    # …y ninguno de los medibles, porque no son meses de medición.
    assert sobre_medibles.loc["meses_completos", "dias_medibles_que_quita"] == 0
    assert sobre_medibles.loc["meses_completos", "afecta_al_denominador"] == "NO"


def test_los_fines_de_semana_son_la_regla_que_mas_quita(feriados):
    tabla = aporte_sobre_medibles(ANIO, feriados=feriados)
    assert tabla.iloc[0]["regla"] == "fin_de_semana"
    assert tabla.iloc[0]["dias_medibles_que_quita"] > 20


def test_la_clasificacion_separa_lo_estructural_de_lo_accidental():
    tabla = clasificar_redundancias(comparar_anios((2024, 2025, 2026, 2027)))
    por_regla = tabla.set_index("regla")

    # Estructurales: no afectan en ningún año, por construcción del calendario.
    for regla in ("meses_completos", "vacaciones_invierno", "dia_joven_combatiente"):
        assert por_regla.loc[regla, "clasificacion"] == "redundante estructural"
        assert por_regla.loc[regla, "maximo_que_quita"] == 0

    # Efectivas: quitan días todos los años.
    for regla in ("fin_de_semana", "dias_28_y_29", "semana_fiestas_patrias"):
        assert por_regla.loc[regla, "clasificacion"] == "efectiva"
        assert por_regla.loc[regla, "minimo_que_quita"] > 0

    # Y al menos una accidental, que depende de cómo cayó el calendario.
    assert (tabla["clasificacion"] == "redundante accidental").any()


def test_el_denominador_cambia_entre_anios():
    """Comparar el índice entre años compara promedios sobre denominadores distintos."""
    comparacion = comparar_anios((2024, 2025, 2026, 2027))
    medibles = comparacion["dias_medibles"]
    assert medibles.min() >= 60 and medibles.max() <= 95
    assert medibles.max() - medibles.min() >= 4, (
        "la variación entre años es parte del hallazgo"
    )


# ------------------------------------------------------------------ resumen y cruce
def test_el_resumen_declara_el_denominador_real(feriados):
    valores = resumen_medicion(ANIO, feriados=feriados).set_index("indicador").valor
    assert valores["dias_del_anio"] == 365
    assert valores["dias_laborales"] == 261
    assert valores["dias_medibles"] < valores["dias_elegibles"] < valores["dias_laborales"]
    assert 0 < valores["retencion_sobre_laborales_pct"] < 100


def test_los_dias_medibles_estan_todos_en_meses_de_medicion(feriados):
    marco = dias_medibles(ANIO, feriados=feriados)
    medibles = marco.loc[marco["medible"]]
    assert set(medibles["mes"]) <= set(MESES_DE_MEDICION)
    assert medibles["incluido"].all()


def test_la_sensibilidad_del_supuesto_se_mide(feriados):
    tabla = sensibilidad_invierno(ANIO)
    assert len(tabla) == 5
    base = tabla.loc[tabla["desplazamiento_dias"].eq(0)].iloc[0]
    assert base["diferencia_vs_supuesto"] == 0
    # Mover el supuesto hacia junio, que SÍ es mes de medición, cambia el resultado.
    hacia_junio = tabla.loc[tabla["desplazamiento_dias"].eq(-14)].iloc[0]
    assert hacia_junio["diferencia_vs_supuesto"] < 0, (
        "si las vacaciones cayeran en junio, el supuesto sí importaría"
    )


# -------------------------------------------------------------------------- informe
def test_analizar_devuelve_todas_las_tablas_y_exportar_las_escribe(tmp_path):
    resultados = analizar(ANIO)
    esperadas = {"validacion_feriados", "resumen_calendario", "exclusion_por_regla",
                 "reglas_redundantes", "solapamiento", "por_mes", "resumen_medicion",
                 "aporte_sobre_medibles", "sensibilidad_invierno", "comparacion_anios",
                 "clasificacion_reglas", "dias_medibles"}
    assert set(resultados) == esperadas
    destino = exportar(resultados, destino=tmp_path / "salida")
    assert {p.stem for p in destino.glob("*.csv")} == esperadas


def test_los_resultados_versionados_existen():
    carpeta = Path(__file__).resolve().parents[1] / "cases" / "calendario_medicion" / "resultados"
    assert carpeta.exists(), "los resultados agregados se versionan"
    assert len(list(carpeta.glob("*.csv"))) >= 10
