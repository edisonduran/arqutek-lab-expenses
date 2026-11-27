# Arquitectura — gastos

**Stack:** Python 3.11, solo stdlib (argparse, json, decimal, csv, datetime, pathlib, os); pytest solo para pruebas.
**Riesgo:** bajo (herramienta local, sin infraestructura ni seguridad; el único contrato público es el formato de gastos.json y la CLI).

## Capas y módulos
| Ruta | Responsabilidad |
|---|---|
| `gastos/domain.py` | Dominio puro: Gasto, validaciones, totales (Decimal) |
| `gastos/service.py` | Casos de uso: registrar, resumen, exportar, categorias, listar |
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
11. **Comando `listar [--mes AAAA-MM] [--categoria NOMBRE]`** (US-12..16): solo lectura, sin módulos nuevos.
    - `domain.ordenar_por_fecha(gastos) -> list[Gasto]`: `sorted` por `fecha` (estable => mismo día conserva el orden de registro); puro.
    - `domain.filtrar_categoria(gastos, categoria) -> list[Gasto]`: compara `strip().lower()` de ambos lados (Comida == COMIDA).
    - `service.listar(ruta, mes=None, categoria=None, hoy=None) -> tuple[list[Gasto], Decimal, tuple[int, int]]`: reutiliza `_mes` y `filtrar_mes`, aplica categoría y orden; total con `Decimal`. Devuelve el mes efectivo para el mensaje vacío. No usa `storage.guardar`.
    - `cli.py`: subparser `listar` con `--mes` y `--categoria`. Línea por gasto: `AAAA-MM-DD categoria monto.XX nota` separado por un espacio (sin espacio final si la nota es vacía). Pie: `N gastos, total: X.XX`. Sin resultados (mes o categoría) => stdout `No hay gastos en AAAA-MM`, sin pie, código 0.
    - Errores (mes inválido con el mismo mensaje de `resumen`, JSON corrupto, uso/`--foo`) por `GastoError` → stderr, código 1. Archivo ausente: no se crea.
    - Docs: README (Uso y garantías) y CHANGELOG en `[Sin publicar]`, sin tocar 0.1.0.

## Pruebas
pytest, ejecuta `main([...])` directamente con `capsys`; fixtures con tmp_path (ausente, válido, corrupto, vacío). Unitarias del dominio (montos, fechas, mes, categoría) + integración por comando, verificando código 1 y bytes intactos. Un test de rendimiento con 10 000 gastos.
Para `categorias`: nuevo `tests/test_categorias.py` (orden, empates, Comida/COMIDA, total, mes vacío, mes inválido, `--foo`, archivo ausente no creado, bytes idénticos, JSON corrupto); los tests existentes no se tocan.
Para `listar`: nuevo `tests/test_listar.py` (orden por fecha, mismo día en orden de registro, pie con cantidad y total, filtro categoría e insensibilidad a mayúsculas, ambos filtros, mes vacío, categoría sin coincidencias, mes inválido, `--foo`, archivo ausente no creado, bytes idénticos, JSON corrupto).

## Ejecución
`python -m gastos registrar 12.50 comida` · tests: `python -m pytest`
