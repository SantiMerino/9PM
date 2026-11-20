# Prompt para tu AI · Santiago Merino · Integración en main.py + casos límite + entrega

> Copia todo este archivo y pégalo en tu AI con el repo abierto. Arranca cuando estén
> fusionados los PR de Frederick (`grafo.py`), Juan Diego (`misiones.py`) y Ricardo (`estado_mundo.py`).

---

## Contexto para la AI

Eres mi asistente de programación en un proyecto universitario de **Estructura de Datos y
Algoritmos** (Python 3.12 + pygame 2.6.1). El repo es `github.com/SantiMerino/9PM`: un RPG de
sigilo en el que un estudiante tiene que completar 13 encargos en el campus antes del toque de
queda (21:00) sin que lo atrape el vigilante. Se ejecuta con `python main.py` y las pruebas
corren con `python -m unittest discover -s tests`.

Somos 5. Mi parte es la **integración (10 pts)**: que el grafo, el árbol y el diccionario **trabajen
juntos dentro de la partida**, que el CP2 siga funcionando y que el programa nunca se cierre con
datos inválidos. También me toca la entrega (el tag `checkpoint-3`). La rúbrica dice:

> *No se evalúa que cada estructura exista por separado, sino que el juego funcione gracias a ellas:
> lo que ocurre en un grafo, un árbol o un diccionario debe afectar a los otros y a la partida. Un
> recorrido que nunca se usa en el juego no cuenta. El deshacer y los eventos del Checkpoint 2 deben
> seguir funcionando.*

### Lo que ya entregaron los demás (contratos)

- **`grafo.py`** (Frederick): `Grafo` con `self.grafo`, `bfs_ruta(o, d, bloqueadas=())`, `dfs`,
  `alcanzables`, `componentes`, `hay_ruta`, `vecinos`, más `grafo_desde_mazmorra(mazmorra, atajos=2, semilla=None)`
  (con `.atajos`). `MapaCampus(Grafo)` mantiene `bfs(o, d, bloqueadas=())` y `posiciones`.
- **`misiones.py`** (Juan Diego): `crear_arbol_misiones_juego()` (raíz con `es_raiz`), `Mision.padre`,
  `desbloqueada()`, `recompensa`, `efecto`, `todas_las_misiones(raiz)` (preorden, 13), `buscar_por_sala`,
  `disponibles`, `completar_por_sala`, `lineas_preorden`, `por_niveles`, `recompensa_rama`, `texto_arbol`.
  `crear_mision_principal()` sigue devolviendo la versión plana; **yo hago el cambio**.
- **`estado_mundo.py`** (Ricardo): secciones `luces`, `puertas` (claves de tupla ordenada con `clave_puerta`),
  `misiones` y `alertas`; `consultar`, `actualizar`, `insertar`, `eliminar`, `aplicar_efecto -> cambios`,
  `revertir_cambios`, `puertas_cerradas`, `salas_iluminadas`, `misiones_con_estado` y `resumen`.
  `avanzar_tiempo` cierra `PUERTA_LOBBY` al iniciar el toque de queda y devuelve las alertas vencidas.

### Dónde se usa hoy la lista plana de misiones (hay que migrar todo)

- `main.py`: `self.mision = crear_mision_principal()` y `self.mision_libro, self.mision_lab, self.mision_profesor = self.mision.hijas[:3]` (~línea 560),
  y `self.mision.hijas` en ~752 (deshacer `usar`), ~837, ~1360, ~1419 (interactuar con una estación), ~1527 y ~1639 (puntaje).
- `hud_campus.py`: líneas ~23, 24, 52, 53, 108, 119–121, 137 y 141.
- `habilidades.py`: línea 28.
- Pruebas: `tests/test_campus.py:117`, `tests/test_carreras.py:40, 67 y 123+`, y las pruebas de
  `mision_lab` en `test_campus` y `test_carreras`.

---

## Qué tienes que construir

### Archivos que puedes tocar
`main.py` · `habilidades.py` · `hud_campus.py` (**solo** el cambio mecánico de `p.mision.hijas` → `p.encargos`;
el rediseño de `dibujar_diario` es de Nathaly) · `tests/test_campus.py` · `tests/test_carreras.py` ·
`tests/test_checkpoint3.py` (nuevo).

### Paso 1 · Cambiar al árbol de misiones
- `self.mision = crear_arbol_misiones_juego()` y `self.encargos = todas_las_misiones(self.mision)`.
- `self.mision_libro/lab/profesor = buscar_por_sala(self.mision, "biblioteca"/"lab_siemens"/"sala_reuniones")`.
- Cambiar todas las `self.mision.hijas` / `p.mision.hijas` por `self.encargos` / `p.encargos`.
- En `interactuar` con una estación (~1419): si `not mision.desbloqueada()`, mostrar el toast
  `"Bloqueada: primero completa «{mision.padre.titulo}»."` y no avanzar.
- Ajustar las pruebas: iterar `p.encargos` (preorden = respeta dependencias), cambiar `len(p.mision.hijas) == 13`
  por `len(p.encargos) == 13` y, en las pruebas de `mision_lab`, completar antes `biblioteca` y `r101`.
- Commit: `Integra el árbol de misiones con bloqueo por dependencias`

### Paso 2 · Árbol → diccionario (y deshacer)
- Al crear la partida, `insertar(estado, "misiones", m.ubicacion, "disponible" o "bloqueada")` para cada encargo.
- Cuando una misión se completa: `cambios = aplicar_efecto(self.estado_mundo, mision.efecto)`, actualizar
  `misiones[sala] = "completada"` y las hijas recién desbloqueadas a `"disponible"` (también como cambios),
  y guardar `cambios` en la acción `usar` del historial (`self._registrar(..., cambios=cambios)`).
- Al deshacer esa acción (~752): `revertir_cambios(self.estado_mundo, accion.get("cambios", []))`.
  La hora no se revierte. Esta es la decisión de Ricardo: confirmala con él.
- Toast cuando el efecto se nota: "Se abrió la salida de la terraza" o "La biblioteca apagó sus luces".
- Commit: `Conecta los efectos de las misiones con el estado del mundo y el deshacer`

### Paso 3 · Diccionario → grafo → partida
- **Ruta del jugador:** cada cierto tiempo, BFS desde el nodo visible más cercano al jugador hasta el nodo
  más cercano al `retorno` de `PUERTAS[sala]` del siguiente encargo disponible, con
  `bloqueadas=puertas_cerradas(self.estado_mundo)`. Mostrar en el HUD o el minimapa "Ruta: N tramos" o "Sin ruta".
- **Salidas:** las `SALIDAS` de `mapa_nivel1.py` (`lobby_sur` y `terraza_norte`) solo funcionan si su puerta
  está abierta en el diccionario. Si el jugador intenta salir por una cerrada, mostrar un mensaje claro, sin cerrar el juego.
- **Toque de queda:** cuando `avanzar_tiempo` cierra el lobby, avisar "El lobby cerró: sal por la terraza"
  y recalcular la ruta. Si la terraza también está cerrada (no completó *Cierre de caja*), avisar "No hay salida abierta".
- **Vigilante:** puede seguir ignorando las puertas (tiene llaves). Documenta esa decisión.
- **Alertas:** cuando un evento de cámara active la alerta, `insertar(estado, "alertas", sala, minutos)`;
  `avanzar_tiempo` elimina las vencidas.
- Commit: `El jugador ve su ruta al encargo y las puertas cerradas cambian la salida`

### Paso 4 · La Torre con el grafo genérico
- `self.grafo_torre = grafo_desde_mazmorra(self.torre, atajos=2, semilla=semilla)`.
- Moverse en la Torre permite usar los atajos: validar el destino con `self.grafo_torre.vecinos(actual)`
  en vez de solo `estan_conectadas`, sin romper `tests/test_checkpoint2.py`.
- Nueva opción en `OPCIONES_TORRE`: **"Ruta a una sala"**. Se pide el nombre (`buscar_sala`), se calcula
  `bfs_ruta` y se muestran los pasos. Si la sala no existe o no hay ruta, se muestra un mensaje.
- Commit: `La Torre usa el grafo genérico con atajos y muestra rutas con BFS`

### Paso 5 · Puntaje y resumen con los recorridos
- El puntaje final suma `recompensa_rama(self.mision)` (postorden).
- En el resumen de fin de partida: la etapa alcanzada (`por_niveles`) y `resumen(self.estado_mundo)`.
- Commit: `El puntaje final suma las recompensas del árbol de misiones`

### Paso 6 · Casos límite + `tests/test_checkpoint3.py`
Pruebas de integración (con `Partida(crear_mapa_universidad(), {}, semilla=3)`, igual que en `test_checkpoint2.py`):
1. Al inicio solo `biblioteca` está disponible, y una estación de `lab_siemens` no avanza (toast de bloqueo).
2. Completar `cafeteria` abre la terraza en el diccionario y el BFS con `puertas_cerradas` ya llega a `terraza_n`.
3. Deshacer ese `usar` vuelve a cerrar la terraza.
4. Avanzar hasta el toque de queda cierra el lobby y la ruta a `lobby` da `None` → mensaje "Sin ruta", sin excepción.
5. En el menú de la Torre, la opción "Ruta a una sala" con una sala inexistente o vacía muestra un mensaje.
6. `leer_numero` con `"abc"`, `"0"`, `"-3"` y `"99"` en el menú nuevo → mensaje, nunca excepción.
7. Completar la misma misión dos veces no duplica la recompensa.
8. El CP2 completo sigue en verde (pila, colas, Torre).
- Commit: `Agrega pruebas de integración del Checkpoint 3`

### Paso 7 · Entrega (viernes 20:00–22:00)
```bash
git pull origin main
python -m unittest discover -s tests
# Clon limpio, como lo va a hacer el docente:
cd %TEMP% && git clone git@github.com:SantiMerino/9PM.git 9pm-limpio && cd 9pm-limpio
python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt && python main.py
git shortlog -sn          # los 5 integrantes con commits propios
git tag checkpoint-3 && git push origin checkpoint-3
```
Subir el link del repo en Canvas antes de las 23:30 y revisar que el docente tenga acceso.

---

## Resultado esperado

1. **Juego:** se arranca con `python main.py`. Al inicio solo está disponible la biblioteca; al completarla se desbloquean
   3 encargos y la bitácora lo muestra. *Cierre de caja* abre la terraza. A las 21:00 el lobby cierra
   y el jugador ve que su ruta cambia. Deshacer revierte los efectos en el mundo.
2. **Torre:** se mueve también por los atajos y la opción "Ruta a una sala" responde con BFS o con un mensaje claro.
3. **Pruebas:** `OK` con todas: las 77 originales (ajustadas) + las de Frederick, Juan Diego y Ricardo + 8 o más de integración.
4. **Robustez:** ningún menú se cierra con texto, 0, negativos o fuera de rango, y ninguna sala, misión o ruta inexistente provoca un error.
5. **Historial:** 6 o más commits míos, uno por paso, con el juego funcionando después de cada uno.
6. **Tag:** `checkpoint-3` en GitHub apuntando a la versión final. Link entregado en Canvas.
7. **Para el README** (mándaselo a Nathaly): la lista de cómo cada estructura afecta a las otras en la partida
   y las decisiones (el vigilante ignora puertas; la hora no se deshace).

## Lo que NO debes hacer
- No reescribas `grafo.py`, `misiones.py` ni `estado_mundo.py`. Si falta algo, pídeselo a su dueño para que el commit sea de él.
- No rediseñes `dibujar_diario` (es de Nathaly); solo el cambio mecánico de nombres.
- No hagas commits a nombre de otros ni subas el trabajo de otro como tuyo.
