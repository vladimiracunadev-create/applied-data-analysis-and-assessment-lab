"""Cuaderno de P17: gobernanza y catálogo de activos DTPM."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.gobernanza_datos_dtpm import solution as governance  # noqa: E402
from lab.cuaderno import Cuaderno, Paso  # noqa: E402
from lab.diagrama_svg import ACENTO, AZUL, OCRE, TINTA, Etapa, Flujo, Mapa, Rama  # noqa: E402
from lab.hoja_svg import Columna, Hoja  # noqa: E402

PROBLEMA = """
Los casos anteriores prueban que los archivos se pueden usar, pero no que tengan
responsables, periodicidad, licencia, esquema y retención explícitos. P17 separa una
ausencia documental de un defecto de datos: escribe «no declarado» cuando no hay
evidencia, en vez de completar el catálogo con una suposición cómoda.
"""

SOLUCION = """
Se define una fila por activo, se valida su identificador, se convierten cinco ausencias
en banderas auditables y se publica una fórmula de prioridad. La criticidad modifica el
orden de atención, pero no cambia la evidencia observada ni convierte el puntaje en una
probabilidad de incidente.
"""

FLUJO = Flujo(titulo="De archivos utilizables a activos gobernables", etapas=[
    Etapa("Evidencia", ["P01–P16", "procedencia", "licencias"], color=TINTA),
    Etapa("Catálogo", ["1 fila por activo", "identidad", "responsables"], color=AZUL),
    Etapa("Brechas", ["5 controles", "sin imputar", "trazables"], color=OCRE),
    Etapa("Prioridad", ["criticidad", "fórmula pública", "acciones"], color=ACENTO),
])

MAPA = Mapa(centro="P17 · Gobernanza DTPM", subtitulo="8 pasos", ramas=[
    Rama("Definir", ["1 · Grano", "2 · Contrato"], color=AZUL),
    Rama("Medir", ["3 · Ausencias", "4 · Puntaje"], color=OCRE),
    Rama("Revisar", ["5 · Brechas", "6 · Ranking"], color=AZUL),
    Rama("Decidir", ["7 · Acciones", "8 · Límites"], color=ACENTO),
])


def construir() -> Cuaderno:
    pasos = [
        Paso("Nombrar el grano del catálogo", "Una fila representa un activo, no un archivo descargado ni una columna.",
             "catalogo = governance.cargar()\ncatalogo[['activo_id', 'nombre', 'publicador', 'formato']]",
             "Crear una tabla y documentar que `activo_id` identifica un activo lógico.",
             "Contar cada publicación mensual como un activo infla el inventario y mezcla versión con identidad.", filas=10),
        Paso("Validar el contrato mínimo", "La gobernanza empieza por comprobar que el propio catálogo tenga identidad y vocabularios válidos.",
             "{'filas': len(catalogo), 'ids_unicos': catalogo['activo_id'].nunique(), 'criticidades': sorted(catalogo['criticidad'].unique())}",
             "`=CONTARA(A2:A9)=CONTARA(UNICOS(A2:A9))` para comprobar identidad.",
             "Una columna llamada ID no garantiza unicidad.", mostrar="valor"),
        Paso("Conservar lo no declarado", "Los vacíos documentales son resultados y no deben imputarse como cumplimiento.",
             "catalogo[['activo_id', 'responsable_operativo', 'retencion_meses', 'actualizacion_declarada']]",
             "Usar `NO_DECLARADO` como categoría y no una celda vacía ambigua.",
             "Completar responsable o retención por intuición fabrica evidencia.", filas=10),
        Paso("Calcular las cinco banderas", "Cada brecha responde una pregunta verificable y conserva su columna de origen.",
             "auditoria = governance.evaluar(catalogo)\nauditoria[['activo_id', 'brecha_licencia', 'brecha_esquema', 'brecha_actualizacion', 'brecha_responsable', 'brecha_retencion']]",
             "Cada control es `SI(condición;1;0)`; no esconderlos dentro del puntaje.",
             "Un puntaje sin componentes no se puede auditar.", filas=10),
        Paso("Publicar la fórmula de prioridad", "Los pesos son una decisión pedagógica y deben quedar visibles.",
             "auditoria[['activo_id', 'puntaje_brecha', 'peso_criticidad', 'puntaje_riesgo']].sort_values('puntaje_riesgo', ascending=False)",
             "`=(3*licencia+2*esquema+2*actualizacion+2*responsable+retencion)*peso`.",
             "El puntaje ordena aclaraciones; no es una probabilidad.", filas=10,
             hoja=Hoja(columnas=[Columna("A", "activo", 120), Columna("B", "brecha", 80), Columna("C", "peso", 70), Columna("D", "riesgo", 80)],
                       filas=[["GTFS-VIGENTE", "7", "3", "21"], ["BIP-PCMA", "7", "3", "21"]],
                       celda="D2", formula="=B2*C2", resultado="21", nota="El peso modifica prioridad, no evidencia.")),
        Paso("Contar activos afectados por brecha", "El resumen revela problemas transversales que conviene resolver una sola vez.",
             "resultados = governance.analizar(catalogo)\nresultados['brechas']",
             "Sumar cada columna binaria; no sumar el puntaje ponderado como si fueran activos.",
             "Cinco brechas de un activo no equivalen a cinco activos.", filas=8),
        Paso("Construir el ranking de atención", "El orden conserva el activo, su criticidad y los dos puntajes para poder explicarlo.",
             "resultados['riesgo_por_activo']",
             "Ordenar `puntaje_riesgo` descendente y conservar el desempate por ID.",
             "Ocultar empates hace parecer más precisa una prioridad ordinal.", filas=10),
        Paso("Traducir el resultado en acciones", "Cada brecha requiere una acción documental distinta y una validación con el publicador.",
             "{'licencia': 'verificar condiciones', 'esquema': 'publicar contrato', 'actualizacion': 'declarar periodicidad', 'responsable': 'validar stewardship', 'retencion': 'definir ciclo de vida'}",
             "Agregar columnas `acción`, `responsable de validar` y `estado`, sin asignar nombres no confirmados.",
             "El laboratorio no puede nombrar responsables institucionales por cuenta propia.", mostrar="valor"),
    ]
    return Cuaderno(
        caso="P17", titulo="Gobernanza y catálogo de activos de datos DTPM",
        pregunta="¿Qué información de gobernanza falta aclarar para los activos usados por P01–P16?",
        datos="Catálogo pedagógico versionado de ocho activos, derivado de la procedencia documentada; no es un catálogo oficial DTPM.",
        pasos=pasos, contexto={"governance": governance}, problema=PROBLEMA, solucion=SOLUCION,
        flujo=FLUJO, mapa=MAPA,
        cierre=("El ranking prioriza aclaraciones documentales. La acción siguiente es validar el catálogo con "
                "los publicadores; hasta entonces, no declarado permanece no declarado."),
        aprendizajes=("Un catálogo necesita grano e identidad.", "Ausencia de evidencia no es cumplimiento.",
                      "Los pesos deben ser públicos.", "Gobernanza no se reemplaza con limpieza técnica."),
        relacionados=(("Metadatos completos", "case.json"),
                      ("P01 · Procedencia de lugares bip!", "../bip_lugares_carga/CUADERNO.md"),
                      ("P14/P15 · Publicaciones GTFS", "../evolucion_gtfs/CUADERNO.md")),
        reproducir="python -m cases.gobernanza_datos_dtpm.solution",
        importes="from cases.gobernanza_datos_dtpm import solution as governance",
        columnas_excel=("activo_id", "brecha", "peso_criticidad", "puntaje_riesgo"),
    )
