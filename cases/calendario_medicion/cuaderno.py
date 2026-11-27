"""Cuaderno de P11: calendario reproducible de medición de un indicador oficial."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cases.calendario_medicion import solution as p11  # noqa: E402
from lab.cuaderno import Cuaderno, Paso  # noqa: E402
from lab.diagrama_svg import ACENTO, AZUL, OCRE, TINTA, Etapa, Flujo, Mapa, Rama  # noqa: E402
from lab.hoja_svg import Columna, Hoja  # noqa: E402

PROBLEMA = """
El denominador de un indicador oficial no es «los días del año». La metodología
descarta fines de semana, feriados, tres meses completos, vacaciones de invierno, la
semana de fiestas patrias y otras fechas. Además, la medición ocurre solo en cuatro
meses. Una nota al pie decide qué observaciones pueden entrar al indicador.

El riesgo no está en restar días, sino en sumar exclusiones solapadas. En 2026 las ocho
reglas marcan 256 días, pero el calendario contiene 365 y solo 201 quedan excluidos: 55
marcas se superponen. El cuaderno construye cada regla como una máscara auditable y
mide su aporte al denominador final.
"""

SOLUCION = """
Se valida primero el listado de feriados contra Pascua y fechas fijas. Luego se genera
un calendario diario, se aplican las ocho reglas y se auditan sus solapamientos. El
resultado se cruza con los meses efectivos de medición. Por último se compara 2024–2027
para distinguir redundancias estructurales de coincidencias accidentales y se somete a
sensibilidad el único supuesto no fijado por la fuente: las vacaciones de invierno.
"""

FLUJO = Flujo(titulo="De una nota metodológica a un denominador verificable", etapas=[
    Etapa("Fuente oficial", ["8 reglas", "4 meses de medición", "1 fecha no especificada"], color=TINTA),
    Etapa("Calendario", ["365 filas", "día laboral", "máscara por regla"], color=AZUL),
    Etapa("Auditoría", ["201 excluidos", "55 solapamientos", "reglas redundantes"], color=OCRE),
    Etapa("Intersección", ["marzo, junio", "septiembre, noviembre", "78 días medibles"], color=AZUL),
    Etapa("Decisión", ["denominador trazable", "comparación anual", "sensibilidad"], color=ACENTO),
])

MAPA = Mapa(centro="P11 · Calendario de medición", subtitulo="8 pasos · 8 reglas", ramas=[
    Rama("Validar insumos", ["1 · Feriados", "2 · Reglas declaradas"], color=AZUL),
    Rama("Construir", ["3 · Calendario diario", "4 · Aporte y solape"], color=AZUL),
    Rama("Encontrar el denominador", ["5 · Meses de medición", "6 · Días finales"], color=ACENTO),
    Rama("Desafiar", ["7 · Comparación anual", "8 · Sensibilidad"], color=OCRE),
])


def construir() -> Cuaderno:
    """Construye el cuaderno ejecutable de P11."""
    pasos = [
        Paso(
            titulo="Validar la fuente de feriados",
            objetivo="El insumo externo se confronta con Pascua calculada y diez fechas fijas.",
            pandas="resultados = p11.analizar(2026)\nresultados['validacion_feriados']",
            excel="Comparar el listado contra una tabla de fechas esperadas con `BUSCARX` y marcar faltantes.",
            trampa="Un CSV descargado no se vuelve verdadero por estar bien formado.", filas=10,
        ),
        Paso(
            titulo="Declarar las ocho reglas antes de calcular",
            objetivo="Cada exclusión conserva nombre, descripción y fuente.",
            pandas="resultados['exclusion_por_regla'][['regla','excluye','exclusiva','solapada','aporte_pct']]",
            excel="Una columna booleana por regla; nunca una única fórmula opaca con todas mezcladas.",
            trampa="Sumar los excluidos por regla cuenta 55 días más de una vez.", filas=10,
        ),
        Paso(
            titulo="Construir el calendario diario",
            objetivo="Una fila por fecha permite auditar por qué cada día entra o sale.",
            pandas="resultados['resumen_calendario']",
            excel="`=SECUENCIA(FECHA(2027;1;1)-FECHA(2026;1;1);1;FECHA(2026;1;1);1)`.",
            formula_excel="=SECUENCIA(365;1;FECHA(2026;1;1);1)", esperado="365 fechas",
            trampa="Trabajar solo con totales impide explicar un día particular.", filas=10,
            hoja=Hoja(
                columnas=[Columna("A", "fecha", 105), Columna("B", "laboral", 85), Columna("C", "medible", 90)],
                filas=[["2026-03-02", "SÍ", "SÍ"], ["2026-03-28", "NO", "NO"], ["2026-09-18", "NO", "NO"]],
                celda="B2", formula="=DIASEM(A2;2)<=5", resultado="VERDADERO",
                nota="El criterio de día laboral queda visible y se combina con las otras máscaras.",
            ),
        ),
        Paso(
            titulo="Medir solapamientos y redundancias",
            objetivo="Una regla puede excluir días y aun no aportar ninguno dado el resto.",
            pandas="resultados['reglas_redundantes']",
            excel="Contar `regla=VERDADERO` y `otras_reglas=FALSO` para obtener el aporte exclusivo.",
            trampa="Que una regla sea redundante en un año no demuestra que sea innecesaria siempre.", filas=8,
        ),
        Paso(
            titulo="Cruzar con los meses efectivos de medición",
            objetivo="El denominador real es la intersección, no todos los días elegibles del año.",
            pandas="resultados['resumen_medicion']",
            excel="`=Y(elegible;ESNUMERO(COINCIDIR(MES(fecha);{3;6;9;11};0)))`.",
            formula_excel="=Y(C2;ESNUMERO(COINCIDIR(MES(A2);{3;6;9;11};0)))",
            esperado="78 días medibles",
            trampa="Publicar 164 días elegibles responde otra pregunta; solo 78 están en meses de medición.", filas=12,
        ),
        Paso(
            titulo="Cuantificar el aporte al denominador final",
            objetivo="Se quita una regla a la vez y se recalcula la intersección.",
            pandas="resultados['aporte_sobre_medibles']",
            excel="Recalcular el conteo medible desactivando cada columna de regla por turno.",
            trampa="Meses completos excluye 90 días del año y cero días del denominador medido.", filas=10,
        ),
        Paso(
            titulo="Distinguir redundancia estructural de accidental",
            objetivo="Cuatro años muestran qué reglas jamás afectan y cuáles dependen del calendario.",
            pandas="resultados['clasificacion_reglas']",
            excel="Tabla por año y regla; `=MAX(rango)=0` identifica redundancia estructural en el período.",
            trampa="Feriados no afecta en 2026, pero sí elimina entre uno y tres días en otros años.", filas=10,
        ),
        Paso(
            titulo="Medir el supuesto de vacaciones de invierno",
            objetivo="La fecha no publicada se desplaza ±14 días para comprobar si cambia la decisión.",
            pandas="resultados['sensibilidad_invierno']",
            excel="Tabla de escenarios con el inicio supuesto y recálculo del conteo medible.",
            trampa="Mover el supuesto a junio reduce el denominador hasta seis días; no es un detalle narrativo.", filas=8,
        ),
    ]
    return Cuaderno(
        caso="P11", titulo="Calendario de medición de un indicador oficial",
        pregunta="¿Qué días de 2026 entran en la medición según las reglas oficiales?",
        datos="Metodología DIPRES, listado versionado de feriados y calendario gregoriano.",
        pasos=pasos, contexto={"p11": p11}, problema=PROBLEMA, solucion=SOLUCION,
        flujo=FLUJO, mapa=MAPA,
        cierre=("De 261 días laborales quedan 164 elegibles y 78 medibles. Cuatro reglas no cambian "
                "el denominador de 2026, pero solo tres son estructuralmente redundantes en 2024–2027."),
        aprendizajes=(
            "El denominador es una decisión documentada y debe poder explicarse fecha por fecha.",
            "Las exclusiones se combinan como conjuntos; sumar conteos ignora sus intersecciones.",
            "Una redundancia de un año puede ser accidental.",
            "Todo supuesto de calendario se somete a sensibilidad antes de publicar.",
        ),
        relacionados=(("Hallazgos auditables del caso", "README.md"),
                      ("Indicadores oficiales de transporte", "../../docs/indicadores-oficiales-transporte.md")),
        anterior=("P10 · Correspondencia buses–Metro", "../correspondencia_metro/CUADERNO.md"),
        siguiente=("P12-P13 · Frecuencia programada", "../frecuencia_programada/CUADERNO.md"),
        reproducir="python -m cases.calendario_medicion.solution",
        importes="from cases.calendario_medicion import solution as p11",
        columnas_excel=("fecha", "laboral", "medible"),
    )
