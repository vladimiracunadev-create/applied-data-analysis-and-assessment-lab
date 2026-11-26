---
id: cruce-con-cardinalidad
tipo: patron
titulo: Cruzar tablas controlando la cardinalidad
etiquetas: [cruce-consolidacion, calidad-datos, pandas, sql, excel, equivalencias]
fuente: lab/core.py, lab/contracts.py
relacionados: [vacio-no-es-cero, count-asterisco-vs-columna]
---

Un cruce puede fallar de dos maneras opuestas, y ambas pasan desapercibidas si no se
comprueban los recuentos antes y después.

**Pérdida de filas.** Un cruce interno descarta en silencio los registros cuya clave
no existe en el catálogo. En el caso de transporte, los viajes con `recorrido_id =
'R99'` desaparecerían y la demanda total bajaría sin explicación.

**Multiplicación de filas.** Si el catálogo no es único en su clave, cada fila de la
tabla izquierda se duplica. Una suma de pasajeros sobre el resultado quedaría
inflada, y el total seguiría pareciendo verosímil.

**Procedimiento.**

1. Contar filas de la tabla izquierda antes del cruce.
2. Comprobar que la clave del catálogo es única.
3. Cruzar por la izquierda, no internamente, para conservar lo que no encuentra par.
4. Contar filas después: deben ser las mismas.
5. Contar y reportar las claves sin correspondencia.

**En Pandas.** `validate` convierte el paso 2 en un error inmediato en lugar de un
resultado silenciosamente erróneo:

```python
izquierda.merge(catalogo, on="clave", how="left", validate="many_to_one", indicator=True)
```

`lab.core.audited_join` hace esto y devuelve además la tabla de auditoría del
indicador. `lab.contracts.ForeignKey` declara la relación para que la validación la
compruebe antes del cruce.

**En SQL.** `LEFT JOIN` y, para detectar duplicación, comparar
`COUNT(*)` antes y después. Las claves huérfanas se cuentan con la diferencia entre
`COUNT(*)` y `COUNT(columna_del_catalogo)`. Ver
[[count-asterisco-vs-columna]].

**En Excel.** `BUSCARX` con el cuarto argumento declarado:
`=BUSCARX([@recorrido_id];Recorridos[recorrido_id];Recorridos[operador_id];"SIN CLAVE")`.
El valor por defecto hace visible la clave desconocida; sin él, `#N/D` se propaga a
las tablas dinámicas.
