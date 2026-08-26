"""Inventario visual en estilo 8/16 bits: un botón para el HUD y un panel
tipo Fortnite (rejilla de ranuras + detalle del objeto seleccionado).

Esto es solo presentación: los datos siguen viviendo en `inventario.Inventario`.
Todo se dibuja con rectángulos de borde duro, sin antialias y sin esquinas
redondeadas, que es lo que da la sensación de consola vieja.
"""

import math

import pygame

# --------------------------------------------------------------------------
# Paleta retro (pocos colores, bien contrastados)
# --------------------------------------------------------------------------
NEGRO = (12, 10, 24)
MARCO_LUZ = (112, 124, 184)
MARCO_SOMBRA = (26, 28, 58)
FONDO_PANEL = (30, 34, 68)
FONDO_CAJA = (20, 23, 48)
CASILLA = (24, 27, 56)
CASILLA_HOVER = (44, 50, 96)
CASILLA_SEL = (62, 70, 130)
TEXTO = (232, 234, 246)
TEXTO_TENUE = (138, 146, 190)
ORO = (255, 205, 92)
ROJO = (224, 76, 76)

RAREZAS = {
    "comun": ("COMUN", (152, 160, 182)),
    "raro": ("RARO", (72, 148, 232)),
    "epico": ("EPICO", (176, 92, 224)),
    "legendario": ("LEGENDARIO", (255, 178, 48)),
}

# --------------------------------------------------------------------------
# Catálogo: cada objeto trae su sprite 8x8, su rareza y su descripción
# --------------------------------------------------------------------------
CATALOGO = {
    "libro": {
        "titulo": "Libro atrasado",
        "icono": "L",
        "rareza": "raro",
        "descripcion": "Se vencio hoy. Devuelvelo en la biblioteca antes del toque de queda.",
        "arte": {
            "paleta": {
                "a": (198, 62, 62),
                "b": (248, 238, 214),
                "c": (128, 32, 32),
                "d": (232, 200, 160),
            },
            "pixeles": [
                "        ",
                " aaaaaa ",
                " abbbba ",
                " abddba ",
                " abbbba ",
                " abddba ",
                " acccca ",
                "        ",
            ],
        },
    },
    "usb": {
        "titulo": "USB del trabajo",
        "icono": "U",
        "rareza": "comun",
        "descripcion": "Tiene el archivo que hay que imprimir en el laboratorio.",
        "arte": {
            "paleta": {"a": (60, 66, 110), "b": (170, 178, 210), "c": (255, 205, 92)},
            "pixeles": [
                "        ",
                "  bbbb  ",
                "  bbbb  ",
                " aaaaaa ",
                " acccca ",
                " aaaaaa ",
                " aaaaaa ",
                "        ",
            ],
        },
    },
}

# Sprite genérico para cualquier objeto que todavía no esté en el catálogo.
ARTE_GENERICO = {
    "paleta": {"a": (140, 148, 176), "b": (90, 96, 128)},
    "pixeles": [
        "        ",
        " aaaaaa ",
        " abbbba ",
        " abbbba ",
        " abbbba ",
        " abbbba ",
        " aaaaaa ",
        "        ",
    ],
}

# Sprite de la mochila que va dentro del botón del HUD.
ARTE_MOCHILA = {
    "paleta": {
        "a": (176, 114, 62),
        "b": (206, 148, 88),
        "c": (92, 56, 26),
        "d": (255, 205, 92),
    },
    "pixeles": [
        "  cccc  ",
        " cbbbbc ",
        "caaaaaac",
        "caaaaaac",
        "caddddac",
        "caddddac",
        "caaaaaac",
        " cccccc ",
    ],
}


def crear_objeto(nombre, **extra):
    """Devuelve el dict que se guarda en `Inventario`, ya con datos de catálogo."""
    base = CATALOGO.get(nombre, {})
    objeto = {
        "nombre": nombre,
        "icono": base.get("icono", nombre[:1].upper()),
        "titulo": base.get("titulo", nombre.capitalize()),
        "rareza": base.get("rareza", "comun"),
        "descripcion": base.get("descripcion", "Un objeto que recogiste por el campus."),
    }
    objeto.update(extra)
    return objeto


# --------------------------------------------------------------------------
# Dibujo de bajo nivel
# --------------------------------------------------------------------------
_FUENTES = {}
_SCANLINES = {}


def _fuente(tam):
    if tam not in _FUENTES:
        _FUENTES[tam] = pygame.font.SysFont(
            "pressstart2p,perfectdosvga437,fixedsys,lucidaconsole,couriernew",
            tam,
            bold=True,
        )
    return _FUENTES[tam]


def _texto(pantalla, cadena, pos, tam=12, color=TEXTO, centro=False, sombra=True):
    fuente = _fuente(tam)
    imagen = fuente.render(cadena, False, color)   # antialias apagado: pixeles duros
    x, y = pos
    if centro:
        x -= imagen.get_width() // 2
    if sombra:
        pantalla.blit(fuente.render(cadena, False, NEGRO), (x + 2, y + 2))
    pantalla.blit(imagen, (x, y))
    return imagen.get_width()


def _envolver(cadena, tam, ancho_max):
    """Parte el texto en lineas que quepan en `ancho_max` pixeles."""
    fuente = _fuente(tam)
    lineas, actual = [], ""
    for palabra in cadena.split():
        prueba = f"{actual} {palabra}".strip()
        if fuente.size(prueba)[0] <= ancho_max:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def marco_pixel(pantalla, rect, relleno, luz=MARCO_LUZ, sombra=MARCO_SOMBRA, grosor=4):
    """Caja biselada: contorno negro, luz arriba-izquierda, sombra abajo-derecha."""
    rect = pygame.Rect(rect)
    pygame.draw.rect(pantalla, NEGRO, rect)
    interior = rect.inflate(-grosor, -grosor)
    pygame.draw.rect(pantalla, relleno, interior)
    pygame.draw.rect(pantalla, luz, (interior.x, interior.y, interior.w, grosor))
    pygame.draw.rect(pantalla, luz, (interior.x, interior.y, grosor, interior.h))
    pygame.draw.rect(pantalla, sombra, (interior.x, interior.bottom - grosor, interior.w, grosor))
    pygame.draw.rect(pantalla, sombra, (interior.right - grosor, interior.y, grosor, interior.h))
    return interior


def dibujar_arte(pantalla, arte, centro, escala):
    """Pinta un sprite definido como lista de strings, un caracter por pixel."""
    filas = arte["pixeles"]
    paleta = arte["paleta"]
    origen_x = centro[0] - len(filas[0]) * escala // 2
    origen_y = centro[1] - len(filas) * escala // 2
    for j, fila in enumerate(filas):
        for i, caracter in enumerate(fila):
            color = paleta.get(caracter)
            if color:
                pygame.draw.rect(
                    pantalla,
                    color,
                    (origen_x + i * escala, origen_y + j * escala, escala, escala),
                )


def _scanlines(tam):
    """Rayas horizontales tenues; le da el aire de monitor CRT."""
    if tam not in _SCANLINES:
        capa = pygame.Surface(tam, pygame.SRCALPHA)
        for y in range(0, tam[1], 3):
            pygame.draw.line(capa, (0, 0, 0, 38), (0, y), (tam[0], y))
        _SCANLINES[tam] = capa
    return _SCANLINES[tam]


def _arte_de(objeto):
    return CATALOGO.get(objeto["nombre"], {}).get("arte", ARTE_GENERICO)


# --------------------------------------------------------------------------
# Botón del HUD
# --------------------------------------------------------------------------
class BotonInventario:
    """Botón pixelado que abre y cierra el panel."""

    def __init__(self, rect, tecla="I"):
        self.rect = pygame.Rect(rect)
        self.tecla = tecla
        self.hover = False

    def actualizar(self, pos_mouse):
        self.hover = self.rect.collidepoint(pos_mouse)

    def contiene(self, pos):
        return self.rect.collidepoint(pos)

    def dibujar(self, pantalla, cantidad, capacidad, abierto):
        if abierto:
            relleno, luz, sombra = (46, 52, 96), MARCO_SOMBRA, MARCO_LUZ
        elif self.hover:
            relleno, luz, sombra = (58, 64, 112), MARCO_LUZ, MARCO_SOMBRA
        else:
            relleno, luz, sombra = (38, 43, 82), MARCO_LUZ, MARCO_SOMBRA

        # Cuando está "presionado" el botón baja 2px, como los botones de NES.
        rect = self.rect.move(0, 2 if abierto else 0)
        interior = marco_pixel(pantalla, rect, relleno, luz, sombra)

        dibujar_arte(pantalla, ARTE_MOCHILA, (interior.x + 20, interior.centery), 3)
        _texto(pantalla, "BOLSA", (interior.x + 42, interior.y + 6), tam=12,
               color=TEXTO if abierto else ORO)
        lleno = cantidad >= capacidad
        _texto(pantalla, f"[{self.tecla}] {cantidad}/{capacidad}",
               (interior.x + 42, interior.y + 22), tam=10,
               color=ROJO if lleno else TEXTO_TENUE)


# --------------------------------------------------------------------------
# Panel del inventario
# --------------------------------------------------------------------------
class PanelInventario:
    """Rejilla de ranuras estilo Fortnite, con el detalle del objeto al lado."""

    COLUMNAS = 3
    LADO_RANURA = 84
    SEPARACION = 10

    def __init__(self, ancho_pantalla, alto_pantalla, capacidad=6):
        self.capacidad = capacidad
        self.abierto = False
        self.seleccion = 0
        self.hover = None
        self._parpadeo = 0.0

        self.filas = math.ceil(capacidad / self.COLUMNAS)
        alto_rejilla = self.filas * self.LADO_RANURA + (self.filas - 1) * self.SEPARACION
        ancho = 660
        alto = 46 + 20 + alto_rejilla + 20 + 34
        self.rect = pygame.Rect(0, 0, ancho, alto)
        self.rect.center = (ancho_pantalla // 2, alto_pantalla // 2)

        ancho_rejilla = self.COLUMNAS * self.LADO_RANURA + (self.COLUMNAS - 1) * self.SEPARACION
        self.rejilla_x = self.rect.x + 24
        self.rejilla_y = self.rect.y + 66
        detalle_x = self.rejilla_x + ancho_rejilla + 20
        self.detalle = pygame.Rect(
            detalle_x, self.rejilla_y, self.rect.right - 24 - detalle_x, alto_rejilla
        )

    # -- geometría ---------------------------------------------------------
    def rect_ranura(self, indice):
        fila, columna = divmod(indice, self.COLUMNAS)
        return pygame.Rect(
            self.rejilla_x + columna * (self.LADO_RANURA + self.SEPARACION),
            self.rejilla_y + fila * (self.LADO_RANURA + self.SEPARACION),
            self.LADO_RANURA,
            self.LADO_RANURA,
        )

    def _ranura_en(self, pos):
        for indice in range(self.capacidad):
            if self.rect_ranura(indice).collidepoint(pos):
                return indice
        return None

    # -- estado ------------------------------------------------------------
    def alternar(self):
        self.abierto = not self.abierto
        if self.abierto:
            self.seleccion = 0

    def cerrar(self):
        self.abierto = False

    def actualizar(self, dt, pos_mouse):
        self._parpadeo = (self._parpadeo + dt) % 1.0
        self.hover = self._ranura_en(pos_mouse) if self.abierto else None

    def _mover_seleccion(self, dx, dy):
        fila, columna = divmod(self.seleccion, self.COLUMNAS)
        columna = (columna + dx) % self.COLUMNAS
        fila = (fila + dy) % self.filas
        self.seleccion = min(fila * self.COLUMNAS + columna, self.capacidad - 1)

    def manejar_evento(self, evento):
        """True si el panel consumió el evento (para que el juego lo ignore)."""
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_i, pygame.K_TAB):
                self.alternar()
                return True
            if not self.abierto:
                return False
            if evento.key == pygame.K_ESCAPE:
                self.cerrar()
                return True
            if evento.key in (pygame.K_LEFT, pygame.K_a):
                self._mover_seleccion(-1, 0)
                return True
            if evento.key in (pygame.K_RIGHT, pygame.K_d):
                self._mover_seleccion(1, 0)
                return True
            if evento.key in (pygame.K_UP, pygame.K_w):
                self._mover_seleccion(0, -1)
                return True
            if evento.key in (pygame.K_DOWN, pygame.K_s):
                self._mover_seleccion(0, 1)
                return True
            return True   # con el panel abierto no dejamos pasar ninguna otra tecla
        if evento.type == pygame.MOUSEBUTTONDOWN and self.abierto:
            indice = self._ranura_en(evento.pos)
            if indice is not None:
                self.seleccion = indice
            elif not self.rect.collidepoint(evento.pos):
                self.cerrar()
            return True
        return False

    # -- dibujo ------------------------------------------------------------
    def dibujar(self, pantalla, inventario):
        if not self.abierto:
            return

        oscurecer = pygame.Surface(pantalla.get_size(), pygame.SRCALPHA)
        oscurecer.fill((6, 6, 18, 190))
        pantalla.blit(oscurecer, (0, 0))

        interior = marco_pixel(pantalla, self.rect, FONDO_PANEL, grosor=6)

        # Cabecera
        cabecera = pygame.Rect(interior.x + 6, interior.y + 6, interior.w - 12, 34)
        pygame.draw.rect(pantalla, FONDO_CAJA, cabecera)
        pygame.draw.rect(pantalla, MARCO_LUZ, (cabecera.x, cabecera.bottom - 2, cabecera.w, 2))
        _texto(pantalla, "INVENTARIO", (cabecera.x + 10, cabecera.y + 9), tam=15, color=ORO)

        ocupadas = len(inventario.objetos)
        conteo = f"{ocupadas}/{self.capacidad}"
        _texto(pantalla, conteo,
               (cabecera.right - 12 - _fuente(13).size(conteo)[0], cabecera.y + 11),
               tam=13, color=ROJO if ocupadas >= self.capacidad else TEXTO_TENUE)

        # Rejilla de ranuras
        for indice in range(self.capacidad):
            objeto = inventario.objetos[indice] if indice < ocupadas else None
            self._dibujar_ranura(pantalla, indice, objeto)

        # Detalle del objeto seleccionado
        self._dibujar_detalle(
            pantalla,
            inventario.objetos[self.seleccion] if self.seleccion < ocupadas else None,
        )

        _texto(pantalla, "FLECHAS / CLIC: elegir     I o ESC: cerrar",
               (self.rect.centerx, self.rect.bottom - 28), tam=10,
               color=TEXTO_TENUE, centro=True)

        pantalla.blit(_scanlines(self.rect.size), self.rect.topleft)

    def _dibujar_ranura(self, pantalla, indice, objeto):
        rect = self.rect_ranura(indice)
        seleccionada = indice == self.seleccion
        if seleccionada:
            relleno = CASILLA_SEL
        elif self.hover == indice:
            relleno = CASILLA_HOVER
        else:
            relleno = CASILLA
        interior = marco_pixel(pantalla, rect, relleno, MARCO_SOMBRA, MARCO_LUZ, grosor=4)

        if objeto:
            _, color_rareza = RAREZAS.get(objeto.get("rareza", "comun"), RAREZAS["comun"])
            # Franja de rareza en la base, como en los juegos de loot.
            pygame.draw.rect(pantalla, color_rareza,
                             (interior.x, interior.bottom - 6, interior.w, 6))
            dibujar_arte(pantalla, _arte_de(objeto), (interior.centerx, interior.centery - 4), 6)
        else:
            _texto(pantalla, "-", (interior.centerx, interior.centery - 8),
                   tam=14, color=(74, 82, 132), centro=True, sombra=False)

        if seleccionada and self._parpadeo < 0.6:
            pygame.draw.rect(pantalla, ORO, rect, 3)

    def _dibujar_detalle(self, pantalla, objeto):
        interior = marco_pixel(pantalla, self.detalle, FONDO_CAJA, MARCO_SOMBRA, MARCO_LUZ, grosor=4)
        x = interior.x + 12
        ancho_texto = interior.w - 24

        if objeto is None:
            _texto(pantalla, "RANURA VACIA", (interior.centerx, interior.y + 24),
                   tam=12, color=TEXTO_TENUE, centro=True)
            for i, linea in enumerate(
                _envolver("Recoge objetos por el campus con ESPACIO.", 10, ancho_texto)
            ):
                _texto(pantalla, linea, (x, interior.y + 54 + i * 16), tam=10, color=(96, 102, 140))
            return

        etiqueta, color = RAREZAS.get(objeto.get("rareza", "comun"), RAREZAS["comun"])

        marco_pixel(pantalla, (interior.x + 12, interior.y + 12, 72, 72), CASILLA,
                    MARCO_SOMBRA, MARCO_LUZ, grosor=4)
        dibujar_arte(pantalla, _arte_de(objeto), (interior.x + 48, interior.y + 48), 6)

        _texto(pantalla, etiqueta, (interior.x + 96, interior.y + 16), tam=10, color=color)
        titulo = objeto.get("titulo", objeto["nombre"]).upper()
        for i, linea in enumerate(_envolver(titulo, 12, interior.w - 108)):
            _texto(pantalla, linea, (interior.x + 96, interior.y + 34 + i * 18), tam=12)

        pygame.draw.rect(pantalla, (48, 54, 100), (x, interior.y + 96, ancho_texto, 2))
        for i, linea in enumerate(_envolver(objeto.get("descripcion", ""), 10, ancho_texto)):
            _texto(pantalla, linea, (x, interior.y + 108 + i * 16), tam=10, color=TEXTO_TENUE)
