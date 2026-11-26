---
id: cruce-sin-clave
tipo: metodologia
titulo: Cuando no hay clave compartida, el criterio de emparejamiento es la mitad del resultado
etiquetas: [cruce-consolidacion, metodologia, geoespacial, pensamiento-critico, datos-reales]
fuente: cases/cobertura_de_carga/solution.py
relacionados: [clave-que-no-es-clave, clave-falla-al-volver, sesgo-con-eje, denominador-es-una-decision, unidad-de-la-decision]
---

**El caso.** Dos fuentes públicas describen cosas del mismo territorio: 12 497 paradas
de transporte en un feed GTFS y 1 927 lugares de carga de tarjeta en cinco planillas.
No comparten **ningún** campo: ni identificador, ni dirección, ni comuna. La pregunta
—«¿a qué distancia está el lugar de carga más cercano de cada parada?»— no se puede
contestar con un `JOIN`, porque no hay sobre qué unir.

**Lo que cambia respecto de un cruce normal.** En un cruce con clave, el criterio está
dado y el trabajo es de calidad: comprobar cardinalidad, nulos, huérfanos. Sin clave,
**el criterio hay que inventarlo**, y cada decisión del criterio es una decisión
metodológica que entra en el resultado sin dejar rastro.

En este caso la proximidad geométrica trajo cuatro decisiones:

| Decisión | Alternativas | Efecto medido en la respuesta |
| --- | --- | --- |
| Fórmula de distancia | haversine / euclídea sobre grados | 59,29 % → 54,69 % |
| Representación de la coordenada | publicada / derivada de UTM | 59,29 % → 59,17 %, pero 1 673 paradas cambian de local |
| Línea recta o caminata | factor de rodeo de 1,0 a 1,5 | 59,29 % → 39,60 % |
| Qué entra al denominador | con o sin las paradas a más de 3 km | 59,29 % → 59,58 % |

La respuesta plausible va del 39 % al 81 % sin que ningún dato cambie.

**La trampa.** Ninguna de las cuatro decisiones es incorrecta. Todas son defendibles, y
por eso el resultado parece sólido cualquiera sea la combinación elegida. Un indicador
producido por un cruce sin clave **no se puede auditar mirando el número**: hay que ver
el criterio.

**Qué hacer.**

1. **Nombrar el criterio** como constantes del código, y no dejarlo implícito en una
   llamada de función.
2. **Informar la sensibilidad de cada decisión**, no solo el valor elegido. Una curva
   en lugar de una cifra.
3. **Separar qué propiedad es robusta de cuál no.** Aquí el agregado aguanta el cambio
   de coordenada y la asignación individual no: son dos resultados distintos, y
   habilitan usos distintos.
4. **Declarar la decisión que no se pudo tomar con fundamento.** Para el factor de
   rodeo no se encontró un valor peatonal canónico, de modo que no se eligió ninguno.

**Dónde más aparece.** Sucursales y clientes, antenas y reclamos, bodegas y pedidos,
estaciones de medición y parcelas, transacciones y comercios por razón social. También
en cruces no geométricos: emparejar por nombre con similitud de cadenas es exactamente
el mismo problema, y peor, porque un acierto por casualidad no se distingue de un
acierto legítimo. Ver [[normalizar-antes-de-agrupar]].
