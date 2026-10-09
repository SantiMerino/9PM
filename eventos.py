"""Semana 6 / Guía 6: COLAS (FIFO) con collections.deque.

En 9PM hay tres colas:

1. Eventos del mapa (Torre de Laboratorios): se encolan al iniciar la partida
   y cada movimiento del jugador dentro de la Torre procesa el SIGUIENTE con
   `popleft`, en el mismo orden en que llegaron.
2. Turnos de la Torre: estudiante, vigilante y robot de limpieza rotan con
   `popleft` + `append`; el que acaba de jugar vuelve al final de la fila.
3. Avisos del reloj del campus (10 min, 5 min, toque de queda): se programan
   en orden cronológico y salen cuando llega su hora.

Se usa `deque` porque `popleft` y `append` son O(1). Con una lista,
`lista.pop(0)` es O(n): tiene que correr todos los demás elementos una
posición a la izquierda.
"""

import random
from collections import deque

# ---------------------------------------------------------------------------
# 1. Eventos del mapa de la Torre
# ---------------------------------------------------------------------------
TIPOS_EVENTO = ("trampa", "enemigo", "camara", "apagon", "cofre", "mensaje")

ETIQUETAS_TIPO = {
    "trampa": "Trampas",
    "enemigo": "Vigilante cerca",
    "camara": "Cámaras",
    "apagon": "Apagones",
    "cofre": "Casilleros",
    "mensaje": "Mensajes",
}

EVENTOS_TORRE = (
    {"tipo": "trampa", "titulo": "Piso recién trapeado",
     "texto": "Resbalas en el piso mojado y pierdes 1 minuto.", "minutos": 1},
    {"tipo": "trampa", "titulo": "Puerta corrediza trabada",
     "texto": "La puerta se traba a medio camino: forcejeas 2 minutos.", "minutos": 2},
    {"tipo": "trampa", "titulo": "Cable de red suelto",
     "texto": "Se te enreda la mochila en un cable: pierdes 1 minuto.", "minutos": 1},
    {"tipo": "enemigo", "titulo": "Pasos en el pasillo",
     "texto": "Se oyen pasos: el vigilante de la torre camina hacia ti."},
    {"tipo": "enemigo", "titulo": "Radio del vigilante",
     "texto": "Chilla un radio: «Revisen el segundo nivel». El vigilante se acerca."},
    {"tipo": "camara", "titulo": "Cámara de seguridad",
     "texto": "Una cámara gira hacia ti: el vigilante te seguirá 3 turnos.", "turnos": 3},
    {"tipo": "apagon", "titulo": "Apagón parcial",
     "texto": "Las luces parpadean y se apagan: el vigilante pierde tu rastro."},
    {"tipo": "cofre", "titulo": "Casillero entreabierto",
     "texto": "Dentro hay una nota: marca en el plano dónde quedó un objeto perdido."},
    {"tipo": "cofre", "titulo": "Caja de objetos perdidos",
     "texto": "Una etiqueta de la caja dice en qué sala quedó otro objeto."},
    {"tipo": "mensaje", "titulo": "Pizarra olvidada",
     "texto": "Alguien escribió: «Examen de EDA el lunes: pilas, colas y recursión»."},
    {"tipo": "mensaje", "titulo": "Ventana al jardín",
     "texto": "Desde la ventana ves al vigilante del campus cruzar el jardín."},
    {"tipo": "mensaje", "titulo": "Afiche de la feria",
     "texto": "Se despega un afiche de la feria de proyectos. Nadie más lo vio."},
)


def crear_cola_eventos_torre(azar=None):
    """Arma la cola de eventos del mapa al iniciar la partida: copia los
    eventos de la Torre, los baraja y los encola uno por uno (append)."""
    azar = azar or random.Random()
    eventos = [dict(evento) for evento in EVENTOS_TORRE]
    azar.shuffle(eventos)
    cola = deque()
    for evento in eventos:
        encolar_evento(cola, evento)
    return cola


def encolar_evento(cola_eventos, evento):
    """Agrega un evento al FINAL de la cola (append, O(1))."""
    cola_eventos.append(evento)
    return evento


def procesar_siguiente_evento(cola_eventos):
    """Quita y devuelve el evento MÁS ANTIGUO (popleft, O(1)).
    Devuelve None si la cola está vacía, en vez de lanzar IndexError."""
    if cola_vacia(cola_eventos):
        return None
    return cola_eventos.popleft()


def ver_siguiente_evento(cola_eventos):
    """Consulta el evento más antiguo sin sacarlo. None si la cola está vacía."""
    if cola_vacia(cola_eventos):
        return None
    return cola_eventos[0]


def cola_vacia(cola_eventos):
    """True si no quedan eventos pendientes."""
    return len(cola_eventos) == 0


# --- Funciones de la Guía 6 adaptadas a 9PM --------------------------------
def procesar_multiples_eventos(cola_eventos, cantidad):
    """Procesa hasta `cantidad` eventos seguidos (o hasta vaciar la cola) y los
    devuelve en orden de llegada."""
    procesados = []
    for _ in range(max(0, cantidad)):
        if cola_vacia(cola_eventos):
            break
        procesados.append(procesar_siguiente_evento(cola_eventos))
    return procesados


def contar_eventos_de_tipo(cola_eventos, tipo):
    """Cuenta cuántos eventos pendientes son de un tipo, SIN modificar la cola
    (solo se recorre con un for). Alimenta el panel "Ver eventos"."""
    contador = 0
    for evento in cola_eventos:
        if evento["tipo"] == tipo:
            contador += 1
    return contador


def invertir_cola(cola_eventos):
    """Invierte el orden de la cola usando una pila auxiliar: se vacía la cola
    (popleft) apilando cada evento y luego se desapila (pop) volviendo a
    encolar. Modifica la cola recibida."""
    pila = []
    while not cola_vacia(cola_eventos):
        pila.append(cola_eventos.popleft())
    while pila:
        cola_eventos.append(pila.pop())
    return cola_eventos


def resumen_eventos(cola_eventos):
    """Diccionario {tipo: cantidad} de los eventos pendientes."""
    return {tipo: contar_eventos_de_tipo(cola_eventos, tipo) for tipo in TIPOS_EVENTO}


# ---------------------------------------------------------------------------
# 2. Sistema de turnos de la Torre
# ---------------------------------------------------------------------------
ESTUDIANTE = "Estudiante"
VIGILANTE = "Vigilante de la torre"
ROBOT = "Robot de limpieza"
PARTICIPANTES_TORRE = (ESTUDIANTE, VIGILANTE, ROBOT)


def crear_turnos(participantes=PARTICIPANTES_TORRE):
    """Cola de turnos con los participantes en el orden en que juegan."""
    return deque(participantes)


def siguiente_turno(turnos):
    """Saca al primero de la fila (popleft), lo devuelve al final (append) y
    devuelve a quién le toca jugar. None si no hay participantes."""
    if len(turnos) == 0:
        return None
    actual = turnos.popleft()
    turnos.append(actual)
    return actual


def ver_turno_actual(turnos):
    """A quién le toca ahora, sin rotar la fila."""
    return turnos[0] if turnos else None


def ronda_completa(turnos):
    """Juega una ronda: cada participante recibe exactamente un turno.
    Devuelve la lista de participantes en el orden en que jugaron."""
    return [siguiente_turno(turnos) for _ in range(len(turnos))]


def simular_turnos(participantes, rondas):
    """Guía 6 (reto): reparte `rondas` turnos en ciclo sobre una COPIA de la
    fila, sin alterar la cola real. Devuelve las líneas "Turno n: le toca a X"
    que se muestran en el panel "Ver turnos"."""
    fila = deque(participantes)
    if len(fila) == 0:
        return []
    lineas = []
    for ronda in range(1, rondas + 1):
        actual = fila.popleft()
        lineas.append(f"Turno {ronda}: le toca a {actual}")
        fila.append(actual)
    return lineas


# ---------------------------------------------------------------------------
# 3. Avisos programados del reloj del campus
# ---------------------------------------------------------------------------
class Evento:
    """Aviso que se dispara a una hora del juego (minutos desde medianoche)."""

    def __init__(self, tiempo_disparo_min, tipo, datos=None):
        self.tiempo_disparo_min = tiempo_disparo_min
        self.tipo = tipo
        self.datos = datos or {}


class ColaEventos:
    """Cola FIFO de avisos del reloj. Se programan en orden cronológico, así
    que basta mirar el frente: si su hora llegó, sale con popleft."""

    def __init__(self):
        self._cola = deque()

    def programar(self, evento):
        """Encola un aviso al final (append)."""
        self._cola.append(evento)

    def eventos_listos(self, tiempo_actual_min):
        """Saca del frente (popleft) todos los avisos cuya hora ya llegó."""
        listos = []
        while self._cola and self._cola[0].tiempo_disparo_min <= tiempo_actual_min:
            listos.append(self._cola.popleft())
        return listos

    def __len__(self):
        return len(self._cola)
