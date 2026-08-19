# 9PM

Eres un estudiante que se quedó tarde en la universidad. Son las **20:15** y
a las **21:00** empieza el toque de queda: si un vigilante te ve después de
esa hora, te expulsan del campus por esa noche. Resuelve tus tres pendientes
y llega al parqueadero antes de que te atrapen.

Es un juego de un solo jugador (no cooperativo), estilo mini RPG/sandbox
visto desde arriba: exploras un mapa fijo (el campus) libremente, recoges
objetos, hablas con NPCs y evitas a un vigilante que patrulla, todo ambientado
de noche.

## Cómo correrlo

```bash
pip install -r requirements.txt
python main.py
```

## Controles

| Tecla | Acción |
|---|---|
| `W A S D` / flechas | Moverse |
| `ESPACIO` | Interactuar con la sala más cercana |
| `Z` | Deshacer el último movimiento |
| `F` | Buscar el libro en tu inventario |
| `ENTER` | Confirmar en el menú / pantalla final |
| `ESC` | Salir |

## Estructura del proyecto

Cada archivo corresponde a un tema del curso y ya está integrado y
funcionando dentro del juego (no son solo plantillas vacías):

| Archivo | Tema | Uso dentro de 9PM |
|---|---|---|
| `main.py` | — | Arma el juego: ventana, bucle principal, estados (menú/jugando/fin), dibujo |
| `inventario.py` | Semana 3 — lista | Objetos que el jugador recoge (ej. el libro) |
| `historial.py` | Semana 5 — pila | Deshacer el último movimiento (`Z`) |
| `eventos.py` | Semana 6 — cola | Avisos programados (10 min, 5 min, toque de queda) |
| `mazmorra.py` | Semana 7 — recursión | Genera los pisos/aulas de la Torre de Laboratorios |
| `ranking.py` | Semana 9 — ordenamiento | Ordena y guarda los mejores puntajes en `puntajes.json` |
| `buscador.py` | Semana 11 — búsqueda | Busca objetos en el inventario (`F`) |
| `mapa.py` | Semana 12-13 — grafo, BFS/DFS | Grafo del campus; BFS mueve al vigilante, DFS arma su ronda |
| `misiones.py` | Semana 14 — árbol | Misión principal con 3 sub-misiones |
| `estado_mundo.py` | Semana 15 — diccionario | Hora actual, toque de queda, luces |

`puntajes.json` se crea automáticamente la primera vez que termines una
partida (no debe subirse a git si conectas el repo, ya que es un archivo
generado).

## Próximos pasos sugeridos

- Reemplazar los círculos/glows por sprites (personaje, vigilante, salas) y
  un tilemap real en `assets/`.
- Más de un vigilante, o vigilantes con distinto radio de detección por sala.
- Sub-misiones con más pasos (por ejemplo, que "imprimir el trabajo" primero
  requiera recoger una USB en el salón 101).
- Un mapa más grande usando `mazmorra.py` para generar edificios completos
  con varios pisos jugables, no solo como dato de sabor.
