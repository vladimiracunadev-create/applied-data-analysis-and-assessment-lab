"""Cuaderno de P08: distancia desde cada parada al lugar de carga más cercano."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.cobertura_de_carga import solution as p08  # noqa: E402
from lab.cuaderno import Cuaderno, Paso  # noqa: E402
from lab.diagrama_svg import ACENTO, AZUL, OCRE, TINTA, Etapa, Flujo, Mapa, Rama  # noqa: E402
from lab.hoja_svg import Columna, Hoja  # noqa: E402

PROBLEMA = """
Las paradas y los lugares de carga describen la misma ciudad, pero no comparten una
clave. La pregunta —qué proporción de las paradas tiene un lugar de carga a 300 metros—
obliga a declarar qué es una parada, cómo se mide una distancia sobre la Tierra y qué
significa «cerca».

El cruce comprende 12 497 paradas de embarque y 1 927 locales abiertos: más de 24
millones de pares. Una fórmula equivocada sigue produciendo un número razonable. Medir
grados como si fueran metros reduce la cobertura del 59,29 % al 54,69 % y asigna otro
local a 814 paradas. Además, la distancia en línea recta no es la distancia caminada;
por eso el cuaderno separa el dato calculado del supuesto de rodeo.
"""

SOLUCION = """
Primero se fija el denominador y se audita la supuesta llave de los locales. Después se
calcula la distancia mínima con haversine por bloques, se describe su distribución y se
mide la sensibilidad al umbral y al factor de rodeo. Finalmente se confrontan dos
fórmulas y dos representaciones de coordenadas, se localizan zonas rezagadas y se
declara el límite que impide afirmar si el lugar cercano está abierto.
"""

FLUJO = Flujo(
    titulo="Dos fuentes sin llave: el criterio de cruce es parte del resultado",
    etapas=[
        Etapa("GTFS", ["12 497 paradas", "coordenadas WGS84", "solo location_type 0"],
              color=TINTA),
        Etapa("Lugares bip!", ["1 927 abiertos", "cinco tipos", "dos coordenadas"],
              color=AZUL),
        Etapa("Cruce espacial", ["24,1 M de pares", "haversine por bloques", "mínimo por parada"],
              color=AZUL),
        Etapa("Sensibilidad", ["umbral 300 m", "rodeo 1,0–1,5", "fórmula alternativa"],
              color=OCRE),
        Etapa("Decisión", ["59,29 % en línea", "46,02 % con rodeo 1,3", "52,6 % sin horario"],
              color=ACENTO),
    ],
)

MAPA = Mapa(
    centro="P08 · Cobertura espacial",
    subtitulo="9 pasos · 8 controles",
    ramas=[
        Rama("Definir", ["1 · Denominador", "2 · Identidad de locales"], color=AZUL),
        Rama("Medir", ["3 · Cruce por distancia", "4 · Distribución", "5 · Umbral"], color=AZUL),
        Rama("Desafiar", ["6 · Rodeo", "7 · Fórmulas y coordenadas"], color=OCRE),
        Rama("Decidir", ["8 · Zonas con menor cobertura", "9 · Límite del horario"], color=ACENTO),
    ],
)


def construir() -> Cuaderno:
    """Construye el cuaderno ejecutable de P08."""
    pasos = [
        Paso(
            titulo="Fijar qué filas son paradas",
            objetivo="El denominador contiene lugares donde sube gente, no estaciones, accesos ni nodos.",
            pandas="resultados = p08.analizar()\nresultados['paradas_por_tipo']",
            excel="Filtrar `location_type = 0` y contar solo filas con latitud y longitud válidas.",
            trampa="Contar todo `stops.txt` agrega 5 989 elementos que no son paradas de embarque.",
            filas=8,
        ),
        Paso(
            titulo="Comprobar la llave de los locales",
            objetivo="Antes del cruce, se mide si `codigo` identifica un lugar de carga.",
            pandas="resultados['identificador']",
            excel="Tabla dinámica: tipo en filas, recuento de código y recuento distinto de código en valores.",
            trampa="En Metro el código es la línea: 143 filas comparten solo siete códigos.",
            filas=8,
        ),
        Paso(
            titulo="Medir el vecino más cercano",
            objetivo="Se evalúan 24 081 719 pares con haversine por bloques y se conserva el mínimo por parada.",
            pandas="resultados['resumen']",
            excel="Para pocos registros: `=MIN(DISTANCIA.HAVERSINE(parada;locales))`; a esta escala, Power Query o Python.",
            trampa="Crear la matriz completa consume memoria innecesaria; por bloques conserva el mismo mínimo.",
            filas=12,
        ),
        Paso(
            titulo="Describir la distribución, no solo la media",
            objetivo="Percentiles, mediana y máximo muestran una cola que la media oculta.",
            pandas="resultados['distribucion']",
            excel="`=PERCENTIL.INC(rango;0,5)` para la mediana y percentiles 0,9; 0,95 y 0,99.",
            formula_excel="=PERCENTIL.INC(rango_distancia;0,5)",
            esperado="249,6 m de mediana",
            trampa="El máximo de 40 km pertenece al borde de cobertura de los archivos, no a una caminata plausible.",
            filas=12,
            hoja=Hoja(
                columnas=[Columna("A", "stop_id", 100), Columna("B", "distancia_m", 110), Columna("C", "cubierta", 90)],
                filas=[["PA1", "249,6", "SÍ"], ["PA2", "671,0", "NO"], ["PA3", "131,2", "SÍ"]],
                celda="C2", formula="=SI(B2<=300;\"SÍ\";\"NO\")", resultado="SÍ",
                nota="La columna conserva la distancia; el umbral se aplica después.",
            ),
        ),
        Paso(
            titulo="Mostrar cuánto depende del umbral",
            objetivo="La cobertura se publica junto a la curva de 200 a 1 000 metros.",
            pandas="resultados['cobertura_por_umbral']",
            excel="`=CONTAR.SI(rango_distancia;\"<=\"&E2)/CONTAR(rango_distancia)` para cada umbral.",
            formula_excel="=CONTAR.SI(rango_distancia;\"<=\"&E2)/CONTAR(rango_distancia)",
            esperado="59,29 % a 300 m",
            trampa="Elegir el umbral después de ver el resultado convierte el criterio en una meta móvil.",
            filas=10,
        ),
        Paso(
            titulo="Separar línea recta de distancia caminada",
            objetivo="El factor de rodeo es un supuesto explícito y su efecto se expresa en puntos porcentuales.",
            pandas="resultados['sensibilidad_rodeo']",
            excel="`=CONTAR.SI(rango_distancia*factor;\"<=300\")/CONTAR(rango_distancia)`.",
            formula_excel="=SUMAPRODUCTO(--(rango_distancia*factor<=300))/CONTAR(rango_distancia)",
            esperado="46,02 % con factor 1,3",
            trampa="Decir 300 m caminando a partir de una línea geodésica sobrestima la cobertura.",
            filas=8,
        ),
        Paso(
            titulo="Validar fórmula y representación",
            objetivo="Dos controles independientes cuantifican cuánto cambia la clasificación de cada parada.",
            pandas="pd.concat([resultados['formulas_comparadas'], resultados['representaciones_comparadas']], ignore_index=True)",
            excel="Comparar una columna haversine con el atajo euclídeo y marcar `=ABS(correcta-atajo)>tolerancia`.",
            trampa="Que el agregado cambie poco no significa que las mismas paradas queden cubiertas.",
            filas=20,
        ),
        Paso(
            titulo="Localizar zonas con menor cobertura",
            objetivo="Una rejilla publicable sustituye la comuna que no existe en el GTFS.",
            pandas="resultados['por_rejilla'].head(10)",
            excel="Crear latitud y longitud redondeadas, agrupar ambas en una tabla dinámica y ordenar por cobertura.",
            trampa="Asignar la comuna del local más cercano a la parada crea comunas falsas en los bordes.",
            filas=10,
        ),
        Paso(
            titulo="Declarar lo que el dato no permite afirmar",
            objetivo="Se distingue cercanía física de disponibilidad efectiva del punto de carga.",
            pandas="resultados['limite_por_horario']",
            excel="Contar por separado local cercano, horario conocido y local cercano con horario conocido.",
            trampa="Una parada cubierta espacialmente puede apuntar a un local cuyo horario no fue publicado.",
            filas=10,
        ),
    ]
    return Cuaderno(
        caso="P08",
        titulo="Distancia al lugar de carga más cercano",
        pregunta="¿Qué proporción de las paradas tiene un lugar de carga bip! a 300 metros o menos?",
        datos="GTFS Red Movilidad y los cinco Excel públicos de lugares de carga bip!.",
        pasos=pasos,
        contexto={"p08": p08},
        problema=PROBLEMA,
        solucion=SOLUCION,
        flujo=FLUJO,
        mapa=MAPA,
        cierre=("La cobertura es 59,29 % en línea recta y 46,02 % con un rodeo supuesto de 1,3. "
                "Son dos respuestas a dos preguntas distintas; ninguna autoriza a afirmar que el local esté abierto."),
        aprendizajes=(
            "Un cruce espacial también tiene una llave: el criterio, el umbral y la fórmula declarados.",
            "La sensibilidad debe acompañar al resultado cuando una decisión metodológica cambia más de diez puntos.",
            "Un agregado estable puede esconder centenares de filas que cambian de clasificación.",
            "La ausencia de comuna y horario limita qué recomendación es defendible.",
        ),
        relacionados=(("Hallazgos auditables del caso", "README.md"),
                      ("P01 · Consolidación de locales", "../bip_lugares_carga/CUADERNO.md"),
                      ("P09 · Cobertura nocturna", "../carga_nocturna/README.md")),
        anterior=("P06 · Expediciones por hora", "../gtfs_red_movilidad/CUADERNO.md"),
        siguiente=("P09 · Cobertura nocturna", "../carga_nocturna/CUADERNO.md"),
        reproducir="python -m cases.cobertura_de_carga.solution",
        importes="from cases.cobertura_de_carga import solution as p08\nimport pandas as pd",
        fuentes_datos=(
            "gtfs-red-movilidad bip-metro bip-puntos bip-centros-alto-estandar "
            "bip-centros-estandar bip-retail"
        ),
        columnas_excel=("stop_id", "distancia_m", "cubierta"),
    )
