"""Cuaderno P19: red bipartita de correspondencias Metro–bus."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.red_correspondencias_dtpm import solution as network  # noqa: E402
from lab.cuaderno import Cuaderno, Paso  # noqa: E402
from lab.diagrama_svg import ACENTO, AZUL, OCRE, TINTA, Etapa, Flujo, Mapa, Rama  # noqa: E402

PROBLEMA = """
Una estación con muchos servicios cercanos y un servicio que conecta muchas estaciones
son dos grados distintos. P19 modela ambos sin convertir la estructura programada en
una afirmación sobre pasajeros, puntualidad o capacidad.
"""
SOLUCION = """
Se transforma cada lista de servicios de P03/P10 en aristas únicas, se calculan grados
en ambos lados y se retiran servicios por grado descendente en cinco escenarios. Cada
resultado puede reconstruirse desde la tabla de aristas.
"""
FLUJO = Flujo(titulo="De correspondencias a red bipartita", etapas=[
    Etapa("P03/P10", ["126 estaciones", "servicios cercanos", "radio 200 m"], color=TINTA),
    Etapa("Aristas", ["estación", "servicio", "sin duplicados"], color=AZUL),
    Etapa("Grados", ["por estación", "por servicio", "ranking"], color=OCRE),
    Etapa("Escenarios", ["retiro", "conexiones", "límites"], color=ACENTO),
])
MAPA = Mapa(centro="P19 · Red DTPM", subtitulo="8 pasos", ramas=[
    Rama("Modelo", ["1 · Grano", "2 · Aristas"], color=AZUL),
    Rama("Medidas", ["3 · Grado servicio", "4 · Grado estación"], color=OCRE),
    Rama("Escenarios", ["5 · Regla", "6 · Resultados"], color=AZUL),
    Rama("Interpretar", ["7 · Visualizar", "8 · Límites"], color=ACENTO),
])


def construir() -> Cuaderno:
    pasos = [
        Paso("Declarar los dos tipos de nodo", "Estación y servicio no son intercambiables.",
             "estaciones = network.cargar()\nestaciones[['stop_id', 'stop_name', 'servicios_distintos']]",
             "Una tabla de estaciones y otra de servicios; declarar el grano.", "Usar el nombre de estación como ID fusiona homónimos.", filas=8),
        Paso("Convertir listas en aristas", "Una relación por fila hace auditable cualquier medida de red.",
             "aristas = network.aristas(estaciones)\naristas", "Dividir por coma y expandir filas; quitar duplicados por par.",
             "Contar el texto separado por comas incluye espacios y duplicados.", filas=10),
        Paso("Calcular el grado de cada servicio", "El grado cuenta estaciones distintas conectadas.",
             "resultados = network.analizar()\nresultados['servicios_centrales']", "`CONTARA(UNICOS(FILTRAR(estacion;servicio=actual)))`.",
             "Contar aristas sin deduplicar sobrestima servicios repetidos.", filas=15),
        Paso("Calcular el grado de cada estación", "La medida inversa cuenta alternativas programadas cercanas.",
             "resultados['grado_por_estacion']", "Tabla dinámica: estación en filas y servicio como recuento distinto.",
             "Más servicios no implica más frecuencia ni capacidad.", filas=10),
        Paso("Publicar la regla de retiro", "Los escenarios retiran primero los servicios de mayor grado, con desempate por ID.",
             "{'orden': 'estaciones_conectadas descendente, servicio ascendente', 'escenarios': [0, 1, 3, 5, 10]}",
             "Ordenar la tabla de grado y marcar los primeros K.", "Cambiar el criterio entre escenarios invalida la comparación.", mostrar="valor"),
        Paso("Recalcular cinco escenarios", "Cada escenario vuelve a contar aristas y estaciones con alternativa.",
             "resultados['escenarios']", "Excluir servicios marcados y recalcular, no restar promedios.",
             "Aristas perdidas no son pasajeros afectados.", filas=8),
        Paso("Visualizar los servicios de mayor alcance", "La gráfica muestra grado estructural con fuente y unidad.",
             "resultados['servicios_centrales'][['servicio', 'estaciones_conectadas']]", "Barras horizontales ordenadas; no usar un eje sin unidad.",
             "Una barra alta no demuestra importancia social.", filas=15),
        Paso("Escribir lo que el modelo no observa", "Los límites definen la siguiente fuente necesaria.",
             "{'no_observa': ['pasajeros', 'GPS', 'capacidad', 'puntualidad', 'secuencia completa'], 'sí_observa': 'correspondencia programada por proximidad'}",
             "Bloque visible de alcance y fuentes faltantes.", "Llamar resiliencia operacional a este escenario excede la evidencia.", mostrar="valor"),
    ]
    return Cuaderno(
        caso="P19", titulo="Estructura de la red programada de correspondencias Metro–bus",
        pregunta="¿Qué servicios conectan más estaciones y cómo cambia la red programada al retirarlos?",
        datos="Resultado reproducible de P03/P10 basado en GTFS DTPM y lugares bip! públicos.",
        pasos=pasos, contexto={"network": network}, problema=PROBLEMA, solucion=SOLUCION,
        flujo=FLUJO, mapa=MAPA,
        cierre="El modelo mide relaciones programadas; la operación real requiere demanda, GPS y capacidad.",
        aprendizajes=("El grano define el grafo.", "Grado no es demanda.", "Escenarios requieren regla fija.", "Las aristas preservan trazabilidad."),
        relacionados=(("P03/P10 · Fuente de correspondencias", "../correspondencia_metro/CUADERNO.md"),
                      ("P18 · Pipeline de datos", "../etl_gtfs_automatizado/CUADERNO.md")),
        reproducir="python -m cases.red_correspondencias_dtpm.solution",
        importes="from cases.red_correspondencias_dtpm import solution as network",
        columnas_excel=("stop_id", "stop_name", "servicio"),
    )
