---
id: supuesto-medido
tipo: metodologia
titulo: Un supuesto que no se puede resolver se mide
etiquetas: [metodologia, incertidumbre, comunicacion-resultados, gobernanza-datos, datos-reales]
fuente: cases/calendario_medicion/solution.py
relacionados: [denominador-es-una-decision, regla-redundante, hecho-inferencia-hipotesis, cobertura-de-un-indicador]
---

**La situación.** Una metodología publicada dice «**vacaciones de invierno (dos
semanas, considerando los calendarios escolares)**» y no da fechas. El calendario
escolar cambia cada año y no se consiguió.

Hay tres salidas, y solo una es defendible.

| Salida | Qué pasa |
| --- | --- |
| Elegir fechas y no decirlo | El resultado depende de una decisión invisible. Si alguien la cuestiona, no hay respuesta |
| Declarar que no se puede calcular | Honesto y estéril: no hay entregable |
| **Declarar el supuesto y medir su efecto** | Convierte una incertidumbre en un riesgo acotado y nombrado |

### Cómo se mide

Se recalcula el resultado desplazando el supuesto, y se reporta la tabla:

| Inicio supuesto | Desplazamiento | Días medibles | Diferencia |
| --- | --- | --- | --- |
| 2026-06-22 | −14 días | **72** | **−6** |
| 2026-06-29 | −7 días | 77 | −1 |
| **2026-07-06** | **0 (supuesto)** | **78** | **0** |
| 2026-07-13 | +7 días | 78 | 0 |
| 2026-07-20 | +14 días | 78 | 0 |

### Lo que la tabla permite decir

No «supongo que las vacaciones empiezan el primer lunes de julio», sino algo mucho más
útil:

> **El supuesto solo importa si el receso de invierno empieza antes del 1 de julio.**
> Mientras caiga dentro de julio, moverlo dos semanas en cualquier dirección no cambia
> el denominador. Si empezara en la segunda mitad de junio —que sí es mes de medición—
> el denominador bajaría de 78 a 72 días, un 7,7 %.

Eso es un riesgo **acotado** y **nombrado**: queda claro qué habría que averiguar, en
qué condición, y cuánto cambiaría el resultado si se averiguara.

### La regla general

Ante un supuesto que no se puede resolver:

1. **Declararlo** donde se vea, no en un comentario del código.
2. **Parametrizarlo**, de modo que se pueda cambiar sin reescribir nada.
3. **Medir su efecto** sobre el resultado final, no sobre un intermedio.
4. **Escribir la condición** bajo la cual el supuesto deja de ser inofensivo.
5. **Decir qué habría que conseguir** para eliminarlo.

Los pasos 3 y 4 son los que distinguen un informe que se sostiene de uno que solo
confiesa.

### Por qué importa el paso 3

Un supuesto declarado sin medir sigue siendo una incógnita: quien lee no sabe si da
igual o si lo cambia todo. Medir cuesta, en este caso, cinco ejecuciones del mismo
cálculo. Es el análisis de sensibilidad más barato que existe y casi nunca se hace.

### Dónde más aparece

Cualquier parámetro que el dato no entrega: una tasa de ocupación supuesta, un tipo de
cambio de una fecha dudosa, el umbral de un criterio de clasificación, la antigüedad a
partir de la cual un registro se considera inactivo, el método de interpolación de un
percentil. En todos, la pregunta es la misma: **¿cuánto cambia la respuesta si me
equivoqué en esto?**

Y conviene notar que la misma metodología de este caso declara otro supuesto sin
medirlo: la tasa de ocupación de los vehículos particulares proviene de una encuesta de
**2012** y se usa en un indicador de 2019. Está declarado, que es lo correcto. Medir
cuánto cambiaría el índice con otra tasa habría sido mejor.
