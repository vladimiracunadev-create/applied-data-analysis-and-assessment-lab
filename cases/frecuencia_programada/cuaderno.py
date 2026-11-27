"""Cuaderno de P12 y P13."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.frecuencia_programada import solution as frecuencia  # noqa: E402
from lab.cuaderno import Cuaderno, Paso  # noqa: E402
from lab.diagrama_svg import ACENTO, AZUL, OCRE, TINTA, Etapa, Flujo, Mapa, Rama  # noqa: E402
from lab.hoja_svg import Columna, Hoja  # noqa: E402

PROBLEMA = """
El ICF oficial parece una razón simple, pero su numerador y denominador son mediciones
GPS. El GTFS solo contiene el programa. Confundir ambos convierte una promesa de oferta
en una medición de cumplimiento inexistente. El mismo archivo sí permite contestar P13:
cómo se distribuyen los intervalos programados y qué servicios tienen mayor espera.
"""

SOLUCION = """
Se validan las ventanas, se calculan sus salidas con fin exclusivo y se construye una
matriz de alcance del ICF. La distribución se resume con percentiles y tres unidades de
análisis. La punta mañana se filtra por intersección temporal, no por hora de inicio.
"""

FLUJO = Flujo(titulo="Programa disponible, cumplimiento ausente", etapas=[
    Etapa("GTFS", ["14 520 ventanas", "inicio, fin, intervalo", "servicio y sentido"], color=TINTA),
    Etapa("Validar", ["tiempos parseables", "intervalo positivo", "fin no anterior"], color=AZUL),
    Etapa("Describir", ["percentiles", "punta mañana", "tres ponderaciones"], color=AZUL),
    Etapa("Delimitar ICF", ["programa: sí", "GPS: no", "cumplimiento: no"], color=OCRE),
    Etapa("Comunicar", ["oferta prometida", "no operación", "no demanda"], color=ACENTO),
])

MAPA = Mapa(centro="P12 + P13 · Frecuencia", subtitulo="8 pasos", ramas=[
    Rama("Preparar", ["1 · Tablas", "2 · Ventanas válidas"], color=AZUL),
    Rama("ICF", ["3 · Alcance", "4 · Denominador ausente"], color=OCRE),
    Rama("Distribuir", ["5 · Percentiles", "6 · Ponderaciones"], color=AZUL),
    Rama("Priorizar", ["7 · Punta mañana", "8 · Interpretación"], color=ACENTO),
])


def construir() -> Cuaderno:
    pasos = [
        Paso("Leer solo tres tablas", "El ICF programado no necesita el archivo de 1,1 millones de horarios.",
             "tablas = frecuencia.cargar()\n{k: v.shape for k, v in tablas.items()}",
             "Power Query: cargar `frequencies`, `trips` y `routes`; no importar `stop_times`.",
             "Cargar por costumbre la tabla grande duplica memoria sin aportar una columna al cálculo.", mostrar="valor"),
        Paso("Validar las ventanas", "Inicio, fin e intervalo se tipan antes de resumir.",
             "ventanas = frecuencia.ventanas_programadas(tablas)\nventanas[['valida','salidas_programadas']].agg(['count','sum'])",
             "Columnas auxiliares para segundos, duración, intervalo positivo y fin posterior al inicio.",
             "Una ventana inválida no se descarta sin contarla."),
        Paso("Separar programa de observación", "La matriz impide presentar el programa como ICF.",
             "resultados = frecuencia.analizar()\nresultados['alcance_icf']",
             "Tabla de control con componente, disponibilidad, valor y unidad.",
             "142 366 salidas programadas no son 142 366 mediciones GPS.", filas=10),
        Paso("Conservar el ICF como no calculable", "La ausencia de GPS es un resultado de alcance, no un error de ejecución.",
             "resultados['alcance_icf'].query(\"calculable_con_gtfs == 'NO'\")",
             "Dejar numerador, denominador e ICF en blanco y acompañarlos con la causa.",
             "Rellenar con cero produciría un ICF de 0 % que los datos jamás observaron.", filas=6),
        Paso("Describir la distribución", "Percentiles muestran la asimetría entre 3,10 y 330 minutos.",
             "resultados['distribucion']", "`PERCENTIL.INC` sobre `headway_secs/60`.",
             "La media de 21,17 minutos no representa la ventana típica de 15.",
             formula_excel="=PERCENTIL.INC(rango_intervalo_min;0,5)", esperado="15 minutos", filas=12,
             hoja=Hoja(columnas=[Columna("A","servicio",100),Columna("B","intervalo_min",115)],
                       filas=[["101","10"],["B30n","240"],["G37","150"]], celda="B2",
                       formula="=headway_secs/60", resultado="10", nota="La unidad publicada es minutos entre salidas.")),
        Paso("Cambiar la unidad de análisis", "Ventana, servicio y salida responden preguntas distintas.",
             "resultados['ponderaciones']", "Tres tablas dinámicas o tres ponderaciones explícitas.",
             "Promediar servicios sin declarar peso da el mismo voto a uno diario y a uno intensivo.", filas=6),
        Paso("Filtrar la punta por intersección", "Entra toda ventana que toca 08:00–09:00.",
             "resultados['punta_manana'].head(15)",
             "Condición: inicio < 09:00 Y fin > 08:00; agrupar por servicio y sentido.",
             "Filtrar solo `start_time` pierde ventanas que comenzaron antes de las 08:00.", filas=15),
        Paso("Publicar una conclusión proporcional", "Se distingue frecuencia larga de incumplimiento.",
             "resultados['ventanas_invalidas']", "Mostrar el recuento de inválidas junto a la tabla final.",
             "Un intervalo programado largo puede ser diseño de servicio; no demuestra falla operacional.", filas=6),
    ]
    return Cuaderno(
        caso="P12-P13", titulo="ICF y distribución de la frecuencia programada",
        pregunta="¿Qué parte del ICF se puede calcular con GTFS y cómo se distribuye la frecuencia programada?",
        datos="frequencies.txt, trips.txt y routes.txt del GTFS vigente, más la definición oficial del ICF.",
        pasos=pasos, contexto={"frecuencia": frecuencia}, problema=PROBLEMA, solucion=SOLUCION,
        flujo=FLUJO, mapa=MAPA,
        cierre=("El GTFS permite construir 142 366 salidas programadas y describir sus intervalos. "
                "No contiene mediciones GPS: el ICF oficial permanece no calculable."),
        aprendizajes=("Programa no es operación observada.", "La unidad de análisis cambia el intervalo típico.",
                      "Las ventanas se filtran por intersección temporal.", "Un vacío metodológico no se rellena con cero."),
        relacionados=(("Resultados auditables", "README.md"),
                      ("Definición oficial del ICF", "../../docs/indicadores-oficiales-transporte.md")),
        anterior=("P11 · Calendario", "../calendario_medicion/CUADERNO.md"),
        siguiente=("P14-P15 · Evolución GTFS", "../evolucion_gtfs/CUADERNO.md"),
        reproducir="python -m cases.frecuencia_programada.solution",
        importes="from cases.frecuencia_programada import solution as frecuencia",
        fuentes_datos="gtfs-red-movilidad", columnas_excel=("servicio", "intervalo_min"),
    )
