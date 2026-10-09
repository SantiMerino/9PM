"""Señalética pixelada de KEY y emblemas de carrera basados en la referencia."""
import math
import pygame
from arte_pixel import texto

AZUL_KEY = (24, 113, 244)

def dibujar_key(s, pos, escala=1, color=(233,238,230)):
    x,y=pos
    centro=(x+16*escala,y+18*escala)
    for i in range(6):
        a=math.pi/3*i-math.pi/2
        start=(centro[0]+5*escala*math.cos(a),centro[1]+5*escala*math.sin(a))
        end=(centro[0]+18*escala*math.cos(a),centro[1]+18*escala*math.sin(a))
        pygame.draw.line(s,AZUL_KEY,start,end,max(2,3*escala))
    texto(s,'key',(x+40*escala,y-2*escala),color,32*escala)

def emblema(s, clave, centro, tam, color):
    x,y=centro[0]-tam/2,centro[1]-tam/2
    formas={
        'computacion': [[(45,4),(12,24),(12,46),(42,64),(42,50),(24,40),(24,31),(57,12)],
                       [(58,39),(88,57),(88,79),(55,99),(44,91),(76,71),(76,64),(58,53)]],
        'industrial': [[(6,14),(42,35),(42,65),(6,86),(18,94),(56,72),(56,28),(6,0)],
                       [(94,0),(58,21),(58,65),(94,86),(94,71),(72,58),(72,30),(100,13)]],
        'mecatronica': [[(0,28),(34,8),(55,20),(55,56),(80,42),(100,53),(100,90),
                        (89,97),(89,62),(80,57),(44,78),(44,29),(34,23),(12,36)]],
        'quimica': [[(18,20),(48,2),(75,18),(65,26),(48,16),(29,27),(29,74),(48,85),
                    (64,75),(64,89),(48,99),(18,81)],
                   [(57,36),(87,54),(87,75),(67,88),(67,74),(77,68),(77,60),(47,42)]],
    }
    for points in formas[clave]:
        pygame.draw.polygon(s,color,[(int(x+px*tam/100),int(y+py*tam/100)) for px,py in points])
