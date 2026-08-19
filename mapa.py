"""Semana 12-13: grafo del mundo (el campus) + búsqueda BFS y DFS.

El campus se modela como un grafo no dirigido: cada sala es un nodo y cada
pasillo que conecta dos salas es una arista. BFS se usa para calcular la
ruta más corta entre dos salas (por ejemplo, la ruta del vigilante hacia su
siguiente punto de ronda) y DFS se usa para generar el recorrido de patrulla
completo del vigilante.
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
    """Arma el grafo del campus de 9PM con sus salas y pasillos."""
    mapa = MapaCampus()
    salas = {
        "entrada": (90, 320),
        "patio_central": (280, 320),
        "biblioteca": (280, 130),
        "cafeteria": (480, 130),
        "salon_101": (480, 320),
        "salon_102": (680, 320),
        "laboratorio": (680, 130),
        "auditorio": (860, 320),
        "oficina_profesor": (280, 500),
        "parqueadero": (860, 500),
    }
    for nombre, pos in salas.items():
        mapa.agregar_sala(nombre, pos)

    conexiones = [
        ("entrada", "patio_central"),
        ("patio_central", "biblioteca"),
        ("patio_central", "salon_101"),
        ("patio_central", "oficina_profesor"),
        ("biblioteca", "cafeteria"),
        ("salon_101", "cafeteria"),
        ("salon_101", "salon_102"),
        ("salon_102", "laboratorio"),
        ("salon_102", "auditorio"),
        ("auditorio", "parqueadero"),
        ("oficina_profesor", "parqueadero"),
    ]
    for a, b in conexiones:
        mapa.conectar(a, b)
    return mapa
