"""Pruebas de aceptación de listar (US-08 a US-11)."""
import json
from datetime import date
from pathlib import Path

import pytest

from gastos import service
from gastos.cli import main

DATOS = [
    ("2026-11-20", "comida", "10.00", "almuerzo"),
    ("2026-11-03", "transporte", "3.00", "bus"),
    ("2026-11-10", "comida", "5.50", ""),
    ("2026-10-15", "comida", "8.00", "cena"),
]


def sembrar(ruta, items=DATOS):
    ruta.write_text(json.dumps({"version": 1, "gastos": [
        {"fecha": f, "categoria": c, "monto": m, "nota": n} for f, c, m, n in items]}))


@pytest.fixture(autouse=True)
def hoy_fijo(monkeypatch):
    class D(date):
        @classmethod
        def today(cls):
            return cls(2026, 11, 25)
    monkeypatch.setattr(service, "date", D)


def out(capsys):
    return capsys.readouterr().out.splitlines()


# US-08
def test_us08_solo_mes_actual_ordenado_con_formato(ruta_gastos, capsys):
    sembrar(ruta_gastos)
    assert main(["listar"]) == 0
    assert out(capsys) == [
        "2026-11-03 transporte 3.00 bus",
        "2026-11-10 comida 5.50",
        "2026-11-20 comida 10.00 almuerzo",
        "gastos: 3", "total: 18.50"]


def test_us08_misma_fecha_orden_de_registro(ruta_gastos, capsys):
    sembrar(ruta_gastos, [("2026-11-05", "b", "1", "x"), ("2026-11-01", "z", "1", "q"),
                          ("2026-11-05", "a", "2", "y"), ("2026-11-05", "c", "3", "w")])
    assert main(["listar"]) == 0
    cats = [l.split()[1] for l in out(capsys)[:4]]
    assert cats == ["z", "b", "a", "c"]


def test_us08_pie_ultima_linea(ruta_gastos, capsys):
    sembrar(ruta_gastos)
    main(["listar"])
    assert out(capsys)[-2:] == ["gastos: 3", "total: 18.50"]


def test_us08_mes_octubre(ruta_gastos, capsys):
    sembrar(ruta_gastos)
    assert main(["listar", "--mes", "2026-10"]) == 0
    assert out(capsys) == ["2026-10-15 comida 8.00 cena", "gastos: 1", "total: 8.00"]


@pytest.mark.parametrize("mes", ["2026-13", "abc"])
def test_us08_mes_invalido(ruta_gastos, capsys, mes):
    sembrar(ruta_gastos)
    assert main(["listar", "--mes", mes]) == 1
    c = capsys.readouterr()
    assert c.out == "" and c.err.strip()
    # mismo mensaje que resumen
    main(["resumen", "--mes", mes])
    assert capsys.readouterr().err == c.err


def test_us08_sin_nota_no_se_rompe(ruta_gastos, capsys):
    sembrar(ruta_gastos, [("2026-11-10", "comida", "5.50", "")])
    assert main(["listar"]) == 0
    l = out(capsys)
    assert l[0].startswith("2026-11-10 comida 5.50") and l[0].split() == ["2026-11-10", "comida", "5.50"]


# US-09
SEED9 = [("2026-11-01", "comida", "10.00", ""), ("2026-11-02", "Comida", "5.50", ""),
         ("2026-11-03", "transporte", "3.00", ""), ("2026-10-04", "comida", "8.00", "")]


@pytest.mark.parametrize("cat", ["COMIDA", "comida", "Comida"])
def test_us09_filtro_categoria_insensible(ruta_gastos, capsys, cat):
    sembrar(ruta_gastos, SEED9)
    assert main(["listar", "--categoria", cat]) == 0
    l = out(capsys)
    assert len(l) == 4 and "transporte" not in "".join(l)
    assert l[-2:] == ["gastos: 2", "total: 15.50"]


def test_us09_ambos_filtros(ruta_gastos, capsys):
    sembrar(ruta_gastos, SEED9)
    assert main(["listar", "--categoria", "Comida", "--mes", "2026-10"]) == 0
    assert out(capsys) == ["2026-10-04 comida 8.00", "gastos: 1", "total: 8.00"]


def test_us09_categoria_sin_gastos(ruta_gastos, capsys):
    sembrar(ruta_gastos, SEED9)
    assert main(["listar", "--categoria", "inexistente"]) == 0
    assert out(capsys) == ["No hay gastos para mostrar"]


@pytest.mark.parametrize("cat", ["", "   "])
def test_us09_categoria_invalida_mismo_mensaje_que_registrar(ruta_gastos, capsys, cat):
    sembrar(ruta_gastos, SEED9)
    assert main(["listar", "--categoria", cat]) == 1
    err = capsys.readouterr().err
    assert main(["registrar", "1", cat]) == 1
    assert capsys.readouterr().err == err and err.strip()


# US-10
def test_us10_mes_sin_gastos_y_sin_pie(ruta_gastos, capsys):
    sembrar(ruta_gastos, [("2026-10-15", "comida", "8.00", "x")])
    assert main(["listar"]) == 0
    assert out(capsys) == ["No hay gastos para mostrar"]


def test_us10_archivo_inexistente_no_se_crea(ruta_gastos, capsys):
    assert main(["listar"]) == 0
    assert out(capsys) == ["No hay gastos para mostrar"]
    assert not ruta_gastos.exists()
    assert list(Path(ruta_gastos.parent).iterdir()) == []


@pytest.mark.parametrize("args", [[], ["--mes", "2026-10"], ["--categoria", "comida"],
                                  ["--mes", "2026-01", "--categoria", "x"], ["--mes", "abc"]])
def test_us10_archivo_intacto(ruta_gastos, capsys, args):
    sembrar(ruta_gastos)
    antes = ruta_gastos.read_bytes()
    main(["listar", *args])
    assert ruta_gastos.read_bytes() == antes


def test_us10_json_corrupto(ruta_gastos, capsys):
    ruta_gastos.write_bytes(b"{corrupto")
    assert main(["listar"]) == 1
    c = capsys.readouterr()
    assert c.err.strip() and c.out == ""
    assert ruta_gastos.read_bytes() == b"{corrupto"


def test_us10_opcion_desconocida(ruta_gastos, capsys):
    sembrar(ruta_gastos)
    assert main(["listar", "--foo"]) == 1
    assert capsys.readouterr().err.startswith("Error de uso:")


# US-11
def test_us11_readme_documenta_listar():
    t = (Path(__file__).resolve().parent.parent / "README.md").read_text()
    assert "gastos listar" in t and "gastos listar --mes 2026-10" in t and "--categoria" in t
    assert "listar" in t and "no crean" in t and "modifica" in t
