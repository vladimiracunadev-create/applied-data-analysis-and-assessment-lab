"""Interpretación de horarios de atención escritos en texto libre.

Qué hace
    Convierte una cadena como `«Lun a Vie 06:00 a 23:00 Sab 07:00 a 23:00 Dom y
    Festivos 08:00 a 23:00»` en intervalos de apertura por día de la semana, y permite
    preguntar si un momento dado cae dentro.

Por qué existe
    Un campo de horario escrito por personas es el caso habitual en datos
    administrativos: aparece en catastros de locales, en directorios de sucursales, en
    registros de atención de público. Y es un campo que **no se puede usar como texto**:
    para cruzarlo con cualquier otra cosa hay que interpretarlo.

    La alternativa —leerlo a ojo y clasificar a mano— no escala y no se puede auditar.

La decisión que gobierna todo el módulo
    Lo que no se entiende es **desconocido**, nunca «cerrado».

    Es la decisión que distingue un intérprete honesto de uno que produce cifras
    cómodas. Si una cadena no se puede interpretar, `parse_schedule` devuelve un
    horario sin intervalos y lo deja marcado: `is_open` responde `None`, no `False`.
    Tratar lo ilegible como cerrado convierte un vacío de datos en una afirmación sobre
    el mundo, y lo hace en la dirección que infla el problema.

    Por eso `is_open` tiene tres respuestas y no dos: `True`, `False` y `None`.

Lo que NO hace, declarado
    - **No resuelve festivos.** Los textos distinguen «Domingos y festivos», y saber si
      una fecha es festivo exige un calendario de feriados. `lab.calendars` lo tiene;
      este módulo recibe el día de la semana y un indicador opcional de festivo, y no
      los averigua por su cuenta.
    - **No infiere lo que no está.** Un texto que solo menciona «Lun a Vie» no dice
      nada del sábado: el sábado queda desconocido, no cerrado.
    - **No adivina por parecido.** Cada patrón de día y de hora está declarado en una
      tabla. Una variante nueva no se interpreta: se informa como no interpretada, para
      que alguien la agregue mirando el dato.

Cómo se valida
    `tests/test_schedules.py` prueba cada patrón declarado, los casos límite (medianoche,
    cruce de medianoche, intervalos invertidos) y la regla central: que lo ilegible
    devuelva `None` y no `False`.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

import pandas as pd

#: Días de la semana en la convención de `datetime`: lunes es 0, domingo es 6.
LUNES, MARTES, MIERCOLES, JUEVES, VIERNES, SABADO, DOMINGO = range(7)

#: Nombres de día admitidos, ya normalizados (sin tildes, en minúsculas). El orden
#: importa: las formas largas van antes que las cortas para que `domingo` no se
#: interprete como `dom` seguido de basura.
NOMBRES_DE_DIA: dict[str, int] = {
    "lunes": LUNES, "lun": LUNES, "lu": LUNES,
    "martes": MARTES, "mar": MARTES, "ma": MARTES,
    "miercoles": MIERCOLES, "mie": MIERCOLES, "mi": MIERCOLES,
    "jueves": JUEVES, "jue": JUEVES, "ju": JUEVES,
    "viernes": VIERNES, "vie": VIERNES, "vi": VIERNES,
    "sabados": SABADO, "sabado": SABADO, "sab": SABADO, "sa": SABADO,
    "domingos": DOMINGO, "domingo": DOMINGO, "dom": DOMINGO, "do": DOMINGO,
}

#: Palabras que marcan los días festivos. No son un día de la semana: son una
#: condición sobre la fecha, y se guardan aparte.
NOMBRES_DE_FESTIVO: tuple[str, ...] = ("festivos", "festivo", "fest", "feriados", "feriado")

#: Separadores que significan «desde … hasta …» entre dos días.
_RANGO = r"(?:\s*(?:-|a|hasta|al)\s*)"

#: Separadores que significan «y también» entre dos días.
_UNION = r"(?:\s*(?:y|,|/|\+|e)\s*)"

_DIAS_ALT = "|".join(sorted(NOMBRES_DE_DIA, key=len, reverse=True))
_FEST_ALT = "|".join(sorted(NOMBRES_DE_FESTIVO, key=len, reverse=True))

#: Un rango de días: `lun a vie`, `lun-dom`, `lunes al viernes`.
_PATRON_RANGO_DIAS = re.compile(rf"\b({_DIAS_ALT}){_RANGO}({_DIAS_ALT})\b")

#: Un día suelto o una unión de días y festivos: `sab`, `dom y festivos`, `festivos`.
_PATRON_DIA_O_FESTIVO = re.compile(rf"\b({_DIAS_ALT}|{_FEST_ALT})\b")

#: Un rango de horas: `08:00-21:00`, `6:00 a 23:00`, `8 a 14 horas`.
_PATRON_HORAS = re.compile(
    r"\b(\d{1,2})(?::(\d{2}))?\s*(?:-|a|hasta|al)\s*(\d{1,2})(?::(\d{2}))?\b"
)

#: Expresiones que declaran atención continua.
_PATRON_CONTINUO = re.compile(r"24\s*(?:horas|hrs|h)\b|24/7|todo\s+el\s+dia|continuado")

SEGUNDOS_POR_DIA = 86400


def _es_nulo(valor: object) -> bool:
    """Si el valor es ausencia de dato, en cualquiera de las formas en que pandas la trae.

    Hay que preguntarlo así y no con `isinstance(valor, float) and pd.isna(valor)`:
    una columna de tipo `string` trae `pd.NA`, que no es un `float`. Con la versión
    estrecha, `pd.NA` llegaba al normalizador, se convertía en la cadena `«<NA>»` y
    terminaba informado como «no se reconoce ningún rango de horas» en lugar de «sin
    dato». Son 1 579 registros del archivo real: el motivo equivocado en la tabla de
    calidad justamente donde está el hallazgo.
    """
    if valor is None:
        return True
    try:
        return bool(pd.isna(valor))
    except (TypeError, ValueError):
        return False


def _normalizar(texto: object) -> str:
    """Minúsculas, sin tildes, con los separadores reducidos a un espacio."""
    if _es_nulo(texto):
        return ""
    plano = unicodedata.normalize("NFKD", str(texto))
    plano = "".join(c for c in plano if not unicodedata.combining(c))
    plano = plano.lower().replace(":", ":")
    # Los dos puntos de las horas se conservan; el resto de la puntuación se separa.
    plano = re.sub(r"[.;()]", " ", plano)
    return re.sub(r"\s+", " ", plano).strip()


@dataclass(frozen=True)
class Schedule:
    """Horario interpretado: intervalos de apertura por día de la semana.

    Attributes:
        intervals: `{día_de_la_semana: [(inicio_s, fin_s), …]}`, en segundos desde la
            medianoche del propio día. Un día ausente del diccionario es **desconocido**,
            no cerrado.
        holiday_intervals: intervalos que el texto declara para los días festivos.
        source: el texto original, para poder rastrear cualquier resultado.
        parsed: si se pudo interpretar algo. `False` significa desconocido.
        note: por qué no se pudo interpretar, cuando corresponda.
    """

    intervals: dict[int, tuple[tuple[int, int], ...]] = field(default_factory=dict)
    holiday_intervals: tuple[tuple[int, int], ...] = ()
    source: str = ""
    parsed: bool = False
    note: str = ""

    @property
    def known_days(self) -> tuple[int, ...]:
        """Los días de la semana sobre los que el texto dice algo."""
        return tuple(sorted(self.intervals))

    def opens_at(self, weekday: int) -> int | None:
        """La hora de apertura más temprana de ese día, en segundos. `None` si no se sabe."""
        tramos = self.intervals.get(weekday)
        return min(inicio for inicio, _ in tramos) if tramos else None

    def closes_at(self, weekday: int) -> int | None:
        """La hora de cierre más tardía de ese día, en segundos. `None` si no se sabe."""
        tramos = self.intervals.get(weekday)
        return max(fin for _, fin in tramos) if tramos else None


def _horas_a_segundos(hora: str, minuto: str | None) -> int:
    return int(hora) * 3600 + (int(minuto) if minuto else 0) * 60


def _extraer_horas(fragmento: str) -> tuple[tuple[int, int], ...]:
    """Todos los rangos de horas de un fragmento, en segundos.

    Un rango invertido —`22:00 a 02:00`— se interpreta como cruce de medianoche y se
    parte en dos: hasta el final del día y desde el comienzo. Es la lectura correcta
    para un local nocturno, y la única que no produce un intervalo vacío.
    """
    if _PATRON_CONTINUO.search(fragmento):
        return ((0, SEGUNDOS_POR_DIA),)
    tramos: list[tuple[int, int]] = []
    for h1, m1, h2, m2 in _PATRON_HORAS.findall(fragmento):
        inicio = _horas_a_segundos(h1, m1)
        fin = _horas_a_segundos(h2, m2)
        if not (0 <= inicio <= SEGUNDOS_POR_DIA and 0 <= fin <= SEGUNDOS_POR_DIA):
            continue
        if fin == inicio:
            continue
        if fin < inicio:
            tramos.append((inicio, SEGUNDOS_POR_DIA))
            tramos.append((0, fin))
        else:
            tramos.append((inicio, fin))
    return tuple(sorted(set(tramos)))


def _dias_del_fragmento(fragmento: str) -> tuple[tuple[int, ...], bool]:
    """Los días que nombra un fragmento, y si menciona los festivos.

    Un rango `lun a vie` se expande; `lun-dom` da los siete. Un rango que va hacia
    atrás en la semana —`sab a lun`— se envuelve, que es la lectura habitual.
    """
    dias: set[int] = set()
    festivo = any(re.search(rf"\b{p}\b", fragmento) for p in NOMBRES_DE_FESTIVO)

    restante = fragmento
    for desde, hasta in _PATRON_RANGO_DIAS.findall(fragmento):
        a, b = NOMBRES_DE_DIA[desde], NOMBRES_DE_DIA[hasta]
        if a <= b:
            dias.update(range(a, b + 1))
        else:
            dias.update(list(range(a, 7)) + list(range(0, b + 1)))
        restante = restante.replace(f"{desde}", " ", 1).replace(f"{hasta}", " ", 1)

    for nombre in _PATRON_DIA_O_FESTIVO.findall(restante):
        if nombre in NOMBRES_DE_DIA:
            dias.add(NOMBRES_DE_DIA[nombre])
    return tuple(sorted(dias)), festivo


def _partir_en_tramos(texto: str) -> list[str]:
    """Corta el texto donde empieza una nueva mención de días.

    `«Lun a Vie 06:00 a 23:00 Sab 07:00 a 23:00»` son dos tramos. El corte se hace en
    cada nombre de día que aparece **después** de un rango de horas, porque ahí es
    donde empieza a hablarse de otro día.
    """
    if not texto:
        return []
    limites = [0]
    for coincidencia in _PATRON_HORAS.finditer(texto):
        resto = texto[coincidencia.end():]
        siguiente = _PATRON_DIA_O_FESTIVO.search(resto)
        if siguiente:
            limites.append(coincidencia.end() + siguiente.start())
    limites.append(len(texto))
    # strict=False a propósito: se recorren los límites por pares consecutivos, de
    # modo que la segunda lista es siempre un elemento más corta.
    pares = zip(limites, limites[1:], strict=False)
    tramos = [texto[a:b].strip() for a, b in pares if texto[a:b].strip()]
    return tramos or [texto]


def parse_schedule(texto: object) -> Schedule:
    """Interpreta un horario de atención escrito en texto libre.

    Args:
        texto: la cadena tal como viene en el dato. Puede ser nula o vacía.

    Returns:
        Un `Schedule`. Si no se pudo interpretar, `parsed` es `False`, `intervals`
        está vacío y `note` dice por qué. **Nunca** se devuelve un horario cerrado
        como resultado de no haber entendido.

    Example:
        >>> h = parse_schedule("Lun a Vie 06:00 a 23:00 Sab 07:00 a 23:00")
        >>> h.opens_at(LUNES), h.closes_at(LUNES)
        (21600, 82800)
        >>> h.intervals.get(DOMINGO) is None   # el texto no habla del domingo
        True
    """
    original = "" if _es_nulo(texto) else str(texto)
    plano = _normalizar(texto)
    if not plano:
        return Schedule(source=original, parsed=False, note="sin dato")

    intervalos: dict[int, set[tuple[int, int]]] = {}
    festivos: set[tuple[int, int]] = set()
    visto_algo = False

    for tramo in _partir_en_tramos(plano):
        horas = _extraer_horas(tramo)
        if not horas:
            continue
        dias, es_festivo = _dias_del_fragmento(tramo)
        if not dias and not es_festivo:
            continue
        visto_algo = True
        for dia in dias:
            intervalos.setdefault(dia, set()).update(horas)
        if es_festivo:
            festivos.update(horas)

    if not visto_algo:
        tiene_horas = bool(_PATRON_HORAS.search(plano)) or bool(_PATRON_CONTINUO.search(plano))
        nota = (
            "se reconocen horas pero no a qué días corresponden" if tiene_horas
            else "no se reconoce ningún rango de horas"
        )
        return Schedule(source=original, parsed=False, note=nota)

    return Schedule(
        intervals={d: tuple(sorted(v)) for d, v in sorted(intervalos.items())},
        holiday_intervals=tuple(sorted(festivos)),
        source=original,
        parsed=True,
    )


def is_open(
    horario: Schedule,
    weekday: int,
    second: int,
    holiday: bool = False,
) -> bool | None:
    """Si el local está abierto ese día a esa hora. `None` cuando no se sabe.

    Args:
        horario: salida de `parse_schedule`.
        weekday: día de la semana, lunes 0 a domingo 6.
        second: segundos desde la medianoche de ese día, de 0 a 86 399.
        holiday: si la fecha es festiva. Entonces manda el tramo de festivos, cuando el
            texto lo declara.

    Returns:
        `True`, `False`, o `None` si el horario no se pudo interpretar o no dice nada
        de ese día. La tercera respuesta es la que hay que propagar: un indicador que
        la convierta en `False` afirma algo que el dato no respalda.

    Raises:
        ValueError: si el día o el segundo están fuera de rango.
    """
    if not 0 <= weekday <= 6:
        raise ValueError(f"Día de la semana inválido: {weekday}. Debe estar entre 0 y 6.")
    if not 0 <= second < SEGUNDOS_POR_DIA:
        raise ValueError(f"Segundo inválido: {second}. Debe estar entre 0 y {SEGUNDOS_POR_DIA - 1}.")
    if not horario.parsed:
        return None

    tramos = horario.holiday_intervals if holiday else horario.intervals.get(weekday)
    if holiday and not tramos:
        tramos = horario.intervals.get(weekday)
    if not tramos:
        return None
    return any(inicio <= second < fin for inicio, fin in tramos)


def covers_window(
    horario: Schedule,
    weekday: int,
    start: int,
    end: int,
    holiday: bool = False,
) -> bool | None:
    """Si el local está abierto en **algún** momento de la ventana `[start, end)`.

    Es la pregunta que necesita un indicador de cobertura: no «¿está abierto a esta
    hora exacta?» sino «¿sirve de algo durante este rango?».

    Returns:
        `True`, `False` o `None`. Igual que `is_open`, `None` se propaga.

    Raises:
        ValueError: si la ventana está vacía o fuera de rango.
    """
    if not 0 <= start < end <= SEGUNDOS_POR_DIA:
        raise ValueError(f"Ventana inválida: [{start}, {end}).")
    if not horario.parsed:
        return None
    tramos = horario.holiday_intervals if holiday else horario.intervals.get(weekday)
    if holiday and not tramos:
        tramos = horario.intervals.get(weekday)
    if not tramos:
        return None
    return any(inicio < end and start < fin for inicio, fin in tramos)


def parse_series(series: pd.Series) -> pd.Series:
    """Interpreta una columna de horarios. Devuelve una serie de `Schedule`.

    Interpreta cada **texto distinto** una vez y reparte el resultado. En el archivo
    real son 348 valores con solo 10 textos diferentes, de modo que la deduplicación
    evita el 97 % del trabajo; y en un archivo donde los textos sean todos distintos no
    cuesta nada.
    """
    textos = pd.Series(series).astype("object")
    unicos = {t: parse_schedule(t) for t in textos.drop_duplicates()}
    return textos.map(unicos)


def parse_report(series: pd.Series) -> pd.DataFrame:
    """Qué se pudo interpretar y qué no, un texto por fila.

    Es el entregable de calidad del módulo: antes de usar un horario interpretado hay
    que poder mostrar cuánto del campo se entendió, y qué quedó fuera con su motivo.
    Las filas no interpretadas van primero, porque son las que hay que mirar.
    """
    textos = pd.Series(series).astype("object")
    filas = []
    for texto, cuenta in textos.value_counts(dropna=False).items():
        horario = parse_schedule(texto)
        filas.append({
            "texto": "" if pd.isna(texto) else str(texto).replace("\n", " ⏎ "),
            "registros": int(cuenta),
            "interpretado": "sí" if horario.parsed else "no",
            "dias_declarados": len(horario.known_days),
            "declara_festivos": "sí" if horario.holiday_intervals else "no",
            "motivo": horario.note,
        })
    vacios = int(textos.isna().sum() + (textos.astype("string").str.strip() == "").sum())
    tabla = pd.DataFrame(filas)
    tabla = tabla.sort_values(
        ["interpretado", "registros"], ascending=[True, False]
    ).reset_index(drop=True)
    tabla.attrs["sin_dato"] = vacios
    return tabla


def coverage(series: pd.Series) -> float:
    """Porcentaje de registros cuyo horario se pudo interpretar."""
    horarios = parse_series(series)
    if len(horarios) == 0:
        return float("nan")
    return float(sum(h.parsed for h in horarios) / len(horarios) * 100)
