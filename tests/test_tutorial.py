"""Onboarding: tutorial con focos, progreso guardado y clics en la Torre."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pygame
pygame.init()
pygame.display.set_mode((960, 640))

import main
from main import Partida as PartidaReal
import ui_torre
from tutorial import Tutorial, PASOS, ILUSTRACIONES, cargar_progreso, guardar_progreso


def tecla(k, u=''):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode=u)


def partida_en_torre():
    p = main.Partida(main.crear_mapa_universidad(), {}, semilla=1)
    p._aplicar_entrar_torre()
    return p


class TutorialTests(unittest.TestCase):
    def test_navegacion_con_teclado_y_raton(self):
        t = Tutorial()
        self.assertFalse(t.manejar_evento(tecla(pygame.K_RETURN)))
        t.iniciar('campus')
        self.assertTrue(t.manejar_evento(tecla(pygame.K_RETURN)))
        self.assertEqual(t.indice, 1)
        t.manejar_evento(tecla(pygame.K_LEFT))
        t.manejar_evento(tecla(pygame.K_LEFT))
        self.assertEqual(t.indice, 0)
        self.assertTrue(t.manejar_evento(tecla(pygame.K_q)))  # se consume, no pasa al juego
        for _ in range(len(PASOS['campus']) - 1):
            self.assertTrue(t.manejar_evento(tecla(pygame.K_SPACE)))
        self.assertEqual(t.manejar_evento(tecla(pygame.K_RETURN)), 'fin')
        self.assertFalse(t.activo)
        t.iniciar('torre')
        self.assertEqual(t.manejar_evento(tecla(pygame.K_ESCAPE)), 'fin')

    def test_todos_los_pasos_se_dibujan_y_sus_focos_caben(self):
        pantalla = pygame.Surface((960, 640))
        campus = main.Partida(main.crear_mapa_universidad(), {}, semilla=1)
        torre = partida_en_torre()
        camara = main.calcular_camara(campus.jugador.pos)
        for contexto, p, cam in (('campus', campus, camara), ('torre', torre, (0, 0))):
            t = Tutorial()
            t.iniciar(contexto)
            for i, paso in enumerate(PASOS[contexto]):
                with self.subTest(contexto=contexto, paso=i):
                    self.assertIn(paso['dibujo'], ILUSTRACIONES)
                    t.indice = i
                    for tiempo in (0.0, 0.7, 2.3):
                        t.dibujar(pantalla, p, cam, tiempo)
                    foco = t.foco_actual(p, cam)
                    if 'foco' in paso:
                        self.assertIsNotNone(foco)
                        self.assertTrue(pantalla.get_rect().contains(foco), foco)
            # El botón Saltar del primer paso termina el recorrido.
            t.indice = 0
            t.dibujar(pantalla, p, cam, 0)
            clic = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=t._botones['saltar'].center)
            self.assertEqual(t.manejar_evento(clic), 'fin')

    def test_progreso_se_guarda_y_tolera_archivos_danados(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'tutorial.json'
            self.assertEqual(cargar_progreso(ruta), {})
            guardar_progreso(ruta, {'campus': True})
            self.assertEqual(cargar_progreso(ruta), {'campus': True})
            ruta.write_text('{roto', encoding='utf-8')
            self.assertEqual(cargar_progreso(ruta), {})

    def test_primera_partida_muestra_el_tutorial_y_luego_no(self):
        instancias = []

        def crear(*args, **kwargs):
            p = PartidaReal(*args, **kwargs)
            instancias.append(p)
            return p
        enter = tecla(pygame.K_RETURN, '\r')
        # Carrera 2 (Industrial): su herramienta funciona en cualquier lugar.
        teclas = [enter, tecla(pygame.K_2, '2'), enter, tecla(pygame.K_q, 'q'),
                  tecla(pygame.K_ESCAPE, '\x1b'), tecla(pygame.K_q, 'q')]
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'tutorial.json'
            eventos = [[e] for e in teclas] + [[pygame.event.Event(pygame.QUIT)]]
            try:
                with patch('pygame.event.get', side_effect=eventos), patch('main.Partida', side_effect=crear), \
                        patch('main.guardar_puntaje'), patch('main.ECO_CONSOLA', False), \
                        patch('main.ARCHIVO_TUTORIAL', ruta):
                    main.main()
            finally:
                pygame.init(); pygame.display.set_mode((960, 640))
            self.assertEqual(json.loads(ruta.read_text(encoding='utf-8')), {'campus': True})
        # La primera Q la consumió el tutorial; la segunda ya usó la herramienta.
        self.assertGreater(instancias[0].habilidad.recarga, 0)

    def test_la_torre_lanza_su_tutorial_y_f1_lo_repite(self):
        def crear(*args, **kwargs):
            p = PartidaReal(*args, **kwargs)
            p._aplicar_entrar_torre()
            return p
        enter = tecla(pygame.K_RETURN, '\r')
        teclas = [enter, enter, tecla(pygame.K_ESCAPE, '\x1b'), tecla(pygame.K_F1), tecla(pygame.K_ESCAPE, '\x1b')]
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'tutorial.json'
            guardar_progreso(ruta, {'campus': True})
            eventos = [[e] for e in teclas] + [[pygame.event.Event(pygame.QUIT)]]
            try:
                with patch('pygame.event.get', side_effect=eventos), patch('main.Partida', side_effect=crear), \
                        patch('main.guardar_puntaje'), patch('main.ECO_CONSOLA', False), \
                        patch('main.ARCHIVO_TUTORIAL', ruta):
                    main.main()
            finally:
                pygame.init(); pygame.display.set_mode((960, 640))
            self.assertEqual(cargar_progreso(ruta), {'campus': True, 'torre': True})


class ClicsTorreTests(unittest.TestCase):
    def test_clic_en_puerta_mueve_y_en_barra_abre_paneles(self):
        p = partida_en_torre()
        numero, destino, rect, tipo = ui_torre.puertas_escena(p)[0]
        self.assertEqual(tipo, 'hija')
        self.assertEqual(ui_torre.objetivo_clic(p, rect.center), ('puerta', numero))
        p.torre_ir_a_puerta(numero)
        self.assertEqual(p.sala_torre, destino)
        self.assertEqual(p.historial[-1]['tipo'], 'mover')
        regreso = next(r for _, _, r, t in ui_torre.puertas_escena(p) if t == 'padre')
        self.assertEqual(ui_torre.objetivo_clic(p, regreso.center)[0], 'puerta')
        _, boton = ui_torre.rects_barra()[5]
        self.assertEqual(ui_torre.objetivo_clic(p, boton.center), ('accion', 6))
        p.torre_accion(6)
        self.assertEqual(p.panel_activo, 'historial')
        p.panel_activo = None
        # Desde un submenú, el clic en una puerta cancela y se mueve igual.
        p.torre_enviar('5')
        self.assertEqual(p.menu_torre, 'deshacer_varias')
        fila = ui_torre.rects_submenu(p)[0][1]
        self.assertEqual(ui_torre.objetivo_clic(p, fila.center), ('submenu', 1))
        p.torre_ir_a_puerta(regreso and next(n for n, _, _, t in ui_torre.puertas_escena(p) if t == 'padre'))
        self.assertEqual(p.sala_torre, p.torre['raiz'])
        gradas = next((n, r) for n, _, r, t in ui_torre.puertas_escena(p) if t == 'gradas')
        self.assertEqual(ui_torre.objetivo_clic(p, gradas[1].center), ('puerta', gradas[0]))
        p.torre_ir_a_puerta(gradas[0])
        self.assertTrue(p.en_transicion)


if __name__ == '__main__':
    unittest.main()
