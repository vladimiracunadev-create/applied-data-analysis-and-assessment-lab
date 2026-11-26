---
id: punto-ciego-del-control
tipo: leccion
titulo: Toda comprobación de calidad tiene un punto ciego, y el punto ciego es medible
etiquetas: [calidad-datos, gobernanza-datos, validacion-independiente, pensamiento-critico, errores-frecuentes]
fuente: cases/correspondencia_metro/solution.py
relacionados: [dos-coordenadas-un-lugar, dos-afirmaciones-de-la-misma-fila, defecto-que-no-existe, vacio-concentrado]
---

**El caso.** Un archivo público de lugares trae la misma ubicación dos veces, en UTM y
en latitud/longitud. Comparar las dos representaciones es una validación elegante: no
necesita ninguna fuente externa y encontró **tres errores en 1 928 filas**.

Después, otro caso comparó el mismo archivo contra un feed GTFS independiente. **Once
estaciones de Metro** estaban a más de 500 m de donde la otra fuente las pone, hasta
13 km. **Ninguna** había quedado marcada por la validación anterior.

No porque estuviera mal escrita. Porque un error que afecta a las **dos**
representaciones por igual es invisible para una comprobación que las compara entre sí.

**La anatomía.** Una comprobación encuentra la clase de error que su comparación puede
revelar, y es ciega a todo lo demás. En este archivo:

| Comprobación | Compara | ¿Fuente externa? | Ciega a |
| --- | --- | --- | --- |
| Dos representaciones de una fila | UTM contra lat/lon | no | un error que afecte a las dos por igual |
| Filas hermanas de una entidad | fila contra fila | no | la entidad que tiene una sola fila |
| Coordenada contra unidad declarada | fila contra sus pares | no | un error dentro de la propia unidad |
| Contra otra fuente | archivo contra archivo | **sí** | un error que las dos fuentes compartan |

Cada punto ciego tiene el tamaño exacto de lo que encuentra la comprobación siguiente. Y
la última también tiene el suyo: dos fuentes que copian del mismo origen se equivocan
juntas.

**Las dos conclusiones prácticas.**

*Primera: antes de confiar en un informe de calidad, preguntarle qué no mira.* Un
informe que dice «3 errores en 1 928 filas» está diciendo «3 errores de esta clase»,
y casi nunca lo dice así. La cobertura de los controles es tan auditable como los datos.

*Segunda, y menos obvia: antes de pedir otra fuente, preguntarle al archivo si se
contradice consigo mismo.* De los cuatro detectores de arriba, **tres no necesitan nada
externo**:

- dos filas que nombran la misma entidad deben describir el mismo lugar;
- una coordenada debe ser compatible con la comuna que la propia fila declara;
- una dirección postal y una coordenada son dos afirmaciones independientes.

El archivo podía delatar sus propios errores y nadie le hizo esas preguntas. Conseguir
una segunda fuente cuesta negociación, licencia y mantenimiento; estas tres
comprobaciones cuestan veinte líneas.

**Cómo se publica.** Una tabla de detectores con una columna `ciego_a`, al lado de la de
hallazgos. Obliga a escribir la limitación en el momento de escribir el control, que es
el único momento en que se tiene presente.

**Regla corta.** «Validado» no es una propiedad de un dato: es una propiedad de un dato
**respecto de una comprobación**. Siempre hay que nombrar cuál.
