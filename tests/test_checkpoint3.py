"""Checkpoint 3: integración de grafo, árbol de misiones y estado del mundo
en la partida. Sin ventana y sin escribir puntajes."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import unittest
import pygame
pygame.init()
pygame.display.set_mode((960, 640))

from main import Partida, crear_mapa_universidad
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


if __name__ == '__main__':
    unittest.main()
