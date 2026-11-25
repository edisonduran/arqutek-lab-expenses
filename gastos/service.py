"""Casos de uso: registrar, resumen, exportar, listar."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from gastos import domain, storage
from gastos.exporter import exportar_csv


def _mes(mes, hoy):
    if mes is None:
        h = hoy or date.today()
        return h.year, h.month
    return domain.parse_mes(mes)


def registrar(ruta, monto, categoria, fecha=None, nota="", hoy=None) -> domain.Gasto:
    m = domain.parse_monto(monto)
    cat = domain.normalizar_categoria(categoria)
    f = domain.parse_fecha(fecha) if fecha is not None else (hoy or date.today())
    g = domain.Gasto(f, cat, m, nota or "")
    gastos = storage.cargar(ruta)
    gastos.append(g)
    storage.guardar(ruta, gastos)
    return g


def resumen(ruta, mes=None, hoy=None) -> tuple[dict[str, Decimal], Decimal]:
    a, m = _mes(mes, hoy)
    sel = domain.filtrar_mes(storage.cargar(ruta), a, m)
    t = domain.totales_por_categoria(sel)
    return t, sum(t.values(), Decimal("0.00"))


def exportar(ruta, destino, mes=None, hoy=None) -> int:
    a, m = _mes(mes, hoy)
    d = Path(destino)
    if d.exists():
        raise domain.GastoError(f"Error: {destino} ya existe; no se sobrescribe")
    sel = domain.filtrar_mes(storage.cargar(ruta), a, m)
    exportar_csv(Path(destino), sel)
    return len(sel)


def listar(ruta, mes=None, categoria=None, hoy=None) -> tuple[list[domain.Gasto], Decimal]:
    a, m = _mes(mes, hoy)
    if categoria is not None:
        domain.normalizar_categoria(categoria)
    sel = domain.filtrar_mes(storage.cargar(ruta), a, m)
    if categoria is not None:
        sel = domain.filtrar_categoria(sel, categoria)
    sel = domain.ordenar_por_fecha(sel)
    return sel, sum((g.monto for g in sel), Decimal("0.00"))
