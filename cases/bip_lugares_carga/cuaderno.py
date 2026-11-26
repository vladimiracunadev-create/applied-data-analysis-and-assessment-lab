"""Cuaderno de trabajo de P01: los pasos, en Pandas y en Excel.

Declara los pasos y el espacio de nombres sobre el que corren. Se genera con
`python scripts/build_cuadernos.py` y produce, junto a este archivo:

    CUADERNO.md              el documento, para leer
    cuaderno/pasos.py        el código seguido, para correr
    cuaderno/practica.xlsx   las fórmulas y el resultado que deben dar
    cuaderno/svg/            las figuras

Las fórmulas suponen el consolidado pegado con encabezado en la fila 1 y los datos en
las filas 2 a 1929, con las diez columnas del esquema en este orden:

    A codigo · B entidad · C nombre · D direccion · E comuna · F horario
    G este · H norte · I latitud · J longitud
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.bip_lugares_carga import solution as p01  # noqa: E402
from lab.cuaderno import Cuaderno, Paso  # noqa: E402
from lab.diagrama_svg import (  # noqa: E402
    ACENTO,
    AZUL,
    OCRE,
    TINTA,
    Etapa,
    Flujo,
    Mapa,
    Rama,
)
from lab.excel import detect_header_row, read_all_sheets, sheet_names  # noqa: E402
from lab.geo import haversine_km, utm_to_latlon  # noqa: E402
from lab.hoja_svg import Columna, Hoja  # noqa: E402
from lab.textual import normalize_key  # noqa: E402
from lab.viz import bar_chart, histogram  # noqa: E402

#: Última fila de datos en la hoja, para que las fórmulas se copien tal cual.
FIN = 1929

#: Columnas de la hoja donde se pega el consolidado, en su orden.
COLUMNAS = (
    "codigo", "entidad", "nombre", "direccion", "comuna", "horario",
    "este", "norte", "latitud", "longitud",
)


#: Las columnas del fragmento que se dibuja, con su ancho. Se declaran una vez para
#: que todos los pasos muestren la misma hoja y se reconozca de paso en paso.
COL_A = Columna("A", "codigo", 84)
COL_B = Columna("B", "entidad", 100)
COL_E = Columna("E", "comuna", 116)
COL_F = Columna("F", "horario", 150)
COL_I = Columna("I", "latitud", 92)
COL_J = Columna("J", "longitud", 96)


PROBLEMA = """
Para pagar un viaje en el transporte público de Santiago hay que llevar saldo en la
tarjeta bip!, y el saldo se carga en locales físicos. El organismo publica dónde están
esos locales, y lo publica como lo publica un organismo: **cinco archivos de Excel
distintos**, uno por tipo de local, hechos en momentos distintos por personas distintas.

La pregunta que llega es simple y legítima: *¿cuántos lugares de carga hay y dónde
están?* Alguien tiene que contestarla para decidir dónde instalar el próximo, o para
responder una consulta ciudadana, o para cruzarla con la red de transporte.

**Lo que la vuelve difícil no es el volumen.** Son 1 928 filas: cabrían en una pantalla
y media. Lo difícil es que los cinco archivos no se parecen entre sí:

- el **encabezado no está en la primera fila** de ninguno, y está en una distinta en
  cada uno, porque arriba hay un título y filas en blanco;
- los **esquemas no coinciden**: unos traen nueve columnas y otros diez, y el mismo
  campo se llama de dos formas;
- el **tipo de local no está en los datos**: está en el nombre del archivo;
- una hoja describe locales **fuera de servicio**, y si se lee todo junto quedan
  contados como abiertos;
- la columna que parece la clave **no identifica una fila**;
- y la misma ubicación viene **dos veces**, en dos sistemas de coordenadas que no
  coinciden.

Ninguno de esos seis problemas produce un error. Cada uno produce una tabla que se puede
sumar, graficar y presentar, con un número equivocado.

Ese es el trabajo real de quien gestiona datos que no generó: no calcular, sino
**descubrir en qué no se puede confiar antes de calcular**. Y es exactamente lo que se
pide en una evaluación técnica de cuatro horas con Excel y Pandas.
"""

SOLUCION = """
El recorrido va de lo que no se puede suponer a lo que sí se puede afirmar, en cinco
bloques.

**Leer lo que no está ordenado** (pasos 1 a 3). Antes de leer, mirar: cuántas hojas hay
y en qué fila empieza cada tabla. La fila del encabezado se **detecta** en lugar de
fijarse, y de cada lectura queda un informe de qué hubo que hacer. Ese informe es lo que
después permite defender el recuento.

**Armonizar lo que no coincide** (pasos 4 a 6). La correspondencia entre el nombre de
cada archivo y el campo del esquema común se **declara** en una tabla, no se adivina por
parecido: un acierto por casualidad hoy es un error mañana. Y al apilar se agrega el tipo
de local, que vive en el nombre del archivo y se perdería para siempre.

**Comprobar lo que se supone** (pasos 7 y 8). Dos suposiciones que todo el mundo hace y
nadie mide: que la columna llamada «código» es una clave, y que los textos que nombran lo
mismo están escritos igual. Las dos son falsas en este archivo, y medirlo cuesta una
línea cada una.

**Responder, y declarar el límite** (pasos 9 y 10). Recién aquí se cuenta por comuna. Y
se mide cuánto del campo de horario existe de verdad, porque de eso depende qué se puede
concluir después.

**Validar sin fuente externa** (pasos 11 y 12). El archivo trae la ubicación dos veces.
Convertir una y compararla con la otra es una validación que no necesita pedirle nada a
nadie, y es la que encuentra los tres errores de kilómetros que ninguna de las
comprobaciones anteriores podía ver.

Cada paso trae el Pandas, su salida real, y la fórmula de Excel dibujada en su hoja. Diez
de los doce traen además **la trampa**: lo que sale mal si el paso se hace de la forma
obvia, que es la parte que no está en ningún tutorial y la que se pregunta en una prueba.
"""

FLUJO = Flujo(
    titulo="El problema: cinco planillas que describen lo mismo y no se parecen",
    etapas=[
        Etapa("5 archivos .xlsx",
              ["Metro, Puntos, Retail,", "Centros estándar y alto", "6 hojas en total"],
              nota="1 928 filas", color=TINTA),
        Etapa("Leer",
              ["Encabezado en fila 7, 9,", "13, 10 y 9", "Una hoja de cerrados"],
              nota="y el informe de qué costó", color=AZUL),
        Etapa("Armonizar",
              ["9 y 10 columnas", "Un campo, dos nombres",
               "El tipo, en el nombre del archivo"],
              nota="esquema de 10 campos", color=AZUL),
        Etapa("Comprobar",
              ["El código no es clave", "Dos coordenadas por fila",
               "Horario en el 18 %"],
              nota="3 errores de hasta 10,3 km", color=OCRE),
        Etapa("Una tabla que se cuenta",
              ["46 comunas", "3 entidades", "5 tipos de local"],
              nota="y sus límites, escritos", color=ACENTO),
    ],
)

MAPA = Mapa(
    centro="P01 · Consolidar cinco Excel",
    subtitulo="12 pasos · 10 trampas",
    ramas=[
        Rama("Leer lo que no está ordenado",
             ["1 · Mirar las hojas antes de leer",
              "2 · Encontrar la fila del encabezado",
              "3 · Leer las seis con su informe"], color=AZUL),
        Rama("Armonizar lo que no coincide",
             ["4 · Los esquemas no coinciden",
              "5 · Apilar al esquema común",
              "6 · El tipo no está en los datos"], color=AZUL),
        Rama("Comprobar lo que se supone",
             ["7 · El código no es una clave",
              "8 · Normalizar antes de agrupar"], color=OCRE),
        Rama("Responder, y declarar el límite",
             ["9 · Contar por comuna",
              "10 · Cuánto del horario existe"], color=ACENTO),
        Rama("Validar sin fuente externa",
             ["11 · Las dos coordenadas de cada fila",
              "12 · Dónde se contradicen"], color=OCRE),
    ],
)

APRENDIZAJES = (
    "El encabezado de una planilla real **no está en la primera fila**, y la fila se "
    "detecta en lugar de fijarse: así el código sobrevive a la versión siguiente.",
    "Una correspondencia de columnas se **declara**. Deducirla por parecido acierta hoy "
    "y falla cuando cambie un nombre, sin avisar.",
    "Lo que no está en ninguna columna —aquí, el tipo de local— se pierde al apilar si "
    "no se agrega a propósito. Y la tabla resultante queda completa y sumable.",
    "Una columna llamada «código» **no es una clave hasta que se mide**, y en este "
    "archivo no lo es ni junto al nombre del archivo de origen.",
    "Normalizar es decidir qué cosas son la misma, y hay que guardar **las dos** formas: "
    "la clave para agrupar y la etiqueta para mostrar.",
    "El **denominador es una decisión**: la cobertura del horario es 18,10 % o 18,06 % "
    "según se cuenten todas las filas o solo las abiertas, y hay que decir cuál se "
    "publica.",
    "Un campo redundante —la misma ubicación dos veces— es una validación gratuita que "
    "no necesita ninguna fuente externa.",
    "Un resumen de cinco números **esconde la forma**: la media y los percentiles no "
    "distinguen dos sistemas de coordenadas de un error de redondeo. El histograma, sí.",
    "Un umbral se escribe con su motivo. Elegirlo después de ver los datos, para que el "
    "número de hallazgos quede cómodo, es el resultado disfrazado de criterio.",
    "Lo que corresponde con un error de datos ajenos es **reportarlo al publicador**, no "
    "corregirlo en silencio: no se sabe cuál de las dos versiones es la buena.",
)

RELACIONADOS = (
    ("Qué se encontró, con las cifras y los límites — README del caso", "README.md"),
    ("P08 · El cruce que no tiene clave, que usa esta tabla",
     "../cobertura_de_carga/README.md"),
    ("P10 · Lo que esta validación de coordenadas no puede ver",
     "../correspondencia_metro/README.md"),
    ("Equivalencias entre SQL, Pandas, Excel y R",
     "../../docs/equivalencias.md"),
    ("Mapa de los 16 problemas de la instancia",
     "../../docs/problemas-de-la-instancia.md"),
)


def construir() -> Cuaderno:
    """El cuaderno de P01."""
    contexto = {
        "p01": p01,
        "ORIGINAL": p01.ORIGINAL,
        "ruta_metro": p01.ORIGINAL / "bip-metro.xlsx",
        "sheet_names": sheet_names,
        "detect_header_row": detect_header_row,
        "read_all_sheets": read_all_sheets,
        "normalize_key": normalize_key,
        "utm_to_latlon": utm_to_latlon,
        "haversine_km": haversine_km,
        "bar_chart": bar_chart,
        "histogram": histogram,
        "ESQUEMA": list(p01.ESQUEMA),
        "pd": pd,
    }

    pasos = [
        Paso(
            titulo="Mirar el archivo antes de leerlo",
            objetivo=(
                "Cuántas hojas tiene cada archivo y cómo se llaman. Uno tiene dos, y la "
                "segunda son locales **fuera de servicio**."
            ),
            pandas=(
                "{archivo.stem: sheet_names(archivo)\n"
                " for archivo in sorted(ORIGINAL.glob('bip-*.xlsx'))}"
            ),
            excel="Abrir el archivo y mirar las pestañas. Aquí Excel gana.",
            trampa=(
                "`pd.read_excel(ruta)` sin `sheet_name` lee **solo la primera hoja** y no "
                "avisa. Y las hojas no se llaman igual en los cinco archivos "
                "—`Abiertos`, `Abierto`, `PCMA`—, de modo que tampoco sirve pedirla por "
                "nombre."
            ),
            mostrar="valor",
        ),
        Paso(
            titulo="Encontrar la fila del encabezado",
            objetivo=(
                "No está en la fila 1: está en la 7, 9, 13, 10 y 9, una por archivo. Con "
                "`header=0` las columnas salen como `Unnamed: 0`."
            ),
            pandas=(
                "crudo = pd.read_excel(ruta_metro, sheet_name='Abiertos', header=None)\n"
                "detect_header_row(crudo)"
            ),
            excel=(
                "**Datos ▸ Obtener datos ▸ Desde un libro**, y en Power Query "
                "**Quitar filas superiores** y **Usar la primera fila como encabezado**."
            ),
            trampa=(
                "No sirve «la primera fila sin celdas vacías»: una fila de datos también "
                "lo cumple. Hay que exigir varias celdas de **texto** seguidas de filas "
                "con datos."
            ),
            mostrar="valor",
        ),
        Paso(
            titulo="Leer las seis hojas con su encabezado",
            objetivo=(
                "El informe de lectura no es decorativo: es lo que permite afirmar "
                "después que el 1 928 no se inventó."
            ),
            pandas="hojas = p01.cargar()\np01.informe_de_lectura(hojas)",
            excel="Repetir el paso anterior cinco veces y **anotar** la fila de cada uno.",
            filas=7,
        ),
        Paso(
            titulo="Los esquemas no coinciden",
            objetivo=(
                "Nueve columnas en unos archivos y diez en otros, y el mismo campo con "
                "dos nombres: `NOMBRE FANTASIA` y `NOMBRE DE FANTASIA`."
            ),
            pandas="p01.informe_de_esquemas(hojas)",
            excel="`=COINCIDIR(A1;$B$1:$B$10;0)` da `#N/D` donde el campo no existe.",
            formula_excel="=COINCIDIR(A1;$B$1:$B$10;0)",
            hoja=Hoja(
                columnas=[
                    Columna("A", "campos archivo 1", 150),
                    Columna("B", "campos archivo 2", 150),
                    Columna("C", "¿existe en 2?", 118),
                ],
                filas=[
                    ["CODIGO", "CODIGO", "1"],
                    ["NOMBRE FANTASIA", "NOMBRE DE FANTASIA", "#N/D"],
                    ["HORARIO REFERENCIAL", "HORARIO", "#N/D"],
                ],
                primera_fila=1,
                celda="C1",
                formula="=COINCIDIR(A1;$B$1:$B$10;0)",
                resultado="1",
                nota="#N/D marca el campo que el otro archivo llama de otra forma.",
            ),
            trampa=(
                "Una columna trae un **espacio al final del nombre**. Es invisible, y un "
                "renombrado por igualdad exacta falla sin error: la columna queda fuera "
                "del esquema."
            ),
            filas=7,
        ),
        Paso(
            titulo="Apilar los cinco al esquema común",
            objetivo=(
                "La correspondencia está **declarada** en el diccionario `ALIAS`, no "
                "deducida por parecido."
            ),
            pandas="consolidado = p01.consolidar(hojas)\nconsolidado[ESQUEMA]",
            excel=(
                "**Datos ▸ Obtener datos ▸ Combinar consultas ▸ Anexar**. Copiar y pegar "
                "funciona una vez y no se repite cuando el portal publique otra versión."
            ),
            filas=5,
        ),
        Paso(
            titulo="El tipo de local no está en los datos",
            objetivo=(
                "Está en el **nombre del archivo**. Si no se agrega al apilar, se pierde."
            ),
            pandas="consolidado.groupby('tipo_local').size().sort_values(ascending=False)",
            excel=(
                "En Power Query, una **columna personalizada** por consulta antes de "
                "anexar: `= \"Estación de Metro\"`."
            ),
            trampa=(
                "Es el error más fácil de no notar: la tabla queda completa, sumable y "
                "sin huecos, y ya no se puede responder «¿cuántos son de Metro?»."
            ),
            mostrar="serie",
            figura=(
                "bar_chart(\n"
                "    consolidado.groupby('tipo_local').size().rename('locales')\n"
                "       .reset_index(),\n"
                "    category='tipo_local', value='locales', path=SVG_DESTINO,\n"
                "    title='Lugares de carga por tipo de local',\n"
                "    ylabel='locales', xlabel='',\n"
                "    source='Datos abiertos MTT · bip!, CC BY-NC 2.0')"
            ),
            pie_figura=(
                "Los puntos bip! son el 82 % del archivo, y son también los que no "
                "declaran horario."
            ),
        ),
        Paso(
            titulo="¿La columna «código» es una clave?",
            objetivo="Medirlo cuesta una línea, y hay que hacerlo antes de cruzar.",
            pandas=(
                "{'filas': len(consolidado),\n"
                " 'distintos': consolidado['codigo'].nunique(),\n"
                " 'repetidos': int(consolidado['codigo'].duplicated().sum())}"
            ),
            excel=(
                f"`=CONTAR.SI($A$2:$A${FIN};A2)>1` y arrastrar. Distintos: "
                f"`=CONTARA(UNICOS(A2:A{FIN}))`."
            ),
            formula_excel=f"=SUMAPRODUCTO((CONTAR.SI(A2:A{FIN};A2:A{FIN})>1)*1)",
            esperado="136 filas con código repetido, de 1 928",
            hoja=Hoja(
                columnas=[COL_A, COL_B, COL_E, Columna("K", "repetido?", 124)],
                filas=[
                    ["L1", "METRO", "LO PRADO", "VERDADERO"],
                    ["L1", "METRO", "LO PRADO", ""],
                    ["9878", "FULLCARGA", "HUECHURABA", ""],
                ],
                celda="K2",
                formula="=CONTAR.SI($A$2:$A$1929;A2)>1",
                resultado="VERDADERO",
                nota="Las dos primeras filas son estaciones distintas con el mismo código.",
            ),
            trampa=(
                "En el archivo de Metro el código es la **línea** (`L1`, `L5`), no el "
                "local: 143 estaciones con 7 códigos. Y tampoco sirve `archivo + código`."
            ),
            mostrar="valor",
        ),
        Paso(
            titulo="Normalizar antes de agrupar",
            objetivo=(
                "`FULLCARGA` y `Fullcarga` son dos grupos para `groupby` y uno para una "
                "persona."
            ),
            pandas=(
                "{'crudas': consolidado['entidad'].nunique(),\n"
                " 'normalizadas': consolidado['entidad'].map(normalize_key).nunique()}"
            ),
            excel=(
                "`=MAYUSC(ESPACIOS(B2))` cubre mayúsculas y espacios. Las tildes, con "
                "`SUSTITUIR` anidado una por vocal."
            ),
            formula_excel="=MAYUSC(ESPACIOS(B2))",
            esperado="4 valores crudos, 3 normalizados",
            hoja=Hoja(
                columnas=[COL_B, Columna("L", "normalizada", 134)],
                filas=[
                    ["Fullcarga", "FULLCARGA"],
                    ["FULLCARGA", ""],
                    ["METRO", ""],
                ],
                celda="L2",
                formula="=MAYUSC(ESPACIOS(B2))",
                resultado="FULLCARGA",
                nota="Dos formas crudas, un solo grupo. Sin esto, groupby cuenta dos.",
            ),
            trampa=(
                "Guardar **las dos** formas: la clave para agrupar y la etiqueta para "
                "mostrar. Con solo la clave, el informe dice `NUNOA` en vez de `Ñuñoa`."
            ),
            mostrar="valor",
        ),
        Paso(
            titulo="Contar por comuna",
            objetivo="La pregunta que se pedía, con el desglose por tipo de local.",
            pandas="p01.por_comuna(consolidado)",
            excel=(
                "**Insertar ▸ Tabla dinámica**: `comuna` en Filas, `tipo_local` en "
                "Columnas, `codigo` en Valores con **Contar**."
            ),
            formula_excel=f"=CONTAR.SI.CONJUNTO($E$2:$E${FIN};$N2;$M$2:$M${FIN};O$1)",
            hoja=Hoja(
                columnas=[
                    Columna("N", "comuna", 120),
                    Columna("O", "Punto bip!", 104),
                    Columna("P", "Retail", 86),
                    Columna("Q", "Metro", 84),
                ],
                filas=[
                    ["MAIPU", "131", "19", "5"],
                    ["SANTIAGO", "", "", ""],
                    ["LAS CONDES", "", "", ""],
                ],
                primera_fila=2,
                celda="O2",
                formula="=CONTAR.SI.CONJUNTO($E$2:$E$1929;$N2;$M$2:$M$1929;O$1)",
                resultado="131",
                nota="El tipo de local va en la fila 1; la comuna, en la columna N.",
            ),
            esperado="Maipú 157, Santiago 148, Las Condes 104",
            trampa=(
                "`groupby` **descarta los nulos de la clave** sin avisar, y el total deja "
                "de sumar las filas. Con `dropna=False` aparecen como grupo propio."
            ),
            filas=8,
        ),
        Paso(
            titulo="Cuánto del campo «horario» existe",
            objetivo=(
                "Antes de usar un campo, saber cuánto está lleno. Y declarar **sobre "
                "qué**: la cobertura cambia según se cuenten las 1 928 filas o las "
                "1 927 abiertas."
            ),
            pandas=(
                "def cobertura(tabla):\n"
                "    lleno = tabla['horario'].notna() & (\n"
                "        tabla['horario'].astype('string').str.strip() != '')\n"
                "    return round(float(lleno.mean() * 100), 2)\n"
                "\n"
                "{'todas las filas': cobertura(consolidado),\n"
                " 'solo abiertas': cobertura(consolidado[consolidado['abierto']])}"
            ),
            excel=f"`=CONTAR.SI(F2:F{FIN};\"?*\")/FILAS(F2:F{FIN})`, en formato porcentaje.",
            formula_excel=f'=CONTAR.SI(F2:F{FIN};"?*")/FILAS(F2:F{FIN})',
            esperado="18,10 % sobre las 1 928 filas · 18,06 % sobre las 1 927 abiertas",
            hoja=Hoja(
                columnas=[COL_A, COL_F, Columna("M", "cobertura", 130)],
                filas=[
                    ["L1", "Lunes a Viernes: 6:00 a…", "18,10 %"],
                    ["9878", "", ""],
                    ["1224", "", ""],
                ],
                celda="M2",
                formula='=CONTAR.SI(F2:F1929;"?*")/FILAS(F2:F1929)',
                resultado="18,10 %",
                nota='Con "<>" en vez de "?*" daría 100 % si la columna viene de una consulta.',
            ),
            trampa=(
                "Dos trampas en el mismo paso. Una: `CONTARA` y "
                "`CONTAR.SI(...;\"<>\")` cuentan como no vacía una celda con **fórmula "
                "que devuelve cadena vacía**, de modo que una columna traída por una "
                "consulta da 100 % estando vacía; `\"?*\"` exige al menos un carácter. "
                "Otra: el **denominador es una decisión**. 18,10 % y 18,06 % son la "
                "misma medición sobre dos poblaciones distintas, y hay que decir cuál "
                "se publica."
            ),
            mostrar="valor",
        ),
        Paso(
            titulo="Las dos coordenadas de cada fila",
            objetivo=(
                "El archivo trae la misma ubicación en UTM y en grados. Convertir una y "
                "comparar con la otra es una validación que no necesita fuente externa."
            ),
            pandas=(
                "lat_utm, lon_utm = utm_to_latlon(\n"
                "    consolidado['este'], consolidado['norte'], zona=19)\n"
                "desvio_m = haversine_km(\n"
                "    lat_utm, lon_utm,\n"
                "    consolidado['latitud'], consolidado['longitud']) * 1000\n"
                "pd.cut(desvio_m, [0, 10, 50, 58, 62, 100, 1e9]).value_counts().sort_index()"
            ),
            excel=(
                "La conversión de UTM a grados no se hace en Excel: es una serie de ocho "
                "términos. La distancia entre dos pares de grados, sí:\n\n"
                "```\n=2*6371000*ASENO(RAIZ(SENO((RADIANES(I2)-RADIANES(L2))/2)^2\n"
                "  + COS(RADIANES(L2))*COS(RADIANES(I2))\n"
                "  * SENO((RADIANES(J2)-RADIANES(M2))/2)^2))\n```\n\n"
                f"Y el histograma: topes en `P1:P6`, y `=FRECUENCIA(N2:N{FIN};P1:P6)` "
                "seleccionando `Q1:Q7`."
            ),
            formula_excel=f"=FRECUENCIA(N2:N{FIN};P1:P6)",
            esperado="109 filas bajo 10 m y 1 768 entre 58 y 62 m",
            hoja=Hoja(
                columnas=[
                    COL_I, COL_J,
                    Columna("L", "lat. desde UTM", 112),
                    Columna("M", "lon. desde UTM", 114),
                    Columna("N", "desvío (m)", 100),
                ],
                filas=[
                    ["-33,444355", "-70,723068", "-33,443805", "-70,723130", "61,2"],
                    ["-33,451453", "-70,723086", "-33,450903", "-70,723148", ""],
                    ["-33,457279", "-70,714218", "-33,456729", "-70,714280", ""],
                ],
                celda="N2",
                formula=(
                    "=2*6371000*ASENO(RAIZ(SENO((RADIANES(I2)-RADIANES(L2))/2)^2"
                    "+COS(RADIANES(L2))*COS(RADIANES(I2))"
                    "*SENO((RADIANES(J2)-RADIANES(M2))/2)^2))"
                ),
                resultado="61,2",
                nota="Las columnas L y M vienen de convertir el UTM, que no se hace en Excel.",
            ),
            trampa=(
                "La media y los percentiles 50, 90 y 99 **esconden el hallazgo**: los tres "
                "caen en 61 m y parece un desvío único con tres atípicos. El histograma "
                "muestra **dos grupos**, que es la firma de dos datums distintos y no de "
                "un redondeo. Un resumen de cinco números no los distingue."
            ),
            mostrar="serie",
            filas=10,
            figura=(
                "histogram(\n"
                "    desvio_m[desvio_m < 100], path=SVG_DESTINO,\n"
                "    title='Desvío entre las dos coordenadas del mismo archivo',\n"
                "    xlabel='metros', bins=40,\n"
                "    source='Datos abiertos MTT · bip!, CC BY-NC 2.0')"
            ),
            pie_figura=(
                "Dos grupos: uno en 0 m y otro en 61 m. Se recortan los mayores de 100 m "
                "—tres filas— para que la forma se vea; esos tres son el paso siguiente."
            ),
        ),
        Paso(
            titulo="Las filas donde las dos coordenadas se contradicen",
            objetivo=(
                "Con el desvío calculado, un umbral declarado separa el desplazamiento "
                "sistemático de los errores reales."
            ),
            pandas=(
                "p01.coordenadas_sospechosas(consolidado)[\n"
                "    ['fuente', 'codigo', 'comuna', 'desvio_m']]"
            ),
            excel="Con el desvío en N: `=SI(N2>200;\"revisar\";\"\")` y autofiltro.",
            formula_excel=f'=CONTAR.SI(N2:N{FIN};">200")',
            esperado="3 filas, con desvíos de 893 m a 10,3 km",
            hoja=Hoja(
                columnas=[
                    COL_A, COL_E,
                    Columna("N", "desvío (m)", 100),
                    Columna("O", "¿revisar?", 110),
                ],
                filas=[
                    ["123375", "MACUL", "10.271,6", "revisar"],
                    ["9878", "HUECHURABA", "10.087,0", ""],
                    ["L1", "LO PRADO", "61,2", ""],
                ],
                celda="O2",
                formula='=SI(N2>200;"revisar";"")',
                resultado="revisar",
                nota="El umbral de 200 m es una decisión declarada, no un resultado.",
            ),
            trampa=(
                "El umbral es una **decisión** y se escribe con su motivo. Elegirlo "
                "después de ver los datos, para que el número de hallazgos quede cómodo, "
                "es el resultado disfrazado de criterio."
            ),
            filas=5,
        ),
    ]

    return Cuaderno(
        caso="P01",
        titulo="Consolidar cinco Excel públicos que describen lo mismo y no se parecen",
        pregunta=(
            "¿Cuántos lugares de carga de la tarjeta bip! hay, dónde están, y qué "
            "identifica a cada uno?"
        ),
        datos=(
            "Cinco `.xlsx` del portal de datos abiertos del MTT, licencia CC BY-NC 2.0 "
            "verificada. Seis hojas, 1 928 filas, una en la hoja de cerrados."
        ),
        pasos=pasos,
        contexto=contexto,
        importes=(
            "from cases.bip_lugares_carga import solution as p01\n"
            "from lab.excel import detect_header_row, read_all_sheets, sheet_names\n"
            "from lab.geo import haversine_km, utm_to_latlon\n"
            "from lab.textual import normalize_key\n"
            "\n"
            "import pandas as pd\n"
            "\n"
            "ORIGINAL = p01.ORIGINAL\n"
            "ruta_metro = ORIGINAL / 'bip-metro.xlsx'\n"
            "ESQUEMA = list(p01.ESQUEMA)"
        ),
        columnas_excel=COLUMNAS,
        problema=PROBLEMA,
        solucion=SOLUCION,
        flujo=FLUJO,
        mapa=MAPA,
        aprendizajes=APRENDIZAJES,
        relacionados=RELACIONADOS,
        siguiente=("P08 · El cruce que no tiene clave",
                   "../cobertura_de_carga/README.md"),
        cierre=(
            "1 928 filas, 1 927 abiertas, 46 comunas, 3 entidades. El `codigo` no "
            "identifica una fila, ni junto al archivo de origen. La validación cruzada de "
            "las dos coordenadas encontró 3 errores de hasta 10,3 km y un desplazamiento "
            "sistemático de 61 m con distribución bimodal.\n\n"
            "**No** se puede concluir cuánta gente usa cada local —no hay transacciones— "
            "ni si está abierto cuando alguien llega —el horario está en el 18,06 % de "
            "las filas—."
        ),
        reproducir=(
            "python scripts/fetch_data.py bip-metro bip-puntos bip-centros-alto-estandar bip-centros-estandar bip-retail\n"
            "python -m cases.bip_lugares_carga.solution\n"
            "python cases/bip_lugares_carga/cuaderno/pasos.py"
        ),
    )
