"""P18 · ETL histórico y control automatizado de publicaciones GTFS

¿Cómo incorporar un nuevo corte GTFS sin romper la serie ni fingir formatos no ejecutados?

Generado por scripts/build_cuadernos.py desde cuaderno.py. No editar a mano.
La explicación de cada paso está en CUADERNO.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.etl_gtfs_automatizado import solution as etl


# ----------------------------------------------------------------------------
# Paso 1 · Leer el inventario reproducible
# Trampa: Concatenar publicaciones sin guardar el corte impide reconstruir
# la historia.
# ----------------------------------------------------------------------------
inventario = etl.cargar()
print("\n=== Paso 1 · Leer el inventario reproducible ===")
print(inventario)

# ----------------------------------------------------------------------------
# Paso 2 · Comprobar el esquema
# Trampa: Aceptar columnas por posición desplaza silenciosamente las
# medidas.
# ----------------------------------------------------------------------------
print("\n=== Paso 2 · Comprobar el esquema ===")
print({'requeridas': len(etl.REQUIRED), 'presentes': len(set(inventario.columns) & etl.REQUIRED), 'filas': len(inventario)})

# ----------------------------------------------------------------------------
# Paso 3 · Tipar y validar magnitudes
# Trampa: Convertir errores a nulos permite que un corte roto continúe.
# ----------------------------------------------------------------------------
transformado = etl.transformar(inventario)
print("\n=== Paso 3 · Tipar y validar magnitudes ===")
print(transformado[['publicacion', 'anio', 'filas_stop_times', 'mb_stop_times']])

# ----------------------------------------------------------------------------
# Paso 4 · Publicar cada control
# Trampa: Un único estado global borra la causa del fallo.
# ----------------------------------------------------------------------------
controles = etl.controles(transformado)
print("\n=== Paso 4 · Publicar cada control ===")
print(controles)

# ----------------------------------------------------------------------------
# Paso 5 · Construir particiones deterministas
# Trampa: Particionar sólo por año produce colisiones si hay dos cortes
# anuales.
# ----------------------------------------------------------------------------
print("\n=== Paso 5 · Construir particiones deterministas ===")
print(transformado[['publicacion', 'particion']])

# ----------------------------------------------------------------------------
# Paso 6 · Medir el volumen por publicación
# Trampa: Un cambio de tamaño no demuestra por sí mismo un cambio de
# servicio.
# ----------------------------------------------------------------------------
resultados = etl.analizar()
print("\n=== Paso 6 · Medir el volumen por publicación ===")
print(resultados['volumen_por_publicacion'])

# ----------------------------------------------------------------------------
# Paso 7 · Distinguir formatos ejecutados
# Trampa: Renombrar un CSV como .parquet no crea un archivo columnar.
# ----------------------------------------------------------------------------
print("\n=== Paso 7 · Distinguir formatos ejecutados ===")
print(resultados['formatos'])

# ----------------------------------------------------------------------------
# Paso 8 · Definir recuperación y reintento
# Trampa: Reintentar sin registrar el error oculta una fuente inestable.
# ----------------------------------------------------------------------------
print("\n=== Paso 8 · Definir recuperación y reintento ===")
print({'orden': ['descargar', 'registrar huella', 'validar', 'transformar', 'publicar'], 'ante_fallo': 'no reemplazar salida válida'})

