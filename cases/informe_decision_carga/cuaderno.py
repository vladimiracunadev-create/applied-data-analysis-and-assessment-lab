"""Cuaderno de P16."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.informe_decision_carga import solution as decision  # noqa: E402
from lab.cuaderno import Cuaderno, Paso  # noqa: E402
from lab.diagrama_svg import ACENTO, AZUL, OCRE, TINTA, Etapa, Flujo, Mapa, Rama  # noqa: E402
from lab.hoja_svg import Columna, Hoja  # noqa: E402

PROBLEMA = """
Quien decide no necesita cuarenta tablas, pero reducirlas puede borrar los límites que
hacen honesta la conclusión. P16 debe responder qué estudiar para un nuevo centro de
carga sin afirmar dónde hay más necesidad: los datos describen oferta programada y
proximidad, no transacciones, demanda, seguridad, costos ni predios.
"""

SOLUCION = """
Se seleccionan cuatro indicadores con unidad y lectura, se aplica una regla pública de
cribado a una rejilla geográfica y se separan evidencia, inferencia, hipótesis y lo no
demostrable. `lab.report` exige contexto, método, validación y limitaciones antes de
exportar el informe.
"""

FLUJO = Flujo(titulo="De resultados técnicos a una decisión defendible", etapas=[
    Etapa("P06", ["64 011 salidas", "perfil horario", "oferta programada"], color=TINTA),
    Etapa("P08", ["12 497 paradas", "59,29 % a 300 m", "rejilla geográfica"], color=TINTA),
    Etapa("Sintetizar", ["4 indicadores", "unidad y lectura", "sin doble conteo"], color=AZUL),
    Etapa("Priorizar", ["brecha × distancia", "lista corta", "factibilidad pendiente"], color=OCRE),
    Etapa("Comunicar", ["evidencia", "inferencia", "no demostrable"], color=ACENTO),
])

MAPA = Mapa(centro="P16 · Informe ejecutivo", subtitulo="8 pasos", ramas=[
    Rama("Reducir", ["1 · Auditar entradas", "2 · Cuatro cifras"], color=AZUL),
    Rama("Priorizar", ["3 · Regla", "4 · Lista corta"], color=OCRE),
    Rama("Calibrar", ["5 · Afirmaciones", "6 · Límites"], color=AZUL),
    Rama("Entregar", ["7 · Completitud", "8 · Informe"], color=ACENTO),
])


def construir() -> Cuaderno:
    pasos = [
        Paso("Auditar las tablas de entrada", "El informe consume agregados versionados, no cifras copiadas a mano.",
             "tablas = decision.cargar()\n{k: v.shape for k, v in tablas.items()}",
             "Una hoja por resultado de origen, con nombre, fecha y unidad.",
             "Copiar cuatro números a una diapositiva rompe la trazabilidad hasta su denominador.", mostrar="valor"),
        Paso("Reducir a cuatro indicadores", "Cada cifra incluye unidad y la lectura que sí permite.",
             "resultados = decision.analizar()\nresultados['resumen']",
             "Tabla ejecutiva de cuatro filas; no mezclar porcentaje, hora y conteo en un mismo eje.",
             "64 011 salidas son oferta programada, no viajes de personas.", filas=6),
        Paso("Declarar la regla de prioridad", "La regla combina paradas descubiertas y distancia mediana solo como cribado.",
             "{'formula': 'paradas_sin_cobertura × mediana_m', 'uso': 'ordenar estudios de factibilidad'}",
             "`=(paradas-cubiertas)*mediana_m` y conservar ambos componentes visibles.",
             "Un puntaje sin fórmula publicada convierte criterio en opinión.", mostrar="valor"),
        Paso("Construir una lista corta", "Diez celdas reducen el territorio a revisar con datos adicionales.",
             "resultados['prioridades']", "Ordenar el puntaje descendente y mostrar los componentes, no solo el ranking.",
             "La coordenada de celda no es un predio ni una recomendación de construcción.", filas=10,
             hoja=Hoja(columnas=[Columna("A","celda",115),Columna("B","sin_cobertura",115),Columna("C","mediana_m",95),Columna("D","puntaje",95)],
                       filas=[["−33,40;−70,66","40","582,4","23296"],["−33,62;−70,70","29","663,8","19250"]],
                       celda="D2", formula="=B2*C2", resultado="23296",
                       nota="El puntaje sirve para ordenar investigación, no para estimar beneficio.")),
        Paso("Clasificar cada afirmación", "Hecho calculado, inferencia e hipótesis se leen de forma distinta.",
             "resultados['afirmaciones']", "Columna obligatoria de tipo y otra de respaldo.",
             "Presentar una hipótesis como evidencia es más dañino que omitirla.", filas=8),
        Paso("Escribir lo que no se puede concluir", "Los datos faltantes se vinculan a la decisión que bloquean.",
             "resultados['afirmaciones'].query(\"tipo == 'no demostrable'\")",
             "Sección visible de límites: demanda, red peatonal, predios, costo, seguridad y horario.",
             "Baja cobertura no equivale a alta necesidad.", filas=4),
        Paso("Validar la completitud", "El informe no se exporta si falta una sección obligatoria.",
             "resultados['completitud']", "Lista de verificación con doce secciones y estado sí/no.",
             "Un resumen sin supuestos o limitaciones parece más concluyente de lo que es.", filas=15),
        Paso("Exportar el entregable reproducible", "La misma ejecución escribe tablas y el informe Markdown.",
             "ruta = decision.exportar(resultados)\nstr(ruta / 'informe.md')",
             "Guardar fórmulas, fuentes y fecha en el mismo libro que la portada ejecutiva.",
             "El formato profesional no sustituye el vínculo al cálculo.", mostrar="valor"),
    ]
    return Cuaderno(
        caso="P16", titulo="Informe de una página para quien decide",
        pregunta="¿Qué zonas conviene estudiar para un nuevo centro de carga y qué no se puede afirmar todavía?",
        datos="Resultados reproducibles de P06 y P08; no contiene datos de demanda ni factibilidad de predios.",
        pasos=pasos, contexto={"decision": decision}, problema=PROBLEMA, solucion=SOLUCION,
        flujo=FLUJO, mapa=MAPA,
        cierre=("La entrega produce una lista corta de zonas para factibilidad, no una ubicación aprobada. "
                "La recomendación siguiente es recopilar demanda, red peatonal, horarios, predios, costos y seguridad."),
        aprendizajes=("Reducir no debe borrar denominadores.", "Un ranking necesita fórmula pública.",
                      "Baja cobertura no demuestra necesidad.", "La sección de límites cambia la decisión siguiente."),
        relacionados=(("Informe generado", "resultados/informe.md"),
                      ("P06 · Oferta programada", "../gtfs_red_movilidad/CUADERNO.md"),
                      ("P08 · Cobertura espacial", "../cobertura_de_carga/CUADERNO.md")),
        anterior=("P14-P15 · Evolución", "../evolucion_gtfs/CUADERNO.md"),
        reproducir="python -m cases.informe_decision_carga.solution",
        importes="from cases.informe_decision_carga import solution as decision",
        columnas_excel=("celda", "sin_cobertura", "mediana_m", "puntaje"),
    )
