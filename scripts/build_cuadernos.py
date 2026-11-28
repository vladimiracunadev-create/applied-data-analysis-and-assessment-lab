"""Genera los cuadernos de trabajo de los casos que declaran uno, y su índice.

Un cuaderno es el caso resuelto **paso a paso**: el problema explicado como problema, el
plan de la solución antes de ejecutarla, y para cada paso el código de Python, la salida
que devuelve de verdad, la fórmula de Excel dibujada en su hoja y una visualización
estadística. Cada caso incluye además un trío comparable en Pandas, Polars y R. Se lee de
arriba abajo sin abrir ningún otro archivo.

Qué escribe por cada caso

    CUADERNO.md                      el documento
    cuaderno/pasos.py                el código seguido, que corre y muestra sus salidas
    cuaderno/solucion_pandas.py      referencia comparable y gráfico Matplotlib
    cuaderno/solucion_polars.py      contraste columnar y gráfico Matplotlib
    cuaderno/solucion.R              contraste dplyr/readr y gráfico ggplot2
    cuaderno/solucion.Rmd            distribución para RStudio y Posit Cloud
    cuaderno/practica.xlsx           las fórmulas y el resultado que deben dar
    cuaderno/svg/flujo.svg           el diagrama del problema
    cuaderno/svg/mapa.svg            el mapa mental de la solución
    cuaderno/svg/paso-NN*.svg        las figuras y las hojas de Excel de cada paso
    cuaderno/caso-completo.zip       todo lo anterior, más el caso, en un archivo

Y un índice común en `docs/cuadernos.md`, con el estado de los problemas publicados.

Por qué se genera y no se escribe
    El código que aparece es el que se ejecutó y la salida es la que devolvió. Si el
    código deja de funcionar, el cuaderno no se genera: no hay forma de que el documento
    mienta y siga publicado. Un apunte con salidas copiadas a mano envejece sin avisar.

Necesita los datos descargados
    A diferencia de `build_docs.py`, este script **ejecuta el caso**. No corre en
    integración continua por eso, y lo que produce se versiona —texto, código y
    agregados, nunca datos de terceros—, igual que las tablas de `resultados/`.

Uso
    python scripts/build_cuadernos.py                # todos los declarados
    python scripts/build_cuadernos.py bip_lugares_carga
    python scripts/build_cuadernos.py --check        # falla si alguno quedó desfasado
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lab.console import enable_utf8  # noqa: E402
from lab.cuaderno import (  # noqa: E402
    ARCHIVO_IPYNB,
    ARCHIVO_PY,
    ARCHIVO_XLSX,
    CARPETA,
    ejecutar,
    escribir_colab,
    escribir_implementaciones,
    escribir_pasos_py,
    escribir_practica_xlsx,
    escribir_zip,
    nombre_zip,
    render,
    url_colab,
)

NOMBRE_SALIDA = "CUADERNO.md"

#: El índice de cuadernos, al que apunta la navegación de cada uno. Se genera para que
#: no se desvíe: un índice escrito a mano envejece en cuanto se agrega un cuaderno.
INDICE_SALIDA = ROOT / "docs" / "cuadernos.md"

#: Los problemas de la instancia DTPM, con el caso que los resuelve. El estado
#: detallado vive en `docs/problemas-de-la-instancia.md`; aquí solo hace falta saber a
#: qué caso mirar. Un problema sin caso necesita el análisis además del cuaderno, y el
#: cuarto elemento dice en qué pasos de otro cuaderno queda cubierto, cuando no tiene
#: uno propio: decir «abrir» sin más haría creer que hay un cuaderno dedicado.
PROBLEMAS: tuple[tuple[str, str, str, str], ...] = (
    ("P01", "Consolidar los cinco Excel de lugares de carga", "bip_lugares_carga", ""),
    ("P02", "¿El código es una clave?", "bip_lugares_carga", "pasos 7 a 9"),
    ("P03", "Validación cruzada de coordenadas", "correspondencia_metro", ""),
    ("P04", "Normalizar comuna y entidad para agrupar", "bip_lugares_carga", "pasos 10 a 12"),
    ("P05", "Interpretar horarios escritos en texto libre", "carga_nocturna", ""),
    ("P06", "Expediciones por hora en un día laboral", "gtfs_red_movilidad", ""),
    ("P07", "¿Cuándo conviene dejar Pandas?", "rendimiento_gtfs", ""),
    ("P08", "Distancia de cada parada al lugar de carga", "cobertura_de_carga", ""),
    ("P09", "Cobertura de carga en el servicio nocturno", "carga_nocturna", ""),
    ("P10", "Correspondencia entre buses y Metro", "correspondencia_metro", ""),
    ("P11", "El calendario de medición de un indicador oficial", "calendario_medicion", ""),
    ("P12", "El ICF sobre la oferta programada", "frecuencia_programada", ""),
    ("P13", "Distribución de la frecuencia programada", "frecuencia_programada", ""),
    ("P14", "Qué cambió entre dos versiones del feed", "evolucion_gtfs", ""),
    ("P15", "Evolución de la oferta programada por año", "evolucion_gtfs", ""),
    ("P16", "Informe de una página para quien decide", "informe_decision_carga", ""),
    ("P17", "Gobernanza y catálogo de activos de datos", "gobernanza_datos_dtpm", ""),
    ("P18", "ETL histórico y control automatizado GTFS", "etl_gtfs_automatizado", ""),
)


def casos_con_cuaderno() -> list[str]:
    """Los casos que declaran un cuaderno, en orden alfabético."""
    return sorted(
        ruta.parent.name
        for ruta in (ROOT / "cases").glob("*/cuaderno.py")
    )


def construir(slug: str, artefactos: bool = True) -> tuple[Path, str, list[str]]:
    """Genera el cuaderno de un caso, sus figuras y sus artefactos descargables.

    Returns:
        La ruta del `CUADERNO.md`, su contenido, y los artefactos escritos junto a él.
    """
    modulo = importlib.import_module(f"cases.{slug}.cuaderno")
    if not hasattr(modulo, "construir"):
        raise AttributeError(
            f"cases/{slug}/cuaderno.py no define construir(); "
            "tiene que devolver un lab.cuaderno.Cuaderno"
        )
    cuaderno = modulo.construir()
    from lab.notebook_enrichment import enriquecer_cuaderno
    cuaderno = enriquecer_cuaderno(slug, cuaderno)
    carpeta_caso = ROOT / "cases" / slug
    carpeta = carpeta_caso / CARPETA
    svg = carpeta / "svg"
    if artefactos:
        svg.mkdir(parents=True, exist_ok=True)

    documento = render(cuaderno, carpeta=svg if artefactos else None, slug=slug)
    destino = carpeta_caso / NOMBRE_SALIDA
    escritos: list[str] = []
    if artefactos:
        salidas = ejecutar(cuaderno, carpeta=svg)
        escribir_pasos_py(cuaderno, salidas, carpeta / ARCHIVO_PY)
        escritos.append(f"{CARPETA}/{ARCHIVO_PY}")
        escribir_practica_xlsx(cuaderno, salidas, carpeta / ARCHIVO_XLSX)
        escritos.append(f"{CARPETA}/{ARCHIVO_XLSX}")
        escribir_colab(cuaderno, salidas, slug, carpeta / ARCHIVO_IPYNB)
        escritos.append(f"{CARPETA}/{ARCHIVO_IPYNB}")
        for ruta in escribir_implementaciones(cuaderno, carpeta):
            escritos.append(f"{CARPETA}/{ruta.name}")
        escritos.extend(
            f"{CARPETA}/svg/{ruta.name}" for ruta in sorted(svg.glob("*.svg"))
        )
        # El documento se escribe antes del ZIP, para que el ZIP lo lleve dentro.
        destino.write_text(documento, encoding="utf-8")
        zip_nombre = nombre_zip(cuaderno.caso)
        escribir_zip(cuaderno, carpeta_caso, carpeta / zip_nombre)
        escritos.append(f"{CARPETA}/{zip_nombre}")
    return destino, documento, escritos


def codigo_de(slug: str) -> str:
    """El código del problema cuyo caso lleva ese slug como cuaderno propio."""
    for codigo, _, otro, donde in PROBLEMAS:
        if otro == slug and not donde:
            return codigo
    return slug


def escribir_indice(con_cuaderno: set[str]) -> Path:
    """Escribe el índice de cuadernos, con el estado de los problemas publicados."""
    lineas = [
        "# Cuadernos de trabajo",
        "",
        "Un **cuaderno** es el problema resuelto paso a paso: el problema explicado como",
        "problema, el plan de la solución antes de ejecutarla, y para cada paso el",
        "código de Python, la salida que devuelve de verdad, la fórmula de Excel y",
        "contrastes ejecutables en Polars y R. Cada caso incluye al menos un gráfico",
        "estadístico con unidades, período y fuente. Se lee de arriba abajo y trae",
        "sus descargables al lado, incluido un ZIP con todo el caso.",
        "",
        "No es lo mismo que el `README.md` de un caso, que cuenta **qué se encontró** y",
        "sirve para auditar el resultado.",
        "",
        "> Archivo generado por `scripts/build_cuadernos.py`. No lo edite a mano.",
        "",
        "## Ruta lineal de los cuadernos",
        "",
        "La navegación anterior/siguiente sigue este orden, sin saltar del P01 al P08:",
        "",
    ]
    from lab.notebook_enrichment import NAVIGATION
    for position, (slug, label) in enumerate(NAVIGATION, start=1):
        lineas.append(
            f"{position}. [{label}](../cases/{slug}/{NOMBRE_SALIDA}) · "
            f"[Abrir en Colab]({url_colab(slug)})"
        )
    lineas += [
        "",
        f"## Los {len(PROBLEMAS)} problemas de la instancia DTPM",
        "",
        "| Problema | Cuaderno | Caso |",
        "| --- | --- | --- |",
    ]
    cuadernos_distintos: set[str] = set()
    cubiertos_en_otro = 0
    primer_codigo_por_slug: dict[str, str] = {}
    for codigo, titulo, slug, donde in PROBLEMAS:
        ruta = f"../cases/{slug}/{NOMBRE_SALIDA}"
        if slug and slug in con_cuaderno and not donde:
            if slug in primer_codigo_por_slug:
                primero = primer_codigo_por_slug[slug]
                enlace = f"[mismo cuaderno que {primero}]({ruta})"
                cubiertos_en_otro += 1
            else:
                enlace = f"[**abrir**]({ruta})"
                primer_codigo_por_slug[slug] = codigo
                cuadernos_distintos.add(slug)
        elif slug and slug in con_cuaderno:
            enlace = f"[dentro del de {codigo_de(slug)}, {donde}]({ruta})"
            cubiertos_en_otro += 1
        elif slug:
            enlace = "pendiente"
        else:
            enlace = "pendiente · falta el análisis"
        caso = f"[`{slug}`](../cases/{slug}/README.md)" if slug else "—"
        lineas.append(f"| {codigo} · {titulo} | {enlace} | {caso} |")

    cubiertos = len(cuadernos_distintos) + cubiertos_en_otro
    resumen = [
        "",
        f"**{len(cuadernos_distintos)} cuadernos distintos cubren "
        f"{cubiertos} de {len(PROBLEMAS)} problemas**:",
        f"{cubiertos_en_otro} están integrados en el cuaderno de un problema relacionado.",
    ]
    if cubiertos < len(PROBLEMAS):
        resumen += ["Los problemas sin caso necesitan el análisis además del cuaderno."]
    resumen += [
        "El estado detallado de cada uno, con lo que enseña y lo que no se puede",
        "contestar, está en el [mapa de problemas](problemas-de-la-instancia.md).",
        "",
        "## Regenerar",
        "",
        "```powershell",
        "python scripts/build_cuadernos.py",
        "```",
        "",
        "Necesita los datos descargados: un cuaderno se genera **ejecutando el caso**,",
        "de modo que el código que aparece es el que corrió y la salida es la que",
        "devolvió.",
    ]
    lineas += resumen
    INDICE_SALIDA.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return INDICE_SALIDA


def main() -> int:
    enable_utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("casos", nargs="*", help="slugs a generar; por defecto, todos")
    parser.add_argument(
        "--check", action="store_true",
        help="no escribe: falla si algún cuaderno quedó desfasado del código",
    )
    argumentos = parser.parse_args()

    seleccion = argumentos.casos or casos_con_cuaderno()
    if not seleccion:
        print("Ningún caso declara un cuaderno todavía.")
        return 0

    desfasados: list[str] = []
    for slug in seleccion:
        # Con --check no se escriben artefactos: solo se comprueba que el documento
        # siga siendo el que el código produce.
        destino, documento, escritos = construir(slug, artefactos=not argumentos.check)
        relativo = destino.relative_to(ROOT).as_posix()
        if argumentos.check:
            actual = destino.read_text(encoding="utf-8") if destino.exists() else ""
            if actual != documento:
                desfasados.append(relativo)
                print(f"desfasado {relativo}")
            else:
                print(f"al día    {relativo}")
            continue
        pasos = documento.count("\n### Paso ")
        print(f"escrito {relativo}  ({pasos} pasos, {len(documento):,} caracteres)")
        for artefacto in escritos:
            print(f"        + cases/{slug}/{artefacto}")

    if not argumentos.check:
        indice = escribir_indice(set(casos_con_cuaderno()))
        print(f"escrito {indice.relative_to(ROOT).as_posix()}")

    if desfasados:
        print(
            f"\n{len(desfasados)} cuaderno(s) desfasado(s). "
            "Ejecute: python scripts/build_cuadernos.py"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
