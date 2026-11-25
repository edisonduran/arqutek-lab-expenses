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

### US-08 Listar los gastos de un mes (must, 3 pts)
Como persona que controla sus finanzas quiero `gastos listar [--mes AAAA-MM]` para ver cada gasto del mes, uno por línea y en orden de fecha, y así revisar en qué gasté sin abrir el JSON ni exportar un CSV.
- Given gastos de 2026-11 con fechas 2026-11-20, 2026-11-03 y 2026-11-10 y de 2026-10, When ejecuto `gastos listar` (mes actual 2026-11), Then muestra solo los tres de noviembre, uno por línea, ordenados por fecha ascendente, cada línea con fecha (AAAA-MM-DD), categoría, monto con dos decimales y descripción (la nota), y código 0.
- Given dos gastos con la misma fecha, When listo, Then aparecen en el orden en que se registraron.
- Given los gastos mostrados, When termina el listado, Then la última línea indica cuántos gastos se muestran y su total con dos decimales (p. ej. `gastos: 3` y `total: 18.50`, en el estilo de `resumen`).
- Given `--mes 2026-10`, When listo, Then solo aparecen los gastos de octubre.
- Given `--mes 2026-13` o `--mes abc`, When listo, Then mensaje claro en stderr (igual que `resumen`) y código 1.
- Given un gasto sin nota, When listo, Then su línea se muestra sin romperse (descripción vacía).

### US-09 Filtrar el listado por categoría (should, 2 pts)
Como usuario quiero `gastos listar --categoria NOMBRE` para ver solo los gastos de una categoría y comprobar cuánto llevo en ella.
- Given gastos de "comida" y "transporte" en el mes, When ejecuto `gastos listar --categoria COMIDA`, Then solo se listan los de comida (sin distinguir mayúsculas, igual que al registrar), y el pie cuenta y suma solo esos.
- Given `--categoria Comida --mes 2026-10`, When listo, Then se aplican ambos filtros a la vez.
- Given una categoría sin gastos en el mes, When listo, Then se aplica el mensaje de "sin gastos" de US-10 y código 0.
- Given `--categoria ""` o solo espacios, When listo, Then mensaje de categoría inválida igual que al registrar y código 1.

### US-10 Listado sin gastos, de solo lectura y robusto (must, 2 pts)
Como usuario quiero que `listar` se comporte como `resumen` y `exportar` ante datos ausentes o dañados, para no perder ni alterar mis datos.
- Given un mes sin gastos (o un gastos.json inexistente), When ejecuto `gastos listar`, Then imprime el mensaje `No hay gastos para mostrar`, no imprime el pie de totales y el código es 0.
- Given que gastos.json no existe, When ejecuto `listar`, Then no se crea el archivo.
- Given un gastos.json con gastos, When ejecuto `listar` con cualquier opción, Then el archivo queda byte a byte intacto.
- Given un gastos.json con JSON corrupto, When ejecuto `listar`, Then mensaje de error en stderr, código 1 y el archivo queda intacto.
- Given una opción desconocida (`--foo`), When ejecuto `listar`, Then "Error de uso: ..." en stderr y código 1.

### US-11 Documentar y probar `listar` (must, 2 pts)
Como usuario y como equipo quiero README actualizado y pruebas de `listar` para descubrir el comando y evitar regresiones.
- Given el README, When se revisa, Then la sección Uso incluye `gastos listar`, `gastos listar --mes 2026-10` y `--categoria`, y menciona que `listar` no crea `gastos.json` ni lo modifica.
- Given la suite pytest, When se ejecuta, Then hay pruebas de listar: orden por fecha, filtro de mes y categoría, pie con cuenta y total, mes sin gastos, mes inválido, JSON corrupto intacto y archivo inexistente sin crear.
- Given las pruebas existentes, When se ejecuta toda la suite, Then siguen pasando sin modificarse.

## No funcionales
- Python 3.11, solo biblioteca estándar (pytest solo para pruebas).
- Decimal para dinero; nunca float.
- Escritura del JSON atómica (archivo temporal + reemplazo) para no corromper datos.
- Mensajes en español, claros, en stderr para errores.
- Ejecución en menos de 1 s con hasta 10 000 gastos.

## Fuera de alcance
- Para `listar`: paginación, otros órdenes, rangos de fechas, formato CSV/JSON de salida, colores.
- Editar o borrar gastos, múltiples monedas, sincronización, interfaz gráfica, presupuestos, importar CSV, cifrado.
