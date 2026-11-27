"""Aceptación de `gastos listar` (US-12 a US-16)."""
import json
from datetime import date
from pathlib import Path

from gastos.cli import main

MES = date.today().strftime("%Y-%m")
ROOT = Path(__file__).resolve().parent.parent


def _datos(ruta, items):
    ruta.write_text(json.dumps({"version": 1, "gastos": [
        {"fecha": f, "categoria": c, "monto": m, "nota": n} for f, c, m, n in items]}))


def _base(ruta):
    _datos(ruta, [(MES + "-20", "ocio", "20.00", "cine"), (MES + "-03", "comida", "10.00", ""),
                  (MES + "-10", "transporte", "3.5", "taxi")])


def test_us12_orden_fecha_y_formato(ruta_gastos, capsys):
    _base(ruta_gastos)
    assert main(["listar"]) == 0
    l = [x.rstrip() for x in capsys.readouterr().out.splitlines()]
    assert l[:3] == [MES + "-03 comida 10.00", MES + "-10 transporte 3.50 taxi",
                     MES + "-20 ocio 20.00 cine"]


def test_us12_pie_cantidad_y_total(ruta_gastos, capsys):
    _base(ruta_gastos)
    main(["listar"])
    l = capsys.readouterr().out.splitlines()
    assert len(l) == 4 and l[-1] == "3 gastos, total: 33.50"


def test_us12_filtra_por_mes(ruta_gastos, capsys):
    _datos(ruta_gastos, [(MES + "-01", "comida", "10.00", ""), ("2026-10-05", "ocio", "7.00", "a")])
    assert main(["listar", "--mes", "2026-10"]) == 0
    l = capsys.readouterr().out.splitlines()
    assert len(l) == 2 and l[0].startswith("2026-10-05 ocio 7.00")
    assert l[1] == "1 gastos, total: 7.00"


def test_us12_misma_fecha_orden_de_registro(ruta_gastos, capsys):
    _datos(ruta_gastos, [("2026-10-05", "zeta", "1.00", ""), ("2026-10-05", "alfa", "2.00", ""),
                         ("2026-10-05", "medio", "3.00", "")])
    main(["listar", "--mes", "2026-10"])
    l = capsys.readouterr().out.splitlines()
    assert [x.split()[1] for x in l[:3]] == ["zeta", "alfa", "medio"]


def test_us12_mes_invalido_igual_que_resumen(ruta_gastos, capsys):
    for mes in ("2026-13", "abc"):
        assert main(["resumen", "--mes", mes]) == 1
        esperado = capsys.readouterr().err
        assert esperado
        assert main(["listar", "--mes", mes]) == 1
        cap = capsys.readouterr()
        assert cap.err == esperado and cap.out == ""


def test_us13_filtro_categoria(ruta_gastos, capsys):
    _datos(ruta_gastos, [(MES + "-01", "comida", "10.00", ""), (MES + "-02", "comida", "5.50", ""),
                         (MES + "-03", "ocio", "20.00", "")])
    assert main(["listar", "--categoria", "comida"]) == 0
    l = capsys.readouterr().out.splitlines()
    assert len(l) == 3 and "ocio" not in "".join(l)
    assert l[-1] == "2 gastos, total: 15.50"


def test_us13_sin_distincion_mayusculas(ruta_gastos, capsys):
    _datos(ruta_gastos, [(MES + "-01", "Comida", "10.00", ""), (MES + "-02", "ocio", "1.00", "")])
    assert main(["listar", "--categoria", "COMIDA"]) == 0
    l = capsys.readouterr().out.splitlines()
    assert len(l) == 2 and l[-1] == "1 gastos, total: 10.00"


def test_us13_ambos_filtros(ruta_gastos, capsys):
    _datos(ruta_gastos, [(MES + "-01", "comida", "10.00", ""), ("2026-10-05", "comida", "7.00", ""),
                         ("2026-10-06", "ocio", "3.00", "")])
    assert main(["listar", "--mes", "2026-10", "--categoria", "comida"]) == 0
    l = capsys.readouterr().out.splitlines()
    assert len(l) == 2 and l[-1] == "1 gastos, total: 7.00"


def test_us13_categoria_sin_gastos_mensaje(ruta_gastos, capsys):
    _base(ruta_gastos)
    assert main(["listar", "--categoria", "viajes"]) == 0
    assert capsys.readouterr().out == f"No hay gastos en {MES}\n"


def test_us14_mes_vacio_sin_archivo(ruta_gastos, capsys):
    assert main(["listar", "--mes", "2026-09"]) == 0
    assert capsys.readouterr().out == "No hay gastos en 2026-09\n"


def test_us14_mes_vacio_con_datos_en_otro_mes(ruta_gastos, capsys):
    _base(ruta_gastos)
    assert main(["listar", "--mes", "2026-09"]) == 0
    assert capsys.readouterr().out == "No hay gastos en 2026-09\n"


def test_us14_argumento_desconocido(ruta_gastos, capsys):
    assert main(["listar", "--foo"]) == 1
    cap = capsys.readouterr()
    assert cap.err and cap.out == ""


def test_us15_sin_archivo_no_se_crea(ruta_gastos):
    assert main(["listar"]) == 0
    assert not ruta_gastos.exists()


def test_us15_archivo_valido_identico(ruta_gastos):
    _base(ruta_gastos)
    antes = ruta_gastos.read_bytes()
    assert main(["listar"]) == 0
    assert main(["listar", "--categoria", "ocio"]) == 0
    assert ruta_gastos.read_bytes() == antes


def test_us15_json_corrupto(ruta_gastos, capsys):
    ruta_gastos.write_bytes(b"{corrupto")
    assert main(["listar"]) == 1
    cap = capsys.readouterr()
    assert cap.err and cap.out == ""
    assert ruta_gastos.read_bytes() == b"{corrupto"


def test_us16_readme_y_changelog():
    r = (ROOT / "README.md").read_text()
    for c in ("gastos listar", "gastos listar --mes 2026-10", "gastos listar --categoria comida"):
        assert c in r
    g = [x for x in r.splitlines() if "no crean" in x and "listar" in x]
    assert g and all(w in g[0] for w in ("resumen", "categorias", "exportar"))
    ch = (ROOT / "CHANGELOG.md").read_text()
    sp, rest = ch.split("## [Sin publicar]")[1].split("## [0.1.0]", 1)
    assert "gastos listar" in sp and "gastos categorias" in sp
    assert "gastos listar" not in rest
