---
id: normalizar-tiene-dos-direcciones
tipo: patron
titulo: Normalizar tiene dos direcciones de error y solo una se nota
etiquetas: [limpieza-normalizacion, calidad-datos, errores-frecuentes, pandas, comunicacion-resultados]
fuente: lab/textual.py
relacionados: [normalizar-antes-de-agrupar, punto-ciego-del-control, agregado-que-suaviza, clave-candidata-no-es-identificador]
---

**Las dos direcciones.**

| Error | Qué produce | ¿Se nota? |
| --- | --- | --- |
| **Dejar separado lo que es igual** — `FULLCARGA` y `Fullcarga` | un grupo de más, con el total partido | **sí**: aparecen dos filas donde debería haber una |
| **Juntar lo que es distinto** — `AV` y `AVENIDA`, cuando una entidad se llama `AV` | un grupo de menos, con el total sumado | **no**: el resultado es verosímil |

Casi toda la atención va a la primera, que es la que salta a la vista. La segunda no
deja rastro: produce una tabla más limpia, con menos filas y totales mayores, y no hay
nada en el resultado que sugiera revisarla. Ver [[punto-ciego-del-control]].

**Las dos preguntas, y las dos funciones.**

```python
from lab.textual import normalization_report, merge_audit

normalization_report(datos["entidad"], "entidad")   # ¿CUÁNTAS fusiones?  → el argumento
merge_audit(datos["entidad"], "entidad")            # ¿CUÁLES fusiones?   → la revisión
```

La primera cuantifica los grupos espurios evitados: es el argumento a favor de
normalizar. La segunda devuelve, por cada clave normalizada, **las formas crudas que
absorbió**, y es la única parte de una normalización que una persona tiene que confirmar.

```
  columna   clave_normalizada                              formas
  entidad           FULLCARGA    Fullcarga (1579) | FULLCARGA (36)
direccion  AVENIDA AMERICO...   AV. AMÉRICO VESPUCIO 1737 (1) | AV. AMERICO ... (1)
```

Cada fila es la afirmación «estos dos textos distintos nombran la misma cosa». Son
pocas y se leen en un minuto.

**La sorpresa habitual: normalizar fusiona mucho menos de lo que se teme.** En un
archivo público real de 1 928 filas:

| Columna | Valores crudos | Normalizados | Fusiones |
| --- | --- | --- | --- |
| `comuna` | 46 | 46 | **0** |
| `entidad` | 4 | 3 | 1 |
| `direccion` | 1 919 | 1 914 | 5 |

Seis fusiones en todo el archivo, las seis correctas: mayúsculas, tildes, un apóstrofo
escrito como acento grave y un espacio doble.

Eso no vuelve inútil normalizar —sin ello `Fullcarga` y `FULLCARGA` serían dos
entidades, y el grupo grande se partiría en 1 579 y 36— pero sí recomienda **medir antes
de suponer**. El riesgo de no normalizar es concreto y pequeño; el de normalizar de más
es silencioso.

**El componente que hay que vigilar: la expansión de abreviaturas.** Es la única
transformación que puede juntar cosas genuinamente distintas, porque reemplaza por
significado y no por forma. En el mismo archivo, sobre las 1 919 direcciones, la
expansión de trece abreviaturas declaradas **no fusionó ni una**: las cinco fusiones las
produjo el resto de la normalización.

Que una capacidad exista y esté probada no significa que aporte algo sobre los datos
que uno tiene. Medirlo aparte evita atribuirle un mérito que no tiene:

```python
sin_expandir = columna.map(normalize_key)
con_expandir = columna.map(lambda v: normalize_key(v, expand_abbreviations=True))
aporte = sin_expandir.nunique() - con_expandir.nunique()    # 0 en ese archivo
```

**Lo que nunca hay que hacer.** Fusionar por **parecido** sin revisión humana. Una
similitud de 0,9 entre dos nombres es una hipótesis, no un hecho:
`lab.textual.duplicate_candidates` propone pares y **no fusiona nada**, que es la
división de trabajo correcta.

**Regla corta.** Toda regla de normalización es una afirmación sobre qué cosas son la
misma. Las afirmaciones se publican y se revisan, no se aplican en silencio.
