"""Cuaderno de P18: ETL histórico y control automatizado GTFS."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.etl_gtfs_automatizado import solution as etl  # noqa: E402
from lab.cuaderno import Cuaderno, Paso  # noqa: E402
from lab.diagrama_svg import ACENTO, AZUL, OCRE, TINTA, Etapa, Flujo, Mapa, Rama  # noqa: E402

PROBLEMA = """
Una carpeta con publicaciones históricas no es todavía un pipeline incremental. Un
corte duplicado, una fecha ilegible o un volumen vacío debe detener el proceso antes de
mezclarse con la historia. P18 enseña ese contrato sin prometer un formato o un motor
que no se ejecutó.
"""

SOLUCION = """
Se valida el inventario producido por P14/P15, se tipan fechas y magnitudes, se publican
cinco controles independientes y se calcula una partición determinista. La ruta Parquet
es opcional y falla con una instrucción concreta cuando falta su motor.
"""

FLUJO = Flujo(titulo="ETL incremental de publicaciones GTFS", etapas=[
    Etapa("Entrada", ["inventario P14/P15", "3 cortes", "misma definición"], color=TINTA),
    Etapa("Contrato", ["columnas", "tipos", "unicidad"], color=AZUL),
    Etapa("Transformar", ["fecha", "MB", "partición"], color=OCRE),
    Etapa("Publicar", ["CSV ejecutado", "Parquet opcional", "estado honesto"], color=ACENTO),
])
MAPA = Mapa(centro="P18 · ETL GTFS", subtitulo="8 pasos", ramas=[
    Rama("Entrada", ["1 · Inventario", "2 · Contrato"], color=AZUL),
    Rama("Calidad", ["3 · Tipos", "4 · Controles"], color=OCRE),
    Rama("Incremental", ["5 · Particiones", "6 · Volumen"], color=AZUL),
    Rama("Salida", ["7 · Formatos", "8 · Recuperación"], color=ACENTO),
])


def construir() -> Cuaderno:
    pasos = [
        Paso("Leer el inventario reproducible", "La entrada es el resultado versionado de P14/P15, no una cifra copiada.",
             "inventario = etl.cargar()\ninventario", "Importar la tabla y conservar la fecha como texto hasta validarla.",
             "Concatenar publicaciones sin guardar el corte impide reconstruir la historia.", filas=5),
        Paso("Comprobar el esquema", "El pipeline falla antes de calcular cuando falta una columna contractual.",
             "{'requeridas': len(etl.REQUIRED), 'presentes': len(set(inventario.columns) & etl.REQUIRED), 'filas': len(inventario)}",
             "Comparar encabezados con una lista de campos requeridos.", "Aceptar columnas por posición desplaza silenciosamente las medidas.", mostrar="valor"),
        Paso("Tipar y validar magnitudes", "Fechas y conteos se interpretan explícitamente antes de derivar métricas.",
             "transformado = etl.transformar(inventario)\ntransformado[['publicacion', 'anio', 'filas_stop_times', 'mb_stop_times']]",
             "`=ESNUMERO(fecha)` y reglas `>=0` para cada medida.", "Convertir errores a nulos permite que un corte roto continúe.", filas=5),
        Paso("Publicar cada control", "Cinco resultados separados permiten saber qué regla falló.",
             "controles = etl.controles(transformado)\ncontroles", "Una fila por regla con nombre, resultado y explicación.",
             "Un único estado global borra la causa del fallo.", filas=8),
        Paso("Construir particiones deterministas", "La fecha del corte es la identidad incremental y evita reescribir toda la historia.",
             "transformado[['publicacion', 'particion']]", "`=AÑO(fecha)` y texto ISO para la carpeta.",
             "Particionar sólo por año produce colisiones si hay dos cortes anuales.", filas=5),
        Paso("Medir el volumen por publicación", "El volumen permite detectar cambios que requieren inspección sin atribuirles una causa.",
             "resultados = etl.analizar()\nresultados['volumen_por_publicacion']", "Convertir bytes a MB con divisor declarado de 1.000.000.",
             "Un cambio de tamaño no demuestra por sí mismo un cambio de servicio.", filas=5),
        Paso("Distinguir formatos ejecutados", "La salida informa la disponibilidad real de Parquet.",
             "resultados['formatos']", "Registrar formato, estado y requisito en tres columnas.",
             "Renombrar un CSV como `.parquet` no crea un archivo columnar.", filas=5),
        Paso("Definir recuperación y reintento", "Un nuevo corte se incorpora sólo después de validar; un fallo conserva el último resultado válido.",
             "{'orden': ['descargar', 'registrar huella', 'validar', 'transformar', 'publicar'], 'ante_fallo': 'no reemplazar salida válida'}",
             "Hoja de control con fecha, huella, estado y mensaje de error.",
             "Reintentar sin registrar el error oculta una fuente inestable.", mostrar="valor"),
    ]
    return Cuaderno(
        caso="P18", titulo="ETL histórico y control automatizado de publicaciones GTFS",
        pregunta="¿Cómo incorporar un nuevo corte GTFS sin romper la serie ni fingir formatos no ejecutados?",
        datos="Inventario reproducible de P14/P15 para publicaciones DTPM 2024–2026.",
        pasos=pasos, contexto={"etl": etl}, problema=PROBLEMA, solucion=SOLUCION,
        flujo=FLUJO, mapa=MAPA,
        cierre="El corte sólo se publica si sus controles pasan; Parquet permanece opcional y verificable.",
        aprendizajes=("Validar antes de transformar.", "Incremental necesita identidad.",
                      "Cada control conserva evidencia.", "No ejecutado debe declararse."),
        relacionados=(("P14/P15 · Origen del inventario", "../evolucion_gtfs/CUADERNO.md"),
                      ("P17 · Gobernanza", "../gobernanza_datos_dtpm/CUADERNO.md")),
        reproducir="python -m cases.etl_gtfs_automatizado.solution",
        importes="from cases.etl_gtfs_automatizado import solution as etl",
        dependencias_colab="pyarrow>=15",
        columnas_excel=("publicacion", "filas_stop_times", "bytes_stop_times", "particion"),
    )
