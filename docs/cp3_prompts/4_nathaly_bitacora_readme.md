# Prompt para tu AI · Nathaly Mena · Bitácora en árbol + README + evidencia

> Copia todo este archivo y pégalo en tu AI (Claude, ChatGPT, Cursor…) con el repo abierto.
> La AI te ayuda, pero **los commits los haces tú desde tu cuenta** y tienes que poder
> explicar cada línea si el docente te pregunta.

---

## Contexto para la AI

Eres mi asistente de programación en un proyecto universitario de **Estructura de Datos y
Algoritmos** (Python 3.12 + pygame 2.6.1). El repo es `github.com/SantiMerino/9PM`: un RPG de
sigilo en el que un estudiante tiene que completar encargos en el campus antes del toque de
queda (21:00) sin que lo atrape el vigilante. Se ejecuta con `python main.py` y las pruebas
corren con `python -m unittest discover -s tests`.

Somos 5 integrantes y cada uno tiene **su propia parte del Checkpoint 3** (grafos, árboles,
diccionarios). La mía es **la documentación (10 pts) y la bitácora en pantalla** que muestra el
árbol de misiones. La rúbrica pide, para el README:

> *Explica cómo ejecutar el juego y, para cada estructura: qué parte del juego resuelve, por qué
> esa estructura es la adecuada, y la complejidad de sus operaciones principales (BFS y DFS en
> O(V + E), recorridos de un árbol en O(n), acceso a un diccionario en O(1) en promedio contra
> una búsqueda lineal en una lista en O(n)). Incluye la lista de funcionalidades que el juego tiene
> hasta ahora, el dibujo de su grafo y de su árbol, la decisión sobre el estado al deshacer, evidencia
> de ejecución (capturas o texto de consola) y qué aportó cada integrante.*

### Lo que hacen los demás (de ahí sale lo que documento)

| Integrante | Parte | Archivo |
|---|---|---|
| Frederick | Clase `Grafo` genérica: BFS con puertas bloqueadas, DFS, alcanzables, zonas aisladas. `MapaCampus` hereda de ella y la Torre se convierte en grafo con atajos | `grafo.py`, `mapa.py` |
| Juan Diego | Misiones como árbol con dependencias. Preorden (bitácora con sangría), por niveles (etapas) y postorden (recompensas) | `misiones.py` |
| Ricardo | Diccionario del estado del mundo: luces, puertas con tuplas como clave, misiones y alertas. `.get`, insertar, eliminar, filtros y deshacer | `estado_mundo.py` |
| Santiago | Integración en `main.py`, casos límite, pruebas de integración y tag | `main.py`, `tests/test_checkpoint3.py` |
| Nathaly | Bitácora en árbol, README y evidencia | `hud_campus.py`, `README.md`, `docs/` |

**El flujo que une todo** (es lo más importante del README):
completar una misión en el árbol → su `efecto` cambia el diccionario (abre o cierra puertas, apaga
luces) → `puertas_cerradas(estado)` se le pasa al BFS del grafo como `bloqueadas` → el jugador y el
vigilante cambian de ruta. A las 21:00 el toque de queda cierra el lobby y el BFS busca la salida por la
terraza, que solo está abierta si ya completaste *Cierre de caja*; si no, el juego avisa que no hay ruta.

### Estado actual del repo (lo relevante para mí)

- `README.md` (~560 líneas) tiene: Equipo, Cómo correrlo, Controles, Estructura del proyecto,
  la sección completa del **Checkpoint 2** (con "Cómo trabajan juntas", cada estructura, decisión de
  deshacer, casos límite, evidencia, pruebas y aporte de cada integrante) y Campus y arte.
  **Usa la sección del CP2 como plantilla de estilo para la del CP3.**
- `hud_campus.py → dibujar_diario(s, p)` dibuja la "BITÁCORA DE LA NOCHE" como una **cuadrícula plana**
  de 13 tarjetas (`for i, m in enumerate(p.mision.hijas)`).
- `capturar_juego.py` genera capturas reales sin abrir ventana (`docs/capturas/*.png`) y ya
  importa `dibujar_diario`.
- `arboles.py` y `docs/9PM · Árboles de misiones y de decisión.pptx` tienen la exposición de árboles.

### Contrato que uso (lo entregan Juan Diego y Santiago)

- `lineas_preorden(raiz) -> list[(nivel, Mision)]` y `por_niveles(raiz) -> list[list[Mision]]`, de `misiones.py`.
- `Mision`: `titulo`, `ubicacion`, `completada`, `desbloqueada()`, `recompensa`, `paso`, `pasos`.
- Después de la integración de Santiago, `p.mision` es la **raíz del árbol** y `p.encargos` es la lista plana de los 13.

---

## Qué tienes que construir

### Archivos que puedes tocar
`hud_campus.py` (**solo** `dibujar_diario` y funciones auxiliares nuevas) · `README.md` · `docs/` · `capturar_juego.py` (solo para agregar capturas).

### Orden (importante, porque dependes de otros)
1. **Desde hoy:** el esqueleto del README del CP3, los diagramas y la lista de funcionalidades.
   No depende de nadie.
2. **Después de que Santiago fusione la integración del árbol (viernes ~14:00):** `dibujar_diario`.
3. **Viernes 18:00–20:00:** evidencia (capturas + consola) y la tabla de aportes con los datos reales.

### 1. `dibujar_diario` muestra el árbol con sangría

- Recorre `lineas_preorden(p.mision)` y dibuja una fila por misión con sangría `nivel * 22 px`
  y conectores (`├─` y `└─`, o líneas con `pygame.draw.line`).
- Estado visual: **completada** con el check verde que ya existe (`dibujar_check`), **disponible**
  en crema o blanco con el objetivo actual (`m.objetivo_actual`) y **bloqueada** en gris con
  candado o el texto "bloqueada".
- Arriba se mantiene el contador `hechas/total` con la barra de progreso (usa `p.encargos`).
- Abajo, una línea "ETAPA N de 5" calculada con `por_niveles` (el primer nivel que tiene misiones sin completar)
  y la recompensa acumulada si Santiago expone `recompensa_rama`.
- Tiene que caber en 960×640: 14 filas de unos 34 px, o dos columnas si no alcanza.
- No uses `p.mision.hijas` en esta función.
- Verifícalo con `python capturar_juego.py` y revisa `docs/capturas/bitacora.png`.

### 2. README · nueva sección `## Checkpoint 3: grafo, árbol de misiones y estado del mundo`

Colócala antes de "## Checkpoint 2" (lo más nuevo primero) y agrégala a la tabla o índice si lo hay.
Debe tener **todas** estas subsecciones:

1. **Cómo ejecutar** (revisa que "Cómo correrlo" siga siendo correcto) y **funcionalidades hasta ahora**:
   una lista con viñetas que cubra el CP1 (inventario), el CP2 (pila, colas, Torre recursiva) y el CP3.
2. **Cómo trabajan juntas las estructuras**: el flujo de arriba con un diagrama ASCII y un ejemplo jugado
   paso a paso (por ejemplo: "completo Cierre de caja → la terraza se abre → a las 21:00 el lobby cierra
   → el BFS me manda por la terraza").
3. **Grafo** (`grafo.py`, `mapa.py`, Semanas 12–13):
   - Qué resuelve: la ruta del vigilante (DFS = ronda, BFS = persecución), la ruta del jugador al siguiente
     encargo, la salida cuando hay puertas cerradas, los atajos de la Torre y las zonas aisladas.
   - Por qué es la estructura adecuada: los pasillos son relaciones entre lugares y se usa lista de
     adyacencia porque cada nodo tiene pocos vecinos (con una matriz serían O(V²) de memoria).
   - Por qué es genérica: la misma clase sirve para el campus y para la Torre.
   - **Dibujo del grafo del campus** (ASCII con los 16 nodos y 17 aristas, marcando las 2 puertas) y del grafo de la Torre con sus atajos.
   - Tabla de complejidades: `agregar_arista` O(1), `vecinos` O(1), `bfs_ruta` O(V+E), `dfs` O(V+E), `alcanzables` O(V+E), `componentes` O(V+E).
4. **Árbol de misiones** (`misiones.py`, Semana 14):
   - Qué resuelve: las dependencias entre encargos; completar uno desbloquea a sus hijos.
   - Por qué un árbol: cada encargo depende de un solo anterior y no hay ciclos.
   - **Dibujo del árbol** (el de 14 nodos, pídeselo a Juan Diego o sácalo de `texto_arbol`).
   - Los recorridos y para qué los usa el juego: preorden → bitácora, por niveles → etapas,
     postorden → recompensas. Todos son O(n).
5. **Diccionario del estado del mundo** (`estado_mundo.py`, Semana 15):
   - Qué guarda: hora, luces, puertas, misiones y alertas.
   - Por qué esas claves: textos únicos y tuplas ordenadas para las puertas; nunca listas, porque no son *hashables*.
   - Operaciones (`.get`, insertar, actualizar, eliminar) y funciones propias (`puertas_cerradas`, `salas_iluminadas`, `resumen`…).
   - Complejidad: O(1) promedio contra O(n) si fuera una lista de pares.
6. **Decisión: ¿qué pasa con el estado del mundo al deshacer?** El texto lo escribe Ricardo y tú lo integras.
7. **Casos límite del CP3**: nodo, sala o misión inexistente, ruta imposible, misión bloqueada, misión repetida,
   y texto, 0, negativos o fuera de rango en los menús. Para cada uno, qué mensaje muestra el juego.
8. **Evidencia de ejecución**: 3–4 capturas nuevas en `docs/capturas/cp3_*.png` (bitácora en árbol,
   ruta alternativa con la puerta cerrada, misión bloqueada y el menú de la Torre con una opción inválida) +
   la salida de consola de las demos de Frederick, Juan Diego y Ricardo + la salida de
   `python -m unittest discover -s tests` (las últimas líneas con el total y `OK`).
9. **Aporte de cada integrante (CP3)**: una tabla como la del CP2, con qué hizo cada uno y en qué archivos,
   **verificada contra `git shortlog -sn` y `git log --author=...`**. Nada que no esté en el historial.

---

## Plan de trabajo y commits (repartidos, no todos al final)

```bash
git clone git@github.com:SantiMerino/9PM.git && cd 9PM
git config user.name "Nathaly Mena"
git config user.email "<el correo de tu cuenta de GitHub>"
python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt
git checkout -b cp3/nathaly
```

| # | Cuándo | Qué hacer | Mensaje de commit |
|---|---|---|---|
| 1 | Jueves | Esqueleto de la sección CP3, funcionalidades y "cómo trabajan juntas" | `Agrega al README la sección del Checkpoint 3 con el flujo entre estructuras` |
| 2 | Jueves / viernes temprano | Dibujos ASCII del grafo del campus, de la Torre y del árbol de misiones | `Agrega diagramas del grafo del campus y del árbol de misiones` |
| 3 | Viernes, al fusionarse lo de los demás | Secciones de grafo, árbol y diccionario con su porqué y su complejidad | `Documenta grafo, árbol y diccionario con su complejidad` |
| 4 | Viernes, tras la integración | `dibujar_diario` con el árbol con sangría (haz `git pull origin main` primero) | `La bitácora muestra el árbol de misiones con sangría y bloqueos` |
| 5 | Viernes 18:00–20:00 | Capturas `cp3_*`, consola, casos límite y decisión de deshacer | `Agrega evidencia de ejecución y casos límite del Checkpoint 3` |
| 6 | Viernes 20:00 | Tabla de aportes verificada con `git shortlog` | `Actualiza el aporte de cada integrante en el Checkpoint 3` |

Puedes abrir el PR temprano (como *draft*) y seguir subiendo commits a tu rama.
Antes de cada commit de código: `python -m unittest discover -s tests` y `python main.py` → tecla de la bitácora.

---

## Resultado esperado

1. **README:** una sección "Checkpoint 3" completa con las 9 subsecciones, diagramas que se leen bien en GitHub
   (dentro de bloques ```` ``` ````) y tablas de complejidad.
2. **Bitácora:** al abrirla en el juego se ve el árbol con sangría y los tres estados (completada, disponible
   y bloqueada), y se actualiza en cuanto completas un encargo.
3. **Capturas:** `docs/capturas/cp3_01_bitacora_arbol.png`, `cp3_02_ruta_alternativa.png`,
   `cp3_03_mision_bloqueada.png` y `cp3_04_opcion_invalida.png`, referenciadas desde el README.
4. **Pruebas:** siguen en `OK`; tu cambio en `hud_campus.py` no rompe nada.
5. **Historial:** 5–6 commits tuyos repartidos entre jueves y viernes, en `git log --author="Nathaly"`.
6. Un lector que no conoce el juego entiende, con solo leer el README, **por qué** cada estructura
   es la adecuada y no solo qué hace el código.

## Lo que NO debes hacer
- No toques `main.py`, `grafo.py`, `misiones.py` ni `estado_mundo.py`. Si encuentras un error, avísale a su dueño.
- No borres ni reescribas la sección del Checkpoint 2.
- No pongas en la tabla de aportes nada que no esté en el historial de commits.
- No hagas un solo commit gigante al final.
