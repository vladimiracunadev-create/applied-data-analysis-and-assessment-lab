"""Calendarios por reglas: construir el denominador de un indicador y auditarlo.

Qué hace
    Construye el conjunto de fechas que entran en la medición de un indicador a partir
    de **reglas declaradas**, y mide cuánto excluye cada regla por separado, cuánto
    excluye en exclusiva y cuánto se solapa con las demás.

Por qué existe
    El denominador de un indicador oficial casi nunca es «todos los días». Es una
    decisión documentada, y la documentación suele estar en una nota al pie. El índice
    de variación de tiempos de viaje del transporte público de Santiago, por ejemplo,
    declara **siete** reglas de exclusión encadenadas, una de las cuales descarta los
    días 28 y 29 de cada mes porque algunos incidentes empiezan la tarde anterior.

    Reconstruir ese calendario a mano es propenso a error y no se puede revisar. Con
    las reglas como objetos, el calendario se vuelve a generar, se audita y se compara
    entre años.

La exclusión marginal, que es el punto
    Siete reglas aplicadas en cadena excluyen menos días que la suma de lo que excluye
    cada una, porque se solapan. La **exclusión marginal** de una regla es cuántos días
    quedarían dentro si se quitara esa sola regla: es la medida de cuánto aporta de
    verdad. Una regla con exclusión marginal cero es redundante, y eso es información
    valiosa sobre la metodología que uno está reproduciendo.

Qué NO hace
    No conoce la legislación de ningún país. Los feriados se pasan como dato, con su
    fuente declarada. Lo único de calendario civil que implementa es el cálculo del
    Domingo de Pascua, porque es un algoritmo determinista y verificable que permite
    validar de forma independiente la parte movible de cualquier lista de feriados.

Cómo se valida
    `tests/test_calendars.py` comprueba el algoritmo de Pascua contra fechas publicadas
    de varios años, cada constructor de regla por separado, y que la exclusión marginal
    y el solapamiento cuadren con recuentos calculados a mano.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np
import pandas as pd

#: Días de la semana que por defecto se consideran no laborales (sábado y domingo),
#: en la numeración de pandas: lunes 0, domingo 6.
FIN_DE_SEMANA: tuple[int, ...] = (5, 6)

NOMBRES_DIA = ("lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo")


def easter_sunday(year: int) -> date:
    """Domingo de Pascua del año indicado, en el calendario gregoriano.

    Implementa el algoritmo gregoriano anónimo (Meeus/Jones/Butcher). Es aritmética
    entera exacta, sin tablas ni aproximaciones, de modo que sirve como **verificación
    independiente** de la parte movible de una lista de feriados: Viernes Santo es dos
    días antes y Sábado Santo uno.

    Args:
        year: año, entre 1583 y 4099, rango de validez del algoritmo.

    Raises:
        ValueError: si el año está fuera del rango de validez.

    Example:
        >>> easter_sunday(2026)
        datetime.date(2026, 4, 5)
    """
    if not 1583 <= year <= 4099:
        raise ValueError(
            f"Año fuera del rango de validez del algoritmo (1583–4099): {year}."
        )
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    el = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * el) // 451
    mes, dia = divmod(h + el - 7 * m + 114, 31)
    return date(year, mes, dia + 1)


@dataclass(frozen=True)
class DayRule:
    """Una regla de exclusión de días, con su procedencia declarada.

    Args:
        name: identificador corto, usado como nombre de columna.
        description: qué excluye, en palabras.
        exclude: función que recibe el índice de fechas y devuelve una máscara booleana
            con True en los días que la regla **excluye**.
        source: de dónde sale la regla. Una regla sin fuente no se puede defender.
    """

    name: str
    description: str
    exclude: Callable[[pd.DatetimeIndex], np.ndarray]
    source: str = ""

    def apply(self, fechas: pd.DatetimeIndex) -> np.ndarray:
        """Máscara de días excluidos por esta regla."""
        mascara = np.asarray(self.exclude(fechas), dtype=bool)
        if mascara.shape != (len(fechas),):
            raise ValueError(
                f"La regla {self.name!r} devolvió una máscara de forma {mascara.shape} "
                f"y se esperaba ({len(fechas)},)."
            )
        return mascara


# ------------------------------------------------------------- constructores de regla
def weekends(weekdays_off: Sequence[int] = FIN_DE_SEMANA, source: str = "") -> DayRule:
    """Excluye los días de la semana indicados. Por defecto, sábado y domingo."""
    dias = tuple(sorted(set(weekdays_off)))
    if any(d < 0 or d > 6 for d in dias):
        raise ValueError(f"Días de la semana inválidos: {dias}. Use 0 (lunes) a 6.")
    nombres = ", ".join(NOMBRES_DIA[d] for d in dias)
    return DayRule(
        name="fin_de_semana",
        description=f"Solo días laborales: se excluyen {nombres}",
        exclude=lambda f: np.isin(f.weekday, dias),
        source=source,
    )


def specific_dates(dates: Iterable[date | str], name: str, description: str,
                   source: str = "") -> DayRule:
    """Excluye una lista explícita de fechas.

    Es la regla para los feriados: la lista llega como **dato**, con su fuente, no
    codificada en el módulo.
    """
    conjunto = pd.DatetimeIndex(pd.to_datetime(list(dates))).normalize()
    return DayRule(
        name=name,
        description=description,
        exclude=lambda f: np.isin(f.normalize(), conjunto),
        source=source,
    )


def whole_months(months: Iterable[int], source: str = "") -> DayRule:
    """Excluye todos los días de los meses indicados (1 a 12)."""
    meses = tuple(sorted(set(months)))
    if any(m < 1 or m > 12 for m in meses):
        raise ValueError(f"Meses inválidos: {meses}. Use 1 a 12.")
    nombres = {1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo",
               6: "junio", 7: "julio", 8: "agosto", 9: "septiembre",
               10: "octubre", 11: "noviembre", 12: "diciembre"}
    return DayRule(
        name="meses_completos",
        description="Se excluyen todos los días de " + ", ".join(nombres[m] for m in meses),
        exclude=lambda f: np.isin(f.month, meses),
        source=source,
    )


def days_of_month(days: Iterable[int], name: str = "dias_del_mes",
                  description: str = "", source: str = "") -> DayRule:
    """Excluye los días indicados de **todos** los meses.

    Es la forma de la séptima regla del índice de tiempos de viaje: descartar los días
    28 y 29 de cada mes. Una regla así es fácil de pasar por alto y excluye alrededor
    del 6 % del año.
    """
    numeros = tuple(sorted(set(days)))
    if any(d < 1 or d > 31 for d in numeros):
        raise ValueError(f"Días del mes inválidos: {numeros}. Use 1 a 31.")
    texto = description or (
        "Se excluyen los días " + ", ".join(str(d) for d in numeros) + " de cada mes"
    )
    return DayRule(
        name=name,
        description=texto,
        exclude=lambda f: np.isin(f.day, numeros),
        source=source,
    )


def date_ranges(ranges: Iterable[tuple[date | str, date | str]], name: str,
                description: str, source: str = "") -> DayRule:
    """Excluye uno o más rangos de fechas, con ambos extremos incluidos."""
    pares = [(pd.Timestamp(a).normalize(), pd.Timestamp(b).normalize())
             for a, b in ranges]
    for inicio, fin in pares:
        if fin < inicio:
            raise ValueError(f"Rango invertido: {inicio.date()} a {fin.date()}.")

    def excluir(f: pd.DatetimeIndex) -> np.ndarray:
        normal = f.normalize()
        mascara = np.zeros(len(f), dtype=bool)
        for inicio, fin in pares:
            mascara |= (normal >= inicio) & (normal <= fin)
        return mascara

    return DayRule(name=name, description=description, exclude=excluir, source=source)


def weeks_containing(dates: Iterable[date | str], name: str, description: str,
                     source: str = "", week_start: int = 0) -> DayRule:
    """Excluye la semana completa que contiene cada una de las fechas indicadas.

    Es la forma de «la semana de fiestas patrias»: la regla no nombra días concretos,
    nombra una semana. Hay que decidir —y declarar— dónde empieza la semana, porque de
    eso dependen hasta dos días de diferencia.

    Args:
        dates: fechas ancla.
        week_start: día en que empieza la semana; 0 es lunes.
    """
    if not 0 <= week_start <= 6:
        raise ValueError(f"week_start inválido: {week_start}. Use 0 (lunes) a 6.")
    semanas: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    for valor in dates:
        ancla = pd.Timestamp(valor).normalize()
        desplazamiento = (ancla.weekday() - week_start) % 7
        inicio = ancla - pd.Timedelta(days=desplazamiento)
        semanas.append((inicio, inicio + pd.Timedelta(days=6)))

    def excluir(f: pd.DatetimeIndex) -> np.ndarray:
        normal = f.normalize()
        mascara = np.zeros(len(f), dtype=bool)
        for inicio, fin in semanas:
            mascara |= (normal >= inicio) & (normal <= fin)
        return mascara

    return DayRule(name=name, description=description, exclude=excluir, source=source)


def easter_relative(offsets: Iterable[int], years: Iterable[int], name: str,
                    description: str, source: str = "") -> DayRule:
    """Excluye días definidos como un desplazamiento respecto del Domingo de Pascua.

    `offsets=(-2, -1)` son Viernes Santo y Sábado Santo. Sirve para construir la parte
    movible de una lista de feriados **de forma verificable**, en lugar de copiarla.
    """
    fechas = [
        easter_sunday(anio) + timedelta(days=int(d))
        for anio in years
        for d in offsets
    ]
    return specific_dates(fechas, name=name, description=description, source=source)


# ------------------------------------------------------------------------ calendario
@dataclass
class Calendar:
    """Calendario construido, con una columna booleana por regla."""

    frame: pd.DataFrame
    rules: tuple[DayRule, ...] = field(default_factory=tuple)

    @property
    def included(self) -> pd.DataFrame:
        """Solo los días que entran en la medición."""
        return self.frame.loc[self.frame["incluido"]]

    def __len__(self) -> int:
        return len(self.frame)


def build_calendar(
    start: date | str, end: date | str, rules: Sequence[DayRule]
) -> Calendar:
    """Construye el calendario de medición entre dos fechas, ambas incluidas.

    Args:
        start: primera fecha del rango.
        end: última fecha del rango.
        rules: reglas de exclusión. El orden no afecta al resultado —la exclusión es
            la unión de todas— pero sí al orden de las columnas del informe.

    Returns:
        `Calendar` cuyo `frame` tiene una fila por día, con sus atributos de calendario,
        una columna booleana por regla y la columna `incluido`.

    Raises:
        ValueError: si el rango está invertido, si no hay reglas, o si dos reglas
            comparten nombre: dos columnas con el mismo nombre harían el informe
            ilegible.
    """
    inicio, fin = pd.Timestamp(start).normalize(), pd.Timestamp(end).normalize()
    if fin < inicio:
        raise ValueError(f"Rango invertido: {inicio.date()} a {fin.date()}.")
    if not rules:
        raise ValueError(
            "Un calendario de medición sin reglas es el rango completo; declare al "
            "menos una regla, aunque sea la de días laborales."
        )
    nombres = [r.name for r in rules]
    repetidos = sorted({n for n in nombres if nombres.count(n) > 1})
    if repetidos:
        raise ValueError(f"Reglas con nombre repetido: {repetidos}.")

    fechas = pd.date_range(inicio, fin, freq="D")
    marco = pd.DataFrame({
        "fecha": fechas,
        "anio": fechas.year,
        "mes": fechas.month,
        "dia": fechas.day,
        "dia_semana": fechas.weekday,
        "nombre_dia": [NOMBRES_DIA[d] for d in fechas.weekday],
    })
    excluido = np.zeros(len(fechas), dtype=bool)
    for regla in rules:
        mascara = regla.apply(fechas)
        marco[regla.name] = mascara
        excluido |= mascara
    marco["incluido"] = ~excluido
    return Calendar(frame=marco, rules=tuple(rules))


def exclusion_report(calendar: Calendar) -> pd.DataFrame:
    """Cuánto excluye cada regla: en bruto, en exclusiva y en solapamiento.

    Columnas:

    - `excluye`: días que la regla excluye por su cuenta.
    - `exclusiva`: días que **solo** esta regla excluye. Es su aporte real: si se
      quitara la regla, estos días volverían a entrar en la medición.
    - `solapada`: días que también excluye otra regla.
    - `aporte_pct`: la exclusión exclusiva sobre el total de días del rango.

    Una regla con `exclusiva = 0` es **redundante** dado el resto: su efecto ya está
    cubierto. Saberlo importa al reproducir una metodología ajena, porque indica que la
    regla puede existir por una razón histórica o por prudencia, no por su efecto.
    """
    marco = calendar.frame
    total = len(marco)
    if not calendar.rules:
        return pd.DataFrame(columns=["regla", "descripcion", "excluye", "exclusiva",
                                     "solapada", "aporte_pct", "fuente"])
    matrices = {r.name: marco[r.name].to_numpy() for r in calendar.rules}
    filas = []
    for regla in calendar.rules:
        propia = matrices[regla.name]
        otras = np.zeros(total, dtype=bool)
        for nombre, mascara in matrices.items():
            if nombre != regla.name:
                otras |= mascara
        exclusiva = int((propia & ~otras).sum())
        filas.append({
            "regla": regla.name,
            "descripcion": regla.description,
            "excluye": int(propia.sum()),
            "exclusiva": exclusiva,
            "solapada": int(propia.sum()) - exclusiva,
            "aporte_pct": round(100.0 * exclusiva / total, 2) if total else 0.0,
            "fuente": regla.source,
        })
    return pd.DataFrame(filas)


def overlap_matrix(calendar: Calendar) -> pd.DataFrame:
    """Cuántos días excluye cada par de reglas a la vez.

    La diagonal es el total de cada regla. Los valores fuera de la diagonal muestran
    dónde está la redundancia, que es lo que explica por qué siete reglas excluyen
    menos días que la suma de sus exclusiones.
    """
    nombres = [r.name for r in calendar.rules]
    matriz = pd.DataFrame(0, index=nombres, columns=nombres, dtype=int)
    for a in nombres:
        for b in nombres:
            matriz.loc[a, b] = int((calendar.frame[a] & calendar.frame[b]).sum())
    return matriz


def summary(calendar: Calendar) -> pd.DataFrame:
    """Resumen del calendario: cuántos días entran y cuántos salen."""
    marco = calendar.frame
    total = len(marco)
    incluidos = int(marco["incluido"].sum())
    laborales = int((~marco["dia_semana"].isin(FIN_DE_SEMANA)).sum())
    suma_de_reglas = int(sum(marco[r.name].sum() for r in calendar.rules))
    filas = [
        ("dias_del_rango", total, "días"),
        ("dias_laborales", laborales, "días"),
        ("dias_incluidos", incluidos, "días"),
        ("dias_excluidos", total - incluidos, "días"),
        ("inclusion_pct", round(100.0 * incluidos / total, 2) if total else 0.0, "%"),
        ("inclusion_sobre_laborales_pct",
         round(100.0 * incluidos / laborales, 2) if laborales else 0.0, "%"),
        ("suma_de_exclusiones_por_regla", suma_de_reglas, "días"),
        ("solapamiento_total", suma_de_reglas - (total - incluidos), "días"),
    ]
    return pd.DataFrame(filas, columns=["indicador", "valor", "unidad"])


def by_month(calendar: Calendar) -> pd.DataFrame:
    """Días incluidos por mes. Deja ver de un golpe qué meses quedan vacíos."""
    marco = calendar.frame
    tabla = (marco.groupby(["anio", "mes"])
                  .agg(dias=("fecha", "size"),
                       laborales=("dia_semana", lambda s: int((~s.isin(FIN_DE_SEMANA)).sum())),
                       incluidos=("incluido", "sum"))
                  .reset_index())
    tabla["incluidos"] = tabla["incluidos"].astype(int)
    tabla["inclusion_pct"] = np.where(
        tabla["laborales"] > 0,
        (100.0 * tabla["incluidos"] / tabla["laborales"]).round(2),
        np.nan,
    )
    return tabla


def intersect_with(calendar: Calendar, months: Iterable[int],
                   label: str = "mes_de_medicion") -> pd.DataFrame:
    """Cruza el calendario con los meses en que efectivamente se mide.

    Muchas metodologías combinan dos cosas que conviene no confundir: qué días son
    **elegibles** y en qué meses se **mide**. El índice de tiempos de viaje excluye
    enero, febrero y diciembre por regla, y además mide solo en marzo, junio,
    septiembre y noviembre. Cruzarlos revela cuánto de la primera regla era redundante
    con la segunda.
    """
    meses = tuple(sorted(set(months)))
    marco = calendar.frame.copy()
    marco[label] = marco["mes"].isin(meses)
    marco["medible"] = marco["incluido"] & marco[label]
    return marco
