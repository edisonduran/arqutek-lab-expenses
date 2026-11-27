"""Importación desde CSV (solo lectura del CSV; todo o nada)."""
from __future__ import annotations

import csv
import io
from pathlib import Path

from gastos import domain
from gastos.domain import Gasto, GastoError

CABECERA = ["fecha", "categoria", "monto", "nota"]


def leer_csv(origen: Path) -> list[Gasto]:
    origen = Path(origen)
    gastos: list[Gasto] = []
    try:
        with open(origen, "r", encoding="utf-8", newline="") as f:
            texto = f.read()
            if "\ufffd" in texto:
                raise UnicodeDecodeError("utf-8", b"", 0, 1, "carácter de reemplazo")
            lector = csv.reader(io.StringIO(texto, newline=""))
            cab = next(lector, None)
            if cab is None:
                raise GastoError(f"El CSV {origen} está vacío; se esperaba la cabecera fecha,categoria,monto,nota")
            if cab != CABECERA:
                raise GastoError(f"Cabecera inválida en {origen}; se esperaba fecha,categoria,monto,nota")
            for n, fila in enumerate(lector, start=1):
                if len(fila) != 4:
                    raise GastoError(f"Fila {n}: se esperaban 4 columnas y hay {len(fila)}")
                try:
                    fecha = domain.parse_fecha(fila[0])
                    cat = domain.normalizar_categoria(fila[1])
                    monto = domain.parse_monto(fila[2])
                    if monto != domain.parse_monto_exacto(fila[2]):
                        raise GastoError(f"Monto inválido: '{fila[2]}'. Use como máximo dos decimales.")
                except GastoError as e:
                    raise GastoError(f"Fila {n}: {e}") from None
                gastos.append(Gasto(fecha, cat, monto, fila[3]))
    except FileNotFoundError:
        raise GastoError(f"No existe el archivo CSV: {origen}") from None
    except UnicodeDecodeError:
        raise GastoError(f"No se pudo leer {origen}: no es UTF-8 válido") from None
    except csv.Error as e:
        raise GastoError(f"No se pudo leer {origen}: CSV inválido ({e})") from None
    except OSError as e:
        raise GastoError(f"No se pudo leer {origen}: {e.strerror or e}") from None
    return gastos
