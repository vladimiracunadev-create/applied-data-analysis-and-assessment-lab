# Excel: fórmulas verificables y tablas dinámicas

## Objetivos de aprendizaje

1. Importar un CSV controlando codificación y separador, y convertirlo en tabla con
   nombre.
2. Construir cruces con `BUSCARX` declarando el valor para la clave no encontrada.
3. Agregar con `SUMAR.SI.CONJUNTO`, `CONTAR.SI.CONJUNTO` y `PROMEDIO.SI.CONJUNTO`
   usando el denominador correcto.
4. Construir una tabla dinámica y saber qué cuenta cada campo de valores.
5. Separar entradas, cálculos y resultados en hojas distintas y dejar el libro
   auditable.
6. Reproducir en Excel un indicador calculado en Python y confrontar ambos resultados.

## Prerrequisitos

Bloque de fundamentos. Excel 2021, Microsoft 365, LibreOffice Calc reciente o Google
Sheets. `BUSCARX` requiere Microsoft 365 / Excel 2021 o Google Sheets; en versiones
anteriores se usa `INDICE` + `COINCIDIR`.

## Definiciones simples y formales

**Tabla de Excel.** *Simple:* un rango convertido en tabla con `Ctrl+T`. *Formal:*
rango con nombre, encabezados tipados y referencias estructuradas que se expanden
automáticamente al agregar filas. Es el único objeto de Excel cuyas fórmulas no se
rompen al crecer los datos.

**Referencia estructurada.** `Viajes[pasajeros]` en lugar de `E6:E455`. Sobrevive a la
inserción de filas y columnas.

**Referencia absoluta y relativa.** `$A$1` fija fila y columna; `A1` las desplaza al
copiar; `$A1` fija solo la columna. Es el mecanismo que permite escribir una fórmula
una vez y arrastrarla.

**Tabla dinámica.** Resumen interactivo que agrupa por campos de fila y columna y
agrega un campo de valores. Es un `groupby` con interfaz gráfica.

**Función de matriz dinámica.** Función que devuelve varios valores y los derrama en
celdas vecinas: `UNICOS`, `FILTRAR`, `ORDENAR`, `BUSCARX` con rango de retorno.

## Explicación conceptual

Un libro de Excel puede ser la mejor o la peor herramienta de una entrega técnica, y
la diferencia no está en las fórmulas: está en la estructura.

El patrón que el laboratorio exige es de **tres zonas**:

- **Entradas.** Los datos como llegaron. No se editan, no se ordenan, no se corrigen.
  Si hay que corregir algo, se hace en una columna de la zona de cálculos.
- **Cálculos.** Una columna por regla, con una fórmula que se lee de izquierda a
  derecha. Aquí viven los cruces, las conversiones y las banderas de validez.
- **Resultados.** Los indicadores, agregados desde la zona de cálculos con
  `SUMAR.SI.CONJUNTO` o tablas dinámicas.

Esta separación es exactamente la misma que en el código: datos crudos inmutables,
transformación explícita, salida. La ventaja de Excel es que cada paso es visible
abriendo una celda; la desventaja es que nada obliga a mantener el orden. La
estructura lo suple.

El segundo principio: **un resultado pegado como valor no demuestra nada.** Si el
número viene de Python y se copió a la celda, el libro no aporta verificación: solo
repite. La verificación aparece cuando las dos herramientas calculan por separado y se
comparan en una hoja de control.

## Desarrollo de fundamentos

### Importar sin romper los acentos

**Datos → Obtener datos → Desde texto/CSV**. En el cuadro de diálogo se eligen origen
del archivo (UTF-8) y delimitador. Hacer doble clic sobre el CSV usa la configuración
regional del sistema y es la causa habitual de los acentos roto s y de las fechas
interpretadas al revés.

Las fechas merecen atención aparte: una columna de texto `2026-10-01 08:23:00` no es
una fecha hasta que se convierte. Mientras siga siendo texto, `(fin − inicio)`
devuelve `#¡VALOR!`.

### `BUSCARX` y el cuarto argumento

```excel
=BUSCARX([@recorrido_id];Recorridos[recorrido_id];Recorridos[operador_id];"SIN CLAVE")
```

| Argumento | Papel |
| --- | --- |
| 1.º | valor buscado |
| 2.º | rango donde buscar |
| 3.º | rango que se devuelve |
| 4.º | **qué devolver si no se encuentra** |

El cuarto argumento es opcional en la sintaxis y obligatorio en la práctica del
laboratorio. Sin él, una clave desconocida devuelve `#N/D`, y `#N/D` se propaga: las
tablas dinámicas lo muestran como error, las sumas fallan, y el cruce queda incompleto
sin que nadie lo cuantifique. Con `"SIN CLAVE"` el problema se vuelve visible y
contable con un `CONTAR.SI`.

`BUSCARV` sigue funcionando pero exige que la columna buscada sea la primera del rango
y cuenta columnas por número, de modo que insertar una columna rompe el resultado sin
error visible. En Excel 2019 o anterior, la alternativa robusta es
`=INDICE(Recorridos[operador_id];COINCIDIR([@recorrido_id];Recorridos[recorrido_id];0))`.

### Las funciones `.SI.CONJUNTO` y el denominador

```excel
Numerador:   =SUMAR.SI.CONJUNTO(Calculos[pasajeros];Calculos[operador];$A6;Calculos[valido];1)
Recuento:    =CONTAR.SI.CONJUNTO(Calculos[operador];$A6;Calculos[valido];1)
Promedio:    =PROMEDIO.SI.CONJUNTO(Calculos[duracion];Calculos[recorrido];$A6;Calculos[dur_ok];1)
```

El orden de argumentos difiere entre ellas y es una fuente constante de errores:
`SUMAR.SI.CONJUNTO` y `PROMEDIO.SI.CONJUNTO` reciben **primero** el rango a agregar;
`CONTAR.SI.CONJUNTO` empieza directamente por los pares rango/criterio.

El criterio del denominador es el punto delicado. Una columna de bandera que devuelve
`""` cuando el indicador no aplica **no** se cuenta con `"<>"`: ese criterio incluye
las celdas con cadena vacía. Se usa `">=0"`, que solo admite números. Ver
[[countifs-cadena-vacia]].

### División protegida

```excel
=SI(N(C6)=0;"";100*D6/C6)
```

`N()` convierte texto y vacío en cero, de modo que la condición cubre los tres casos
problemáticos con una sola comprobación. `SI.ERROR` no sirve aquí: oculta cualquier
error, incluido un `#¡REF!` producido por una columna borrada, y convierte un problema
estructural en una celda vacía.

### Tabla dinámica: qué cuenta cada cosa

| Campo de valores | Qué cuenta |
| --- | --- |
| Suma | total del campo numérico |
| Cuenta | celdas **no vacías**, texto incluido |
| Cuenta numérica | solo celdas con número |
| Promedio | media de las celdas numéricas; ignora vacías |

«Cuenta» sobre una columna con fórmulas que devuelven `""` incluye esas celdas, con el
mismo efecto que el `"<>"` de `CONTAR.SI.CONJUNTO`. Cuando el recuento es el
denominador de una tasa, hay que usar **cuenta numérica**.

## Fórmulas matemáticas explicadas

La conversión de fechas de Excel es la única aritmética propia de esta clase:

```
Excel almacena una fecha-hora como días decimales desde 1899-12-30.
1 día = 24 h = 1440 min = 86 400 s

duración en minutos = (fin − inicio) · 1440
duración en horas   = (fin − inicio) · 24
```

El resultado de `(fin − inicio)` hereda el formato de fecha de las celdas de origen:
hay que cambiar el formato de la celda de resultado a **Número**, o el valor 0,03125
se mostrará como una hora del día.

Los indicadores son los mismos del bloque de matemáticas:

```
demanda        = Σ pasajeros sobre viajes válidos
cumplimiento   = 100 · realizados / programados          [%]
puntualidad    = 100 · puntuales / evaluados             [%]
```

## Significado de variables, símbolos y unidades

| Elemento | Significado | Unidad |
| --- | --- | --- |
| 1440 | Minutos en un día; factor de conversión del serial de Excel | min/día |
| `[@campo]` | Valor del campo en la fila actual de la tabla | según el campo |
| `$A6` | Columna fija, fila relativa | referencia |
| `N()` | Convierte a número; texto y vacío dan 0 | adimensional |
| `valido` | Bandera 1/0 de validez para el indicador | 0/1 |
| `""` | Cadena vacía devuelta por fórmula; **no** es celda vacía | texto |

## Ejemplos, de simple a complejo

### Ejemplo 1 — duración en minutos

Con `C6` el inicio y `D6` el fin, ambos ya convertidos a fecha-hora:

```excel
=SI(O(C6="";D6="");"";(D6-C6)*1440)
```

Devuelve vacío si falta un extremo, en lugar de un número negativo o un error.

### Ejemplo 2 — bandera de validez para la demanda

```excel
=SI(Y(K6=1;ESNUMERO(E6);E6>=0);1;0)
```

Tres condiciones encadenadas: el viaje es realizado con clave conocida (`K6=1`), el
conteo de pasajeros es un número y no es negativo. `ESNUMERO` es lo que distingue
celda vacía de cero.

### Ejemplo 3 — demanda por operador con verificación

| | A | B | C | D | E |
| --- | --- | --- | --- | --- | --- |
| 5 | operador | pasajeros_excel | pasajeros_python | diferencia | control |
| 6 | Operador A | `=SUMAR.SI.CONJUNTO(...)` | 6124 | `=B6-C6` | `=SI(ABS(D6)<0,0001;"OK";"REVISAR")` |

La columna de control es el entregable que cierra la validación cruzada. Una hoja
resumen cuenta los `REVISAR`:

```excel
=CONTAR.SI('20_demanda'!E:E;"REVISAR")
```

Ese número debe ser cero.

### Ejemplo 4 — puntualidad con el denominador correcto

Columna `puntual` (1, 0 o `""`):

```excel
Numerador:   =CONTAR.SI.CONJUNTO(Calc[recorrido];$A6;Calc[puntual];1)
Denominador: =CONTAR.SI.CONJUNTO(Calc[recorrido];$A6;Calc[puntual];">=0")
Indicador:   =SI(Denominador=0;"";100*Numerador/Denominador)
```

Con `"<>"` en lugar de `">=0"`, el denominador incluiría todos los viajes cancelados y
la puntualidad bajaría sin motivo.

## Aplicaciones profesionales

- **Evaluaciones técnicas del sector público.** Excel es herramienta obligatoria en
  buena parte de ellas, y lo que se evalúa es la verificabilidad del libro, no la
  destreza con atajos.
- **Conciliaciones contables.** La estructura de tres zonas es el estándar: extracto
  como entrada, cálculos de conciliación, diferencias como resultado.
- **Informes de gestión mensuales.** Una tabla dinámica actualizable sobre datos
  importados con Power Query reemplaza un proceso manual repetido.
- **Control de calidad en operaciones.** Banderas de validez por regla, contadas en
  una hoja de resumen.

## Código fuente comentado

El libro resuelto del laboratorio se construye con `scripts/build_excel_solutions.py`,
que escribe **fórmulas**, no valores. Las que importan:

```python
# Cruce con valor por defecto explícito para la clave desconocida.
f'=XLOOKUP({cell["recorrido_id"]},{rec_id},{rec_ope},"SIN CLAVE")'

# Duración en minutos, protegida ante extremos ausentes.
f'=IF(OR({cell["inicio"]}="",{cell["fin"]}=""),"",({cell["fin"]}-{cell["inicio"]})*1440)'

# Bandera de demanda válida: realizado + clave conocida + número + no negativo.
f'=IF(AND({cell["realizado"]}=1,ISNUMBER({cell["pasajeros"]}),{cell["pasajeros"]}>=0),1,0)'

# Agregación con filtro por bandera.
f'=SUMIFS({ranges["pasajeros"]},{ranges["operador"]},$A{row},{ranges["valido_demanda"]},1)'

# Denominador correcto de la puntualidad: ">=0", no "<>".
f'=COUNTIFS({ranges["recorrido_id"]},$A{row},{ranges["puntual"]},">=0")'
```

El archivo `.xlsx` almacena los nombres de función en inglés; Excel los muestra
traducidos según la configuración regional. El separador de argumentos en el archivo es
siempre la coma, aunque Excel muestre punto y coma. `docs/equivalencias.md` tiene la
correspondencia completa.

Para construir el libro:

```powershell
uv run python scripts/build_excel_solutions.py --case 1
```

Abra `solutions/excel/case_1_resuelto.xlsx`, vaya a la hoja `30_control` y compruebe
que los cuatro valores son cero.

## Ejercicios prácticos

1. Importe `data/case_2/viajes.csv` con **Desde texto/CSV** en UTF-8 y conviértalo en
   tabla llamada `Viajes`. Verifique que las fechas son fechas y no texto.
2. Agregue las columnas de cálculo: `operador`, `meta`, `duracion_min`, `realizado`,
   `valido_demanda`, `puntual`. Use `BUSCARX` con cuarto argumento.
3. Construya la demanda por operador con `SUMAR.SI.CONJUNTO` y verifíquela contra
   `reference_outputs/case_2/demanda.csv`.
4. Construya la misma demanda con una tabla dinámica. ¿Coincide? Si no, revise qué
   campo de valores está usando.
5. Calcule la puntualidad por recorrido con `">=0"` y luego con `"<>"`. Explique la
   diferencia numérica.
6. Agregue una hoja `30_control` con una columna de diferencia y un recuento de
   `REVISAR`. El recuento debe ser cero.
7. Inserte una columna nueva en medio de la tabla de entradas. ¿Qué fórmulas se rompen
   y por qué las referencias estructuradas no?

## Soluciones explicadas

1. Si las fechas quedan alineadas a la izquierda, siguen siendo texto. Se corrige en
   el paso de importación, eligiendo el tipo de la columna, o con
   `=VALOR.FECHA()`/`=FECHANUMERO()` en una columna de cálculo. No se corrige editando
   la zona de entradas.

2. El cuarto argumento de `BUSCARX` convierte el `#N/D` en `"SIN CLAVE"`, y así se
   puede contar: `=CONTAR.SI(Calculos[operador_id];"SIN CLAVE")` debe dar 2 en el
   caso 2.

3. Debe coincidir exactamente. Si difiere, las causas más probables en orden: la
   bandera `valido_demanda` está mal construida; se está sumando sobre todos los
   viajes y no solo los válidos; o los duplicados exactos no se eliminaron.

4. Una tabla dinámica con **Cuenta** en lugar de **Suma** da el número de viajes y no
   los pasajeros. Con **Cuenta** sobre una columna que tiene `""`, el resultado incluye
   esas celdas.

5. Con `"<>"` el denominador incluye los viajes cancelados y los de duración
   inválida, cuya celda `puntual` contiene `""`. La puntualidad resultante es más baja
   y no corresponde a ningún indicador definido.

6. La diferencia debe ser cero en todas las filas. Si aparece un `REVISAR`, el valor
   de Python y el de Excel se calcularon sobre conjuntos distintos: el error está en
   una bandera, no en la fórmula de agregación.

7. Las fórmulas con referencias de rango (`E6:E455`) apuntan ahora a la columna
   equivocada y siguen devolviendo un número, sin error visible. Las referencias
   estructuradas (`Viajes[pasajeros]`) siguen el nombre de la columna y continúan
   siendo correctas. Es la razón por la que el laboratorio exige tablas con nombre.

## Errores frecuentes

- **Hacer doble clic sobre el CSV** y romper los acentos o el orden de día y mes.
- **Pegar como valor** un resultado calculado en otra herramienta y presentarlo como
  verificación.
- **`BUSCARX` sin cuarto argumento**, dejando que `#N/D` se propague.
- **`CONTAR.SI.CONJUNTO` con `"<>"`** como denominador de una tasa.
- **`SI.ERROR` envolviendo toda la fórmula**, lo que oculta errores estructurales.
- **Promediar porcentajes** en la fila de totales, en lugar de dividir las sumas.
- **Editar la zona de entradas** para «arreglar» un dato.
- **Rangos sin nombre** que se desalinean al insertar filas o columnas.
- **Dejar el resultado de una resta de fechas con formato de fecha**, mostrando
  «00:45» donde debía decir 45.

## Criterios de validación

1. Las hojas están separadas en entradas, cálculos y resultados.
2. La zona de entradas no tiene ninguna celda editada a mano.
3. Todo indicador es una fórmula que se puede abrir y leer.
4. Los cruces declaran el valor para la clave no encontrada, y las claves no
   encontradas están contadas.
5. Cada tasa tiene su denominador escrito y protegido contra cero.
6. Existe una hoja de control que compara contra la otra herramienta, y su recuento de
   discrepancias es cero.
7. Los gráficos declaran unidad y período.

## Preguntas de evaluación

1. ¿Por qué `(D6-C6)*1440` puede mostrar una hora del día en lugar de un número?
2. ¿Qué devuelve `BUSCARX` si no encuentra la clave y no se declaró el cuarto
   argumento? ¿Qué consecuencia tiene en una tabla dinámica?
3. ¿Cuál es la diferencia entre `CONTAR`, `CONTARA` y `CONTAR.BLANCO` sobre una columna
   con fórmulas que devuelven `""`?
4. ¿Por qué se prefiere `SI(N(C6)=0;"";...)` a `SI.ERROR(...;"")`?
5. ¿En qué orden recibe sus argumentos `SUMAR.SI.CONJUNTO` frente a
   `CONTAR.SI.CONJUNTO`?
6. ¿Qué ventaja tiene una tabla con nombre frente a un rango al insertar una columna?

## Referencias verificables

- Microsoft. «Función BUSCARX».
  <https://support.microsoft.com/es-es/office/buscarx-funci%C3%B3n-buscarx-b7fd680e-6d10-43e6-84f9-88eae8bf5929>
- Microsoft. «Función SUMAR.SI.CONJUNTO».
  <https://support.microsoft.com/es-es/office/sumar-si-conjunto-funci%C3%B3n-sumar-si-conjunto-c9e748f5-7ea7-455d-9406-611cebce642b>
- Microsoft. «Función CONTAR.SI.CONJUNTO».
  <https://support.microsoft.com/es-es/office/contar-si-conjunto-funci%C3%B3n-contar-si-conjunto-dda3dc6e-f74e-4aee-88bc-aa8c2a866842>
- Microsoft. «Crear una tabla dinámica para analizar datos de una hoja de cálculo».
  <https://support.microsoft.com/es-es/office/crear-una-tabla-din%C3%A1mica-para-analizar-datos-de-una-hoja-de-c%C3%A1lculo-a9a84538-bfe9-40a9-a8e9-f99134456576>
- Microsoft. «Usar referencias estructuradas en tablas de Excel».
  <https://support.microsoft.com/es-es/office/usar-referencias-estructuradas-en-tablas-de-excel-f5ed2452-2337-4f71-bed3-c8ae6d2b276e>
- Documentación de XlsxWriter, biblioteca usada para generar los libros.
  <https://xlsxwriter.readthedocs.io/>

## Glosario técnico

| Término | Definición |
| --- | --- |
| Campo de valores | Campo agregado en una tabla dinámica. |
| Matriz dinámica | Función que derrama varios resultados en celdas vecinas. |
| Power Query | Motor de obtención y transformación de datos de Excel. |
| Referencia absoluta | `$A$1`: no cambia al copiar la fórmula. |
| Referencia estructurada | `Tabla[columna]`: referencia por nombre, robusta. |
| Serial de fecha | Representación de una fecha como días decimales. |
| Tabla de Excel | Rango con nombre, encabezados y expansión automática. |
| Tabla dinámica | Resumen agrupado e interactivo de una tabla. |
| `#N/D` | Error de valor no encontrado; se propaga a las agregaciones. |
| `#¡DIV/0!` | Error de división por cero. |
| `#¡VALOR!` | Error de tipo: operación aritmética sobre texto. |
