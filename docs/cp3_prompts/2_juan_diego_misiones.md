# Prompt para tu AI · Juan Diego Cornejo · Árbol de misiones del juego

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

Somos 5 integrantes y cada uno tiene **su propia parte del Checkpoint 3**. La mía son los
**árboles**. La rúbrica pide:

> *Utilicen árboles para modelar lo que en su juego dependa de algo anterior (misiones…).
> Completar o desbloquear un nodo debe tener efecto en la partida. Implementen al menos 2
> recorridos (preorden, postorden o por niveles) y úsenlos con un propósito real: mostrar el
> árbol con sangría, sumar recompensas de una rama o listar lo disponible por etapa.*

### Estado actual del repo (lo relevante para mí)

- `misiones.py` tiene `class Mision` con `titulo`, `descripcion`, `ubicacion` (id de sala),
  `completada`, `hijas`, `pasos` (tupla de textos), `paso` (int), `completar()`,
  `todas_completas()`, `pendientes()` y la propiedad `objetivo_actual`.
  `crear_mision_principal()` arma una raíz "Salir del campus" con **13 hijas planas** a partir de
  la lista `ENCARGOS` (sala, título, pasos).
- **Hoy no hay dependencias:** las 13 están disponibles desde el inicio. Eso es lo que hay que cambiar.
- `arboles.py` es una **demo aparte** (el juego no la usa) con un árbol de misiones con
  dependencias, `recorrido_preorden`, `recorrido_postorden`, `misiones_disponibles` y
  `completar_mision`, más `tests/test_arboles.py`. Puedes reutilizar su lógica, pero **no rompas
  esos archivos ni sus pruebas**.
- `main.py`, `hud_campus.py`, `habilidades.py` y las pruebas usan `p.mision.hijas` como la
  lista plana de 13 encargos. Por eso **`crear_mision_principal()` NO se cambia en tu PR**:
  agregas una función nueva y Santiago hace el cambio en `main.py` cuando integre.

### Contrato con el resto del equipo (no cambies los nombres)

- **Santiago** (integración) va a usar `crear_arbol_misiones_juego()`, `todas_las_misiones`,
  `buscar_por_sala`, `Mision.desbloqueada()`, `Mision.efecto`, `disponibles` y `recompensa_rama`.
- **Nathaly** (bitácora en pantalla) va a usar `lineas_preorden(raiz)` y `por_niveles(raiz)`.
- **Ricardo** (diccionario) recibe `mision.efecto` y lo aplica al estado del mundo. Formato del efecto:
  `{"abre": ("terraza", "terraza_n")}`, `{"cierra": (a, b)}`, `{"apaga": "biblioteca"}`,
  `{"enciende": "sala"}` o `None`. Las tuplas de puertas van **ordenadas alfabéticamente**.

---

## Qué tienes que construir

### Archivos que puedes tocar
`misiones.py` · `tests/test_misiones.py` (nuevo). **Ningún otro.**

### 1. Ampliar `Mision` (sin romper lo existente)

Agrega estos atributos y métodos y mantén todo lo que ya existe:
```python
self.padre = None          # un solo padre → es árbol, no grafo
self.recompensa = 0        # puntos al completarla
self.efecto = None         # dict para el estado del mundo (ver contrato)
self.es_raiz = False

def agregar_submision(self, mision):     # ya existe: ahora también hace mision.padre = self
def desbloqueada(self) -> bool:          # True si no tiene padre, si el padre es la raíz o si el padre está completada
def nivel(self) -> int:                  # 0 para la raíz, 1 para sus hijas, etc.
```

### 2. Árbol con dependencias: `crear_arbol_misiones_juego()`

Usa **los mismos 13 encargos de `ENCARGOS`** (mismos títulos, salas y pasos) y cuélgalos así.
La raíz es un contenedor (`es_raiz=True`) que se considera "completada" solo cuando todas sus
descendientes lo están:

```
Salir del campus (lobby)  [raíz]
└── Préstamo de medianoche (biblioteca)            efecto {"apaga": "biblioteca"}
    ├── Una última firma (sala_reuniones)
    │   ├── Cálculo pendiente (r102)
    │   └── Última exposición (r105)
    │       └── Bitácora de física (r104)
    ├── Entrega digital (r101)
    │   ├── Puesta en marcha (lab_siemens)
    │   │   └── Prototipo listo (lab_kite)
    │   └── Redes conectadas (r103)
    │       └── Respaldo completo (lab_click)
    └── Cierre de caja (cafeteria)                 efecto {"abre": ("terraza", "terraza_n")}
        └── Todo en su lugar (bodega)
            └── Señal estable (lab_spark)
```

- La lógica sale del juego: con el libro de la biblioteca arranca la noche, la USB de R101 se usa
  en Siemens, el profesor firma antes de las entregas de aulas y la cafetería se cierra antes de la bodega.
- Recompensa por nivel: nivel 1 = 10, nivel 2 = 20, nivel 3 = 30, nivel 4 = 40 (o la que
  decidas, pero documentada).
- Devuelve 4 niveles debajo de la raíz y 13 encargos en total.

### 3. Funciones del módulo (recorridos con propósito)

```python
def todas_las_misiones(raiz) -> list[Mision]:
    """PREORDEN sin la raíz. Es la lista plana que usa el juego (13 encargos).
    Como el preorden visita al padre antes que a sus hijas, completar en este
    orden siempre respeta las dependencias. O(n)."""

def buscar_por_sala(raiz, sala) -> Mision | None: ...           # O(n); None si no existe

def disponibles(raiz) -> list[Mision]: ...    # desbloqueadas y sin completar

def completar_por_sala(raiz, sala) -> tuple[bool, str | list[Mision]]:
    """(True, hijas_que_se_desbloquean) o (False, "mensaje claro") si la sala no
    existe, si ya estaba completada o si está bloqueada ("Primero completa «X»")."""

def lineas_preorden(raiz) -> list[tuple[int, Mision]]:
    """PREORDEN con nivel: [(0, raiz), (1, biblioteca), (2, sala_reuniones), ...].
    Lo usa la bitácora para dibujar el árbol con sangría."""

def por_niveles(raiz) -> list[list[Mision]]:
    """Recorrido POR NIVELES (BFS con deque): [[raiz], [biblioteca], [sala_reuniones, r101, cafeteria], ...].
    Sirve para mostrar en qué etapa de la noche va el jugador."""

def recompensa_rama(mision, solo_completadas=True) -> int:
    """POSTORDEN: suma las recompensas de la rama (primero las hijas, después el nodo).
    Se usa para el puntaje final y para mostrar cuánto vale cada rama."""

def texto_arbol(raiz) -> str:
    """El árbol con sangría y marcas [x] completada, [ ] disponible, [bloqueada]. Usa lineas_preorden."""
```

- Ninguna lanza excepción con datos inválidos (sala inexistente, `None`, misión repetida).
- Cada función con un docstring que diga **para qué la usa el juego y su complejidad** (O(n)).
- `completar_por_sala` es para la lógica y las pruebas. En el juego, las estaciones siguen
  avanzando `paso` y llaman a `mision.completar()`; Santiago revisa `desbloqueada()` antes de dejar avanzar.

### 4. `tests/test_misiones.py` (unittest, sin pygame)

1. El árbol tiene 13 encargos, la raíz tiene 1 hija y cada encargo tiene exactamente 1 padre.
2. Al inicio solo `biblioteca` está disponible.
3. Completar `lab_siemens` antes que `r101` falla con un mensaje que nombra «Entrega digital».
4. Completar `biblioteca` desbloquea `sala_reuniones`, `r101` y `cafeteria`.
5. Completar la misma misión dos veces → `(False, mensaje)`.
6. `buscar_por_sala(raiz, "no_existe")` → `None`. `completar_por_sala` con una sala inexistente → `(False, ...)`.
7. `todas_las_misiones` respeta las dependencias: completar en ese orden nunca falla.
8. `por_niveles` devuelve 5 niveles con 1, 1, 3, 5, 4 misiones (raíz incluida).
9. `recompensa_rama` de la raíz con todo completado = suma de todas las recompensas; sin nada completado = 0.
10. `texto_arbol` tiene 14 líneas y la sangría crece con el nivel.
11. `crear_mision_principal()` sigue devolviendo 13 hijas planas (para no romper el juego).

---

## Plan de trabajo y commits (uno por paso, el juego corre después de cada uno)

```bash
git clone git@github.com:SantiMerino/9PM.git && cd 9PM
git config user.name "Juan Diego Cornejo"
git config user.email "<el correo de tu cuenta de GitHub>"
python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt
git checkout -b cp3/juan-diego
```

| # | Qué hacer | Mensaje de commit |
|---|---|---|
| 1 | `padre`, `desbloqueada`, `nivel`, `recompensa`, `efecto` en `Mision` + prueba 11 | `Agrega padre, desbloqueo y recompensa a las misiones` |
| 2 | `crear_arbol_misiones_juego()` con las dependencias + pruebas 1, 2 y 4 | `Arma el árbol de misiones con dependencias entre encargos` |
| 3 | `buscar_por_sala`, `disponibles`, `completar_por_sala` + pruebas 3, 5 y 6 | `Agrega búsqueda y completado con bloqueo por dependencias` |
| 4 | `todas_las_misiones`, `lineas_preorden`, `texto_arbol` + pruebas 7 y 10 | `Agrega recorrido preorden con sangría para la bitácora` |
| 5 | `por_niveles` y `recompensa_rama` + pruebas 8 y 9 | `Agrega recorridos por niveles y postorden para etapas y recompensas` |

Antes de **cada** commit:
```bash
python -m unittest discover -s tests
python main.py
```
Al final: `git push -u origin cp3/juan-diego` y abre un **Pull Request a `main`** con
título "CP3 · Árbol de misiones con dependencias y recorridos". **Fecha límite: viernes 20, 12:00.**
Avísale a Nathaly y a Santiago cuando esté fusionado, porque los dos dependen de ti.

---

## Resultado esperado

1. **Archivos:** `misiones.py` ampliado (unas 150–200 líneas con docstrings) y
   `tests/test_misiones.py` con 11 o más pruebas.
2. **Pruebas:** `python -m unittest discover -s tests` termina en `OK` (las 77 de antes + las tuyas).
3. **Juego:** `python main.py` funciona **igual que antes**. Tu árbol todavía no está conectado;
   eso lo hace Santiago.
4. **Demo en consola** (para la evidencia del README, pásale el texto a Nathaly):
   ```
   >>> from misiones import *
   >>> r = crear_arbol_misiones_juego()
   >>> print(texto_arbol(r))
   Salir del campus
     [ ] Préstamo de medianoche (biblioteca)
       [bloqueada] Una última firma (sala_reuniones)
         [bloqueada] Cálculo pendiente (r102)
         ...
   >>> completar_por_sala(r, "lab_siemens")
   (False, 'Primero completa «Entrega digital».')
   >>> [[m.ubicacion for m in nivel] for nivel in por_niveles(r)][2]
   ['sala_reuniones', 'r101', 'cafeteria']
   ```
5. **Historial:** 5 commits tuyos en `git log --author="Juan Diego"`, con mensajes claros.
6. **Para el README** (mándaselo a Nathaly): 3–4 líneas sobre por qué un árbol es la estructura
   adecuada (cada encargo depende de **un solo** anterior y no hay ciclos), qué hace cada recorrido
   en el juego y su complejidad (O(n) cada recorrido, porque visita cada nodo una vez).

## Lo que NO debes hacer
- No cambies `crear_mision_principal()` ni la lista `ENCARGOS`, porque el juego actual depende de ellos.
- No toques `main.py`, `hud_campus.py`, `arboles.py` ni el README.
- No hagas un solo commit gigante ni commits vacíos.
