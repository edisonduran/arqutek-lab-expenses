import json
from datetime import date

from gastos import service
from gastos.cli import main

DATOS = [
    ("2026-11-20", "comida", "10.00", "almuerzo"),
    ("2026-11-03", "transporte", "3.00", "bus"),
    ("2026-11-10", "comida", "5.50", ""),
    ("2026-10-15", "comida", "8.00", "cena"),
]


def _escribir(ruta, datos=DATOS):
    ruta.write_text(json.dumps({"version": 1, "gastos": [
        {"fecha": f, "categoria": c, "monto": m, "nota": n} for f, c, m, n in datos]}))


def test_orden_mes_y_pie(ruta_gastos, capsys):
    _escribir(ruta_gastos)
    assert main(["listar", "--mes", "2026-11"]) == 0
    lin = capsys.readouterr().out.splitlines()
    assert lin[0].startswith("2026-11-03") and lin[1].startswith("2026-11-10")
    assert lin[2] == "2026-11-20 comida 10.00 almuerzo"
    assert lin[-2:] == ["gastos: 3", "total: 18.50"]


def test_misma_fecha_orden_registro(ruta_gastos):
    _escribir(ruta_gastos, [("2026-11-01", "a", "1", "x"), ("2026-11-01", "b", "2", "y")])
    sel, _ = service.listar(ruta_gastos, hoy=date(2026, 11, 25))
    assert [g.categoria for g in sel] == ["a", "b"]


def test_mes_octubre_y_categoria(ruta_gastos, capsys):
    _escribir(ruta_gastos)
    assert main(["listar", "--mes", "2026-10", "--categoria", "COMIDA"]) == 0
    assert "gastos: 1" in capsys.readouterr().out
    assert main(["listar", "--mes", "2026-11", "--categoria", "Comida"]) == 0
    assert "total: 15.50" in capsys.readouterr().out


def test_sin_gastos(ruta_gastos, capsys):
    _escribir(ruta_gastos)
    assert main(["listar", "--mes", "2026-01"]) == 0
    out = capsys.readouterr().out
    assert "No hay gastos para mostrar" in out and "total" not in out


def test_inexistente_no_se_crea(ruta_gastos, capsys):
    assert main(["listar"]) == 0
    assert not ruta_gastos.exists()


def test_errores(ruta_gastos, capsys):
    for args in (["--mes", "2026-13"], ["--mes", "abc"], ["--categoria", "  "], ["--foo"]):
        assert main(["listar", *args]) == 1
    assert "Error de uso" in capsys.readouterr().err


def test_corrupto_intacto(ruta_gastos, capsys):
    ruta_gastos.write_bytes(b"{corrupto")
    assert main(["listar"]) == 1
    assert capsys.readouterr().err
    assert ruta_gastos.read_bytes() == b"{corrupto"
