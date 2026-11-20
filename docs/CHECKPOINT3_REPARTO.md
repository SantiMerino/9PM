# Checkpoint 3 · Reparto de tareas

> **Instrucciones detalladas para pegar en su AI:** `docs/cp3_prompts/` (un archivo por integrante).
> Si algo de este resumen no coincide con esos archivos, mandan los archivos de `cp3_prompts`.

**Entrega:** viernes 20 de noviembre, **23:30** (Canvas cierra a esa hora).
**Qué se entrega:** el link a `github.com/SantiMerino/9PM` con el tag `checkpoint-3`.
**Rúbrica:** participación en GitHub 50 · grafos 15 · árboles y diccionario 15 ·
integración y casos límite 10 · README 10.

> La participación (50 pts) se evalúa **por persona** en el historial de commits.
> Cada quien hace commits **desde su propia cuenta de GitHub**, con mensajes que
> digan qué cambió, y el juego tiene que seguir corriendo después de cada commit.
> No sirven los commits vacíos, los que solo renombran archivos ni los de "cambios".

---

## La idea: cómo trabajan juntas las estructuras

Este flujo es el que pide el punto 5 de la rúbrica. Cada parte de abajo es una pieza de él:

```
Árbol de misiones ──completar──▶ Diccionario del mundo ──puertas cerradas──▶ Grafo
 (Juan Diego)                     (Ricardo)                                    (Frederick)
   │ desbloquea hijas              │ abre/cierra puertas, apaga luces            │ BFS esquiva aristas bloqueadas
   ▼                               ▼                                             ▼
 Bitácora con sangría (Nathaly)   Toque de queda cierra el lobby ───────▶ ruta alternativa por la terraza
                                                                          o "no hay salida" (caso límite)
                    Todo se conecta en main.py (Santiago)
```

Ejemplos concretos:
- Completar **Cierre de caja** abre la puerta `("terraza", "terraza_n")` en el diccionario,
  y desde ahí el BFS ya puede usar esa salida.
- A las 21:00 el toque de queda cierra `("lobby_frente", "lobby")`. El BFS busca una ruta
  alternativa y, si la terraza sigue cerrada, el juego avisa que no hay salida (sin crashear).
- Una misión bloqueada (porque su padre no está completo) no se puede hacer, y el juego
  muestra un mensaje que dice cuál falta primero.

---

## Reglas para no pisarnos

1. **Cada quien trabaja en sus propios archivos.** Solo Santiago toca `main.py`.
2. Cada quien trabaja en una rama `cp3/<nombre>` y abre un Pull Request a `main`.
3. Antes de cada commit corran `python -m unittest discover -s tests` y verifiquen que
   el juego abra con `python main.py`.
4. Configuren su identidad **una vez**, con el mismo correo de su cuenta de GitHub:
   `git config user.name "Su Nombre"` y `git config user.email "correo@de-github"`.
5. Los nombres y firmas de abajo son el **contrato** entre las partes. Si alguien los
   cambia, avisa en el grupo.

---

## 1. Frederick Argueta: grafo genérico + BFS/DFS (15 pts de grafos)

**Archivos:** `grafo.py` (nuevo), `mapa.py`, `tests/test_grafo.py` (nuevo).

Una clase `Grafo` reutilizable con lista de adyacencia (`dict` nodo → `set` de vecinos)
que no sepa nada del campus:

```python
class Grafo:
    def agregar_nodo(self, nodo): ...
    def agregar_arista(self, a, b): ...           # no dirigida
    def quitar_arista(self, a, b): ...            # no falla si no existe
    def existe_nodo(self, nodo) -> bool: ...
    def vecinos(self, nodo) -> set: ...           # set() si no existe
    def bfs_ruta(self, origen, destino, bloqueadas=()) -> list | None: ...
    def dfs(self, origen) -> list: ...
    def alcanzables(self, origen, bloqueadas=()) -> set: ...   # BFS
    def componentes(self) -> list[set]: ...                    # zonas aisladas
```

- `bloqueadas` es una colección de tuplas `(a, b)` de aristas que no se pueden usar
  (puertas cerradas). Tienen que funcionar en los dos sentidos.
- Si el nodo no existe o no hay ruta, se devuelve `None` o un resultado vacío, **nunca una excepción**.
- `MapaCampus` (en `mapa.py`) pasa a heredar de `Grafo` y solo agrega `posiciones`.
  Mantengan `bfs(origen, destino)` como alias de `bfs_ruta` para que el vigilante siga funcionando.
- **Segundo uso (lo que lo hace genérico):** `grafo_desde_mazmorra(mazmorra, atajos=2, semilla=None)`
  convierte la Torre del CP2 en un `Grafo` y le agrega 1 o 2 atajos entre salas del mismo nivel,
  para que haya caminos alternativos.
- Pruebas: ruta más corta, ruta con una arista bloqueada, ruta imposible, nodo inexistente,
  DFS, componentes.

Commits sugeridos:
- `Agrega clase Grafo con lista de adyacencia`
- `Agrega BFS con aristas bloqueadas y DFS al Grafo`
- `MapaCampus hereda de Grafo`
- `Convierte la Torre en grafo con atajos`
- `Agrega pruebas del Grafo`

## 2. Juan Diego Cornejo: árbol de misiones del juego (árboles)

**Archivos:** `misiones.py`, `tests/test_misiones.py` (nuevo). Pueden reutilizar la lógica
de `arboles.py`, que hoy es solo una demo y el juego no usa.

Las misiones del juego pasan de una lista plana a un **árbol con dependencias**, usando los
ids de sala del juego (`"biblioteca"`, `"lab_siemens"`, `"r101"`…). Las dependencias pueden
salir de `crear_arbol_misiones()` en `arboles.py`.

```python
class Mision:          # agrega: padre, recompensa (int), efecto (dict o None)
    def desbloqueada(self) -> bool: ...          # True si no tiene padre o el padre está completo

def crear_mision_principal() -> Mision: ...      # la raíz
def todas_las_misiones(raiz) -> list[Mision]: ...        # preorden, lista plana (para main.py)
def buscar_por_sala(raiz, sala) -> Mision | None: ...
def crear_arbol_misiones_juego() -> Mision: ...  # crear_mision_principal() queda igual hasta la integración
def completar_por_sala(raiz, sala) -> tuple[bool, str | list[Mision]]: ...
    # (True, hijas_desbloqueadas) o (False, "mensaje claro") si no existe, ya está o está bloqueada
def lineas_preorden(raiz) -> list[tuple[int, Mision]]: ...   # (nivel, misión) para dibujar con sangría
def por_niveles(raiz) -> list[list[Mision]]: ...              # recorrido por niveles: etapas
def recompensa_rama(mision) -> int: ...                       # postorden: suma de la rama
```

- Recorridos con propósito real: el **preorden** dibuja la bitácora, el recorrido **por niveles**
  lista lo disponible por etapa y el **postorden** suma las recompensas para el puntaje final.
- `efecto` es un dato para el diccionario, por ejemplo `{"abre": ("terraza", "terraza_n")}` en
  *Cierre de caja* o `{"apaga": "biblioteca"}` en *Préstamo de medianoche*.
- Pruebas: misión bloqueada, misión repetida, sala inexistente, los tres recorridos, suma de rama.

Commits sugeridos:
- `Convierte las misiones en árbol con dependencias`
- `Agrega recorridos preorden, por niveles y postorden a las misiones`
- `Agrega efectos y recompensas a las misiones`
- `Agrega pruebas del árbol de misiones`

## 3. Ricardo Vides: diccionario del estado del mundo + deshacer (diccionarios)

**Archivos:** `estado_mundo.py`, `tests/test_estado_mundo.py` (nuevo).

Hoy el diccionario solo guarda la hora. Tiene que cubrir lo que cambia durante la partida
y lo que el juego consulta seguido:

```python
estado = {
    "hora_actual_min": ..., "hora_toque_queda_min": ..., "toque_queda_activo": False,
    "luces":   {"biblioteca": True, ...},                    # clave: texto
    "puertas": {("terraza", "terraza_n"): "cerrada",          # clave: TUPLA (nunca lista)
                ("lobby_frente", "lobby"): "abierta"},
    "misiones": {"biblioteca": "disponible", ...},            # bloqueada / disponible / completada
    "vigilante_alerta": False,
}

def consultar(estado, seccion, clave, defecto=None): ...   # usa .get(), nunca []
def actualizar(estado, seccion, clave, valor) -> valor_anterior: ...
def insertar(estado, seccion, clave, valor) -> bool: ...    # False si ya existía
def eliminar(estado, seccion, clave) -> bool: ...           # .pop(clave, None)
def aplicar_efecto(estado, efecto) -> list[cambio]: ...     # cambio = (seccion, clave, valor_anterior)
def revertir_cambios(estado, cambios): ...                  # para deshacer
# Al menos 2 funciones propias de resumen/filtro:
def puertas_cerradas(estado) -> list[tuple]: ...            # se le pasa al BFS como `bloqueadas`
def salas_iluminadas(estado) -> list[str]: ...
def resumen(estado) -> dict: ...                            # conteos para el HUD/README
```

- El toque de queda (`avanzar_tiempo`) tiene que cerrar `("lobby_frente", "lobby")`.
- **Decisión de deshacer** (la pide la rúbrica). Propuesta: al deshacer un `usar` que completó
  una misión, se revierten sus cambios en el diccionario con `revertir_cambios`, pero la hora
  no retrocede y el toque de queda no se deshace. Escriban el porqué en dos líneas para el README.
- Pruebas: `.get` con clave inexistente, insertar repetido, eliminar inexistente, efecto y reversión,
  toque de queda que cierra el lobby.

Commits sugeridos:
- `Amplía el estado del mundo con luces, puertas y misiones`
- `Agrega consulta, inserción, actualización y eliminación seguras`
- `Agrega aplicar_efecto y revertir_cambios para deshacer`
- `Agrega filtros puertas_cerradas, salas_iluminadas y resumen`
- `Agrega pruebas del estado del mundo`

## 4. Santiago Merino: integración en main.py + casos límite (integración)

**Archivos:** `main.py`, `tests/test_checkpoint3.py` (nuevo). Arranca cuando estén los PR 1 a 3.

- Reemplazar `self.mision.hijas` por `todas_las_misiones(...)` y bloquear las estaciones de
  misiones no desbloqueadas, con el mensaje "Primero completa X".
- Al completar una misión: `aplicar_efecto` → guardar los `cambios` en la acción del historial
  → al deshacer, `revertir_cambios`.
- El vigilante y la "ruta al siguiente encargo" usan `bfs_ruta(..., bloqueadas=puertas_cerradas(estado))`.
- La Torre usa `grafo_desde_mazmorra` para moverse y mostrar rutas alternativas.
- El puntaje final suma `recompensa_rama(raiz)`.
- Casos límite en todos los menús: texto, 0, negativos, fuera de rango, sala o misión inexistente,
  ruta imposible, acción repetida. Revisar que el CP2 siga pasando.
- Al final: probar en un clon limpio, crear el tag `checkpoint-3` y entregar en Canvas.

Commits sugeridos:
- `Integra el árbol de misiones con bloqueo por dependencias`
- `Conecta efectos de misiones con el estado del mundo y el deshacer`
- `El vigilante y la ruta al encargo esquivan puertas cerradas`
- `Usa el grafo de la Torre con atajos`
- `Agrega pruebas de integración del Checkpoint 3`

## 5. Nathaly Mena: bitácora en árbol + README + evidencia (documentación)

**Archivos:** `hud_campus.py` (la función `dibujar_diario`), `README.md`, `docs/`.

- `dibujar_diario` dibuja el árbol con sangría usando `lineas_preorden(raiz)`: completadas en
  verde, disponibles en blanco y bloqueadas con candado o en gris. Abajo, la etapa actual
  usando `por_niveles`.
- **README · sección Checkpoint 3**, con todo lo que pide el punto 9:
  - Cómo ejecutar el juego y la lista de funcionalidades hasta ahora.
  - Para cada estructura (grafo, árbol, diccionario): qué resuelve en el juego, por qué es la
    adecuada y su complejidad (BFS/DFS O(V+E), recorridos O(n), dict O(1) promedio contra lista O(n)).
  - El dibujo del grafo del campus, del grafo de la Torre y del árbol de misiones (ASCII o imagen).
  - Cómo trabajan juntas las estructuras (el diagrama de arriba) y la decisión sobre deshacer (la de Ricardo).
  - Los casos límite que se cubren.
  - Evidencia: capturas con `capturar_juego.py` y la salida de las pruebas.
  - Aporte de cada integrante (actualizar la tabla).

Commits sugeridos:
- `La bitácora muestra el árbol de misiones con sangría`
- `Documenta grafo, árbol y diccionario del Checkpoint 3 en el README`
- `Agrega diagramas del grafo y del árbol de misiones`
- `Agrega evidencia de ejecución del Checkpoint 3`

---

## Calendario

| Cuándo | Qué |
|---|---|
| **Jueves 19 (hoy en la noche)** | Santiago invita a todos y al docente como colaboradores. Cada quien clona el repo, crea su rama y hace su **primer commit real** (esqueleto y primeras pruebas). |
| **Viernes 20, antes de las 12:00** | PR de Frederick, Juan Diego y Ricardo listos, con pruebas pasando. Santiago los revisa y los fusiona. |
| **Viernes 20, de 12:00 a 18:00** | Santiago integra en `main.py`. Nathaly hace la bitácora y el README (puede empezar antes con los contratos de arriba). |
| **Viernes 20, 20:00** | Todos prueban un clon limpio: `python main.py` y las pruebas. Arreglos finales, cada uno en su parte. |
| **Viernes 20, 22:00** | Tag `checkpoint-3` y entrega del link en Canvas. **No esperar a las 23:30.** |

## Checklist final

- [ ] El docente y los 5 integrantes tienen acceso al repo.
- [ ] Cada integrante tiene varios commits propios en `git shortlog -sn`.
- [ ] Un clon limpio corre desde `main.py` y pasan todas las pruebas (CP2 + CP3).
- [ ] El grafo, el árbol y el diccionario se afectan entre sí dentro de la partida.
- [ ] Los menús aguantan texto, 0, negativos y fuera de rango.
- [ ] El README tiene el porqué y la complejidad de cada estructura, los diagramas y la decisión de deshacer.
- [ ] `git tag checkpoint-3 && git push origin checkpoint-3` sobre la versión final.
