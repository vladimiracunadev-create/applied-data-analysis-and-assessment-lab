"""Genera los datos sintéticos de los tres casos de transporte.

Qué produce
    `data/case_<n>/` con cuatro archivos CSV: `operadores.csv`, `recorridos.csv`,
    `viajes.csv` y `programacion.csv`. El caso 1 es pequeño (una semana), el 2 mediano
    (dos semanas) y el 3 grande (tres semanas).

Por qué datos sintéticos
    Son reproducibles con una semilla, no contienen datos personales y no arrastran
    restricciones de licencia. La estructura es análoga a la de un sistema real de
    transporte —hechos de operación más catálogos más programación— para que lo
    aprendido se transfiera; las magnitudes no lo son y no deben citarse como cifras
    de ningún sistema.

Defectos deliberados
    El generador introduce defectos controlados, porque un dataset limpio no enseña
    gestión de datos. Por cada caso `n`:

    - `4n` duplicados exactos, copiados de las primeras filas;
    - `n` viajes con `recorrido_id = 'R99'`, que no existe en el catálogo;
    - `n` viajes realizados con `pasajeros` vacío;
    - `n` viajes realizados con `pasajeros = -5`, un valor imposible.

    Las posiciones de los defectos (índices 20, 40 y 60) están elegidas para no caer
    sobre las filas duplicadas, de modo que el recuento de duplicados exactos sea
    exactamente `4n` y las pruebas puedan afirmarlo.

Reproducibilidad
    La semilla es `20261126 + numero_de_caso`. Dos ejecuciones producen archivos
    idénticos byte a byte, lo que permite versionar los resultados de referencia y
    detectar cualquier cambio involuntario del generador.

Uso
    python scripts/generate_data.py
"""

from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Semilla base. Cambiarla invalida los resultados de referencia versionados.
SEMILLA_BASE = 20261126

#: Número de viajes por caso, indexado por número de caso (la posición 0 no se usa).
VIAJES_POR_CASO = (0, 450, 1400, 3500)

#: Operadores ficticios. Ningún nombre corresponde a una empresa real.
OPERADORES = [("O1", "Operador A"), ("O2", "Operador B"), ("O3", "Operador C")]


def save(path: Path, headers: list[str], rows: list) -> None:
    """Escribe un CSV en UTF-8 con BOM y saltos de línea normalizados.

    Se usa `utf-8-sig` —UTF-8 con marca inicial— porque es la codificación que Excel
    en Windows reconoce al abrir un CSV sin pasar por el asistente de importación. Sin
    la marca, los acentos se rompen al hacer doble clic sobre el archivo.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def generate(case: int) -> None:
    """Genera los cuatro archivos del caso indicado.

    Args:
        case: 1, 2 o 3. Determina el volumen, la ventana de días y la cantidad de
            defectos introducidos.
    """
    rng = random.Random(SEMILLA_BASE + case)
    base = ROOT / "data" / f"case_{case}"

    operators = list(OPERADORES)
    # Nueve recorridos, repartidos cíclicamente entre los tres operadores, con metas
    # de duración crecientes (43 a 67 minutos).
    routes = [(f"R{i:02}", operators[(i - 1) % 3][0], 40 + i * 3) for i in range(1, 10)]

    trips = []
    for i in range(VIAJES_POR_CASO[case]):
        route, _, target = rng.choice(routes)
        start = datetime(2026, 10, 1) + timedelta(
            days=rng.randrange(case * 7), minutes=rng.randrange(360, 1380)
        )
        # Duración alrededor de la meta del recorrido, con un piso de 10 minutos.
        duration = max(10, round(rng.gauss(target, 12)))
        pax = rng.randrange(0, 110)
        status = rng.choices(["REALIZADO", "CANCELADO"], [94, 6])[0]
        trips.append([
            f"T{i + 1:05}",
            route,
            start.isoformat(sep=" "),
            # Un viaje cancelado no tiene hora de fin: el campo queda vacío por
            # diseño, y eso no es un defecto de calidad.
            (start + timedelta(minutes=duration)).isoformat(sep=" ") if status == "REALIZADO" else "",
            pax if status == "REALIZADO" else 0,
            status,
        ])

    # Defectos controlados (ver el encabezado del módulo).
    for i in range(case * 4):
        trips.append(trips[i].copy())
    for i in range(case):
        trips[20 + i][1] = "R99"   # clave que no existe en el catálogo
        trips[40 + i][4] = ""      # pasajeros sin registrar
        trips[60 + i][4] = -5      # pasajeros imposible

    save(base / "operadores.csv", ["operador_id", "operador"], operators)
    save(base / "recorridos.csv", ["recorrido_id", "operador_id", "meta_min"], routes)
    save(
        base / "viajes.csv",
        ["viaje_id", "recorrido_id", "inicio", "fin", "pasajeros", "estado"],
        trips,
    )

    # Programación: un objetivo por recorrido y día de la ventana del caso.
    targets = [
        (route[0], day, rng.randrange(18, 31))
        for route in routes
        for day in range(1, case * 7 + 1)
    ]
    save(
        base / "programacion.csv",
        ["recorrido_id", "dia_octubre", "viajes_programados"],
        targets,
    )


def main() -> None:
    for case in (1, 2, 3):
        generate(case)
        print(f"caso {case}: {VIAJES_POR_CASO[case]} viajes base en data/case_{case}")


if __name__ == "__main__":
    main()
