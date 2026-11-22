"""Fixtures: aíslan siempre el gastos.json real usando tmp_path y GASTOS_FILE."""
import pytest


@pytest.fixture
def ruta_gastos(tmp_path, monkeypatch):
    """Ruta a un gastos.json inexistente dentro de tmp_path (también vía GASTOS_FILE)."""
    ruta = tmp_path / "gastos.json"
    monkeypatch.setenv("GASTOS_FILE", str(ruta))
    monkeypatch.chdir(tmp_path)
    return ruta
