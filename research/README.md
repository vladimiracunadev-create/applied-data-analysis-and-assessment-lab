# Laboratorio de investigación aplicada

Espacio para investigaciones completas: exploratorias, descriptivas, correlacionales,
explicativas, experimentales y documentales, con metodologías cuantitativas,
cualitativas o mixtas.

## Estado actual

**Ninguna investigación completa publicada todavía.** Lo que existe es la
infraestructura para hacerlas:

| Pieza | Estado | Dónde |
| --- | --- | --- |
| Metodología de 18 etapas, auditable | implementada | `lab.method`, [`docs/metodologia.md`](../docs/metodologia.md) |
| Informe con 20 secciones obligatorias | implementado | `lab.report.research_report` |
| Inferencia estadística sin dependencias externas | implementada | `lab.stats` |
| Clase sobre método, preguntas e hipótesis | publicada | [`docs/learning/50-investigacion/01-metodo-preguntas-e-hipotesis.md`](../docs/learning/50-investigacion/01-metodo-preguntas-e-hipotesis.md) |
| Plantilla de protocolo | disponible | [`templates/protocolo.md`](templates/protocolo.md) |
| Primera investigación aplicada | **proyectada** | ver [`docs/roadmap.md`](../docs/roadmap.md), fase 2 |

Esta distinción es deliberada: el laboratorio no declara implementado lo que está
proyectado.

## Cómo iniciar una investigación

1. Copie [`templates/protocolo.md`](templates/protocolo.md) a
   `research/<slug>/protocolo.md` y complételo **antes** de mirar los datos. Un
   protocolo escrito después de ver los resultados no protege de nada.
2. Abra una corrida de la metodología y regístrela:

   ```python
   from datetime import date
   from lab.method import MethodRun

   corrida = MethodRun(problem="<pregunta>", owner="<responsable>",
                       started=date.today())
   corrida.complete("recepcion", evidence="research/<slug>/protocolo.md")
   ```

3. Trabaje los datos con el núcleo (`lab.contracts`, `lab.metrics`, `lab.stats`),
   dejando constancia de cada exclusión.
4. Redacte con `lab.report.research_report`, que se niega a exportar mientras falte
   una de las 20 secciones obligatorias.
5. Registre lo aprendido en `knowledge/` y, si hizo falta una capacidad nueva,
   agréguela al núcleo con su prueba.

## Reglas

- **No inventar fuentes, referencias, cifras ni resultados.** Si no pudo abrir la
  fuente, no la cite. El ejemplo de cómo documentar esto está en
  [`docs/dtpm-antecedentes.md`](../docs/dtpm-antecedentes.md): lo verificado separado
  de lo pendiente.
- **Distinguir hecho, evidencia, inferencia, interpretación e hipótesis.**
  `lab.report.Report.claim` lo exige y lo imprime clasificado.
- **Declarar el diseño antes de interpretar.** Un estudio observacional no sostiene
  una afirmación causal, por sofisticado que sea el método.
- **Reportar tamaño de efecto e incertidumbre**, no solo el valor p.
- **Declarar las limitaciones.** Un informe sin limitaciones es un informe cuyas
  limitaciones encontrará otra persona.
- **Datos personales, nunca.** Si el problema los exige, se trabaja fuera del
  repositorio y se publica solo el agregado, con su método de anonimización escrito.

## Estructura de una investigación

```
research/<slug>/
├── protocolo.md        escrito antes de ver los datos
├── seguimiento.md      salida de MethodRun.to_markdown()
├── analisis.py         código reproducible
├── datos/              o una referencia a data/ si usa los del laboratorio
├── resultados/         tablas y gráficos generados
└── informe.md          las 20 secciones obligatorias
```
