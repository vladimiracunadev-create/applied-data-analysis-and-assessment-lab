"""Indicadores y estadística descriptiva con denominadores y métodos explícitos.

Qué hace
    Implementa las operaciones que más errores producen en una evaluación técnica:
    razones con denominador cero, tasas ponderadas frente a promedios de porcentajes,
    percentiles con método declarado y detección de valores atípicos.

Por qué existe
    `suma/suma` y `promedio de porcentajes` no son lo mismo, y un percentil cambia de
    valor según el método de interpolación. Tener una sola implementación documentada
    evita discrepancias entre el informe, el Excel y el código.

Fórmulas
    Media aritmética:        x̄ = (1/n) · Σ xᵢ                      [unidad de x]
    Tasa ponderada:          r  = 100 · Σ aᵢ / Σ bᵢ                 [%]
    Promedio de tasas:       r̄  = (1/n) · Σ (100 · aᵢ / bᵢ)         [%]
    Percentil lineal (q):    posición h = (n − 1) · q, interpolación entre ⌊h⌋ y ⌈h⌉
    Rango intercuartílico:   IQR = P75 − P25
    Límites de atípicos:     [P25 − k·IQR, P75 + k·IQR], k = 1.5 por convención de Tukey

Cómo se valida
    `tests/test_metrics.py` compara contra valores calculados a mano y contra
    `numpy.percentile`, y comprueba el comportamiento con denominador cero.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

#: Métodos de percentil admitidos, con el nombre que usa numpy.
PERCENTILE_METHODS = ("linear", "lower", "higher", "nearest", "midpoint")


def safe_ratio(
    numerator: float | pd.Series,
    denominator: float | pd.Series,
    scale: float = 1.0,
) -> float | pd.Series:
    """Razón que devuelve NaN cuando el denominador es cero o nulo.

    Args:
        numerator: numerador.
        denominator: denominador.
        scale: factor de escala (use 100 para porcentajes).

    Returns:
        `scale * numerator / denominator`, o NaN donde el denominador no es válido.

    Example:
        >>> safe_ratio(1, 0)
        nan
        >>> safe_ratio(30, 40, scale=100)
        75.0
    """
    num_es_serie = isinstance(numerator, pd.Series)
    den_es_serie = isinstance(denominator, pd.Series)
    if num_es_serie or den_es_serie:
        # Al mezclar serie y escalar hay que difundir el escalar sobre el índice de la
        # serie. Envolverlo con `pd.Series(escalar)` crea una serie de un solo elemento
        # con índice 0, y la división alinea por índice: todas las filas salvo la
        # primera quedarían en NaN sin que nada avise.
        indice = numerator.index if num_es_serie else denominator.index  # type: ignore[union-attr]
        num = numerator if num_es_serie else pd.Series(numerator, index=indice)
        den = denominator if den_es_serie else pd.Series(denominator, index=indice)
        den = pd.to_numeric(den, errors="coerce")
        return scale * pd.to_numeric(num, errors="coerce") / den.where(den != 0)
    try:
        den = float(denominator)
    except (TypeError, ValueError):
        return float("nan")
    if den == 0 or np.isnan(den):
        return float("nan")
    return scale * float(numerator) / den


def percentile(series: pd.Series, q: float, method: str = "linear") -> float:
    """Percentil de una serie, declarando el método de interpolación.

    Args:
        series: valores; los nulos se descartan.
        q: cuantil en el intervalo [0, 1].
        method: uno de `PERCENTILE_METHODS`.

    Raises:
        ValueError: si `q` está fuera de [0, 1] o el método no es admitido.
    """
    if not 0.0 <= q <= 1.0:
        raise ValueError(f"El cuantil debe estar entre 0 y 1; recibido {q!r}.")
    if method not in PERCENTILE_METHODS:
        raise ValueError(f"Método inválido: {method!r}. Use {PERCENTILE_METHODS}.")
    values = pd.to_numeric(pd.Series(series), errors="coerce").dropna().to_numpy()
    if values.size == 0:
        return float("nan")
    return float(np.quantile(values, q, method=method))


def describe_numeric(series: pd.Series, unit: str = "") -> pd.DataFrame:
    """Estadística descriptiva completa de una serie numérica.

    Incluye cobertura (cuántos valores se pudieron usar), que es lo que permite
    interpretar honestamente una media calculada sobre datos incompletos.
    """
    raw = pd.Series(series)
    values = pd.to_numeric(raw, errors="coerce")
    usable = values.dropna()
    n = int(usable.size)
    rows = [
        ("filas", len(raw), ""),
        ("valores_usables", n, ""),
        ("cobertura_pct", safe_ratio(n, len(raw), scale=100) if len(raw) else float("nan"), "%"),
        ("media", float(usable.mean()) if n else float("nan"), unit),
        ("desviacion_estandar", float(usable.std(ddof=1)) if n > 1 else float("nan"), unit),
        ("minimo", float(usable.min()) if n else float("nan"), unit),
        ("p25", percentile(usable, 0.25) if n else float("nan"), unit),
        ("mediana", percentile(usable, 0.50) if n else float("nan"), unit),
        ("p75", percentile(usable, 0.75) if n else float("nan"), unit),
        ("p90", percentile(usable, 0.90) if n else float("nan"), unit),
        ("maximo", float(usable.max()) if n else float("nan"), unit),
        ("iqr", (percentile(usable, 0.75) - percentile(usable, 0.25)) if n else float("nan"), unit),
    ]
    return pd.DataFrame(rows, columns=["indicador", "valor", "unidad"])


@dataclass(frozen=True)
class RateComparison:
    """Comparación entre tasa ponderada y promedio simple de tasas.

    Attributes:
        weighted: 100 · Σa / Σb. Es la tasa del conjunto.
        simple: promedio de las tasas individuales. Da peso igual a cada fila.
        difference: `weighted - simple`, expresada en puntos porcentuales.
    """

    weighted: float
    simple: float
    difference: float


def compare_rates(numerator: pd.Series, denominator: pd.Series) -> RateComparison:
    """Calcula la tasa ponderada y el promedio simple, y su diferencia.

    Por qué importa: el promedio simple de porcentajes trata igual a una unidad con
    10 observaciones y a otra con 10 000. Cuando ambos difieren, hay que informar
    cuál se usó y por qué. La diferencia se expresa en *puntos porcentuales*, no en
    porcentaje.
    """
    num = pd.to_numeric(pd.Series(numerator), errors="coerce")
    den = pd.to_numeric(pd.Series(denominator), errors="coerce")
    weighted = safe_ratio(num.sum(), den.sum(), scale=100)
    per_row = safe_ratio(num, den, scale=100)
    simple = float(per_row.mean()) if per_row.notna().any() else float("nan")
    weighted = float(weighted)
    return RateComparison(weighted=weighted, simple=simple, difference=weighted - simple)


def outliers_iqr(series: pd.Series, k: float = 1.5) -> pd.Series:
    """Marca valores atípicos por el criterio de Tukey.

    Args:
        series: valores a evaluar.
        k: multiplicador del IQR; 1.5 señala atípicos, 3.0 atípicos extremos.

    Returns:
        Serie booleana alineada con el índice original. Los nulos devuelven False,
        porque un valor ausente no es un valor atípico: es un valor ausente.
    """
    if k < 0:
        raise ValueError("El multiplicador k no puede ser negativo.")
    values = pd.to_numeric(pd.Series(series), errors="coerce")
    q1, q3 = percentile(values, 0.25), percentile(values, 0.75)
    if np.isnan(q1) or np.isnan(q3):
        return pd.Series(False, index=values.index)
    iqr = q3 - q1
    low, high = q1 - k * iqr, q3 + k * iqr
    return ((values < low) | (values > high)).fillna(False)


def coverage(series: pd.Series) -> float:
    """Porcentaje de valores no nulos y convertibles a número."""
    raw = pd.Series(series)
    if len(raw) == 0:
        return float("nan")
    usable = pd.to_numeric(raw, errors="coerce").notna().sum()
    return float(safe_ratio(usable, len(raw), scale=100))


def indicator_table(rows: dict[str, tuple[float, str, str]]) -> pd.DataFrame:
    """Construye una tabla de indicadores con unidad y definición.

    Args:
        rows: `{nombre: (valor, unidad, definición)}`.

    Un indicador sin unidad ni definición no es auditable; esta función obliga a
    declarar ambas al construir la tabla.
    """
    data = [
        {"indicador": name, "valor": value, "unidad": unit, "definicion": definition}
        for name, (value, unit, definition) in rows.items()
    ]
    return pd.DataFrame(data, columns=["indicador", "valor", "unidad", "definicion"])
