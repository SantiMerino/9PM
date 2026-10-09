"""Regresiones de navegación y progreso, sin ventana ni escritura de puntajes."""
import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import unittest
from unittest.mock import patch
from collections import deque
import pygame
pygame.init()
pygame.display.set_mode((960,640))
from mapa_nivel1 import *
from interiores import INTERIORES,colision_interior,interactivo_cercano
from main import Partida,crear_mapa_universidad
from ui_inventario import crear_objeto


def alcanzables(spawn,libre,w,h,step=8):
    # Rejilla con origen en spawn y expansión por cuatro vecinos; prueba pasillos reales.
    start=tuple(map(int,spawn)); visited={start}; q=deque([start])
    while q:
        x,y=q.popleft()
        for p in ((x-step,y),(x+step,y),(x,y-step),(x,y+step)):
            if p not in visited and 0<=p[0]<=w and 0<=p[1]<=h and libre(*p):
                visited.add(p); q.append(p)
    return visited

def terminar_transicion(p):
    from collections import defaultdict
    while p.en_transicion:
        p.actualizar(.3,defaultdict(bool))

class CampusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exterior=alcanzables(SPAWN_LOBBY,es_caminable,MUNDO_ANCHO,MUNDO_ALTO)
    def test_plano(self):
        self.assertEqual(verificar_sin_solapes(),[])
        self.assertLess(SALAS_RECT['r102'][0],SALAS_RECT['r101'][0])
        self.assertLess(SALAS_RECT['biblioteca'][1],SALAS_RECT['sala_reuniones'][1])
        self.assertEqual([k for k in ('lab_siemens','lab_click','lab_spark','lab_kite')],
            sorted(('lab_siemens','lab_click','lab_spark','lab_kite'),key=lambda k:SALAS_RECT[k][1]))
    def test_bucle_menu_mapa_diario_inventario(self):
        import main
        eventos=[[pygame.event.Event(pygame.KEYDOWN,key=k)] for k in
                 (pygame.K_RETURN,pygame.K_RETURN,pygame.K_m,pygame.K_ESCAPE,pygame.K_j,
                  pygame.K_m,pygame.K_ESCAPE,pygame.K_i,pygame.K_ESCAPE)]
        eventos.append([pygame.event.Event(pygame.QUIT)])
        try:
            with patch('pygame.event.get',side_effect=eventos), patch('main.guardar_puntaje') as guardar,                     patch('main.ECO_CONSOLA',False),patch('main.TUTORIAL_AUTOMATICO',False):
                main.main()
                guardar.assert_not_called()
        finally:
            pygame.init(); pygame.display.set_mode((960,640))
    def test_objetos_necesarios_alcanzables(self):
        from main import OBJETOS_MAPA, RADIO_INTERACCION
        for objeto in OBJETOS_MAPA:
            ox,oy=objeto['pos']
            self.assertTrue(any((x-ox)**2+(y-oy)**2<RADIO_INTERACCION**2
                                for x,y in self.exterior),objeto['nombre'])
    def test_gradas_suben_a_la_torre_y_bajan_a_un_punto_libre(self):
        from collections import defaultdict
        from main import POS_PIE_GRADAS
        p=Partida(crear_mapa_universidad(),{})
        p.jugador.x,p.jugador.y=(924,704)
        p.actualizar(.016,defaultdict(bool))
        self.assertTrue(p.en_transicion)
        p.actualizar(.3,defaultdict(bool))
        self.assertEqual(p.ubicacion,'torre')
        self.assertEqual(p.sala_torre,p.torre['raiz'])
        p._aplicar_salir_torre()
        self.assertEqual(p.jugador.pos,POS_PIE_GRADAS)
        self.assertTrue(es_caminable(*p.jugador.pos))
        self.assertFalse(punto_en_rect(*p.jugador.pos,GRADAS_TRIGGER))
    def test_reloj_y_limite_en_interior(self):
        from collections import defaultdict
        from main import SEGUNDOS_POR_MINUTO_JUEGO
        p=Partida(crear_mapa_universidad(),{})
        p._aplicar_entrar('lab_siemens')
        p.actualizar(SEGUNDOS_POR_MINUTO_JUEGO,defaultdict(bool))
        self.assertEqual(p.estado_mundo['hora_actual_min'],20*60+16)
        p.estado_mundo['hora_actual_min']=p.hora_limite
        p.actualizar(.016,defaultdict(bool))
        self.assertTrue(p.terminado)
        self.assertFalse(p.gano)
    def test_todas_las_puertas_y_salidas(self):
        self.assertTrue(es_caminable(*SPAWN_LOBBY))
        for pid,p in PUERTAS.items():
            with self.subTest(puerta=pid):
                self.assertTrue(es_caminable(*p['retorno']),p['retorno'])
                self.assertTrue(any(punto_en_rect(*xy,p['trigger']) for xy in self.exterior))
                self.assertTrue(any(abs(x-p['retorno'][0])<12 and abs(y-p['retorno'][1])<12 for x,y in self.exterior))
        for salida in SALIDAS.values():
            self.assertTrue(any(punto_en_rect(*xy,salida['trigger']) for xy in self.exterior))
    def test_patrulla_no_atraviesa_paredes(self):
        mapa=crear_mapa_universidad()
        for a,vecinos in mapa.grafo.items():
            for b in vecinos:
                ax,ay=mapa.posiciones[a]; bx,by=mapa.posiciones[b]
                for i in range(101):
                    self.assertTrue(es_caminable(ax+(bx-ax)*i/100,ay+(by-ay)*i/100),f'{a} -> {b}, {i}%')
    def test_interiores_y_estaciones(self):
        for nombre,sala in INTERIORES.items():
            with self.subTest(sala=nombre):
                self.assertFalse(colision_interior(sala,*sala['spawn']),'Spawn bloqueado')
                reach=alcanzables(sala['spawn'],lambda x,y:not colision_interior(sala,x,y),sala['ancho'],sala['alto'])
                self.assertTrue(any(punto_en_rect(*p,sala['exit_zone']) for p in reach),'Salida inaccesible')
                for item in sala['interactivos']:
                    self.assertTrue(any(interactivo_cercano(sala,*xy) is item for xy in reach),item['id'])
    def test_cadena_misiones_y_persistencia(self):
        p=Partida(crear_mapa_universidad(),{})
        p.inventario.agregar(crear_objeto('libro'))
        p.inventario.agregar(crear_objeto('usb'))
        for nombre in PUERTAS:
            p._aplicar_entrar(nombre)
            sala=p.interior_data
            reach=alcanzables(sala['spawn'],lambda x,y:not colision_interior(sala,x,y),sala['ancho'],sala['alto'])
            m=next(m for m in p.mision.hijas if m.ubicacion==nombre)
            for paso in range(len(m.pasos)):
                item=next(i for i in p.interior_interactivos if i['paso']==paso)
                spot=next(xy for xy in reach if interactivo_cercano(sala,*xy) is item)
                p.jugador.x,p.jugador.y=spot
                p.interactuar()
                self.assertEqual(m.paso,paso+1,nombre)
            self.assertTrue(m.completada,nombre)
            p._aplicar_salir(); p._aplicar_entrar(nombre)
            self.assertTrue(all(i['usado'] for i in p.interior_interactivos if i['paso'] is not None))
            p._aplicar_salir()
        self.assertFalse(p.inventario.tiene('usb'))
        self.assertFalse(p.inventario.tiene('libro'))
        p.jugador.x,p.jugador.y=(856,952)
        p.interactuar()
        self.assertTrue(p.gano)
    def test_orden_y_requisito_siemens(self):
        p=Partida(crear_mapa_universidad(),{}); p._aplicar_entrar('lab_siemens')
        p.jugador.x,p.jugador.y=(770,144); p.interactuar()
        self.assertEqual(p.mision_lab.paso,0)
        for xy in ((768,472),(328,208)):
            p.jugador.x,p.jugador.y=xy; p.interactuar()
        self.assertEqual(p.mision_lab.paso,2)
        p.jugador.x,p.jugador.y=(770,144); p.interactuar()
        self.assertFalse(p.mision_lab.completada)
        p.inventario.agregar(crear_objeto('usb')); p.interactuar()
        self.assertTrue(p.mision_lab.completada)
        p.interactuar(); self.assertEqual(p.mision_lab.paso,3)
    def test_deshacer_devuelve_a_la_sala_anterior(self):
        from collections import defaultdict
        p=Partida(crear_mapa_universidad(),{})
        p._aplicar_entrar('r101')
        self.assertEqual(p.historial[-1]['tipo'],'mover')
        self.assertTrue(p.deshacer_accion())
        terminar_transicion(p)
        self.assertEqual(p.ubicacion,'pasillo')
        self.assertEqual(p.jugador.pos,PUERTAS['r101']['retorno'])
        self.assertEqual(p.historial,[])
        p._aplicar_entrar('r101'); p._aplicar_salir()
        self.assertTrue(p.deshacer_accion())
        terminar_transicion(p)
        self.assertEqual((p.ubicacion,p.sala_interior),('interior','r101'))
        self.assertEqual(p.jugador.pos,p.interior_data['spawn'])

if __name__=='__main__': unittest.main()
