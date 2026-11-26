"""Fechas, horas y duraciones: el bloque donde más resultados se pierden.

Qué hace
    Convierte texto a fecha-hora con control de errores, calcula duraciones en
    minutos, deriva atributos de calendario y clasifica registros en bandas horarias
    operacionales (punta mañana, valle, punta tarde, nocturno).

Por qué existe
    Un CSV entrega fechas como texto. Si se restan sin convertir, el resultado es un
    error; si se convierten con `dayfirst` equivocado, el resultado es peor: un número
    plausible pero falso. Estas funciones dejan explícito el formato supuesto y
    reportan cuántos valores no se pudieron interpretar.

Fórmulas
    Duración en minutos:  d = (fin − inicio) / 60 s      [min]
    En Excel la misma operación es `(fin − inicio) * 1440`, porque Excel almacena
    fechas como días decimales y 1 día = 1440 minutos.

Cómo se valida
    `tests/test_dates.py` cubre formato ambiguo, duraciones negativas, bandas
    horarias en los límites y el equivalente de Excel.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

#: Bandas horarias por defecto: (nombre, hora_inicio_inclusive, hora_fin_exclusive).
#: Son bandas pedagógicas y genéricas; cada sistema de transporte define las suyas.
DEFAULT_BANDS: tuple[tuple[str, int, int], ...] = (
    ("nocturno", 0, 6),
    ("punta_manana", 6, 9),
    ("valle_manana", 9, 12),
    ("valle_tarde", 12, 17),
    ("punta_tarde", 17, 21),
    ("tarde_noche", 21, 24),
)

#: Minutos en un día. Factor de conversión entre el serial de Excel y los minutos.
MINUTES_PER_DAY = 1440


@dataclass(frozen=True)
class ParseResult:
    """Resultado de convertir una columna a fecha-hora.

    Attributes:
        values: serie convertida; los valores no interpretables quedan como NaT.
        invalid: cantidad de valores presentes que no se pudieron interpretar.
        empty: cantidad de valores originalmente vacíos o nulos.
    """

    values: pd.Series
    invalid: int
    empty: int

    @property
    def coverage_pct(self) -> float:
        total = len(self.values)
        if total == 0:
            return float("nan")
        return 100.0 * float(self.values.notna().sum()) / total


def parse_datetime(series: pd.Series, dayfirst: bool = False, fmt: str | None = None) -> ParseResult:
    """Convierte a fecha-hora informando qué se perdió en el camino.

    Args:
        series: columna de origen (texto, fecha o mezcla).
        dayfirst: True si el texto viene en formato día/mes/año, como es habitual en
            Chile y en buena parte de América Latina y Europa.
        fmt: formato explícito (`"%d-%m-%Y %H:%M"`). Si se conoce, úselo: es más
            rápido y elimina la ambigüedad entre día y mes.

    Returns:
        `ParseResult` con la serie convertida y el recuento de fallos.
    """
    raw = pd.Series(series)
    empty = int(raw.isna().sum() + (raw.astype("string").str.strip() == "").sum())
    if fmt:
        values = pd.to_datetime(raw, format=fmt, errors="coerce")
    else:
        values = pd.to_datetime(raw, dayfirst=dayfirst, errors="coerce", format="mixed")
    present = raw.notna() & (raw.astype("string").str.strip() != "")
    invalid = int((values.isna() & present).sum())
    return ParseResult(values=values, invalid=invalid, empty=empty)


def duration_minutes(start: pd.Series, end: pd.Series) -> pd.Series:
    """Duración en minutos entre dos series de fecha-hora.

    Devuelve NaN cuando falta alguno de los extremos. No corrige duraciones
    negativas: esa decisión pertenece al análisis, que debe declararla como
    exclusión y reportarla en el informe de calidad.
    """
    s = pd.to_datetime(pd.Series(start), errors="coerce")
    e = pd.to_datetime(pd.Series(end), errors="coerce")
    return (e - s).dt.total_seconds() / 60.0


def duration_minutes_excel(start_serial: pd.Series, end_serial: pd.Series) -> pd.Series:
    """Equivalente de `duration_minutes` usando el serial de días de Excel.

    Sirve para comprobar que la fórmula `(fin − inicio) * 1440` de la planilla y el
    cálculo de Python producen el mismo número.
    """
    s = pd.to_numeric(pd.Series(start_serial), errors="coerce")
    e = pd.to_numeric(pd.Series(end_serial), errors="coerce")
    return (e - s) * MINUTES_PER_DAY


def time_band(
    series: pd.Series, bands: tuple[tuple[str, int, int], ...] = DEFAULT_BANDS
) -> pd.Series:
    """Clasifica cada fecha-hora en una banda horaria.

    Args:
        series: fechas-hora.
        bands: tuplas `(nombre, desde_inclusive, hasta_exclusive)` en horas enteras.

    Returns:
        Serie de texto con el nombre de la banda; NaN si la fecha es nula.

    Raises:
        ValueError: si las bandas no cubren las 24 horas sin solaparse. Una
            clasificación con huecos produce registros silenciosamente perdidos.
    """
    _check_bands(bands)
    values = pd.to_datetime(pd.Series(series), errors="coerce")
    hours = values.dt.hour
    out = pd.Series(pd.NA, index=values.index, dtype="object")
    for name, start, end in bands:
        out = out.mask((hours >= start) & (hours < end), name)
    return out


def _check_bands(bands: tuple[tuple[str, int, int], ...]) -> None:
    covered = [False] * 24
    for name, start, end in bands:
        if not 0 <= start < end <= 24:
            raise ValueError(f"Banda {name!r} inválida: {start}–{end}.")
        for hour in range(start, end):
            if covered[hour]:
                raise ValueError(f"Las bandas se solapan en la hora {hour}.")
            covered[hour] = True
    if not all(covered):
        missing = [h for h, c in enumerate(covered) if not c]
        raise ValueError(f"Las bandas no cubren las horas {missing}.")


def calendar_features(series: pd.Series) -> pd.DataFrame:
    """Atributos de calendario derivados de una fecha-hora.

    Columnas: fecha, anio, mes, dia, dia_semana (0 = lunes), nombre_dia, es_fin_semana,
    hora, banda. Todas alineadas con el índice de entrada.
    """
    values = pd.to_datetime(pd.Series(series), errors="coerce")
    names = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    # `day_of_week` y no `weekday`: el segundo está obsoleto desde pandas 4 y el
    # filtro de advertencias del proyecto convierte esa obsolescencia en un error.
    weekday = values.dt.day_of_week
    return pd.DataFrame(
        {
            "fecha": values.dt.date,
            "anio": values.dt.year,
            "mes": values.dt.month,
            "dia": values.dt.day,
            "dia_semana": weekday,
            "nombre_dia": weekday.map(lambda d: names[int(d)] if pd.notna(d) else pd.NA),
            "es_fin_semana": weekday.isin([5, 6]),
            "hora": values.dt.hour,
            "banda": time_band(values),
        },
        index=values.index,
    )


def date_quality(series: pd.Series, dayfirst: bool = False) -> pd.DataFrame:
    """Informe de calidad de una columna de fecha-hora, listo para el entregable."""
    result = parse_datetime(series, dayfirst=dayfirst)
    values = result.values
    rows = [
        ("filas", len(values), ""),
        ("vacios", result.empty, ""),
        ("no_interpretables", result.invalid, ""),
        ("interpretadas", int(values.notna().sum()), ""),
        ("cobertura_pct", round(result.coverage_pct, 4), "%"),
        ("minimo", values.min() if values.notna().any() else pd.NaT, ""),
        ("maximo", values.max() if values.notna().any() else pd.NaT, ""),
    ]
    return pd.DataFrame(rows, columns=["indicador", "valor", "unidad"])
