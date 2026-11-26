"""Pruebas de los contratos de agentes y del arnés (`lab.agents`)."""

from __future__ import annotations

from dataclasses import replace

from lab.agents import REGISTRY, AgentContract, contracts_markdown, harness, registry_frame


def contrato(**kwargs) -> AgentContract:
    base: dict = {
        "name": "agente-demo",
        "role": "Rol",
        "purpose": "Propósito",
        "responsibility": "Responsabilidad única de demostración",
        "inputs": ("entrada",),
        "outputs": ("salida",),
        "tools": ("lab.core",),
        "restrictions": ("no hace otra cosa",),
        "acceptance": ("criterio uno", "criterio dos"),
    }
    base.update(kwargs)
    return AgentContract(**base)  # type: ignore[arg-type]


def test_el_arnes_no_encuentra_hallazgos_en_el_registro_del_repositorio():
    assert harness() == []


def test_el_registro_tiene_contenido_y_nombres_unicos():
    assert len(REGISTRY) >= 15
    nombres = [c.name for c in REGISTRY]
    assert len(set(nombres)) == len(nombres)


def test_cada_contrato_exige_revision_humana():
    assert all(c.human_review for c in REGISTRY)


def test_todas_las_coordinaciones_apuntan_a_agentes_existentes():
    nombres = {c.name for c in REGISTRY}
    for contrato_registrado in REGISTRY:
        for destino in contrato_registrado.coordinates_with:
            assert destino in nombres, f"{contrato_registrado.name} → {destino}"


def test_el_registro_cubre_las_capacidades_declaradas_en_el_prompt_maestro():
    roles = " ".join(c.role.lower() + " " + c.purpose.lower() for c in REGISTRY)
    for capacidad in ("problema", "documental", "fuente", "adquisi", "calidad",
                      "exploratorio" if "exploratorio" in roles else "explor",
                      "estadística", "python", "hoja", "sql", "visualiza",
                      "validación", "revisión de código", "evaluaci", "informe",
                      "instruccional", "conocimiento", "auditoría", "privacidad"):
        assert capacidad in roles, f"falta una capacidad para {capacidad!r}"


# --------------------------------------------------------------- reglas del arnés
def test_detecta_nombres_repetidos():
    dos = [contrato(), contrato(responsibility="otra responsabilidad")]
    assert any("nombre repetido" in h for h in harness(dos))


def test_detecta_responsabilidades_duplicadas():
    dos = [contrato(name="uno"), contrato(name="dos")]
    assert any("responsabilidad duplicada" in h for h in harness(dos))


def test_detecta_nombre_que_no_es_kebab_case_minusculas():
    assert any("kebab-case" in h for h in harness([contrato(name="Agente_Demo")]))


def test_detecta_contratos_incompletos():
    assert any("no declara entradas" in h for h in harness([contrato(inputs=())]))
    assert any("no declara salidas" in h for h in harness([contrato(outputs=())]))
    assert any("no declara restricciones" in h for h in harness([contrato(restrictions=())]))
    assert any("no declara herramientas" in h for h in harness([contrato(tools=())]))
    assert any("dos criterios de aceptación" in h
               for h in harness([contrato(acceptance=("solo uno",))]))


def test_detecta_coordinacion_consigo_mismo_y_con_agentes_inexistentes():
    assert any("consigo mismo" in h
               for h in harness([contrato(coordinates_with=("agente-demo",))]))
    assert any("inexistente" in h
               for h in harness([contrato(coordinates_with=("fantasma",))]))


def test_detecta_la_renuncia_a_la_revision_humana():
    assert any("revisión humana" in h for h in harness([contrato(human_review=False)]))


def test_un_contrato_correcto_pasa_el_arnes():
    assert harness([contrato()]) == []


# ------------------------------------------------------------------ presentación
def test_registry_frame_lista_los_contratos():
    tabla = registry_frame()
    assert len(tabla) == len(REGISTRY)
    assert list(tabla.columns)[:3] == ["agente", "rol", "responsabilidad"]
    assert (tabla.criterios_aceptacion >= 2).all()
    assert set(tabla.revision_humana) == {"sí"}
    assert registry_frame([]).empty


def test_contracts_markdown_documenta_cada_contrato_por_completo():
    texto = contracts_markdown()
    for contrato_registrado in REGISTRY:
        assert f"### `{contrato_registrado.name}`" in texto
        assert contrato_registrado.responsibility in texto
        for restriccion in contrato_registrado.restrictions:
            assert restriccion in texto
    assert texto.count("**Criterios de aceptación.**") == len(REGISTRY)
    assert "**Revisión humana.** obligatoria" in texto


def test_as_row_resume_el_contrato():
    fila = replace(contrato(), coordinates_with=()).as_row()
    assert fila["agente"] == "agente-demo"
    assert fila["se_coordina_con"] == "—"
    assert fila["criterios_aceptacion"] == 2
