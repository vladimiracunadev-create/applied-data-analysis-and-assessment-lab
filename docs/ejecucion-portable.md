# Ejecución portable: Python, Google Colab y R

Esta guía parte de un entorno limpio. No supone archivos descargados, paquetes
instalados ni rutas del equipo del autor. Cada cuaderno conserva la resolución completa
en Pandas y añade un laboratorio equivalente en Pandas, Polars y R sobre el mismo
contrato de resultado.

## Requisitos compatibles

| Entorno | Versión o requisito | Estado comprobado |
| --- | --- | --- |
| Python local | 3.11–3.14; CI ejecuta 3.11, 3.12 y 3.13 | ejecución automatizada |
| Pandas / Matplotlib | Pandas 2.2–3.x; Matplotlib 3.8+ | ejecución local y CI |
| Polars | 1.x, extra `polars` | ejecución local y CI |
| R | versión `release` de `setup-r`; paquetes `readr`, `dplyr`, `ggplot2` | ejecución en CI |
| Google Colab Python | runtime Python actual compatible con los rangos anteriores | notebook preparado; ejecución manual pendiente |
| RStudio / Posit Cloud / IRkernel | R compatible con los tres paquetes | portabilidad documentada; ejecución manual pendiente |

La [matriz de validación](matriz-validacion-cuadernos.md) distingue esos estados; una
instrucción documentada no se presenta como prueba ejecutada.

## Python local

```powershell
git clone https://github.com/vladimiracunadev-create/applied-data-analysis-and-assessment-lab.git
cd applied-data-analysis-and-assessment-lab
uv sync --extra polars
uv run python scripts/fetch_data.py --listar
uv run python scripts/fetch_data.py gtfs-red-movilidad
uv run python cases/gtfs_red_movilidad/cuaderno/solucion_pandas.py --grafico pandas.png
uv run --extra polars python cases/gtfs_red_movilidad/cuaderno/solucion_polars.py --grafico polars.png
```

Cambie la fuente y el caso según el cuaderno. `fetch_data.py --listar` muestra URL,
publicador, formato, descripción y estado de licencia antes de descargar. El archivo se
guarda en `data/original/` con un registro de procedencia y SHA-256.

## Google Colab

1. Abra el enlace **Abrir en Colab** del [índice de cuadernos](cuadernos.md), o use
   **Archivo → Subir cuaderno** con `cuaderno/colab.ipynb`.
2. Seleccione **Entorno de ejecución → Ejecutar todas**.
3. La primera celda detecta Colab, clona el repositorio si hace falta, instala versiones
   compatibles y muestra las versiones efectivas.
4. La siguiente celda obtiene las fuentes originales y falla con un mensaje explícito
   si la red, la URL o la licencia impiden continuar.
5. Los pasos Pandas se ejecutan en orden; luego se ejecutan los scripts comparables de
   Pandas y Polars y se muestran sus gráficos.

### Formas alternativas de entregar datos a Colab

Carga desde el equipo:

```python
from google.colab import files
subidos = files.upload()  # el estudiante elige el archivo; no se codifica una ruta
```

Google Drive:

```python
from google.colab import drive
drive.mount('/content/drive')
```

Descarga de un archivo versionado en GitHub:

```python
import pandas as pd
url = "https://raw.githubusercontent.com/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/main/cases/calendario_medicion/feriados.csv"
datos = pd.read_csv(url)
```

Para fuentes externas use `scripts/fetch_data.py`: resuelve páginas de descarga,
registra procedencia y permite exigir una huella con `--sha256`. No sustituya una
fuente caída por datos simulados sin cambiar explícitamente la naturaleza del ejercicio.
Los CSV bajo `resultados/` son la alternativa reproducible para el laboratorio de tres
motores, pero no reemplazan la adquisición del caso completo.

### Errores frecuentes en Colab

- **La carpeta ya existe:** la celda reutiliza `lab-dtpm`; reinicie el runtime para una
  copia totalmente limpia.
- **`ModuleNotFoundError`:** vuelva a ejecutar preparación y compruebe las versiones.
- **HTTP/SSL/timeout:** reintente, revise la URL con `--listar`, cargue la copia cuya
  huella coincide o use Drive. No desactive la validación TLS.
- **Cambio de esquema:** revise las columnas requeridas en el diccionario del cuaderno;
  los scripts fallan antes de calcular si falta una.

## R local y RStudio Desktop

Instale R desde CRAN y RStudio Desktop desde Posit. Luego, en la raíz del repositorio:

```r
install.packages(c("readr", "dplyr", "ggplot2", "rmarkdown"))
sessionInfo()
```

Ejecute desde Terminal:

```powershell
Rscript cases/gtfs_red_movilidad/cuaderno/solucion.R --grafico r.png
```

O abra `solucion.Rmd` en RStudio y pulse **Knit**. El documento reutiliza
`solucion.R`; no mantiene una segunda versión de las reglas. Los scripts buscan
`pyproject.toml` hacia arriba, por lo que no dependen de `setwd("C:/...")`. Si una
herramienta impone otro directorio, defina `LAB_ROOT` con la raíz clonada.

Para congelar un proyecto docente de larga duración puede usar `renv`:

```r
install.packages("renv")
renv::init(bare = TRUE)
renv::snapshot()
```

No se versiona un `renv.lock` global porque el repositorio también tiene un entorno
Python mínimo y sólo tres dependencias R comunes; cada curso puede fijar el snapshot de
su plataforma sin imponerlo a los demás.

## Posit Cloud

1. Cree un proyecto desde el repositorio GitHub.
2. Abra `cases/<caso>/cuaderno/solucion.Rmd`.
3. Ejecute la celda de paquetes y luego **Knit**.
4. Si el proyecto se abre en una subcarpeta, defina `LAB_ROOT` con la raíz del proyecto.

Compatibilidad documentada: esta entrega no tuvo una sesión Posit Cloud disponible y
por eso no se marca como validación real.

## Jupyter con IRkernel

```r
install.packages(c("IRkernel", "readr", "dplyr", "ggplot2"))
IRkernel::installspec(user = TRUE)
```

Abra Jupyter, elija el kernel R y ejecute `source("cases/<caso>/cuaderno/solucion.R")`.
La instalación y la selección del kernel están documentadas; no se ejecutaron en esta
entrega.

## R en Google Colab

Colab estándar usa Python. Un runtime R comunitario o una instalación de R dentro del
runtime puede ejecutar `solucion.R`, pero no es una interfaz estable garantizada por
este repositorio. Se considera **compatibilidad condicional documentada**, no validación
real. Para docencia reproducible se recomienda Posit Cloud o RStudio.

## Contrato de equivalencia

Cada trío admite `--salida resultado.csv` y `--grafico figura.png`. Las pruebas comparan
columnas, filas y valores con tolerancia absoluta y relativa `1e-9`. Los gráficos deben
usar las mismas variables, unidades, período y fuente; no se exige igualdad de píxeles
entre Matplotlib y ggplot2.
