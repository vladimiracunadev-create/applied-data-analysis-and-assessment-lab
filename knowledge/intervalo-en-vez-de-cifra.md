---
id: intervalo-en-vez-de-cifra
tipo: patron
titulo: Cuando el denominador tiene huecos, el indicador es un intervalo y su ancho es otro indicador
etiquetas: [indicadores, incertidumbre, comunicacion-resultados, gobernanza-datos, denominadores]
fuente: cases/carga_nocturna/solution.py
relacionados: [tres-respuestas-no-dos, vacio-concentrado, denominador-es-una-decision, supuesto-medido]
---

**El problema.** Un indicador con datos faltantes se publica de una de tres maneras, y
dos son malas.

| Forma de publicarlo | Qué hace con los huecos | Problema |
| --- | --- | --- |
| Un número con nota al pie | los esconde | nadie lee la nota; el número viaja solo |
| Un número sobre los casos conocidos | cambia el denominador en silencio | mide otra población y no lo dice |
| **Un intervalo** | los pone en el ancho | ninguno |

**El patrón.** Dos cifras y una tercera que las resume:

- **el piso**, que es lo verificado: el indicador contando como favorables solo los
  casos comprobados;
- **el techo**, suponiendo que **todos** los casos desconocidos sean favorables;
- **el ancho**, que mide cuánto de la pregunta sigue abierto.

```
cobertura_minima_pct     0,00   %
cobertura_maxima_pct    52,62   %
ancho_del_intervalo_pp  52,62   puntos
```

**Por qué el ancho es un indicador y no una disculpa.** Porque tiene un dueño y una
acción. 52,6 puntos de ancho no los produce la red ni la geografía: los produce una
columna vacía, y se sabe cuál, de quién es y cuántos registros hay que completar. El
ancho convierte «faltan datos» en una cifra que se puede llevar a una reunión.

Y porque se mueve. Si el publicador completa los registros, el ancho baja; si el
indicador se recalcula el mes siguiente y el ancho creció, eso es una señal de
gobernanza que ningún número único habría dado.

**El techo es deliberadamente absurdo, y así tiene que ser.** Suponer que los 1 579
locales sin horario abren de madrugada es falso casi con certeza: ninguno de los 348
que sí declaran lo hace. Pero es la cota que el dato permite, y rebajarla con una
estimación plausible —«supongamos que se comportan como los conocidos»— convierte el
intervalo en un pronóstico y pierde justamente la propiedad que lo hace útil: que la
respuesta real está dentro, con certeza.

Si hace falta una estimación central, va **aparte**, con su supuesto declarado. Ver
[[supuesto-medido]].

**Cuándo no usarlo.** Cuando el ancho es trivial. Si el piso y el techo difieren en dos
décimas, publicar el intervalo es ruido: se publica el número y se menciona el hueco.
El patrón gana cuando el ancho es grande, que es precisamente cuando un número único
sería más engañoso.

**La prueba que lo mantiene honesto.** El ancho tiene que ser **cero** cuando no falta
ningún dato. Si no lo es, hay una indeterminación que el cálculo está inventando.
