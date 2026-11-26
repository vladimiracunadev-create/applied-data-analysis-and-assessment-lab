---
id: tres-respuestas-no-dos
tipo: patron
titulo: Un indicador construido sobre datos incompletos necesita tres respuestas, no dos
etiquetas: [calidad-datos, gobernanza-datos, indicadores, incertidumbre, comunicacion-resultados]
fuente: lab/schedules.py
relacionados: [intervalo-en-vez-de-cifra, vacio-concentrado, cambiar-la-pregunta, denominador-es-una-decision]
---

**El caso.** Hay que decir si cada parada con servicio de madrugada tiene un lugar de
carga abierto cerca. De los 1 927 locales, 348 declaran horario y 1 579 no declaran
nada.

Con dos respuestas, los 1 579 silencios hay que ponerlos en algún lado, y el lado
cómodo es «cerrado»: da una tabla completa, un porcentaje redondo y un titular. También
afirma que 1 579 locales cierran de madrugada sin que nadie lo haya dicho.

**La regla.** Lo que no se sabe se propaga como **no se sabe**.

```python
def is_open(horario, dia, segundo) -> bool | None:
    if not horario.parsed:
        return None          # NO False
    tramos = horario.intervals.get(dia)
    if not tramos:
        return None          # el texto no habla de ese día
    return any(i <= segundo < f for i, f in tramos)
```

El tipo de retorno es la documentación: `bool | None`, y el `None` tiene que llegar
hasta el informe.

**Cómo se ve en el resultado.** Cuatro clases excluyentes, con una columna que dice
cuáles permiten afirmar algo:

| Situación | Paradas | ¿Permite afirmar? |
| --- | --- | --- |
| Con cobertura verificada | 0 | sí |
| Sin nada cerca | 4 225 | sí |
| Cerca y cerrado, verificado | 759 | sí |
| **Indeterminado** | **5 536** | **no** |

Fundir las dos últimas daría «59,8 % sin cobertura verificada». Suena a medición. Es
una invención, y de las peores: la que se construye con datos reales.

**La asimetría que hay que respetar.** Las tres clases afirmables no son equivalentes
entre sí. «Sin nada cerca» es la conclusión más firme de todas, porque **no depende de
ningún horario**: ningún dato futuro la cambia. Conviene separarla, porque es la parte
del resultado sobre la que se puede actuar hoy.

**Dónde más aparece.** Cumplimiento de requisitos cuando falta un certificado;
elegibilidad de beneficiarios con un campo sin llenar; conformidad de proveedores sin
respuesta a una encuesta; cobertura de pruebas en un archivo que no se puede analizar.
En todos, la tentación es la misma y tiene la misma forma: el silencio se interpreta
como la respuesta que conviene al relato.

**La regla corta.** Un booleano es un tipo pobre para un dato que puede faltar. Si el
dato puede faltar, el tipo tiene tres valores, y los tres tienen que llegar al informe.
Ver [[intervalo-en-vez-de-cifra]] para cómo se publica después.
