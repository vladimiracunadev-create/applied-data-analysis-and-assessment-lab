---
id: intervalo-de-confianza
tipo: formula
titulo: Intervalo de confianza de una media y de una proporción
etiquetas: [estadistica, inferencia-estadistica, formulas, incertidumbre]
fuente: lab/stats.py
relacionados: [valor-p-que-significa, cobertura-de-un-indicador]
---

**Media.** Con `n` observaciones, media `x̄` y desviación muestral `s`:

```
SE = s / √n                                   error estándar  [unidad de x]
IC = x̄ ± t_{1−α/2, n−1} · SE                  [unidad de x]
```

El valor crítico viene de la t de Student con `n − 1` grados de libertad, no de la
normal, porque `s` se estimó de los mismos datos. Con `n = 5` y 95 %, el crítico es
2,776; con `n = 121`, 1,980; y tiende a 1,960 al crecer `n`.

**Proporción (intervalo de Wilson).** Preferible al intervalo normal, que con `p̂`
cercano a 0 o 1 produce límites fuera de [0, 1]:

```
             p̂ + z²/2n  ±  z · √( p̂(1−p̂)/n + z²/4n² )
IC_Wilson = ───────────────────────────────────────────
                            1 + z²/n
```

Con 40 éxitos de 100 y 95 %: [0,3094; 0,4980]. El intervalo no es simétrico alrededor
de 0,40, y eso es correcto.

**Interpretación.** «Si repitiéramos el muestreo muchas veces y construyéramos el
intervalo de la misma forma, el 95 % de esos intervalos contendría el valor
poblacional.» **No** significa «hay 95 % de probabilidad de que el valor esté en este
intervalo»: el valor poblacional es fijo, el intervalo es lo aleatorio.

**Qué informar.** Estimación, límites, nivel de confianza y `n`.
`lab.stats.Estimate` reúne los cuatro.

**Condición de uso.** El intervalo supone observaciones independientes. Con datos
operacionales agrupados (varios viajes del mismo recorrido y del mismo día) la
independencia no se cumple y el intervalo resulta más estrecho de lo que corresponde.
Conviene declararlo como limitación.
