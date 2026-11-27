"""P08 · Distancia al lugar de carga más cercano

¿Qué proporción de las paradas tiene un lugar de carga bip! a 300 metros o menos?

Generado por scripts/build_cuadernos.py desde cuaderno.py. No editar a mano.
La explicación de cada paso está en CUADERNO.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.cobertura_de_carga import solution as p08
import pandas as pd


# ----------------------------------------------------------------------------
# Paso 1 · Fijar qué filas son paradas
# Trampa: Contar todo stops.txt agrega 5 989 elementos que no son paradas de
# embarque.
# ----------------------------------------------------------------------------
resultados = p08.analizar()
print("\n=== Paso 1 · Fijar qué filas son paradas ===")
print(resultados['paradas_por_tipo'])

# ----------------------------------------------------------------------------
# Paso 2 · Comprobar la llave de los locales
# Trampa: En Metro el código es la línea: 143 filas comparten solo siete
# códigos.
# ----------------------------------------------------------------------------
print("\n=== Paso 2 · Comprobar la llave de los locales ===")
print(resultados['identificador'])

# ----------------------------------------------------------------------------
# Paso 3 · Medir el vecino más cercano
# Trampa: Crear la matriz completa consume memoria innecesaria; por bloques
# conserva el mismo mínimo.
# ----------------------------------------------------------------------------
print("\n=== Paso 3 · Medir el vecino más cercano ===")
print(resultados['resumen'])

# ----------------------------------------------------------------------------
# Paso 4 · Describir la distribución, no solo la media
# En Excel: =PERCENTIL.INC(rango_distancia;0,5)
# Trampa: El máximo de 40 km pertenece al borde de cobertura de los
# archivos, no a una caminata plausible.
# ----------------------------------------------------------------------------
print("\n=== Paso 4 · Describir la distribución, no solo la media ===")
print(resultados['distribucion'])

# ----------------------------------------------------------------------------
# Paso 5 · Mostrar cuánto depende del umbral
# En Excel: =CONTAR.SI(rango_distancia;"<="&E2)/CONTAR(rango_distancia)
# Trampa: Elegir el umbral después de ver el resultado convierte el criterio
# en una meta móvil.
# ----------------------------------------------------------------------------
print("\n=== Paso 5 · Mostrar cuánto depende del umbral ===")
print(resultados['cobertura_por_umbral'])

# ----------------------------------------------------------------------------
# Paso 6 · Separar línea recta de distancia caminada
# En Excel: =SUMAPRODUCTO(--(rango_distancia*factor<=300))/CONTAR(rango_distancia)
# Trampa: Decir 300 m caminando a partir de una línea geodésica sobrestima
# la cobertura.
# ----------------------------------------------------------------------------
print("\n=== Paso 6 · Separar línea recta de distancia caminada ===")
print(resultados['sensibilidad_rodeo'])

# ----------------------------------------------------------------------------
# Paso 7 · Validar fórmula y representación
# Trampa: Que el agregado cambie poco no significa que las mismas paradas
# queden cubiertas.
# ----------------------------------------------------------------------------
print("\n=== Paso 7 · Validar fórmula y representación ===")
print(pd.concat([resultados['formulas_comparadas'], resultados['representaciones_comparadas']], ignore_index=True))

# ----------------------------------------------------------------------------
# Paso 8 · Localizar zonas con menor cobertura
# Trampa: Asignar la comuna del local más cercano a la parada crea comunas
# falsas en los bordes.
# ----------------------------------------------------------------------------
print("\n=== Paso 8 · Localizar zonas con menor cobertura ===")
print(resultados['por_rejilla'].head(10))

# ----------------------------------------------------------------------------
# Paso 9 · Declarar lo que el dato no permite afirmar
# Trampa: Una parada cubierta espacialmente puede apuntar a un local cuyo
# horario no fue publicado.
# ----------------------------------------------------------------------------
print("\n=== Paso 9 · Declarar lo que el dato no permite afirmar ===")
print(resultados['limite_por_horario'])

