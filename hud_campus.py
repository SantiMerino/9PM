"""HUD, mapa y bitácora: paneles legibles y controles de exploración."""
import math
import pygame
from arte_pixel import texto,caja,fuente,dibujar_objeto,CREAM,TEAL,INK
from mapa_nivel1 import NOMBRES,PUERTAS,MUNDO_ANCHO,MUNDO_ALTO
from mundo_visual import campus
from interiores import interactivo_cercano
from estado_mundo import formatear_hora


def lineas(cadena,ancho,size=14):
    result=[]; actual=''
    for word in cadena.split():
        candidate=(actual+' '+word).strip()
        if fuente(size).size(candidate)[0]>ancho and actual:
            result.append(actual); actual=word
        else: actual=candidate
    if actual: result.append(actual)
    return result

def objetivo(p):
    if p.ubicacion=='interior':
        return next((m for m in p.mision.hijas if m.ubicacion==p.sala_interior),None)
    return next((m for m in p.mision.hijas if not m.completada),None)

def contexto(p):
    if p.ubicacion=='interior':
        i=interactivo_cercano(p.interior_data,*p.jugador.pos)
        return i['label'] if i else 'Acércate a una estación marcada'
    from mapa_nivel1 import puerta_en,GRADAS_TRIGGER
    pid=puerta_en(*p.jugador.pos)
    if pid: return 'Entrar a '+NOMBRES[pid]
    gx,gy,gw,gh=GRADAS_TRIGGER
    if math.hypot(p.jugador.x-gx-gw/2,p.jugador.y-gy-gh/2)<70:
        return 'Subir a la Torre de Laboratorios (2º nivel)'
    obj=p._objeto_cercano()
    if obj: return 'Recoger '+obj['nombre']
    return 'Explora el campus'

_MINIMAPA=None
def dibujar_hud(s,p,fuentes=None):
    global _MINIMAPA
    pygame.draw.rect(s,INK,(0,0,960,64)); pygame.draw.rect(s,TEAL,(0,62,960,2))
    texto(s,'9PM',(20,12),(241,199,116),24)
    lugar=p.interior_data['titulo'] if p.ubicacion=='interior' else 'INSTITUTO KRIETE · NIVEL 1'
    texto(s,lugar,(96,12),CREAM,16)
    m=objetivo(p)
    caption=m.objetivo_actual if m else 'Todo listo. Sal por el lobby o la terraza.'
    for l in lineas(caption,470,12)[:1]: texto(s,l,(96,38),(162,194,185),12)
    color=(239,124,100) if p.estado_mundo['toque_queda_activo'] else CREAM
    texto(s,formatear_hora(p.estado_mundo['hora_actual_min']),(626,9),color,24)
    done=sum(m.completada for m in p.mision.hijas)
    texto(s,f'{done:02}/{len(p.mision.hijas)} ENCARGOS',(626,39),TEAL,12)
    if p.ubicacion=='pasillo':
        if _MINIMAPA is None: _MINIMAPA=pygame.transform.scale(campus(),(174,120))
        caja(s,(768,78,180,150),INK)
        s.blit(_MINIMAPA,(771,81))
        x=771+p.jugador.x*174/MUNDO_ANCHO; y=81+p.jugador.y*120/MUNDO_ALTO
        pygame.draw.rect(s,CREAM,(x-3,y-3,6,6)); pygame.draw.rect(s,(217,107,80),(x-1,y-1,2,2))
        texto(s,'M  MAPA DEL CAMPUS',(780,208),CREAM,12)
    pygame.draw.rect(s,INK,(0,592,960,48)); pygame.draw.rect(s,TEAL,(0,592,960,2))
    texto(s,'ESPACIO',(18,603),(241,199,116),14)
    label=contexto(p)
    texto(s,lineas(label,410,12)[0],(106,605),CREAM,12)
    texto(s,'M mapa  J misiones  H historial  Z deshacer',(534,605),(164,193,187),12)
    h=p.habilidad
    estado=(f'ACTIVA {math.ceil(h.activa)} s' if h.activa>0 else
            f'RECARGA {math.ceil(h.recarga)} s' if h.recarga>0 else 'LISTA')
    texto(s,f'[Q] {h.perfil.habilidad} / {h.perfil.corto}',(18,623),h.perfil.color,12)
    texto(s,estado,(488,623),CREAM,12)
    pygame.draw.rect(s,(59,81,92),(622,624,140,7))
    pygame.draw.rect(s,h.perfil.color,(622,624,int(140*(1-h.recarga/h.perfil.recarga)),7))
    texto(s,'F1 ayuda · ESC pausa',(790,623),(164,193,187),12)
    if p.toasts:
        lines=lineas(p.toasts[0].texto,660,14)
        h=30+20*len(lines)
        caja(s,(24,580-h,704,h),(32,57,68),(147,184,175))
        texto(s,'CAMPUS / AVISO',(40,588-h),TEAL,11)
        for i,l in enumerate(lines): texto(s,l,(40,607-h+i*20),CREAM,14)

VERDE=(104,214,132)
VERDE_OSCURO=(30,78,54)
DORADO=(240,194,105)

def dibujar_check(s,x,y,t=12,color=VERDE):
    """Palomita dibujada con líneas (la fuente no tiene el carácter ✓)."""
    pts=[(x,y+t*.55),(x+t*.38,y+t*.92),(x+t,y+t*.08)]
    pygame.draw.lines(s,INK,False,pts,5)
    pygame.draw.lines(s,color,False,pts,3)

def insignia_completada(s,derecha,y,texto_insignia='COMPLETADA'):
    """Sello verde con palomita para los encargos terminados."""
    ancho=fuente(11).size(texto_insignia)[0]+34
    r=pygame.Rect(derecha-ancho,y,ancho,20)
    pygame.draw.rect(s,INK,r.move(0,2)); pygame.draw.rect(s,VERDE,r)
    pygame.draw.rect(s,(176,240,190),(r.x+2,r.y+2,r.w-4,2))
    pygame.draw.rect(s,INK,r,2)
    dibujar_check(s,r.x+6,r.y+4,11,(255,255,255))
    texto(s,texto_insignia,(r.x+24,r.y+4),INK,11)
    return r

def dibujar_mapa(s,p):
    overlay=pygame.Surface((960,640),pygame.SRCALPHA); overlay.fill((8,20,30,235)); s.blit(overlay,(0,0))
    texto(s,'PLANO DEL CAMPUS',(28,22),CREAM,24)
    texto(s,'Primer nivel · distribución del plano de referencia',(28,54),(161,191,181),13)
    scale=.48; ox,oy=20,88
    s.blit(pygame.transform.scale(campus(),(int(MUNDO_ANCHO*scale),int(MUNDO_ALTO*scale))),(ox,oy))
    for m in p.mision.hijas:
        x,y=PUERTAS[m.ubicacion]['retorno']
        cx,cy=int(ox+x*scale),int(oy+y*scale)
        if m.completada:
            pygame.draw.circle(s,INK,(cx,cy),8); pygame.draw.circle(s,VERDE,(cx,cy),6)
            dibujar_check(s,cx-4,cy-4,8,(255,255,255))
        else:
            pygame.draw.circle(s,INK,(cx,cy),6); pygame.draw.circle(s,DORADO,(cx,cy),4)
    pos=PUERTAS[p.sala_interior]['retorno'] if p.ubicacion=='interior' else p.jugador.pos
    x,y=ox+pos[0]*scale,oy+pos[1]*scale
    pygame.draw.circle(s,INK,(int(x),int(y)),7); pygame.draw.circle(s,CREAM,(int(x),int(y)),4)
    hechas=sum(m.completada for m in p.mision.hijas)
    texto(s,f'DESTINOS  {hechas}/{len(p.mision.hijas)}',(772,98),TEAL,16)
    for i,m in enumerate(p.mision.hijas):
        y=126+i*29
        if m.completada:
            pygame.draw.rect(s,VERDE_OSCURO,(766,y-3,182,24)); pygame.draw.rect(s,VERDE,(766,y-3,4,24))
            dibujar_check(s,776,y+2,12)
            texto(s,NOMBRES[m.ubicacion],(796,y+2),(176,240,190),13)
        else:
            pygame.draw.rect(s,DORADO,(778,y+5,8,8))
            texto(s,NOMBRES[m.ubicacion],(796,y+2),CREAM,13)
    texto(s,'Blanco: tú   Dorado: pendiente   Verde con palomita: completado',(28,604),CREAM,13)
    texto(s,'M / ESC cerrar · PAUSA',(694,604),TEAL,13)

def recortar(cadena,ancho,size):
    """Corta el texto para que quepa en `ancho` px y agrega '…' si sobró."""
    cadena=str(cadena or '')
    if fuente(size).size(cadena)[0]<=ancho: return cadena
    while cadena and fuente(size).size(cadena+'…')[0]>ancho: cadena=cadena[:-1]
    return cadena.rstrip()+'…'

def _filas_preorden(raiz):
    """Preorden (nivel, misión): se usa si misiones.py aún no trae lineas_preorden."""
    filas=[]; pila=[(0,raiz)]
    while pila:
        nivel,nodo=pila.pop(); filas.append((nivel,nodo))
        pila.extend((nivel+1,h) for h in reversed(getattr(nodo,'hijas',())))
    return filas

def _niveles(raiz):
    """Recorrido por niveles: se usa si misiones.py aún no trae por_niveles."""
    niveles=[]; actual=[raiz]
    while actual:
        niveles.append(actual)
        actual=[h for nodo in actual for h in getattr(nodo,'hijas',())]
    return niveles

def _encargos(p):
    encargos=getattr(p,'encargos',None)
    if encargos is not None: return list(encargos)
    return [m for _,m in _filas_preorden(p.mision)[1:] if getattr(m,'ubicacion',None)]

def _estado_mision(m,p,encargos):
    """'completada', 'disponible' o 'bloqueada' según el árbol de dependencias."""
    if getattr(m,'completada',False): return 'completada'
    if m is p.mision and m not in encargos:
        # La raíz es la salida: se abre cuando ya no queda ningún encargo.
        return 'disponible' if all(getattr(e,'completada',False) for e in encargos) else 'bloqueada'
    desbloqueada=getattr(m,'desbloqueada',None)
    if callable(desbloqueada): return 'disponible' if desbloqueada() else 'bloqueada'
    padre=getattr(m,'padre',None)  # sin contrato CP3 las misiones no dependen entre sí
    return 'bloqueada' if padre is not None and not getattr(padre,'completada',False) else 'disponible'

def dibujar_diario(s,p):
    """Bitácora: el árbol de misiones en preorden, con sangría y conectores."""
    overlay=pygame.Surface((960,640),pygame.SRCALPHA); overlay.fill((8,20,30,235)); s.blit(overlay,(0,0))
    texto(s,'BITÁCORA DE LA NOCHE',(28,22),CREAM,24)
    texto(s,'Cada misión se desbloquea al completar la misión de la que depende.',(28,58),(156,187,177),13)
    encargos=_encargos(p)
    hechas=sum(bool(getattr(m,'completada',False)) for m in encargos); total=len(encargos)
    texto(s,f'{hechas}/{total} COMPLETADAS',(676,20),VERDE if hechas else CREAM,16)
    pygame.draw.rect(s,INK,(676,44,256,12)); pygame.draw.rect(s,(52,72,80),(678,46,252,8))
    if total: pygame.draw.rect(s,VERDE,(678,46,int(252*hechas/total),8))

    try:
        from misiones import lineas_preorden
        filas=lineas_preorden(p.mision)
    except ImportError:
        filas=_filas_preorden(p.mision)
    try:
        from misiones import por_niveles
        niveles=por_niveles(p.mision)
    except ImportError:
        niveles=_niveles(p.mision)

    MAX_FILAS,ALTO,Y0,SANGRIA=14,30,88,22
    visibles=filas[:MAX_FILAS]
    xs=[28+nivel*SANGRIA for nivel,_ in visibles]
    ys=[Y0+i*(ALTO+4) for i in range(len(visibles))]
    # Conectores primero (├─ / └─): de cada hija a la fila de su madre.
    ultima_en_nivel={}
    for i,(nivel,_) in enumerate(visibles):
        madre=ultima_en_nivel.get(nivel-1)
        if madre is not None:
            cx=xs[madre]+10; cy=ys[i]+ALTO//2
            pygame.draw.line(s,(84,118,123),(cx,ys[madre]+ALTO),(cx,cy),2)
            pygame.draw.line(s,(84,118,123),(cx,cy),(xs[i],cy),2)
        ultima_en_nivel[nivel]=i
        for n in [k for k in ultima_en_nivel if k>nivel]: del ultima_en_nivel[n]

    for i,(nivel,m) in enumerate(visibles):
        x,y=xs[i],ys[i]; ancho=932-x
        estado=_estado_mision(m,p,encargos)
        if estado=='completada':
            caja(s,(x,y,ancho,ALTO),VERDE_OSCURO,VERDE); pygame.draw.rect(s,VERDE,(x,y,4,ALTO))
            dibujar_check(s,x+10,y+9,12)
            color=(196,246,206); detalle='completada'; color_detalle=(150,208,166)
        elif estado=='disponible':
            caja(s,(x,y,ancho,ALTO),(34,59,69),(84,118,123))
            pasos=len(getattr(m,'pasos',()) or ())
            if pasos: texto(s,f'{getattr(m,"paso",0)}/{pasos}',(x+8,y+9),DORADO,11)
            else: pygame.draw.rect(s,DORADO,(x+12,y+11,8,8))
            obj=getattr(m,'objetivo_actual','')
            color=CREAM; detalle=obj() if callable(obj) else obj; color_detalle=(169,195,181)
        else:
            caja(s,(x,y,ancho,ALTO),(31,43,49),(63,76,80))
            gris=(153,166,164)
            pygame.draw.arc(s,gris,(x+12,y+5,10,11),0,math.pi,2)
            pygame.draw.rect(s,gris,(x+10,y+11,14,11),1)
            padre=getattr(m,'padre',None)
            color=gris; color_detalle=gris
            detalle=f'bloqueada · primero: {padre.titulo}' if getattr(padre,'titulo',None) else 'bloqueada'
        ubicacion=getattr(m,'ubicacion',None)
        nombre=NOMBRES.get(ubicacion,ubicacion or 'MISIÓN PRINCIPAL').upper()
        ancho_titulo=max(80,int((ancho-44)*.48))
        texto(s,recortar(f'{nombre} / {getattr(m,"titulo","")}',ancho_titulo,11),(x+36,y+9),color,11)
        x_det=x+44+ancho_titulo
        texto(s,recortar(detalle,932-x_det-10,10),(x_det,y+10),color_detalle,10)
    if len(filas)>MAX_FILAS:
        texto(s,f'+{len(filas)-MAX_FILAS} misiones más',(704,574),(156,187,177),11)

    # Etapas = niveles del árbol sin la raíz; la salida (raíz) es la última etapa.
    etapas=[[m for m in nivel if m is not p.mision] for nivel in niveles]
    etapas=[e for e in etapas if e]
    if p.mision not in encargos and etapas: etapas.append([p.mision])
    etapa=next((i+1 for i,e in enumerate(etapas) if any(not getattr(m,'completada',False) for m in e)),len(etapas))
    texto(s,f'ETAPA {max(etapa,1)} DE {max(len(etapas),1)}',(28,572),DORADO,14)

    todas=[m for _,m in filas]
    if any(hasattr(m,'recompensa') for m in todas):
        acumulada=sum(getattr(m,'recompensa',0) or 0 for m in todas if getattr(m,'completada',False))
        try:
            from misiones import recompensa_rama
            maxima=recompensa_rama(p.mision)
        except ImportError:
            maxima=sum(getattr(m,'recompensa',0) or 0 for m in todas)
        texto(s,f'RECOMPENSA ACUMULADA  {acumulada}/{maxima}',(220,572),TEAL,13)
    texto(s,'J / ESC cerrar · PAUSA',(704,604),TEAL,13)


def dibujar_efecto_habilidad(s,p,camara):
    h=p.habilidad
    px,py=int(p.jugador.x-camara[0]),int(p.jugador.y-camara[1])
    if h.activa>0:
        pygame.draw.ellipse(s,h.perfil.color,(px-20,py-8,40,12),2)
        for i in range(3):
            dx=int(math.sin(p.tiempo_animacion*3+i*2)*25)
            pygame.draw.rect(s,h.perfil.color,(px+dx,py-20-i*13,3,3))
    if h.destello>0 and h.escena==(p.ubicacion,p.sala_interior):
        tx,ty=int(h.destino[0]-camara[0]),int(h.destino[1]-camara[1])
        for i in range(0,20,2):
            a=(px+(tx-px)*i/20,py-18+(ty-py+18)*i/20)
            b=(px+(tx-px)*(i+1)/20,py-18+(ty-py+18)*(i+1)/20)
            pygame.draw.line(s,h.perfil.color,a,b,2)
        pygame.draw.circle(s,h.perfil.color,(tx,ty),18,2)


def dibujar_pausa(s,p):
    from menu_inicio import boton
    overlay=pygame.Surface((960,640),pygame.SRCALPHA)
    overlay.fill((8,20,30,220)); s.blit(overlay,(0,0))
    texto(s,'PAUSA',(480,180),CREAM,44,True)
    texto(s,'El campus puede esperar un momento.',(480,238),TEAL,15,True)
    boton(s,(280,282,400,48),'CONTINUAR  /  ENTER',True,p.habilidad.perfil.color)
    boton(s,(280,344,400,48),'VOLVER A LA PORTADA  /  H',size=16)
    boton(s,(280,406,400,48),'SALIR DEL JUEGO',size=16)
    texto(s,'Volver a la portada termina la partida actual.',(480,486),(187,199,183),13,True)
    texto(s,'ESC para continuar · F1 repite el tutorial',(480,520),TEAL,13,True)
