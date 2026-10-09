"""Genera vistas reales con Pygame sin abrir ventana (QA visual reproducible)."""
import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
from pathlib import Path
import pygame
import main
from mundo_visual import campus
from hud_campus import dibujar_mapa,dibujar_diario
from menu_inicio import PantallaInicio
from carreras import CARRERAS
from sprites_jugador import sprite_estudiante
pygame.init(); pygame.display.set_mode((960,640))
fuentes={k:pygame.font.SysFont('consolas',n) for k,n in [('titulo',52),('reloj',30),('normal',20),('chica',15)]}
sprites=main.cargar_sprites_jugador()
s=pygame.Surface((960,640)); out=Path('docs/capturas'); out.mkdir(exist_ok=True)
p=main.Partida(main.crear_mapa_universidad(),fuentes)
glow=main.crear_glow(130,(255,220,130),55)
main.dibujar_menu(s,fuentes,[],sprites,0,0); pygame.image.save(s,out/'menu.png')
inicio=PantallaInicio(); inicio.vista='crear'
for i,carrera in enumerate(CARRERAS):
    inicio.indice_carrera=i
    inicio.indice_personaje=i%2
    inicio.dibujar(s,0)
    pygame.image.save(s,out/('seleccion_'+carrera.id+'.png'))
inicio.vista='ayuda'; inicio.dibujar(s,0); pygame.image.save(s,out/'ayuda.png')
galeria=pygame.Surface((960,380)); galeria.fill((23,40,55))
for i,carrera in enumerate(CARRERAS):
    main.texto(galeria,carrera.corto,(120+i*240,30),carrera.color,18,True)
    for j,avatar in enumerate(main.PERSONAJES):
        im=sprite_estudiante(avatar,carrera.id,escala=4)
        galeria.blit(im,im.get_rect(midbottom=(120+i*240,175+j*160)))
pygame.image.save(galeria,out/'ocho_estudiantes.png')
pygame.image.save(campus(),out/'campus_completo.png')
p.jugador.x,p.jugador.y=(884,400); p.toasts=[]
cam=main.calcular_camara(p.jugador.pos)
main.dibujar_overworld(s,cam); main.dibujar_objetos_mundo(s,p.objetos_mundo,p.jugador.pos,0,cam)
main.dibujar_interactivos(s,p.interactivos,p.jugador.pos,0,cam)
main.dibujar_jugador(s,p.jugador,glow,cam,sprites,0); main.dibujar_hud(s,p,fuentes)
main.BotonInventario((782,8,160,40)).dibujar(s,0,6,False)
pygame.image.save(s,out/'campus.png')
for nombre in main.PUERTAS:
    p._aplicar_entrar(nombre); p.toasts=[]
    p.jugador.x,p.jugador.y=(432,420)
    if main.colision_interior(p.interior_data,*p.jugador.pos):
        p.jugador.x,p.jugador.y=p.interior_data['spawn']
    cam=main.calcular_camara(p.jugador.pos,*p.mundo_actual_size())
    s.fill((18,34,44)); main.dibujar_interior(s,p.interior_data,cam,fuentes['chica'])
    main.dibujar_interactivos_interior(s,p.interior_data,p.jugador.pos,0,cam)
    main.dibujar_jugador(s,p.jugador,glow,cam,sprites,0)
    main.dibujar_hud(s,p,fuentes); main.BotonInventario((782,8,160,40)).dibujar(s,0,6,False)
    pygame.image.save(s,out/(nombre+'.png'))
p._aplicar_salir(); dibujar_mapa(s,p); pygame.image.save(s,out/'mapa.png')
dibujar_diario(s,p); pygame.image.save(s,out/'bitacora.png')
p.inventario.agregar(main.crear_objeto('libro')); p.inventario.agregar(main.crear_objeto('usb'))
panel=main.PanelInventario(960,640); panel.alternar(); panel.actualizar(1,(-1,-1)); panel.dibujar(s,p.inventario)
pygame.image.save(s,out/'inventario.png')
print('Capturas creadas en',out.resolve())
pygame.quit()
