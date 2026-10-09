"""Portada panorámica y creación de estudiante con teclado y ratón."""
import math
from functools import lru_cache
import pygame
from arte_pixel import texto, fuente, caja, CREAM, INK, TEAL
from carreras import CARRERAS
from sprites_jugador import PERSONAJES, sprite_estudiante
from mundo_visual import campus
from identidad_key import dibujar_key, emblema


def envolver(cadena, ancho, size=14):
    lineas=[]; linea=''
    for palabra in cadena.split():
        nueva=(linea+' '+palabra).strip()
        if linea and fuente(size).size(nueva)[0]>ancho:
            lineas.append(linea); linea=palabra
        else: linea=nueva
    if linea: lineas.append(linea)
    return lineas


def boton(s, rect, label, activo=False, color=TEAL, size=18):
    r=pygame.Rect(rect)
    pygame.draw.rect(s,(7,17,27),r.move(0,5))
    pygame.draw.rect(s,(43,76,88) if activo else (51,64,77),r)
    pygame.draw.rect(s,color if activo else (136,154,159),r,2)
    pygame.draw.line(s,(209,221,206),r.topleft,(r.right-2,r.top),3)
    pygame.draw.line(s,(15,32,43),(r.x,r.bottom-3),(r.right,r.bottom-3),3)
    if activo:
        pygame.draw.rect(s,color,(r.x+2,r.y+3,5,r.h-6))
    texto(s,label,r.center,CREAM,size,True)

@lru_cache(maxsize=1)
def panorama():
    return pygame.transform.scale(campus(),(1152,792))


def fondo(s,tiempo,oscuro=120):
    x=-96+int(math.sin(tiempo*.075)*80)
    y=-64+int(math.cos(tiempo*.055)*35)
    s.blit(panorama(),(x,y))
    capa=pygame.Surface((960,640),pygame.SRCALPHA)
    capa.fill((9,21,38,oscuro)); s.blit(capa,(0,0))
    for i in range(26):
        xx=(i*139+int(tiempo*3))%960; yy=(i*73)%600
        pygame.draw.rect(s,(104,150,158),(xx,yy,2,2))
    for i,c in enumerate(CARRERAS):
        pygame.draw.rect(s,c.color,(i*240,634,240,6))


class PantallaInicio:
    def __init__(self):
        self.vista='inicio'
        self.indice_opcion=0
        self.indice_carrera=0
        self.indice_personaje=0

    @property
    def carrera(self): return CARRERAS[self.indice_carrera]
    @property
    def personaje(self): return PERSONAJES[self.indice_personaje]

    @staticmethod
    def botones_inicio():
        return [pygame.Rect(284,318+i*62,392,48) for i in range(3)]

    @staticmethod
    def tarjetas():
        return [pygame.Rect(24+i*232,124,216,208) for i in range(4)]

    @staticmethod
    def botones_avatar():
        return [pygame.Rect(48+i*110,506,100,34) for i in range(2)]

    @staticmethod
    def boton_jugar(): return pygame.Rect(554,564,382,44)
    @staticmethod
    def boton_volver(): return pygame.Rect(24,564,188,44)

    def _activar_inicio(self):
        if self.indice_opcion==0: self.vista='crear'
        elif self.indice_opcion==1: self.vista='ayuda'
        else: return 'salir'
        return None

    def manejar_evento(self,ev):
        if ev.type==pygame.KEYDOWN:
            k=ev.key
            if self.vista=='inicio':
                if k in (pygame.K_UP,pygame.K_w): self.indice_opcion=(self.indice_opcion-1)%3
                elif k in (pygame.K_DOWN,pygame.K_s): self.indice_opcion=(self.indice_opcion+1)%3
                elif k in (pygame.K_RETURN,pygame.K_SPACE): return self._activar_inicio()
            elif self.vista=='crear':
                if k in (pygame.K_LEFT,pygame.K_a): self.indice_carrera=(self.indice_carrera-1)%4
                elif k in (pygame.K_RIGHT,pygame.K_d): self.indice_carrera=(self.indice_carrera+1)%4
                elif k in (pygame.K_1,pygame.K_2,pygame.K_3,pygame.K_4): self.indice_carrera=k-pygame.K_1
                elif k==pygame.K_g: self.indice_personaje=(self.indice_personaje+1)%2
                elif k==pygame.K_RETURN: return 'jugar'
                elif k==pygame.K_ESCAPE: self.vista='inicio'
            elif self.vista=='ayuda' and k in (pygame.K_ESCAPE,pygame.K_RETURN): self.vista='inicio'
        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
            if self.vista=='inicio':
                for i,r in enumerate(self.botones_inicio()):
                    if r.collidepoint(ev.pos):
                        self.indice_opcion=i
                        return self._activar_inicio()
            elif self.vista=='crear':
                for i,r in enumerate(self.tarjetas()):
                    if r.collidepoint(ev.pos): self.indice_carrera=i
                for i,r in enumerate(self.botones_avatar()):
                    if r.collidepoint(ev.pos): self.indice_personaje=i
                if self.boton_jugar().collidepoint(ev.pos): return 'jugar'
                if self.boton_volver().collidepoint(ev.pos): self.vista='inicio'
            elif self.vista=='ayuda' and self.boton_volver().collidepoint(ev.pos): self.vista='inicio'
        return None

    def dibujar(self,s,tiempo,mouse=(-1,-1)):
        fondo(s,tiempo,120 if self.vista=='inicio' else 210)
        if self.vista=='inicio': self._inicio(s,tiempo,mouse)
        elif self.vista=='crear': self._crear(s,tiempo,mouse)
        else: self._ayuda(s,mouse)

    def _inicio(self,s,tiempo,mouse):
        dibujar_key(s,(30,26))
        texto(s,'INSTITUTO KRIETE',(166,32),CREAM,12)
        texto(s,'INGENIERÍA Y CIENCIAS',(166,49),(171,195,187),10)
        # Título con relieve de bloques y texto flotante original.
        for dy,color in ((10,(7,15,25)),(6,(67,89,103)),(0,(230,234,214))):
            texto(s,'9PM',(480,157+dy),color,116,True)
        texto(s,'LA ÚLTIMA NOCHE EN KEY',(480,235),CREAM,19,True)
        splash=fuente(16).render('¡Entrega antes del cierre!',False,(249,228,82))
        splash=pygame.transform.rotate(splash, -12)
        s.blit(splash,splash.get_rect(center=(667,203+int(math.sin(tiempo*3)*3))))
        texto(s,'Un campus real. Cuatro maneras de recorrerlo.',(480,276),(181,210,197),13,True)
        for i,(r,label) in enumerate(zip(self.botones_inicio(),('Jugar','Cómo jugar','Salir del juego'))):
            boton(s,r,label,i==self.indice_opcion or r.collidepoint(mouse),size=20)
        texto(s,'UN JUGADOR  /  13 MISIONES  /  4 CARRERAS',(480,540),(189,211,195),12,True)
        texto(s,'↑ ↓ elegir   ·   ENTER confirmar   ·   F11 pantalla completa',(480,584),CREAM,12,True)
        texto(s,'9PM · Proyecto estudiantil',(20,613),(159,183,180),11)
        texto(s,'KEY / NIVEL 01',(805,613),(159,183,180),11)

    def _crear(self,s,tiempo,mouse):
        texto(s,'CREA TU ESTUDIANTE',(24,25),CREAM,28)
        texto(s,'Elige una carrera y tu avatar. Ambos pueden usar las cuatro especialidades.',(24,69),(173,202,188),13)
        texto(s,'01 / CARRERA',(24,99),TEAL,12)
        for i,(c,r) in enumerate(zip(CARRERAS,self.tarjetas())):
            selected=i==self.indice_carrera
            caja(s,r,(35,54,70) if selected else (22,36,51),c.color if selected else (70,89,103))
            pygame.draw.rect(s,c.color,(r.x+2,r.y+2,r.w-4,5))
            emblema(s,c.id,(r.centerx,r.y+48),54,c.color)
            for j,linea in enumerate(c.lineas):
                texto(s,linea,(r.centerx,r.y+96+j*21),CREAM,14,True)
            texto(s,f'{i+1} / '+('ELEGIDA' if selected else 'SELECCIONAR'),(r.centerx,r.bottom-25),c.color,11,True)
        c=self.carrera
        caja(s,(24,350,256,194),(25,43,58),(89,118,126))
        texto(s,'02 / TU AVATAR',(42,364),TEAL,12)
        im=sprite_estudiante(self.personaje,c.id,escala=3)
        pygame.draw.ellipse(s,(13,30,41),(108,476,90,10))
        s.blit(im,im.get_rect(midbottom=(152,480)))
        for i,(r,label) in enumerate(zip(self.botones_avatar(),('Niño','Niña'))):
            boton(s,r,label,i==self.indice_personaje or r.collidepoint(mouse),c.color,14)
        caja(s,(300,350,636,194),(25,43,58),c.color)
        texto(s,'03 / HERRAMIENTA DE CARRERA',(320,365),c.color,12)
        texto(s,c.herramienta,(320,389),CREAM,24)
        texto(s,'[Q] '+c.habilidad,(320,426),c.color,16)
        for j,l in enumerate(envolver(c.descripcion,596,14)):
            texto(s,l,(320,454+j*19),CREAM,14)
        texto(s,f'Recarga: {int(c.recarga)} s · No ocupa espacio en la bolsa',(320,520),(146,180,179),12)
        boton(s,self.boton_volver(),'Volver',self.boton_volver().collidepoint(mouse),size=16)
        boton(s,self.boton_jugar(),'ENTRAR AL CAMPUS  >',True,c.color,18)
        texto(s,'← → / 1-4 carrera    G cambiar avatar    ENTER jugar',(24,618),(177,201,187),12)

    def _ayuda(self,s,mouse):
        texto(s,'ANTES DE QUE DEN LAS 9',(28,28),CREAM,28)
        texto(s,'Son las 20:15. Recorre KEY, resuelve tus encargos y vuelve a casa.',(28,76),(167,198,188),14)
        controles=[('WASD / FLECHAS','Camina por pasillos; las puertas llevan a cada sala.'),
            ('ESPACIO','Recoge objetos o usa la estación cercana.'),('Q','Usa tu herramienta de carrera. La barra indica la recarga.'),
            ('M / J','Abre el mapa o la bitácora: el tiempo se pausa.'),('I / TAB','Abre la bolsa. G suelta el último objeto en el pasillo.'),
            ('Z / H','Deshace tu última acción (pila) o abre el historial.'),
            ('GRADAS','Suben a la Torre: escribe el número de la opción y ENTER.'),
            ('ESC','Pausa durante la partida; cierra los paneles.'),('F11','Alterna ventana y pantalla completa.')]
        for i,(tecla,descripcion) in enumerate(controles):
            y=112+i*37
            caja(s,(28,y,180,34),(32,63,76),TEAL)
            texto(s,tecla,(118,y+17),CREAM,13,True)
            texto(s,descripcion,(226,y+10),CREAM,13)
        for j,l in enumerate(envolver('Todas las carreras pueden completar las 13 misiones. Busca el libro en el lobby y la USB frente a R101. La Torre de las gradas cambia cada noche: va por turnos y guarda objetos perdidos en sus salas más profundas.',895,14)):
            texto(s,l,(28,486+j*22),(187,205,177),14)
        boton(s,self.boton_volver(),'Volver',self.boton_volver().collidepoint(mouse),size=16)
        texto(s,'ENTER / ESC volver',(706,582),TEAL,13)
