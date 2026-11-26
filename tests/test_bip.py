"""Pruebas del caso de consolidación (`cases.bip_lugares_carga.solution`) y de la
lectura de Excel desordenado (`lab.excel`).

Por qué no se usan los archivos reales
    Son cinco Excel con licencia Creative Commons NoComercial que no se versionan. Las
    pruebas construyen libros mínimos que **reproducen exactamente la maqueta del
    original**: fila de título, filas vacías, encabezado en una fila distinta en cada
    archivo, esquemas que no coinciden, un nombre de columna con espacio al final, una
    hoja de cerrados, y las dos representaciones de la coordenada.

    Así se prueba la lógica con cifras calculables a mano, y la suite corre sin
    descargar nada.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from lab.excel import detect_header_row, read_all_sheets, read_messy_sheet, sheet_names


def escribir_libro(
    destino: Path,
    hojas: dict[str, tuple[int, list[str], list[list]]],
) -> Path:
    """Escribe un libro con el encabezado desplazado, como los archivos reales.

    Args:
        destino: ruta del `.xlsx`.
        hojas: `{nombre_hoja: (filas_de_titulo, columnas, filas)}`.
    """
    with pd.ExcelWriter(destino, engine="xlsxwriter") as writer:
        for hoja, (titulo, columnas, filas) in hojas.items():
            frame = pd.DataFrame(filas, columns=columnas)
            frame.to_excel(writer, sheet_name=hoja, index=False, startrow=titulo)
            # La fila de título: una sola celda llena, como en el original.
            writer.sheets[hoja].write(0, 0, hoja.upper())
    return destino


#: Coordenadas reales de una estación, en ambas representaciones. El desvío entre
#: las dos es de unos 61 metros en el archivo original: una diferencia de datum.
ESTE, NORTE = 339892, 6298155
LAT, LON = -33.444355, -70.723068


@pytest.fixture(scope="module")
def libros(tmp_path_factory) -> Path:
    """Cinco libros que reproducen la maqueta de los archivos públicos."""
    carpeta = tmp_path_factory.mktemp("bip")

    # Metro: encabezado en la fila 7, código = línea (se repite), con horario.
    escribir_libro(carpeta / "bip-metro.xlsx", {
        "Abiertos": (7,
            ["CODIGO", "ENTIDAD", "NOMBRE FANTASIA", "DIRECCION", "COMUNA",
             "HORARIO REFERENCIAL", "ESTE", "NORTE", "LONGITUD", "LATITUD"],
            # Las dos filas usan el mismo par de coordenadas, tomado del archivo
            # real, donde UTM y lat/lon son coherentes entre sí. Variar una sin la
            # otra crearía una fila corrupta sin querer, y aquí la corrupción tiene
            # que ser deliberada y única.
            [["L1", "METRO", "SAN PABLO L1", "Av. San Pablo 6190", "LO PRADO",
              "Lunes a Viernes: 06:00-23:00", ESTE, NORTE, LON, LAT],
             ["L1", "METRO", "NEPTUNO", "Av. Neptuno 1", "LO PRADO",
              "Lunes a Viernes: 06:00-23:00", ESTE, NORTE, LON, LAT]]),
    })

    # Puntos bip!: encabezado en la fila 9, SIN horario, nombre con espacio al final,
    # y una fila cuya coordenada UTM apunta a otro lugar.
    escribir_libro(carpeta / "bip-puntos.xlsx", {
        "PCMA": (9,
            ["CODIGO", "ENTIDAD", "NOMBRE DE FANTASIA ", "DIRECCION", "COMUNA",
             "ESTE", "NORTE", "LONGITUD", "LATITUD"],
            # Dos filas coherentes, con 'Fullcarga' y 'FULLCARGA' para ejercer la
            # normalización, y UNA tercera deliberadamente corrupta: su UTM apunta a
            # un punto que está a kilómetros de su latitud y longitud publicadas.
            [["1224", "Fullcarga", "MARION", "LOS DURAZNOS 356 A", "ESTACION CENTRAL",
              349448, 6285070, -70.622688, -33.563601],
             ["3316", "FULLCARGA", "NISSY", "JOAQUIN EDWARDS 100", "LA PINTANA",
              349448, 6285070, -70.622688, -33.563601],
             ["9999", "Fullcarga", "ERROR", "SIN DIRECCION", "MACUL",
              341573, 6290982, -70.618279, -33.452271]]),
    })

    # Centros alto estándar: encabezado en la fila 13, SIN nombre de fantasía.
    escribir_libro(carpeta / "bip-centros-alto-estandar.xlsx", {
        "Abiertos": (13,
            ["CODIGO", "ENTIDAD", "DIRECCION", "COMUNA", "HORARIO",
             "ESTE", "NORTE", "LONGITUD", "LATITUD"],
            [["55", "FULLCARGA", "SAN FRANCISCO 10", "SANTIAGO",
              "Lun a Vie 07:00 a 22:00", 347089, 6296751, -70.645912, -33.458069]]),
    })

    # Centros estándar: encabezado en la fila 10, hoja en singular.
    escribir_libro(carpeta / "bip-centros-estandar.xlsx", {
        "Abierto": (10,
            ["CODIGO", "ENTIDAD", "DIRECCION", "COMUNA", "HORARIO",
             "ESTE", "NORTE", "LONGITUD", "LATITUD"],
            [["52", "FULLCARGA", "AV. INDEPENDENCIA 1", "CONCHALI",
              "Lun a Sab 08:00 a 20:00", 344838, 6303385, -70.669021, -33.397985]]),
    })

    # Retail: dos hojas, una de cerrados.
    columnas_retail = ["CODIGO", "ENTIDAD", "NOMBRE FANTASIA", "DIRECCION", "COMUNA",
                       "HORARIO REFERENCIAL", "ESTE", "NORTE", "LONGITUD", "LATITUD"]
    escribir_libro(carpeta / "bip-retail.xlsx", {
        "Abiertos": (9, columnas_retail,
            [["200", "WALMART", "LIDER EXPRESS LYON", "AV. NUEVA PROVIDENCIA 1",
              "PROVIDENCIA", "Lun-Dom 08:00-21:00", 350507, 6300726,
              -70.608475, -33.422710]]),
        "Cerrados": (9, columnas_retail,
            [["239", "WALMART", "LIDER EXPRESS COLINA", "LOS ALAMOS 1", "COLINA",
              "Lun-Dom 08:30-22:30", 342929, 6323318, -70.685467, -33.217646]]),
    })
    return carpeta


@pytest.fixture(scope="module")
def caso(libros: Path, monkeypatch_module=None):
    """El módulo del caso apuntando a los libros de prueba."""
    from cases.bip_lugares_carga import solution

    original = solution.ORIGINAL
    solution.ORIGINAL = libros
    yield solution
    solution.ORIGINAL = original


# ------------------------------------------------- lectura de Excel desordenado
def test_detect_header_row_encuentra_el_encabezado_tras_el_titulo():
    frame = pd.DataFrame([
        ["METRO", None, None, None],
        [None, None, None, None],
        ["CODIGO", "ENTIDAD", "COMUNA", "ESTE"],
        ["L1", "METRO", "LO PRADO", 339892],
    ])
    assert detect_header_row(frame, min_filled=4) == 2


def test_detect_header_row_ignora_las_filas_de_titulo_de_una_celda():
    frame = pd.DataFrame([
        ["PUNTOS BIP! (PCMA)", None, None, None],
        ["Actualizado 2024", None, None, None],
        ["CODIGO", "ENTIDAD", "COMUNA", "ESTE"],
    ])
    assert detect_header_row(frame) == 2


def test_detect_header_row_no_confunde_una_fila_de_datos_con_el_encabezado():
    """Una fila con números no puede ser el encabezado."""
    frame = pd.DataFrame([
        ["L1", "METRO", "LO PRADO", 339892],
        ["CODIGO", "ENTIDAD", "COMUNA", "ESTE"],
    ])
    assert detect_header_row(frame) == 1


def test_detect_header_row_falla_en_lugar_de_adivinar():
    frame = pd.DataFrame([["solo una celda"], [None]])
    with pytest.raises(ValueError, match="No se encontró una fila de encabezado"):
        detect_header_row(frame, min_filled=4)
    with pytest.raises(ValueError, match="min_filled"):
        detect_header_row(frame, min_filled=0)


def test_read_messy_sheet_informa_lo_que_hizo(libros: Path):
    tabla, informe = read_messy_sheet(libros / "bip-centros-alto-estandar.xlsx",
                                      sheet="Abiertos")
    assert informe.header_row == 13
    assert informe.rows_before_header == 13
    assert informe.rows_read == 1
    assert informe.columns_read == 9
    assert list(tabla.columns)[:2] == ["CODIGO", "ENTIDAD"]


def test_read_messy_sheet_recorta_los_espacios_de_los_nombres_de_columna(libros: Path):
    tabla, _ = read_messy_sheet(libros / "bip-puntos.xlsx", sheet="PCMA")
    assert "NOMBRE DE FANTASIA" in tabla.columns
    assert "NOMBRE DE FANTASIA " not in tabla.columns


def test_read_messy_sheet_lee_todo_como_texto(libros: Path):
    tabla, _ = read_messy_sheet(libros / "bip-metro.xlsx", sheet="Abiertos")
    # El código L1 sobrevive; leído como número se habría destruido.
    assert tabla["CODIGO"].iloc[0] == "L1"
    assert not pd.api.types.is_numeric_dtype(tabla["ESTE"])


def test_read_messy_sheet_acepta_la_fila_de_encabezado_si_ya_se_conoce(libros: Path):
    tabla, informe = read_messy_sheet(libros / "bip-metro.xlsx", sheet="Abiertos",
                                      header_row=7)
    assert informe.header_row == 7
    assert len(tabla) == 2


def test_sheet_names_y_read_all_sheets(libros: Path):
    assert sheet_names(libros / "bip-retail.xlsx") == ["Abiertos", "Cerrados"]
    hojas = read_all_sheets(libros / "bip-retail.xlsx")
    assert set(hojas) == {"Abiertos", "Cerrados"}
    solo_abiertos = read_all_sheets(libros / "bip-retail.xlsx", skip=("Cerrados",))
    assert set(solo_abiertos) == {"Abiertos"}


# --------------------------------------------------------------------- el caso
def test_el_caso_detecta_los_cinco_encabezados_distintos(caso):
    lectura = caso.informe_de_lectura(caso.cargar())
    filas = lectura.set_index(["fuente", "hoja"])["encabezado_en_fila"].to_dict()
    assert filas[("bip-metro", "Abiertos")] == 7
    assert filas[("bip-puntos", "PCMA")] == 9
    assert filas[("bip-centros-alto-estandar", "Abiertos")] == 13
    assert filas[("bip-centros-estandar", "Abierto")] == 10
    assert filas[("bip-retail", "Abiertos")] == 9
    assert len(lectura) == 6, "cinco archivos y seis hojas"


def test_el_caso_marca_la_hoja_de_cerrados(caso):
    lectura = caso.informe_de_lectura(caso.cargar())
    cerrada = lectura.loc[lectura.hoja.eq("Cerrados")].iloc[0]
    assert cerrada.abierto == "no"
    assert (lectura.loc[lectura.hoja.ne("Cerrados"), "abierto"] == "sí").all()


def test_el_informe_de_esquemas_muestra_que_falta_en_cada_archivo(caso):
    esquemas = caso.informe_de_esquemas(caso.cargar()).set_index("fuente")
    assert esquemas.loc["bip-puntos", "horario"] == "—"
    assert esquemas.loc["bip-centros-alto-estandar", "nombre"] == "—"
    assert esquemas.loc["bip-puntos", "nombre"] == "NOMBRE DE FANTASIA"
    assert esquemas.loc["bip-metro", "horario"] == "HORARIO REFERENCIAL"


def test_la_consolidacion_lleva_todo_al_esquema_comun(caso):
    consolidado = caso.consolidar()
    assert len(consolidado) == 9, "2 + 3 + 1 + 1 + 1 abiertos, mas 1 cerrado"
    for campo in caso.ESQUEMA:
        assert campo in consolidado.columns
    assert set(consolidado["tipo_local"]) == set(caso.TIPOS.values())


def test_la_consolidacion_conserva_el_origen_que_no_esta_en_los_datos(caso):
    consolidado = caso.consolidar()
    # El tipo de local vive en el nombre del archivo: sin declararlo se pierde.
    metro = consolidado.loc[consolidado.fuente.eq("bip-metro")]
    assert set(metro["tipo_local"]) == {"Estación de Metro"}
    assert consolidado["abierto"].sum() == 8
    assert (~consolidado["abierto"]).sum() == 1


def test_la_normalizacion_une_fullcarga_con_Fullcarga(caso):
    consolidado = caso.consolidar()
    # En los datos de prueba aparece como 'Fullcarga' y como 'FULLCARGA'.
    crudas = consolidado["entidad"].dropna().nunique()
    normalizadas = consolidado["entidad_clave"].replace("", pd.NA).dropna().nunique()
    assert crudas > normalizadas, "sin normalizar habría grupos espurios"
    assert set(consolidado["entidad_clave"]) == {"METRO", "FULLCARGA", "WALMART"}


def test_la_etiqueta_conserva_las_tildes_aunque_la_clave_no(caso):
    consolidado = caso.consolidar()
    fila = consolidado.loc[consolidado.comuna.eq("CONCHALI")].iloc[0]
    assert fila.comuna_clave == "CONCHALI"
    assert fila.comuna_etiqueta == "Conchali"


def test_el_codigo_no_es_clave_y_la_compuesta_tampoco(caso):
    """En el archivo de Metro el código es la línea, no el local."""
    tabla = caso.validar_clave(caso.consolidar()).set_index("ambito")
    assert tabla.loc["consolidado", "es_clave"] == "no"
    assert tabla.loc["solo bip-metro", "es_clave"] == "no"
    assert tabla.loc["solo bip-puntos", "es_clave"] == "sí"
    # Y el hallazgo que importa: ni siquiera fuente + código identifica una fila.
    assert tabla.loc["clave compuesta (fuente + codigo)", "es_clave"] == "no"


def test_la_cobertura_declara_que_fuentes_no_traen_cada_campo(caso):
    cobertura = caso.cobertura_de_campos(caso.consolidar()).set_index("campo")
    assert "bip-puntos" in cobertura.loc["horario", "fuentes_sin_el_campo"]
    assert "bip-centros-alto-estandar" in cobertura.loc["nombre", "fuentes_sin_el_campo"]
    assert cobertura.loc["codigo", "cobertura_pct"] == 100.0
    assert cobertura.loc["horario", "cobertura_pct"] < 100.0


# ------------------------------------------------- validación cruzada de coordenadas
def test_la_validacion_cruzada_distingue_el_desvio_sistematico_del_error(caso):
    consolidado = caso.consolidar()
    validacion = caso.validar_coordenadas(consolidado).set_index("fuente")
    # Los archivos sin filas corruptas no deben reportar sospechosas.
    assert validacion.loc["bip-retail", "sospechosas"] == 0
    assert "sin errores de registro" in validacion.loc["bip-retail", "veredicto"]
    # El que tiene la fila inventada a propósito, sí.
    assert validacion.loc["bip-puntos", "sospechosas"] == 1
    assert "revisar" in validacion.loc["bip-puntos", "veredicto"]


def test_la_validacion_cruzada_encuentra_la_fila_corrupta(caso):
    sospechosas = caso.coordenadas_sospechosas(caso.consolidar())
    assert len(sospechosas) == 1
    assert sospechosas.iloc[0].codigo == "9999"
    assert sospechosas.iloc[0].desvio_m > caso.UMBRAL_COORDENADA_M
    # Y el desvío se expresa en metros, no en grados.
    assert sospechosas.iloc[0].desvio_m > 1000


def test_el_desvio_sistematico_no_se_reporta_como_error(caso):
    """Mil filas con el mismo desplazamiento no son mil errores."""
    consolidado = caso.consolidar()
    normales = consolidado.loc[~consolidado.coordenada_sospechosa, "desvio_m"].dropna()
    assert len(normales) == 8
    # La mayoría arrastra el desplazamiento sistemático de decenas de metros, y
    # ninguna queda marcada: el desvío constante no es un error de registro.
    assert normales.median() > 10
    assert normales.max() < caso.UMBRAL_COORDENADA_M
    assert consolidado["coordenada_sospechosa"].sum() == 1


# -------------------------------------------------------------------- resultados
def test_el_resumen_declara_unidad_y_definicion(caso):
    resumen = caso.resumen(caso.consolidar())
    assert list(resumen.columns) == ["indicador", "valor", "unidad", "definicion"]
    assert resumen.definicion.str.len().gt(0).all()
    valores = resumen.set_index("indicador").valor
    assert valores["lugares_totales"] == 9
    assert valores["lugares_abiertos"] == 8
    assert valores["lugares_cerrados"] == 1
    assert valores["coordenadas_sospechosas"] == 1


def test_el_resumen_informa_la_cobertura_del_horario(caso):
    valores = caso.resumen(caso.consolidar()).set_index("indicador").valor
    # Tres de los ocho abiertos provienen del archivo que no publica horario.
    assert valores["con_horario_declarado"] == 5
    assert valores["cobertura_horario_pct"] == pytest.approx(100 * 5 / 8, abs=0.01)


def test_por_comuna_excluye_los_cerrados(caso):
    tabla = caso.por_comuna(caso.consolidar())
    assert "COLINA" not in set(tabla.comuna_clave), "la comuna del local cerrado"
    assert tabla.total.sum() == 8


def test_por_entidad_agrupa_sobre_la_clave_normalizada(caso):
    tabla = caso.por_entidad(caso.consolidar()).set_index("entidad_clave")
    assert set(tabla.index) == {"FULLCARGA", "METRO", "WALMART"}
    assert tabla.loc["FULLCARGA", "locales"] == 5
    assert tabla.loc["METRO", "locales"] == 2


def test_analizar_devuelve_todas_las_tablas_y_exportar_las_escribe(caso, tmp_path):
    resultados = caso.analizar()
    esperadas = {"lectura", "esquemas", "cobertura_campos", "clave",
                 "validacion_coordenadas", "coordenadas_sospechosas", "resumen",
                 "por_comuna", "por_entidad",
                 # P02: qué identifica una fila.
                 "claves_candidatas", "claves_evaluadas", "columnas_como_clave",
                 "clave_subrogada",
                 # P04: qué cambió la normalización y si estuvo bien.
                 "efecto_de_normalizar", "auditoria_de_fusiones",
                 "aporte_de_abreviaturas"}
    assert set(resultados) == esperadas
    destino = caso.exportar(resultados, destino=tmp_path / "salida")
    assert {p.stem for p in destino.glob("*.csv")} == esperadas


def test_los_archivos_ausentes_explican_como_conseguirlos(tmp_path):
    from cases.bip_lugares_carga import solution

    original = solution.ORIGINAL
    try:
        solution.ORIGINAL = tmp_path / "vacio"
        with pytest.raises(FileNotFoundError, match="fetch_data.py"):
            solution.cargar()
    finally:
        solution.ORIGINAL = original


# ============================================================ P02: claves · P04: normalización
#
# Estas pruebas no construyen libros: las funciones de P02 y P04 reciben el consolidado,
# de modo que se les pasa una tabla con la **forma** del real y las cifras conocidas.

def consolidado_de_prueba() -> pd.DataFrame:
    """Seis filas con la estructura del consolidado real.

    Reproduce lo que P02 mide: **ninguna columna sola identifica una fila**.

    - `codigo` vale la línea en Metro y se repite;
    - las dos filas de Metro son la misma estación, de modo que comparten coordenada;
    - `direccion` se repite entre dos locales de retail del mismo centro comercial;
    - `nombre` falla por las dos causas a la vez: tiene un nulo **y** un repetido.

    Y lo que P04 audita: `Fullcarga` contra `FULLCARGA`, una dirección con tilde que la
    normalización fusiona, y un `PJE` contra `PASAJE` que solo fusiona la expansión de
    abreviaturas.
    """
    return pd.DataFrame({
        "fuente": ["bip-metro", "bip-metro", "bip-retail", "bip-retail",
                   "bip-puntos", "bip-puntos"],
        "hoja": ["Abiertos"] * 6,
        "codigo": ["L1", "L1", "R1", "R2", "P1", "P2"],
        "entidad": ["METRO", "METRO", "WALMART", "WALMART", "Fullcarga", "FULLCARGA"],
        "nombre": ["SAN PABLO", None, "LIDER UNO", "LIDER DOS", "ALMACEN", "ALMACEN"],
        "direccion": ["AV. AMÉRICO VESPUCIO 1", "AV. AMERICO VESPUCIO 1",
                      "CALLE UNO 10", "CALLE UNO 10", "PJE TRES 30", "PASAJE TRES 30"],
        "comuna": ["Santiago", "Santiago", "Maipu", "Maipu", "Ñuñoa", "Ñuñoa"],
        "este": [340000, 340000, 341000, 342000, 343000, 344000],
        "norte": [6290000, 6290000, 6291000, 6292000, 6293000, 6294000],
        "tipo_local": ["Estación de Metro", "Estación de Metro", "Retail", "Retail",
                       "Punto bip!", "Punto bip!"],
    })


def test_p02_ninguna_columna_sola_identifica_una_fila():
    from cases.bip_lugares_carga.solution import informe_de_columnas

    informe = informe_de_columnas(consolidado_de_prueba()).set_index("columna")
    assert (informe["es_clave"] == "no").all()
    # El código de Metro vale la línea y se repite.
    assert informe.loc["codigo", "repetidos"] == 1
    # `nombre` falla por las dos causas a la vez, igual que en el archivo real, de modo
    # que completarlo no bastaría.
    assert informe.loc["nombre", "nulos"] == 1
    assert informe.loc["nombre", "repetidos"] == 1
    assert informe.loc["nombre", "por_que_no"] == "tiene nulos y repetidos"
    # Y todas las que fallan dicen por qué.
    assert (informe["por_que_no"].str.len() > 0).all()


def test_p02_la_clave_compuesta_con_el_archivo_tampoco_basta():
    """Es la corrección al enunciado de P02, que proponía esa salida.

    El enunciado decía «hace falta una clave compuesta, o una clave nueva con el origen
    del archivo». La primera mitad es cierta y la segunda no: en el archivo real 136
    filas comparten `fuente + codigo`.
    """
    from cases.bip_lugares_carga.solution import claves_candidatas

    consolidado = consolidado_de_prueba()
    assert consolidado[["fuente", "codigo"]].duplicated().any()
    candidatas = list(claves_candidatas(consolidado)["columnas"])
    assert "fuente + codigo" not in candidatas


def test_p02_las_candidatas_son_minimas_y_se_evaluan_todas():
    from cases.bip_lugares_carga.solution import (
        claves_candidatas,
        claves_candidatas_evaluadas,
    )

    consolidado = consolidado_de_prueba()
    candidatas = claves_candidatas(consolidado)
    evaluadas = claves_candidatas_evaluadas(consolidado)
    assert len(evaluadas) == len(candidatas)
    # Ninguna candidata se declara apta sin justificar por qué.
    assert (evaluadas["por_que"].str.len() > 10).all()
    assert (evaluadas["unica_hoy"] == "si").all()


def test_p02_la_clave_subrogada_identifica_cada_fila():
    from cases.bip_lugares_carga.solution import (
        PREFIJO_ID,
        clave_subrogada,
        informe_de_clave_subrogada,
    )

    consolidado = consolidado_de_prueba()
    ids = clave_subrogada(consolidado)
    assert ids.nunique() == len(consolidado)
    assert ids.str.startswith(PREFIJO_ID).all()
    informe = informe_de_clave_subrogada(consolidado).set_index("indicador")["valor"]
    assert informe["es_clave"] == "sí"
    assert informe["filas_con_identidad_repetida"] == 0


def test_p02_la_clave_subrogada_es_determinista_entre_llamadas():
    """Es su única ventaja frente al número de fila que usaron P08, P09 y P10."""
    from cases.bip_lugares_carga.solution import clave_subrogada

    consolidado = consolidado_de_prueba()
    assert list(clave_subrogada(consolidado)) == list(clave_subrogada(consolidado))
    revuelto = consolidado.iloc[[3, 1, 5, 0, 4, 2]]
    assert set(clave_subrogada(revuelto)) == set(clave_subrogada(consolidado))


def test_p04_el_efecto_de_normalizar_se_mide_por_columna():
    from cases.bip_lugares_carga.solution import efecto_de_normalizar

    tabla = efecto_de_normalizar(consolidado_de_prueba()).set_index("columna")
    # `Fullcarga` y `FULLCARGA` son un grupo, no dos.
    assert tabla.loc["entidad", "grupos_espurios_evitados"] == 1
    # La comuna no gana nada, igual que en el archivo real.
    assert tabla.loc["comuna", "grupos_espurios_evitados"] == 0
    assert tabla.loc["direccion", "grupos_espurios_evitados"] >= 1


def test_p04_cada_fusion_queda_a_la_vista_para_poder_verificarla():
    from cases.bip_lugares_carga.solution import auditoria_de_fusiones

    tabla = auditoria_de_fusiones(consolidado_de_prueba())
    assert not tabla.empty
    entidad = tabla.loc[tabla["columna"] == "entidad"].iloc[0]
    assert entidad["clave_normalizada"] == "FULLCARGA"
    assert "Fullcarga" in entidad["formas"]
    assert "FULLCARGA" in entidad["formas"]
    # Toda fusión informada nombra al menos dos formas crudas.
    assert (tabla["formas_crudas"] >= 2).all()


def test_p04_la_expansion_de_abreviaturas_se_mide_aparte():
    """En el fixture sí aporta —`PJE TRES 30` y `PASAJE TRES 30`—; en el archivo real, no.

    Separar las dos cifras es lo que permite afirmar que sobre los datos reales la
    expansión no fusiona nada, en lugar de suponer que ayuda porque existe.
    """
    from cases.bip_lugares_carga.solution import aporte_de_las_abreviaturas

    tabla = aporte_de_las_abreviaturas(consolidado_de_prueba()).set_index("indicador")
    valores = tabla["valor"]
    assert valores["fusiones_que_aporta_expandir"] == 1
    assert valores["normalizadas_expandiendo"] < valores["normalizadas_sin_expandir"]
    assert valores["fusiones_de_la_normalizacion"] >= 1
