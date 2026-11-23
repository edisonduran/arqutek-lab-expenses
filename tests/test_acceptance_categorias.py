"""Aceptación de `gastos categorias` (US-08 a US-11)."""
import json
from datetime import date
from pathlib import Path

from gastos.cli import main

MES = date.today().strftime("%Y-%m")


def _datos(ruta, items):
    ruta.write_text(json.dumps({"version": 1, "gastos": [
        {"fecha": f, "categoria": c, "monto": m, "nota": ""} for f, c, m in items]}))


def test_us08_orden_descendente_y_total(ruta_gastos, capsys):
    _datos(ruta_gastos, [(MES + "-01", "comida", "10.00"), (MES + "-02", "comida", "5.50"),
                         (MES + "-03", "transporte", "3.00"), (MES + "-04", "ocio", "20.00")])
    assert main(["categorias"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "ocio: 20.00", "comida: 15.50", "transporte: 3.00", "total: 38.50"]


def test_us08_filtra_por_mes(ruta_gastos, capsys):
    _datos(ruta_gastos, [(MES + "-01", "comida", "10.00"), ("2026-10-05", "comida", "7.00"),
                         ("2026-10-06", "ocio", "1.00")])
    assert main(["categorias", "--mes", "2026-10"]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "comida: 7.00", "ocio: 1.00", "total: 8.00"]


def test_us08_empate_alfabetico(ruta_gastos, capsys):
    _datos(ruta_gastos, [("2026-10-01", "b", "4.00"), ("2026-10-02", "a", "4.00")])
    assert main(["categorias", "--mes", "2026-10"]) == 0
    assert capsys.readouterr().out.splitlines() == ["a: 4.00", "b: 4.00", "total: 8.00"]


def test_us08_mayusculas_una_linea(ruta_gastos, capsys):
    _datos(ruta_gastos, [("2026-10-01", "Comida", "1.00"), ("2026-10-02", "COMIDA", "2.00")])
    assert main(["categorias", "--mes", "2026-10"]) == 0
    assert capsys.readouterr().out.splitlines() == ["comida: 3.00", "total: 3.00"]


def test_us09_mes_vacio(ruta_gastos, capsys):
    _datos(ruta_gastos, [("2026-10-01", "a", "1.00")])
    assert main(["categorias", "--mes", "2026-09"]) == 0
    assert capsys.readouterr().out.strip() == "No hay gastos en 2026-09"


def test_us09_sin_archivo(ruta_gastos, capsys):
    assert main(["categorias", "--mes", "2026-09"]) == 0
    assert capsys.readouterr().out.strip() == "No hay gastos en 2026-09"


def test_us09_mes_invalido_igual_que_resumen(ruta_gastos, capsys):
    for mes in ("2026-13", "abc"):
        assert main(["resumen", "--mes", mes]) == 1
        esperado = capsys.readouterr().err
        assert "inválido" in esperado
        assert main(["categorias", "--mes", mes]) == 1
        cap = capsys.readouterr()
        assert cap.err == esperado and cap.out == ""


def test_us09_argumento_desconocido(ruta_gastos, capsys):
    assert main(["categorias", "--foo"]) == 1
    cap = capsys.readouterr()
    assert cap.err and cap.out == ""


def test_us10_sin_archivo_no_se_crea(ruta_gastos):
    assert main(["categorias"]) == 0
    assert not ruta_gastos.exists()


def test_us10_archivo_valido_intacto(ruta_gastos):
    _datos(ruta_gastos, [("2026-10-01", "a", "1.00"), ("2026-10-02", "b", "2.00")])
    antes = ruta_gastos.read_bytes()
    assert main(["categorias", "--mes", "2026-10"]) == 0
    assert ruta_gastos.read_bytes() == antes


def test_us10_json_corrupto(ruta_gastos, capsys):
    ruta_gastos.write_text("{corrupto")
    assert main(["categorias"]) == 1
    assert capsys.readouterr().err
    assert ruta_gastos.read_text() == "{corrupto"


def test_us11_readme_documenta_categorias():
    r = (Path(__file__).resolve().parent.parent / "README.md").read_text()
    assert "gastos categorias" in r
    assert "gastos categorias --mes 2026-10" in r
    linea = [l for l in r.splitlines() if "no crean" in l and "categorias" in l]
    assert linea and "resumen" in linea[0] and "exportar" in linea[0]
