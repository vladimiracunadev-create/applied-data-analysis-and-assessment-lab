"""P07 · Cuándo conviene dejar Pandas

¿Qué se gana y qué se pierde al leer completo, por bloques o con DuckDB?

Generado por scripts/build_cuadernos.py desde cuaderno.py. No editar a mano.
La explicación de cada paso está en CUADERNO.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.rendimiento_gtfs import solution as rendimiento


# ----------------------------------------------------------------------------
# Paso 1 · Fijar una agregación idéntica
# Trampa: Comparar una lectura selectiva con otra que carga ocho columnas
# mide cosas distintas.
# ----------------------------------------------------------------------------
print("\n=== Paso 1 · Fijar una agregación idéntica ===")
print({'archivo': 'stop_times.txt', 'operacion': 'COUNT(*) GROUP BY stop_id', 'columnas': ['stop_id']})

# ----------------------------------------------------------------------------
# Paso 2 · Declarar qué se mide
# Trampa: Un único tiempo total oculta que DuckDB necesita preparar un CSV
# temporal.
# ----------------------------------------------------------------------------
print("\n=== Paso 2 · Declarar qué se mide ===")
print(['segundos','lectura_s','agregacion_s','memoria_datos_mb','bloques','filas_entrada'])

# ----------------------------------------------------------------------------
# Paso 3 · Ejecutar Pandas completo
# Trampa: El DataFrame usa más memoria que los 51 MB del CSV porque cada
# texto es un objeto.
# ----------------------------------------------------------------------------
referencia = rendimiento.cargar_referencia()
print("\n=== Paso 3 · Ejecutar Pandas completo ===")
print(referencia['benchmark'].query("metodo == 'Pandas completo'"))

# ----------------------------------------------------------------------------
# Paso 4 · Ejecutar Pandas por bloques
# Trampa: Una mediana exacta no se puede combinar sumando medianas de
# bloques.
# ----------------------------------------------------------------------------
print("\n=== Paso 4 · Ejecutar Pandas por bloques ===")
print(referencia['benchmark'].query("metodo == 'Pandas por bloques'"))

# ----------------------------------------------------------------------------
# Paso 5 · Ejecutar DuckDB
# Trampa: Sumar extracción y consulta o excluirla cambia la pregunta; por
# eso se muestran ambas.
# ----------------------------------------------------------------------------
print("\n=== Paso 5 · Ejecutar DuckDB ===")
print(referencia['benchmark'].query("metodo == 'DuckDB sobre CSV'"))

# ----------------------------------------------------------------------------
# Paso 6 · Exigir igualdad antes de mirar velocidad
# Trampa: Comparar solo el total puede ocultar errores que se compensan
# entre paradas.
# ----------------------------------------------------------------------------
print("\n=== Paso 6 · Exigir igualdad antes de mirar velocidad ===")
print(referencia['validacion'])

# ----------------------------------------------------------------------------
# Paso 7 · Comparar tiempo y memoria
# Trampa: El color de 'ganador' borra que bloques compra memoria a cambio de
# tiempo.
# ----------------------------------------------------------------------------
print("\n=== Paso 7 · Comparar tiempo y memoria ===")
print(referencia['benchmark'])

# ----------------------------------------------------------------------------
# Paso 8 · Tomar una decisión proporcional
# Trampa: Extrapolar linealmente una sola corrida no sustituye medir el
# siguiente orden de magnitud.
# ----------------------------------------------------------------------------
print("\n=== Paso 8 · Tomar una decisión proporcional ===")
print({'este_feed': 'Pandas completo cabe', 'memoria_restringida': 'bloques', 'muchos_feeds_o_consultas': 'DuckDB/columnar'})

