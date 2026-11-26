"""Pruebas de la metodología universal (`lab.method`)."""

from __future__ import annotations

import pytest

from lab.method import STAGES, MethodRun, stages_markdown


def test_las_etapas_estan_numeradas_en_orden_y_sin_claves_repetidas():
    assert [s.number for s in STAGES] == list(range(1, 19))
    assert len({s.key for s in STAGES}) == 18
    assert all(s.question and s.output for s in STAGES)


def test_una_corrida_nace_con_todas_las_etapas_pendientes():
    run = MethodRun(problem="Medir cumplimiento")
    assert run.coverage() == 0.0
    assert len(run.pending()) == 18
    assert run.pending()[0].key == "recepcion"


def test_completar_exige_evidencia():
    run = MethodRun(problem="x")
    with pytest.raises(ValueError, match="evidencia"):
        run.complete("recepcion")
    with pytest.raises(ValueError, match="evidencia"):
        run.complete("recepcion", evidence=["", ""])


def test_completar_registra_evidencia_y_decisiones():
    run = MethodRun(problem="x")
    record = run.complete("datos", evidence=["data/case_1", "docs/diccionario.md"],
                          decisions="Se excluyen claves desconocidas", notes="revisado")
    assert record.status == "completada"
    assert len(record.evidence) == 2
    assert record.decisions == ["Se excluyen claves desconocidas"]
    assert record.notes == "revisado"
    assert run.coverage() == pytest.approx(1 / 18)


def test_etapa_desconocida_falla_con_mensaje_util():
    run = MethodRun(problem="x")
    with pytest.raises(KeyError, match="Etapa desconocida"):
        run.complete("inexistente", evidence="a")


def test_estado_invalido_se_rechaza():
    run = MethodRun(problem="x")
    with pytest.raises(ValueError, match="Estado inválido"):
        run.set_status("recepcion", "casi")  # type: ignore[arg-type]


def test_no_aplica_exige_motivo_y_sale_del_denominador():
    run = MethodRun(problem="x", stages=STAGES[:2])
    with pytest.raises(ValueError, match="motivo"):
        run.skip("recepcion", "   ")
    run.skip("recepcion", "el problema llegó ya caracterizado")
    run.complete("contexto", evidence="docs/contexto.md")
    assert run.coverage() == 1.0
    assert run.pending() == []


def test_cobertura_de_una_corrida_sin_etapas_aplicables_es_total():
    run = MethodRun(problem="x", stages=STAGES[:1])
    run.skip("recepcion", "no corresponde")
    assert run.coverage() == 1.0


def test_una_corrida_sin_etapas_se_rechaza():
    with pytest.raises(ValueError, match="al menos una etapa"):
        MethodRun(problem="x", stages=[])


def test_exportaciones_contienen_las_etapas_y_los_pendientes():
    run = MethodRun(problem="Problema de prueba", owner="equipo")
    run.complete("recepcion", evidence="docs/enunciado.md")
    payload = run.to_dict()
    assert payload["problem"] == "Problema de prueba"
    assert len(payload["stages"]) == 18
    assert payload["stages"][0]["status"] == "completada"
    markdown = run.to_markdown()
    assert "Problema de prueba" in markdown
    assert "docs/enunciado.md" in markdown
    assert "## Pendientes" in markdown
    assert markdown.count("|") > 18


def test_tabla_de_referencia_incluye_las_dieciocho_etapas():
    table = stages_markdown()
    assert table.count("\n") == 20  # encabezado, separador y 18 filas
    for stage in STAGES:
        assert stage.name in table
