"""Cuaderno de P05 y P09: horarios libres y cobertura nocturna."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.carga_nocturna import solution as p09  # noqa: E402
from lab.cuaderno import Cuaderno, Paso  # noqa: E402
from lab.diagrama_svg import ACENTO, AZUL, OCRE, TINTA, Etapa, Flujo, Mapa, Rama  # noqa: E402
from lab.hoja_svg import Columna, Hoja  # noqa: E402

PROBLEMA = """
La cobertura nocturna une tres preguntas: dónde pasa un bus entre las 00:00 y las
05:00, si hay un local de carga a 300 metros y si ese local está abierto. Las dos
primeras se calculan; la tercera tropieza con un dato ausente: 1 579 de los 1 927
locales no publican horario.

El GTFS agrega otra trampa. En expediciones por frecuencia, `arrival_time` es un
desplazamiento desde el inicio y no una hora de reloj. Filtrarlo como texto inventa
1 681 paradas nocturnas. La cifra falsa sobrestima solo 15,98 %, suficiente para parecer
plausible. La respuesta correcta no es un sí/no: tiene una tercera categoría,
indeterminada, y se expresa como intervalo.
"""

SOLUCION = """
Se auditan las ventanas de servicio, se mide el error del filtro ingenuo y se obtiene
la intensidad nocturna sin expandir millones de filas. En paralelo se interpreta cada
texto de horario y se cuantifica la cobertura del campo. El cruce espacial clasifica
cada parada en cuatro estados observables y el informe final transforma la falta de
datos en un intervalo y en una lista concreta de información que falta recopilar.
"""

FLUJO = Flujo(titulo="Cobertura nocturna: tiempo, espacio y un dato ausente", etapas=[
    Etapa("GTFS", ["3 tipos de día", "ventanas de frecuencia", "00:00–05:00"], color=TINTA),
    Etapa("Servicio", ["10 520 paradas", "367 251 llegadas", "sin filtro textual"], color=AZUL),
    Etapa("Lugares bip!", ["1 927 abiertos", "348 con horario", "0 abiertos de madrugada"], color=AZUL),
    Etapa("Cruce", ["radio 300 m", "4 estados", "52,6 % indeterminado"], color=OCRE),
    Etapa("Respuesta", ["mínimo 0 %", "máximo 52,62 %", "dato faltante priorizado"], color=ACENTO),
])

MAPA = Mapa(centro="P05 + P09 · Cobertura nocturna", subtitulo="9 pasos · 7 trampas", ramas=[
    Rama("Medir servicio", ["1 · Ventanas", "2 · Atajo falso", "3 · Intensidad"], color=AZUL),
    Rama("Estructurar horarios", ["4 · Textos", "5 · Cobertura del campo"], color=AZUL),
    Rama("Cruzar", ["6 · Cuatro estados", "7 · Tipo de día"], color=OCRE),
    Rama("Decidir", ["8 · Intervalo", "9 · Qué dato falta"], color=ACENTO),
])


def construir() -> Cuaderno:
    """Construye el cuaderno ejecutable de P05 y P09."""
    pasos = [
        Paso(
            titulo="Auditar las ventanas de servicio",
            objetivo="Se mide qué servicios y ventanas aportan llegadas a la madrugada.",
            pandas="resultados = p09.analizar()\nresultados['ventanas_por_servicio']",
            excel="Filtrar ventanas que intersectan [00:00;05:00), no solo las que empiezan dentro.",
            trampa="Una ventana que empieza antes de medianoche puede aportar servicio después de las 00:00.", filas=8,
        ),
        Paso(
            titulo="Demostrar por qué el filtro textual falla",
            objetivo="El atajo se calcula al lado del método correcto y se mide su error.",
            pandas="resultados['atajo_comparado']",
            excel="Separar expediciones con frecuencia antes de interpretar `arrival_time` como reloj.",
            trampa="El 100 % de las filas que toma el atajo son desplazamientos relativos, no horas.", filas=12,
        ),
        Paso(
            titulo="Describir la intensidad nocturna",
            objetivo="No basta con saber que una parada aparece: se cuentan llegadas y se muestran percentiles.",
            pandas="resultados['intensidad']",
            excel="Tabla dinámica por parada y percentiles sobre el conteo de llegadas.",
            formula_excel="=PERCENTIL.INC(rango_llegadas;0,5)", esperado="23 llegadas medianas en cinco horas",
            trampa="Una sola llegada y 459 llegadas no representan la misma disponibilidad.", filas=12,
        ),
        Paso(
            titulo="Convertir horarios libres en datos",
            objetivo="Cada texto se interpreta en días y tramos, y los no interpretables permanecen visibles.",
            pandas="resultados['horarios_interpretados']",
            excel="Power Query: normalizar saltos y abreviaturas; separar por día; convertir cada tramo a inicio y fin.",
            trampa="Vacío no significa cerrado: significa que el publicador no entregó el campo.", filas=12,
        ),
        Paso(
            titulo="Medir la cobertura del campo horario",
            objetivo="La ausencia se reporta por tipo de local, no como una nota al pie.",
            pandas="resultados['cobertura_del_campo']",
            excel="`=CONTAR.SI.CONJUNTO(tipo;A2;horario;\"<>\")/CONTAR.SI(tipo;A2)`.",
            formula_excel="=CONTAR.SI.CONJUNTO(tipo;A2;horario;\"<>\")/CONTAR.SI(tipo;A2)",
            esperado="18,1 % del total con horario",
            trampa="Promediar por archivo daría 80 %: cuatro fuentes completas y una vacía, sin ponderar sus tamaños.", filas=8,
            hoja=Hoja(
                columnas=[Columna("A", "tipo_local", 135), Columna("B", "horario", 190), Columna("C", "estado", 115)],
                filas=[["Punto bip!", "", "INDETERMINADO"], ["Metro", "06:00–23:00", "CERRADO"], ["Retail", "08:00–21:00", "CERRADO"]],
                celda="C2", formula="=SI(B2=\"\";\"INDETERMINADO\";\"EVALUAR\")", resultado="INDETERMINADO",
                nota="El vacío conserva su significado: ausencia de observación.",
            ),
        ),
        Paso(
            titulo="Clasificar en cuatro estados observables",
            objetivo="La respuesta conserva cubierta, sin local, cerrado verificado e indeterminado.",
            pandas="resultados['respuesta']",
            excel="`SI.CONJUNTO` con distancia, horario conocido y apertura; nunca rellenar el vacío con FALSO.",
            trampa="Reducir a cubierto/no cubierto mezcla 5 536 incógnitas con evidencia negativa.", filas=8,
        ),
        Paso(
            titulo="Comprobar estabilidad por tipo de día",
            objetivo="Laboral, sábado y domingo se publican separados para no ocultar variación.",
            pandas="resultados['por_servicio']",
            excel="Tabla dinámica: tipo de día en filas, estado en columnas y paradas en valores.",
            trampa="Sumar los servicios repite una parada hasta tres veces; cada denominador se interpreta por separado.", filas=8,
        ),
        Paso(
            titulo="Expresar la respuesta como intervalo",
            objetivo="El mínimo usa solo evidencia; el máximo muestra el caso favorable de todos los desconocidos.",
            pandas="resultados['intervalo']",
            excel="Mínimo = abiertos verificados / total; máximo = (abiertos + indeterminados) / total.",
            formula_excel="=(abiertos_verificados+indeterminados)/total_nocturnas",
            esperado="0,00 % a 52,62 %",
            trampa="Elegir el punto medio no agrega información: inventa una probabilidad que los datos no contienen.", filas=8,
        ),
        Paso(
            titulo="Convertir la incertidumbre en una tarea",
            objetivo="Se identifica qué fuente completar y cuántas paradas desbloquea.",
            pandas="resultados['lo_que_falta']",
            excel="Agrupar los indeterminados por tipo de local y contar paradas asociadas.",
            trampa="Pedir 'mejorar los datos' sin señalar el campo y el impacto no es una recomendación ejecutable.", filas=8,
        ),
    ]
    return Cuaderno(
        caso="P05-P09", titulo="Horarios libres y cobertura de carga nocturna",
        pregunta="Donde hay buses entre las 00:00 y las 05:00, ¿hay dónde cargar la tarjeta?",
        datos="GTFS Red Movilidad y horarios publicados en los cinco Excel de lugares bip!.",
        pasos=pasos, contexto={"p09": p09}, problema=PROBLEMA, solucion=SOLUCION,
        flujo=FLUJO, mapa=MAPA,
        cierre=("Hay 10 520 paradas con servicio nocturno. La cobertura abierta verificable es 0 %, "
                "pero 52,62 % permanece indeterminado: el dato correcto es un intervalo, no un cero definitivo."),
        aprendizajes=(
            "Horario relativo y hora absoluta son magnitudes distintas aunque compartan formato.",
            "Vacío, cero y falso no son intercambiables.",
            "Una clasificación honesta necesita una tercera respuesta cuando falta observación.",
            "El ancho del intervalo mide el valor potencial de completar el dato.",
        ),
        relacionados=(("Hallazgos auditables del caso", "README.md"),
                      ("P06 · Expansión de frecuencias", "../gtfs_red_movilidad/CUADERNO.md"),
                      ("P08 · Cobertura espacial", "../cobertura_de_carga/CUADERNO.md")),
        anterior=("P08 · Cobertura espacial", "../cobertura_de_carga/CUADERNO.md"),
        siguiente=("P10 · Correspondencia buses–Metro", "../correspondencia_metro/CUADERNO.md"),
        reproducir="python -m cases.carga_nocturna.solution",
        importes="from cases.carga_nocturna import solution as p09",
        fuentes_datos=(
            "gtfs-red-movilidad bip-metro bip-puntos bip-centros-alto-estandar "
            "bip-centros-estandar bip-retail"
        ),
        columnas_excel=("tipo_local", "horario", "estado"),
    )
