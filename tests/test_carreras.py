"""Carreras, herramientas y selección independiente de los ocho estudiantes."""
import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
from collections import defaultdict
import unittest
from unittest.mock import patch
import pygame
from carreras import CARRERAS
from main import Partida,crear_mapa_universidad
from menu_inicio import PantallaInicio
from sprites_jugador import PERSONAJES,sprite_estudiante
from ui_inventario import crear_objeto
from interiores import colision_interior,interactivo_cercano
from test_campus import alcanzables


def tecla(k): return pygame.event.Event(pygame.KEYDOWN,key=k)
def clic(pos): return pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos)

class CarreraTests(unittest.TestCase):
    def setUp(self):
        pygame.init(); pygame.display.set_mode((960,640))
    def partida(self,carrera): return Partida(crear_mapa_universidad(),{},carrera=carrera)

    def test_ocho_combinaciones_en_selector_y_partida(self):
        for i,carrera in enumerate(CARRERAS):
            for j,avatar in enumerate(PERSONAJES):
                with self.subTest(carrera=carrera.id,avatar=avatar):
                    inicio=PantallaInicio(); inicio.manejar_evento(tecla(pygame.K_RETURN))
                    self.assertEqual(inicio.vista,'crear')
                    inicio.manejar_evento(clic(inicio.tarjetas()[i].center))
                    inicio.manejar_evento(clic(inicio.botones_avatar()[j].center))
                    self.assertEqual(inicio.carrera.id,carrera.id)
                    self.assertEqual(inicio.personaje,avatar)
                    self.assertEqual(inicio.manejar_evento(clic(inicio.boton_jugar().center)),'jugar')
                    p=Partida(crear_mapa_universidad(),{},personaje=inicio.personaje,carrera=inicio.carrera.id)
                    self.assertEqual((p.jugador.carrera,p.jugador.personaje),(carrera.id,avatar))
                    self.assertEqual(p.habilidad.perfil.id,carrera.id)
                    self.assertEqual(len(p.mision.hijas),13)
                    self.assertEqual(sprite_estudiante(avatar,carrera.id).get_size(),(48,60))

    def test_cambiar_carrera_conserva_avatar(self):
        inicio=PantallaInicio(); inicio.vista='crear'
        inicio.manejar_evento(tecla(pygame.K_g))
        for _ in range(8):
            inicio.manejar_evento(tecla(pygame.K_RIGHT))
            self.assertEqual(inicio.personaje,'universitaria')

    def test_ayuda_volver_y_salida(self):
        inicio=PantallaInicio()
        inicio.manejar_evento(tecla(pygame.K_DOWN)); inicio.manejar_evento(tecla(pygame.K_RETURN))
        self.assertEqual(inicio.vista,'ayuda')
        inicio.manejar_evento(tecla(pygame.K_ESCAPE)); self.assertEqual(inicio.vista,'inicio')
        self.assertEqual(inicio.manejar_evento(clic(inicio.botones_inicio()[2].center)),'salir')

    def test_terminal_respeta_orden_y_alcance(self):
        p=self.partida('computacion'); p._aplicar_entrar('r101')
        p.jugador.x,p.jugador.y=(560,196)
        self.assertFalse(p.habilidad.usar(p))
        self.assertEqual(p.habilidad.recarga,0)
        p.jugador.x,p.jugador.y=(176,196); p.interactuar()
        p.jugador.x,p.jugador.y=(432,196)
        self.assertFalse(p.habilidad.usar(p))
        p.jugador.x,p.jugador.y=(500,196)
        self.assertTrue(p.habilidad.usar(p))
        self.assertTrue(next(m for m in p.mision.hijas if m.ubicacion=='r101').completada)
        self.assertFalse(p.habilidad.usar(p))
        self.assertGreater(p.habilidad.recarga,0)

    def test_microbot_recoge_sin_duplicar_y_no_gasta_si_bolsa_llena(self):
        p=self.partida('mecatronica'); p.jugador.x,p.jugador.y=(740,840)
        self.assertTrue(p.habilidad.usar(p)); self.assertTrue(p.inventario.tiene('libro'))
        self.assertEqual(sum(o['nombre']=='libro' for o in p.inventario.objetos),1)
        p.habilidad.avanzar(30)
        p.jugador.x,p.jugador.y=(580,520)
        while len(p.inventario.objetos)<p.inventario.capacidad_maxima:
            p.inventario.agregar(crear_objeto('cafe'))
        self.assertFalse(p.habilidad.usar(p)); self.assertEqual(p.habilidad.recarga,0)
        self.assertFalse(next(o for o in p.objetos_mundo if o['nombre']=='usb')['recogido'])

    def test_robot_no_omite_seguridad_o_usb(self):
        p=self.partida('mecatronica'); p._aplicar_entrar('lab_siemens')
        p.jugador.x,p.jugador.y=(400,208)
        self.assertFalse(p.habilidad.usar(p)); self.assertEqual(p.mision_lab.paso,0)
        p.jugador.x,p.jugador.y=(768,472); p.interactuar()
        p.jugador.x,p.jugador.y=(440,208)
        self.assertTrue(p.habilidad.usar(p)); self.assertEqual(p.mision_lab.paso,2)
        p.habilidad.avanzar(30)
        p.jugador.x,p.jugador.y=(770,144)
        self.assertFalse(p.habilidad.usar(p))
        p.interactuar(); self.assertFalse(p.mision_lab.completada)

    def test_industrial_velocidad_temporal_y_colisiones(self):
        p=self.partida('industrial'); p._aplicar_entrar('lab_siemens')
        p.jugador.x,p.jugador.y=(432,400)
        keys=defaultdict(bool,{pygame.K_w:True})
        self.assertTrue(p.habilidad.usar(p)); self.assertEqual(p.habilidad.factor_velocidad,1.45)
        antes=p.jugador.y; p.actualizar(.05,keys)
        self.assertAlmostEqual(antes-p.jugador.y,190*1.45*.05)
        p.jugador.x,p.jugador.y=(432,70)
        p.actualizar(.05,keys); self.assertEqual(p.jugador.y,70)
        p.habilidad.avanzar(12); self.assertEqual(p.habilidad.factor_velocidad,1)
        self.assertFalse(p.habilidad.usar(p)); p.habilidad.avanzar(30)
        self.assertTrue(p.habilidad.usar(p))

    def test_quimica_reloj_mitad_y_fin_del_efecto(self):
        p=self.partida('quimica'); p._aplicar_entrar('lab_siemens')
        self.assertTrue(p.habilidad.usar(p))
        p.actualizar(12,defaultdict(bool))
        self.assertAlmostEqual(p._tiempo_acumulado,6)
        self.assertEqual(p.estado_mundo['hora_actual_min'],20*60+15)
        p.actualizar(6,defaultdict(bool))
        self.assertEqual(p.estado_mundo['hora_actual_min'],20*60+16)
        self.assertEqual(p.habilidad.factor_velocidad,1)

    def test_habilidades_bloqueadas_en_transicion_y_panel(self):
        p=self.partida('industrial'); p.panel_activo='mapa'
        self.assertFalse(p.habilidad.usar(p))
        p.panel_activo=None; p.entrar_interior('r101')
        self.assertFalse(p.habilidad.usar(p)); self.assertEqual(p.habilidad.recarga,0)

    def test_cualquier_carrera_completa_todas_las_misiones_sin_habilidad(self):
        for carrera in CARRERAS:
            p=self.partida(carrera.id)
            p.inventario.agregar(crear_objeto('libro')); p.inventario.agregar(crear_objeto('usb'))
            for m in p.mision.hijas:
                p._aplicar_entrar(m.ubicacion); sala=p.interior_data
                reach=alcanzables(sala['spawn'],lambda x,y:not colision_interior(sala,x,y),sala['ancho'],sala['alto'])
                for paso in range(len(m.pasos)):
                    item=next(i for i in p.interior_interactivos if i.get('paso')==paso)
                    p.jugador.x,p.jugador.y=next(xy for xy in reach if interactivo_cercano(sala,*xy) is item)
                    p.interactuar()
                self.assertTrue(m.completada,(carrera.id,m.ubicacion))
                p._aplicar_salir()
            p.jugador.x,p.jugador.y=(856,952); p.interactuar()
            self.assertTrue(p.gano,carrera.id)

    def test_arranque_habilidad_pausa_y_nueva_partida(self):
        import main
        instancias=[]
        def crear(*args,**kwargs):
            p=Partida(*args,**kwargs); instancias.append(p); return p
        keys=(pygame.K_RETURN,pygame.K_2,pygame.K_g,pygame.K_RETURN,
              pygame.K_q,pygame.K_ESCAPE,pygame.K_h,pygame.K_RETURN,pygame.K_RETURN)
        eventos=[[tecla(k)] for k in keys]+[[pygame.event.Event(pygame.QUIT)]]
        try:
            with patch('pygame.event.get',side_effect=eventos),patch('main.Partida',side_effect=crear),patch('main.guardar_puntaje') as guardar,patch('main.ECO_CONSOLA',False),patch('main.TUTORIAL_AUTOMATICO',False):
                main.main()
                guardar.assert_not_called()
        finally:
            pygame.init(); pygame.display.set_mode((960,640))
        self.assertEqual(len(instancias),2)
        self.assertEqual(instancias[0].jugador.personaje,'universitaria')
        self.assertEqual(instancias[0].jugador.carrera,'industrial')
        self.assertGreater(instancias[0].habilidad.recarga,0)
        self.assertEqual(instancias[1].habilidad.recarga,0)
        self.assertFalse(any(m.completada for m in instancias[1].mision.hijas))

if __name__=='__main__': unittest.main()
