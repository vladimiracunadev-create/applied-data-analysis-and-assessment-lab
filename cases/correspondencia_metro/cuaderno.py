"""Cuaderno de P03 y P10: conciliación de Metro y correspondencia con buses."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.correspondencia_metro import solution as p10  # noqa: E402
from lab.cuaderno import Cuaderno, Paso  # noqa: E402
from lab.diagrama_svg import ACENTO, AZUL, OCRE, TINTA, Etapa, Flujo, Mapa, Rama  # noqa: E402
from lab.hoja_svg import Columna, Hoja  # noqa: E402

PROBLEMA = """
Dos fuentes públicas describen las estaciones de Metro con granos diferentes: el GTFS
tiene 126 estaciones y el archivo bip! tiene 143 filas, una por estación y línea. La
diferencia no es un error. El problema empieza cuando se cruzan como si cada fila
representara lo mismo.

La conciliación usa dos criterios independientes —nombre normalizado y proximidad— y
convierte sus desacuerdos en casos para revisar. Esto descubre once estaciones del
archivo bip! a más de 500 metros de la ubicación GTFS y una separación de 26,2 km entre
dos filas que dicen «Plaza de Armas». Luego se responde la pregunta operativa: qué
estaciones tienen buses a 200 metros y cuántos servicios distintos las atienden.
"""

SOLUCION = """
Se diagnostica el grano antes del cruce, se reducen las filas bip! a estaciones sin
ocultar su dispersión y se confronta nombre con distancia. Cuatro detectores de calidad
declaran qué comparan y cuál es su punto ciego. Solo después se calculan las paradas y
servicios de bus cercanos. La respuesta se repite con la otra fuente de coordenadas
para medir cuánto depende del proveedor elegido.
"""

FLUJO = Flujo(titulo="Conciliar antes de contar correspondencias", etapas=[
    Etapa("GTFS", ["126 estaciones", "12 497 paradas bus", "jerarquía explícita"], color=TINTA),
    Etapa("bip! Metro", ["143 filas", "una por línea", "dos coordenadas"], color=AZUL),
    Etapa("Conciliar", ["nombre normalizado", "vecino más cercano", "13 desacuerdos"], color=AZUL),
    Etapa("Auditar", ["4 detectores", "punto ciego declarado", "11 desvíos >500 m"], color=OCRE),
    Etapa("Responder", ["126 con bus", "mediana 13 servicios", "sensibilidad a fuente"], color=ACENTO),
])

MAPA = Mapa(centro="P03 + P10 · Metro y buses", subtitulo="9 pasos · 4 detectores", ramas=[
    Rama("Entender", ["1 · Grano", "2 · Conciliación"], color=AZUL),
    Rama("Investigar", ["3 · Criterios discordantes", "4 · Detectores"], color=OCRE),
    Rama("Responder", ["5 · Radio de 200 m", "6 · Servicios", "7 · Prioridades"], color=ACENTO),
    Rama("Desafiar", ["8 · Fuente de coordenadas", "9 · Síntesis"], color=OCRE),
])


def construir() -> Cuaderno:
    """Construye el cuaderno ejecutable de P03 y P10."""
    pasos = [
        Paso(
            titulo="Diagnosticar el grano de las dos fuentes",
            objetivo="126 y 143 se reconcilian explicando qué representa cada fila.",
            pandas="resultados = p10.analizar()\nresultados['grano']",
            excel="Quitar el sufijo de línea al nombre bip! y contar valores distintos antes de cruzar.",
            trampa="Forzar una unión uno a uno elimina 17 filas legítimas de estaciones de combinación.", filas=10,
        ),
        Paso(
            titulo="Conciliar por nombre y por distancia",
            objetivo="Dos criterios independientes permiten medir cobertura y desacuerdo.",
            pandas="resultados['conciliacion']",
            excel="Una columna con nombre normalizado y otra con la distancia mínima; comparar ambos pares.",
            trampa="El nombre encuentra 125 de 126; la fila restante no debe desaparecer en silencio.", filas=14,
        ),
        Paso(
            titulo="Revisar donde los criterios discrepan",
            objetivo="Los trece desacuerdos son el conjunto pequeño que requiere inspección.",
            pandas="resultados['criterios_discrepantes']",
            excel="Filtrar `par_por_nombre <> par_mas_cercano` y ordenar por desvío descendente.",
            trampa="Elegir automáticamente el criterio con más coincidencias puede confirmar una coordenada corrupta.", filas=15,
        ),
        Paso(
            titulo="Declarar el punto ciego de cada detector",
            objetivo="Calidad significa saber qué error puede y qué error no puede observar cada control.",
            pandas="resultados['detectores']",
            excel="Matriz de control: detector, comparación, fuente externa, hallazgos y punto ciego.",
            trampa="UTM y lat/lon pueden estar ambas equivocadas de la misma forma: el detector interno no lo ve.", filas=8,
        ),
        Paso(
            titulo="Medir la correspondencia a 200 metros",
            objetivo="Cada estación se cruza con paradas de bus por distancia haversine.",
            pandas="resultados['correspondencia']",
            excel="Para cada estación, contar paradas cuya distancia sea `<=200` y servicios distintos asociados.",
            formula_excel="=CONTAR.SI.CONJUNTO(estacion;A2;distancia_m;\"<=200\")",
            esperado="126 de 126 estaciones con al menos una parada",
            trampa="Contar filas de horarios multiplica un mismo servicio; la unidad es servicio distinto.", filas=10,
            hoja=Hoja(
                columnas=[Columna("A", "estacion", 145), Columna("B", "paradas", 85), Columna("C", "servicios", 90)],
                filas=[["Santa Lucía", "9", "55"], ["La Moneda", "7", "50"], ["Estación Central", "11", "47"]],
                celda="C2", formula="=FILAS(UNICOS(FILTRAR(servicio;distancia<=200)))", resultado="55",
                nota="Se deduplican servicios; no se cuentan viajes ni filas repetidas.",
            ),
        ),
        Paso(
            titulo="Mostrar la distribución de servicios",
            objetivo="La mediana, el p90 y el máximo evitan resumir toda la red con un único extremo.",
            pandas="resultados['resumen']",
            excel="`MEDIANA`, `PERCENTIL.INC(...;0,9)` y `MAX` sobre servicios distintos por estación.",
            trampa="El máximo de 55 describe Santa Lucía, no la estación típica; la mediana es 13.", filas=12,
        ),
        Paso(
            titulo="Identificar las estaciones con más alternativas",
            objetivo="La tabla prioriza estaciones por servicios distintos y conserva el número de paradas.",
            pandas="resultados['mejores_correspondencias']",
            excel="Ordenar por servicios distintos descendente y mostrar los primeros doce.",
            trampa="Más paradas físicas no implica necesariamente más servicios diferentes.", filas=12,
        ),
        Paso(
            titulo="Medir la sensibilidad a la fuente de coordenadas",
            objetivo="La misma pregunta se recalcula con GTFS y bip! para cuantificar dependencia.",
            pandas="resultados['sensibilidad_a_la_fuente']",
            excel="Dos columnas de conteo, una por fuente, y `=B2<>C2` para marcar cambios.",
            trampa="Con bip!, tres estaciones parecerían no tener bus y 48 cambian su conteo de servicios.", filas=10,
        ),
        Paso(
            titulo="Separar hallazgo de explicación",
            objetivo="El cierre publica evidencia y límites sin atribuir causas no observadas.",
            pandas="resultados['detector_4_contra_gtfs']",
            excel="Lista de revisión con estación, desvío y fuente; no corregir coordenadas en silencio.",
            trampa="Un desvío demuestra inconsistencia entre fuentes, no cuál de las dos es correcta ni por qué.", filas=12,
        ),
    ]
    return Cuaderno(
        caso="P03-P10", titulo="Conciliar Metro y medir correspondencias con buses",
        pregunta="¿Qué estaciones de Metro tienen buses a 200 m y cuánto depende la respuesta de la fuente?",
        datos="GTFS Red Movilidad y el archivo público de estaciones de Metro para carga bip!.",
        pasos=pasos, contexto={"p10": p10}, problema=PROBLEMA, solucion=SOLUCION,
        flujo=FLUJO, mapa=MAPA,
        cierre=("Las 126 estaciones GTFS tienen al menos una parada de bus a 200 m y la mediana es 13 servicios. "
                "Pero 48 estaciones cambian su conteo al usar la coordenada bip!: la fuente es parte del método."),
        aprendizajes=(
            "Dos conteos distintos pueden ser correctos si sus filas tienen granos diferentes.",
            "El desacuerdo entre criterios es información para revisar, no ruido que deba borrarse.",
            "Toda prueba de calidad tiene un punto ciego medible.",
            "Una inconsistencia entre fuentes no autoriza a declarar cuál es la verdadera.",
        ),
        relacionados=(("Hallazgos auditables del caso", "README.md"),
                      ("P01 · Validación interna de coordenadas", "../bip_lugares_carga/CUADERNO.md")),
        anterior=("P09 · Cobertura nocturna", "../carga_nocturna/CUADERNO.md"),
        siguiente=("P11 · Calendario de medición", "../calendario_medicion/CUADERNO.md"),
        reproducir="python -m cases.correspondencia_metro.solution",
        importes="from cases.correspondencia_metro import solution as p10",
        fuentes_datos="gtfs-red-movilidad bip-lugares-carga",
        columnas_excel=("estacion", "paradas", "servicios"),
    )
