"""Coherencia del repositorio: lo declarado contra lo verificable.

Qué protege esta suite
    Las afirmaciones de estado se desincronizan con el tiempo: la versión del README
    deja de coincidir con la del `pyproject.toml`, una tabla generada se queda vieja,
    un enlace relativo apunta a un archivo que se movió. Estas pruebas convierten cada
    afirmación verificable en un control automático.

    También protege las invariantes de arquitectura: el núcleo no debe conocer los
    casos, y los casos no deben conocerse entre sí.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import pytest

import lab
from scripts.build_docs import SALIDAS, build

ROOT = Path(__file__).resolve().parents[1]

#: Archivos que deben declarar la misma versión que el paquete.
ARCHIVOS_CON_VERSION = ("README.md", "CHANGELOG.md")


# ------------------------------------------------------------------------- versión
def test_la_version_es_la_misma_en_todas_partes():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = pyproject["project"]["version"]
    assert version == lab.__version__, (
        f"pyproject.toml declara {version} y lab.__version__ declara {lab.__version__}"
    )
    for nombre in ARCHIVOS_CON_VERSION:
        texto = (ROOT / nombre).read_text(encoding="utf-8")
        assert version in texto, f"{nombre} no menciona la versión {version}"


def test_la_primera_version_oficial_es_la_0_1_0():
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "0.1.0" in changelog
    # El changelog no debe anunciar versiones anteriores como releases oficiales.
    anteriores = re.findall(r"^##\s*0\.0\.\d+", changelog, flags=re.MULTILINE)
    assert not anteriores, f"el changelog anuncia prototipos como releases: {anteriores}"


# --------------------------------------------------------- documentación derivada
def test_la_documentacion_derivada_esta_al_dia():
    desfasados = build(check=True)
    assert not desfasados, (
        "documentación derivada desincronizada: "
        + ", ".join(desfasados)
        + ". Ejecute: python scripts/build_docs.py"
    )


def test_los_archivos_generados_llevan_su_aviso():
    for ruta_relativa in SALIDAS:
        texto = (ROOT / ruta_relativa).read_text(encoding="utf-8")
        assert texto.startswith("<!-- Archivo generado"), ruta_relativa


# ------------------------------------------------------------------------- enlaces
def _enlaces_relativos(texto: str) -> list[str]:
    enlaces = re.findall(r"\[[^\]]*\]\(([^)]+)\)", texto)
    salida = []
    for enlace in enlaces:
        destino = enlace.split("#")[0].strip()
        if not destino or destino.startswith(("http://", "https://", "mailto:", "internal:")):
            continue
        salida.append(destino)
    return salida


def test_todos_los_enlaces_relativos_de_la_documentacion_existen():
    rotos: list[str] = []
    for archivo in sorted(ROOT.glob("*.md")) + sorted((ROOT / "docs").rglob("*.md")) + \
            sorted((ROOT / "knowledge").glob("*.md")) + sorted((ROOT / "cases").rglob("*.md")):
        texto = archivo.read_text(encoding="utf-8")
        for destino in _enlaces_relativos(texto):
            if not (archivo.parent / destino).resolve().exists():
                rotos.append(f"{archivo.relative_to(ROOT).as_posix()} → {destino}")
    assert not rotos, "enlaces relativos rotos:\n" + "\n".join(rotos)


def test_los_archivos_de_gobernanza_existen():
    for nombre in ("LICENSE", "CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md",
                   "README.md", "PROMPT_MAESTRO.md"):
        assert (ROOT / nombre).exists(), f"falta {nombre}"
    assert "MIT License" in (ROOT / "LICENSE").read_text(encoding="utf-8")


# ---------------------------------------------------- invariantes de arquitectura
def _importa_de(archivo: Path, paquetes: tuple[str, ...]) -> list[str]:
    texto = archivo.read_text(encoding="utf-8")
    encontrados = []
    for paquete in paquetes:
        patron = rf"^\s*(?:from\s+{paquete}[\s.]|import\s+{paquete}[\s.])"
        if re.search(patron, texto, flags=re.MULTILINE):
            encontrados.append(paquete)
    return encontrados


def test_el_nucleo_no_conoce_los_casos_ni_las_soluciones():
    prohibidos = ("cases", "solutions", "assessments", "scripts")
    infracciones: list[str] = []
    for modulo in sorted((ROOT / "lab").glob("*.py")):
        for paquete in _importa_de(modulo, prohibidos):
            infracciones.append(f"lab/{modulo.name} importa de {paquete}")
    assert not infracciones, (
        "el núcleo debe ser independiente del dominio:\n" + "\n".join(infracciones)
    )


def test_un_caso_solo_depende_de_otro_si_lo_declara():
    """Un caso puede apoyarse en otro, pero la dependencia tiene que estar escrita.

    La regla original prohibía toda dependencia entre casos, para que cada uno se
    pudiera leer y ejecutar por separado. `cobertura_de_carga` la rompió por una razón
    que vale: reutiliza la consolidación de los cinco Excel de `bip_lugares_carga` en
    lugar de repetir doscientas líneas de armonización de esquemas y de validación de
    coordenadas. Duplicarlas enseñaría que el trabajo de calidad no se amortiza, que es
    lo contrario de lo que sostiene el laboratorio.

    De modo que la invariante pasó a ser más exigente que «no se puede»: la dependencia
    vale **solo si el `case.json` la declara en `implementaciones`**. Así queda a la
    vista de quien lee el caso y de quien lo ejecuta, y una dependencia que aparezca
    por descuido sigue fallando.
    """
    slugs = tuple(p.name for p in sorted((ROOT / "cases").iterdir()) if p.is_dir())
    infracciones: list[str] = []
    for slug in slugs:
        otros = tuple(f"cases.{s}" for s in slugs if s != slug)
        if not otros:
            continue
        metadatos = ROOT / "cases" / slug / "case.json"
        declaradas = ""
        if metadatos.exists():
            datos = json.loads(metadatos.read_text(encoding="utf-8"))
            declaradas = " ".join(datos.get("implementaciones", []))
        for modulo in sorted((ROOT / "cases" / slug).glob("*.py")):
            for paquete in _importa_de(modulo, otros):
                dependencia = paquete.removeprefix("cases.")
                if f"cases/{dependencia}/" not in declaradas:
                    infracciones.append(
                        f"cases/{slug}/{modulo.name} importa de {paquete} "
                        "sin declararlo en las implementaciones de su case.json"
                    )
    assert not infracciones, (
        "toda dependencia entre casos debe estar declarada:\n" + "\n".join(infracciones)
    )


def test_el_nucleo_no_tiene_rutas_absolutas_del_equipo_de_desarrollo():
    sospechosas = re.compile(r"(?:[A-Za-z]:[\\/]{1,2}(?:Users|dev)|/home/|/Users/)")
    infracciones: list[str] = []
    propio = Path(__file__).name
    for carpeta in ("lab", "scripts", "solutions", "cases", "tests"):
        for modulo in sorted((ROOT / carpeta).rglob("*.py")):
            if modulo.name == propio:
                continue  # este archivo contiene, como dato, el patrón que busca
            for numero, linea in enumerate(modulo.read_text(encoding="utf-8").splitlines(), 1):
                if sospechosas.search(linea):
                    infracciones.append(f"{carpeta}/{modulo.name}:{numero}")
    assert not infracciones, f"rutas absolutas encontradas: {infracciones}"


# ----------------------------------------------------------------- datos y secretos
def test_no_hay_secretos_evidentes_en_el_arbol():
    patrones = (
        re.compile(r"(?i)(?:api[_-]?key|secret[_-]?key|password|passwd|token)\s*=\s*"
                   r"['\"][A-Za-z0-9_\-]{16,}['\"]"),
        re.compile(r"(?:ghp|gho|github_pat)_[A-Za-z0-9_]{20,}"),
        re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    )
    hallazgos: list[str] = []
    for archivo in ROOT.rglob("*"):
        if not archivo.is_file() or archivo.suffix not in {".py", ".md", ".json", ".yml",
                                                           ".yaml", ".toml", ".ipynb", ".txt"}:
            continue
        if any(parte in {".git", ".venv", "__pycache__", "node_modules"}
               for parte in archivo.parts):
            continue
        texto = archivo.read_text(encoding="utf-8", errors="ignore")
        for patron in patrones:
            if patron.search(texto):
                hallazgos.append(archivo.relative_to(ROOT).as_posix())
                break
    assert not hallazgos, f"posibles secretos en: {hallazgos}"


def test_los_datos_sinteticos_se_declaran_como_tales():
    diccionario = (ROOT / "docs" / "diccionario.md").read_text(encoding="utf-8")
    assert "sintétic" in diccionario.lower()
    for ruta in sorted((ROOT / "cases").glob("*/case.json")):
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        fuentes = " ".join(datos["fuentes"]).lower()
        assert "sintétic" in fuentes or "público" in fuentes, (
            f"{ruta.parent.name} no declara la procedencia de sus datos"
        )


def test_las_simulaciones_declaran_que_no_son_pruebas_oficiales():
    for ruta in sorted((ROOT / "simulations").glob("*.md")):
        texto = ruta.read_text(encoding="utf-8").lower()
        assert "ficticios" in texto or "sintétic" in texto, ruta.name
        assert "no es la rúbrica oficial" in texto or "no oficial" in texto, ruta.name


# ------------------------------------------------------------- configuración del repo
def test_el_gitignore_protege_el_trabajo_propio_y_los_generados():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for patron in (".venv/", "__pycache__/", "submissions/*", "reference_outputs/"):
        assert patron in gitignore, f"falta {patron} en .gitignore"


def test_el_entorno_minimo_no_crecio_sin_aviso():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declaradas = {re.split(r"[><=!~\[]", d)[0].strip().lower()
                  for d in pyproject["project"]["dependencies"]}
    esperadas = {"pandas", "numpy", "openpyxl", "xlsxwriter", "matplotlib", "jupyterlab"}
    assert esperadas <= declaradas, f"faltan dependencias mínimas: {esperadas - declaradas}"
    extras = declaradas - esperadas - {"pytest"}
    assert not extras, (
        f"dependencias nuevas en el entorno mínimo: {sorted(extras)}. "
        "Las dependencias adicionales deben ser opcionales (ver CONTRIBUTING.md)."
    )
    opcionales = pyproject["project"]["optional-dependencies"]
    assert any(dependency.startswith("polars") for dependency in opcionales["polars"])


def test_cada_modulo_del_nucleo_tiene_docstring_con_proposito():
    sin_docstring: list[str] = []
    for modulo in sorted((ROOT / "lab").glob("*.py")):
        texto = modulo.read_text(encoding="utf-8").lstrip()
        if not texto.startswith(('"""', "'''")):
            sin_docstring.append(modulo.name)
    assert not sin_docstring, f"módulos del núcleo sin docstring: {sin_docstring}"


def test_el_paquete_declara_todos_sus_modulos():
    archivos = {p.stem for p in (ROOT / "lab").glob("*.py")} - {"__init__"}
    declarados = set(lab.__all__)
    assert archivos == declarados, (
        f"lab.__all__ desincronizado. Solo en disco: {sorted(archivos - declarados)}; "
        f"solo en __all__: {sorted(declarados - archivos)}"
    )


@pytest.mark.parametrize("comando", [
    "python scripts/generate_data.py",
    "python scripts/build_excel_solutions.py",
    "python scripts/build_assessment.py",
    "python scripts/build_docs.py",
    "python scripts/build_all_cases.py",
    "python -m pytest",
])
def test_los_comandos_documentados_en_el_readme_existen(comando):
    """Todo comando que el README promete debe corresponder a un archivo real."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    nucleo = comando.replace("python ", "")
    assert nucleo in readme, f"el README no documenta {comando!r}"
    if nucleo.startswith("scripts/"):
        assert (ROOT / nucleo).exists(), f"{nucleo} no existe"
