# Caso: indicadores operacionales de transporte público

Caso prioritario del laboratorio. Entrena las competencias de un **gestor de datos**
del sector público: consolidar fuentes heterogéneas, declarar exclusiones, producir
indicadores operacionales y poder defenderlos.

> Datos completamente **sintéticos**, generados con semilla fija. No reproducen
> magnitudes de ningún sistema real ni material oficial de ninguna institución. Los
> antecedentes públicos que sí se verificaron están en
> [`docs/dtpm-antecedentes.md`](../../docs/dtpm-antecedentes.md), separando lo
> comprobado de lo pendiente.

Metadatos completos del caso: [`case.json`](case.json).

## Qué contiene

| Recurso | Ruta | Para qué |
| --- | --- | --- |
| Enunciados de 4 horas | [`simulations/`](../../simulations/) | resolver con reloj |
| Datos de los tres casos | `data/case_1` … `case_3` | entrada del ejercicio |
| Diccionario de datos y reglas | [`docs/diccionario.md`](../../docs/diccionario.md) | qué significa cada campo |
| Solución en Pandas | `solutions/reference.py` | referencia, **después** de resolver |
| Solución en Polars | `solutions/polars_reference.py` | implementación columnar independiente |
| Solución en R base | `solutions/r_reference.R` | implementación independiente sin paquetes |
| Solución en SQL | `solutions/sql_reference.py` | segunda implementación independiente |
| Guía de Excel | [`solutions/EXCEL.md`](../../solutions/EXCEL.md) | cómo construir el libro |
| Libros de Excel resueltos | `solutions/excel/case_N_resuelto.xlsx` | fórmulas vivas y hoja de control |
| Equivalencias entre herramientas | [`docs/equivalencias.md`](../../docs/equivalencias.md) | SQL ↔ Pandas ↔ Polars ↔ Excel ↔ R |
| Banco de ítems y rúbricas | `assessments/items/` | practicar por competencia |

## Preparar el entorno

```powershell
uv sync
```

```powershell
uv run python scripts/generate_data.py
```

```powershell
uv run python -m pytest
```

Polars es opcional; para ejecutar la validación multitecnología:

```powershell
uv sync --extra polars
uv run python solutions/polars_reference.py transport 1
Rscript solutions/r_reference.R transport 1 reference_outputs/r/transport
```

R usa únicamente la biblioteca base. CI instala el runtime y confronta sus siete
tablas con Pandas; no se exige R para usar el entorno mínimo de Python.

Para trabajar en Excel, exporte los cuatro CSV a un libro de entradas:

```powershell
uv run python scripts/export_inputs.py
```

También puede importarlos a mano: **Datos → Obtener datos → Desde texto/CSV**, con
codificación UTF-8 y separador coma. **No** haga doble clic sobre el CSV: Excel usa la
configuración regional del sistema y ahí se rompen los acentos y el orden de día y mes.

**Respaldos.** Google Colab: suba los CSV a la sesión y use el notebook; no requiere
`uv`. Google Sheets: **Archivo → Importar**, separador coma. Verifique con una fórmula
trivial si su documento usa coma o punto y coma como separador de argumentos antes de
construir nada.

## Trabajo recomendado

1. Lea el diccionario de datos y el enunciado. **No abra `solutions/` todavía.**
2. Resuelva con reloj de cuatro horas. Distribución sugerida: 15 min de lectura,
   30 de calidad, 80 de Python, 55 de Excel, 30 de análisis, 20 de validación y 10 de
   envío.
3. Guarde su trabajo en `submissions/` (no se versiona).
4. Corríjase con la rúbrica del enunciado antes de mirar la solución.
5. Compare contra la referencia:

   ```powershell
   uv run python solutions/reference.py 1
   ```

6. Construya el libro resuelto y abra la hoja `30_control`: compara Excel contra Python
   al abrirlo, y sus cuatro valores deben ser cero.

   ```powershell
   uv run python scripts/build_excel_solutions.py --case 1
   ```

7. Registre el intento y revise la tendencia, no la nota aislada:

   ```python
   from lab.assessment import progress_frame
   progress_frame([
       {"fecha": "2026-11-27", "simulacion": "01", "nota": 68, "minutos": 240},
       {"fecha": "2026-11-28", "simulacion": "02", "nota": 79, "minutos": 235},
   ])
   ```

## Ruta intensiva

Cuatro días, de lo más barato a lo más caro en tiempo. Si va corto, el orden importa
más que la cobertura: la calidad de datos y los denominadores pesan más en una
corrección que un indicador adicional.

| Día | Foco | Material |
| --- | --- | --- |
| **Jueves 26** | Entorno y fundamentos. Verificar que `uv run python -m pytest` pasa. Clases de fundamentos y estadística descriptiva. Ejercicios de limpieza. | `docs/learning/00-fundamentos/`, `docs/learning/10-matematicas/` |
| **Viernes 27** | Pandas y Excel a fondo, equivalencias, y **simulación 1** completa con reloj. | `docs/learning/20-programacion/`, `docs/equivalencias.md`, `simulations/01_enunciado.md` |
| **Sábado 28** | Corrección de la simulación 1 con rúbrica. Cruces, contratos y validación cruzada. **Simulación 2.** | `docs/learning/30-ingenieria/01`, `simulations/02_enunciado.md` |
| **Domingo 29** | Indicadores, visualización e interpretación. **Simulación 3.** Repaso de los registros de tipo `error` de la base de conocimiento. | `docs/learning/40-analisis/01`, `simulations/03_enunciado.md`, `docs/conocimiento.md` |
| **Lunes 30** | Solo verificación: entorno, Colab y Sheets de respaldo, formatos de entrega. **No estudiar temas nuevos.** | — |

Repaso rápido de los defectos que más puntos cuestan:

```powershell
uv run python -m lab.knowledge "denominador cobertura duplicados"
```

## Las cinco cosas que se corrigen

Resumen de lo que las rúbricas premian, en orden de peso:

1. **Calidad y trazabilidad.** Cada defecto cuantificado, cada exclusión contada y con
   su efecto declarado por indicador.
2. **Transformación y cruces.** Tipos resueltos, cardinalidad comprobada, claves
   desconocidas reportadas y no descartadas en silencio.
3. **Indicadores correctos.** Denominador explícito, unidad declarada, totales que
   cuadran entre tablas. Suma sobre suma, **no** promedio de porcentajes.
4. **Verificación en Excel.** Fórmulas que se pueden abrir y leer, no valores pegados.
5. **Interpretación y supuestos.** Hallazgos clasificados como hecho, inferencia o
   hipótesis, y ninguna causa atribuida sin evidencia.

## Reglas

La evaluación real define sus propios entregables y condiciones. Este material es de
entrenamiento y **no autoriza el uso de asistentes de inteligencia artificial durante
una evaluación**. No publique datos de postulaciones, correos ni información personal
en este repositorio.
