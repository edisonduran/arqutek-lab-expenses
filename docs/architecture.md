# Arquitectura — gastos

**Stack:** Python 3.11, solo stdlib (argparse, json, decimal, csv, datetime, pathlib, os); pytest solo para pruebas.
**Riesgo:** bajo (herramienta local, sin infraestructura ni seguridad; el único contrato público es el formato de gastos.json y la CLI).

## Capas y módulos
| Ruta | Responsabilidad |
|---|---|
| `gastos/domain.py` | Dominio puro: Gasto, validaciones, totales (Decimal) |
| `gastos/service.py` | Casos de uso: registrar, resumen, exportar, categorias |
| `gastos/storage.py` | Lectura/escritura atómica de gastos.json |
| `gastos/exporter.py` | Escritura CSV |
| `gastos/cli.py`, `__main__.py` | Interfaz argparse, stderr, códigos de salida |
| `tests/` | pytest con tmp_path |

Dependencias: cli → service → (domain, storage, exporter); domain no depende de nada.

## ADRs
1. **Decimal serializado como string** ("12.50") en JSON: exactitud, sin float. Cuantización `ROUND_HALF_UP` a 0.01 (10.005 → 10.01).
2. **Escritura atómica**: temporal en el mismo directorio + `os.replace`.
3. **Validar antes de tocar el archivo**: errores de entrada no modifican gastos.json; JSON corrupto/vacío => error, archivo intacto.
4. **Lectura sin creación**: resumen/exportar con archivo ausente tratan [] y no crean nada.
5. **Errores**: `GastoError` en dominio/servicio; `main` lo captura, imprime en stderr y devuelve 1. Errores de argparse también 1.
6. **Categoría** normalizada (strip+lower) al guardar.
7. **Reloj inyectable** (`hoy`) para pruebas deterministas.
8. **Ubicación**: `GASTOS_FILE` o `./gastos.json`.
9. **Rendimiento**: carga única, una pasada; 10 000 gastos << 1 s.
10. **Comando `categorias [--mes AAAA-MM]`** (US-08..11): solo lectura, sin módulos nuevos.
    - `domain.ordenar_categorias(totales) -> list[tuple[str, Decimal]]`: orden por total descendente y nombre ascendente en empates; función pura.
    - `service.categorias(ruta, mes=None, hoy=None) -> tuple[list[tuple[str, Decimal]], Decimal]`: reutiliza `_mes`, `filtrar_mes`, `totales_por_categoria`; agrupa por `categoria.strip().lower()` (defensivo ante archivos editados a mano).
    - `cli.py`: subparser `categorias` con `--mes`; mes sin gastos => stdout `No hay gastos en AAAA-MM` y código 0 (el mes mostrado es el efectivo, también si es el actual). Salida: `cat: 0.00` por línea y `total: X.XX`.
    - Errores (mes inválido, JSON corrupto, uso) por el mismo camino `GastoError` → stderr, código 1. No usa `storage.guardar`, por lo que nunca crea ni modifica gastos.json.
    - `service.categorias` devuelve el mes efectivo vía el vacío de la lista; la CLI necesita el mes para el mensaje: el Developer debe exponer `(año, mes)` (p. ej. devolviéndolo como tercer elemento o un helper `service.mes_efectivo`) sin cambiar `resumen`/`exportar`.

## Pruebas
pytest, ejecuta `main([...])` directamente con `capsys`; fixtures con tmp_path (ausente, válido, corrupto, vacío). Unitarias del dominio (montos, fechas, mes, categoría) + integración por comando, verificando código 1 y bytes intactos. Un test de rendimiento con 10 000 gastos.
Para `categorias`: nuevo `tests/test_categorias.py` (orden, empates, Comida/COMIDA, total, mes vacío, mes inválido, `--foo`, archivo ausente no creado, bytes idénticos, JSON corrupto); los tests existentes no se tocan.

## Ejecución
`python -m gastos registrar 12.50 comida` · tests: `python -m pytest`
