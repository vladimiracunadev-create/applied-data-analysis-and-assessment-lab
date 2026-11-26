"""Pruebas de los perfiles profesionales (`lab.profiles`)."""

from __future__ import annotations

from pathlib import Path

import pytest

from lab.catalog import discover_cases
from lab.learning import BLOCK_TITLES
from lab.profiles import (
    COMPETENCIES,
    PROFILES,
    Profile,
    competency_coverage,
    profiles_frame,
    profiles_markdown,
)


def perfil(**kwargs) -> Profile:
    base: dict = {
        "slug": "demo",
        "name": "Perfil de demostración",
        "focus": "Hacer algo concreto.",
        "core": ("calidad-datos",),
        "supporting": ("sql",),
        "tools": ("Python",),
        "blocks": ("00-fundamentos",),
        "evidence": ("un caso resuelto",),
    }
    base.update(kwargs)
    return Profile(**base)  # type: ignore[arg-type]


def test_el_vocabulario_de_competencias_no_tiene_repetidos():
    assert len(set(COMPETENCIES)) == len(COMPETENCIES)
    assert all(c == c.lower() and " " not in c for c in COMPETENCIES)


def test_los_perfiles_del_repositorio_son_consistentes():
    assert len(PROFILES) >= 10
    slugs = [p.slug for p in PROFILES]
    assert len(set(slugs)) == len(slugs)
    for p in PROFILES:
        assert p.core, f"{p.slug} no declara competencias núcleo"
        assert p.evidence, f"{p.slug} no declara evidencias"
        assert set(p.blocks) <= set(BLOCK_TITLES)


def test_un_perfil_con_competencia_inexistente_se_rechaza():
    with pytest.raises(ValueError, match="competencias no declaradas"):
        perfil(core=("telepatia",))


def test_una_competencia_no_puede_ser_nucleo_y_apoyo_a_la_vez():
    with pytest.raises(ValueError, match="núcleo y apoyo"):
        perfil(core=("sql",), supporting=("sql",))


def test_un_perfil_sin_evidencias_no_es_verificable():
    with pytest.raises(ValueError, match="sin evidencias no es verificable"):
        perfil(evidence=())


def test_un_bloque_inexistente_se_rechaza():
    with pytest.raises(ValueError, match="bloques inexistentes"):
        perfil(blocks=("99-inventado",))


def test_profiles_frame_describe_la_ruta_de_cada_perfil():
    tabla = profiles_frame()
    assert len(tabla) == len(PROFILES)
    assert list(tabla.columns)[:3] == ["perfil", "nombre", "foco"]
    assert tabla.ruta.str.contains("→").any()
    assert (tabla.competencias_nucleo > 0).all()
    assert profiles_frame([]).empty


def test_competency_coverage_calcula_lo_cubierto_y_lo_que_falta():
    cobertura = competency_coverage(
        ["calidad-datos"], [perfil(core=("calidad-datos", "sql"), supporting=())]
    )
    fila = cobertura.iloc[0]
    assert fila.nucleo == 2
    assert fila.cubiertas == 1
    assert fila.cobertura_pct == 50.0
    assert "sql" in fila.faltantes


def test_competency_coverage_sin_faltantes_lo_declara_con_guion():
    cobertura = competency_coverage(["calidad-datos"], [perfil(core=("calidad-datos",))])
    assert cobertura.iloc[0].faltantes == "—"
    assert cobertura.iloc[0].cobertura_pct == 100.0


def test_profiles_markdown_documenta_cada_perfil():
    texto = profiles_markdown()
    for p in PROFILES:
        assert f"(`{p.slug}`)" in texto
        assert p.focus in texto
        for evidencia in p.evidence:
            assert evidencia in texto


# ------------------------------------------------- estado real del repositorio
def test_la_cobertura_real_de_los_perfiles_se_puede_informar():
    competencias = {c for caso in discover_cases() for c in caso.get("competencias", [])}
    assert competencias, "los casos deben declarar competencias"
    cobertura = competency_coverage(competencias)
    assert len(cobertura) == len(PROFILES)
    # No se exige cobertura total: lo que se exige es que el número sea real y que los
    # perfiles con cobertura parcial declaren qué les falta.
    assert (cobertura.cobertura_pct >= 0).all() and (cobertura.cobertura_pct <= 100).all()
    parciales = cobertura.loc[cobertura.cobertura_pct < 100]
    assert (parciales.faltantes != "—").all()


def test_el_caso_prioritario_cubre_casi_todo_el_perfil_de_gestor_de_datos():
    # El caso de transporte es la prioridad declarada del laboratorio. No se exige
    # cobertura total: se exige que la cobertura sea alta y que lo que falte esté
    # declarado en la hoja de ruta, en lugar de quedar como una promesa implícita.
    transporte = next(c for c in discover_cases() if c.slug == "transport")
    gestor = next(p for p in PROFILES if p.slug == "gestor-de-datos")
    cubiertas = set(gestor.core) & set(transporte.get("competencias", []))
    faltantes = sorted(set(gestor.core) - cubiertas)
    assert len(cubiertas) / len(gestor.core) >= 0.85, f"cobertura insuficiente: {faltantes}"

    hoja_de_ruta = (Path(__file__).resolve().parents[1] / "docs" / "roadmap.md").read_text(
        encoding="utf-8"
    )
    sin_declarar = [c for c in faltantes if c not in hoja_de_ruta]
    assert not sin_declarar, (
        f"competencias del núcleo sin caso y sin declarar en docs/roadmap.md: {sin_declarar}"
    )
