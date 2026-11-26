---
id: encabezado-no-esta-en-la-primera-fila
tipo: patron
titulo: Detectar la fila del encabezado en una planilla maquetada para imprimir
etiquetas: [excel, hojas-de-calculo, lectura-escritura-datos, datos-reales, calidad-datos]
fuente: lab/excel.py, cases/bip_lugares_carga/solution.py
relacionados: [clave-que-no-es-clave, normalizar-antes-de-agrupar, defecto-que-no-existe]
---

**El hecho.** Cinco archivos Excel publicados por el **mismo organismo**, con el mismo
tipo de contenido, tenían el encabezado en las filas **7, 9, 13, 10 y 9**.

Lo que devuelve `pd.read_excel` sin más:

```
  Unnamed: 0          Unnamed: 1  Unnamed: 2  ...
0      METRO                 NaN         NaN
1        NaN                 NaN         NaN
```

Diez columnas `Unnamed` y una primera fila que dice `METRO` en una celda y nada en las
otras nueve. Nada de eso es un error del archivo: arriba hay un título, un logo, una
fecha de actualización y filas en blanco de maquetación, porque el archivo se hizo para
que una persona lo imprimiera.

**Por qué no fijar el número de fila.** Funciona el día que se escribe. En la próxima
publicación el organismo agrega una línea al título y el proceso lee la tabla corrida
una fila, sin error y sin aviso: los nombres de columna pasan a ser el primer registro
y el primer registro desaparece.

**El criterio que funciona.** La primera fila con **al menos cuatro celdas no vacías
cuyos valores sean todos texto**:

```python
def detect_header_row(frame, min_filled=4, max_scan=40):
    for posicion in range(min(max_scan, len(frame))):
        llenas = frame.iloc[posicion].dropna()
        if len(llenas) >= min_filled and all(
            isinstance(v, str) and v.strip() for v in llenas
        ):
            return posicion
    raise ValueError("No se encontró una fila de encabezado…")
```

Funciona porque las tres poblaciones son distinguibles:

| Tipo de fila | Celdas llenas | Contenido |
| --- | --- | --- |
| Título | 1 | texto |
| Blanco de maquetación | 0 | — |
| **Encabezado** | **muchas** | **todo texto** |
| Datos | muchas | mezcla con números |

Hay que leer con `header=None` primero, para que nada se interprete como encabezado
antes de decidir cuál es.

**Fallar en lugar de adivinar.** Si no encuentra candidata, levanta un error. Devolver
una fila arbitraria convierte datos en nombres de columna y contamina todo lo que
sigue; un error detiene el proceso donde el problema es visible.

**Informar lo que se hizo.** Que el encabezado estaba en la fila 13 y se descartaron 13
filas de título es parte del entregable de calidad. Una hoja de 151 filas que entrega
143 registros no tiene 8 registros perdidos: tiene 8 filas de maquetación. Sin ese
dato, nadie puede distinguir una cosa de la otra.

**Dónde más aparece.** Extractos bancarios, informes de gestión exportados de un
sistema, nóminas, planillas de inventario, cualquier archivo que alguien formateó para
una reunión. Y el caso hermano: el **pie** de tabla con totales, que hay que descartar
por abajo con el mismo cuidado.
