---
id: clave-que-no-es-clave
tipo: error
titulo: Una columna llamada «código» no es una clave hasta que se mide
etiquetas: [calidad-datos, cruce-consolidacion, datos-reales, errores-frecuentes]
fuente: cases/bip_lugares_carga/solution.py
relacionados: [cruce-con-cardinalidad, encabezado-no-esta-en-la-primera-fila, normalizar-antes-de-agrupar]
---

**El caso.** Cinco archivos públicos de lugares de carga, todos con una columna
`CODIGO`. La suposición natural: es la clave, sirve para cruzar y para contar.

Lo que dicen los números:

| Ámbito | Filas | Códigos distintos | Repetidos | ¿Es clave? |
| --- | --- | --- | --- | --- |
| Consolidado | 1 928 | 1 792 | 136 | **no** |
| Solo Metro | 143 | **7** | 136 | **no** |
| Solo Puntos bip! | 1 579 | 1 579 | 0 | sí |
| Solo retail | 170 | 170 | 0 | sí |
| **Compuesta (archivo + código)** | 1 928 | 1 792 | 136 | **no** |

**La causa.** En el archivo de Metro el código no identifica el local: identifica la
**línea** (`L1`, `L2`, `L3`…). Hay 143 estaciones y 7 códigos. La columna se llama
igual que en los otros archivos y significa otra cosa.

**El hallazgo que importa.** Ni siquiera la clave compuesta `archivo + código`
identifica una fila. Es el resultado que uno no espera: lo habitual es que añadir el
origen resuelva la colisión. Aquí no, porque la colisión es **dentro** de un archivo.
Hace falta una clave subrogada, o un tercer componente.

**El costo de no medirlo.** Un cruce sobre esa columna multiplica filas: cada registro
que se una contra `L1` se replica 143 veces. La suma posterior queda inflada sin ningún
error visible, y el total sigue pareciendo verosímil.

**La comprobación, que cuesta tres líneas:**

```python
total, distintos = len(df), df["codigo"].nunique()
nulos = int(df["codigo"].isna().sum())
es_clave = distintos == total and nulos == 0
```

Y las dos preguntas que hay que hacerse cuando no lo es:

1. **¿Se repite con contenido idéntico?** Entonces es un duplicado exacto, y se elimina
   contando.
2. **¿Se repite con contenido distinto?** Entonces la columna no es lo que se creía, y
   hay que averiguar **qué** identifica antes de usarla.

**Regla general.** El nombre de una columna es una pista, no una especificación. Lo
mismo vale para `id`, `rut`, `folio`, `sku`, `nro_documento`: identifican algo, y hay
que establecer qué. Ver [[cruce-con-cardinalidad]].
