"""Checkpoint 3: integración de grafo, árbol de misiones y estado del mundo
en la partida. Sin ventana y sin escribir puntajes."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import unittest
import pygame
pygame.init()
pygame.display.set_mode((960, 640))

from main import OPCIONES_TORRE, Partida, crear_mapa_universidad, leer_numero
from estado_mundo import PUERTA_LOBBY, PUERTA_TERRAZA, avanzar_tiempo, consultar, puertas_cerradas
from misiones import recompensa_rama
from mapa_nivel1 import PUERTAS


def partida(semilla=3):
    return Partida(crear_mapa_universidad(), {}, semilla=semilla)


class EncargosTests(unittest.TestCase):
    """La partida consulta los encargos por sala con un diccionario, sin
    depender de la forma interna de la misión principal."""

    def setUp(self):
        self.p = partida()

    def test_hay_un_encargo_por_sala_con_puerta(self):
        self.assertEqual(len(self.p.encargos), 13)
        self.assertEqual(set(self.p.encargo_por_sala), set(PUERTAS))

    def test_encargo_en_sala_existente(self):
        m = self.p.encargo_en('lab_siemens')
        self.assertIs(m, self.p.mision_lab)
        self.assertEqual(m.ubicacion, 'lab_siemens')

    def test_encargo_en_sala_inexistente_no_lanza_error(self):
        self.assertIsNone(self.p.encargo_en('sala_que_no_existe'))
        self.assertIsNone(self.p.encargo_en(None))
        self.assertIsNone(self.p.encargo_en(''))

    def test_conteo_y_completos(self):
        self.assertEqual(self.p.encargos_hechos(), 0)
        self.assertFalse(self.p.encargos_completos())
        self.p.mision_libro.completar()
        self.assertEqual(self.p.encargos_hechos(), 1)
        for m in self.p.encargos:
            m.completar()
        self.assertTrue(self.p.encargos_completos())

    def test_puntaje_usa_los_encargos_hechos(self):
        antes = self.p.calcular_puntaje()
        self.p.mision_profesor.completar()
        despues = self.p.calcular_puntaje()
        self.assertGreater(despues['puntos'], antes['puntos'])

    def test_deshacer_uso_en_sala_sin_encargo_no_rompe(self):
        accion = {'tipo': 'usar', 'texto': 'x', 'hora': '', 'sala': 'no_existe',
                  'paso': 0, 'objeto': 'libro', 'estacion': {'usado': True}}
        self.assertFalse(self.p._revertir(accion))  # no debe lanzar excepción
        self.assertIn('no tiene encargo', self.p.consola[-1])


class IntegracionTests(unittest.TestCase):
    """Árbol -> diccionario -> grafo dentro de la partida."""

    def setUp(self):
        self.p = partida()

    def _completar(self, sala):
        m = self.p.encargo_en(sala)
        m.paso = len(m.pasos)
        return self.p._completar_encargo(m)

    def test_al_inicio_solo_la_biblioteca_esta_disponible(self):
        mundo = self.p.estado_mundo['misiones']
        self.assertEqual([s for s, v in mundo.items() if v == 'disponible'], ['biblioteca'])
        self.assertEqual(len(mundo), 13)

    def test_estacion_bloqueada_no_avanza(self):
        self.p._aplicar_entrar('lab_siemens')
        self.p.jugador.x, self.p.jugador.y = (768, 472)
        self.p.interactuar()
        self.assertEqual(self.p.mision_lab.paso, 0)
        self.assertTrue(any('Bloqueada: primero completa' in t for t in self.p.consola[-3:]))

    def test_completar_desbloquea_hijas_en_el_diccionario(self):
        self._completar('biblioteca')
        mundo = self.p.estado_mundo['misiones']
        self.assertEqual(mundo['biblioteca'], 'completada')
        for sala in ('sala_reuniones', 'r101', 'cafeteria'):
            self.assertEqual(mundo[sala], 'disponible')
        self.assertFalse(consultar(self.p.estado_mundo, 'luces', 'biblioteca'))  # efecto: apaga

    def test_cierre_de_caja_abre_la_terraza_para_el_bfs(self):
        mapa = self.p.mapa
        self.assertIsNone(mapa.bfs_ruta('terraza', 'terraza_n', puertas_cerradas(self.p.estado_mundo)))
        self._completar('biblioteca')
        self._completar('cafeteria')
        self.assertNotIn(PUERTA_TERRAZA, puertas_cerradas(self.p.estado_mundo))
        self.assertEqual(mapa.bfs_ruta('terraza', 'terraza_n', puertas_cerradas(self.p.estado_mundo)),
                         ['terraza', 'terraza_n'])

    def test_deshacer_vuelve_a_cerrar_la_terraza(self):
        self._completar('biblioteca')
        m = self.p.encargo_en('cafeteria')
        cambios = self._completar('cafeteria')
        accion = {'tipo': 'usar', 'texto': 'x', 'hora': '', 'sala': 'cafeteria',
                  'paso': len(m.pasos) - 1, 'objeto': 'libro', 'estacion': {'usado': True},
                  'cambios': cambios}
        hora = self.p.estado_mundo['hora_actual_min']
        self.assertTrue(self.p._revertir(accion))
        self.assertIn(PUERTA_TERRAZA, puertas_cerradas(self.p.estado_mundo))
        self.assertEqual(self.p.estado_mundo['misiones']['cafeteria'], 'disponible')
        self.assertEqual(self.p.estado_mundo['hora_actual_min'], hora)   # la hora no se deshace

    def test_toque_de_queda_sin_terraza_no_hay_salida(self):
        self.p._avanzar_minutos(45)
        self.assertIn(PUERTA_LOBBY, puertas_cerradas(self.p.estado_mundo))
        self.assertEqual(self.p.ruta_a_salida(), (None, None))
        self.assertTrue(any('No hay salida abierta' in t for t in self.p.consola[-4:]))
        self.assertFalse(self.p.salida_abierta('lobby_sur'))

    def test_toque_de_queda_con_terraza_da_ruta_alternativa(self):
        self._completar('biblioteca')
        self._completar('cafeteria')
        self.p.jugador.x, self.p.jugador.y = self.p.mapa.posiciones['jardin_c']
        self.p._avanzar_minutos(45)
        ruta, destino = self.p.ruta_a_salida()
        self.assertEqual(ruta[0], 'jardin_c')
        self.assertEqual(destino, 'terraza_n')
        self.assertNotIn(('lobby', 'lobby_frente'), list(zip(ruta, ruta[1:])))

    def test_salida_cerrada_no_termina_la_partida(self):
        for m in self.p.encargos:
            m.completar()
        self.p._avanzar_minutos(45)          # cierra el lobby
        self.p.jugador.x, self.p.jugador.y = (856, 952)
        self.p.interactuar()
        self.assertFalse(self.p.terminado)
        self.assertTrue(any('la puerta está cerrada' in t for t in self.p.consola[-4:]))

    def test_completar_dos_veces_no_duplica_la_recompensa(self):
        self._completar('biblioteca')
        antes = recompensa_rama(self.p.mision)
        self.p.encargo_en('biblioteca').completar()
        self.assertEqual(recompensa_rama(self.p.mision), antes)
        self.assertGreater(antes, 0)


class TorreGrafoTests(unittest.TestCase):
    def setUp(self):
        self.p = partida()
        self.p._aplicar_entrar_torre()

    def test_torre_tiene_atajos_del_mismo_nivel(self):
        g, torre = self.p.grafo_torre, self.p.torre
        self.assertEqual(len(g.atajos), 2)
        for a, b in g.atajos:
            self.assertEqual(torre['niveles'][a], torre['niveles'][b])

    def test_moverse_por_un_atajo(self):
        a, b = self.p.grafo_torre.atajos[0]
        self.p.sala_torre = a
        self.assertTrue(self.p.mover_en_torre(b))
        self.assertEqual(self.p.sala_torre, b)

    def test_ruta_a_una_sala(self):
        destino = self.p.torre['salas'][-1]
        ruta = self.p._opcion_ruta(destino)
        self.assertEqual(ruta[0], self.p.sala_torre)
        self.assertEqual(ruta[-1], destino)

    def test_ruta_a_sala_inexistente_o_vacia(self):
        self.assertIsNone(self.p._opcion_ruta('sala que no existe'))
        self.assertIn('no existe', self.p.consola[-1])
        self.assertIsNone(self.p._opcion_ruta(''))
        self.p.torre_enviar('10')
        self.assertEqual(self.p.menu_torre, 'ruta')
        self.p.torre_enviar('zzz')
        self.assertEqual(self.p.menu_torre, 'ruta')

    def test_menu_con_entradas_invalidas(self):
        self.assertEqual(OPCIONES_TORRE[-1], 'Ruta a una sala')
        for texto in ('abc', '0', '-3', '99', ''):
            numero, error = leer_numero(texto, 1, len(OPCIONES_TORRE))
            self.assertIsNone(numero, texto)
            self.assertTrue(error, texto)
            self.p.torre_enviar(texto)        # nunca lanza excepción
        self.assertEqual(self.p.menu_torre, 'principal')


if __name__ == '__main__':
    unittest.main()
