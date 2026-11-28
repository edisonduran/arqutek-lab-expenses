"""Aceptación US-17..US-21: comando `gastos meses`."""
import json
from pathlib import Path

from gastos import cli

RAIZ = Path(__file__).resolve().parents[1]


def _w(p, items):
    p.write_text(json.dumps({"version": 1, "gastos": [
        {"fecha": f, "categoria": c, "monto": m, "nota": ""} for f, c, m in items]}))


BASE = [("2026-11-03", "comida", "10.00"), ("2026-11-10", "comida", "5.50"),
        ("2026-09-15", "ocio", "20.00"), ("2026-10-05", "transporte", "3.50")]


def test_us17_lineas_orden_y_total(ruta_gastos, capsys):
    _w(ruta_gastos, BASE)
    assert cli.main(["meses"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "2026-09: 1 gastos, total: 20.00", "2026-10: 1 gastos, total: 3.50",
        "2026-11: 2 gastos, total: 15.50", "total: 39.00"]


def test_us17_orden_cronologico_entre_anios(ruta_gastos, capsys):
    _w(ruta_gastos, [("2026-01-01", "comida", "2.00"), ("2025-12-31", "comida", "1.00")])
    assert cli.main(["meses"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0].startswith("2025-12") and out[1].startswith("2026-01")


def test_us17_mes_sin_gastos_no_aparece(ruta_gastos, capsys):
    _w(ruta_gastos, [("2026-09-01", "ocio", "1.00"), ("2026-11-01", "ocio", "1.00")])
    cli.main(["meses"])
    assert "2026-10" not in capsys.readouterr().out


FILT = [("2026-10-01", "comida", "10.00"), ("2026-10-02", "ocio", "5.00"),
        ("2026-11-01", "Comida", "4.50"), ("2026-11-02", "ocio", "7.00")]


def test_us18_filtro_categoria(ruta_gastos, capsys):
    _w(ruta_gastos, FILT)
    assert cli.main(["meses", "--categoria", "comida"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "2026-10: 1 gastos, total: 10.00", "2026-11: 1 gastos, total: 4.50", "total: 14.50"]


def test_us18_mayusculas(ruta_gastos, capsys):
    _w(ruta_gastos, FILT)
    assert cli.main(["meses", "--categoria", "COMIDA"]) == 0
    assert capsys.readouterr().out.splitlines()[-1] == "total: 14.50"


def test_us18_categoria_solo_un_mes(ruta_gastos, capsys):
    _w(ruta_gastos, FILT + [("2026-10-09", "viajes", "9.00")])
    cli.main(["meses", "--categoria", "viajes"])
    assert capsys.readouterr().out.splitlines() == [
        "2026-10: 1 gastos, total: 9.00", "total: 9.00"]


def test_us19_sin_archivo(ruta_gastos, capsys):
    assert cli.main(["meses"]) == 0
    cap = capsys.readouterr()
    assert cap.out.strip() == "No hay gastos"


def test_us19_categoria_sin_coincidencias(ruta_gastos, capsys):
    _w(ruta_gastos, [("2026-10-01", "comida", "10.00")])
    assert cli.main(["meses", "--categoria", "viajes"]) == 0
    assert capsys.readouterr().out.strip() == "No hay gastos"


def test_us19_argumentos_invalidos(ruta_gastos, capsys):
    _w(ruta_gastos, BASE)
    for args in (["meses", "--foo"], ["meses", "--mes", "2026-10"]):
        capsys.readouterr()
        assert cli.main(args) == 1
        cap = capsys.readouterr()
        assert cap.err.strip() and cap.out == ""


def test_us20_no_crea_archivo(ruta_gastos):
    assert cli.main(["meses"]) == 0
    assert not ruta_gastos.exists()


def test_us20_no_modifica(ruta_gastos):
    _w(ruta_gastos, BASE[:2])
    antes = ruta_gastos.read_bytes()
    assert cli.main(["meses"]) == 0
    assert ruta_gastos.read_bytes() == antes


def test_us20_json_corrupto(ruta_gastos, capsys):
    ruta_gastos.write_bytes(b"{corrupto")
    assert cli.main(["meses"]) == 1
    cap = capsys.readouterr()
    assert cap.err.strip() and cap.out == ""
    assert ruta_gastos.read_bytes() == b"{corrupto"


def test_us21_docs():
    readme = (RAIZ / "README.md").read_text()
    assert "gastos meses" in readme and "gastos meses --categoria comida" in readme
    assert "`resumen`, `categorias`, `listar`, `meses` y `exportar`" in readme
    cl = (RAIZ / "CHANGELOG.md").read_text()
    sp = cl.index("Sin publicar")
    v = cl.index("0.1.0")
    assert sp < cl.index("meses") < v
