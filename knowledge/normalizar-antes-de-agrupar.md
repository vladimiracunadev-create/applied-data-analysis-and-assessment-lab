---
id: normalizar-antes-de-agrupar
tipo: patron
titulo: Normalizar para agrupar y conservar la etiqueta para informar
etiquetas: [limpieza-normalizacion, cruce-consolidacion, pandas, datos-reales, comunicacion-resultados]
fuente: lab/textual.py, cases/bip_lugares_carga/solution.py
relacionados: [clave-que-no-es-clave, encabezado-no-esta-en-la-primera-fila, cruce-con-cardinalidad]
---

**El problema.** `FULLCARGA` y `Fullcarga` son **dos grupos** para `groupby` y **uno**
para una persona. En un archivo público real aparecen las dos formas, y agrupar sobre
el texto crudo da un informe con dos filas donde hay una entidad.

Tres variantes del mismo problema, todas verificadas en el mismo conjunto de archivos:

| Variante | Ejemplo real | Qué rompe |
| --- | --- | --- |
| Mayúsculas inconsistentes | `FULLCARGA` / `Fullcarga` | grupos duplicados |
| Tildes | `CONCHALI` vs `Conchalí` de otra fuente | el cruce no empareja |
| Espacio al final | `NOMBRE DE FANTASIA ` | la columna «no existe» |

Ninguna de las tres produce un error. Las tres producen un resultado equivocado.

**La solución, y su matiz importante.** Hay que normalizar, pero **no** hay que
guardar solo la forma normalizada:

```python
df["comuna_clave"]     = normalize_series(df["comuna"])      # para agrupar
df["comuna_etiqueta"]  = df["comuna"].map(normalize_label)   # para mostrar
```

Si solo se guarda la clave, el informe final dice `NUNOA` en lugar de `Ñuñoa`. Es un
empobrecimiento gratuito: la clave sirve para que la máquina agrupe, la etiqueta para
que una persona lea. Se conservan las dos y se agrupa por una mostrando la otra.

**La misma regla en los dos lados del cruce.** Dos normalizaciones parecidas aplicadas
a cada lado producen un cruce que falla justo en los casos límite, que son los que
importan. Por eso la función vive en el núcleo y no se reescribe en cada caso.

**Cuantificar lo que se gana.** El argumento para normalizar es un número, no una
opinión:

```python
distintos_antes   = serie.nunique()
distintos_despues = normalize_series(serie).nunique()
grupos_espurios   = distintos_antes - distintos_despues
```

Esa diferencia es exactamente el número de grupos falsos que `groupby` habría creado.
`lab.textual.normalization_report` la entrega como tabla.

**Qué no es normalizar.** No es deduplicar. Normalizar hace comparables dos textos;
decidir que dos **registros** son la misma entidad es una decisión con criterio
declarado. `lab.textual.duplicate_candidates` propone pares por parecido, y el umbral
es una heurística: alguien tiene que firmar la fusión.

**Dónde más aparece.** Nombres de clientes, razones sociales, proveedores, localidades,
códigos escritos a mano. Es el primer paso de cualquier deduplicación en banca,
seguros, retail o salud, y el motivo por el que `lab.textual` no sabe nada de
transporte.
