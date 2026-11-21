"""Semana 12-13: grafo del mundo (el campus) + búsqueda BFS y DFS.

El campus se modela como un grafo no dirigido: cada sala/waypoint es un nodo
y cada pasillo que conecta dos nodos es una arista. BFS calcula la ruta más
corta; DFS genera el recorrido de patrulla del vigilante.

El layout físico del nivel 1 vive en mapa_nivel1.py (croquis Instituto Kriete).
"""

from grafo import Grafo


class MapaCampus(Grafo):
    """El campus es un Grafo (self.grafo: dict sala -> set de vecinas) que además
    sabe dónde se dibuja cada sala. BFS, DFS, alcanzables y componentes vienen
    de Grafo."""

    def __init__(self):
        super().__init__()
        self.posiciones = {}   # nombre_sala -> (x, y) en pantalla, para dibujar

    def agregar_sala(self, nombre, posicion):
        self.agregar_nodo(nombre)
        self.posiciones[nombre] = posicion

    def conectar(self, sala_a, sala_b):
        self.agregar_arista(sala_a, sala_b)

    def bfs(self, origen, destino, bloqueadas=()):
        """Alias que mantiene el nombre que usa main.py (vigilante)."""
        return self.bfs_ruta(origen, destino, bloqueadas)


def crear_mapa_universidad():
    """Arma el grafo de patrulla del nivel 1 (pasillos del croquis)."""
    from mapa_nivel1 import crear_mapa_nivel1
    return crear_mapa_nivel1()
