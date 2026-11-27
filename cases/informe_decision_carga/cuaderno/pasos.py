"""P16 · Informe de una página para quien decide

¿Qué zonas conviene estudiar para un nuevo centro de carga y qué no se puede afirmar todavía?

Generado por scripts/build_cuadernos.py desde cuaderno.py. No editar a mano.
La explicación de cada paso está en CUADERNO.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.informe_decision_carga import solution as decision


# ----------------------------------------------------------------------------
# Paso 1 · Auditar las tablas de entrada
# Trampa: Copiar cuatro números a una diapositiva rompe la trazabilidad
# hasta su denominador.
# ----------------------------------------------------------------------------
tablas = decision.cargar()
print("\n=== Paso 1 · Auditar las tablas de entrada ===")
print({k: v.shape for k, v in tablas.items()})

# ----------------------------------------------------------------------------
# Paso 2 · Reducir a cuatro indicadores
# Trampa: 64 011 salidas son oferta programada, no viajes de personas.
# ----------------------------------------------------------------------------
resultados = decision.analizar()
print("\n=== Paso 2 · Reducir a cuatro indicadores ===")
print(resultados['resumen'])

# ----------------------------------------------------------------------------
# Paso 3 · Declarar la regla de prioridad
# Trampa: Un puntaje sin fórmula publicada convierte criterio en opinión.
# ----------------------------------------------------------------------------
print("\n=== Paso 3 · Declarar la regla de prioridad ===")
print({'formula': 'paradas_sin_cobertura × mediana_m', 'uso': 'ordenar estudios de factibilidad'})

# ----------------------------------------------------------------------------
# Paso 4 · Construir una lista corta
# Trampa: La coordenada de celda no es un predio ni una recomendación de
# construcción.
# ----------------------------------------------------------------------------
print("\n=== Paso 4 · Construir una lista corta ===")
print(resultados['prioridades'])

# ----------------------------------------------------------------------------
# Paso 5 · Clasificar cada afirmación
# Trampa: Presentar una hipótesis como evidencia es más dañino que omitirla.
# ----------------------------------------------------------------------------
print("\n=== Paso 5 · Clasificar cada afirmación ===")
print(resultados['afirmaciones'])

# ----------------------------------------------------------------------------
# Paso 6 · Escribir lo que no se puede concluir
# Trampa: Baja cobertura no equivale a alta necesidad.
# ----------------------------------------------------------------------------
print("\n=== Paso 6 · Escribir lo que no se puede concluir ===")
print(resultados['afirmaciones'].query("tipo == 'no demostrable'"))

# ----------------------------------------------------------------------------
# Paso 7 · Validar la completitud
# Trampa: Un resumen sin supuestos o limitaciones parece más concluyente de
# lo que es.
# ----------------------------------------------------------------------------
print("\n=== Paso 7 · Validar la completitud ===")
print(resultados['completitud'])

# ----------------------------------------------------------------------------
# Paso 8 · Exportar el entregable reproducible
# Trampa: El formato profesional no sustituye el vínculo al cálculo.
# ----------------------------------------------------------------------------
ruta = decision.exportar(resultados)
print("\n=== Paso 8 · Exportar el entregable reproducible ===")
print(str(ruta / 'informe.md'))

