"""Interiores transitables con mobiliario e interacciones propias por sala."""
import math
from functools import lru_cache
import pygame
from arte_pixel import prop, personaje, suelo, texto, caja, INK, CREAM, TEAL
from misiones import ENCARGOS
from mapa_nivel1 import NOMBRES


def mueble(tipo,rect,var=0):
    return {'tipo':tipo,'rect':rect,'var':var}

def accion(id,pos,label,paso=None,requiere=None,mensaje=''):
    return dict(id=id,pos=pos,label=label,paso=paso,requiere=requiere,
                mensaje=mensaje or label,once=False)

def sala_base(nombre,titulo):
    return dict(nombre=nombre,titulo=titulo,ancho=864,alto=512,
        spawn=(432,472),exit_zone=(400,482,64,28),estilo=nombre,
        muebles=[],interactivos=[],props=[])

INTERIORES={}
for nombre,titulo,pasos in ENCARGOS:
    s=sala_base(nombre,NOMBRES[nombre]+' · '+titulo)
    if nombre=='lab_siemens':
        s['titulo']='SIEMENS · Action Lab'
        # Dos filas a los lados de un pasillo central; cuatro bancos reales.
        for idx,(x,y) in enumerate(((72,154),(552,154),(72,302),(552,302))):
            s['muebles'].append(mueble('banco_plc',(x,y,240,80)))
            for k,xx in enumerate((x+24,x+176)):
                s['muebles'].append(mueble('silla',(xx,y+80,32,40),(idx+k)%3))
        s['muebles'] += [mueble('pizarra',(352,80,160,56)),
            mueble('pc',(664,72,80,56)),mueble('impresora',(756,80,48,48)),
            mueble('carrito',(80,428,64,60)),mueble('extintor',(780,434,24,44)),
            mueble('basurero',(820,432,28,44)),mueble('robot',(40,72,112,64))]
        s['interactivos']=[
            accion('seguridad',(768,472),'Revisar extintor',0,mensaje='Presión correcta. Área despejada: estación segura.'),
            accion('panel_plc',(328,208),'PLC · activar simulación',1,mensaje='PLC en RUN. Motor de práctica activado; prueba de señal correcta.'),
            accion('pc_impresora',(770,144),'Imprimir informe',2,'usb','Informe impreso. Práctica de Siemens completada.'),
            accion('pizarra_trivia',(432,152),'Leer pizarra TRIVIA',mensaje='TRIVIA: un PLC lee entradas, ejecuta el programa y actualiza salidas. Sigue ese orden.'),
            accion('carrito',(156,468),'Revisar herramientas',mensaje='Carrito verde: cables, manuales y herramientas ordenadas por estación.'),
        ]
    elif nombre=='biblioteca':
        s['muebles']=[mueble('estante',(x,88,104,156)) for x in (56,192,568,704)]
        s['muebles'] += [mueble('mostrador',(344,184,176,64)),mueble('mesa',(144,336,192,64)),mueble('mesa',(528,336,192,64))]
        s['interactivos']=[accion('devolucion',(432,268),'Devolver libro',0,'libro','Préstamo cerrado. El libro vuelve a su estante.')]
    elif nombre=='sala_reuniones':
        s['muebles']=[mueble('mesa',(280,208,304,96)),mueble('estante',(64,80,120,160))]
        s['muebles'] += [mueble('silla',(x,y,32,40),i%3) for i,(x,y) in enumerate(((300,308),(388,308),(496,308),(300,162),(496,162)))]
        s['interactivos']=[accion('profesor',(632,272),'Hablar con el profesor',0,mensaje='Profesor: «Recibí tu excusa. Termina tus encargos y vuelve a casa.»')]
    else:
        tipos={
            'r101':('pizarra','pc'),'r102':('pizarra','mostrador'),
            'r103':('pizarra','pc'),'r104':('osciloscopio','mostrador'),
            'r105':('pc','mostrador'),'lab_click':('servidor','pc'),
            'lab_spark':('osciloscopio','hmi'),'lab_kite':('robot','pc'),
            'cafeteria':('maquina','mostrador'),'bodega':('caja','pc')}
        a,b=tipos[nombre]
        s['muebles']=[mueble(a,(96,96,160,80)),mueble(b,(584,96,160,80))]
        s['interactivos']=[accion('paso_0',(176,196),pasos[0],0,mensaje='Revisión registrada. Continúa en la segunda estación.'),
                           accion('paso_1',(664,196),pasos[1],1,mensaje='Registro confirmado. Encargo completado.')]
        if nombre.startswith('r'):
            for idx,(x,y) in enumerate(( (x,y) for y in (264,368) for x in (128,368,608))):
                s['muebles'] += [mueble('mesa',(x,y,104,52)),mueble('silla',(x+36,y+52,32,36),idx%3)]
        elif nombre=='cafeteria':
            for x in (128,368,608):
                s['muebles'] += [mueble('cafe_mesa',(x,304,104,64)),mueble('silla',(x+36,374,32,40),0)]
        elif nombre=='bodega':
            s['muebles'] += [mueble('estante',(x,280,120,128)) for x in (88,304,616)]
        else:
            for x in (104,552):
                s['muebles'] += [mueble('banco_plc' if nombre=='lab_spark' else 'mesa',(x,304,208,80)),
                                 mueble('silla',(x+80,388,32,40),1)]
    s['muebles'] += [mueble('planta',(24,432,40,56)),mueble('planta',(804,72,40,56))]
    # Las siluetas físicas usan los mismos rectángulos que los sprites.
    s['props']=[o['rect'] for o in s['muebles']]
    INTERIORES[nombre]=s


def obtener_interior(nombre): return INTERIORES[nombre]

def punto_en_rect_local(px,py,rect):
    x,y,w,h=rect
    return x<=px<=x+w and y<=py<=y+h

def colision_interior(sala,px,py,radio=10):
    w,h=sala['ancho'],sala['alto']
    if punto_en_rect_local(px,py,sala['exit_zone']): return False
    if not (20+radio<=px<=w-20-radio and 60+radio<=py<=h-20-radio): return True
    for x,y,pw,ph in sala['props']:
        if x-radio<px<x+pw+radio and y-radio<py<y+ph+radio: return True
    return False

def en_zona_salida(sala,px,py): return punto_en_rect_local(px,py,sala['exit_zone'])

def interactivo_cercano(sala,px,py,radio=50):
    candidatos=[(math.hypot(px-i['pos'][0],py-i['pos'][1]),i) for i in sala['interactivos']]
    candidatos.sort(key=lambda it:it[0])
    return candidatos[0][1] if candidatos and candidatos[0][0]<radio else None

@lru_cache(maxsize=20)
def fondo_interior(nombre):
    sala=INTERIORES[nombre]; w,h=sala['ancho'],sala['alto']
    s=pygame.Surface((w,h)); s.fill(INK)
    suelo(s,(16,48,w-32,h-64),'interior')
    # Corte de paredes: cara de ladrillo, cornisa y zócalo.
    pygame.draw.rect(s,(209,218,204),(0,0,w,54))
    pygame.draw.rect(s,(49,69,90) if nombre=='lab_siemens' else (71,113,124),(8,8,w-16,36))
    pygame.draw.rect(s,(242,232,200),(0,0,w,6))
    pygame.draw.rect(s,(89,114,118),(0,50,w,8))
    for xx in (0,w-16):
        pygame.draw.rect(s,(111,137,135),(xx,54,16,h-54))
        pygame.draw.rect(s,(202,213,195),(xx,54,4,h-54))
    for xx in (48,160,584,696):
        caja(s,(xx,14,88,24),(130,184,191),(223,229,209))
        pygame.draw.line(s,(222,236,218),(xx+44,16),(xx+44,36),2)
        pygame.draw.line(s,(181,218,209),(xx+4,32),(xx+24,18),2)
    texto(s,'SIEMENS' if nombre=='lab_siemens' else nombre.replace('_',' ').upper(),(w//2,26),size=20,center=True)
    texto(s,'key',(804,17),CREAM,22)
    for o in sala['muebles']:
        x,y,ow,oh=o['rect']
        pygame.draw.rect(s,(137,155,150),(x+4,y+oh-6,ow,10))
        s.blit(prop(o['tipo'],ow,oh,o['var']),(x,y))
    if nombre=='lab_siemens':
        texto(s,'TRIVIA',(432,94),(49,88,104),12,True)
        for idx,(x,y) in enumerate(((72,154),(552,154),(72,302),(552,302)),1):
            texto(s,f'{idx:02}',(x+12,y+61),INK,12)
        texto(s,'SIMULACIÓN PLC',(432,262),(78,109,118),14,True)
        texto(s,'SEGURIDAD > RUN > INFORME',(432,282),(78,109,118),12,True)
    if nombre=='sala_reuniones':
        npc=personaje('profesor')
        s.blit(npc,npc.get_rect(midbottom=(632,264)))
    ex,ey,ew,eh=sala['exit_zone']
    caja(s,(ex,ey,ew,eh),(72,135,132),(154,197,164))
    texto(s,'SALIR',(ex+ew//2,ey+eh//2),size=12,center=True)
    return s

def dibujar_interior(pantalla,sala,camara,fuentes_chica=None):
    pantalla.blit(fondo_interior(sala['nombre']),(-int(camara[0]),-int(camara[1])))
    if sala['nombre']=='lab_siemens' and any(i.get('id')=='panel_plc' and i.get('usado') for i in sala['interactivos']):
        for x in (96,136,176):
            pygame.draw.rect(pantalla,(126,239,169),(x-camara[0],174-camara[1],6,4))
        texto(pantalla,'RUN',(322-camara[0],170-camara[1]),TEAL,12)

def dibujar_interactivos_interior(pantalla,sala,jugador_pos,tiempo,camara,radio=50):
    nearest=interactivo_cercano(sala,*jugador_pos,radio)
    for item in sala['interactivos']:
        x,y=item['pos']; px,py=int(x-camara[0]),int(y-camara[1])-24
        if item.get('usado'):
            texto(pantalla,'✓',(px,py),TEAL,16,True)
        else:
            yy=py+int(math.sin(tiempo*3)*2)
            pygame.draw.polygon(pantalla,INK,[(px-7,yy-5),(px+7,yy-5),(px,yy+5)])
            pygame.draw.polygon(pantalla,(241,199,116),[(px-4,yy-3),(px+4,yy-3),(px,yy+2)])
        if item is nearest:
            caja(pantalla,(px-19,py-32,38,22),(40,76,87))
            texto(pantalla,'ESP',(px,py-21),CREAM,12,True)
