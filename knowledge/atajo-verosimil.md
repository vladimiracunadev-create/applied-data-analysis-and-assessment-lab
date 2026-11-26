---
id: atajo-verosimil
tipo: leccion
titulo: El atajo peligroso no es el que da una cifra absurda, es el que da una cifra verosímil
etiquetas: [errores-frecuentes, pensamiento-critico, calidad-datos, gtfs, fechas-horarios]
fuente: cases/carga_nocturna/solution.py
relacionados: [horario-relativo-vs-absoluto, unidad-de-la-decision, defecto-que-no-existe, sesgo-con-eje]
---

**El caso.** Hay que contar cuántas paradas tienen servicio de bus entre las 00:00 y
las 05:00. El atajo evidente:

```python
noche = stop_times[stop_times["arrival_time"].between("00:00:00", "04:59:59")]
paradas = noche["stop_id"].nunique()     # 12 201
```

El valor correcto es **10 520**. El atajo sobreestima un **16 %**.

**Por qué el 16 % es el problema.** Si el atajo hubiera devuelto 120 000 paradas en una
red de 12 497, alguien lo habría visto en un segundo. Si hubiera devuelto 3, también.
Devolvió 12 201, que es:

- del orden de magnitud correcto;
- menor que el total de paradas de la red, de modo que no es imposible;
- consistente con la intuición de que la red nocturna cubre buena parte de la ciudad.

No hay nada en el resultado que grite. Y el cálculo que lo produjo **no estaba midiendo
horas en absoluto**: el 100 % de las 851 773 filas que tomó son de expediciones de
frecuencia, cuyo `arrival_time` es un desplazamiento desde el inicio del viaje y no una
hora de reloj. Ver [[horario-relativo-vs-absoluto]].

**La forma del error.** Un atajo equivocado que produce una cifra verosímil suele tener
esta estructura: está midiendo **otra cosa** que correlaciona con la correcta. Aquí, los
desplazamientos de las expediciones de frecuencia se concentran en las primeras horas
de un viaje, de modo que «parada que aparece con desplazamiento bajo» correlaciona con
«parada con mucho servicio», y «parada con mucho servicio» correlaciona con «parada con
servicio nocturno». La correlación hace el trabajo de parecer correcto.

**Cómo se detecta, en orden de costo.**

1. **Preguntar qué tiene que ser verdad para que el cálculo signifique lo que se cree.**
   Aquí: que `arrival_time` sea una hora. Comprobarlo cuesta una línea: `¿cuántas de
   las filas que tomo vienen de expediciones con frecuencia declarada?`. La respuesta
   fue 100 %.
2. **Mirar el rango del campo antes de filtrarlo.** Los desplazamientos iban de 0 a
   3,30 h y las horas absolutas de 5,17 a 23,79 h: dos poblaciones que no se solapan,
   visibles en un `describe` agrupado.
3. **Implementar los dos métodos y comparar.** Es lo que hace el caso, y por eso la
   magnitud del error está medida en lugar de argumentada.

**El patrón que sí protege.** Dejar el atajo en el código, al lado del cálculo correcto,
y publicar la comparación:

```
paradas_segun_el_atajo    12 201
     paradas_correctas    10 520
       sobreestimacion     15,98 %
```

Cuesta unas líneas y hace dos cosas: justifica por qué el código correcto es más
complicado de lo que parece necesario, y deja una prueba que falla si alguien «lo
simplifica» más adelante.

**La regla general.** Una cifra verosímil no es evidencia de nada. La verosimilitud es
una propiedad del lector, no del cálculo.
