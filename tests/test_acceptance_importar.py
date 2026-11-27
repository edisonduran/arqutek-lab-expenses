"""Aceptación US-17..US-22: `gastos importar`."""
import json
import os
import stat

import pytest

from gastos.cli import main

H = "fecha,categoria,monto,nota\n"


def csv_(tmp_path, texto, name="in.csv"):
    p = tmp_path / name
    p.write_bytes(texto if isinstance(texto, bytes) else texto.encode())
    return p


def datos(ruta):
    return json.loads(ruta.read_text())["gastos"]


# ---- US-17
def test_us17_dos_filas_validas(ruta_gastos, tmp_path, capsys):
    p = csv_(tmp_path, H + "2026-11-03,Comida,10,\n2026-11-10,transporte,3.5,taxi\n")
    assert main(["importar", str(p)]) == 0
    out = capsys.readouterr().out
    assert "2" in out and "13.50" in out
    g = datos(ruta_gastos)
    assert [x["monto"] for x in g] == ["10.00", "3.50"]
    assert [x["categoria"] for x in g] == ["comida", "transporte"]
    assert g[1]["nota"] == "taxi" and g[0]["fecha"] == "2026-11-03"


def test_us17_conserva_previos_y_agrega_al_final(ruta_gastos, tmp_path):
    main(["registrar", "5", "previo", "--fecha", "2026-11-01"])
    p = csv_(tmp_path, H + "2026-11-03,a,1,\n2026-11-04,b,2,\n")
    assert main(["importar", str(p)]) == 0
    g = datos(ruta_gastos)
    assert [x["categoria"] for x in g] == ["previo", "a", "b"]


def test_us17_nota_con_comas_y_comillas(ruta_gastos, tmp_path):
    p = csv_(tmp_path, H + '2026-11-03,comida,4,"almuerzo, ""menú"" del día"\n')
    assert main(["importar", str(p)]) == 0
    assert datos(ruta_gastos)[0]["nota"] == 'almuerzo, "menú" del día'


def test_us17_solo_cabecera(ruta_gastos, tmp_path, capsys):
    assert main(["importar", str(csv_(tmp_path, H))]) == 0
    out = capsys.readouterr().out
    assert "0" in out and "0.00" in out


# ---- US-18
def test_us18_fecha_invalida_fila3_sin_cambios(ruta_gastos, tmp_path, capsys):
    main(["registrar", "5", "previo", "--fecha", "2026-11-01"])
    antes = ruta_gastos.read_bytes()
    p = csv_(tmp_path, H + "2026-11-01,a,1,\n2026-11-02,a,1,\n2026-13-40,a,1,\n")
    assert main(["importar", str(p)]) == 1
    err = capsys.readouterr().err
    assert "3" in err
    assert ruta_gastos.read_bytes() == antes


@pytest.mark.parametrize("monto", ["0", "-5", "abc", "1.234"])
def test_us18_montos_invalidos(ruta_gastos, tmp_path, capsys, monto):
    main(["registrar", "5", "previo", "--fecha", "2026-11-01"])
    antes = ruta_gastos.read_bytes()
    p = csv_(tmp_path, H + f"2026-11-01,a,{monto},\n")
    assert main(["importar", str(p)]) == 1
    assert "1" in capsys.readouterr().err
    assert ruta_gastos.read_bytes() == antes


def test_us18_categoria_vacia(ruta_gastos, tmp_path, capsys):
    main(["registrar", "5", "previo", "--fecha", "2026-11-01"])
    antes = ruta_gastos.read_bytes()
    p = csv_(tmp_path, H + "2026-11-01,   ,1,\n")
    assert main(["importar", str(p)]) == 1
    assert "1" in capsys.readouterr().err
    assert ruta_gastos.read_bytes() == antes


def test_us18_sexta_invalida_no_crea_archivo(ruta_gastos, tmp_path):
    p = csv_(tmp_path, H + "2026-11-01,a,1,\n" * 5 + "2026-11-01,a,xx,\n")
    assert main(["importar", str(p)]) == 1
    assert not ruta_gastos.exists()


def test_us18_informa_primera_invalida(ruta_gastos, tmp_path, capsys):
    p = csv_(tmp_path, H + "2026-11-01,a,1,\n2026-11-01,a,0,\n2026-13-40,a,1,\n")
    assert main(["importar", str(p)]) == 1
    err = capsys.readouterr().err
    assert "2" in err and "3" not in err.replace("2026", "").replace("-", "")


# ---- US-19
def test_us19_csv_inexistente(ruta_gastos, tmp_path, capsys):
    assert main(["importar", str(tmp_path / "no_existe.csv")]) == 1
    assert capsys.readouterr().err.strip()
    assert not ruta_gastos.exists()


@pytest.mark.parametrize("contenido", ["fecha,categoria,monto\n2026-11-01,a,1\n", "", "a,b,c,d\n"])
def test_us19_cabecera_incorrecta(ruta_gastos, tmp_path, capsys, contenido):
    main(["registrar", "5", "previo", "--fecha", "2026-11-01"])
    antes = ruta_gastos.read_bytes()
    assert main(["importar", str(csv_(tmp_path, contenido))]) == 1
    assert capsys.readouterr().err.strip()
    assert ruta_gastos.read_bytes() == antes


def test_us19_directorio(ruta_gastos, tmp_path, capsys):
    d = tmp_path / "dir.csv"
    d.mkdir()
    assert main(["importar", str(d)]) == 1
    assert capsys.readouterr().err.strip()
    assert not ruta_gastos.exists()


def test_us19_no_utf8(ruta_gastos, tmp_path, capsys):
    p = csv_(tmp_path, H.encode() + "2026-11-01,café,1,\n".encode("latin-1"))
    assert main(["importar", str(p)]) == 1
    assert capsys.readouterr().err.strip()
    assert not ruta_gastos.exists()


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignora permisos")
def test_us19_sin_permiso(ruta_gastos, tmp_path, capsys):
    p = csv_(tmp_path, H + "2026-11-01,a,1,\n")
    p.chmod(0)
    try:
        assert main(["importar", str(p)]) == 1
    finally:
        p.chmod(stat.S_IRUSR | stat.S_IWUSR)
    assert not ruta_gastos.exists()


@pytest.mark.parametrize("texto", [H + "2026-11-01,a,1,x\n", H + "2026-13-40,a,1,x\n", H, "mala\n"])
def test_us19_csv_intacto(ruta_gastos, tmp_path, texto):
    p = csv_(tmp_path, texto)
    main(["importar", str(p)])
    assert p.read_bytes() == texto.encode()


@pytest.mark.parametrize("fila", ["a,b", "a,b,c,d,e"])
def test_us19_columnas_distintas_de_4(ruta_gastos, tmp_path, capsys, fila):
    p = csv_(tmp_path, H + "2026-11-01,a,1,\n" + fila + "\n")
    assert main(["importar", str(p)]) == 1
    assert "2" in capsys.readouterr().err
    assert not ruta_gastos.exists()


# ---- US-20
def test_us20_crea_gastos_json(ruta_gastos, tmp_path):
    assert not ruta_gastos.exists()
    assert main(["importar", str(csv_(tmp_path, H + "2026-11-01,a,1,\n2026-11-02,b,2,\n"))]) == 0
    assert len(datos(ruta_gastos)) == 2


def test_us20_gastos_file_otra_ruta(tmp_path, monkeypatch):
    otra = tmp_path / "otra" / "x.json"
    otra.parent.mkdir()
    monkeypatch.setenv("GASTOS_FILE", str(otra))
    monkeypatch.chdir(tmp_path)
    assert main(["importar", str(csv_(tmp_path, H + "2026-11-01,a,1,\n"))]) == 0
    assert len(datos(otra)) == 1
    assert not (tmp_path / "gastos.json").exists()


def test_us20_json_corrupto_intacto(ruta_gastos, tmp_path, capsys):
    ruta_gastos.write_bytes(b"{corrupto")
    assert main(["importar", str(csv_(tmp_path, H + "2026-11-01,a,1,\n"))]) == 1
    assert capsys.readouterr().err.strip()
    assert ruta_gastos.read_bytes() == b"{corrupto"


def test_us20_escritura_atomica(ruta_gastos, tmp_path, monkeypatch):
    llamadas = []
    real = os.replace
    monkeypatch.setattr(os, "replace", lambda a, b: (llamadas.append((str(a), str(b))), real(a, b))[1])
    assert main(["importar", str(csv_(tmp_path, H + "2026-11-01,a,1,\n"))]) == 0
    assert len(llamadas) == 1
    assert llamadas[0][1] == str(ruta_gastos) and llamadas[0][0] != llamadas[0][1]
    assert [f for f in os.listdir(tmp_path) if f.endswith(".tmp")] == []


# ---- US-21
def test_us21_importar_dos_veces(ruta_gastos, tmp_path):
    p = csv_(tmp_path, H + "2026-11-01,a,1,\n2026-11-02,b,2,\n")
    assert main(["importar", str(p)]) == 0
    assert main(["importar", str(p)]) == 0
    assert len(datos(ruta_gastos)) == 4


def test_us21_ciclo_exportar_importar(ruta_gastos, tmp_path, monkeypatch):
    main(["registrar", "10", "comida", "--fecha", "2026-11-03", "--nota", 'a, "b"'])
    main(["registrar", "3.5", "transporte", "--fecha", "2026-11-10"])
    original = datos(ruta_gastos)
    salida = tmp_path / "salida.csv"
    assert main(["exportar", str(salida), "--mes", "2026-11"]) == 0
    ruta_gastos.unlink()
    assert main(["importar", str(salida)]) == 0
    assert datos(ruta_gastos) == original
    assert datos(ruta_gastos)[0]["nota"] == 'a, "b"'


# ---- US-22
def test_us22_docs():
    r = open("/work/README.md", encoding="utf-8").read() if os.path.exists("/work/README.md") else ""
    assert "gastos importar archivo.csv" in r
    assert "duplica" in r
    assert "`importar`" in r
    c = open("/work/CHANGELOG.md", encoding="utf-8").read()
    sin, _, resto = c.partition("## [0.1.0]")
    assert "importar" in sin and "categorias" in sin and "listar" in sin
    assert "importar" not in resto
