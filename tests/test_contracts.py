"""Pruebas de los contratos de datos (`lab.contracts`)."""

from __future__ import annotations

import pandas as pd
import pytest

from lab.contracts import (
    Column,
    ForeignKey,
    TableContract,
    contract_markdown,
    findings_frame,
    validate_dataset,
)


def rules(report) -> set[str]:
    return {f.rule for f in report.findings}


def test_tabla_conforme_no_produce_hallazgos():
    contract = TableContract(
        "viajes",
        (Column("viaje_id", "texto", unique=True, nullable=False),
         Column("pasajeros", "entero", minimum=0, unit="personas")),
        primary_key=("viaje_id",),
    )
    report = contract.validate(pd.DataFrame({"viaje_id": ["A", "B"], "pasajeros": [1, 2]}))
    assert report.ok
    assert report.findings == []
    assert report.to_frame().empty


def test_columna_requerida_ausente_es_error():
    contract = TableContract("t", (Column("falta"),))
    report = contract.validate(pd.DataFrame({"otra": [1]}))
    assert "columna_faltante" in rules(report)
    assert not report.ok


def test_columna_opcional_ausente_no_molesta():
    contract = TableContract("t", (Column("opcional", required=False),))
    assert contract.validate(pd.DataFrame({"otra": [1]})).ok


def test_nulos_unicidad_y_rango():
    contract = TableContract(
        "t",
        (Column("id", "entero", nullable=False, unique=True, minimum=1, maximum=10),),
    )
    report = contract.validate(pd.DataFrame({"id": [1, 1, None, 99]}))
    assert {"nulo_no_permitido", "valor_repetido", "sobre_maximo"} <= rules(report)


def test_tipos_invalidos_en_numero_y_fecha():
    contract = TableContract(
        "t", (Column("n", "entero"), Column("f", "fecha_hora"))
    )
    report = contract.validate(pd.DataFrame({"n": ["3", "x"], "f": ["2026-10-01", "ayer"]}))
    tipos = [f for f in report.findings if f.rule == "tipo_invalido"]
    assert {f.column for f in tipos} == {"n", "f"}
    assert all(f.count == 1 for f in tipos)


def test_entero_con_decimales_es_aviso_no_error():
    contract = TableContract("t", (Column("n", "entero"),))
    report = contract.validate(pd.DataFrame({"n": [1.5, 2.0]}))
    hallazgo = next(f for f in report.findings if f.rule == "entero_con_decimales")
    assert hallazgo.severity == "aviso"
    assert report.ok


def test_dominio_cerrado():
    contract = TableContract("t", (Column("estado", "texto", allowed=("REALIZADO", "CANCELADO")),))
    report = contract.validate(pd.DataFrame({"estado": ["REALIZADO", "OTRO"]}))
    hallazgo = next(f for f in report.findings if f.rule == "fuera_de_dominio")
    assert hallazgo.count == 1


def test_booleano_rechaza_valores_que_no_son_verdadero_falso():
    contract = TableContract("t", (Column("flag", "booleano"),))
    report = contract.validate(pd.DataFrame({"flag": [True, 1, "quizas"]}))
    assert "tipo_invalido" in rules(report)


def test_clave_primaria_compuesta_repetida_y_nula():
    contract = TableContract(
        "programacion",
        (Column("recorrido_id", "texto"), Column("dia", "entero")),
        primary_key=("recorrido_id", "dia"),
    )
    frame = pd.DataFrame({"recorrido_id": ["R1", "R1", None], "dia": [1, 1, 2]})
    report = contract.validate(frame)
    assert {"clave_primaria_repetida", "clave_primaria_nula"} <= rules(report)


def test_clave_primaria_con_columna_ausente():
    contract = TableContract("t", (Column("a", required=False),), primary_key=("a", "b"))
    report = contract.validate(pd.DataFrame({"x": [1]}))
    assert "clave_primaria_incompleta" in rules(report)


def test_clave_foranea_detecta_huerfanos():
    hijo = TableContract(
        "viajes", (Column("recorrido_id", "texto"),),
        foreign_keys=(ForeignKey("recorrido_id", "recorridos", "recorrido_id"),),
    )
    tablas = {
        "viajes": pd.DataFrame({"recorrido_id": ["R01", "R99"]}),
        "recorridos": pd.DataFrame({"recorrido_id": ["R01"]}),
    }
    report = hijo.validate(tablas["viajes"], related=tablas)
    hallazgo = next(f for f in report.findings if f.rule == "clave_desconocida")
    assert hallazgo.count == 1 and hallazgo.severity == "error"


def test_clave_foranea_con_faltantes_admitidos_es_aviso():
    hijo = TableContract(
        "viajes", (Column("recorrido_id", "texto"),),
        foreign_keys=(ForeignKey("recorrido_id", "recorridos", "recorrido_id",
                                 allow_missing=True),),
    )
    tablas = {
        "viajes": pd.DataFrame({"recorrido_id": ["R99"]}),
        "recorridos": pd.DataFrame({"recorrido_id": ["R01"]}),
    }
    report = hijo.validate(tablas["viajes"], related=tablas)
    assert report.ok
    assert next(f for f in report.findings if f.rule == "clave_desconocida").severity == "aviso"


def test_tabla_referenciada_ausente_se_informa_sin_fingir_validacion():
    hijo = TableContract(
        "viajes", (Column("recorrido_id", "texto"),),
        foreign_keys=(ForeignKey("recorrido_id", "recorridos", "recorrido_id"),),
    )
    report = hijo.validate(pd.DataFrame({"recorrido_id": ["R01"]}))
    assert "tabla_referenciada_ausente" in rules(report)


def test_columnas_no_declaradas_segun_politica():
    estricto = TableContract("t", (Column("a"),), allow_extra_columns=False)
    report = estricto.validate(pd.DataFrame({"a": [1], "b": [2]}))
    assert "columna_no_declarada" in rules(report)
    permisivo = TableContract("t", (Column("a"),))
    assert "columna_no_declarada" not in rules(permisivo.validate(pd.DataFrame({"a": [1], "b": [2]})))


def test_duplicados_exactos_se_cuentan_como_aviso():
    contract = TableContract("t", (Column("a"),))
    report = contract.validate(pd.DataFrame({"a": [1, 1, 2]}))
    assert next(f for f in report.findings if f.rule == "duplicados_exactos").count == 1


def test_raise_for_errors_interrumpe_solo_con_errores():
    contract = TableContract("t", (Column("a", "entero", nullable=False),))
    contract.validate(pd.DataFrame({"a": [1]})).raise_for_errors()
    with pytest.raises(ValueError, match="incumple su contrato"):
        contract.validate(pd.DataFrame({"a": [None]})).raise_for_errors()


def test_validate_dataset_informa_tabla_ausente():
    contract = TableContract("falta", (Column("a"),))
    reports = validate_dataset([contract], {})
    assert not reports["falta"].ok
    assert "tabla_ausente" in rules(reports["falta"])


def test_findings_frame_une_informes_y_soporta_el_caso_vacio():
    contract = TableContract("t", (Column("a", "entero", nullable=False),))
    sucio = contract.validate(pd.DataFrame({"a": [None]}))
    limpio = contract.validate(pd.DataFrame({"a": [1]}))
    assert len(findings_frame([sucio, limpio])) == len(sucio.findings)
    assert findings_frame([limpio]).empty
    assert list(findings_frame([]).columns) == ["tabla", "regla", "columna", "severidad",
                                                "filas", "detalle"]


def test_tipo_logico_invalido_se_rechaza_al_declarar():
    with pytest.raises(ValueError, match="Tipo lógico inválido"):
        Column("a", "numero_entero_grande")


def test_contract_markdown_documenta_columnas_y_claves():
    contract = TableContract(
        "viajes",
        (Column("viaje_id", "texto", unique=True, nullable=False),
         Column("pasajeros", "entero", minimum=0, unit="personas"),
         Column("estado", "texto", allowed=("REALIZADO", "CANCELADO"))),
        primary_key=("viaje_id",),
        foreign_keys=(ForeignKey("recorrido_id", "recorridos", "recorrido_id"),),
    )
    texto = contract_markdown(contract)
    assert "viajes" in texto and "personas" in texto
    assert "REALIZADO, CANCELADO" in texto
    assert "`recorrido_id` → `recorridos.recorrido_id`" in texto


def test_column_lanza_keyerror_si_no_existe():
    contract = TableContract("t", (Column("a"),))
    assert contract.column("a").name == "a"
    with pytest.raises(KeyError):
        contract.column("z")
