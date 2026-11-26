---
id: regla-redundante
tipo: patron
titulo: Distinguir una regla redundante por construcción de una redundante por azar
etiquetas: [indicadores, gobernanza-datos, metodologia, datos-reales, pensamiento-critico]
fuente: lab/calendars.py, cases/calendario_medicion/solution.py
relacionados: [denominador-es-una-decision, supuesto-medido, defecto-que-no-existe]
---

**El problema.** Una metodología declara ocho reglas de exclusión. ¿Cuánto aporta cada
una? La respuesta intuitiva —cuántos días excluye— está mal, por dos motivos distintos.

### Primer motivo: las reglas se solapan

Sobre el año 2026, las ocho reglas excluyen **256 días** si se suma lo que excluye cada
una, y **201 días** en total. El solapamiento es de **55 días**.

La medida correcta es la **exclusión exclusiva**: cuántos días **solo** esa regla
excluye. Es lo que se recuperaría al quitarla.

| Regla | Excluye | Exclusiva | Solapada |
| --- | --- | --- | --- |
| fin de semana | 104 | 62 | 42 |
| meses completos | 90 | 58 | 32 |
| días 28 y 29 | 23 | 11 | 12 |
| **día del joven combatiente** | **1** | **0** | **1** |

El «Día del joven combatiente» es el 29 de marzo, y la regla de los días 28 y 29 ya lo
descarta. Exclusión exclusiva **cero**: la regla no cambia un solo día.

### Segundo motivo: el denominador real no es el año

El indicador se mide solo en marzo, junio, septiembre y noviembre. Al medir cuántos
días **medibles** recuperaría el quitar cada regla, aparece algo que la tabla anterior
no mostraba:

| Regla | Exclusiva sobre el año | Días medibles que quita |
| --- | --- | --- |
| fin de semana | 62 | **25** |
| **meses completos (ene, feb, dic)** | **58** | **0** |
| **vacaciones de invierno (julio)** | **9** | **0** |
| días 28 y 29 | 11 | 2 |

Excluir enero, febrero y diciembre descarta 58 días en exclusiva del año y **ninguno**
de los que se miden, porque esos meses no son meses de medición. Lo mismo con las
vacaciones de invierno, que caen en julio.

### La distinción que evita el error

Comparando cuatro años, las reglas se separan en tres grupos:

| Clasificación | Reglas | Qué significa |
| --- | --- | --- |
| **Efectiva** | fin de semana, días 28 y 29, semana de fiestas patrias | Quitan días medibles **todos** los años |
| **Redundante accidental** | feriados, 11 de septiembre | Sin efecto **este** año, por cómo cayó el calendario |
| **Redundante estructural** | meses completos, vacaciones de invierno, día del joven combatiente | Sin efecto en **ningún** año, por construcción |

Es la diferencia operativa que importa: **quitar una regla estructuralmente redundante
no cambia nada nunca; quitar una accidental funciona este año y falla el siguiente.** En
2026 los feriados no quitan ningún día medible; en 2027 quitan tres.

El motivo de ese cero en 2026 es instructivo: el 29 de junio es a la vez feriado y día
29, de modo que está doblemente excluido y quitar la regla de feriados no lo recupera.

### Cómo medirlo

No por diferencia algebraica, que se equivoca con los solapamientos, sino **quitando la
regla y reconstruyendo el resultado**:

```python
base = contar(aplicar(todas_las_reglas))
for regla in todas_las_reglas:
    resto = [r for r in todas_las_reglas if r is not regla]
    aporte = contar(aplicar(resto)) - base
```

Es más caro —reconstruye el cálculo una vez por regla— y es correcto.

### Lo que no se concluye

**Que una regla sea redundante no significa que la metodología esté mal.** Puede existir
por prudencia, por herencia histórica, o porque en otro contexto —otro calendario de
medición, otro año— sí haría falta. Lo que aporta medirlo es saber **cuáles** son
redundantes y **por qué**, que es exactamente lo que necesita quien reproduce o audita
el indicador.

### Dónde más aparece

Cualquier conjunto de filtros encadenados heredados de alguien: reglas de validación
acumuladas en un formulario, condiciones de exclusión en una consulta de negocio,
criterios de elegibilidad de un beneficio. Antes de simplificar un filtro, hay que
comprobar si su inutilidad es permanente o circunstancial.
