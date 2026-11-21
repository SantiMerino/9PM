"""Árbol de misiones del juego: dependencias, recorridos y recompensas (sin pygame)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import misiones as M


class TestMision(unittest.TestCase):
    def test_mision_principal_sigue_plana(self):
        # Prueba 11: el juego actual usa p.mision.hijas como 13 encargos planos.
        raiz = M.crear_mision_principal()
        self.assertEqual(len(raiz.hijas), 13)
        self.assertTrue(all(not h.hijas for h in raiz.hijas))
        self.assertTrue(all(h.padre is raiz for h in raiz.hijas))
        self.assertTrue(all(h.desbloqueada() for h in raiz.hijas))
        self.assertEqual([h.ubicacion for h in raiz.hijas][:3],
                         ['biblioteca', 'lab_siemens', 'sala_reuniones'])

    def test_padre_nivel_y_desbloqueo(self):
        raiz = M.Mision('Raíz', '', es_raiz=True)
        a = raiz.agregar_submision(M.Mision('A', '', 'a', recompensa=10))
        b = a.agregar_submision(M.Mision('B', '', 'b'))
        self.assertIs(b.padre, a)
        self.assertEqual((raiz.nivel(), a.nivel(), b.nivel()), (0, 1, 2))
        self.assertTrue(a.desbloqueada())
        self.assertFalse(b.desbloqueada())
        a.completar()
        self.assertTrue(b.desbloqueada())
        self.assertEqual(a.recompensa, 10)
        self.assertIsNone(a.efecto)

    def test_agregar_submision_invalida_no_rompe_el_arbol(self):
        raiz = M.Mision('Raíz', '', es_raiz=True)
        a = raiz.agregar_submision(M.Mision('A', '', 'a'))
        otra = M.Mision('Otra', '', 'otra')
        self.assertIsNone(raiz.agregar_submision(None))
        self.assertIsNone(raiz.agregar_submision(a))     # repetida: ya tiene padre
        self.assertIsNone(otra.agregar_submision(a))     # tendría dos padres
        self.assertIsNone(a.agregar_submision(raiz))     # formaría un ciclo
        self.assertIsNone(a.agregar_submision(a))
        self.assertEqual(raiz.hijas, [a])
        self.assertIs(a.padre, raiz)

    def test_raiz_contenedora_se_completa_con_sus_descendientes(self):
        raiz = M.Mision('Raíz', '', es_raiz=True)
        a = raiz.agregar_submision(M.Mision('A', '', 'a'))
        b = a.agregar_submision(M.Mision('B', '', 'b'))
        self.assertFalse(raiz.completada)
        a.completar()
        self.assertFalse(raiz.completada)
        b.completar()
        self.assertTrue(raiz.completada)
        b.completada = False                              # deshacer
        self.assertFalse(raiz.completada)


if __name__ == '__main__':
    unittest.main()
