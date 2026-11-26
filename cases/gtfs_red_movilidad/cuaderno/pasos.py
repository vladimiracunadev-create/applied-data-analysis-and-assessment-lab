"""P06 · Contar expediciones en un horario donde el 77,5 % de las horas no son horas

¿Cuántas expediciones de transporte público salen por hora en un día laboral, y cómo se reparten entre buses, Metro y trenes?

Generado por scripts/build_cuadernos.py desde cuaderno.py. No editar a mano.
La explicación de cada paso está en CUADERNO.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.gtfs_red_movilidad import solution as p06
from lab.dates import parse_hms_seconds, service_day_hour
from lab.sources import zip_members

import pandas as pd

FEED = p06.FEED


# ----------------------------------------------------------------------------
# Paso 1 · Mirar el ZIP antes de abrirlo
# Trampa: Es el único caso del laboratorio donde Excel no alcanza. Y el
# límite no avisa bien: al abrir un CSV más largo, Excel carga el millón de
# filas que caben y descarta el resto sin error.
# ----------------------------------------------------------------------------
print("\n=== Paso 1 · Mirar el ZIP antes de abrirlo ===")
print(zip_members(FEED))

# ----------------------------------------------------------------------------
# Paso 2 · Leer del flujo comprimido, sin descomprimir
# ----------------------------------------------------------------------------
tablas = p06.cargar()
print("\n=== Paso 2 · Leer del flujo comprimido, sin descomprimir ===")
print({nombre: tabla.shape for nombre, tabla in tablas.items()})

# ----------------------------------------------------------------------------
# Paso 3 · Cuatro columnas de ocho, y todas como texto
# Trampa: Dejar que pandas infiera los tipos convierte las horas a algo
# antes de que las validemos, y las de 24:00 o más se vuelven nulas o texto
# según la fila. El diagnóstico del paso siguiente ya no se podría hacer.
# ----------------------------------------------------------------------------
horarios = tablas['stop_times']
print("\n=== Paso 3 · Cuatro columnas de ocho, y todas como texto ===")
print(
    {'filas': len(horarios), 'columnas': list(horarios.columns),
     'memoria_MB': round(horarios.memory_usage(deep=True).sum() / 1e6, 1)}
)

# ----------------------------------------------------------------------------
# Paso 4 · El 77,5 % de las «horas» no son horas
# En Excel: =CONTAR.SI($A$2:$A$14521;A2)>0
# Trampa: Agrupar arrival_time por su hora sin esta comprobación da 635 574
# llegadas a medianoche y un gráfico con un pico absurdo a las 00:00. El
# pico es el 0:00:00 de cada primera parada de cada expedición de
# frecuencia.
# ----------------------------------------------------------------------------
print("\n=== Paso 4 · El 77,5 % de las «horas» no son horas ===")
print(p06.diagnosticar_horas(tablas))

# ----------------------------------------------------------------------------
# Paso 5 · El relleno de ceros miente al ordenar
# Trampa: No produce un error: produce la primera parada de cada expedición
# ordenada al final, de modo que el origen y el destino quedan cambiados. Un
# informe de tiempos de viaje con el signo invertido.
# ----------------------------------------------------------------------------
print("\n=== Paso 5 · El relleno de ceros miente al ordenar ===")
print('0:00:00' > '00:00:51')

# ----------------------------------------------------------------------------
# Paso 6 · Convertir a segundos, admitiendo horas de 24:00 y más
# En Excel: =RESIDUO(ENTERO(E2/3600);24)
# Trampa: pd.to_datetime('25:10:00') falla, y con errors='coerce' devuelve
# nulo en silencio. Las horas del servicio nocturno desaparecerían del
# conteo sin que nada avise.
# ----------------------------------------------------------------------------
ejemplos = pd.Series(['0:00:00', '00:00:51', '25:10:00', '28:00:00'])
print("\n=== Paso 6 · Convertir a segundos, admitiendo horas de 24:00 y más ===")
print(
    pd.DataFrame({'texto': ejemplos,
                  'segundos': parse_hms_seconds(ejemplos),
                  'hora_de_reloj': service_day_hour(parse_hms_seconds(ejemplos))})
)

# ----------------------------------------------------------------------------
# Paso 7 · Una ventana de frecuencia son muchas salidas
# En Excel: =ENTERO((C2-B2)*86400/D2)
# ----------------------------------------------------------------------------
expandido = p06.expandir_frecuencias(tablas)
print("\n=== Paso 7 · Una ventana de frecuencia son muchas salidas ===")
print(expandido.head(4))

# ----------------------------------------------------------------------------
# Paso 8 · El fin de la ventana es exclusivo
# En Excel: =SUMA(E2:E14521)
# Trampa: Es el error más fácil de defender y el más fácil de cometer:
# contar «de las 6 a las 7 cada 10 minutos» como siete salidas en lugar de
# seis. Infla el total un 10,37 %, que es una magnitud que nadie cuestiona
# en un informe.
# ----------------------------------------------------------------------------
comparacion = p06.comparar_ingenuo_vs_correcto(tablas)
print("\n=== Paso 8 · El fin de la ventana es exclusivo ===")
print(comparacion)

# ----------------------------------------------------------------------------
# Paso 9 · Expediciones por hora del día
# En Excel: =CONTAR.SI($F$2:$F$14521;G2)
# ----------------------------------------------------------------------------
por_hora = p06.expediciones_por_hora(tablas)
print("\n=== Paso 9 · Expediciones por hora del día ===")
print(por_hora)

# ----------------------------------------------------------------------------
# Paso 10 · «El 32 % de las paradas no se usa»: el defecto que no existe
# En Excel: =CONTAR.SI(horarios!$D:$D;A2)=0
# Trampa: Reportar «el 32 % de las paradas está huérfano» cuesta
# credibilidad: 5 989 de esas filas no son paradas, son estaciones, accesos
# y nodos de pasillo, y la especificación las distingue con un campo. El
# feed es complejo, no sucio. Un informe de calidad que no mira la jerarquía
# del formato produce hallazgos que el publicador descarta en treinta
# segundos, y con ellos descarta el resto del informe.
# ----------------------------------------------------------------------------
print("\n=== Paso 10 · «El 32 % de las paradas no se usa»: el defecto que no existe ===")
print(p06.paradas_sin_uso(tablas))

