---
id: clave-falla-al-volver
tipo: error
titulo: Una clave que no es única no falla al cruzar: falla al volver, y a veces no falla
etiquetas: [calidad-datos, cruce-consolidacion, errores-frecuentes, pandas, datos-reales]
fuente: cases/cobertura_de_carga/solution.py
relacionados: [clave-que-no-es-clave, cruce-sin-clave, defecto-que-no-existe]
---

**El caso.** Una búsqueda del punto más cercano devuelve, para cada parada, el lugar de
carga que le queda más próximo. ¿Cómo se identifica ese lugar? La columna `codigo`
parece lo natural.

**Lo que pasó, en dos actos.**

*Acto uno, el error ruidoso.* Al unir el resultado con la tabla de lugares:

```
pandas.errors.InvalidIndexError: Reindexing only valid with uniquely valued Index objects
```

Molesto, y bienvenido: 143 estaciones de Metro comparten siete códigos, porque allí el
código es la línea. El error aparece **al volver** —al usar el identificador para
recuperar los atributos— y no al calcular. Ver [[clave-que-no-es-clave]].

*Acto dos, el error silencioso.* Peor. Antes de ese fallo, una comparación entre dos
métodos de cálculo había contado cuántas paradas cambiaban de lugar más cercano:

| Comparación | Contando por código | Contando por posición |
| --- | --- | --- |
| Haversine contra euclídea | 807 | **814** |
| Coordenada publicada contra la derivada de UTM | 1 657 | **1 673** |

Dos estaciones distintas de la misma línea se contaban como la misma, de modo que un
cambio real de local pasaba por «no cambió». El resultado no explotó: **devolvió un
número un poco menor**, en la dirección que hacía ver más estable el método.

**Por qué este modo de falla es el peligroso.** Una clave repetida da tres resultados
distintos según qué se haga con ella:

| Operación | Qué pasa | ¿Se nota? |
| --- | --- | --- |
| `merge` o `join` | multiplica filas | A veces, si se mira el conteo |
| `map` o `reindex` | levanta excepción | Sí, es ruidoso |
| **comparar dos listas de claves** | **colapsa diferencias reales** | **No** |

La tercera es la que no avisa, porque comparar claves iguales es una operación
perfectamente válida: solo que las claves no identifican lo que uno cree.

**Qué hacer.** Cuando una función devuelve «el elemento que corresponde», que devuelva
la **posición de fila** y no un campo del dato. La posición es única por construcción.
Después se traducen los atributos con un `map` sobre el índice, que no puede colisionar.

```python
# nearest_point sin id_destino devuelve el índice del destino
cercano = nearest_point(origen, destino)
salida["nombre"] = cercano["destino_mas_cercano"].map(destino["nombre"])
```

**La prueba que lo deja fijo.** Dos registros distintos con el mismo código, y la
afirmación de que se distinguen. Sin esa prueba el defecto vuelve en cuanto alguien
«simplifique» la función para devolver algo legible.

**Regla general.** Un identificador legible es cómodo para leer y malo para computar.
Computar con la posición, mostrar el código.
