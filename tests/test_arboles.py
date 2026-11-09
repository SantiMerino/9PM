"""Exposición de árboles: árbol de misiones y árbol de decisión (sin pygame)."""
import io
import os
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import arboles as A


class TestArbolMisiones(unittest.TestCase):
    def setUp(self):
        self.raiz = A.crear_arbol_misiones()

    def test_cumple_minimos_de_la_rubrica(self):
        self.assertGreaterEqual(A.contar_nodos(self.raiz), 8)
        self.assertGreaterEqual(A.altura(self.raiz) + 1, 3)  # niveles

    def test_un_solo_padre_por_mision(self):
        vistos = []

        def recorrer(nodo):
            vistos.append(nodo.nombre)
            for hijo in nodo.hijos:
                self.assertIs(hijo.padre, nodo)
                recorrer(hijo)

        recorrer(self.raiz)
        self.assertEqual(len(vistos), len(set(vistos)))

    def test_altura_y_hojas(self):
        self.assertEqual(A.altura(self.raiz), 3)
        self.assertEqual(A.contar_hojas(self.raiz), len(A.hojas(self.raiz)))
        hoja = A.Nodo("sola")
        self.assertEqual(A.altura(hoja), 0)
        self.assertEqual(A.contar_hojas(hoja), 1)

    def test_preorden_con_sangria(self):
        lineas = A.recorrido_preorden(self.raiz)
        self.assertEqual(len(lineas), A.contar_nodos(self.raiz))
        self.assertTrue(lineas[0].startswith("[ ] Préstamo de medianoche"))
        self.assertTrue(lineas[1].startswith("    [ ] Una última firma"))

    def test_postorden_termina_en_la_raiz(self):
        orden = A.recorrido_postorden(self.raiz)
        self.assertEqual(orden[-1], self.raiz.nombre)
        self.assertLess(orden.index("Bitácora de física"), orden.index("Última exposición"))

    def test_al_inicio_solo_la_raiz_esta_disponible(self):
        self.assertEqual(A.misiones_disponibles(self.raiz), [self.raiz])

    def test_mision_bloqueada_no_se_completa(self):
        ok, mensaje = A.completar_mision(self.raiz, "Puesta en marcha")
        self.assertFalse(ok)
        self.assertIn("bloqueada", mensaje)
        self.assertFalse(A.buscar(self.raiz, "Puesta en marcha").completada)

    def test_completar_desbloquea_a_los_hijos(self):
        ok, nuevas = A.completar_mision(self.raiz, "Préstamo de medianoche")
        self.assertTrue(ok)
        self.assertEqual([m.nombre for m in nuevas],
                         ["Una última firma", "Entrega digital", "Cierre de caja"])
        self.assertEqual(A.misiones_disponibles(self.raiz), nuevas)
        A.completar_mision(self.raiz, "Entrega digital")
        disponibles = [m.nombre for m in A.misiones_disponibles(self.raiz)]
        self.assertIn("Puesta en marcha", disponibles)
        self.assertNotIn("Entrega digital", disponibles)

    def test_errores_de_completar(self):
        self.assertFalse(A.completar_mision(self.raiz, "No existe")[0])
        A.completar_mision(self.raiz, "Préstamo de medianoche")
        ok, mensaje = A.completar_mision(self.raiz, "Préstamo de medianoche")
        self.assertFalse(ok)
        self.assertIn("ya estaba", mensaje)


class TestArbolDecision(unittest.TestCase):
    def setUp(self):
        self.arbol = A.crear_arbol_decision()

    def test_cumple_minimos_de_la_rubrica(self):
        self.assertGreaterEqual(A.contar_preguntas(self.arbol), 3)
        self.assertGreaterEqual(A.contar_decisiones(self.arbol), 4)

    def test_situaciones_llegan_a_decisiones_distintas(self):
        decisiones = [A.decidir(self.arbol, s) for _, s in A.SITUACIONES]
        self.assertEqual(len(set(decisiones)), len(A.SITUACIONES))

    def test_decisiones_esperadas(self):
        base = {"reportando": False, "jugador_cerca": False, "toque_queda": False,
                "alerta_robot": False, "minutos_para_toque": 30}
        self.assertEqual(A.decidir(self.arbol, {**base, "jugador_cerca": True, "toque_queda": True}),
                         "Expulsar al estudiante")
        self.assertEqual(A.decidir(self.arbol, {**base, "jugador_cerca": True}),
                         "Sermonear 3 minutos")
        self.assertEqual(A.decidir(self.arbol, base), "Patrullar una sala al azar")

    def test_decidir_hace_como_maximo_h_preguntas(self):
        h = A.altura_decision(self.arbol)
        for _, situacion in A.SITUACIONES:
            camino = []
            A.decidir(self.arbol, situacion, camino)
            self.assertLessEqual(len(camino), h)

    def test_degenerado_tiene_altura_igual_a_sus_preguntas(self):
        deg = A.arbol_decision_degenerado()
        self.assertEqual(A.altura_decision(deg), A.contar_preguntas(deg))
        self.assertGreater(A.altura_decision(deg), A.altura_decision(self.arbol))

    def test_recorridos_visitan_todos_los_nodos(self):
        total = A.contar_preguntas(self.arbol) + A.contar_decisiones(self.arbol)
        pre = A.preorden_decision(self.arbol)
        ino = A.inorden_decision(self.arbol)
        post = A.postorden_decision(self.arbol)
        self.assertEqual(len(pre), total)
        self.assertEqual(sorted(pre), sorted(ino))
        self.assertEqual(sorted(pre), sorted(post))
        self.assertEqual(pre[0], post[-1])  # la raíz


class TestDemo(unittest.TestCase):
    def test_main_corre_completo(self):
        salida = io.StringIO()
        with redirect_stdout(salida):
            A.main()
        texto = salida.getvalue()
        self.assertIn("ERROR", texto)
        self.assertIn("Se desbloquea", texto)
        self.assertIn("Expulsar al estudiante", texto)


if __name__ == "__main__":
    unittest.main()
