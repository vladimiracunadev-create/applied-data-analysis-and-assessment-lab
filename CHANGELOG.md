# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
Este proyecto usa [versionado semántico](https://semver.org/lang/es/).

La **primera versión oficial es la 0.1.0**. Los prototipos anteriores no se consideran
releases y no se publican como tales.

## [0.9.1] — 2026-11-26

### Corregido

- **`tabla_de_detectores` de P10 leía los cinco Excel por su cuenta.** Una función de
  informe con una lectura de disco escondida: llamaba a `detectar_contra_comuna()`, que
  llama a `consolidar()`. Pasaba en una máquina con los archivos descargados y **falló
  en integración continua** en los tres Python de la matriz y en el canario. Ahora
  recibe la tabla del detector 3 como argumento, que `analizar` ya calculaba, de modo
  que además deja de calcularla dos veces.

  La prueba que debía cubrirlo tenía el mismo defecto heredado: se le pasa ahora una
  tabla sintética, y se agregó una que comprueba el caso sin hallazgos.

### Agregado

- **La comprobación que faltaba en CONTRIBUTING**: cómo correr la suite sin los archivos
  descargados, que es como corre en integración continua. Verificado que las 702
  pruebas pasan con `data/original/` apartada. La corrección cuando falla es recibir la
  tabla como argumento, no marcar la prueba como omitida.

## [0.9.0] — 2026-11-26

### Agregado

- **P02 y P04 resueltos**, los dos dentro de
  [`cases/bip_lugares_carga`](cases/bip_lugares_carga/README.md), que es el caso que
  tiene esos datos. No se creó un caso nuevo para no duplicar la lectura de los cinco
  Excel, igual que P05 se resolvió dentro de `carga_nocturna` y P03 dentro de
  `correspondencia_metro`.

- **`lab/keys.py`**, módulo nuevo del núcleo: contesta la primera pregunta de cualquier
  cruce, que casi nunca tiene respuesta escrita. `key_report` diagnostica cada columna
  —nulos, repetidos y **por qué** no es clave, porque las dos causas piden acciones
  distintas—; `candidate_keys` busca de forma exhaustiva las combinaciones **mínimas**
  que identifican una fila; y `surrogate_key` construye un identificador determinista
  sobre los campos que se declaren como identidad, con comprobación de colisiones.

- **`lab.textual.merge_audit`**: por cada clave normalizada, las formas crudas que
  absorbió. Es la dirección del error que ninguna métrica de calidad mide.

### Lo que P02 encontró

- **Ninguna columna del consolidado identifica una fila.** `direccion` tiene 9
  repetidos, `norte` 91, `este` 108 y `codigo` 136. Y `nombre` falla por **las dos**
  causas a la vez —36 nulos y 98 repetidos—, de modo que ni completándolo serviría.

- **Ni `fuente + codigo` identifica una fila**: 136 filas lo comparten. El enunciado de
  P02 proponía «una clave compuesta, o una clave nueva con el origen del archivo», y la
  segunda mitad de esa frase no resuelve nada. El enunciado quedó corregido en el mapa
  de problemas.

- **Hay tres claves candidatas mínimas y ninguna sirve de identificador**:
  `codigo + direccion`, `codigo + este` y `codigo + norte`. La segunda es la lección:
  es perfectamente única hoy, y P10 demostró que varias coordenadas de este archivo
  están equivocadas por kilómetros. El día en que el publicador corrija la de Santa
  Lucía, esa fila cambiará de identidad y aparecerá como un lugar nuevo.

  > Una clave que cambia cuando se corrige un error no es una clave: es un número de
  > serie del error.

- **La salida es una clave subrogada** sobre la identidad declarada
  `fuente + codigo + direccion`: 1 928 identificadores distintos, sin colisiones. Su
  ventaja sobre el número de fila —que es lo que P08, P09 y P10 tuvieron que usar por no
  haber nada mejor— es que no depende de la ejecución. Su límite queda dicho: hereda la
  inestabilidad de `direccion`, y la solución real es que la fuente publique un
  identificador y lo mantenga.

### Lo que P04 encontró, y es más modesto de lo esperado

- **La normalización fusiona seis veces en todo el archivo.** Cero en `comuna` —46
  valores crudos y 46 normalizados, de modo que el ejemplo clásico no gana nada—, una en
  `entidad` y cinco en `direccion`. El riesgo de no normalizar era concreto y pequeño.

- **Las seis fusiones se revisaron una por una y son correctas**: mayúsculas, tildes, un
  apóstrofo escrito como acento grave y un espacio doble. Y se puede afirmar **porque se
  leyeron**, no porque el recuento pareciera razonable. Para eso existe `merge_audit`.

- **La expansión de abreviaturas no fusiona ninguna de las 1 919 direcciones.**
  `ABREVIATURAS` declara trece equivalencias, está implementada y probada, y sobre estos
  datos no hace nada: las cinco fusiones de `direccion` las produce el resto de la
  normalización. La capacidad no sobra —cuesta nada y protege de un archivo donde haga
  falta— pero atribuirle un mérito aquí sería falso, y ahora está medido aparte.

- **Normalizar tiene dos direcciones de error y solo una se nota.** Dejar separado lo
  que es igual parte un total y salta a la vista. Juntar lo que es distinto produce un
  grupo menos con un total mayor, y es perfectamente verosímil. La expansión de
  abreviaturas es la única transformación que puede hacerlo, porque reemplaza por
  significado y no por forma.

### Corregido

- **El README de P01 decía «tres entidades, no cinco variantes»** donde el texto crudo
  trae cuatro valores y la normalización deja tres. Una fusión, no dos. La cifra
  inflaba el mérito de la normalización, que es justamente lo que esta versión mide.

- **El contrato de `analizar()` en las pruebas de P01** se actualizó a las siete tablas
  nuevas. La prueba existía para fijar ese contrato y funcionó: falló al cambiarlo.

### Agregado al núcleo y a las pruebas

- **Dos registros nuevos en la base de conocimiento**, que pasa de 40 a 42:
  `clave-candidata-no-es-identificador` y `normalizar-tiene-dos-direcciones`.

- **42 pruebas nuevas** (`tests/test_keys.py`, más las de `merge_audit` en
  `tests/test_textual.py` y las de P02 y P04 en `tests/test_bip.py`). La suite pasa de
  659 a **701**.

### Límites declarados

- **La estabilidad de la clave subrogada entre publicaciones no se pudo verificar**:
  solo hay una descarga de los archivos. Queda declarado como no verificado en lugar de
  suponerlo.
- **La identidad declarada incluye un campo de texto libre.** Es la menos mala de las
  opciones disponibles, no una buena.

## [0.8.0] — 2026-11-26

### Agregado

- **P10 resuelto: `cases/correspondencia_metro`.** Dos archivos públicos describen la
  misma realidad —las estaciones de Metro de Santiago— con identificadores distintos y
  sin ningún campo en común: el feed GTFS trae 126 estaciones y el Excel de bip!, 143
  filas. La respuesta a la pregunta es cómoda: las **126** estaciones tienen al menos
  una parada de bus a 200 m —el 100 %—, con una mediana de **13 servicios** distintos,
  P90 de 34 y máximo de **55** en Santa Lucía.

- **El grano, escrito como identidad.** 126 contra 143 no es un problema de
  completitud: una fuente tiene una fila por estación y la otra una por estación y
  línea. `126 − 17 combinaciones + 34 filas de desdoble = 143`. El GTFS delata su grano
  con identificadores compuestos (`AN-NA`, `BA-BQ`); el Excel, con la línea pegada al
  **texto del nombre** (`SAN PABLO L1`), porque su campo `codigo` vale la línea y no
  identifica nada. Quitado el sufijo quedan 126 estaciones, de las cuales **125
  coinciden por nombre normalizado**.

- **Dos criterios de emparejamiento independientes.** Nombre y proximidad, calculados
  por separado y comparados entre sí: coinciden en 113 de 126, y las 13 discrepancias
  son exactamente donde hay algo que explicar. Un cruce solo por nombre perdería una
  estación sin avisar (`Presidente Pedro Aguirre Cerda` contra `PEDRO AGUIRRE CERDA`,
  que están a 1,4 m); uno solo por proximidad aceptaría en silencio pares equivocados.

- **P03 resuelto de paso**, y ampliado. Pedía la validación cruzada de coordenadas, que
  P01 ya hacía comparando las dos representaciones de cada fila. Aquí pasa a ser
  **cuatro detectores, cada uno con su punto ciego declarado y medido**.

- **Cinco registros nuevos en la base de conocimiento**, que pasa de 35 a 40:
  `grano-antes-de-cruzar`, `punto-ciego-del-control`, `agregado-que-suaviza`,
  `dos-afirmaciones-de-la-misma-fila` y `que-fuente-provee-el-campo`.

- **31 pruebas nuevas** (`tests/test_correspondencia_metro.py`), sobre un inventario
  sintético de cuatro estaciones con todas las distancias calculables a mano. La suite
  pasa de 628 a **659**.

### Hallazgo sobre el propio laboratorio

- **La validación de coordenadas de P01 tenía un punto ciego medible, y ahora está
  medido.** Comparar las dos representaciones de una fila —UTM contra latitud/longitud—
  encuentra errores de conversión y de digitación de una de las dos, y **no puede ver un
  error que afecte a las dos por igual**. De las 143 filas de Metro, **ninguna** quedó
  marcada como sospechosa. Y once estaciones están a más de 500 m de donde el GTFS las
  pone, hasta 13,1 km.

  Lo que importa del hallazgo: **tres de los cuatro detectores no necesitan ninguna
  fuente externa**. El archivo podía delatar sus propios errores comparando las filas
  hermanas de una misma estación —Plaza de Armas tiene dos, separadas **26,2 km**— y
  comparando cada coordenada con la comuna que la propia fila declara —Santa Lucía está
  a 12,0 km de la mediana de su comuna—. Nadie le hizo esas preguntas.

  En los dos casos la **dirección postal del propio Excel** coincide con la posición del
  GTFS y no con su propia coordenada. Eso es evidencia de dónde está el error, y queda
  declarado como evidencia y no como prueba: no se afirma que el GTFS tenga razón.

### Corregido

- **Reducir el grano por mediana escondía la mitad del error.** Para comparar las filas
  de bip! con el GTFS hay que llevarlas al grano de estación, y la mediana de las dos
  filas de Plaza de Armas —separadas 26,2 km— cae a 13,1 km de cada una, en un punto
  donde no hay ninguna estación. El desvío aparente se reducía a la **mitad exacta**. El
  caso publica ahora tres columnas en lugar de una: el desvío con el agregado, el desvío
  de la peor fila, y la dispersión interna, que es lo que el agregado reemplazó.
  Registrado en `agregado-que-suaviza`.

### Declarado como medido

- **Qué fuente provee la coordenada decide el 38,4 % del informe.** Calculada con las
  coordenadas de bip! en lugar de las del GTFS, la correspondencia de bus cambia en **48
  de 125 estaciones**, el total de servicios baja un 9 % y **tres estaciones aparecerían
  sin ninguna parada de bus cerca** cuando sí la tienen. Es una decisión metodológica que
  casi nunca se declara, porque las dos fuentes son oficiales y ninguna se presenta como
  aproximada.

- **El detector de coherencia contra la comuna declarada es una señal, no un veredicto.**
  A 3 km marca 227 locales, que son demasiados para ser todos errores en comunas
  extensas; a 10 km marca 8, de los cuales 3 son estaciones con error verificado. Se
  publica la curva completa de umbrales en lugar de esconder la elección en una
  constante. Usa la mediana y no el promedio: con una fila a 26 km, un promedio arrastra
  la referencia y el detector se ciega contra sí mismo.

### Límites declarados

- **No se demuestra que el GTFS tenga razón**, solo que las dos fuentes discrepan y que
  la evidencia interna del Excel apunta al GTFS en los casos inspeccionados.
- **La correspondencia es geométrica**: no considera de qué lado de la avenida está el
  acceso, si hay cruce semaforizado, ni si la combinación está habilitada
  tarifariamente.
- **El radio de 200 m lo fija el enunciado del problema**, no una norma publicada, y
  describe otra cosa que los 300 m de P08.
- **Faltan estaciones en las dos fuentes**: la Línea 7 y las extensiones en construcción
  no aparecen en ninguna.

## [0.7.0] — 2026-11-26

### Agregado

- **P09 resuelto: `cases/carga_nocturna`.** Donde hay servicio de buses de madrugada,
  ¿hay dónde cargar la tarjeta? El servicio nocturno existe y no es marginal: **367 251
  llegadas** en **10 520 paradas**, el 84,2 % de la red, con una mediana de 23 llegadas
  por parada en las cinco horas de la ventana.

  La respuesta es **cero**: ninguna de esas paradas tiene a 300 m un local que declare
  abrir en la madrugada, y **ninguno de los 1 927 locales abiertos** lo declara —el más
  tardío cierra a las 23:00—. Pero la cifra sola miente por omisión. El reparto:
  4 225 paradas (40,2 %) sin ningún local cerca, 759 (7,2 %) con locales cerca todos
  verificados cerrados, y **5 536 (52,6 %) indeterminadas**.

  De modo que el resultado no es un número sino un **intervalo: entre 0,0 % y 52,6 %**.
  El ancho —52,6 puntos— no lo produce la red ni la geografía: lo produce una columna
  vacía.

- **`lab/schedules.py`**, módulo nuevo del núcleo: interpreta horarios de atención
  escritos en texto libre. La regla que lo gobierna es que **lo que no se entiende es
  desconocido, nunca «cerrado»**, y por eso `is_open` tiene tres respuestas —`True`,
  `False` y `None`— y el `None` se propaga hasta el informe. Sobre el archivo real
  interpreta los 348 valores con horario, que son solo **10 textos distintos**, incluido
  uno con saltos de línea dentro de la celda. No resuelve festivos: recibe el indicador
  y no lo averigua, declarado en el docstring.

- **P05 resuelto de paso.** Pedía interpretar los horarios escritos en texto libre, que
  es exactamente lo que P09 necesitaba. Los diez formatos del archivo quedan fijados
  como caso de prueba: si el publicador agrega un local nocturno, la prueba cae, y debe
  caer, porque la conclusión de P09 dejaría de ser válida.

- **El hallazgo de gobernanza, que es el resultado que vale.** El campo
  `horario referencial` está completo al **100 % en cuatro de los cinco archivos y al
  0 % en el quinto**, que es el que tiene 1 579 de los 1 927 locales. Un vacío uniforme
  es un problema de captura; concentrado en un archivo, es una decisión de publicación.
  Y la consecuencia está medida: **1 546 de esos locales están a menos de 300 m de una
  parada con servicio nocturno**, de modo que completar esos registros —el 97,9 % de los
  que faltan— vuelve contestable el 52,6 % de la red nocturna. Eso es un pedido
  priorizado al publicador, no una queja.

- **Cinco registros nuevos en la base de conocimiento**, que pasa de 30 a 35:
  `tres-respuestas-no-dos`, `intervalo-en-vez-de-cifra`, `vacio-concentrado`,
  `atajo-verosimil` y `progresion-sin-expandir`.

- **84 pruebas nuevas** (`tests/test_schedules.py` y `tests/test_carga_nocturna.py`),
  sobre un feed sintético con aritmética temporal calculable a mano. La suite pasa de
  544 a **628** y sigue corriendo sin descargar ningún dato.

### Corregido

- **`lab.schedules` leía `pd.NA` como si fuera texto.** La comprobación de nulos era
  `isinstance(valor, float) and pd.isna(valor)`, y `pd.NA` —que es lo que trae una
  columna de tipo `string`— no es un `float`. Pasaba de largo, se convertía en la cadena
  `«<NA>»` y el informe de calidad decía «no se reconoce ningún rango de horas» en lugar
  de «sin dato». Eran los 1 579 registros donde está el hallazgo del caso: el motivo
  equivocado justamente en la fila que importa. Las dos causas piden acciones distintas
  —una se completa, la otra se corrige—, de modo que confundirlas no es cosmético.

### Declarado como medido, no como supuesto

- **El atajo que daba una cifra verosímil y falsa.** Filtrar `arrival_time` entre
  `00:00:00` y `04:59:59` devuelve 851 773 filas y **12 201 paradas** donde hay 10 520.
  El 100 % de esas filas son de expediciones de frecuencia, cuyo `arrival_time` es un
  desplazamiento desde el inicio del viaje y no una hora: el atajo no está midiendo
  horas en absoluto. Y sobreestima apenas un **16 %**, lo bastante poco para que nada
  parezca roto. El caso implementa el atajo junto al cálculo correcto y publica la
  comparación.

- **Las 00:00–05:00 de reloj son dos intervalos de segundos de servicio**, `[0, 18 000)`
  y `[86 400, 104 400)`, porque un bus que sale a las 23:40 llega a sus paradas finales
  pasada la medianoche. **1 490 paradas** tienen servicio nocturno únicamente por esa
  segunda vía.

- **El conteo se hace sin expandir nada.** Las llegadas de una ventana de frecuencia a
  una parada forman una progresión aritmética; contar cuántas caen en un intervalo son
  dos techos acotados y una resta. Expandir las 142 366 salidas contra 1,1 millones de
  filas de `stop_times` produciría cientos de millones de filas para responder una
  pregunta de sí o no por parada.

### Límites declarados

- **La ventana de 00:00 a 05:00 es una elección del caso.** No se encontró ninguna
  definición oficial de «servicio nocturno» para la red.
- **El horario, donde existe, es de cadena y no de local**: diez textos para 348
  registros, 311 de ellos con solo dos. El campo describe la política de quien agrupa
  los locales, y el propio archivo lo llama «referencial».
- **El pliegue entre el día de servicio y el día del calendario no se resuelve**: una
  llegada a las 24:30 de un viernes de servicio ocurre un sábado. El caso lo evita
  preguntando por el día más favorable de los siete, lo que da una cota superior. Como
  ningún local abre ningún día, aquí no cambia nada; con otros datos cambiaría, y queda
  dicho.

## [0.6.0] — 2026-11-26

### Agregado

- **P08 resuelto en parte: `cases/cobertura_de_carga`.** Distancia de cada una de las
  12 497 paradas de embarque del GTFS al más cercano de los 1 927 lugares de carga
  bip! abiertos. Es el primer caso del laboratorio con un **cruce sin clave
  compartida**: las dos fuentes no comparten ningún campo, de modo que el criterio de
  emparejamiento hay que construirlo, y construirlo trae cuatro decisiones que mueven
  la respuesta plausible entre el 39 % y el 81 % sin que ningún dato cambie.

  Resultado central: **59,29 %** de las paradas tiene un local a 300 m o menos en
  línea recta; con un factor de rodeo de 1,3, el **46,02 %**. Mediana 249,6 m, P90
  671,0 m. Catorce tablas de resultado versionadas.

- **Sesgo de la euclídea sobre grados, medido.** A la latitud de Santiago el atajo de
  multiplicar la distancia euclídea en grados por 111,32 km/grado sobreestima la
  componente este-oeste un 20 %. Sobre las 12 497 paradas: error mediano del +9,41 %,
  **cero subestimaciones**, 574 paradas que cambian de clase y 814 que reciben otro
  local como el más cercano. Que el error tenga eje, y no magnitud aleatoria, es lo
  que lo convierte en un sesgo que no se cancela al promediar.

- **Umbral con cita y con su advertencia.** Los 300 m salen del manual de diseño de
  paradas del DTPM (febrero de 2026, p. 36), que asocia esa distancia a una caminata
  de 3 a 5 minutos. El manual lo dice del **espaciamiento entre paradas** y no
  menciona la carga de la tarjeta: el traslado es una analogía y queda declarado como
  tal, con la cobertura informada a seis umbrales. El documento se agregó a
  `docs/dtpm-antecedentes.md` con su SHA-256 y su licencia no verificada.

- **Cinco registros nuevos en la base de conocimiento**, que pasa de 25 a 30:
  `cruce-sin-clave`, `sesgo-con-eje`, `clave-falla-al-volver`, `unidad-de-la-decision`
  y `cambiar-la-pregunta`.

- **25 pruebas nuevas** (`tests/test_cobertura_de_carga.py`), sobre una geometría
  sintética con distancias exactas derivadas de `lab.geo.grados_por_km`. La suite pasa
  de 519 a **544** y sigue corriendo sin descargar ningún dato.

### Corregido

- **`lab.geo.nearest_point` devolvía un identificador que no identificaba.** Pedirle
  `codigo` como identificador del destino producía dos fallas: una ruidosa
  (`InvalidIndexError` al unir el resultado, porque 143 estaciones de Metro comparten
  siete códigos) y una **silenciosa**, que es la grave. Al comparar dos métodos de
  cálculo contando por código, 814 paradas que cambiaban de local se contaban como
  807, y 1 673 como 1 657: dos estaciones distintas de la misma línea colapsaban en
  una. El caso devuelve la posición de fila, y hay una prueba con dos locales de igual
  código para que no vuelva a pasar. Registrado en `clave-falla-al-volver`.

### Cambiado

- **La invariante «ningún caso importa de otro» pasó a «ningún caso importa de otro
  sin declararlo».** `cobertura_de_carga` reutiliza la consolidación de los cinco
  Excel de `bip_lugares_carga` en lugar de repetir doscientas líneas de armonización
  de esquemas y validación de coordenadas; duplicarlas enseñaría que el trabajo de
  calidad no se amortiza. La prueba de coherencia ahora exige que la dependencia
  figure en `implementaciones` del `case.json`, que es más estricto que prohibirla:
  una dependencia por descuido sigue fallando.

### Declarado como no resuelto

- **La segunda mitad de P08 no se puede contestar con estos datos.** Las paradas del
  GTFS no traen comuna, y atribuirle a cada parada la comuna de su local más cercano
  produce un proxy sesgado por construcción, que falla precisamente donde la cobertura
  es peor: Paine recibe cinco paradas con una mediana de 18,9 km. El caso publica esa
  medición y ofrece como sustituto una rejilla geográfica, que no necesita límites
  administrativos. `docs/problemas-de-la-instancia.md` pasa de 7 a 10 preguntas
  declaradas como incontestables.

- **No se puede saber si el local está abierto cuando pasa el pasajero.** El horario
  referencial está en el 18,06 % de los locales: de las 7 409 paradas cubiertas a
  300 m, **5 701** lo están por un local de horario desconocido. Toda cifra de
  cobertura del caso supone disponibilidad permanente, y lo dice.

- **No existe un factor de rodeo peatonal canónico que citar.** Se buscó; los valores
  publicados varían por ciudad y por método de medición. En lugar de adoptar uno sin
  respaldo, el caso informa la curva completa de 1,0 a 1,5.

## [0.5.1] — 2026-11-26

### Corregido

- **La integración continua instalaba dependencias distintas de las probadas.** El paso
  usaba `uv sync`, que vuelve a resolver cuando cambia el `pyproject.toml` —y cambia en
  cada subida de versión—, de modo que CI traía versiones más nuevas que `uv.lock`. Dos
  veces falló por una obsolescencia de pandas que nadie había visto en local. Ahora los
  trabajos de prueba usan `uv sync --locked`, que **falla si el lockfile está
  desincronizado** en lugar de resolver en silencio.
- **`lab.calendars` usaba `DatetimeIndex.weekday`**, obsoleto en pandas 4, que el filtro
  de advertencias del proyecto convierte en error. Reemplazado por `day_of_week`.

### Agregado

- **Canario de dependencias** en integración continua: un trabajo que resuelve las
  versiones más nuevas compatibles y corre la suite. No bloquea la publicación
  (`continue-on-error`), pero avisa de una obsolescencia antes de que rompa algo. Es el
  mecanismo que faltaba para que la detección temprana no dependiera de que el
  lockfile quedara desactualizado por accidente.

### Cambiado

- **README reescrito.** Antes abría con una definición abstracta del laboratorio y no
  decía qué problema resuelve. Ahora abre con el problema concreto —datos ajenos con
  encabezados corridos, claves que no son claves, horas que ninguna librería acepta,
  indicadores con reglas en una nota al pie—, una tabla de **por dónde entrar** según
  lo que uno necesite, y los seis casos con **lo que cada uno encontró** en lugar de
  una lista de características.
- **Nuevo [índice de la documentación](docs/README.md)**, organizado por lo que el
  lector viene a hacer: prepararse para una evaluación, resolver un problema, aprender,
  o entender el estado real del repositorio. Incluye las cuatro convenciones que
  explican por qué algunos párrafos dicen «no se verificó» en lugar de callarlo.

## [0.5.0] — 2026-11-26

Resuelve el problema **P11**: reconstruir el calendario de medición de un indicador
oficial y auditar sus reglas. Es el caso que más se parece al trabajo real de un gestor
de datos del sector público.

### Agregado

- **Instancia `cases/calendario_medicion`.** Toma las ocho reglas de exclusión del
  índice de variación de tiempos de viaje, publicadas en un documento de DIPRES, y
  reconstruye el denominador del indicador. Resultado para 2026: de **261** días
  laborales quedan **164** elegibles (62,84 %) y **78 medibles** tras cruzar con los
  meses de medición.
- **`lab.calendars`: calendarios por reglas.** Cada regla es un objeto con su fuente
  citada. Mide la **exclusión exclusiva** de cada una —cuántos días solo ella
  excluye— y la matriz de solapamiento. Incluye el cálculo del Domingo de Pascua con
  el algoritmo gregoriano anónimo, validado en las pruebas contra diez fechas
  publicadas entre 1900 y 2027 y contra sus propiedades en doscientos años.
- **Fuente de feriados en el catálogo**, declarada explícitamente como **tercero, no
  oficial**: la API del gobierno no resolvía. El listado se descarga una vez, se
  valida y se **versiona** dentro del caso, porque depender de un servicio de tercero
  en cada ejecución haría el caso irreproducible.
- Tres registros de conocimiento: `denominador-es-una-decision`, `regla-redundante` y
  `supuesto-medido`.

### Los tres hallazgos

**1. La mitad de las reglas no cambia el denominador.** Al medir cuántos días medibles
recuperaría el quitar cada regla:

| Regla | Días medibles que quita |
| --- | --- |
| fin de semana | 25 |
| semana de fiestas patrias | 4 |
| días 28 y 29 | 2 |
| 11 de septiembre | 1 |
| vacaciones de invierno | **0** |
| meses completos (enero, febrero, diciembre) | **0** |
| feriados | **0** |
| día del joven combatiente | **0** |

Excluir enero, febrero y diciembre descarta 90 días del año y **ninguno** de los que se
miden, porque la medición ocurre en marzo, junio, septiembre y noviembre.

**2. Hay dos clases de redundancia, y confundirlas cuesta.** Comparando 2024 a 2027:

| Clasificación | Reglas |
| --- | --- |
| Efectiva (quita días todos los años) | fin de semana, días 28 y 29, semana de fiestas patrias |
| **Redundante accidental** | feriados (cero en 2026, tres en 2027), 11 de septiembre (cero en 2027) |
| **Redundante estructural** | meses completos, vacaciones de invierno, día del joven combatiente |

Quitar una estructuralmente redundante no cambia nada nunca; quitar una accidental
funciona este año y falla el siguiente. El «Día del joven combatiente» es el 29 de
marzo y la regla de los días 28 y 29 ya lo descarta: exclusión exclusiva cero.

**3. El denominador cambia entre años.** 70, 74, 78 y 75 días medibles para 2024, 2025,
2026 y 2027: una variación del **11 %** producida solo por cómo cae el calendario. El
valor anual del indicador es el promedio de cuatro mediciones trimestrales, de modo que
comparar dos años compara promedios calculados sobre cantidades distintas de días.

### El supuesto que no se pudo resolver, medido

La metodología dice «vacaciones de invierno (dos semanas, considerando los calendarios
escolares)» **sin fechas**, y el calendario escolar no se obtuvo. En lugar de elegir
unas fechas en silencio, el caso declara el supuesto y mide su efecto: moverlo dentro
de julio no cambia nada, y moverlo a la segunda mitad de junio —que sí es mes de
medición— baja el denominador de 78 a 72 días. Eso convierte una incertidumbre en un
riesgo acotado: hay que conseguir el calendario escolar **solo si** el receso empieza
antes del 1 de julio.

### Validación

- El listado de feriados **no se guarda** si no contiene el Viernes Santo calculado: un
  dato de entrada que no pasa su propia validación no entra.
- La identidad `suma_de_exclusiones − solapamiento = días_excluidos` se comprueba en
  las pruebas.
- El aporte de cada regla se calcula **quitándola y reconstruyendo** el calendario, no
  por diferencia algebraica, que se equivoca con los solapamientos.
- Las pruebas del caso corren **sin red**, y la descarga desde la API de tercero se
  ejerce contra un servidor falso para comprobar que valida antes de guardar.

## [0.4.0] — 2026-11-26

Resuelve el problema **P01** del mapa: consolidar cinco Excel públicos heterogéneos.
Es el primer caso del laboratorio con datos reales **de licencia verificada**, y el que
más se parece a lo que pide una evaluación técnica de cuatro horas con Excel y Pandas.

### Agregado

- **Instancia `cases/bip_lugares_carga`.** Consolida los cinco archivos de lugares de
  carga de la tarjeta bip! publicados por la Subsecretaría de Transporte: 1 928 filas
  en seis hojas, licencia Creative Commons Atribución-NoComercial 2.0 verificada.
  Responde cuántos lugares hay, de qué tipo, en qué comuna y de qué entidad: 1 927
  abiertos, 5 tipos, 46 comunas, 3 entidades, y solo el **18,06 %** con horario
  publicado.
- **`lab.excel`: lectura de planillas desordenadas.** `detect_header_row`,
  `read_messy_sheet`, `read_all_sheets`, `sheet_names` y el informe `SheetReport`. En
  los cinco archivos el encabezado estaba en las filas **7, 9, 13, 10 y 9**: detectarlo
  es más robusto que fijarlo, y si la detección falla el módulo falla en lugar de
  adivinar.
- **`lab.textual`: normalización de texto.** `normalize_key` para agrupar y
  `normalize_label` para mostrar, porque guardar solo la clave convierte `Ñuñoa` en
  `NUNOA` en el informe final. Más `similarity`, `duplicate_candidates` —que propone
  pares para revisión humana, nunca fusiona— y `normalization_report`, que cuantifica
  los grupos espurios que la normalización evita.
- **`lab.geo`: geografía mínima sin dependencias.** `haversine_km`, `utm_to_latlon`
  (transversa de Mercator inversa sobre WGS84), `grados_por_km` y `nearest_point` con
  búsqueda por bloques. Habilita el problema P08 del mapa.
- Cuatro registros de conocimiento: `encabezado-no-esta-en-la-primera-fila`,
  `clave-que-no-es-clave`, `normalizar-antes-de-agrupar` y `dos-coordenadas-un-lugar`.

### Lo que la validación cruzada encontró

El archivo trae la ubicación **dos veces** —UTM y geográficas—, lo que permite validarlo
contra sí mismo sin ninguna fuente externa. La distribución de los 1 928 desvíos es
**bimodal**:

| Desvío | Filas | Qué es |
| --- | --- | --- |
| menos de 5 m | 109 | las dos columnas coinciden |
| 50 a 80 m | 1 779 | desplazamiento sistemático (diferencia de datum) |
| más de 200 m | **3** | **errores de registro: 4 623 m, 10 087 m y 10 272 m** |

Y entre 80 y 200 m, **nada**. Que los dos grupos estén separados por un orden de
magnitud es lo que permite distinguir el problema sistemático del error puntual:
reportar los 1 779 como errores sería un falso positivo masivo, callar los tres una
omisión.

Que 109 filas **no** tengan el desplazamiento es el hallazgo de fondo: si fuera solo
una diferencia de datum, sería uniforme. Las dos columnas no se produjeron con un único
proceso consistente. Es gobernanza de datos, no limpieza: se reporta al publicador.

### Otros hallazgos del caso

- **`CODIGO` no es una clave**, y ni la clave compuesta `archivo + código` lo es: en el
  archivo de Metro el código es la **línea**, de modo que 143 estaciones comparten 7
  códigos.
- **El `horario` cubre el 18,06 %** porque 1 579 locales vienen de un archivo que no
  publica esa columna. No es un campo con nulos: es un campo que esa población no tiene.
- **`FULLCARGA` y `Fullcarga`** convivían en el mismo archivo, creando grupos espurios
  en cualquier `groupby` sobre el texto crudo.

### Corregido

- **`lab.geo.haversine_km` no aceptaba arreglos de NumPy difundidos entre sí**, que es
  justo lo que necesita una búsqueda del punto más cercano por bloques. Lo encontró la
  prueba de `nearest_point`.
- **`scripts/fetch_data.py` guardaba todo con extensión `.zip`.** Un `.xlsx` guardado
  como `.zip` funciona —un xlsx es un zip— pero nadie lo reconoce al abrir la carpeta.
  Ahora la extensión se deriva del tipo de contenido declarado.

### Cambiado

- `docs/roadmap.md` da por cubierta la competencia `gobernanza-datos`, cuyo hallazgo
  central aporta esta instancia, y mantiene pendiente el caso de gobernanza explícita
  (catálogo, propiedad del dato, retención), que este caso no toca.

## [0.3.0] — 2026-11-26

Inventario de lo que **sí se puede resolver** con datos públicos verificados, y las
definiciones oficiales de los indicadores del sector.

### Agregado

- **`docs/problemas-de-la-instancia.md`**: dieciséis problemas con su pregunta exacta,
  los datos que usa cada uno, la tecnología que exige, la trampa que enseña y su
  estado —resuelto, disponible o no se puede—. Incluye una sección de **siete
  preguntas que estos datos no permiten contestar**, con el motivo: no hay demanda, no
  hay GPS, no hay transacciones, no hay límites comunales.
- **`docs/indicadores-oficiales-transporte.md`**: las definiciones oficiales del índice
  de cumplimiento de regularidad (ICR), del de frecuencia (ICF) y del índice de
  variación de tiempos de viaje, con fórmula, grano, fuente y reglas de exclusión,
  citadas textualmente de un documento público de DIPRES (Partida 19, Ministerio de
  Transporte y Telecomunicaciones). Lo relevante: el grano del ICR y del ICF es
  **servicio × sentido × mes**, el denominador son **mediciones** —más de veinte
  millones al año—, el plan de referencia cambia dos veces al año de modo que la serie
  no es comparable sin advertirlo, y el índice de tiempos de viaje declara **siete
  reglas de exclusión** encadenadas, entre ellas descartar enero, febrero y diciembre
  completos y los días 28 y 29 de cada mes.
- **Cinco fuentes nuevas en `lab.sources.CATALOG`**: los lugares de carga de la tarjeta
  bip! publicados por la Subsecretaría de Transporte en el portal de datos abiertos,
  con licencia **Creative Commons Atribución-NoComercial 2.0 verificada**. El catálogo
  ahora distingue fuentes con licencia comprobada de fuentes sin comprobar, y una
  prueba exige que esa distinción exista.

### Por qué esos Excel son mejor material que un dataset sintético

Verificado archivo por archivo: el encabezado está en una fila distinta en cada uno
(7, 9, 13, 10 y 9), los esquemas tienen 9 o 10 columnas, los nombres de columna varían
(`NOMBRE FANTASIA` / `NOMBRE DE FANTASIA ` con espacio final / ausente;
`DIRECCION` / `DIRECCIÓN`), los nombres de hoja varían (`Abiertos`, `Abierto`, `PCMA`),
uno trae una hoja `Cerrados` que no debe entrar en un indicador de cobertura, hay dos
sistemas de coordenadas a la vez, la entidad viene con mayúsculas inconsistentes, los
horarios son texto libre en tres formatos distintos, y el contenido incluye un carácter
que rompe una consola de Windows en cp1252.

### Verificado y no encontrado

Se buscó el documento de la convocatoria del cargo en el sitio del DTPM, en el del
Ministerio de Transportes, en el portal de datos abiertos del Estado y en buscadores.
**No se encontró**, y el sitio del DTPM no tiene sección de concursos. Queda declarado
en `docs/problemas-de-la-instancia.md` para que nadie suponga que el material está
modelado sobre la prueba real.

## [0.2.0] — 2026-11-26

Primera instancia con **datos públicos reales** y el módulo de adquisición que la hace
posible. Define el laboratorio como un recorrido reutilizable para leer datos de
cualquier dominio, no como un programa sobre transporte.

### Agregado

- **`lab.sources`: adquisición de datos con procedencia.** Descarga registrando URL,
  fecha, tamaño, tipo de contenido, huella SHA-256 y licencia en un registro que queda
  junto al dato. `discover_link` resuelve la URL de descarga **leyendo el enlace de la
  página índice**, porque el nombre del archivo publicado cambia en cada versión y un
  nombre construido a mano falla sin aviso. Incluye lectura de tablas desde dentro de
  un ZIP, con y sin bloques, e inventario de lo adquirido.
- **Instancia `cases/gtfs_red_movilidad` con datos reales.** GTFS vigente de la Red
  Metropolitana de Movilidad publicado por el DTPM: 12,8 MB comprimidos, 69,7 MB
  descomprimidos, 1 098 717 filas de horarios, 26 137 expediciones, 18 486 lugares y
  425 recorridos de cuatro operadores. Resuelve «¿cuántas expediciones salen por hora
  en un día laboral?» y documenta las cuatro trampas que contiene:
  - el **77,5 %** de la tabla de horarios no contiene horas de reloj, sino
    desplazamientos desde el inicio del viaje;
  - el relleno de ceros es irregular, de modo que `'0:00:00' > '00:00:51'` como texto y
    la primera parada queda ordenada después de la segunda;
  - contar expediciones en lugar de expandir sus ventanas de frecuencia subestima el
    servicio en un **87,65 %** (7 905 frente a 64 011), y tomar el fin de ventana como
    inclusivo lo sobreestima en un **10,37 %**;
  - el «32 % de paradas huérfanas» es **falso**: 5 989 de las 5 991 filas sin horarios
    no son paradas, sino estaciones, accesos, nodos de pasillo y áreas de abordaje. Las
    paradas realmente sin uso son **dos**.

  Los seis cruces de clave foránea del modelo tienen **cero** huérfanos: el feed está
  bien formado. El problema nunca fue la integridad, fue la semántica.
- **`lab.dates.parse_hms_seconds`, `seconds_to_hms` y `service_day_hour`** para
  horarios de día de servicio: admiten horas de 24 o más y relleno de ceros irregular,
  que `pd.to_datetime` rechaza. Sirven para cualquier horario operacional —turnos,
  guardias, jornadas de producción—, no solo para transporte.
- **`scripts/fetch_data.py`** para traer una fuente del catálogo desde la línea de
  comandos, declarando el estado de su licencia.
- **`docs/instancias.md`**: el recorrido de nueve etapas que se aplica a cualquier
  dominio, con lo que cada etapa evita, y una lista de instancias candidatas —banca,
  astronomía, clientes, empresa, salud, energía, logística, ciberseguridad— marcada
  explícitamente como trabajo pendiente y no como capacidad existente.
- Cuatro registros de conocimiento nuevos, todos con origen en datos reales:
  `horario-relativo-vs-absoluto`, `relleno-de-ceros-y-orden`, `expandir-frecuencias` y
  `defecto-que-no-existe`.

### Corregido

- **`lab.metrics.safe_ratio` no difundía un escalar sobre el índice de una serie.**
  Envolver el escalar con `pd.Series(escalar)` creaba una serie de un elemento con
  índice 0, y la división alineaba por índice: todas las filas salvo la primera
  quedaban en NaN sin que nada avisara. Se detectó calculando los errores relativos de
  la tabla comparativa de la instancia del GTFS, y tiene prueba de regresión.
- El mensaje de error que avisa que falta el feed fallaba al construirse cuando la
  ruta estaba fuera del repositorio: `Path.relative_to` levanta `ValueError`. Un
  mensaje de error que no se puede construir es peor que no tener mensaje.

### Cambiado

- **Toda la documentación queda en español.** Se eliminó `README.en.md` y las
  referencias a él. Los nombres técnicos se conservan en su forma original cuando es la
  que usa la herramienta (`groupby`, `SUMIFS`, `LEFT JOIN`), porque traducirlos
  impediría buscarlos.
- El README describe el laboratorio como un recorrido para leer datos de cualquier
  dominio, con las instancias como aplicaciones de ese recorrido.
- `docs/roadmap.md` da por cubierta la competencia `ingenieria-datos`, que la instancia
  real entrena.

## [0.1.0] — 2026-11-26

Primera versión oficial. Consolida el laboratorio como infraestructura genérica de
análisis, investigación, aprendizaje y evaluación, con la preparación para una
evaluación técnica de gestor de datos como primer caso aplicado.

### Núcleo transversal (`lab/`, 17 módulos)

- `method`: metodología universal de 18 etapas como objeto auditable. Una etapa no se
  puede completar sin evidencia verificable; declararla no aplicable exige un motivo.
- `contracts`: contratos de datos con tipos lógicos, dominios, rangos, claves
  primarias y foráneas, y severidad por hallazgo. No elimina filas: informa.
- `metrics`: razones con denominador seguro, estadística descriptiva con cobertura,
  percentiles con método declarado, comparación entre tasa ponderada y promedio simple,
  atípicos por el criterio de Tukey.
- `dates`: conversión defensiva de fecha-hora informando qué no se pudo interpretar,
  duraciones, bandas horarias validadas contra huecos y solapes, atributos de
  calendario.
- `stats`: intervalos de confianza de media y proporción (Wilson), prueba de Welch,
  correlación de Pearson y chi-cuadrado de independencia, con las distribuciones
  acumuladas implementadas en Python puro. **Sin SciPy.**
- `sqlbridge`: ejecución de SQL de solo lectura sobre DataFrames mediante `sqlite3`, y
  comparación formal de resultados entre implementaciones.
- `excel`: libros con paleta del estándar visual, fila de unidades sobre el encabezado,
  autofiltro, congelado, formatos numéricos, hoja índice y escritura de fórmulas reales.
- `viz`: gráficos que exigen título, rótulo con unidad, período y fuente, con escala
  honesta y paleta accesible.
- `report`: informes de caso (12 secciones) y de investigación (20 secciones) que se
  niegan a exportarse incompletos, con clasificación obligatoria de las afirmaciones.
- `catalog`: descubrimiento y validación de casos contra 26 campos de metadatos, con
  matriz de cobertura de competencias.
- `knowledge`: base de conocimiento con índice invertido y búsqueda TF-IDF, sin
  modelos ni red, con control de referencias cruzadas.
- `learning`: modelo del programa y validador del estándar de 17 secciones por clase.
- `assessment`: motor de evaluaciones con configuraciones, banco de ítems, generación
  reproducible por semilla, rúbricas ponderadas y seguimiento de intentos.
- `agents`: 20 contratos de capacidades especializadas y un arnés que detecta
  responsabilidades duplicadas, contratos incompletos y referencias inexistentes.
- `profiles`: 11 perfiles profesionales sobre un vocabulario de 20 competencias, con
  cobertura real medida contra los casos implementados.
- `core`: se conserva sin cambios de comportamiento (lectura, perfil, cruce auditado,
  exportación).
- `console`: salida UTF-8 legible en consolas de Windows.

### Caso prioritario: transporte

- `solutions/sql_reference.py`: **segunda implementación completa en SQL**, que parte
  de los CSV cargados como texto y hace su propio casteo, cruce y agregación. No
  comparte código con la implementación en Pandas.
- `scripts/build_excel_solutions.py`: libros `solutions/excel/case_N_resuelto.xlsx` con
  **fórmulas reales de Excel** (`XLOOKUP`, `SUMIFS`, `COUNTIFS`, `AVERAGEIFS`,
  duración por factor 1440), hojas separadas de entradas, cálculos, resultados,
  control y documentación, y una hoja de control que confronta Excel con Python al
  abrir el libro.
- `cases/transport/case.json`: metadatos completos, incluidos supuestos, metodologías
  alternativas, validaciones, limitaciones, conocimiento adquirido y capacidades
  reutilizables.
- `docs/dtpm-antecedentes.md`: antecedentes públicos **verificados** el 26 de noviembre
  de 2026 (GTFS vigente y GTFS históricos publicados por el DTPM, con sus URL y la
  fecha de vigencia leída en el sitio), con una sección explícita de lo que **no** se
  pudo verificar.
- `docs/equivalencias.md`: equivalencias entre SQL, Pandas, Excel y R, con una columna
  de trampas donde las versiones «equivalentes» dejan de serlo.

### Laboratorio de evaluaciones

- `assessments/items/gestion-de-datos.json`: banco de 15 ítems con enunciado,
  competencias, herramientas, tiempo, entregable, criterios de corrección y las
  trampas que cada ítem busca detectar.
- `assessments/blueprints.py`: tres configuraciones (simulación de cuatro horas para
  gestor de datos, diagnóstico rápido, análisis y comunicación) con rúbricas que suman
  100 puntos.
- `scripts/build_assessment.py`: generación reproducible por semilla, declarando las
  competencias obligatorias que el banco todavía no cubre.

### Programa de aprendizaje

Ocho clases publicadas, cada una con las 17 secciones del estándar:

- Fundamentos: datos, tablas, tipos y claves; calidad de datos.
- Matemáticas: estadística descriptiva.
- Programación: Pandas para gestión de datos; Excel con fórmulas y tablas dinámicas.
- Ingeniería: cruces, contratos y SQL equivalente.
- Análisis: indicadores, visualización y comunicación.
- Investigación: método, preguntas, hipótesis y validez.

### Base de conocimiento

Catorce registros atómicos con procedencia y referencias cruzadas, entre ellos los
defectos encontrados durante esta versión: la pérdida de precisión de `julianday`, el
denominador inflado por `CONTAR.SI.CONJUNTO` con criterio `"<>"`, la confusión entre
ausente, cero e inválido, y la diferencia entre puntos porcentuales y variación
porcentual.

### Documentación

- README en español, con navegación, diagramas Mermaid, insignias
  verificables y una sección explícita de lo que las pruebas **no** cubren.
- `docs/arquitectura.md`: vista de componentes, contratos entre módulos, flujo de un
  problema nuevo y decisiones de arquitectura con sus alternativas descartadas.
- `docs/roadmap.md`: separación estricta entre implementado y proyectado, con las
  brechas **medidas** (competencias sin caso, bloque sin clases, lo que las pruebas no
  cubren).
- `scripts/build_docs.py`: genera catálogo, agentes, perfiles, programa, metodología e
  índice de conocimiento **desde el código**, de modo que la documentación no pueda
  desincronizarse. `--check` lo verifica en integración continua.
- `LICENSE` (MIT), `CONTRIBUTING.md` y `SECURITY.md`.

### Calidad

- Suite de pruebas que cubre el núcleo módulo por módulo, la validación cruzada entre
  Pandas y SQL en los tres casos, la estructura de los libros de Excel, el estándar
  pedagógico, los metadatos de los casos, el arnés de agentes y la coherencia del
  repositorio (versión única, enlaces relativos vivos, núcleo sin dependencias de
  dominio, documentación derivada al día, ausencia de secretos y de rutas absolutas).
- Integración continua con `uv`, lockfile versionado, y comprobación de que la
  documentación generada está al día.

### Corregido

- **Precisión de la duración en SQL.** El cálculo con
  `(julianday(fin) − julianday(inicio)) × 1440` perdía dígitos significativos y
  devolvía `42.999999971` donde el valor exacto era `43`. La comparación
  `duración ≤ meta` se invertía en todos los empates, moviendo la puntualidad varios
  puntos porcentuales mientras la media coincidía hasta el octavo decimal. Se
  reemplazó por una resta de segundos enteros con `strftime('%s', …)`. Detectado por la
  validación cruzada con la implementación en Pandas.
- **Denominador de la puntualidad en Excel.** `COUNTIFS(rango, "<>")` cuenta como no
  vacías las celdas cuya fórmula devuelve cadena vacía, de modo que inflaba el
  denominador y bajaba la tasa. Se reemplazó por `">=0"`, que solo admite valores
  numéricos.
- **Fila de unidades dentro del autofiltro de Excel.** Estaba bajo el encabezado, de
  modo que el filtro la trataba como un registro más. Se movió encima del encabezado.
- **IDF que anulaba términos frecuentes.** Con `log(N/df)`, un término presente en
  todos los registros pesaba exactamente cero y una búsqueda legítima no devolvía
  nada. Se cambió a la IDF suavizada `log(1 + N/df)`.
- **`UnicodeEncodeError` en consolas de Windows.** Imprimir una fórmula con símbolos
  matemáticos abortaba el comando en consolas con página de códigos cp1252, aunque el
  cálculo fuera correcto. Resuelto en `lab.console`.
- **Fallo del validador de clases fuera del repositorio.** `Lesson.reference` levantaba
  `ValueError` al validar un directorio externo; ahora devuelve la ruta absoluta.
- **`ORDER BY` en consulta compuesta.** La emulación del `FULL OUTER JOIN` con `UNION
  ALL` fallaba porque el `ORDER BY` no encontraba las columnas; se agregaron alias
  explícitos en el primer `SELECT`.

### Conservado sin cambios de comportamiento

Las tres simulaciones de cuatro horas, los tres datasets sintéticos con sus semillas,
`solutions/reference.py`, `cases/retail`, `cases/education`, `lab/core.py`,
`scripts/generate_data.py`, `scripts/export_inputs.py`, `scripts/new_case.py`,
`docs/manual.md`, `docs/diccionario.md`, `docs/research-method.md`,
`docs/visual-standard.md`, `solutions/EXCEL.md`, la plantilla de caso y las pruebas
previas (`tests/test_generic.py`, `tests/test_reference.py`), que siguen pasando.
