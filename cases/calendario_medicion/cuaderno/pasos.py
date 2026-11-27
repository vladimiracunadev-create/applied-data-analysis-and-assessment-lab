"""P11 · Calendario de medición de un indicador oficial

¿Qué días de 2026 entran en la medición según las reglas oficiales?

Generado por scripts/build_cuadernos.py desde cuaderno.py. No editar a mano.
La explicación de cada paso está en CUADERNO.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.calendario_medicion import solution as p11


# ----------------------------------------------------------------------------
# Paso 1 · Validar la fuente de feriados
# Trampa: Un CSV descargado no se vuelve verdadero por estar bien formado.
# ----------------------------------------------------------------------------
resultados = p11.analizar(2026)
print("\n=== Paso 1 · Validar la fuente de feriados ===")
print(resultados['validacion_feriados'])

# ----------------------------------------------------------------------------
# Paso 2 · Declarar las ocho reglas antes de calcular
# Trampa: Sumar los excluidos por regla cuenta 55 días más de una vez.
# ----------------------------------------------------------------------------
print("\n=== Paso 2 · Declarar las ocho reglas antes de calcular ===")
print(resultados['exclusion_por_regla'][['regla','excluye','exclusiva','solapada','aporte_pct']])

# ----------------------------------------------------------------------------
# Paso 3 · Construir el calendario diario
# En Excel: =SECUENCIA(365;1;FECHA(2026;1;1);1)
# Trampa: Trabajar solo con totales impide explicar un día particular.
# ----------------------------------------------------------------------------
print("\n=== Paso 3 · Construir el calendario diario ===")
print(resultados['resumen_calendario'])

# ----------------------------------------------------------------------------
# Paso 4 · Medir solapamientos y redundancias
# Trampa: Que una regla sea redundante en un año no demuestra que sea
# innecesaria siempre.
# ----------------------------------------------------------------------------
print("\n=== Paso 4 · Medir solapamientos y redundancias ===")
print(resultados['reglas_redundantes'])

# ----------------------------------------------------------------------------
# Paso 5 · Cruzar con los meses efectivos de medición
# En Excel: =Y(C2;ESNUMERO(COINCIDIR(MES(A2);{3;6;9;11};0)))
# Trampa: Publicar 164 días elegibles responde otra pregunta; solo 78 están
# en meses de medición.
# ----------------------------------------------------------------------------
print("\n=== Paso 5 · Cruzar con los meses efectivos de medición ===")
print(resultados['resumen_medicion'])

# ----------------------------------------------------------------------------
# Paso 6 · Cuantificar el aporte al denominador final
# Trampa: Meses completos excluye 90 días del año y cero días del
# denominador medido.
# ----------------------------------------------------------------------------
print("\n=== Paso 6 · Cuantificar el aporte al denominador final ===")
print(resultados['aporte_sobre_medibles'])

# ----------------------------------------------------------------------------
# Paso 7 · Distinguir redundancia estructural de accidental
# Trampa: Feriados no afecta en 2026, pero sí elimina entre uno y tres días
# en otros años.
# ----------------------------------------------------------------------------
print("\n=== Paso 7 · Distinguir redundancia estructural de accidental ===")
print(resultados['clasificacion_reglas'])

# ----------------------------------------------------------------------------
# Paso 8 · Medir el supuesto de vacaciones de invierno
# Trampa: Mover el supuesto a junio reduce el denominador hasta seis días;
# no es un detalle narrativo.
# ----------------------------------------------------------------------------
print("\n=== Paso 8 · Medir el supuesto de vacaciones de invierno ===")
print(resultados['sensibilidad_invierno'])

