"""Pruebas de inferencia estadística (`lab.stats`).

Las distribuciones se contrastan con valores de tablas estadísticas publicadas, que
es la única forma honesta de validar una implementación propia de funciones
especiales: si coincide con la tabla en varios puntos, la implementación es correcta;
si solo es consistente consigo misma, no se ha probado nada.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from lab.stats import (
    chi2_sf,
    chi_square_independence,
    incomplete_beta,
    mean_ci,
    normal_cdf,
    normal_quantile,
    pearson_test,
    proportion_ci,
    regularized_gamma_p,
    results_frame,
    t_cdf,
    t_quantile,
    welch_t_test,
)


# --------------------------------------------------------------------- distribuciones
def test_normal_cdf_en_puntos_conocidos():
    assert normal_cdf(0.0) == pytest.approx(0.5)
    assert normal_cdf(1.0) == pytest.approx(0.8413447461, abs=1e-9)
    assert normal_cdf(1.96) == pytest.approx(0.9750021049, abs=1e-9)
    assert normal_cdf(-1.0) == pytest.approx(1 - normal_cdf(1.0), abs=1e-12)


def test_normal_quantile_es_la_inversa_de_la_cdf():
    assert normal_quantile(0.975) == pytest.approx(1.959963985, abs=1e-7)
    assert normal_quantile(0.5) == pytest.approx(0.0, abs=1e-9)
    for p in (0.001, 0.02, 0.3, 0.7, 0.98, 0.999):
        assert normal_cdf(normal_quantile(p)) == pytest.approx(p, abs=1e-9)


def test_normal_quantile_rechaza_probabilidades_fuera_del_intervalo_abierto():
    for p in (0.0, 1.0, -0.1, 1.5):
        with pytest.raises(ValueError):
            normal_quantile(p)


def test_t_cdf_contra_tabla_publicada():
    # Valores de tabla: P(T <= 2) con 10 gl = 0.963306; con 1 gl = 0.852416.
    assert t_cdf(2.0, 10) == pytest.approx(0.963306, abs=1e-6)
    assert t_cdf(2.0, 1) == pytest.approx(0.852416, abs=1e-6)
    assert t_cdf(0.0, 7) == pytest.approx(0.5, abs=1e-12)
    assert t_cdf(-2.0, 10) == pytest.approx(1 - t_cdf(2.0, 10), abs=1e-12)


def test_t_quantile_contra_valores_criticos_clasicos():
    # Columna de 97.5 % de la tabla t de Student.
    esperados = {1: 12.7062, 2: 4.3027, 5: 2.5706, 10: 2.2281, 30: 2.0423, 120: 1.9799}
    for gl, critico in esperados.items():
        assert t_quantile(0.975, gl) == pytest.approx(critico, abs=5e-5)


def test_t_tiende_a_la_normal_al_crecer_los_grados_de_libertad():
    assert t_quantile(0.975, 10_000) == pytest.approx(normal_quantile(0.975), abs=1e-3)


def test_t_cdf_rechaza_grados_de_libertad_no_positivos():
    with pytest.raises(ValueError, match="positivos"):
        t_cdf(1.0, 0)


def test_chi2_sf_contra_valores_criticos_al_5_por_ciento():
    criticos = {1: 3.841459, 2: 5.991465, 3: 7.814728, 9: 16.918978, 20: 31.410433}
    for gl, valor in criticos.items():
        assert chi2_sf(valor, gl) == pytest.approx(0.05, abs=1e-6)


def test_chi2_sf_es_monotona_y_acotada():
    assert chi2_sf(0.0, 3) == 1.0
    assert chi2_sf(-5.0, 3) == 1.0
    assert chi2_sf(1.0, 3) > chi2_sf(10.0, 3) > chi2_sf(100.0, 3) >= 0.0


def test_funciones_especiales_validan_su_dominio():
    assert incomplete_beta(2.0, 3.0, 0.0) == 0.0
    assert incomplete_beta(2.0, 3.0, 1.0) == 1.0
    assert incomplete_beta(1.0, 1.0, 0.3) == pytest.approx(0.3, abs=1e-12)
    with pytest.raises(ValueError):
        incomplete_beta(2.0, 3.0, 1.5)
    with pytest.raises(ValueError):
        incomplete_beta(0.0, 3.0, 0.5)
    assert regularized_gamma_p(2.0, 0.0) == 0.0
    with pytest.raises(ValueError):
        regularized_gamma_p(2.0, -1.0)


# --------------------------------------------------------------------------- pruebas
def test_mean_ci_calculado_a_mano():
    # x = [1..5]: media 3, s = 1.5811, SE = 0.7071, t(0.975, 4) = 2.7764.
    estimacion = mean_ci([1, 2, 3, 4, 5])
    assert estimacion.value == pytest.approx(3.0)
    assert estimacion.n == 5
    medio = 2.776445 * 1.5811388 / math.sqrt(5)
    assert estimacion.lower == pytest.approx(3.0 - medio, abs=1e-4)
    assert estimacion.upper == pytest.approx(3.0 + medio, abs=1e-4)


def test_mean_ci_mas_confianza_implica_intervalo_mas_ancho():
    datos = [2, 4, 6, 8, 10, 12]
    estrecho = mean_ci(datos, confidence=0.90)
    ancho = mean_ci(datos, confidence=0.99)
    assert (ancho.upper - ancho.lower) > (estrecho.upper - estrecho.lower)


def test_mean_ci_exige_al_menos_dos_observaciones():
    with pytest.raises(ValueError, match="al menos 2"):
        mean_ci([5])
    with pytest.raises(ValueError, match="al menos 2"):
        mean_ci([None, "x"])


def test_proportion_ci_wilson_en_un_caso_publicado():
    # 40 de 100 con 95 %: intervalo de Wilson ≈ [0.3094, 0.4980].
    estimacion = proportion_ci(40, 100)
    assert estimacion.value == pytest.approx(0.40)
    assert estimacion.lower == pytest.approx(0.3094, abs=1e-4)
    assert estimacion.upper == pytest.approx(0.4980, abs=1e-4)


def test_proportion_ci_no_sale_del_intervalo_cero_uno():
    for exitos in (0, 1, 4, 5):
        estimacion = proportion_ci(exitos, 5)
        assert 0.0 <= estimacion.lower <= estimacion.upper <= 1.0


def test_proportion_ci_valida_sus_argumentos():
    with pytest.raises(ValueError, match="positivo"):
        proportion_ci(0, 0)
    with pytest.raises(ValueError, match="entre 0"):
        proportion_ci(11, 10)


def test_welch_t_test_calculado_a_mano():
    resultado = welch_t_test([1, 2, 3, 4, 5], [6, 7, 8, 9, 10])
    # Ambas muestras tienen varianza 2.5 y n = 5: t = -5/sqrt(1) = -5, gl = 8.
    assert resultado.statistic == pytest.approx(-5.0)
    assert resultado.df == pytest.approx(8.0)
    assert resultado.p_value == pytest.approx(0.00105283, abs=1e-7)
    assert resultado.significant(0.05)
    assert not resultado.significant(0.0001)


def test_welch_detecta_la_ausencia_de_diferencia():
    resultado = welch_t_test([5, 6, 7, 8], [5, 6, 7, 8])
    assert resultado.statistic == pytest.approx(0.0)
    assert resultado.p_value == pytest.approx(1.0)


def test_welch_valida_entradas_degeneradas():
    with pytest.raises(ValueError, match="al menos 2"):
        welch_t_test([1], [1, 2, 3])
    with pytest.raises(ValueError, match="constantes"):
        welch_t_test([3, 3, 3], [3, 3, 3])


def test_significant_rechaza_alpha_invalido():
    resultado = welch_t_test([1, 2, 3], [4, 5, 6])
    with pytest.raises(ValueError, match="alpha"):
        resultado.significant(1.5)


def test_pearson_test_en_relacion_lineal_perfecta_y_en_una_parcial():
    perfecto = pearson_test([1, 2, 3, 4], [2, 4, 6, 8])
    assert perfecto.effect == pytest.approx(1.0)
    assert perfecto.p_value == 0.0

    parcial = pearson_test([1, 2, 3, 4, 5], [2, 4, 5, 4, 5])
    assert parcial.effect == pytest.approx(0.7745966692, abs=1e-9)
    assert parcial.p_value == pytest.approx(0.1240270627, abs=1e-9)


def test_pearson_no_detecta_relacion_no_lineal_y_lo_dejamos_documentado():
    # Relación cuadrática simétrica: r ≈ 0 aunque la relación sea determinista.
    x = [-3, -2, -1, 0, 1, 2, 3]
    y = [v * v for v in x]
    assert pearson_test(x, y).effect == pytest.approx(0.0, abs=1e-12)


def test_pearson_valida_entradas():
    with pytest.raises(ValueError, match="al menos 3"):
        pearson_test([1, 2], [1, 2])
    with pytest.raises(ValueError, match="constante"):
        pearson_test([1, 1, 1], [1, 2, 3])


def test_chi_square_independence_calculado_a_mano():
    tabla = pd.DataFrame([[20, 30], [30, 20]], index=["a", "b"], columns=["x", "y"])
    resultado = chi_square_independence(tabla)
    assert resultado.statistic == pytest.approx(4.0)
    assert resultado.df == 1
    assert resultado.p_value == pytest.approx(0.0455002639, abs=1e-9)
    assert resultado.effect == pytest.approx(0.2)  # V de Cramér


def test_chi_square_detecta_independencia():
    tabla = pd.DataFrame([[25, 25], [25, 25]])
    resultado = chi_square_independence(tabla)
    assert resultado.statistic == pytest.approx(0.0)
    assert resultado.p_value == pytest.approx(1.0)


def test_chi_square_rechaza_frecuencias_esperadas_pequenas():
    with pytest.raises(ValueError, match="menores que 5"):
        chi_square_independence(pd.DataFrame([[1, 2], [3, 4]]))


def test_chi_square_valida_la_forma_y_el_contenido_de_la_tabla():
    with pytest.raises(ValueError, match="al menos 2 filas"):
        chi_square_independence(pd.DataFrame([[10, 20]]))
    with pytest.raises(ValueError, match="negativos"):
        chi_square_independence(pd.DataFrame([[-10, 20], [30, 40]]))
    with pytest.raises(ValueError, match="vacía"):
        chi_square_independence(pd.DataFrame([[0, 0], [0, 0]]))


def test_results_frame_reune_pruebas_y_soporta_el_caso_vacio():
    pruebas = [welch_t_test([1, 2, 3], [4, 5, 6]), pearson_test([1, 2, 3], [1, 2, 4])]
    tabla = results_frame(pruebas)
    assert len(tabla) == 2
    assert {"prueba", "hipotesis_nula", "valor_p", "tamano_efecto"} <= set(tabla.columns)
    assert results_frame([]).empty
