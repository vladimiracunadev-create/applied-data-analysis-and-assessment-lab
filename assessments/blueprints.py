"""Configuraciones de evaluación disponibles en el laboratorio.

Cada configuración describe un tipo de evaluación técnica: a qué cargo apunta, qué
herramientas admite, qué competencias debe cubrir sí o sí, cuánto tiempo hay y con
qué rúbrica se corrige. El motor de `lab.assessment` toma una configuración y el
banco de ítems y produce una simulación reproducible.

Todas las configuraciones producen **simulaciones de entrenamiento**. Ninguna
reproduce un instrumento oficial de selección de ninguna institución.
"""

from __future__ import annotations

from lab.assessment import Blueprint, Rubric, RubricCriterion

#: Rúbrica estándar de un ejercicio de gestión de datos. Reparte los 100 puntos
#: según lo que realmente distingue una entrega defendible de una entrega correcta
#: por casualidad: la trazabilidad y la validación pesan tanto como el cálculo.
RUBRICA_GESTION_DATOS = Rubric((
    RubricCriterion(
        "calidad_y_trazabilidad", 25,
        "Los defectos están cuantificados y cada exclusión queda registrada con su efecto.",
    ),
    RubricCriterion(
        "transformacion_y_cruces", 20,
        "Tipos resueltos, cardinalidad controlada y claves desconocidas reportadas.",
    ),
    RubricCriterion(
        "indicadores_correctos", 20,
        "Denominadores correctos, unidades declaradas y totales que cuadran entre tablas.",
    ),
    RubricCriterion(
        "verificacion_en_hoja_de_calculo", 20,
        "Los indicadores se reproducen con fórmulas auditables, no con valores pegados.",
    ),
    RubricCriterion(
        "interpretacion_y_supuestos", 10,
        "Hallazgos clasificados, supuestos explícitos y ninguna causa atribuida sin evidencia.",
    ),
    RubricCriterion(
        "reproducibilidad_y_entrega", 5,
        "El trabajo se vuelve a ejecutar desde cero y los archivos entregados abren bien.",
    ),
))

#: Rúbrica para un ejercicio de análisis y comunicación, donde el peso se desplaza
#: hacia la lectura del resultado.
RUBRICA_ANALISIS = Rubric((
    RubricCriterion("calidad_de_datos", 20,
                    "El estado de los datos se mide antes de analizar."),
    RubricCriterion("analisis", 30,
                    "Los indicadores responden la pregunta planteada."),
    RubricCriterion("visualizacion", 20,
                    "Gráficos con unidad, período, fuente y escala honesta."),
    RubricCriterion("comunicacion", 20,
                    "El informe separa hecho, inferencia e hipótesis."),
    RubricCriterion("limitaciones", 10,
                    "Las limitaciones y la incertidumbre están declaradas."),
))

#: Simulación de cuatro horas orientada al perfil de gestor de datos del sector
#: público. Es el caso prioritario del laboratorio, no su único propósito.
GESTOR_DATOS_TRANSPORTE = Blueprint(
    nombre="Simulación de evaluación técnica — Gestor de datos, sector transporte",
    cargo="Gestor de datos",
    especialidad="Gestión y análisis de datos operacionales",
    industria="Transporte público",
    herramientas=("Excel", "Python", "Pandas", "Google Sheets", "SQL"),
    competencias_obligatorias=(
        "calidad-datos",
        "limpieza-normalizacion",
        "cruce-consolidacion",
        "fechas-horarios",
        "agregacion-indicadores",
        "hojas-de-calculo",
        "validacion-independiente",
        "comunicacion-resultados",
    ),
    dificultad="avanzado",
    minutos=240,
    entregables=(
        "Script o notebook reproducible (`analisis.py` o `analisis.ipynb`).",
        "Libro `resultados.xlsx` con hojas de calidad, indicadores y control de validación.",
        "Informe `informe.md` con tres hallazgos clasificados, supuestos y limitaciones.",
    ),
    rubrica=RUBRICA_GESTION_DATOS,
    permite_ia=False,
)

#: Versión corta de diagnóstico, para medir el punto de partida antes de estudiar.
DIAGNOSTICO_RAPIDO = Blueprint(
    nombre="Evaluación diagnóstica — fundamentos de manejo de datos",
    cargo="Analista de datos",
    especialidad="Fundamentos de manejo de datos",
    industria="Genérica",
    herramientas=("Excel", "Python", "Pandas"),
    competencias_obligatorias=(
        "calidad-datos",
        "fechas-horarios",
        "agregacion-indicadores",
        "lectura-escritura-datos",
    ),
    dificultad="intermedio",
    minutos=90,
    entregables=(
        "Tabla de calidad con defectos cuantificados.",
        "Tabla de indicadores con unidad y denominador declarados.",
    ),
    rubrica=RUBRICA_ANALISIS,
    permite_ia=False,
)

#: Ejercicio de comunicación: datos ya limpios, el desafío es la lectura.
ANALISIS_Y_COMUNICACION = Blueprint(
    nombre="Simulación de análisis y comunicación de resultados",
    cargo="Analista de datos",
    especialidad="Análisis y comunicación",
    industria="Genérica",
    herramientas=("Python", "Excel", "Power BI"),
    competencias_obligatorias=(
        "agregacion-indicadores",
        "visualizacion",
        "comunicacion-resultados",
        "apoyo-decision",
    ),
    dificultad="intermedio",
    minutos=120,
    entregables=(
        "Dos gráficos rotulados con unidad, período y fuente.",
        "Informe de una página con hallazgos clasificados y recomendación proporcional.",
    ),
    rubrica=RUBRICA_ANALISIS,
    permite_ia=False,
)

#: Catálogo por nombre corto, para usarlo desde la línea de comandos.
BLUEPRINTS: dict[str, Blueprint] = {
    "gestor-datos-transporte": GESTOR_DATOS_TRANSPORTE,
    "diagnostico-rapido": DIAGNOSTICO_RAPIDO,
    "analisis-comunicacion": ANALISIS_Y_COMUNICACION,
}


def get(name: str) -> Blueprint:
    """Devuelve una configuración por su nombre corto.

    Raises:
        KeyError: con la lista de nombres válidos, para no obligar a leer el código.
    """
    try:
        return BLUEPRINTS[name]
    except KeyError as exc:
        raise KeyError(
            f"Configuración desconocida: {name!r}. Disponibles: {sorted(BLUEPRINTS)}."
        ) from exc
