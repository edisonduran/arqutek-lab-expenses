"""Dominio puro: Gasto, validaciones y totales (Decimal)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

CENT = Decimal("0.01")


class GastoError(Exception):
    """Error de dominio con mensaje en español."""


@dataclass(frozen=True)
class Gasto:
    fecha: date
    categoria: str
    monto: Decimal
    nota: str = ""


def parse_monto(texto: str) -> Decimal:
    try:
        valor = Decimal(str(texto).strip())
    except (InvalidOperation, ValueError):
        raise GastoError(f"Monto inválido: '{texto}'. Debe ser un número.") from None
    if not valor.is_finite():
        raise GastoError(f"Monto inválido: '{texto}'. Debe ser un número finito.")
    if valor <= 0:
        raise GastoError(f"Monto inválido: '{texto}'. Debe ser mayor que cero.")
    try:
        q = valor.quantize(CENT, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise GastoError(f"Monto inválido: '{texto}'. Valor demasiado grande.") from None
    if q <= 0:
        raise GastoError(f"Monto inválido: '{texto}'. Debe ser al menos 0.01.")
    return q


def parse_fecha(texto: str) -> date:
    s = str(texto).strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        raise GastoError(f"Fecha inválida: '{texto}'. Use el formato AAAA-MM-DD.")
    try:
        return date.fromisoformat(s)
    except ValueError:
        raise GastoError(f"Fecha inválida: '{texto}'. Esa fecha no existe.") from None


def parse_mes(texto: str) -> tuple[int, int]:
    s = str(texto).strip()
    m = re.fullmatch(r"(\d{4})-(\d{2})", s)
    if not m or not (1 <= int(m.group(2)) <= 12) or int(m.group(1)) < 1:
        raise GastoError(f"Mes inválido: '{texto}'. Use el formato AAAA-MM.")
    return int(m.group(1)), int(m.group(2))


def normalizar_categoria(texto: str) -> str:
    c = str(texto).strip().lower()
    if not c:
        raise GastoError("La categoría no puede estar vacía.")
    return c


def filtrar_mes(gastos, anio: int, mes: int) -> list[Gasto]:
    return [g for g in gastos if g.fecha.year == anio and g.fecha.month == mes]


def totales_por_categoria(gastos) -> dict[str, Decimal]:
    t: dict[str, Decimal] = {}
    for g in gastos:
        t[g.categoria] = t.get(g.categoria, Decimal("0.00")) + g.monto
    return t


def ordenar_categorias(totales) -> list[tuple[str, Decimal]]:
    """Total descendente; nombre ascendente en empates."""
    return sorted(totales.items(), key=lambda kv: (-kv[1], kv[0]))


def ordenar_por_fecha(gastos) -> list[Gasto]:
    """Por fecha ascendente; estable (mismo día conserva el orden de registro)."""
    return sorted(gastos, key=lambda g: g.fecha)


def filtrar_categoria(gastos, categoria: str) -> list[Gasto]:
    c = str(categoria).strip().lower()
    return [g for g in gastos if g.categoria.strip().lower() == c]


def agrupar_por_mes(gastos):
    """Agrupa por AAAA-MM: lista (mes, cantidad, total) en orden cronológico."""
    acc = {}
    for g in gastos:
        k = f"{g.fecha.year:04d}-{g.fecha.month:02d}"
        n, t = acc.get(k, (0, Decimal("0.00")))
        acc[k] = (n + 1, t + g.monto)
    return [(k, acc[k][0], acc[k][1]) for k in sorted(acc)]
