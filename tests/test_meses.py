import json

import pytest

from gastos import cli


def _w(p, items):
    p.write_text(json.dumps({"version": 1, "gastos": [
        {"fecha": f, "categoria": c, "monto": m, "nota": ""} for f, c, m in items]}))


@pytest.fixture
def f(tmp_path, monkeypatch):
    p = tmp_path / "gastos.json"
    monkeypatch.setenv("GASTOS_FILE", str(p))
    return p


def test_meses_orden_y_totales(f, capsys):
    _w(f, [("2026-11-03", "comida", "10.00"), ("2026-11-10", "Comida", "5.50"),
           ("2026-09-15", "ocio", "20.00"), ("2025-12-31", "comida", "1.00")])
    assert cli.main(["meses"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "2025-12: 1 gastos, total: 1.00", "2026-09: 1 gastos, total: 20.00",
        "2026-11: 2 gastos, total: 15.50", "total: 36.50"]
    assert cli.main(["meses", "--categoria", "COMIDA"]) == 0
    assert capsys.readouterr().out.splitlines()[-1] == "total: 16.50"


def test_meses_vacio_y_no_crea(f, capsys):
    assert cli.main(["meses"]) == 0
    assert capsys.readouterr().out.strip() == "No hay gastos"
    assert not f.exists()


def test_meses_errores(f, capsys):
    assert cli.main(["meses", "--foo"]) == 1
    assert cli.main(["meses", "--mes", "2026-10"]) == 1
    f.write_text("{corrupto")
    assert cli.main(["meses"]) == 1
    assert f.read_text() == "{corrupto"
