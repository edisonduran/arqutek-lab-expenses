import csv
import json

import pytest

from gastos.cli import main
from gastos.domain import parse_monto


def test_registrar_ok(ruta_gastos):
    assert main(["registrar", "12.50", "Comida", "--fecha", "2026-10-15", "--nota", "taxi"]) == 0
    d = json.loads(ruta_gastos.read_text())
    assert d["gastos"][0] == {"fecha": "2026-10-15", "categoria": "comida", "monto": "12.50", "nota": "taxi"}


@pytest.mark.parametrize("m", ["-5", "0", "abc", "nan"])
def test_monto_invalido(ruta_gastos, m, capsys):
    assert main(["registrar", m, "x"]) == 1
    assert not ruta_gastos.exists()


def test_fecha_invalida_no_modifica(ruta_gastos):
    main(["registrar", "1", "a"])
    antes = ruta_gastos.read_bytes()
    assert main(["registrar", "1", "a", "--fecha", "2026-13-40"]) == 1
    assert ruta_gastos.read_bytes() == antes


def test_redondeo():
    assert str(parse_monto("10.005")) == "10.01"


def test_resumen_exacto_y_mes(ruta_gastos, capsys):
    for _ in range(3):
        main(["registrar", "0.1", "Comida", "--fecha", "2026-11-01"])
    main(["registrar", "5", "COMIDA", "--fecha", "2026-10-01"])
    capsys.readouterr()
    assert main(["resumen", "--mes", "2026-11"]) == 0
    assert "total: 0.30" in capsys.readouterr().out
    assert main(["resumen", "--mes", "2026-13"]) == 1
    assert main(["resumen", "--mes", "abc"]) == 1


def test_resumen_exportar_sin_archivo(ruta_gastos, tmp_path, capsys):
    assert main(["resumen"]) == 0
    assert "total: 0.00" in capsys.readouterr().out
    assert main(["exportar", str(tmp_path / "o.csv")]) == 0
    assert not ruta_gastos.exists()


@pytest.mark.parametrize("contenido", [b"{not json", b""])
def test_corrupto_intacto(ruta_gastos, contenido, tmp_path):
    ruta_gastos.write_bytes(contenido)
    for cmd in (["registrar", "1", "a"], ["resumen"], ["exportar", str(tmp_path / "o.csv")]):
        assert main(cmd) == 1
        assert ruta_gastos.read_bytes() == contenido


def test_exportar_csv(ruta_gastos, tmp_path):
    main(["registrar", "3", "pan", "--fecha", "2026-10-02", "--nota", 'pan, "integral"'])
    main(["registrar", "4", "pan", "--fecha", "2026-09-02"])
    out = tmp_path / "s.csv"
    assert main(["exportar", str(out), "--mes", "2026-10"]) == 0
    rows = list(csv.reader(out.open(newline="")))
    assert rows == [["fecha", "categoria", "monto", "nota"], ["2026-10-02", "pan", "3.00", 'pan, "integral"']]


def test_exportar_ruta_invalida(ruta_gastos):
    assert main(["exportar", "/no/existe/x.csv"]) == 1
