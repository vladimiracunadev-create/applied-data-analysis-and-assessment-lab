# Base de conocimiento

Registros atómicos y autocontenidos de lo aprendido resolviendo los casos del
laboratorio. Cada archivo es un registro con encabezado de metadatos y cuerpo en
Markdown; `lab.knowledge` los indexa y permite buscarlos.

## Cómo consultarla

```powershell
uv run python -m lab.knowledge                      # resumen por tipo
uv run python -m lab.knowledge "denominador cero"   # búsqueda
```

La búsqueda es léxica (TF-IDF), sin modelos ni red: funciona en integración continua
y se puede explicar por qué un registro salió primero. La búsqueda semántica con
embeddings está en la hoja de ruta como extensión opcional; **no** está implementada.

## Cómo agregar un registro

1. Cree `knowledge/<id>.md`, donde `<id>` es el nombre del archivo sin extensión y
   coincide con el campo `id`.
2. Complete el encabezado:

   ```markdown
   ---
   id: mi-registro
   tipo: concepto
   titulo: Título legible
   etiquetas: [etiqueta-a, etiqueta-b]
   fuente: ruta/dentro/del/repositorio
   relacionados: [otro-registro]
   ---
   ```

3. Tipos admitidos: `concepto`, `definicion`, `formula`, `algoritmo`, `metodologia`,
   `investigacion`, `ejercicio`, `solucion`, `caso`, `error`, `patron`, `leccion`.
4. `tests/test_knowledge.py` comprueba el formato, los identificadores únicos y que
   no queden referencias cruzadas rotas.

## Criterio de admisión

Un registro entra si responde a algo que costó descubrir y que volverá a aparecer en
otro caso. No entra lo que ya dice la documentación de una biblioteca.
