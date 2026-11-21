"""Niveles de dificultad de 9PM.

Cada nivel es un diccionario de parámetros que la partida consulta en vez de
usar constantes fijas: qué tan rápido corre el reloj, qué tan rápido es el
vigilante y qué tan difícil es convencerlo en una batalla de argumentos.
"""

DIFICULTADES = {
    "facil": {
        "id": "facil",
        "nombre": "Tranquilo",
        "descripcion": "El reloj corre lento y el vigilante se cree casi todo.",
        "segundos_por_minuto": 15.0,
        "vel_vigilante": 95.0,
        "vel_persecucion": 205.0,
        "sospecha": 70,          # "vida" del vigilante en la batalla
        "dano": 0.75,            # cuánto te baja la credibilidad
        "huir": 0.65,            # probabilidad base de escapar
        "minutos_sermon": 2,
        "multiplicador_puntos": 0.8,
    },
    "normal": {
        "id": "normal",
        "nombre": "Normal",
        "descripcion": "La noche como debe ser: justa, pero sin regalos.",
        "segundos_por_minuto": 12.0,
        "vel_vigilante": 110.0,
        "vel_persecucion": 230.0,
        "sospecha": 90,
        "dano": 1.0,
        "huir": 0.5,
        "minutos_sermon": 3,
        "multiplicador_puntos": 1.0,
    },
    "dificil": {
        "id": "dificil",
        "nombre": "Pesadilla",
        "descripcion": "El reloj vuela, el vigilante corre y no se traga ninguna excusa.",
        "segundos_por_minuto": 9.0,
        "vel_vigilante": 128.0,
        "vel_persecucion": 250.0,
        "sospecha": 115,
        "dano": 1.3,
        "huir": 0.35,
        "minutos_sermon": 5,
        "multiplicador_puntos": 1.5,
    },
}

ORDEN = ("facil", "normal", "dificil")


def obtener_dificultad(clave):
    """Parámetros del nivel; si la clave no existe devuelve "normal". O(1)."""
    return DIFICULTADES.get(clave, DIFICULTADES["normal"])
