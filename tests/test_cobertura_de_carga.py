"""Pruebas del caso P08 (`cases.cobertura_de_carga.solution`).

Por qué no se usan los datos reales
    El caso cruza el feed GTFS del DTPM (12,8 MB, licencia no verificada) con los cinco
    Excel de bip! (CC BY-NC 2.0). Ninguno se versiona, de modo que las pruebas
    construyen una geometría **sintética y calculable a mano**.

Qué geometría
    Un único lugar de carga en el centro de Santiago, y paradas colocadas a distancias
    exactas usando los grados por kilómetro de esa latitud. Eso permite afirmar, sin
    depender de ninguna tabla externa:

    - que una parada a 0,010779° de longitud está a 1 km, y una a 0,008993° de latitud
      también, aunque los desplazamientos en grados sean distintos;
    - que la euclídea sobre grados escalada con los 111,32 km/grado del meridiano
      **sobreestima un 20 % hacia el este** y acierta hacia el norte. El sesgo queda
      anclado al eje, que es la forma de demostrar que es un sesgo y no un ruido.

    El valor de 0,010779 no se escribe a mano: se obtiene de `lab.geo.grados_por_km`,
    de modo que la prueba falla si esa función cambia de comportamiento.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from cases.cobertura_de_carga.solution import (
    CITA_UMBRAL,
    FACTORES_RODEO,
    KM_POR_GRADO,
    MINIMO_ATRIBUIDAS,
    MINIMO_POR_CELDA,
    PASO_REJILLA,
    RADIO_DE_ALCANCE_M,
    UMBRAL_M,
    UMBRALES_M,
    cargar_paradas,
    cobertura_por_umbral,
    comparar_formulas,
    distribucion,
    informe_de_identificador,
    informe_de_paradas,
    limite_por_horario,
    medir,
    paradas_fuera_de_alcance,
    por_rejilla,
    por_tipo_de_lugar,
    resumen,
    resumen_con_y_sin_lejanas,
    sensibilidad_rodeo,
    sesgo_del_proxy_de_comuna,
)
from lab.geo import grados_por_km, haversine_km

#: Centro de la geometría: el único lugar de carga de la mayoría de las pruebas.
LAT0, LON0 = -33.45, -70.66

#: Grados que mide un kilómetro a esa latitud. La asimetría es el punto de la prueba.
GRADO_LAT_KM, GRADO_LON_KM = grados_por_km(LAT0)


def parada(stop_id: str, km_norte: float = 0.0, km_este: float = 0.0,
           nombre: str | None = None) -> dict:
    """Una parada a una distancia exacta del centro, expresada en kilómetros."""
    return {
        "stop_id": stop_id,
        "stop_name": nombre or f"{stop_id}-Parada de prueba",
        "lat": LAT0 + km_norte * GRADO_LAT_KM,
        "lon": LON0 + km_este * GRADO_LON_KM,
    }


def tabla_de_lugares(filas: list[dict]) -> pd.DataFrame:
    """Lugares con las columnas que el caso espera de `cargar_lugares`."""
    base = pd.DataFrame(filas)
    for columna, defecto in (
        ("codigo", "C1"),
        ("tipo_local", "Punto bip!"),
        ("nombre", "Local de prueba"),
        ("comuna_etiqueta", "Santiago"),
        ("horario", pd.NA),
        ("coordenada_sospechosa", False),
    ):
        if columna not in base.columns:
            base[columna] = defecto
    if "latitud_utm" not in base.columns:
        base["latitud_utm"] = base["lat"]
    if "longitud_utm" not in base.columns:
        base["longitud_utm"] = base["lon"]
    return base.reset_index(drop=True)


@pytest.fixture
def un_lugar() -> pd.DataFrame:
    return tabla_de_lugares([{"lat": LAT0, "lon": LON0}])


# ------------------------------------------------- la geometría, calculable a mano
def test_un_kilometro_al_este_y_al_norte_miden_lo_mismo(un_lugar):
    """Desplazamientos distintos en grados, la misma distancia en metros."""
    paradas = pd.DataFrame([
        parada("ESTE", km_este=1.0),
        parada("NORTE", km_norte=1.0),
    ])
    medidas = medir(paradas, un_lugar)
    assert medidas["metros"].to_list() == pytest.approx([1000.0, 1000.0], abs=1.0)
    # Y los desplazamientos en grados NO son iguales: eso es lo que rompe la euclídea.
    assert GRADO_LON_KM > GRADO_LAT_KM
    assert pytest.approx(1.199, abs=0.01) == GRADO_LON_KM / GRADO_LAT_KM


def test_la_euclidea_sobre_grados_se_equivoca_solo_en_un_eje(un_lugar):
    """El sesgo del atajo está anclado al eje este-oeste. Esa es su firma."""
    paradas = pd.DataFrame([
        parada("ESTE", km_este=1.0),
        parada("NORTE", km_norte=1.0),
    ])
    lat_o = paradas["lat"].to_numpy()[:, None]
    lon_o = paradas["lon"].to_numpy()[:, None]
    euclid = np.sqrt(
        (lat_o - un_lugar["lat"].to_numpy()[None, :]) ** 2
        + (lon_o - un_lugar["lon"].to_numpy()[None, :]) ** 2
    ) * KM_POR_GRADO * 1000
    este, norte = float(euclid[0, 0]), float(euclid[1, 0])
    assert este == pytest.approx(1200.0, rel=0.01)   # 20 % de más
    assert norte == pytest.approx(1001.0, rel=0.01)  # acierta
    assert este > norte


def test_comparar_formulas_no_encuentra_ni_una_subestimacion(un_lugar):
    """Si el error fuera ruido habría subestimaciones. No hay ninguna."""
    paradas = pd.DataFrame([
        parada(f"P{i}", km_norte=i * 0.1, km_este=(10 - i) * 0.1) for i in range(11)
    ])
    tabla = comparar_formulas(paradas, un_lugar).set_index("indicador")["valor"]
    assert tabla["errores_negativos"] == 0
    assert tabla["error_mediano_m"] > 0
    assert tabla["cobertura_euclidea_pct"] <= tabla["cobertura_haversine_pct"]


def test_medir_coincide_con_haversine_calculado_aparte(un_lugar):
    """Validación cruzada: la distancia del caso contra una llamada directa."""
    paradas = pd.DataFrame([parada("A", km_este=0.25), parada("B", km_norte=1.5)])
    medidas = medir(paradas, un_lugar)
    esperado = haversine_km(
        paradas["lat"], paradas["lon"], LAT0, LON0
    ) * 1000
    assert medidas["metros"].to_numpy() == pytest.approx(esperado.to_numpy(), abs=1e-6)


# --------------------------------------------------- el identificador no es el código
def test_el_lugar_mas_cercano_se_devuelve_por_posicion_no_por_codigo():
    """Dos locales distintos con el mismo código deben quedar distinguibles.

    Es el defecto que apareció al resolver el caso: con `codigo` como identificador,
    dos estaciones de Metro de la misma línea son indistinguibles, y la comparación
    entre métodos subestima en silencio cuántas paradas cambian de local.
    """
    lugares = tabla_de_lugares([
        {"lat": LAT0, "lon": LON0, "codigo": "L1", "nombre": "Estación A"},
        {"lat": LAT0, "lon": LON0 + 3 * GRADO_LON_KM, "codigo": "L1",
         "nombre": "Estación B"},
    ])
    paradas = pd.DataFrame([parada("CERCA_A"), parada("CERCA_B", km_este=3.0)])
    medidas = medir(paradas, lugares)
    assert medidas["lugar"].to_list() == [0, 1]
    assert medidas["nombre_lugar"].to_list() == ["Estación A", "Estación B"]


def test_informe_de_identificador_delata_el_codigo_repetido():
    lugares = tabla_de_lugares([
        {"lat": LAT0, "lon": LON0, "codigo": "L1", "tipo_local": "Estación de Metro"},
        {"lat": LAT0, "lon": LON0, "codigo": "L1", "tipo_local": "Estación de Metro"},
        {"lat": LAT0, "lon": LON0, "codigo": "P7", "tipo_local": "Punto bip!"},
    ])
    informe = informe_de_identificador(lugares).set_index("tipo_local")
    assert informe.loc["Estación de Metro", "sirve_de_llave"] == "no"
    assert informe.loc["Estación de Metro", "codigos_repetidos"] == 1
    assert informe.loc["Punto bip!", "sirve_de_llave"] == "sí"
    assert informe.loc["TOTAL", "filas"] == 3
    assert informe.loc["TOTAL", "sirve_de_llave"] == "no"


# ------------------------------------------------------------------ umbral y rodeo
def test_la_cobertura_no_puede_bajar_al_subir_el_umbral(un_lugar):
    paradas = pd.DataFrame([parada(f"P{i}", km_este=i * 0.1) for i in range(20)])
    tabla = cobertura_por_umbral(medir(paradas, un_lugar))
    assert tabla["umbral_m"].to_list() == list(UMBRALES_M)
    assert tabla["cobertura_pct"].is_monotonic_increasing
    assert (tabla["es_referencia"] == "sí").sum() == 1
    assert tabla.loc[tabla["es_referencia"] == "sí", "umbral_m"].iloc[0] == UMBRAL_M


def test_el_umbral_de_referencia_lleva_su_cita():
    """La cifra no se sostiene sola: el código guarda de dónde viene."""
    assert UMBRAL_M == 300.0
    assert "300 m" in CITA_UMBRAL
    assert "DTPM" in CITA_UMBRAL
    assert "caminata" in CITA_UMBRAL


def test_rodear_nunca_mejora_la_cobertura(un_lugar):
    paradas = pd.DataFrame([parada(f"P{i}", km_este=i * 0.05) for i in range(20)])
    tabla = sensibilidad_rodeo(medir(paradas, un_lugar))
    assert tabla["factor_rodeo"].to_list() == list(FACTORES_RODEO)
    assert tabla["cobertura_pct"].is_monotonic_decreasing
    assert tabla["puntos_vs_linea_recta"].iloc[0] == 0.0
    assert (tabla["puntos_vs_linea_recta"] <= 0).all()


def test_rodear_equivale_a_encoger_el_umbral(un_lugar):
    """Identidad que mantiene honesta la implementación: `d·f ≤ u` ⇔ `d ≤ u/f`.

    Si alguna vez el factor se aplicara de otro modo —por ejemplo al umbral y a la
    distancia a la vez— esta prueba lo detecta.
    """
    paradas = pd.DataFrame([parada(f"P{i}", km_este=i * 0.03) for i in range(40)])
    medidas = medir(paradas, un_lugar)
    rodeo = sensibilidad_rodeo(medidas, umbral=UMBRAL_M, factores=(1.3,))
    equivalente = cobertura_por_umbral(medidas, umbrales=(UMBRAL_M / 1.3,))
    assert rodeo["paradas_cubiertas"].iloc[0] == equivalente["paradas_cubiertas"].iloc[0]


def test_el_factor_de_rodeo_no_fija_un_valor_unico():
    """La constante es una curva, no una estimación. 1,0 tiene que estar: es el piso."""
    assert len(FACTORES_RODEO) >= 3
    assert FACTORES_RODEO[0] == 1.0
    assert all(f >= 1.0 for f in FACTORES_RODEO)


# --------------------------------------------------------------- el denominador
def test_cargar_paradas_descarta_lo_que_no_es_parada(tmp_path):
    feed = _feed_sintetico(tmp_path)
    paradas = cargar_paradas(feed)
    assert paradas["stop_id"].to_list() == ["P1", "P2", "P3"]
    assert paradas["lat"].notna().all()


def test_informe_de_paradas_explica_cada_fila_descartada(tmp_path):
    informe = informe_de_paradas(_feed_sintetico(tmp_path))
    assert informe["filas"].sum() == 6
    entra = informe[informe["entra_al_denominador"] == "sí"]
    assert entra["filas"].sum() == 3
    nodo = informe[informe["location_type"] == "3"].iloc[0]
    assert nodo["con_coordenada"] == 0
    assert "pasillo" in nodo["significado"]


def test_el_campo_vacio_de_location_type_cuenta_como_parada(tmp_path):
    """La especificación GTFS dice que vacío equivale a 0. P3 lo trae vacío."""
    paradas = cargar_paradas(_feed_sintetico(tmp_path))
    assert "P3" in paradas["stop_id"].to_list()


def test_las_paradas_lejanas_se_listan_y_no_se_descartan(un_lugar):
    paradas = pd.DataFrame([
        parada("CERCA", km_este=0.1),
        parada("LEJOS", km_este=5.0),
        parada("LEJISIMOS", km_este=40.0),
    ])
    medidas = medir(paradas, un_lugar)
    fuera = paradas_fuera_de_alcance(medidas)
    assert fuera["stop_id"].to_list() == ["LEJISIMOS", "LEJOS"]
    assert fuera["metros"].is_monotonic_decreasing
    # Siguen en la medición: excluirlas es una decisión de quien lee, no del cálculo.
    assert len(medidas) == 3


def test_el_denominador_se_informa_de_las_dos_formas(un_lugar):
    paradas = pd.DataFrame(
        [parada(f"C{i}", km_este=0.1) for i in range(9)] + [parada("LEJOS", km_este=10)]
    )
    tabla = resumen_con_y_sin_lejanas(medir(paradas, un_lugar))
    assert len(tabla) == 2
    assert tabla["paradas"].to_list() == [10, 9]
    assert tabla["cubiertas"].to_list() == [9, 9]
    assert tabla["cobertura_pct"].to_list() == [90.0, 100.0]
    assert RADIO_DE_ALCANCE_M == 3000.0


# ------------------------------------------------------------------- desagregación
def test_la_rejilla_ignora_las_celdas_con_pocas_paradas(un_lugar):
    """Una celda con tres paradas da 0 % o 100 %, que no informa de nada."""
    cercanas = [parada(f"C{i}", km_este=0.01 * i) for i in range(MINIMO_POR_CELDA + 5)]
    solitaria = [parada("SOLA", km_norte=20.0)]
    medidas = medir(pd.DataFrame(cercanas + solitaria), un_lugar)
    rejilla = por_rejilla(medidas)
    assert (rejilla["paradas"] >= MINIMO_POR_CELDA).all()
    assert "SOLA" not in " ".join(rejilla["parada_mas_lejana"])


def test_la_rejilla_ordena_las_peores_celdas_primero(un_lugar):
    # Todas en el mismo punto: con un desplazamiento minimo las paradas se reparten
    # entre dos celdas vecinas y ninguna alcanza el minimo, que fue el primer fallo
    # de esta prueba.
    lejos = [parada(f"L{i}", km_norte=10.0) for i in range(MINIMO_POR_CELDA)]
    cerca = [parada(f"C{i}", km_este=0.0) for i in range(MINIMO_POR_CELDA)]
    rejilla = por_rejilla(medir(pd.DataFrame(lejos + cerca), un_lugar))
    assert len(rejilla) == 2
    assert rejilla["cobertura_pct"].iloc[0] == 0.0
    assert rejilla["cobertura_pct"].iloc[1] == 100.0
    assert rejilla["cobertura_pct"].is_monotonic_increasing


def test_la_celda_se_asigna_por_el_piso_de_la_coordenada(un_lugar):
    """Comprobable a mano: −33,45 con paso 0,01 cae en la celda −33,45."""
    medidas = medir(pd.DataFrame([parada("A")] * MINIMO_POR_CELDA), un_lugar)
    rejilla = por_rejilla(medidas)
    assert rejilla["celda_lat"].iloc[0] == pytest.approx(
        np.floor(LAT0 / PASO_REJILLA) * PASO_REJILLA, abs=1e-9
    )


def test_por_tipo_de_lugar_cuenta_locales_y_paradas():
    lugares = tabla_de_lugares([
        {"lat": LAT0, "lon": LON0, "tipo_local": "Estación de Metro"},
        {"lat": LAT0, "lon": LON0 + 5 * GRADO_LON_KM, "tipo_local": "Retail"},
    ])
    paradas = pd.DataFrame([
        parada("A", km_este=0.1), parada("B", km_este=0.2),
        parada("C", km_este=5.0),
    ])
    tabla = por_tipo_de_lugar(medir(paradas, lugares), lugares).set_index("tipo_local")
    assert tabla.loc["Estación de Metro", "paradas"] == 2
    assert tabla.loc["Retail", "paradas"] == 1
    assert tabla.loc["Retail", "locales"] == 1
    assert tabla["cobertura_pct"].max() <= 100.0


# ------------------------------------------------------- los límites, medidos
def test_el_proxy_de_comuna_marca_sus_propios_artefactos():
    """La comuna del local lejano no es la comuna de la parada, y se dice."""
    lugares = tabla_de_lugares([
        {"lat": LAT0, "lon": LON0, "comuna_etiqueta": "Santiago"},
        {"lat": LAT0 + 30 * GRADO_LAT_KM, "lon": LON0, "comuna_etiqueta": "Paine"},
    ])
    paradas = pd.DataFrame(
        [parada(f"C{i}", km_este=0.05) for i in range(MINIMO_ATRIBUIDAS + 2)]
        + [parada("REMOTA", km_norte=22.0)]
    )
    proxy = sesgo_del_proxy_de_comuna(medir(paradas, lugares), lugares)
    proxy = proxy.set_index("comuna_del_lugar_cercano")
    assert proxy.loc["Paine", "paradas_atribuidas"] == 1
    assert proxy.loc["Paine", "es_artefacto"] == "probable"
    assert proxy.loc["Paine", "mediana_m"] > 5000
    assert proxy.loc["Santiago", "es_artefacto"] == "no"
    # Las peores primero, que es donde está el artefacto.
    assert proxy["cobertura_pct"].is_monotonic_increasing


def test_la_cobertura_sin_horario_se_cuenta_aparte():
    """Una parada «cubierta» por un local de horario desconocido es un supuesto."""
    lugares = tabla_de_lugares([
        {"lat": LAT0, "lon": LON0, "horario": "09:00 a 18:00"},
        {"lat": LAT0, "lon": LON0 + 2 * GRADO_LON_KM, "horario": pd.NA},
    ])
    paradas = pd.DataFrame([parada("CON", km_este=0.05), parada("SIN", km_este=1.95)])
    tabla = limite_por_horario(medir(paradas, lugares)).set_index("indicador")["valor"]
    assert tabla["con_horario_conocido"] == 1
    assert tabla["con_horario_conocido_pct"] == 50.0
    assert tabla["cubiertas_con_horario"] == 1
    # SIN esta a 50 m de su local: cubierta, y no se sabe si abre. Es el caso que la
    # funcion existe para contar.
    assert tabla["cubiertas_sin_horario"] == 1


def test_el_horario_en_blanco_no_cuenta_como_conocido():
    """Una cadena de espacios no es un horario, y `notna()` sola no lo detecta."""
    lugares = tabla_de_lugares([{"lat": LAT0, "lon": LON0, "horario": "   "}])
    tabla = limite_por_horario(
        medir(pd.DataFrame([parada("A")]), lugares)
    ).set_index("indicador")["valor"]
    assert tabla["con_horario_conocido"] == 0


# ----------------------------------------------------------------------- resumen
def test_el_resumen_declara_unidad_y_definicion_de_cada_cifra(un_lugar):
    paradas = pd.DataFrame([parada(f"P{i}", km_este=i * 0.1) for i in range(10)])
    tabla = resumen(medir(paradas, un_lugar), un_lugar)
    assert list(tabla.columns) == ["indicador", "valor", "unidad", "definicion"]
    assert (tabla["definicion"].str.len() > 10).all()
    assert (tabla["unidad"].str.len() > 0).all()
    fila = tabla.set_index("indicador")
    assert fila.loc["pares_calculados", "valor"] == 10 * 1
    assert fila.loc["cobertura_rodeo_13_pct", "valor"] <= fila.loc[
        "cobertura_linea_recta_pct", "valor"
    ]


def test_la_distribucion_informa_la_cola_y_no_solo_la_media(un_lugar):
    paradas = pd.DataFrame(
        [parada(f"C{i}", km_este=0.1) for i in range(99)] + [parada("LEJOS", km_este=50)]
    )
    tabla = distribucion(medir(paradas, un_lugar)).set_index("estadistico")["metros"]
    assert tabla["paradas medidas"] == 100
    assert tabla["P50"] == pytest.approx(100.0, abs=2.0)
    assert tabla["media"] > tabla["P50"]     # la cola arrastra la media
    assert tabla["máximo"] == pytest.approx(50000.0, rel=0.01)


# -------------------------------------------------------------------------- fixture
def _feed_sintetico(carpeta: Path) -> Path:
    """Un `stops.txt` mínimo con la jerarquía de `location_type` del feed real.

    Reproduce que los tipos 3 y 4 vienen **sin coordenadas**, que es lo que hace que
    contarlos como paradas produzca filas sin cobertura que no son paradas.
    """
    destino = carpeta / "feed.zip"
    with zipfile.ZipFile(destino, "w") as zf:
        zf.writestr("stops.txt",
            "stop_id,stop_name,stop_lat,stop_lon,location_type\n"
            "P1,Parada uno,-33.45,-70.66,0\n"
            "P2,Parada dos,-33.46,-70.67,0\n"
            "P3,Parada sin tipo,-33.47,-70.68,\n"
            "E1,Estacion,-33.44,-70.65,1\n"
            "N1,Nodo de pasillo,,,3\n"
            "B1,Area de abordaje,,,4\n"
        )
    return destino
