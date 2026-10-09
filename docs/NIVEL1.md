# Primer nivel · rediseño visual

El plano y las tres fotos proporcionadas están en `assets/refs/`. Son referencias visuales; su señalización no se interpreta como instrucciones de desarrollo.

## Mapa

`mapa_nivel1.py` conserva la orientación de la fotografía: terraza arriba; R104/R105 al oeste del jardín central; bodega sobre R103; R102 a la izquierda de R101; biblioteca bajo el jardín central; reuniones, servicios y escaleras debajo; Siemens, Click, Spark y Kite al este, en ese orden. Lobby y fachada de Kite conservan el acceso diagonal.

Las coordenadas se adaptan a una rejilla de 8 píxeles. La fotografía no aporta medidas, por lo que es una adaptación jugable de su distribución, no un plano a escala. Las zonas técnicas y servicios se representan en el exterior; desde el Checkpoint 2, las gradas suben a la Torre de Laboratorios (segundo nivel generado con recursividad, ver README). Las salidas jugables son lobby y terraza.

Las huellas del mapa, las puertas, los puntos de retorno y el grafo de patrulla comparten la misma fuente de datos. El polígono de Kite también se usa para colisión. Árboles, bancos y macetas tienen obstáculos definidos junto con su dibujo.

## Arte y presentación

- `arte_pixel.py`: sprites originales de personajes en cuatro direcciones, pasos de marcha, vigilante y profesor; muebles, objetos e iconos; suelos y paleta. Píxeles dibujados a media resolución y ampliados sin suavizado. Superficies cacheadas.
- `mundo_visual.py`: campus con fachadas, tejados, ventanas, puertas, vegetación y señalización.
- `interiores.py`: 13 salas amuebladas; los rectángulos físicos se derivan del mobiliario visible. Los interiores distintos de Siemens son interpretaciones artísticas porque no se proporcionaron fotografías de ellos.
- `hud_campus.py`: objetivo contextual, hora, minimapa, mapa completo (`M`) y bitácora (`J`). Mapa, bitácora e inventario pausan la partida.
- `sprites_jugador.py`: selección de personajes y retratos coherentes con el mundo. Los PNG antiguos del usuario se conservan, pero ya no se usan en el renderer.

## Laboratorio Siemens

Muro azul marino y ventanas altas, suelo de loseta clara, cuatro bancos agrupados en dos filas laterales, tableros claros con particiones negras, módulos PLC y motores, sillas naranja/azul/verde, pizarra TRIVIA, carrito verde, extintor y papelera. La composición usa las tres fotos como referencia y deja un pasillo central transitable.

La misión tiene tres estaciones ordenadas:

1. Revisar el extintor de la entrada.
2. Activar la simulación PLC en la mesa 1: los indicadores cambian a verde / RUN.
3. Imprimir el informe con la USB recogida frente a R101.

Los pasos completados se conservan al salir y regresar durante la misma partida. La impresión consume la USB una sola vez. Las interacciones representan una simulación de juego.

## Encargos y ritmo

Hay 13 encargos: uno por cada aula R101–R105, Siemens/Click/Spark/Kite, biblioteca, reuniones, cafetería y bodega. Se consultan en la bitácora. Las estaciones solo avanzan en el orden indicado y deben estar cerca del jugador. Devolver el libro requiere llevarlo desde el lobby. La victoria exige completar los 13 encargos y llegar a una salida.

Un minuto del juego dura 12 segundos reales: hay 9 minutos de exploración hasta las 21:00 y 3 minutos adicionales antes del cierre definitivo. El vigilante comienza a detectar después de las 21:00. No hay guardado de progreso entre ejecuciones; reiniciar crea una partida nueva.

## Verificación reproducible

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe capturar_juego.py
```

Las pruebas comprueban acceso a puertas/salidas, puntos de aparición, navegación a todas las estaciones, rutas del vigilante, orden de Siemens, consumo de objetos, persistencia al cambiar de sala, victoria y deshacer que devuelve a la sala anterior. `tests/test_checkpoint2.py` cubre la Torre, el historial y las colas. `capturar_juego.py` genera capturas reales de Pygame en `docs/capturas/`, sin abrir una ventana ni modificar puntajes.
