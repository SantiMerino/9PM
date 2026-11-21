"""Pruebas del Grafo genérico del Checkpoint 3 (sin pygame)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grafo import Grafo
from mapa import crear_mapa_universidad


def grafo_cuadrado():
    """Cuadrado a-b-c-d con la diagonal a-c."""
    g = Grafo()
    for a, b in [("a", "b"), ("b", "c"), ("c", "d"), ("d", "a"), ("a", "c")]:
        g.agregar_arista(a, b)
    return g


class TestGrafoBasico(unittest.TestCase):
    def test_agregar_nodo_no_duplica(self):
        g = Grafo()
        g.agregar_nodo("x")
        g.agregar_nodo("x")
        self.assertEqual(g.nodos(), ["x"])
        self.assertEqual(g.vecinos("x"), set())

    def test_agregar_arista_crea_nodos_e_ignora_lazos(self):
        g = Grafo()
        g.agregar_arista("a", "b")
        g.agregar_arista("a", "a")
        self.assertTrue(g.existe_nodo("a") and g.existe_nodo("b"))
        self.assertEqual(g.vecinos("a"), {"b"})
        self.assertEqual(g.vecinos("b"), {"a"})
        self.assertEqual(g.numero_aristas(), 1)

    def test_numero_aristas_cuadrado(self):
        self.assertEqual(grafo_cuadrado().numero_aristas(), 5)

    def test_quitar_arista(self):
        g = grafo_cuadrado()
        self.assertTrue(g.quitar_arista("c", "a"))
        self.assertNotIn("c", g.vecinos("a"))
        self.assertEqual(g.numero_aristas(), 4)

    def test_quitar_arista_inexistente_devuelve_false(self):
        g = grafo_cuadrado()
        self.assertFalse(g.quitar_arista("b", "d"))
        self.assertFalse(g.quitar_arista("a", "zzz"))
        self.assertEqual(g.numero_aristas(), 5)

    def test_nodo_inexistente_sin_excepcion(self):
        g = Grafo()
        self.assertFalse(g.existe_nodo("nada"))
        self.assertEqual(g.vecinos("nada"), set())
        self.assertFalse(g.existe_nodo(["no", "hasheable"]))


class TestBFS(unittest.TestCase):
    def test_ruta_mas_corta_usa_la_diagonal(self):
        g = grafo_cuadrado()
        self.assertEqual(g.bfs_ruta("b", "d"), ["b", "a", "d"])
        self.assertEqual(g.bfs_ruta("a", "c"), ["a", "c"])
        self.assertEqual(g.bfs_ruta("a", "a"), ["a"])

    def test_arista_bloqueada_da_ruta_alternativa(self):
        g = grafo_cuadrado()
        self.assertEqual(g.bfs_ruta("a", "c", bloqueadas=[("a", "c")]), ["a", "b", "c"])

    def test_bloqueo_en_cualquier_orden(self):
        g = grafo_cuadrado()
        self.assertEqual(g.bfs_ruta("a", "b", bloqueadas=[("b", "a")]), ["a", "c", "b"])
        self.assertEqual(g.bfs_ruta("b", "a", bloqueadas=[("a", "b")]), ["b", "c", "a"])

    def test_ruta_imposible_y_nodo_inexistente(self):
        g = grafo_cuadrado()
        g.agregar_nodo("isla")
        self.assertIsNone(g.bfs_ruta("a", "isla"))
        self.assertIsNone(g.bfs_ruta("a", "no_existe"))
        self.assertIsNone(g.bfs_ruta("no_existe", "a"))
        self.assertFalse(g.hay_ruta("a", "isla"))
        self.assertTrue(g.hay_ruta("a", "d"))

    def test_bloqueadas_invalidas_no_fallan(self):
        g = grafo_cuadrado()
        self.assertEqual(g.bfs_ruta("a", "c", bloqueadas=[None, "x", (1, 2, 3)]), ["a", "c"])

    def test_alcanzables_con_puerta_de_terraza_cerrada(self):
        campus = Grafo()
        campus.grafo = {n: set(v) for n, v in crear_mapa_universidad().grafo.items()}
        abiertos = campus.alcanzables("lobby")
        cerrada = campus.alcanzables("lobby", bloqueadas=[("terraza", "terraza_n")])
        self.assertIn("terraza_n", abiertos)
        self.assertNotIn("terraza_n", cerrada)
        self.assertIn("terraza", cerrada)
        self.assertEqual(campus.alcanzables("no_existe"), set())


class TestDFS(unittest.TestCase):
    def test_dfs_orden_preorden_sorted(self):
        g = grafo_cuadrado()
        self.assertEqual(g.dfs("a"), ["a", "b", "c", "d"])
        self.assertEqual(g.dfs("no_existe"), [])

    def test_dfs_campus_visita_los_16_sin_repetir(self):
        campus = crear_mapa_universidad()
        campus_generico = Grafo()
        campus_generico.grafo = {n: set(v) for n, v in campus.grafo.items()}
        recorrido = campus_generico.dfs("lobby")
        self.assertEqual(len(recorrido), 16)
        self.assertEqual(len(set(recorrido)), 16)
        self.assertEqual(set(recorrido), set(campus.grafo))

    def test_componentes_detecta_una_isla(self):
        g = grafo_cuadrado()
        g.agregar_arista("isla_1", "isla_2")
        zonas = g.componentes()
        self.assertEqual(len(zonas), 2)
        self.assertEqual(zonas[0], {"a", "b", "c", "d"})
        self.assertEqual(zonas[1], {"isla_1", "isla_2"})

    def test_componentes_grafo_vacio(self):
        self.assertEqual(Grafo().componentes(), [])


if __name__ == "__main__":
    unittest.main()
