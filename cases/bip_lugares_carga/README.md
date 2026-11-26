# P01 · Consolidar cinco Excel públicos heterogéneos

**Datos públicos reales con licencia verificada.** Es el ejercicio más parecido a lo
que se pide en una evaluación técnica de cuatro horas con Excel y Pandas: cinco
archivos que hay que leer, armonizar, limpiar y agregar, con el desorden que tienen
los archivos de verdad.

> Licencia **Creative Commons Atribución-NoComercial 2.0**, declarada y verificada en
> los metadatos del portal de datos abiertos. Los archivos de origen no se versionan;
> sí se versionan el registro de procedencia y las tablas de resultado.

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

### 5.5 Normalizar antes de agrupar

`FULLCARGA` y `Fullcarga` son dos grupos para `groupby` y uno para una persona.
`lab.textual.normalize_key` quita tildes, pasa a mayúsculas, colapsa espacios y recorta
los extremos. Resultado: **tres entidades**, no cinco variantes.

| Entidad | Locales | Comunas | Tipos |
| --- | --- | --- | --- |
| FULLCARGA | 1 615 | 36 | 3 |
| WALMART | 169 | 44 | 1 |
| METRO | 143 | 26 | 1 |

Y se conserva la etiqueta legible aparte, para que el informe diga `Ñuñoa` y no
`NUNOA`.

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

Capacidades nuevas en el núcleo, reutilizables en cualquier dominio:

- `lab.excel.detect_header_row`, `read_messy_sheet`, `read_all_sheets` y `sheet_names`:
  leer la planilla que alguien maquetó para imprimir.
- `lab.textual`: normalización de claves, etiquetas legibles, medida de parecido y
  candidatos a duplicado. Sirve para deduplicar clientes, proveedores o nombres de
  empresa igual que para comunas.
- `lab.geo`: haversine, conversión de UTM y búsqueda del punto más cercano. Habilita
  el problema P08 (distancia de cada parada al lugar de carga más próximo).

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
