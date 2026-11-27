import json
import os

from gastos.cli import main

H = "fecha,categoria,monto,nota\n"


def csv_(tmp_path, texto, name="in.csv"):
    p = tmp_path / name
    p.write_bytes(texto if isinstance(texto, bytes) else texto.encode())
    return p


def test_valida_y_total(ruta_gastos, tmp_path, capsys):
    p = csv_(tmp_path, H + '2026-11-03,Comida,10,\n2026-11-10,transporte,3.5,"almuerzo, ""menú"""\n')
    assert main(["importar", str(p)]) == 0
    assert "Importados 2 gastos, total: 13.50" in capsys.readouterr().out
    g = json.loads(ruta_gastos.read_text())["gastos"]
    assert g[0]["monto"] == "10.00" and g[0]["categoria"] == "comida"
    assert g[1]["nota"] == 'almuerzo, "menú"'


def test_solo_cabecera(ruta_gastos, tmp_path, capsys):
    assert main(["importar", str(csv_(tmp_path, H))]) == 0
    assert "Importados 0 gastos, total: 0.00" in capsys.readouterr().out
    assert not ruta_gastos.exists()


def test_todo_o_nada(ruta_gastos, tmp_path, capsys):
    p = csv_(tmp_path, H + "2026-11-01,a,1,\n" * 5 + "2026-13-40,a,1,\n2026-13-41,a,1,\n")
    assert main(["importar", str(p)]) == 1
    assert "Fila 6" in capsys.readouterr().err
    assert not ruta_gastos.exists()


def test_montos_y_categoria_invalidos(ruta_gastos, tmp_path, capsys):
    for fila in ["2026-11-01,a,0,", "2026-11-01,a,-5,", "2026-11-01,a,abc,", "2026-11-01,a,1.234,", "2026-11-01,   ,1,"]:
        assert main(["importar", str(csv_(tmp_path, H + fila + "\n"))]) == 1
        assert "Fila 1" in capsys.readouterr().err
    assert not ruta_gastos.exists()


def test_errores_archivo(ruta_gastos, tmp_path, capsys):
    assert main(["importar", str(tmp_path / "no.csv")]) == 1
    assert main(["importar", str(csv_(tmp_path, "fecha,categoria,monto\n"))]) == 1
    assert main(["importar", str(csv_(tmp_path, ""))]) == 1
    assert main(["importar", str(tmp_path)]) == 1
    assert main(["importar", str(csv_(tmp_path, H.encode() + "2026-11-01,café,1,\n".encode("latin-1")))]) == 1
    assert main(["importar", str(csv_(tmp_path, H + "a,b\n"))]) == 1
    assert "Fila 1" in capsys.readouterr().err
    assert not ruta_gastos.exists()


def test_csv_intacto(ruta_gastos, tmp_path):
    for t in (H + "2026-11-01,a,1,x\n", H + "bad,a,1,x\n"):
        p = csv_(tmp_path, t)
        main(["importar", str(p)])
        assert p.read_bytes() == t.encode()


def test_json_corrupto(ruta_gastos, tmp_path, capsys):
    ruta_gastos.write_text("{corrupto")
    assert main(["importar", str(csv_(tmp_path, H + "2026-11-01,a,1,\n"))]) == 1
    assert ruta_gastos.read_text() == "{corrupto"


def test_gastos_file_y_duplicacion(tmp_path, monkeypatch):
    otra = tmp_path / "sub.json"
    monkeypatch.setenv("GASTOS_FILE", str(otra))
    p = csv_(tmp_path, H + "2026-11-01,a,1,\n2026-11-02,b,2,\n")
    assert main(["importar", str(p)]) == 0
    assert main(["importar", str(p)]) == 0
    assert len(json.loads(otra.read_text())["gastos"]) == 4
    assert not [f for f in os.listdir(tmp_path) if f.endswith(".tmp")]


def test_ciclo_exportar_importar(ruta_gastos, tmp_path):
    main(["registrar", "10", "comida", "--fecha", "2026-11-03", "--nota", 'a, "b"'])
    main(["registrar", "3.5", "transporte", "--fecha", "2026-11-10"])
    antes = ruta_gastos.read_text()
    out = tmp_path / "salida.csv"
    assert main(["exportar", str(out), "--mes", "2026-11"]) == 0
    ruta_gastos.unlink()
    assert main(["importar", str(out)]) == 0
    assert ruta_gastos.read_text() == antes
