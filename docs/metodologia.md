<!-- Archivo generado por scripts/build_docs.py. No lo edite a mano: modifique el código fuente y vuelva a ejecutar el script. -->

# Metodología universal de resolución de problemas

**18 etapas**, implementadas en `lab.method` como objetos de
seguimiento auditables. Una etapa no se puede marcar como completada sin
evidencia verificable, y declararla no aplicable exige un motivo escrito.

## Etapas

| # | Etapa | Pregunta que responde | Entregable mínimo |
| --- | --- | --- | --- |
| 1 | Recepción y comprensión del problema | ¿Qué se está pidiendo exactamente y con qué palabras lo pide quien consulta? | Enunciado reformulado y lista de ambigüedades detectadas. |
| 2 | Identificación del contexto | ¿En qué dominio, organización, marco legal y momento ocurre el problema? | Descripción del contexto y de los actores afectados. |
| 3 | Determinación de objetivos y restricciones | ¿Qué resultado se busca, con qué límites de tiempo, datos, herramientas y ética? | Objetivo general, objetivos específicos y restricciones explícitas. |
| 4 | Descomposición del problema | ¿En qué subproblemas independientes se puede partir? | Árbol de subproblemas con dependencias. |
| 5 | Identificación del conocimiento necesario | ¿Qué hay que saber para resolverlo y qué parte de eso aún no se sabe? | Lista de conocimientos requeridos, disponibles y faltantes. |
| 6 | Investigación de antecedentes | ¿Quién resolvió algo parecido y con qué resultado? | Revisión de antecedentes con referencias verificables. |
| 7 | Selección de fuentes y herramientas | ¿Qué fuentes y tecnologías son apropiadas y por qué, frente a qué alternativas? | Decisión justificada con alternativas descartadas. |
| 8 | Adquisición y preparación de datos | ¿De dónde vienen los datos, con qué licencia y en qué estado llegan? | Datos crudos inmutables, diccionario, contrato e informe de calidad. |
| 9 | Diseño de alternativas | ¿Qué caminos de solución existen y cómo se comparan? | Dos o más alternativas con criterios de comparación. |
| 10 | Experimentación | ¿Qué se prueba, con qué parámetros y qué se mide? | Diseño experimental reproducible y registro de corridas. |
| 11 | Implementación de soluciones | ¿Cómo queda construida la solución elegida? | Código ejecutable, documentado y versionado. |
| 12 | Medición y evaluación | ¿Qué métricas describen el desempeño de la solución? | Indicadores calculados con denominadores explícitos. |
| 13 | Validación independiente | ¿Un método distinto produce el mismo resultado? | Comprobación cruzada con herramienta o implementación alternativa. |
| 14 | Interpretación de resultados | ¿Qué significan los números en el dominio del problema? | Interpretación que separa hecho, inferencia e hipótesis. |
| 15 | Comunicación de conclusiones | ¿Cómo se explica a quien debe decidir? | Informe o visualización con unidades, período y fuente. |
| 16 | Identificación de limitaciones | ¿Qué no permite concluir este trabajo? | Limitaciones, sesgos e incertidumbre declarados. |
| 17 | Generación de conocimiento reutilizable | ¿Qué quedó aprendido y en qué forma se puede volver a usar? | Registro en la base de conocimiento con patrón y lecciones. |
| 18 | Incorporación de capacidades al laboratorio | ¿Qué del núcleo, pruebas o documentación cambió gracias a este problema? | Cambios integrados al repositorio y pruebas que los protegen. |

## Uso

```python
from datetime import date
from lab.method import MethodRun

corrida = MethodRun(problem="Medir cumplimiento de la programación",
                    owner="equipo de datos", started=date(2026, 11, 26))
corrida.complete("recepcion", evidence="docs/enunciado.md",
                 decisions="Se acota a octubre de 2026")
corrida.skip("experimentacion", reason="no hay intervención que probar")

print(corrida.coverage())      # proporción de etapas aplicables completadas
print(corrida.pending())       # qué falta, en orden
print(corrida.to_markdown())   # informe de seguimiento
```

## Por qué está implementada y no solo escrita

Una metodología en un documento no se puede auditar. Representada como datos, se
puede validar (¿quedaron etapas sin evidencia?), comparar entre casos y exigir en
las pruebas automáticas. La cobertura de una corrida es un número, no una
impresión.
