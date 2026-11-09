"""9PM · Exposición de árboles: árbol de misiones y árbol de decisión.

Se ejecuta solo, sin internet y sin librerías externas:

    python arboles.py

Contenido
---------
1. Árbol de misiones del campus (árbol general, un solo padre por misión).
   Una misión solo se puede completar cuando su misión padre ya está
   completada. Es la base del árbol de misiones del Checkpoint 3.
2. Árbol de decisión del vigilante de la Torre de Laboratorios (árbol
   binario: cada nodo interno es una pregunta de sí/no y cada hoja es una
   decisión). Reproduce lo que hace el vigilante en `main.py`.

Convención de altura (libro de Weiss): una hoja tiene altura 0 y la altura
del árbol es la cantidad de aristas del camino más largo de la raíz a una
hoja. Por eso un árbol con 4 niveles tiene altura 3 (niveles = altura + 1).

Tabla de complejidades (n = cantidad de nodos, h = altura)
---------------------------------------------------------
| Función                   | Big O | Por qué                                              |
|---------------------------|-------|------------------------------------------------------|
| agregar_hijo              | O(1)  | Solo agrega al final de la lista de hijos.           |
| recorrido_preorden        | O(n)  | Visita cada nodo exactamente una vez.                |
| recorrido_postorden       | O(n)  | Visita cada nodo exactamente una vez.                |
| altura                    | O(n)  | Necesita la altura de todos los subárboles.          |
| contar_hojas              | O(n)  | Revisa todos los nodos para saber cuáles son hojas.  |
| buscar                    | O(n)  | En el peor caso la misión está al final o no existe. |
| misiones_disponibles      | O(n)  | En el peor caso (todo completado) baja por todo.     |
| completar_mision          | O(n)  | Domina la búsqueda; marcar y revisar el padre es O(1).|
| decidir                   | O(h)  | Baja por UN solo camino: una pregunta por nivel.     |
| preorden/inorden/postorden| O(n)  | (árbol de decisión) visitan cada nodo una vez.       |

Árbol degenerado: si las preguntas del vigilante se encadenaran en una sola
fila (cada "no" lleva a la siguiente pregunta, como una cadena de if/elif),
h crece hasta ser igual al número de preguntas, y decidir pasa de O(log n)
(árbol balanceado) a O(n). Ver `arbol_decision_degenerado()` en la demo.
"""

import sys


# ---------------------------------------------------------------------------
# 1. Árbol de misiones
# ---------------------------------------------------------------------------

class Nodo:
    """Una misión del campus: nombre, sala, hijos y si ya está completada."""

    def __init__(self, nombre, sala=""):
        self.nombre = nombre
        self.sala = sala
        self.hijos = []
        self.completada = False
        self.padre = None  # Un solo padre: así sigue siendo árbol y no grafo.

    def __repr__(self):
        return f"Nodo({self.nombre!r})"


def agregar_hijo(padre, hijo):
    """Cuelga `hijo` debajo de `padre`. O(1)."""
    hijo.padre = padre
    padre.hijos.append(hijo)
    return hijo


def recorrido_preorden(nodo, nivel=0, lineas=None):
    """Preorden: primero el nodo, luego sus hijos de izquierda a derecha.

    Devuelve las líneas con sangría según el nivel. Es el mismo orden en que
    DFS descubre los nodos si se empieza en la raíz (Semana 13). O(n).
    """
    if lineas is None:
        lineas = []
    marca = "[x]" if nodo.completada else "[ ]"
    sala = f"  ({nodo.sala})" if nodo.sala else ""
    lineas.append(f"{'    ' * nivel}{marca} {nodo.nombre}{sala}")
    for hijo in nodo.hijos:
        recorrido_preorden(hijo, nivel + 1, lineas)
    return lineas


def recorrido_postorden(nodo, visitados=None):
    """Postorden: primero todos los hijos, al final el nodo. O(n)."""
    if visitados is None:
        visitados = []
    for hijo in nodo.hijos:
        recorrido_postorden(hijo, visitados)
    visitados.append(nodo.nombre)
    return visitados


def altura(nodo):
    """Aristas del camino más largo hasta una hoja. Una hoja mide 0. O(n)."""
    if not nodo.hijos:
        return 0
    return 1 + max(altura(hijo) for hijo in nodo.hijos)


def contar_hojas(nodo):
    """Cantidad de misiones sin hijos (las últimas de cada rama). O(n)."""
    if not nodo.hijos:
        return 1
    return sum(contar_hojas(hijo) for hijo in nodo.hijos)


def hojas(nodo):
    """Nombres de las hojas, de izquierda a derecha. O(n)."""
    if not nodo.hijos:
        return [nodo.nombre]
    resultado = []
    for hijo in nodo.hijos:
        resultado += hojas(hijo)
    return resultado


def contar_nodos(nodo):
    """Total de misiones del árbol: 1 + lo de cada subárbol. O(n)."""
    return 1 + sum(contar_nodos(hijo) for hijo in nodo.hijos)


def buscar(nodo, nombre):
    """Busca una misión por nombre (recorrido en preorden). O(n)."""
    if nodo.nombre == nombre:
        return nodo
    for hijo in nodo.hijos:
        encontrado = buscar(hijo, nombre)
        if encontrado is not None:
            return encontrado
    return None


def misiones_disponibles(nodo):
    """Misiones sin completar cuyo padre sí está completado (o la raíz).

    Si una misión no está completada, todo lo que cuelga de ella sigue
    bloqueado, así que no hace falta bajar por esa rama. O(n).
    """
    if not nodo.completada:
        return [nodo]
    disponibles = []
    for hijo in nodo.hijos:
        disponibles += misiones_disponibles(hijo)
    return disponibles


def completar_mision(raiz, nombre):
    """Completa la misión `nombre` si está desbloqueada.

    Devuelve (True, misiones_que_se_desbloquean) si se pudo, o
    (False, mensaje_de_error) si no existe, ya estaba hecha o está bloqueada.
    O(n) por la búsqueda.
    """
    mision = buscar(raiz, nombre)
    if mision is None:
        return False, f"No existe la misión «{nombre}»."
    if mision.completada:
        return False, f"«{nombre}» ya estaba completada."
    if mision.padre is not None and not mision.padre.completada:
        return False, (f"«{nombre}» está bloqueada: primero completa "
                       f"«{mision.padre.nombre}».")
    mision.completada = True
    return True, list(mision.hijos)


def crear_arbol_misiones():
    """Las misiones de 9PM ordenadas por dependencias (14 misiones, 4 niveles).

    La lógica de cada dependencia sale del juego: el libro de la biblioteca
    abre el campus, la USB de R101 se usa en el Lab Siemens, el profesor de la
    sala de reuniones firma antes de las entregas de aulas, y la cafetería se
    cierra antes de ordenar la bodega.
    """
    raiz = Nodo("Préstamo de medianoche", "Biblioteca")

    firma = agregar_hijo(raiz, Nodo("Una última firma", "Sala de reuniones"))
    agregar_hijo(firma, Nodo("Cálculo pendiente", "R102"))
    exposicion = agregar_hijo(firma, Nodo("Última exposición", "R105"))
    agregar_hijo(exposicion, Nodo("Bitácora de física", "R104"))

    entrega = agregar_hijo(raiz, Nodo("Entrega digital", "R101"))
    marcha = agregar_hijo(entrega, Nodo("Puesta en marcha", "Lab Siemens"))
    agregar_hijo(marcha, Nodo("Prototipo listo", "Lab Kite"))
    redes = agregar_hijo(entrega, Nodo("Redes conectadas", "R103"))
    agregar_hijo(redes, Nodo("Respaldo completo", "Lab Click"))

    caja = agregar_hijo(raiz, Nodo("Cierre de caja", "Cafetería"))
    bodega = agregar_hijo(caja, Nodo("Todo en su lugar", "Bodega"))
    agregar_hijo(bodega, Nodo("Señal estable", "Lab Spark"))
    agregar_hijo(caja, Nodo("Salida por la terraza", "Terraza"))

    return raiz


# ---------------------------------------------------------------------------
# 2. Árbol de decisión del vigilante
# ---------------------------------------------------------------------------

class NodoDecision:
    """Nodo interno: pregunta + hijo `si` + hijo `no`. Hoja: solo `decision`."""

    def __init__(self, pregunta=None, condicion=None, si=None, no=None, decision=None):
        self.pregunta = pregunta      # Texto que se muestra en la exposición.
        self.condicion = condicion    # Función que responde la pregunta con la situación.
        self.si = si
        self.no = no
        self.decision = decision

    def es_hoja(self):
        return self.decision is not None

    def etiqueta(self):
        return self.decision if self.es_hoja() else self.pregunta


def hoja(decision):
    return NodoDecision(decision=decision)


def pregunta(texto, condicion, si, no):
    return NodoDecision(pregunta=texto, condicion=condicion, si=si, no=no)


def decidir(nodo, situacion, camino=None):
    """Baja desde la raíz respondiendo una pregunta por nivel. O(h).

    `situacion` es un diccionario, por ejemplo
    {"reportando": False, "jugador_cerca": True, "toque_queda": False,
     "alerta_robot": False, "minutos_para_toque": 20}.
    Si se pasa una lista en `camino`, ahí quedan las preguntas respondidas.
    """
    if nodo.es_hoja():
        return nodo.decision
    respuesta = bool(nodo.condicion(situacion))
    if camino is not None:
        camino.append(f"{nodo.pregunta} -> {'sí' if respuesta else 'no'}")
    return decidir(nodo.si if respuesta else nodo.no, situacion, camino)


def crear_arbol_decision():
    """Cómo decide su turno el vigilante de la Torre (5 preguntas, 6 decisiones).

                         ¿Está llenando un reporte?
                         /sí                    \\no
           Seguir con el reporte        ¿El estudiante está en su sala?
                                        /sí                         \\no
                         ¿Ya es el toque de queda?          ¿El robot dio la alerta?
                          /sí            \\no                 /sí               \\no
               Expulsar al        Sermonear      Seguir el rastro   ¿Faltan 5 min o menos?
               estudiante         3 minutos      del estudiante       /sí            \\no
                                                               Revisar salas    Patrullar una
                                                               profundas        sala al azar
    """
    return pregunta(
        "¿Está llenando un reporte?", lambda s: s["reportando"],
        si=hoja("Seguir con el reporte"),
        no=pregunta(
            "¿El estudiante está en su sala?", lambda s: s["jugador_cerca"],
            si=pregunta(
                "¿Ya es el toque de queda?", lambda s: s["toque_queda"],
                si=hoja("Expulsar al estudiante"),
                no=hoja("Sermonear 3 minutos"),
            ),
            no=pregunta(
                "¿El robot dio la alerta?", lambda s: s["alerta_robot"],
                si=hoja("Seguir el rastro del estudiante"),
                no=pregunta(
                    "¿Faltan 5 minutos o menos?", lambda s: s["minutos_para_toque"] <= 5,
                    si=hoja("Revisar las salas profundas"),
                    no=hoja("Patrullar una sala al azar"),
                ),
            ),
        ),
    )


def arbol_decision_degenerado():
    """Las mismas 5 preguntas en una sola fila (como una cadena de if/elif).

    Cada "sí" termina en una hoja y cada "no" baja a la siguiente pregunta,
    así que la altura es igual al número de preguntas.
    """
    return pregunta(
        "¿Está llenando un reporte?", lambda s: s["reportando"],
        si=hoja("Seguir con el reporte"),
        no=pregunta(
            "¿Ya es el toque de queda y está en su sala?",
            lambda s: s["toque_queda"] and s["jugador_cerca"],
            si=hoja("Expulsar al estudiante"),
            no=pregunta(
                "¿El estudiante está en su sala?", lambda s: s["jugador_cerca"],
                si=hoja("Sermonear 3 minutos"),
                no=pregunta(
                    "¿El robot dio la alerta?", lambda s: s["alerta_robot"],
                    si=hoja("Seguir el rastro del estudiante"),
                    no=pregunta(
                        "¿Faltan 5 minutos o menos?", lambda s: s["minutos_para_toque"] <= 5,
                        si=hoja("Revisar las salas profundas"),
                        no=hoja("Patrullar una sala al azar"),
                    ),
                ),
            ),
        ),
    )


def altura_decision(nodo):
    """Máximo de preguntas que hace el vigilante antes de decidir. O(n)."""
    if nodo.es_hoja():
        return 0
    return 1 + max(altura_decision(nodo.si), altura_decision(nodo.no))


def contar_preguntas(nodo):
    return 0 if nodo.es_hoja() else 1 + contar_preguntas(nodo.si) + contar_preguntas(nodo.no)


def contar_decisiones(nodo):
    return 1 if nodo.es_hoja() else contar_decisiones(nodo.si) + contar_decisiones(nodo.no)


def preorden_decision(nodo, visitados=None):
    """Nodo, subárbol sí, subárbol no. O(n)."""
    if visitados is None:
        visitados = []
    visitados.append(nodo.etiqueta())
    if not nodo.es_hoja():
        preorden_decision(nodo.si, visitados)
        preorden_decision(nodo.no, visitados)
    return visitados


def inorden_decision(nodo, visitados=None):
    """Subárbol sí, nodo, subárbol no. Solo tiene sentido en árboles binarios. O(n)."""
    if visitados is None:
        visitados = []
    if not nodo.es_hoja():
        inorden_decision(nodo.si, visitados)
    visitados.append(nodo.etiqueta())
    if not nodo.es_hoja():
        inorden_decision(nodo.no, visitados)
    return visitados


def postorden_decision(nodo, visitados=None):
    """Subárbol sí, subárbol no, nodo. O(n)."""
    if visitados is None:
        visitados = []
    if not nodo.es_hoja():
        postorden_decision(nodo.si, visitados)
        postorden_decision(nodo.no, visitados)
    visitados.append(nodo.etiqueta())
    return visitados


SITUACIONES = [
    ("El vigilante sigue escribiendo tras sermonearte",
     {"reportando": True, "jugador_cerca": True, "toque_queda": False,
      "alerta_robot": False, "minutos_para_toque": 30}),
    ("Te encuentra a las 20:40",
     {"reportando": False, "jugador_cerca": True, "toque_queda": False,
      "alerta_robot": False, "minutos_para_toque": 20}),
    ("Te encuentra a las 21:02",
     {"reportando": False, "jugador_cerca": True, "toque_queda": True,
      "alerta_robot": False, "minutos_para_toque": 0}),
    ("El robot te detectó y avisó por radio",
     {"reportando": False, "jugador_cerca": False, "toque_queda": False,
      "alerta_robot": True, "minutos_para_toque": 15}),
    ("Faltan 3 minutos y no te ha visto",
     {"reportando": False, "jugador_cerca": False, "toque_queda": False,
      "alerta_robot": False, "minutos_para_toque": 3}),
    ("Noche tranquila a las 20:20",
     {"reportando": False, "jugador_cerca": False, "toque_queda": False,
      "alerta_robot": False, "minutos_para_toque": 40}),
]


# ---------------------------------------------------------------------------
# Demo en vivo
# ---------------------------------------------------------------------------

def titulo(texto):
    print()
    print("=" * 64)
    print(texto)
    print("=" * 64)


def mostrar_disponibles(raiz):
    nombres = [m.nombre for m in misiones_disponibles(raiz)]
    print("Disponibles ahora:", ", ".join(nombres) if nombres else "ninguna")


def intentar(raiz, nombre):
    print(f"\n> completar_mision(«{nombre}»)")
    ok, resultado = completar_mision(raiz, nombre)
    if ok:
        nuevas = ", ".join(m.nombre for m in resultado) or "nada (es una hoja)"
        print(f"  Completada. Se desbloquea: {nuevas}")
    else:
        print(f"  ERROR: {resultado}")
    mostrar_disponibles(raiz)


def main():
    # Acentos y ñ también en la consola de Windows.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    misiones = crear_arbol_misiones()

    titulo("1. ÁRBOL DE MISIONES DE 9PM (recorrido en preorden)")
    print("\n".join(recorrido_preorden(misiones)))
    print(f"\nRaíz: {misiones.nombre}")
    print(f"Misiones (n): {contar_nodos(misiones)}")
    print(f"Altura: {altura(misiones)}  ->  {altura(misiones) + 1} niveles")
    print(f"Hojas ({contar_hojas(misiones)}): {', '.join(hojas(misiones))}")
    print(f"Postorden: {' -> '.join(recorrido_postorden(misiones))}")

    titulo("2. DEPENDENCIAS: completar misiones en vivo")
    mostrar_disponibles(misiones)
    intentar(misiones, "Puesta en marcha")        # bloqueada: falta R101
    intentar(misiones, "Préstamo de medianoche")  # raíz
    intentar(misiones, "Entrega digital")
    intentar(misiones, "Puesta en marcha")        # ahora sí
    print()
    print("\n".join(recorrido_preorden(misiones)))

    titulo("3. ÁRBOL DE DECISIÓN DEL VIGILANTE DE LA TORRE")
    vigilante = crear_arbol_decision()
    print(f"Preguntas: {contar_preguntas(vigilante)}   Decisiones: {contar_decisiones(vigilante)}")
    print(f"Altura (máximo de preguntas para decidir): {altura_decision(vigilante)}")
    for descripcion, situacion in SITUACIONES:
        camino = []
        decision = decidir(vigilante, situacion, camino)
        print(f"\n* {descripcion}")
        for paso in camino:
            print(f"    {paso}")
        print(f"    => {decision}  ({len(camino)} preguntas)")

    titulo("4. RECORRIDOS DEL ÁRBOL DE DECISIÓN (árbol binario)")
    print("Preorden :", " | ".join(preorden_decision(vigilante)))
    print("Inorden  :", " | ".join(inorden_decision(vigilante)))
    print("Postorden:", " | ".join(postorden_decision(vigilante)))

    titulo("5. COMPLEJIDAD Y ÁRBOL DEGENERADO")
    degenerado = arbol_decision_degenerado()
    peor = SITUACIONES[-1][1]
    camino_bal, camino_deg = [], []
    decidir(vigilante, peor, camino_bal)
    decidir(degenerado, peor, camino_deg)
    print(f"Recorrido completo de misiones: visita {contar_nodos(misiones)} nodos -> O(n)")
    print(f"Árbol de decisión actual: altura {altura_decision(vigilante)}, "
          f"'{SITUACIONES[-1][0]}' hace {len(camino_bal)} preguntas -> O(h)")
    print(f"Árbol degenerado (una sola fila): altura {altura_decision(degenerado)}, "
          f"la misma situación hace {len(camino_deg)} preguntas -> h = n preguntas, O(n)")


if __name__ == "__main__":
    main()
