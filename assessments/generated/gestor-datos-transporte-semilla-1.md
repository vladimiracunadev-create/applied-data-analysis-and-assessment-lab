# Simulación de evaluación técnica — Gestor de datos, sector transporte

> **Simulación de entrenamiento.** No es una prueba oficial de ninguna institución ni reproduce instrumentos reales de selección.

- Cargo de referencia: Gestor de datos
- Especialidad: Gestión y análisis de datos operacionales · Industria: Transporte público
- Nivel declarado: avanzado
- Tiempo: 260 de 240 minutos presupuestados
- Herramientas admitidas: Excel, Python, Pandas, Google Sheets, SQL
- Uso de asistentes de IA: no permitido
- Semilla de generación: 1 (reproducible)

## Entregables

1. Script o notebook reproducible (`analisis.py` o `analisis.ipynb`).
2. Libro `resultados.xlsx` con hojas de calidad, indicadores y control de validación.
3. Informe `informe.md` con tres hallazgos clasificados, supuestos y limitaciones.

## Ítems

### Ítem 1 · gd-002-tipos-y-fechas (20 min, introductorio)

Convierta las columnas de fecha-hora y la columna numérica de pasajeros a su tipo correcto. Informe cuántos valores no se pudieron interpretar en cada columna y qué supuso sobre el formato de fecha (día/mes/año o mes/día/año) y por qué.

- Entregable: Código o pasos de conversión más un recuento de valores no interpretables por columna.
- Competencias: fechas-horarios, limpieza-normalizacion
- Datos: `data/case_1`
- Se corrige:
  - El supuesto de formato de fecha está declarado explícitamente.
  - Los valores no interpretables quedan como nulos y contados, no eliminados en silencio.
  - La conversión numérica distingue vacío de cero.

### Ítem 2 · gd-015-exportacion-entregables (15 min, introductorio)

Exporte los resultados a un único libro de Excel con una hoja por indicador y a archivos CSV. Compruebe que los totales del libro coinciden con los del código y que los archivos se abren con la codificación correcta en un equipo distinto.

- Entregable: Libro .xlsx con una hoja por indicador y los CSV equivalentes.
- Competencias: lectura-escritura-datos, reproducibilidad
- Datos: `data/case_1`
- Se corrige:
  - Los totales del libro coinciden con los del código.
  - La codificación de los CSV permite leer los acentos correctamente.
  - Los nombres de hoja y de archivo son explícitos.

### Ítem 3 · gd-003-duplicados (20 min, intermedio)

Distinga duplicados exactos de duplicados por clave de negocio. Informe cuántas filas son idénticas en todas sus columnas y cuántas repiten el identificador de viaje con contenido distinto. Proponga un tratamiento distinto para cada caso y justifíquelo.

- Entregable: Tabla con ambos recuentos y una nota con el tratamiento elegido.
- Competencias: calidad-datos, limpieza-normalizacion
- Datos: `data/case_1`
- Se corrige:
  - Los dos tipos de duplicado se cuentan por separado.
  - El tratamiento propuesto no borra información sin registrarla.
  - Se explica por qué un duplicado exacto se puede eliminar y uno por clave no.

### Ítem 4 · gd-005-demanda-por-operador (25 min, intermedio)

Calcule la demanda de pasajeros por operador, considerando únicamente viajes realizados con clave conocida y conteo de pasajeros válido. Informe además cuántos viajes aportaron dato, de modo que se pueda juzgar la cobertura de la suma.

- Entregable: Tabla de demanda por operador con pasajeros y viajes con dato.
- Competencias: agregacion-indicadores, calidad-datos
- Datos: `data/case_1`
- Se corrige:
  - El denominador o la cobertura del indicador está informada.
  - Los viajes cancelados quedan fuera de la demanda.
  - El resultado se puede reproducir con una segunda herramienta.

### Ítem 5 · gd-006-demanda-por-hora (20 min, intermedio)

Calcule la demanda por hora del día a partir de la hora de inicio del viaje. Identifique la hora de mayor demanda y explique por qué la hora de inicio del viaje no equivale a la hora en que subió cada pasajero.

- Entregable: Tabla y gráfico de demanda por hora, con la limitación declarada.
- Competencias: fechas-horarios, agregacion-indicadores
- Datos: `data/case_1`
- Se corrige:
  - La agrupación horaria cubre las 24 horas sin huecos.
  - La limitación del supuesto está escrita en el entregable.
  - El total por hora coincide con el total general.

### Ítem 6 · gd-009-excel-verificable (45 min, intermedio)

Reproduzca en Excel la demanda por operador y el recuento de viajes realizados por recorrido, usando fórmulas o tablas dinámicas. El libro debe permitir auditar el cálculo abriendo las celdas, y debe separar las hojas de entrada, de cálculo y de resultado.

- Entregable: Libro .xlsx con hojas de entradas, cálculos y resultados, y un gráfico rotulado.
- Competencias: hojas-de-calculo, agregacion-indicadores
- Datos: `data/case_1`
- Se corrige:
  - Los resultados son fórmulas, no valores pegados.
  - Las entradas no se editan.
  - El gráfico declara unidad y período.

### Ítem 7 · gd-013-informe-y-supuestos (30 min, intermedio)

Redacte un informe de una página con tres hallazgos, los supuestos aplicados y las limitaciones del análisis. Para cada hallazgo indique si es un hecho verificable en los datos, una inferencia o una hipótesis por contrastar.

- Entregable: Informe con hallazgos clasificados, supuestos y limitaciones.
- Competencias: comunicacion-resultados, apoyo-decision
- Datos: `data/case_3`
- Se corrige:
  - Cada hallazgo está clasificado como hecho, inferencia o hipótesis.
  - Los supuestos aplicados aparecen enumerados.
  - Ninguna conclusión atribuye causas que los datos no permiten establecer.

### Ítem 8 · gd-008-cumplimiento (35 min, avanzado)

Calcule el cumplimiento de la programación por recorrido y día, y luego por operador. Conserve los días programados sin viajes realizados. Explique por qué el cumplimiento global no es el promedio de los cumplimientos diarios.

- Entregable: Dos tablas de cumplimiento, por recorrido/día y por operador, con la explicación del denominador.
- Competencias: agregacion-indicadores, cruce-consolidacion
- Datos: `data/case_2`
- Se corrige:
  - Los días programados sin viajes aparecen con cero realizados.
  - El cumplimiento global divide suma por suma, no promedia porcentajes.
  - No se recorta el indicador a 100 % sin declararlo.

### Ítem 9 · gd-010-validacion-cruzada (25 min, avanzado)

Compare los indicadores obtenidos en Excel con los obtenidos en Python o SQL. Construya una tabla de control que muestre, por indicador, el valor de cada herramienta, la diferencia y un veredicto. Explique el origen de cualquier diferencia que no sea cero.

- Entregable: Hoja de control con valores de ambas herramientas, diferencia y veredicto por indicador.
- Competencias: validacion-independiente, reproducibilidad
- Datos: `data/case_1`
- Se corrige:
  - Toda diferencia está cuantificada y explicada.
  - La segunda implementación no reutiliza el resultado de la primera.
  - Lo que no se pudo verificar se informa como tal, no como verificado.

### Ítem 10 · gd-014-prioridades-operacionales (25 min, avanzado)

Identifique los tres recorridos que requieren atención prioritaria. Declare el criterio de priorización, muéstrelo calculado y explique qué información adicional necesitaría para confirmar que la prioridad es correcta.

- Entregable: Tabla de priorización con el criterio explícito y la justificación.
- Competencias: apoyo-decision, agregacion-indicadores
- Datos: `data/case_3`
- Se corrige:
  - El criterio es reproducible, no una apreciación.
  - Se declara qué información falta para confirmar la decisión.
  - El resultado no se presenta como diagnóstico de causa.

## Rúbrica

| Criterio | Puntos | Qué se evalúa |
| --- | --- | --- |
| calidad_y_trazabilidad | 25 | Los defectos están cuantificados y cada exclusión queda registrada con su efecto. |
| transformacion_y_cruces | 20 | Tipos resueltos, cardinalidad controlada y claves desconocidas reportadas. |
| indicadores_correctos | 20 | Denominadores correctos, unidades declaradas y totales que cuadran entre tablas. |
| verificacion_en_hoja_de_calculo | 20 | Los indicadores se reproducen con fórmulas auditables, no con valores pegados. |
| interpretacion_y_supuestos | 10 | Hallazgos clasificados, supuestos explícitos y ninguna causa atribuida sin evidencia. |
| reproducibilidad_y_entrega | 5 | El trabajo se vuelve a ejecutar desde cero y los archivos entregados abren bien. |
| **Total** | **100** | |
