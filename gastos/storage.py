"""Persistencia en gastos.json. Formato (ADR-001): {"version":1,"gastos":[...]}."""
from __future__ import annotations

import json
import os
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path

from gastos.domain import Gasto, GastoError, parse_fecha


def ruta_por_defecto() -> Path:
    return Path(os.environ.get("GASTOS_FILE") or "gastos.json")


def _corrupto(ruta: Path, motivo: str) -> GastoError:
    return GastoError(f"El archivo {ruta} está corrupto ({motivo}). No se modificó.")


def cargar(ruta) -> list[Gasto]:
    ruta = Path(ruta)
    try:
        datos = ruta.read_bytes()
    except FileNotFoundError:
        return []
    except OSError as e:
        raise GastoError(f"No se pudo leer {ruta}: {e.strerror or e}") from None
    try:
        obj = json.loads(datos.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise _corrupto(ruta, "JSON inválido o vacío") from None
    items = obj.get("gastos") if isinstance(obj, dict) else obj
    if not isinstance(items, list):
        raise _corrupto(ruta, "estructura inesperada")
    out: list[Gasto] = []
    try:
        for it in items:
            nota = it.get("nota", "")
            if not isinstance(nota, str) or not isinstance(it["categoria"], str):
                raise TypeError
            out.append(Gasto(parse_fecha(it["fecha"]), it["categoria"],
                             Decimal(str(it["monto"])).quantize(Decimal("0.01")), nota))
    except (KeyError, TypeError, AttributeError, InvalidOperation, GastoError):
        raise _corrupto(ruta, "registro inválido") from None
    return out


def guardar(ruta, gastos) -> None:
    ruta = Path(ruta)
    payload = {"version": 1, "gastos": [
        {"fecha": g.fecha.isoformat(), "categoria": g.categoria,
         "monto": f"{g.monto:.2f}", "nota": g.nota} for g in gastos]}
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(dir=ruta.parent, prefix=".gastos-", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, ruta)
    except OSError as e:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)
        raise GastoError(f"No se pudo escribir {ruta}: {e.strerror or e}") from None
