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


class TestCompletarPorSala(unittest.TestCase):
    def setUp(self):
        self.raiz = M.crear_arbol_misiones_juego()

    def test_disponibles_al_inicio_y_despues_de_biblioteca(self):
        self.assertEqual([m.ubicacion for m in M.disponibles(self.raiz)], ['biblioteca'])
        ok, nuevas = M.completar_por_sala(self.raiz, 'biblioteca')
        self.assertTrue(ok)
        self.assertEqual([m.ubicacion for m in nuevas], ['sala_reuniones', 'r101', 'cafeteria'])
        self.assertEqual([m.ubicacion for m in M.disponibles(self.raiz)],
                         ['sala_reuniones', 'r101', 'cafeteria'])

    def test_bloqueada_nombra_a_su_padre(self):
        # Prueba 3
        M.completar_por_sala(self.raiz, 'biblioteca')
        ok, mensaje = M.completar_por_sala(self.raiz, 'lab_siemens')
        self.assertFalse(ok)
        self.assertIn('«Entrega digital»', mensaje)
        self.assertFalse(M.buscar_por_sala(self.raiz, 'lab_siemens').completada)

    def test_repetida(self):
        # Prueba 5
        self.assertTrue(M.completar_por_sala(self.raiz, 'biblioteca')[0])
        ok, mensaje = M.completar_por_sala(self.raiz, 'biblioteca')
        self.assertFalse(ok)
        self.assertIsInstance(mensaje, str)
        self.assertIn('ya estaba completada', mensaje)

    def test_sala_inexistente_y_datos_invalidos(self):
        # Prueba 6
        self.assertIsNone(M.buscar_por_sala(self.raiz, 'no_existe'))
        self.assertIsNone(M.buscar_por_sala(self.raiz, None))
        self.assertIsNone(M.buscar_por_sala(None, 'biblioteca'))
        self.assertIsNone(M.buscar_por_sala(self.raiz, 'lobby'))   # la raíz no es encargo
        for raiz, sala in ((self.raiz, 'no_existe'), (self.raiz, None), (self.raiz, 42),
                           (None, 'biblioteca'), (self.raiz, 'lobby')):
            ok, mensaje = M.completar_por_sala(raiz, sala)
            self.assertFalse(ok)
            self.assertIsInstance(mensaje, str)
        self.assertEqual(M.disponibles(None), [])

    def test_buscar_por_sala(self):
        mision = M.buscar_por_sala(self.raiz, 'r104')
        self.assertEqual(mision.titulo, 'Bitácora de física')
        self.assertEqual(mision.padre.ubicacion, 'r105')


class TestPreorden(unittest.TestCase):
    def setUp(self):
        self.raiz = M.crear_arbol_misiones_juego()

    def test_lineas_preorden(self):
        lineas = M.lineas_preorden(self.raiz)
        self.assertEqual(len(lineas), 14)
        self.assertEqual(lineas[0], (0, self.raiz))
        self.assertEqual([(n, m.ubicacion) for n, m in lineas[1:4]],
                         [(1, 'biblioteca'), (2, 'sala_reuniones'), (3, 'r102')])
        for nivel, mision in lineas:
            self.assertEqual(nivel, mision.nivel())
        self.assertEqual(M.lineas_preorden(None), [])

    def test_todas_las_misiones_respeta_dependencias(self):
        # Prueba 7
        lista = M.todas_las_misiones(self.raiz)
        self.assertEqual(len(lista), 13)
        self.assertNotIn(self.raiz, lista)
        for mision in lista:
            ok, resultado = M.completar_por_sala(self.raiz, mision.ubicacion)
            self.assertTrue(ok, resultado)
        self.assertTrue(self.raiz.completada)
        self.assertEqual(M.disponibles(self.raiz), [])

    def test_texto_arbol_con_sangria(self):
        # Prueba 10
        renglones = M.texto_arbol(self.raiz).split('\n')
        self.assertEqual(len(renglones), 14)
        self.assertEqual(renglones[0], 'Salir del campus')
        self.assertEqual(renglones[1], '  [ ] Préstamo de medianoche (biblioteca)')
        self.assertEqual(renglones[2], '    [bloqueada] Una última firma (sala_reuniones)')
        for (nivel, _), renglon in zip(M.lineas_preorden(self.raiz), renglones):
            self.assertEqual(len(renglon) - len(renglon.lstrip(' ')), 2 * nivel)
        M.completar_por_sala(self.raiz, 'biblioteca')
        renglones = M.texto_arbol(self.raiz).split('\n')
        self.assertTrue(renglones[1].strip().startswith('[x]'))
        self.assertTrue(renglones[2].strip().startswith('[ ]'))
        self.assertEqual(M.texto_arbol(None), '')


if __name__ == '__main__':
    unittest.main()
