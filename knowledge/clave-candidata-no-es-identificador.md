---
id: clave-candidata-no-es-identificador
tipo: concepto
titulo: Una combinación única en los datos de hoy no es un identificador
etiquetas: [calidad-datos, cruce-consolidacion, gobernanza-datos, pensamiento-critico, errores-frecuentes]
fuente: lab/keys.py
relacionados: [clave-que-no-es-clave, clave-falla-al-volver, grano-antes-de-cruzar, que-fuente-provee-el-campo]
---

**Las tres cosas que se confunden.**

1. **Una columna sin repetidos** no es clave si admite nulos: dos filas con el valor
   ausente no se distinguen entre sí.
2. **Una clave candidata** es un conjunto de columnas sin nulos y sin repetidos. Puede
   haber varias; las interesantes son las **mínimas**, las que dejan de ser únicas si se
   les quita cualquier columna.
3. **Una clave candidata no es necesariamente un identificador.** Que una combinación
   resulte única hoy depende de los datos de hoy. Que sirva de identificador depende de
   si sus campos son **estables**.

La tercera es la que casi nunca se piensa, y es la que decide si el cruce sobrevive a la
siguiente publicación.

**El caso.** Un archivo público de 1 928 lugares. Ninguna columna sola es clave. La
búsqueda exhaustiva devuelve tres claves candidatas mínimas, todas de dos columnas:

| Clave candidata | ¿Única hoy? | ¿Sirve de identificador? |
| --- | --- | --- |
| `codigo + direccion` | sí | **no**: `direccion` es texto libre |
| `codigo + este` | sí | **no**: `este` es una coordenada medida |
| `codigo + norte` | sí | **no**: igual que `este` |

La más instructiva es `codigo + este`. Es perfectamente única. Y otro caso del mismo
laboratorio demostró que varias coordenadas de ese archivo están equivocadas por
kilómetros. El día en que el publicador las corrija, esas filas **cambiarán de
identidad** y aparecerán como lugares nuevos.

> Una clave que cambia cuando se corrige un error no es una clave: es un número de serie
> del error.

Lo mismo, más suave, con `direccion`: una tilde añadida o un espacio de más cambian la
identidad de la fila.

**Qué preguntarle a una clave candidata antes de usarla.**

- **¿El campo se mide o se declara?** Un valor medido —coordenada, peso, lectura de
  sensor— se vuelve a medir.
- **¿El campo se corrige?** Un texto escrito a mano se corrige, y cada corrección es un
  cambio de identidad.
- **¿El campo se deriva de otro?** Entonces hereda su inestabilidad.
- **¿La fuente lo trata como identificador?** Si no lo trata así, no se compromete a
  mantenerlo.

**La salida cuando ninguna sirve: una clave subrogada.** Un identificador determinista
derivado de los campos que **se declaran** como identidad:

```python
from lab.keys import surrogate_key
ids = surrogate_key(frame, ["fuente", "codigo", "direccion"], prefix="bip-")
```

Tres propiedades y una limitación que hay que decir:

- **determinista**: el mismo contenido da el mismo identificador en cualquier máquina y
  ejecución, a diferencia de un número de fila;
- **verifica sus colisiones**: si dos filas con contenido distinto producen el mismo
  identificador, falla en lugar de devolver duplicados;
- **declara la identidad**: la lista de campos queda escrita, que es lo que el archivo
  no hacía;
- **hereda la inestabilidad de sus campos**. Si uno cambia entre publicaciones, el
  identificador cambia. No hay forma de evitarlo sin un identificador provisto por la
  fuente, y **pedirlo es lo que corresponde**.

**La comprobación, que cuesta una llamada.**

```python
from lab.keys import key_report, candidate_keys
key_report(frame)        # por columna: nulos, repetidos, y por qué no es clave
candidate_keys(frame)    # las combinaciones mínimas que sí identifican
```

Que la segunda devuelva una tabla vacía es un resultado y no un fallo: significa que hay
que construir la identidad en lugar de encontrarla.
