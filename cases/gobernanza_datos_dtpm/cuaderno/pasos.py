"""P17 · Gobernanza y catálogo de activos de datos DTPM

¿Qué información de gobernanza falta aclarar para los activos usados por P01–P16?

Generado por scripts/build_cuadernos.py desde cuaderno.py. No editar a mano.
La explicación de cada paso está en CUADERNO.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.gobernanza_datos_dtpm import solution as governance


# ----------------------------------------------------------------------------
# Paso 1 · Nombrar el grano del catálogo
# Trampa: Contar cada publicación mensual como un activo infla el inventario
# y mezcla versión con identidad.
# ----------------------------------------------------------------------------
catalogo = governance.cargar()
print("\n=== Paso 1 · Nombrar el grano del catálogo ===")
print(catalogo[['activo_id', 'nombre', 'publicador', 'formato']])

# ----------------------------------------------------------------------------
# Paso 2 · Validar el contrato mínimo
# Trampa: Una columna llamada ID no garantiza unicidad.
# ----------------------------------------------------------------------------
print("\n=== Paso 2 · Validar el contrato mínimo ===")
print({'filas': len(catalogo), 'ids_unicos': catalogo['activo_id'].nunique(), 'criticidades': sorted(catalogo['criticidad'].unique())})

# ----------------------------------------------------------------------------
# Paso 3 · Conservar lo no declarado
# Trampa: Completar responsable o retención por intuición fabrica evidencia.
# ----------------------------------------------------------------------------
print("\n=== Paso 3 · Conservar lo no declarado ===")
print(catalogo[['activo_id', 'responsable_operativo', 'retencion_meses', 'actualizacion_declarada']])

# ----------------------------------------------------------------------------
# Paso 4 · Calcular las cinco banderas
# Trampa: Un puntaje sin componentes no se puede auditar.
# ----------------------------------------------------------------------------
auditoria = governance.evaluar(catalogo)
print("\n=== Paso 4 · Calcular las cinco banderas ===")
print(auditoria[['activo_id', 'brecha_licencia', 'brecha_esquema', 'brecha_actualizacion', 'brecha_responsable', 'brecha_retencion']])

# ----------------------------------------------------------------------------
# Paso 5 · Publicar la fórmula de prioridad
# Trampa: El puntaje ordena aclaraciones; no es una probabilidad.
# ----------------------------------------------------------------------------
print("\n=== Paso 5 · Publicar la fórmula de prioridad ===")
print(auditoria[['activo_id', 'puntaje_brecha', 'peso_criticidad', 'puntaje_riesgo']].sort_values('puntaje_riesgo', ascending=False))

# ----------------------------------------------------------------------------
# Paso 6 · Contar activos afectados por brecha
# Trampa: Cinco brechas de un activo no equivalen a cinco activos.
# ----------------------------------------------------------------------------
resultados = governance.analizar(catalogo)
print("\n=== Paso 6 · Contar activos afectados por brecha ===")
print(resultados['brechas'])

# ----------------------------------------------------------------------------
# Paso 7 · Construir el ranking de atención
# Trampa: Ocultar empates hace parecer más precisa una prioridad ordinal.
# ----------------------------------------------------------------------------
print("\n=== Paso 7 · Construir el ranking de atención ===")
print(resultados['riesgo_por_activo'])

# ----------------------------------------------------------------------------
# Paso 8 · Traducir el resultado en acciones
# Trampa: El laboratorio no puede nombrar responsables institucionales por
# cuenta propia.
# ----------------------------------------------------------------------------
print("\n=== Paso 8 · Traducir el resultado en acciones ===")
print({'licencia': 'verificar condiciones', 'esquema': 'publicar contrato', 'actualizacion': 'declarar periodicidad', 'responsable': 'validar stewardship', 'retencion': 'definir ciclo de vida'})

