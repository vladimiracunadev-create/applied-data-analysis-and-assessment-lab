---
id: defecto-que-no-existe
tipo: leccion
titulo: Un cruce que falla puede estar diciendo que el cruce no correspondía
etiquetas: [calidad-datos, cruce-consolidacion, pensamiento-critico, datos-reales, errores-frecuentes]
fuente: cases/gtfs_red_movilidad/solution.py
relacionados: [cruce-con-cardinalidad, horario-relativo-vs-absoluto, hecho-inferencia-hipotesis]
---

**El falso hallazgo.** En el GTFS de la red de Santiago, 5 991 de las 18 486 filas de
`stops.txt` no aparecen en la tabla de horarios. El **32 %**. La conclusión tentadora,
y la que se escribe cuando hay prisa: «un tercio de las paradas está huérfano, hay un
problema de calidad de datos».

**Por qué es falso.** `stops.txt` no es una lista de paradas: es una **jerarquía de
lugares**, y la columna `location_type` dice de qué tipo es cada uno.

| `location_type` | Qué es | Filas | En horarios | Huérfanas de verdad |
| --- | --- | --- | --- | --- |
| 0 | parada o andén | 12 497 | 12 495 | **2** |
| 3 | nodo genérico de pasillo | 5 031 | 0 | 0 |
| 4 | área de abordaje | 534 | 0 | 0 |
| 2 | acceso o salida | 298 | 0 | 0 |
| 1 | estación | 126 | 0 | 0 |

Solo el tipo 0 es un lugar donde sube gente. Las 5 989 restantes **no deben** aparecer
en los horarios: son la estructura de las estaciones, no puntos de parada. Las paradas
realmente sin uso son **dos**, el 0,016 %.

**El costo de equivocarse.** Reportar ese 32 % como hallazgo de calidad en una
evaluación cuesta más puntos que no reportar nada: demuestra que no se leyó el modelo
de datos, y pone en duda el resto del informe. Un falso positivo ruidoso es peor que
un silencio.

**El procedimiento que lo evita.** Ante un cruce con muchas filas sin pareja, antes de
declarar un defecto:

1. **¿La población de la izquierda es la que creo?** Casi siempre el error está aquí.
   Una tabla puede contener varios tipos de entidad distinguidos por una columna de
   tipo, de estado o de nivel.
2. **¿Hay una columna que segmente la tabla?** `location_type`, `tipo_registro`,
   `nivel`, `es_resumen`, `activo`. Agrupar los huérfanos por ella: si se concentran
   en un valor, es semántica, no calidad.
3. **¿La especificación dice algo?** Diez minutos de documentación ahorran un hallazgo
   falso.
4. **Recién entonces, el residuo es el defecto real.** Y se reporta con su recuento
   exacto: «dos paradas sin uso, el 0,016 %».

**La forma de escribirlo en un informe.** No «el 32 % de las paradas está huérfano»,
sino:

> De las 18 486 filas de `stops.txt`, 5 991 no aparecen en los horarios. 5 989 de ellas
> corresponden a estaciones, accesos, nodos de pasillo y áreas de abordaje
> (`location_type` distinto de 0), que por especificación no tienen horarios. Las
> paradas efectivamente sin servicio son dos.

**Regla general.** Un número sorprendente exige dos explicaciones antes de ser un
hallazgo: que el dato esté mal, o que yo lo esté leyendo mal. La segunda es más
frecuente y más barata de comprobar. Ver [[hecho-inferencia-hipotesis]].
