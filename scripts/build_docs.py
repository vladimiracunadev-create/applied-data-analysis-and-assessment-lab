"""Genera la documentación derivada desde el código, que es su única fuente de verdad.

Qué produce
    `docs/catalogo-casos.md`      desde `lab.catalog` y los `case.json`
    `docs/agentes.md`             desde `lab.agents.REGISTRY`
    `docs/perfiles.md`            desde `lab.profiles.PROFILES`
    `docs/programa.md`            desde `lab.learning` y los archivos de clase
    `docs/metodologia.md`         desde `lab.method.STAGES`
    `docs/conocimiento.md`        desde `lab.knowledge`

Por qué se genera y no se escribe
    Una tabla de contratos de agentes escrita a mano queda desincronizada del registro
    la primera vez que alguien agrega un agente, y nadie lo nota. Generándola, la
    documentación no puede mentir sobre el código. `tests/test_repo_coherence.py`
    comprueba que lo versionado coincida con lo que este script produce: si alguien
    cambia el código y no regenera, la suite falla.

Uso
    python scripts/build_docs.py            # escribe los archivos
    python scripts/build_docs.py --check    # solo comprueba; código 1 si hay desfase
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lab.agents import REGISTRY, contracts_markdown, registry_frame  # noqa: E402
from lab.catalog import catalog_markdown, competency_matrix, discover_cases  # noqa: E402
from lab.console import enable_utf8  # noqa: E402
from lab.knowledge import KnowledgeBase  # noqa: E402
from lab.learning import (  # noqa: E402
    BLOCKS,
    REQUIRED_SECTIONS,
    coverage_summary,
    discover_lessons,
    learning_map_mermaid,
    program_markdown,
)
from lab.method import STAGES, stages_markdown  # noqa: E402
from lab.profiles import COMPETENCIES, PROFILES, competency_coverage, profiles_markdown  # noqa: E402

AVISO = (
    "<!-- Archivo generado por scripts/build_docs.py. No lo edite a mano: "
    "modifique el código fuente y vuelva a ejecutar el script. -->"
)


def _frame_markdown(frame) -> str:
    if frame.empty:
        return "_Sin filas._\n"
    encabezado = "| " + " | ".join(str(c) for c in frame.columns) + " |"
    separador = "| " + " | ".join("---" for _ in frame.columns) + " |"
    filas = ["| " + " | ".join("" if v is None else str(v) for v in fila) + " |"
             for fila in frame.astype(str).to_numpy()]
    return "\n".join([encabezado, separador, *filas]) + "\n"


# ------------------------------------------------------------------- generadores
def catalogo() -> str:
    casos = discover_cases()
    partes = [
        AVISO, "", "# Catálogo de casos de estudio", "",
        "Casos independientes del laboratorio. Cada uno declara sus metadatos en",
        "`cases/<slug>/case.json`, y `tests/test_catalog.py` exige que las 26 secciones",
        "obligatorias estén presentes: un caso con metadatos incompletos aparece aquí",
        "marcado como tal, no se oculta.", "",
        "## Casos", "",
        catalog_markdown(casos),
        "## Cobertura de competencias", "",
        "Cuántos casos entrenan cada competencia. Las competencias con cero casos están",
        "declaradas en la hoja de ruta como brechas conocidas.", "",
        _frame_markdown(competency_matrix(casos)),
        "## Cómo agregar un caso", "",
        "```powershell",
        "uv run python scripts/new_case.py mi-caso",
        "```", "",
        "Luego complete `cases/mi-caso/case.json` con los 26 campos obligatorios y",
        "`uv run python -m pytest tests/test_catalog.py` para validarlo.", "",
    ]
    return "\n".join(partes)


def agentes() -> str:
    partes = [
        AVISO, "", "# Skills, agentes y subagentes", "",
        f"El laboratorio declara **{len(REGISTRY)} contratos** de capacidades",
        "especializadas. Un contrato es la especificación que cualquier plataforma de",
        "inteligencia artificial —o una persona— debe cumplir para desempeñar ese rol.",
        "", "**Este módulo no ejecuta modelos de lenguaje ni llama a ningún proveedor.**",
        "La independencia es deliberada: el conocimiento del repositorio no debe quedar",
        "atado a un proveedor concreto.", "",
        "## Arnés de verificación", "",
        "`python -m lab.agents` ejecuta el arnés, que comprueba que no haya nombres ni",
        "responsabilidades duplicadas, que cada contrato declare entradas, salidas,",
        "restricciones y al menos dos criterios de aceptación, que las coordinaciones",
        "apunten a contratos existentes y que ninguno renuncie a la revisión humana.",
        "`tests/test_agents.py` exige que el arnés no encuentre hallazgos.", "",
        "## Registro", "",
        _frame_markdown(registry_frame()),
        "## Contratos en detalle", "",
        contracts_markdown(),
    ]
    return "\n".join(partes)


def perfiles() -> str:
    casos = discover_cases()
    competencias_cubiertas = {c for caso in casos for c in caso.get("competencias", [])}
    partes = [
        AVISO, "", "# Perfiles y rutas profesionales", "",
        f"El laboratorio describe **{len(PROFILES)} perfiles** sobre un vocabulario de",
        f"**{len(COMPETENCIES)} competencias**. Cada perfil declara sus competencias",
        "núcleo, su ruta por los bloques del programa y las evidencias que lo demuestran.",
        "", "## Cobertura real por perfil", "",
        "Qué parte del núcleo de cada perfil está cubierta por los casos **implementados**.",
        "No se aspira a 100 % en todos: la columna de faltantes es la lista de trabajo, y",
        "`docs/roadmap.md` declara cada brecha.", "",
        _frame_markdown(competency_coverage(competencias_cubiertas)),
        "## Perfiles", "",
        profiles_markdown(),
        "## Vocabulario de competencias", "",
        "Los casos y los ítems de evaluación declaran competencias de esta lista, de modo",
        "que todo quede cruzable:", "",
    ]
    partes += [f"- `{c}`" for c in COMPETENCIES]
    partes.append("")
    return "\n".join(partes)


def programa() -> str:
    lecciones = discover_lessons()
    partes = [
        AVISO, "", "# Programa de aprendizaje", "",
        f"**{len(lecciones)} clases publicadas** en {len(BLOCKS)} bloques. Cada clase",
        f"debe contener las **{len(REQUIRED_SECTIONS)} secciones** del estándar; una clase",
        "incompleta aparece marcada y `tests/test_learning.py` falla.", "",
        "## Mapa de aprendizaje", "",
        learning_map_mermaid(),
        "## Cobertura por bloque", "",
        _frame_markdown(coverage_summary(lecciones)),
        "## Clases", "",
        program_markdown(lecciones),
        "## Estándar de clase", "",
        "Toda clase del laboratorio contiene, como encabezados de nivel 2:", "",
    ]
    partes += [f"{n}. {texto.capitalize()}" for n, (_, texto) in enumerate(REQUIRED_SECTIONS, 1)]
    partes += [
        "",
        "El validador compara sin distinguir tildes ni mayúsculas, de modo que",
        "«Fórmulas matemáticas explicadas» y «FORMULAS» cuentan igual.", "",
        "```powershell",
        "uv run python -m lab.learning",
        "```", "",
    ]
    return "\n".join(partes)


def metodologia() -> str:
    partes = [
        AVISO, "", "# Metodología universal de resolución de problemas", "",
        f"**{len(STAGES)} etapas**, implementadas en `lab.method` como objetos de",
        "seguimiento auditables. Una etapa no se puede marcar como completada sin",
        "evidencia verificable, y declararla no aplicable exige un motivo escrito.", "",
        "## Etapas", "",
        stages_markdown(),
        "## Uso", "",
        "```python",
        "from datetime import date",
        "from lab.method import MethodRun",
        "",
        'corrida = MethodRun(problem="Medir cumplimiento de la programación",',
        '                    owner="equipo de datos", started=date(2026, 11, 26))',
        'corrida.complete("recepcion", evidence="docs/enunciado.md",',
        '                 decisions="Se acota a octubre de 2026")',
        'corrida.skip("experimentacion", reason="no hay intervención que probar")',
        "",
        "print(corrida.coverage())      # proporción de etapas aplicables completadas",
        "print(corrida.pending())       # qué falta, en orden",
        "print(corrida.to_markdown())   # informe de seguimiento",
        "```", "",
        "## Por qué está implementada y no solo escrita", "",
        "Una metodología en un documento no se puede auditar. Representada como datos, se",
        "puede validar (¿quedaron etapas sin evidencia?), comparar entre casos y exigir en",
        "las pruebas automáticas. La cobertura de una corrida es un número, no una",
        "impresión.", "",
    ]
    return "\n".join(partes)


def indice_conocimiento() -> str:
    base = KnowledgeBase.from_directory()
    estadisticas = {k: v for k, v in base.stats().items() if v}
    partes = [
        AVISO, "", "# Índice de la base de conocimiento", "",
        f"**{len(base)} registros**. Búsqueda: `python -m lab.knowledge \"consulta\"`.", "",
        "## Por tipo", "",
        "| Tipo | Registros |", "| --- | --- |",
    ]
    partes += [f"| {tipo} | {cantidad} |" for tipo, cantidad in sorted(estadisticas.items())]
    partes += ["", "## Registros", "", base.index_markdown(link_prefix="../knowledge/")]
    return "\n".join(partes)


SALIDAS: dict[str, callable] = {
    "docs/catalogo-casos.md": catalogo,
    "docs/agentes.md": agentes,
    "docs/perfiles.md": perfiles,
    "docs/programa.md": programa,
    "docs/metodologia.md": metodologia,
    "docs/conocimiento.md": indice_conocimiento,
}


def build(check: bool = False) -> list[str]:
    """Escribe (o comprueba) la documentación derivada.

    Returns:
        Lista de rutas desincronizadas. Vacía significa que todo está al día.
    """
    desfasados: list[str] = []
    for ruta_relativa, generador in SALIDAS.items():
        destino = ROOT / ruta_relativa
        contenido = generador()
        if check:
            actual = destino.read_text(encoding="utf-8") if destino.exists() else ""
            if actual != contenido:
                desfasados.append(ruta_relativa)
        else:
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(contenido, encoding="utf-8")
    return desfasados


def main() -> None:
    enable_utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="comprueba sin escribir; termina con código 1 si hay desfase")
    args = parser.parse_args()

    desfasados = build(check=args.check)
    if args.check:
        if desfasados:
            print("Documentación derivada desincronizada:")
            for ruta in desfasados:
                print(f"  - {ruta}")
            print("\nEjecute: python scripts/build_docs.py")
            raise SystemExit(1)
        print(f"Documentación derivada al día ({len(SALIDAS)} archivos).")
        return
    for ruta in SALIDAS:
        print(f"escrito {ruta}")


if __name__ == "__main__":
    main()
