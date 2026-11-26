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
CATALOG: dict[str, DataSource] = {
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
}


def get(name: str) -> DataSource:
    """Devuelve una fuente del catálogo.

    Raises:
        KeyError: con los nombres disponibles.
    """
    try:
        return CATALOG[name]
    except KeyError as exc:
        raise KeyError(f"Fuente desconocida: {name!r}. Disponibles: {sorted(CATALOG)}.") from exc
