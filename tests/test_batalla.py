"""Batalla de argumentos, logros y dificultad."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
pygame.init()
pygame.display.set_mode((960, 640))

import batalla as B
from dificultad import obtener_dificultad
from logros import RegistroLogros
from main import VIGILANTE, Partida, crear_mapa_universidad


def hasta_elegir(b):
    while b.fase == 'mensajes':
        b.continuar()


def indice(b, clave):
    return [o[0] for o in b.opciones()].index(clave)


def mejor_opcion(b):
    """Índice de la excusa más efectiva contra la acusación actual (sin huir)."""
    excusas = b.opciones()[:4]
    return max(range(4), key=lambda i: b.efectividad(excusas[i][2]))


class BatallaTests(unittest.TestCase):
    def test_empieza_con_mensajes_y_luego_toca_elegir(self):
        b = B.Batalla(semilla=1)
        self.assertEqual(b.fase, 'mensajes')
        self.assertIn('te encontró', b.mensaje_actual)
        hasta_elegir(b)
        self.assertEqual(b.fase, 'elegir')
        self.assertEqual(len(b.opciones()), 5)
        self.assertEqual(b.opciones()[-1][0], 'huir')

    def test_excusa_efectiva_baja_mas_la_sospecha(self):
        fuerte, debil = B.Batalla(semilla=2), B.Batalla(semilla=2)
        for b in (fuerte, debil):
            hasta_elegir(b)
        excusas = debil.opciones()[:4]
        peor = min(range(4), key=lambda i: debil.efectividad(excusas[i][2]))
        fuerte.elegir(mejor_opcion(fuerte))
        debil.elegir(peor)
        self.assertLess(fuerte.sospecha, debil.sospecha)
        self.assertGreater(fuerte.credibilidad, debil.credibilidad)

    def test_tabla_de_efectividad_completa(self):
        for acusacion in B.EFECTIVIDAD.values():
            self.assertEqual(set(acusacion), {'academico', 'autoridad', 'calma', 'tecnico', 'evidencia'})
            self.assertIn(2.0, acusacion.values())

    def test_repetir_excusa_rinde_menos(self):
        b = B.Batalla(semilla=5, dificultad='facil')
        hasta_elegir(b)
        b.elegir(0)
        hasta_elegir(b)
        if b.terminada:
            self.skipTest('terminó antes de repetir')
        b.elegir(0)
        self.assertTrue(any('ya me lo dijiste' in m for m in b.mensajes))

    def test_ganar_con_buenas_excusas(self):
        b = B.Batalla(semilla=3, dificultad='facil')
        for _ in range(30):
            hasta_elegir(b)
            if b.terminada:
                break
            b.elegir(mejor_opcion(b))
        while not b.terminada:
            b.continuar()
        self.assertEqual(b.resultado, 'ganaste')

    def test_perder_con_malas_excusas(self):
        b = B.Batalla(semilla=4, dificultad='dificil', toque_queda=True)
        for _ in range(40):
            hasta_elegir(b)
            if b.terminada:
                break
            excusas = b.opciones()[:4]
            b.elegir(min(range(4), key=lambda i: b.efectividad(excusas[i][2])))
        while not b.terminada:
            b.continuar()
        self.assertEqual(b.resultado, 'perdiste')

    def test_prueba_solo_con_objeto_y_una_vez(self):
        sin = B.Batalla(semilla=1)
        hasta_elegir(sin)
        self.assertNotIn('evidencia', [o[0] for o in sin.opciones()])
        con = B.Batalla(semilla=1, inventario=['tarjeta'], dificultad='dificil')
        hasta_elegir(con)
        con.elegir(indice(con, 'evidencia'))
        self.assertTrue(con.evidencia_usada)
        hasta_elegir(con)
        if not con.terminada:
            self.assertNotIn('evidencia', [o[0] for o in con.opciones()])

    def test_huir_termina_o_contraataca(self):
        b = B.Batalla(semilla=9)
        hasta_elegir(b)
        antes = b.credibilidad
        b.elegir(4)
        self.assertTrue(b.resultado == 'huiste' or b.credibilidad < antes)

    def test_entradas_invalidas_no_rompen(self):
        b = B.Batalla(semilla=1)
        self.assertFalse(b.elegir(0))             # todavía hay mensajes
        hasta_elegir(b)
        for malo in (-1, 5, 99, 'abc', None):
            self.assertFalse(b.elegir(malo))
        self.assertEqual(b.fase, 'elegir')
        self.assertEqual(B.Batalla(carrera='no_existe').carrera, 'computacion')

    def test_toque_de_queda_lo_pone_mas_dificil(self):
        self.assertGreater(B.Batalla(toque_queda=True).sospecha_max, B.Batalla().sospecha_max)
        self.assertGreater(obtener_dificultad('dificil')['sospecha'], obtener_dificultad('facil')['sospecha'])
        self.assertEqual(obtener_dificultad('rarísima')['id'], 'normal')


class LogrosTests(unittest.TestCase):
    def test_logro_una_sola_vez_y_cola(self):
        r = RegistroLogros()
        self.assertIsNotNone(r.otorgar('labia_de_oro'))
        self.assertIsNone(r.otorgar('labia_de_oro'))
        self.assertEqual(len(r.cola), 1)
        self.assertEqual(r.puntos(), 50)
        r.actualizar(10)
        self.assertIsNone(r.mostrando)


class PartidaConMejorasTests(unittest.TestCase):
    def setUp(self):
        self.p = Partida(crear_mapa_universidad(), {}, semilla=3)

    def _completar(self, sala):
        m = self.p.encargo_en(sala)
        m.paso = len(m.pasos)
        self.p._completar_encargo(m)

    def test_completar_encargo_da_insignia_y_primer_paso(self):
        self._completar('biblioteca')
        self.assertTrue(self.p.logros.tiene('encargo:biblioteca'))
        self.assertTrue(self.p.logros.tiene('primer_encargo'))
        self.assertEqual(self.p.logros.mostrando['titulo'], self.p.mision_libro.titulo)

    def test_rama_completa(self):
        for sala in ('biblioteca', 'cafeteria', 'bodega', 'lab_spark'):
            self._completar(sala)
        self.assertFalse(self.p.logros.tiene('rama:biblioteca'))   # la raíz de la rama aún tiene pendientes
        for m in self.p.encargos:
            if not m.completada:
                m.paso = len(m.pasos)
                self.p._completar_encargo(m)
        self.assertTrue(self.p.logros.tiene('rama:biblioteca'))
        self.assertTrue(self.p.logros.tiene('todos_encargos'))

    def test_vigilante_en_la_torre_abre_batalla(self):
        p = self.p
        p._aplicar_entrar_torre()
        p._encuentros_ronda = set()
        p.posiciones_torre[VIGILANTE] = p.sala_torre
        p._revisar_encuentros()
        self.assertIsNotNone(p.batalla)
        self.assertFalse(p.terminado)

    def test_ganar_batalla_no_quita_tiempo_y_da_logro(self):
        p = self.p
        p._aplicar_entrar_torre()
        p.iniciar_batalla()
        hora = p.estado_mundo['hora_actual_min']
        p.batalla.resultado, p.batalla.fase = 'ganaste', 'fin'
        p.terminar_batalla()
        self.assertIsNone(p.batalla)
        self.assertEqual(p.estado_mundo['hora_actual_min'], hora)
        self.assertTrue(p.logros.tiene('labia_de_oro'))
        self.assertGreater(p.pausa_vigilante, 0)

    def test_perder_antes_del_toque_cuesta_minutos(self):
        p = self.p
        p._aplicar_entrar_torre()
        p.iniciar_batalla()
        hora = p.estado_mundo['hora_actual_min']
        p.batalla.resultado, p.batalla.fase = 'perdiste', 'fin'
        p.terminar_batalla()
        self.assertFalse(p.terminado)
        self.assertEqual(p.estado_mundo['hora_actual_min'], hora + p.dificultad['minutos_sermon'])

    def test_huir_te_mueve_de_sala(self):
        p = self.p
        p._aplicar_entrar_torre()
        antes = p.sala_torre
        p.iniciar_batalla()
        p.batalla.resultado, p.batalla.fase = 'huiste', 'fin'
        p.terminar_batalla()
        self.assertNotEqual(p.sala_torre, antes)
        self.assertGreater(p.alerta_vigilante, 0)

    def test_controles_de_la_batalla(self):
        p = self.p
        p._aplicar_entrar_torre()
        b = p.iniciar_batalla()
        for _ in range(20):
            if b.fase == 'elegir':
                break
            p.batalla_confirmar()       # primero completa el texto, luego avanza
        self.assertEqual(b.fase, 'elegir')
        p.batalla_mover(1, 0)
        self.assertEqual(p.visual_batalla.seleccion, 1)
        p.batalla_mover(0, 1)
        self.assertEqual(p.visual_batalla.seleccion, 3)
        p.batalla_mover(0, 1)
        self.assertEqual(p.visual_batalla.seleccion, 4)

    def test_dificultad_cambia_el_juego(self):
        facil = Partida(crear_mapa_universidad(), {}, semilla=3, dificultad='facil')
        dificil = Partida(crear_mapa_universidad(), {}, semilla=3, dificultad='dificil')
        self.assertLess(facil.vigilante.vel_persecucion, dificil.vigilante.vel_persecucion)
        self.assertGreater(facil.dificultad['segundos_por_minuto'], dificil.dificultad['segundos_por_minuto'])

    def test_pantallas_nuevas_se_dibujan(self):
        from ui_batalla import dibujar_batalla, dibujar_logro
        s = pygame.Surface((960, 640))
        p = self.p
        p._aplicar_entrar_torre()
        p.iniciar_batalla()
        for _ in range(12):
            p.actualizar(0.3, None)
            dibujar_batalla(s, p, p.visual_batalla)
            p.batalla_confirmar()
            if p.batalla is None:
                break
        self._completar('biblioteca')
        dibujar_logro(s, p.logros.mostrando, 1.0)


if __name__ == '__main__':
    unittest.main()
