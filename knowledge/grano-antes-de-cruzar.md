---
id: grano-antes-de-cruzar
tipo: patron
titulo: Antes de cruzar dos inventarios, nombrar el grano de cada uno y cerrar la identidad
etiquetas: [cruce-consolidacion, calidad-datos, metodologia, datos-reales, gobernanza-datos]
fuente: cases/correspondencia_metro/solution.py
relacionados: [clave-que-no-es-clave, cruce-sin-clave, agregado-que-suaviza, cruce-con-cardinalidad]
---

**El caso.** Dos archivos públicos describen las estaciones de Metro de Santiago. Uno
trae **126 filas** y el otro **143**. La reacción habitual es tratar la diferencia como
un problema de completitud y «arreglarla» descartando lo que no cruza, que es la forma
más eficaz de perder precisamente las estaciones de combinación.

No falta nada. Son **granos distintos**:

| Fuente | Grano | Cómo lo delata |
| --- | --- | --- |
| Feed GTFS | una fila por **estación** | las 17 combinaciones llevan un identificador compuesto: `AN-NA`, `BA-BQ` |
| Excel | una fila por **estación y línea** | sus 34 filas de combinación llevan la línea pegada al **nombre**: `SAN PABLO L1` |

**La identidad que hay que cerrar.** No basta con decir «el grano es distinto»: hay que
escribir la cuenta y comprobar que da.

```
126 estaciones − 17 combinaciones + 34 filas de desdoble = 143 filas
```

En general, para conciliar A con B:

```
filas(A) − casos que A fusiona + filas que B desdobla = filas(B)
```

Si la cuenta no cierra, falta entender algo, y es mejor saberlo antes del cruce que
después del informe.

**Dónde buscar la pista del grano.** Casi nunca está documentado, y casi siempre está
en un campo que no es el pensado para eso:

- **un identificador compuesto** —un guion, un prefijo, una concatenación— delata una
  fusión de entidades;
- **un sufijo en un campo de texto libre** delata un desdoble, y aparece cuando el
  campo que debería distinguir no distingue. Aquí la línea va pegada al nombre porque el
  campo `codigo` vale la línea y no identifica nada. Ver [[clave-que-no-es-clave]];
- **un recuento que no cuadra con el número de entidades que uno cree que hay.**

**El orden de las operaciones.** Reducir el grano del más fino al más grueso, y hacerlo
con una regla **declarada**. Aquí, quitar el sufijo de línea con un patrón escrito:

```python
SUFIJO_DE_LINEA = re.compile(r"\s+L\d+A?$")
```

Declarado y no deducido por parecido, porque una entidad que legítimamente termine en
algo similar quedaría mutilada en silencio. Y a una columna nueva, conservando el
original: perder el dato de origen para quedarse con el derivado impide auditar la
transformación.

**La comprobación que cierra el paso.** Tras reducir, el número de entidades distintas
tiene que coincidir con el de la otra fuente. Aquí: 126 y 126. Si no coincide, la regla
de reducción está mal y conviene descubrirlo ahí.

**Dónde más aparece.** Sucursales y centros de costo, productos y SKU, personas y
contratos, cuentas y titulares, pacientes y episodios, vehículos y patentes. En todos,
el error es el mismo: cruzar dos tablas que cuentan cosas distintas y leer la diferencia
como un problema de calidad.
