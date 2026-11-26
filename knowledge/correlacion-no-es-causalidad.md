---
id: correlacion-no-es-causalidad
tipo: concepto
titulo: Qué permite y qué no permite concluir una correlación
etiquetas: [estadistica, inferencia-estadistica, pensamiento-critico, errores-frecuentes]
fuente: lab/stats.py
relacionados: [hecho-inferencia-hipotesis, valor-p-que-significa]
---

El coeficiente de Pearson mide **asociación lineal** entre dos variables, en el
rango [-1, 1]:

```
r = Σ(xᵢ − x̄)(yᵢ − ȳ) / √[ Σ(xᵢ − x̄)² · Σ(yᵢ − ȳ)² ]
```

Qué **sí** permite afirmar un `r = 0,85`: cuando una variable es alta, la otra tiende
a ser alta, de forma aproximadamente lineal, en esta muestra.

Qué **no** permite afirmar:

1. **Dirección.** `r` es simétrico: `r(x, y) = r(y, x)`. No distingue causa de efecto.
2. **Causa.** Una tercera variable puede producir ambas (confusión). El ejemplo
   clásico: la venta de helados y los ahogamientos suben juntos porque sube la
   temperatura.
3. **Relación no lineal.** Con `x = [-3..3]` e `y = x²`, la relación es determinista y
   `r = 0`. Un `r` cercano a cero **no** significa independencia.
4. **Magnitud del efecto en unidades.** `r` es adimensional; no dice cuánto cambia `y`
   por unidad de `x`. Eso lo da una regresión, con su pendiente y su unidad.

**Qué se necesita para hablar de causa.** Un diseño que lo sostenga:
asignación aleatoria, una variación exógena creíble, o un argumento explícito sobre
las variables de confusión controladas. Nada de eso viene del coeficiente.

**Redacción correcta en un informe.** «Los recorridos con mayor duración media
presentan menor puntualidad (r = -0,72). Los datos no permiten establecer la
dirección causal: ambas podrían reflejar congestión no observada.»
