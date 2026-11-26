---
id: que-fuente-provee-el-campo
tipo: leccion
titulo: Qué fuente provee cada campo es una decisión metodológica, y casi nunca se declara
etiquetas: [gobernanza-datos, metodologia, comunicacion-resultados, calidad-datos, indicadores]
fuente: cases/correspondencia_metro/solution.py
relacionados: [cruce-sin-clave, punto-ciego-del-control, grano-antes-de-cruzar, unidad-de-la-decision]
---

**El caso.** Dos fuentes oficiales traen la coordenada de las mismas 126 estaciones de
Metro. Hay que contar cuántas paradas de bus tiene cada una a 200 m. ¿Con qué coordenada?

Nadie hace la pregunta, porque las dos fuentes son del mismo organismo, ninguna se
presenta como aproximada y la respuesta parece que no debería depender de eso.

Depende:

```
       estaciones_comparables    125
cambia_el_conteo_de_servicios     48   (38,4 %)
          aparecerian_sin_bus      3
   servicios_totales_con_gtfs   2014
    servicios_totales_con_bip   1834   (−9 %)
```

El **38,4 %** de las filas del informe cambia según cuál de las dos coordenadas se use. Y
tres estaciones aparecerían sin ninguna parada de bus cerca cuando sí la tienen.

**Por qué el caso es tan frecuente y tan invisible.** Un análisis moderno junta campos de
varios orígenes, y el `merge` deja la decisión implícita en el orden de los argumentos y
en los sufijos `_x` y `_y`. La elección queda registrada en el código y en ninguna parte
más:

```python
# ¿De quién es la coordenada después de esto? Está decidido, y no está escrito.
tabla = estaciones.merge(otro_inventario, on="clave", how="left")
```

**Cómo se declara.** Tres cosas, y ninguna cuesta mucho:

1. **Una tabla de linaje por campo**: qué fuente provee cada columna del resultado y por
   qué. Una fila por campo, en el README o en los metadatos del caso.
2. **La función parametrizada por el origen**, para poder repetir el cálculo con la otra:

   ```python
   def correspondencia(estaciones, buses, lat_columna="lat", lon_columna="lon"):
       ...
   ```

   La función no sabe de dónde viene la coordenada, y ahí está su valor: permite medir
   la sensibilidad en lugar de argumentarla.
3. **La sensibilidad publicada** junto al resultado: cuántas filas cambian, cuántas
   cambian de clase, y cuánto se mueve el total.

**Cómo se elige, cuando hay que elegir.** No por autoridad de la fuente —las dos eran
oficiales— sino por **evidencia dentro de los datos**. Aquí: las direcciones postales que
trae el propio Excel coinciden con las posiciones del GTFS y no con sus propias
coordenadas. Ver [[dos-afirmaciones-de-la-misma-fila]].

Y lo que se afirma después es modesto a propósito: no «el GTFS tiene razón», sino «las
dos fuentes discrepan, y en los casos inspeccionados la evidencia interna del Excel
apunta al GTFS». La diferencia importa cuando alguien reutilice la conclusión.

**Dónde más aparece.** El precio en el maestro de productos o en el sistema de ventas; la
dirección en el CRM o en la facturación; la fecha de alta en el sistema de personas o en
el de accesos; el nombre del cliente en el contrato o en el registro tributario. En todos
los casos hay dos valores, los dos de origen legítimo, y un informe que usa uno sin decir
cuál.

**Regla corta.** Si dos fuentes pueden proveer un campo, la elección es parte del método
y va en la documentación, con la medición de cuánto habría cambiado la otra.
