import json

from gastos.cli import main


def _datos(tmp_path, monkeypatch, gastos):
    f = tmp_path / "gastos.json"
    monkeypatch.setenv("GASTOS_FILE", str(f))
    if gastos is not None:
        f.write_text(json.dumps({"version": 1, "gastos": [
            {"fecha": a, "categoria": b, "monto": c, "nota": d} for a, b, c, d in gastos]}))
    return f


G = [("2026-11-20", "ocio", "20.00", "cine"), ("2026-11-03", "comida", "10.00", ""),
     ("2026-11-10", "transporte", "3.50", "taxi"), ("2026-11-10", "Comida", "1.00", "x"),
     ("2026-10-05", "comida", "7.00", "")]


def test_orden_pie_y_filtros(tmp_path, monkeypatch, capsys):
    _datos(tmp_path, monkeypatch, G)
    assert main(["listar", "--mes", "2026-11"]) == 0
    l = capsys.readouterr().out.splitlines()
    assert l[0] == "2026-11-03 comida 10.00"
    assert l[2].startswith("2026-11-10 Comida") or l[1].startswith("2026-11-10 transporte")
    assert l[-1] == "4 gastos, total: 34.50"
    main(["listar", "--mes", "2026-11", "--categoria", "COMIDA"])
    assert capsys.readouterr().out.splitlines()[-1] == "2 gastos, total: 11.00"
    main(["listar", "--mes", "2026-10", "--categoria", "comida"])
    assert capsys.readouterr().out.splitlines()[-1] == "1 gastos, total: 7.00"


def test_vacio_e_invalidos(tmp_path, monkeypatch, capsys):
    f = _datos(tmp_path, monkeypatch, None)
    assert main(["listar", "--mes", "2026-09"]) == 0
    assert capsys.readouterr().out == "No hay gastos en 2026-09\n"
    assert not f.exists()
    assert main(["listar", "--mes", "2026-13"]) == 1
    assert "Mes inválido" in capsys.readouterr().err
    assert main(["listar", "--foo"]) == 1


def test_corrupto_intacto(tmp_path, monkeypatch, capsys):
    f = _datos(tmp_path, monkeypatch, None)
    f.write_text("{corrupto")
    assert main(["listar"]) == 1
    assert capsys.readouterr().err
    assert f.read_text() == "{corrupto"


def test_valido_sin_cambios(tmp_path, monkeypatch):
    f = _datos(tmp_path, monkeypatch, G)
    antes = f.read_bytes()
    main(["listar"])
    assert f.read_bytes() == antes
