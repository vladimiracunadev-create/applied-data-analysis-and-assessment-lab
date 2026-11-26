"""Pruebas de `lab.keys`: qué identifica una fila, y qué hacer cuando nada lo hace.

Qué se prueba
    Tablas pequeñas con la respuesta conocida de antemano, para que cada afirmación se
    pueda verificar leyendo el fixture:

    - la minimalidad de las claves devueltas, que es lo que hace la tabla legible;
    - el rechazo de columnas con nulos, porque dos ausencias no se distinguen;
    - el determinismo de la clave subrogada, que es su única razón de ser frente a un
      número de fila;
    - la detección de colisiones, que distingue el contenido repetido —legítimo— de dos
      contenidos distintos con el mismo identificador —un error que no se devuelve—.
"""

from __future__ import annotations

import pandas as pd
import pytest

from lab.keys import (
    LARGO_ID,
    MAX_COMBINACION,
    candidate_keys,
    key_report,
    surrogate_key,
    surrogate_report,
)


@pytest.fixture
def tabla() -> pd.DataFrame:
    """Cuatro filas donde `a + b` es la única clave mínima de dos columnas.

    - `a` se repite (x, x, y, y) y `b` también (1, 2, 1, 2);
    - `a + b` es única;
    - `c` no tiene repetidos pero **tiene un nulo**, de modo que no es clave;
    - `d` es constante.
    """
    return pd.DataFrame({
        "a": ["x", "x", "y", "y"],
        "b": [1, 2, 1, 2],
        "c": ["p", "q", "r", None],
        "d": [7, 7, 7, 7],
    })


# ------------------------------------------------------------- diagnóstico por columna
def test_el_informe_distingue_las_dos_causas(tabla):
    """Nulos y repetidos piden acciones distintas, de modo que se informan aparte."""
    informe = key_report(tabla).set_index("columna")
    assert informe.loc["a", "repetidos"] == 2
    assert informe.loc["a", "nulos"] == 0
    assert informe.loc["a", "por_que_no"] == "tiene valores repetidos"
    assert informe.loc["c", "nulos"] == 1
    assert "nulos" in informe.loc["c", "por_que_no"]
    assert informe.loc["d", "distintos"] == 1


def test_una_columna_sin_repetidos_pero_con_nulos_no_es_clave(tabla):
    """`c` tiene tres valores distintos en tres filas no nulas. Y no sirve."""
    informe = key_report(tabla).set_index("columna")
    assert informe.loc["c", "repetidos"] == 0
    assert informe.loc["c", "es_clave"] == "no"


def test_una_columna_realmente_unica_se_declara_clave():
    frame = pd.DataFrame({"id": [1, 2, 3], "otro": ["a", "a", "b"]})
    informe = key_report(frame).set_index("columna")
    assert informe.loc["id", "es_clave"] == "sí"
    assert informe.loc["id", "por_que_no"] == ""
    assert informe.loc["otro", "es_clave"] == "no"


def test_el_informe_pone_primero_lo_mas_cercano_a_una_clave():
    frame = pd.DataFrame({"malo": [1, 1, 1], "bueno": [1, 2, 3]})
    informe = key_report(frame)
    assert informe["columna"].iloc[0] == "bueno"


def test_el_informe_rechaza_una_columna_inexistente(tabla):
    with pytest.raises(ValueError, match="No existen"):
        key_report(tabla, ["a", "inexistente"])


# ------------------------------------------------------- búsqueda de claves candidatas
def test_encuentra_la_clave_minima_y_solo_la_minima(tabla):
    """Si `a + b` es clave, `a + b + d` también. Devolver las dos no aporta nada."""
    candidatas = candidate_keys(tabla)
    assert list(candidatas["columnas"]) == ["a + b"]
    assert candidatas["tamano"].iloc[0] == 2


def test_una_columna_unica_gana_a_cualquier_combinacion():
    frame = pd.DataFrame({"id": [1, 2, 3], "a": ["x", "x", "y"], "b": [1, 2, 1]})
    candidatas = candidate_keys(frame)
    assert "id" in list(candidatas["columnas"])
    # `a + b` también es única, pero no contiene a `id`: las dos son mínimas.
    assert candidatas["tamano"].min() == 1
    assert candidatas["tamano"].is_monotonic_increasing


def test_las_columnas_con_nulos_no_entran_en_ninguna_clave(tabla):
    """`c` no aparece en ninguna candidata, aunque sea casi única."""
    candidatas = candidate_keys(tabla)
    assert all("c" not in columnas for columnas in candidatas["columnas"])


def test_sin_clave_posible_devuelve_una_tabla_vacia_con_columnas():
    """Que no haya clave es un resultado, no un fallo."""
    frame = pd.DataFrame({"a": [1, 1], "b": ["x", "x"]})
    candidatas = candidate_keys(frame)
    assert candidatas.empty
    assert list(candidatas.columns) == ["columnas", "tamano", "combinaciones_evaluadas"]


def test_el_tope_de_tamano_se_respeta():
    """Con `max_size=1` no se evalúan combinaciones, por mucho que existan."""
    frame = pd.DataFrame({"a": ["x", "x", "y"], "b": [1, 2, 1]})
    assert candidate_keys(frame, max_size=1).empty
    assert not candidate_keys(frame, max_size=2).empty
    assert MAX_COMBINACION >= 2


def test_rechaza_un_tope_invalido(tabla):
    with pytest.raises(ValueError, match="max_size"):
        candidate_keys(tabla, max_size=0)


def test_rechaza_una_columna_inexistente(tabla):
    with pytest.raises(ValueError, match="No existen"):
        candidate_keys(tabla, ["a", "fantasma"])


def test_una_tabla_de_una_fila_tiene_cualquier_columna_como_clave():
    """Caso límite que conviene no dejar sin probar."""
    frame = pd.DataFrame({"a": ["x"], "b": [1]})
    candidatas = candidate_keys(frame)
    assert set(candidatas["columnas"]) == {"a", "b"}


# ----------------------------------------------------------------- clave subrogada
def test_el_identificador_es_determinista(tabla):
    """La única razón de ser frente a un número de fila: no depende de la ejecución."""
    primera = surrogate_key(tabla, ["a", "b"])
    segunda = surrogate_key(tabla, ["a", "b"])
    assert list(primera) == list(segunda)


def test_el_orden_de_las_columnas_declaradas_no_cambia_el_identificador(tabla):
    assert list(surrogate_key(tabla, ["a", "b"])) == list(surrogate_key(tabla, ["b", "a"]))


def test_el_identificador_no_depende_del_orden_de_las_filas(tabla):
    """Reordenar la tabla no debe cambiar la identidad de sus filas."""
    directo = surrogate_key(tabla, ["a", "b"])
    invertido = surrogate_key(tabla.iloc[::-1], ["a", "b"])
    assert set(directo) == set(invertido)
    assert directo.iloc[0] == invertido.iloc[-1]


def test_el_prefijo_y_el_largo_se_respetan(tabla):
    ids = surrogate_key(tabla, ["a", "b"], prefix="bip-", length=8)
    assert ids.str.startswith("bip-").all()
    assert (ids.str.len() == len("bip-") + 8).all()
    assert LARGO_ID == 16


def test_contenido_identico_comparte_identificador_y_eso_no_es_colision():
    """Dos filas iguales en los campos declarados SON el mismo registro."""
    frame = pd.DataFrame({"a": ["x", "x"], "b": [1, 1]})
    ids = surrogate_key(frame, ["a", "b"])
    assert ids.iloc[0] == ids.iloc[1]
    assert ids.nunique() == 1


def test_una_colision_real_levanta_error_en_lugar_de_devolver_duplicados():
    """Con un largo absurdo se fuerza una colisión, y no se devuelve una clave mala.

    Se buscan dos valores que choquen con cuatro caracteres hexadecimales. Si no se
    encuentran en el rango probado, la prueba se omite en lugar de dar un falso verde.
    """
    import hashlib

    vistos: dict[str, int] = {}
    par: tuple[int, int] | None = None
    for numero in range(200000):
        digesto = hashlib.sha256(str(numero).encode()).hexdigest()[:4]
        if digesto in vistos:
            par = (vistos[digesto], numero)
            break
        vistos[digesto] = numero
    if par is None:  # pragma: no cover
        pytest.skip("no se encontró una colisión de cuatro caracteres en el rango")

    frame = pd.DataFrame({"a": [str(par[0]), str(par[1])]})
    with pytest.raises(ValueError, match="colisión"):
        surrogate_key(frame, ["a"], length=4)


def test_el_separador_evita_colisiones_por_concatenacion():
    """Sin separador, `("ab", "c")` y `("a", "bc")` producirían la misma cadena."""
    frame = pd.DataFrame({"x": ["ab", "a"], "y": ["c", "bc"]})
    ids = surrogate_key(frame, ["x", "y"])
    assert ids.iloc[0] != ids.iloc[1]


def test_los_nulos_se_distinguen_de_la_cadena_vacia():
    frame = pd.DataFrame({"a": [None, ""], "b": ["x", "x"]})
    ids = surrogate_key(frame, ["a", "b"])
    assert ids.iloc[0] != ids.iloc[1]


@pytest.mark.parametrize("largo", [3, 65, 0, -1])
def test_rechaza_un_largo_fuera_de_rango(tabla, largo):
    with pytest.raises(ValueError, match="length"):
        surrogate_key(tabla, ["a", "b"], length=largo)


def test_rechaza_una_declaracion_de_identidad_vacia(tabla):
    with pytest.raises(ValueError, match="al menos una columna"):
        surrogate_key(tabla, [])


def test_rechaza_un_campo_de_identidad_inexistente(tabla):
    with pytest.raises(ValueError, match="No existen"):
        surrogate_key(tabla, ["a", "fantasma"])


def test_el_informe_de_la_subrogada_dice_si_la_identidad_distingue(tabla):
    informe = surrogate_report(tabla, ["a", "b"]).set_index("indicador")["valor"]
    assert informe["filas"] == 4
    assert informe["identificadores_distintos"] == 4
    assert informe["filas_con_identidad_repetida"] == 0
    assert informe["es_clave"] == "sí"
    assert informe["campos_declarados"] == "a + b"


def test_el_informe_delata_una_identidad_que_no_distingue(tabla):
    """Declarar solo `a` deja dos pares de filas indistinguibles, y se dice."""
    informe = surrogate_report(tabla, ["a"]).set_index("indicador")["valor"]
    assert informe["identificadores_distintos"] == 2
    assert informe["filas_con_identidad_repetida"] == 2
    assert informe["es_clave"] == "no"
