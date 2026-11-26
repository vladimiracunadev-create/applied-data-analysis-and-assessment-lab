"""Pruebas de la adquisición de datos (`lab.sources`).

Ninguna prueba sale a internet. `fetch` y `discover_link` se ejercen contra URL
`file://`, que `urllib` resuelve igual que `http`, de modo que la suite corre en
integración continua sin red y sin depender de que un servidor de terceros esté
disponible.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from lab.sources import (
    CATALOG,
    PROVENANCE_SUFFIX,
    UNVERIFIED_LICENCE,
    DataSource,
    Provenance,
    citations,
    discover_link,
    fetch,
    get,
    iter_zip_table,
    manifest,
    read_zip_table,
    sha256_of,
    zip_members,
)

#: SHA-256 de la cadena "contenido de prueba\n", calculado aparte para no comprobar la
#: implementación contra sí misma.
CONTENIDO = b"columna_a,columna_b\n1,x\n2,y\n"


def url_de(path: Path) -> str:
    return path.resolve().as_uri()


@pytest.fixture
def origen(tmp_path: Path) -> Path:
    archivo = tmp_path / "origen" / "datos.csv"
    archivo.parent.mkdir(parents=True)
    archivo.write_bytes(CONTENIDO)
    return archivo


@pytest.fixture
def fuente(origen: Path) -> DataSource:
    return DataSource(
        name="fuente-de-prueba",
        url=url_de(origen),
        publisher="Organismo de prueba",
        description="Dos filas y dos columnas.",
    )


# ------------------------------------------------------------------------ DataSource
def test_la_fuente_valida_su_declaracion(origen: Path):
    with pytest.raises(ValueError, match="Nombre de fuente inválido"):
        DataSource(name="Fuente_Mala", url=url_de(origen), publisher="x", description="y")
    with pytest.raises(ValueError, match="Esquema no admitido"):
        DataSource(name="f", url="ftp://servidor/a.zip", publisher="x", description="y")
    with pytest.raises(ValueError, match="debe declarar quién la publica"):
        DataSource(name="f", url=url_de(origen), publisher="   ", description="y")


def test_la_licencia_no_verificada_no_pasa_por_verificada(fuente: DataSource, origen: Path):
    assert fuente.licence == UNVERIFIED_LICENCE
    assert not fuente.licence_verified
    con_licencia = DataSource(name="f", url=url_de(origen), publisher="x",
                              description="y", licence="CC BY 4.0")
    assert con_licencia.licence_verified


# ----------------------------------------------------------------------------- fetch
def test_fetch_descarga_y_deja_el_registro_de_procedencia(fuente: DataSource, tmp_path: Path):
    destino = tmp_path / "bajada" / "datos.csv"
    ruta, procedencia = fetch(fuente, destino)
    assert ruta == destino
    assert ruta.read_bytes() == CONTENIDO
    assert procedencia.bytes == len(CONTENIDO)
    assert procedencia.sha256 == sha256_of(ruta)
    assert procedencia.publisher == "Organismo de prueba"
    assert procedencia.downloaded_at.endswith("+00:00")

    registro = Path(f"{destino}{PROVENANCE_SUFFIX}")
    assert registro.exists()
    guardado = json.loads(registro.read_text(encoding="utf-8"))
    assert guardado["sha256"] == procedencia.sha256


def test_una_licencia_sin_verificar_queda_anotada(fuente: DataSource, tmp_path: Path):
    _, procedencia = fetch(fuente, tmp_path / "datos.csv")
    assert any("licencia no verificada" in nota for nota in procedencia.notes)
    assert not procedencia.licence_verified


def test_la_huella_esperada_se_comprueba_y_el_archivo_malo_no_se_conserva(
    fuente: DataSource, tmp_path: Path
):
    destino = tmp_path / "datos.csv"
    with pytest.raises(ValueError, match="no coincide con la esperada"):
        fetch(fuente, destino, expected_sha256="0" * 64)
    assert not destino.exists(), "un archivo que no es el esperado no debe conservarse"
    assert not Path(f"{destino}{PROVENANCE_SUFFIX}").exists()


def test_la_huella_correcta_pasa(fuente: DataSource, tmp_path: Path, origen: Path):
    esperada = sha256_of(origen)
    ruta, procedencia = fetch(fuente, tmp_path / "datos.csv", expected_sha256=esperada)
    assert procedencia.sha256 == esperada
    assert ruta.exists()


def test_no_vuelve_a_descargar_si_ya_esta_y_coincide(fuente: DataSource, tmp_path: Path,
                                                      origen: Path):
    destino = tmp_path / "datos.csv"
    _, primera = fetch(fuente, destino)
    # Se borra el origen: si volviera a descargar, fallaría.
    origen.unlink()
    _, segunda = fetch(fuente, destino)
    assert segunda.downloaded_at == primera.downloaded_at


def test_forzar_vuelve_a_descargar(fuente: DataSource, tmp_path: Path):
    destino = tmp_path / "datos.csv"
    fetch(fuente, destino)
    _, segunda = fetch(fuente, destino, force=True)
    assert segunda.sha256 == sha256_of(destino)


def test_un_archivo_sin_registro_se_vuelve_a_descargar(fuente: DataSource, tmp_path: Path):
    destino = tmp_path / "datos.csv"
    destino.write_bytes(b"contenido ajeno")
    _, procedencia = fetch(fuente, destino)
    assert destino.read_bytes() == CONTENIDO
    assert procedencia.sha256 == sha256_of(destino)


def test_un_dato_sin_procedencia_no_se_usa(tmp_path: Path):
    huerfano = tmp_path / "suelto.csv"
    huerfano.write_bytes(b"a,b\n1,2\n")
    with pytest.raises(FileNotFoundError, match="no tiene registro de procedencia"):
        Provenance.from_path(huerfano)


def test_la_cita_es_legible_y_declara_el_estado_de_la_licencia(fuente: DataSource,
                                                               tmp_path: Path):
    _, procedencia = fetch(fuente, tmp_path / "datos.csv")
    cita = procedencia.summary()
    assert "Organismo de prueba" in cita
    assert "sin comprobar" in cita
    assert procedencia.sha256[:12] in cita
    assert citations([procedencia]).startswith("- ")
    assert "Sin fuentes" in citations([])


# --------------------------------------------------------------------- discover_link
def test_discover_link_lee_el_enlace_de_la_pagina(tmp_path: Path):
    pagina = tmp_path / "indice.html"
    pagina.write_text(
        '<html><body><p>GTFS vigente</p>'
        '<a href="/descargas/gtfs/GTFS_20261114_v2.zip">GTFS</a>'
        '<a href="/otros/manual.pdf">manual</a></body></html>',
        encoding="utf-8",
    )
    resuelto = discover_link(url_de(pagina), r'href="([^"]*GTFS_[^"]*\.zip)"')
    assert resuelto.endswith("/descargas/gtfs/GTFS_20261114_v2.zip")


def test_discover_link_exige_un_grupo_y_avisa_si_no_hay_coincidencia(tmp_path: Path):
    pagina = tmp_path / "indice.html"
    pagina.write_text("<html><body>sin enlaces</body></html>", encoding="utf-8")
    with pytest.raises(ValueError, match="exactamente un grupo"):
        discover_link(url_de(pagina), r'href="([^"]*)"\s*(title)?')
    with pytest.raises(ValueError, match="pudo cambiar de estructura"):
        discover_link(url_de(pagina), r'href="([^"]*\.zip)"')


def test_fetch_resuelve_el_enlace_cuando_la_fuente_lo_declara(tmp_path: Path):
    datos = tmp_path / "GTFS_20261114_v2.zip"
    datos.write_bytes(b"PK\x03\x04 contenido falso")
    pagina = tmp_path / "indice.html"
    pagina.write_text(f'<a href="{datos.name}">descargar</a>', encoding="utf-8")
    fuente = DataSource(
        name="con-indice", url=url_de(pagina), publisher="Organismo",
        description="Resuelto desde la página.",
        link_pattern=r'href="([^"]*GTFS_[^"]*\.zip)"',
    )
    ruta, procedencia = fetch(fuente, tmp_path / "bajado.zip")
    assert ruta.read_bytes() == datos.read_bytes()
    assert procedencia.resolved_url.endswith(datos.name)
    assert procedencia.requested_url == url_de(pagina)
    assert any("enlace resuelto" in nota for nota in procedencia.notes)


# ------------------------------------------------------------------- lectura desde ZIP
@pytest.fixture
def archivo_zip(tmp_path: Path) -> Path:
    destino = tmp_path / "paquete.zip"
    with zipfile.ZipFile(destino, "w") as z:
        z.writestr("grande.txt", "a,b\n" + "\n".join(f"{n},{n * 2}" for n in range(500)))
        z.writestr("chico.txt", "x,y\n1,2\n")
    return destino


def test_zip_members_ordena_por_tamano(archivo_zip: Path):
    inventario = zip_members(archivo_zip)
    assert list(inventario.columns) == ["archivo", "bytes_comprimido", "bytes", "modificado"]
    assert inventario.iloc[0].archivo == "grande.txt"
    assert inventario.bytes.is_monotonic_decreasing


def test_read_zip_table_lee_sin_descomprimir(archivo_zip: Path):
    tabla = read_zip_table(archivo_zip, "chico.txt")
    assert tabla.to_dict("records") == [{"x": 1, "y": 2}]
    con_texto = read_zip_table(archivo_zip, "chico.txt", dtype=str)
    assert con_texto.x.iloc[0] == "1"


def test_read_zip_table_avisa_que_archivos_hay(archivo_zip: Path):
    with pytest.raises(KeyError, match="chico.txt"):
        read_zip_table(archivo_zip, "inexistente.txt")


def test_read_zip_table_quita_la_marca_inicial_utf8(tmp_path: Path):
    destino = tmp_path / "con_bom.zip"
    with zipfile.ZipFile(destino, "w") as z:
        z.writestr("t.txt", "﻿columna,otra\n1,2\n")
    tabla = read_zip_table(destino, "t.txt")
    assert list(tabla.columns) == ["columna", "otra"], "la marca inicial ensucia el encabezado"


def test_iter_zip_table_recorre_por_bloques(archivo_zip: Path):
    bloques = list(iter_zip_table(archivo_zip, "grande.txt", chunksize=100))
    assert len(bloques) == 5
    assert sum(len(b) for b in bloques) == 500
    assert pd.concat(bloques).a.sum() == sum(range(500))


# ------------------------------------------------------------------------- inventario
def test_manifest_lista_lo_descargado_con_su_licencia(fuente: DataSource, tmp_path: Path):
    carpeta = tmp_path / "original"
    fetch(fuente, carpeta / "datos.csv")
    inventario = manifest(carpeta)
    assert len(inventario) == 1
    fila = inventario.iloc[0]
    assert fila.archivo == "datos.csv"
    assert fila.fuente == "fuente-de-prueba"
    assert fila.licencia_verificada == "no"
    assert manifest(tmp_path / "no-existe").empty


# -------------------------------------------------- estado real del catálogo del repo
def test_el_catalogo_del_repositorio_declara_fuentes_consistentes():
    assert CATALOG, "el catálogo no debe estar vacío"
    for nombre, fuente in CATALOG.items():
        assert nombre == fuente.name
        assert fuente.publisher.strip()
        assert fuente.description.strip()
        assert fuente.licence.strip()


def test_la_fuente_del_gtfs_resuelve_su_enlace_y_no_finge_licencia():
    fuente = get("gtfs-red-movilidad")
    assert "dtpm.cl" in fuente.url
    assert fuente.link_pattern, "el nombre del archivo cambia: hay que resolver el enlace"
    assert not fuente.licence_verified, (
        "la licencia de este feed no se verificó; declararla verificada sería falso"
    )
    with pytest.raises(KeyError, match="Disponibles"):
        get("fuente-inexistente")
