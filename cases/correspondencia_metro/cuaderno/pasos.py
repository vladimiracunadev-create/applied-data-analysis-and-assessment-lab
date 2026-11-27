"""P03-P10 · Conciliar Metro y medir correspondencias con buses

¿Qué estaciones de Metro tienen buses a 200 m y cuánto depende la respuesta de la fuente?

Generado por scripts/build_cuadernos.py desde cuaderno.py. No editar a mano.
La explicación de cada paso está en CUADERNO.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.correspondencia_metro import solution as p10


# ----------------------------------------------------------------------------
# Paso 1 · Diagnosticar el grano de las dos fuentes
# Trampa: Forzar una unión uno a uno elimina 17 filas legítimas de
# estaciones de combinación.
# ----------------------------------------------------------------------------
resultados = p10.analizar()
print("\n=== Paso 1 · Diagnosticar el grano de las dos fuentes ===")
print(resultados['grano'])

# ----------------------------------------------------------------------------
# Paso 2 · Conciliar por nombre y por distancia
# Trampa: El nombre encuentra 125 de 126; la fila restante no debe
# desaparecer en silencio.
# ----------------------------------------------------------------------------
print("\n=== Paso 2 · Conciliar por nombre y por distancia ===")
print(resultados['conciliacion'])

# ----------------------------------------------------------------------------
# Paso 3 · Revisar donde los criterios discrepan
# Trampa: Elegir automáticamente el criterio con más coincidencias puede
# confirmar una coordenada corrupta.
# ----------------------------------------------------------------------------
print("\n=== Paso 3 · Revisar donde los criterios discrepan ===")
print(resultados['criterios_discrepantes'])

# ----------------------------------------------------------------------------
# Paso 4 · Declarar el punto ciego de cada detector
# Trampa: UTM y lat/lon pueden estar ambas equivocadas de la misma forma: el
# detector interno no lo ve.
# ----------------------------------------------------------------------------
print("\n=== Paso 4 · Declarar el punto ciego de cada detector ===")
print(resultados['detectores'])

# ----------------------------------------------------------------------------
# Paso 5 · Medir la correspondencia a 200 metros
# En Excel: =CONTAR.SI.CONJUNTO(estacion;A2;distancia_m;"<=200")
# Trampa: Contar filas de horarios multiplica un mismo servicio; la unidad
# es servicio distinto.
# ----------------------------------------------------------------------------
print("\n=== Paso 5 · Medir la correspondencia a 200 metros ===")
print(resultados['correspondencia'])

# ----------------------------------------------------------------------------
# Paso 6 · Mostrar la distribución de servicios
# Trampa: El máximo de 55 describe Santa Lucía, no la estación típica; la
# mediana es 13.
# ----------------------------------------------------------------------------
print("\n=== Paso 6 · Mostrar la distribución de servicios ===")
print(resultados['resumen'])

# ----------------------------------------------------------------------------
# Paso 7 · Identificar las estaciones con más alternativas
# Trampa: Más paradas físicas no implica necesariamente más servicios
# diferentes.
# ----------------------------------------------------------------------------
print("\n=== Paso 7 · Identificar las estaciones con más alternativas ===")
print(resultados['mejores_correspondencias'])

# ----------------------------------------------------------------------------
# Paso 8 · Medir la sensibilidad a la fuente de coordenadas
# Trampa: Con bip!, tres estaciones parecerían no tener bus y 48 cambian su
# conteo de servicios.
# ----------------------------------------------------------------------------
print("\n=== Paso 8 · Medir la sensibilidad a la fuente de coordenadas ===")
print(resultados['sensibilidad_a_la_fuente'])

# ----------------------------------------------------------------------------
# Paso 9 · Separar hallazgo de explicación
# Trampa: Un desvío demuestra inconsistencia entre fuentes, no cuál de las
# dos es correcta ni por qué.
# ----------------------------------------------------------------------------
print("\n=== Paso 9 · Separar hallazgo de explicación ===")
print(resultados['detector_4_contra_gtfs'])

