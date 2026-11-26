"""Contratos de skills, agentes y subagentes, con un arnés que los verifica.

Qué hace
    Declara en código el contrato de cada capacidad especializada del laboratorio
    (propósito, entradas, salidas, herramientas, restricciones, criterios de
    aceptación y con quién se coordina), lo valida y permite ejecutar el arnés que
    comprueba la integridad del conjunto.

Qué NO hace
    No ejecuta modelos de lenguaje ni llama a ningún proveedor. Un contrato es la
    especificación que cualquier plataforma de IA —o una persona— debe cumplir para
    desempeñar ese rol dentro del laboratorio. Esa independencia es deliberada: el
    conocimiento del repositorio no debe quedar atado a un proveedor.

Por qué existe
    Sin contrato, un agente «de calidad de datos» y otro «de exploración» acaban
    haciendo lo mismo con distinto nombre, y nadie puede decir si su salida sirve.
    El arnés detecta responsabilidades duplicadas, salidas sin criterio de aceptación
    y referencias a agentes inexistentes.

Cómo se valida
    `tests/test_agents.py` ejecuta el arnés sobre el registro completo y exige que no
    haya hallazgos, además de probar cada regla con contratos defectuosos.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class AgentContract:
    """Contrato de una capacidad especializada.

    Args:
        name: identificador en kebab-case.
        role: rol en una línea.
        purpose: qué problema resuelve.
        responsibility: responsabilidad única y exclusiva dentro del laboratorio.
        inputs: qué recibe, con formato esperado.
        outputs: qué entrega, con formato esperado.
        tools: módulos del núcleo o herramientas externas que utiliza.
        restrictions: qué no puede hacer.
        acceptance: criterios verificables para aceptar su salida.
        coordinates_with: nombres de otros contratos con los que se encadena.
        human_review: si su salida exige revisión humana antes de usarse.
    """

    name: str
    role: str
    purpose: str
    responsibility: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    tools: tuple[str, ...]
    restrictions: tuple[str, ...]
    acceptance: tuple[str, ...]
    coordinates_with: tuple[str, ...] = ()
    human_review: bool = True

    def as_row(self) -> dict[str, object]:
        return {
            "agente": self.name,
            "rol": self.role,
            "responsabilidad": self.responsibility,
            "entradas": " | ".join(self.inputs),
            "salidas": " | ".join(self.outputs),
            "criterios_aceptacion": len(self.acceptance),
            "revision_humana": "sí" if self.human_review else "no",
            "se_coordina_con": ", ".join(self.coordinates_with) or "—",
        }


#: Registro de contratos. Es la fuente única: la documentación se genera desde aquí.
REGISTRY: tuple[AgentContract, ...] = (
    AgentContract(
        name="clasificador-de-problemas",
        role="Comprensión y clasificación de problemas",
        purpose="Convertir un pedido en lenguaje natural en un problema caracterizado.",
        responsibility="Caracterizar y clasificar el problema recibido.",
        inputs=("enunciado libre del problema", "contexto declarado por la persona"),
        outputs=("ficha de problema con objetivo, restricciones y subproblemas",
                 "etapas de lab.method que corresponden"),
        tools=("lab.method",),
        restrictions=("no adquiere datos", "no propone resultados numéricos"),
        acceptance=("la ficha declara objetivo, restricciones y unidad de análisis",
                    "toda ambigüedad queda listada en lugar de resuelta por supuesto propio"),
        coordinates_with=("investigador-documental", "descubridor-de-fuentes"),
    ),
    AgentContract(
        name="investigador-documental",
        role="Investigación documental y científica",
        purpose="Reunir antecedentes verificables sobre el problema.",
        responsibility="Revisar antecedentes y referencias.",
        inputs=("ficha de problema", "preguntas de investigación"),
        outputs=("revisión de antecedentes con cita y fecha de consulta",
                 "vacíos de conocimiento identificados"),
        tools=("navegador", "lab.knowledge"),
        restrictions=("no inventa fuentes, autores, cifras ni resultados",
                      "no cita una fuente que no pudo abrir"),
        acceptance=("cada afirmación tiene fuente localizable",
                    "se distingue hecho, hipótesis e interpretación"),
        coordinates_with=("clasificador-de-problemas", "gestor-de-conocimiento"),
    ),
    AgentContract(
        name="descubridor-de-fuentes",
        role="Descubrimiento y evaluación de fuentes de datos",
        purpose="Localizar datos aptos para el problema y evaluar su idoneidad.",
        responsibility="Identificar y evaluar fuentes de datos.",
        inputs=("ficha de problema", "variables requeridas"),
        outputs=("catálogo de fuentes con licencia, cobertura, frecuencia y limitaciones",
                 "recomendación justificada con alternativas descartadas"),
        tools=("navegador",),
        restrictions=("no descarga datos personales",
                      "no usa una fuente sin registrar su licencia"),
        acceptance=("cada fuente declara procedencia, licencia y fecha",
                    "se explicita qué variable del problema cubre cada fuente"),
        coordinates_with=("adquisidor-de-datos", "auditor-de-privacidad"),
    ),
    AgentContract(
        name="adquisidor-de-datos",
        role="Adquisición de datos",
        purpose="Obtener los datos y dejarlos inmutables y documentados.",
        responsibility="Adquirir y almacenar datos crudos.",
        inputs=("catálogo de fuentes aprobado",),
        outputs=("datos crudos en data/original con metadatos",
                 "registro del método de adquisición y su fecha"),
        tools=("lab.core", "scripts/generate_data.py"),
        restrictions=("no modifica los datos crudos",
                      "no publica credenciales ni claves de acceso"),
        acceptance=("los datos crudos son reproducibles o están versionados",
                    "existe diccionario y metadatos de procedencia"),
        coordinates_with=("descubridor-de-fuentes", "controlador-de-calidad"),
    ),
    AgentContract(
        name="controlador-de-calidad",
        role="Calidad de datos",
        purpose="Medir el estado de los datos antes de analizarlos.",
        responsibility="Validar los datos contra su contrato y reportar defectos.",
        inputs=("datos crudos", "contrato de tabla"),
        outputs=("informe de hallazgos por regla, columna y cantidad de filas",
                 "propuesta de exclusiones con su justificación"),
        tools=("lab.contracts", "lab.dates"),
        restrictions=("no elimina filas por su cuenta",
                      "no imputa valores sin aprobación explícita"),
        acceptance=("cada defecto indica regla, columna y recuento",
                    "la propuesta de exclusión señala qué indicador afecta"),
        coordinates_with=("adquisidor-de-datos", "explorador-de-datos"),
    ),
    AgentContract(
        name="explorador-de-datos",
        role="Análisis exploratorio",
        purpose="Describir la estructura y el comportamiento de los datos.",
        responsibility="Explorar distribuciones, relaciones y anomalías.",
        inputs=("datos validados", "informe de calidad"),
        outputs=("perfil descriptivo con cobertura por variable",
                 "hipótesis exploratorias marcadas como tales"),
        tools=("lab.metrics", "lab.dates", "lab.viz"),
        restrictions=("no concluye causalidad",
                      "no reporta una media sin su cobertura"),
        acceptance=("toda estadística indica n y unidad",
                    "las anomalías quedan documentadas, no eliminadas en silencio"),
        coordinates_with=("controlador-de-calidad", "estadistico"),
    ),
    AgentContract(
        name="estadistico",
        role="Estadística e inferencia",
        purpose="Cuantificar incertidumbre y contrastar hipótesis.",
        responsibility="Ejecutar e interpretar pruebas estadísticas.",
        inputs=("datos validados", "hipótesis formuladas"),
        outputs=("resultados con estadístico, grados de libertad, valor p y tamaño de efecto",
                 "declaración de supuestos de cada prueba"),
        tools=("lab.stats", "lab.metrics"),
        restrictions=("no aplica una prueba cuyos supuestos no se cumplen",
                      "no presenta el valor p como probabilidad de que la hipótesis sea cierta"),
        acceptance=("cada prueba declara su hipótesis nula en palabras",
                    "se reporta tamaño de efecto además de significancia"),
        coordinates_with=("explorador-de-datos", "validador-independiente"),
    ),
    AgentContract(
        name="desarrollador-python",
        role="Implementación en Python",
        purpose="Construir la solución de forma legible, probada y reproducible.",
        responsibility="Implementar la solución en Python.",
        inputs=("especificación del análisis", "datos validados"),
        outputs=("módulo ejecutable con docstrings", "pruebas que cubren el cálculo"),
        tools=("lab.*", "pytest"),
        restrictions=("no deja credenciales ni rutas absolutas en el código",
                      "no declara una prueba como superada sin ejecutarla"),
        acceptance=("el módulo corre desde la raíz del repositorio",
                    "las pruebas nuevas fallan si se rompe el cálculo"),
        coordinates_with=("revisor-de-codigo", "validador-independiente"),
    ),
    AgentContract(
        name="especialista-excel",
        role="Implementación en hojas de cálculo",
        purpose="Reproducir el análisis con fórmulas y tablas dinámicas auditables.",
        responsibility="Construir la solución en hoja de cálculo.",
        inputs=("datos de entrada", "indicadores a reproducir"),
        outputs=("libro con hojas de entradas, cálculos y resultados",
                 "fórmulas visibles y documentadas"),
        tools=("lab.excel",),
        restrictions=("no pega valores calculados en otra herramienta como si fueran fórmulas",
                      "no usa rangos sin nombre en fórmulas destinadas a revisión"),
        acceptance=("cada indicador se puede recalcular abriendo la celda",
                    "las entradas quedan separadas de los cálculos"),
        coordinates_with=("desarrollador-python", "validador-independiente"),
    ),
    AgentContract(
        name="consultor-sql",
        role="Consultas SQL",
        purpose="Expresar el análisis en SQL como implementación alternativa.",
        responsibility="Escribir y verificar consultas SQL.",
        inputs=("modelo de datos", "indicadores a calcular"),
        outputs=("consultas comentadas", "resultados tabulares"),
        tools=("lab.sqlbridge",),
        restrictions=("no modifica datos en el puente de validación",
                      "no confunde COUNT(*) con COUNT(columna)"),
        acceptance=("la consulta declara su grano y sus denominadores",
                    "el resultado coincide con la implementación en Pandas dentro de tolerancia"),
        coordinates_with=("validador-independiente", "desarrollador-python"),
    ),
    AgentContract(
        name="disenador-de-visualizaciones",
        role="Visualización y comunicación",
        purpose="Hacer legible el resultado para quien decide.",
        responsibility="Diseñar gráficos e informes visuales.",
        inputs=("resultados validados", "audiencia y decisión a apoyar"),
        outputs=("gráficos con título, unidades, período y fuente",
                 "informe o panel con lectura guiada"),
        tools=("lab.viz", "lab.report"),
        restrictions=("no trunca ejes sin declararlo",
                      "no usa solo el color para transmitir un estado"),
        acceptance=("cada gráfico indica unidad, período y fuente",
                    "el texto no afirma más de lo que muestran los datos"),
        coordinates_with=("redactor-de-informes",),
    ),
    AgentContract(
        name="validador-independiente",
        role="Validación independiente de resultados",
        purpose="Recalcular por otra vía y confrontar.",
        responsibility="Verificar resultados con una implementación distinta.",
        inputs=("resultados a verificar", "datos y reglas declaradas"),
        outputs=("tabla de diferencias por indicador",
                 "veredicto por resultado: coincide, difiere o no verificable"),
        tools=("lab.sqlbridge", "lab.metrics", "lab.stats"),
        restrictions=("no reutiliza el código que produjo el resultado original",
                      "no declara verificado lo que no pudo recalcular"),
        acceptance=("toda diferencia queda cuantificada",
                    "lo no verificable se informa como tal, no como aprobado"),
        coordinates_with=("desarrollador-python", "especialista-excel", "consultor-sql"),
    ),
    AgentContract(
        name="revisor-de-codigo",
        role="Revisión de código",
        purpose="Detectar defectos antes de que lleguen a un resultado publicado.",
        responsibility="Revisar el código de la solución.",
        inputs=("diferencias de código", "pruebas existentes"),
        outputs=("hallazgos con archivo, línea y escenario de falla",
                 "sugerencias de prueba faltante"),
        tools=("pytest", "ruff"),
        restrictions=("no reescribe la solución",
                      "no reporta un hallazgo sin escenario concreto de falla"),
        acceptance=("cada hallazgo indica cómo reproducirlo",
                    "los hallazgos se clasifican por severidad"),
        coordinates_with=("desarrollador-python", "auditor-tecnico"),
    ),
    AgentContract(
        name="generador-de-evaluaciones",
        role="Generación de evaluaciones y simulaciones",
        purpose="Producir simulaciones reproducibles con rúbrica.",
        responsibility="Generar instrumentos de evaluación de entrenamiento.",
        inputs=("configuración de la evaluación", "banco de ítems"),
        outputs=("enunciado con rúbrica y entregables", "datasets asociados y semilla"),
        tools=("lab.assessment", "scripts/generate_data.py"),
        restrictions=("no presenta una simulación como prueba oficial",
                      "no reproduce instrumentos reales de selección"),
        acceptance=("la instancia es reproducible con su semilla",
                    "declara qué competencias obligatorias no alcanzó a cubrir"),
        coordinates_with=("disenador-pedagogico", "corrector-de-evaluaciones"),
    ),
    AgentContract(
        name="corrector-de-evaluaciones",
        role="Corrección y retroalimentación",
        purpose="Corregir una entrega con la rúbrica y devolver aprendizaje.",
        responsibility="Corregir entregas y producir retroalimentación.",
        inputs=("entrega", "rúbrica", "solución de referencia"),
        outputs=("nota por criterio con justificación", "plan de reforzamiento"),
        tools=("lab.assessment",),
        restrictions=("no corrige criterios que no evaluó",
                      "no revela la solución antes de cerrar el intento"),
        acceptance=("la nota se reconstruye desde los niveles por criterio",
                    "la retroalimentación señala el error y su corrección"),
        coordinates_with=("generador-de-evaluaciones", "disenador-pedagogico"),
    ),
    AgentContract(
        name="disenador-pedagogico",
        role="Diseño instruccional",
        purpose="Convertir conocimiento en material que se pueda aprender.",
        responsibility="Diseñar y validar el material de aprendizaje.",
        inputs=("tema y nivel", "conocimiento disponible en el laboratorio"),
        outputs=("clase con las secciones obligatorias del estándar",
                 "ejercicios con solución y errores frecuentes"),
        tools=("lab.learning", "lab.knowledge"),
        restrictions=("no publica una clase sin referencias verificables",
                      "no omite los criterios de validación"),
        acceptance=("la clase pasa el validador de secciones obligatorias",
                    "cada fórmula declara variables y unidades"),
        coordinates_with=("gestor-de-conocimiento", "generador-de-evaluaciones"),
    ),
    AgentContract(
        name="gestor-de-conocimiento",
        role="Gestión del conocimiento",
        purpose="Capturar lo aprendido en registros reutilizables.",
        responsibility="Mantener la base de conocimiento.",
        inputs=("informes de casos", "errores y patrones detectados"),
        outputs=("registros atómicos con etiquetas y relaciones",
                 "índice actualizado de la base"),
        tools=("lab.knowledge",),
        restrictions=("no duplica un registro existente",
                      "no registra conocimiento sin fuente dentro del repositorio"),
        acceptance=("cada registro es autocontenido y citable",
                    "no quedan referencias cruzadas rotas"),
        coordinates_with=("investigador-documental", "disenador-pedagogico"),
    ),
    AgentContract(
        name="redactor-de-informes",
        role="Generación de informes",
        purpose="Comunicar el resultado a quien debe decidir.",
        responsibility="Redactar el informe final del caso o la investigación.",
        inputs=("resultados validados", "supuestos y limitaciones"),
        outputs=("informe con las secciones obligatorias del método",
                 "resumen ejecutivo con la decisión que apoya"),
        tools=("lab.report",),
        restrictions=("no concluye más allá de la evidencia",
                      "no omite las limitaciones"),
        acceptance=("el informe separa hecho, inferencia e hipótesis",
                    "incluye supuestos, limitaciones y reproducibilidad"),
        coordinates_with=("disenador-de-visualizaciones", "validador-independiente"),
    ),
    AgentContract(
        name="auditor-tecnico",
        role="Auditoría técnica del repositorio",
        purpose="Comprobar que lo declarado coincide con lo implementado.",
        responsibility="Auditar coherencia entre documentación, código y pruebas.",
        inputs=("repositorio", "documentación publicada"),
        outputs=("informe de incoherencias", "lista de afirmaciones no respaldadas"),
        tools=("lab.catalog", "lab.learning", "pytest"),
        restrictions=("no corrige el código que audita",
                      "no acepta una afirmación sin evidencia ejecutable"),
        acceptance=("cada incoherencia cita archivo y línea",
                    "distingue estado actual de referencia histórica"),
        coordinates_with=("revisor-de-codigo", "auditor-de-privacidad"),
    ),
    AgentContract(
        name="auditor-de-privacidad",
        role="Seguridad y privacidad",
        purpose="Evitar que el laboratorio publique lo que no debe.",
        responsibility="Auditar privacidad, licencias y secretos.",
        inputs=("datasets", "documentación y código a publicar"),
        outputs=("hallazgos de datos personales, licencias y secretos",
                 "registros a excluir antes de publicar"),
        tools=("lab.contracts",),
        restrictions=("no entrega asesoría legal",
                      "no publica el dato sensible dentro del propio hallazgo"),
        acceptance=("cada hallazgo indica archivo y tipo de riesgo",
                    "las licencias de fuentes combinadas quedan evaluadas"),
        coordinates_with=("descubridor-de-fuentes", "auditor-tecnico"),
    ),
)


def registry_frame(contracts: Iterable[AgentContract] = REGISTRY) -> pd.DataFrame:
    """Registro de contratos como tabla."""
    rows = [c.as_row() for c in contracts]
    columns = ["agente", "rol", "responsabilidad", "entradas", "salidas",
               "criterios_aceptacion", "revision_humana", "se_coordina_con"]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows, columns=columns)


def harness(contracts: Iterable[AgentContract] = REGISTRY) -> list[str]:
    """Arnés de verificación del conjunto de contratos.

    Comprueba que:

    1. los nombres y las responsabilidades no se repiten (sin duplicidad de roles);
    2. cada contrato declara entradas, salidas, restricciones y al menos dos
       criterios de aceptación;
    3. las coordinaciones apuntan a contratos existentes y no a sí mismo;
    4. ningún contrato con salida publicable renuncia a la revisión humana.

    Returns:
        Lista de hallazgos. Vacía significa que el conjunto es consistente.
    """
    items = list(contracts)
    findings: list[str] = []
    names = [c.name for c in items]
    for name in sorted({n for n in names if names.count(n) > 1}):
        findings.append(f"nombre repetido: {name}")
    responsibilities = [c.responsibility.strip().lower() for c in items]
    for responsibility in sorted({r for r in responsibilities if responsibilities.count(r) > 1}):
        findings.append(f"responsabilidad duplicada entre agentes: {responsibility!r}")

    known = set(names)
    for contract in items:
        if not contract.name.replace("-", "").isalnum() or contract.name != contract.name.lower():
            findings.append(f"{contract.name}: el nombre debe ir en minúsculas y kebab-case")
        if not contract.inputs:
            findings.append(f"{contract.name}: no declara entradas")
        if not contract.outputs:
            findings.append(f"{contract.name}: no declara salidas")
        if not contract.restrictions:
            findings.append(f"{contract.name}: no declara restricciones")
        if len(contract.acceptance) < 2:
            findings.append(f"{contract.name}: necesita al menos dos criterios de aceptación")
        if not contract.tools:
            findings.append(f"{contract.name}: no declara herramientas")
        for target in contract.coordinates_with:
            if target == contract.name:
                findings.append(f"{contract.name}: se coordina consigo mismo")
            elif target not in known:
                findings.append(f"{contract.name}: se coordina con un agente inexistente ({target})")
        if not contract.human_review:
            findings.append(f"{contract.name}: toda capacidad del laboratorio exige revisión humana")
    return findings


def contracts_markdown(contracts: Iterable[AgentContract] = REGISTRY) -> str:
    """Documentación completa de los contratos, generada desde el registro."""
    items = list(contracts)
    lines = [
        "| Agente | Rol | Responsabilidad única | Coordina con |",
        "| --- | --- | --- | --- |",
    ]
    for c in items:
        lines.append(f"| `{c.name}` | {c.role} | {c.responsibility} | "
                     f"{', '.join(f'`{t}`' for t in c.coordinates_with) or '—'} |")
    lines.append("")
    for c in items:
        lines += [
            f"### `{c.name}`",
            "",
            f"**Rol.** {c.role}",
            "",
            f"**Propósito.** {c.purpose}",
            "",
            f"**Responsabilidad única.** {c.responsibility}",
            "",
            "**Entradas.**",
            "",
        ]
        lines += [f"- {i}" for i in c.inputs]
        lines += ["", "**Salidas.**", ""]
        lines += [f"- {o}" for o in c.outputs]
        lines += ["", "**Herramientas.** " + ", ".join(f"`{t}`" for t in c.tools), ""]
        lines += ["**Restricciones.**", ""]
        lines += [f"- {r}" for r in c.restrictions]
        lines += ["", "**Criterios de aceptación.**", ""]
        lines += [f"- {a}" for a in c.acceptance]
        lines += ["", f"**Revisión humana.** {'obligatoria' if c.human_review else 'no exigida'}", ""]
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover - utilidad de consola
    from lab.console import enable_utf8

    enable_utf8()
    problems = harness()
    print(f"Contratos registrados: {len(REGISTRY)}")
    if problems:
        print("Hallazgos del arnés:")
        for problem in problems:
            print(f"  - {problem}")
        raise SystemExit(1)
    print("Arnés sin hallazgos: el conjunto de contratos es consistente.")
