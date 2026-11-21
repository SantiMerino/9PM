"""Checkpoint 3: grafo genérico y reutilizable.

Grafo no dirigido guardado como lista de adyacencia: un diccionario que va de
cada nodo al conjunto de sus vecinos. No depende de ningún mapa en particular:
lo usan el campus (MapaCampus) y la Torre (grafo_desde_mazmorra).

Lista de adyacencia y no matriz: cada sala tiene pocos vecinos, así que se
guardan O(V + E) datos en vez de O(V²) y recorrer los vecinos de un nodo cuesta
lo que tiene, no V.
"""

from collections import deque


def _normalizar_bloqueadas(bloqueadas):
    """Convierte las aristas bloqueadas [(a, b), ...] en un set de frozenset({a, b})
    para que bloqueen en los dos sentidos y la consulta sea O(1). Ignora lo inválido."""
    normalizadas = set()
    for arista in bloqueadas or ():
        try:
            a, b = arista
            normalizadas.add(frozenset((a, b)))
        except (TypeError, ValueError):
            continue
    return normalizadas


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

    # ------------------------------------------------------------------
    # BFS: ruta con menos saltos y nodos alcanzables
    # ------------------------------------------------------------------
    def bfs_ruta(self, origen, destino, bloqueadas=()):
        """Ruta con menos saltos de origen a destino sin cruzar aristas bloqueadas.
        BFS visita los nodos por capas (distancia 1, luego 2...), así que el primer
        camino que llega al destino es el más corto. [origen] si son iguales,
        None si algún nodo no existe o no hay camino. O(V + E)."""
        if not self.existe_nodo(origen) or not self.existe_nodo(destino):
            return None
        if origen == destino:
            return [origen]
        cerradas = _normalizar_bloqueadas(bloqueadas)
        visitados = {origen}
        cola = deque([[origen]])
        while cola:
            camino = cola.popleft()
            actual = camino[-1]
            for vecino in sorted(self.vecinos(actual)):
                if vecino in visitados or frozenset((actual, vecino)) in cerradas:
                    continue
                nuevo_camino = camino + [vecino]
                if vecino == destino:
                    return nuevo_camino
                visitados.add(vecino)
                cola.append(nuevo_camino)
        return None

    def hay_ruta(self, origen, destino, bloqueadas=()):
        """True si se puede ir de origen a destino. O(V + E)."""
        return self.bfs_ruta(origen, destino, bloqueadas) is not None

    def alcanzables(self, origen, bloqueadas=()):
        """Conjunto de nodos a los que se llega desde origen (incluido) sin cruzar
        aristas bloqueadas, usando BFS. set() si el origen no existe. O(V + E)."""
        if not self.existe_nodo(origen):
            return set()
        cerradas = _normalizar_bloqueadas(bloqueadas)
        visitados = {origen}
        cola = deque([origen])
        while cola:
            actual = cola.popleft()
            for vecino in self.vecinos(actual):
                if vecino not in visitados and frozenset((actual, vecino)) not in cerradas:
                    visitados.add(vecino)
                    cola.append(vecino)
        return visitados

    # ------------------------------------------------------------------
    # DFS: recorrido en profundidad y zonas aisladas
    # ------------------------------------------------------------------
    def dfs(self, origen):
        """Recorrido en profundidad (preorden recursivo, vecinos en orden sorted).
        Es el mismo orden que usaba MapaCampus, porque de él sale la ronda del
        vigilante. [] si el origen no existe. O(V + E)."""
        if not self.existe_nodo(origen):
            return []
        orden, visitados = [], set()
        self._dfs_visitar(origen, orden, visitados)
        return orden

    def _dfs_visitar(self, nodo, orden, visitados):
        visitados.add(nodo)
        orden.append(nodo)
        for vecino in sorted(self.vecinos(nodo)):
            if vecino not in visitados:
                self._dfs_visitar(vecino, orden, visitados)

    def componentes(self):
        """Zonas conectadas del grafo como lista de sets, la más grande primero.
        Si hay más de una, las demás son zonas aisladas. O(V + E)."""
        zonas, vistos = [], set()
        for nodo in self.nodos():
            if nodo not in vistos:
                zona = set(self.dfs(nodo))
                vistos |= zona
                zonas.append(zona)
        zonas.sort(key=len, reverse=True)
        return zonas
