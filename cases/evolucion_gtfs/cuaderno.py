"""Cuaderno de P14 y P15."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.evolucion_gtfs import solution as evolucion  # noqa: E402
from lab.cuaderno import Cuaderno, Paso  # noqa: E402
from lab.diagrama_svg import ACENTO, AZUL, OCRE, TINTA, Etapa, Flujo, Mapa, Rama  # noqa: E402
from lab.hoja_svg import Columna, Hoja  # noqa: E402

PROBLEMA = """
Comparar publicaciones no es restar sus conteos. Una ruta puede conservar el nombre y
cambiar de trazado; un identificador puede cambiar sin que la realidad cambie; una
versión puede modelar horarios absolutos donde otra usa frecuencias. P14 pregunta qué
cambió y P15 cuánto cambió la oferta: ambas requieren fijar identidad, grano y método.

La ejecución usa tres publicaciones oficiales reales y conserva sus fechas. Es una
trayectoria reciente 2024–2026, no una supuesta serie completa de trece años.
"""

SOLUCION = """
Se leen las últimas publicaciones de 2024 y 2025 desde ZIP anuales y la vigente de 2026.
Se inventaría cada tabla, se comparan conjuntos de rutas y paradas de embarque, y se
firman las secuencias de coordenadas para detectar cambios geométricos. La oferta se
recalcula en las tres versiones con la misma expansión y el mismo `service_id` laboral.
"""

FLUJO = Flujo(titulo="Tres publicaciones, una sola definición", etapas=[
    Etapa("2024 y 2025", ["2 ZIP anuales", "última publicación", "de cada año"], color=TINTA),
    Etapa("2026-11-14", ["feed vigente", "tercer punto", "misma definición"], color=TINTA),
    Etapa("Identidad", ["altas y bajas", "IDs persistentes", "geometrías firmadas"], color=AZUL),
    Etapa("Oferta", ["mismo día laboral", "misma expansión", "24 horas"], color=AZUL),
    Etapa("Trayectoria", ["68 533 → 68 011", "→ 64 011 salidas", "causa no atribuida"], color=ACENTO),
])

MAPA = Mapa(centro="P14 + P15 · Evolución GTFS", subtitulo="8 pasos", ramas=[
    Rama("Asegurar comparabilidad", ["1 · Fuentes", "2 · Inventario"], color=AZUL),
    Rama("Comparar red", ["3 · Rutas", "4 · Paradas", "5 · Trazados"], color=OCRE),
    Rama("Comparar oferta", ["6 · Perfil horario", "7 · Total"], color=AZUL),
    Rama("Interpretar", ["8 · Límites y ampliación"], color=ACENTO),
])


def construir() -> Cuaderno:
    pasos = [
        Paso("Nombrar las publicaciones por fecha", "La etiqueta temporal pertenece al dato, no al momento de análisis.",
             "[(r.etiqueta, r.ruta.name, r.miembro or 'ZIP directo') for r in evolucion.REFERENCIAS]",
             "Hoja Fuentes: fecha, URL, archivo, miembro interno y huella.",
             "Llamar a ambos archivos 'GTFS' borra qué estado de la red representa cada uno.", mostrar="valor"),
        Paso("Inventariar antes de comparar", "Volúmenes y esquemas muestran si las cargas son comparables.",
             "resultados = evolucion.analizar()\nresultados['inventario']",
             "Una fila por publicación y una columna por tabla/unidad.",
             "El salto de viajes declarados no se interpreta antes de revisar la mecánica de frecuencias.", filas=6),
        Paso("Comparar rutas como conjuntos", "Se separan permanencias, altas y bajas.",
             "resultados['identidades'].query(\"entidad == 'rutas'\")",
             "`CONTAR.SI` contra la otra versión: presente, aparece o desaparece.",
             "Una baja de `route_id` no prueba que el recorrido físico dejó de existir.", filas=6),
        Paso("Comparar solo paradas de embarque", "El denominador excluye estaciones, accesos y nodos de pasillo.",
             "resultados['identidades'].query(\"entidad == 'paradas de embarque'\")",
             "Filtrar `location_type=0` en ambas versiones antes del cruce externo.",
             "Comparar todo `stops.txt` confunde cambios de jerarquía con paradas nuevas.", filas=6),
        Paso("Firmar el trazado, no solo el ID", "Cada geometría se resume desde su secuencia completa de puntos.",
             "resultados['trazados'].query('cambio_de_conjunto').head(15)",
             "Power Query: ordenar puntos por secuencia, concatenarlos por shape y comparar la firma.",
             "Un `shape_id` estable puede ocultar coordenadas nuevas; uno nuevo puede dibujar lo mismo.", filas=15),
        Paso("Recalcular la oferta por hora", "La misma función combina frecuencias y horarios absolutos en ambas versiones.",
             "resultados['oferta_por_hora'].head(30)",
             "Tabla dinámica: publicación en columnas, hora en filas, salidas en valores.",
             "Comparar filas de `trips.txt` daría una serie rota: una ventana representa muchas salidas.", filas=30),
        Paso("Medir el cambio total", "Se publica diferencia absoluta y porcentual con su período.",
             "resultados['oferta_total']", "`=(salidas_2026/salidas_2025)-1` con formato porcentual.",
             "Tres puntos describen una trayectoria reciente, no toda la serie 2014–2026.",
             formula_excel="=(B3/B2)-1", esperado="−0,76 % y −5,88 %", filas=5,
             hoja=Hoja(columnas=[Columna("A","publicacion",110),Columna("B","salidas",90),Columna("C","cambio_pct",95)],
                       filas=[["2024-11-24","68533",""],["2025-12-20","68011","−0,76 %"],
                              ["2026-11-14","64011","−5,88 %"]],
                       celda="C3", primera_fila=2, formula="=(B3/B2)-1", resultado="−0,76 %",
                       nota="El período y la base quedan visibles junto al porcentaje.")),
        Paso("Dejar preparada la ampliación", "Agregar un año es agregar una FeedRef; la definición no cambia.",
             "{'publicaciones_ejecutadas': len(evolucion.REFERENCIAS), 'primera': evolucion.REFERENCIAS[0].etiqueta, 'ultima': evolucion.REFERENCIAS[-1].etiqueta}",
             "Agregar una fila por publicación manteniendo idénticas fórmulas y filtros.",
             "Completar años con cifras copiadas de informes rompería la comparabilidad del método.", mostrar="valor"),
    ]
    return Cuaderno(
        caso="P14-P15", titulo="Cambios de red y oferta entre publicaciones GTFS",
        pregunta="¿Qué cambió entre 2024 y 2026 y cómo varió la oferta programada por hora?",
        datos="Últimas publicaciones GTFS de 2024 y 2025, más el feed vigente del 14 de noviembre de 2026.",
        pasos=pasos, contexto={"evolucion": evolucion}, problema=PROBLEMA, solucion=SOLUCION,
        flujo=FLUJO, mapa=MAPA,
        cierre=("La oferta laboral calculada con idéntica definición pasa de 68 533 salidas en 2024 "
                "a 68 011 en 2025 y 64 011 en 2026; el último cambio es −5,88 %."),
        aprendizajes=("La identidad en el tiempo no se supone.", "El trazado se compara por geometría.",
                      "La serie debe recalcular cada versión con la misma definición.",
                      "Tres puntos describen una trayectoria reciente, no una historia completa."),
        relacionados=(("Resultados auditables", "README.md"),
                      ("P06 · Definición de salidas", "../gtfs_red_movilidad/CUADERNO.md")),
        anterior=("P12-P13 · Frecuencia", "../frecuencia_programada/CUADERNO.md"),
        siguiente=("P16 · Informe de decisión", "../informe_decision_carga/CUADERNO.md"),
        reproducir="python -m cases.evolucion_gtfs.solution",
        importes="from cases.evolucion_gtfs import solution as evolucion",
        fuentes_datos="gtfs-historicos-2024 gtfs-historicos-2025 gtfs-red-movilidad",
        columnas_excel=("publicacion", "salidas", "cambio_pct"),
    )
