# P16 · Informe de una página para quien decide

◀ [P14/P15 · Evolución GTFS](../evolucion_gtfs/CUADERNO.md) · [Todos los cuadernos](../../docs/cuadernos.md) · [P17 · Gobernanza de datos DTPM](../gobernanza_datos_dtpm/CUADERNO.md) ▶

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/blob/main/cases/informe_decision_carga/cuaderno/colab.ipynb) — corre los pasos sin instalar nada: el cuaderno clona el repositorio y descarga los datos del portal.

> **¿Qué zonas conviene estudiar para un nuevo centro de carga y qué no se puede afirmar todavía?**

## 1 · El problema

Quien decide no necesita cuarenta tablas, pero reducirlas puede borrar los límites que
hacen honesta la conclusión. P16 debe responder qué estudiar para un nuevo centro de
carga sin afirmar dónde hay más necesidad: los datos describen oferta programada y
proximidad, no transacciones, demanda, seguridad, costos ni predios.

**Los datos.** Resultados reproducibles de P06 y P08; no contiene datos de demanda ni factibilidad de predios.

![El flujo del problema](cuaderno/svg/flujo.svg)

## 2 · La solución que se va a aplicar

Se seleccionan cuatro indicadores con unidad y lectura, se aplica una regla pública de
cribado a una rejilla geográfica y se separan evidencia, inferencia, hipótesis y lo no
demostrable. `lab.report` exige contexto, método, validación y limitaciones antes de
exportar el informe.

![El recorrido](cuaderno/svg/mapa.svg)

### El mismo resultado en Pandas, Polars y R

Los pasos anteriores y siguientes conservan la resolución completa en Pandas. Este laboratorio adicional aísla el indicador central para resolverlo tres veces sobre **la misma tabla, las mismas reglas y la misma escala gráfica**. Así la comparación cambia el motor, no el problema.

#### Contrato común del ejercicio

- **Objetivo.** Contrastar los indicadores porcentuales que sostienen la recomendación final.
- **Fuente que leen las tres implementaciones.**
  [`resultados/resumen.csv`](resultados/resumen.csv), CSV UTF-8 versionado y producido
  por la resolución completa del caso. Los datos originales, su publicador, fecha,
  licencia, URL y huella se documentan en [`case.json`](case.json) y, cuando existe,
  `procedencia.json`. Este CSV es un **resultado reproducible**, no se presenta como
  una nueva fuente oficial.
- **Alcance.** indicadores porcentuales de cobertura. Los tres scripts comparables no sustituyen la adquisición,
  limpieza ni controles completos de los pasos Pandas: aíslan el indicador para que
  una diferencia observada sea atribuible al motor.
- **Fórmula o regla.** cobertura = 100 × paradas cubiertas / paradas evaluables. Se filtra unidad='%' para no mezclar magnitudes incompatibles.
- **Interpretación.** La brecha entre supuestos espaciales cuantifica sensibilidad y debe acompañar cualquier decisión.
- **Error frecuente.** Poner porcentajes y recuentos en el mismo eje produce una comparación visual sin unidad común.

| Campo | Tipo observado | Función en el ejercicio |
| --- | --- | --- |
| `indicador` | `str` | categoría/eje X |
| `valor` | `float64` | medida/eje Y |
| `unidad` | `str` | campo auxiliar del contrato |
| `lectura` | `str` | campo auxiliar del contrato |

#### Qué cambia entre motores

| Dimensión | Pandas | Polars | R (`dplyr`/`readr`) |
| --- | --- | --- | --- |
| Modelo | DataFrame mutable por operaciones | expresiones columnares y plan optimizable | tubería declarativa sobre `tibble` |
| Nulos | `NaN`/`NA`; `groupby` exige decidir `dropna` | `null` separado de `NaN` | `NA`; muchas funciones exigen `na.rm` explícito |
| Orden | varias operaciones lo conservan, pero se ordena explícitamente | no se presupone tras agrupar | se fija con `arrange` |
| Gráfico | Matplotlib | Matplotlib tras extraer sólo X/Y | ggplot2 y su gramática de capas |
| Ventaja típica | ecosistema amplio y aprendizaje gradual | paralelismo, tipos y consultas grandes | estadística, comunicación y análisis reproducible |
| Límite aquí | el índice puede introducir alineaciones implícitas | añade una dependencia y otra semántica de tipos | requiere runtime y paquetes R independientes |

La equivalencia se valida sobre CSV normalizados con tolerancia numérica `1e-9`; no
se exige que la sintaxis ni los píxeles sean idénticos. Para ejecutar en un entorno
limpio consulte [`docs/ejecucion-portable.md`](../../docs/ejecucion-portable.md).

| Motor | Alcance verificado | Archivo | Ejecutar |
| --- | --- | --- | --- |
| Pandas + Matplotlib | indicadores porcentuales de cobertura | [`solucion_pandas.py`](cuaderno/solucion_pandas.py) | `python cases/informe_decision_carga/cuaderno/solucion_pandas.py` |
| Polars + Matplotlib | indicadores porcentuales de cobertura | [`solucion_polars.py`](cuaderno/solucion_polars.py) | `uv run --extra polars python cases/informe_decision_carga/cuaderno/solucion_polars.py` |
| R + ggplot2 | indicadores porcentuales de cobertura | [`solucion.R`](cuaderno/solucion.R) | `Rscript cases/informe_decision_carga/cuaderno/solucion.R` |

#### Pandas + Matplotlib

```python
"""Laboratorio comparable Pandas + Matplotlib del caso informe_decision_carga.

Lee el mismo contrato CSV que las versiones Polars y R. La resolución completa del
caso permanece en ``solution.py`` y en los pasos del cuaderno; este archivo aísla el
indicador central para que la comparación entre motores sea controlada.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Buscar la raíz desde el propio archivo evita rutas C:\... específicas del autor y
# funciona igual después de clonar el repositorio en Linux, Windows o Google Colab.
ROOT = Path(__file__).resolve().parents[3] if "__file__" in globals() else Path.cwd()
SOURCE = ROOT / "cases" / "informe_decision_carga" / "resultados" / "resumen.csv"
REQUIRED = {"indicador", "valor"}


def analizar() -> pd.DataFrame:
    """Carga, valida y transforma el indicador; no modifica el archivo de entrada."""
    datos = pd.read_csv(SOURCE)
    faltantes = REQUIRED.difference(datos.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas en {SOURCE}: {sorted(faltantes)}")
    # La expresión conserva explícitos filtro, agrupación, orden y selección para que
    # el estudiante pueda alinearlos con las expresiones de Polars y dplyr.
    resultado = datos.loc[datos["unidad"] == "%", ["indicador", "valor"]]
    return resultado.reset_index(drop=True)


def graficar(resultado: pd.DataFrame, destino: Path) -> Path:
    """Representa exactamente las columnas comparadas y explicita sus unidades."""
    x = resultado["indicador"].tolist()
    y = resultado["valor"].tolist()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh([str(value) for value in x], y, color="#11253B")
    ax.invert_yaxis()  # el primer puesto del ranking queda arriba, como se lee una tabla
    ax.set_xlabel("Cobertura de paradas (%)")
    ax.set_ylabel("Indicador")
    ax.set_xlim(left=0)
    ax.set_title("Dos supuestos espaciales producen coberturas distintas")
    ax.grid(axis="y", alpha=0.25)
    fig.text(0.01, 0.01, "Fuente: Resultados reproducibles del caso P16 · Período: corte publicado", fontsize=8, color="#58677A")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(destino, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return destino


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, help="CSV normalizado para comparar motores")
    parser.add_argument("--grafico", type=Path, help="PNG de la visualización comparable")
    args = parser.parse_args()
    resultado = analizar()
    print(resultado.to_string(index=False))
    if args.salida:
        resultado.to_csv(args.salida, index=False)
    if args.grafico:
        print(graficar(resultado, args.grafico))


if __name__ == "__main__":
    main()
```

#### Polars + Matplotlib

```python
"""Laboratorio comparable Polars + Matplotlib del caso informe_decision_carga.

Usa el mismo CSV, columnas, reglas y escala que Pandas y R. Polars expresa las
transformaciones como un plan de expresiones columnares; esa diferencia de método es
el objeto de aprendizaje, no una razón para cambiar la pregunta.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[3] if "__file__" in globals() else Path.cwd()
SOURCE = ROOT / "cases" / "informe_decision_carga" / "resultados" / "resumen.csv"
REQUIRED = {"indicador", "valor"}


def analizar() -> pl.DataFrame:
    """Carga y valida antes de transformar para producir un error explicativo."""
    datos = pl.read_csv(SOURCE)
    faltantes = REQUIRED.difference(datos.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas en {SOURCE}: {sorted(faltantes)}")
    # select al final fija el contrato de salida y evita comparar columnas auxiliares.
    return datos.filter(pl.col("unidad") == "%").select(["indicador", "valor"])


def graficar(resultado: pl.DataFrame, destino: Path) -> Path:
    """Convierte sólo las series del gráfico; el análisis permanece en Polars."""
    x = resultado["indicador"].to_list()
    y = resultado["valor"].to_list()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh([str(value) for value in x], y, color="#11253B")
    ax.invert_yaxis()  # el primer puesto del ranking queda arriba, como se lee una tabla
    ax.set_xlabel("Cobertura de paradas (%)")
    ax.set_ylabel("Indicador")
    ax.set_xlim(left=0)
    ax.set_title("Dos supuestos espaciales producen coberturas distintas")
    ax.grid(axis="y", alpha=0.25)
    fig.text(
        0.01,
        0.01,
        "Fuente: Resultados reproducibles del caso P16 · Período: corte publicado",
        fontsize=8,
        color="#58677A",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(destino, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return destino


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, help="CSV normalizado para comparar motores")
    parser.add_argument("--grafico", type=Path, help="PNG de la visualización comparable")
    args = parser.parse_args()
    resultado = analizar()
    print(resultado)
    if args.salida:
        resultado.write_csv(args.salida)
    if args.grafico:
        print(graficar(resultado, args.grafico))


if __name__ == "__main__":
    main()
```

#### R + ggplot2

```r
#!/usr/bin/env Rscript
# Laboratorio comparable R + dplyr/readr + ggplot2 del caso informe_decision_carga.
#
# La resolución completa sigue en solution.py y en los pasos Pandas. Este script
# cambia el motor sobre el mismo contrato CSV para estudiar sintaxis y semántica sin
# cambiar datos, indicador ni escala gráfica.

required <- c("readr", "dplyr")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) {
  stop(
    "Faltan paquetes: ", paste(missing, collapse = ", "),
    ". Instálelos con install.packages(c('readr', 'dplyr', 'ggplot2'))."
  )
}

# Buscar pyproject.toml hacia arriba hace portable el script entre terminal, RStudio,
# Posit Cloud, IRkernel y un clon en Colab. LAB_ROOT permite una ruta explícita sin
# codificar la unidad o el directorio del desarrollador.
find_root <- function(start = getwd()) {
  current <- normalizePath(start, mustWork = TRUE)
  repeat {
    if (file.exists(file.path(current, "pyproject.toml"))) return(current)
    parent <- dirname(current)
    if (identical(parent, current)) stop("No se encontró la raíz del repositorio.")
    current <- parent
  }
}
root <- Sys.getenv("LAB_ROOT", unset = find_root())
source_csv <- file.path(root, "cases", "informe_decision_carga", "resultados", "resumen.csv")

# readr conserva nombres y tipos previsibles. La validación temprana produce un error
# que explica el contrato roto, en vez de fallar más tarde dentro de una gráfica.
datos <- readr::read_csv(source_csv, show_col_types = FALSE, progress = FALSE)
required_columns <- c("indicador", "valor")
missing_columns <- setdiff(required_columns, names(datos))
if (length(missing_columns)) stop("Faltan columnas: ", paste(missing_columns, collapse = ", "))

# dplyr expresa la misma selección, filtro, agrupación y orden que las otras vías.
resultado <- datos |> dplyr::filter(.data$unidad == "%") |> dplyr::select(.data$indicador, .data$valor)
print(resultado)

args <- commandArgs(trailingOnly = TRUE)
value_after <- function(flag) {
  pos <- match(flag, args)
  if (is.na(pos)) return(NULL)
  if (pos == length(args)) stop(flag, " necesita una ruta de salida")
  args[pos + 1]
}

csv_output <- value_after("--salida")
if (!is.null(csv_output)) readr::write_csv(resultado, csv_output)

plot_output <- value_after("--grafico")
if (!is.null(plot_output)) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) {
    stop("Instale ggplot2 para generar el gráfico: install.packages('ggplot2')")
  }
  grafico <- ggplot2::ggplot(
    resultado,
    ggplot2::aes(x = .data[["indicador"]], y = .data[["valor"]])
  ) +
    ggplot2::geom_col(fill = "#11253B") +
    ggplot2::scale_x_discrete(limits = rev) +
    ggplot2::coord_flip() +
    ggplot2::labs(
      title = "Dos supuestos espaciales producen coberturas distintas",
      x = "Cobertura de paradas (%)", y = "Indicador",
      caption = "Fuente: Resultados reproducibles del caso P16 · Período: corte publicado"
    ) +
    ggplot2::theme_minimal(base_size = 11)
  ggplot2::ggsave(plot_output, grafico, width = 9, height = 5, dpi = 150)
  cat(plot_output, "\n")
}
```

8 pasos. Cada uno trae el código de **Python**, la salida que devuelve de verdad, y la **fórmula de Excel** equivalente dibujada en su hoja. 8 traen además la trampa de hacerlo de la forma obvia.

| # | Paso | Trampa |
| --- | --- | --- |
| 1 | [Auditar las tablas de entrada](#paso-1) | sí |
| 2 | [Reducir a cuatro indicadores](#paso-2) | sí |
| 3 | [Declarar la regla de prioridad](#paso-3) | sí |
| 4 | [Construir una lista corta](#paso-4) | sí |
| 5 | [Clasificar cada afirmación](#paso-5) | sí |
| 6 | [Escribir lo que no se puede concluir](#paso-6) | sí |
| 7 | [Validar la completitud](#paso-7) | sí |
| 8 | [Exportar el entregable reproducible](#paso-8) | sí |

### Para trabajar

| Archivo | Qué es |
| --- | --- |
| [`P16-caso-completo.zip`](cuaderno/P16-caso-completo.zip) | **todo el caso en un ZIP**: el cuaderno, el script, el libro de Excel y las figuras |
| [`pasos.py`](cuaderno/pasos.py) | los 8 pasos seguidos. Se corre y muestra cada salida |
| [`practica.xlsx`](cuaderno/practica.xlsx) | las fórmulas y **el resultado que deben dar**, para corregirse solo. Se abre igual en Google Sheets |
| [`colab.ipynb`](cuaderno/colab.ipynb) | el cuaderno **ejecutable en Colab**: clona, descarga los datos del portal y corre los 8 pasos |
| [`solucion_pandas.py`](cuaderno/solucion_pandas.py) | solución ejecutable en Pandas + Matplotlib; incluye el contraste numérico y el gráfico del caso |
| [`solucion_polars.py`](cuaderno/solucion_polars.py) | solución ejecutable en Polars + Matplotlib; incluye el contraste numérico y el gráfico del caso |
| [`solucion.R`](cuaderno/solucion.R) | solución ejecutable en R + ggplot2; incluye el contraste numérico y el gráfico del caso |
| [`solucion.Rmd`](cuaderno/solucion.Rmd) | documento R Markdown para RStudio, Posit Cloud y render reproducible; reutiliza `solucion.R` sin duplicar la lógica |

---

## 3 · Los pasos

<a id="paso-1"></a>

### Paso 1 · Auditar las tablas de entrada

El informe consume agregados versionados, no cifras copiadas a mano.

#### Python

```python
tablas = decision.cargar()
{k: v.shape for k, v in tablas.items()}
```

```
{'salidas_por_hora': (75, 4), 'cobertura_por_umbral': (6, 5), 'sensibilidad_rodeo': (5, 5), 'por_rejilla': (296, 7)}
```

![Auditar las tablas de entrada](cuaderno/svg/paso-01.svg)

*Dos supuestos espaciales producen coberturas distintas. Ejes con unidad, período y fuente; el código Polars y R genera la misma vista.*

#### Excel

Una hoja por resultado de origen, con nombre, fecha y unidad.

> **La trampa.** Copiar cuatro números a una diapositiva rompe la trazabilidad hasta su denominador.

[↑ volver al recorrido](#2--la-solución-que-se-va-a-aplicar)

---

<a id="paso-2"></a>

### Paso 2 · Reducir a cuatro indicadores

Cada cifra incluye unidad y la lectura que sí permite.

#### Python

```python
resultados = decision.analizar()
resultados['resumen']
```

| indicador | valor | unidad | lectura |
| --- | --- | --- | --- |
| salidas programadas en día laboral | 64011.0 | salidas | oferta programada, no demanda |
| hora de mayor oferta | 7.0 | hora | 4541 salidas programadas |
| paradas con carga a 300 m en línea recta | 59.29 | % | referencia espacial |
| paradas con factor de rodeo 1,3 | 46.02 | % | supuesto, no ruta peatonal observada |
*4 filas × 4 columnas.*

#### Excel

Tabla ejecutiva de cuatro filas; no mezclar porcentaje, hora y conteo en un mismo eje.

> **La trampa.** 64 011 salidas son oferta programada, no viajes de personas.

[↑ volver al recorrido](#2--la-solución-que-se-va-a-aplicar)

---

<a id="paso-3"></a>

### Paso 3 · Declarar la regla de prioridad

La regla combina paradas descubiertas y distancia mediana solo como cribado.

#### Python

```python
{'formula': 'paradas_sin_cobertura × mediana_m', 'uso': 'ordenar estudios de factibilidad'}
```

```
{'formula': 'paradas_sin_cobertura × mediana_m', 'uso': 'ordenar estudios de factibilidad'}
```

#### Excel

`=(paradas-cubiertas)*mediana_m` y conservar ambos componentes visibles.

> **La trampa.** Un puntaje sin fórmula publicada convierte criterio en opinión.

[↑ volver al recorrido](#2--la-solución-que-se-va-a-aplicar)

---

<a id="paso-4"></a>

### Paso 4 · Construir una lista corta

Diez celdas reducen el territorio a revisar con datos adicionales.

#### Python

```python
resultados['prioridades']
```

| celda_lat | celda_lon | paradas | cubiertas | paradas_sin_cobertura | mediana_m | cobertura_pct | parada_mas_lejana | prioridad_exploratoria |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| -33.4 | -70.66 | 41 | 1 | 40 | 582.4 | 2.4 | PB1400-Emiliano Zapata / esq. Bernardo O'Higg… | 23296.0 |
| -33.62 | -70.7 | 29 | 0 | 29 | 663.8 | 0.0 | PG987-Los Suspiros / esq. Avenida Central | 19250.2 |
| -33.63 | -70.62 | 38 | 9 | 29 | 625.2 | 23.7 | PF673-Belén / esq. Río Maihue | 18130.8 |
| -33.62 | -70.59 | 26 | 2 | 24 | 721.7 | 7.7 | PF720-Sargento Menadier / esq. Uruguay | 17320.8 |
| -33.5 | -70.71 | 23 | 2 | 21 | 741.1 | 8.7 | PI1967-Av. Los Cerrillos / esq. C. Teresa Her… | 15563.1 |
| -33.51 | -70.67 | 24 | 0 | 24 | 643.8 | 0.0 | PH269-Av. J. J. Prieto Vial / esq. Vecinal | 15451.2 |
| -33.62 | -70.57 | 20 | 0 | 20 | 745.6 | 0.0 | PF978-Av. Circunvalación / esq. Nonato Coo | 14912.0 |
| -33.62 | -70.58 | 28 | 5 | 23 | 570.6 | 17.9 | PF791-Av.Pdte. Salvador Allende / esq. Pdte. … | 13123.8 |
| -33.62 | -70.6 | 39 | 9 | 30 | 414.8 | 23.1 | PF882-Rafael Alberti / esq. Ejército Libertad… | 12444.0 |
| -33.54 | -70.68 | 26 | 4 | 22 | 564.3 | 15.4 | PG1149-Avenida Ossa / esq. Alhué | 12414.6 |
*10 filas × 9 columnas.*

#### Excel

![La hoja](cuaderno/svg/paso-04-excel.svg)

Ordenar el puntaje descendente y mostrar los componentes, no solo el ranking.

> **La trampa.** La coordenada de celda no es un predio ni una recomendación de construcción.

[↑ volver al recorrido](#2--la-solución-que-se-va-a-aplicar)

---

<a id="paso-5"></a>

### Paso 5 · Clasificar cada afirmación

Hecho calculado, inferencia e hipótesis se leen de forma distinta.

#### Python

```python
resultados['afirmaciones']
```

| tipo | afirmacion | respaldo |
| --- | --- | --- |
| evidencia | 59,29 % de las paradas está a 300 m en línea … | P08, 7 409 de 12 497 paradas. |
| inferencia | Las celdas con muchas paradas descubiertas am… | Supuesto: cobertura espacial es criterio de c… |
| hipotesis | Un nuevo centro en esas zonas podría reducir … | Requiere demanda, predios, seguridad, costo y… |
| no demostrable | Esas zonas tienen mayor necesidad de carga. | No hay transacciones, saldo, demanda ni orige… |
*4 filas × 3 columnas.*

#### Excel

Columna obligatoria de tipo y otra de respaldo.

> **La trampa.** Presentar una hipótesis como evidencia es más dañino que omitirla.

[↑ volver al recorrido](#2--la-solución-que-se-va-a-aplicar)

---

<a id="paso-6"></a>

### Paso 6 · Escribir lo que no se puede concluir

Los datos faltantes se vinculan a la decisión que bloquean.

#### Python

```python
resultados['afirmaciones'].query("tipo == 'no demostrable'")
```

| tipo | afirmacion | respaldo |
| --- | --- | --- |
| no demostrable | Esas zonas tienen mayor necesidad de carga. | No hay transacciones, saldo, demanda ni orige… |
*1 filas × 3 columnas.*

#### Excel

Sección visible de límites: demanda, red peatonal, predios, costo, seguridad y horario.

> **La trampa.** Baja cobertura no equivale a alta necesidad.

[↑ volver al recorrido](#2--la-solución-que-se-va-a-aplicar)

---

<a id="paso-7"></a>

### Paso 7 · Validar la completitud

El informe no se exporta si falta una sección obligatoria.

#### Python

```python
resultados['completitud']
```

| seccion | clave | presente |
| --- | --- | --- |
| Contexto | contexto | sí |
| Definición del problema | problema | sí |
| Objetivos | objetivos | sí |
| Datos y diccionario | datos | sí |
| Metodología | metodologia | sí |
| Supuestos | supuestos | sí |
| Resultados | resultados | sí |
| Validación independiente | validacion | sí |
| Interpretación | interpretacion | sí |
| Limitaciones | limitaciones | sí |
| Conclusiones | conclusiones | sí |
| Reproducibilidad | reproducibilidad | sí |
*12 filas × 3 columnas.*

#### Excel

Lista de verificación con doce secciones y estado sí/no.

> **La trampa.** Un resumen sin supuestos o limitaciones parece más concluyente de lo que es.

[↑ volver al recorrido](#2--la-solución-que-se-va-a-aplicar)

---

<a id="paso-8"></a>

### Paso 8 · Exportar el entregable reproducible

La misma ejecución escribe tablas y el informe Markdown.

#### Python

```python
ruta = decision.exportar(resultados)
str(ruta / 'informe.md')
```

```
'C:\\dev\\applied-data-analysis-and-assessment-lab\\cases\\informe_decision_carga\\resultados\\informe.md'
```

#### Excel

Guardar fórmulas, fuentes y fecha en el mismo libro que la portada ejecutiva.

> **La trampa.** El formato profesional no sustituye el vínculo al cálculo.

[↑ volver al recorrido](#2--la-solución-que-se-va-a-aplicar)

---

## 4 · El resultado

La entrega produce una lista corta de zonas para factibilidad, no una ubicación aprobada. La recomendación siguiente es recopilar demanda, red peatonal, horarios, predios, costos y seguridad.

## 5 · Qué queda aprendido

1. Reducir no debe borrar denominadores.
2. Un ranking necesita fórmula pública.
3. Baja cobertura no demuestra necesidad.
4. La sección de límites cambia la decisión siguiente.

## Reproducir

```powershell
python -m cases.informe_decision_carga.solution
```

## Seguir

Lo que este caso toca y se trata a fondo en otro sitio:

- [Informe generado](resultados/informe.md)
- [P06 · Oferta programada](../gtfs_red_movilidad/CUADERNO.md)
- [P08 · Cobertura espacial](../cobertura_de_carga/CUADERNO.md)

◀ [P14/P15 · Evolución GTFS](../evolucion_gtfs/CUADERNO.md) · [Todos los cuadernos](../../docs/cuadernos.md) · [P17 · Gobernanza de datos DTPM](../gobernanza_datos_dtpm/CUADERNO.md) ▶
