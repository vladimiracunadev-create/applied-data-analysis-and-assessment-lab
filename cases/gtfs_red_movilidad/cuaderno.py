"""Cuaderno de trabajo de P06: los pasos, en Pandas y en Excel.

Se genera con `python scripts/build_cuadernos.py`. El rango de Excel de las fórmulas
supone `frequencies.txt` pegado con encabezado en la fila 1 y los datos en las filas 2 a
14521, con sus cuatro columnas en este orden:

    A trip_id · B start_time · C end_time · D headway_secs
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.gtfs_red_movilidad import solution as p06  # noqa: E402
from lab.cuaderno import Cuaderno, Paso  # noqa: E402
from lab.dates import parse_hms_seconds, service_day_hour  # noqa: E402
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
from lab.hoja_svg import Columna, Hoja  # noqa: E402
from lab.sources import zip_members  # noqa: E402
from lab.viz import bar_chart  # noqa: E402

#: Última fila de `frequencies.txt` pegado en una hoja: 14 520 ventanas más encabezado.
FIN = 14521

#: Columnas de la hoja donde se pega `frequencies.txt`.
COLUMNAS = ("trip_id", "start_time", "end_time", "headway_secs")

PROBLEMA = """
El Ministerio publica el horario completo del transporte público de Santiago en formato
GTFS: un ZIP de 12,8 MB que descomprimido pesa 69,7 MB, de los cuales 51 MB son un solo
archivo de **1 098 717 filas**.

La pregunta que llega es de las más básicas que se le pueden hacer a un horario:
*¿cuántas expediciones de transporte público salen por hora en un día laboral?* Es la
cifra que va en el primer párrafo de cualquier informe de oferta, y la que alguien usa
para decir si el servicio de la mañana es el doble que el de la tarde.

**Y hay cuatro formas de contestarla mal**, todas plausibles.

La tabla de horarios no contiene horas en el 77,5 % de sus filas: contiene
**desplazamientos desde el inicio del viaje**, porque esos recorridos no se publican con
horario fijo sino con frecuencia —«cada diez minutos entre las 6 y las 9»—. Agrupar ese
campo por su hora da 635 574 llegadas «a medianoche».

El relleno de ceros no es consistente: la misma expedición mezcla `0:00:00` y `00:00:51`,
y ordenadas como texto la primera queda **después** de la segunda.

Contar las expediciones declaradas en lugar de expandir las frecuencias subestima el
servicio por un **factor de seis**.

Y hay un cuarto problema que no existe: el 32 % de las paradas «no se usa». No es un
defecto de calidad, y reportarlo costaría más que no reportar nada.

Lo que distingue este caso de los demás es el **volumen**: aquí las decisiones de lectura
—qué columnas, qué tipos, descomprimir o no— dejan de ser estilo y pasan a decidir si el
análisis corre.
"""

SOLUCION = """
El recorrido va de leer el archivo sin romper la memoria, a un conteo que se valida por
dos caminos independientes.

**Leer solo lo necesario** (pasos 1 a 3). Mirar el inventario del ZIP antes de abrirlo,
leer del flujo comprimido sin descomprimir a disco, y de la tabla grande pedir **cuatro
de sus ocho columnas** como texto. `dtype=str` es deliberado: queremos ver los valores
como los publicó el organismo y decidir nosotros qué es un número y qué es una hora.

**Diagnosticar antes de calcular** (pasos 4 y 5). Medir cuántas filas traen horas de
reloj y cuántas desplazamientos, y comprobar el relleno de ceros. Las dos
comprobaciones cuestan una línea y las dos cambian el resultado.

**Expandir las frecuencias** (pasos 6 y 7). Cada ventana de frecuencia representa muchas
salidas reales. La expansión se hace vectorizada con `Index.repeat`, y el fin de la
ventana es **exclusivo**: la salida de `end_time` pertenece a la ventana siguiente, y
contarla infla el total en una salida por cada una de las 14 520 ventanas.

**Contestar, y medir el error del atajo** (pasos 8 y 9). El conteo correcto por hora, y
al lado lo que habría dado cada forma equivocada, con su magnitud.

**Y el defecto que no existe** (paso 10). 5 991 de las 18 486 filas de `stops.txt` no
aparecen en la tabla de horarios. 5 989 de ellas no son paradas: son estaciones, accesos
y nodos de pasillo, distinguidos por un campo de la especificación. Las paradas
realmente huérfanas son **dos**.
"""

FLUJO = Flujo(
    titulo="El problema: un horario donde el 77,5 % de las horas no son horas",
    etapas=[
        Etapa("GTFS, 12,8 MB", ["12 archivos", "stop_times: 1,1 M filas",
                                 "51 MB de los 69,7"],
              nota="no se descomprime", color=TINTA),
        Etapa("Leer selectivo", ["4 de 8 columnas", "dtype=str a propósito",
                                 "del flujo del ZIP"],
              nota="la mitad de la memoria", color=AZUL),
        Etapa("Diagnosticar", ["77,5 % no son horas", "relleno de ceros irregular",
                               "horas de 24:00 y más"],
              nota="antes de calcular", color=OCRE),
        Etapa("Expandir", ["14 520 ventanas", "fin EXCLUSIVO",
                           "Index.repeat vectorizado"],
              nota="142 366 salidas", color=AZUL),
        Etapa("Contar por hora", ["64 011 expediciones", "validado por dos caminos",
                                  "y el error de cada atajo"],
              nota="y 2 paradas huérfanas", color=ACENTO),
    ],
)

MAPA = Mapa(
    centro="P06 · Expediciones por hora",
    subtitulo="10 pasos · 7 trampas",
    ramas=[
        Rama("Leer sin romper la memoria",
             ["1 · Mirar el ZIP antes de abrirlo",
              "2 · Leer del flujo, sin descomprimir",
              "3 · Cuatro columnas de ocho, como texto"], color=AZUL),
        Rama("Diagnosticar antes de calcular",
             ["4 · El 77,5 % no son horas de reloj",
              "5 · El relleno de ceros miente al ordenar"], color=OCRE),
        Rama("Expandir las frecuencias",
             ["6 · Una ventana son muchas salidas",
              "7 · El fin de la ventana es exclusivo"], color=AZUL),
        Rama("Contestar y medir el atajo",
             ["8 · Expediciones por hora del día",
              "9 · Lo que habría dado cada error"], color=ACENTO),
        Rama("Y el defecto que no existe",
             ["10 · «El 32 % de las paradas no se usa»"], color=OCRE),
    ],
)

APRENDIZAJES = (
    "Un campo que se llama `arrival_time` **no siempre es una hora**. En GTFS depende de "
    "si la expedición se publica con horario fijo o con frecuencia, y hay que comprobarlo "
    "antes de agrupar por él.",
    "Las horas de un día de servicio **pasan de 24:00**: `25:10:00` es la 01:10 del día "
    "siguiente y es un valor legítimo que `pd.to_datetime` rechaza.",
    "Ordenar horas **como texto** pone `0:00:00` después de `00:00:51`. El relleno de "
    "ceros irregular es invisible hasta que algo sale en el orden equivocado.",
    "Un intervalo publicado como «cada N minutos entre A y B» tiene el **fin exclusivo**. "
    "Contarlo inclusivo infla el total en una salida por ventana, y aquí hay 14 520.",
    "`usecols` y `dtype=str` no son estilo cuando la tabla tiene 1,1 millones de filas: "
    "deciden si el análisis corre en esta máquina.",
    "Leer del flujo comprimido evita duplicar 70 MB en disco sin ganar nada a cambio.",
    "Un recuento que **no se puede validar por dos caminos independientes** es una "
    "afirmación, no una medición. Aquí los dos caminos dan 64 011.",
    "«El 32 % de las paradas está huérfano» es un defecto que **no existe**: 5 989 de "
    "esas filas no son paradas. Reportarlo costaría más que no reportar nada.",
)

RELACIONADOS = (
    ("Qué se encontró, con las cuatro trampas medidas — README del caso", "README.md"),
    ("P09 · La cobertura nocturna, que usa esta expansión",
     "../carga_nocturna/README.md"),
    ("P10 · La jerarquía de paradas del feed, a fondo",
     "../correspondencia_metro/README.md"),
    ("Equivalencias entre SQL, Pandas, Excel y R", "../../docs/equivalencias.md"),
)


def construir() -> Cuaderno:
    """El cuaderno de P06."""
    contexto = {
        "p06": p06,
        "FEED": p06.FEED,
        "zip_members": zip_members,
        "parse_hms_seconds": parse_hms_seconds,
        "service_day_hour": service_day_hour,
        "bar_chart": bar_chart,
        "pd": pd,
    }

    pasos = [
        Paso(
            titulo="Mirar el ZIP antes de abrirlo",
            objetivo=(
                "Qué archivos trae, cuánto pesa cada uno descomprimido, y cuál es el "
                "grande. Decide si se puede leer todo o hay que elegir."
            ),
            pandas="zip_members(FEED)",
            excel=(
                "Abrir el ZIP en el explorador y mirar los tamaños. Excel **no puede "
                "abrir** el archivo grande: 1 098 717 filas superan el límite de "
                "1 048 576 de una hoja, de modo que este caso no se hace en Excel sin "
                "partir el archivo antes."
            ),
            trampa=(
                "Es el único caso del laboratorio donde Excel no alcanza. Y el límite no "
                "avisa bien: al abrir un CSV más largo, Excel carga el millón de filas "
                "que caben y **descarta el resto sin error**."
            ),
            filas=12,
        ),
        Paso(
            titulo="Leer del flujo comprimido, sin descomprimir",
            objetivo=(
                "El feed pesa 12,8 MB comprimido y 69,7 MB descomprimido. Descomprimir "
                "primero duplica el espacio sin aportar nada: `zipfile` da un flujo que "
                "`read_csv` lee directamente."
            ),
            pandas="tablas = p06.cargar()\n{nombre: tabla.shape for nombre, tabla in tablas.items()}",
            excel=(
                "Power Query puede leer de un ZIP, pero traerá el archivo entero a la "
                "hoja y choca con el límite de filas. La ruta en Excel es cargar solo "
                "`frequencies.txt`, que son 14 520 filas y sí cabe."
            ),
            mostrar="valor",
        ),
        Paso(
            titulo="Cuatro columnas de ocho, y todas como texto",
            objetivo=(
                "De `stop_times.txt` se usan cuatro de sus ocho columnas. Y `dtype=str` "
                "es deliberado: queremos ver los valores como los publicó el organismo y "
                "decidir nosotros qué es un número y qué es una hora."
            ),
            pandas=(
                "horarios = tablas['stop_times']\n"
                "{'filas': len(horarios), 'columnas': list(horarios.columns),\n"
                " 'memoria_MB': round(horarios.memory_usage(deep=True).sum() / 1e6, 1)}"
            ),
            excel=(
                "En Power Query, **Elegir columnas** antes de cargar, y poner el tipo de "
                "las horas en **Texto**. Si se deja en automático, Power Query convierte "
                "`0:00:00` a una hora y `25:10:00` a error."
            ),
            trampa=(
                "Dejar que pandas infiera los tipos convierte las horas a algo **antes** "
                "de que las validemos, y las de 24:00 o más se vuelven nulas o texto "
                "según la fila. El diagnóstico del paso siguiente ya no se podría hacer."
            ),
            mostrar="valor",
        ),
        Paso(
            titulo="El 77,5 % de las «horas» no son horas",
            objetivo=(
                "La comprobación que decide todo el resto. Una expedición con frecuencia "
                "declarada publica en `arrival_time` el **desplazamiento desde el inicio "
                "del viaje**, no la hora de reloj."
            ),
            pandas="p06.diagnosticar_horas(tablas)",
            excel=(
                "Sobre `frequencies.txt` cargado y la lista de `trip_id` de los horarios: "
                f"`=CONTAR.SI($A$2:$A${FIN};A2)>0` marca las expediciones con frecuencia. "
                "La proporción de filas marcadas es la cifra."
            ),
            formula_excel=f"=CONTAR.SI($A$2:$A${FIN};A2)>0",
            esperado="851 773 de 1 098 717 filas: el 77,5 %",
            trampa=(
                "Agrupar `arrival_time` por su hora sin esta comprobación da **635 574 "
                "llegadas a medianoche** y un gráfico con un pico absurdo a las 00:00. El "
                "pico es el `0:00:00` de cada primera parada de cada expedición de "
                "frecuencia."
            ),
            filas=6,
            hoja=Hoja(
                columnas=[
                    Columna("A", "trip_id", 120),
                    Columna("B", "arrival_time", 112),
                    Columna("E", "¿frecuencia?", 118),
                ],
                filas=[
                    ["101-I-L-B00", "0:00:00", "VERDADERO"],
                    ["101-I-L-B00", "00:00:51", ""],
                    ["T-ABS-01", "07:15:00", "FALSO"],
                ],
                celda="E2",
                formula="=CONTAR.SI($A$2:$A$14521;A2)>0",
                resultado="VERDADERO",
                nota="VERDADERO significa que ese 0:00:00 no es medianoche: es el minuto 0.",
            ),
        ),
        Paso(
            titulo="El relleno de ceros miente al ordenar",
            objetivo=(
                "La misma expedición mezcla `0:00:00` con una cifra y `00:00:51` con dos. "
                "Como texto, la primera es mayor que la segunda."
            ),
            pandas="'0:00:00' > '00:00:51'",
            excel=(
                "Pasa igual: con las horas en texto, ordenar la columna pone `0:00:00` "
                "después de `00:00:51`. Se arregla normalizando con "
                "`=TEXTO(VALOR.NUMERO(IZQUIERDA(B2;BUSCAR(\":\";B2)-1));\"00\")&EXTRAE(B2;BUSCAR(\":\";B2);9)`, "
                "que es ilegible, o convirtiendo a segundos como hace Pandas."
            ),
            trampa=(
                "No produce un error: produce la **primera parada de cada expedición "
                "ordenada al final**, de modo que el origen y el destino quedan "
                "cambiados. Un informe de tiempos de viaje con el signo invertido."
            ),
            mostrar="valor",
        ),
        Paso(
            titulo="Convertir a segundos, admitiendo horas de 24:00 y más",
            objetivo=(
                "Un día de servicio puede pasar de la medianoche: `25:10:00` es la 01:10 "
                "del día siguiente. Es un valor legítimo de la especificación que "
                "`pd.to_datetime` rechaza."
            ),
            pandas=(
                "ejemplos = pd.Series(['0:00:00', '00:00:51', '25:10:00', '28:00:00'])\n"
                "pd.DataFrame({'texto': ejemplos,\n"
                "              'segundos': parse_hms_seconds(ejemplos),\n"
                "              'hora_de_reloj': service_day_hour(parse_hms_seconds(ejemplos))})"
            ),
            excel=(
                "`=VALOR.NUMERO(IZQUIERDA(B2;BUSCAR(\":\";B2)-1))*3600 + ...` suma las "
                "tres partes. La hora de reloj es el resto: `=RESIDUO(ENTERO(E2/3600);24)`."
            ),
            formula_excel="=RESIDUO(ENTERO(E2/3600);24)",
            esperado="25:10:00 → 90 600 s → hora de reloj 1",
            trampa=(
                "`pd.to_datetime('25:10:00')` **falla**, y con `errors='coerce'` devuelve "
                "nulo en silencio. Las horas del servicio nocturno desaparecerían del "
                "conteo sin que nada avise."
            ),
            filas=4,
        ),
        Paso(
            titulo="Una ventana de frecuencia son muchas salidas",
            objetivo=(
                "Cada fila de `frequencies.txt` dice «entre A y B sale un vehículo cada N "
                "segundos». Son 14 520 filas que representan 142 366 salidas reales."
            ),
            pandas=(
                "expandido = p06.expandir_frecuencias(tablas)\n"
                "expandido.head(4)"
            ),
            excel=(
                "El número de salidas de cada ventana es "
                "`=ENTERO((C2-B2)*86400/D2)`, con las horas como fracción de día. "
                "Expandirlas a una fila cada una exige Power Query: columna con "
                "`List.Numbers(0; salidas)` y luego **Expandir a nuevas filas**."
            ),
            formula_excel="=ENTERO((C2-B2)*86400/D2)",
            esperado="142 366 salidas en total",
            filas=4,
            hoja=Hoja(
                columnas=[
                    Columna("A", "trip_id", 118),
                    Columna("B", "start_time", 100),
                    Columna("C", "end_time", 96),
                    Columna("D", "headway", 84),
                    Columna("E", "salidas", 86),
                ],
                filas=[
                    ["101-I-L-B00", "06:00:00", "07:00:00", "600", "6"],
                    ["102-I-L-B00", "00:00:00", "01:00:00", "1800", ""],
                    ["101-R-L-B01", "01:00:00", "05:30:00", "8100", ""],
                ],
                celda="E2",
                formula="=ENTERO((C2-B2)*86400/D2)",
                resultado="6",
                nota="De 06:00 a 07:00 cada 600 s son SEIS salidas, no siete.",
            ),
        ),
        Paso(
            titulo="El fin de la ventana es exclusivo",
            objetivo=(
                "La salida de `end_time` pertenece a la ventana siguiente. Es lo que fija "
                "la especificación, y de ello depende un 10 % del total."
            ),
            pandas=(
                "comparacion = p06.comparar_ingenuo_vs_correcto(tablas)\n"
                "comparacion"
            ),
            excel=(
                "`=ENTERO((C2-B2)*86400/D2)` ya es exclusivo. La versión inclusiva es "
                "`=ENTERO((C2-B2)*86400/D2)+1`, y la diferencia entre las dos sumas es "
                "el error: una salida por ventana."
            ),
            formula_excel=f"=SUMA(E2:E{FIN})",
            esperado="64 011 correctas · 6 641 salidas de más si se cuenta inclusivo",
            trampa=(
                "Es el error más fácil de defender y el más fácil de cometer: contar «de "
                "las 6 a las 7 cada 10 minutos» como siete salidas en lugar de seis. "
                "Infla el total un **10,37 %**, que es una magnitud que nadie cuestiona "
                "en un informe."
            ),
            filas=8,
        ),
        Paso(
            titulo="Expediciones por hora del día",
            objetivo=(
                "La pregunta, contestada. Las salidas expandidas más las de horario "
                "absoluto, agrupadas por hora del día de servicio."
            ),
            pandas="por_hora = p06.expediciones_por_hora(tablas)\npor_hora",
            excel=(
                "Con las salidas expandidas y su hora en una columna: **tabla dinámica** "
                "con la hora en Filas y el conteo en Valores. Sin dinámica, "
                f"`=CONTAR.SI($F$2:$F${FIN};G2)` con las horas 0 a 23 en la columna G."
            ),
            formula_excel=f"=CONTAR.SI($F$2:$F${FIN};G2)",
            esperado="64 011 expediciones en el día laboral",
            filas=26,
            figura=(
                "total = por_hora.groupby('hora_reloj', as_index=False)['salidas'].sum()\n"
                "total['hora'] = total['hora_reloj'].astype(str).str.zfill(2)\n"
                "bar_chart(\n"
                "    total, category='hora', value='salidas', path=SVG_DESTINO,\n"
                "    title='Salidas programadas por hora del día de servicio',\n"
                "    ylabel='salidas', xlabel='hora de reloj', sort=False,\n"
                "    source='GTFS DTPM · licencia no verificada')"
            ),
            pie_figura=(
                "Las dos puntas se ven solas. Y las horas 0 a 4 no están vacías: es el "
                "servicio nocturno, que es el tema de P09."
            ),
        ),
        Paso(
            titulo="«El 32 % de las paradas no se usa»: el defecto que no existe",
            objetivo=(
                "5 991 de las 18 486 filas de `stops.txt` no aparecen en la tabla de "
                "horarios. Antes de reportarlo, mirar **qué son** esas filas."
            ),
            pandas="p06.paradas_sin_uso(tablas)",
            excel=(
                "`=CONTAR.SI(horarios!$D:$D;A2)=0` marca las filas sin uso, y una tabla "
                "dinámica por `location_type` muestra qué son. La fila que importa es la "
                "del tipo 0."
            ),
            formula_excel="=CONTAR.SI(horarios!$D:$D;A2)=0",
            esperado="5 991 sin uso, de las cuales solo 2 son paradas de embarque",
            trampa=(
                "Reportar «el 32 % de las paradas está huérfano» cuesta credibilidad: "
                "5 989 de esas filas **no son paradas**, son estaciones, accesos y nodos "
                "de pasillo, y la especificación las distingue con un campo. El feed es "
                "**complejo**, no sucio.\n\n"
                "Un informe de calidad que no mira la jerarquía del formato produce "
                "hallazgos que el publicador descarta en treinta segundos, y con ellos "
                "descarta el resto del informe."
            ),
            filas=6,
        ),
    ]

    return Cuaderno(
        caso="P06",
        titulo="Contar expediciones en un horario donde el 77,5 % de las horas no son horas",
        pregunta=(
            "¿Cuántas expediciones de transporte público salen por hora en un día "
            "laboral, y cómo se reparten entre buses, Metro y trenes?"
        ),
        datos=(
            "Feed GTFS estático de la Red Metropolitana de Movilidad (DTPM), 12,8 MB "
            "comprimidos y 69,7 descomprimidos. 1 098 717 filas de horarios, 26 137 "
            "expediciones, 18 486 lugares, 425 recorridos. **Licencia no verificada**: "
            "el sitio no publica condiciones de uso."
        ),
        pasos=pasos,
        contexto=contexto,
        importes=(
            "from cases.gtfs_red_movilidad import solution as p06\n"
            "from lab.dates import parse_hms_seconds, service_day_hour\n"
            "from lab.sources import zip_members\n"
            "\n"
            "import pandas as pd\n"
            "\n"
            "FEED = p06.FEED"
        ),
        columnas_excel=COLUMNAS,
        fuentes_datos="gtfs-red-movilidad",
        problema=PROBLEMA,
        solucion=SOLUCION,
        flujo=FLUJO,
        mapa=MAPA,
        aprendizajes=APRENDIZAJES,
        relacionados=RELACIONADOS,
        anterior=("P01 · Consolidar cinco Excel", "../bip_lugares_carga/CUADERNO.md"),
        siguiente=("P08 · El cruce que no tiene clave",
                   "../cobertura_de_carga/README.md"),
        cierre=(
            "**64 011 expediciones** en el día laboral, validadas por dos caminos sin "
            "código común: expansión vectorizada con agrupación, y suma aritmética por "
            "ventana más el horario absoluto. Los dos dan la misma cifra.\n\n"
            "Lo que habrían dado los atajos: contar expediciones declaradas, 7 905 "
            "—un **−87,65 %**—; tomar el fin de ventana como inclusivo, 70 652 —un "
            "**+10,37 %**—; agrupar `arrival_time` como hora, un pico de 635 574 "
            "llegadas a medianoche.\n\n"
            "Y dos paradas realmente huérfanas, no 5 991."
        ),
        reproducir=(
            "python scripts/fetch_data.py gtfs-red-movilidad\n"
            "python -m cases.gtfs_red_movilidad.solution\n"
            "python cases/gtfs_red_movilidad/cuaderno/pasos.py"
        ),
    )
