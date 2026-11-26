"""Cuaderno de trabajo de P01: los pasos, en Pandas y en Excel.

Declara los pasos y el espacio de nombres sobre el que corren. El documento se genera
con `python scripts/build_cuadernos.py` y queda en `CUADERNO.md`, junto a este archivo.

El rango de Excel que se usa en las fórmulas supone el consolidado pegado en una hoja
con encabezado en la fila 1 y los datos en las filas 2 a 1929, con las diez columnas del
esquema común en este orden:

    A codigo · B entidad · C nombre · D direccion · E comuna · F horario
    G este · H norte · I latitud · J longitud

Ese libro se obtiene con `python scripts/export_inputs.py` o copiando la salida de
`consolidar()`.
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
from lab.excel import detect_header_row, read_all_sheets, sheet_names  # noqa: E402
from lab.geo import haversine_km, utm_to_latlon  # noqa: E402
from lab.textual import normalize_key  # noqa: E402

#: Última fila de datos en la hoja de Excel, para que las fórmulas del cuaderno sean
#: copiables tal cual. 1 928 filas de datos más el encabezado.
ULTIMA_FILA = 1929


def construir() -> Cuaderno:
    """El cuaderno de P01, con los objetos que sus pasos necesitan."""
    # Se usan dos archivos como ejemplo: el de retail, que es el único con hoja de
    # cerrados, y el de Metro, cuyo encabezado está en la fila 7.
    ruta_retail = p01.ORIGINAL / "bip-retail.xlsx"
    ruta_metro = p01.ORIGINAL / "bip-metro.xlsx"
    contexto = {
        "p01": p01,
        "ruta_retail": ruta_retail,
        "ruta_metro": ruta_metro,
        "ORIGINAL": p01.ORIGINAL,
        "sheet_names": sheet_names,
        "detect_header_row": detect_header_row,
        "read_all_sheets": read_all_sheets,
        "normalize_key": normalize_key,
        "utm_to_latlon": utm_to_latlon,
        "haversine_km": haversine_km,
        "ESQUEMA": list(p01.ESQUEMA),
        "pd": pd,
    }

    pasos = [
        Paso(
            titulo="Mirar el archivo antes de leerlo",
            objetivo=(
                "Un `read_excel` directo sobre uno de estos archivos devuelve basura, y "
                "conviene saber por qué antes de que pase. Lo primero es cuántas hojas "
                "hay y cómo se llaman. En el archivo de retail hay **dos**, y la segunda "
                "describe locales fuera de servicio: si se leen juntas quedan contados "
                "como abiertos."
            ),
            pandas=(
                "{archivo.stem: sheet_names(archivo)\n"
                " for archivo in sorted(ORIGINAL.glob('bip-*.xlsx'))}"
            ),
            excel=(
                "Abrir el archivo y mirar las pestañas de abajo. Es el único paso del "
                "cuaderno donde Excel es mejor herramienta que Pandas: la estructura se "
                "ve de un vistazo."
            ),
            trampa=(
                "`pd.read_excel(ruta)` sin `sheet_name` lee **solo la primera hoja** y no "
                "avisa de que hay otras. En el archivo de retail eso descarta en silencio "
                "la hoja `Cerrados`; en otro archivo podría descartar la mitad de los "
                "datos. Con `sheet_name=None` devuelve un diccionario con todas.\n\n"
                "Y de paso: las hojas no se llaman igual en los cinco archivos "
                "—`Abiertos`, `Abierto`, `PCMA`—, de modo que tampoco sirve pedir una "
                "hoja por nombre."
            ),
            mostrar="valor",
        ),
        Paso(
            titulo="Encontrar en qué fila está el encabezado",
            objetivo=(
                "El encabezado de estos archivos no está en la fila 1: está en la 7, la "
                "9, la 13, la 10 y la 9, una distinta por archivo, porque arriba hay un "
                "título y filas vacías. Fijar `header=0` produce columnas llamadas "
                "`Unnamed: 0` y los nombres reales metidos como una fila de datos."
            ),
            pandas=(
                "crudo = pd.read_excel(ruta_metro, sheet_name='Abiertos', header=None)\n"
                "detect_header_row(crudo)"
            ),
            excel=(
                "Mirar la hoja y contar las filas. Para leer desde ahí: "
                "**Datos ▸ Obtener datos ▸ Desde un libro**, y en el editor de Power "
                "Query usar **Quitar filas superiores** y **Usar la primera fila como "
                "encabezado**."
            ),
            trampa=(
                "La detección no puede ser «la primera fila sin celdas vacías»: una fila "
                "de datos también la cumple. `detect_header_row` busca la primera fila "
                "con varias celdas de **texto** no vacías seguida de filas con datos, y "
                "la declara. Si el archivo cambia de maqueta, el valor cambia y el "
                "código no se toca."
            ),
            mostrar="valor",
        ),
        Paso(
            titulo="Leer las seis hojas con su encabezado",
            objetivo=(
                "`read_all_sheets` aplica la detección a cada hoja de cada archivo y "
                "devuelve, junto a la tabla, un informe de qué hubo que hacer para "
                "leerla. El informe no es decorativo: es lo que permite afirmar después "
                "que el 1 928 no se inventó."
            ),
            pandas=(
                "hojas = p01.cargar()\n"
                "p01.informe_de_lectura(hojas)"
            ),
            excel=(
                "Repetir el paso anterior cinco veces, una por archivo, y **anotar** la "
                "fila de encabezado de cada uno. Esa anotación es el equivalente manual "
                "de esta tabla, y es la que se pierde cuando alguien más abre el libro."
            ),
            filas=7,
        ),
        Paso(
            titulo="Comprobar que los esquemas no coinciden",
            objetivo=(
                "Los cinco archivos describen lo mismo con columnas distintas: unos traen "
                "nueve y otros diez, y el nombre del mismo campo cambia entre archivos "
                "—`NOMBRE FANTASIA` y `NOMBRE DE FANTASIA`—. Apilarlos sin armonizar "
                "produce una tabla con columnas duplicadas y medio llenas."
            ),
            pandas="p01.informe_de_esquemas(hojas)",
            excel=(
                "Pegar los encabezados de los cinco archivos en columnas contiguas y "
                "compararlos con `=COINCIDIR(A1;$B$1:$B$10;0)`: devuelve `#N/D` donde el "
                "campo no existe en el otro archivo."
            ),
            trampa=(
                "Una de las columnas trae un **espacio al final del nombre**. Es "
                "invisible en Excel y en la salida de Pandas, y hace que un renombrado "
                "por igualdad exacta falle sin error: la columna simplemente no se "
                "renombra y queda fuera del esquema común."
            ),
            filas=7,
        ),
        Paso(
            titulo="Apilar los cinco al esquema común",
            objetivo=(
                "La correspondencia entre el nombre de cada archivo y el campo del "
                "esquema está **declarada** en el diccionario `ALIAS`, no deducida por "
                "parecido. Un acierto por casualidad hoy es un error mañana."
            ),
            pandas=(
                "consolidado = p01.consolidar(hojas)\n"
                "consolidado[ESQUEMA]"
            ),
            excel=(
                "**Datos ▸ Obtener datos ▸ Combinar consultas ▸ Anexar**. A mano sería "
                "copiar y pegar cinco bloques, que funciona una vez y no se puede repetir "
                "cuando el portal publique la versión siguiente."
            ),
            # Sin `guardar_como`: la asignación del fragmento ya deja `consolidado` en
            # el espacio de nombres, con sus columnas derivadas. Guardar el resultado de
            # la última expresión lo reemplazaría por el subconjunto de diez columnas que
            # se muestra, y los pasos siguientes perderían `tipo_local`.
            filas=5,
        ),
        Paso(
            titulo="El tipo de local no está en los datos",
            objetivo=(
                "Ninguna columna dice si la fila es una estación de Metro, un punto bip! "
                "o un local de retail. Esa información está en el **nombre del archivo**, "
                "y si no se agrega al apilar se pierde para siempre."
            ),
            pandas="consolidado.groupby('tipo_local').size()",
            excel=(
                "Antes de anexar, agregar en cada consulta una **columna personalizada** "
                "con el tipo: en Power Query, `= \"Estación de Metro\"`. Copiando y "
                "pegando a mano, escribir el tipo en una columna nueva antes de pegar el "
                "bloque siguiente."
            ),
            trampa=(
                "Es el error más fácil de cometer y el más difícil de notar: la tabla "
                "consolidada queda completa, sumable y sin ningún hueco, y simplemente ya "
                "no se puede responder «¿cuántos son estaciones de Metro?»."
            ),
            mostrar="serie",
        ),
        Paso(
            titulo="¿La columna «código» es una clave?",
            objetivo=(
                "Se llama `codigo`, es la primera columna y parece un identificador. "
                "Medirlo cuesta una línea, y conviene hacerlo **antes** de cruzar con "
                "cualquier otra cosa."
            ),
            pandas=(
                "len(consolidado), consolidado['codigo'].nunique(), "
                "int(consolidado['codigo'].duplicated().sum())"
            ),
            excel=(
                "En una columna libre, `=CONTAR.SI($A$2:$A$" + str(ULTIMA_FILA)
                + ";A2)>1` y arrastrar. Cuenta de `VERDADERO` con "
                "`=CONTAR.SI(K2:K" + str(ULTIMA_FILA) + ";VERDADERO)`. "
                "Valores distintos: `=CONTARA(UNICOS(A2:A" + str(ULTIMA_FILA) + "))`."
            ),
            trampa=(
                "En el archivo de Metro el código es la **línea** (`L1`, `L5`), no el "
                "local: 143 estaciones con 7 códigos. Y tampoco sirve la clave compuesta "
                "con el archivo de origen, que es la salida que uno probaría después."
            ),
            mostrar="valor",
        ),
        Paso(
            titulo="Normalizar antes de agrupar",
            objetivo=(
                "`FULLCARGA` y `Fullcarga` son dos grupos para `groupby` y uno para una "
                "persona. Normalizar es quitar tildes, pasar a mayúsculas y colapsar "
                "espacios, con **la misma regla** en las dos tablas que se vayan a cruzar."
            ),
            pandas=(
                "crudas = consolidado['entidad'].nunique()\n"
                "normalizadas = consolidado['entidad'].map(normalize_key).nunique()\n"
                "{'crudas': crudas, 'normalizadas': normalizadas}"
            ),
            excel=(
                "`=MAYUSC(ESPACIOS(B2))` cubre mayúsculas y espacios. Las tildes hay que "
                "quitarlas a mano con `SUSTITUIR` anidado: "
                "`=SUSTITUIR(SUSTITUIR(MAYUSC(ESPACIOS(B2));\"Á\";\"A\");\"É\";\"E\")`, "
                "y así con cada vocal. Es feo, y es el motivo por el que esta parte se "
                "hace en Pandas."
            ),
            trampa=(
                "Hay que guardar **las dos** formas: la clave para agrupar y la etiqueta "
                "para mostrar. Quedarse solo con la clave convierte `Ñuñoa` en `NUNOA` en "
                "el informe final, que es un empobrecimiento gratuito."
            ),
            mostrar="valor",
        ),
        Paso(
            titulo="Contar por comuna",
            objetivo=(
                "La pregunta que se pedía: cuántos lugares de carga hay por comuna, con "
                "el desglose por tipo de local. Se agrupa por la **clave** normalizada y "
                "se muestra la **etiqueta** legible."
            ),
            pandas="p01.por_comuna(consolidado)",
            excel=(
                "**Insertar ▸ Tabla dinámica**: `comuna` en Filas, `tipo_local` en "
                "Columnas, `codigo` en Valores con **Contar**. Sin dinámica: "
                "`=CONTAR.SI.CONJUNTO($E$2:$E$" + str(ULTIMA_FILA) + ";$N2;"
                "$M$2:$M$" + str(ULTIMA_FILA) + ";O$1)`, con la comuna en la columna N y "
                "el tipo en la fila 1."
            ),
            trampa=(
                "`groupby` **descarta los nulos de la clave** sin avisar. Si una fila no "
                "trae comuna, desaparece del cuadro y el total deja de sumar el número de "
                "filas. Con `dropna=False` aparece como grupo propio, que es lo que hay "
                "que informar."
            ),
            filas=8,
        ),
        Paso(
            titulo="Cuánto del campo «horario» existe de verdad",
            objetivo=(
                "Antes de usar un campo hay que saber cuánto está lleno. Este está "
                "presente en menos de la quinta parte de las filas, lo que limita "
                "cualquier conclusión que dependa de él."
            ),
            pandas=(
                "con_dato = consolidado['horario'].notna() & "
                "(consolidado['horario'].astype('string').str.strip() != '')\n"
                "round(float(con_dato.mean() * 100), 2)"
            ),
            excel=(
                "`=CONTARA(F2:F" + str(ULTIMA_FILA) + ")/FILAS(F2:F" + str(ULTIMA_FILA)
                + ")`, con la celda en formato porcentaje."
            ),
            trampa=(
                "`CONTARA` cuenta como no vacía una celda con una **fórmula que devuelve "
                "cadena vacía**. Si la columna viene de una consulta, el resultado es "
                "100 % de cobertura sobre un campo vacío. `CONTAR.SI(F2:F"
                + str(ULTIMA_FILA) + ";\"<>\")` tiene el mismo problema; la forma "
                "fiable es `CONTAR.SI(F2:F" + str(ULTIMA_FILA) + ";\"?*\")`, que exige "
                "al menos un carácter."
            ),
            mostrar="valor",
        ),
        Paso(
            titulo="Las dos coordenadas de cada fila, y cuál no cuadra",
            objetivo=(
                "Los archivos traen la **misma ubicación dos veces**: en UTM "
                "(`este`/`norte`) y en grados (`latitud`/`longitud`). Convertir una y "
                "compararla con la otra es una validación que no necesita ninguna fuente "
                "externa, y es la que encontró tres errores de hasta 10,3 km."
            ),
            pandas=(
                "lat_utm, lon_utm = utm_to_latlon(consolidado['este'], consolidado['norte'], zona=19)\n"
                "desvio_m = haversine_km(lat_utm, lon_utm, consolidado['latitud'], consolidado['longitud']) * 1000\n"
                "pd.cut(desvio_m, [0, 10, 50, 58, 62, 100, 1e9]).value_counts().sort_index()"
            ),
            excel=(
                "La conversión de UTM a grados **no se hace en Excel** de forma "
                "razonable: es una serie de ocho términos. Lo que sí se hace es la "
                "distancia entre dos pares de grados, con haversine en una celda:\n\n"
                "```\n=2*6371000*ASENO(RAIZ(SENO((RADIANES(I2)-RADIANES(L2))/2)^2\n"
                "  + COS(RADIANES(L2))*COS(RADIANES(I2))\n"
                "  * SENO((RADIANES(J2)-RADIANES(M2))/2)^2))\n```\n\n"
                "con la coordenada publicada en I y J, y la convertida en L y M.\n\n"
                "Y el histograma, que es lo que revela la forma: poner los topes de los "
                "tramos en `P1:P6` y seleccionar `Q1:Q7` para "
                "`=FRECUENCIA(N2:N" + str(ULTIMA_FILA) + ";P1:P6)`. Devuelve un "
                "tramo más que topes, porque el último recoge todo lo que los supera."
            ),
            trampa=(
                "Mirar la media, o incluso los percentiles 50, 90 y 99, **esconde el "
                "hallazgo**: los tres caen en 61 m y la distribución parece un desvío "
                "único con tres atípicos. El histograma muestra otra cosa: **109 filas "
                "en torno a 0 m y 1 768 en torno a 61 m**, dos grupos nítidos.\n\n"
                "Esa bimodalidad es la firma de **dos datums distintos** —parte del "
                "archivo con un sistema de referencia y parte con otro— y no de un error "
                "de redondeo, que daría una sola campana. Un resumen de cinco números no "
                "distingue una cosa de la otra: hay que mirar la forma.\n\n"
                "Y lo que corresponde con un hallazgo así es reportarlo al publicador, no "
                "corregirlo en silencio: no se sabe cuál de las dos representaciones es "
                "la buena."
            ),
            mostrar="serie",
            filas=10,
        ),
        Paso(
            titulo="Las filas donde las dos coordenadas se contradicen",
            objetivo=(
                "Con el desvío calculado, un umbral declarado separa el desplazamiento "
                "sistemático de los errores reales. 200 m es holgado frente a los 61 m de "
                "mediana y estricto frente a los errores, que son de kilómetros."
            ),
            pandas=(
                "sospechosas = p01.coordenadas_sospechosas(consolidado)\n"
                "sospechosas[['fuente', 'codigo', 'comuna', 'desvio_m']]"
            ),
            excel=(
                "Con el desvío en la columna N: filtro `>200`, o "
                "`=SI(N2>200;\"revisar\";\"\")` y autofiltro sobre esa columna."
            ),
            trampa=(
                "El umbral es una **decisión** y hay que escribirla con su motivo. Un "
                "umbral elegido después de ver los datos, para que el número de hallazgos "
                "quede cómodo, no es un criterio: es el resultado disfrazado de criterio."
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
            "Cinco archivos `.xlsx` del portal de datos abiertos del Ministerio de "
            "Transportes, licencia CC BY-NC 2.0 verificada. Seis hojas en total, 1 928 "
            "filas, de las cuales una está en la hoja de cerrados."
        ),
        pasos=pasos,
        contexto=contexto,
        cierre=(
            "1 928 filas consolidadas, 1 927 abiertas, 46 comunas y 3 entidades. El "
            "`codigo` no identifica una fila, ni junto al archivo de origen. La "
            "validación cruzada de las dos coordenadas encontró tres errores de hasta "
            "10,3 km y un desplazamiento sistemático de 61 m con distribución bimodal.\n\n"
            "Lo que **no** se puede concluir con estos datos: cuánta gente usa cada "
            "local —no hay transacciones—, ni si está abierto cuando alguien llega —el "
            "horario está en el 18,06 % de las filas—."
        ),
        reproducir=(
            "python scripts/fetch_data.py bip-metro bip-puntos bip-centros-alto-estandar bip-centros-estandar bip-retail\n"
            "python -m cases.bip_lugares_carga.solution"
        ),
    )
