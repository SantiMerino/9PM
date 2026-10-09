"""Checkpoint 2: pila (historial), colas (eventos y turnos), mazmorra recursiva
y su integración en la partida. Sin ventana y sin escribir puntajes."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import re
import unittest
from collections import deque, defaultdict
from unittest.mock import patch
import pygame
pygame.init()
pygame.display.set_mode((960, 640))

import historial as H
import eventos as E
import mazmorra as M
from main import Partida, crear_mapa_universidad, leer_numero, PASILLO
from ui_inventario import crear_objeto, es_tesoro
from mapa_nivel1 import PUERTAS


def accion(tipo, texto='x'):
    return H.crear_accion(tipo, texto)


def partida(semilla=3):
    return Partida(crear_mapa_universidad(), {}, semilla=semilla)


def terminar_transicion(p):
    while p.en_transicion:
        p.actualizar(.3, defaultdict(bool))


def en_torre(semilla=3):
    p = partida(semilla)
    p._aplicar_entrar_torre()
    return p


class HistorialTests(unittest.TestCase):
    def test_pila_lifo_peek_y_vacio(self):
        pila = []
        self.assertIsNone(H.deshacer_ultima_accion(pila))
        self.assertIsNone(H.consultar_ultima_accion(pila))
        for t in ('mover', 'recoger', 'soltar'):
            H.apilar_accion(pila, accion(t))
        self.assertEqual(H.consultar_ultima_accion(pila)['tipo'], 'soltar')
        self.assertEqual(len(pila), 3)  # peek no saca
        self.assertEqual(H.deshacer_ultima_accion(pila)['tipo'], 'soltar')
        self.assertEqual(H.deshacer_ultima_accion(pila)['tipo'], 'recoger')
        self.assertEqual([a['tipo'] for a in pila], ['mover'])

    def test_mostrar_de_reciente_a_antigua(self):
        pila = [accion('mover', 'A'), accion('recoger', 'B'), accion('usar', 'C')]
        lineas = H.mostrar_historial(pila)
        self.assertTrue(lineas[0].startswith('1. Usar: C'))
        self.assertTrue(lineas[-1].startswith('3. Mover: A'))
        self.assertEqual(len(pila), 3)
        self.assertIn('vacío', H.mostrar_historial([])[0])

    def test_funciones_guia5(self):
        pila = [accion('mover'), accion('recoger'), accion('mover'), accion('soltar')]
        self.assertEqual(H.contar_acciones_de_tipo(pila, 'mover'), 2)
        self.assertEqual([a['tipo'] for a in H.invertir_historial(pila)], ['soltar', 'mover', 'recoger', 'mover'])
        self.assertEqual(len(pila), 4)
        sacadas = H.deshacer_hasta_tipo(pila, 'mover')
        self.assertEqual([a['tipo'] for a in sacadas], ['soltar', 'mover'])
        self.assertEqual(H.deshacer_hasta_tipo(pila, 'usar'), [])
        self.assertEqual(len(pila), 2)
        self.assertEqual(len(H.deshacer_multiples(pila, 10)), 2)
        self.assertEqual(pila, [])
        self.assertEqual(H.deshacer_multiples(pila, 3), [])


class ColasTests(unittest.TestCase):
    def test_cola_fifo_y_vacia(self):
        cola = deque()
        for i in range(3):
            E.encolar_evento(cola, {'tipo': 'mensaje', 'id': i})
        self.assertEqual(E.ver_siguiente_evento(cola)['id'], 0)
        self.assertEqual([E.procesar_siguiente_evento(cola)['id'] for _ in range(3)], [0, 1, 2])
        self.assertIsNone(E.procesar_siguiente_evento(cola))
        self.assertIsNone(E.ver_siguiente_evento(cola))

    def test_funciones_guia6(self):
        cola = E.crear_cola_eventos_torre()
        self.assertEqual(len(cola), len(E.EVENTOS_TORRE))
        antes = list(cola)
        self.assertEqual(E.contar_eventos_de_tipo(cola, 'trampa'), 3)
        self.assertEqual(list(cola), antes)
        E.invertir_cola(cola)
        self.assertEqual(list(cola), antes[::-1])
        self.assertEqual(len(E.procesar_multiples_eventos(cola, 5)), 5)
        self.assertEqual(len(E.procesar_multiples_eventos(cola, 50)), len(antes) - 5)
        self.assertEqual(E.procesar_multiples_eventos(cola, 2), [])

    def test_turnos_rotan_con_tres_participantes(self):
        turnos = E.crear_turnos()
        self.assertEqual(len(turnos), 3)
        orden = [E.siguiente_turno(turnos) for _ in range(5)]
        self.assertEqual(orden, [E.ESTUDIANTE, E.VIGILANTE, E.ROBOT, E.ESTUDIANTE, E.VIGILANTE])
        self.assertEqual(E.ver_turno_actual(turnos), E.ROBOT)
        copia = list(turnos)
        self.assertEqual(E.simular_turnos(copia, 4)[3], f'Turno 4: le toca a {copia[0]}')
        self.assertEqual(list(turnos), copia)
        self.assertEqual(E.ronda_completa(turnos), copia)
        self.assertIsNone(E.siguiente_turno(deque()))
        self.assertEqual(E.simular_turnos([], 3), [])

    def test_avisos_del_reloj(self):
        cola = E.ColaEventos()
        for t in (10, 20, 30):
            cola.programar(E.Evento(t, 'aviso'))
        self.assertEqual([e.tiempo_disparo_min for e in cola.eventos_listos(20)], [10, 20])
        self.assertEqual(len(cola), 1)


class MazmorraTests(unittest.TestCase):
    def test_requisitos_en_muchas_semillas(self):
        todos = {n for nombres in M.NOMBRES_POR_NIVEL.values() for n in nombres} | {M.NOMBRE_RAIZ}
        for semilla in range(300):
            m = M.generar_mazmorra(semilla)
            with self.subTest(semilla=semilla):
                self.assertGreaterEqual(len(m['salas']), 7)
                self.assertGreaterEqual(m['profundidad_real'], 2)
                self.assertEqual(len(set(m['salas'])), len(m['salas']))
                self.assertTrue(set(m['salas']) <= todos)
                self.assertFalse(any(re.fullmatch(r'[\d.]+', s) for s in m['salas']))
                self.assertEqual(len(m['conexiones']), len(m['salas']) - 1)
                self.assertEqual(sum(m['por_nivel'].values()), len(m['salas']))
                self.assertEqual(M.calcular_profundidad_real(m['raiz'], 0, m['hijos']), m['profundidad_real'])
                self.assertTrue(all(m['niveles'][s] == m['profundidad_real'] for s in m['profundas']))
                self.assertEqual(set(m['objetos']), set(m['profundas']))
                self.assertTrue(all(es_tesoro(o) for o in m['objetos'].values()))
                self.assertEqual(len(M.dibujar_arbol(m['raiz'], m['hijos'])), len(m['salas']))

    def test_caso_base_y_semilla(self):
        import random
        salas, conexiones = [], []
        nombres = {n: list(v) for n, v in M.NOMBRES_POR_NIVEL.items()}
        alcanzada = M.generar_salas('Rellano', 0, 0, conexiones, salas, {}, nombres, random.Random(1))
        self.assertEqual((salas, conexiones, alcanzada), (['Rellano'], [], 0))
        self.assertEqual(M.generar_mazmorra(5), M.generar_mazmorra(5))

    def test_navegacion_del_arbol(self):
        m = M.generar_mazmorra(11)
        hoja = m['profundas'][0]
        camino = M.camino_desde_raiz(m['raiz'], hoja, m['hijos'])
        self.assertEqual(camino[0], m['raiz'])
        self.assertEqual(M.paso_hacia(m, m['raiz'], hoja), camino[1])
        self.assertEqual(M.paso_hacia(m, hoja, m['raiz']), m['padres'][hoja])
        self.assertTrue(M.estan_conectadas(m, m['raiz'], camino[1]))
        self.assertFalse(M.estan_conectadas(m, m['raiz'], hoja))
        self.assertEqual(M.buscar_sala(m, 'RELLANO DEL SEGUNDO NIVEL'), m['raiz'])
        self.assertIsNone(M.buscar_sala(m, 'Sala inventada'))
        self.assertEqual(M.salas_conectadas(m, 'no existe'), [])


class IntegracionTests(unittest.TestCase):
    def test_inicio_genera_mazmorra_y_encola_eventos(self):
        p = partida()
        self.assertGreaterEqual(len(p.torre['salas']), 7)
        self.assertEqual(len(p.eventos_torre), len(E.EVENTOS_TORRE))
        self.assertEqual(list(p.turnos), list(E.PARTICIPANTES_TORRE))
        self.assertTrue(any('Mazmorra generada' in l for l in p.consola))
        self.assertFalse(p.deshacer_accion())
        self.assertIn('historial está vacío', p.consola[-1])

    def test_mover_registra_procesa_evento_y_juega_ronda(self):
        p = en_torre()
        hora, eventos = p.estado_mundo['hora_actual_min'], len(p.eventos_torre)
        destino = p.torre['hijos'][p.torre['raiz']][0]
        p.torre_enviar('1'); p.torre_enviar('1')
        self.assertEqual(p.sala_torre, destino)
        self.assertEqual(p.historial[-1]['tipo'], 'mover')
        self.assertEqual((p.historial[-1]['desde'], p.historial[-1]['hacia']), (p.torre['raiz'], destino))
        self.assertEqual(len(p.eventos_torre), eventos - 1)
        self.assertEqual(p.rondas_jugadas, 1)
        self.assertEqual(list(p.turnos), list(E.PARTICIPANTES_TORRE))
        self.assertGreater(p.estado_mundo['hora_actual_min'], hora)
        self.assertTrue(any('Turno de Robot' in l for l in p.consola))

    def test_deshacer_vuelve_a_la_sala_anterior_y_el_evento_se_pierde(self):
        p = en_torre()
        origen = p.sala_torre
        p.torre_enviar('1'); p.torre_enviar('1')
        eventos = len(p.eventos_torre)
        p.torre_enviar('4')
        self.assertEqual(p.sala_torre, origen)
        self.assertEqual(len(p.eventos_torre), eventos)
        self.assertEqual(p.rondas_jugadas, 2)
        self.assertEqual(len(p.historial), 1)
        p.torre_enviar('4')  # deshace la subida por las gradas
        terminar_transicion(p)
        self.assertEqual(p.ubicacion, 'pasillo')

    def test_opciones_invalidas_no_rompen_ningun_menu(self):
        p = en_torre()
        pila = len(p.historial)
        for texto in ('abc', '0', '-1', '99', '', '  ', '3.5'):
            p.torre_enviar(texto)
            self.assertEqual(p.menu_torre, 'principal')
        p.torre_enviar('1')
        for texto in ('0', '-3', '99', 'Sala inventada'):
            p.torre_enviar(texto)
            self.assertEqual(p.menu_torre, 'mover')
        self.assertEqual(len(p.historial), pila)
        lejana = next(s for s in p.torre['salas'] if p.torre['niveles'][s] >= 2)
        p.torre_enviar(lejana)
        self.assertEqual(p.sala_torre, p.torre['raiz'])
        self.assertIn('no están conectadas', p.consola[-1])
        self.assertFalse(p.mover_en_torre('Sótano que no existe'))
        for numero, error in ((5, None), (0, '0 no es'), (-2, 'negativo'), (12, 'fuera de rango')):
            self.assertEqual(leer_numero(str(numero), 1, 9)[0] is None, error is not None)
        self.assertIn('no es un número', leer_numero('hola', 1, 9)[1])

    def test_cola_vacia_al_moverse(self):
        p = en_torre()
        E.procesar_multiples_eventos(p.eventos_torre, 100)
        p.torre_enviar('1'); p.torre_enviar('1')
        self.assertTrue(any('cola de eventos de este piso está vacía' in l for l in p.consola))
        p.torre_enviar('8')
        self.assertFalse(p.terminado)

    def test_sala_marcada_entrega_objeto_al_inventario(self):
        p = en_torre()
        p.posiciones_torre[E.VIGILANTE] = p.posiciones_torre[E.ROBOT] = p.torre['raiz']
        p.pausa_vigilante = 99
        objetivo = p.torre['profundas'][0]
        for sala in M.camino_desde_raiz(p.torre['raiz'], objetivo, p.torre['hijos'])[1:]:
            self.assertTrue(p.mover_en_torre(sala))
        tesoro = p.torre['objetos'][objetivo]
        p.torre_enviar('2')
        self.assertTrue(p.inventario.tiene(tesoro))
        self.assertEqual(p.historial[-1]['tipo'], 'recoger')
        self.assertEqual(p.tesoros_en_mochila(), 1)
        self.assertGreaterEqual(p.calcular_puntaje()['puntos'], 150)
        p.torre_enviar('2')
        self.assertIn('No hay nada que recoger', p.consola[-1])
        p.torre_enviar('4')
        self.assertFalse(p.inventario.tiene(tesoro))
        self.assertEqual(p.objetos_torre[objetivo], [tesoro])
        # Soltar y deshacer el soltar.
        p.torre_enviar('2'); p.torre_enviar('3'); p.torre_enviar('1')
        self.assertEqual(p.objetos_torre[objetivo], [tesoro])
        self.assertEqual(p.historial[-1]['tipo'], 'soltar')
        p.deshacer_accion()
        self.assertTrue(p.inventario.tiene(tesoro))
        # Deshacer varias regresa por el mismo camino.
        p.torre_enviar('5'); p.torre_enviar('99')
        self.assertEqual(p.menu_torre, 'deshacer_varias')
        disponibles = p.acciones_deshacibles_en_torre()
        p.torre_enviar(str(disponibles))
        self.assertEqual(p.sala_torre, p.torre['raiz'])

    def test_mochila_llena_y_vigilante_tras_toque_de_queda(self):
        p = en_torre()
        while not p.inventario.esta_lleno():
            p.inventario.agregar(crear_objeto('cafe'))
        sala = p.torre['profundas'][0]
        p.sala_torre = sala
        p.posiciones_torre[E.VIGILANTE] = p.posiciones_torre[E.ROBOT] = p.torre['raiz']
        p.torre_enviar('2')
        self.assertIn('mochila está llena', p.consola[-1])
        p.estado_mundo['toque_queda_activo'] = True
        p.posiciones_torre[E.VIGILANTE] = sala
        p._revisar_encuentros()
        self.assertTrue(p.terminado)
        self.assertFalse(p.gano)

    def test_acciones_del_campus_quedan_en_el_historial(self):
        p = partida()
        libro = next(o for o in p.objetos_mundo if o['nombre'] == 'libro')
        p.jugador.x, p.jugador.y = libro['pos']
        p.interactuar()
        self.assertEqual(p.historial[-1]['tipo'], 'recoger')
        p.soltar_objeto()
        self.assertEqual(p.historial[-1]['tipo'], 'soltar')
        p.deshacer_accion()
        self.assertTrue(p.inventario.tiene('libro'))
        p.deshacer_accion()
        self.assertFalse(p.inventario.tiene('libro'))
        self.assertFalse(libro['recogido'])
        # Usar el libro en la biblioteca y deshacerlo.
        p.inventario.agregar(crear_objeto('libro'))
        p._aplicar_entrar('biblioteca')
        estacion = next(i for i in p.interior_interactivos if i.get('requiere') == 'libro')
        p.jugador.x, p.jugador.y = estacion['pos']
        self.assertTrue(p.resolver_estacion(estacion))
        self.assertTrue(p.mision_libro.completada)
        self.assertEqual(p.historial[-1]['tipo'], 'usar')
        p.deshacer_accion()
        self.assertFalse(p.mision_libro.completada)
        self.assertTrue(p.inventario.tiene('libro'))
        self.assertEqual(p.lugar_actual(), 'biblioteca')
        self.assertEqual(p.historial[-1]['hacia'], 'biblioteca')

    def test_bucle_principal_con_teclado_en_la_torre(self):
        import main
        instancias = []

        def crear(*args, **kwargs):
            p = Partida(*args, **kwargs)
            p._aplicar_entrar_torre()
            instancias.append(p)
            return p

        def escribir(caracter, key):
            return pygame.event.Event(pygame.KEYDOWN, key=key, unicode=caracter)
        enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode='\r')
        teclas = [enter, enter,                                    # portada -> jugar
                  escribir('x', pygame.K_x), enter,                # texto inválido
                  escribir('1', pygame.K_1), enter,                # moverse
                  escribir('1', pygame.K_1), enter,                # primera sala
                  escribir('6', pygame.K_6), enter,                # historial
                  pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode='\x1b'),
                  escribir('9', pygame.K_9), enter,                # inventario
                  pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode='\x1b')]
        eventos = [[t] for t in teclas] + [[pygame.event.Event(pygame.QUIT)]]
        try:
            with patch('pygame.event.get', side_effect=eventos), patch('main.Partida', side_effect=crear), \
                    patch('main.guardar_puntaje'), patch('main.ECO_CONSOLA', False), patch('main.TUTORIAL_AUTOMATICO', False):
                main.main()
        finally:
            pygame.init(); pygame.display.set_mode((960, 640))
        p = instancias[0]
        self.assertNotEqual(p.sala_torre, p.torre['raiz'])
        self.assertEqual(len(p.historial), 2)
        self.assertTrue(any('no es un número' in l for l in p.consola))
        self.assertTrue(any('Historial (' in l for l in p.consola))

    def test_pantallas_de_la_torre_se_dibujan(self):
        import main
        p = en_torre()
        s = pygame.Surface((960, 640))
        for menu in ('principal', 'mover', 'deshacer_varias'):
            if menu == 'mover':
                p.torre_enviar('1')
            p.menu_torre = menu
            main.dibujar_torre(s, p, 0.5, (500, 260))
        for dibujar in (main.dibujar_panel_historial, main.dibujar_panel_turnos, main.dibujar_panel_eventos):
            dibujar(s, p)
        q = partida()
        main.dibujar_panel_historial(s, q)


if __name__ == '__main__':
    unittest.main()
