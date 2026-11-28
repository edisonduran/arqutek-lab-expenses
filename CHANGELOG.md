# Changelog

## [Sin publicar]

### Añadido
- US-08..US-10 Comando `gastos categorias [--mes AAAA-MM]`: categorías del mes ordenadas por total descendente (empates por nombre), con total; mes vacío imprime `No hay gastos en AAAA-MM` (código 0); solo lectura, no crea `gastos.json`.
- US-12..US-16 Comando `gastos listar [--mes AAAA-MM] [--categoria NOMBRE]`: un gasto por línea en orden de fecha (`fecha categoria monto nota`) y pie `N gastos, total: X.XX`; sin resultados imprime `No hay gastos en AAAA-MM` (código 0); solo lectura, no crea `gastos.json`.
- US-17..US-21 Comando `gastos meses [--categoria NOMBRE]`: cada mes con gastos (cronológico) con cantidad y total, y total general; sin resultados imprime `No hay gastos` (código 0); solo lectura, no crea `gastos.json`.

## [0.1.0] - 2026-11-07

### Añadido
- US-01 Registrar un gasto (`gastos registrar <monto> <categoria> [--fecha] [--nota]`).
- US-02 Validación de montos (negativo, cero, no numérico); sumas exactas con Decimal.
- US-03 Categorías sin distinción de mayúsculas (se guardan en minúsculas).
- US-04 Creación automática y robustez de `gastos.json` (escritura atómica; JSON corrupto no se sobrescribe).
- US-05 Resumen mensual (`gastos resumen [--mes AAAA-MM]`).
- US-06 Exportación a CSV (`gastos exportar <archivo.csv> [--mes AAAA-MM]`).
- US-07 Suite de pruebas pytest aislada con directorios temporales.

### Decisiones
- ADR-001: formato `{"version":1,"gastos":[...]}`.
- ADR-002: `./gastos.json` con override `GASTOS_FILE`.
