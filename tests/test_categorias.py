"""Pruebas del comando `gastos categorias` (US-08 a US-11)."""
import json

from gastos.cli import main


def _datos(ruta, items):
    ruta.write_text(json.dumps({"version": 1, "gastos": [
        {"fecha": f, "categoria": c, "monto": m, "nota": ""} for f, c, m in items]}))


def test_orden_total_empate_y_mayusculas(ruta_gastos, capsys):
    from datetime import date
    mes = date.today().strftime("%Y-%m")
    _datos(ruta_gastos, [(mes + "-01", "comida", "10.00"), (mes + "-02", "Comida", "5.50"),
                         (mes + "-03", "COMIDA", "0.00"), (mes + "-04", "b", "4.00"),
                         (mes + "-05", "a", "4.00"), (mes + "-06", "ocio", "20.00"),
                         ("2020-01-01", "x", "9.00")])
    assert main(["categorias"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "ocio: 20.00", "comida: 15.50", "a: 4.00", "b: 4.00", "total: 43.50"]


def test_mes_vacio_y_sin_archivo(ruta_gastos, capsys):
    assert main(["categorias", "--mes", "2026-09"]) == 0
    assert capsys.readouterr().out.strip() == "No hay gastos en 2026-09"
    assert not ruta_gastos.exists()


def test_mes_invalido_y_uso(ruta_gastos, capsys):
    for args in (["--mes", "2026-13"], ["--mes", "abc"], ["--foo"]):
        assert main(["categorias", *args]) == 1
        assert capsys.readouterr().err


def test_no_modifica_y_corrupto(ruta_gastos):
    _datos(ruta_gastos, [("2026-10-01", "a", "1.00"), ("2026-10-02", "b", "2.00")])
    antes = ruta_gastos.read_bytes()
    assert main(["categorias", "--mes", "2026-10"]) == 0
    assert ruta_gastos.read_bytes() == antes
    ruta_gastos.write_text("{corrupto")
    assert main(["categorias"]) == 1
    assert ruta_gastos.read_text() == "{corrupto"
