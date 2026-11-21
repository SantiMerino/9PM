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


def _recorrer(mision):
    """Todas las misiones debajo de `mision` (sin ella), para las pruebas."""
    resultado = []
    for hija in mision.hijas:
        resultado.append(hija)
        resultado += _recorrer(hija)
    return resultado


class TestArbolJuego(unittest.TestCase):
    def setUp(self):
        self.raiz = M.crear_arbol_misiones_juego()
        self.encargos = _recorrer(self.raiz)
        self.por_sala = {m.ubicacion: m for m in self.encargos}

    def test_13_encargos_con_un_solo_padre(self):
        # Prueba 1
        self.assertEqual(len(self.encargos), 13)
        self.assertEqual(len(set(map(id, self.encargos))), 13)
        self.assertEqual(len(self.raiz.hijas), 1)
        self.assertTrue(self.raiz.es_raiz)
        for mision in self.encargos:
            self.assertIsNotNone(mision.padre)
            self.assertEqual(sum(mision in m.hijas for m in [self.raiz] + self.encargos), 1)

    def test_mismos_encargos_que_la_lista_plana(self):
        esperados = {sala: (titulo, tuple(pasos)) for sala, titulo, pasos in M.ENCARGOS}
        self.assertEqual({m.ubicacion: (m.titulo, m.pasos) for m in self.encargos}, esperados)
        self.assertEqual(max(m.nivel() for m in self.encargos), 4)

    def test_al_inicio_solo_biblioteca(self):
        # Prueba 2
        libres = [m.ubicacion for m in self.encargos if m.desbloqueada()]
        self.assertEqual(libres, ['biblioteca'])

    def test_biblioteca_desbloquea_tres(self):
        # Prueba 4
        self.por_sala['biblioteca'].completar()
        libres = {m.ubicacion for m in self.encargos
                  if m.desbloqueada() and not m.completada}
        self.assertEqual(libres, {'sala_reuniones', 'r101', 'cafeteria'})

    def test_recompensas_y_efectos(self):
        for mision in self.encargos:
            self.assertEqual(mision.recompensa, 10 * mision.nivel())
        self.assertEqual(self.por_sala['biblioteca'].efecto, {'apaga': 'biblioteca'})
        self.assertEqual(self.por_sala['cafeteria'].efecto, {'abre': ('terraza', 'terraza_n')})
        self.assertIsNone(self.por_sala['r102'].efecto)

    def test_cada_llamada_crea_un_arbol_nuevo(self):
        otro = M.crear_arbol_misiones_juego()
        self.por_sala['biblioteca'].completar()
        self.assertFalse(otro.hijas[0].completada)


if __name__ == '__main__':
    unittest.main()
