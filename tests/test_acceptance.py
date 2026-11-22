import csv
import json
from datetime import date

import pytest

from gastos.cli import main

HOY = date.today().isoformat()
MES = HOY[:7]


def datos(ruta):
    return json.loads(ruta.read_text())["gastos"]


def sembrar(ruta, items):
    ruta.write_text(json.dumps({"version": 1, "gastos": [
        {"fecha": f, "categoria": c, "monto": m, "nota": n} for f, c, m, n in items]}))


# US-01
def test_us01_registrar_basico_fecha_hoy(ruta_gastos):
    assert main(["registrar", "12.50", "comida"]) == 0
    assert datos(ruta_gastos) == [{"fecha": HOY, "categoria": "comida", "monto": "12.50", "nota": ""}]


def test_us01_fecha_y_nota(ruta_gastos):
    assert main(["registrar", "7", "Transporte", "--fecha", "2026-10-15", "--nota", "taxi"]) == 0
    assert datos(ruta_gastos) == [{"fecha": "2026-10-15", "categoria": "transporte", "monto": "7.00", "nota": "taxi"}]


def test_us01_fecha_invalida(ruta_gastos, capsys):
    main(["registrar", "1", "a"])
    antes = ruta_gastos.read_bytes()
    assert main(["registrar", "5", "a", "--fecha", "2026-13-40"]) == 1
    assert capsys.readouterr().err.strip()
    assert ruta_gastos.read_bytes() == antes


def test_us01_fecha_invalida_sin_archivo(ruta_gastos):
    assert main(["registrar", "5", "a", "--fecha", "2026-13-40"]) == 1
    assert not ruta_gastos.exists()


# US-02
@pytest.mark.parametrize("m", ["-5", "0", "abc", "0.00", ""])
def test_us02_montos_invalidos(ruta_gastos, m, capsys):
    main(["registrar", "1", "a"])
    antes = ruta_gastos.read_bytes()
    assert main(["registrar", m, "a"]) == 1
    assert capsys.readouterr().err.strip()
    assert ruta_gastos.read_bytes() == antes


def test_us02_suma_exacta(ruta_gastos, capsys):
    for _ in range(3):
        assert main(["registrar", "0.1", "x"]) == 0
    assert [g["monto"] for g in datos(ruta_gastos)] == ["0.10"] * 3
    capsys.readouterr()
    assert main(["resumen"]) == 0
    out = capsys.readouterr().out
    assert "total: 0.30" in out


def test_us02_redondeo_dos_decimales(ruta_gastos):
    assert main(["registrar", "10.005", "x"]) == 0
    assert datos(ruta_gastos)[0]["monto"] == "10.01"


# US-03
def test_us03_resumen_una_linea(ruta_gastos, capsys):
    for c, m in [("Comida", "10.00"), ("COMIDA", "5.00"), ("comida", "1.00")]:
        assert main(["registrar", m, c]) == 0
    capsys.readouterr()
    assert main(["resumen"]) == 0
    out = capsys.readouterr().out
    assert out.count("comida") == 1
    assert "comida: 16.00" in out
    assert "Comida" not in out and "COMIDA" not in out


def test_us03_se_guarda_minuscula(ruta_gastos):
    main(["registrar", "1", "Comida"])
    assert datos(ruta_gastos)[0]["categoria"] == "comida"


# US-04
def test_us04_crea_archivo(ruta_gastos):
    assert not ruta_gastos.exists()
    assert main(["registrar", "3", "a"]) == 0
    assert len(datos(ruta_gastos)) == 1


@pytest.mark.parametrize("contenido", [b"{not json", b""])
@pytest.mark.parametrize("cmd", [["registrar", "1", "a"], ["resumen"], ["exportar", "o.csv"]])
def test_us04_corrupto_intacto(ruta_gastos, contenido, cmd, capsys):
    ruta_gastos.write_bytes(contenido)
    assert main(cmd) == 1
    assert capsys.readouterr().err.strip()
    assert ruta_gastos.read_bytes() == contenido


def test_us04_ausente_resumen_exportar(ruta_gastos, tmp_path, capsys):
    assert main(["resumen"]) == 0
    assert main(["exportar", str(tmp_path / "o.csv")]) == 0
    assert not ruta_gastos.exists()


# US-05
def test_us05_resumen_mes_actual(ruta_gastos, capsys):
    sembrar(ruta_gastos, [(HOY, "comida", "10.00", ""), (HOY, "comida", "5.50", ""),
                          (HOY, "transporte", "3.00", "")])
    assert main(["resumen"]) == 0
    out = capsys.readouterr().out
    assert "comida: 15.50" in out and "transporte: 3.00" in out and "total: 18.50" in out


def test_us05_mes_filtra(ruta_gastos, capsys):
    sembrar(ruta_gastos, [("2026-10-05", "a", "4.00", ""), ("2026-11-05", "b", "9.00", "")])
    assert main(["resumen", "--mes", "2026-10"]) == 0
    out = capsys.readouterr().out
    assert "a: 4.00" in out and "total: 4.00" in out and "b:" not in out


def test_us05_mes_vacio(ruta_gastos, capsys):
    sembrar(ruta_gastos, [("2026-10-05", "a", "4.00", "")])
    assert main(["resumen", "--mes", "2025-01"]) == 0
    assert "total: 0.00" in capsys.readouterr().out


@pytest.mark.parametrize("mes", ["2026-13", "abc", "2026-00", "2026-1x"])
def test_us05_mes_invalido(ruta_gastos, mes, capsys):
    assert main(["resumen", "--mes", mes]) == 1
    assert capsys.readouterr().err.strip()


# US-06
def leer_csv(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def test_us06_exporta_mes_actual(ruta_gastos, tmp_path):
    sembrar(ruta_gastos, [(HOY, "comida", "10.00", "x"), ("2020-01-01", "viejo", "1.00", "")])
    out = tmp_path / "salida.csv"
    assert main(["exportar", str(out)]) == 0
    assert leer_csv(out) == [["fecha", "categoria", "monto", "nota"], [HOY, "comida", "10.00", "x"]]


def test_us06_mes_filtra(ruta_gastos, tmp_path):
    sembrar(ruta_gastos, [("2026-10-05", "a", "4.00", ""), ("2026-11-05", "b", "9.00", "")])
    out = tmp_path / "s.csv"
    assert main(["exportar", str(out), "--mes", "2026-10"]) == 0
    assert leer_csv(out) == [["fecha", "categoria", "monto", "nota"], ["2026-10-05", "a", "4.00", ""]]


def test_us06_escapa_nota(ruta_gastos, tmp_path):
    nota = 'pan, "integral"'
    sembrar(ruta_gastos, [(HOY, "a", "1.00", nota)])
    out = tmp_path / "s.csv"
    assert main(["exportar", str(out)]) == 0
    assert '"pan, ""integral"""' in out.read_text()
    assert leer_csv(out)[1][3] == nota


def test_us06_ruta_no_escribible(ruta_gastos, tmp_path, capsys):
    sembrar(ruta_gastos, [(HOY, "a", "1.00", "")])
    assert main(["exportar", "/no/existe/x.csv"]) == 1
    assert capsys.readouterr().err.strip()


def test_us06_mes_invalido(ruta_gastos, tmp_path):
    assert main(["exportar", str(tmp_path / "o.csv"), "--mes", "2026-13"]) == 1
    assert not (tmp_path / "o.csv").exists()


# US-07
def test_us07_aislamiento(ruta_gastos, tmp_path):
    main(["registrar", "1", "a"])
    assert ruta_gastos.parent == tmp_path
    assert ruta_gastos.exists()
