"""Pantalla de la batalla de argumentos y tarjeta de logros.

La batalla usa la perspectiva clásica de un combate por turnos: el vigilante
de frente arriba a la derecha, tu estudiante de espaldas abajo a la izquierda,
las barras de cada uno y el cuadro de texto abajo con las opciones.
"""

import math

import pygame

from arte_pixel import CREAM, INK, caja, fuente, personaje, texto
from logros import COLORES_ICONO
from sprites_jugador import sprite_estudiante

ROJO = (239, 124, 100)
VERDE = (104, 196, 128)
AMARILLO = (241, 199, 116)
TEAL = (72, 169, 158)
TENUE = (162, 194, 185)

CAJA_TEXTO = pygame.Rect(12, 470, 936, 158)
VELOCIDAD_TEXTO = 55          # letras por segundo
DURACION_SACUDIDA = 0.45

COLOR_TIPO = {
    "academico": (110, 165, 184), "autoridad": (176, 168, 238), "calma": (104, 196, 128),
    "tecnico": (241, 199, 116), "evidencia": (226, 124, 172), "huir": (162, 194, 185),
}
NOMBRE_TIPO = {
    "academico": "ACADÉMICO", "autoridad": "AUTORIDAD", "calma": "CALMA",
    "tecnico": "TÉCNICO", "evidencia": "PRUEBA", "huir": "HUIR",
}
NOMBRE_ACUSACION = {"horario": "HORARIO", "zona": "ZONA", "sospecha": "SOSPECHA", "permiso": "PERMISO"}


def partes_mensaje(mensaje):
    """("VIGILANTE" | "TÚ" | None, color, cuerpo) de un mensaje de la batalla."""
    for prefijo, color in (("VIGILANTE:", ROJO), ("TÚ:", TEAL)):
        if mensaje.startswith(prefijo):
            return prefijo[:-1], color, mensaje[len(prefijo):].strip()
    return None, None, mensaje


class EstadoVisual:
    """Lo que solo le importa a la pantalla: máquina de escribir, sacudidas y destellos."""

    def __init__(self):
        self.mensaje = None
        self.t_mensaje = 0.0
        self.golpes_vistos = 0
        self.sacudida = {"vigilante": 0.0, "jugador": 0.0}
        self.destello = 0.0
        self.seleccion = 0
        self.tiempo = 0.0
        self.barra_sospecha = None
        self.barra_credibilidad = None

    def letras_visibles(self):
        return int(self.t_mensaje * VELOCIDAD_TEXTO)

    def texto_completo(self, batalla):
        return self.letras_visibles() >= len(partes_mensaje(batalla.mensaje_actual)[2])

    def completar_texto(self, batalla):
        self.t_mensaje = len(partes_mensaje(batalla.mensaje_actual)[2]) / VELOCIDAD_TEXTO + 0.01

    def actualizar(self, dt, batalla, sonido=None):
        self.tiempo += dt
        if batalla.mensaje_actual != self.mensaje:
            self.mensaje = batalla.mensaje_actual
            self.t_mensaje = 0.0
        else:
            self.t_mensaje += dt
        # Los golpes nuevos se ven cuando aparece el mensaje del efecto.
        while self.golpes_vistos < len(batalla.golpes):
            quien, efecto = batalla.golpes[self.golpes_vistos]
            self.golpes_vistos += 1
            self.sacudida[quien] = DURACION_SACUDIDA
            if quien == "vigilante" and efecto == "super":
                self.destello = 0.25
            if sonido is not None:
                if quien == "vigilante":
                    sonido.efecto({"super": "golpe_super", "debil": "golpe_debil"}.get(efecto, "golpe"))
                else:
                    sonido.efecto("golpe_debil" if efecto == "debil" else "golpe")
        for quien in self.sacudida:
            self.sacudida[quien] = max(0.0, self.sacudida[quien] - dt)
        self.destello = max(0.0, self.destello - dt)
        # Las barras bajan suave, no de golpe.
        for attr, objetivo, maximo in (("barra_sospecha", batalla.sospecha, batalla.sospecha_max),
                                       ("barra_credibilidad", batalla.credibilidad, 100)):
            actual = getattr(self, attr)
            if actual is None:
                actual = objetivo
            actual += (objetivo - actual) * min(1.0, dt * 6)
            if abs(actual - objetivo) < 0.3:
                actual = objetivo
            setattr(self, attr, max(0.0, min(maximo, actual)))


def rects_opciones():
    """4 excusas en 2x2 y el botón de huir."""
    x0, y0 = 476, 486
    excusas = [pygame.Rect(x0 + (i % 2) * 226, y0 + (i // 2) * 52, 218, 46) for i in range(4)]
    return excusas + [pygame.Rect(x0 + 226 * 2 - 452, y0 + 104, 444, 24)]


def opcion_en(pos):
    for i, r in enumerate(rects_opciones()):
        if r.collidepoint(pos):
            return i
    return None


def _barra(s, rect, valor, maximo, color):
    x, y, w, h = rect
    pygame.draw.rect(s, (20, 28, 36), (x - 2, y - 2, w + 4, h + 4))
    pygame.draw.rect(s, (52, 62, 70), rect)
    frac = 0 if maximo <= 0 else max(0.0, min(1.0, valor / maximo))
    pygame.draw.rect(s, color, (x, y, int(w * frac), h))
    pygame.draw.rect(s, (255, 255, 255), (x, y, int(w * frac), 2))


def _color_vida(frac):
    if frac > 0.5:
        return VERDE
    if frac > 0.22:
        return AMARILLO
    return ROJO


def _partir(cadena, ancho, size):
    palabras, lineas, actual = cadena.split(), [], ""
    for p in palabras:
        prueba = (actual + " " + p).strip()
        if fuente(size).size(prueba)[0] <= ancho:
            actual = prueba
        else:
            lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas


def _fondo(s, tiempo, toque_queda):
    arriba = (34, 22, 48) if toque_queda else (24, 34, 58)
    abajo = (70, 40, 52) if toque_queda else (40, 62, 74)
    for y in range(0, 470, 4):
        f = y / 470
        color = tuple(int(arriba[i] + (abajo[i] - arriba[i]) * f) for i in range(3))
        pygame.draw.rect(s, color, (0, y, 960, 4))
    # Ventanales de la Torre con la luna detrás.
    for i in range(5):
        x = 60 + i * 190
        pygame.draw.rect(s, (16, 22, 36), (x, 40, 110, 150))
        pygame.draw.rect(s, (52, 72, 100), (x + 6, 46, 98, 138))
        pygame.draw.line(s, (16, 22, 36), (x + 55, 46), (x + 55, 184), 4)
    pygame.draw.circle(s, (236, 228, 196), (470, 78), 24)
    # Linterna del vigilante barriendo el fondo.
    barrido = int(480 + math.sin(tiempo * 0.9) * 360)
    luz = pygame.Surface((220, 470), pygame.SRCALPHA)
    pygame.draw.polygon(luz, (255, 236, 170, 26), [(110, 0), (0, 470), (220, 470)])
    s.blit(luz, (barrido - 110, 0))
    pygame.draw.rect(s, (30, 38, 46), (0, 300, 960, 170))
    for x in range(0, 960, 64):
        pygame.draw.line(s, (40, 50, 58), (x, 300), (x - 120, 470), 1)


def _plataforma(s, centro, ancho):
    cx, cy = centro
    pygame.draw.ellipse(s, (22, 30, 36), (cx - ancho // 2, cy - 16, ancho, 34))
    pygame.draw.ellipse(s, (66, 96, 98), (cx - ancho // 2 + 8, cy - 12, ancho - 16, 24))


def _caja_info(s, rect, nombre, etiqueta, valor, maximo, color_barra, detalle):
    caja(s, rect, (238, 232, 208), INK)
    x, y, w, h = rect
    texto(s, nombre, (x + 16, y + 10), INK, 18)
    texto(s, etiqueta, (x + 16, y + 44), (90, 74, 60), 12)
    _barra(s, (x + 110, y + 46, w - 130, 12), valor, maximo, color_barra)
    if detalle:
        texto(s, detalle, (x + w - 16 - fuente(13).size(detalle)[0], y + 64), INK, 13)


def dibujar_batalla(s, partida, visual):
    b = partida.batalla
    t = visual.tiempo
    _fondo(s, t, b.toque_queda)

    # --- Vigilante (de frente) ---
    _plataforma(s, (706, 292), 280)
    dx = int(math.sin(visual.sacudida["vigilante"] * 60) * 10) if visual.sacudida["vigilante"] else 0
    bob = int(math.sin(t * 2.2) * 3)
    guardia = personaje("vigilante", "abajo", int(t * 2) % 2 if b.fase == "mensajes" else 0, 7)
    if visual.sacudida["vigilante"] and int(visual.sacudida["vigilante"] * 20) % 2:
        guardia = guardia.copy()
        guardia.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
    s.blit(guardia, guardia.get_rect(midbottom=(706 + dx, 288 + bob)))
    frac_s = (visual.barra_sospecha or 0) / max(1, b.sospecha_max)
    _caja_info(s, pygame.Rect(40, 36, 392, 88), "VIGILANTE NOCTURNO",
               "SOSPECHA", visual.barra_sospecha or 0, b.sospecha_max, ROJO if frac_s > 0.3 else AMARILLO,
               "TOQUE DE QUEDA" if b.toque_queda else "Turno de noche")

    # --- Tú (de espaldas) ---
    _plataforma(s, (250, 470), 330)
    dxj = int(math.sin(visual.sacudida["jugador"] * 60) * 10) if visual.sacudida["jugador"] else 0
    alumno = sprite_estudiante(partida.jugador.personaje, partida.jugador.carrera, "arriba", 0, 9)
    s.blit(alumno, alumno.get_rect(midbottom=(250 + dxj, 520)))
    cred = visual.barra_credibilidad if visual.barra_credibilidad is not None else b.credibilidad
    _caja_info(s, pygame.Rect(536, 330, 392, 96), "TÚ · ESTUDIANTE", "CREDIBILIDAD", cred, 100,
               _color_vida(cred / 100), f"{int(round(cred))}/100")

    if visual.destello:
        flash = pygame.Surface((960, 640), pygame.SRCALPHA)
        flash.fill((255, 255, 255, int(170 * visual.destello / 0.25)))
        s.blit(flash, (0, 0))

    # --- Cuadro de texto ---
    caja(s, CAJA_TEXTO, (24, 34, 46), (236, 228, 196))
    pygame.draw.rect(s, (236, 228, 196), CAJA_TEXTO.inflate(-8, -8), 2)
    if b.fase == "elegir":
        tipo = NOMBRE_ACUSACION.get(b.acusacion["tipo"], "") if b.acusacion else ""
        texto(s, "¿Qué le dices?", (36, 492), CREAM, 22)
        for j, linea in enumerate(_partir(f"«{b.acusacion['texto']}»", 400, 14)[:3]):
            texto(s, linea, (36, 530 + j * 20), TENUE, 14)
        texto(s, f"ACUSACIÓN: {tipo}", (36, 598), ROJO, 12)
        texto(s, "1-4 / flechas + ENTER  ·  5 huir", (240, 598), (120, 140, 140), 11)
        _opciones(s, b, visual, partida)
    else:
        hablante, color, cuerpo = partes_mensaje(b.mensaje_actual)
        cuerpo = cuerpo[:visual.letras_visibles()]
        y = 494
        if hablante:
            texto(s, hablante, (36, y), color, 14)
            y += 24
        for j, linea in enumerate(_partir(cuerpo, 880, 22)[:3]):
            texto(s, linea, (36, y + j * 32), CREAM, 22)
        if visual.texto_completo(b) and int(t * 3) % 2:
            pygame.draw.polygon(s, CREAM, [(912, 600), (928, 600), (920, 610)])


def _opciones(s, b, visual, partida):
    mostrar_pista = partida.dificultad["id"] == "facil"
    for i, ((clave, nombre, tipo, disponible), r) in enumerate(zip(b.opciones(), rects_opciones())):
        elegido = i == visual.seleccion
        color = COLOR_TIPO.get(tipo, TENUE)
        if clave == "huir":
            caja(s, r, (40, 50, 60) if not elegido else (60, 74, 84), color if elegido else (80, 96, 104))
            texto(s, "5 · " + nombre, r.center, CREAM if elegido else TENUE, 13, True)
            continue
        caja(s, r, (46, 62, 76) if elegido else (30, 44, 56), color if elegido else (78, 98, 108))
        pygame.draw.rect(s, color, (r.x + 2, r.y + 2, 5, r.h - 4))
        texto(s, f"{i + 1} · {nombre}", (r.x + 14, r.y + 6), CREAM, 15)
        texto(s, NOMBRE_TIPO.get(tipo, ""), (r.x + 14, r.y + 27), color, 11)
        if mostrar_pista:
            mult = b.efectividad(tipo)
            pista = "MUY BUENA" if mult > 1 else ("NORMAL" if mult == 1 else "FLOJA")
            texto(s, pista, (r.right - 12 - fuente(12).size(pista)[0], r.y + 26), AMARILLO, 12)
        if elegido:
            pygame.draw.polygon(s, CREAM, [(r.x - 10, r.centery - 6), (r.x - 2, r.centery), (r.x - 10, r.centery + 6)])


# ----------------------------------------------------------------------
# Logros
# ----------------------------------------------------------------------
def _icono_logro(s, centro, icono, radio, tiempo):
    cx, cy = centro
    color = COLORES_ICONO.get(icono, AMARILLO)
    # Cintas de la medalla.
    pygame.draw.polygon(s, (190, 70, 70), [(cx - 16, cy - radio - 22), (cx - 4, cy - radio - 22), (cx - 2, cy - radio + 6), (cx - 14, cy - radio + 6)])
    pygame.draw.polygon(s, (70, 110, 190), [(cx + 4, cy - radio - 22), (cx + 16, cy - radio - 22), (cx + 14, cy - radio + 6), (cx + 2, cy - radio + 6)])
    brillo = int(30 * (1 + math.sin(tiempo * 6)))
    pygame.draw.circle(s, INK, (cx, cy), radio + 4)
    pygame.draw.circle(s, tuple(min(255, c + brillo) for c in color), (cx, cy), radio)
    pygame.draw.circle(s, (255, 250, 230), (cx, cy), radio - 6, 2)
    r = radio * 0.5
    if icono in ("estrella", "encargo"):
        puntos = []
        for k in range(10):
            ang = -math.pi / 2 + k * math.pi / 5
            rr = r if k % 2 == 0 else r * 0.45
            puntos.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
        pygame.draw.polygon(s, INK, puntos)
    elif icono == "luna":
        pygame.draw.circle(s, INK, (cx, cy), int(r))
        pygame.draw.circle(s, color, (cx + int(r * 0.45), cy - int(r * 0.25)), int(r * 0.85))
    elif icono == "arbol":
        pygame.draw.polygon(s, INK, [(cx, cy - r), (cx - r, cy + r * 0.5), (cx + r, cy + r * 0.5)])
        pygame.draw.rect(s, INK, (cx - 3, cy + r * 0.5, 6, r * 0.5))
    elif icono == "burbuja":
        pygame.draw.ellipse(s, INK, (cx - r, cy - r * 0.7, 2 * r, 1.4 * r))
        pygame.draw.polygon(s, INK, [(cx - r * 0.4, cy + r * 0.4), (cx - r * 0.8, cy + r), (cx, cy + r * 0.5)])
    elif icono == "mascara":
        pygame.draw.ellipse(s, INK, (cx - r, cy - r * 0.6, 2 * r, 1.3 * r))
        pygame.draw.circle(s, color, (cx - int(r * 0.4), cy - int(r * 0.1)), int(r * 0.22))
        pygame.draw.circle(s, color, (cx + int(r * 0.4), cy - int(r * 0.1)), int(r * 0.22))
    elif icono == "rayo":
        pygame.draw.polygon(s, INK, [(cx + r * 0.2, cy - r), (cx - r * 0.6, cy + r * 0.1), (cx - r * 0.05, cy + r * 0.1),
                                     (cx - r * 0.3, cy + r), (cx + r * 0.6, cy - r * 0.15), (cx + r * 0.05, cy - r * 0.15)])
    elif icono == "llave":
        pygame.draw.circle(s, INK, (cx - int(r * 0.4), cy), int(r * 0.45), 4)
        pygame.draw.rect(s, INK, (cx, cy - 3, r, 6))
        pygame.draw.rect(s, INK, (cx + r * 0.6, cy, 5, r * 0.45))


def dibujar_logro(s, logro, tiempo):
    """Tarjeta que baja desde arriba, se queda y vuelve a subir."""
    if not logro:
        return
    t = logro["t"]
    entrada = min(1.0, t / 0.35)
    salida = max(0.0, (t - 3.0) / 0.4)
    y = int(-130 + 150 * (1 - (1 - entrada) ** 3) - 150 * salida ** 2)
    rect = pygame.Rect(230, y, 500, 112)
    sombra = pygame.Surface(rect.size, pygame.SRCALPHA)
    sombra.fill((0, 0, 0, 110))
    s.blit(sombra, rect.move(6, 6))
    caja(s, rect, (24, 34, 46), COLORES_ICONO.get(logro.get("icono"), AMARILLO))
    pygame.draw.rect(s, COLORES_ICONO.get(logro.get("icono"), AMARILLO), (rect.x + 2, rect.y + 2, rect.w - 4, 4))
    _icono_logro(s, (rect.x + 62, rect.y + 62), logro.get("icono", "encargo"), 30, tiempo)
    encabezado = "¡ENCARGO COMPLETADO!" if logro.get("clave", "").startswith("encargo:") else "¡LOGRO DESBLOQUEADO!"
    texto(s, encabezado, (rect.x + 112, rect.y + 16), AMARILLO, 13)
    texto(s, logro["titulo"], (rect.x + 112, rect.y + 36), CREAM, 22)
    for j, linea in enumerate(_partir(logro.get("texto", ""), 360, 13)[:2]):
        texto(s, linea, (rect.x + 112, rect.y + 68 + j * 18), TENUE, 13)
    if logro.get("puntos"):
        etiqueta = f"+{logro['puntos']}"
        texto(s, etiqueta, (rect.right - 16 - fuente(20).size(etiqueta)[0], rect.y + 14), VERDE, 20)
