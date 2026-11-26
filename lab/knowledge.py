"""Base de conocimiento: registros atómicos recuperables por búsqueda léxica.

Qué hace
    Lee los registros de `knowledge/` (Markdown con encabezado de metadatos),
    construye un índice invertido y permite recuperarlos por consulta de texto con
    puntuación TF-IDF, filtros por tipo y etiquetas, y navegación por relaciones.

Por qué existe
    Cada problema resuelto deja conocimiento: una definición, una fórmula, un patrón
    de resolución, un error que costó una hora. Si ese conocimiento queda enterrado
    en el informe de un caso, no se reutiliza. Aquí queda indexado y consultable.

Por qué búsqueda léxica y no vectorial
    TF-IDF no necesita modelos, red ni dependencias, funciona en integración continua
    y es auditable: se puede explicar por qué un registro salió primero. La búsqueda
    semántica con embeddings está declarada en la hoja de ruta como extensión
    opcional; no está implementada y no se presenta como si lo estuviera.

Formato de un registro
    ```
    ---
    id: tasa-ponderada-vs-promedio-simple
    tipo: concepto
    titulo: Tasa ponderada frente a promedio simple de porcentajes
    etiquetas: [estadistica, indicadores, errores-frecuentes]
    fuente: docs/learning/.../clase.md
    relacionados: [denominador-cero]
    ---
    Cuerpo en Markdown.
    ```

Cómo se valida
    `tests/test_knowledge.py` comprueba el parseo del encabezado, el rechazo de
    registros sin campos obligatorios, el ranking de la búsqueda y la integridad de
    las referencias cruzadas de todos los registros del repositorio.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = ROOT / "knowledge"

#: Tipos de registro admitidos. Cerrar el vocabulario permite filtrar con sentido.
RECORD_TYPES: tuple[str, ...] = (
    "concepto", "definicion", "formula", "algoritmo", "metodologia", "investigacion",
    "ejercicio", "solucion", "caso", "error", "patron", "leccion",
)

REQUIRED_KEYS: tuple[str, ...] = ("id", "tipo", "titulo", "etiquetas")

#: Palabras sin valor discriminante en español e inglés técnico.
STOPWORDS: frozenset[str] = frozenset(["a", "al", "algo", "algunas", "algunos", "ante", "antes", "como", "con", "contra", "cual", "cuando", "de", "del", "desde", "donde", "dos", "el", "ella", "ellas", "ellos", "en", "entre", "era", "eran", "es", "esa", "ese", "eso", "esta", "estas", "este", "esto", "estos", "fue", "fueron", "ha", "hasta", "hay", "la", "las", "le", "les", "lo", "los", "mas", "más", "me", "mi", "mucho", "muy", "no", "nos", "o", "os", "otra", "otro", "para", "pero", "poco", "por", "porque", "que", "quien", "se", "ser", "si", "sin", "so", "sobre", "su", "sus", "también", "tanto", "te", "tiene", "tienen", "todo", "todos", "tu", "un", "una", "uno", "unos", "y", "ya", "the", "of", "and", "to", "in", "is", "it", "for", "on", "with", "as", "by", "be", "or", "an", "at", "from", "this", "that"])

_WORD = re.compile(r"[a-záéíóúñü0-9_]+", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    """Divide un texto en términos comparables: minúsculas, sin palabras vacías."""
    return [t for t in (m.group(0).lower() for m in _WORD.finditer(text))
            if t not in STOPWORDS and len(t) > 1]


@dataclass
class Record:
    """Un registro de conocimiento."""

    id: str
    tipo: str
    titulo: str
    etiquetas: tuple[str, ...]
    cuerpo: str
    fuente: str = ""
    relacionados: tuple[str, ...] = ()
    path: Path | None = None

    @property
    def text(self) -> str:
        """Texto indexable: título, etiquetas y cuerpo."""
        return f"{self.titulo} {' '.join(self.etiquetas)} {self.cuerpo}"

    def summary(self, width: int = 160) -> str:
        """Primeras líneas del cuerpo, en una sola línea."""
        flat = " ".join(self.cuerpo.split())
        return flat if len(flat) <= width else flat[: width - 1] + "…"


def _parse_front_matter(raw: str, path: Path) -> tuple[dict[str, str], str]:
    if not raw.lstrip().startswith("---"):
        raise ValueError(f"{path}: el registro debe comenzar con un encabezado '---'.")
    stripped = raw.lstrip()
    end = stripped.find("\n---", 3)
    if end == -1:
        raise ValueError(f"{path}: el encabezado de metadatos no está cerrado con '---'.")
    header = stripped[3:end]
    body = stripped[end + 4:].lstrip("\n")
    meta: dict[str, str] = {}
    for line in header.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"{path}: línea de metadatos sin ':' → {line!r}")
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, body


def _parse_list(value: str) -> tuple[str, ...]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return tuple(item.strip().strip("'\"") for item in value.split(",") if item.strip())


def load_record(path: str | Path) -> Record:
    """Carga un registro desde disco y valida sus metadatos.

    Raises:
        ValueError: si falta un campo obligatorio, el tipo no es admitido o el
            identificador no coincide con el nombre del archivo.
    """
    file_path = Path(path)
    meta, body = _parse_front_matter(file_path.read_text(encoding="utf-8"), file_path)
    missing = [k for k in REQUIRED_KEYS if not meta.get(k)]
    if missing:
        raise ValueError(f"{file_path}: faltan metadatos obligatorios {missing}.")
    if meta["tipo"] not in RECORD_TYPES:
        raise ValueError(f"{file_path}: tipo '{meta['tipo']}' fuera de {RECORD_TYPES}.")
    if meta["id"] != file_path.stem:
        raise ValueError(f"{file_path}: el id '{meta['id']}' no coincide con el nombre del archivo.")
    if not body.strip():
        raise ValueError(f"{file_path}: el registro no tiene cuerpo.")
    return Record(
        id=meta["id"],
        tipo=meta["tipo"],
        titulo=meta["titulo"],
        etiquetas=_parse_list(meta["etiquetas"]),
        cuerpo=body.strip(),
        fuente=meta.get("fuente", ""),
        relacionados=_parse_list(meta.get("relacionados", "")),
        path=file_path,
    )


@dataclass
class SearchHit:
    """Un resultado de búsqueda con su puntuación."""

    record: Record
    score: float
    matched: tuple[str, ...]


@dataclass
class KnowledgeBase:
    """Colección indexada de registros de conocimiento."""

    records: dict[str, Record] = field(default_factory=dict)
    _df: Counter = field(default_factory=Counter, init=False, repr=False)
    _tf: dict[str, Counter] = field(default_factory=dict, init=False, repr=False)

    # ------------------------------------------------------------------- construcción
    def add(self, record: Record) -> None:
        """Agrega un registro y actualiza el índice.

        Raises:
            ValueError: si el identificador ya existe. Dos registros con el mismo id
                hacen imposible citar el conocimiento de forma estable.
        """
        if record.id in self.records:
            raise ValueError(f"Identificador repetido en la base de conocimiento: {record.id!r}")
        self.records[record.id] = record
        tokens = Counter(tokenize(record.text))
        self._tf[record.id] = tokens
        for term in tokens:
            self._df[term] += 1

    @classmethod
    def from_directory(cls, directory: str | Path = KNOWLEDGE_DIR) -> KnowledgeBase:
        """Carga todos los `.md` de un directorio, de forma recursiva."""
        base = cls()
        path = Path(directory)
        if not path.exists():
            return base
        for file_path in sorted(path.rglob("*.md")):
            if file_path.name.upper().startswith("README"):
                continue
            base.add(load_record(file_path))
        return base

    # ----------------------------------------------------------------------- consulta
    def __len__(self) -> int:
        return len(self.records)

    def get(self, record_id: str) -> Record:
        try:
            return self.records[record_id]
        except KeyError as exc:
            raise KeyError(f"No existe el registro {record_id!r}.") from exc

    def by_type(self, tipo: str) -> list[Record]:
        if tipo not in RECORD_TYPES:
            raise ValueError(f"Tipo inválido: {tipo!r}. Use {RECORD_TYPES}.")
        return [r for r in self.records.values() if r.tipo == tipo]

    def by_tag(self, tag: str) -> list[Record]:
        return [r for r in self.records.values() if tag in r.etiquetas]

    def search(
        self,
        query: str,
        limit: int = 5,
        tipos: Sequence[str] | None = None,
        etiquetas: Sequence[str] | None = None,
    ) -> list[SearchHit]:
        """Busca registros por relevancia TF-IDF.

        Puntuación: para cada término t de la consulta presente en el registro d,
        `score(d) += (1 + log tf(t, d)) · log(1 + N / df(t))`, donde N es el número
        de registros.

        Se usa la IDF suavizada `log(1 + N/df)` y no la clásica `log(N/df)`. Con la
        clásica, un término que aparece en **todos** los registros pesa exactamente
        cero, y en una base pequeña y temática eso significa que una búsqueda
        perfectamente razonable no devuelve nada. La suavizada mantiene el peso
        siempre positivo y sigue penalizando los términos poco discriminantes.

        Args:
            query: texto libre.
            limit: cantidad máxima de resultados.
            tipos: si se indica, restringe a esos tipos de registro.
            etiquetas: si se indica, exige al menos una de esas etiquetas.

        Returns:
            Resultados ordenados por puntuación descendente y, a igual puntuación,
            por identificador, para que el orden sea reproducible.
        """
        if limit <= 0:
            raise ValueError("El límite debe ser positivo.")
        terms = tokenize(query)
        if not terms:
            return []
        total = max(len(self.records), 1)
        hits: list[SearchHit] = []
        for record_id, record in self.records.items():
            if tipos and record.tipo not in tipos:
                continue
            if etiquetas and not set(etiquetas) & set(record.etiquetas):
                continue
            tf = self._tf[record_id]
            score = 0.0
            matched: list[str] = []
            for term in set(terms):
                count = tf.get(term, 0)
                if not count:
                    continue
                idf = math.log(1 + total / self._df[term]) if self._df[term] else 0.0
                score += (1 + math.log(count)) * idf
                matched.append(term)
            if score > 0:
                hits.append(SearchHit(record, round(score, 6), tuple(sorted(matched))))
        hits.sort(key=lambda h: (-h.score, h.record.id))
        return hits[:limit]

    # ---------------------------------------------------------------------- integridad
    def broken_links(self) -> list[tuple[str, str]]:
        """Pares `(origen, destino)` donde el destino no existe en la base."""
        return [
            (record.id, target)
            for record in self.records.values()
            for target in record.relacionados
            if target not in self.records
        ]

    def index_markdown(self, link_prefix: str = "") -> str:
        """Índice navegable de la base, agrupado por tipo.

        Args:
            link_prefix: prefijo de los enlaces, para cuando el índice se publica
                fuera de `knowledge/` (por ejemplo `"../knowledge/"` desde `docs/`).
        """
        lines = ["| Tipo | Registro | Título | Etiquetas |", "| --- | --- | --- | --- |"]
        for record in sorted(self.records.values(), key=lambda r: (r.tipo, r.id)):
            rel = link_prefix + (record.path.name if record.path else f"{record.id}.md")
            lines.append(
                f"| {record.tipo} | [`{record.id}`]({rel}) | {record.titulo} | "
                f"{', '.join(record.etiquetas)} |"
            )
        if len(lines) == 2:
            lines.append("| — | — | Sin registros | — |")
        return "\n".join(lines) + "\n"

    def stats(self) -> dict[str, int]:
        """Recuento de registros por tipo, para informar cobertura real."""
        counts = Counter(r.tipo for r in self.records.values())
        return {tipo: counts.get(tipo, 0) for tipo in RECORD_TYPES}


def search_cli(query: str, limit: int = 5) -> str:
    """Búsqueda formateada para la línea de comandos."""
    base = KnowledgeBase.from_directory()
    hits = base.search(query, limit=limit)
    if not hits:
        return f"Sin resultados para {query!r} entre {len(base)} registros."
    lines = [f"{len(hits)} resultado(s) para {query!r} entre {len(base)} registros:", ""]
    for position, hit in enumerate(hits, start=1):
        lines.append(f"{position}. [{hit.record.tipo}] {hit.record.titulo}  (score {hit.score})")
        lines.append(f"   id: {hit.record.id} · términos: {', '.join(hit.matched)}")
        lines.append(f"   {hit.record.summary()}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover - utilidad de consola
    import sys

    from lab.console import enable_utf8

    enable_utf8()
    if len(sys.argv) < 2:
        base = KnowledgeBase.from_directory()
        print(f"Base de conocimiento: {len(base)} registros")
        for tipo, count in base.stats().items():
            if count:
                print(f"  {tipo:18} {count}")
        print('\nUso: python -m lab.knowledge "consulta"')
    else:
        print(search_cli(" ".join(sys.argv[1:])))
