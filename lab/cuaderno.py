"""Cuadernos de trabajo: el mismo problema resuelto en Pandas y en Excel, paso a paso.

Qué hace
    Toma una lista de pasos declarados —objetivo, código de Pandas, equivalente en
    Excel, trampa— los **ejecuta**, captura la salida real de cada uno, y escribe un
    solo documento que se lee de arriba abajo sin saltar a ningún otro archivo.

Por qué existe
    Un caso resuelto y un caso que se puede estudiar no son lo mismo.

    Los casos del laboratorio documentaban **qué se encontró**: las cifras, los
    defectos, lo que no se puede concluir. Eso sirve para auditar el resultado y no
    sirve para aprender a producirlo. Quien se prepara para una evaluación técnica de
    Excel y Pandas necesita ver otra cosa: **el código, su salida, y cómo se hace lo
    mismo en una planilla**.

    Y lo necesita en un archivo, no repartido entre un README que cuenta hallazgos, un
    `solution.py` de seiscientas líneas y una tabla de equivalencias en otra carpeta.

La propiedad que hace que el documento sirva
    El código que se muestra **es** el código que se ejecutó, y la salida **es** la que
    devolvió. No hay transcripción a mano en ninguna parte, de modo que el documento no
    puede desviarse del comportamiento real: si el código deja de funcionar, el cuaderno
    no se genera.

    Eso vale más de lo que parece. Un apunte con salidas copiadas a mano envejece sin
    avisar, y el día que se estudia ya no describe lo que pasa.

Las cuatro partes de un paso
    - **Objetivo**: qué se consigue. Una línea, en el lenguaje del problema y no de la
      herramienta.
    - **Pandas**: el código. Corto a propósito: si un paso necesita quince líneas, son
      varios pasos.
    - **Excel**: la fórmula o el camino de menú que hace lo mismo, con los nombres de
      función en español, siguiendo la convención de `docs/equivalencias.md`.
    - **Trampa**: qué sale mal al hacerlo de la forma obvia. Es la parte que no está en
      ningún tutorial y la que se pregunta en una evaluación.

Cómo se usa
    Cada caso declara su cuaderno en un módulo `cuaderno.py` con dos cosas: un
    diccionario `CONTEXTO` con los objetos sobre los que corre el código, y una lista
    `PASOS`. `scripts/build_cuadernos.py` los recorre y escribe `CUADERNO.md` en la
    carpeta del caso.

Sobre ejecutar código declarado como texto
    Los fragmentos se evalúan con `eval` y `exec` en un espacio de nombres que el caso
    provee. Es código **del propio repositorio**, versionado y revisado como cualquier
    otro, no entrada de nadie: la alternativa —envolver cada fragmento en una función y
    mostrar su fuente— añade una línea `def` y un docstring a cada ejemplo y vuelve el
    documento ilegible para lo que se necesita aquí.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

#: Filas que se muestran de un resultado tabular, salvo que el paso pida otra cosa.
#: Seis es suficiente para reconocer la forma de la tabla sin tapar el resto del
#: documento.
FILAS_POR_DEFECTO = 6

#: Ancho máximo de una celda al renderizar. Una dirección de ochenta caracteres rompe
#: la tabla de Markdown y no aporta nada al ejemplo.
ANCHO_CELDA = 46


@dataclass(frozen=True)
class Paso:
    """Un paso de un cuaderno de trabajo.

    Attributes:
        titulo: qué hace el paso, en el lenguaje del problema.
        objetivo: por qué hace falta. Una o dos líneas.
        pandas: el código. Se ejecuta tal como se muestra.
        excel: cómo se hace lo mismo en una planilla. Fórmula con nombres de función en
            español, o el camino de menú cuando no hay fórmula.
        trampa: qué sale mal al hacerlo de la forma obvia. Opcional, y es la parte más
            valiosa cuando existe.
        filas: filas a mostrar del resultado.
        mostrar: `"tabla"`, `"valor"`, `"texto"` o `"auto"`.
        guardar_como: nombre con el que el resultado queda disponible para los pasos
            siguientes. Sin esto, el resultado se muestra y se descarta.
    """

    titulo: str
    objetivo: str
    pandas: str
    excel: str
    trampa: str = ""
    filas: int = FILAS_POR_DEFECTO
    mostrar: str = "auto"
    guardar_como: str = ""


@dataclass
class Cuaderno:
    """Un cuaderno completo: la pregunta, los datos y los pasos."""

    caso: str
    titulo: str
    pregunta: str
    datos: str
    pasos: list[Paso]
    contexto: dict[str, Any] = field(default_factory=dict)
    cierre: str = ""
    reproducir: str = ""


def _recortar(valor: object) -> str:
    """Un valor listo para una celda de Markdown: sin tuberías y sin desbordar."""
    texto = "" if valor is None or (isinstance(valor, float) and pd.isna(valor)) else str(valor)
    texto = texto.replace("|", "\\|").replace("\n", " ")
    if len(texto) > ANCHO_CELDA:
        texto = texto[: ANCHO_CELDA - 1] + "…"
    return texto


def _tabla_markdown(frame: pd.DataFrame, filas: int) -> str:
    """Un DataFrame como tabla de Markdown, recortado y con el total declarado."""
    vista = frame.head(filas)
    columnas = [str(c) for c in vista.columns]
    lineas = ["| " + " | ".join(columnas) + " |",
              "| " + " | ".join("---" for _ in columnas) + " |"]
    for _, fila in vista.iterrows():
        lineas.append("| " + " | ".join(_recortar(v) for v in fila) + " |")
    pie = f"\n*{len(frame)} filas × {len(frame.columns)} columnas"
    if len(frame) > filas:
        pie += f", se muestran las primeras {filas}"
    pie += ".*"
    return "\n".join(lineas) + pie


def _serie_markdown(serie: pd.Series, filas: int) -> str:
    """Una Series como tabla de dos columnas: el índice y el valor."""
    vista = serie.head(filas)
    nombre = str(serie.name) if serie.name is not None else "valor"
    indice = str(serie.index.name) if serie.index.name else ""
    lineas = [f"| {indice} | {nombre} |", "| --- | --- |"]
    for clave, valor in vista.items():
        lineas.append(f"| {_recortar(clave)} | {_recortar(valor)} |")
    pie = f"\n*{len(serie)} valores"
    if len(serie) > filas:
        pie += f", se muestran los primeros {filas}"
    pie += ".*"
    return "\n".join(lineas) + pie


def _renderizar_resultado(resultado: object, paso: Paso) -> str:
    """El resultado de un paso, en la forma que le corresponda."""
    modo = paso.mostrar
    if modo == "auto":
        if isinstance(resultado, pd.DataFrame):
            modo = "tabla"
        elif isinstance(resultado, pd.Series):
            modo = "serie"
        elif resultado is None:
            return ""
        else:
            modo = "valor"

    if modo == "tabla" and isinstance(resultado, pd.DataFrame):
        return _tabla_markdown(resultado, paso.filas)
    if modo == "serie" and isinstance(resultado, pd.Series):
        return _serie_markdown(resultado, paso.filas)
    if modo == "texto":
        return "```\n" + str(resultado).rstrip() + "\n```"
    # valor
    return "```\n" + repr(resultado) + "\n```"


def ejecutar(cuaderno: Cuaderno) -> list[tuple[Paso, object]]:
    """Ejecuta los pasos en orden y devuelve cada uno con su resultado.

    Raises:
        RuntimeError: si un paso falla, con su número y su título. Un cuaderno que no
            se puede ejecutar no se publica: es la propiedad que impide que el documento
            se desvíe del comportamiento real.
    """
    espacio: dict[str, Any] = {"pd": pd, **cuaderno.contexto}
    salidas: list[tuple[Paso, object]] = []
    for numero, paso in enumerate(cuaderno.pasos, start=1):
        codigo = paso.pandas.strip()
        try:
            try:
                resultado = eval(codigo, espacio)  # noqa: S307 — código del repositorio
            except SyntaxError:
                # Varias sentencias, o una asignación: se ejecuta y se toma la última
                # expresión si la hay.
                lineas = codigo.splitlines()
                exec("\n".join(lineas[:-1]), espacio)  # noqa: S102
                ultima = lineas[-1].strip()
                try:
                    resultado = eval(ultima, espacio)  # noqa: S307
                except SyntaxError:
                    exec(ultima, espacio)  # noqa: S102
                    resultado = None
        except Exception as error:  # noqa: BLE001 — se reenvía con contexto
            raise RuntimeError(
                f"El paso {numero} del cuaderno de {cuaderno.caso} "
                f"(«{paso.titulo}») falló: {type(error).__name__}: {error}"
            ) from error
        if paso.guardar_como:
            espacio[paso.guardar_como] = resultado
        salidas.append((paso, resultado))
    return salidas


def render(cuaderno: Cuaderno) -> str:
    """El cuaderno completo como un documento de Markdown."""
    salidas = ejecutar(cuaderno)
    buffer = io.StringIO()
    escribir = buffer.write

    escribir(f"# {cuaderno.caso} · Cuaderno de trabajo\n\n")
    escribir(f"## {cuaderno.titulo}\n\n")
    escribir(f"**La pregunta.** {cuaderno.pregunta}\n\n")
    escribir(f"**Los datos.** {cuaderno.datos}\n\n")
    escribir(
        "Este documento se lee de arriba abajo y no hay que abrir nada más. Cada paso "
        "trae el código de Pandas, **la salida que devuelve de verdad**, y cómo se hace "
        "lo mismo en Excel.\n\n"
    )

    escribir("### Los pasos\n\n")
    # Sin columna de Excel: el equivalente no cabe recortado a una celda, y recortado
    # no informa. Va completo en cada paso, que es donde se necesita.
    escribir("| # | Paso | Dónde está la trampa |\n| --- | --- | --- |\n")
    for numero, (paso, _) in enumerate(salidas, start=1):
        marca = "sí" if paso.trampa else "—"
        escribir(
            f"| {numero} | [{paso.titulo}](#paso-{numero}) | {marca} |\n"
        )
    con_trampa = sum(1 for paso, _ in salidas if paso.trampa)
    escribir(
        f"\n{len(salidas)} pasos, {con_trampa} con una trampa que conviene conocer "
        "antes de que aparezca en un dato propio.\n\n---\n\n"
    )

    for numero, (paso, resultado) in enumerate(salidas, start=1):
        escribir(f'<a id="paso-{numero}"></a>\n\n')
        escribir(f"## Paso {numero} · {paso.titulo}\n\n")
        escribir(f"{paso.objetivo}\n\n")
        escribir("**En Pandas**\n\n```python\n" + paso.pandas.strip() + "\n```\n\n")
        cuerpo = _renderizar_resultado(resultado, paso)
        if cuerpo:
            escribir("**Lo que devuelve**\n\n" + cuerpo + "\n\n")
        escribir(f"**En Excel**\n\n{paso.excel}\n\n")
        if paso.trampa:
            escribir(f"> **La trampa.** {paso.trampa}\n\n")
        escribir("---\n\n")

    if cuaderno.cierre:
        escribir("## Qué quedó resuelto\n\n" + cuaderno.cierre.strip() + "\n\n")
    if cuaderno.reproducir:
        escribir(
            "## Reproducir\n\n```powershell\n" + cuaderno.reproducir.strip() + "\n```\n"
        )
    return buffer.getvalue()
