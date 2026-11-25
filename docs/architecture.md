# Arquitectura — gastos

**Stack:** Python 3.11, solo stdlib (argparse, json, decimal, csv, datetime, pathlib, os); pytest solo para pruebas.
**Riesgo:** bajo (herramienta local, sin infraestructura ni seguridad; el único contrato público es el formato de gastos.json y la CLI).

## Capas y módulos
| Ruta | Responsabilidad |
|---|---|
| `gastos/domain.py` | Dominio puro: Gasto, validaciones, totales (Decimal) |
| `gastos/service.py` | Casos de uso: registrar, resumen, exportar, listar |
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
10. **Comando `listar` (US-08..US-11)**: solo lectura, reutiliza `_mes`, `storage.cargar` y `domain.filtrar_mes`. Nuevo en dominio `filtrar_categoria(gastos, cat)` (compara con la categoría normalizada vía `normalizar_categoria`, así `""`/espacios dan el mismo error que al registrar) y `ordenar_por_fecha` con `sorted(key=fecha)` (estable: misma fecha conserva el orden de registro). `service.listar(ruta, mes=None, categoria=None, hoy=None)` valida mes y categoría antes de cargar y devuelve `(lista, total)`. `cli` imprime una línea por gasto `AAAA-MM-DD categoria monto:.2f nota` (nota vacía no rompe la línea) y pie `gastos: N` / `total: X.XX`; sin resultados imprime `No hay gastos para mostrar` sin pie, código 0. Errores vía `GastoError` → stderr, 1; opción desconocida → `Error de uso`. Nunca llama a `storage.guardar`.
11. **Pruebas de `listar`**: nuevo `tests/test_listar.py` (los tests existentes no se modifican); fecha actual fijada con `hoy` inyectado en el servicio y `--mes` explícito en CLI cuando sea necesario.

## Pruebas
pytest, ejecuta `main([...])` directamente con `capsys`; fixtures con tmp_path (ausente, válido, corrupto, vacío). Unitarias del dominio (montos, fechas, mes, categoría) + integración por comando, verificando código 1 y bytes intactos. Un test de rendimiento con 10 000 gastos.

## Ejecución
`python -m gastos registrar 12.50 comida` · `python -m gastos listar [--mes AAAA-MM] [--categoria X]` · tests: `python -m pytest`
