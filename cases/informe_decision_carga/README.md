# Informe de una página para decidir qué estudiar

P16 convierte los resultados de P06 y P08 en un informe ejecutivo validado. La salida
no recomienda automáticamente un predio: prioriza celdas geográficas para un estudio
de factibilidad y enumera la evidencia que falta.

## Mensaje ejecutivo

- La red programa 64 011 salidas en un día laboral; la hora máxima es 07:00, con 4 541.
- 59,29 % de las paradas tiene un lugar de carga a 300 m en línea recta.
- Con un factor de rodeo supuesto de 1,3, la cobertura baja a 46,02 %.
- Las celdas con muchas paradas descubiertas son candidatas para estudiar, no sitios de
  inversión aprobados.

No hay datos de transacciones, saldo, demanda, red peatonal, seguridad, predios ni
costos. Por eso no se afirma dónde existe mayor necesidad ni dónde debe construirse.

## Reproducir

```powershell
python -m cases.informe_decision_carga.solution
```

El informe validado queda en `resultados/informe.md`; `lab.report` impide exportarlo si
falta alguna sección obligatoria.
