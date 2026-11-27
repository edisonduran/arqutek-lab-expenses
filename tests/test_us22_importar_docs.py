"""US-22: lo que documenta el README sobre `importar` es verdad."""
import json

from gastos.cli import main

H = "fecha,categoria,monto,nota\n"


def test_us22_docs_importar_dos_veces_duplica(ruta_gastos, tmp_path):
    readme = open("/work/README.md", encoding="utf-8").read()
    assert "gastos importar archivo.csv" in readme and "duplica" in readme
    p = tmp_path / "archivo.csv"
    p.write_text(H + "2026-11-03,comida,10,\n", encoding="utf-8")
    assert main(["importar", str(p)]) == 0
    assert main(["importar", str(p)]) == 0
    assert len(json.loads(ruta_gastos.read_text())["gastos"]) == 2


def test_us22_docs_todo_o_nada_y_csv_intacto(ruta_gastos, tmp_path, capsys):
    p = tmp_path / "archivo.csv"
    txt = H + "2026-11-03,comida,10,\n2026-11-04,x,-1,\n"
    p.write_text(txt, encoding="utf-8")
    assert main(["importar", str(p)]) == 1
    err = capsys.readouterr().err
    assert "Fila 2" in err
    assert not ruta_gastos.exists() or json.loads(ruta_gastos.read_text())["gastos"] == []
    assert p.read_text(encoding="utf-8") == txt
