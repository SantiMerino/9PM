"""Pruebas del Grafo genérico del Checkpoint 3 (sin pygame)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grafo import Grafo


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


if __name__ == "__main__":
    unittest.main()
