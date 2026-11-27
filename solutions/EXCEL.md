# Solución guiada de Excel

Esta es una de cinco representaciones del mismo contrato. Pandas, Polars, R base y SQL
parten de los CSV crudos; Excel conserva fórmulas vivas y una hoja de control. Las
implementaciones ejecutables están en `solutions/` y su acuerdo se verifica en CI.
Trabaje sobre una copia de entradas.xlsx o importe los CSV. Quite duplicados exactos en Viajes; cree columnas operador, meta, válido_demanda, duración y realizado. BUSCARX permite recuperar operador_id desde Recorridos y operador desde Operadores. Marque claves desconocidas. Marque demanda válida si estado=REALIZADO, clave conocida, pasajeros numérico y >=0. En tabla dinámica filtre demanda válida y agrupe operador con suma de pasajeros. En otra tabla dinámica filtre realizados con clave conocida y cuente viaje_id por recorrido. Inserte gráfico de columnas de demanda. Compare con los CSV de referencia. Para cumplimiento, use CONTAR.SI.CONJUNTO con recorrido, día y estado; divida por programados si es >0. No promedie porcentajes diarios para obtener el porcentaje global: divida sumas. Documente diferencias. El libro producido por Python no sustituye la demostración de fórmulas y tablas dinámicas de Excel.
