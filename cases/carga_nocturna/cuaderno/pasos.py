"""P05-P09 · Horarios libres y cobertura de carga nocturna

Donde hay buses entre las 00:00 y las 05:00, ¿hay dónde cargar la tarjeta?

Generado por scripts/build_cuadernos.py desde cuaderno.py. No editar a mano.
La explicación de cada paso está en CUADERNO.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.carga_nocturna import solution as p09


# ----------------------------------------------------------------------------
# Paso 1 · Auditar las ventanas de servicio
# Trampa: Una ventana que empieza antes de medianoche puede aportar servicio
# después de las 00:00.
# ----------------------------------------------------------------------------
resultados = p09.analizar()
print("\n=== Paso 1 · Auditar las ventanas de servicio ===")
print(resultados['ventanas_por_servicio'])

# ----------------------------------------------------------------------------
# Paso 2 · Demostrar por qué el filtro textual falla
# Trampa: El 100 % de las filas que toma el atajo son desplazamientos
# relativos, no horas.
# ----------------------------------------------------------------------------
print("\n=== Paso 2 · Demostrar por qué el filtro textual falla ===")
print(resultados['atajo_comparado'])

# ----------------------------------------------------------------------------
# Paso 3 · Describir la intensidad nocturna
# En Excel: =PERCENTIL.INC(rango_llegadas;0,5)
# Trampa: Una sola llegada y 459 llegadas no representan la misma
# disponibilidad.
# ----------------------------------------------------------------------------
print("\n=== Paso 3 · Describir la intensidad nocturna ===")
print(resultados['intensidad'])

# ----------------------------------------------------------------------------
# Paso 4 · Convertir horarios libres en datos
# Trampa: Vacío no significa cerrado: significa que el publicador no entregó
# el campo.
# ----------------------------------------------------------------------------
print("\n=== Paso 4 · Convertir horarios libres en datos ===")
print(resultados['horarios_interpretados'])

# ----------------------------------------------------------------------------
# Paso 5 · Medir la cobertura del campo horario
# En Excel: =CONTAR.SI.CONJUNTO(tipo;A2;horario;"<>")/CONTAR.SI(tipo;A2)
# Trampa: Promediar por archivo daría 80 %: cuatro fuentes completas y una
# vacía, sin ponderar sus tamaños.
# ----------------------------------------------------------------------------
print("\n=== Paso 5 · Medir la cobertura del campo horario ===")
print(resultados['cobertura_del_campo'])

# ----------------------------------------------------------------------------
# Paso 6 · Clasificar en cuatro estados observables
# Trampa: Reducir a cubierto/no cubierto mezcla 5 536 incógnitas con
# evidencia negativa.
# ----------------------------------------------------------------------------
print("\n=== Paso 6 · Clasificar en cuatro estados observables ===")
print(resultados['respuesta'])

# ----------------------------------------------------------------------------
# Paso 7 · Comprobar estabilidad por tipo de día
# Trampa: Sumar los servicios repite una parada hasta tres veces; cada
# denominador se interpreta por separado.
# ----------------------------------------------------------------------------
print("\n=== Paso 7 · Comprobar estabilidad por tipo de día ===")
print(resultados['por_servicio'])

# ----------------------------------------------------------------------------
# Paso 8 · Expresar la respuesta como intervalo
# En Excel: =(abiertos_verificados+indeterminados)/total_nocturnas
# Trampa: Elegir el punto medio no agrega información: inventa una
# probabilidad que los datos no contienen.
# ----------------------------------------------------------------------------
print("\n=== Paso 8 · Expresar la respuesta como intervalo ===")
print(resultados['intervalo'])

# ----------------------------------------------------------------------------
# Paso 9 · Convertir la incertidumbre en una tarea
# Trampa: Pedir 'mejorar los datos' sin señalar el campo y el impacto no es
# una recomendación ejecutable.
# ----------------------------------------------------------------------------
print("\n=== Paso 9 · Convertir la incertidumbre en una tarea ===")
print(resultados['lo_que_falta'])

