"""Pantalla de la Torre de Laboratorios (nivel 2) y paneles de las estructuras.

Solo presentación: los datos viven en la Partida (main.py) y en historial.py,
eventos.py y mazmorra.py.

La Torre se ve como una sala en pixel art: las puertas del fondo llevan a las
salas hijas, la puerta de abajo vuelve a la sala anterior (o baja las gradas
en el rellano) y la barra de iconos tiene las 9 opciones del menú. Todo se
puede hacer con clic, o escribiendo el número y ENTER como en una consola.
"""
import math
from functools import lru_cache

import pygame
from arte_pixel import texto, caja, fuente, dibujar_objeto, suelo, prop, objeto as sprite_objeto
from arte_pixel import personaje, CREAM, TEAL, INK
from sprites_jugador import sprite_estudiante
from estado_mundo import formatear_hora
from historial import mostrar_historial, consultar_ultima_accion, resumen_por_tipo, describir_accion
from eventos import resumen_eventos, simular_turnos, ETIQUETAS_TIPO, EVENTOS_TORRE, ESTUDIANTE, VIGILANTE, ROBOT
from mazmorra import dibujar_arbol, DESCRIPCIONES
from hud_campus import lineas

ORO = (241, 199, 116)
ROJO = (239, 124, 100)
AZUL = (110, 165, 184)
TENUE = (162, 194, 185)
APAGADO = (104, 128, 132)
FONDO = (16, 27, 37)
AMBAR = (240, 194, 105)

OPCIONES = ("Moverse", "Recoger objeto", "Soltar objeto", "Deshacer última",
            "Deshacer varias", "Ver historial", "Ver turnos", "Ver eventos", "Ver inventario")
ETIQUETAS_BARRA = ("Mover", "Recoger", "Soltar", "Deshacer", "Deshacer+",
                   "Historial", "Turnos", "Eventos", "Bolsa")

ESCENA = pygame.Rect(16, 72, 600, 352)
MAPA = pygame.Rect(628, 72, 316, 352)
BARRA = pygame.Rect(16, 432, 928, 66)
REGISTRO = pygame.Rect(16, 506, 620, 80)
ENTRADA = pygame.Rect(644, 506, 300, 80)
PIE = pygame.Rect(0, 592, 960, 48)
MURO_ALTO = 150
PUERTA_W, PUERTA_H = 72, 100
SEGUNDOS_AVISO_EVENTO = 4.0

_COLOR_MURO = {0: (54, 92, 98), 1: (58, 78, 112), 2: (84, 70, 106), 3: (104, 64, 70)}


# --------------------------------------------------------------------------
# Geometría (también la usan main.py para los clics y tutorial.py para el foco)
# --------------------------------------------------------------------------
def puertas_escena(p):
    """Lista de (numero_en_submenu_mover, destino, rect, tipo) de la sala actual.
    tipo: 'hija' (puertas del fondo), 'padre' (volver) o 'gradas'."""
    t = p.torre
    hijas = t['hijos'][p.sala_torre]
    puertas = []
    for i, hija in enumerate(hijas):
        cx = ESCENA.x + ESCENA.w * (i + 1) // (len(hijas) + 1)
        puertas.append((i + 1, hija, pygame.Rect(cx - PUERTA_W // 2, ESCENA.y + 44, PUERTA_W, PUERTA_H), 'hija'))
    abajo = pygame.Rect(ESCENA.x + 16, ESCENA.bottom - 70, 150, 62)
    padre = t['padres'].get(p.sala_torre)
    if padre:
        puertas.append((len(hijas) + 1, padre, abajo, 'padre'))
    else:
        puertas.append((len(hijas) + 1, 'gradas', abajo, 'gradas'))
    return puertas


def rect_cancelar():
    return pygame.Rect(ESCENA.right - 118, ESCENA.y + 8, 108, 24)


def rects_barra():
    """(número de opción, rect) de los 9 botones de la barra de acciones."""
    return [(i + 1, pygame.Rect(BARRA.x + 4 + i * 103, BARRA.y + 4, 99, 58)) for i in range(9)]


def _rect_submenu():
    return pygame.Rect(ESCENA.x + 110, ESCENA.y + 70, 380, 230)


def rects_submenu(p):
    """Filas clicables de los submenús Soltar y Deshacer varias."""
    caja_sub = _rect_submenu()
    if p.menu_torre == 'soltar':
        return [(i + 1, pygame.Rect(caja_sub.x + 14, caja_sub.y + 44 + i * 24, caja_sub.w - 28, 22))
                for i in range(len(p.opciones_submenu))]
    if p.menu_torre == 'deshacer_varias':
        maximo = min(8, p.acciones_deshacibles_en_torre())
        return [(i + 1, pygame.Rect(caja_sub.x + 14 + (i % 4) * 88, caja_sub.y + 70 + (i // 4) * 50, 80, 42))
                for i in range(maximo)]
    return []


def objetivo_clic(p, pos):
    """Qué hay bajo el ratón: ('puerta', n), ('accion', n), ('submenu', n),
    ('cancelar', None) o None."""
    if p.menu_torre in ('soltar', 'deshacer_varias'):
        for numero, rect in rects_submenu(p):
            if rect.collidepoint(pos):
                return ('submenu', numero)
        if _rect_submenu().collidepoint(pos):
            return None
    if p.menu_torre != 'principal' and rect_cancelar().collidepoint(pos):
        return ('cancelar', None)
    for numero, _, rect, _ in puertas_escena(p):
        if rect.collidepoint(pos):
            return ('puerta', numero)
    for numero, rect in rects_barra():
        if rect.collidepoint(pos):
            return ('accion', numero)
    return None


# --------------------------------------------------------------------------
# Piezas de pixel art
# --------------------------------------------------------------------------
def dibujar_robot(s, centro, escala=2):
    """Robot de limpieza: disco con parachoques y LED."""
    x, y = centro
    r = 9 * escala
    pygame.draw.ellipse(s, (47, 74, 73), (x - r, y - 3 * escala, 2 * r, 6 * escala))
    pygame.draw.circle(s, INK, (x, y - 6 * escala), r)
    pygame.draw.circle(s, (150, 172, 182), (x, y - 6 * escala), r - 2 * escala)
    pygame.draw.circle(s, (93, 117, 130), (x, y - 6 * escala), r - 5 * escala)
    pygame.draw.rect(s, (105, 218, 166), (x - escala, y - 11 * escala, 2 * escala, 2 * escala))
    pygame.draw.arc(s, (236, 231, 205), (x - r + escala, y - 6 * escala - r + escala, 2 * r - 2 * escala,
                                         2 * r - 2 * escala), 0.4, 2.7, escala)


@lru_cache(maxsize=32)
def icono(nombre, escala=2):
    """Iconos de 16x16 de la barra de acciones (pixel art, sin assets externos)."""
    if nombre == 'bolsa':
        return pygame.transform.scale(sprite_objeto('mochila'), (16 * escala, 16 * escala))
    s = pygame.Surface((16, 16), pygame.SRCALPHA)

    def r(c, x, y, w, h):
        pygame.draw.rect(s, c, (x, y, w, h))
    if nombre == 'mover':            # puerta con flecha
        r(INK, 2, 1, 9, 14); r((150, 110, 78), 3, 2, 7, 13); r(ORO, 8, 8, 1, 1)
        r(INK, 10, 6, 5, 3); r(CREAM, 11, 7, 3, 1); r(INK, 13, 5, 1, 5); r(CREAM, 13, 6, 1, 3)
    elif nombre == 'recoger':        # mano
        r(INK, 3, 6, 10, 9); r((227, 174, 130), 4, 7, 8, 7)
        for x in (4, 6, 8, 10):
            r(INK, x - 1, 2, 3, 6); r((227, 174, 130), x, 3, 1, 5)
        r(INK, 12, 8, 3, 4); r((227, 174, 130), 12, 9, 2, 2)
        r(ORO, 1, 1, 1, 1); r(ORO, 14, 2, 1, 1)
    elif nombre == 'soltar':         # caja y flecha hacia abajo
        r(INK, 6, 0, 4, 7); r(CREAM, 7, 1, 2, 5); r(INK, 4, 5, 8, 2); r(CREAM, 5, 5, 6, 1); r(CREAM, 7, 6, 2, 1)
        r(INK, 2, 9, 12, 6); r((178, 135, 86), 3, 10, 10, 4); r((224, 188, 132), 7, 10, 2, 4)
    elif nombre in ('deshacer', 'deshacer_varias'):
        pygame.draw.arc(s, INK, (3, 3, 12, 11), -1.6, 3.2, 3)
        pygame.draw.arc(s, ORO, (4, 4, 10, 9), -1.6, 3.2, 1)
        pygame.draw.polygon(s, INK, [(0, 9), (7, 9), (3, 14)])
        pygame.draw.polygon(s, ORO, [(1, 9), (6, 9), (3, 12)])
        if nombre == 'deshacer_varias':
            r(INK, 10, 0, 6, 6); r(CREAM, 11, 1, 1, 1); r(CREAM, 13, 1, 1, 1); r(CREAM, 12, 2, 1, 1)
            r(CREAM, 11, 3, 1, 1); r(CREAM, 13, 3, 1, 1)
    elif nombre == 'historial':      # pila de tarjetas
        for i, c in enumerate(((120, 140, 150), (170, 190, 186), CREAM)):
            r(INK, 2 + i, 8 - i * 3, 12, 6); r(c, 3 + i, 9 - i * 3, 10, 4)
        r(INK, 6, 5, 6, 1)
    elif nombre == 'turnos':         # tres caras en fila y un ciclo
        for x, c in ((1, ORO), (6, ROJO), (11, AZUL)):
            r(INK, x, 2, 5, 5); r(c, x + 1, 3, 3, 3)
        pygame.draw.arc(s, INK, (2, 7, 12, 8), 3.4, 6.0, 2)
        r(INK, 2, 9, 3, 2)
    elif nombre == 'eventos':        # señal de aviso
        pygame.draw.polygon(s, INK, [(8, 0), (16, 15), (0, 15)])
        pygame.draw.polygon(s, AMBAR, [(8, 3), (14, 14), (2, 14)])
        r(INK, 7, 6, 2, 5); r(INK, 7, 12, 2, 1)
    return pygame.transform.scale(s, (16 * escala, 16 * escala))


ICONOS_BARRA = ('mover', 'recoger', 'soltar', 'deshacer', 'deshacer_varias',
                'historial', 'turnos', 'eventos', 'bolsa')
ICONOS_EVENTO = {'trampa': 'eventos', 'enemigo': 'turnos', 'camara': 'eventos',
                 'apagon': 'historial', 'cofre': 'recoger', 'mensaje': 'historial'}


def dibujar_puerta(s, rect, color, iluminada=False, peligro=None):
    """Puerta en el muro del fondo, con ventanilla y manija."""
    pygame.draw.rect(s, INK, rect.inflate(10, 6).move(0, 3))
    pygame.draw.rect(s, (36, 44, 52), rect.inflate(6, 4).move(0, 2))
    pygame.draw.rect(s, color, rect)
    claro = tuple(min(255, c + 28) for c in color)
    pygame.draw.rect(s, claro, (rect.x + 6, rect.y + 8, rect.w - 12, rect.h - 16), 2)
    pygame.draw.rect(s, INK, (rect.x + 14, rect.y + 14, rect.w - 28, 22))
    pygame.draw.rect(s, (168, 214, 206) if iluminada else (62, 82, 92), (rect.x + 16, rect.y + 16, rect.w - 32, 18))
    pygame.draw.rect(s, ORO, (rect.right - 16, rect.centery + 4, 6, 6))
    if peligro:
        luz = pygame.Surface((rect.w, 8), pygame.SRCALPHA)
        luz.fill((*peligro, 170))
        s.blit(luz, (rect.x, rect.bottom - 4))


def dibujar_diamante(s, centro, radio=7):
    cx, cy = centro
    pygame.draw.polygon(s, INK, [(cx, cy - radio - 2), (cx + radio + 2, cy), (cx, cy + radio + 2), (cx - radio - 2, cy)])
    pygame.draw.polygon(s, ORO, [(cx, cy - radio), (cx + radio, cy), (cx, cy + radio), (cx - radio, cy)])


def _insignia(s, centro, numero, tiempo):
    pulso = 2 if int(tiempo * 3) % 2 else 0
    pygame.draw.circle(s, INK, centro, 15 + pulso)
    pygame.draw.circle(s, ORO, centro, 13 + pulso)
    texto(s, str(numero), centro, INK, 16, True)


def _props_sala(nombre):
    claves = (
        (('Servidores', 'Racks', 'Control', 'Eléctrico', 'Baterías'), (('servidor', 56, 96, 1), ('servidor', 56, 96, 0))),
        (('Aula', 'Tutorías'), (('mesa', 96, 56, 0), ('silla', 32, 40, 1))),
        (('Archivo', 'Closet', 'Bodega', 'Depósito', 'Bóveda'), (('estante', 72, 96, 0), ('caja', 48, 40, 0))),
        (('Óptica', 'Química', 'Energía', 'Anecoica', 'Oscuro'), (('osciloscopio', 88, 56, 0), ('banco_plc', 104, 64, 0))),
        (('Robótica',), (('robot', 104, 64, 0), ('maquina', 56, 80, 1))),
        (('Impresión',), (('impresora', 56, 56, 0), ('impresora', 56, 56, 0))),
        (('Oficina', 'Simulación', 'Grabación'), (('pc', 80, 56, 0), ('silla', 32, 40, 2))),
    )
    for palabras, props in claves:
        if any(palabra in nombre for palabra in palabras):
            return props
    return (('planta', 40, 56, 0), ('banco', 72, 32, 0))


def _encabezado(s, p):
    pygame.draw.rect(s, INK, (0, 0, 960, 64))
    pygame.draw.rect(s, TEAL, (0, 62, 960, 2))
    texto(s, '9PM', (20, 12), ORO, 24)
    texto(s, p.sala_torre.upper(), (96, 10), CREAM, 17)
    desc = lineas(DESCRIPCIONES.get(p.sala_torre, ''), 440, 12)
    if desc:
        texto(s, desc[0] + ('…' if len(desc) > 1 else ''), (96, 38), TENUE, 12)
    color = ROJO if p.estado_mundo['toque_queda_activo'] else CREAM
    texto(s, formatear_hora(p.estado_mundo['hora_actual_min']), (560, 9), color, 24)
    hechas = sum(m.completada for m in p.mision.hijas)
    texto(s, f'{hechas:02}/{len(p.mision.hijas)} ENCARGOS · {p.tesoros_en_mochila()} OBJ. PERDIDOS', (560, 39), TEAL, 12)


def _escena(s, p, tiempo, mouse):
    t = p.torre
    sala = p.sala_torre
    nivel = t['niveles'][sala]
    x0, y0 = ESCENA.topleft
    clip = s.get_clip()
    s.set_clip(ESCENA)
    # Piso y muro del fondo
    suelo(s, (x0, y0 + MURO_ALTO, ESCENA.w, ESCENA.h - MURO_ALTO), 'interior')
    noche = pygame.Surface((ESCENA.w, ESCENA.h - MURO_ALTO), pygame.SRCALPHA)
    noche.fill((14, 24, 44, 120))
    s.blit(noche, (x0, y0 + MURO_ALTO))
    muro = _COLOR_MURO.get(nivel, (60, 80, 96))
    pygame.draw.rect(s, muro, (x0, y0, ESCENA.w, MURO_ALTO))
    for yy in range(y0 + 10, y0 + MURO_ALTO - 10, 14):
        pygame.draw.line(s, tuple(max(0, c - 10) for c in muro), (x0, yy), (ESCENA.right, yy), 2)
    pygame.draw.rect(s, (34, 46, 54), (x0, y0 + MURO_ALTO - 8, ESCENA.w, 8))
    # Linterna del jugador
    luz = pygame.Surface((300, 160), pygame.SRCALPHA)
    for r in range(150, 0, -10):
        pygame.draw.ellipse(luz, (255, 226, 150, int(26 * (1 - r / 150))), (150 - r, 80 - r // 2, 2 * r, r))
    s.blit(luz, (x0 + 170, y0 + 214))
    # Muebles según el nombre de la sala
    for (tipo, w, h, var), (px, py) in zip(_props_sala(sala), ((x0 + 28, y0 + 160), (x0 + ESCENA.w - 128, y0 + 168))):
        s.blit(prop(tipo, w, h, var), (px, py))

    moviendo = p.menu_torre == 'mover'
    if not t['hijos'][sala]:
        aviso_muro = pygame.Rect(0, 0, 330, 40)
        aviso_muro.center = (x0 + ESCENA.w // 2, y0 + 70)
        pygame.draw.rect(s, INK, aviso_muro)
        pygame.draw.rect(s, (196, 190, 160), aviso_muro.inflate(-4, -4))
        texto(s, 'Fondo de la Torre: no hay más puertas.', (aviso_muro.centerx, aviso_muro.y + 13), INK, 11, True)
        texto(s, 'Regresa por la puerta de abajo.', (aviso_muro.centerx, aviso_muro.y + 27), INK, 11, True)
    for numero, destino, rect, tipo in puertas_escena(p):
        hover = rect.collidepoint(mouse)
        if tipo == 'hija':
            vigilante = p.posiciones_torre[VIGILANTE] == destino
            robot = p.posiciones_torre[ROBOT] == destino
            peligro = ROJO if vigilante else AZUL if robot else None
            color = (124, 92, 68) if destino in p.salas_visitadas else (92, 104, 118)
            dibujar_puerta(s, rect, color, destino in p.salas_visitadas, peligro)
            # Placa con el nombre de la sala de destino
            placa = pygame.Rect(0, 0, 158, 34)
            placa.midbottom = (rect.centerx, rect.y - 4)
            pygame.draw.rect(s, INK, placa)
            pygame.draw.rect(s, (222, 214, 178) if hover else (196, 190, 160), placa.inflate(-4, -4))
            for j, linea in enumerate(lineas(destino, 148, 11)[:2]):
                texto(s, linea, (placa.centerx, placa.y + 10 + j * 13), INK, 11, True)
            piso_destino = p.objetos_torre.get(destino, [])
            if piso_destino and (destino in p.salas_visitadas or destino in p.tesoros_revelados):
                dibujar_objeto(s, piso_destino[-1], (placa.right - 2, placa.y + 2), 20)
            elif piso_destino and destino in t['profundas']:
                dibujar_diamante(s, (placa.right - 2, placa.y + 2))
            if vigilante:
                texto(s, '!', (rect.centerx, rect.bottom + 10), ROJO, 18, True)
            if hover:
                pygame.draw.rect(s, ORO, rect.inflate(10, 8), 3)
        else:
            # Puerta de regreso (o las gradas en el rellano), abajo a la izquierda
            pygame.draw.rect(s, INK, rect)
            if tipo == 'gradas':
                for k in range(5):
                    tono = (150 - k * 18, 170 - k * 18, 162 - k * 18)
                    pygame.draw.rect(s, tono, (rect.x + 6, rect.y + 6 + k * 11, rect.w - 12, 8))
                etiqueta = 'Bajar al campus'
            else:
                pygame.draw.rect(s, (40, 56, 66), rect.inflate(-8, -8))
                pygame.draw.rect(s, (118, 92, 70), (rect.x + 14, rect.bottom - 18, rect.w - 28, 10))
                etiqueta = f'Volver: {destino}'
            flecha_y = rect.y + 18 + int(math.sin(tiempo * 4) * 3)
            pygame.draw.polygon(s, INK, [(rect.right - 33, flecha_y - 2), (rect.right - 9, flecha_y - 2),
                                         (rect.right - 21, flecha_y + 14)])
            pygame.draw.polygon(s, ORO, [(rect.right - 30, flecha_y), (rect.right - 12, flecha_y),
                                         (rect.right - 21, flecha_y + 11)])
            for j, linea in enumerate(lineas(etiqueta, 196, 11)[:2]):
                texto(s, linea, (rect.x + 2, rect.y - 30 + j * 13), CREAM, 11)
            if hover:
                pygame.draw.rect(s, ORO, rect.inflate(6, 6), 3)
        if moviendo:
            centro = rect.center if tipo != 'hija' else (rect.centerx, rect.centery + 10)
            _insignia(s, centro, numero, tiempo)

    # Ocupantes: objeto en el suelo, vigilante, robot y tú
    piso = p.objetos_torre.get(sala, [])
    if piso:
        ox, oy = x0 + 440, y0 + 292
        brillo = int(4 + 3 * math.sin(tiempo * 5))
        pygame.draw.circle(s, (176, 150, 80), (ox, oy + 4), 22 + brillo, 2)
        dibujar_objeto(s, piso[-1], (ox, oy - int(math.sin(tiempo * 3) * 3)), 36)
        texto(s, '2 = recoger', (ox, oy + 34), ORO, 11, True)
    paso = int(tiempo * 2) % 2
    if p.posiciones_torre[VIGILANTE] == sala:
        im = personaje('vigilante', 'derecha', 1 + paso, 3)
        s.blit(im, im.get_rect(midbottom=(x0 + 230, y0 + 330)))
        texto(s, '!', (x0 + 230, y0 + 228), ROJO, 26, True)
    if p.posiciones_torre[ROBOT] == sala:
        dibujar_robot(s, (x0 + 520, y0 + 336), 3)
    pygame.draw.ellipse(s, (30, 40, 44), (x0 + 296, y0 + 322, 48, 12))
    im = sprite_estudiante(p.jugador.personaje, p.jugador.carrera, 'abajo', 0, 3)
    s.blit(im, im.get_rect(midbottom=(x0 + 320, y0 + 330)))

    # Aviso del último evento procesado
    if tiempo - getattr(p, 'evento_t', -99.0) < SEGUNDOS_AVISO_EVENTO:
        aviso = pygame.Rect(0, 0, 340, 46)
        aviso.midtop = (x0 + ESCENA.w // 2 + 20, y0 + MURO_ALTO + 18)
        caja(s, aviso, (46, 52, 40), AMBAR)
        if p.ultimo_evento:
            s.blit(icono(ICONOS_EVENTO.get(p.ultimo_evento['tipo'], 'eventos')), (aviso.x + 8, aviso.y + 7))
            texto(s, 'EVENTO DE LA COLA', (aviso.x + 48, aviso.y + 6), AMBAR, 10)
            texto(s, lineas(p.ultimo_evento['titulo'], 280, 14)[0], (aviso.x + 48, aviso.y + 21), CREAM, 14)
        else:
            texto(s, 'Silencio: la cola de eventos está vacía.', (aviso.x + 12, aviso.y + 15), CREAM, 12)

    texto(s, f'TORRE · NIVEL {nivel} DE {t["profundidad_real"]}', (ESCENA.right - 172, ESCENA.bottom - 20), CREAM, 11)
    if moviendo:
        banda = pygame.Rect(ESCENA.x, ESCENA.y + MURO_ALTO - 10, ESCENA.w, 22)
        pygame.draw.rect(s, (24, 34, 44), banda)
        texto(s, 'Elige una puerta: clic, o su número + ENTER', banda.center, ORO, 12, True)
    if p.menu_torre != 'principal':
        r = rect_cancelar()
        pygame.draw.rect(s, INK, r)
        pygame.draw.rect(s, (70, 84, 92), r.inflate(-4, -4))
        etiqueta = f'{len(p.opciones_submenu)}) Cancelar' if moviendo else 'ESC cancelar'
        texto(s, etiqueta, r.center, CREAM, 11, True)
    s.set_clip(clip)
    pygame.draw.rect(s, INK, ESCENA, 3)
    pygame.draw.rect(s, (108, 148, 151), ESCENA.inflate(2, 2), 1)


def _submenu(s, p, mouse):
    if p.menu_torre not in ('soltar', 'deshacer_varias'):
        return
    capa = pygame.Surface(ESCENA.size, pygame.SRCALPHA)
    capa.fill((8, 14, 22, 150))
    s.blit(capa, ESCENA.topleft)
    r = _rect_submenu()
    caja(s, r, (30, 50, 60), ORO)
    if p.menu_torre == 'soltar':
        texto(s, '¿QUÉ OBJETO SUELTAS AQUÍ?', (r.x + 14, r.y + 14), ORO, 13)
        for numero, fila in rects_submenu(p):
            tipo, nombre = p.opciones_submenu[numero - 1]
            if fila.collidepoint(mouse):
                pygame.draw.rect(s, (52, 86, 92), fila)
            texto(s, str(numero), (fila.x + 4, fila.y + 4), ORO, 13)
            if tipo == 'objeto':
                dibujar_objeto(s, p.inventario.objetos[numero - 1]['nombre'], (fila.x + 34, fila.centery), 18)
            texto(s, nombre, (fila.x + 50, fila.y + 4), APAGADO if tipo == 'cancelar' else CREAM, 12)
    else:
        maximo = p.acciones_deshacibles_en_torre()
        texto(s, '¿CUÁNTAS ACCIONES DESHACES?', (r.x + 14, r.y + 14), ORO, 13)
        texto(s, f'Puedes retroceder de 1 a {maximo} pasos dentro de la Torre.', (r.x + 14, r.y + 38), TENUE, 11)
        for numero, boton in rects_submenu(p):
            hover = boton.collidepoint(mouse)
            pygame.draw.rect(s, INK, boton)
            pygame.draw.rect(s, (60, 98, 104) if hover else (42, 70, 80), boton.inflate(-4, -4))
            texto(s, str(numero), boton.center, ORO, 18, True)
        texto(s, 'Clic en un número, o escríbelo y ENTER.', (r.x + 14, r.bottom - 30), TENUE, 11)


def _mapa(s, p):
    caja(s, MAPA, (30, 50, 60))
    t = p.torre
    texto(s, 'PLANO DE LA TORRE', (MAPA.x + 12, MAPA.y + 10), TEAL, 13)
    por_nivel = '/'.join(str(c) for _, c in sorted(t['por_nivel'].items()))
    texto(s, f"{len(t['salas'])} salas · profundidad {t['profundidad_real']} · {por_nivel}",
          (MAPA.x + 12, MAPA.y + 28), TENUE, 11)
    f = fuente(11)
    y = MAPA.y + 50
    for sala, linea in zip(t['salas'], dibujar_arbol(t['raiz'], t['hijos'])):
        prefijo = linea[:len(linea) - len(sala)]
        actual = sala == p.sala_torre
        if actual:
            pygame.draw.rect(s, (58, 84, 78), (MAPA.x + 6, y - 2, MAPA.w - 12, 17))
            pygame.draw.rect(s, ORO, (MAPA.x + 6, y - 2, 3, 17))
        texto(s, prefijo, (MAPA.x + 12, y), APAGADO, 11)
        x = MAPA.x + 12 + f.size(prefijo)[0]
        color = ORO if actual else CREAM if sala in p.salas_visitadas else (126, 150, 152)
        nombre = sala
        while f.size(nombre)[0] > MAPA.right - 74 - x and len(nombre) > 4:
            nombre = nombre[:-2] + '…'
        texto(s, nombre, (x, y), color, 11)
        mx = MAPA.right - 10
        if actual:
            mx -= 20
            pygame.draw.rect(s, ORO, (mx, y + 1, 18, 12))
            texto(s, 'TÚ', (mx + 2, y), INK, 10)
        if p.posiciones_torre[VIGILANTE] == sala:
            mx -= 15
            pygame.draw.rect(s, ROJO, (mx, y + 1, 13, 12))
            texto(s, 'V', (mx + 3, y), INK, 10)
        if p.posiciones_torre[ROBOT] == sala:
            mx -= 15
            pygame.draw.rect(s, AZUL, (mx, y + 1, 13, 12))
            texto(s, 'R', (mx + 3, y), INK, 10)
        piso = p.objetos_torre.get(sala, [])
        if piso and (sala in p.salas_visitadas or sala in p.tesoros_revelados):
            mx -= 16
            dibujar_objeto(s, piso[-1], (mx + 7, y + 7), 14)
        elif piso and sala in t['profundas']:
            mx -= 14
            dibujar_diamante(s, (mx + 6, y + 7), 5)
        y += 18
    ly = MAPA.bottom - 22
    for x, (color, letra, desc) in zip((MAPA.x + 12, MAPA.x + 64, MAPA.x + 160),
                                       ((ORO, 'TÚ', 'tú'), (ROJO, 'V', 'vigilante'), (AZUL, 'R', 'robot'))):
        pygame.draw.rect(s, color, (x, ly, 18, 12))
        texto(s, letra, (x + 2, ly - 1), INK, 10)
        texto(s, desc, (x + 22, ly - 1), TENUE, 10)
    dibujar_diamante(s, (MAPA.x + 248, ly + 6), 5)
    texto(s, 'objeto', (MAPA.x + 258, ly - 1), TENUE, 10)


def _disponible(p, numero):
    if numero == 2:
        return bool(p.objetos_torre.get(p.sala_torre))
    if numero == 3:
        return bool(p.inventario.objetos)
    if numero == 4:
        return bool(p.historial)
    if numero == 5:
        return p.acciones_deshacibles_en_torre() > 0
    return True


def _barra(s, p, tiempo, mouse):
    caja(s, BARRA, (24, 40, 50))
    for numero, rect in rects_barra():
        activo = _disponible(p, numero)
        hover = rect.collidepoint(mouse) and activo
        destacado = numero == 2 and activo and int(tiempo * 2) % 2 == 0
        fondo = (60, 98, 104) if hover else (70, 92, 54) if destacado else (36, 58, 68)
        pygame.draw.rect(s, INK, rect)
        pygame.draw.rect(s, fondo if activo else (30, 40, 46), rect.inflate(-4, -4))
        im = icono(ICONOS_BARRA[numero - 1])
        if not activo:
            im = im.copy()
            im.set_alpha(70)
        s.blit(im, im.get_rect(center=(rect.centerx + 6, rect.y + 22)))
        texto(s, ETIQUETAS_BARRA[numero - 1], (rect.centerx, rect.bottom - 11),
              CREAM if activo else APAGADO, 11, True)
        pygame.draw.rect(s, ORO if activo else APAGADO, (rect.x + 4, rect.y + 4, 16, 16))
        texto(s, str(numero), (rect.x + 12, rect.y + 12), INK, 12, True)


def _registro(s, p):
    caja(s, REGISTRO, (14, 24, 32), (84, 118, 123))
    texto(s, 'LO ÚLTIMO QUE PASÓ', (REGISTRO.x + 10, REGISTRO.y + 6), TEAL, 10)
    visibles = []
    for linea in p.consola[-24:]:
        limpia = linea.split('] ', 1)[1] if linea.startswith('[') else linea
        if limpia.startswith(('  (historial', 'Salas conectadas', 'Estás en', 'En el suelo')):
            continue
        for parte in lineas(limpia.strip(), REGISTRO.w - 24, 12) or ['']:
            visibles.append((limpia, parte))
    for i, (completa, parte) in enumerate(visibles[-4:]):
        if completa.startswith('> '):
            color = ORO
        elif any(k in completa for k in ('no válida', 'no existe', 'No hay paso', 'vacía', 'vacío',
                                         'llena', 'FIN DE', 'No puedes', 'no está', 'sermonea', 'BIP')):
            color = ROJO
        elif completa.startswith(('Evento', '  Pista')):
            color = AMBAR
        elif 'Turno de' in completa or completa.startswith('Ronda'):
            color = AZUL
        else:
            color = CREAM
        texto(s, parte, (REGISTRO.x + 10, REGISTRO.y + 20 + i * 14), color, 12)


def _entrada(s, p, tiempo):
    caja(s, ENTRADA, (14, 24, 32), ORO if p.entrada_torre else (84, 118, 123))
    texto(s, 'TECLADO: ESCRIBE Y PRESIONA ENTER', (ENTRADA.x + 10, ENTRADA.y + 6), TEAL, 10)
    cursor = '_' if int(tiempo * 2.5) % 2 == 0 else ' '
    texto(s, f'{p.prompt_torre()} {p.entrada_torre}{cursor}', (ENTRADA.x + 10, ENTRADA.y + 26), ORO, 15)
    texto(s, 'o haz clic en puertas y botones', (ENTRADA.x + 10, ENTRADA.y + 56), APAGADO, 11)


def _pie(s, p):
    pygame.draw.rect(s, INK, PIE)
    pygame.draw.rect(s, TEAL, (0, PIE.y, 960, 2))
    texto(s, 'TURNOS', (18, 598), AZUL, 10)
    x = 18
    for i, nombre in enumerate(p.turnos):
        if nombre == ESTUDIANTE:
            s.blit(sprite_estudiante(p.jugador.personaje, p.jugador.carrera, 'abajo', 0, 1), (x, 609))
        elif nombre == VIGILANTE:
            s.blit(personaje('vigilante', 'abajo', 0, 1), (x, 609))
        else:
            dibujar_robot(s, (x + 12, 636), 1)
        if i < len(p.turnos) - 1:
            texto(s, '→', (x + 29, 614), CREAM, 14)
        x += 48
    texto(s, 'cada paso = 1 ronda + 1 minuto', (166, 616), TENUE, 11)
    s.blit(icono('eventos', 1), (416, 600))
    texto(s, f'EVENTOS EN COLA: {len(p.eventos_torre)}', (438, 601), AMBAR, 12)
    s.blit(icono('historial', 1), (416, 620))
    texto(s, f'HISTORIAL: {len(p.historial)} acciones', (438, 621), TENUE, 12)
    if p.alerta_vigilante:
        texto(s, f'¡EL VIGILANTE TE SIGUE! ({p.alerta_vigilante})', (640, 601), ROJO, 12)
    texto(s, 'F1 tutorial · ESC pausa', (770, 621), TEAL, 12)


def dibujar_torre(s, p, tiempo=0.0, mouse=None):
    """Pantalla completa de la Torre."""
    if mouse is None:
        try:
            from render import ventana_a_logico
            surf = pygame.display.get_surface()
            mouse = ventana_a_logico(*pygame.mouse.get_pos(), surf.get_size()) if surf else None
        except pygame.error:
            mouse = None
        mouse = mouse or (-1, -1)
    s.fill(FONDO)
    _encabezado(s, p)
    _escena(s, p, tiempo, mouse)
    _submenu(s, p, mouse)
    _mapa(s, p)
    _barra(s, p, tiempo, mouse)
    _registro(s, p)
    _entrada(s, p, tiempo)
    _pie(s, p)


# --------------------------------------------------------------------------
# Paneles de las estructuras (pausan la partida)
# --------------------------------------------------------------------------
def _turnos(n):
    return f'{n} turno' if n == 1 else f'{n} turnos'


def _fondo_panel(s, titulo, subtitulo):
    capa = pygame.Surface((960, 640), pygame.SRCALPHA)
    capa.fill((8, 20, 30, 238))
    s.blit(capa, (0, 0))
    texto(s, titulo, (28, 22), CREAM, 24)
    texto(s, subtitulo, (28, 58), TENUE, 13)


def dibujar_panel_historial(s, p):
    """Historial completo: de la acción más reciente (cima) a la más antigua."""
    _fondo_panel(s, 'HISTORIAL DE ACCIONES · PILA',
                 'De la más reciente (cima) a la más antigua. Deshacer siempre saca la cima con pop().')
    filas = mostrar_historial(p.historial)
    maximo = 15
    for i, linea in enumerate(filas[:maximo]):
        y = 92 + i * 30
        cima = i == 0 and p.historial
        caja(s, (28, y, 580, 26), (44, 72, 70) if cima else (30, 52, 62), ORO if cima else (84, 118, 123))
        texto(s, lineas(linea, 500 if cima else 556, 12)[0], (40, y + 6), CREAM if p.historial else TENUE, 12)
        if cima:
            texto(s, 'CIMA', (560, y + 6), ORO, 12)
    if len(filas) > maximo:
        resto = len(filas) - maximo
        cola = '1 acción más antigua' if resto == 1 else f'{resto} acciones más antiguas'
        texto(s, f'… y {cola} debajo.', (40, 92 + maximo * 30), TENUE, 12)
    caja(s, (632, 92, 300, 420), (30, 52, 62))
    texto(s, 'RESUMEN', (648, 104), TEAL, 14)
    texto(s, 'contar_acciones_de_tipo()', (648, 124), APAGADO, 11)
    for i, (tipo, cantidad) in enumerate(resumen_por_tipo(p.historial).items()):
        y = 150 + i * 28
        texto(s, tipo.capitalize(), (648, y), CREAM, 14)
        texto(s, str(cantidad), (900, y), ORO, 14)
        pygame.draw.rect(s, (59, 81, 92), (740, y + 5, 140, 7))
        pygame.draw.rect(s, TEAL, (740, y + 5, min(140, cantidad * 14), 7))
    texto(s, f'Total en la pila: {len(p.historial)}', (648, 268), CREAM, 14)
    ultima = consultar_ultima_accion(p.historial)
    texto(s, 'Última acción (peek, sin sacarla):', (648, 300), TEAL, 12)
    for j, l in enumerate(lineas(describir_accion(ultima) if ultima else 'ninguna', 268, 12)[:3]):
        texto(s, l, (648, 320 + j * 16), CREAM, 12)
    ayuda = ('Deshacer en la Torre: opción 4 (o 5 para varias). En el campus: tecla Z. '
             'Mover vuelve de verdad a la sala anterior; recoger devuelve el objeto a su sitio.')
    for j, l in enumerate(lineas(ayuda, 268, 12)):
        texto(s, l, (648, 384 + j * 16), TENUE, 12)
    pie = 'ENTER / ESC cerrar' if p.ubicacion == 'torre' else 'H / ESC cerrar · Z deshace la cima'
    texto(s, pie, (28, 604), TEAL, 13)


def dibujar_panel_turnos(s, p):
    """Cola de turnos de la Torre y simulación de los próximos turnos."""
    _fondo_panel(s, 'SISTEMA DE TURNOS · COLA',
                 'Cada movimiento en la Torre juega una ronda: popleft() saca al primero y append() lo devuelve al final.')
    x = 28
    estados = {
        ESTUDIANTE: p.sala_torre or 'campus',
        VIGILANTE: p.posiciones_torre[VIGILANTE],
        ROBOT: p.posiciones_torre[ROBOT],
    }
    colores = {ESTUDIANTE: ORO, VIGILANTE: ROJO, ROBOT: AZUL}
    for i, nombre in enumerate(p.turnos):
        rect = pygame.Rect(x, 100, 270, 92)
        caja(s, rect, (30, 52, 62), colores[nombre])
        texto(s, 'FRENTE' if i == 0 else 'FINAL' if i == len(p.turnos) - 1 else 'EN FILA', (x + 12, 108), TENUE, 11)
        texto(s, f'{i + 1}. {nombre}', (x + 12, 126), colores[nombre], 14)
        for j, l in enumerate(lineas(estados[nombre], 246, 12)[:2]):
            texto(s, l, (x + 12, 150 + j * 16), CREAM, 12)
        if i < len(p.turnos) - 1:
            texto(s, '→', (x + 284, 134), CREAM, 20)
        x += 304
    if p.pausa_vigilante:
        estado = f'llenando un reporte ({_turnos(p.pausa_vigilante)})'
    elif p.alerta_vigilante:
        estado = f'te persigue ({_turnos(p.alerta_vigilante)} de alerta)'
    else:
        estado = 'patrulla al azar'
    texto(s, f'Vigilante: {estado}.   Rondas jugadas: {p.rondas_jugadas}.', (28, 212), CREAM, 13)
    caja(s, (28, 244, 440, 250), (30, 52, 62))
    texto(s, 'PRÓXIMOS TURNOS', (44, 256), TEAL, 14)
    texto(s, 'simular_turnos(): usa una copia, no mueve la cola real', (44, 276), APAGADO, 11)
    for i, linea in enumerate(simular_turnos(list(p.turnos), 6)):
        texto(s, linea, (44, 304 + i * 28), CREAM, 14)
    reglas = ('Reglas: si el vigilante comparte sala contigo antes de las 21:00 te sermonea 3 minutos; '
              'después del toque de queda te expulsa. Si el robot te encuentra, avisa por radio y el '
              'vigilante te sigue 2 turnos. Tras sermonearte, se queda 3 turnos escribiendo un reporte. '
              'Deshacer un movimiento también gasta tu turno.')
    caja(s, (492, 244, 440, 250), (30, 52, 62))
    for j, l in enumerate(lineas(reglas, 404, 13)):
        texto(s, l, (508, 260 + j * 20), TENUE, 13)
    texto(s, 'ENTER / ESC cerrar', (28, 604), TEAL, 13)


def dibujar_panel_eventos(s, p):
    """Eventos pendientes de la cola FIFO de la Torre."""
    _fondo_panel(s, 'EVENTOS DEL MAPA · COLA FIFO',
                 'Se encolaron al iniciar la partida. Cada movimiento procesa el siguiente con popleft().')
    total = len(EVENTOS_TORRE)
    quedan = len(p.eventos_torre)
    caja(s, (28, 96, 440, 330), (30, 52, 62))
    texto(s, f'PENDIENTES: {quedan} de {total}', (44, 108), ORO if quedan else ROJO, 16)
    texto(s, 'contar_eventos_de_tipo(): recorre la cola sin modificarla', (44, 132), APAGADO, 11)
    for i, (tipo, cantidad) in enumerate(resumen_eventos(p.eventos_torre).items()):
        y = 160 + i * 38
        texto(s, ETIQUETAS_TIPO[tipo], (44, y), CREAM, 14)
        pygame.draw.rect(s, (59, 81, 92), (220, y + 4, 200, 10))
        pygame.draw.rect(s, (240, 194, 105), (220, y + 4, cantidad * 50, 10))
        texto(s, str(cantidad), (432, y), ORO, 14)
    caja(s, (492, 96, 440, 330), (30, 52, 62))
    texto(s, 'ÚLTIMO EVENTO PROCESADO', (508, 108), TEAL, 14)
    ev = p.ultimo_evento
    if ev:
        texto(s, ev['titulo'], (508, 136), ORO, 14)
        for j, l in enumerate(lineas(ev['texto'], 404, 13)[:3]):
            texto(s, l, (508, 160 + j * 18), CREAM, 13)
    else:
        texto(s, 'Ninguno todavía.', (508, 136), TENUE, 13)
    nota = ('El orden exacto es secreto: los eventos salen en el mismo orden en que entraron. '
            'Decisión de diseño: si deshaces un movimiento, el evento que disparó NO vuelve a la cola. '
            'El reloj de 9PM no retrocede.')
    if not quedan:
        nota = 'La cola está vacía: los próximos movimientos serán en silencio. ' + nota
    for j, l in enumerate(lineas(nota, 404, 13)):
        texto(s, l, (508, 238 + j * 20), TENUE, 13)
    texto(s, 'ENTER / ESC cerrar', (28, 604), TEAL, 13)
