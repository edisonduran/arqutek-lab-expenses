"""Exportación a CSV."""
from __future__ import annotations

import csv
from pathlib import Path

from gastos.domain import GastoError


def exportar_csv(destino: Path, gastos) -> None:
    try:
        with open(destino, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["fecha", "categoria", "monto", "nota"])
            for g in gastos:
                w.writerow([g.fecha.isoformat(), g.categoria, f"{g.monto:.2f}", g.nota])
    except OSError as e:
        raise GastoError(f"No se pudo escribir {destino}: {e.strerror or e}") from None
