---
id: denominador-es-una-decision
tipo: metodologia
titulo: El denominador de un indicador oficial es una decisión, no un dato
etiquetas: [indicadores, gobernanza-datos, denominadores, metodologia, datos-reales]
fuente: cases/calendario_medicion/solution.py, docs/indicadores-oficiales-transporte.md
relacionados: [regla-redundante, supuesto-medido, cobertura-de-un-indicador, denominador-cero]
---

**El hecho.** El índice de variación de tiempos de viaje del transporte público de
Santiago tiene una fórmula de dos líneas y **ocho reglas de exclusión** en su nota al
pie. La fórmula no dice nada sobre qué días entran; la nota lo dice todo.

Textual, de un documento público de DIPRES:

> «se consideran sólo días laborales, descartando los siguientes casos: Días feriados;
> Todos los días de los meses de enero, febrero y diciembre; Vacaciones de invierno
> (dos semanas, considerando los calendarios escolares); Semana de fiestas patrias;
> 11 de septiembre; Día del joven combatiente. Dado que en algunas ocasiones los
> incidentes inician en la tarde del día anterior, **se descartan todos los datos de
> los días 28 y 29**.»

Siete reglas, más «solo días laborales». Y una de ellas —descartar los días 28 y 29 de
cada mes— no la adivina nadie.

**El efecto, medido sobre 2026:**

| | Días |
| --- | --- |
| Días del año | 365 |
| Días laborales | 261 |
| **Elegibles tras las ocho reglas** | **164** (62,84 % de los laborales) |
| **Medibles**, cruzando con los meses en que se mide | **78** |

De 365 días quedan 78. **El 21 %.** Y ese 21 % es el denominador del indicador.

### Las tres consecuencias prácticas

**1. Un indicador no se puede reproducir sin su metodología.** Dos analistas con los
mismos datos y sin la nota al pie obtienen números distintos, y los dos creen tener
razón. La fórmula es la parte fácil.

**2. El denominador cambia entre años.** Para 2024, 2025, 2026 y 2027 los días
medibles son 70, 74, 78 y 75: una variación del **11 %** producida solo por cómo cae el
calendario. El valor anual es el promedio de cuatro mediciones trimestrales, de modo
que comparar dos años compara promedios calculados sobre cantidades distintas de días.
No invalida el indicador; sí es algo que un informe honesto dice.

**3. Hay dos calendarios, y confundirlos cambia el resultado.** Uno dice qué días son
**elegibles** y otro en qué meses se **mide**. Cruzarlos es lo que da el denominador
real, y revela que algunas reglas no afectan nada. Ver [[regla-redundante]].

### Qué hacer al reproducir un indicador ajeno

1. **Buscar la nota al pie.** La fórmula está en la tabla; la metodología, en la nota.
2. **Escribir cada regla con su cita.** Una regla sin fuente no se puede defender ante
   quien audita.
3. **Separar elegibilidad de medición.** Son dos calendarios.
4. **Medir el aporte de cada regla**, no suponerlo.
5. **Declarar lo que la metodología no especifica**, y medir su efecto. Ver
   [[supuesto-medido]].
6. **Informar el denominador junto con el valor.** Siempre.

### Dónde más aparece

Cualquier indicador con calendario declarado: días hábiles de un acuerdo de nivel de
servicio, días de bolsa en una serie financiera, días de clase en un indicador
educativo, turnos de producción, días de atención en un indicador hospitalario. En
todos, la pregunta es la misma y la respuesta vive en una nota: **¿sobre qué días se
calcula esto?**
