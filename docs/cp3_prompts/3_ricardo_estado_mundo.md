# Prompt para tu AI · Ricardo Vides · Diccionario del estado del mundo + deshacer

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

Somos 5 integrantes y cada uno tiene **su propia parte del Checkpoint 3**. La mía es el
**diccionario del estado del mundo**. La rúbrica pide:

> *Guarden en un diccionario el estado del mundo: lo que cambia mientras se juega y que el
> juego necesita consultar rápido. Elijan con cuidado la clave (un texto único o una tupla,
> nunca una lista) y el valor. Usen consulta con `.get()`, actualización, inserción y
> eliminación, y al menos 2 funciones propias que resuman o filtren ese estado.* También pide que
> el equipo **decida y explique qué pasa con el estado del mundo cuando se deshace una acción**.

### Estado actual del repo (lo relevante para mí)

- `estado_mundo.py` tiene `crear_estado_inicial()`, que devuelve
  `{"hora_actual_min", "hora_toque_queda_min", "toque_queda_activo", "luces_encendidas", "vigilante_alerta"}`,
  además de `avanzar_tiempo(estado, minutos)` (activa el toque de queda) y `formatear_hora(min)`.
  **Solo se accede con `[]`; no hay `.get`, inserción, eliminación ni funciones de resumen.**
  `luces_encendidas` no se usa en ningún lado.
- `main.py` y las pruebas leen `estado_mundo["hora_actual_min"]`, `["hora_toque_queda_min"]` y
  `["toque_queda_activo"]` directamente. **Esas 3 claves de primer nivel y las firmas de
  `avanzar_tiempo` y `formatear_hora` tienen que seguir igual.**
- `historial.py` (el que hiciste en el CP2) guarda acciones como dicts con `crear_accion(tipo, texto, hora, **datos)`.
  Al deshacer, `main.py` revierte cada tipo de acción. Hoy, deshacer un `usar` que completó
  una misión vuelve `mision.completada = False`.
- Los nodos del campus (grafo de Frederick) son waypoints como `"lobby"`, `"lobby_frente"`,
  `"terraza"`, `"terraza_n"`. Las salas con misión usan ids como `"biblioteca"`, `"lab_siemens"`, `"r101"`.

### Contrato con el resto del equipo (no cambies los nombres)

- **Juan Diego** le pone a cada misión un `efecto`: `{"abre": (a, b)}`, `{"cierra": (a, b)}`,
  `{"apaga": sala}`, `{"enciende": sala}` o `None`. Las tuplas de puertas vienen **ordenadas**.
- **Frederick** expone `grafo.bfs_ruta(origen, destino, bloqueadas=[...])`, que recibe
  la lista de puertas cerradas que devuelve tu `puertas_cerradas(estado)`.
- **Santiago** (integración) va a llamar a `aplicar_efecto` al completar una misión, va a guardar
  los `cambios` en la acción del historial y va a llamar a `revertir_cambios` al deshacer.

---

## Qué tienes que construir

### Archivos que puedes tocar
`estado_mundo.py` · `tests/test_estado_mundo.py` (nuevo). **Ningún otro.**

### 1. Estructura del diccionario

```python
PUERTA_LOBBY = ("lobby", "lobby_frente")
PUERTA_TERRAZA = ("terraza", "terraza_n")

def clave_puerta(a, b) -> tuple:
    """Clave canónica de una puerta: tupla ORDENADA, así (b, a) y (a, b) son la misma. O(1)."""
    return tuple(sorted((a, b)))

def crear_estado_inicial():
    return {
        "hora_actual_min": 20 * 60 + 15,
        "hora_toque_queda_min": 21 * 60,
        "toque_queda_activo": False,
        "vigilante_alerta": False,
        "luces":    {"biblioteca": True, "cafeteria": True, "lab_siemens": True, "lobby": True},  # clave: texto
        "puertas":  {PUERTA_LOBBY: "abierta", PUERTA_TERRAZA: "cerrada"},                         # clave: TUPLA
        "misiones": {},   # sala -> "bloqueada" | "disponible" | "completada" (Santiago lo llena con insertar)
        "alertas":  {},   # sala -> minutos de alerta restantes (se inserta al activarse y se elimina al vencer)
    }
```

Justificación para el README (escríbela tú): las claves son textos únicos (ids de sala) o
**tuplas** (una puerta une dos nodos). Una lista no puede ser clave porque es mutable y no es *hashable*.

### 2. Operaciones básicas (todas seguras, **nunca** `KeyError`)

```python
SECCIONES = ("luces", "puertas", "misiones", "alertas")

def consultar(estado, seccion, clave, defecto=None):
    """Valor de estado[seccion][clave] con .get(); si la sección o la clave no existen,
    devuelve `defecto`. O(1) promedio."""

def actualizar(estado, seccion, clave, valor):
    """Cambia el valor y devuelve el valor ANTERIOR (None si no existía). O(1)."""

def insertar(estado, seccion, clave, valor) -> bool:
    """Agrega la clave solo si no existía. False si ya estaba o la sección no existe. O(1)."""

def eliminar(estado, seccion, clave) -> bool:
    """Borra la clave con .pop(clave, None). False si no existía. O(1)."""
```

Las claves de puertas se normalizan siempre con `clave_puerta` dentro de estas funciones.

### 3. Efectos de misiones y deshacer

```python
def aplicar_efecto(estado, efecto) -> list[tuple]:
    """Aplica el efecto de una misión al mundo y devuelve la lista de cambios
    [(seccion, clave, valor_anterior), ...] para poder deshacerlo.
    "abre"/"cierra" -> puertas[clave] = "abierta"/"cerrada"
    "apaga"/"enciende" -> luces[sala] = False/True
    efecto None o desconocido -> [] (sin error)."""

def revertir_cambios(estado, cambios):
    """Deshace los cambios en orden inverso. Si valor_anterior es None, la clave
    no existía antes y se elimina."""
```

**Decisión de deshacer** (propuesta, ajústala y escríbela para el README):
> Al deshacer una acción que completó una misión, se revierten sus cambios en el diccionario
> (la puerta vuelve a cerrarse, la luz se vuelve a encender) usando los `cambios` guardados en la
> acción. **La hora y el toque de queda no se deshacen**: el tiempo del juego no retrocede, igual
> que en el CP2 los eventos ya procesados no se vuelven a encolar.

### 4. Tiempo y toque de queda

`avanzar_tiempo(estado, minutos)` mantiene su firma y, **la primera vez** que se activa el
toque de queda, cierra `PUERTA_LOBBY` en `estado["puertas"]`. A partir de ahí el jugador
tiene que salir por la terraza, y solo puede si ya completó *Cierre de caja*. Además,
`avanzar_tiempo` descuenta los minutos de `alertas` y **elimina** las que llegan a 0.
Devuelve la lista de salas cuya alerta venció (antes no devolvía nada, así que no rompe nada).

### 5. Funciones propias de resumen y filtro (mínimo 2; haz estas 4)

```python
def puertas_cerradas(estado) -> list[tuple]:      # lo que el BFS recibe como `bloqueadas`
def salas_iluminadas(estado) -> list[str]:        # ordenadas
def misiones_con_estado(estado, valor) -> list[str]:   # p. ej. todas las "disponible"
def resumen(estado) -> dict:
    """{'hora': '20:45', 'toque_queda': False, 'puertas_cerradas': 1,
        'luces_encendidas': 3, 'misiones': {'completada': 2, 'disponible': 3, 'bloqueada': 8},
        'alertas': 0}"""
```

Cada una con un docstring que diga su complejidad: recorrer una sección es O(k), con k = número de
claves, y una consulta es O(1) promedio contra O(n) si se buscara en una lista.

### 6. `tests/test_estado_mundo.py` (unittest, sin pygame)

1. `consultar` con una clave o sección inexistente devuelve `defecto` (sin `KeyError`).
2. `clave_puerta("terraza_n", "terraza") == ("terraza", "terraza_n")`, y consultar en cualquier orden da lo mismo.
3. `insertar` repetido → `False` y el valor no cambia. `eliminar` de algo inexistente → `False`.
4. `actualizar` devuelve el valor anterior.
5. `aplicar_efecto({"abre": PUERTA_TERRAZA})` abre la terraza y `revertir_cambios` la vuelve a cerrar.
6. `aplicar_efecto(None)` y `aplicar_efecto({"vuela": 1})` → `[]` sin error.
7. Avanzar hasta las 21:00 activa el toque de queda y cierra el lobby: `PUERTA_LOBBY in puertas_cerradas(estado)`.
8. Una alerta insertada con 3 minutos se elimina después de `avanzar_tiempo(estado, 3)`.
9. `resumen` devuelve los conteos correctos después de varias operaciones.
10. Las claves viejas `hora_actual_min`, `hora_toque_queda_min` y `toque_queda_activo` siguen existiendo.

---

## Plan de trabajo y commits (uno por paso, el juego corre después de cada uno)

```bash
git clone git@github.com:SantiMerino/9PM.git && cd 9PM
git config user.name "Ricardo Vides"
git config user.email "<el correo de tu cuenta de GitHub>"
python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt
git checkout -b cp3/ricardo
```

| # | Qué hacer | Mensaje de commit |
|---|---|---|
| 1 | Nueva estructura con `luces`, `puertas` (tuplas), `misiones` y `alertas`, más `clave_puerta` + pruebas 2 y 10 | `Amplía el estado del mundo con luces, puertas con tuplas y misiones` |
| 2 | `consultar`, `actualizar`, `insertar` y `eliminar` + pruebas 1, 3 y 4 | `Agrega consulta con get, inserción, actualización y eliminación seguras` |
| 3 | `aplicar_efecto` y `revertir_cambios` + pruebas 5 y 6 | `Agrega efectos de misiones sobre el mundo y su reversión al deshacer` |
| 4 | Toque de queda que cierra el lobby y alertas que vencen + pruebas 7 y 8 | `El toque de queda cierra el lobby y las alertas vencen con el tiempo` |
| 5 | `puertas_cerradas`, `salas_iluminadas`, `misiones_con_estado` y `resumen` + prueba 9 | `Agrega filtros y resumen del estado del mundo` |

Antes de **cada** commit:
```bash
python -m unittest discover -s tests
python main.py       # deja correr el reloj hasta las 21:00 y revisa que nada se rompa
```
Al final: `git push -u origin cp3/ricardo` y abre un **Pull Request a `main`** con
título "CP3 · Diccionario del estado del mundo". **Fecha límite: viernes 20, 12:00.**

---

## Resultado esperado

1. **Archivos:** `estado_mundo.py` ampliado (unas 130–180 líneas con docstrings) y
   `tests/test_estado_mundo.py` con 10 o más pruebas.
2. **Pruebas:** `python -m unittest discover -s tests` termina en `OK` (las 77 de antes + las tuyas).
3. **Juego:** `python main.py` funciona igual que antes, incluido el toque de queda.
4. **Demo en consola** (para la evidencia del README, pásale el texto a Nathaly):
   ```
   >>> from estado_mundo import *
   >>> e = crear_estado_inicial()
   >>> consultar(e, "puertas", ("terraza_n", "terraza"))
   'cerrada'
   >>> cambios = aplicar_efecto(e, {"abre": ("terraza", "terraza_n")}); puertas_cerradas(e)
   []
   >>> revertir_cambios(e, cambios); puertas_cerradas(e)
   [('terraza', 'terraza_n')]
   >>> consultar(e, "luces", "sala_que_no_existe", "sin datos")
   'sin datos'
   >>> avanzar_tiempo(e, 45); resumen(e)["toque_queda"], puertas_cerradas(e)
   (True, [('lobby', 'lobby_frente'), ('terraza', 'terraza_n')])
   ```
5. **Historial:** 5 commits tuyos en `git log --author="Ricardo"`, con mensajes claros.
6. **Para el README** (mándaselo a Nathaly):
   - Por qué un diccionario: el juego consulta "¿está cerrada esta puerta?" muchas veces por
     segundo; con un dict es O(1) promedio y con una lista de pares sería O(n).
   - Por qué esas claves: un texto único por sala y una tupla ordenada por puerta.
   - La **decisión de deshacer** de la sección 3, en dos o tres líneas.

## Lo que NO debes hacer
- No cambies los nombres ni el formato de `hora_actual_min`, `hora_toque_queda_min` y `toque_queda_activo`.
- No uses `estado[seccion][clave]` para leer en tus funciones: usa `.get()` o `in`.
- No toques `main.py`, `historial.py`, `misiones.py` ni el README.
- No hagas un solo commit gigante ni commits vacíos.
