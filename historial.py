"""Semana 5: pila (LIFO) para poder deshacer el último movimiento del jugador."""


class Historial:
    def __init__(self, limite=200):
        self._pila = []
        self.limite = limite

    def registrar(self, posicion):
        self._pila.append(posicion)
        if len(self._pila) > self.limite:
            self._pila.pop(0)

    def deshacer(self):
        if not self._pila:
            return None
        return self._pila.pop()

    def esta_vacia(self):
        return len(self._pila) == 0
