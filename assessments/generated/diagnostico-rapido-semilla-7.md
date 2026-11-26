# Evaluación diagnóstica — fundamentos de manejo de datos

> **Simulación de entrenamiento.** No es una prueba oficial de ninguna institución ni reproduce instrumentos reales de selección.

- Cargo de referencia: Analista de datos
- Especialidad: Fundamentos de manejo de datos · Industria: Genérica
- Nivel declarado: intermedio
- Tiempo: 85 de 90 minutos presupuestados
- Herramientas admitidas: Excel, Python, Pandas
- Uso de asistentes de IA: no permitido
- Semilla de generación: 7 (reproducible)

## Entregables

1. Tabla de calidad con defectos cuantificados.
2. Tabla de indicadores con unidad y denominador declarados.

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

### Ítem 3 · gd-004-cruce-con-cardinalidad (30 min, intermedio)

Cruce los viajes con el catálogo de recorridos y con el de operadores. Compruebe que el número de filas no aumenta después del cruce y cuantifique las claves que no encontraron correspondencia. Explique qué tipo de cruce usó y por qué.

- Entregable: Dataset consolidado más una tabla de auditoría del cruce.
- Competencias: cruce-consolidacion, calidad-datos
- Datos: `data/case_1`
- Se corrige:
  - Se verifica la cardinalidad antes y después del cruce.
  - Las claves desconocidas se reportan, no se descartan en silencio.
  - La elección entre cruce por la izquierda e interno está justificada.

### Ítem 4 · gd-006-demanda-por-hora (20 min, intermedio)

Calcule la demanda por hora del día a partir de la hora de inicio del viaje. Identifique la hora de mayor demanda y explique por qué la hora de inicio del viaje no equivale a la hora en que subió cada pasajero.

- Entregable: Tabla y gráfico de demanda por hora, con la limitación declarada.
- Competencias: fechas-horarios, agregacion-indicadores
- Datos: `data/case_1`
- Se corrige:
  - La agrupación horaria cubre las 24 horas sin huecos.
  - La limitación del supuesto está escrita en el entregable.
  - El total por hora coincide con el total general.

## Rúbrica

| Criterio | Puntos | Qué se evalúa |
| --- | --- | --- |
| calidad_de_datos | 20 | El estado de los datos se mide antes de analizar. |
| analisis | 30 | Los indicadores responden la pregunta planteada. |
| visualizacion | 20 | Gráficos con unidad, período, fuente y escala honesta. |
| comunicacion | 20 | El informe separa hecho, inferencia e hipótesis. |
| limitaciones | 10 | Las limitaciones y la incertidumbre están declaradas. |
| **Total** | **100** | |
