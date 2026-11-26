---
id: vacio-concentrado
tipo: leccion
titulo: Un vacío uniforme es un problema de captura; concentrado en un archivo, es una decisión
etiquetas: [gobernanza-datos, calidad-datos, datos-reales, pensamiento-critico, comunicacion-resultados]
fuente: cases/carga_nocturna/solution.py
relacionados: [tres-respuestas-no-dos, intervalo-en-vez-de-cifra, cambiar-la-pregunta, clave-que-no-es-clave]
---

**El dato.** El campo `horario referencial` está presente en el 18,06 % de los 1 927
lugares de carga. Dicho así, es un problema de calidad de datos como cualquier otro.

Desagregado por archivo, es otra cosa:

| Tipo de local | Locales | Con horario |
| --- | --- | --- |
| Estación de Metro | 143 | **100 %** |
| Retail | 169 | **100 %** |
| Centro bip! estándar | 29 | **100 %** |
| Centro bip! alto estándar | 7 | **100 %** |
| **Punto bip!** | **1 579** | **0 %** |

Cuatro archivos completos y uno vacío — y es el que tiene el 82 % de los registros.

**Por qué la distinción importa.** Cambia el diagnóstico, el destinatario y el pedido:

| | Vacío uniforme | Vacío concentrado |
| --- | --- | --- |
| Qué es | falla de captura o de validación | decisión de publicación |
| A quién se le reporta | al proceso | al dueño del archivo |
| Qué se pide | corregir el formulario | publicar el campo que ya tiene |
| Qué se puede inferir del resto | poco | que el campo **es obtenible** |

La última fila es la que suele decidir la conversación. Que cuatro archivos lo tengan
al 100 % demuestra que el dato existe, se captura y se publica. No se está pidiendo
algo nuevo: se está pidiendo que el quinto archivo haga lo que hacen los otros cuatro.

**Cómo se mide el efecto, que es lo que vuelve el hallazgo accionable.** No basta con
señalar el vacío: hay que decir qué desbloquea cerrarlo.

```
tipo_local  locales_por_completar  del_total_sin_horario_pct  paradas_que_desbloquean
Punto bip!                   1546                       97.9                     5536
```

1 546 de los 1 579 locales sin horario están a menos de 300 m de una parada con
servicio nocturno. Completar esos registros vuelve contestable el 52,6 % de la red
nocturna.

> No «faltan horarios», sino «estos 1 546 registros desbloquean el 52,6 % de la red
> nocturna». La primera frase es una queja. La segunda es una solicitud priorizada.

**Un matiz que conviene no saltarse.** Que un campo esté presente no significa que
sirva. Los 348 locales que declaran horario usan **diez textos distintos**, y 311 de
ellos usan dos: 143 estaciones de Metro con la misma frase, 168 locales de una cadena
con otra. El campo no describe un local, describe la política de una cadena. El vacío
es el problema grande; la granularidad es el problema que queda después.

**La comprobación, siempre.** Antes de informar la cobertura de un campo, desagregarla
por su origen: archivo, fuente, sistema, sucursal, período de carga. Un promedio de
cobertura esconde exactamente el patrón que indica la causa.

```python
tabla = datos.groupby("origen")["campo"].agg(["size", "count"])
tabla["cobertura_pct"] = (tabla["count"] / tabla["size"] * 100).round(1)
```
