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
- `categorias`: formato de línea `categoria: 0.00` y `total: 0.00` (igual que `resumen`); orden por total descendente, empate por nombre ascendente; mes vacío imprime `No hay gastos en AAAA-MM` en stdout con código 0 (a diferencia de `resumen`, que imprime total 0.00).

- `listar`: línea por gasto `AAAA-MM-DD categoria monto nota` (separados por espacio, monto con dos decimales, nota al final y vacía si no hay); pie `N gastos` y `total: 0.00` (formato igual a `resumen`); orden por fecha ascendente, empate por orden de registro; mes sin gastos (o filtro sin coincidencias) imprime `No hay gastos en AAAA-MM` con código 0, como `categorias`. El formato exacto del pie lo fija el Arquitecto/Desarrollador siguiendo el estilo existente.

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

### US-08 Listar categorías del mes por total (must, 3 pts)
Como persona que controla sus finanzas quiero `gastos categorias [--mes AAAA-MM]` para ver qué categorías pesan más en el mes y decidir dónde recortar.
- Given gastos en 2026-11 de comida 10.00 y 5.50, transporte 3.00 y ocio 20.00, When ejecuto `gastos categorias` (mes actual 2026-11), Then imprime en este orden `ocio: 20.00`, `comida: 15.50`, `transporte: 3.00`, y al final `total: 38.50`, con código 0.
- Given gastos en octubre y noviembre, When ejecuto `gastos categorias --mes 2026-10`, Then solo se suman y listan los gastos de octubre.
- Given dos categorías con el mismo total, When ejecuto el comando, Then se ordenan alfabéticamente entre sí (orden determinista).
- Given categorías registradas como "Comida" y "COMIDA", When ejecuto el comando, Then aparecen en una sola línea `comida`.

### US-09 Mes sin gastos y errores en `categorias` (must, 2 pts)
Como usuario quiero que `categorias` avise claramente cuando no hay datos o la entrada es inválida, con el mismo estilo que `resumen` y `exportar`, para no confundir un mes vacío con un fallo.
- Given un mes sin gastos (o sin gastos.json), When ejecuto `gastos categorias --mes 2026-09`, Then se imprime en stdout el mensaje `No hay gastos en 2026-09`, sin líneas de categorías, y el código de salida es 0.
- Given `--mes 2026-13` o `--mes abc`, When ejecuto `gastos categorias`, Then se muestra el mismo mensaje de mes inválido que `resumen` en stderr y el código es 1.
- Given un argumento desconocido (`gastos categorias --foo`), When ejecuto, Then error de uso en stderr y código 1.

### US-10 `categorias` es de solo lectura y robusto (must, 2 pts)
Como usuario quiero que `categorias` nunca cambie ni cree mis datos y respete archivos dañados, para no perder información.
- Given que gastos.json no existe, When ejecuto `gastos categorias`, Then termina con código 0 y gastos.json sigue sin existir.
- Given un gastos.json válido, When ejecuto `gastos categorias`, Then el archivo queda byte a byte idéntico.
- Given un gastos.json con JSON corrupto, When ejecuto `gastos categorias`, Then se informa el error en stderr, código 1 y el archivo queda byte a byte intacto.

### US-11 Documentar `categorias` y probarlo (should, 2 pts)
Como usuario y como equipo quiero README actualizado y pruebas pytest del comando para descubrirlo y evitar regresiones.
- Given el README, When se revisa, Then la sección Uso incluye `gastos categorias` y `gastos categorias --mes 2026-10`, y la lista de garantías menciona `categorias` junto a `resumen` y `exportar`.
- Given la suite, When ejecuto `pytest`, Then hay pruebas de orden descendente, total, mes vacío, mes inválido, sin crear archivo, sin modificar datos y JSON corrupto, y las pruebas existentes siguen pasando sin modificarse.

### US-12 Listar los gastos de un mes (must, 3 pts)
Como persona que controla sus finanzas quiero `gastos listar [--mes AAAA-MM]` para ver cada gasto del mes, uno por línea y en orden de fecha, y revisar en qué gasté exactamente.
- Given gastos en 2026-11: 2026-11-20 ocio 20.00 nota "cine", 2026-11-03 comida 10.00 sin nota y 2026-11-10 transporte 3.5 nota "taxi", When ejecuto `gastos listar` (mes actual 2026-11), Then imprime una línea por gasto en orden de fecha ascendente (03, 10, 20) con fecha, categoría, monto con dos decimales y nota (vacía si no tiene), con código 0.
- Given los mismos gastos, When termina el listado, Then la última línea indica cuántos gastos se muestran y su total (`3 gastos`, `total: 33.50`).
- Given gastos de octubre y noviembre, When ejecuto `gastos listar --mes 2026-10`, Then solo se listan y suman los de octubre.
- Given dos gastos con la misma fecha, When ejecuto el comando, Then salen en el orden en que fueron registrados (orden determinista).
- Given `--mes 2026-13` o `--mes abc`, When ejecuto `gastos listar`, Then se muestra en stderr el mismo mensaje de mes inválido que `resumen` y el código es 1.

### US-13 Filtrar el listado por categoría (must, 2 pts)
Como usuario quiero `gastos listar --categoria NOMBRE` para ver solo los gastos de una categoría y comprobar cuánto gasto en ella.
- Given gastos de "comida" y "ocio" en 2026-11, When ejecuto `gastos listar --categoria comida`, Then solo se listan los de comida y el pie muestra su cantidad y total.
- Given gastos registrados como "Comida", When ejecuto `gastos listar --categoria COMIDA`, Then se incluyen (sin distinción de mayúsculas, igual que al registrar).
- Given `--mes 2026-10 --categoria comida`, When ejecuto, Then se aplican ambos filtros a la vez.
- Given una categoría sin gastos en el mes, When ejecuto el comando, Then se aplica el mensaje de "sin gastos" de US-14.

### US-14 Mes sin gastos y errores en `listar` (must, 2 pts)
Como usuario quiero que `listar` avise claramente cuando no hay gastos que mostrar o la entrada es inválida, con el mismo estilo que `categorias`, para no confundir un mes vacío con un fallo.
- Given un mes sin gastos (o sin gastos.json), When ejecuto `gastos listar --mes 2026-09`, Then se imprime en stdout `No hay gastos en 2026-09`, sin líneas de gastos ni pie, y el código es 0.
- Given un filtro `--categoria viajes` sin coincidencias en 2026-11, When ejecuto `gastos listar --categoria viajes`, Then se imprime `No hay gastos en 2026-11` y el código es 0.
- Given un argumento desconocido (`gastos listar --foo`), When ejecuto, Then error de uso en stderr y código 1.

### US-15 `listar` es de solo lectura y robusto (must, 2 pts)
Como usuario quiero que `listar` nunca cambie ni cree mis datos y respete archivos dañados, para no perder información.
- Given que gastos.json no existe, When ejecuto `gastos listar`, Then termina con código 0 y gastos.json sigue sin existir.
- Given un gastos.json válido, When ejecuto `gastos listar`, Then el archivo queda byte a byte idéntico.
- Given un gastos.json con JSON corrupto, When ejecuto `gastos listar`, Then se informa el error en stderr, código 1 y el archivo queda byte a byte intacto.

### US-16 Documentar `listar` y probarlo (should, 2 pts)
Como usuario y como equipo quiero README y CHANGELOG actualizados y pruebas pytest del comando para descubrirlo y evitar regresiones.
- Given el README, When se revisa, Then la sección Uso incluye `gastos listar`, `gastos listar --mes 2026-10` y `gastos listar --categoria comida`, y la lista de garantías menciona `listar` junto a `resumen`, `categorias` y `exportar`.
- Given el CHANGELOG, When se revisa, Then la entrada de `listar` está en la sección `[Sin publicar]` junto a la de `categorias` y la versión `0.1.0` no cambia.
- Given la suite, When ejecuto `pytest`, Then hay pruebas de orden por fecha, pie con cantidad y total, filtro de categoría, mes vacío, mes inválido, sin crear archivo, sin modificar datos y JSON corrupto, y las pruebas existentes siguen pasando sin modificarse.

## No funcionales
- Python 3.11, solo biblioteca estándar (pytest solo para pruebas).
- Decimal para dinero; nunca float.
- Escritura del JSON atómica (archivo temporal + reemplazo) para no corromper datos.
- Mensajes en español, claros, en stderr para errores.
- Ejecución en menos de 1 s con hasta 10 000 gastos.

## Fuera de alcance
- Editar o borrar gastos, múltiples monedas, sincronización, interfaz gráfica, presupuestos, importar CSV, cifrado.
