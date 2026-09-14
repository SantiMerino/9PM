# Checkpoint 1 — Aventura Algorítmica: *9PM*

Equipo de 5 · Semanas 1 a 3 · 10% de la nota final

**Integrantes:**

- José Santiago Merino Herrera
- Frederick William Argueta Tejada
- Nathaly Alessandra Mena Guevara
- Juan Diego Cornejo Gonzalez
- Ricardo Andres Vides Portillo

Este documento reúne los cuatro entregables del Checkpoint 1: el concepto del
juego, el diagrama de flujo con su pseudocódigo de una mecánica, el inventario
del jugador funcionando con listas, y la explicación del código con sus
fragmentos relevantes. El proyecto completo vive en la carpeta
[`9PM/`](..); este archivo está en `9PM/docs/CHECKPOINT1.md`.

---

## 1. Concepto del juego (Semana 1)

| Elemento | Descripción |
|---|---|
| **Mundo** | El campus de una universidad, de noche. Son las **20:15** y a las **21:00** empieza el toque de queda. El campus se modela como un grafo de salas conectadas por pasillos (entrada, patio central, biblioteca, cafetería, salones, laboratorio, auditorio, oficina del profesor y parqueadero). |
| **Protagonista** | Un/a estudiante que se quedó tarde resolviendo pendientes académicos y debe salir del campus antes de que empiece el toque de queda. Es la persona que el jugador controla y mueve por el mapa. |
| **Antagonista** | El **vigilante** nocturno del campus. Patrulla el campus siguiendo una ronda fija; si te ve *después* de las 21:00, te expulsa del campus por esa noche (game over). |
| **Objeto especial** | **El libro atrasado.** Hay que recogerlo en la entrada y devolverlo en la biblioteca antes de irte; es el objeto que primero se guarda y se usa desde el inventario. |
| **Problema a resolver** | Resolver tres pendientes — devolver el libro, imprimir un trabajo en el laboratorio y hablar con el profesor — y llegar al parqueadero antes de las 21:00, sin ser visto por el vigilante una vez empiece el toque de queda. |

Estos elementos ya están implementados: el grafo del campus en
[`mapa.py`](../mapa.py), el estado del reloj y el toque de queda en
[`estado_mundo.py`](../estado_mundo.py), y las tres misiones en
[`misiones.py`](../misiones.py).

---

## 2. Diagrama de flujo y pseudocódigo (Semana 2 / Guía 2)

Se documentan dos mecánicas del juego: **recoger / usar / soltar un objeto**
(la mecánica de inventario que pide este checkpoint) y **la detección del
vigilante** (la mecánica que genera la tensión y el "game over" del juego).

### 2.1 Mecánica: recoger, usar y soltar un objeto

El inventario tiene tres operaciones y cada una está atada a una tecla:

| Tecla | Operación | Qué hace con la lista |
|---|---|---|
| `ESPACIO` | **recoger** un objeto tirado en el mapa, o **usar** el libro/USB en su sala | `agregar()` → `list.append()`, o `usar()` → `list.remove()` |
| `G` | **soltar** el último objeto de la mochila | `soltar_ultimo()` → `list.pop()` |

Implementadas en `Partida.interactuar()` y `Partida.soltar_objeto()` dentro de
[`main.py`](../main.py), sobre `Inventario.agregar()`, `Inventario.usar()` y
`Inventario.soltar_ultimo()` de [`inventario.py`](../inventario.py).

```mermaid
flowchart TD
    A([El jugador presiona ESPACIO]) --> B{¿Hay un objeto tirado\nen el mapa a menos de\n55 px del jugador?}
    B -- Sí --> C{¿inventario.esta_lleno()?}
    C -- Sí --> D[Mostrar aviso:\n'Tu mochila está llena']
    D --> Z([Fin])
    C -- No --> E[inventario.agregar objeto\nlista.append]
    E --> F[Marcar el objeto como\nrecogido y avisar\n'Recogiste: ...']
    F --> Z
    B -- No --> G{¿Sala más cercana =\n'biblioteca' Y\ninventario.tiene 'libro'?}
    G -- Sí --> H[inventario.usar 'libro'\nlista.remove]
    H --> I[mision_libro.completar\ny avisar 'Devolviste el libro']
    I --> Z
    G -- No --> K[Probar otras salas\nlaboratorio, oficina, parqueadero]
    K --> Z

    P([El jugador presiona G]) --> Q[objeto = inventario.soltar_ultimo\nlista.pop]
    Q --> R{¿objeto = None\nmochila vacía?}
    R -- Sí --> S[Avisar 'No tienes nada que soltar']
    S --> Z
    R -- No --> T[Dejar el objeto tirado en\nel mapa en la posición del\njugador y avisar 'Soltaste: ...']
    T --> Z
```

**Pseudocódigo:**

```
Algoritmo Interactuar   // tecla ESPACIO -> Partida.interactuar()
    objeto_cercano <- objeto del mapa a menos de RADIO_INTERACCION del jugador

    Si objeto_cercano <> nulo Entonces
        Si inventario.esta_lleno() Entonces
            Mostrar "Tu mochila está llena"
        SiNo
            inventario.agregar(objeto_cercano)   // lista.append()
            objeto_cercano.recogido <- verdadero
            Mostrar "Recogiste: " + objeto_cercano.titulo
        FinSi
        Terminar

    sala <- sala más cercana al jugador
    Si sala = "biblioteca" Y inventario.tiene("libro") Entonces
        inventario.usar("libro")                 // lista.remove()
        mision_libro.completar()
        Mostrar "Devolviste el libro. Misión completa"
    SiNo Si sala = "laboratorio" Y inventario.tiene("usb") Entonces
        inventario.usar("usb")                   // lista.remove()
        mision_lab.completar()
    FinSi
FinAlgoritmo


Algoritmo SoltarObjeto   // tecla G -> Partida.soltar_objeto()
    objeto <- inventario.soltar_ultimo()         // lista.pop()
    Si objeto = nulo Entonces
        Mostrar "No tienes nada que soltar"
    SiNo
        agregar objeto a los objetos del mapa en la posición del jugador
        Mostrar "Soltaste: " + objeto.titulo
    FinSi
FinAlgoritmo
```

### 2.2 Mecánica: detección del vigilante

Se evalúa en cada cuadro del juego dentro de `Partida.actualizar()`
([`main.py`](../main.py)), usando el grafo y BFS/DFS de
[`mapa.py`](../mapa.py) para mover al vigilante y el diccionario de
[`estado_mundo.py`](../estado_mundo.py) para saber si el toque de queda ya
empezó.

```mermaid
flowchart TD
    A([Inicio: cada cuadro del juego]) --> B[Mover al vigilante un paso\nsobre su ruta BFS actual]
    B --> C{¿Terminó la ruta\nactual del vigilante?}
    C -- Sí --> D[Calcular nueva ruta con BFS\nhacia la siguiente sala de su\nronda DFS]
    D --> E
    C -- No --> E{¿Ya está activo\nel toque de queda?}
    E -- No --> Z([Fin del cuadro])
    E -- Sí --> F[Calcular distancia entre\njugador y vigilante]
    F --> G{¿distancia < RADIO_DETECCION\n_(75 px)_?}
    G -- Sí --> H[Fin de la partida:\n'Un vigilante te vio\ndespués del toque de queda']
    H --> Z
    G -- No --> Z
```

**Pseudocódigo:**

```
Algoritmo DetectarJugador
    Definir toque_queda_activo Como Lógico
    Definir pos_jugador, pos_vigilante Como Punto
    Definir RADIO_DETECCION Como Entero = 75

    vigilante.moverUnPaso()   // avanza por su ruta BFS; si la terminó, arma
                              // una nueva con BFS hacia la siguiente sala
                              // de su ronda (calculada con DFS al iniciar)

    Si toque_queda_activo Entonces
        distancia <- Distancia(pos_jugador, pos_vigilante)
        Si distancia < RADIO_DETECCION Entonces
            partida.terminar("Un vigilante te vio después del toque de queda")
        FinSi
    FinSi
FinAlgoritmo
```

---

## 3. Inventario funcional con listas (Semana 3)

El inventario del jugador es una **lista** de diccionarios (`self.objetos = []`),
implementada en [`inventario.py`](../inventario.py). Las tres operaciones que
pide el checkpoint son métodos sobre esa lista:

```python
class Inventario:
    def __init__(self, capacidad_maxima=6):
        self.objetos = []                      # <-- la lista de la Semana 3
        self.capacidad_maxima = capacidad_maxima

    # AGREGAR (recoger): mete el objeto al final de la lista
    def agregar(self, objeto):
        if len(self.objetos) >= self.capacidad_maxima:
            return False                       # mochila llena: no se agrega
        self.objetos.append(objeto)
        return True

    # USAR (consumir): busca por nombre y lo saca de la lista
    def usar(self, nombre_objeto):
        for objeto in self.objetos:
            if objeto["nombre"] == nombre_objeto:
                self.objetos.remove(objeto)
                return objeto                  # se devuelve para aplicar su efecto
        return None

    # SOLTAR (tirar): igual que usar a nivel de lista, pero el objeto
    # vuelve a quedar tirado en el mapa
    def soltar(self, nombre_objeto):
        for objeto in self.objetos:
            if objeto["nombre"] == nombre_objeto:
                self.objetos.remove(objeto)
                return objeto
        return None

    def soltar_ultimo(self):                   # tecla G: suelta lo último recogido
        if not self.objetos:
            return None
        return self.objetos.pop()

    def tiene(self, nombre_objeto):
        return any(o["nombre"] == nombre_objeto for o in self.objetos)

    def esta_lleno(self):
        return len(self.objetos) >= self.capacidad_maxima
```

- **Agregar (recoger):** `agregar()` usa `list.append()` y respeta la
  `capacidad_maxima` (devuelve `False` y no agrega nada si la mochila ya está
  llena).
- **Usar (consumir):** `usar()` recorre la lista, saca el objeto con
  `list.remove()` y lo devuelve para aplicar su efecto — por ejemplo, al
  entregar el libro en la biblioteca se llama `usar("libro")` y se completa la
  misión. `tiene()` se usa antes para confirmar que el objeto está.
- **Soltar (tirar):** `soltar()` / `soltar_ultimo()` sacan el objeto de la
  lista (`list.remove()` / `list.pop()`) y el juego lo vuelve a dejar tirado en
  el mapa para recogerlo después.

Dentro del juego, `main.py` conecta estas acciones a la interacción del
jugador (`Partida.interactuar` y `Partida.soltar_objeto`):

```python
# ESPACIO: recoger un objeto tirado en el mapa (AGREGAR)
objeto_mundo = self._objeto_cercano()
if objeto_mundo is not None:
    objeto = crear_objeto(objeto_mundo["nombre"])
    if self.inventario.agregar(objeto):
        objeto_mundo["recogido"] = True
        self._agregar_toast(f"Recogiste: {objeto['titulo']}.")
    else:
        self._agregar_toast("Tu mochila está llena.")
    return

# ESPACIO en la biblioteca con el libro encima: USAR
if sala == "biblioteca" and self.inventario.tiene("libro"):
    self.inventario.usar("libro")
    self.mision_libro.completar()
    self._agregar_toast("Devolviste el libro. Misión completa.")

# G: SOLTAR el último objeto y dejarlo tirado en el mapa
def soltar_objeto(self):
    objeto = self.inventario.soltar_ultimo()
    if objeto is None:
        self._agregar_toast("No tienes nada que soltar.")
        return
    self.objetos_mundo.append({
        "nombre": objeto["nombre"],
        "pos": (self.jugador.x, self.jugador.y + 24),
        "recogido": False,
    })
    self._agregar_toast(f"Soltaste: {objeto['titulo']}.")
```

El panel visual del inventario (tecla `I`/`TAB`) está en
[`ui_inventario.py`](../ui_inventario.py), y la búsqueda de un objeto por
nombre (tecla `F`) usa la misma lista en
[`buscador.py`](../buscador.py).

### Evidencia de ejecución

[`demo_inventario.py`](../demo_inventario.py) ejercita `Inventario` de forma
independiente (sin abrir la ventana del juego): agrega objetos hasta llenar la
mochila, usa uno (se consume), suelta otro (se tira) y prueba los casos límite
(mochila llena, y usar/soltar algo que ya no está). Se ejecuta con:

```bash
cd 9PM
python demo_inventario.py
```

Salida real de la ejecución:

```
--- 1. Inventario vacio ---
Objetos: []

--- 2. AGREGAR objetos (recoger) -> list.append() ---
agregar('libro'): OK
agregar('usb'): OK
agregar('cafe'): OK
Objetos actuales: ['libro', 'usb', 'cafe']

--- 3. Caso limite: AGREGAR con la mochila llena ---
agregar('llaves') con mochila llena: RECHAZADO
esta_lleno(): True

--- 4. Consultar antes de USAR -> tiene() ---
tiene('libro'): True
tiene('llaves'): False

--- 5. USAR un objeto (se consume: sale de la lista) -> list.remove() ---
usar('libro') devolvio: Libro atrasado
Objetos despues de usar: ['usb', 'cafe']

--- 6. SOLTAR un objeto (se tira: sale de la lista) -> list.remove() ---
soltar('usb') devolvio: USB del trabajo
Objetos despues de soltar: ['cafe']

--- 7. Casos limite: USAR y SOLTAR algo que ya no esta ---
usar('libro'): None
soltar('usb'): None

--- 8. Ahora hay espacio: AGREGAR las llaves que antes se rechazaron ---
agregar('llaves'): OK
Objetos finales: ['cafe', 'llaves']
```

Esto confirma que **agregar**, **usar** y **soltar** funcionan sin errores,
incluyendo los casos límite: mochila llena, y usar/soltar un objeto que ya no
está. El inventario también funciona integrado en el juego: `python main.py`,
`ESPACIO` cerca del libro para recogerlo, `ESPACIO` en la biblioteca para
usarlo, `G` para soltar el último objeto y `I`/`TAB` para ver la mochila.

---

## 4. Organización del código (Guía 1)

El proyecto sigue un archivo por estructura de datos / tema, con `main.py`
como archivo central que arma la ventana, el bucle del juego y conecta todo
lo demás:

| Archivo | Estructura de datos | Uso |
|---|---|---|
| [`main.py`](../main.py) | — | Archivo central: ventana, bucle principal, estados del juego |
| [`inventario.py`](../inventario.py) | **Lista** (Semana 3) | Objetos que el jugador recoge, usa y suelta |
| [`ui_inventario.py`](../ui_inventario.py) | — | Panel visual del inventario y catálogo de objetos |
| [`estado_mundo.py`](../estado_mundo.py) | Diccionario | Hora actual, toque de queda, luces |
| [`mapa.py`](../mapa.py) | Grafo (BFS/DFS) | Campus y movimiento/detección del vigilante |
| [`misiones.py`](../misiones.py) | Árbol | Misión principal y sus tres sub-misiones |
| [`historial.py`](../historial.py) | Pila | Deshacer el último movimiento (`Z`) |
| [`eventos.py`](../eventos.py) | Cola | Avisos programados de la noche |
| [`mazmorra.py`](../mazmorra.py) | Recursión | Generación de pisos de un edificio |
| [`ranking.py`](../ranking.py) | Ordenamiento | Mejores puntajes de partidas |
| [`buscador.py`](../buscador.py) | Búsqueda | Buscar un objeto en el inventario por nombre |
| [`demo_inventario.py`](../demo_inventario.py) | — | Evidencia de ejecución del inventario (Checkpoint 1) |

Este checkpoint solo pide hasta la Semana 3 (concepto, diagrama/pseudocódigo
e inventario); los demás archivos ya están integrados y funcionando porque el
equipo avanzó el desarrollo del juego más allá del checkpoint actual, pero no
son parte de lo que se evalúa aquí.

---

## 5. Cómo correr el proyecto

```bash
cd 9PM
pip install -r requirements.txt
python main.py            # el juego completo
python demo_inventario.py # evidencia del inventario por consola
```

Ver [`README.md`](../README.md) para los controles completos del juego.
