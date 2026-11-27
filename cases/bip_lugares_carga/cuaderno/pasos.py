"""P01 · P02/P04 · Consolidar, validar la identidad y normalizar cinco Excel

¿Cuántos lugares de carga de la tarjeta bip! hay, dónde están, y qué identifica a cada uno?

Generado por scripts/build_cuadernos.py desde cuaderno.py. No editar a mano.
La explicación de cada paso está en CUADERNO.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.bip_lugares_carga import solution as p01
from lab.excel import detect_header_row, read_all_sheets, sheet_names
from lab.geo import haversine_km, utm_to_latlon
from lab.textual import normalize_key

import pandas as pd

ORIGINAL = p01.ORIGINAL
ruta_metro = ORIGINAL / 'bip-metro.xlsx'
ESQUEMA = list(p01.ESQUEMA)


# ----------------------------------------------------------------------------
# Paso 1 · Mirar el archivo antes de leerlo
# Trampa: pd.read_excel(ruta) sin sheet_name lee solo la primera hoja y no
# avisa. Y las hojas no se llaman igual en los cinco archivos -Abiertos,
# Abierto, PCMA-, de modo que tampoco sirve pedirla por nombre.
# ----------------------------------------------------------------------------
print("\n=== Paso 1 · Mirar el archivo antes de leerlo ===")
print(
    {archivo.stem: sheet_names(archivo)
     for archivo in sorted(ORIGINAL.glob('bip-*.xlsx'))}
)

# ----------------------------------------------------------------------------
# Paso 2 · Encontrar la fila del encabezado
# Trampa: No sirve «la primera fila sin celdas vacías»: una fila de datos
# también lo cumple. Hay que exigir varias celdas de texto seguidas de filas
# con datos.
# ----------------------------------------------------------------------------
crudo = pd.read_excel(ruta_metro, sheet_name='Abiertos', header=None)
print("\n=== Paso 2 · Encontrar la fila del encabezado ===")
print(detect_header_row(crudo))

# ----------------------------------------------------------------------------
# Paso 3 · Leer las seis hojas con su encabezado
# ----------------------------------------------------------------------------
hojas = p01.cargar()
print("\n=== Paso 3 · Leer las seis hojas con su encabezado ===")
print(p01.informe_de_lectura(hojas))

# ----------------------------------------------------------------------------
# Paso 4 · Los esquemas no coinciden
# En Excel: =COINCIDIR(A1;$B$1:$B$10;0)
# Trampa: Una columna trae un espacio al final del nombre. Es invisible, y
# un renombrado por igualdad exacta falla sin error: la columna queda fuera
# del esquema.
# ----------------------------------------------------------------------------
print("\n=== Paso 4 · Los esquemas no coinciden ===")
print(p01.informe_de_esquemas(hojas))

# ----------------------------------------------------------------------------
# Paso 5 · Apilar los cinco al esquema común
# ----------------------------------------------------------------------------
consolidado = p01.consolidar(hojas)
print("\n=== Paso 5 · Apilar los cinco al esquema común ===")
print(consolidado[ESQUEMA])

# ----------------------------------------------------------------------------
# Paso 6 · El tipo de local no está en los datos
# Trampa: Es el error más fácil de no notar: la tabla queda completa,
# sumable y sin huecos, y ya no se puede responder «¿cuántos son de Metro?».
# ----------------------------------------------------------------------------
print("\n=== Paso 6 · El tipo de local no está en los datos ===")
print(consolidado.groupby('tipo_local').size().sort_values(ascending=False))

# ----------------------------------------------------------------------------
# Paso 7 · ¿La columna «código» es una clave?
# En Excel: =SUMAPRODUCTO((CONTAR.SI(A2:A1929;A2:A1929)>1)*1)
# Trampa: En el archivo de Metro el código es la línea (L1, L5), no el
# local: 143 estaciones con 7 códigos. Y tampoco sirve archivo + código.
# ----------------------------------------------------------------------------
print("\n=== Paso 7 · ¿La columna «código» es una clave? ===")
print(
    {'filas': len(consolidado),
     'distintos': consolidado['codigo'].nunique(),
     'repetidos': int(consolidado['codigo'].duplicated().sum())}
)

# ----------------------------------------------------------------------------
# Paso 8 · P02 · Buscar claves candidatas mínimas
# Trampa: Confundir unicidad observada con identidad. codigo + este puede
# ser única y cambiar cuando el publicador corrige una coordenada.
# ----------------------------------------------------------------------------
print("\n=== Paso 8 · P02 · Buscar claves candidatas mínimas ===")
print(p01.claves_candidatas(consolidado))

# ----------------------------------------------------------------------------
# Paso 9 · P02 · Declarar y comprobar una clave subrogada
# Trampa: El hash no vuelve estable una dirección de texto libre: si la
# fuente corrige la dirección, cambia el identificador.
# ----------------------------------------------------------------------------
print("\n=== Paso 9 · P02 · Declarar y comprobar una clave subrogada ===")
print(p01.informe_de_clave_subrogada(consolidado))

# ----------------------------------------------------------------------------
# Paso 10 · Normalizar antes de agrupar
# En Excel: =MAYUSC(ESPACIOS(B2))
# Trampa: Guardar las dos formas: la clave para agrupar y la etiqueta para
# mostrar. Con solo la clave, el informe dice NUNOA en vez de Ñuñoa.
# ----------------------------------------------------------------------------
print("\n=== Paso 10 · Normalizar antes de agrupar ===")
print(
    {'crudas': consolidado['entidad'].nunique(),
     'normalizadas': consolidado['entidad'].map(normalize_key).nunique()}
)

# ----------------------------------------------------------------------------
# Paso 11 · P04 · Auditar cada fusión de la normalización
# Trampa: Contar solamente cuántos valores desaparecieron no dice cuáles se
# fusionaron ni si la fusión era correcta.
# ----------------------------------------------------------------------------
print("\n=== Paso 11 · P04 · Auditar cada fusión de la normalización ===")
print(p01.auditoria_de_fusiones(consolidado))

# ----------------------------------------------------------------------------
# Paso 12 · P04 · Medir el aporte real de expandir abreviaturas
# Trampa: Que una transformación esté implementada no prueba que aporte
# algo: en esta descarga la expansión de abreviaturas fusiona cero valores.
# ----------------------------------------------------------------------------
print("\n=== Paso 12 · P04 · Medir el aporte real de expandir abreviaturas ===")
print(p01.aporte_de_las_abreviaturas(consolidado))

# ----------------------------------------------------------------------------
# Paso 13 · Contar por comuna
# En Excel: =CONTAR.SI.CONJUNTO($E$2:$E$1929;$N2;$M$2:$M$1929;O$1)
# Trampa: groupby descarta los nulos de la clave sin avisar, y el total deja
# de sumar las filas. Con dropna=False aparecen como grupo propio.
# ----------------------------------------------------------------------------
print("\n=== Paso 13 · Contar por comuna ===")
print(p01.por_comuna(consolidado))

# ----------------------------------------------------------------------------
# Paso 14 · Cuánto del campo «horario» existe
# En Excel: =CONTAR.SI(F2:F1929;"?*")/FILAS(F2:F1929)
# Trampa: Dos trampas en el mismo paso. Una: CONTARA y CONTAR.SI(...;"<>")
# cuentan como no vacía una celda con fórmula que devuelve cadena vacía, de
# modo que una columna traída por una consulta da 100 % estando vacía; "?*"
# exige al menos un carácter. Otra: el denominador es una decisión. 18,10 %
# y 18,06 % son la misma medición sobre dos poblaciones distintas, y hay que
# decir cuál se publica.
# ----------------------------------------------------------------------------
def cobertura(tabla):
    lleno = tabla['horario'].notna() & (
        tabla['horario'].astype('string').str.strip() != '')
    return round(float(lleno.mean() * 100), 2)
print("\n=== Paso 14 · Cuánto del campo «horario» existe ===")
print(
    {'todas las filas': cobertura(consolidado),
     'solo abiertas': cobertura(consolidado[consolidado['abierto']])}
)

# ----------------------------------------------------------------------------
# Paso 15 · Las dos coordenadas de cada fila
# En Excel: =FRECUENCIA(N2:N1929;P1:P6)
# Trampa: La media y los percentiles 50, 90 y 99 esconden el hallazgo: los
# tres caen en 61 m y parece un desvío único con tres atípicos. El
# histograma muestra dos grupos, que es la firma de dos datums distintos y
# no de un redondeo. Un resumen de cinco números no los distingue.
# ----------------------------------------------------------------------------
lat_utm, lon_utm = utm_to_latlon(
    consolidado['este'], consolidado['norte'], zona=19)
desvio_m = haversine_km(
    lat_utm, lon_utm,
    consolidado['latitud'], consolidado['longitud']) * 1000
print("\n=== Paso 15 · Las dos coordenadas de cada fila ===")
print(pd.cut(desvio_m, [0, 10, 50, 58, 62, 100, 1e9]).value_counts().sort_index())

# ----------------------------------------------------------------------------
# Paso 16 · Las filas donde las dos coordenadas se contradicen
# En Excel: =CONTAR.SI(N2:N1929;">200")
# Trampa: El umbral es una decisión y se escribe con su motivo. Elegirlo
# después de ver los datos, para que el número de hallazgos quede cómodo, es
# el resultado disfrazado de criterio.
# ----------------------------------------------------------------------------
print("\n=== Paso 16 · Las filas donde las dos coordenadas se contradicen ===")
print(
    p01.coordenadas_sospechosas(consolidado)[
        ['fuente', 'codigo', 'comuna', 'desvio_m']]
)

