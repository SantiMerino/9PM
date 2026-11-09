"""Vigilante del campus: avisos desde las 20:45, persecución a las 21:00 y captura."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import unittest
from collections import defaultdict

import pygame
pygame.init()
pygame.display.set_mode((960, 640))

import main as M
from main import Partida, crear_mapa_universidad
from mapa_nivel1 import es_caminable, PUERTAS
from estado_mundo import avanzar_tiempo

SIN_TECLAS = defaultdict(bool)


def partida(semilla=3):
    return Partida(crear_mapa_universidad(), {}, semilla=semilla)


def poner_hora(p, minutos):
    """Avanza el reloj de la partida hasta `minutos` desde medianoche."""
    avanzar_tiempo(p.estado_mundo, minutos - p.estado_mundo['hora_actual_min'])


def jugar(p, segundos, dt=1 / 60):
    for _ in range(int(segundos / dt)):
        p.actualizar(dt, SIN_TECLAS)
        if p.terminado:
            break


class TestDialogos(unittest.TestCase):
    def test_callado_antes_de_las_2045(self):
        p = partida()
        jugar(p, 2)
        self.assertEqual(p.dialogo_vigilante, '')

    def test_habla_desde_las_2045(self):
        p = partida()
        poner_hora(p, 20 * 60 + 45)
        jugar(p, 0.1)
        self.assertIn(p.dialogo_vigilante, M.DIALOGOS_VIGILANTE['ronda'])
        self.assertGreater(p.t_dialogo, 0)

    def test_ultimo_aviso_desde_las_2053(self):
        p = partida()
        poner_hora(p, 20 * 60 + 55)
        jugar(p, 0.1)
        self.assertIn(p.dialogo_vigilante, M.DIALOGOS_VIGILANTE['ultimo_aviso'])

    def test_no_repite_la_misma_frase_seguida(self):
        p = partida()
        poner_hora(p, 20 * 60 + 45)
        frases = []
        for _ in range(8):
            p._t_proximo_dialogo = 0
            p._actualizar_dialogos(0.01)
            frases.append(p.dialogo_vigilante)
        self.assertTrue(all(a != b for a, b in zip(frases, frases[1:])))

    def test_dentro_de_una_sala_se_le_oye_en_un_aviso(self):
        p = partida()
        p._aplicar_entrar('lab_siemens')
        poner_hora(p, 20 * 60 + 45)
        jugar(p, 0.1)
        self.assertTrue(any('Se oye al vigilante en el pasillo' in t.texto for t in p.toasts))


class TestPersecucion(unittest.TestCase):
    def test_a_las_21_deja_la_ronda_y_te_persigue(self):
        p = partida()
        self.assertFalse(p.vigilante.persiguiendo)
        poner_hora(p, 21 * 60)
        jugar(p, 0.1)
        self.assertTrue(p.vigilante.persiguiendo)
        self.assertIn(p.dialogo_vigilante, M.DIALOGOS_VIGILANTE['persecucion'])

    def test_se_acerca_al_jugador(self):
        p = partida()
        poner_hora(p, 21 * 60)
        jugar(p, 0.1)
        antes = M.distancia(p.jugador.pos, p.vigilante.pos)
        jugar(p, 2)
        self.assertLess(M.distancia(p.jugador.pos, p.vigilante.pos), antes)

    def test_no_atraviesa_paredes(self):
        p = partida()
        poner_hora(p, 21 * 60)
        for _ in range(60 * 20):
            p.actualizar(1 / 60, SIN_TECLAS)
            if p.capturado or p.terminado:
                break
            self.assertTrue(es_caminable(*p.vigilante.pos), p.vigilante.pos)

    def test_te_atrapa_y_muestra_la_escena(self):
        p = partida()
        poner_hora(p, 21 * 60)
        for _ in range(60 * 60):
            p.actualizar(1 / 60, SIN_TECLAS)
            if p.capturado:
                break
        self.assertTrue(p.capturado)
        self.assertFalse(p.terminado)          # primero la escena...
        self.assertEqual(p.dialogo_vigilante, M.FRASE_CAPTURA)
        jugar(p, M.SEGUNDOS_ESCENA_CAPTURA + 0.2)
        self.assertTrue(p.terminado)           # ...luego la pantalla de fin
        self.assertFalse(p.gano)
        self.assertEqual(p.motivo_fin, M.MOTIVO_CAPTURA)

    def test_durante_la_escena_no_te_puedes_mover(self):
        p = partida()
        p._atrapar()
        antes = p.jugador.pos
        teclas = defaultdict(bool, {pygame.K_RIGHT: True, pygame.K_d: True})
        p.actualizar(0.1, teclas)
        self.assertEqual(p.jugador.pos, antes)

    def test_te_sigue_dentro_de_una_sala(self):
        p = partida()
        p._aplicar_entrar('lab_siemens')
        poner_hora(p, 21 * 60)
        jugar(p, 0.1)
        self.assertTrue(p.vigilante.persiguiendo)
        self.assertEqual(p.vigilante.pos, tuple(p.interior_data['spawn']))
        self.assertTrue(any('entró' in t.texto for t in p.toasts))
        p.jugador.x, p.jugador.y = p.interior_data['spawn'][0], p.interior_data['spawn'][1] - 200
        for _ in range(60 * 30):
            p.actualizar(1 / 60, SIN_TECLAS)
            if p.capturado:
                break
        self.assertTrue(p.capturado)

    def test_entrar_a_una_sala_no_lo_despista(self):
        p = partida()
        poner_hora(p, 21 * 60)
        jugar(p, 0.1)
        p._aplicar_entrar('lab_siemens')
        self.assertEqual(p.vigilante.pos, tuple(p.interior_data['spawn']))
        self.assertGreater(p.vigilante.retraso, 0)
        p._aplicar_salir()
        self.assertEqual(p.vigilante.pos, tuple(PUERTAS['lab_siemens']['retorno']))

    def test_antes_de_las_21_sigue_su_ronda(self):
        p = partida()
        poner_hora(p, 20 * 60 + 58)
        jugar(p, 3)
        self.assertFalse(p.vigilante.persiguiendo)
        self.assertFalse(p.capturado)


if __name__ == '__main__':
    unittest.main()
