# gastos

CLI de gastos personales en Python 3.11, solo biblioteca estándar. Guarda los datos en `gastos.json`.

## Instalación

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[test]"     # instala el comando `gastos` y pytest
```

También funciona sin instalar: `python -m gastos ...` desde la raíz del proyecto.

## Uso

```bash
gastos registrar 12.50 comida                         # fecha de hoy
gastos registrar 8 Transporte --fecha 2026-10-15 --nota "taxi"
gastos resumen                                        # mes actual
gastos resumen --mes 2026-10
gastos exportar salida.csv --mes 2026-10              # CSV: fecha,categoria,monto,nota
```

- Montos con Decimal y dos decimales (ROUND_HALF_UP); deben ser > 0.
- Las categorías se guardan en minúsculas.
- Errores: mensaje en stderr y código de salida 1; éxito: 0.
- `resumen` y `exportar` no crean `gastos.json` si no existe.
- Un `gastos.json` corrupto o vacío nunca se sobrescribe.

## Datos

Por defecto `./gastos.json` (directorio actual); se cambia con la variable `GASTOS_FILE` (ADR-002).
Formato: `{"version": 1, "gastos": [...]}` con el monto como cadena (ADR-001). La escritura es atómica.

## Pruebas

```bash
python -m pytest
```

Usan directorios temporales y `GASTOS_FILE`; no tocan tu `gastos.json`.

## Docker

```bash
docker build -t gastos .
docker run --rm -v "$PWD/data:/data" gastos registrar 12.50 comida
```

Los datos se guardan en `/data/gastos.json` dentro del contenedor.

## Documentación

`docs/requirements.md`, `docs/architecture.md`, `docs/adr/`, `docs/review.md`.
