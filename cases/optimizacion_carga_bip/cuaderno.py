"""Cuaderno P20: optimización exploratoria de estudios de carga bip!."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.optimizacion_carga_bip import solution as portfolio  # noqa: E402
from lab.cuaderno import Cuaderno, Paso  # noqa: E402
from lab.diagrama_svg import ACENTO, AZUL, OCRE, TINTA, Etapa, Flujo, Mapa, Rama  # noqa: E402

PROBLEMA = """
P16 produce una lista corta, pero una lista no resuelve qué estudiar con un presupuesto
limitado. P20 formula esa elección como una cartera auditable y mantiene separados el
óptimo matemático, la evidencia observada y la decisión pública que todavía falta.
"""
SOLUCION = """
Se identifican candidatos, se asignan tres bandas relativas de latitud, se enumeran
todas las combinaciones de uno a cinco estudios y se maximiza el puntaje P16 sujeto a
diversidad mínima. La frontera y sus tres mejores alternativas se publican completas.
"""
FLUJO = Flujo(titulo="De lista corta a cartera de estudios", etapas=[
    Etapa("P16", ["10 celdas", "puntaje", "límites"], color=TINTA),
    Etapa("Modelo", ["variable", "objetivo", "restricción"], color=AZUL),
    Etapa("Enumerar", ["presupuesto 1–5", "diversidad", "desempate"], color=OCRE),
    Etapa("Decidir", ["frontera", "alternativas", "no construir"], color=ACENTO),
])
MAPA = Mapa(centro="P20 · Cartera bip!", subtitulo="8 pasos", ramas=[
    Rama("Evidencia", ["1 · Contrato", "2 · Candidatos"], color=AZUL),
    Rama("Formular", ["3 · Variables", "4 · Restricción"], color=OCRE),
    Rama("Resolver", ["5 · Enumerar", "6 · Frontera"], color=AZUL),
    Rama("Interpretar", ["7 · Visualizar", "8 · Límites"], color=ACENTO),
])


def construir() -> Cuaderno:
    pasos = [
        Paso("Validar el contrato heredado de P16", "La optimización sólo es trazable si conserva la fuente y el significado del puntaje.",
             "datos = portfolio.cargar()\ndatos", "Comprobar columnas, coordenadas únicas y puntajes no negativos.",
             "Tratar prioridad como demanda convierte una regla de cribado en una medición inexistente.", filas=10),
        Paso("Crear candidatos y bandas relativas", "Un ID estable permite auditar selecciones; la banda introduce diversidad explícita.",
             "candidatos = portfolio.preparar_candidatos(datos)\ncandidatos[['candidato_id', 'celda_lat', 'celda_lon', 'banda_territorial', 'prioridad_exploratoria']]",
             "Ordenar por puntaje, numerar y dividir el rango de latitud en terciles relativos.",
             "Llamar comuna a la banda inventaría una geografía administrativa.", filas=10),
        Paso("Definir la variable de decisión", "xᵢ vale 1 si la celda i entra en la cartera y 0 en caso contrario.",
             "{'variable': 'x_i ∈ {0,1}', 'objetivo': 'max Σ prioridad_i × x_i', 'presupuesto': 'Σ x_i = k'}",
             "Una columna binaria por candidato; SUMAPRODUCTO calcula el objetivo.",
             "Permitir valores fraccionarios describe medio estudio y cambia el problema.", mostrar="valor"),
        Paso("Hacer visible la diversidad mínima", "Para k=1,2,≥3 se exigen una, dos o tres bandas relativas.",
             "{k: min(k, 3) for k in range(1, 6)}", "Contar bandas distintas entre filas elegidas.",
             "Agregar la restricción después de ver el ganador sería ajustar la regla al resultado.", mostrar="valor"),
        Paso("Enumerar las combinaciones factibles", "Con diez candidatos, revisar exhaustivamente es simple y verificable.",
             "frontera, alternativas = portfolio.optimizar(candidatos)\nalternativas",
             "Generar combinaciones de tamaño k, filtrar diversidad y ordenar por objetivo.",
             "Usar una heurística sin necesidad puede ocultar una cartera mejor.", filas=15),
        Paso("Construir la frontera presupuestaria", "Cada fila conserva el mejor objetivo bajo exactamente k estudios.",
             "frontera", "Seleccionar la primera alternativa de cada presupuesto tras un desempate estable.",
             "Comparar carteras de distinto tamaño sin declarar presupuesto favorece siempre la más grande.", filas=8),
        Paso("Visualizar valor acumulado por presupuesto", "La curva hace visible el incremento, no un beneficio monetario.",
             "frontera[['presupuesto', 'puntaje_total']]", "Línea con presupuesto en X y puntaje exploratorio acumulado en Y.",
             "Etiquetar el eje como rentabilidad atribuye dinero que el modelo no contiene.", filas=8),
        Paso("Separar estudio, factibilidad e inversión", "El escenario de cuatro estudios es ilustrativo y requiere validación externa.",
             "resultados = portfolio.analizar()\nresultados['seleccion_presupuesto_4'][['candidato_id', 'banda_territorial', 'prioridad_exploratoria']]",
             "Publicar selección, regla, límites y datos faltantes en el mismo entregable.",
             "Presentar coordenadas como sitios aprobados excede la evidencia y el alcance de P20.", filas=8),
    ]
    return Cuaderno(
        caso="P20", titulo="Optimización exploratoria de una cartera de estudios para carga bip!",
        pregunta="¿Qué combinación de zonas conviene estudiar primero bajo un presupuesto y una regla de diversidad explícitos?",
        datos="Diez celdas candidatas de P16, derivadas de GTFS DTPM y lugares bip! públicos.",
        pasos=pasos, contexto={"portfolio": portfolio}, problema=PROBLEMA, solucion=SOLUCION,
        flujo=FLUJO, mapa=MAPA,
        cierre="El óptimo selecciona estudios bajo reglas declaradas; no selecciona predios ni autoriza inversión.",
        aprendizajes=("Un modelo hereda los límites de su entrada.", "Las restricciones expresan criterios.", "La enumeración es auditable.", "Óptimo no significa decisión final."),
        relacionados=(("P16 · Lista corta de decisión", "../informe_decision_carga/CUADERNO.md"),
                      ("P17 · Gobernanza de datos", "../gobernanza_datos_dtpm/CUADERNO.md"),
                      ("P18 · Pipeline reproducible", "../etl_gtfs_automatizado/CUADERNO.md")),
        reproducir="python -m cases.optimizacion_carga_bip.solution",
        importes="from cases.optimizacion_carga_bip import solution as portfolio",
        columnas_excel=("candidato_id", "banda_territorial", "prioridad_exploratoria"),
    )

