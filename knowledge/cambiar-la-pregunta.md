---
id: cambiar-la-pregunta
tipo: leccion
titulo: Cuando el dato no está, a veces lo honesto es cambiar la pregunta y no el dato
etiquetas: [pensamiento-critico, gobernanza-datos, comunicacion-resultados, metodologia, incertidumbre]
fuente: cases/cobertura_de_carga/solution.py
relacionados: [supuesto-medido, denominador-es-una-decision, cruce-sin-clave, defecto-que-no-existe]
---

**El caso.** La pregunta era doble: «¿qué proporción de las paradas tiene un lugar de
carga cerca, y **qué comunas quedan peor**?». La primera mitad se contestó. La segunda
no se puede: las paradas del feed GTFS no traen comuna, y no hay capa de límites
administrativos con licencia verificable en el entorno.

**Las tres salidas, y por qué dos son malas.**

*Inventar el dato.* Atribuir a cada parada la comuna de su lugar de carga más cercano.
Produce una tabla completa y con aspecto normal, y está sesgada **por construcción**: a
la parada sin cobertura se le asigna la comuna del local lejano, que es justamente la
comuna equivocada. El sesgo es peor donde el indicador sería más interesante.

Medido, el artefacto se ve:

| Comuna atribuida | Paradas | Mediana | Cobertura |
| --- | --- | --- | --- |
| Paine | 5 | **18 924 m** | 0,0 % |
| Calera de Tango | 4 | 2 565 m | 0,0 % |
| Padre Hurtado | 47 | 541 m | 23,4 % |

Paine no tiene mala cobertura: tiene un local que quedó siendo el más cercano de unas
paradas que están a diecinueve kilómetros. Publicada sin esa medición, la fila dice
algo falso sobre una comuna real.

*No contestar nada.* Correcto y estéril. La necesidad detrás de la pregunta —saber
dónde está el problema— sigue sin respuesta, y quien preguntó va a estimarla peor por
su cuenta.

*Cambiar la unidad de análisis.* Una rejilla de 0,01° derivada de las propias
coordenadas. No necesita ninguna fuente nueva, no finge precisión administrativa, y
contesta la necesidad real: cuatro celdas con veinte o más paradas y **cero** cobertura
a 300 m, cada una identificada por el nombre de su parada más lejana para que se
reconozca sin un mapa.

**Lo que hay que declarar al cambiar la pregunta.** El sustituto tiene costos, y
callarlos lo convierte en el primer camino con otro nombre:

- una celda **no es una unidad con la que nadie gobierne**: localiza zonas, no asigna
  responsabilidades;
- la celda no es cuadrada —1,11 km de norte a sur, 0,93 de este a oeste—, de modo que no
  sirve para medir superficies ni densidades;
- el tamaño de celda es una decisión más, y hay que decir cuál se eligió.

**El patrón, en tres pasos.**

1. **Medir por qué el camino evidente no sirve**, y publicar esa medición. Un «no se
   puede» respaldado por una tabla es un resultado; sin tabla es una opinión.
2. **Ofrecer el sustituto más cercano a la necesidad**, no a la pregunta literal.
3. **Nombrar lo que el sustituto pierde**, en el mismo lugar donde se publica.

**Lo que no es este patrón.** No es rebajar el alcance para evitar trabajo. Si el dato
se puede conseguir, se consigue: aquí no se consiguió porque habría significado
incorporar una fuente cartográfica nueva, verificar su licencia y añadir una dependencia
geoespacial, para una mitad de pregunta. Esa frontera se declara y queda disponible
para que alguien la cruce después. Ver [[supuesto-medido]] para el caso en que el dato
que falta sí se puede suplir con un supuesto y medir su efecto.
