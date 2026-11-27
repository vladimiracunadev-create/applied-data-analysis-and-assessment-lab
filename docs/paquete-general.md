# Paquete general de todos los casos

[`todos-los-casos.zip`](../dist/todos-los-casos.zip) reúne en una sola descarga los
trece casos publicados, los diez cuadernos, sus artefactos y resultados versionados,
los tres datasets sintéticos y las implementaciones comparables en Pandas, Polars,
R, SQL y Excel. Cada cuaderno real incluye además su propio script Polars con
Matplotlib, script R con ggplot2 y gráfico estadístico.

## Qué contiene

- `cases/`: metadatos, README, cuadernos, scripts Pandas/Polars/R, R Markdown, Colab, libros, SVG y
  resultados de los trece casos;
- `solutions/`: referencias independientes en Pandas, Polars, R base y SQL, además de
  los libros de Excel resueltos;
- `data/case_1` a `data/case_3`: los datos sintéticos reproducibles;
- `lab/`, `scripts/` y `tests/`: núcleo, generadores y contratos para reproducir y
  verificar el contenido;
- `docs/`, `knowledge/`, `simulations/` y `assessments/`: documentación, aprendizaje,
  conocimiento acumulado y material de práctica;
- `MANIFEST.json`: ruta, tamaño y SHA-256 de cada archivo, conteo de casos y motores.

## Qué no contiene

No redistribuye los archivos públicos de terceros guardados localmente en
`data/original`. Los casos que los necesitan conservan su procedencia, resultados y
comando de descarga, pero respetan su licencia original.

## Regenerar y verificar

```powershell
python scripts/build_all_cases.py
python scripts/build_all_cases.py --check
```

El ZIP fija orden, timestamps y contenido de cada entrada; dentro del mismo runtime,
dos construcciones producen exactamente los mismos bytes. Entre versiones de Python,
la integración continua compara las entradas y su manifiesto SHA-256, y comprueba que
no se haya incluido ningún dato de terceros.
