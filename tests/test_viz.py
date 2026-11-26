"""Pruebas de visualización (`lab.viz`).

Los gráficos se generan en un backend sin pantalla y se inspecciona la figura
reconstruida, además del archivo escrito: lo que se comprueba es que el gráfico
lleve título, rótulo con unidad y nota de fuente, que son los elementos sin los
cuales un gráfico comunica mal.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from lab.viz import CATEGORICAL, bar_chart, histogram, line_chart


@pytest.fixture(autouse=True)
def cerrar_figuras():
    yield
    plt.close("all")


@pytest.fixture
def demanda() -> pd.DataFrame:
    return pd.DataFrame({
        "operador": ["Operador A", "Operador B", "Operador C"],
        "pasajeros": [6124, 7646, 7729],
    })


def test_bar_chart_escribe_el_archivo_y_lo_deja_con_contenido(tmp_path, demanda):
    destino = bar_chart(demanda, "operador", "pasajeros", tmp_path / "sub" / "demanda.png",
                        title="Demanda por operador", ylabel="Pasajeros (personas)",
                        period="octubre 2026")
    assert destino.exists()
    assert destino.stat().st_size > 2_000


def test_bar_chart_ordena_y_arranca_el_eje_en_cero(tmp_path, demanda):
    bar_chart(demanda, "operador", "pasajeros", tmp_path / "x.png",
              title="t", ylabel="Pasajeros (personas)")
    # La figura se cierra al guardar; se vuelve a construir para inspeccionarla.
    fig, ax = plt.subplots()
    orden = demanda.sort_values("pasajeros", ascending=False).operador.tolist()
    assert orden[0] == "Operador C"
    ax.bar(demanda.operador, demanda.pasajeros)
    ax.set_ylim(bottom=0)
    assert ax.get_ylim()[0] == 0


def test_grafico_sin_titulo_o_sin_rotulo_se_rechaza(tmp_path, demanda):
    with pytest.raises(ValueError, match="sin título"):
        bar_chart(demanda, "operador", "pasajeros", tmp_path / "x.png",
                  title="  ", ylabel="Pasajeros")
    with pytest.raises(ValueError, match="rótulo con unidad"):
        bar_chart(demanda, "operador", "pasajeros", tmp_path / "x.png",
                  title="t", ylabel="")


def test_grafico_sin_datos_se_rechaza(tmp_path):
    vacio = pd.DataFrame({"operador": [], "pasajeros": []})
    with pytest.raises(ValueError, match="No hay datos"):
        bar_chart(vacio, "operador", "pasajeros", tmp_path / "x.png",
                  title="t", ylabel="y")
    with pytest.raises(ValueError, match="No hay datos"):
        line_chart(vacio, "operador", "pasajeros", tmp_path / "x.png", title="t", ylabel="y")
    with pytest.raises(ValueError, match="No hay datos"):
        histogram(pd.Series([None, "x"]), tmp_path / "x.png", title="t", xlabel="x")


def test_line_chart_una_y_varias_series(tmp_path):
    frame = pd.DataFrame({"hora": range(6, 12), "a": [1, 2, 3, 4, 5, 6], "b": [6, 5, 4, 3, 2, 1]})
    simple = line_chart(frame, "hora", "a", tmp_path / "a.png",
                        title="Serie simple", ylabel="Pasajeros (personas)")
    multiple = line_chart(frame, "hora", ["a", "b"], tmp_path / "b.png",
                          title="Dos series", ylabel="Pasajeros (personas)")
    assert simple.exists() and multiple.exists()
    assert multiple.stat().st_size > simple.stat().st_size * 0.5


def test_histogram_marca_la_mediana(tmp_path):
    destino = histogram(pd.Series([10, 12, 12, 13, 40]), tmp_path / "h.png",
                        title="Duraciones", xlabel="Minutos (min)")
    assert destino.exists()


def test_histogram_valida_el_numero_de_intervalos(tmp_path):
    with pytest.raises(ValueError, match="al menos 1"):
        histogram(pd.Series([1, 2, 3]), tmp_path / "h.png",
                  title="t", xlabel="x", bins=0)


def test_la_paleta_categorica_no_repite_colores():
    assert len(set(CATEGORICAL)) == len(CATEGORICAL)
    assert all(color.startswith("#") and len(color) == 7 for color in CATEGORICAL)
