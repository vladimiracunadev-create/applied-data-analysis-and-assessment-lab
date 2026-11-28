"""P19 · Estructura de la red programada de correspondencias Metro–bus

¿Qué servicios conectan más estaciones y cómo cambia la red programada al retirarlos?

Generado por scripts/build_cuadernos.py desde cuaderno.py. No editar a mano.
La explicación de cada paso está en CUADERNO.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.red_correspondencias_dtpm import solution as network


# ----------------------------------------------------------------------------
# Paso 1 · Declarar los dos tipos de nodo
# Trampa: Usar el nombre de estación como ID fusiona homónimos.
# ----------------------------------------------------------------------------
estaciones = network.cargar()
print("\n=== Paso 1 · Declarar los dos tipos de nodo ===")
print(estaciones[['stop_id', 'stop_name', 'servicios_distintos']])

# ----------------------------------------------------------------------------
# Paso 2 · Convertir listas en aristas
# Trampa: Contar el texto separado por comas incluye espacios y duplicados.
# ----------------------------------------------------------------------------
aristas = network.aristas(estaciones)
print("\n=== Paso 2 · Convertir listas en aristas ===")
print(aristas)

# ----------------------------------------------------------------------------
# Paso 3 · Calcular el grado de cada servicio
# Trampa: Contar aristas sin deduplicar sobrestima servicios repetidos.
# ----------------------------------------------------------------------------
resultados = network.analizar()
print("\n=== Paso 3 · Calcular el grado de cada servicio ===")
print(resultados['servicios_centrales'])

# ----------------------------------------------------------------------------
# Paso 4 · Calcular el grado de cada estación
# Trampa: Más servicios no implica más frecuencia ni capacidad.
# ----------------------------------------------------------------------------
print("\n=== Paso 4 · Calcular el grado de cada estación ===")
print(resultados['grado_por_estacion'])

# ----------------------------------------------------------------------------
# Paso 5 · Publicar la regla de retiro
# Trampa: Cambiar el criterio entre escenarios invalida la comparación.
# ----------------------------------------------------------------------------
print("\n=== Paso 5 · Publicar la regla de retiro ===")
print({'orden': 'estaciones_conectadas descendente, servicio ascendente', 'escenarios': [0, 1, 3, 5, 10]})

# ----------------------------------------------------------------------------
# Paso 6 · Recalcular cinco escenarios
# Trampa: Aristas perdidas no son pasajeros afectados.
# ----------------------------------------------------------------------------
print("\n=== Paso 6 · Recalcular cinco escenarios ===")
print(resultados['escenarios'])

# ----------------------------------------------------------------------------
# Paso 7 · Visualizar los servicios de mayor alcance
# Trampa: Una barra alta no demuestra importancia social.
# ----------------------------------------------------------------------------
print("\n=== Paso 7 · Visualizar los servicios de mayor alcance ===")
print(resultados['servicios_centrales'][['servicio', 'estaciones_conectadas']])

# ----------------------------------------------------------------------------
# Paso 8 · Escribir lo que el modelo no observa
# Trampa: Llamar resiliencia operacional a este escenario excede la
# evidencia.
# ----------------------------------------------------------------------------
print("\n=== Paso 8 · Escribir lo que el modelo no observa ===")
print({'no_observa': ['pasajeros', 'GPS', 'capacidad', 'puntualidad', 'secuencia completa'], 'sí_observa': 'correspondencia programada por proximidad'})

