---
id: hecho-inferencia-hipotesis
tipo: metodologia
titulo: Distinguir hecho, evidencia, inferencia, interpretación e hipótesis
etiquetas: [metodologia, investigacion-aplicada, comunicacion-resultados, pensamiento-critico]
fuente: lab/report.py, docs/research-method.md
relacionados: [correlacion-no-es-causalidad, cobertura-de-un-indicador]
---

Cinco categorías que un informe debe mantener separadas, porque cada una admite un
grado distinto de confianza:

| Categoría | Definición | Ejemplo |
| --- | --- | --- |
| **Hecho** | Verificable directamente en los datos entregados | «El archivo tiene 454 filas y 4 duplicados exactos» |
| **Evidencia** | Resultado de un cálculo con método declarado | «La demanda del operador C fue 7 729 pasajeros, cobertura 99,6 %» |
| **Inferencia** | Conclusión derivada de la evidencia, con un supuesto explícito | «El operador C concentra más demanda, suponiendo que el registro es comparable entre operadores» |
| **Interpretación** | Lectura del resultado en el dominio del problema | «La brecha de cumplimiento es operacionalmente relevante» |
| **Hipótesis** | Explicación posible, aún no contrastada | «La brecha podría deberse a disponibilidad de flota» |

**Por qué importa.** Quien decide necesita saber qué puede dar por cierto y qué debe
verificar antes de actuar. Un informe que presenta las cinco categorías con el mismo
tono obliga a quien lee a adivinar, y lo normal es que dé por hecho lo que era
hipótesis.

**Cómo se aplica en el laboratorio.** `lab.report.Report.claim` exige el tipo y el
respaldo de cada afirmación, y el informe final imprime la tabla de clasificación con
su leyenda. Una afirmación sin respaldo declarado no se puede registrar.

**Señal de alarma en una redacción.** Las palabras «porque», «debido a» y «explica»
convierten una evidencia en inferencia causal. Antes de usarlas hay que poder nombrar
el diseño que sostiene la causa. Ver [[correlacion-no-es-causalidad]].
