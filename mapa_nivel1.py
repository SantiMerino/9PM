"""Nivel 1 trazado sobre el plano adjunto, con su misma orientación.

Cotas adaptadas a una rejilla de 8 px: se conservan adyacencias, patios y
el acceso diagonal del lobby/Kite. La referencia no contiene medidas.
"""
from __future__ import annotations
MUNDO_ANCHO, MUNDO_ALTO = 1536, 1056
CORR = 80
SALAS_RECT = {
    'cafeteria': (432,64,136,96), 'terraza': (568,64,496,96),
    'r104': (248,160,200,184), 'r105': (448,160,200,184),
    'bodega': (16,344,232,80), 'r103': (16,424,232,176),
    'jardin_oeste': (280,416,368,120),
    'r102': (248,600,200,184), 'r101': (448,600,208,184),
    'jardin_central': (736,200,296,320), 'biblioteca': (736,520,296,72),
    'sala_reuniones': (736,600,80,112), 'servicios': (816,600,80,112),
    'gradas': (896,600,56,112), 'servicios_este': (952,600,80,112),
    'lobby': (720,784,216,72), 'lab_siemens': (1128,168,232,184),
    'lab_click': (1128,352,312,184), 'lab_spark': (1128,536,312,208),
    'lab_kite': (1000,744,360,192), 'servicios_norte': (1128,32,232,136),
}
POLIGONOS_SALA = {'lab_kite': [(1128,744),(1360,744),(1360,936),(1120,936),(1000,840)]}
PASILLO_DIAGONAL = [(1064,720),(1136,768),(864,1000),(704,864),(704,784),(824,904)]
ZONAS_CAMINABLES = [
    SALAS_RECT['terraza'], SALAS_RECT['lobby'], SALAS_RECT['jardin_central'],
    SALAS_RECT['jardin_oeste'], (648,128,88,736), (1032,128,96,616),
    (648,128,480,72), (232,344,504,72), (232,536,504,64),
    (248,416,32,120), (648,712,480,72), (896,680,56,64), (936,784,72,72),
]
NOMBRES = {k:k.upper() for k in ('r101','r102','r103','r104','r105')}
NOMBRES.update({'cafeteria':'Cafetería','terraza':'Terraza','bodega':'Bodega',
    'jardin_oeste':'Jardín oeste','jardin_central':'Jardín central',
    'biblioteca':'Biblioteca','sala_reuniones':'Reuniones','gradas':'Gradas',
    'lobby':'Lobby','lab_siemens':'Lab Siemens','lab_click':'Lab Click',
    'lab_spark':'Lab Spark','lab_kite':'Lab Kite','servicios':'Servicios',
    'servicios_este':'Servicios','servicios_norte':'Área técnica'})
COLORES_SALA = {k:(96,143,158) for k in SALAS_RECT}
COLORES_SALA.update({'lab_siemens':(50,124,137),'lab_click':(103,124,171),
    'lab_spark':(196,146,78),'lab_kite':(122,155,117),
    'biblioteca':(160,115,130),'cafeteria':(196,140,102)})
def _puerta(nombre, trigger, retorno, lado):
    return dict(trigger=trigger,retorno=retorno,interior=nombre,etiqueta=NOMBRES[nombre],lado=lado)
PUERTAS = {
    'cafeteria': _puerta('cafeteria',(552,104,32,48),(612,128),'este'),
    'r104': _puerta('r104',(312,328,56,32),(340,392),'sur'),
    'r105': _puerta('r105',(512,328,56,32),(540,392),'sur'),
    'bodega': _puerta('bodega',(232,360,32,48),(296,384),'este'),
    'r103': _puerta('r103',(216,552,48,32),(296,568),'este'),
    'r102': _puerta('r102',(312,584,56,32),(340,552),'norte'),
    'r101': _puerta('r101',(520,584,56,32),(548,552),'norte'),
    'biblioteca': _puerta('biblioteca',(1016,536,32,48),(1080,560),'este'),
    'sala_reuniones': _puerta('sala_reuniones',(760,696,48,32),(784,756),'sur'),
    'lab_siemens': _puerta('lab_siemens',(1112,280,32,48),(1080,304),'oeste'),
    'lab_click': _puerta('lab_click',(1112,432,32,48),(1080,456),'oeste'),
    'lab_spark': _puerta('lab_spark',(1112,616,32,48),(1080,640),'oeste'),
    'lab_kite': _puerta('lab_kite',(1040,796,48,32),(1016,792),'diagonal'),
}
GRADAS_TRIGGER = (904,680,40,32)
SALIDAS = {
    'lobby_sur': {'trigger':(824,936,64,40),'mensaje':'Salida sur del lobby'},
    'terraza_norte': {'trigger':(784,64,80,32),'mensaje':'Salida por la terraza'},
}
SPAWN_LOBBY = (816,816)
# Fuente compartida por renderer y colisiones: no hay obstáculos invisibles.
DECORACION = []
for key in ('jardin_central','jardin_oeste'):
    x,y,w,h=SALAS_RECT[key]
    posiciones=[(x+22,y+16),(x+w-94,y+16)]
    if h>160:
        posiciones.extend([(x+22,y+h-92),(x+w-94,y+h-92)])
    for xx,yy in posiciones:
        DECORACION.append(('arbol',(xx,yy,64,80)))
DECORACION += [('banco',(x,72,64,28)) for x in (590,976)]
DECORACION += [('planta',(x,784,32,40)) for x in (744,888)]
OBSTACULOS = [(x+16,y+54,w-32,22) if tipo=='arbol' else (x,y,w,h)
              for tipo,(x,y,w,h) in DECORACION]
def centro_sala(nombre):
    x,y,w,h = SALAS_RECT[nombre]
    return x+w//2,y+h//2

def punto_en_rect(px,py,rect):
    x,y,w,h = rect
    return x <= px <= x+w and y <= py <= y+h

def punto_en_poligono(x,y,vertices):
    dentro = False
    j = len(vertices)-1
    for i,(xi,yi) in enumerate(vertices):
        xj,yj = vertices[j]
        if (yi>y)!=(yj>y) and x < (xj-xi)*(y-yi)/(yj-yi)+xi:
            dentro = not dentro
        j=i
    return dentro

def _punto_libre(x,y):
    if any(punto_en_rect(x,y,r) for r in OBSTACULOS):
        return False
    if any(punto_en_rect(x,y,p['trigger']) for p in PUERTAS.values()):
        return True
    # La diagonal de Kite se recorta igual en el dibujo y en la colisión.
    if punto_en_poligono(x,y,POLIGONOS_SALA['lab_kite']):
        return False
    return (any(punto_en_rect(x,y,r) for r in ZONAS_CAMINABLES)
        or punto_en_poligono(x,y,PASILLO_DIAGONAL)
        or any(punto_en_rect(x,y,p['trigger']) for p in SALIDAS.values()))

def es_caminable(x,y,radio=10):
    return all(_punto_libre(x+dx*radio,y+dy*radio) for dx,dy in
        ((0,0),(-1,0),(1,0),(0,-1),(0,1),(-.7,-.7),(.7,-.7),(-.7,.7),(.7,.7)))

def puerta_en(x,y,radio=36):
    for nombre,p in PUERTAS.items():
        tx,ty,w,h=p['trigger']
        if (x-tx-w/2)**2+(y-ty-h/2)**2 < radio**2:
            return nombre
    return None

def crear_mapa_nivel1():
    from mapa import MapaCampus
    mapa=MapaCampus()
    nodos={'jardin_c':(884,360),'jardin_o':(692,360),'oeste_n':(692,168),
        'norte':(1080,168),'este_c':(1080,360),'este_s':(1080,748),'sur':(692,748),
        'oeste_s':(692,568),'aulas_sur':(288,568),'aulas_norte':(288,380),
        'oeste_m':(692,380),'terraza':(824,168),'terraza_n':(824,112),
        'lobby_acceso':(692,840),'lobby_frente':(816,840),'lobby':SPAWN_LOBBY}
    for nombre,pos in nodos.items():
        mapa.agregar_sala(nombre,pos)
    for a,b in (('jardin_c','jardin_o'),('jardin_c','este_c'),('jardin_o','oeste_n'),
        ('oeste_n','terraza'),('terraza','norte'),('terraza','terraza_n'),
        ('norte','este_c'),('este_c','este_s'),('este_s','sur'),('sur','oeste_s'),
        ('oeste_s','oeste_m'),('oeste_m','jardin_o'),('oeste_m','aulas_norte'),
        ('oeste_s','aulas_sur'),('sur','lobby_acceso'),
        ('lobby_acceso','lobby_frente'),('lobby_frente','lobby')):
        mapa.conectar(a,b)
    return mapa

def verificar_sin_solapes():
    pares=[]
    for i,(a,ar) in enumerate(SALAS_RECT.items()):
        for b,br in list(SALAS_RECT.items())[i+1:]:
            if a in POLIGONOS_SALA or b in POLIGONOS_SALA:
                continue
            x,y,w,h=ar
            bx,by,bw,bh=br
            if x<bx+bw and x+w>bx and y<by+bh and y+h>by:
                pares.append((a,b))
    return pares
