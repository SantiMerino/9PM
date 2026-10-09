"""Semana 12-13: grafo del mundo (el campus) + búsqueda BFS y DFS.

El campus se modela como un grafo no dirigido: cada sala/waypoint es un nodo
y cada pasillo que conecta dos nodos es una arista. BFS calcula la ruta más
corta; DFS genera el recorrido de patrulla del vigilante.

El layout físico del nivel 1 vive en mapa_nivel1.py (croquis Instituto Kriete).
"""

from collections import deque


class MapaCampus:
    def __init__(self):
        self.grafo = {}        # nombre_sala -> set(nombres de salas vecinas)
        self.posiciones = {}   # nombre_sala -> (x, y) en pantalla, para dibujar

    def agregar_sala(self, nombre, posicion):
        self.grafo.setdefault(nombre, set())
        self.posiciones[nombre] = posicion

    def conectar(self, sala_a, sala_b):
        self.grafo.setdefault(sala_a, set()).add(sala_b)
        self.grafo.setdefault(sala_b, set()).add(sala_a)

    def vecinos(self, sala):
        return self.grafo.get(sala, set())

    def bfs(self, origen, destino):
        """Ruta más corta (en número de salas) entre origen y destino."""
        if origen == destino:
            return [origen]
        visitados = {origen}
        cola = deque([[origen]])
        while cola:
            camino = cola.popleft()
            actual = camino[-1]
            for vecino in sorted(self.vecinos(actual)):
                if vecino in visitados:
                    continue
                nuevo_camino = camino + [vecino]
                if vecino == destino:
                    return nuevo_camino
                visitados.add(vecino)
                cola.append(nuevo_camino)
        return None

    def dfs(self, origen, visitados=None):
        """Recorrido en profundidad; se usa para armar la ronda del vigilante."""
        if visitados is None:
            visitados = []
        if origen not in visitados:
            visitados.append(origen)
            for vecino in sorted(self.vecinos(origen)):
                self.dfs(vecino, visitados)
        return visitados


def crear_mapa_universidad():
    """Arma el grafo de patrulla del nivel 1 (pasillos del croquis)."""
    from mapa_nivel1 import crear_mapa_nivel1
    return crear_mapa_nivel1()
