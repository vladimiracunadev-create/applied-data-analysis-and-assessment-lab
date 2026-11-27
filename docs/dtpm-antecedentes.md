# Antecedentes públicos verificados: DTPM y datos abiertos de transporte

> **Alcance de este documento.** Reúne únicamente lo que se **abrió y leyó** en una
> sesión de consulta el **26 de noviembre de 2026**. Lo que no se pudo verificar
> aparece en la sección final como pendiente, no como hecho. Este laboratorio no
> publica material oficial del DTPM ni reproduce instrumentos de evaluación de ningún
> proceso de selección.

## 1. Fuentes verificadas

### 1.1 GTFS vigente

- **Página:** <https://www.dtpm.cl/index.php/gtfs-vigente>
- **Estado al 26-11-2026:** declara «GTFS Vigente desde 14 de noviembre de 2026».
- **Archivo publicado:** `https://www.dtpm.cl/descargas/gtfs/GTFS_20261114_v2.zip`
- **Observación técnica:** el nombre del archivo cambia en cada publicación
  (`GTFS_<AAAAMMDD>[_vN].zip`). Un proceso automatizado debe **leer el enlace de la
  página**, no construir el nombre a partir de una fecha: un nombre construido deja de
  existir en la siguiente publicación.

### 1.2 GTFS históricos

- **Página:** <https://www.dtpm.cl/index.php/programas-de-operaciones/gtfs-historicos>
- **Estado al 26-11-2026:** publica versiones agrupadas por año, desde **2014** hasta
  **2026**, y un documento «Descripción GTFS estático DTPM».
- **Utilidad para el laboratorio:** permite construir análisis longitudinales de la
  red (cambios de recorridos, de frecuencias programadas y de paraderos) con datos
  públicos reales.

### 1.3 Qué es GTFS

La *General Transit Feed Specification* define un formato común para horarios de
transporte público y la información geográfica asociada, de modo que distintas
aplicaciones puedan consumirlos de forma interoperable. La propia página del DTPM lo
describe así.

Tablas principales de un feed GTFS estático, todas en CSV dentro del ZIP:

| Archivo | Contenido | Clave |
| --- | --- | --- |
| `agency.txt` | Operadores del servicio | `agency_id` |
| `routes.txt` | Recorridos | `route_id` |
| `trips.txt` | Expediciones de un recorrido | `trip_id` |
| `stops.txt` | Paraderos, con latitud y longitud | `stop_id` |
| `stop_times.txt` | Horario de cada expedición por paradero | `trip_id` + `stop_sequence` |
| `calendar.txt` | Días de servicio | `service_id` |
| `shapes.txt` | Trazado geográfico | `shape_id` + `shape_pt_sequence` |

**Por qué es un buen ejercicio de gestión de datos.** `stop_times.txt` es una tabla
de varios millones de filas con un grano compuesto, horas que pueden pasar de 24
(`25:10:00` significa la madrugada del día de servicio siguiente, y es un formato que
rompe cualquier conversión ingenua de hora), y claves foráneas hacia cuatro tablas.
Es decir: exactamente el tipo de archivo donde los defectos tratados en este
laboratorio aparecen de verdad.

### 1.4 Manual de diseño de puntos de parada

- **Página:** <https://www.dtpm.cl/descargas/manuales/Manual%20de%20paradas%20DTPM%20(06-03-26)%20alta.pdf>
- **Documento:** «Puntos de Parada · Manual de Diseño», febrero de 2026.
- **Abierto y leído el 26-11-2026.** 12 083 891 bytes,
  sha256 `d6b611483313babd66104523bea3f980e12387bfbf895261a7eebc3fb5cfdc51`.
- **Licencia:** no verificada. El sitio no publica condiciones de uso.
- **Lo que aporta al laboratorio**, citado textualmente de la página 36:

  > «La ubicación de un punto de parada responde a múltiples parámetros donde el
  > distanciamiento entre puntos de parada promedio es de 300 m, que considera un
  > tiempo de caminata de 3 a 5 minutos aproximadamente.»

  Es la única cifra oficial encontrada que asocia una distancia a un tiempo de
  caminata, y por eso ancla el umbral de
  [`cases/cobertura_de_carga`](../cases/cobertura_de_carga/README.md).

- **Lo que NO aporta, y conviene no confundir.** El manual habla del **espaciamiento
  entre paradas**. No fija ningún criterio de distancia a un lugar de carga de la
  tarjeta, y no menciona la carga de la tarjeta en ninguna de sus páginas. Trasladar
  los 300 m de un contexto al otro es una analogía del laboratorio, no una norma del
  organismo, y el caso lo declara así.
- **Otras cifras del documento**, por si sirven: el distanciamiento reducido entre
  paradas divididas es de 100 a 150 m; la línea de detención debe quedar al menos a
  20 m de un cruce; la densidad de usuarios de referencia para dimensionar un refugio
  es de 2 pasajeros por metro cuadrado.

## 2. Qué hace el DTPM, según fuentes públicas consultadas

- El **Directorio de Transporte Público Metropolitano** regula, supervisa y opera la
  red de transporte público de la Región Metropolitana, según una ficha sectorial de
  la agencia de comercio del gobierno de Estados Unidos
  (<https://www.trade.gov/market-intelligence/chile-smart-mobility>).
- Una presentación de 2016 atribuida a la Gerencia de Desarrollo del DTPM trata sobre
  la transformación de datos de GPS y de tarjeta electrónica en información para
  planificar el transporte, incluida la construcción de matrices origen-destino
  (<https://cims3.dc.uba.ar/CIMS3/Gschwender.pdf>).
- Un trabajo del repositorio de la Universidad de Chile sobre usos y gestión de la
  información del sistema señala que el organismo evalúa a las empresas concesionarias
  y toma decisiones de política pública a partir de datos operacionales
  (<https://repositorio.uchile.cl/handle/2250/146129>).

**Lectura para la preparación.** El trabajo de un gestor de datos en este contexto
combina tres cosas: consolidar fuentes heterogéneas (GPS, transacciones de tarjeta,
programación), producir indicadores operacionales comparables entre operadores, y
sostener esos indicadores ante quien los va a usar para evaluar un contrato. Las tres
están cubiertas por el caso `cases/transport` del laboratorio.

## 3. Lo que el laboratorio construyó a partir de esto

| Elemento del laboratorio | Qué toma de los antecedentes |
| --- | --- |
| `data/case_1..3` | Estructura relacional análoga: hechos de viaje + catálogo de recorridos + operadores + programación |
| `docs/diccionario.md` | Diccionario con reglas de tratamiento declaradas, como exige un dato operacional auditado |
| Indicadores del caso | Demanda, duración, puntualidad y cumplimiento de programación, que son las familias de indicadores que aparecen en la literatura consultada |
| Validación cruzada | Recálculo en SQL y en Excel, porque un indicador que evalúa a un tercero tiene que poder defenderse |

**Los datos del laboratorio son sintéticos y con semilla fija.** No reproducen
magnitudes reales de ningún sistema. La estructura es análoga a propósito, para que lo
aprendido se transfiera; los números no lo son.

## 4. Mapa de capacidades de la evaluación y dónde practicarlas

El perfil del cargo contempla Excel y Python con Pandas, o RStudio como alternativa,
con una duración máxima de cuatro horas. El laboratorio cubre cada tema así:

| Tema | Dónde se estudia | Dónde se practica |
| --- | --- | --- |
| Importación y exportación CSV / JSON / Excel | `docs/learning/00-fundamentos/01` | ítem `gd-001`, `gd-015` |
| Limpieza y normalización | `docs/learning/00-fundamentos/02` | ítem `gd-002`, `gd-003` |
| Nulos y duplicados | `docs/learning/00-fundamentos/02` | ítem `gd-001`, `gd-003` |
| Cruce y consolidación | `docs/learning/30-ingenieria/01` | ítem `gd-004` |
| Fechas y horarios | `docs/learning/20-programacion/01` | ítem `gd-002`, `gd-006` |
| Agrupaciones y agregaciones | `docs/learning/20-programacion/01` | ítem `gd-005`, `gd-008` |
| Fórmulas y tablas dinámicas | `docs/learning/20-programacion/02` | ítem `gd-009` |
| Estadística descriptiva | `docs/learning/10-matematicas/01` | ítem `gd-007` |
| Indicadores operacionales | `docs/learning/40-analisis/01` | ítem `gd-005`, `gd-008` |
| Análisis de demanda | `docs/learning/40-analisis/01` | ítem `gd-005`, `gd-006` |
| Visualización | `docs/learning/40-analisis/01` | ítem `gd-012` |
| Interpretación y justificación | `docs/learning/40-analisis/01` | ítem `gd-013`, `gd-014` |
| Declaración de supuestos | `docs/learning/00-fundamentos/02` | ítem `gd-013` |
| Validación de entregables | `docs/learning/30-ingenieria/01` | ítem `gd-010` |
| Equivalencias SQL / Pandas / Polars / Excel / R | `docs/equivalencias.md` | ítem `gd-011` |

## 5. Entornos alternativos

| Entorno | Para qué sirve | Qué tener listo antes |
| --- | --- | --- |
| Local con `uv` | Entorno principal | `uv sync`; comprobar que `uv run pytest` pasa |
| JupyterLab | Exploración y entrega en notebook | `uv run jupyter lab`; abrir `notebooks/01_inicio.ipynb` |
| Google Colab | Respaldo si falla el equipo local | Abrir el enlace del cuaderno: clona el repo, instala Pandas/Polars y obtiene las fuentes; ver `docs/ejecucion-portable.md` |
| Google Sheets | Respaldo de Excel | Importar los CSV con **Archivo → Importar**, separador coma, UTF-8. `BUSCARX` y `SUMAR.SI.CONJUNTO` existen; las tablas dinámicas se llaman «tablas dinámicas» y están en **Insertar** |
| RStudio | Alternativa declarada en el perfil del cargo | Abrir `cuaderno/solucion.Rmd` o ejecutar `solucion.R`; requiere `readr`, `dplyr` y `ggplot2` |

**Advertencia práctica sobre Google Sheets.** El separador decimal y el de argumentos
dependen de la configuración regional del documento, no del equipo. Conviene verificarlo
con una fórmula trivial antes de construir nada.

## 6. Pendientes y límites de esta investigación

Lo siguiente **no** se verificó y por lo tanto no se afirma:

1. **Términos de licencia y condiciones de reutilización** del GTFS del DTPM. La
   página de descarga se abrió; sus términos de uso no se leyeron. Antes de
   redistribuir el dato hay que revisarlos.
2. **Existencia de una API pública** de posición de buses en tiempo real o de
   transacciones de tarjeta. No se encontró en esta consulta.
3. **Datasets del DTPM en el portal de datos abiertos del Gobierno de Chile.** El
   portal `datos.gob.cl` devolvió un error HTTP 405 a la consulta de búsqueda
   realizada, de modo que no se pudo revisar su catálogo.
4. **Contenido, formato o instrumentos de la evaluación técnica del cargo.** No se
   buscó y no se buscará: el laboratorio prepara competencias, no reproduce pruebas.
5. **Volúmenes, magnitudes o indicadores reales del sistema.** Los datos del
   laboratorio son sintéticos y no deben citarse como cifras del transporte público de
   Santiago.

## 7. Reglas de uso de este material

- Las simulaciones del laboratorio son **material de entrenamiento**. Cada enunciado
  generado lo declara en su encabezado.
- Cada proceso de selección fija sus propias reglas sobre el uso de asistentes de
  inteligencia artificial. El laboratorio **no** autoriza su uso durante una
  evaluación: la configuración de cada simulación declara explícitamente
  `permite_ia: false`, y quien practica debe respetar la regla del proceso real.
- No publique en este repositorio datos de postulaciones, correos, credenciales ni
  material entregado por un tercero.
