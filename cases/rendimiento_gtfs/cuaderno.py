"""Cuaderno de P07."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.rendimiento_gtfs import solution as rendimiento  # noqa: E402
from lab.cuaderno import Cuaderno, Paso  # noqa: E402
from lab.diagrama_svg import ACENTO, AZUL, OCRE, TINTA, Etapa, Flujo, Mapa, Rama  # noqa: E402
from lab.hoja_svg import Columna, Hoja  # noqa: E402

PROBLEMA = """
«Pandas no escala» y «DuckDB es más rápido» son afirmaciones incompletas. La decisión
depende del volumen, la operación, la memoria disponible y el costo de preparar los
datos. P07 fija una sola agregación y exige que todos los motores devuelvan exactamente
lo mismo antes de comparar tiempos.
"""

SOLUCION = """
Se cuentan filas de horario por parada con lectura completa, seis bloques, una consulta
DuckDB y un plan lazy de Polars. Se separa el tiempo de extracción del ZIP de cada
consulta, se mide la memoria del DataFrame o bloque y se hace una unión por clave para
encontrar cualquier diferencia. La conclusión se expresa como criterio, no como ganador
universal.
"""

FLUJO = Flujo(titulo="Misma pregunta, cuatro caminos medidos", etapas=[
    Etapa("stop_times", ["1 098 717 filas", "51 MB sin comprimir", "12 495 paradas usadas"], color=TINTA),
    Etapa("Pandas completo", ["1 DataFrame", "~60 MB de datos", "groupby directo"], color=AZUL),
    Etapa("Pandas bloques", ["6 bloques", "~11 MB máximo", "suma incremental"], color=AZUL),
    Etapa("DuckDB + Polars", ["CSV temporal", "SQL y plan lazy", "preparación separada"], color=OCRE),
    Etapa("Decisión", ["0 diferencias", "tiempo + memoria", "criterio por escala"], color=ACENTO),
])

MAPA = Mapa(centro="P07 · Benchmark", subtitulo="8 pasos", ramas=[
    Rama("Diseñar", ["1 · Misma agregación", "2 · Métricas"], color=AZUL),
    Rama("Ejecutar", ["3 · Completo", "4 · Bloques", "5 · DuckDB/Polars"], color=AZUL),
    Rama("Validar", ["6 · Igualdad exacta"], color=OCRE),
    Rama("Elegir", ["7 · Comparar", "8 · Regla de decisión"], color=ACENTO),
])


def construir() -> Cuaderno:
    pasos = [
        Paso("Fijar una agregación idéntica", "Todos cuentan filas por `stop_id`; cambiar la pregunta invalidaría el benchmark.",
             "{'archivo': 'stop_times.txt', 'operacion': 'COUNT(*) GROUP BY stop_id', 'columnas': ['stop_id']}",
             "Tabla dinámica: `stop_id` en filas y recuento en valores.",
             "Comparar una lectura selectiva con otra que carga ocho columnas mide cosas distintas.", mostrar="valor"),
        Paso("Declarar qué se mide", "Tiempo, memoria de datos, bloques y filas se guardan en la misma tabla.",
             "['segundos','lectura_s','agregacion_s','memoria_datos_mb','bloques','filas_entrada']",
             "Hoja Benchmark con método en filas y una columna por métrica.",
             "Un único tiempo total oculta que DuckDB necesita preparar un CSV temporal.", mostrar="valor"),
        Paso("Ejecutar Pandas completo", "Es la referencia simple mientras el archivo cabe en memoria.",
             "referencia = rendimiento.cargar_referencia()\nreferencia['benchmark'].query(\"metodo == 'Pandas completo'\")",
             "Cargar columna y crear tabla dinámica.",
             "El DataFrame usa más memoria que los 51 MB del CSV porque cada texto es un objeto.", mostrar="valor"),
        Paso("Ejecutar Pandas por bloques", "Cada bloque se agrega y los parciales se suman por clave.",
             "referencia['benchmark'].query(\"metodo == 'Pandas por bloques'\")",
             "Power Query puede agrupar antes de cargar, equivalente al patrón incremental.",
             "Una mediana exacta no se puede combinar sumando medianas de bloques.", mostrar="valor"),
        Paso("Ejecutar DuckDB y Polars", "Ambos consultan el CSV extraído y reportan la extracción aparte.",
             "referencia['benchmark'].query(\"metodo in ['DuckDB sobre CSV', 'Polars lazy sobre CSV']\")",
             "En Power Query, agrupar durante la consulta evita cargar el detalle a la hoja.",
             "DuckDB y Polars lazy no son equivalentes internamente; solo comparten la pregunta y la salida.", mostrar="valor"),
        Paso("Exigir igualdad antes de mirar velocidad", "Una implementación rápida y distinta es incorrecta.",
             "referencia['validacion']",
             "Cruce por `stop_id` y columna `=conteo_A=conteo_B`; contar falsos.",
             "Comparar solo el total puede ocultar errores que se compensan entre paradas.", filas=6),
        Paso("Comparar tiempo y memoria", "Ningún método domina las dos dimensiones en todos los volúmenes.",
             "referencia['benchmark']", "Tabla con formato condicional por métrica, sin semáforo único.",
             "El color de 'ganador' borra que bloques compra memoria a cambio de tiempo.", filas=6,
             hoja=Hoja(columnas=[Columna("A","metodo",145),Columna("B","segundos",90),Columna("C","memoria_MB",95)],
                       filas=[["Pandas completo","medido","60,25"],["Pandas bloques","medido","11,31"],["DuckDB/Polars","medido","n/a"]],
                       celda="C3", formula="=MAX(memoria_de_cada_bloque)", resultado="11,31",
                       nota="La memoria de DuckDB no se compara con memoria de DataFrame.")),
        Paso("Tomar una decisión proporcional", "Se elige el camino más simple que cumple el límite real de recursos.",
             "{'este_feed': 'Pandas completo cabe', 'memoria_restringida': 'bloques', 'muchos_feeds_o_consultas': 'DuckDB/Polars'}",
             "Documentar volumen, operación, máquina y fecha junto a la elección.",
             "Extrapolar linealmente una sola corrida no sustituye medir el siguiente orden de magnitud.", mostrar="valor"),
    ]
    return Cuaderno(
        caso="P07", titulo="Cuándo conviene dejar Pandas",
        pregunta="¿Qué se gana y qué se pierde al leer completo, por bloques, con DuckDB o con Polars?",
        datos="stop_times.txt del GTFS vigente: 1 098 717 filas y la misma agregación por parada.",
        pasos=pasos, contexto={"rendimiento": rendimiento}, problema=PROBLEMA, solucion=SOLUCION,
        flujo=FLUJO, mapa=MAPA,
        cierre=("En este feed Pandas completo cabe y es simple; bloques reduce cerca de 81 % la memoria de datos. "
                "DuckDB y Polars ejecutan planes columnares con la preparación informada aparte."),
        aprendizajes=("Un benchmark empieza por igualdad de resultado.", "Tiempo y memoria son objetivos distintos.",
                      "La agregación por bloques exige una operación combinable.", "Los tiempos se vuelven a medir por equipo."),
        relacionados=(("Resultados y límites", "README.md"),
                      ("P06 · El mismo archivo en un análisis", "../gtfs_red_movilidad/CUADERNO.md")),
        anterior=("P06 · Expediciones por hora", "../gtfs_red_movilidad/CUADERNO.md"),
        siguiente=("P08 · Cobertura espacial", "../cobertura_de_carga/CUADERNO.md"),
        reproducir="python -m cases.rendimiento_gtfs.solution",
        importes="from cases.rendimiento_gtfs import solution as rendimiento",
        fuentes_datos="gtfs-red-movilidad", columnas_excel=("metodo", "segundos", "memoria_MB"),
        dependencias_colab="'duckdb>=1.0' 'polars>=1.0,<2'",
    )
