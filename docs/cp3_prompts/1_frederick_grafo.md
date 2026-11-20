# Prompt para tu AI · Frederick Argueta · Grafo genérico + BFS/DFS

> Copia todo este archivo y pégalo en tu AI (Claude, ChatGPT, Cursor…) con el repo abierto.
> La AI te ayuda, pero **los commits los haces tú desde tu cuenta** y tienes que poder
> explicar cada línea si el docente te pregunta.

---

## Contexto para la AI

Eres mi asistente de programación en un proyecto universitario de **Estructura de Datos y
Algoritmos** (Python 3.12 + pygame 2.6.1). El repo es `github.com/SantiMerino/9PM`: un RPG de
sigilo en el que un estudiante tiene que completar encargos en el campus antes del toque de
queda (21:00) sin que lo atrape el vigilante. Se ejecuta con `python main.py` y las pruebas
corren con `python -m unittest discover -s tests` (hoy pasan 77).

Somos 5 integrantes y cada uno tiene **su propia parte del Checkpoint 3** (grafos, árboles,
diccionarios). La mía son los **grafos**. La rúbrica pide:

> *Implementan grafos de manera genérica en el proyecto (una implementación reutilizable, no
> atada a un solo mapa), con BFS y DFS funcionando* (15 pts). BFS y DFS deben resolver algo
> concreto del juego: la ruta con menos saltos, lo que el jugador alcanza desde donde está,
> las zonas aisladas o una ruta alternativa cuando algo está bloqueado.

### Estado actual del repo (lo relevante para mí)

- `mapa.py` tiene `class MapaCampus` con `self.grafo` (dict nodo → set de vecinos),
  `self.posiciones` (dict nodo → (x, y)), `agregar_sala(nombre, pos)`, `conectar(a, b)`,
  `vecinos(sala)`, `bfs(origen, destino)` (devuelve una lista o `None`, y `[origen]` si son iguales)
  y `dfs(origen)` (recursivo, con los vecinos en orden `sorted`).
- `mapa_nivel1.py → crear_mapa_nivel1()` arma el grafo del campus con 16 waypoints
  (`jardin_c`, `terraza`, `terraza_n`, `lobby_frente`, `lobby`…) y los conecta con `conectar`.
- `main.py` usa el grafo para el vigilante: `mapa.dfs(...)` arma su ronda,
  `mapa.bfs(...)` lo hace perseguirte y `mapa.posiciones[...]` lo ubica. **No lo modifiques.**
- `tests/test_campus.py` recorre `mapa.grafo.items()` y `mapa.posiciones`, así que
  **el atributo `self.grafo` tiene que seguir existiendo** con ese formato.
- `mazmorra.py → generar_mazmorra()` arma la Torre (2º nivel) como un **árbol** y devuelve un dict
  con `"raiz"`, `"salas"` (lista de nombres), `"conexiones"` (lista de tuplas `(padre, hija)`) y
  `"niveles"` (dict sala → nivel). Hoy la Torre se recorre con funciones propias del árbol.

### Contrato con el resto del equipo (no cambies los nombres)

- Ricardo guarda las puertas en un diccionario con claves de tupla **ordenada**,
  por ejemplo `("terraza", "terraza_n")`, y expone `puertas_cerradas(estado) -> list[tuple]`.
  Santiago va a llamar `grafo.bfs_ruta(origen, destino, bloqueadas=puertas_cerradas(estado))`.
  Por eso `bloqueadas` tiene que aceptar las tuplas en **cualquier orden**.
- Santiago va a usar `grafo_desde_mazmorra(...)` para la Torre y `alcanzables`/`componentes`
  para mostrar información en el juego.

---

## Qué tienes que construir

### Archivos que puedes tocar
`grafo.py` (nuevo) · `mapa.py` · `tests/test_grafo.py` (nuevo). **Ningún otro.**

### 1. `grafo.py` · clase genérica

```python
from collections import deque

class Grafo:
    """Grafo no dirigido con lista de adyacencia: dict nodo -> set(vecinos)."""
    def __init__(self):
        self.grafo = {}

    def agregar_nodo(self, nodo): ...               # no duplica si ya existe
    def agregar_arista(self, a, b): ...             # crea los nodos si faltan; ignora a == b
    def quitar_arista(self, a, b) -> bool: ...      # False si no existía (sin excepción)
    def existe_nodo(self, nodo) -> bool: ...
    def vecinos(self, nodo) -> set: ...             # set() si no existe
    def nodos(self) -> list: ...                    # ordenados
    def numero_aristas(self) -> int: ...

    def bfs_ruta(self, origen, destino, bloqueadas=()) -> list | None: ...
    def hay_ruta(self, origen, destino, bloqueadas=()) -> bool: ...
    def dfs(self, origen) -> list: ...
    def alcanzables(self, origen, bloqueadas=()) -> set: ...
    def componentes(self) -> list[set]: ...
```

Reglas:
- `bfs_ruta` devuelve la ruta con **menos saltos**: `[origen]` si `origen == destino`, `None` si
  algún nodo no existe o no hay camino. Recorre los vecinos en orden `sorted` para que el
  resultado sea determinista (igual que el código actual).
- `bloqueadas` es una colección de tuplas `(a, b)`. Normalízala una vez a un `set` de
  `frozenset({a, b})` para que bloquee en los dos sentidos y la consulta sea O(1).
- `dfs` devuelve el **mismo orden** que el `MapaCampus.dfs` actual (preorden recursivo con
  vecinos `sorted`), porque la ronda del vigilante depende de ese orden. Si el origen no
  existe, devuelve `[]`.
- `alcanzables` usa BFS y devuelve el conjunto de nodos a los que se llega sin cruzar
  aristas bloqueadas (incluye el origen; `set()` si no existe).
- `componentes` devuelve las zonas conectadas (lista de sets, la más grande primero). Sirve
  para detectar zonas aisladas.
- Ningún método lanza excepción con datos inválidos.
- Cada método con un docstring corto que diga **qué hace y su complejidad**
  (BFS/DFS/alcanzables/componentes O(V + E), vecinos O(1) promedio, etc.).

### 2. `grafo.py` · segundo uso: la Torre como grafo con atajos

```python
def grafo_desde_mazmorra(mazmorra, atajos=2, semilla=None) -> Grafo:
    """Convierte el árbol de la Torre en un Grafo y le agrega `atajos` aristas extra
    entre salas del MISMO nivel que no estén conectadas, para que haya caminos alternativos.
    Guarda la lista de atajos agregados en grafo.atajos (lista de tuplas)."""
```

- Usa `random.Random(semilla)` para elegir los atajos, así es reproducible.
- Si no hay pares posibles, agrega los que pueda (incluso 0) sin fallar.
- Un árbol es un grafo conexo sin ciclos: con los atajos deja de ser árbol y aparecen rutas alternativas.

### 3. `mapa.py` · `MapaCampus` hereda de `Grafo`

```python
from grafo import Grafo

class MapaCampus(Grafo):
    def __init__(self):
        super().__init__()
        self.posiciones = {}
    def agregar_sala(self, nombre, posicion): ...   # agregar_nodo + posición
    def conectar(self, a, b): ...                   # = agregar_arista
    def bfs(self, origen, destino, bloqueadas=()):  # alias para el código existente
        return self.bfs_ruta(origen, destino, bloqueadas)
```

Borra de `MapaCampus` el BFS y el DFS duplicados (ya vienen de `Grafo`). El vigilante tiene
que seguir funcionando igual. Deja `crear_mapa_universidad()` como está.

### 4. `tests/test_grafo.py` (unittest, sin pygame)

Mínimo estas pruebas:
1. Ruta más corta en un grafo chico armado a mano (ejemplo: un cuadrado con diagonal).
2. `bfs_ruta` con una arista bloqueada encuentra la **ruta alternativa**.
3. Bloquear `("b", "a")` también bloquea `("a", "b")`.
4. Ruta imposible → `None`. Nodo inexistente → `None`, sin excepción.
5. `dfs` sobre el campus real (`crear_mapa_universidad()`) visita los 16 nodos sin repetir.
6. `componentes` detecta 2 zonas cuando hay una isla.
7. `alcanzables` con la puerta `("terraza", "terraza_n")` bloqueada **no** incluye `terraza_n`.
8. `grafo_desde_mazmorra(generar_mazmorra(semilla=3), atajos=2, semilla=1)` tiene
   `numero_aristas() == len(conexiones) + len(grafo.atajos)` y cada atajo une salas del mismo nivel.
9. `quitar_arista` de una arista que no existe devuelve `False`.

---

## Plan de trabajo y commits (uno por paso, el juego corre después de cada uno)

```bash
git clone git@github.com:SantiMerino/9PM.git && cd 9PM
git config user.name "Frederick Argueta"
git config user.email "<el correo de tu cuenta de GitHub>"
python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt
git checkout -b cp3/frederick
```

| # | Qué hacer | Mensaje de commit |
|---|---|---|
| 1 | `grafo.py` con la clase, `agregar_*`, `quitar_arista`, `vecinos`, `nodos`, `numero_aristas` + sus pruebas | `Agrega clase Grafo genérica con lista de adyacencia` |
| 2 | `bfs_ruta`, `hay_ruta` y `alcanzables` con `bloqueadas` + pruebas 1–4 y 7 | `Agrega BFS con aristas bloqueadas y nodos alcanzables` |
| 3 | `dfs` y `componentes` + pruebas 5 y 6 | `Agrega DFS y detección de zonas aisladas al Grafo` |
| 4 | `MapaCampus` hereda de `Grafo` (correr **todas** las pruebas: las 77 viejas tienen que seguir pasando) | `MapaCampus hereda de Grafo y reutiliza su BFS y DFS` |
| 5 | `grafo_desde_mazmorra` + prueba 8 | `Convierte la Torre en grafo con atajos entre salas del mismo nivel` |

Antes de **cada** commit:
```bash
python -m unittest discover -s tests
python main.py        # abre, camina un poco, espera a que el vigilante patrulle, cierra
```
Al final: `git push -u origin cp3/frederick` y abre un **Pull Request a `main`** con
título "CP3 · Grafo genérico con BFS y DFS". **Fecha límite: viernes 20, 12:00.**

---

## Resultado esperado

1. **Archivos:** `grafo.py` nuevo (unas 120–170 líneas con docstrings), `mapa.py` más corto
   (sin BFS/DFS duplicados) y `tests/test_grafo.py` con 9 o más pruebas.
2. **Pruebas:** `python -m unittest discover -s tests` termina en `OK` con 86 o más pruebas
   (las 77 de antes + las tuyas).
3. **Juego:** `python main.py` funciona igual que antes; el vigilante patrulla y persigue.
4. **Demo en consola** (para la evidencia del README, pásale el texto a Nathaly):
   ```python
   >>> from mapa import crear_mapa_universidad
   >>> m = crear_mapa_universidad()
   >>> m.bfs_ruta("lobby", "terraza_n")
   ['lobby', 'lobby_frente', 'lobby_acceso', 'sur', 'este_s', 'este_c', 'norte', 'terraza', 'terraza_n']
   >>> m.bfs_ruta("lobby", "terraza_n", bloqueadas=[("terraza", "terraza_n")])
   None
   >>> len(m.alcanzables("lobby", bloqueadas=[("lobby", "lobby_frente")]))
   1
   ```
5. **Historial:** 5 commits tuyos en `git log --author="Frederick"`, con mensajes claros.
6. **Para el README** (mándaselo a Nathaly): 3–4 líneas sobre por qué un grafo con lista de
   adyacencia es la estructura adecuada para el campus (pasillos = aristas, pocos vecinos
   por nodo → lista mejor que matriz), la complejidad de BFS y DFS (O(V + E)) y por qué BFS
   da la ruta con menos saltos.

## Lo que NO debes hacer
- No toques `main.py`, `misiones.py`, `estado_mundo.py`, `hud_campus.py` ni el README.
- No cambies el formato de `self.grafo` ni el orden del DFS.
- No hagas un solo commit gigante ni commits vacíos.
