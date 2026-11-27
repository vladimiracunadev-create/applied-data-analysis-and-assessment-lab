# Dónde estudiar el próximo centro de carga bip!

Fecha: 2026-11-26

> Cribado territorial con oferta programada y proximidad; no es una decisión de inversión.

## Contexto

La red tiene 12 497 paradas de embarque y 1 927 lugares de carga abiertos publicados.

## Definición del problema

Priorizar zonas para estudiar un nuevo centro sin confundir baja cobertura con demanda demostrada.

## Objetivos

Resumir oferta, medir cobertura y producir una lista corta de celdas para factibilidad.

## Datos y diccionario

Resultados reproducibles de P06 y P08; GTFS vigente y lugares bip! públicos.

## Metodología

Cobertura haversine a 300 m; rejilla de 0,01°; prioridad exploratoria = paradas descubiertas × distancia mediana.

## Supuestos

300 m es referencia; factor de rodeo 1,3 es sensibilidad; una celda no es un predio.

## Resultados

Cuatro cifras para la decisión:

| indicador | valor | unidad | lectura |
| --- | --- | --- | --- |
| salidas programadas en día laboral | 64,011.00 | salidas | oferta programada, no demanda |
| hora de mayor oferta | 7.00 | hora | 4541 salidas programadas |
| paradas con carga a 300 m en línea recta | 59.29 | % | referencia espacial |
| paradas con factor de rodeo 1,3 | 46.02 | % | supuesto, no ruta peatonal observada |

## Validación independiente

P06 valida el total por dos caminos; P08 confronta fórmulas y representaciones de coordenadas.

## Interpretación

Las celdas superiores son zonas para estudiar, no ubicaciones aprobadas.

## Limitaciones

Faltan demanda, transacciones, red peatonal, seguridad, disponibilidad de predios, costos y horarios completos.

## Conclusiones

Lista corta para estudio de factibilidad:

| celda_lat | celda_lon | paradas | cubiertas | paradas_sin_cobertura | mediana_m | cobertura_pct | parada_mas_lejana | prioridad_exploratoria |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| -33.40 | -70.66 | 41 | 1 | 40 | 582.40 | 2.40 | PB1400-Emiliano Zapata / esq. Bernardo O'Higgins | 23,296.00 |
| -33.62 | -70.70 | 29 | 0 | 29 | 663.80 | 0.00 | PG987-Los Suspiros / esq. Avenida Central | 19,250.20 |
| -33.63 | -70.62 | 38 | 9 | 29 | 625.20 | 23.70 | PF673-Belén / esq. Río Maihue | 18,130.80 |
| -33.62 | -70.59 | 26 | 2 | 24 | 721.70 | 7.70 | PF720-Sargento Menadier / esq. Uruguay | 17,320.80 |
| -33.50 | -70.71 | 23 | 2 | 21 | 741.10 | 8.70 | PI1967-Av. Los Cerrillos / esq. C. Teresa Herrera | 15,563.10 |

## Reproducibilidad

python -m cases.informe_decision_carga.solution

## Clasificación de afirmaciones

| Tipo | Afirmación | Respaldo |
| --- | --- | --- |
| evidencia | La cobertura en línea recta a 300 m es 59,29 %. | P08: 7 409/12 497. |
| inferencia | Las celdas priorizadas ameritan revisión. | Regla declarada de cribado territorial. |
| hipotesis | Un nuevo centro podría reducir la brecha. | Debe contrastarse con demanda y factibilidad. |

Cómo leer esta tabla:

- **evidencia**: Resultado de un cálculo sobre los datos, con método declarado.
- **hipotesis**: Explicación posible, todavía no contrastada.
- **inferencia**: Conclusión derivada de la evidencia, con el supuesto que la sostiene.
