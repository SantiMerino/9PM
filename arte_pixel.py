"""Arte original de 9PM: atlas procedural de píxeles, sin assets externos.

Todo se dibuja a media resolución y se amplía por vecino más cercano.
Las superficies están cacheadas; no se regeneran texturas en cada frame.
"""
from functools import lru_cache
import pygame

INK=(28,43,57)
CREAM=(237,231,205)
TEAL=(72,169,158)

@lru_cache(maxsize=24)
def fuente(size=14):
    return pygame.font.SysFont('consolas',size,bold=True)

def texto(s,text,pos,color=CREAM,size=14,center=False):
    im=fuente(size).render(text,False,color)
    s.blit(im,im.get_rect(center=pos) if center else pos)

def caja(s,rect,color=INK,borde=(108,148,151)):
    r=pygame.Rect(rect)
    pygame.draw.rect(s,(12,24,34),r.move(0,4))
    pygame.draw.rect(s,color,r)
    pygame.draw.rect(s,borde,r,2)
    pygame.draw.line(s,(171,193,178),r.topleft,(r.right-1,r.top),2)

@lru_cache(maxsize=256)
def personaje(tipo='universitario',direccion='abajo',paso=0,escala=2,acento=None,herramienta=None):
    s=pygame.Surface((24,30),pygame.SRCALPHA)
    def r(c,rect): pygame.draw.rect(s,c,rect)
    female=tipo=='universitaria'
    male=tipo=='universitario'
    guard=tipo=='vigilante'
    skin=(227,174,130); light=(249,203,150)
    # Ella: melena castaño rojizo con moño rosa y falda. Él: pelo corto oscuro,
    # orejas a la vista y jeans. Así se distinguen aunque compartan carrera.
    if female:
        hair=(150,70,48); hair_hi=(198,110,70)
    elif male:
        hair=(40,32,36); hair_hi=(84,66,62)
    else:
        hair=(57,44,44); hair_hi=(99,67,51)
    lazo=(242,104,146); lazo_hi=(255,188,204)
    shirt=(180,80,98) if female else (65,121,171)
    if acento is not None:
        shirt=tuple(int(c*.74) for c in acento)
    if guard: shirt=(62,87,110)
    # Silueta chibi, mangas, mochila y suelas.
    r(INK,(7,19,10,10)); r(INK,(4,13,16,11))
    r(shirt,(6,14,12,9)); r((112,163,187) if not female else (214,123,130),(7,14,9,2))
    if acento is not None:
        r(acento,(7,14,9,2))
    piernas=(70,54,84) if female else (52,76,124) if male else (54,65,91)
    for x,dy in ((7,paso%2),(13,(paso+1)%2 if paso else 0)):
        r(piernas,(x,23,4,4+dy)); r(INK,(x-1,27+dy,6,2)); r((198,211,204),(x,27+dy,4,1))
    if female:
        falda=(118,52,92)
        r(INK,(5,21,14,5)); r(falda,(6,21,12,4)); r((170,88,130),(6,21,12,1))
        r((92,40,72),(9,22,1,3)); r((92,40,72),(14,22,1,3))
    r(skin,(4,19,2,4)); r(skin,(18,19,2,4))
    r(INK,(5,3,14,12)); r(hair,(4,5,16,8)); r(hair,(7,2,10,3))
    r(hair_hi,(6,4,9,3)); r(light,(6,8,12,7)); r(skin,(8,15,8,2))
    if male:
        # Pelo corto en puntas y orejas visibles.
        r(INK,(7,1,2,1)); r(INK,(11,0,2,2)); r(INK,(15,1,2,1))
        r(hair,(8,1,2,2)); r(hair,(12,1,2,2)); r(hair,(15,2,2,1))
    if direccion=='arriba':
        r(INK,(7,17,10,8)); r((175,128,70),(8,17,8,7)); r((222,171,91),(9,18,6,2)); r((108,84,61),(9,22,6,1))
        if female:
            r(hair,(4,5,16,14)); r(hair_hi,(7,6,2,10)); r(hair_hi,(13,6,2,9)); r(INK,(4,18,16,1))
        else:
            r(hair,(5,5,14,9)); r(hair_hi,(6,4,9,3))
            if male:
                r(skin,(9,14,6,1)); r(skin,(4,9,1,2)); r(skin,(19,9,1,2))
    elif direccion in ('izquierda','derecha'):
        if female:
            r(hair,(11,5,9,14)); r(hair_hi,(14,6,2,10)); r(INK,(11,18,9,1))
            r(INK,(6,9,1,1))
        else:
            r(hair,(12,6,7,7 if male else 9))
            if male:
                r(skin,(13,10,3,2)); r((196,140,104),(14,10,1,1))
        r(INK,(7,10,2,3)); r(light,(4,12,3,2))
        r((190,140,77),(16,17,4,7)); r((233,185,104),(17,18,2,2))
    else:
        r(INK,(8,10,2,3)); r(INK,(14,10,2,3))
        r((255,239,207),(8,10,1,1)); r((255,239,207),(14,10,1,1))
        r((215,176,102),(6,17,2,5)); r((215,176,102),(16,17,2,5))
        r((199,219,213),(10,18,4,3))
        if female:
            # Flequillo de lado, pestañas, rubor y boca rosa.
            r(hair,(6,8,7,1)); r(hair,(6,9,3,1)); r(hair,(15,8,3,1))
            r(INK,(7,10,1,1)); r(INK,(16,10,1,1))
            r((240,150,140),(7,13,2,1)); r((240,150,140),(15,13,2,1))
            r((206,92,104),(11,14,2,1))
        else:
            r(hair,(6,7,3,3)); r(hair,(15,7,3,2)); r((172,105,89),(11,14,3,1))
            if male:
                r((58,40,38),(8,9,2,1)); r((58,40,38),(14,9,2,1))
                r(skin,(4,9,2,3)); r(skin,(18,9,2,3)); r((196,140,104),(4,10,1,1)); r((196,140,104),(19,10,1,1))
    if female:
        # Melena hasta los hombros y moño rosa (se ve desde cualquier lado).
        if direccion=='abajo':
            r(hair,(3,7,3,12)); r(hair,(18,7,3,12)); r(hair_hi,(3,8,1,9)); r(hair_hi,(20,8,1,9))
        elif direccion!='arriba':
            r(hair,(3,7,2,6))
        bx=16 if direccion!='izquierda' and direccion!='derecha' else 14
        r(INK,(bx-1,0,8,5)); r(lazo,(bx,1,3,3)); r(lazo,(bx+3,1,3,3)); r(lazo_hi,(bx+2,2,2,1))
    if guard:
        r(INK,(4,3,16,5)); r((69,100,125),(6,2,12,4)); r((225,188,89),(11,3,3,2))
        r((231,189,80),(14,18,3,3))
    if tipo=='profesor':
        r((203,194,169),(6,17,12,6)); r(INK,(7,10,4,3)); r(INK,(13,10,4,3)); r((153,194,199),(8,11,2,1))
    if herramienta=='computacion':
        r(INK,(19,18,5,7)); r((73,181,148),(20,19,3,4)); r(CREAM,(21,20,1,1))
    elif herramienta=='industrial':
        r(INK,(19,18,5,7)); r((227,214,151),(20,19,3,5)); r((113,124,94),(20,21,2,1))
    elif herramienta=='mecatronica':
        r(INK,(18,19,6,6)); r((183,192,212),(19,19,4,4)); r((155,83,255),(20,20,2,1))
        r(INK,(19,24,1,2)); r(INK,(22,24,1,2))
    elif herramienta=='quimica':
        r((197,225,220),(20,17,2,5)); r(INK,(18,21,6,5)); r((228,236,215),(19,21,4,4))
        r((255,154,66),(19,23,4,2))
    if direccion=='derecha': s=pygame.transform.flip(s,True,False)
    return pygame.transform.scale(s,(24*escala,30*escala))

@lru_cache(maxsize=256)
def prop(tipo,w=64,h=64,var=0):
    w,h=max(8,w//2),max(8,h//2)
    s=pygame.Surface((w,h),pygame.SRCALPHA)
    def r(c,x,y,ww,hh): pygame.draw.rect(s,c,(x,y,max(1,ww),max(1,hh)))
    def line(c,a,b,n=1): pygame.draw.line(s,c,a,b,n)
    def box(x,y,ww,hh,c):
        r(INK,x,y,ww,hh); r(c,x+1,y+1,ww-2,hh-3)
        line(tuple(min(255,k+25) for k in c),(x+1,y+1),(x+ww-2,y+1))
    if tipo=='arbol':
        r((72,57,47),w//2-3,h-15,6,15); r((137,101,65),w//2-1,h-13,2,12)
        pts=[(8,3),(13,3),(13,0),(23,0),(23,3),(28,3),(28,8),
             (31,8),(31,21),(28,21),(28,27),(23,27),(23,30),
             (9,30),(9,27),(3,27),(3,22),(0,22),(0,10),(4,10),(4,5),(8,5)]
        pygame.draw.polygon(s,INK,pts)
        pygame.draw.polygon(s,(41,91,79),[(x*.86+w*.07,y*.86+2) for x,y in pts])
        for x,y,ww,hh in ((7,11,13,8),(13,4,13,9),(4,20,12,8),(16,17,15,10),(12,30,14,5)):
            r((73,133,95),x,y,ww,hh); r((116,164,109),x+2,y,ww-5,2)
    elif tipo in ('mesa','banco_plc','pc','mostrador','robot','osciloscopio','cafe_mesa'):
        r((44,59,63),3,h-7,w-3,6)
        for x in (3,w-6): r(INK,x,h-9,3,9)
        box(0,3,w,h-9,(200,208,194) if tipo=='banco_plc' else (166,133,95))
        r((234,236,217),2,4,w-4,3)
        if tipo=='banco_plc':
            box(2,0,w-4,h//2,(38,47,57))
            for x in range(7,w-16,20):
                box(x,3,12,11,(137,158,165)); r((38,74,82),x+2,5,7,4)
                for xx in (x+2,x+5,x+8): r((105,218,166),xx,10,1,1)
                line((218,155,86),(x+4,14),(x+4,h//2+6))
            # Motor, eje y cable en el tablero blanco.
            box(w-24,h-19,12,9,(101,124,133)); r((211,222,211),w-11,h-16,7,2)
            for xx in range(w-22,w-13,3): line(INK,(xx,h-17),(xx,h-12))
            r((52,142,145),2,h-8,w-4,2)
        elif tipo in ('pc','osciloscopio'):
            box(6,0,min(26,w-12),h-15,(42,57,74)); r((81,161,163),9,3,min(20,w-18),max(3,h-22))
            if tipo=='osciloscopio':
                for xx in range(10,min(w-8,28),3): line((192,231,124),(xx,7),(xx+2,11))
            else: r((186,226,194),11,6,min(12,w-20),2)
            r((56,72,81),8,h-13,min(22,w-14),5)
            for xx in range(9,min(w-4,28),3): r((150,170,170),xx,h-12,1,2)
        elif tipo=='robot':
            box(w//2-9,h-23,18,12,(70,91,105))
            line((230,161,74),(w//2,h-17),(w//2-8,8),5)
            line((240,190,96),(w//2-8,8),(w//2+10,4),4)
            r(INK,w//2+8,1,5,6)
        elif tipo=='cafe_mesa':
            box(w//2-6,9,12,10,CREAM); r((83,63,51),w//2-4,10,8,2)
        else:
            r((231,219,175),w//2-8,8,16,9)
            for yy in (10,13): r((119,133,132),w//2-5,yy,10,1)
    elif tipo in ('pizarra','hmi','impresora','servidor','maquina','estante','carrito','caja','cartel'):
        base={'pizarra':(192,226,222),'hmi':(47,63,74),'impresora':(168,185,184),
              'servidor':(69,88,101),'maquina':(66,133,142),'estante':(137,98,72),
              'carrito':(146,181,107),'caja':(178,135,86),'cartel':(207,186,130)}[tipo]
        box(0,0,w,h-3,base)
        if tipo=='pizarra':
            r((235,237,215),2,2,w-4,h-8)
            for yy in range(5,h-10,5):
                r((69,114,128),5,yy,w//2+(yy%3)*3,1)
            r((56,137,162),2,h-5,w-4,2)
        elif tipo in ('hmi','servidor','maquina'):
            for yy in range(3,h-8,9):
                box(3,yy,w-6,7,(112,142,148)); r((32,66,78),5,yy+2,w-13,3)
                r((115,233,160) if var else (236,188,81),w-6,yy+2,2,2)
        elif tipo=='impresora':
            r(INK,3,3,w-6,4); r(CREAM,6,0,w-12,6)
            r((47,62,74),4,h-11,w-8,5); r(CREAM,6,h-9,w-12,8)
            r(TEAL,w-6,10,2,2)
        elif tipo=='estante':
            colors=[(90,159,160),(204,121,96),(216,184,104),(122,139,175)]
            for yy in range(3,h-6,11):
                r((65,57,52),2,yy,w-4,9)
                for xx in range(3,w-4,4):
                    r(colors[(xx//4+yy)%4],xx,yy+1,3,7); r(CREAM,xx,yy+3,2,1)
        elif tipo=='carrito':
            for yy in (4,h//2,h-7):
                r((208,223,156),2,yy,w-4,2)
                box(4,yy-3,7,4,(163,134,91))
        elif tipo=='caja':
            r((224,188,132),w//2-2,1,4,h-5); r(CREAM,3,h//2,8,5)
        else:
            for yy in (4,8,12): r((84,102,100),4,yy,w-8,1)
        for xx in (2,w-5): r(INK,xx,h-3,3,3)
    elif tipo=='silla':
        color=[(210,133,88),(110,165,184),(158,191,117)][var%3]
        line(INK,(w//2,h//2),(w//2,h-2),2)
        line(INK,(2,h-3),(w-2,h-3)); box(1,1,w-2,h//2,color)
        r(tuple(min(255,c+30) for c in color),3,2,w-6,2)
        r(INK,w//2-2,4,4,2)
        for xx in (1,w-3): r(INK,xx,h-3,2,3)
    elif tipo=='extintor':
        r(INK,w//2-5,4,10,h-5); r((198,77,67),w//2-4,6,8,h-8)
        r((247,137,104),w//2-3,7,2,h-11); r(CREAM,w//2-3,h//2,6,4)
        r((159,180,179),w//2-2,1,4,5); line(INK,(w//2+2,3),(w//2+6,h-3))
    elif tipo=='planta':
        box(w//2-6,h-10,12,10,(178,116,82))
        for x,y in ((w//2,4),(w//2-6,8),(w//2+5,10)):
            line((91,126,87),(w//2,h-8),(x,y),2)
            r((80,151,104),x-3,y,7,6); r((151,190,111),x-2,y,3,2)
    elif tipo=='banco':
        for yy in (1,5,9): box(0,yy,w,4,(170,127,82))
        for xx in (3,w-5): r(INK,xx,13,3,h-13)
    elif tipo=='basurero':
        box(2,4,w-4,h-4,(125,147,153)); box(1,1,w-2,6,(45,64,74))
        r((175,194,191),4,9,2,h-12)
    return pygame.transform.scale(s,(w*2,h*2))

@lru_cache(maxsize=32)
def objeto(nombre):
    s=pygame.Surface((16,16),pygame.SRCALPHA)
    def r(c,x,y,w,h): pygame.draw.rect(s,c,(x,y,w,h))
    if nombre=='libro':
        r(INK,2,1,12,14); r((176,84,94),3,2,10,10); r((231,140,127),4,2,2,9)
        r((234,217,172),7,4,4,4); r(CREAM,4,12,9,2); r((156,137,124),5,13,7,1)
    elif nombre=='usb':
        r(INK,5,0,6,15); r((186,210,205),6,1,4,5); r(INK,7,2,1,2); r(INK,9,2,1,2)
        r((67,136,151),4,6,8,8); r((112,201,190),5,7,2,6); r((245,199,111),8,9,2,2)
    elif nombre=='cafe':
        r(INK,2,5,10,9); r(CREAM,3,6,8,7); r((118,79,56),4,6,6,2)
        r(INK,12,6,3,6); r(CREAM,12,7,2,3); r((200,156,106),4,9,6,2)
        r((196,217,202),5,1,1,3); r((196,217,202),8,0,1,3)
    elif nombre=='llaves':
        pygame.draw.circle(s,INK,(5,5),4); pygame.draw.circle(s,(228,187,100),(5,5),3)
        pygame.draw.circle(s,INK,(5,5),1); r(INK,7,7,6,7); r((222,179,97),8,7,2,6)
        r((249,220,147),10,10,3,2); r((249,220,147),10,13,3,1)
    elif nombre=='paraguas':
        pygame.draw.polygon(s,INK,[(1,8),(4,2),(8,0),(12,2),(15,8)])
        pygame.draw.polygon(s,(197,90,121),[(2,7),(5,3),(8,1),(11,3),(14,7)])
        r((245,160,158),7,2,2,5); r(INK,7,8,2,6); r((217,172,111),8,8,1,6)
        r((217,172,111),9,13,3,2); r((217,172,111),11,11,1,3)
    elif nombre=='mochila':
        r(INK,4,1,8,3); r((228,182,104),5,2,6,2); r(INK,2,4,12,11)
        r((178,125,76),3,4,10,10); r((229,175,97),4,5,8,3)
        r((110,80,61),4,10,8,3); r((240,211,140),5,10,6,1)
    # Objetos perdidos de la Torre de Laboratorios (Checkpoint 2).
    elif nombre=='disco_duro':
        r(INK,1,3,14,11); r((96,108,122),2,4,12,9); r((171,184,190),3,5,7,7)
        pygame.draw.circle(s,(214,224,222),(6,8),3); r(INK,6,8,1,1)
        r((105,218,166),12,11,1,1); r((60,70,84),11,5,2,4)
    elif nombre=='calculadora':
        r(INK,3,0,10,16); r((58,66,82),4,1,8,14); r((150,201,140),5,2,6,3)
        for yy in (7,10,13):
            for xx in (5,8,10): r((220,214,190) if xx<10 else (232,140,88),xx,yy,2,2)
    elif nombre=='bata':
        pygame.draw.polygon(s,INK,[(4,1),(12,1),(15,6),(13,15),(3,15),(1,6)])
        pygame.draw.polygon(s,(236,238,230),[(5,2),(11,2),(14,6),(12,14),(4,14),(2,6)])
        r((178,196,196),7,2,2,12); r((92,152,190),10,8,2,2); r(INK,7,3,2,1)
    elif nombre=='trofeo':
        r(INK,3,1,10,8); r((246,196,82),4,2,8,6); r((255,236,150),5,2,2,5)
        r(INK,1,2,3,4); r(INK,12,2,3,4); r((246,196,82),2,3,1,2); r((246,196,82),13,3,1,2)
        r(INK,7,9,2,3); r((214,160,60),7,9,2,3); r(INK,4,12,8,3); r((120,84,56),5,12,6,2)
    elif nombre=='tarjeta':
        r(INK,1,3,14,10); r((72,148,232),2,4,12,8); r((236,231,205),3,6,4,4)
        r((227,174,130),4,6,2,2); r((236,231,205),8,6,5,1); r((236,231,205),8,8,4,1)
        r((246,196,82),8,10,3,1)
    elif nombre=='audifonos':
        pygame.draw.arc(s,INK,(2,1,12,12),0,3.15,3); pygame.draw.arc(s,(197,90,121),(3,2,10,10),0,3.15,1)
        r(INK,1,7,4,7); r((197,90,121),2,8,2,5); r(INK,11,7,4,7); r((197,90,121),12,8,2,5)
    else:
        r(INK,2,2,12,12); r(TEAL,3,3,10,10); r(CREAM,5,5,6,2)
    return s

def dibujar_objeto(s,nombre,centro,tamano=32):
    im=pygame.transform.scale(objeto(nombre),(tamano,tamano))
    s.blit(im,im.get_rect(center=centro))

@lru_cache(maxsize=16)
def baldosa(tipo='piedra',var=0):
    s=pygame.Surface((16,16))
    if tipo=='hierba':
        s.fill((60+var*3,103+var*2,80))
        for x,y in ((2,3),(10,8),(5,13)):
            pygame.draw.rect(s,(90,139,92),(x,y,1,2)); pygame.draw.rect(s,(48,90,75),(x+2,y+1,2,1))
    else:
        base=(194,201,194) if tipo=='interior' else (145,165,153)
        s.fill(tuple(c+var*2 for c in base))
        juntas=(167,181,175) if tipo=='interior' else (126,148,140)
        pygame.draw.rect(s,juntas,(0,0,16,16),1)
        pygame.draw.line(s,(214,220,207),(1,1),(14,1))
        pygame.draw.rect(s,tuple(min(255,c+6) for c in base),(3,4,10,9))
    return pygame.transform.scale(s,(32,32))

def suelo(s,rect,tipo='piedra'):
    clip=s.get_clip(); s.set_clip(rect)
    x,y,w,h=rect
    for yy in range(y,y+h,32):
        for xx in range(x,x+w,32):
            s.blit(baldosa(tipo,(xx//32+yy//32)%3),(xx,yy))
    s.set_clip(clip)
