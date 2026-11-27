"""Cuadernos de trabajo: un problema resuelto y contrastado en varios motores.

Qué hace
    Toma una lista de pasos declarados —objetivo, código de Pandas, equivalente en
    Excel, trampa— los **ejecuta**, captura la salida real de cada uno, y escribe un
    solo documento que se lee de arriba abajo sin saltar a ningún otro archivo.

Por qué existe
    Un caso resuelto y un caso que se puede estudiar no son lo mismo.

    Los casos del laboratorio documentaban **qué se encontró**: las cifras, los
    defectos, lo que no se puede concluir. Eso sirve para auditar el resultado y no
    sirve para aprender a producirlo. Quien se prepara para una evaluación técnica de
    Excel y Pandas necesita ver otra cosa: **el código, su salida, cómo se hace lo
    mismo en una planilla y cómo se contrasta en Polars y R**.

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

Contraste y visualización
    Cada cuaderno agrega una implementación completa en Polars con Matplotlib y otra en
    R con ggplot2. Ambas leen el contrato de resultado versionado del caso, recalculan
    el indicador central y producen una gráfica con unidad, período y fuente visibles.

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

import ast
import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from lab.diagrama_svg import Flujo, Mapa, render_flujo, render_mapa
from lab.hoja_svg import Hoja, render_hoja

#: Filas que se muestran de un resultado tabular, salvo que el paso pida otra cosa.
#: Seis es suficiente para reconocer la forma de la tabla sin tapar el resto del
#: documento.
FILAS_POR_DEFECTO = 6

#: Ancho máximo de una celda al renderizar. Una dirección de ochenta caracteres rompe
#: la tabla de Markdown y no aporta nada al ejemplo.
ANCHO_CELDA = 46

#: Carpeta, junto al `CUADERNO.md`, donde viven los artefactos descargables: el script
#: con los pasos, el libro de práctica y las figuras.
CARPETA = "cuaderno"

#: El script con los pasos seguidos, para correr y para tener abierto al lado mientras
#: se practica. Es el código sin la prosa.
ARCHIVO_PY = "pasos.py"

#: El libro de práctica: las fórmulas de Excel y el resultado que deben dar. **Sin
#: datos de terceros**: quien practica pega el consolidado que obtuvo él mismo.
ARCHIVO_XLSX = "practica.xlsx"

#: El cuaderno ejecutable para Google Colab. Mismo contenido que el documento, en celdas.
ARCHIVO_IPYNB = "colab.ipynb"

#: Implementaciones comparables completas que acompañan a cada cuaderno.
ARCHIVO_POLARS = "solucion_polars.py"
ARCHIVO_R = "solucion.R"

#: Repositorio público, para el botón de Colab y el clonado del cuaderno ejecutable.
REPO = "vladimiracunadev-create/applied-data-analysis-and-assessment-lab"

#: Plantilla del ZIP con todo el contenido del caso. Lleva el código del problema en
#: el nombre para que, descargado entre otros, se reconozca de qué caso es.
PLANTILLA_ZIP = "{caso}-caso-completo.zip"


def nombre_zip(caso: str) -> str:
    """El nombre del ZIP de un caso, por ejemplo `P01-caso-completo.zip`."""
    return PLANTILLA_ZIP.format(caso=caso)

#: El índice de todos los cuadernos, al que apunta la navegación de cada uno.
INDICE = "../../docs/cuadernos.md"


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
        figura: código que produce un SVG y devuelve su ruta. Se ejecuta en el mismo
            espacio de nombres, de modo que puede usar lo que los pasos anteriores
            guardaron. El SVG se incrusta en el documento.
        pie_figura: qué mirar en la figura. Una línea.
        formula_excel: la fórmula sola, sin prosa, para la hoja de práctica. Si está
            vacía, el paso no entra en el libro de Excel.
        esperado: el resultado que esa fórmula debe dar sobre el archivo real. Es lo que
            permite que la hoja de práctica corrija por su cuenta.
        hoja: fragmento de hoja de cálculo a dibujar, con la fórmula en su celda. Una
            fórmula en prosa no dice dónde va ni sobre qué rango opera; dibujada, sí.
        sheets: qué cambia en Google Sheets. **Solo cuando cambia**: la mayoría de las
            funciones se llaman igual, y repetir la misma fórmula dos veces hace creer
            que son distintas. Si está vacío, el cuaderno dice que es idéntica.
    """

    titulo: str
    objetivo: str
    pandas: str
    excel: str
    trampa: str = ""
    filas: int = FILAS_POR_DEFECTO
    mostrar: str = "auto"
    guardar_como: str = ""
    figura: str = ""
    pie_figura: str = ""
    formula_excel: str = ""
    esperado: str = ""
    hoja: Hoja | None = None
    sheets: str = ""


@dataclass(frozen=True)
class Implementacion:
    """Una implementación ejecutable alternativa incluida en el cuaderno."""

    motor: str
    lenguaje: str
    archivo: str
    comando: str
    alcance: str
    codigo: str


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
    #: Líneas de importación que `pasos.py` necesita para correr por su cuenta. Se
    #: escriben una vez por caso en lugar de repetirlas en cada paso.
    importes: str = ""
    #: Fuentes que `scripts/fetch_data.py` debe descargar para que el cuaderno de
    #: Colab corra. Sin esto, la celda de preparación no descarga nada.
    fuentes_datos: str = ""
    #: Paquetes opcionales que este cuaderno necesita en Colab. Vacío mantiene el
    #: entorno mínimo; por ejemplo, P07 declara DuckDB solo para su benchmark.
    dependencias_colab: str = ""
    #: Encabezados de la hoja donde se pega el consolidado, en su orden. Son los que
    #: hacen que las referencias de las fórmulas —`A2`, `$E$2:$E$1929`— sean correctas.
    columnas_excel: tuple[str, ...] = ()
    #: El problema explicado como problema: de dónde sale, a quién le importa y qué lo
    #: vuelve difícil. Varios párrafos, antes de cualquier código.
    problema: str = ""
    #: Qué se va a hacer y en qué orden, **antes** de hacerlo. Un plan, no un resumen.
    solucion: str = ""
    #: Diagrama del problema: de dónde vienen los datos y qué sale.
    flujo: Flujo | None = None
    #: Mapa mental de la solución: los pasos agrupados por bloque.
    mapa: Mapa | None = None
    #: Qué se aprende, en una lista. Va al final, cuando ya se vio todo.
    aprendizajes: tuple[str, ...] = ()
    #: Cuadernos y documentos con los que este se relaciona: `(texto, ruta)`.
    relacionados: tuple[tuple[str, str], ...] = ()
    #: Navegación entre cuadernos: `(texto, ruta)` del anterior y del siguiente.
    anterior: tuple[str, str] | None = None
    siguiente: tuple[str, str] | None = None
    #: Implementaciones ejecutables que resuelven el indicador principal con otro
    #: motor. Se publican como archivos y también se muestran dentro del cuaderno.
    implementaciones: tuple[Implementacion, ...] = ()


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


@dataclass(frozen=True)
class Salida:
    """Un paso ya ejecutado: su resultado y el nombre de su figura, si tiene."""

    numero: int
    paso: Paso
    resultado: object
    svg: str = ""
    svg_hoja: str = ""


def ejecutar(cuaderno: Cuaderno, carpeta: Path | None = None) -> list[Salida]:
    """Ejecuta los pasos en orden, con sus figuras, y devuelve cada uno con su resultado.

    Args:
        cuaderno: el cuaderno a ejecutar.
        carpeta: dónde escribir los SVG. Sin ella, las figuras no se generan y el
            documento sale sin imágenes, que es lo que hace falta para `--check`.

    Raises:
        RuntimeError: si un paso falla, con su número y su título. Un cuaderno que no
            se puede ejecutar no se publica: es la propiedad que impide que el documento
            se desvíe del comportamiento real.
    """
    espacio: dict[str, Any] = {"pd": pd, **cuaderno.contexto}
    if carpeta is not None:
        espacio["CARPETA_SVG"] = carpeta
        # Los dos diagramas del cuaderno: el del problema y el de la solución.
        if cuaderno.flujo is not None:
            (carpeta / "flujo.svg").write_text(
                render_flujo(cuaderno.flujo), encoding="utf-8")
        if cuaderno.mapa is not None:
            (carpeta / "mapa.svg").write_text(
                render_mapa(cuaderno.mapa), encoding="utf-8")
    salidas: list[Salida] = []
    for numero, paso in enumerate(cuaderno.pasos, start=1):
        resultado = _correr(paso.pandas, espacio, cuaderno.caso, numero, paso.titulo)
        if paso.guardar_como:
            espacio[paso.guardar_como] = resultado
        # El nombre del SVG es **determinista**: depende del número de paso y de que el
        # paso declare una figura, no de si esta ejecución escribe archivos. Así el
        # documento que produce `--check` es idéntico al que se publica.
        svg = f"paso-{numero:02d}.svg" if paso.figura else ""
        svg_hoja = f"paso-{numero:02d}-excel.svg" if paso.hoja is not None else ""
        if carpeta is not None:
            if paso.figura:
                espacio["SVG_DESTINO"] = carpeta / svg
                _correr(paso.figura, espacio, cuaderno.caso, numero,
                        f"{paso.titulo} (figura)")
            if paso.hoja is not None:
                (carpeta / svg_hoja).write_text(
                    render_hoja(paso.hoja), encoding="utf-8"
                )
        salidas.append(Salida(numero=numero, paso=paso, resultado=resultado, svg=svg,
                              svg_hoja=svg_hoja))
    return salidas


def _correr(codigo: str, espacio: dict[str, Any], caso: str, numero: int,
            titulo: str) -> object:
    """Ejecuta un fragmento y devuelve el valor de su última expresión.

    La separación entre lo que se ejecuta y la última expresión se hace con `ast` y no
    contando líneas: un `def` de varias líneas, o un diccionario por comprensión,
    rompen cualquier partición por renglones.
    """
    antes, expresion = _partir_ultima_expresion(codigo.strip())
    try:
        if antes:
            exec(antes, espacio)  # noqa: S102 — código del repositorio
        if not expresion:
            return None
        return eval(expresion, espacio)  # noqa: S307 — código del repositorio
    except Exception as error:  # noqa: BLE001 — se reenvía con contexto
        raise RuntimeError(
            f"El paso {numero} del cuaderno de {caso} («{titulo}») falló: "
            f"{type(error).__name__}: {error}"
        ) from error


def _enlace(par: tuple[str, str] | None) -> str:
    """Un par `(texto, ruta)` como enlace de Markdown. Vacío si no hay par."""
    if not par:
        return ""
    texto, ruta = par
    return f"[{texto}]({ruta})"


def render(cuaderno: Cuaderno, carpeta: Path | None = None,
           slug: str = "") -> str:
    """El cuaderno completo como documento de Markdown.

    El orden no es casual. Primero **el problema**, porque sin él los pasos son
    manipulaciones sin motivo. Después **el plan**, para saber a dónde va cada paso
    antes de darlo. Luego los pasos. Y al final el resultado, lo que se aprende y los
    límites de lo que se puede afirmar.
    """
    salidas = ejecutar(cuaderno, carpeta)
    buffer = io.StringIO()
    escribir = buffer.write
    con_trampa = sum(1 for s in salidas if s.paso.trampa)

    # ------------------------------------------------------------------ encabezado
    escribir(f"# {cuaderno.caso} · {cuaderno.titulo}\n\n")
    navegacion = [
        _enlace(cuaderno.anterior) and f"◀ {_enlace(cuaderno.anterior)}",
        f"[Todos los cuadernos]({INDICE})",
        _enlace(cuaderno.siguiente) and f"{_enlace(cuaderno.siguiente)} ▶",
    ]
    escribir(" · ".join(parte for parte in navegacion if parte) + "\n\n")
    if slug:
        escribir(
            "[![Abrir en Colab](https://colab.research.google.com/assets/"
            f"colab-badge.svg)]({url_colab(slug)}) — corre los pasos sin instalar "
            "nada: el cuaderno clona el repositorio y descarga los datos del portal.\n\n"
        )
    escribir(f"> **{cuaderno.pregunta}**\n\n")

    # -------------------------------------------------------------------- el problema
    escribir("## 1 · El problema\n\n")
    if cuaderno.problema:
        escribir(cuaderno.problema.strip() + "\n\n")
    escribir(f"**Los datos.** {cuaderno.datos}\n\n")
    if cuaderno.flujo is not None:
        escribir(f"![El flujo del problema]({CARPETA}/svg/flujo.svg)\n\n")

    # -------------------------------------------------------------------- la solución
    escribir("## 2 · La solución que se va a aplicar\n\n")
    if cuaderno.solucion:
        escribir(cuaderno.solucion.strip() + "\n\n")
    if cuaderno.mapa is not None:
        escribir(f"![El recorrido]({CARPETA}/svg/mapa.svg)\n\n")

    if cuaderno.implementaciones:
        escribir("### El mismo resultado en Pandas, Polars y R\n\n")
        escribir(
            "La ruta principal de los pasos usa Pandas y Excel. Las implementaciones "
            "siguientes recalculan el indicador que sostiene la conclusión con otro "
            "motor y producen el mismo gráfico estadístico. El alcance queda declarado "
            "para no confundir validación independiente con una traducción cosmética.\n\n"
        )
        escribir("| Motor | Alcance verificado | Archivo | Ejecutar |\n")
        escribir("| --- | --- | --- | --- |\n")
        for implementacion in cuaderno.implementaciones:
            escribir(
                f"| {implementacion.motor} | {implementacion.alcance} | "
                f"[`{implementacion.archivo}`]({CARPETA}/{implementacion.archivo}) | "
                f"`{implementacion.comando}` |\n"
            )
        escribir("\n")
        for implementacion in cuaderno.implementaciones:
            escribir(f"#### {implementacion.motor}\n\n")
            escribir(f"```{implementacion.lenguaje}\n")
            escribir(implementacion.codigo.strip() + "\n```\n\n")

    escribir(
        f"{len(salidas)} pasos. Cada uno trae el código de **Python**, la salida que "
        f"devuelve de verdad, y la **fórmula de Excel** equivalente dibujada en su "
        f"hoja. {con_trampa} traen además la trampa de hacerlo de la forma obvia.\n\n"
    )
    escribir("| # | Paso | Trampa |\n| --- | --- | --- |\n")
    for salida in salidas:
        escribir(
            f"| {salida.numero} | [{salida.paso.titulo}](#paso-{salida.numero}) "
            f"| {'sí' if salida.paso.trampa else '—'} |\n"
        )
    escribir("\n")

    # ------------------------------------------------------------------- descargables
    escribir("### Para trabajar\n\n")
    escribir("| Archivo | Qué es |\n| --- | --- |\n")
    escribir(
        f"| [`{nombre_zip(cuaderno.caso)}`]"
        f"({CARPETA}/{nombre_zip(cuaderno.caso)}) "
        "| **todo el caso en un ZIP**: el cuaderno, el script, el libro de Excel y "
        "las figuras |\n"
    )
    escribir(
        f"| [`{ARCHIVO_PY}`]({CARPETA}/{ARCHIVO_PY}) "
        f"| los {len(salidas)} pasos seguidos. Se corre y muestra cada salida |\n"
    )
    escribir(
        f"| [`{ARCHIVO_XLSX}`]({CARPETA}/{ARCHIVO_XLSX}) "
        "| las fórmulas y **el resultado que deben dar**, para corregirse solo. "
        "Se abre igual en Google Sheets |\n"
    )
    if slug:
        escribir(
            f"| [`{ARCHIVO_IPYNB}`]({CARPETA}/{ARCHIVO_IPYNB}) "
            "| el cuaderno **ejecutable en Colab**: clona, descarga los datos del "
            f"portal y corre los {len(salidas)} pasos |\n"
        )
    for implementacion in cuaderno.implementaciones:
        escribir(
            f"| [`{implementacion.archivo}`]({CARPETA}/{implementacion.archivo}) "
            f"| solución ejecutable en {implementacion.motor}; incluye el contraste "
            "numérico y el gráfico del caso |\n"
        )
    escribir("\n---\n\n")

    # ------------------------------------------------------------------------ los pasos
    escribir("## 3 · Los pasos\n\n")
    for salida in salidas:
        paso = salida.paso
        escribir(f'<a id="paso-{salida.numero}"></a>\n\n')
        escribir(f"### Paso {salida.numero} · {paso.titulo}\n\n")
        escribir(f"{paso.objetivo}\n\n")

        escribir("#### Python\n\n```python\n" + paso.pandas.strip() + "\n```\n\n")
        cuerpo = _renderizar_resultado(salida.resultado, paso)
        if cuerpo:
            escribir(cuerpo + "\n\n")
        if salida.svg:
            escribir(f"![{paso.titulo}]({CARPETA}/svg/{salida.svg})\n\n")
            if paso.pie_figura:
                escribir(f"*{paso.pie_figura}*\n\n")

        escribir("#### Excel\n\n")
        if salida.svg_hoja:
            escribir(f"![La hoja]({CARPETA}/svg/{salida.svg_hoja})\n\n")
        escribir(f"{paso.excel}\n\n")
        if paso.esperado:
            escribir(f"Debe dar: **{paso.esperado}**\n\n")
        if paso.sheets:
            escribir(f"**En Google Sheets:** {paso.sheets}\n\n")
        elif paso.formula_excel:
            escribir("**En Google Sheets:** la misma fórmula, sin cambios.\n\n")
        if paso.trampa:
            cuerpo_trampa = paso.trampa.strip().replace("\n\n", "\n>\n> ")
            escribir(f"> **La trampa.** {cuerpo_trampa}\n\n")
        escribir("[↑ volver al recorrido](#2--la-solución-que-se-va-a-aplicar)\n\n")
        escribir("---\n\n")

    # -------------------------------------------------------------------- el resultado
    if cuaderno.cierre:
        escribir("## 4 · El resultado\n\n" + cuaderno.cierre.strip() + "\n\n")
    if cuaderno.aprendizajes:
        escribir("## 5 · Qué queda aprendido\n\n")
        for numero, aprendizaje in enumerate(cuaderno.aprendizajes, start=1):
            escribir(f"{numero}. {aprendizaje}\n")
        escribir("\n")
    if cuaderno.reproducir:
        escribir(
            "## Reproducir\n\n```powershell\n" + cuaderno.reproducir.strip()
            + "\n```\n\n"
        )

    # -------------------------------------------------------------------- navegación
    escribir("## Seguir\n\n")
    if cuaderno.relacionados:
        escribir("Lo que este caso toca y se trata a fondo en otro sitio:\n\n")
        for texto, ruta in cuaderno.relacionados:
            escribir(f"- [{texto}]({ruta})\n")
        escribir("\n")
    escribir(" · ".join(parte for parte in navegacion if parte) + "\n")
    return buffer.getvalue()


def escribir_zip(cuaderno: Cuaderno, carpeta_caso: Path, destino: Path) -> Path:
    """Empaqueta todo el contenido del caso en un ZIP.

    Lleva el cuaderno, el script, el libro de Excel y las figuras. **No lleva datos de
    terceros**: ni los archivos del portal ni nada derivado de ellos que los reconstruya.
    Lo que va dentro es texto, código y agregados, que es lo mismo que el repositorio
    versiona.
    """
    import zipfile

    destino.parent.mkdir(parents=True, exist_ok=True)
    nombre_base = f"{cuaderno.caso.lower()}-{carpeta_caso.name}"
    # Se escribe a un temporal y se reemplaza al final: si el ZIP se escribiera sobre sí
    # mismo mientras se recorre la carpeta, se incluiría a medio escribir.
    temporal = destino.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporal, "w", zipfile.ZIP_DEFLATED) as zf:
        for ruta in sorted(carpeta_caso.rglob("*")):
            if not ruta.is_file():
                continue
            relativa = ruta.relative_to(carpeta_caso)
            if relativa.suffix in {".zip", ".tmp"} or "__pycache__" in relativa.parts:
                continue
            zf.write(ruta, arcname=f"{nombre_base}/{relativa.as_posix()}")
    temporal.replace(destino)
    return destino


def escribir_pasos_py(cuaderno: Cuaderno, salidas: list[Salida], destino: Path) -> Path:
    """Escribe el script con los pasos seguidos, listo para correr y para leer.

    No es el cuaderno en otro formato: es el **código sin la prosa**, que es lo que
    alguien quiere tener abierto al lado mientras practica.
    """
    buffer = io.StringIO()
    buffer.write(f'"""{cuaderno.caso} · {cuaderno.titulo}\n\n')
    buffer.write(f"{cuaderno.pregunta}\n\n")
    buffer.write(
        "Generado por scripts/build_cuadernos.py desde cuaderno.py. No editar a mano.\n"
        'La explicación de cada paso está en CUADERNO.md.\n"""\n\n'
    )
    buffer.write("from __future__ import annotations\n\nimport sys\n")
    buffer.write("from pathlib import Path\n\n")
    buffer.write("ROOT = Path(__file__).resolve().parents[3]\n")
    buffer.write("if str(ROOT) not in sys.path:\n    sys.path.insert(0, str(ROOT))\n\n")
    for linea in cuaderno.importes.strip().splitlines():
        buffer.write(linea + "\n")
    buffer.write("\n\n")
    for salida in salidas:
        paso = salida.paso
        buffer.write("# " + "-" * 76 + "\n")
        buffer.write(f"# Paso {salida.numero} · {paso.titulo}\n")
        if paso.formula_excel:
            buffer.write(f"# En Excel: {paso.formula_excel}\n")
        if paso.trampa:
            for linea in _envolver("Trampa: " + _sin_markdown(paso.trampa), 74):
                buffer.write(f"# {linea}\n")
        buffer.write("# " + "-" * 76 + "\n")
        # La última expresión se envuelve en un print con la cabecera del paso: correr
        # el script tiene que **mostrar** las salidas, no calcularlas en silencio.
        antes, expresion = _partir_ultima_expresion(paso.pandas.strip())
        if antes:
            buffer.write(antes + "\n")
        if expresion:
            buffer.write(f'print("\\n=== Paso {salida.numero} · {paso.titulo} ===")\n')
            if "\n" in expresion:
                buffer.write("print(\n" + _sangrar(expresion, 4) + "\n)\n")
            else:
                buffer.write(f"print({expresion})\n")
        buffer.write("\n")
    destino.write_text(buffer.getvalue(), encoding="utf-8")
    return destino


def escribir_implementaciones(cuaderno: Cuaderno, carpeta: Path) -> list[Path]:
    """Escribe los motores alternativos exactamente como aparecen en el cuaderno."""
    escritos: list[Path] = []
    for implementacion in cuaderno.implementaciones:
        destino = carpeta / implementacion.archivo
        destino.write_text(implementacion.codigo.strip() + "\n", encoding="utf-8")
        escritos.append(destino)
    return escritos


def _sin_markdown(texto: str) -> str:
    """El texto sin los adornos de Markdown, para un comentario de Python."""
    return (
        texto.replace("**", "").replace("`", "").replace("—", "-").replace("\n", " ")
    )


def _envolver(texto: str, ancho: int) -> list[str]:
    """Parte un texto en líneas de hasta `ancho` caracteres, sin cortar palabras."""
    lineas: list[str] = []
    actual = ""
    for palabra in texto.split():
        if actual and len(actual) + 1 + len(palabra) > ancho:
            lineas.append(actual)
            actual = palabra
        else:
            actual = f"{actual} {palabra}".strip()
    if actual:
        lineas.append(actual)
    return lineas


def _sangrar(texto: str, espacios: int) -> str:
    """El texto con cada línea sangrada, para meterlo dentro de un `print(...)`."""
    relleno = " " * espacios
    return "\n".join(relleno + linea for linea in texto.splitlines())


def _partir_ultima_expresion(codigo: str) -> tuple[str, str]:
    """Separa el código en lo que se ejecuta y la última expresión, si la hay.

    Se decide con `ast` y no contando líneas, porque una expresión puede ocupar varias
    —un diccionario por comprensión, una llamada con argumentos en vertical— y partir
    por la última línea produce código roto.

    Returns:
        `(antes, expresion)`. Si el código no termina en una expresión, `expresion` es
        vacía y `antes` es todo.
    """
    try:
        arbol = ast.parse(codigo)
    except SyntaxError:
        return codigo, ""
    if not arbol.body or not isinstance(arbol.body[-1], ast.Expr):
        return codigo, ""

    renglones = codigo.splitlines()
    ultimo = arbol.body[-1]
    desde = (ultimo.lineno or 1) - 1
    antes = "\n".join(renglones[:desde]).rstrip()
    expresion = "\n".join(renglones[desde:]).strip()
    return antes, expresion


def escribir_practica_xlsx(cuaderno: Cuaderno, salidas: list[Salida],
                           destino: Path) -> Path:
    """Escribe el libro de práctica: las fórmulas y el resultado que deben dar.

    **No contiene los datos de terceros.** La hoja de datos trae solo los encabezados:
    quien practica pega ahí el consolidado que obtuvo con el comando del caso. Es la
    política del laboratorio —los archivos del portal son NoComercial y no se
    redistribuyen— y de paso obliga a haber producido el consolidado antes de usar la
    hoja, que es el ejercicio.

    La hoja de comprobación compara lo que da la fórmula de cada paso con el resultado
    esperado, de modo que el libro **corrige por su cuenta**.
    """
    from lab.excel import Sheet, write_workbook

    con_formula = [s for s in salidas if s.paso.formula_excel]

    instrucciones = pd.DataFrame({
        "paso": ["1", "2", "3", "4"],
        "qué hacer": [
            "Obtener el consolidado con el comando del caso "
            "(está al final de CUADERNO.md).",
            "Pegar el resultado en la hoja 02_datos, desde la celda A2, "
            "respetando el orden de las columnas.",
            "Ir a la hoja 03_formulas y copiar cada fórmula a una columna libre "
            "de 02_datos.",
            "Comparar con la columna «debe dar». Si no coincide, la explicación del "
            "paso está en CUADERNO.md.",
        ],
    })

    datos = pd.DataFrame({columna: pd.Series(dtype="object")
                          for columna in cuaderno.columnas_excel})

    formulas = pd.DataFrame({
        "paso": [s.numero for s in con_formula],
        "qué mide": [s.paso.titulo for s in con_formula],
        "fórmula de Excel": [s.paso.formula_excel for s in con_formula],
        "debe dar": [s.paso.esperado or "—" for s in con_formula],
        "trampa": [
            (s.paso.trampa.split(".")[0].replace("**", "") + ".") if s.paso.trampa
            else "—"
            for s in con_formula
        ],
    })

    hojas = [
        Sheet(
            name="01_instrucciones", frame=instrucciones, kind="documentacion",
            notes=(
                f"{cuaderno.caso} · {cuaderno.titulo}. Esta hoja NO trae los datos: "
                "los archivos del portal son NoComercial y el laboratorio no los "
                "redistribuye. Péguelos usted, que además es parte del ejercicio."
            ),
        ),
        Sheet(
            name="02_datos", frame=datos, kind="entradas",
            notes=(
                "Pegue el consolidado desde A2, respetando el orden de las columnas. "
                "Las fórmulas de la hoja siguiente suponen ese orden."
            ),
        ),
        Sheet(
            name="03_formulas", frame=formulas, kind="resultados",
            notes=(
                "Una fila por paso. Copie la fórmula a una columna libre de 02_datos y "
                "compare con «debe dar»: si no coincide, la explicación está en "
                "CUADERNO.md."
            ),
        ),
    ]
    write_workbook(
        destino, hojas,
        title=f"{cuaderno.caso} · práctica en Excel",
        source="Las fórmulas son texto, para leerlas y copiarlas. Los datos los pega usted.",
        # Las fórmulas son el CONTENIDO de este libro: evaluadas sobre una hoja vacía
        # darían 0, y lo que hace falta es poder leerlas y copiarlas.
        strings_to_formulas=False,
    )
    return destino


def url_colab(slug: str) -> str:
    """El enlace que abre el cuaderno ejecutable de un caso directamente en Colab."""
    return (
        f"https://colab.research.google.com/github/{REPO}/blob/main/"
        f"cases/{slug}/{CARPETA}/{ARCHIVO_IPYNB}"
    )


def _celda(tipo: str, texto: str) -> dict[str, Any]:
    """Una celda de notebook. Las líneas van con su salto, como pide el formato."""
    lineas = texto.splitlines(keepends=True)
    celda: dict[str, Any] = {
        "cell_type": tipo,
        "metadata": {},
        "source": lineas,
    }
    if tipo == "code":
        celda["execution_count"] = None
        celda["outputs"] = []
    return celda


def escribir_colab(cuaderno: Cuaderno, salidas: list[Salida], slug: str,
                   destino: Path) -> Path:
    """Escribe el cuaderno ejecutable para Google Colab.

    Qué lleva
        El mismo contenido del documento, en celdas: el problema, el plan, y por cada
        paso una celda de texto con el objetivo, la fórmula de Excel y la trampa, más
        una celda de código con el paso.

    Por qué la primera celda clona y descarga
        En Colab no hay repositorio ni datos. La celda de preparación clona el
        repositorio público e invoca `scripts/fetch_data.py`, que **descarga los
        archivos desde el portal de datos abiertos**, no de aquí: el laboratorio no
        redistribuye datos de terceros, y en Colab tampoco.

        Eso hace que el cuaderno corra de principio a fin sin instalar nada en la
        máquina de quien estudia, que es la única razón de que exista esta versión.
    """
    import json

    cabecera = (
        f"# {cuaderno.caso} · {cuaderno.titulo}\n"
        f"\n> **{cuaderno.pregunta}**\n"
        f"\n{cuaderno.datos}\n"
        f"\nEste cuaderno corre de principio a fin en Colab. La explicación completa, "
        f"con las hojas de Excel dibujadas, está en "
        f"[CUADERNO.md](https://github.com/{REPO}/blob/main/cases/{slug}/CUADERNO.md).\n"
        f"\n*Generado por `scripts/build_cuadernos.py`. No editar a mano: los cambios se "
        f"pierden al regenerar.*\n"
    )

    dependencias_extra = (
        f" {cuaderno.dependencias_colab.strip()}" if cuaderno.dependencias_colab.strip() else ""
    )
    preparacion = (
        "# Preparación: clona el repositorio y descarga los datos públicos.\n"
        "# Los datos NO vienen del repositorio: se descargan del portal de datos\n"
        "# abiertos, porque el laboratorio no redistribuye datos de terceros.\n"
        f"!git clone --depth 1 https://github.com/{REPO}.git lab-dtpm\n"
        "%cd lab-dtpm\n"
        "!pip install --quiet 'pandas>=2.2' 'numpy>=1.26' openpyxl XlsxWriter matplotlib"
        f"{dependencias_extra}\n"
        f"!python scripts/fetch_data.py {cuaderno.fuentes_datos or ''}\n"
    )

    celdas = [
        _celda("markdown", cabecera),
        _celda("code", preparacion),
    ]
    if cuaderno.problema:
        celdas.append(_celda("markdown", "## 1 · El problema\n\n"
                             + cuaderno.problema.strip() + "\n"))
    if cuaderno.solucion:
        celdas.append(_celda("markdown", "## 2 · La solución que se va a aplicar\n\n"
                             + cuaderno.solucion.strip() + "\n"))
    if cuaderno.implementaciones:
        celdas.append(_celda(
            "markdown",
            "## Implementaciones comparables\n\n"
            "La ruta principal usa Pandas. Polars y R recalculan el indicador central "
            "desde el contrato de salida versionado y generan el mismo gráfico.\n",
        ))
        for implementacion in cuaderno.implementaciones:
            celdas.append(_celda(
                "markdown",
                f"### {implementacion.motor}\n\n"
                f"```{implementacion.lenguaje}\n{implementacion.codigo.strip()}\n```\n\n"
                f"Ejecutar con `{implementacion.comando}`.\n",
            ))

    importes = cuaderno.importes.strip()
    if importes:
        celdas.append(_celda(
            "code",
            "import sys\nfrom pathlib import Path\n\n"
            "ROOT = Path.cwd()\n"
            "if str(ROOT) not in sys.path:\n    sys.path.insert(0, str(ROOT))\n\n"
            + importes + "\n\n"
            "pd.set_option('display.width', 140)\n"
            "pd.set_option('display.max_columns', 30)\n",
        ))

    celdas.append(_celda("markdown", "## 3 · Los pasos\n"))
    for salida in salidas:
        paso = salida.paso
        texto = [f"### Paso {salida.numero} · {paso.titulo}\n", "", paso.objetivo, ""]
        if paso.formula_excel:
            texto += [f"**En Excel:** `{paso.formula_excel}`", ""]
            if paso.esperado:
                texto += [f"Debe dar: **{paso.esperado}**", ""]
        if paso.sheets:
            texto += [f"**En Google Sheets:** {paso.sheets}", ""]
        elif paso.formula_excel:
            texto += ["**En Google Sheets:** la misma fórmula, sin cambios.", ""]
        if paso.trampa:
            texto += [f"> ⚠️ {paso.trampa}", ""]
        celdas.append(_celda("markdown", "\n".join(texto)))
        celdas.append(_celda("code", paso.pandas.strip() + "\n"))

    cierre = []
    if cuaderno.cierre:
        cierre.append("## 4 · El resultado\n\n" + cuaderno.cierre.strip())
    if cuaderno.aprendizajes:
        lista = "\n".join(f"{n}. {a}" for n, a in enumerate(cuaderno.aprendizajes, 1))
        cierre.append("## 5 · Qué queda aprendido\n\n" + lista)
    if cierre:
        celdas.append(_celda("markdown", "\n\n".join(cierre) + "\n"))

    notebook = {
        "cells": celdas,
        "metadata": {
            "colab": {"provenance": [], "toc_visible": True},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 0,
    }
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    return destino
