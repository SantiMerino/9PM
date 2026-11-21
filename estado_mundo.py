"""Semana 15 + Checkpoint 3: diccionario con el estado global del mundo.

Todo lo que cambia durante la noche vive en un solo diccionario: la hora, el toque
de queda, las luces, las puertas, el estado de cada misión y las alertas del
vigilante. El juego pregunta muchas veces por segundo "¿está cerrada esta
puerta?"; con un dict eso es O(1) promedio, con una lista de pares sería O(n).

Claves: un texto único por sala ("biblioteca") y una TUPLA ordenada por puerta
(("terraza", "terraza_n")). Una lista no sirve de clave porque es mutable y no
es hashable.
"""

PUERTA_LOBBY = ("lobby", "lobby_frente")
PUERTA_TERRAZA = ("terraza", "terraza_n")
SECCIONES = ("luces", "puertas", "misiones", "alertas")


def clave_puerta(a, b):
    """Clave canónica de una puerta: tupla ORDENADA, así (b, a) y (a, b) son la misma. O(1)."""
    return tuple(sorted((str(a), str(b))))


def _normalizar_clave(seccion, clave):
    """En la sección de puertas acepta (a, b) en cualquier orden. O(1)."""
    if seccion == "puertas" and isinstance(clave, (tuple, list)) and len(clave) == 2:
        return clave_puerta(*clave)
    return clave


def _seccion(estado, seccion):
    """El dict de la sección o None si no existe (nunca KeyError). O(1)."""
    if not isinstance(estado, dict) or seccion not in SECCIONES:
        return None
    valor = estado.get(seccion)
    return valor if isinstance(valor, dict) else None


def crear_estado_inicial():
    return {
        "hora_actual_min": 20 * 60 + 15,   # 20:15
        "hora_toque_queda_min": 21 * 60,   # 21:00
        "toque_queda_activo": False,
        "vigilante_alerta": False,
        # clave: texto (id de sala) -> True si la luz está encendida
        "luces": {"biblioteca": True, "cafeteria": True, "lab_siemens": True, "lobby": True},
        # clave: TUPLA ordenada (puerta entre dos nodos del grafo) -> "abierta" | "cerrada"
        "puertas": {PUERTA_LOBBY: "abierta", PUERTA_TERRAZA: "cerrada"},
        # sala -> "bloqueada" | "disponible" | "completada" (la partida lo llena con insertar)
        "misiones": {},
        # sala -> minutos de alerta restantes (se inserta al activarse y se elimina al vencer)
        "alertas": {},
    }


# ----------------------------------------------------------------------
# Operaciones básicas: todas seguras, nunca KeyError
# ----------------------------------------------------------------------
def consultar(estado, seccion, clave, defecto=None):
    """Valor de estado[seccion][clave] con .get(); si la sección o la clave no
    existen devuelve `defecto`. O(1) promedio."""
    datos = _seccion(estado, seccion)
    if datos is None:
        return defecto
    try:
        return datos.get(_normalizar_clave(seccion, clave), defecto)
    except TypeError:   # clave no hasheable
        return defecto


def actualizar(estado, seccion, clave, valor):
    """Cambia el valor y devuelve el valor ANTERIOR (None si no existía). O(1)."""
    datos = _seccion(estado, seccion)
    if datos is None:
        return None
    clave = _normalizar_clave(seccion, clave)
    try:
        anterior = datos.get(clave)
        datos[clave] = valor
    except TypeError:
        return None
    return anterior


def insertar(estado, seccion, clave, valor):
    """Agrega la clave solo si no existía. False si ya estaba o la sección no existe. O(1)."""
    datos = _seccion(estado, seccion)
    if datos is None:
        return False
    clave = _normalizar_clave(seccion, clave)
    try:
        if clave in datos:
            return False
        datos[clave] = valor
    except TypeError:
        return False
    return True


def eliminar(estado, seccion, clave):
    """Borra la clave con .pop(clave, None). False si no existía. O(1)."""
    datos = _seccion(estado, seccion)
    if datos is None:
        return False
    clave = _normalizar_clave(seccion, clave)
    try:
        if clave not in datos:
            return False
        datos.pop(clave, None)
    except TypeError:
        return False
    return True


# ----------------------------------------------------------------------
# Efectos de misiones y deshacer
# ----------------------------------------------------------------------
_EFECTOS = {
    "abre": ("puertas", "abierta"),
    "cierra": ("puertas", "cerrada"),
    "apaga": ("luces", False),
    "enciende": ("luces", True),
}


def aplicar_efecto(estado, efecto):
    """Aplica el efecto de una misión al mundo y devuelve la lista de cambios
    [(seccion, clave, valor_anterior), ...] para poder deshacerlo.
    "abre"/"cierra" -> puertas[clave] = "abierta"/"cerrada"
    "apaga"/"enciende" -> luces[sala] = False/True
    Efecto None o desconocido -> [] (sin error). O(k), k = acciones del efecto."""
    if not isinstance(efecto, dict):
        return []
    cambios = []
    for accion, objetivo in efecto.items():
        if accion not in _EFECTOS:
            continue
        seccion, valor = _EFECTOS[accion]
        if seccion == "puertas":
            if not (isinstance(objetivo, (tuple, list)) and len(objetivo) == 2):
                continue
            objetivo = clave_puerta(*objetivo)
        elif not isinstance(objetivo, str):
            continue
        anterior = actualizar(estado, seccion, objetivo, valor)
        cambios.append((seccion, objetivo, anterior))
    return cambios


def revertir_cambios(estado, cambios):
    """Deshace los cambios en orden inverso. Si valor_anterior es None, la clave
    no existía antes y se elimina. O(k)."""
    for cambio in reversed(list(cambios or ())):
        try:
            seccion, clave, anterior = cambio
        except (TypeError, ValueError):
            continue
        if anterior is None:
            eliminar(estado, seccion, clave)
        else:
            actualizar(estado, seccion, clave, anterior)


# ----------------------------------------------------------------------
# Tiempo, toque de queda y alertas
# ----------------------------------------------------------------------
def avanzar_tiempo(estado, minutos):
    """Avanza el reloj. La primera vez que llega el toque de queda cierra la puerta
    del lobby. Descuenta los minutos de las alertas y elimina las que llegan a 0.
    Devuelve la lista de salas cuya alerta venció. O(a), a = alertas activas."""
    estado["hora_actual_min"] += minutos
    if estado["hora_actual_min"] >= estado["hora_toque_queda_min"] and not estado["toque_queda_activo"]:
        estado["toque_queda_activo"] = True
        actualizar(estado, "puertas", PUERTA_LOBBY, "cerrada")
    vencidas = []
    alertas = _seccion(estado, "alertas") or {}
    for sala, restantes in list(alertas.items()):
        restantes -= minutos
        if restantes <= 0:
            eliminar(estado, "alertas", sala)
            vencidas.append(sala)
        else:
            alertas[sala] = restantes
    return vencidas


def formatear_hora(minutos_desde_medianoche):
    h = (minutos_desde_medianoche // 60) % 24
    m = minutos_desde_medianoche % 60
    return f"{h:02d}:{m:02d}"


# ----------------------------------------------------------------------
# Filtros y resumen
# ----------------------------------------------------------------------
def puertas_cerradas(estado):
    """Puertas cerradas, ordenadas; es lo que el BFS recibe como `bloqueadas`. O(k)."""
    puertas = _seccion(estado, "puertas") or {}
    return sorted(clave for clave, valor in puertas.items() if valor == "cerrada")


def salas_iluminadas(estado):
    """Salas con la luz encendida, ordenadas. O(k)."""
    luces = _seccion(estado, "luces") or {}
    return sorted(sala for sala, encendida in luces.items() if encendida)


def misiones_con_estado(estado, valor):
    """Salas cuya misión tiene ese estado ("disponible", "bloqueada"...), ordenadas. O(k)."""
    misiones = _seccion(estado, "misiones") or {}
    return sorted(sala for sala, actual in misiones.items() if actual == valor)


def resumen(estado):
    """Conteos para el HUD y el fin de partida. O(k) sumando todas las secciones."""
    conteo = {}
    for valor in (_seccion(estado, "misiones") or {}).values():
        conteo[valor] = conteo.get(valor, 0) + 1
    return {
        "hora": formatear_hora(estado.get("hora_actual_min", 0)),
        "toque_queda": bool(estado.get("toque_queda_activo")),
        "puertas_cerradas": len(puertas_cerradas(estado)),
        "luces_encendidas": len(salas_iluminadas(estado)),
        "misiones": conteo,
        "alertas": len(_seccion(estado, "alertas") or {}),
    }
