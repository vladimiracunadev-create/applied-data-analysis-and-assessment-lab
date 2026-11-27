# P01/P02/P04 · Consolidar, validar claves y normalizar cinco Excel públicos

**Datos públicos reales con licencia verificada.** Es el ejercicio más parecido a lo
que se pide en una evaluación técnica de cuatro horas con Excel y Pandas: cinco
archivos que hay que leer, armonizar, limpiar y agregar, con el desorden que tienen
los archivos de verdad.

> Licencia **Creative Commons Atribución-NoComercial 2.0**, declarada y verificada en
> los metadatos del portal de datos abiertos. Los archivos de origen no se versionan;
> sí se versionan el registro de procedencia y las tablas de resultado.

> **¿Vienes a aprender a hacerlo?** Empieza por el
> **[cuaderno de trabajo](CUADERNO.md)**: los dieciséis pasos de P01/P02/P04 con el código de Pandas, la
> salida que devuelve de verdad, y la fórmula de Excel equivalente. Se lee de arriba
> abajo sin abrir nada más.
>
> Este README cuenta **qué se encontró**, que es otra cosa: sirve para auditar el
> resultado, no para aprender a producirlo.

Metadatos completos: [`case.json`](case.json). Procedencia:
[`procedencia.json`](procedencia.json).

---

## 1. El problema, en palabras

La Subsecretaría de Transporte publica los lugares donde se puede cargar la tarjeta
bip! en **cinco archivos Excel separados**, uno por tipo de local: estaciones de Metro,
Puntos bip!, centros de alto estándar, centros estándar y retail.

La pregunta de negocio: **¿cuántos lugares de carga hay, de qué tipo, en qué comuna y
de qué entidad?** Detrás hay una decisión: dónde falta cobertura de recarga.

Nadie puede contestarla mirando los cinco archivos por separado. Y los cinco están
maquetados para que una persona los lea, no para que un programa los procese.

---

## 2. Descomposición

| # | Pregunta respondible | Qué exige |
| --- | --- | --- |
| 1 | ¿Dónde empieza cada tabla? | Detectar la fila del encabezado, distinta en cada archivo |
| 2 | ¿Qué campos tiene cada archivo? | Armonizar esquemas de 9 y 10 columnas |
| 3 | ¿Qué filas cuentan? | Distinguir la hoja de locales cerrados |
| 4 | ¿Cuál es la clave? | Comprobarlo, no suponerlo |
| 5 | ¿Las coordenadas son fiables? | Validar las dos representaciones entre sí |
| 6 | ¿Cuántos hay por comuna y entidad? | Normalizar antes de agrupar |

---

## 3. De dónde salen los datos

Cinco archivos del portal de datos abiertos del Estado, publicador **Subsecretaría de
Transporte, Ministerio de Transportes y Telecomunicaciones**, descargados el 26 de
noviembre de 2026 con su SHA-256 registrado:

| Fuente | Bytes | Hoja | Encabezado en fila | Filas | Columnas |
| --- | --- | --- | --- | --- | --- |
| `bip-metro` | 22 411 | `Abiertos` | **7** | 143 | 10 |
| `bip-puntos` | 164 941 | `PCMA` | **9** | 1 579 | 9 |
| `bip-centros-alto-estandar` | 12 029 | `Abiertos` | **13** | 7 | 9 |
| `bip-centros-estandar` | 14 087 | `Abierto` | **10** | 29 | 9 |
| `bip-retail` | 29 317 | `Abiertos` | **9** | 169 | 10 |
| `bip-retail` | — | **`Cerrados`** | **9** | 1 | 10 |

Total: **1 928 filas**, de las cuales 1 927 abiertas y 1 cerrada.

### Los nueve defectos, verificados

1. **El encabezado está en una fila distinta en cada archivo**: 7, 9, 13, 10 y 9. Sin
   `header=`, `pd.read_excel` devuelve diez columnas `Unnamed: 0`…`Unnamed: 9` y la
   primera fila de datos dice `METRO` en una celda y nada en las otras nueve.
2. **Los esquemas tienen 9 o 10 columnas** según el archivo.
3. **Los nombres de columna varían**: `NOMBRE FANTASIA`, `NOMBRE DE FANTASIA ` —con un
   espacio al final— o ausente; `DIRECCION` o `DIRECCIÓN`; `HORARIO REFERENCIAL`,
   `HORARIO` o ausente.
4. **Los nombres de hoja varían**: `Abiertos`, `Abierto`, `PCMA`.
5. **Un archivo trae una hoja `Cerrados`.**
6. **Hay dos sistemas de coordenadas a la vez**: UTM (`ESTE`, `NORTE`) y geográficas
   (`LATITUD`, `LONGITUD`).
7. **La entidad viene con mayúsculas inconsistentes**: `FULLCARGA` y `Fullcarga`.
8. **La comuna viene en mayúsculas y sin tildes**: `CONCHALI`, `ESTACION CENTRAL`.
9. **El contenido incluye el carácter `∙`**, que aborta un comando en una consola de
   Windows con página de códigos cp1252.

---

## 4. Qué tecnología se usa y por qué

| Decisión | Alternativas | Por qué esta |
| --- | --- | --- |
| **Detectar** la fila del encabezado | Fijar el número por archivo | Cinco archivos del mismo organismo con cinco filas distintas. Fijarlo funciona hasta la próxima publicación, y falla sin aviso |
| `dtype=str` en todo | Dejar que pandas infiera | Los códigos del archivo de Metro son `L1`, `L2`: leerlos como número los destruye |
| Declarar los alias de columna | Emparejar por parecido de texto | Un acierto por casualidad hoy es un error mañana. La correspondencia se escribe y queda en una tabla del entregable |
| Clave normalizada **más** etiqueta legible | Solo la clave | Guardar solo la clave convierte `Ñuñoa` en `NUNOA` en el informe final. Se conservan las dos |
| `lab.geo.utm_to_latlon` propio | `pyproj`, `GeoPandas` | Mantiene el entorno mínimo y la fórmula explicable. Para trabajo geoespacial serio, use las bibliotecas; aquí la conversión es una validación, no el producto |
| Pandas | Power Query en Excel | Power Query es la respuesta correcta si el entregable tiene que ser un libro. Aquí el entregable es una tabla reutilizable y un informe de calidad |

---

## 5. La resolución, paso a paso

### 5.1 Detectar el encabezado en lugar de fijarlo

El criterio de `lab.excel.detect_header_row`: **la primera fila con al menos cuatro
celdas no vacías cuyos valores sean todos texto.**

Funciona porque las filas de título (`METRO`, `PUNTOS BIP! (PCMA)`) tienen una sola
celda llena, y las filas de datos traen números. El encabezado es la primera fila ancha
y enteramente textual.

Si no encuentra ninguna, **falla** en lugar de devolver una fila arbitraria: un
encabezado mal detectado convierte datos en nombres de columna y contamina todo lo que
sigue.

Y lo que hizo queda en el entregable, porque una hoja de 151 filas que entrega 143
registros no tiene 8 registros perdidos: tiene 8 filas de maquetación.

### 5.2 Armonizar los esquemas con la correspondencia declarada

```python
ALIAS = {
    "nombre": ("NOMBRE FANTASIA", "NOMBRE DE FANTASIA"),
    "horario": ("HORARIO REFERENCIAL", "HORARIO"),
    ...
}
```

La comparación se hace sobre el nombre **normalizado**, de modo que
`NOMBRE DE FANTASIA ` con espacio al final y `DIRECCIÓN` con tilde encuentran su campo.
El campo que un archivo no trae queda nulo, y la cobertura se informa:

| Campo | Cobertura | Fuentes que no lo traen |
| --- | --- | --- |
| `codigo`, `entidad`, `direccion`, `comuna`, coordenadas | 100 % | — |
| `nombre` | 98,13 % | `bip-centros-alto-estandar`, `bip-centros-estandar` |
| **`horario`** | **18,10 %** | `bip-puntos` |

Ese 18,10 % es el dato que cambia la conversación: cualquier indicador que use el
horario se calcula sobre el 18 % de los locales, y hay que decirlo. No es un campo con
nulos: es un campo que 1 579 locales **no tienen**.

### 5.3 El tipo de local no está en los datos

Está en el **nombre del archivo**. Al consolidar hay que declararlo o se pierde, y con
él la única forma de responder «de qué tipo» en la pregunta original.

### 5.4 ¿El código es una clave? No, y el motivo importa

| Ámbito | Filas | Códigos distintos | Repetidos | ¿Es clave? |
| --- | --- | --- | --- | --- |
| consolidado | 1 928 | 1 792 | 136 | **no** |
| solo `bip-metro` | 143 | **7** | 136 | **no** |
| solo `bip-puntos` | 1 579 | 1 579 | 0 | sí |
| solo `bip-retail` | 170 | 170 | 0 | sí |
| **clave compuesta (fuente + código)** | 1 928 | 1 792 | 136 | **no** |

En el archivo de Metro el código es la **línea** (`L1`, `L2`…), no el local: 143
estaciones con 7 códigos. Y el hallazgo que de verdad importa: **ni siquiera
`fuente + codigo` identifica una fila**. Hace falta una clave subrogada, o añadir un
tercer componente.

Quien suponga que una columna llamada «código» es una clave construye un cruce que
duplica filas en silencio.

### 5.4b · P02 · Entonces, ¿qué identifica un lugar de carga?

La sección anterior contesta la pregunta estrecha. La amplia es: **¿hay alguna
combinación de columnas que identifique una fila?**

Primero, ninguna columna sola:

```
   columna  filas  nulos  distintos  repetidos  por_que_no
 direccion   1928      0       1919          9  tiene valores repetidos
     norte   1928      0       1837         91  tiene valores repetidos
      este   1928      0       1820        108  tiene valores repetidos
    codigo   1928      0       1792        136  tiene valores repetidos
    nombre   1928     36       1794         98  tiene nulos y repetidos
```

`nombre` es el caso que conviene mirar: falla por **las dos** causas a la vez, de modo
que ni completando los 36 nulos serviría.

La búsqueda exhaustiva de `lab.keys.candidate_keys` devuelve tres claves candidatas
mínimas, y las tres son de dos columnas:

| Clave candidata | ¿Única hoy? | ¿Sirve de identificador? | Por qué |
| --- | --- | --- | --- |
| `codigo + direccion` | sí | **no** | `direccion` es texto libre: una tilde corregida cambia la identidad |
| `codigo + este` | sí | **no** | `este` es una coordenada **medida** |
| `codigo + norte` | sí | **no** | igual que `este` |

La segunda fila es la lección. Es perfectamente única hoy. Y
[P10](../correspondencia_metro/README.md) demostró que varias coordenadas de este
archivo están equivocadas por kilómetros, de modo que el día en que el publicador
corrija la de Santa Lucía, esa fila **cambiará de identidad** y aparecerá como un lugar
nuevo.

> Una clave que cambia cuando se corrige un error no es una clave: es un número de
> serie del error.

**La salida: una clave subrogada.** Un identificador determinista derivado de los campos
que se **declaran** como identidad —`fuente + codigo + direccion`, en la constante
`IDENTIDAD`—:

```
           campos_declarados   codigo + direccion + fuente
                       filas                          1928
   identificadores_distintos                          1928
filas_con_identidad_repetida                             0
```

Tres cosas que consigue, y una que no:

- es **determinista**: el mismo contenido da el mismo identificador en cualquier máquina
  y ejecución. Es la diferencia con el número de fila, que es lo que P08, P09 y P10
  tuvieron que usar por no haber nada mejor;
- **comprueba sus colisiones** y falla en lugar de devolver una clave con duplicados;
- **deja la identidad escrita**, que es exactamente lo que el archivo no hace;
- **hereda la inestabilidad de `direccion`**. No hay forma de evitarlo sin un
  identificador provisto por la fuente, y pedirlo es lo que corresponde.

---

### 5.5 Normalizar antes de agrupar

`FULLCARGA` y `Fullcarga` son dos grupos para `groupby` y uno para una persona.
`lab.textual.normalize_key` quita tildes, pasa a mayúsculas, colapsa espacios y recorta
los extremos. Resultado: **tres entidades** donde el texto crudo da cuatro.

Una sola fusión, y no es poco: sin ella el grupo de FULLCARGA se parte en 1 579 y 36.
Pero conviene no exagerar el mérito, y la sección 5.5b lo mide.

| Entidad | Locales | Comunas | Tipos |
| --- | --- | --- | --- |
| FULLCARGA | 1 615 | 36 | 3 |
| WALMART | 169 | 44 | 1 |
| METRO | 143 | 26 | 1 |

Y se conserva la etiqueta legible aparte, para que el informe diga `Ñuñoa` y no
`NUNOA`.

### 5.5b · P04 · ¿Y alguna de esas fusiones estuvo mal?

Normalizar tiene **dos direcciones de error** y solo una se nota:

| Error | Qué produce | ¿Se nota? |
| --- | --- | --- |
| Dejar separado lo que es igual | un grupo de más, con el total partido | **sí** |
| Juntar lo que es distinto | un grupo de menos, con el total sumado | **no** |

La primera salta a la vista. La segunda produce una tabla más limpia, con totales
mayores, y nada en el resultado sugiere revisarla.

Lo que gana normalizar, columna por columna:

```
  columna  distintos_crudos  distintos_normalizados  grupos_espurios_evitados
   comuna                46                      46                         0
  entidad                 4                       3                         1
direccion              1919                    1914                         5
```

**Seis fusiones en todo el archivo**, y `comuna` —que es el ejemplo clásico— no gana
nada. El riesgo de no normalizar era concreto y pequeño.

Y las seis, a la vista para poder verificarlas:

```
  columna                          clave_normalizada                              formas
  entidad                                  FULLCARGA   Fullcarga (1579) | FULLCARGA (36)
direccion              AVENIDA AMERICO VESPUCIO 1737   AV. AMÉRICO VESPUCIO 1737 | AV. AMERICO VESPUCIO 1737
direccion              AVENIDA AMERICO VESPUCIO 2500   Av. Américo Vespucio 2500 | AV. AMERICO VESPUCIO 2500
direccion AVENIDA LIBERTADOR BERNARDO O HIGGINS 1020   Av. ... O`Higgins 1020 | Av. ... O'Higgins 1020
direccion             AVENIDA NUEVA PROVIDENCIA 2249   Av. Nueva Providencia 2249 | AV. NUEVA PROVIDENCIA 2249
direccion                             SAN PEDRO 1778   SAN PEDRO 1778 | SAN PEDRO  1778
```

Mayúsculas, tildes, un apóstrofo escrito como acento grave y un espacio doble. Las seis
son correctas, y eso **se puede afirmar porque se leyeron**, no porque el recuento
pareciera razonable. Cada fila es la afirmación de que dos textos distintos nombran la
misma cosa, y es la única parte de una normalización que una persona tiene que confirmar.

#### La capacidad que no aporta nada aquí

`lab.textual.ABREVIATURAS` declara trece equivalencias —`AV` por `AVENIDA`, `PJE` por
`PASAJE`— y la expansión está implementada y probada. Sobre las 1 919 direcciones de
este archivo:

```
   normalizadas_sin_expandir   1914
    normalizadas_expandiendo   1914
fusiones_que_aporta_expandir      0
```

**Cero.** Las cinco fusiones de `direccion` las produce el resto de la normalización:
tildes, mayúsculas y espacios. La expansión no sobra —cuesta nada y protege de un
archivo donde sí haga falta— pero afirmar que hace algo aquí sería falso.

Y es la transformación que **más** hay que vigilar, porque es la única que reemplaza por
significado y no por forma: `AV` por `AVENIDA` es inofensivo hasta que una entidad se
llame literalmente `AV`.

---

### 5.6 La validación cruzada de coordenadas

El defecto 6 —dos representaciones de la misma coordenada— es en realidad una
oportunidad: permite **validar el archivo contra sí mismo**, sin ninguna fuente externa.

Se convierte la UTM a geográficas y se mide la distancia a la publicada. La
distribución de los 1 928 desvíos no es la que uno esperaría:

| Desvío | Filas | Proporción | Qué es |
| --- | --- | --- | --- |
| menos de 5 m | 109 | 5,7 % | las dos columnas coinciden |
| 5 a 50 m | 37 | 1,9 % | zona intermedia |
| **50 a 80 m** | **1 779** | **92,3 %** | desplazamiento sistemático |
| 80 a 200 m | 0 | 0 % | — |
| **más de 200 m** | **3** | 0,16 % | **errores de dato reales** |

**Es bimodal.** Hay dos grupos nítidos: uno en torno a 0 metros y otro en torno a 61
metros, con casi nada en medio. En el archivo de centros de alto estándar el
desplazamiento es de 60,99 m con una desviación típica de **0,28 m**: prácticamente
constante.

Un desplazamiento constante no es un error de cálculo: es una **diferencia de datum
geodésico** entre las dos columnas. Y que haya 109 filas sin desplazamiento significa
algo más incómodo: **las dos columnas no se produjeron con un único proceso
consistente**. El archivo mezcla al menos dos procedencias para el mismo campo.

Eso es un hallazgo de gobernanza de datos, no de limpieza. No se arregla; se reporta y
se pregunta al publicador.

#### Los tres errores reales

Y separadas del desplazamiento, tres filas donde las dos coordenadas apuntan a lugares
distintos de la ciudad:

| Código | Comuna declarada | Desvío |
| --- | --- | --- |
| 123375 | MACUL | **10 272 m** |
| 9878 | HUECHURABA | **10 087 m** |
| 1224 | ESTACION CENTRAL | **4 623 m** |

Diez kilómetros. **La validación cruzada es lo único que los encuentra**, y aparecen
sin consultar ninguna fuente externa.

#### Por qué el umbral está en 200 metros

Porque los dos grupos están separados por un orden de magnitud: el sistemático llega a
80 m y los errores empiezan en 4 600 m. Cualquier umbral entre 100 y 1 000 m da el
mismo resultado, lo que es la señal de que el criterio no es arbitrario. Reportar los
1 779 desplazados como errores sería un falso positivo masivo; callar los tres, una
omisión.

---

## 6. El resultado

| Indicador | Valor |
| --- | --- |
| Lugares de carga totales | 1 928 |
| Abiertos | 1 927 |
| Cerrados (excluidos de los indicadores) | 1 |
| Tipos de local | 5 |
| Comunas distintas | 46 |
| Entidades distintas | 3 |
| Con horario publicado | 348 (**18,06 %**) |
| Coordenadas sospechosas | 3 |

Diez comunas con más lugares de carga:

| Comuna | Total | Puntos bip! | Metro | Retail | Centros |
| --- | --- | --- | --- | --- | --- |
| Maipú | 157 | 131 | 5 | 19 | 2 |
| Santiago | 148 | 105 | 25 | 16 | 2 |
| Las Condes | 104 | 90 | 6 | 8 | 0 |
| Puente Alto | 101 | 84 | 5 | 10 | 2 |
| La Florida | 95 | 74 | 11 | 8 | 2 |
| Pudahuel | 88 | 81 | 3 | 4 | 0 |
| Quilicura | 85 | 73 | 4 | 6 | 2 |
| Ñuñoa | 84 | 54 | 16 | 12 | 2 |
| Providencia | 82 | 56 | 14 | 11 | 1 |
| Cerro Navia | 69 | 69 | 0 | 0 | 0 |

Las tablas completas están en [`resultados/`](resultados/).

### Lo que estos números **no** permiten concluir

- **Nada sobre cobertura por habitante o por superficie.** La comuna llega como texto:
  se puede agrupar por comuna, no calcular densidad. Haría falta población y límites
  comunales, que no están en estas fuentes.
- **Nada sobre uso.** Los archivos dan ubicación y horario, no transacciones. Cerro
  Navia con 69 locales y ninguno de Metro ni de retail describe la **oferta**, no la
  demanda.
- **Nada sobre si el horario publicado es el real.** Es un «horario referencial», y así
  lo llama el propio archivo.

---

## 7. Qué quedó aprendido

Registros nuevos en la base de conocimiento:

- [`encabezado-no-esta-en-la-primera-fila`](../../knowledge/encabezado-no-esta-en-la-primera-fila.md)
- [`clave-que-no-es-clave`](../../knowledge/clave-que-no-es-clave.md)
- [`normalizar-antes-de-agrupar`](../../knowledge/normalizar-antes-de-agrupar.md)
- [`dos-coordenadas-un-lugar`](../../knowledge/dos-coordenadas-un-lugar.md)
- [`clave-candidata-no-es-identificador`](../../knowledge/clave-candidata-no-es-identificador.md)
  — de P02
- [`normalizar-tiene-dos-direcciones`](../../knowledge/normalizar-tiene-dos-direcciones.md)
  — de P04

Capacidades nuevas en el núcleo, reutilizables en cualquier dominio:

- `lab.excel.detect_header_row`, `read_messy_sheet`, `read_all_sheets` y `sheet_names`:
  leer la planilla que alguien maquetó para imprimir.
- `lab.textual`: normalización de claves, etiquetas legibles, medida de parecido y
  candidatos a duplicado. Sirve para deduplicar clientes, proveedores o nombres de
  empresa igual que para comunas.
- `lab.geo`: haversine, conversión de UTM y búsqueda del punto más cercano. Habilita
  el problema P08 (distancia de cada parada al lugar de carga más próximo).
- `lab.keys` (de P02): diagnóstico por columna, búsqueda exhaustiva de claves candidatas
  mínimas y clave subrogada determinista con comprobación de colisiones. Sirve para
  cualquier tabla cuya clave no esté documentada, que son casi todas.
- `lab.textual.merge_audit` (de P04): las formas crudas que absorbió cada fusión, para
  poder revisar la dirección del error que no se nota.

Un defecto corregido en el núcleo: `lab.geo.haversine_km` no aceptaba arreglos de
NumPy difundidos entre sí, que es justo lo que necesita una búsqueda del punto más
cercano por bloques. Lo encontró la prueba de `nearest_point`.

---

## Reproducir

```powershell
uv run python scripts/fetch_data.py bip-metro
```

```powershell
uv run python scripts/fetch_data.py bip-puntos
```

```powershell
uv run python scripts/fetch_data.py bip-centros-alto-estandar
```

```powershell
uv run python scripts/fetch_data.py bip-centros-estandar
```

```powershell
uv run python scripts/fetch_data.py bip-retail
```

```powershell
uv run python -m cases.bip_lugares_carga.solution
```

Los archivos del portal se actualizan: las cifras de este documento corresponden a la
versión descargada el 26 de noviembre de 2026, con las huellas registradas en
`procedencia.json`. Con una versión posterior cambiarán las magnitudes, no los nueve
defectos.

## Cuaderno, motores y gráfico

- [Resolución profesional paso a paso](CUADERNO.md), con el gráfico de distribución y el ranking comunal.
- [Abrir en Google Colab](https://colab.research.google.com/github/vladimiracunadev-create/applied-data-analysis-and-assessment-lab/blob/main/cases/bip_lugares_carga/cuaderno/colab.ipynb).
- [Pandas + Matplotlib](cuaderno/solucion_pandas.py): referencia comparable del ranking por comuna.
- [Polars + Matplotlib](cuaderno/solucion_polars.py): recalcula y grafica el ranking por comuna.
- [R + dplyr/readr + ggplot2](cuaderno/solucion.R) y [R Markdown](cuaderno/solucion.Rmd): contraste y distribución portable.
- [Figura publicada](cuaderno/svg/paso-13.svg).

