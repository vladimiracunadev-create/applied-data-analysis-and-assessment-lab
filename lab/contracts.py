"""Contratos de datos: qué debe cumplir una tabla antes de usarse en un análisis.

Qué hace
    Declara en código las expectativas de una tabla (columnas, tipos, unicidad,
    nulos, rangos, dominios y claves foráneas) y produce un informe de hallazgos
    con la fila y el valor que incumplen.

Por qué existe
    Un análisis correcto sobre datos que incumplen su contrato sigue siendo un
    resultado inválido. Separar la validación del cálculo permite reportar la
    calidad antes de decidir exclusiones, que es exactamente lo que piden las
    evaluaciones técnicas de gestión de datos.

Cómo se valida
    `tests/test_contracts.py` verifica cada tipo de hallazgo con tablas mínimas.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

import pandas as pd

Severity = Literal["error", "aviso"]

#: Tipos lógicos admitidos. Se comprueban sobre el dtype de pandas de forma tolerante,
#: porque un CSV recién leído casi siempre llega como `object`.
LOGICAL_TYPES = ("entero", "decimal", "texto", "fecha_hora", "booleano", "cualquiera")


@dataclass(frozen=True)
class Column:
    """Expectativa sobre una columna.

    Args:
        name: nombre exacto de la columna.
        dtype: tipo lógico esperado (ver `LOGICAL_TYPES`).
        required: si la columna debe existir.
        nullable: si admite valores nulos.
        unique: si sus valores deben ser únicos entre las filas presentes.
        allowed: dominio cerrado de valores admitidos, si aplica.
        minimum: valor mínimo admitido (numérico o fecha).
        maximum: valor máximo admitido (numérico o fecha).
        unit: unidad de medida, para documentación e informes.
    """

    name: str
    dtype: str = "cualquiera"
    required: bool = True
    nullable: bool = True
    unique: bool = False
    allowed: tuple[Any, ...] | None = None
    minimum: Any | None = None
    maximum: Any | None = None
    unit: str = ""

    def __post_init__(self) -> None:
        if self.dtype not in LOGICAL_TYPES:
            raise ValueError(f"Tipo lógico inválido: {self.dtype!r}. Use {LOGICAL_TYPES}.")


@dataclass(frozen=True)
class ForeignKey:
    """Clave foránea: `column` de esta tabla debe existir en `target_table.target_column`."""

    column: str
    target_table: str
    target_column: str
    allow_missing: bool = False


@dataclass(frozen=True)
class Finding:
    """Un incumplimiento concreto del contrato."""

    table: str
    rule: str
    column: str
    severity: Severity
    count: int
    detail: str

    def as_row(self) -> dict[str, Any]:
        return {
            "tabla": self.table,
            "regla": self.rule,
            "columna": self.column,
            "severidad": self.severity,
            "filas": self.count,
            "detalle": self.detail,
        }


@dataclass
class ValidationReport:
    """Resultado de validar una tabla contra su contrato."""

    table: str
    rows: int
    findings: list[Finding] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "error"]

    @property
    def ok(self) -> bool:
        """True si no hay hallazgos de severidad `error`."""
        return not self.errors

    def to_frame(self) -> pd.DataFrame:
        """Hallazgos como tabla, lista para exportar a Excel o CSV."""
        if not self.findings:
            return pd.DataFrame(
                columns=["tabla", "regla", "columna", "severidad", "filas", "detalle"]
            )
        return pd.DataFrame([f.as_row() for f in self.findings])

    def raise_for_errors(self) -> None:
        """Interrumpe la ejecución si el contrato tiene errores."""
        if self.ok:
            return
        detail = "; ".join(f"{f.rule}:{f.column}({f.count})" for f in self.errors)
        raise ValueError(f"La tabla {self.table!r} incumple su contrato → {detail}")


@dataclass(frozen=True)
class TableContract:
    """Contrato completo de una tabla.

    Args:
        name: nombre lógico de la tabla.
        columns: expectativas por columna.
        primary_key: columnas que juntas identifican una fila de forma única.
        foreign_keys: relaciones con otras tablas.
        allow_extra_columns: si se admiten columnas no declaradas.
    """

    name: str
    columns: tuple[Column, ...]
    primary_key: tuple[str, ...] = ()
    foreign_keys: tuple[ForeignKey, ...] = ()
    allow_extra_columns: bool = True

    def column(self, name: str) -> Column:
        for col in self.columns:
            if col.name == name:
                return col
        raise KeyError(f"La columna {name!r} no está declarada en {self.name!r}.")

    # --------------------------------------------------------------- validación
    def validate(
        self, df: pd.DataFrame, related: dict[str, pd.DataFrame] | None = None
    ) -> ValidationReport:
        """Valida una tabla y devuelve todos los hallazgos encontrados.

        No modifica `df` ni elimina filas: la decisión de excluir registros es del
        análisis, no de la validación.
        """
        report = ValidationReport(table=self.name, rows=len(df))
        related = related or {}

        present = set(df.columns)
        for col in self.columns:
            if col.name not in present:
                if col.required:
                    report.findings.append(
                        Finding(self.name, "columna_faltante", col.name, "error", 1,
                                "La columna requerida no está en la tabla.")
                    )
                continue
            self._validate_column(df, col, report)

        if not self.allow_extra_columns:
            for extra in sorted(present - {c.name for c in self.columns}):
                report.findings.append(
                    Finding(self.name, "columna_no_declarada", extra, "aviso", 1,
                            "Columna presente que el contrato no declara.")
                )

        self._validate_primary_key(df, report)
        self._validate_foreign_keys(df, related, report)

        duplicated = int(df.duplicated().sum())
        if duplicated:
            report.findings.append(
                Finding(self.name, "duplicados_exactos", "*", "aviso", duplicated,
                        "Filas idénticas en todas sus columnas.")
            )
        return report

    def _validate_column(self, df: pd.DataFrame, col: Column, report: ValidationReport) -> None:
        series = df[col.name]

        nulls = int(series.isna().sum())
        if nulls and not col.nullable:
            report.findings.append(
                Finding(self.name, "nulo_no_permitido", col.name, "error", nulls,
                        "La columna no admite valores nulos.")
            )

        if col.unique:
            non_null = series.dropna()
            repeated = int(non_null.duplicated().sum())
            if repeated:
                report.findings.append(
                    Finding(self.name, "valor_repetido", col.name, "error", repeated,
                            "Se esperaban valores únicos.")
                )

        if col.dtype in ("entero", "decimal"):
            coerced = pd.to_numeric(series, errors="coerce")
            bad = int((coerced.isna() & series.notna()).sum())
            if bad:
                report.findings.append(
                    Finding(self.name, "tipo_invalido", col.name, "error", bad,
                            f"Valores no convertibles a {col.dtype}.")
                )
            if col.dtype == "entero":
                fractional = coerced.dropna()
                nonint = int((fractional != fractional.round()).sum())
                if nonint:
                    report.findings.append(
                        Finding(self.name, "entero_con_decimales", col.name, "aviso", nonint,
                                "Valores con parte decimal en una columna entera.")
                    )
            self._validate_range(coerced, col, report)
        elif col.dtype == "fecha_hora":
            coerced = pd.to_datetime(series, errors="coerce")
            bad = int((coerced.isna() & series.notna()).sum())
            if bad:
                report.findings.append(
                    Finding(self.name, "tipo_invalido", col.name, "error", bad,
                            "Valores no interpretables como fecha-hora.")
                )
            self._validate_range(coerced, col, report)
        elif col.dtype == "booleano":
            allowed = {True, False, "0", "1", "true", "false", "True", "False"}
            bad = int((~series.dropna().isin(allowed)).sum())
            if bad:
                report.findings.append(
                    Finding(self.name, "tipo_invalido", col.name, "error", bad,
                            "Valores que no representan verdadero/falso.")
                )
        else:
            self._validate_range(series, col, report)

        if col.allowed is not None:
            outside = int((~series.dropna().isin(col.allowed)).sum())
            if outside:
                report.findings.append(
                    Finding(self.name, "fuera_de_dominio", col.name, "error", outside,
                            f"Valores fuera del dominio {list(col.allowed)}.")
                )

    def _validate_range(self, series: pd.Series, col: Column, report: ValidationReport) -> None:
        if col.minimum is not None:
            try:
                below = int((series.dropna() < col.minimum).sum())
            except TypeError:
                below = 0
            if below:
                report.findings.append(
                    Finding(self.name, "bajo_minimo", col.name, "error", below,
                            f"Valores menores que {col.minimum}.")
                )
        if col.maximum is not None:
            try:
                above = int((series.dropna() > col.maximum).sum())
            except TypeError:
                above = 0
            if above:
                report.findings.append(
                    Finding(self.name, "sobre_maximo", col.name, "error", above,
                            f"Valores mayores que {col.maximum}.")
                )

    def _validate_primary_key(self, df: pd.DataFrame, report: ValidationReport) -> None:
        if not self.primary_key:
            return
        missing = [c for c in self.primary_key if c not in df.columns]
        if missing:
            report.findings.append(
                Finding(self.name, "clave_primaria_incompleta", ",".join(missing), "error",
                        len(missing), "Faltan columnas de la clave primaria.")
            )
            return
        key = df[list(self.primary_key)]
        repeated = int(key.duplicated().sum())
        if repeated:
            report.findings.append(
                Finding(self.name, "clave_primaria_repetida", ",".join(self.primary_key),
                        "error", repeated, "La clave primaria no identifica filas de forma única.")
            )
        nulls = int(key.isna().any(axis=1).sum())
        if nulls:
            report.findings.append(
                Finding(self.name, "clave_primaria_nula", ",".join(self.primary_key),
                        "error", nulls, "Filas con clave primaria incompleta.")
            )

    def _validate_foreign_keys(
        self, df: pd.DataFrame, related: dict[str, pd.DataFrame], report: ValidationReport
    ) -> None:
        for fk in self.foreign_keys:
            if fk.column not in df.columns:
                continue
            target = related.get(fk.target_table)
            if target is None:
                report.findings.append(
                    Finding(self.name, "tabla_referenciada_ausente", fk.column, "aviso", 1,
                            f"No se entregó la tabla {fk.target_table!r} para comprobar la clave.")
                )
                continue
            if fk.target_column not in target.columns:
                report.findings.append(
                    Finding(self.name, "columna_referenciada_ausente", fk.column, "error", 1,
                            f"{fk.target_table}.{fk.target_column} no existe.")
                )
                continue
            valid = set(target[fk.target_column].dropna())
            observed = df[fk.column].dropna()
            orphans = int((~observed.isin(valid)).sum())
            if orphans:
                severity: Severity = "aviso" if fk.allow_missing else "error"
                report.findings.append(
                    Finding(self.name, "clave_desconocida", fk.column, severity, orphans,
                            f"Valores sin correspondencia en {fk.target_table}.{fk.target_column}.")
                )


def validate_dataset(
    contracts: Sequence[TableContract], tables: dict[str, pd.DataFrame]
) -> dict[str, ValidationReport]:
    """Valida un conjunto de tablas resolviendo sus claves foráneas entre sí.

    Args:
        contracts: contratos a aplicar.
        tables: tablas por nombre lógico.

    Returns:
        Informe por tabla. Las tablas sin contrato se ignoran y las que tienen
        contrato pero no datos producen un informe con el hallazgo correspondiente.
    """
    reports: dict[str, ValidationReport] = {}
    for contract in contracts:
        df = tables.get(contract.name)
        if df is None:
            report = ValidationReport(table=contract.name, rows=0)
            report.findings.append(
                Finding(contract.name, "tabla_ausente", "*", "error", 1,
                        "El contrato existe pero no se entregó la tabla.")
            )
            reports[contract.name] = report
            continue
        reports[contract.name] = contract.validate(df, related=tables)
    return reports


def findings_frame(reports: Iterable[ValidationReport]) -> pd.DataFrame:
    """Une los hallazgos de varios informes en una sola tabla."""
    frames = [r.to_frame() for r in reports]
    frames = [f for f in frames if not f.empty]
    if not frames:
        return pd.DataFrame(
            columns=["tabla", "regla", "columna", "severidad", "filas", "detalle"]
        )
    return pd.concat(frames, ignore_index=True)


def contract_markdown(contract: TableContract) -> str:
    """Diccionario de datos en Markdown generado desde el contrato."""
    lines = [
        f"### {contract.name}",
        "",
        f"Clave primaria: {', '.join(contract.primary_key) or 'no declarada'}",
        "",
        "| Columna | Tipo | Unidad | Nulos | Único | Dominio / rango |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for col in contract.columns:
        domain = ""
        if col.allowed is not None:
            domain = ", ".join(str(v) for v in col.allowed)
        elif col.minimum is not None or col.maximum is not None:
            domain = f"{col.minimum if col.minimum is not None else '-inf'} … {col.maximum if col.maximum is not None else '+inf'}"
        lines.append(
            f"| {col.name} | {col.dtype} | {col.unit or '—'} | "
            f"{'sí' if col.nullable else 'no'} | {'sí' if col.unique else 'no'} | {domain or '—'} |"
        )
    if contract.foreign_keys:
        lines += ["", "Claves foráneas:", ""]
        for fk in contract.foreign_keys:
            lines.append(
                f"- `{fk.column}` → `{fk.target_table}.{fk.target_column}`"
                f"{' (admite faltantes)' if fk.allow_missing else ''}"
            )
    return "\n".join(lines) + "\n"
