"""P20 · Optimización exploratoria de una cartera de estudios para carga bip!

¿Qué combinación de zonas conviene estudiar primero bajo un presupuesto y una regla de diversidad explícitos?

Generado por scripts/build_cuadernos.py desde cuaderno.py. No editar a mano.
La explicación de cada paso está en CUADERNO.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.optimizacion_carga_bip import solution as portfolio


# ----------------------------------------------------------------------------
# Paso 1 · Validar el contrato heredado de P16
# Trampa: Tratar prioridad como demanda convierte una regla de cribado en
# una medición inexistente.
# ----------------------------------------------------------------------------
datos = portfolio.cargar()
print("\n=== Paso 1 · Validar el contrato heredado de P16 ===")
print(datos)

# ----------------------------------------------------------------------------
# Paso 2 · Crear candidatos y bandas relativas
# Trampa: Llamar comuna a la banda inventaría una geografía administrativa.
# ----------------------------------------------------------------------------
candidatos = portfolio.preparar_candidatos(datos)
print("\n=== Paso 2 · Crear candidatos y bandas relativas ===")
print(candidatos[['candidato_id', 'celda_lat', 'celda_lon', 'banda_territorial', 'prioridad_exploratoria']])

# ----------------------------------------------------------------------------
# Paso 3 · Definir la variable de decisión
# Trampa: Permitir valores fraccionarios describe medio estudio y cambia el
# problema.
# ----------------------------------------------------------------------------
print("\n=== Paso 3 · Definir la variable de decisión ===")
print({'variable': 'x_i ∈ {0,1}', 'objetivo': 'max Σ prioridad_i × x_i', 'presupuesto': 'Σ x_i = k'})

# ----------------------------------------------------------------------------
# Paso 4 · Hacer visible la diversidad mínima
# Trampa: Agregar la restricción después de ver el ganador sería ajustar la
# regla al resultado.
# ----------------------------------------------------------------------------
print("\n=== Paso 4 · Hacer visible la diversidad mínima ===")
print({k: min(k, 3) for k in range(1, 6)})

# ----------------------------------------------------------------------------
# Paso 5 · Enumerar las combinaciones factibles
# Trampa: Usar una heurística sin necesidad puede ocultar una cartera mejor.
# ----------------------------------------------------------------------------
frontera, alternativas = portfolio.optimizar(candidatos)
print("\n=== Paso 5 · Enumerar las combinaciones factibles ===")
print(alternativas)

# ----------------------------------------------------------------------------
# Paso 6 · Construir la frontera presupuestaria
# Trampa: Comparar carteras de distinto tamaño sin declarar presupuesto
# favorece siempre la más grande.
# ----------------------------------------------------------------------------
print("\n=== Paso 6 · Construir la frontera presupuestaria ===")
print(frontera)

# ----------------------------------------------------------------------------
# Paso 7 · Visualizar valor acumulado por presupuesto
# Trampa: Etiquetar el eje como rentabilidad atribuye dinero que el modelo
# no contiene.
# ----------------------------------------------------------------------------
print("\n=== Paso 7 · Visualizar valor acumulado por presupuesto ===")
print(frontera[['presupuesto', 'puntaje_total']])

# ----------------------------------------------------------------------------
# Paso 8 · Separar estudio, factibilidad e inversión
# Trampa: Presentar coordenadas como sitios aprobados excede la evidencia y
# el alcance de P20.
# ----------------------------------------------------------------------------
resultados = portfolio.analizar()
print("\n=== Paso 8 · Separar estudio, factibilidad e inversión ===")
print(resultados['seleccion_presupuesto_4'][['candidato_id', 'banda_territorial', 'prioridad_exploratoria']])

