# Diccionario de datos sintéticos
- viajes: viaje_id (identificador único esperado), recorrido_id (clave foránea), inicio/fin (fecha-hora local sin zona), pasajeros (conteo por viaje), estado (REALIZADO o CANCELADO).
- recorridos: recorrido_id único, operador_id, meta_min (duración objetivo en minutos).
- operadores: operador_id único, operador (nombre ficticio).
- programacion: recorrido_id + dia_octubre (clave compuesta), viajes_programados (cantidad planificada).
## Reglas de referencia
Eliminar duplicados exactos antes de contar. Excluir claves desconocidas de indicadores por recorrido y reportarlas. Viaje realizado con pasajeros nulos o negativos: conservar para indicadores operacionales, excluir de sumas/promedios de pasajeros y reportar cobertura. Cancelados: excluir de duración y demanda. Duraciones válidas: fin >= inicio. Puntualidad pedagógica: duración <= meta (no es el indicador oficial DTPM). Cumplimiento = realizados / programados; no limitar a 100%. No imputar valores sin justificar. Los días sin viajes se incluyen en la programación.
