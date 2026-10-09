"""Campus cacheado: tejados, fachadas, jardines y señalización del plano."""
from functools import lru_cache
import pygame
from arte_pixel import prop, suelo, texto, caja, INK, CREAM
from identidad_key import dibujar_key, emblema, AZUL_KEY
from carreras import CARRERAS
from mapa_nivel1 import (MUNDO_ANCHO,MUNDO_ALTO,SALAS_RECT,NOMBRES,COLORES_SALA,
    ZONAS_CAMINABLES,PUERTAS,SALIDAS,GRADAS_TRIGGER,POLIGONOS_SALA,PASILLO_DIAGONAL,DECORACION)

@lru_cache(maxsize=1)
def campus():
    s=pygame.Surface((MUNDO_ANCHO,MUNDO_ALTO)); s.fill((30,56,59))
    suelo(s,(0,0,MUNDO_ANCHO,MUNDO_ALTO),'hierba')
    shade=pygame.Surface(s.get_size(),pygame.SRCALPHA); shade.fill((16,32,44,105)); s.blit(shade,(0,0))
    for rect in ZONAS_CAMINABLES:
        suelo(s,rect)
    pygame.draw.polygon(s,(143,164,152),PASILLO_DIAGONAL)
    pygame.draw.lines(s,(195,206,181),True,PASILLO_DIAGONAL,3)
    # Jardines abiertos y senderos discretos; las salas siguen el croquis.
    for nombre in ('jardin_central','jardin_oeste'):
        x,y,w,h=SALAS_RECT[nombre]
        suelo(s,(x,y,w,h),'hierba')
        pygame.draw.rect(s,(180,186,147),(x,y,w,h),4)
        pygame.draw.rect(s,(144,160,128),(x,y+h//2-18,w,36))
        pygame.draw.rect(s,(144,160,128),(x+w//2-18,y,36,h))
        texto(s,NOMBRES[nombre].upper(),(x+w//2,y+h//2),(38,71,65),12,True)
    abiertos={'jardin_central','jardin_oeste','terraza','lobby'}
    for nombre,rect in SALAS_RECT.items():
        if nombre in abiertos: continue
        x,y,w,h=rect; color=COLORES_SALA[nombre]
        if nombre=='gradas':
            pygame.draw.rect(s,INK,rect)
            for yy in range(y+6,y+h-6,10):
                pygame.draw.rect(s,(161,179,170),(x+4,yy,w-8,7))
                pygame.draw.line(s,CREAM,(x+4,yy),(x+w-4,yy),2)
            continue
        # Componer cada tejado en su propia capa permite recortar la diagonal.
        roof=pygame.Surface((w,h),pygame.SRCALPHA)
        roof.fill((45,65,74))
        pygame.draw.rect(roof,(210,205,171),(0,h-34,w,34))
        pygame.draw.rect(roof,(139,151,138),(0,h-8,w,8))
        pygame.draw.rect(roof,tuple(max(0,c-32) for c in color),(0,0,w,h-32))
        for yy in range(4,h-34,12):
            pygame.draw.line(roof,color,(3,yy),(w-4,yy),4)
            for xx in range(4+(6 if (yy//12)%2 else 0),w-4,24):
                pygame.draw.line(roof,tuple(max(0,c-20) for c in color),(xx,yy+4),(xx,yy+10),2)
        pygame.draw.rect(roof,(209,212,182),(0,0,w,5))
        pygame.draw.rect(roof,(38,64,72),(0,h-36,w,5))
        for xx in range(16,w-30,64):
            caja(roof,(xx,h-27,34,16),(94,154,161),(103,125,126))
            pygame.draw.line(roof,(209,225,194),(xx+17,h-25),(xx+17,h-13),2)
        if nombre in POLIGONOS_SALA:
            mask=pygame.Surface((w,h),pygame.SRCALPHA)
            pygame.draw.polygon(mask,(255,255,255),[(px-x,py-y) for px,py in POLIGONOS_SALA[nombre]])
            roof.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
        else:
            pygame.draw.rect(s,(26,46,52),(x+6,y+8,w,h))
        s.blit(roof,(x,y))
        if w>=120:
            label=NOMBRES[nombre].upper()
            size=14 if w>180 else 12
            tw=len(label)*(size*.61)+18
            caja(s,(x+(w-tw)//2,y+max(12,(h-32)//2-12),tw,26),(38,62,73),color)
            texto(s,label,(x+w//2,y+max(25,(h-32)//2+1)),CREAM,size,True)
    for data in PUERTAS.values():
        x,y,w,h=data['trigger']
        caja(s,(x-2,y-2,w+4,h+4),(40,61,70),(220,205,157))
        pygame.draw.rect(s,(101,166,166),(x+4,y+4,w-8,h-8))
        pygame.draw.rect(s,(189,219,194),(x+6,y+6,w-12,4))
        pygame.draw.rect(s,CREAM,(x+w-9,y+h//2,3,5))
    for data in SALIDAS.values():
        x,y,w,h=data['trigger']
        caja(s,(x,y,w,h),(46,110,92),(148,191,145))
        texto(s,'SALIDA',(x+w//2,y+h//2),CREAM,12,True)
    for name in ('terraza','lobby'):
        x,y,w,h=SALAS_RECT[name]
        if name=='lobby':
            dibujar_key(s,(784,786),color=(38,65,74))
            texto(s,'LOBBY',(x+w//2,y+h-12),(48,79,78),12,True)
        else:
            texto(s,name.upper(),(x+w//2,y+h//2),(48,79,78),16,True)
    # Equipamiento exterior, ubicado fuera de los pasos de las puertas.
    for tipo,(x,y,w,h) in DECORACION:
        s.blit(prop(tipo,w,h),(x,y))
    for x,y in ((700,244),(1044,216),(700,636),(1040,652)):
        s.blit(prop('extintor',16,28),(x,y))
    texto(s,'INSTITUTO KRIETE',(1120,992),(165,188,164),16,True)
    texto(s,'1er NIVEL',(1120,1016),(120,154,140),12,True)
    # Mural de las cuatro carreras fuera de la circulación; identidad del campus.
    caja(s,(360,848,272,94),(27,49,65),AZUL_KEY)
    texto(s,'INGENIERÍA Y CIENCIAS',(496,864),CREAM,12,True)
    for i,c in enumerate(CARRERAS):
        emblema(s,c.id,(396+i*66,904),36,c.color)
    return s

def dibujar_overworld(pantalla,camara,fuentes_chica=None):
    pantalla.fill((21,39,48))
    pantalla.blit(campus(),(-int(camara[0]),-int(camara[1])))
