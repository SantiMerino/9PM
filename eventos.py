"""Semana 6: cola (FIFO) de eventos programados del turno de la noche
(avisos de hora, rondas de vigilancia, apagado de luces, etc.)."""

from collections import deque


class Evento:
    def __init__(self, tiempo_disparo_min, tipo, datos=None):
        self.tiempo_disparo_min = tiempo_disparo_min
        self.tipo = tipo
        self.datos = datos or {}


class ColaEventos:
    def __init__(self):
        self._cola = deque()

    def programar(self, evento):
        self._cola.append(evento)

    def eventos_listos(self, tiempo_actual_min):
        """Saca de la cola (en orden FIFO) todos los eventos cuya hora ya llegó."""
        listos = []
        pendientes = deque()
        while self._cola:
            evento = self._cola.popleft()
            if evento.tiempo_disparo_min <= tiempo_actual_min:
                listos.append(evento)
            else:
                pendientes.append(evento)
        self._cola = pendientes
        return listos
