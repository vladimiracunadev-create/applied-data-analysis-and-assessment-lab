# Guía de contribución

## Principio

Cada problema nuevo debe **enriquecer** el laboratorio sin romper lo anterior. Una
contribución que agrega un caso pero deja un caso previo sin ejecutar no se acepta,
aunque el caso nuevo sea excelente.

## Antes de escribir código

1. Lea `docs/arquitectura.md`, en particular las tres reglas de diseño y la tabla de
   invariantes.
2. Ejecute la suite completa para tener una línea base limpia:

   ```powershell
   uv sync
   uv run python scripts/generate_data.py
   uv run python -m pytest
   ```

3. Decida dónde va su cambio con la tabla «Cómo se extiende» de
   `docs/arquitectura.md`. Si no encaja en ninguna fila, abra primero una discusión:
   probablemente haga falta una capacidad nueva del núcleo.

## Reglas no negociables

Estas reglas existen porque su incumplimiento produce resultados erróneos con
apariencia correcta, que es el peor defecto posible en un repositorio de análisis.

1. **No declare implementado lo proyectado.** Si algo está a medias, va en
   `docs/roadmap.md`, sección de brechas, no en el README.
2. **No declare probado lo no ejecutado.** Si una prueba no se puede correr en
   integración continua, dígalo en el propio archivo de pruebas y explique qué cubre
   el mecanismo alternativo.
3. **No invente fuentes, referencias, cifras ni resultados.** Toda referencia debe ser
   localizable. Si no pudo abrir la fuente, no la cite.
4. **Nada de datos personales, credenciales ni material de terceros.** Los datos del
   laboratorio son sintéticos con semilla fija, o públicos con licencia verificada.
5. **No elimine funcionalidad ni contenido útil** sin justificación técnica escrita en
   el mensaje del commit.
6. **El núcleo no contiene reglas de negocio.** Si su función necesita saber qué es un
   «viaje realizado», pertenece al caso, no a `lab/`.
7. **Los casos no se importan entre sí.**
8. **Todo indicador declara unidad, denominador y cobertura.**
9. **Toda exclusión de registros se cuenta y se reporta.**

## Estándares por tipo de contribución

### Un caso de estudio

```powershell
uv run python scripts/new_case.py mi-caso
```

Complete `cases/mi-caso/case.json` con los 26 campos obligatorios (ver
`lab.catalog.REQUIRED_FIELDS`). Las competencias deben salir del vocabulario de
`lab.profiles.COMPETENCIES`. El caso necesita:

- datos propios, sintéticos y reproducibles, o públicos con licencia declarada;
- diccionario de datos y contrato ejecutable;
- solución independiente que corra desde la raíz del repositorio;
- validación: un recálculo por otra vía, o una invariante comprobable;
- rúbrica y entregables si es un ejercicio;
- al menos una prueba en `tests/` que falle si el cálculo se rompe.

### Una capacidad del núcleo

- Docstring de módulo con cuatro apartados: **qué hace**, **por qué existe**,
  **fórmulas** (si las hay, con variables y unidades) y **cómo se valida**.
- Tipado en las firmas públicas.
- Errores con mensaje útil: diga qué valor llegó y cuál se esperaba.
- Pruebas que cubran el camino correcto, los límites y cada error que levanta.
- Nada de rutas absolutas ni de dependencias nuevas en el entorno mínimo.

### Una clase del programa

`docs/learning/<bloque>/NN-slug.md`, con las 17 secciones de
`lab.learning.REQUIRED_SECTIONS`. El validador compara sin distinguir tildes ni
mayúsculas:

```powershell
uv run python -m lab.learning
```

Cada clase explica **qué** se hace, **cómo**, **por qué**, **cuándo corresponde** y
**cómo se valida**. Las fórmulas declaran sus variables y unidades. Las referencias son
verificables.

### Un registro de conocimiento

`knowledge/<id>.md`, con el encabezado que documenta `knowledge/README.md`. Criterio de
admisión: entra lo que costó descubrir y volverá a aparecer; no entra lo que ya dice la
documentación de una biblioteca.

### Una dependencia nueva

El entorno mínimo son `pandas`, `numpy`, `openpyxl`, `xlsxwriter`, `matplotlib`,
`jupyterlab` y `pytest`. Todo lo demás va como dependencia **opcional**, con detección
en tiempo de ejecución, como hace `lab.sqlbridge.duckdb_available()`. Justifique la
dependencia explicando qué problema resuelve que no se pueda resolver sin ella.

## Antes de enviar

```powershell
uv run python scripts/generate_data.py
uv run python scripts/build_docs.py
uv run python -m pytest
uv run python scripts/build_docs.py --check
uv run python -m lab.agents
uv run python -m lab.learning
```

Los seis comandos deben terminar sin error. El cuarto falla si cambió el código y no
regeneró la documentación derivada.

## Mensajes de commit

Una línea de asunto en imperativo, de 72 caracteres o menos, y un cuerpo que explique
**por qué**, no qué. Si el cambio corrige un defecto, el cuerpo describe el síntoma, la
causa y cómo se detectó.

Ejemplo real del repositorio:

```
Corregir la precisión de la duración en la implementación SQL

La duración se calculaba con (julianday(fin) - julianday(inicio)) * 1440.
julianday devuelve días en punto flotante y la resta pierde dígitos: el
resultado era 42.999999971 donde el valor exacto es 43. La comparación
duracion <= meta_min se invertía en todos los empates, cambiando la
puntualidad en varios puntos porcentuales mientras la media coincidía
hasta el octavo decimal.

Se detectó con tests/test_cross_validation.py, que confronta esta
implementación con la de Pandas. Con una sola implementación el número
habría pasado por correcto.
```

## Versionado

Versionado semántico. La primera versión oficial es la **0.1.0**; los prototipos
anteriores no son releases. Al cambiar la versión hay que actualizarla de forma
coherente en `pyproject.toml`, `lab/__init__.py`, `README.md` y
`CHANGELOG.md` y las insignias. `tests/test_repo_coherence.py` comprueba que coincidan.

## Conducta

Trate los datos, el trabajo y las preguntas de las demás personas con el mismo rigor
que exige este documento, y con respeto. Las discusiones son sobre la evidencia, no
sobre quién la presenta.
