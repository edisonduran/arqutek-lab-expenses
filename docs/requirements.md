# Requisitos: gastos (CLI de gastos personales)

Herramienta de línea de comandos en Python 3.11, solo biblioteca estándar. Persistencia en `gastos.json` en la carpeta actual.

## Supuestos (interpretaciones propuestas, el PO puede corregirlas)
- Los montos usan Decimal con exactamente dos decimales (redondeo ROUND_HALF_UP si se dan más de dos; se rechaza si no es numérico).
- Se guarda la categoría normalizada en minúsculas (casefold/lower).
- Errores: mensaje claro en stderr y código de salida 1. Éxito: código 0.
- Fecha inválida o mes inválido se rechazan con código 1.
- El JSON guarda el monto como cadena (p. ej. "12.50") para evitar errores de coma flotante.
- Resumen/exportación sin gastos en el mes: éxito, total 0.00, CSV solo con cabecera.
- CSV: cabecera `fecha,categoria,monto,nota`, codificación UTF-8, ordenado por fecha.

## Historias

### US-01 Registrar un gasto (must, 3 pts)
Como persona que controla sus finanzas quiero ejecutar `gastos registrar <monto> <categoria> [--fecha] [--nota]` para guardar un gasto y saber en qué gasto mi dinero.
- Given un gastos.json vacío, When ejecuto `gastos registrar 12.50 comida`, Then se guarda un gasto con monto "12.50", categoría "comida", fecha de hoy, y el código de salida es 0.
- Given que uso `--fecha 2026-10-15 --nota "taxi"`, When registro, Then el gasto se guarda con esa fecha y nota.
- Given `--fecha 2026-13-40`, When registro, Then se muestra un mensaje claro de fecha inválida, código 1 y no se modifica el archivo.

### US-02 Validar montos (must, 2 pts)
Como usuario quiero que montos inválidos se rechacen para que mis totales sean fiables.
- Given monto `-5`, When registro, Then mensaje claro y código 1, sin guardar.
- Given monto `0`, When registro, Then mensaje claro y código 1, sin guardar.
- Given monto `abc`, When registro, Then mensaje claro y código 1, sin guardar.
- Given monto `0.1` registrado tres veces, When veo el resumen, Then el total es exactamente 0.30 y se guarda con dos decimales.

### US-03 Categorías sin distinción de mayúsculas (must, 1 pt)
Como usuario quiero que "Comida" y "comida" sean la misma categoría para que el resumen no la duplique.
- Given gastos registrados con "Comida" y "COMIDA", When pido el resumen, Then aparecen en una sola línea "comida" con la suma.
- Given categoría "Comida", When se guarda, Then se almacena en minúsculas.

### US-04 Creación y robustez de gastos.json (must, 3 pts)
Como usuario quiero que el archivo se cree solo y no se pierda si está dañado, para no perder mis datos.
- Given que gastos.json no existe, When registro un gasto, Then se crea con ese gasto y código 0.
- Given que gastos.json contiene JSON corrupto, When ejecuto cualquier comando, Then se informa el error claramente, código 1 y el archivo queda byte a byte intacto.
- Given que gastos.json no existe, When ejecuto resumen o exportar, Then no falla y no crea el archivo.

### US-05 Resumen mensual (must, 3 pts)
Como usuario quiero `gastos resumen [--mes AAAA-MM]` para ver el total por categoría y el total general del mes.
- Given gastos en 2026-11 de comida 10.00 y 5.50, y transporte 3.00, When ejecuto `gastos resumen`, Then muestra comida 15.50, transporte 3.00 y total general 18.50 (mes actual 2026-11).
- Given gastos en octubre y noviembre, When ejecuto `gastos resumen --mes 2026-10`, Then solo suma los de octubre.
- Given un mes sin gastos, When pido el resumen, Then muestra total general 0.00 y código 0.
- Given `--mes 2026-13` o `--mes abc`, When ejecuto, Then mensaje claro y código 1.

### US-06 Exportar a CSV (must, 3 pts)
Como usuario quiero `gastos exportar <archivo.csv> [--mes AAAA-MM]` para analizar mis gastos en una hoja de cálculo.
- Given gastos registrados, When ejecuto `gastos exportar salida.csv`, Then se crea el CSV con cabecera `fecha,categoria,monto,nota` y una fila por gasto del mes actual.
- Given `--mes 2026-10`, When exporto, Then solo se incluyen los gastos de ese mes.
- Given una nota con comas o comillas, When exporto, Then el CSV la escapa correctamente.
- Given que la ruta de destino no es escribible, When exporto, Then mensaje claro y código 1.

### US-07 Pruebas automatizadas con pytest (must, 3 pts)
Como equipo quiero pruebas pytest de cada comando y de los errores para evitar regresiones.
- Given la suite, When ejecuto `pytest`, Then pasa sin red y usa directorios temporales, sin tocar el gastos.json real.
- Given la suite, When se revisa, Then hay pruebas de éxito para registrar, resumen y exportar.
- Given la suite, When se revisa, Then hay pruebas de monto negativo/cero/no numérico, fecha y mes inválidos, JSON corrupto sin sobrescribir, y comprobación del código de salida 1.

## No funcionales
- Python 3.11, solo biblioteca estándar (pytest solo para pruebas).
- Decimal para dinero; nunca float.
- Escritura del JSON atómica (archivo temporal + reemplazo) para no corromper datos.
- Mensajes en español, claros, en stderr para errores.
- Ejecución en menos de 1 s con hasta 10 000 gastos.

## Fuera de alcance
- Editar o borrar gastos, múltiples monedas, sincronización, interfaz gráfica, presupuestos, importar CSV, cifrado.
