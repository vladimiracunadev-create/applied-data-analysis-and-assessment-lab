# P11 · Reconstruir el calendario de medición de un indicador oficial

El ejercicio que más se parece al trabajo real de un gestor de datos del sector
público: tomar la metodología publicada de un indicador y **reconstruir su
denominador**, con todas sus reglas de exclusión, para después auditarlo.

Metadatos: [`case.json`](case.json) · Indicadores oficiales:
[`docs/indicadores-oficiales-transporte.md`](../../docs/indicadores-oficiales-transporte.md)

---

## 1. El problema, en palabras

El «Índice de variación de tiempos de viaje de las personas en ejes de la red vial
básica de la ciudad de Santiago» tiene una fórmula de dos líneas:

```
        Segundos promedio ponderado de viaje en periodo t
I = ──────────────────────────────────────────────────────── × 100
        Segundos promedio ponderado de viaje en periodo t−1
```

Y **ocho reglas de exclusión** en su nota al pie.

La pregunta: **para un año dado, ¿qué días entran en la medición?**

Esa es la pregunta que decide el denominador, y no se puede contestar mirando los
datos. Hay que leer la metodología, y la metodología está en una nota.

---

## 2. Descomposición

| # | Pregunta respondible | Qué exige |
| --- | --- | --- |
| 1 | ¿Cuáles son las reglas, textualmente? | Leer la nota al pie, no el nombre del indicador |
| 2 | ¿De dónde sale el listado de feriados? | Una fuente declarada, y validarla |
| 3 | ¿Cuántos días quedan? | Aplicar las ocho reglas |
| 4 | ¿Cuánto aporta cada regla? | Exclusión **exclusiva**, no bruta |
| 5 | ¿Cuál es el denominador **real**? | Cruzar con los meses en que se mide |
| 6 | ¿Las reglas sobran o hacen falta? | Medir su aporte al denominador real, año por año |

---

## 3. De dónde salen los datos

### Las reglas

Documento público de DIPRES, «VERSIÓN LEY AÑO 2019», Partida 19 — Ministerio de
Transporte y Telecomunicaciones, Capítulo 01, nota 1 del indicador. Textual:

> «Con el objetivo de homologar la metodología de cálculo empleada por **DTPM** con la
> utilizada por la **UOCT**, se consideran sólo días laborales, descartando los
> siguientes casos: Días feriados; Todos los días de los meses de enero, febrero y
> diciembre; Vacaciones de invierno (dos semanas, considerando los calendarios
> escolares); Semana de fiestas patrias; 11 de septiembre; Día del joven combatiente.
> Dado que en algunas ocasiones los incidentes inician en la tarde del día anterior,
> **se descartan todos los datos de los días 28 y 29**.»

Y aparte de las exclusiones, la medición tiene su propio calendario:

> «Las mediciones se efectúan **trimestralmente**, en los meses de marzo, junio,
> septiembre y noviembre.»

### Los feriados

| Campo | Valor |
| --- | --- |
| Servicio | `api.boostr.cl/holidays/<año>.json` |
| Publicador | **tercero — NO es la fuente oficial** |
| Fuente oficial | Ley 19.973 y sus modificaciones; listado de la Dirección del Trabajo |
| Por qué un tercero | `apis.digital.gob.cl`, la API del gobierno, no resolvía |
| Licencia | **no verificada** |
| Almacenamiento | [`feriados.csv`](feriados.csv), **versionado** |

El listado se descarga una vez y se versiona. Depender de una API de tercero en cada
ejecución haría el caso irreproducible el día que ese servicio desaparezca.

### Lo que no se consiguió

El **calendario escolar** del año, que la metodología necesita para las vacaciones de
invierno. Se declara un supuesto y se mide su efecto. Ver la sección 5.5.

---

## 4. Qué tecnología se usa y por qué

| Decisión | Alternativas | Por qué esta |
| --- | --- | --- |
| Reglas como **objetos** con su fuente | Una lista de fechas excluidas | Un calendario generado se puede auditar, regenerar y comparar entre años. Una lista no dice por qué un día falta |
| Validar Pascua con **un algoritmo propio** | Confiar en el listado | El algoritmo gregoriano anónimo es aritmética entera exacta: valida la parte movible del listado sin otra fuente |
| Feriados en un **CSV versionado** | Llamar a la API en cada ejecución | Reproducibilidad. Y el listado es un dato de entrada, no un detalle de implementación |
| Medir la exclusión **exclusiva** | Sumar lo que excluye cada regla | Ocho reglas excluyen menos días que la suma de sus exclusiones, porque se solapan |
| Medir el aporte al **denominador real** | Medirlo sobre el año completo | Una regla puede excluir 90 días del año y **cero** de los que se miden |
| Comparar **cuatro años** | Analizar solo 2026 | Distingue la redundancia estructural de la accidental |
| Pandas y nada más | — | Son 365 filas. El problema no es de volumen, es de precisión en las reglas |

---

## 5. La resolución

### 5.1 Validar el listado de feriados antes de usarlo

El listado viene de un tercero, así que se comprueba lo que se puede comprobar:

| Comprobación | Resultado 2026 | Veredicto |
| --- | --- | --- |
| Cantidad de feriados | 16 | — |
| Viernes Santo coincide con el cálculo de Pascua | 2026-04-03 | **sí** |
| Sábado Santo coincide con el cálculo | 2026-04-04 | **sí** |
| Feriados de fecha fija presentes | 10 de 10 | **sí** |
| Feriados movibles por Ley 19.973 | no verificable con estos medios | **declarado** |

El Domingo de Pascua de 2026 es el **5 de abril** según el algoritmo gregoriano
anónimo, validado en las pruebas contra diez fechas publicadas entre 1900 y 2027. Si el
Viernes Santo del listado no coincidiera, `actualizar_feriados` **no guarda el
archivo**: un dato de entrada que no pasa su propia validación no entra.

Lo que no se puede verificar queda dicho, no omitido.

### 5.2 Las ocho reglas, cada una con su cita

```python
weekends(source="…«se consideran sólo días laborales»")
specific_dates(feriados_del_anio, name="feriados", source="…«Días feriados»")
whole_months((1, 2, 12), source="…«Todos los días de los meses de enero, febrero y diciembre»")
date_ranges([(inicio_invierno, fin)], name="vacaciones_invierno", …)   # SUPUESTO
weeks_containing([date(año, 9, 18)], name="semana_fiestas_patrias", …)
specific_dates([date(año, 9, 11)], name="once_de_septiembre", …)
specific_dates([date(año, 3, 29)], name="dia_joven_combatiente", …)
days_of_month((28, 29), name="dias_28_y_29", …)
```

Una regla sin fuente no se puede defender. Las ocho la llevan.

### 5.3 El resultado bruto

| Indicador | 2026 |
| --- | --- |
| Días del año | 365 |
| Días laborales | 261 |
| **Días elegibles tras las ocho reglas** | **164** |
| Retención sobre los laborales | **62,84 %** |
| Suma de exclusiones por regla | 256 |
| Solapamiento total | **55** |

Más de un tercio de los días laborales se cae. Y las reglas se solapan en 55 días: la
suma de lo que excluye cada una (256) no es lo que se excluye (201).

Por mes, el perfil deja ver dónde pega cada regla:

| Mes | Laborales | Incluidos | % |
| --- | --- | --- | --- |
| enero, febrero, diciembre | 22, 20, 23 | **0, 0, 0** | 0 % |
| marzo | 22 | 22 | 100 % |
| julio | 23 | **11** | **47,83 %** |
| septiembre | 22 | **14** | **63,64 %** |
| noviembre | 21 | 21 | 100 % |

Julio cae por las vacaciones de invierno. Septiembre, por la semana de fiestas patrias
más el 11.

### 5.4 El aporte exclusivo: la primera redundancia

| Regla | Excluye | **Exclusiva** | Solapada | Aporte |
| --- | --- | --- | --- | --- |
| fin de semana | 104 | 62 | 42 | 16,99 % |
| meses completos | 90 | 58 | 32 | 15,89 % |
| días 28 y 29 | 23 | 11 | 12 | 3,01 % |
| vacaciones de invierno | 14 | 9 | 5 | 2,47 % |
| feriados | 16 | 4 | 12 | 1,10 % |
| semana de fiestas patrias | 7 | 4 | 3 | 1,10 % |
| 11 de septiembre | 1 | 1 | 0 | 0,27 % |
| **día del joven combatiente** | **1** | **0** | **1** | **0,00 %** |

El «Día del joven combatiente» es el **29 de marzo**, y la regla de los días 28 y 29 ya
lo descarta. Su exclusión exclusiva es **cero**: se puede quitar de la metodología sin
cambiar un solo día.

### 5.5 El supuesto de las vacaciones de invierno, medido

La metodología dice «dos semanas, considerando los calendarios escolares», sin fechas.
El supuesto declarado: las dos semanas que empiezan el primer lunes completo de julio.
Y en lugar de dejarlo ahí, se mide cuánto cambia el resultado si esas fechas se mueven:

| Inicio supuesto | Desplazamiento | Días elegibles | **Días medibles** | Diferencia |
| --- | --- | --- | --- | --- |
| 2026-06-22 | −14 días | 164 | **72** | **−6** |
| 2026-06-29 | −7 días | 164 | 77 | −1 |
| **2026-07-06** | **0 (supuesto)** | **164** | **78** | **0** |
| 2026-07-13 | +7 días | 164 | 78 | 0 |
| 2026-07-20 | +14 días | 165 | 78 | 0 |

**El supuesto solo importa si las vacaciones caen en junio**, que sí es mes de
medición. Mientras estén en julio, moverlas no cambia nada. Eso convierte una
incertidumbre en un riesgo acotado y nombrado: hay que conseguir el calendario escolar
únicamente si el receso empieza antes del 1 de julio.

Un supuesto medido es defendible. Uno escondido, no.

### 5.6 El denominador real: la segunda redundancia

Aquí está el hallazgo central del caso. Hay **dos** calendarios que conviene no
confundir: qué días son **elegibles** y en qué meses se **mide**.

| Indicador | 2026 |
| --- | --- |
| Días laborales del año | 261 |
| Días elegibles tras las ocho reglas | 164 |
| Días laborales de marzo, junio, septiembre y noviembre | 87 |
| **Días medibles** (elegibles **y** en mes de medición) | **78** |
| Medibles sobre los laborales del trimestre | 89,66 % |

Y al medir cuántos días medibles recuperaría el **quitar cada regla**:

| Regla | Días medibles que quita | ¿Afecta al denominador? |
| --- | --- | --- |
| fin de semana | **25** | sí |
| semana de fiestas patrias | **4** | sí |
| días 28 y 29 | **2** | sí |
| 11 de septiembre | **1** | sí |
| vacaciones de invierno | 0 | **NO** |
| meses completos (ene, feb, dic) | 0 | **NO** |
| feriados | 0 | **NO** |
| día del joven combatiente | 0 | **NO** |

**La mitad de las reglas no cambia el denominador en 2026.** Excluir enero, febrero y
diciembre descarta 90 días del año y **ninguno** de los que se miden, porque la
medición ocurre en marzo, junio, septiembre y noviembre. Las vacaciones de invierno
caen en julio, que tampoco es mes de medición.

### 5.7 Redundancia estructural frente a accidental

Y aquí está la distinción que evita el error de simplificar de más. Comparando cuatro
años:

| Año | Días medibles | Fin de semana | 28 y 29 | Fiestas patrias | Feriados | 11 sep | Meses | Invierno | Joven comb. |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2024 | 70 | 30 | 4 | 2 | 2 | 1 | 0 | 0 | 0 |
| 2025 | 74 | 28 | 3 | 3 | 1 | 1 | 0 | 0 | 0 |
| 2026 | **78** | 25 | 2 | 4 | **0** | 1 | 0 | 0 | 0 |
| 2027 | 75 | 26 | 4 | 4 | 3 | **0** | 0 | 0 | 0 |

| Clasificación | Reglas | Qué significa |
| --- | --- | --- |
| **Efectiva** | fin de semana, días 28 y 29, semana de fiestas patrias | Quitan días medibles **todos** los años |
| **Redundante accidental** | feriados (0 en 2026), 11 de septiembre (0 en 2027) | Sin efecto **este** año, por cómo cayó el calendario |
| **Redundante estructural** | meses completos, vacaciones de invierno, día del joven combatiente | Sin efecto en **ningún** año, por construcción |

La diferencia es operativa: quitar una regla estructuralmente redundante no cambia
nada nunca; quitar una accidental funciona este año y falla el siguiente. En 2026 los
feriados no quitan ningún día medible; en 2027 quitan tres.

Y un detalle que vale la pena: el **29 de junio de 2026** es a la vez feriado (San Pedro
y San Pablo) y día 29. Está doblemente excluido, de modo que quitar la regla de
feriados no lo recupera. Eso es lo que lleva el aporte de los feriados a cero ese año.

---

## 6. El resultado y lo que implica

**El denominario del indicador en 2026 son 78 días**, repartidos en cuatro meses de
medición. Son el **29,9 %** de los días laborales del año.

Y la consecuencia incómoda: **el denominador cambia entre años** —70, 74, 78, 75—, una
variación del **11 %** producida solo por cómo cae el calendario. El valor anual del
indicador es «el promedio de los valores resultantes de las cuatro mediciones
trimestrales», de modo que comparar el índice de dos años consecutivos compara
promedios calculados sobre **cantidades distintas de días**. No invalida el indicador;
sí es algo que un informe honesto menciona.

### Lo que este caso **no** establece

- **No calcula el indicador.** Construye su denominador. Los tiempos de viaje medidos
  por GPS en los 17 ejes no son públicos.
- **No dice que la metodología esté mal.** Una regla redundante puede existir por
  prudencia o por herencia histórica. Lo que el caso aporta es saber **cuáles** son
  redundantes y por qué, que es lo que necesita quien la reproduce.
- **No verifica el listado de feriados contra la ley.** Verifica su parte movible
  contra el cálculo de Pascua y la presencia de los feriados de fecha fija. Los
  movibles por Ley 19.973 quedan declarados como no verificados.
- **No usa el calendario escolar real.** Declara un supuesto y mide su efecto.

Las tablas completas están en [`resultados/`](resultados/).

---

## 7. Qué quedó aprendido

Registros nuevos en la base de conocimiento:

- [`denominador-es-una-decision`](../../knowledge/denominador-es-una-decision.md)
- [`regla-redundante`](../../knowledge/regla-redundante.md)
- [`supuesto-medido`](../../knowledge/supuesto-medido.md)

Capacidad nueva en el núcleo: **`lab.calendars`**, que no sabe nada de transporte ni de
Chile. Las reglas son objetos con su fuente, el cálculo de Pascua permite validar
cualquier listado de feriados, y la medición de exclusión exclusiva y de aporte
marginal sirve para auditar el denominador de cualquier indicador: días hábiles de un
acuerdo de nivel de servicio, días de bolsa en una serie financiera, días de clase en
un indicador educativo, turnos de producción en uno industrial.

---

## Reproducir

```powershell
uv run python -m cases.calendario_medicion.solution --anio 2026
```

Para actualizar el listado de feriados de un año (requiere red):

```powershell
uv run python -m cases.calendario_medicion.solution --actualizar-feriados 2027
```

Las pruebas corren **sin red**: el listado está versionado, y la descarga se ejerce
contra un servidor falso para comprobar que valida antes de guardar.

## Cuaderno, motores y gráfico

- [Resolución profesional paso a paso](CUADERNO.md).
- [Polars + Matplotlib](cuaderno/solucion_polars.py): comparación anual del denominador.
- [R + ggplot2](cuaderno/solucion.R): contraste y gráfico equivalente.
- [Figura publicada](cuaderno/svg/paso-07.svg).
