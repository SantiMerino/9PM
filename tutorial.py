"""Tutorial de bienvenida (onboarding) con focos sobre la interfaz real.

La primera vez que juegas aparece un recorrido corto por el campus y la
primera vez que subes a la Torre, otro por la pantalla de turnos. Cada paso
oscurece la pantalla, deja iluminada la parte de la interfaz que explica y
muestra una tarjeta con una ilustración en pixel art. F1 lo repite cuando
quieras.

    ENTER / ESPACIO / → / clic   siguiente
    ← / RETROCESO                 atrás
    ESC                           saltar el tutorial

Qué tutoriales ya se vieron se guarda en `tutorial.json` (archivo generado).
"""
import json
import math
from functools import lru_cache

import pygame
from arte_pixel import texto, caja, personaje, prop, dibujar_objeto, objeto as sprite_objeto, CREAM, TEAL, INK
from sprites_jugador import sprite_estudiante
from hud_campus import lineas
from mapa_nivel1 import SALAS_RECT, MUNDO_ANCHO, MUNDO_ALTO
import ui_torre

ORO = (241, 199, 116)
ROJO = (239, 124, 100)
AZUL = (110, 165, 184)
TENUE = (162, 194, 185)
FONDO_ILUSTRACION = (18, 30, 44)
VISTA_MUNDO = pygame.Rect(0, 64, 960, 528)


# --------------------------------------------------------------------------
# Progreso (qué tutoriales ya se vieron)
# --------------------------------------------------------------------------
def cargar_progreso(ruta):
    """Lee el diccionario {contexto: True}; si no existe o está dañado, {}."""
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        return datos if isinstance(datos, dict) else {}
    except (OSError, ValueError):
        return {}


def guardar_progreso(ruta, datos):
    """Guarda el progreso sin romper el juego si no se puede escribir."""
    try:
        ruta.write_text(json.dumps(datos, indent=2), encoding="utf-8")
    except OSError:
        pass


# --------------------------------------------------------------------------
# Focos: la parte de la pantalla que queda iluminada en cada paso
# --------------------------------------------------------------------------
def _foco_jugador(p, camara):
    x, y = p.jugador.x - camara[0], p.jugador.y - camara[1]
    return pygame.Rect(int(x) - 46, int(y) - 86, 92, 100)


def _foco_gradas(p, camara):
    x, y, w, h = SALAS_RECT['gradas']
    foco = pygame.Rect(x - camara[0] - 12, y - camara[1] - 10, w + 24, h + 54)
    return foco if VISTA_MUNDO.contains(foco) else None


def _foco_puertas(p, camara):
    hijas = [rect for _, _, rect, tipo in ui_torre.puertas_escena(p) if tipo == 'hija']
    if not hijas:
        return None
    foco = hijas[0].unionall(hijas[1:]).inflate(140, 0)
    foco.top, foco.height = ui_torre.ESCENA.y + 2, ui_torre.MURO_ALTO
    return foco.clip(ui_torre.ESCENA)


def _foco_regreso(p, camara):
    rect = next(rect for _, _, rect, tipo in ui_torre.puertas_escena(p) if tipo != 'hija')
    return rect.inflate(60, 60).move(26, -16).clip(ui_torre.ESCENA)


PASOS = {
    'campus': [
        dict(dibujo='bienvenida', titulo='Son las 20:15 en KEY',
             texto='Tienes hasta las 21:00 para resolver 13 encargos y salir por el lobby o la terraza. '
                   'Después del toque de queda, si un vigilante te ve, te expulsan.'),
        dict(dibujo='mover', foco=_foco_jugador, titulo='Este eres tú',
             texto='Camina con WASD o las flechas. Pisa una puerta para entrar a esa sala.'),
        dict(dibujo='espacio', foco=pygame.Rect(6, 596, 516, 24), titulo='ESPACIO hace casi todo',
             texto='Entrar, recoger objetos y usar estaciones. Aquí abajo siempre dice qué va a pasar.'),
        dict(dibujo='encargos', foco=pygame.Rect(88, 2, 690, 60), titulo='Qué hacer y cuánto tiempo queda',
             texto='Arriba ves tu objetivo, la hora y tus encargos. J abre la bitácora con los 13.'),
        dict(dibujo='mapa', foco=pygame.Rect(764, 74, 188, 158), titulo='¿Perdido?',
             texto='M abre el plano del campus con todos los encargos marcados.'),
        dict(dibujo='bolsa', foco=pygame.Rect(776, 4, 172, 50), titulo='Tu bolsa',
             texto='Caben 6 objetos. Ábrela con I o con un clic. G suelta el último objeto.'),
        dict(dibujo='pila', foco=pygame.Rect(526, 596, 330, 24), titulo='¿Te equivocaste? Deshazlo',
             texto='Z deshace tu última acción: si entraste a una sala, te regresa. H muestra tu historial.'),
        dict(dibujo='gradas', foco=_foco_gradas, titulo='Las gradas suben a la Torre',
             texto='Un segundo nivel que cambia cada noche. Allá se juega por turnos y hay objetos perdidos.'),
        dict(dibujo='listo', titulo='¡A jugar!',
             texto='Empieza por el libro del lobby: la flecha dorada te lo señala. '
                   'F1 repite este tutorial cuando quieras.'),
    ],
    'torre': [
        dict(dibujo='turnos', titulo='Bienvenido a la Torre',
             texto='Aquí arriba se juega por turnos: cada vez que te mueves, el vigilante y el robot '
                   'también se mueven y pasa 1 minuto del reloj.'),
        dict(dibujo='puertas', foco=_foco_puertas, titulo='Elige una puerta',
             texto='Haz clic en una puerta para cruzarla. La placa dice a qué sala lleva. '
                   'Con teclado: 1, ENTER y el número de la puerta.'),
        dict(dibujo='volver', foco=_foco_regreso, titulo='Por aquí se regresa',
             texto='La puerta de abajo vuelve a la sala anterior. En el rellano, las gradas bajan al campus.'),
        dict(dibujo='acciones', foco=ui_torre.BARRA.inflate(8, 8), titulo='Tus acciones',
             texto='2 recoge objetos, 4 deshace tu último paso (te regresa de sala) y 6, 7 y 8 '
                   'muestran historial, turnos y eventos.'),
        dict(dibujo='eventos', foco=ui_torre.REGISTRO.union(ui_torre.ENTRADA).inflate(8, 8),
             titulo='Cada paso trae un evento',
             texto='Trampas, cámaras, apagones y pistas salen de una cola, en orden. Aquí lees lo que pasó.'),
        dict(dibujo='tesoro', foco=ui_torre.MAPA.inflate(8, 8), titulo='El plano de la Torre',
             texto='TÚ eres tú, V el vigilante y R el robot. Las salas con rombo, las más profundas, '
                   'esconden objetos perdidos que dan puntos.'),
        dict(dibujo='vigilante', foco=pygame.Rect(8, 594, 400, 44), titulo='Cuidado con el vigilante',
             texto='Si te alcanza antes de las 21:00 te sermonea y pierdes 3 minutos. '
                   'Después de las 21:00, te expulsa.'),
        dict(dibujo='listo', titulo='¡Suerte allá arriba!',
             texto='Para bajar, regresa al rellano y cruza las gradas. F1 repite este tutorial.'),
    ],
}


# --------------------------------------------------------------------------
# Piezas de las ilustraciones
# --------------------------------------------------------------------------
def tecla(s, rect, etiqueta, presionada=False, size=14):
    """Tecla de teclado en pixel art."""
    r = pygame.Rect(rect)
    pygame.draw.rect(s, INK, r.move(0, 4))
    cara = r.move(0, 3 if presionada else 0)
    pygame.draw.rect(s, (236, 214, 150) if presionada else (198, 206, 198), cara)
    pygame.draw.rect(s, INK, cara, 2)
    pygame.draw.line(s, (244, 246, 234), (cara.x + 4, cara.y + 4), (cara.right - 5, cara.y + 4), 2)
    texto(s, etiqueta, cara.center, INK, size, True)


def _flecha(s, origen, destino, color=ORO, grosor=4):
    pygame.draw.line(s, INK, origen, destino, grosor + 3)
    pygame.draw.line(s, color, origen, destino, grosor)
    ang = math.atan2(destino[1] - origen[1], destino[0] - origen[0])
    punta = [destino,
             (destino[0] - 14 * math.cos(ang - .5), destino[1] - 14 * math.sin(ang - .5)),
             (destino[0] - 14 * math.cos(ang + .5), destino[1] - 14 * math.sin(ang + .5))]
    pygame.draw.polygon(s, INK, punta)
    pygame.draw.polygon(s, color, [destino,
                                   (destino[0] - 10 * math.cos(ang - .45), destino[1] - 10 * math.sin(ang - .45)),
                                   (destino[0] - 10 * math.cos(ang + .45), destino[1] - 10 * math.sin(ang + .45))])


def _reloj(s, centro, radio, hora_txt, color=CREAM, minutos=15):
    pygame.draw.circle(s, INK, centro, radio + 3)
    pygame.draw.circle(s, (232, 228, 206), centro, radio)
    for i in range(12):
        a = math.pi / 6 * i
        pygame.draw.rect(s, INK, (centro[0] + math.cos(a) * (radio - 5) - 1, centro[1] + math.sin(a) * (radio - 5) - 1, 3, 3))
    a_min = -math.pi / 2 + math.pi * 2 * minutos / 60
    pygame.draw.line(s, INK, centro, (centro[0] + math.cos(a_min) * (radio - 7), centro[1] + math.sin(a_min) * (radio - 7)), 3)
    pygame.draw.line(s, ROJO, centro, (centro[0] - 1, centro[1] - radio * .5), 4)
    texto(s, hora_txt, (centro[0], centro[1] + radio + 14), color, 14, True)


@lru_cache(maxsize=1)
def _mini_campus():
    from mundo_visual import campus
    return pygame.transform.scale(campus(), (MUNDO_ANCHO // 7, MUNDO_ALTO // 7))


def _estudiante(p, direccion='abajo', paso=0, escala=4):
    if p is None:
        return sprite_estudiante('universitario', 'computacion', direccion, paso, escala)
    return sprite_estudiante(p.jugador.personaje, p.jugador.carrera, direccion, paso, escala)


# --------------------------------------------------------------------------
# Ilustraciones (cada una dibuja dentro de `area`)
# --------------------------------------------------------------------------
def _ilu_bienvenida(s, a, t, p):
    for i in range(40):
        x = a.x + (i * 97) % a.w
        y = a.y + (i * 53) % (a.h // 2)
        if (i + int(t * 2)) % 7:
            pygame.draw.rect(s, (150, 176, 190), (x, y, 2, 2))
    pygame.draw.circle(s, (236, 228, 190), (a.x + 60, a.y + 40), 20)
    pygame.draw.circle(s, FONDO_ILUSTRACION, (a.x + 70, a.y + 34), 18)
    base = a.bottom - 34
    for i, (w, h) in enumerate(((90, 70), (130, 96), (80, 60), (120, 84), (100, 74))):
        x = a.x + 20 + i * 118
        pygame.draw.rect(s, (36, 54, 68), (x, base - h, w, h))
        for yy in range(base - h + 10, base - 10, 16):
            for xx in range(x + 10, x + w - 12, 18):
                pygame.draw.rect(s, (241, 199, 116) if (xx + yy) % 3 else (60, 82, 96), (xx, yy, 8, 8))
    pygame.draw.rect(s, (48, 72, 70), (a.x, base, a.w, a.bottom - base))
    im = _estudiante(p, 'derecha', 1 + int(t * 3) % 2, 4)
    s.blit(im, im.get_rect(midbottom=(a.x + 170, a.bottom - 6)))
    luz = pygame.Surface((200, 90), pygame.SRCALPHA)
    pygame.draw.polygon(luz, (255, 236, 150, 70), [(200, 30), (0, 0), (0, 90)])
    s.blit(luz, (a.right - 330, a.bottom - 110))
    im = personaje('vigilante', 'izquierda', 1 + int(t * 2) % 2, 4)
    s.blit(im, im.get_rect(midbottom=(a.right - 110, a.bottom - 6)))
    texto(s, '!', (a.right - 110, a.bottom - 140), ROJO, 28, True)
    _reloj(s, (a.centerx + 20, a.y + 60), 34, '20:15  →  21:00', ORO, 15)


def _ilu_mover(s, a, t, p):
    activa = int(t * 2) % 4
    teclas = (('W', (a.x + 52, a.y + 12)), ('A', (a.x + 8, a.y + 54)), ('S', (a.x + 52, a.y + 54)), ('D', (a.x + 96, a.y + 54)))
    orden = ('W', 'D', 'S', 'A')
    for letra, (x, y) in teclas:
        tecla(s, (x, y, 38, 38), letra, letra == orden[activa], 16)
    texto(s, 'o flechas', (a.x + 71, a.y + 110), TENUE, 12, True)
    direccion = ('arriba', 'derecha', 'abajo', 'izquierda')[activa]
    im = _estudiante(p, direccion, 1 + int(t * 6) % 2, 2)
    s.blit(im, im.get_rect(midbottom=(a.right - 22, a.bottom - 6)))


def _ilu_espacio(s, a, t, p):
    activo = int(t * 1.5) % 3
    centros = [(a.x + 30 + i * 52, a.y + 56) for i in range(3)]
    ui_torre.dibujar_puerta(s, pygame.Rect(centros[0][0] - 16, centros[0][1] - 30, 32, 52), (124, 92, 68), True)
    dibujar_objeto(s, 'libro', centros[1], 40)
    s.blit(prop('pc', 48, 48), prop('pc', 48, 48).get_rect(center=centros[2]))
    for i, (c, etiqueta) in enumerate(zip(centros, ('entrar', 'recoger', 'usar'))):
        texto(s, etiqueta, (c[0], c[1] + 40), ORO if i == activo else TENUE, 11, True)
        if i == activo:
            pygame.draw.rect(s, ORO, (c[0] - 24, c[1] - 34, 48, 64), 2)
    tecla(s, (a.x + 12, a.bottom - 46, a.w - 24, 34), 'ESPACIO', int(t * 3) % 2 == 0, 14)


def _ilu_encargos(s, a, t, p):
    hoja = pygame.Rect(a.x + 10, a.y + 10, a.w - 70, a.h - 20)
    pygame.draw.rect(s, (232, 226, 200), hoja)
    pygame.draw.rect(s, INK, hoja, 2)
    texto(s, 'BITÁCORA', (hoja.x + 10, hoja.y + 8), INK, 12)
    for i, nombre in enumerate(('Biblioteca', 'Siemens', 'R101', 'Cafetería', 'Kite')):
        y = hoja.y + 30 + i * 20
        pygame.draw.rect(s, INK, (hoja.x + 10, y, 12, 12), 2)
        if i < 2 or (i == 2 and int(t * 2) % 2):
            pygame.draw.line(s, (60, 140, 90), (hoja.x + 12, y + 6), (hoja.x + 16, y + 10), 3)
            pygame.draw.line(s, (60, 140, 90), (hoja.x + 16, y + 10), (hoja.x + 22, y + 1), 3)
        texto(s, nombre, (hoja.x + 30, y - 1), INK, 12)
    tecla(s, (a.right - 52, a.y + 16, 40, 40), 'J', int(t * 2) % 2 == 0, 16)
    _reloj(s, (a.right - 32, a.bottom - 52), 18, '20:15', CREAM)


def _ilu_mapa(s, a, t, p):
    im = _mini_campus()
    escala = min((a.w - 20) / im.get_width(), (a.h - 60) / im.get_height())
    im = pygame.transform.scale(im, (int(im.get_width() * escala), int(im.get_height() * escala)))
    r = im.get_rect(midtop=(a.centerx, a.y + 8))
    s.blit(im, r)
    pygame.draw.rect(s, INK, r, 2)
    if p is not None and int(t * 3) % 2:
        x = r.x + p.jugador.x / MUNDO_ANCHO * r.w
        y = r.y + p.jugador.y / MUNDO_ALTO * r.h
        pygame.draw.rect(s, CREAM, (x - 3, y - 3, 7, 7))
    tecla(s, (a.centerx - 20, a.bottom - 46, 40, 40), 'M', int(t * 2) % 2 == 0, 16)


def _ilu_bolsa(s, a, t, p):
    im = pygame.transform.scale(sprite_objeto('mochila'), (64, 64))
    s.blit(im, (a.x + 12, a.y + 14))
    for i in range(6):
        r = pygame.Rect(a.x + 86 + (i % 3) * 26, a.y + 18 + (i // 3) * 26, 22, 22)
        pygame.draw.rect(s, INK, r)
        pygame.draw.rect(s, (40, 66, 76), r.inflate(-4, -4))
        if i < 2:
            dibujar_objeto(s, ('libro', 'usb')[i], r.center, 18)
    tecla(s, (a.x + 18, a.bottom - 50, 40, 40), 'I', int(t * 2) % 2 == 0, 16)
    tecla(s, (a.x + 90, a.bottom - 50, 40, 40), 'G', int(t * 2) % 2 == 1, 16)
    texto(s, 'abrir', (a.x + 38, a.bottom - 6), TENUE, 10, True)
    texto(s, 'soltar', (a.x + 110, a.bottom - 6), TENUE, 10, True)


def _ilu_pila(s, a, t, p):
    cartas = ('Mover → Lobby', 'Recoger libro', 'Mover → R101')
    levanta = int((math.sin(t * 2.5) + 1) * 9)
    for i, etiqueta in enumerate(cartas):
        y = a.bottom - 40 - i * 28 - (levanta if i == 2 else 0)
        x = a.x + 10 + (10 if i == 2 and levanta > 9 else 0)
        r = pygame.Rect(x, y, a.w - 70, 26)
        pygame.draw.rect(s, INK, r)
        pygame.draw.rect(s, CREAM if i == 2 else (176, 190, 186), r.inflate(-4, -4))
        texto(s, etiqueta, (r.x + 8, r.y + 7), INK, 10)
    texto(s, 'CIMA', (a.right - 54, a.bottom - 98 - levanta), ORO, 11)
    tecla(s, (a.right - 52, a.bottom - 52, 40, 40), 'Z', levanta > 12, 16)
    texto(s, 'sale la última', (a.x + 10, a.y + 8), TENUE, 11)


def _ilu_gradas(s, a, t, p):
    base = pygame.Rect(a.x + 14, a.bottom - 80, 80, 70)
    for k in range(6):
        pygame.draw.rect(s, INK, (base.x + k * 12, base.bottom - (k + 1) * 11, base.w - k * 12, 11))
        pygame.draw.rect(s, (160 - k * 8, 180 - k * 8, 172 - k * 8), (base.x + k * 12 + 2, base.bottom - (k + 1) * 11 + 2, base.w - k * 12 - 4, 7))
    torre = pygame.Rect(a.right - 74, a.y + 10, 60, a.h - 24)
    pygame.draw.rect(s, (40, 58, 74), torre)
    pygame.draw.rect(s, INK, torre, 2)
    for yy in range(torre.y + 10, torre.bottom - 12, 22):
        for xx in (torre.x + 10, torre.x + 34):
            pygame.draw.rect(s, ORO if (yy + xx + int(t * 2)) % 3 else (64, 84, 96), (xx, yy, 14, 12))
    texto(s, '2º', (torre.centerx, torre.y - 2), ORO, 12, True)
    rebote = int(math.sin(t * 4) * 5)
    _flecha(s, (base.x + 46, base.top - 4 + rebote), (torre.x - 8, torre.y + 34 + rebote))


def _ilu_listo(s, a, t, p):
    for i in range(24):
        x = a.x + (i * 37 + int(t * 40)) % a.w
        y = a.y + (i * 29 + int(t * 60)) % a.h
        pygame.draw.rect(s, (ORO, AZUL, ROJO, TEAL)[i % 4], (x, y, 4, 4))
    im = _estudiante(p, 'abajo', 0, 4)
    s.blit(im, im.get_rect(midbottom=(a.centerx - 40, a.bottom - 8)))
    tecla(s, (a.centerx + 20, a.bottom - 60, 48, 40), 'F1', int(t * 2) % 2 == 0, 14)


def _ilu_turnos(s, a, t, p):
    actual = int(t * 1.2) % 3
    xs = [a.x + a.w * (i + 1) // 4 for i in range(3)]
    for i, x in enumerate(xs):
        pygame.draw.rect(s, INK, (x - 40, a.bottom - 54, 80, 14))
        pygame.draw.rect(s, ORO if i == actual else (70, 92, 100), (x - 38, a.bottom - 52, 76, 10))
    s.blit(_estudiante(p, 'abajo', 0, 3), _estudiante(p, 'abajo', 0, 3).get_rect(midbottom=(xs[0], a.bottom - 54)))
    im = personaje('vigilante', 'abajo', 0, 3)
    s.blit(im, im.get_rect(midbottom=(xs[1], a.bottom - 54)))
    ui_torre.dibujar_robot(s, (xs[2], a.bottom - 58), 3)
    for i, etiqueta in enumerate(('Tú', 'Vigilante', 'Robot')):
        texto(s, etiqueta, (xs[i], a.bottom - 28), ORO if i == actual else TENUE, 12, True)
        if i == actual:
            texto(s, 'LE TOCA', (xs[i], a.y + 8), ORO, 12, True)
    for i in range(2):
        _flecha(s, (xs[i] + 42, a.bottom - 90), (xs[i + 1] - 42, a.bottom - 90), CREAM, 3)
    pygame.draw.arc(s, CREAM, (xs[0], a.bottom - 22, xs[2] - xs[0], 22), math.pi, 2 * math.pi, 2)


def _ilu_puertas(s, a, t, p):
    xs = [a.x + a.w * (i + 1) // 4 for i in range(3)]
    for i, x in enumerate(xs):
        r = pygame.Rect(x - 22, a.y + 24, 44, 66)
        ui_torre.dibujar_puerta(s, r, (124, 92, 68) if i == 1 else (92, 104, 118), i == 1)
        ui_torre._insignia(s, (x, a.y + 106), i + 1, t)
    bob = int(math.sin(t * 4) * 6)
    cx, cy = xs[1] + 14, a.y + 60 + bob
    cursor = [(cx, cy), (cx, cy + 22), (cx + 6, cy + 16), (cx + 11, cy + 26), (cx + 15, cy + 24), (cx + 10, cy + 14), (cx + 17, cy + 14)]
    pygame.draw.polygon(s, CREAM, cursor)
    pygame.draw.polygon(s, INK, cursor, 2)


def _ilu_volver(s, a, t, p):
    izq = pygame.Rect(a.x + 8, a.y + 30, a.w // 2 - 16, a.h - 70)
    der = pygame.Rect(a.centerx + 8, a.y + 30, a.w // 2 - 16, a.h - 70)
    for r, etiqueta in ((izq, 'antes'), (der, 'aquí')):
        pygame.draw.rect(s, (52, 74, 84), r)
        pygame.draw.rect(s, INK, r, 2)
        texto(s, etiqueta, (r.centerx, r.y - 12), TENUE, 11, True)
    im = _estudiante(p, 'izquierda', 1 + int(t * 4) % 2, 2)
    x = der.centerx - int((math.sin(t * 1.5) + 1) * (der.centerx - izq.centerx) / 2)
    s.blit(im, im.get_rect(midbottom=(x, der.bottom - 6)))
    pygame.draw.arc(s, ORO, (izq.centerx, a.bottom - 46, der.centerx - izq.centerx, 36), math.pi, 2 * math.pi, 3)
    pygame.draw.polygon(s, ORO, [(izq.centerx - 6, a.bottom - 30), (izq.centerx + 6, a.bottom - 30), (izq.centerx, a.bottom - 40)])
    texto(s, '4 Deshacer', (a.centerx, a.bottom - 14), ORO, 11, True)


def _ilu_acciones(s, a, t, p):
    activo = int(t * 1.5) % 5
    for i, (nombre, etiqueta) in enumerate((('recoger', '2'), ('deshacer', '4'), ('historial', '6'),
                                            ('turnos', '7'), ('eventos', '8'))):
        x = a.x + 10 + (i % 3) * 52
        y = a.y + 10 + (i // 3) * 64
        r = pygame.Rect(x, y, 46, 54)
        pygame.draw.rect(s, INK, r)
        pygame.draw.rect(s, (60, 98, 104) if i == activo else (36, 58, 68), r.inflate(-4, -4))
        s.blit(ui_torre.icono(nombre), (x + 7, y + 14))
        texto(s, etiqueta, (x + 8, y + 4), ORO, 11)


def _ilu_eventos(s, a, t, p):
    iconos = ('eventos', 'turnos', 'recoger')
    texto(s, 'cola de eventos', (a.x + 8, a.y + 6), TENUE, 11)
    corrimiento = int((t * 12) % 20)
    for i, nombre in enumerate(iconos):
        x = a.x + 52 + i * 42 - (corrimiento if i == 0 else 0)
        r = pygame.Rect(x, a.y + 34, 38, 46)
        pygame.draw.rect(s, INK, r)
        pygame.draw.rect(s, (90, 80, 46) if i == 0 else (40, 58, 68), r.inflate(-4, -4))
        s.blit(ui_torre.icono(nombre), (x + 3, a.y + 40))
        texto(s, f'{i + 1}º', (r.centerx, r.bottom - 10), ORO if i == 0 else TENUE, 10, True)
    im = _estudiante(p, 'derecha', 0, 2)
    s.blit(im, im.get_rect(midbottom=(a.x + 24, a.y + 84)))
    texto(s, 'sale el primero', (a.x + 8, a.bottom - 34), ORO, 11)
    texto(s, 'que entró (FIFO)', (a.x + 8, a.bottom - 20), ORO, 11)


def _ilu_tesoro(s, a, t, p):
    raiz = (a.centerx, a.y + 16)
    nivel1 = [(a.x + 40, a.y + 50), (a.right - 40, a.y + 50)]
    nivel2 = [(a.x + 20, a.y + 86), (a.x + 64, a.y + 86), (a.right - 64, a.y + 86), (a.right - 20, a.y + 86)]
    nivel3 = [(a.x + 20, a.y + 122), (a.right - 64, a.y + 122)]
    for padre, hijas in ((raiz, nivel1), (nivel1[0], nivel2[:2]), (nivel1[1], nivel2[2:]),
                         (nivel2[0], nivel3[:1]), (nivel2[2], nivel3[1:])):
        for h in hijas:
            pygame.draw.line(s, TENUE, padre, h, 2)
    for punto in [raiz] + nivel1 + nivel2:
        pygame.draw.rect(s, INK, (punto[0] - 7, punto[1] - 7, 14, 14))
        pygame.draw.rect(s, (110, 140, 150), (punto[0] - 5, punto[1] - 5, 10, 10))
    pygame.draw.rect(s, ORO, (raiz[0] - 5, raiz[1] - 5, 10, 10))
    brillo = int(math.sin(t * 5) * 2)
    for punto in nivel3:
        ui_torre.dibujar_diamante(s, punto, 8 + brillo)
    dibujar_objeto(s, 'trofeo', (a.centerx, a.bottom - 22), 32)


def _ilu_vigilante(s, a, t, p):
    im = personaje('vigilante', 'abajo', 1 + int(t * 2) % 2, 3)
    s.blit(im, im.get_rect(midbottom=(a.x + 46, a.bottom - 10)))
    _reloj(s, (a.right - 50, a.y + 40), 22, '21:00', CREAM, 0)
    texto(s, 'antes: -3 min', (a.right - 50, a.y + 96), ORO, 11, True)
    if int(t * 2) % 2:
        texto(s, 'luego: ¡fuera!', (a.right - 50, a.y + 116), ROJO, 11, True)


ILUSTRACIONES = {
    'bienvenida': _ilu_bienvenida, 'mover': _ilu_mover, 'espacio': _ilu_espacio,
    'encargos': _ilu_encargos, 'mapa': _ilu_mapa, 'bolsa': _ilu_bolsa, 'pila': _ilu_pila,
    'gradas': _ilu_gradas, 'listo': _ilu_listo, 'turnos': _ilu_turnos, 'puertas': _ilu_puertas,
    'volver': _ilu_volver, 'acciones': _ilu_acciones, 'eventos': _ilu_eventos,
    'tesoro': _ilu_tesoro, 'vigilante': _ilu_vigilante,
}


# --------------------------------------------------------------------------
# El recorrido
# --------------------------------------------------------------------------
class Tutorial:
    """Recorrido paso a paso. Mientras está activo, pausa la partida."""

    def __init__(self):
        self.activo = False
        self.contexto = None
        self.indice = 0
        self._botones = {}

    @property
    def pasos(self):
        return PASOS.get(self.contexto, [])

    def iniciar(self, contexto):
        """Empieza el recorrido 'campus' o 'torre' desde el primer paso."""
        self.contexto = contexto
        self.indice = 0
        self.activo = True

    def terminar(self):
        self.activo = False
        return 'fin'

    def siguiente(self):
        if self.indice < len(self.pasos) - 1:
            self.indice += 1
            return True
        return self.terminar()

    def anterior(self):
        self.indice = max(0, self.indice - 1)
        return True

    def manejar_evento(self, ev):
        """Consume los eventos mientras está activo. Devuelve 'fin' cuando el
        jugador termina o salta el tutorial, True si solo lo usó, False si no."""
        if not self.activo:
            return False
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                return self.terminar()
            if ev.key in (pygame.K_LEFT, pygame.K_BACKSPACE, pygame.K_a):
                return self.anterior()
            if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_RIGHT, pygame.K_d):
                return self.siguiente()
            return True
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self._botones.get('saltar') and self._botones['saltar'].collidepoint(ev.pos):
                return self.terminar()
            if self._botones.get('atras') and self._botones['atras'].collidepoint(ev.pos):
                return self.anterior()
            return self.siguiente()
        return ev.type in (pygame.MOUSEBUTTONUP, pygame.KEYUP)

    def foco_actual(self, p, camara):
        foco = self.pasos[self.indice].get('foco')
        if callable(foco):
            try:
                foco = foco(p, camara)
            except (AttributeError, KeyError, StopIteration, TypeError):
                foco = None
        return pygame.Rect(foco) if foco else None

    @staticmethod
    def _ubicar(foco, w, h):
        """Pone la tarjeta debajo, arriba, a la izquierda o a la derecha del foco."""
        if foco is None:
            return pygame.Rect((960 - w) // 2, (640 - h) // 2, w, h)
        x = max(12, min(948 - w, foco.centerx - w // 2))
        if foco.bottom + 18 + h <= 632:
            return pygame.Rect(x, foco.bottom + 18, w, h)
        if foco.top - 18 - h >= 8:
            return pygame.Rect(x, foco.top - 18 - h, w, h)
        y = max(8, min(632 - h, foco.centery - h // 2))
        if foco.left - 18 - w >= 8:
            return pygame.Rect(foco.left - 18 - w, y, w, h)
        if foco.right + 18 + w <= 952:
            return pygame.Rect(foco.right + 18, y, w, h)
        return pygame.Rect((960 - w) // 2, (640 - h) // 2, w, h)

    def dibujar(self, s, p, camara=(0, 0), tiempo=0.0):
        if not self.activo or not self.pasos:
            return
        paso = self.pasos[self.indice]
        foco = self.foco_actual(p, camara)
        capa = pygame.Surface((960, 640), pygame.SRCALPHA)
        capa.fill((4, 10, 18, 205))
        if foco:
            capa.fill((0, 0, 0, 0), foco)
        s.blit(capa, (0, 0))
        if foco:
            pulso = int(3 + 2 * math.sin(tiempo * 5))
            marco = foco.inflate(pulso * 2, pulso * 2)
            for (cx, cy), (dx, dy) in (((marco.left, marco.top), (1, 1)), ((marco.right, marco.top), (-1, 1)),
                                       ((marco.left, marco.bottom), (1, -1)), ((marco.right, marco.bottom), (-1, -1))):
                pygame.draw.line(s, ORO, (cx, cy), (cx + 18 * dx, cy), 4)
                pygame.draw.line(s, ORO, (cx, cy), (cx, cy + 18 * dy), 4)
            pygame.draw.rect(s, ORO, marco, 1)

        grande = foco is None
        tarjeta = self._ubicar(foco, 640 if grande else 560, 420 if grande else 214)
        if foco:
            # Pico de la tarjeta apuntando al foco.
            px = max(tarjeta.x + 24, min(tarjeta.right - 24, foco.centerx))
            if tarjeta.top > foco.bottom:
                pico = [(px - 12, tarjeta.top + 2), (px + 12, tarjeta.top + 2), (px, tarjeta.top - 14)]
            elif tarjeta.bottom < foco.top:
                pico = [(px - 12, tarjeta.bottom - 2), (px + 12, tarjeta.bottom - 2), (px, tarjeta.bottom + 14)]
            else:
                pico = None
            if pico:
                pygame.draw.polygon(s, ORO, pico)
        caja(s, tarjeta, (26, 46, 58), ORO)
        if grande:
            area = pygame.Rect(tarjeta.x + 20, tarjeta.y + 20, tarjeta.w - 40, 220)
            tx, ty, ancho = tarjeta.x + 28, area.bottom + 18, tarjeta.w - 56
        else:
            area = pygame.Rect(tarjeta.x + 14, tarjeta.y + 14, 180, tarjeta.h - 58)
            tx, ty, ancho = area.right + 16, tarjeta.y + 18, tarjeta.right - area.right - 32
        pygame.draw.rect(s, FONDO_ILUSTRACION, area)
        clip = s.get_clip()
        s.set_clip(area)
        ILUSTRACIONES[paso['dibujo']](s, area, tiempo, p)
        s.set_clip(clip)
        pygame.draw.rect(s, INK, area, 2)

        texto(s, paso['titulo'], (tx, ty), ORO, 18)
        for i, linea in enumerate(lineas(paso['texto'], ancho, 14)):
            texto(s, linea, (tx, ty + 30 + i * 20), CREAM, 14)

        # Puntos de progreso y botones
        total = len(self.pasos)
        for i in range(total):
            x = tarjeta.x + 18 + i * 12
            y = tarjeta.bottom - 26
            pygame.draw.rect(s, ORO if i == self.indice else (84, 118, 123), (x, y, 8 if i != self.indice else 10, 8))
        ultimo = self.indice == total - 1
        siguiente = pygame.Rect(tarjeta.right - 148, tarjeta.bottom - 38, 132, 28)
        atras = pygame.Rect(siguiente.x - 92, siguiente.y, 84, 28)
        saltar = pygame.Rect(siguiente.x - 196, siguiente.y, 96, 28)
        self._botones = {'siguiente': siguiente, 'atras': atras if self.indice else None,
                         'saltar': None if ultimo else saltar}
        for clave, rect, etiqueta in (('siguiente', siguiente, '¡A jugar!' if ultimo else 'Siguiente >'),
                                      ('atras', atras, '< Atrás'), ('saltar', saltar, 'Saltar (ESC)')):
            if not self._botones.get(clave):
                continue
            principal = clave == 'siguiente'
            pygame.draw.rect(s, INK, rect.move(0, 3))
            pygame.draw.rect(s, ORO if principal else (58, 78, 88), rect)
            pygame.draw.rect(s, INK, rect, 2)
            texto(s, etiqueta, rect.center, INK if principal else CREAM, 12, True)
        texto(s, f'{self.indice + 1}/{total}', (tarjeta.x + 18 + total * 12 + 6, tarjeta.bottom - 29), TENUE, 11)
