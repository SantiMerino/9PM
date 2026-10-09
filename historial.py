"""Semana 5 / Guía 5: historial de acciones con una PILA (LIFO).

El historial es una lista de Python usada con disciplina de pila: solo se
toca el final. Cada acción importante del jugador se apila con `append` y
deshacer saca la más reciente con `pop`, que es justo la que hay que revertir
primero (la última que entró es la primera que sale).

Cada acción es un diccionario:

    {"tipo": "mover", "texto": "Pasillo → R101", "hora": "20:17", ...}

Los tipos que registra 9PM son:

    mover    cambiar de sala (puertas del campus, gradas y salas de la Torre)
    recoger  meter un objeto a la mochila
    usar     consumir un objeto en una estación (libro, USB)
    soltar   dejar un objeto en el suelo

Los datos extra de cada acción (sala de origen, objeto, posición...) son los
que `main.py` necesita para revertirla de verdad.
"""

TIPOS_ACCION = ("mover", "recoger", "usar", "soltar")

ETIQUETAS = {
    "mover": "Mover",
    "recoger": "Recoger",
    "usar": "Usar",
    "soltar": "Soltar",
}


def crear_accion(tipo, texto, hora="", **datos):
    """Arma el diccionario de una acción. `texto` es lo que ve el jugador y
    `datos` guarda lo necesario para deshacerla (origen, objeto, etc.)."""
    accion = {"tipo": tipo, "texto": texto, "hora": hora}
    accion.update(datos)
    return accion


def apilar_accion(historial, accion):
    """Registra una acción nueva en la cima de la pila (append, O(1))."""
    historial.append(accion)
    return accion


def deshacer_ultima_accion(historial):
    """Quita y devuelve la acción más reciente (pop, O(1)).
    Devuelve None si el historial está vacío, en vez de lanzar un error."""
    if historial_vacio(historial):
        return None
    return historial.pop()


def consultar_ultima_accion(historial):
    """Devuelve la acción de la cima SIN sacarla (peek). None si está vacío.
    Se valida el tamaño antes de usar historial[-1]: en una lista vacía
    daría IndexError."""
    if historial_vacio(historial):
        return None
    return historial[-1]


def historial_vacio(historial):
    """True si no hay ninguna acción registrada."""
    return len(historial) == 0


def describir_accion(accion):
    """Texto de una línea para mostrar una acción en pantalla."""
    etiqueta = ETIQUETAS.get(accion["tipo"], accion["tipo"].capitalize())
    hora = f"[{accion['hora']}] " if accion.get("hora") else ""
    return f"{hora}{etiqueta}: {accion['texto']}"


def mostrar_historial(historial):
    """Devuelve las líneas del historial completo, de la acción MÁS RECIENTE a
    la MÁS ANTIGUA (el orden en que saldrían al deshacer). No modifica la pila."""
    if historial_vacio(historial):
        return ["(historial vacío: todavía no has hecho nada esta noche)"]
    return [f"{i}. {describir_accion(a)}"
            for i, a in enumerate(invertir_historial(historial), start=1)]


# ---------------------------------------------------------------------------
# Funciones de la Guía 5 adaptadas a 9PM
# ---------------------------------------------------------------------------
def deshacer_multiples(historial, cantidad):
    """Deshace hasta `cantidad` acciones seguidas y las devuelve en el orden en
    que salieron (la más reciente primero). Si la pila se vacía antes, se
    detiene sin error. Lo usa la opción "Deshacer varias" de la Torre."""
    deshechas = []
    for _ in range(max(0, cantidad)):
        if historial_vacio(historial):
            break
        deshechas.append(historial.pop())
    return deshechas


def contar_acciones_de_tipo(historial, tipo):
    """Cuenta cuántas acciones de un tipo hay en el historial, sin modificarlo.
    Se usa en el resumen del panel de historial (movimientos, objetos...)."""
    contador = 0
    for accion in historial:
        if accion["tipo"] == tipo:
            contador += 1
    return contador


def invertir_historial(historial):
    """Devuelve una lista NUEVA con las acciones de la más reciente a la más
    antigua. Usa una pila auxiliar: se van sacando (pop) de una copia, así que
    salen en orden inverso y el historial original queda intacto."""
    copia = list(historial)
    invertido = []
    while copia:
        invertido.append(copia.pop())
    return invertido


def deshacer_hasta_tipo(historial, tipo):
    """Saca acciones de la cima hasta encontrar (e incluir) la primera del
    `tipo` pedido. Devuelve la lista de acciones sacadas, la más reciente
    primero. Si no hay ninguna de ese tipo, no toca la pila y devuelve []."""
    if contar_acciones_de_tipo(historial, tipo) == 0:
        return []
    deshechas = []
    while historial:
        accion = historial.pop()
        deshechas.append(accion)
        if accion["tipo"] == tipo:
            break
    return deshechas


def resumen_por_tipo(historial):
    """Diccionario {tipo: cantidad} para los cuatro tipos de acción."""
    return {tipo: contar_acciones_de_tipo(historial, tipo) for tipo in TIPOS_ACCION}
