"""Adquisición de datos con procedencia: de dónde salió cada archivo y cuándo.

Qué hace
    Descarga datos públicos registrando la URL, la fecha, el tamaño, el tipo de
    contenido y la huella criptográfica del archivo, en un registro de procedencia que
    queda al lado del dato. Permite además resolver el enlace de descarga **leyéndolo
    de la página índice** en lugar de construir el nombre del archivo, y leer tablas
    directamente desde dentro de un ZIP sin descomprimirlo.

Por qué existe
    Un análisis sobre un archivo del que no se sabe la fecha ni el origen no es
    reproducible: nadie puede repetirlo ni saber si los datos cambiaron. El registro de
    procedencia convierte «descargué un CSV» en un hecho verificable.

    La segunda razón es concreta. El GTFS de la Red Metropolitana de Movilidad se
    publica con un nombre que cambia en cada versión (`GTFS_20261114_v2.zip`). Un
    script que construya ese nombre a partir de una fecha funciona el día que se
    escribe y falla la semana siguiente, sin aviso. `discover_link` lee el enlace de la
    página, que es lo que un proceso automatizado debe hacer.

Qué NO hace
    No decide si tiene derecho a usar un dato. La licencia se declara a mano en el
    `DataSource` y, si no se verificó, se declara como no verificada. El módulo no
    redistribuye nada: descarga a una carpeta local que no se versiona.

Cómo se valida
    `tests/test_sources.py` no usa la red: ejerce `fetch` contra URL `file://` y la
    detección de enlaces contra HTML de prueba, de modo que la suite corre en
    integración continua sin salir a internet.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import urllib.parse
import urllib.request
import zipfile
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

#: Sufijo del registro de procedencia que acompaña a cada archivo descargado.
PROVENANCE_SUFFIX = ".procedencia.json"

#: Tamaño del bloque de lectura. 1 MiB es un compromiso entre memoria y llamadas.
CHUNK = 1024 * 1024

#: Esquemas admitidos. `file` se admite para poder probar sin red.
ALLOWED_SCHEMES = ("http", "https", "file")

#: Valor que debe usarse cuando la licencia no se pudo comprobar. Es deliberadamente
#: incómodo de leer: una licencia sin verificar no debe pasar por verificada.
UNVERIFIED_LICENCE = "NO VERIFICADA"


@dataclass(frozen=True)
class DataSource:
    """Declaración de una fuente de datos.

    Args:
        name: identificador corto, en kebab-case.
        url: URL de descarga directa, o de la página índice si se usa `link_pattern`.
        publisher: quién publica el dato.
        description: qué contiene.
        licence: licencia declarada. Use `UNVERIFIED_LICENCE` si no la comprobó.
        licence_url: dónde se leen los términos.
        link_pattern: expresión regular con un grupo que captura el `href` de descarga
            dentro de la página de `url`. Si se indica, `fetch` resuelve el enlace
            antes de descargar.
        media_type: tipo de contenido esperado; se compara con el que responde el
            servidor y se avisa si no coincide.
    """

    name: str
    url: str
    publisher: str
    description: str
    licence: str = UNVERIFIED_LICENCE
    licence_url: str = ""
    link_pattern: str = ""
    media_type: str = ""

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9-]*", self.name):
            raise ValueError(
                f"Nombre de fuente inválido: {self.name!r}. Use minúsculas y guiones."
            )
        scheme = urllib.parse.urlparse(self.url).scheme
        if scheme not in ALLOWED_SCHEMES:
            raise ValueError(
                f"Esquema no admitido en {self.url!r}: {scheme!r}. Use {ALLOWED_SCHEMES}."
            )
        if not self.publisher.strip():
            raise ValueError(f"La fuente {self.name!r} debe declarar quién la publica.")

    @property
    def licence_verified(self) -> bool:
        """True solo si la licencia se declaró explícitamente y no como no verificada."""
        return self.licence != UNVERIFIED_LICENCE and bool(self.licence.strip())


@dataclass
class Provenance:
    """Registro de una adquisición concreta.

    Es lo que convierte un archivo en un dato citable: dice de dónde salió, cuándo, qué
    tamaño tenía y cuál es su huella, de modo que cualquiera pueda comprobar que está
    mirando exactamente el mismo archivo.
    """

    source: str
    requested_url: str
    resolved_url: str
    downloaded_at: str
    sha256: str
    bytes: int
    media_type: str
    publisher: str
    licence: str
    licence_url: str = ""
    licence_verified: bool = False
    notes: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2) + "\n"

    @classmethod
    def from_path(cls, path: str | Path) -> Provenance:
        """Carga el registro que acompaña a un archivo descargado.

        Raises:
            FileNotFoundError: si el archivo no tiene registro. Un dato sin procedencia
                no se usa: se vuelve a descargar o se descarta.
        """
        record = Path(f"{path}{PROVENANCE_SUFFIX}")
        if not record.exists():
            raise FileNotFoundError(
                f"{path} no tiene registro de procedencia ({record.name}). "
                "Vuelva a descargarlo con lab.sources.fetch."
            )
        return cls(**json.loads(record.read_text(encoding="utf-8")))

    def summary(self) -> str:
        """Una línea citable, para pegar en un informe."""
        licencia = self.licence if self.licence_verified else f"{self.licence} (sin comprobar)"
        return (f"{self.publisher}. {self.source}. {self.resolved_url} "
                f"(descargado {self.downloaded_at[:10]}, {self.bytes:,} bytes, "
                f"sha256 {self.sha256[:12]}…, licencia: {licencia})")


def sha256_of(path: str | Path) -> str:
    """Huella SHA-256 de un archivo, leído por bloques."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def discover_link(page_url: str, pattern: str, timeout: int = 60) -> str:
    """Resuelve una URL de descarga leyendo el enlace de una página índice.

    Args:
        page_url: página que contiene el enlace.
        pattern: expresión regular con **un** grupo que captura el `href`.
        timeout: segundos de espera.

    Returns:
        La URL absoluta del primer enlace que coincide.

    Raises:
        ValueError: si el patrón no tiene exactamente un grupo, o si no hay coincidencia.

    Por qué no construir el nombre del archivo: el nombre cambia en cada publicación.
    Leerlo de la página es la única forma de que el proceso siga funcionando mañana.
    """
    compiled = re.compile(pattern, re.IGNORECASE)
    if compiled.groups != 1:
        raise ValueError(
            f"El patrón debe tener exactamente un grupo de captura; tiene {compiled.groups}."
        )
    with urllib.request.urlopen(page_url, timeout=timeout) as response:  # noqa: S310
        html = response.read().decode("utf-8", errors="replace")
    match = compiled.search(html)
    if not match:
        raise ValueError(
            f"Ningún enlace de {page_url} coincide con {pattern!r}. "
            "La página pudo cambiar de estructura: revísela antes de ajustar el patrón."
        )
    return urllib.parse.urljoin(page_url, match.group(1))


def fetch(
    source: DataSource,
    destination: str | Path,
    expected_sha256: str = "",
    force: bool = False,
    timeout: int = 300,
) -> tuple[Path, Provenance]:
    """Descarga una fuente y deja su registro de procedencia al lado.

    Args:
        source: fuente declarada.
        destination: archivo de destino. Se crean los directorios que falten.
        expected_sha256: huella esperada. Si se indica y no coincide, se levanta un
            error y **no** se conserva el archivo: un dato que no es el que se esperaba
            es peor que ningún dato.
        force: vuelve a descargar aunque el archivo ya exista con registro válido.
        timeout: segundos de espera.

    Returns:
        La ruta del archivo y su registro de procedencia.

    Raises:
        ValueError: si la huella no coincide con `expected_sha256`.
    """
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists() and not force:
        try:
            existing = Provenance.from_path(target)
        except (FileNotFoundError, TypeError, json.JSONDecodeError):
            existing = None
        if existing is not None and sha256_of(target) == existing.sha256:
            if expected_sha256 and existing.sha256 != expected_sha256:
                raise ValueError(
                    f"{target} ya existe pero su huella {existing.sha256} no coincide con "
                    f"la esperada {expected_sha256}."
                )
            return target, existing

    resolved = source.url
    notes: list[str] = []
    if source.link_pattern:
        resolved = discover_link(source.url, source.link_pattern, timeout=timeout)
        notes.append(f"enlace resuelto desde la página índice {source.url}")

    temporary = target.with_suffix(target.suffix + ".parcial")
    digest = hashlib.sha256()
    size = 0
    with urllib.request.urlopen(resolved, timeout=timeout) as response:  # noqa: S310
        media_type = response.headers.get_content_type() or ""
        with temporary.open("wb") as handle:
            while chunk := response.read(CHUNK):
                handle.write(chunk)
                digest.update(chunk)
                size += len(chunk)

    checksum = digest.hexdigest()
    if expected_sha256 and checksum != expected_sha256:
        temporary.unlink(missing_ok=True)
        raise ValueError(
            f"La huella del archivo descargado ({checksum}) no coincide con la esperada "
            f"({expected_sha256}). No se conservó el archivo."
        )
    if source.media_type and media_type and media_type != source.media_type:
        notes.append(
            f"el servidor devolvió {media_type!r} y se esperaba {source.media_type!r}"
        )
    if not source.licence_verified:
        notes.append(
            "licencia no verificada: revise los términos de uso antes de redistribuir"
        )

    temporary.replace(target)
    provenance = Provenance(
        source=source.name,
        requested_url=source.url,
        resolved_url=resolved,
        downloaded_at=datetime.now(UTC).isoformat(timespec="seconds"),
        sha256=checksum,
        bytes=size,
        media_type=media_type,
        publisher=source.publisher,
        licence=source.licence,
        licence_url=source.licence_url,
        licence_verified=source.licence_verified,
        notes=notes,
    )
    Path(f"{target}{PROVENANCE_SUFFIX}").write_text(provenance.to_json(), encoding="utf-8")
    return target, provenance


# ------------------------------------------------------------------ lectura desde ZIP
def zip_members(archive: str | Path) -> pd.DataFrame:
    """Inventario de un ZIP: nombre, tamaño comprimido y descomprimido.

    Mirar esto antes de leer evita el error habitual de cargar en memoria un archivo de
    50 MB sin saberlo.
    """
    with zipfile.ZipFile(archive) as handle:
        rows = [
            {
                "archivo": info.filename,
                "bytes_comprimido": info.compress_size,
                "bytes": info.file_size,
                "modificado": datetime(*info.date_time).isoformat(timespec="seconds"),
            }
            for info in handle.infolist()
        ]
    return pd.DataFrame(rows).sort_values("bytes", ascending=False).reset_index(drop=True)


def read_zip_table(
    archive: str | Path, member: str, encoding: str = "utf-8-sig", **kwargs
) -> pd.DataFrame:
    """Lee un CSV de dentro de un ZIP sin descomprimir el archivo completo.

    Args:
        archive: ruta del ZIP.
        member: nombre exacto del archivo dentro del ZIP.
        encoding: `utf-8-sig` por defecto, porque los publicadores suelen incluir la
            marca inicial de UTF-8 y leerla como dato ensucia el nombre de la primera
            columna.
        **kwargs: se pasan a `pandas.read_csv`. Use `dtype=str` cuando quiera ver los
            datos tal como están, sin que pandas adivine tipos.

    Raises:
        KeyError: con la lista de archivos disponibles, para no obligar a abrir el ZIP
            por fuera.
    """
    with zipfile.ZipFile(archive) as handle:
        if member not in handle.namelist():
            raise KeyError(
                f"{member!r} no está en {archive}. Contiene: {sorted(handle.namelist())}"
            )
        with handle.open(member) as raw:
            return pd.read_csv(io.TextIOWrapper(raw, encoding=encoding), **kwargs)


def iter_zip_table(
    archive: str | Path, member: str, chunksize: int = 200_000, encoding: str = "utf-8-sig",
    **kwargs,
) -> Iterator[pd.DataFrame]:
    """Recorre un CSV grande de dentro de un ZIP por bloques.

    Para tablas de más de un millón de filas, leer por bloques mantiene la memoria
    acotada. El precio es que cada agregación debe poder calcularse de forma
    incremental: una suma sí, una mediana exacta no.
    """
    with zipfile.ZipFile(archive) as handle, handle.open(member) as raw:
        reader = pd.read_csv(
            io.TextIOWrapper(raw, encoding=encoding), chunksize=chunksize, **kwargs
        )
        yield from reader


# ---------------------------------------------------------------------- inventario
def manifest(directory: str | Path) -> pd.DataFrame:
    """Inventario de los datos adquiridos en un directorio, con su procedencia."""
    base = Path(directory)
    columnas = ["archivo", "fuente", "publicado_por", "descargado", "bytes",
                "licencia", "licencia_verificada", "sha256"]
    if not base.exists():
        return pd.DataFrame(columns=columnas)
    filas = []
    for record in sorted(base.rglob(f"*{PROVENANCE_SUFFIX}")):
        datos = json.loads(record.read_text(encoding="utf-8"))
        filas.append({
            "archivo": record.name[: -len(PROVENANCE_SUFFIX)],
            "fuente": datos.get("source", ""),
            "publicado_por": datos.get("publisher", ""),
            "descargado": datos.get("downloaded_at", "")[:10],
            "bytes": datos.get("bytes", 0),
            "licencia": datos.get("licence", ""),
            "licencia_verificada": "sí" if datos.get("licence_verified") else "no",
            "sha256": (datos.get("sha256", "") or "")[:12],
        })
    if not filas:
        return pd.DataFrame(columns=columnas)
    return pd.DataFrame(filas, columns=columnas)


def citations(records: Iterable[Provenance]) -> str:
    """Bloque de citas en Markdown para la sección de fuentes de un informe."""
    lineas = [f"- {record.summary()}" for record in records]
    return "\n".join(lineas) + "\n" if lineas else "_Sin fuentes registradas._\n"


#: Fuentes públicas declaradas en el laboratorio.
#:
#: El GTFS de la Red Metropolitana de Movilidad se resuelve leyendo el enlace de su
#: página índice, porque el nombre del archivo cambia en cada publicación. La licencia
#: figura como no verificada: la página de descarga se abrió y se leyó, sus términos de
#: uso no. Mientras siga así, el laboratorio **no redistribuye** estos datos.
#: Feriados legales de Chile. **Es una fuente de tercero, no oficial.**
#:
#: La fuente oficial son la Ley 19.973 y sus modificaciones, y el listado que publica
#: la Dirección del Trabajo. La API del gobierno (`apis.digital.gob.cl`) no resolvía al
#: momento de escribir esto, de modo que se usa este tercero **declarándolo**, y la
#: parte movible del listado se valida de forma independiente con
#: `lab.calendars.easter_sunday`.
#:
#: El listado se descarga una vez y se versiona dentro del caso que lo usa: depender de
#: una API de tercero en cada ejecución haría el caso irreproducible el día que esa API
#: deje de existir.
_FERIADOS_CL = DataSource(
    name="feriados-cl",
    url="https://api.boostr.cl/holidays.json",
    publisher="api.boostr.cl (tercero, NO es la fuente oficial)",
    description=(
        "Listado de feriados legales de Chile del año en curso. La fuente oficial es la "
        "Ley 19.973 y el listado de la Dirección del Trabajo; este servicio es un "
        "tercero y su listado debe contrastarse."
    ),
    licence=UNVERIFIED_LICENCE,
    media_type="application/json",
)


def feriados_cl(year: int | None = None) -> DataSource:
    """Fuente de feriados de Chile para un año concreto.

    Args:
        year: año a consultar. Sin año, el servicio devuelve el año en curso.

    La fuente **no es oficial** y así lo declara. Quien use el listado tiene que
    contrastarlo: `lab.calendars.easter_relative` permite verificar la parte movible.
    """
    if year is None:
        return _FERIADOS_CL
    return DataSource(
        name=f"feriados-cl-{year}",
        url=f"https://api.boostr.cl/holidays/{year}.json",
        publisher=_FERIADOS_CL.publisher,
        description=f"{_FERIADOS_CL.description} Año consultado: {year}.",
        licence=_FERIADOS_CL.licence,
        media_type=_FERIADOS_CL.media_type,
    )


CATALOG: dict[str, DataSource] = {
    "gtfs-historicos-2024": DataSource(
        name="gtfs-historicos-2024",
        url="https://dtpm.cl/descargas/gtfs/2024.zip",
        publisher="Directorio de Transporte Público Metropolitano (DTPM)",
        description=(
            "Archivo anual con las publicaciones GTFS de 2024. El caso de evolución "
            "selecciona la última publicación, GTFS_20241124.zip."
        ),
        licence=UNVERIFIED_LICENCE,
        licence_url="https://dtpm.cl/index.php/programas-de-operaciones/gtfs-historicos",
        media_type="application/zip",
    ),
    "gtfs-historicos-2025": DataSource(
        name="gtfs-historicos-2025",
        url="https://dtpm.cl/descargas/gtfs/2025.zip",
        publisher="Directorio de Transporte Público Metropolitano (DTPM)",
        description=(
            "Archivo anual con las publicaciones GTFS de 2025. El caso de evolución "
            "selecciona la última publicación, GTFS_20251220.zip."
        ),
        licence=UNVERIFIED_LICENCE,
        licence_url="https://dtpm.cl/index.php/programas-de-operaciones/gtfs-historicos",
        media_type="application/zip",
    ),
    "gtfs-red-movilidad": DataSource(
        name="gtfs-red-movilidad",
        url="https://www.dtpm.cl/index.php/gtfs-vigente",
        publisher="Directorio de Transporte Público Metropolitano (DTPM)",
        description=(
            "GTFS estático vigente de la Red Metropolitana de Movilidad: recorridos, "
            "paradas, expediciones, horarios y frecuencias de buses, Metro, trenes y "
            "bus de acercamiento al aeropuerto."
        ),
        licence=UNVERIFIED_LICENCE,
        licence_url="https://www.dtpm.cl/index.php/gtfs-vigente",
        link_pattern=r'href="([^"]*descargas/gtfs/GTFS_[^"]*\.zip)"',
        media_type="application/zip",
    ),
    # --- Lugares de carga de la tarjeta bip! -------------------------------------
    # Cinco archivos publicados por la Subsecretaría de Transporte en el portal de
    # datos abiertos del Estado. A diferencia del GTFS, aquí la licencia **sí** está
    # declarada y verificada en los metadatos del portal: Creative Commons
    # Atribución-NoComercial 2.0. Eso permite citarlos y trabajarlos; «NoComercial»
    # acota el uso, no la lectura ni el análisis.
    #
    # Son Excel reales con el desorden habitual del sector público: el encabezado
    # está en una fila distinta en cada archivo (7, 9, 13, 10 y 9), los esquemas no
    # coinciden, los nombres de hoja varían y uno trae una hoja de locales cerrados.
    # Por eso son un material de práctica mejor que cualquier dataset sintético.
    "bip-metro": DataSource(
        name="bip-metro",
        url=("https://datos.gob.cl/dataset/ac76c913-3ad2-4831-ab2a-3b0d4165abdd/"
             "resource/3d54e961-d81b-4507-aeee-7a433e00a9bf/download/"
             "metro_20240917oficio-4770_2013.xlsx"),
        publisher="Subsecretaría de Transporte, Ministerio de Transportes y Telecomunicaciones",
        description=(
            "Lugares de carga de la tarjeta bip! en estaciones de Metro: código, "
            "entidad, nombre de fantasía, dirección, comuna, horario referencial y "
            "coordenadas en UTM y en latitud/longitud."
        ),
        licence="Creative Commons Atribución-NoComercial 2.0 (CC BY-NC 2.0)",
        licence_url="http://creativecommons.org/licenses/by-nc/2.0/",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ),
    "bip-puntos": DataSource(
        name="bip-puntos",
        url=("https://datos.gob.cl/dataset/c2969d8a-df82-4a6c-a1f8-e5eba36af6cf/"
             "resource/cbd329c6-9fe6-4dc1-91e3-a99689fd0254/download/"
             "pcma_20240917-oficio-4770_2013.xlsx"),
        publisher="Subsecretaría de Transporte, Ministerio de Transportes y Telecomunicaciones",
        description=(
            "Puntos bip! (PCMA): el archivo más grande de la serie, con alrededor de "
            "1 579 lugares de carga. No trae columna de horario, a diferencia de los "
            "demás."
        ),
        licence="Creative Commons Atribución-NoComercial 2.0 (CC BY-NC 2.0)",
        licence_url="http://creativecommons.org/licenses/by-nc/2.0/",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ),
    "bip-centros-alto-estandar": DataSource(
        name="bip-centros-alto-estandar",
        url=("https://datos.gob.cl/dataset/5993b4cb-869c-4733-a124-7fcdd57bbb05/"
             "resource/fef2a0f6-84f8-4a1a-9a64-e2424efdd376/download/"
             "pcmav-alto-estandar_20240917_oficio-4770_2013.xlsx"),
        publisher="Subsecretaría de Transporte, Ministerio de Transportes y Telecomunicaciones",
        description=(
            "Centros bip! de alto estándar: pocos locales con horario extendido y "
            "servicios adicionales como reemplazo de tarjetas."
        ),
        licence="Creative Commons Atribución-NoComercial 2.0 (CC BY-NC 2.0)",
        licence_url="http://creativecommons.org/licenses/by-nc/2.0/",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ),
    "bip-centros-estandar": DataSource(
        name="bip-centros-estandar",
        url=("https://datos.gob.cl/dataset/29a758f3-4fe8-4582-afc7-8237b83aaddc/"
             "resource/8e827306-e9ef-4e84-a251-38d29a8f66d0/download/"
             "pcmav-estandar-normal_20240917_oficio-4770_2013.xlsx"),
        publisher="Subsecretaría de Transporte, Ministerio de Transportes y Telecomunicaciones",
        description="Centros bip! de estándar normal, con su horario de atención.",
        licence="Creative Commons Atribución-NoComercial 2.0 (CC BY-NC 2.0)",
        licence_url="http://creativecommons.org/licenses/by-nc/2.0/",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ),
    "feriados-cl": _FERIADOS_CL,
    "bip-retail": DataSource(
        name="bip-retail",
        url=("https://datos.gob.cl/dataset/f0fad229-d59a-4992-8c7a-489d1e9ff58c/"
             "resource/2d177f41-08f9-471a-af5c-bc949267f053/download/"
             "retail_20240917_oficio-4770_2013.xlsx"),
        publisher="Subsecretaría de Transporte, Ministerio de Transportes y Telecomunicaciones",
        description=(
            "Lugares de carga en cadenas de retail. Es el único archivo con **dos "
            "hojas**: 'Abiertos' y 'Cerrados'. Consolidar ambas sin mirar infla "
            "cualquier indicador de cobertura."
        ),
        licence="Creative Commons Atribución-NoComercial 2.0 (CC BY-NC 2.0)",
        licence_url="http://creativecommons.org/licenses/by-nc/2.0/",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ),
}

#: Las cinco fuentes de lugares de carga, que se consolidan en una sola tabla.
BIP_SOURCES: tuple[str, ...] = (
    "bip-metro", "bip-puntos", "bip-centros-alto-estandar",
    "bip-centros-estandar", "bip-retail",
)


def get(name: str) -> DataSource:
    """Devuelve una fuente del catálogo.

    Raises:
        KeyError: con los nombres disponibles.
    """
    try:
        return CATALOG[name]
    except KeyError as exc:
        raise KeyError(f"Fuente desconocida: {name!r}. Disponibles: {sorted(CATALOG)}.") from exc
