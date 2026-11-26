# P01 · Cuaderno de trabajo

## Consolidar cinco Excel públicos que describen lo mismo y no se parecen

**La pregunta.** ¿Cuántos lugares de carga de la tarjeta bip! hay, dónde están, y qué identifica a cada uno?

**Los datos.** Cinco archivos `.xlsx` del portal de datos abiertos del Ministerio de Transportes, licencia CC BY-NC 2.0 verificada. Seis hojas en total, 1 928 filas, de las cuales una está en la hoja de cerrados.

Este documento se lee de arriba abajo y no hay que abrir nada más. Cada paso trae el código de Pandas, **la salida que devuelve de verdad**, y cómo se hace lo mismo en Excel.

### Los pasos

| # | Paso | Dónde está la trampa |
| --- | --- | --- |
| 1 | [Mirar el archivo antes de leerlo](#paso-1) | sí |
| 2 | [Encontrar en qué fila está el encabezado](#paso-2) | sí |
| 3 | [Leer las seis hojas con su encabezado](#paso-3) | — |
| 4 | [Comprobar que los esquemas no coinciden](#paso-4) | sí |
| 5 | [Apilar los cinco al esquema común](#paso-5) | — |
| 6 | [El tipo de local no está en los datos](#paso-6) | sí |
| 7 | [¿La columna «código» es una clave?](#paso-7) | sí |
| 8 | [Normalizar antes de agrupar](#paso-8) | sí |
| 9 | [Contar por comuna](#paso-9) | sí |
| 10 | [Cuánto del campo «horario» existe de verdad](#paso-10) | sí |
| 11 | [Las dos coordenadas de cada fila, y cuál no cuadra](#paso-11) | sí |
| 12 | [Las filas donde las dos coordenadas se contradicen](#paso-12) | sí |

12 pasos, 10 con una trampa que conviene conocer antes de que aparezca en un dato propio.

---

<a id="paso-1"></a>

## Paso 1 · Mirar el archivo antes de leerlo

Un `read_excel` directo sobre uno de estos archivos devuelve basura, y conviene saber por qué antes de que pase. Lo primero es cuántas hojas hay y cómo se llaman. En el archivo de retail hay **dos**, y la segunda describe locales fuera de servicio: si se leen juntas quedan contados como abiertos.

**En Pandas**

```python
{archivo.stem: sheet_names(archivo)
 for archivo in sorted(ORIGINAL.glob('bip-*.xlsx'))}
```

**Lo que devuelve**

```
{'bip-centros-alto-estandar': ['Abiertos'], 'bip-centros-estandar': ['Abierto'], 'bip-metro': ['Abiertos'], 'bip-puntos': ['PCMA'], 'bip-retail': ['Abiertos', 'Cerrados']}
```

**En Excel**

Abrir el archivo y mirar las pestañas de abajo. Es el único paso del cuaderno donde Excel es mejor herramienta que Pandas: la estructura se ve de un vistazo.

> **La trampa.** `pd.read_excel(ruta)` sin `sheet_name` lee **solo la primera hoja** y no avisa de que hay otras. En el archivo de retail eso descarta en silencio la hoja `Cerrados`; en otro archivo podría descartar la mitad de los datos. Con `sheet_name=None` devuelve un diccionario con todas.

Y de paso: las hojas no se llaman igual en los cinco archivos —`Abiertos`, `Abierto`, `PCMA`—, de modo que tampoco sirve pedir una hoja por nombre.

---

<a id="paso-2"></a>

## Paso 2 · Encontrar en qué fila está el encabezado

El encabezado de estos archivos no está en la fila 1: está en la 7, la 9, la 13, la 10 y la 9, una distinta por archivo, porque arriba hay un título y filas vacías. Fijar `header=0` produce columnas llamadas `Unnamed: 0` y los nombres reales metidos como una fila de datos.

**En Pandas**

```python
crudo = pd.read_excel(ruta_metro, sheet_name='Abiertos', header=None)
detect_header_row(crudo)
```

**Lo que devuelve**

```
7
```

**En Excel**

Mirar la hoja y contar las filas. Para leer desde ahí: **Datos ▸ Obtener datos ▸ Desde un libro**, y en el editor de Power Query usar **Quitar filas superiores** y **Usar la primera fila como encabezado**.

> **La trampa.** La detección no puede ser «la primera fila sin celdas vacías»: una fila de datos también la cumple. `detect_header_row` busca la primera fila con varias celdas de **texto** no vacías seguida de filas con datos, y la declara. Si el archivo cambia de maqueta, el valor cambia y el código no se toca.

---

<a id="paso-3"></a>

## Paso 3 · Leer las seis hojas con su encabezado

`read_all_sheets` aplica la detección a cada hoja de cada archivo y devuelve, junto a la tabla, un informe de qué hubo que hacer para leerla. El informe no es decorativo: es lo que permite afirmar después que el 1 928 no se inventó.

**En Pandas**

```python
hojas = p01.cargar()
p01.informe_de_lectura(hojas)
```

**Lo que devuelve**

| fuente | hoja | tipo_local | abierto | encabezado_en_fila | filas_de_titulo_descartadas | filas | columnas | filas_vacias_descartadas | columnas_vacias_descartadas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bip-centros-alto-estandar | Abiertos | Centro bip! alto estándar | sí | 13 | 13 | 7 | 9 | 0 | 0 |
| bip-centros-estandar | Abierto | Centro bip! estándar | sí | 10 | 10 | 29 | 9 | 0 | 0 |
| bip-metro | Abiertos | Estación de Metro | sí | 7 | 7 | 143 | 10 | 0 | 0 |
| bip-puntos | PCMA | Punto bip! | sí | 9 | 9 | 1579 | 9 | 0 | 1 |
| bip-retail | Abiertos | Retail | sí | 9 | 9 | 169 | 10 | 0 | 0 |
| bip-retail | Cerrados | Retail | no | 9 | 9 | 1 | 10 | 0 | 0 |
*6 filas × 10 columnas.*

**En Excel**

Repetir el paso anterior cinco veces, una por archivo, y **anotar** la fila de encabezado de cada uno. Esa anotación es el equivalente manual de esta tabla, y es la que se pierde cuando alguien más abre el libro.

---

<a id="paso-4"></a>

## Paso 4 · Comprobar que los esquemas no coinciden

Los cinco archivos describen lo mismo con columnas distintas: unos traen nueve y otros diez, y el nombre del mismo campo cambia entre archivos —`NOMBRE FANTASIA` y `NOMBRE DE FANTASIA`—. Apilarlos sin armonizar produce una tabla con columnas duplicadas y medio llenas.

**En Pandas**

```python
p01.informe_de_esquemas(hojas)
```

**Lo que devuelve**

| fuente | hoja | codigo | entidad | nombre | direccion | comuna | horario | este | norte | latitud | longitud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bip-centros-alto-estandar | Abiertos | CODIGO | ENTIDAD | — | DIRECCION | COMUNA | HORARIO | ESTE | NORTE | LATITUD | LONGITUD |
| bip-centros-estandar | Abierto | CODIGO | ENTIDAD | — | DIRECCION | COMUNA | HORARIO | ESTE | NORTE | LATITUD | LONGITUD |
| bip-metro | Abiertos | CODIGO | ENTIDAD | NOMBRE FANTASIA | DIRECCION | COMUNA | HORARIO REFERENCIAL | ESTE | NORTE | LATITUD | LONGITUD |
| bip-puntos | PCMA | CODIGO | ENTIDAD | NOMBRE DE FANTASIA | DIRECCION | COMUNA | — | ESTE | NORTE | LATITUD | LONGITUD |
| bip-retail | Abiertos | CODIGO | ENTIDAD | NOMBRE FANTASIA | DIRECCION | COMUNA | HORARIO REFERENCIAL | ESTE | NORTE | LATITUD | LONGITUD |
| bip-retail | Cerrados | CODIGO | ENTIDAD | NOMBRE FANTASIA | DIRECCION | COMUNA | HORARIO REFERENCIAL | ESTE | NORTE | LATITUD | LONGITUD |
*6 filas × 12 columnas.*

**En Excel**

Pegar los encabezados de los cinco archivos en columnas contiguas y compararlos con `=COINCIDIR(A1;$B$1:$B$10;0)`: devuelve `#N/D` donde el campo no existe en el otro archivo.

> **La trampa.** Una de las columnas trae un **espacio al final del nombre**. Es invisible en Excel y en la salida de Pandas, y hace que un renombrado por igualdad exacta falle sin error: la columna simplemente no se renombra y queda fuera del esquema común.

---

<a id="paso-5"></a>

## Paso 5 · Apilar los cinco al esquema común

La correspondencia entre el nombre de cada archivo y el campo del esquema está **declarada** en el diccionario `ALIAS`, no deducida por parecido. Un acierto por casualidad hoy es un error mañana.

**En Pandas**

```python
consolidado = p01.consolidar(hojas)
consolidado[ESQUEMA]
```

**Lo que devuelve**

| codigo | entidad | nombre | direccion | comuna | horario | este | norte | latitud | longitud |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| L1 | METRO | SAN PABLO L1 | Av. San Pablo 6190 | LO PRADO | Lunes a Viernes: 6:00 a 23:00 horas, Sábados:… | 339892 | 6298155 | -33.444355 | -70.723068 |
| L1 | METRO | NEPTUNO | Av. Neptuno Oriente frente al 260 | LO PRADO | Lunes a Viernes: 6:00 a 23:00 horas, Sábados:… | 339903 | 6297368 | -33.451453 | -70.723086 |
| L1 | METRO | PAJARITOS | Av. General Bonilla 5900 | LO PRADO | Lunes a Viernes: 6:00 a 23:00 horas, Sábados:… | 340738 | 6296735 | -33.457279 | -70.714218 |
| L1 | METRO | LAS REJAS | Av. Libertador Bernardo O`Higgins 6056 | ESTACION CENTRAL | Lunes a Viernes: 6:00 a 23:00 horas, Sábados:… | 341466 | 6296689 | -33.457802 | -70.706398 |
| L1 | METRO | ECUADOR | Av. Libertador Bernardo O`Higgins Frente al 4… | ESTACION CENTRAL | Lunes a Viernes: 6:00 a 23:00 horas, Sábados:… | 342093 | 6296850 | -33.456448 | -70.699623 |
*1928 filas × 10 columnas, se muestran las primeras 5.*

**En Excel**

**Datos ▸ Obtener datos ▸ Combinar consultas ▸ Anexar**. A mano sería copiar y pegar cinco bloques, que funciona una vez y no se puede repetir cuando el portal publique la versión siguiente.

---

<a id="paso-6"></a>

## Paso 6 · El tipo de local no está en los datos

Ninguna columna dice si la fila es una estación de Metro, un punto bip! o un local de retail. Esa información está en el **nombre del archivo**, y si no se agrega al apilar se pierde para siempre.

**En Pandas**

```python
consolidado.groupby('tipo_local').size()
```

**Lo que devuelve**

| tipo_local | valor |
| --- | --- |
| Centro bip! alto estándar | 7 |
| Centro bip! estándar | 29 |
| Estación de Metro | 143 |
| Punto bip! | 1579 |
| Retail | 170 |
*5 valores.*

**En Excel**

Antes de anexar, agregar en cada consulta una **columna personalizada** con el tipo: en Power Query, `= "Estación de Metro"`. Copiando y pegando a mano, escribir el tipo en una columna nueva antes de pegar el bloque siguiente.

> **La trampa.** Es el error más fácil de cometer y el más difícil de notar: la tabla consolidada queda completa, sumable y sin ningún hueco, y simplemente ya no se puede responder «¿cuántos son estaciones de Metro?».

---

<a id="paso-7"></a>

## Paso 7 · ¿La columna «código» es una clave?

Se llama `codigo`, es la primera columna y parece un identificador. Medirlo cuesta una línea, y conviene hacerlo **antes** de cruzar con cualquier otra cosa.

**En Pandas**

```python
len(consolidado), consolidado['codigo'].nunique(), int(consolidado['codigo'].duplicated().sum())
```

**Lo que devuelve**

```
(1928, 1792, 136)
```

**En Excel**

En una columna libre, `=CONTAR.SI($A$2:$A$1929;A2)>1` y arrastrar. Cuenta de `VERDADERO` con `=CONTAR.SI(K2:K1929;VERDADERO)`. Valores distintos: `=CONTARA(UNICOS(A2:A1929))`.

> **La trampa.** En el archivo de Metro el código es la **línea** (`L1`, `L5`), no el local: 143 estaciones con 7 códigos. Y tampoco sirve la clave compuesta con el archivo de origen, que es la salida que uno probaría después.

---

<a id="paso-8"></a>

## Paso 8 · Normalizar antes de agrupar

`FULLCARGA` y `Fullcarga` son dos grupos para `groupby` y uno para una persona. Normalizar es quitar tildes, pasar a mayúsculas y colapsar espacios, con **la misma regla** en las dos tablas que se vayan a cruzar.

**En Pandas**

```python
crudas = consolidado['entidad'].nunique()
normalizadas = consolidado['entidad'].map(normalize_key).nunique()
{'crudas': crudas, 'normalizadas': normalizadas}
```

**Lo que devuelve**

```
{'crudas': 4, 'normalizadas': 3}
```

**En Excel**

`=MAYUSC(ESPACIOS(B2))` cubre mayúsculas y espacios. Las tildes hay que quitarlas a mano con `SUSTITUIR` anidado: `=SUSTITUIR(SUSTITUIR(MAYUSC(ESPACIOS(B2));"Á";"A");"É";"E")`, y así con cada vocal. Es feo, y es el motivo por el que esta parte se hace en Pandas.

> **La trampa.** Hay que guardar **las dos** formas: la clave para agrupar y la etiqueta para mostrar. Quedarse solo con la clave convierte `Ñuñoa` en `NUNOA` en el informe final, que es un empobrecimiento gratuito.

---

<a id="paso-9"></a>

## Paso 9 · Contar por comuna

La pregunta que se pedía: cuántos lugares de carga hay por comuna, con el desglose por tipo de local. Se agrupa por la **clave** normalizada y se muestra la **etiqueta** legible.

**En Pandas**

```python
p01.por_comuna(consolidado)
```

**Lo que devuelve**

| comuna_clave | comuna | Centro bip! alto estándar | Centro bip! estándar | Estación de Metro | Punto bip! | Retail | total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MAIPU | Maipu | 0 | 2 | 5 | 131 | 19 | 157 |
| SANTIAGO | Santiago | 1 | 1 | 25 | 105 | 16 | 148 |
| LAS CONDES | Las Condes | 0 | 0 | 6 | 90 | 8 | 104 |
| PUENTE ALTO | Puente Alto | 0 | 2 | 5 | 84 | 10 | 101 |
| LA FLORIDA | La Florida | 0 | 2 | 11 | 74 | 8 | 95 |
| PUDAHUEL | Pudahuel | 0 | 0 | 3 | 81 | 4 | 88 |
| QUILICURA | Quilicura | 0 | 2 | 4 | 73 | 6 | 85 |
| NUNOA | Ñuñoa | 2 | 0 | 16 | 54 | 12 | 84 |
*46 filas × 8 columnas, se muestran las primeras 8.*

**En Excel**

**Insertar ▸ Tabla dinámica**: `comuna` en Filas, `tipo_local` en Columnas, `codigo` en Valores con **Contar**. Sin dinámica: `=CONTAR.SI.CONJUNTO($E$2:$E$1929;$N2;$M$2:$M$1929;O$1)`, con la comuna en la columna N y el tipo en la fila 1.

> **La trampa.** `groupby` **descarta los nulos de la clave** sin avisar. Si una fila no trae comuna, desaparece del cuadro y el total deja de sumar el número de filas. Con `dropna=False` aparece como grupo propio, que es lo que hay que informar.

---

<a id="paso-10"></a>

## Paso 10 · Cuánto del campo «horario» existe de verdad

Antes de usar un campo hay que saber cuánto está lleno. Este está presente en menos de la quinta parte de las filas, lo que limita cualquier conclusión que dependa de él.

**En Pandas**

```python
con_dato = consolidado['horario'].notna() & (consolidado['horario'].astype('string').str.strip() != '')
round(float(con_dato.mean() * 100), 2)
```

**Lo que devuelve**

```
18.1
```

**En Excel**

`=CONTARA(F2:F1929)/FILAS(F2:F1929)`, con la celda en formato porcentaje.

> **La trampa.** `CONTARA` cuenta como no vacía una celda con una **fórmula que devuelve cadena vacía**. Si la columna viene de una consulta, el resultado es 100 % de cobertura sobre un campo vacío. `CONTAR.SI(F2:F1929;"<>")` tiene el mismo problema; la forma fiable es `CONTAR.SI(F2:F1929;"?*")`, que exige al menos un carácter.

---

<a id="paso-11"></a>

## Paso 11 · Las dos coordenadas de cada fila, y cuál no cuadra

Los archivos traen la **misma ubicación dos veces**: en UTM (`este`/`norte`) y en grados (`latitud`/`longitud`). Convertir una y compararla con la otra es una validación que no necesita ninguna fuente externa, y es la que encontró tres errores de hasta 10,3 km.

**En Pandas**

```python
lat_utm, lon_utm = utm_to_latlon(consolidado['este'], consolidado['norte'], zona=19)
desvio_m = haversine_km(lat_utm, lon_utm, consolidado['latitud'], consolidado['longitud']) * 1000
pd.cut(desvio_m, [0, 10, 50, 58, 62, 100, 1e9]).value_counts().sort_index()
```

**Lo que devuelve**

|  | count |
| --- | --- |
| (0.0, 10.0] | 109 |
| (10.0, 50.0] | 37 |
| (50.0, 58.0] | 2 |
| (58.0, 62.0] | 1768 |
| (62.0, 100.0] | 9 |
| (100.0, 1000000000.0] | 3 |
*6 valores.*

**En Excel**

La conversión de UTM a grados **no se hace en Excel** de forma razonable: es una serie de ocho términos. Lo que sí se hace es la distancia entre dos pares de grados, con haversine en una celda:

```
=2*6371000*ASENO(RAIZ(SENO((RADIANES(I2)-RADIANES(L2))/2)^2
  + COS(RADIANES(L2))*COS(RADIANES(I2))
  * SENO((RADIANES(J2)-RADIANES(M2))/2)^2))
```

con la coordenada publicada en I y J, y la convertida en L y M.

Y el histograma, que es lo que revela la forma: poner los topes de los tramos en `P1:P6` y seleccionar `Q1:Q7` para `=FRECUENCIA(N2:N1929;P1:P6)`. Devuelve un tramo más que topes, porque el último recoge todo lo que los supera.

> **La trampa.** Mirar la media, o incluso los percentiles 50, 90 y 99, **esconde el hallazgo**: los tres caen en 61 m y la distribución parece un desvío único con tres atípicos. El histograma muestra otra cosa: **109 filas en torno a 0 m y 1 768 en torno a 61 m**, dos grupos nítidos.

Esa bimodalidad es la firma de **dos datums distintos** —parte del archivo con un sistema de referencia y parte con otro— y no de un error de redondeo, que daría una sola campana. Un resumen de cinco números no distingue una cosa de la otra: hay que mirar la forma.

Y lo que corresponde con un hallazgo así es reportarlo al publicador, no corregirlo en silencio: no se sabe cuál de las dos representaciones es la buena.

---

<a id="paso-12"></a>

## Paso 12 · Las filas donde las dos coordenadas se contradicen

Con el desvío calculado, un umbral declarado separa el desplazamiento sistemático de los errores reales. 200 m es holgado frente a los 61 m de mediana y estricto frente a los errores, que son de kilómetros.

**En Pandas**

```python
sospechosas = p01.coordenadas_sospechosas(consolidado)
sospechosas[['fuente', 'codigo', 'comuna', 'desvio_m']]
```

**Lo que devuelve**

| fuente | codigo | comuna | desvio_m |
| --- | --- | --- | --- |
| bip-puntos | 123375 | MACUL | 10271.629696 |
| bip-puntos | 9878 | HUECHURABA | 10086.992305 |
| bip-puntos | 1224 | ESTACION CENTRAL | 4623.378791 |
*3 filas × 4 columnas.*

**En Excel**

Con el desvío en la columna N: filtro `>200`, o `=SI(N2>200;"revisar";"")` y autofiltro sobre esa columna.

> **La trampa.** El umbral es una **decisión** y hay que escribirla con su motivo. Un umbral elegido después de ver los datos, para que el número de hallazgos quede cómodo, no es un criterio: es el resultado disfrazado de criterio.

---

## Qué quedó resuelto

1 928 filas consolidadas, 1 927 abiertas, 46 comunas y 3 entidades. El `codigo` no identifica una fila, ni junto al archivo de origen. La validación cruzada de las dos coordenadas encontró tres errores de hasta 10,3 km y un desplazamiento sistemático de 61 m con distribución bimodal.

Lo que **no** se puede concluir con estos datos: cuánta gente usa cada local —no hay transacciones—, ni si está abierto cuando alguien llega —el horario está en el 18,06 % de las filas—.

## Reproducir

```powershell
python scripts/fetch_data.py bip-metro bip-puntos bip-centros-alto-estandar bip-centros-estandar bip-retail
python -m cases.bip_lugares_carga.solution
```
