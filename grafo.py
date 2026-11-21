"""Checkpoint 3: grafo genérico y reutilizable.

Grafo no dirigido guardado como lista de adyacencia: un diccionario que va de
cada nodo al conjunto de sus vecinos. No depende de ningún mapa en particular:
lo usan el campus (MapaCampus) y la Torre (grafo_desde_mazmorra).
"""


class Grafo:
    """Grafo no dirigido con lista de adyacencia: dict nodo -> set(vecinos)."""

    def __init__(self):
        self.grafo = {}

    # ------------------------------------------------------------------
    # Construcción y consultas básicas
    # ------------------------------------------------------------------
    def agregar_nodo(self, nodo):
        """Agrega un nodo sin vecinos; si ya existe no hace nada. O(1) promedio."""
        self.grafo.setdefault(nodo, set())

    def agregar_arista(self, a, b):
        """Une a y b en los dos sentidos y crea los nodos si faltan.
        Ignora los lazos (a == b). O(1) promedio."""
        if a == b:
            return
        self.grafo.setdefault(a, set()).add(b)
        self.grafo.setdefault(b, set()).add(a)

    def quitar_arista(self, a, b):
        """Quita la arista a-b. Devuelve False si no existía. O(1) promedio."""
        if b not in self.grafo.get(a, set()):
            return False
        self.grafo[a].discard(b)
        self.grafo[b].discard(a)
        return True

    def existe_nodo(self, nodo):
        """True si el nodo está en el grafo. O(1) promedio."""
        try:
            return nodo in self.grafo
        except TypeError:   # nodo no hasheable (por ejemplo, una lista)
            return False

    def vecinos(self, nodo):
        """Conjunto de vecinos del nodo; set() si no existe. O(1) promedio."""
        if not self.existe_nodo(nodo):
            return set()
        return self.grafo[nodo]

    def nodos(self):
        """Lista ordenada de los nodos. O(V log V)."""
        return sorted(self.grafo)

    def numero_aristas(self):
        """Cantidad de aristas (cada una se guarda dos veces). O(V)."""
        return sum(len(v) for v in self.grafo.values()) // 2
