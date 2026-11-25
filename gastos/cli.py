"""Interfaz argparse; errores por stderr; 0 ok, 1 error."""
from __future__ import annotations

import argparse
import sys

from gastos import service, storage
from gastos.domain import GastoError


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise GastoError(f"Error de uso: {message}")


def build_parser() -> argparse.ArgumentParser:
    p = _Parser(prog="gastos", description="Control de gastos personales")
    sub = p.add_subparsers(dest="cmd", required=True, parser_class=_Parser)
    r = sub.add_parser("registrar", help="registrar un gasto")
    r.add_argument("monto")
    r.add_argument("categoria")
    r.add_argument("--fecha")
    r.add_argument("--nota", default="")
    s = sub.add_parser("resumen", help="resumen mensual")
    s.add_argument("--mes")
    e = sub.add_parser("exportar", help="exportar a CSV")
    e.add_argument("archivo")
    e.add_argument("--mes")
    li = sub.add_parser("listar", help="listar gastos de un mes")
    li.add_argument("--mes")
    li.add_argument("--categoria")
    return p


def main(argv=None) -> int:
    try:
        args = build_parser().parse_args(argv)
        ruta = storage.ruta_por_defecto()
        if args.cmd == "registrar":
            g = service.registrar(ruta, args.monto, args.categoria, args.fecha, args.nota)
            print(f"Registrado: {g.fecha.isoformat()} {g.categoria} {g.monto:.2f}")
        elif args.cmd == "resumen":
            tot, total = service.resumen(ruta, args.mes)
            for c in sorted(tot):
                print(f"{c}: {tot[c]:.2f}")
            print(f"total: {total:.2f}")
        elif args.cmd == "listar":
            sel, total = service.listar(ruta, args.mes, args.categoria)
            if not sel:
                print("No hay gastos para mostrar")
            else:
                for g in sel:
                    print(f"{g.fecha.isoformat()} {g.categoria} {g.monto:.2f} {g.nota}".rstrip())
                print(f"gastos: {len(sel)}")
                print(f"total: {total:.2f}")
        else:
            n = service.exportar(ruta, args.archivo, args.mes)
            print(f"Exportados {n} gastos a {args.archivo}")
        return 0
    except GastoError as e:
        print(str(e), file=sys.stderr)
        return 1
    except SystemExit as e:  # --help => 0
        return e.code if isinstance(e.code, int) else 0
