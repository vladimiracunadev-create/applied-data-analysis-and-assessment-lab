"""P12-P13 · ICF y distribución de la frecuencia programada

¿Qué parte del ICF se puede calcular con GTFS y cómo se distribuye la frecuencia programada?

Generado por scripts/build_cuadernos.py desde cuaderno.py. No editar a mano.
La explicación de cada paso está en CUADERNO.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.frecuencia_programada import solution as frecuencia


# ----------------------------------------------------------------------------
# Paso 1 · Leer solo tres tablas
# Trampa: Cargar por costumbre la tabla grande duplica memoria sin aportar
# una columna al cálculo.
# ----------------------------------------------------------------------------
tablas = frecuencia.cargar()
print("\n=== Paso 1 · Leer solo tres tablas ===")
print({k: v.shape for k, v in tablas.items()})

# ----------------------------------------------------------------------------
# Paso 2 · Validar las ventanas
# Trampa: Una ventana inválida no se descarta sin contarla.
# ----------------------------------------------------------------------------
ventanas = frecuencia.ventanas_programadas(tablas)
print("\n=== Paso 2 · Validar las ventanas ===")
print(ventanas[['valida','salidas_programadas']].agg(['count','sum']))

# ----------------------------------------------------------------------------
# Paso 3 · Separar programa de observación
# Trampa: 142 366 salidas programadas no son 142 366 mediciones GPS.
# ----------------------------------------------------------------------------
resultados = frecuencia.analizar()
print("\n=== Paso 3 · Separar programa de observación ===")
print(resultados['alcance_icf'])

# ----------------------------------------------------------------------------
# Paso 4 · Conservar el ICF como no calculable
# Trampa: Rellenar con cero produciría un ICF de 0 % que los datos jamás
# observaron.
# ----------------------------------------------------------------------------
print("\n=== Paso 4 · Conservar el ICF como no calculable ===")
print(resultados['alcance_icf'].query("calculable_con_gtfs == 'NO'"))

# ----------------------------------------------------------------------------
# Paso 5 · Describir la distribución
# En Excel: =PERCENTIL.INC(rango_intervalo_min;0,5)
# Trampa: La media de 21,17 minutos no representa la ventana típica de 15.
# ----------------------------------------------------------------------------
print("\n=== Paso 5 · Describir la distribución ===")
print(resultados['distribucion'])

# ----------------------------------------------------------------------------
# Paso 6 · Cambiar la unidad de análisis
# Trampa: Promediar servicios sin declarar peso da el mismo voto a uno
# diario y a uno intensivo.
# ----------------------------------------------------------------------------
print("\n=== Paso 6 · Cambiar la unidad de análisis ===")
print(resultados['ponderaciones'])

# ----------------------------------------------------------------------------
# Paso 7 · Filtrar la punta por intersección
# Trampa: Filtrar solo start_time pierde ventanas que comenzaron antes de
# las 08:00.
# ----------------------------------------------------------------------------
print("\n=== Paso 7 · Filtrar la punta por intersección ===")
print(resultados['punta_manana'].head(15))

# ----------------------------------------------------------------------------
# Paso 8 · Publicar una conclusión proporcional
# Trampa: Un intervalo programado largo puede ser diseño de servicio; no
# demuestra falla operacional.
# ----------------------------------------------------------------------------
print("\n=== Paso 8 · Publicar una conclusión proporcional ===")
print(resultados['ventanas_invalidas'])

