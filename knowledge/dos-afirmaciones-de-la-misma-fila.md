---
id: dos-afirmaciones-de-la-misma-fila
tipo: patron
titulo: Dos campos que describen lo mismo son dos afirmaciones independientes, y se pueden contrastar
etiquetas: [calidad-datos, validacion-independiente, geoespacial, datos-reales, pensamiento-critico]
fuente: cases/correspondencia_metro/solution.py
relacionados: [punto-ciego-del-control, dos-coordenadas-un-lugar, grano-antes-de-cruzar, agregado-que-suaviza]
---

**La idea.** Una fila de datos suele afirmar la misma cosa más de una vez, por campos
distintos y construidos por caminos distintos. Cada par de afirmaciones redundantes es
una validación gratuita que no necesita ninguna fuente externa.

**El caso.** El registro de una estación de Metro:

```
nombre:     SANTA LUCIA
direccion:  Av. Libertador Bernardo O´Higgins N°511    ← el centro de Santiago
comuna:     Santiago
latitud:    -33.501205
longitud:   -70.762993                                 ← 12,7 km al suroeste
```

Tres afirmaciones sobre dónde está el lugar: la dirección, la comuna y la coordenada. La
coordenada contradice a las otras dos. Y las otras dos son correctas: la contradicción
dice **cuál** de los campos está mal.

Esa fila había pasado la validación de coordenadas del archivo —que compara el UTM con
la latitud/longitud— porque las dos representaciones estaban igual de equivocadas. Ver
[[punto-ciego-del-control]].

**Cómo se contrasta una dirección sin geocodificador.** No hace falta resolverla: basta
con la **unidad administrativa que la propia fila declara**. Si la comuna dice
`Santiago`, la coordenada debería estar donde están los otros locales de la comuna
`Santiago`:

```python
referencia = locales.groupby("comuna_clave").agg(
    lat_comuna=("latitud", "median"),      # mediana, no promedio: un error a 26 km
    lon_comuna=("longitud", "median"),     # arrastra el promedio y ciega el detector
    n=("codigo", "size"),
)
locales = locales.join(referencia, on="comuna_clave")
locales["km_a_su_comuna"] = haversine_km(
    locales["latitud"], locales["longitud"],
    locales["lat_comuna"], locales["lon_comuna"],
)
```

Sobre el archivo real, a más de 10 km de la mediana de su propia comuna quedan **8
locales**, tres de ellos estaciones con la coordenada verificadamente mal. A 3 km quedan
227, que son demasiados para ser todos errores en comunas extensas: el detector es una
**señal y no un veredicto**, y conviene publicar la curva de umbrales en lugar de
esconder la elección en una constante.

**Los pares redundantes que casi siempre existen.**

| Afirmación | Su par | Qué se comprueba |
| --- | --- | --- |
| coordenada | comuna, región, zona, sucursal | pertenencia aproximada |
| coordenada | dirección postal | consistencia de calle y numeración |
| coordenada en UTM | la misma en lat/lon | conversión y digitación |
| fecha de nacimiento | edad declarada | aritmética contra la fecha del registro |
| razón social | identificador tributario | correspondencia en un padrón |
| total | suma del desglose | cuadratura |
| importe bruto | neto más impuesto | cuadratura |
| hora de inicio y fin | duración declarada | aritmética |
| código postal | ciudad | pertenencia |

**Lo que hay que resistir.** La tentación de **derivar** uno de los campos del otro para
«normalizar». Si la comuna se recalcula desde la coordenada, se pierde la única
afirmación independiente que permitía detectar que la coordenada estaba mal. Los campos
redundantes son redundantes **a propósito**: su valor es el desacuerdo.

**Regla corta.** Antes de salir a buscar una segunda fuente, contar cuántas veces la fila
ya dice lo mismo. Casi siempre son dos o tres, y casi nunca se comparan.
