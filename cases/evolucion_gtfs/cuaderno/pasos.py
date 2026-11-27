"""P14-P15 · Cambios de red y oferta entre publicaciones GTFS

¿Qué cambió entre 2024 y 2026 y cómo varió la oferta programada por hora?

Generado por scripts/build_cuadernos.py desde cuaderno.py. No editar a mano.
La explicación de cada paso está en CUADERNO.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.evolucion_gtfs import solution as evolucion


# ----------------------------------------------------------------------------
# Paso 1 · Nombrar las publicaciones por fecha
# Trampa: Llamar a ambos archivos 'GTFS' borra qué estado de la red
# representa cada uno.
# ----------------------------------------------------------------------------
print("\n=== Paso 1 · Nombrar las publicaciones por fecha ===")
print([(r.etiqueta, r.ruta.name, r.miembro or 'ZIP directo') for r in evolucion.REFERENCIAS])

# ----------------------------------------------------------------------------
# Paso 2 · Inventariar antes de comparar
# Trampa: El salto de viajes declarados no se interpreta antes de revisar la
# mecánica de frecuencias.
# ----------------------------------------------------------------------------
resultados = evolucion.analizar()
print("\n=== Paso 2 · Inventariar antes de comparar ===")
print(resultados['inventario'])

# ----------------------------------------------------------------------------
# Paso 3 · Comparar rutas como conjuntos
# Trampa: Una baja de route_id no prueba que el recorrido físico dejó de
# existir.
# ----------------------------------------------------------------------------
print("\n=== Paso 3 · Comparar rutas como conjuntos ===")
print(resultados['identidades'].query("entidad == 'rutas'"))

# ----------------------------------------------------------------------------
# Paso 4 · Comparar solo paradas de embarque
# Trampa: Comparar todo stops.txt confunde cambios de jerarquía con paradas
# nuevas.
# ----------------------------------------------------------------------------
print("\n=== Paso 4 · Comparar solo paradas de embarque ===")
print(resultados['identidades'].query("entidad == 'paradas de embarque'"))

# ----------------------------------------------------------------------------
# Paso 5 · Firmar el trazado, no solo el ID
# Trampa: Un shape_id estable puede ocultar coordenadas nuevas; uno nuevo
# puede dibujar lo mismo.
# ----------------------------------------------------------------------------
print("\n=== Paso 5 · Firmar el trazado, no solo el ID ===")
print(resultados['trazados'].query('cambio_de_conjunto').head(15))

# ----------------------------------------------------------------------------
# Paso 6 · Recalcular la oferta por hora
# Trampa: Comparar filas de trips.txt daría una serie rota: una ventana
# representa muchas salidas.
# ----------------------------------------------------------------------------
print("\n=== Paso 6 · Recalcular la oferta por hora ===")
print(resultados['oferta_por_hora'].head(30))

# ----------------------------------------------------------------------------
# Paso 7 · Medir el cambio total
# En Excel: =(B3/B2)-1
# Trampa: Tres puntos describen una trayectoria reciente, no toda la serie
# 2014–2026.
# ----------------------------------------------------------------------------
print("\n=== Paso 7 · Medir el cambio total ===")
print(resultados['oferta_total'])

# ----------------------------------------------------------------------------
# Paso 8 · Dejar preparada la ampliación
# Trampa: Completar años con cifras copiadas de informes rompería la
# comparabilidad del método.
# ----------------------------------------------------------------------------
print("\n=== Paso 8 · Dejar preparada la ampliación ===")
print({'publicaciones_ejecutadas': len(evolucion.REFERENCIAS), 'primera': evolucion.REFERENCIAS[0].etiqueta, 'ultima': evolucion.REFERENCIAS[-1].etiqueta})

