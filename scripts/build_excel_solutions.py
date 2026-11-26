"""Construye los libros de Excel resueltos de los casos de transporte.

Qué produce
    `solutions/excel/case_<n>_resuelto.xlsx`, un libro por caso con:

    - hojas de **entradas** (`01_viajes` … `04_programacion`) con los datos tal como
      llegan del CSV, sin modificar;
    - una hoja de **cálculos** (`10_calculos`) donde cada columna derivada es una
      **fórmula real** de Excel: `XLOOKUP` para los cruces, `(fin − inicio) × 1440`
      para la duración, banderas de validez con `AND`/`ISNUMBER`;
    - hojas de **resultados** (`20_demanda`, `21_realizados`, `22_cumplimiento`) con
      `SUMIFS` y `COUNTIFS` sobre las columnas de cálculo;
    - una hoja de **control** (`30_control`) que compara cada resultado de Excel con
      el valor obtenido en Python y marca `OK` o `REVISAR`;
    - una hoja de **documentación** (`90_documentacion`) con el diccionario y los
      supuestos aplicados.

Por qué las fórmulas son fórmulas y no valores
    Un libro con valores pegados no demuestra nada en una evaluación técnica. Al
    abrir cualquier celda de resultado se ve el cálculo completo, y la hoja de
    control confronta ese cálculo con la implementación en Python. Si alguien cambia
    un dato de entrada, el libro se recalcula y el control cambia solo.

Nota sobre el idioma
    El archivo almacena los nombres de función en inglés; Excel los muestra
    traducidos (`SUMIFS` → `SUMAR.SI.CONJUNTO`, `XLOOKUP` → `BUSCARX`,
    `COUNTIFS` → `CONTAR.SI.CONJUNTO`). La `docs/equivalencias.md` lista la
    correspondencia completa.

Uso
    python scripts/build_excel_solutions.py          # los tres casos
    python scripts/build_excel_solutions.py --case 1
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lab.console import enable_utf8  # noqa: E402
from lab.excel import (  # noqa: E402
    Sheet,
    column_letter,
    data_start_row,
    range_ref,
    write_workbook,
)
from solutions.reference import analyze  # noqa: E402

OUTPUT_DIR = ROOT / "solutions" / "excel"

#: Nombres de hoja. El prefijo numérico ordena y declara la sección.
S_VIAJES = "01_viajes"
S_RECORRIDOS = "02_recorridos"
S_OPERADORES = "03_operadores"
S_PROGRAMACION = "04_programacion"
S_CALCULOS = "10_calculos"
S_DEMANDA = "20_demanda"
S_REALIZADOS = "21_realizados"
S_CUMPLIMIENTO = "22_cumplimiento"
S_CONTROL = "30_control"
S_DOC = "90_documentacion"

#: Columnas de la hoja de cálculos, en orden. Las primeras seis son datos; el resto
#: son fórmulas. El índice de cada una se usa para construir las referencias.
CALC_COLUMNS: tuple[str, ...] = (
    "viaje_id", "recorrido_id", "inicio", "fin", "pasajeros", "estado",
    "operador_id", "operador", "meta_min", "duracion_min", "dia_octubre",
    "realizado", "valido_demanda", "puntual",
)
COL = {name: index for index, name in enumerate(CALC_COLUMNS)}

CALC_UNITS: dict[str, str] = {
    "inicio": "fecha-hora", "fin": "fecha-hora", "pasajeros": "personas",
    "meta_min": "min", "duracion_min": "min", "dia_octubre": "día",
    "realizado": "0/1", "valido_demanda": "0/1", "puntual": "0/1",
}
CALC_FORMATS: dict[str, str] = {
    "inicio": "fecha_hora", "fin": "fecha_hora", "pasajeros": "entero",
    "meta_min": "decimal", "duracion_min": "decimal", "dia_octubre": "entero",
}


def _load_inputs(case: int) -> dict[str, pd.DataFrame]:
    folder = ROOT / "data" / f"case_{case}"
    if not folder.exists():
        raise FileNotFoundError(
            f"No existe {folder}. Genere los datos con 'python scripts/generate_data.py'."
        )
    return {
        "viajes": pd.read_csv(folder / "viajes.csv"),
        "recorridos": pd.read_csv(folder / "recorridos.csv"),
        "operadores": pd.read_csv(folder / "operadores.csv"),
        "programacion": pd.read_csv(folder / "programacion.csv"),
    }


def _calc_frame(viajes: pd.DataFrame) -> pd.DataFrame:
    """Datos de la hoja de cálculos: viajes sin duplicados exactos y fechas reales.

    Las columnas derivadas se dejan vacías a propósito: las escribe Excel mediante
    fórmulas, no Python. Lo único que Python hace aquí es convertir `inicio` y `fin`
    de texto a fecha-hora, porque Excel no puede restar dos textos.
    """
    frame = viajes.drop_duplicates().reset_index(drop=True).copy()
    for column in ("inicio", "fin"):
        frame[column] = pd.to_datetime(frame[column], errors="coerce")
    frame["pasajeros"] = pd.to_numeric(frame["pasajeros"], errors="coerce")
    for column in CALC_COLUMNS[6:]:
        frame[column] = pd.NA
    return frame[list(CALC_COLUMNS)]


def _calc_formulas(rows: int, inputs: dict[str, pd.DataFrame]) -> dict[str, str]:
    """Fórmulas celda a celda de la hoja de cálculos.

    Cada columna derivada replica una regla del diccionario de datos:

    - `operador_id`: `XLOOKUP` contra `02_recorridos`, con `"SIN CLAVE"` como valor
      por defecto, de modo que una clave desconocida se vea en la planilla en lugar
      de propagar `#N/D`.
    - `duracion_min`: `(fin − inicio) × 1440`, vacío si falta un extremo.
    - `realizado`: estado `REALIZADO` **y** clave conocida.
    - `valido_demanda`: además, pasajeros numérico y no negativo.
    - `puntual`: solo se evalúa sobre realizados con duración válida.
    """
    first = data_start_row()
    rec_rows = len(inputs["recorridos"])
    ope_rows = len(inputs["operadores"])
    rec_first, rec_last = data_start_row(), data_start_row() + rec_rows - 1
    ope_first, ope_last = data_start_row(), data_start_row() + ope_rows - 1

    rec_id = range_ref(S_RECORRIDOS, 0, rec_first, rec_last)
    rec_ope = range_ref(S_RECORRIDOS, 1, rec_first, rec_last)
    rec_meta = range_ref(S_RECORRIDOS, 2, rec_first, rec_last)
    ope_id = range_ref(S_OPERADORES, 0, ope_first, ope_last)
    ope_name = range_ref(S_OPERADORES, 1, ope_first, ope_last)

    formulas: dict[str, str] = {}
    for offset in range(rows):
        row = first + offset
        cell = {name: f"{column_letter(index)}{row}" for name, index in COL.items()}
        formulas[cell["operador_id"]] = (
            f'=XLOOKUP({cell["recorrido_id"]},{rec_id},{rec_ope},"SIN CLAVE")'
        )
        formulas[cell["operador"]] = (
            f'=IF({cell["operador_id"]}="SIN CLAVE","SIN CLAVE",'
            f'XLOOKUP({cell["operador_id"]},{ope_id},{ope_name},"SIN CLAVE"))'
        )
        formulas[cell["meta_min"]] = (
            f'=XLOOKUP({cell["recorrido_id"]},{rec_id},{rec_meta},"")'
        )
        formulas[cell["duracion_min"]] = (
            f'=IF(OR({cell["inicio"]}="",{cell["fin"]}=""),"",'
            f'({cell["fin"]}-{cell["inicio"]})*1440)'
        )
        formulas[cell["dia_octubre"]] = f'=IF({cell["inicio"]}="","",DAY({cell["inicio"]}))'
        formulas[cell["realizado"]] = (
            f'=IF(AND({cell["estado"]}="REALIZADO",{cell["operador_id"]}<>"SIN CLAVE"),1,0)'
        )
        formulas[cell["valido_demanda"]] = (
            f'=IF(AND({cell["realizado"]}=1,ISNUMBER({cell["pasajeros"]}),'
            f'{cell["pasajeros"]}>=0),1,0)'
        )
        formulas[cell["puntual"]] = (
            f'=IF(OR({cell["realizado"]}=0,{cell["duracion_min"]}="",'
            f'{cell["duracion_min"]}<0),"",IF({cell["duracion_min"]}<='
            f'{cell["meta_min"]},1,0))'
        )
    return formulas


def _calc_ranges(rows: int) -> dict[str, str]:
    first, last = data_start_row(), data_start_row() + rows - 1
    return {name: range_ref(S_CALCULOS, index, first, last) for name, index in COL.items()}


def _demanda_sheet(rows: int, reference: dict[str, pd.DataFrame]) -> Sheet:
    ranges = _calc_ranges(rows)
    demanda = reference["demanda"].copy()
    frame = pd.DataFrame({
        "operador": demanda["operador"],
        "pasajeros_excel": pd.NA,
        "viajes_con_dato_excel": pd.NA,
        "pasajeros_python": demanda["pasajeros"],
        "viajes_con_dato_python": demanda["viajes_con_dato"],
        "diferencia_pasajeros": pd.NA,
        "control": pd.NA,
    })
    first = data_start_row()
    formulas: dict[str, str] = {}
    for offset in range(len(frame)):
        row = first + offset
        formulas[f"B{row}"] = (
            f'=SUMIFS({ranges["pasajeros"]},{ranges["operador"]},$A{row},'
            f'{ranges["valido_demanda"]},1)'
        )
        formulas[f"C{row}"] = (
            f'=COUNTIFS({ranges["operador"]},$A{row},{ranges["valido_demanda"]},1)'
        )
        formulas[f"F{row}"] = f"=B{row}-D{row}"
        formulas[f"G{row}"] = f'=IF(ABS(F{row})<0.0001,"OK","REVISAR")'
    return Sheet(
        name=S_DEMANDA, frame=frame, kind="resultados",
        units={"pasajeros_excel": "personas", "pasajeros_python": "personas",
               "diferencia_pasajeros": "personas"},
        formats={"pasajeros_python": "entero", "viajes_con_dato_python": "entero"},
        notes=("Demanda por operador. Las columnas _excel se calculan con SUMAR.SI.CONJUNTO "
               "y CONTAR.SI.CONJUNTO sobre 10_calculos, filtrando valido_demanda = 1. "
               "Las columnas _python vienen de solutions/reference.py y solo sirven de control."),
        formulas=formulas,
    )


def _realizados_sheet(rows: int, reference: dict[str, pd.DataFrame]) -> Sheet:
    ranges = _calc_ranges(rows)
    realizados = reference["realizados_recorrido"].copy()
    duracion = reference["duracion"][["recorrido_id", "media_min", "puntualidad_pct"]]
    merged = realizados.merge(duracion, on="recorrido_id", how="left")
    frame = pd.DataFrame({
        "recorrido_id": merged["recorrido_id"],
        "realizados_excel": pd.NA,
        "duracion_media_excel": pd.NA,
        "puntualidad_pct_excel": pd.NA,
        "realizados_python": merged["realizados"],
        "duracion_media_python": merged["media_min"],
        "puntualidad_pct_python": merged["puntualidad_pct"],
        "control": pd.NA,
    })
    first = data_start_row()
    formulas: dict[str, str] = {}
    for offset in range(len(frame)):
        row = first + offset
        formulas[f"B{row}"] = (
            f'=COUNTIFS({ranges["recorrido_id"]},$A{row},{ranges["realizado"]},1)'
        )
        formulas[f"C{row}"] = (
            f'=AVERAGEIFS({ranges["duracion_min"]},{ranges["recorrido_id"]},$A{row},'
            f'{ranges["realizado"]},1,{ranges["duracion_min"]},">=0")'
        )
        # El denominador usa ">=0" y no "<>". COUNTIFS con "<>" cuenta como no vacías
        # las celdas cuya fórmula devuelve "", de modo que inflaría el denominador y
        # bajaría la puntualidad. Con ">=0" solo entran los 0 y 1 numéricos, que es
        # exactamente el conjunto de viajes realizados con duración válida.
        formulas[f"D{row}"] = (
            f'=IF(COUNTIFS({ranges["recorrido_id"]},$A{row},{ranges["puntual"]},">=0")=0,"",'
            f'100*COUNTIFS({ranges["recorrido_id"]},$A{row},{ranges["puntual"]},1)'
            f'/COUNTIFS({ranges["recorrido_id"]},$A{row},{ranges["puntual"]},">=0"))'
        )
        formulas[f"H{row}"] = (
            f'=IF(AND(B{row}=E{row},ABS(C{row}-F{row})<0.0001,'
            f'ABS(D{row}-G{row})<0.0001),"OK","REVISAR")'
        )
    return Sheet(
        name=S_REALIZADOS, frame=frame, kind="resultados",
        units={"duracion_media_excel": "min", "duracion_media_python": "min",
               "puntualidad_pct_excel": "%", "puntualidad_pct_python": "%"},
        formats={"realizados_python": "entero", "duracion_media_python": "minutos",
                 "puntualidad_pct_python": "porcentaje"},
        notes=("Viajes realizados, duración media y puntualidad por recorrido. La "
               "puntualidad usa PROMEDIO.SI.CONJUNTO y CONTAR.SI.CONJUNTO sobre la "
               "columna puntual, que solo está poblada en viajes realizados con "
               "duración válida: así el denominador es el correcto."),
        formulas=formulas,
    )


def _cumplimiento_sheet(rows: int, reference: dict[str, pd.DataFrame],
                        inputs: dict[str, pd.DataFrame]) -> Sheet:
    ranges = _calc_ranges(rows)
    prog_rows = len(inputs["programacion"])
    prog_first, prog_last = data_start_row(), data_start_row() + prog_rows - 1
    prog_rec = range_ref(S_PROGRAMACION, 0, prog_first, prog_last)
    prog_dia = range_ref(S_PROGRAMACION, 1, prog_first, prog_last)
    prog_val = range_ref(S_PROGRAMACION, 2, prog_first, prog_last)

    cumplimiento = reference["cumplimiento"].sort_values(
        ["recorrido_id", "dia_octubre"]
    ).reset_index(drop=True)
    frame = pd.DataFrame({
        "recorrido_id": cumplimiento["recorrido_id"],
        "dia_octubre": cumplimiento["dia_octubre"],
        "programados_excel": pd.NA,
        "realizados_excel": pd.NA,
        "cumplimiento_pct_excel": pd.NA,
        "realizados_python": cumplimiento["realizados"],
        "cumplimiento_pct_python": cumplimiento["cumplimiento_pct"],
        "control": pd.NA,
    })
    first = data_start_row()
    formulas: dict[str, str] = {}
    for offset in range(len(frame)):
        row = first + offset
        formulas[f"C{row}"] = (
            f'=SUMIFS({prog_val},{prog_rec},$A{row},{prog_dia},$B{row})'
        )
        formulas[f"D{row}"] = (
            f'=COUNTIFS({ranges["recorrido_id"]},$A{row},{ranges["dia_octubre"]},$B{row},'
            f'{ranges["realizado"]},1)'
        )
        formulas[f"E{row}"] = f'=IF(N(C{row})=0,"",100*D{row}/C{row})'
        formulas[f"H{row}"] = f'=IF(D{row}=F{row},"OK","REVISAR")'
    return Sheet(
        name=S_CUMPLIMIENTO, frame=frame, kind="resultados",
        units={"cumplimiento_pct_excel": "%", "cumplimiento_pct_python": "%"},
        formats={"dia_octubre": "entero", "realizados_python": "entero",
                 "cumplimiento_pct_python": "porcentaje"},
        notes=("Cumplimiento por recorrido y día. El porcentaje se calcula fila a fila "
               "con división protegida: si no hay viajes programados, la celda queda "
               "vacía en lugar de mostrar #¡DIV/0!. No promedie esta columna para "
               "obtener el cumplimiento global: divida la suma de realizados por la "
               "suma de programados."),
        formulas=formulas,
    )


def _control_sheet(reference: dict[str, pd.DataFrame]) -> Sheet:
    calidad = reference["calidad"]
    frame = pd.DataFrame({
        "control": [
            "Filas con diferencia en demanda",
            "Filas con diferencia en realizados/duración/puntualidad",
            "Filas con diferencia en cumplimiento",
            "Total de controles en REVISAR",
        ],
        "resultado": pd.NA,
        "criterio": [
            "Debe ser 0: Excel y Python coinciden en pasajeros por operador.",
            "Debe ser 0: coinciden recuento, duración media y puntualidad por recorrido.",
            "Debe ser 0: coinciden los realizados por recorrido y día.",
            "Debe ser 0. Si no lo es, revise la hoja señalada antes de entregar.",
        ],
    })
    first = data_start_row()
    formulas = {
        f"B{first}": f"=COUNTIF('{S_DEMANDA}'!G:G,\"REVISAR\")",
        f"B{first + 1}": f"=COUNTIF('{S_REALIZADOS}'!H:H,\"REVISAR\")",
        f"B{first + 2}": f"=COUNTIF('{S_CUMPLIMIENTO}'!H:H,\"REVISAR\")",
        f"B{first + 3}": f"=SUM(B{first}:B{first + 2})",
    }
    notes = (
        "Validación cruzada Excel ↔ Python. Los cuatro valores deben ser cero. "
        "Indicadores de calidad calculados en Python: "
        + "; ".join(f"{r.indicador} = {r.valor}" for r in calidad.itertuples())
        + "."
    )
    return Sheet(name=S_CONTROL, frame=frame, kind="documentacion",
                 units={"resultado": "filas"}, notes=notes, formulas=formulas)


def _doc_sheet(case: int) -> Sheet:
    frame = pd.DataFrame(
        [
            ("viajes.viaje_id", "Identificador del viaje", "texto",
             "Se espera único tras eliminar duplicados exactos."),
            ("viajes.recorrido_id", "Clave foránea al recorrido", "texto",
             "Puede apuntar a un recorrido inexistente; se marca SIN CLAVE."),
            ("viajes.inicio / fin", "Fecha-hora local sin zona", "fecha-hora",
             "fin vacío en viajes cancelados. Duración válida si fin >= inicio."),
            ("viajes.pasajeros", "Pasajeros registrados en el viaje", "entero",
             "Nulo o negativo: el viaje se conserva, el pasajero no se suma."),
            ("viajes.estado", "REALIZADO o CANCELADO", "texto",
             "Los cancelados se excluyen de demanda y duración."),
            ("recorridos.meta_min", "Duración objetivo del recorrido", "minutos",
             "Base de la puntualidad pedagógica, que no es el indicador oficial."),
            ("programacion", "recorrido_id + dia_octubre", "clave compuesta",
             "Los días programados sin viajes se conservan con realizados = 0."),
        ],
        columns=["campo", "significado", "tipo", "regla aplicada"],
    )
    notes = (
        f"Caso {case}. Datos sintéticos generados con semilla fija por "
        "scripts/generate_data.py. Material de entrenamiento: no es una prueba "
        "oficial ni contiene datos reales de ninguna institución. Supuestos "
        "aplicados: (1) duplicados exactos eliminados antes de contar; (2) claves "
        "desconocidas excluidas de los indicadores por recorrido y reportadas; "
        "(3) cumplimiento sin recorte a 100 %; (4) ningún valor imputado."
    )
    return Sheet(name=S_DOC, frame=frame, kind="documentacion", notes=notes)


def build(case: int, output_dir: Path = OUTPUT_DIR) -> Path:
    """Construye el libro resuelto de un caso y devuelve la ruta escrita."""
    if case not in (1, 2, 3):
        raise ValueError(f"Caso inválido: {case!r}. Use 1, 2 o 3.")
    inputs = _load_inputs(case)
    reference = analyze(case)
    calc = _calc_frame(inputs["viajes"])
    rows = len(calc)

    sheets = [
        Sheet(name=S_VIAJES, frame=inputs["viajes"], kind="entradas",
              units={"pasajeros": "personas"},
              notes="Datos crudos de viajes, exactamente como vienen del CSV. No se editan."),
        Sheet(name=S_RECORRIDOS, frame=inputs["recorridos"], kind="entradas",
              units={"meta_min": "min"}, formats={"meta_min": "decimal"},
              notes="Catálogo de recorridos con su operador y su duración objetivo."),
        Sheet(name=S_OPERADORES, frame=inputs["operadores"], kind="entradas",
              notes="Catálogo de operadores. Nombres ficticios."),
        Sheet(name=S_PROGRAMACION, frame=inputs["programacion"], kind="entradas",
              units={"viajes_programados": "viajes"},
              formats={"dia_octubre": "entero", "viajes_programados": "entero"},
              notes="Programación por recorrido y día. Clave compuesta."),
        Sheet(name=S_CALCULOS, frame=calc, kind="calculos",
              units=CALC_UNITS, formats=CALC_FORMATS,
              notes=("Viajes sin duplicados exactos. Las columnas desde operador_id "
                     "hasta puntual son fórmulas de Excel: abra cualquier celda para "
                     "ver el cálculo. Python solo convirtió inicio y fin de texto a "
                     "fecha-hora, porque Excel no puede restar dos textos."),
              formulas=_calc_formulas(rows, inputs)),
        _demanda_sheet(rows, reference),
        _realizados_sheet(rows, reference),
        _cumplimiento_sheet(rows, reference, inputs),
        _control_sheet(reference),
        _doc_sheet(case),
    ]
    destination = Path(output_dir) / f"case_{case}_resuelto.xlsx"
    return write_workbook(
        destination, sheets,
        title=f"Caso {case} de transporte — solución Excel con fórmulas verificables",
        source="Datos sintéticos del laboratorio (scripts/generate_data.py, semilla fija)",
    )


def main() -> None:
    enable_utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=int, choices=(1, 2, 3), default=None,
                        help="caso a construir; por omisión, los tres")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR,
                        help="directorio de salida")
    args = parser.parse_args()
    cases = [args.case] if args.case else [1, 2, 3]
    for case in cases:
        path = build(case, output_dir=args.output)
        size_kb = path.stat().st_size / 1024
        print(f"Caso {case}: {path.relative_to(ROOT)} ({size_kb:,.0f} KB)")


if __name__ == "__main__":
    main()
