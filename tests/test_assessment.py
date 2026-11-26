"""Pruebas del motor de evaluaciones (`lab.assessment`)."""

from __future__ import annotations

import json

import pytest

from assessments.blueprints import BLUEPRINTS, get
from lab.assessment import (
    Blueprint,
    Item,
    Rubric,
    RubricCriterion,
    generate,
    load_items,
    progress_frame,
)


def item(id_: str, competencias=("calidad-datos",), dificultad="intermedio", minutos=30,
         herramientas=("Python",)) -> Item:
    return Item(
        id=id_, enunciado="Haga algo medible.", competencias=tuple(competencias),
        herramientas=tuple(herramientas), dificultad=dificultad, minutos=minutos,
        entregable="Una tabla.", criterios=("El resultado es reproducible.",),
    )


def rubrica() -> Rubric:
    return Rubric((
        RubricCriterion("calculo", 60, "El cálculo es correcto."),
        RubricCriterion("validacion", 40, "El resultado está verificado."),
    ))


def blueprint(**kwargs) -> Blueprint:
    base: dict = {
        "nombre": "Simulación",
        "cargo": "Analista",
        "especialidad": "Datos",
        "industria": "Genérica",
        "herramientas": ("Python",),
        "competencias_obligatorias": ("calidad-datos",),
        "dificultad": "intermedio",
        "minutos": 60,
        "entregables": ("Una tabla.",),
        "rubrica": rubrica(),
    }
    base.update(kwargs)
    return Blueprint(**base)  # type: ignore[arg-type]


# ----------------------------------------------------------------------------- ítems
def test_item_valida_sus_campos():
    with pytest.raises(ValueError, match="Dificultad inválida"):
        item("x", dificultad="imposible")
    with pytest.raises(ValueError, match="minutos positivos"):
        item("x", minutos=0)
    with pytest.raises(ValueError, match="no declara competencias"):
        item("x", competencias=())
    with pytest.raises(ValueError, match="criterios de corrección"):
        Item(id="x", enunciado="e", competencias=("a",), herramientas=("Python",),
             dificultad="intermedio", minutos=10, entregable="t", criterios=())


# --------------------------------------------------------------------------- rúbrica
def test_rubrica_debe_sumar_cien():
    with pytest.raises(ValueError, match="deben sumar 100"):
        Rubric((RubricCriterion("a", 50, "d"),))
    with pytest.raises(ValueError, match="al menos un criterio"):
        Rubric(())
    with pytest.raises(ValueError, match="Criterios repetidos"):
        Rubric((RubricCriterion("a", 50, "d"), RubricCriterion("a", 50, "d")))


def test_la_nota_se_reconstruye_desde_los_niveles():
    r = rubrica()
    assert r.score({"calculo": "logrado", "validacion": "logrado"}) == 100.0
    assert r.score({"calculo": "logrado", "validacion": "no_logrado"}) == 60.0
    assert r.score({"calculo": "parcial", "validacion": "parcial"}) == 50.0


def test_corregir_sin_evaluar_todos_los_criterios_es_un_error():
    with pytest.raises(ValueError, match="Faltan criterios"):
        rubrica().score({"calculo": "logrado"})
    with pytest.raises(KeyError, match="no definido"):
        rubrica().score({"calculo": "casi", "validacion": "logrado"})


def test_rubrica_markdown_incluye_el_total():
    texto = rubrica().to_markdown()
    assert "calculo" in texto and "**100**" in texto


# ------------------------------------------------------------------------ blueprint
def test_blueprint_valida_su_configuracion():
    with pytest.raises(ValueError, match="Dificultad inválida"):
        blueprint(dificultad="imposible")
    with pytest.raises(ValueError, match="minutos debe ser positivo"):
        blueprint(minutos=0)
    with pytest.raises(ValueError, match="al menos una competencia"):
        blueprint(competencias_obligatorias=())
    with pytest.raises(ValueError, match="al menos un entregable"):
        blueprint(entregables=())


# ------------------------------------------------------------------------ generación
def test_la_misma_semilla_produce_la_misma_instancia():
    banco = [item(f"i{n}", minutos=20) for n in range(6)]
    primera = generate(blueprint(), banco, seed=42)
    segunda = generate(blueprint(), banco, seed=42)
    assert [i.id for i in primera.items] == [i.id for i in segunda.items]


def test_semillas_distintas_pueden_producir_instancias_distintas():
    banco = [item(f"i{n}", minutos=25) for n in range(12)]
    conjuntos = {tuple(i.id for i in generate(blueprint(), banco, seed=s).items)
                 for s in range(8)}
    assert len(conjuntos) > 1


def test_se_respeta_el_presupuesto_de_tiempo_con_su_tolerancia():
    banco = [item(f"i{n}", minutos=30) for n in range(20)]
    instancia = generate(blueprint(minutos=60), banco, seed=1, tolerance_pct=10)
    assert instancia.minutos <= 66


def test_no_se_incluyen_items_sobre_el_nivel_declarado():
    banco = [item("facil", dificultad="introductorio"),
             item("duro", dificultad="especializado")]
    instancia = generate(blueprint(dificultad="intermedio"), banco, seed=0)
    assert [i.id for i in instancia.items] == ["facil"]


def test_solo_entran_items_con_herramientas_admitidas():
    banco = [item("python", herramientas=("Python",)),
             item("sas", herramientas=("SAS",))]
    instancia = generate(blueprint(herramientas=("Python", "Excel")), banco, seed=0)
    assert [i.id for i in instancia.items] == ["python"]


def test_la_cobertura_obligatoria_se_satisface_cuando_el_banco_lo_permite():
    banco = [item("a", competencias=("calidad-datos",)),
             item("b", competencias=("sql",)),
             item("c", competencias=("visualizacion",))]
    instancia = generate(
        blueprint(competencias_obligatorias=("calidad-datos", "sql"), minutos=120),
        banco, seed=3,
    )
    assert instancia.uncovered == ()
    assert {"calidad-datos", "sql"} <= set(instancia.competencias())


def test_lo_que_el_banco_no_cubre_se_declara_en_lugar_de_ocultarse():
    banco = [item("a", competencias=("calidad-datos",))]
    instancia = generate(
        blueprint(competencias_obligatorias=("calidad-datos", "geoespacial")),
        banco, seed=0,
    )
    assert instancia.uncovered == ("geoespacial",)
    assert "geoespacial" in instancia.to_markdown()
    assert "todavía no cubre" in instancia.to_markdown()


def test_banco_vacio_o_incompatible_se_rechaza():
    with pytest.raises(ValueError, match="banco de ítems está vacío"):
        generate(blueprint(), [], seed=0)
    with pytest.raises(ValueError, match="Ningún ítem del banco es compatible"):
        generate(blueprint(dificultad="introductorio"),
                 [item("duro", dificultad="avanzado")], seed=0)


def test_el_enunciado_declara_que_es_una_simulacion_y_las_reglas_de_ia():
    instancia = generate(blueprint(), [item("a")], seed=0)
    texto = instancia.to_markdown()
    assert "Simulación de entrenamiento" in texto
    assert "No es una prueba oficial" in texto
    assert "no permitido" in texto
    assert "Semilla de generación: 0" in texto
    assert "## Rúbrica" in texto


def test_la_instancia_expone_su_composicion():
    instancia = generate(blueprint(minutos=120),
                         [item("a", minutos=20), item("b", minutos=30)], seed=0)
    assert instancia.minutos == 50
    tabla = instancia.to_frame()
    assert list(tabla.columns)[:3] == ["item", "dificultad", "minutos"]
    assert len(tabla) == 2
    assert instancia.nivel_promedio == 2.0


# -------------------------------------------------------------------------- progreso
def test_progress_frame_calcula_la_variacion_y_ordena_por_fecha():
    tabla = progress_frame([
        {"fecha": "2026-11-28", "simulacion": "s2", "nota": 78, "minutos": 230},
        {"fecha": "2026-11-27", "simulacion": "s1", "nota": 65, "minutos": 240},
    ])
    assert tabla.simulacion.tolist() == ["s1", "s2"]
    assert tabla.variacion.tolist()[1] == 13
    assert progress_frame([]).empty


def test_progress_frame_exige_las_columnas_minimas():
    with pytest.raises(KeyError, match="nota"):
        progress_frame([{"fecha": "2026-11-27", "simulacion": "s1", "minutos": 10}])


# ------------------------------------------------- estado real del repositorio
def test_el_banco_del_repositorio_carga_y_no_tiene_ids_repetidos():
    banco = load_items()
    assert len(banco) >= 10, "el banco de ítems debe tener contenido real"
    assert len({i.id for i in banco}) == len(banco)


def test_el_banco_declara_criterios_y_trampas_utiles():
    banco = load_items()
    assert all(i.criterios for i in banco)
    con_trampas = [i for i in banco if i.trampas]
    assert len(con_trampas) >= len(banco) // 2


def test_load_items_rechaza_un_archivo_que_no_sea_una_lista(tmp_path):
    (tmp_path / "malo.json").write_text(json.dumps({"id": "x"}), encoding="utf-8")
    with pytest.raises(ValueError, match="debe contener una lista"):
        load_items(tmp_path)
    assert load_items(tmp_path / "no-existe") == []


def test_las_configuraciones_del_repositorio_generan_instancias_reales():
    banco = load_items()
    for nombre, config in BLUEPRINTS.items():
        instancia = generate(config, banco, seed=1)
        assert instancia.items, f"{nombre} no generó ítems"
        assert instancia.minutos <= config.minutos * 1.1
        assert not config.permite_ia, f"{nombre} debe declarar el uso de IA de forma explícita"
        assert "Simulación de entrenamiento" in instancia.to_markdown()


def test_get_informa_las_configuraciones_disponibles():
    assert get("diagnostico-rapido").minutos == 90
    with pytest.raises(KeyError, match="Disponibles"):
        get("inexistente")
