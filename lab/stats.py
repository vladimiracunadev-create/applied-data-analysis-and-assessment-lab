"""Inferencia estadística sin dependencias externas, con fórmulas documentadas.

Qué hace
    Implementa intervalos de confianza y pruebas de hipótesis de uso frecuente:
    media con intervalo t, diferencia de medias de Welch, correlación de Pearson con
    valor p, proporción con intervalo de Wilson y prueba chi-cuadrado de
    independencia. Las distribuciones acumuladas se calculan con funciones
    especiales implementadas aquí (`math.lgamma`, `math.erf`), de modo que el módulo
    funciona sin SciPy.

Por qué existe
    El laboratorio exige validación estadística y no puede imponer SciPy en el
    entorno mínimo. Además, tener las fórmulas visibles permite explicarlas en el
    programa de aprendizaje en lugar de tratarlas como una caja negra.

Fórmulas principales
    Error estándar de la media:  SE = s / √n
    Intervalo de la media:       x̄ ± t_{1−α/2, n−1} · SE
    Welch (dos muestras):        t = (x̄₁ − x̄₂) / √(s₁²/n₁ + s₂²/n₂)
      grados de libertad:        ν = (s₁²/n₁ + s₂²/n₂)² / [ (s₁²/n₁)²/(n₁−1) + (s₂²/n₂)²/(n₂−1) ]
    Pearson:                     r = Σ(xᵢ−x̄)(yᵢ−ȳ) / √[Σ(xᵢ−x̄)² · Σ(yᵢ−ȳ)²]
      prueba:                    t = r · √((n−2)/(1−r²)),  ν = n − 2
    Wilson (proporción):         (p̂ + z²/2n ± z·√(p̂(1−p̂)/n + z²/4n²)) / (1 + z²/n)
    Chi-cuadrado:                χ² = Σ (Oᵢⱼ − Eᵢⱼ)² / Eᵢⱼ,  Eᵢⱼ = fila_i · col_j / N
      grados de libertad:        ν = (filas − 1)(columnas − 1)

Advertencia de interpretación
    Un valor p pequeño indica que los datos serían poco probables si la hipótesis
    nula fuese cierta. No mide el tamaño del efecto, no prueba causalidad y no
    sustituye el juicio sobre el diseño del estudio.

Cómo se valida
    `tests/test_stats.py` compara contra valores publicados en tablas estadísticas
    y contra resultados calculados a mano, y verifica propiedades (simetría,
    monotonía, límites) de las distribuciones implementadas.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

_MAX_ITER = 300
_EPS = 3.0e-15


# --------------------------------------------------------------------- funciones especiales
def _betacf(a: float, b: float, x: float) -> float:
    """Fracción continua de la función beta incompleta (algoritmo de Lentz)."""
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < 1.0e-30:
        d = 1.0e-30
    d = 1.0 / d
    h = d
    for m in range(1, _MAX_ITER + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < 1.0e-30:
            d = 1.0e-30
        c = 1.0 + aa / c
        if abs(c) < 1.0e-30:
            c = 1.0e-30
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < 1.0e-30:
            d = 1.0e-30
        c = 1.0 + aa / c
        if abs(c) < 1.0e-30:
            c = 1.0e-30
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < _EPS:
            return h
    raise ArithmeticError("La fracción continua de la beta incompleta no converge.")


def incomplete_beta(a: float, b: float, x: float) -> float:
    """Función beta incompleta regularizada I_x(a, b), con 0 ≤ x ≤ 1."""
    if not 0.0 <= x <= 1.0:
        raise ValueError(f"x debe estar en [0, 1]; recibido {x!r}.")
    if a <= 0 or b <= 0:
        raise ValueError("Los parámetros a y b deben ser positivos.")
    if x in (0.0, 1.0):
        return x
    front = math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log1p(-x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def _lower_gamma_series(a: float, x: float) -> float:
    total = 1.0 / a
    term = total
    for n in range(1, _MAX_ITER + 1):
        term *= x / (a + n)
        total += term
        if abs(term) < abs(total) * _EPS:
            return total * math.exp(-x + a * math.log(x) - math.lgamma(a))
    raise ArithmeticError("La serie de la gamma incompleta no converge.")


def _upper_gamma_cf(a: float, x: float) -> float:
    b = x + 1.0 - a
    c = 1.0 / 1.0e-30
    d = 1.0 / b
    h = d
    for i in range(1, _MAX_ITER + 1):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < 1.0e-30:
            d = 1.0e-30
        c = b + an / c
        if abs(c) < 1.0e-30:
            c = 1.0e-30
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < _EPS:
            return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h
    raise ArithmeticError("La fracción continua de la gamma incompleta no converge.")


def regularized_gamma_p(a: float, x: float) -> float:
    """Gamma incompleta inferior regularizada P(a, x). Es la CDF de una gamma(a, 1)."""
    if x < 0 or a <= 0:
        raise ValueError("Se requiere x ≥ 0 y a > 0.")
    if x == 0.0:
        return 0.0
    if x < a + 1.0:
        return _lower_gamma_series(a, x)
    return 1.0 - _upper_gamma_cf(a, x)


def normal_cdf(z: float) -> float:
    """Φ(z): probabilidad acumulada de la normal estándar."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def normal_quantile(p: float) -> float:
    """Inversa de Φ: cuantil de la normal estándar (algoritmo de Acklam, |ε| < 1e-9)."""
    if not 0.0 < p < 1.0:
        raise ValueError("p debe estar en (0, 1).")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        x = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    elif p <= phigh:
        q = p - 0.5
        r = q * q
        x = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
            (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    else:
        q = math.sqrt(-2 * math.log(1 - p))
        x = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    # Un paso de refinamiento de Halley sobre la CDF exacta.
    e = normal_cdf(x) - p
    u = e * math.sqrt(2 * math.pi) * math.exp(x * x / 2)
    return x - u / (1 + x * u / 2)


def t_cdf(t: float, df: float) -> float:
    """CDF de la t de Student con `df` grados de libertad."""
    if df <= 0:
        raise ValueError("Los grados de libertad deben ser positivos.")
    x = df / (df + t * t)
    tail = 0.5 * incomplete_beta(df / 2.0, 0.5, x)
    return 1.0 - tail if t > 0 else tail


def t_quantile(p: float, df: float) -> float:
    """Cuantil de la t de Student, por bisección sobre `t_cdf` (precisión 1e-10)."""
    if not 0.0 < p < 1.0:
        raise ValueError("p debe estar en (0, 1).")
    low, high = -1.0e3, 1.0e3
    for _ in range(200):
        mid = (low + high) / 2.0
        if t_cdf(mid, df) < p:
            low = mid
        else:
            high = mid
        if high - low < 1.0e-10:
            break
    return (low + high) / 2.0


def chi2_sf(x: float, df: float) -> float:
    """Cola superior de la chi-cuadrado: P(X > x). Es el valor p de la prueba."""
    if df <= 0:
        raise ValueError("Los grados de libertad deben ser positivos.")
    if x <= 0:
        return 1.0
    return 1.0 - regularized_gamma_p(df / 2.0, x / 2.0)


# ------------------------------------------------------------------------ resultados
@dataclass(frozen=True)
class Estimate:
    """Estimación puntual con intervalo de confianza."""

    value: float
    lower: float
    upper: float
    confidence: float
    n: int

    def __str__(self) -> str:  # pragma: no cover - presentación
        return (f"{self.value:.4f} (IC {self.confidence:.0%}: "
                f"{self.lower:.4f} a {self.upper:.4f}; n = {self.n})")


@dataclass(frozen=True)
class TestResult:
    """Resultado de una prueba de hipótesis.

    Attributes:
        statistic: valor del estadístico de prueba.
        p_value: probabilidad de observar un estadístico al menos tan extremo si la
            hipótesis nula fuese cierta.
        df: grados de libertad.
        name: nombre de la prueba.
        null_hypothesis: enunciado de la hipótesis nula, en palabras.
        effect: medida del tamaño del efecto, cuando aplica.
    """

    statistic: float
    p_value: float
    df: float
    name: str
    null_hypothesis: str
    effect: float | None = None

    def significant(self, alpha: float = 0.05) -> bool:
        """True si p < alpha. El umbral es una convención, no una verdad."""
        if not 0 < alpha < 1:
            raise ValueError("alpha debe estar en (0, 1).")
        return self.p_value < alpha

    def to_row(self) -> dict:
        return {
            "prueba": self.name,
            "hipotesis_nula": self.null_hypothesis,
            "estadistico": self.statistic,
            "gl": self.df,
            "valor_p": self.p_value,
            "tamano_efecto": self.effect,
        }


def _clean(series) -> np.ndarray:
    return pd.to_numeric(pd.Series(series), errors="coerce").dropna().to_numpy(dtype=float)


# ---------------------------------------------------------------------------- pruebas
def mean_ci(series, confidence: float = 0.95) -> Estimate:
    """Media con intervalo de confianza basado en la t de Student."""
    values = _clean(series)
    n = values.size
    if n < 2:
        raise ValueError("Se requieren al menos 2 observaciones válidas.")
    mean = float(values.mean())
    se = float(values.std(ddof=1)) / math.sqrt(n)
    crit = t_quantile(1 - (1 - confidence) / 2, n - 1)
    return Estimate(mean, mean - crit * se, mean + crit * se, confidence, n)


def proportion_ci(successes: int, trials: int, confidence: float = 0.95) -> Estimate:
    """Proporción con intervalo de Wilson, preferible al normal con n pequeño."""
    if trials <= 0:
        raise ValueError("El número de ensayos debe ser positivo.")
    if not 0 <= successes <= trials:
        raise ValueError("Los éxitos deben estar entre 0 y el número de ensayos.")
    p_hat = successes / trials
    z = normal_quantile(1 - (1 - confidence) / 2)
    denom = 1 + z * z / trials
    centre = (p_hat + z * z / (2 * trials)) / denom
    half = z * math.sqrt(p_hat * (1 - p_hat) / trials + z * z / (4 * trials * trials)) / denom
    return Estimate(p_hat, max(0.0, centre - half), min(1.0, centre + half), confidence, trials)


def welch_t_test(a, b) -> TestResult:
    """Diferencia de medias entre dos muestras independientes (prueba de Welch).

    No asume varianzas iguales, que es el caso habitual con datos operacionales.
    El tamaño del efecto reportado es la d de Cohen con desviación agrupada.
    """
    x, y = _clean(a), _clean(b)
    if x.size < 2 or y.size < 2:
        raise ValueError("Cada muestra necesita al menos 2 observaciones válidas.")
    vx, vy = x.var(ddof=1), y.var(ddof=1)
    nx, ny = x.size, y.size
    se2 = vx / nx + vy / ny
    if se2 == 0:
        raise ValueError("Ambas muestras son constantes: la prueba no está definida.")
    t = (x.mean() - y.mean()) / math.sqrt(se2)
    df = se2 ** 2 / ((vx / nx) ** 2 / (nx - 1) + (vy / ny) ** 2 / (ny - 1))
    p = 2 * (1 - t_cdf(abs(t), df))
    pooled = math.sqrt(((nx - 1) * vx + (ny - 1) * vy) / (nx + ny - 2))
    effect = (x.mean() - y.mean()) / pooled if pooled else float("nan")
    return TestResult(float(t), float(p), float(df), "t de Welch",
                      "Las dos poblaciones tienen la misma media.", float(effect))


def pearson_test(x, y) -> TestResult:
    """Correlación de Pearson y su prueba de significancia.

    Advertencia: r mide asociación lineal. Un r alto no implica causalidad, y un r
    cercano a cero no descarta una relación no lineal.
    """
    sx = pd.to_numeric(pd.Series(x), errors="coerce")
    sy = pd.to_numeric(pd.Series(y), errors="coerce")
    frame = pd.DataFrame({"x": sx, "y": sy}).dropna()
    n = len(frame)
    if n < 3:
        raise ValueError("Se requieren al menos 3 pares completos.")
    # Se comprueba antes de correlacionar: con una serie constante la desviación es
    # cero y el cociente de Pearson no está definido.
    if frame.x.std(ddof=1) == 0 or frame.y.std(ddof=1) == 0:
        raise ValueError("Una de las series es constante: r no está definido.")
    r = float(frame.x.corr(frame.y))
    if math.isnan(r):  # pragma: no cover - red de seguridad
        raise ValueError("No se pudo calcular r con los datos entregados.")
    if abs(r) >= 1.0:
        return TestResult(float("inf"), 0.0, n - 2, "Pearson",
                          "No existe asociación lineal entre las variables.", r)
    t = r * math.sqrt((n - 2) / (1 - r * r))
    p = 2 * (1 - t_cdf(abs(t), n - 2))
    return TestResult(float(t), float(p), n - 2, "Pearson",
                      "No existe asociación lineal entre las variables.", r)


def chi_square_independence(table: pd.DataFrame) -> TestResult:
    """Prueba chi-cuadrado de independencia sobre una tabla de contingencia.

    Args:
        table: recuentos observados; filas y columnas son las dos variables.

    El tamaño del efecto reportado es la V de Cramér, que normaliza χ² al intervalo
    [0, 1] y permite comparar tablas de distinto tamaño.

    Raises:
        ValueError: si hay celdas negativas, totales nulos, o si alguna frecuencia
            esperada es menor que 5, caso en que la aproximación chi-cuadrado no es
            fiable y corresponde una prueba exacta.
    """
    observed = table.to_numpy(dtype=float)
    if observed.ndim != 2 or min(observed.shape) < 2:
        raise ValueError("La tabla de contingencia necesita al menos 2 filas y 2 columnas.")
    if (observed < 0).any():
        raise ValueError("Los recuentos observados no pueden ser negativos.")
    total = observed.sum()
    if total == 0:
        raise ValueError("La tabla está vacía.")
    expected = observed.sum(axis=1, keepdims=True) @ observed.sum(axis=0, keepdims=True) / total
    if (expected < 5).any():
        raise ValueError(
            "Hay frecuencias esperadas menores que 5: la aproximación chi-cuadrado no "
            "es válida. Agrupe categorías o use una prueba exacta."
        )
    chi2 = float(((observed - expected) ** 2 / expected).sum())
    rows, cols = observed.shape
    df = (rows - 1) * (cols - 1)
    p = chi2_sf(chi2, df)
    cramer_v = math.sqrt(chi2 / (total * (min(rows, cols) - 1)))
    return TestResult(chi2, float(p), df, "Chi-cuadrado de independencia",
                      "Las dos variables son independientes.", cramer_v)


def results_frame(results: list[TestResult]) -> pd.DataFrame:
    """Reúne varios resultados de prueba en una tabla para el informe."""
    if not results:
        return pd.DataFrame(
            columns=["prueba", "hipotesis_nula", "estadistico", "gl", "valor_p", "tamano_efecto"]
        )
    return pd.DataFrame([r.to_row() for r in results])
