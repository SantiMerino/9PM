"""9PM — arma el juego completo, importa e integra todos los demás módulos.

Eres un estudiante que se quedó tarde en la universidad. Son las 20:15 y a
las 21:00 empieza el toque de queda: si un vigilante te ve después de esa
hora, te expulsan del campus por esa noche. Resuelve tus tres pendientes
(devolver un libro, imprimir un trabajo, hablar con un profesor) y llega al
parqueadero antes de que te atrapen.

Controles:
    WASD / flechas   moverse
    ESPACIO          interactuar con la sala más cercana
    Z                deshacer el último movimiento (pila de historial)
    ENTER            confirmar en menú / pantallas finales
    ESC              salir
"""

import json
import math
import random
from pathlib import Path

import pygame

from inventario import Inventario
from historial import Historial
from eventos import ColaEventos, Evento
from mazmorra import generar_edificio
from ranking import ordenar_puntajes
from buscador import buscar_por_nombre
from mapa import crear_mapa_universidad
from misiones import crear_mision_principal
from estado_mundo import crear_estado_inicial, avanzar_tiempo, formatear_hora

# --------------------------------------------------------------------------
# Configuración general
# --------------------------------------------------------------------------
ANCHO, ALTO = 960, 640
FPS = 60

VELOCIDAD_JUGADOR = 190.0     # px/seg
VELOCIDAD_VIGILANTE = 110.0   # px/seg
RADIO_INTERACCION = 55
RADIO_DETECCION = 75
SEGUNDOS_POR_MINUTO_JUEGO = 1.0   # 1 seg real = 1 minuto de juego
MINUTOS_DE_GRACIA_TRAS_TOQUE_QUEDA = 15

ARCHIVO_PUNTAJES = Path(__file__).parent / "puntajes.json"

COLOR_FONDO = (10, 14, 33)
COLOR_PASILLO = (58, 66, 99)
COLOR_TEXTO = (232, 234, 246)
COLOR_ACENTO = (255, 205, 92)
COLOR_PELIGRO = (224, 76, 76)

SALAS_COLOR = {
    "entrada": (140, 148, 176),
    "patio_central": (108, 168, 118),
    "biblioteca": (150, 110, 220),
    "cafeteria": (230, 150, 80),
    "salon_101": (98, 150, 220),
    "salon_102": (98, 150, 220),
    "laboratorio": (86, 210, 200),
    "auditorio": (220, 96, 120),
    "oficina_profesor": (120, 200, 130),
    "parqueadero": (255, 205, 92),
}

NOMBRES_SALA = {
    "entrada": "Entrada",
    "patio_central": "Patio central",
    "biblioteca": "Biblioteca",
    "cafeteria": "Cafetería",
    "salon_101": "Salón 101",
    "salon_102": "Salón 102",
    "laboratorio": "Laboratorio",
    "auditorio": "Auditorio",
    "oficina_profesor": "Oficina del profesor",
    "parqueadero": "Parqueadero",
}

MENU, JUGANDO, FIN = "menu", "jugando", "fin"


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------
def distancia(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def cargar_puntajes():
    if ARCHIVO_PUNTAJES.exists():
        try:
            return json.loads(ARCHIVO_PUNTAJES.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def guardar_puntaje(registro, puntajes):
    puntajes.append(registro)
    puntajes = ordenar_puntajes(puntajes)[:5]
    ARCHIVO_PUNTAJES.write_text(json.dumps(puntajes, ensure_ascii=False, indent=2), encoding="utf-8")
    return puntajes


def crear_glow(radio, color, alpha_max=90):
    """Superficie con un resplandor radial (varias circunferencias con alpha decreciente)."""
    superficie = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
    for r in range(radio, 0, -2):
        alpha = int(alpha_max * (1 - r / radio))
        pygame.draw.circle(superficie, (*color, alpha), (radio, radio), r)
    return superficie


# --------------------------------------------------------------------------
# Entidades
# --------------------------------------------------------------------------
class Jugador:
    def __init__(self, posicion_inicial):
        self.x, self.y = posicion_inicial
        self.distancia_recorrida = 0.0

    @property
    def pos(self):
        return (self.x, self.y)

    def mover(self, dt, teclas):
        dx = dy = 0.0
        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
            dx -= 1
        if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
            dx += 1
        if teclas[pygame.K_w] or teclas[pygame.K_UP]:
            dy -= 1
        if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
            dy += 1
        if dx == 0 and dy == 0:
            return 0.0
        largo = math.hypot(dx, dy)
        dx, dy = dx / largo, dy / largo
        paso = VELOCIDAD_JUGADOR * dt
        nuevo_x = min(max(self.x + dx * paso, 24), ANCHO - 24)
        nuevo_y = min(max(self.y + dy * paso, 70), ALTO - 40)
        recorrido = distancia((self.x, self.y), (nuevo_x, nuevo_y))
        self.x, self.y = nuevo_x, nuevo_y
        return recorrido


class Vigilante:
    """Patrulla el campus siguiendo un recorrido DFS; entre salas se mueve
    por la ruta más corta (BFS) para no atravesar paredes que no existen."""

    def __init__(self, mapa, sala_inicial="patio_central"):
        self.mapa = mapa
        recorrido = mapa.dfs(sala_inicial)
        self.ciclo = recorrido + recorrido[-2::-1] if len(recorrido) > 1 else recorrido
        self.indice_objetivo = 1 % len(self.ciclo)
        self.sala_actual = self.ciclo[0]
        self.x, self.y = mapa.posiciones[self.sala_actual]
        self.ruta_actual = []
        self.punto_indice = 0

    @property
    def pos(self):
        return (self.x, self.y)

    def _elegir_nueva_ruta(self):
        objetivo = self.ciclo[self.indice_objetivo]
        ruta = self.mapa.bfs(self.sala_actual, objetivo)
        if not ruta or len(ruta) < 2:
            self.sala_actual = objetivo
            self.indice_objetivo = (self.indice_objetivo + 1) % len(self.ciclo)
            self.ruta_actual = []
            return
        self.ruta_actual = ruta
        self.punto_indice = 1

    def actualizar(self, dt):
        if not self.ruta_actual or self.punto_indice >= len(self.ruta_actual):
            self._elegir_nueva_ruta()
            if not self.ruta_actual:
                return
        destino = self.mapa.posiciones[self.ruta_actual[self.punto_indice]]
        d = distancia((self.x, self.y), destino)
        paso = VELOCIDAD_VIGILANTE * dt
        if d <= paso:
            self.x, self.y = destino
            self.sala_actual = self.ruta_actual[self.punto_indice]
            self.punto_indice += 1
            if self.punto_indice >= len(self.ruta_actual):
                self.indice_objetivo = (self.indice_objetivo + 1) % len(self.ciclo)
                self.ruta_actual = []
        else:
            self.x += (destino[0] - self.x) / d * paso
            self.y += (destino[1] - self.y) / d * paso


class Toast:
    def __init__(self, texto, duracion=3.5):
        self.texto = texto
        self.tiempo = duracion


# --------------------------------------------------------------------------
# Partida
# --------------------------------------------------------------------------
class Partida:
    def __init__(self, mapa, fuentes):
        self.mapa = mapa
        self.fuentes = fuentes
        self.estado_mundo = crear_estado_inicial()
        self.hora_limite = self.estado_mundo["hora_toque_queda_min"] + MINUTOS_DE_GRACIA_TRAS_TOQUE_QUEDA
        self.jugador = Jugador(mapa.posiciones["entrada"])
        self.vigilante = Vigilante(mapa, "patio_central")
        self.inventario = Inventario()
        self.historial = Historial()
        self.eventos = ColaEventos()
        self.mision = crear_mision_principal()
        self.mision_libro, self.mision_lab, self.mision_profesor = self.mision.hijas
        self.toasts = []
        self._tiempo_acumulado = 0.0
        self.terminado = False
        self.gano = False
        self.motivo_fin = ""
        self.edificio_lab = generar_edificio("Torre de Laboratorios")

        toque_queda = self.estado_mundo["hora_toque_queda_min"]
        self.eventos.programar(Evento(toque_queda - 10, "aviso", {"texto": "Quedan 10 minutos para el toque de queda."}))
        self.eventos.programar(Evento(toque_queda - 5, "aviso", {"texto": "¡Quedan 5 minutos! Los vigilantes ya están alerta."}))
        self.eventos.programar(Evento(toque_queda, "toque_queda", {"texto": "¡Toque de queda! No dejes que te vean."}))
        self._agregar_toast(f"Explora {NOMBRES_SALA['entrada']} y resuelve tus 3 pendientes antes de las 9PM.")

    def _agregar_toast(self, texto):
        self.toasts.insert(0, Toast(texto))
        self.toasts = self.toasts[:4]

    def _sala_cercana(self):
        mejor_sala, mejor_dist = None, RADIO_INTERACCION
        for nombre, pos in self.mapa.posiciones.items():
            d = distancia(self.jugador.pos, pos)
            if d < mejor_dist:
                mejor_sala, mejor_dist = nombre, d
        return mejor_sala

    def interactuar(self):
        sala = self._sala_cercana()
        if sala is None:
            return
        if sala == "entrada" and not self.mision_libro.completada and not self.inventario.tiene("libro"):
            if self.inventario.agregar({"nombre": "libro", "icono": "L"}):
                self._agregar_toast("Recogiste el libro que debes devolver a la biblioteca.")
        elif sala == "biblioteca" and self.inventario.tiene("libro"):
            self.inventario.quitar("libro")
            self.mision_libro.completar()
            self._agregar_toast("Devolviste el libro. Misión completa.")
        elif sala == "laboratorio" and not self.mision_lab.completada:
            self.mision_lab.completar()
            piso = self.edificio_lab["pisos"][0]
            self._agregar_toast(f"Imprimiste tu trabajo en {piso['aulas'][0]}. Misión completa.")
        elif sala == "oficina_profesor" and not self.mision_profesor.completada:
            self.mision_profesor.completar()
            self._agregar_toast("Hablaste con el profesor. Misión completa.")
        elif sala == "parqueadero":
            if all(h.completada for h in self.mision.hijas):
                self.mision.completar()
                self.terminado, self.gano = True, True
                self.motivo_fin = "Saliste del campus a tiempo."
            else:
                self._agregar_toast("Todavía tienes pendientes antes de irte.")

    def deshacer_movimiento(self):
        anterior = self.historial.deshacer()
        if anterior:
            self.jugador.x, self.jugador.y = anterior
            self._agregar_toast("Deshiciste tu último movimiento.")

    def buscar_en_inventario(self, texto):
        resultados = buscar_por_nombre(self.inventario, texto)
        if resultados:
            self._agregar_toast(f"Buscador: tienes '{texto}' en el inventario.")
        else:
            self._agregar_toast(f"Buscador: no tienes '{texto}' todavía.")

    def actualizar(self, dt, teclas):
        if self.terminado:
            return

        recorrido = self.jugador.mover(dt, teclas)
        self.jugador.distancia_recorrida += recorrido
        if self.jugador.distancia_recorrida >= 40:
            self.jugador.distancia_recorrida = 0.0
            self.historial.registrar(self.jugador.pos)

        self.vigilante.actualizar(dt)

        self._tiempo_acumulado += dt
        while self._tiempo_acumulado >= SEGUNDOS_POR_MINUTO_JUEGO:
            self._tiempo_acumulado -= SEGUNDOS_POR_MINUTO_JUEGO
            avanzar_tiempo(self.estado_mundo, 1)
            for evento in self.eventos.eventos_listos(self.estado_mundo["hora_actual_min"]):
                self._agregar_toast(evento.datos["texto"])

        for toast in self.toasts:
            toast.tiempo -= dt
        self.toasts = [t for t in self.toasts if t.tiempo > 0]

        if self.estado_mundo["toque_queda_activo"]:
            if distancia(self.jugador.pos, self.vigilante.pos) < RADIO_DETECCION:
                self.terminado, self.gano = True, False
                self.motivo_fin = "Un vigilante te vio después del toque de queda."
            elif self.estado_mundo["hora_actual_min"] >= self.hora_limite:
                self.terminado, self.gano = True, False
                self.motivo_fin = "Se acabó la noche: te quedaste encerrado en el campus."

    def calcular_puntaje(self):
        completadas = sum(1 for h in self.mision.hijas if h.completada)
        puntos = completadas * 100
        if self.gano:
            minutos_restantes = max(0, self.hora_limite - self.estado_mundo["hora_actual_min"])
            puntos += minutos_restantes * 5
        return {
            "nombre": "Jugador",
            "puntos": puntos,
            "resultado": "Victoria" if self.gano else "Expulsado",
            "hora_final": formatear_hora(self.estado_mundo["hora_actual_min"]),
        }


# --------------------------------------------------------------------------
# Dibujo
# --------------------------------------------------------------------------
def dibujar_fondo_noche(pantalla, estrellas):
    pantalla.fill(COLOR_FONDO)
    for x, y, r in estrellas:
        pygame.draw.circle(pantalla, (200, 205, 230), (x, y), r)
    pygame.draw.circle(pantalla, (235, 235, 210), (ANCHO - 70, 60), 30)
    pygame.draw.circle(pantalla, COLOR_FONDO, (ANCHO - 58, 50), 26)


def dibujar_mapa(pantalla, mapa, glows):
    ya_dibujadas = set()
    for sala, vecinos in mapa.grafo.items():
        for vecino in vecinos:
            clave = tuple(sorted((sala, vecino)))
            if clave in ya_dibujadas:
                continue
            ya_dibujadas.add(clave)
            pygame.draw.line(pantalla, COLOR_PASILLO, mapa.posiciones[sala], mapa.posiciones[vecino], 5)

    for nombre, pos in mapa.posiciones.items():
        glow = glows[nombre]
        pantalla.blit(glow, (pos[0] - glow.get_width() // 2, pos[1] - glow.get_height() // 2))
        pygame.draw.circle(pantalla, SALAS_COLOR[nombre], pos, 16)
        pygame.draw.circle(pantalla, COLOR_TEXTO, pos, 16, 2)


def dibujar_etiquetas(pantalla, mapa, fuente):
    for nombre, pos in mapa.posiciones.items():
        texto = fuente.render(NOMBRES_SALA[nombre], True, COLOR_TEXTO)
        pantalla.blit(texto, (pos[0] - texto.get_width() // 2, pos[1] + 20))


def dibujar_jugador(pantalla, jugador, glow_linterna):
    pantalla.blit(glow_linterna, (jugador.x - glow_linterna.get_width() // 2, jugador.y - glow_linterna.get_height() // 2))
    pygame.draw.circle(pantalla, COLOR_ACENTO, (int(jugador.x), int(jugador.y)), 10)
    pygame.draw.circle(pantalla, (60, 45, 10), (int(jugador.x), int(jugador.y)), 10, 2)


def dibujar_vigilante(pantalla, vigilante, activo, glow_peligro):
    if activo:
        pantalla.blit(glow_peligro, (vigilante.x - glow_peligro.get_width() // 2, vigilante.y - glow_peligro.get_height() // 2))
    color = COLOR_PELIGRO if activo else (150, 90, 90)
    pygame.draw.circle(pantalla, color, (int(vigilante.x), int(vigilante.y)), 11)
    pygame.draw.circle(pantalla, (30, 10, 10), (int(vigilante.x), int(vigilante.y)), 11, 2)


def dibujar_hud(pantalla, partida, fuentes):
    fuente_reloj, fuente_normal, fuente_chica = fuentes["reloj"], fuentes["normal"], fuentes["chica"]

    pygame.draw.rect(pantalla, (16, 20, 42), (0, 0, ANCHO, 56))
    color_reloj = COLOR_PELIGRO if partida.estado_mundo["toque_queda_activo"] else COLOR_TEXTO
    reloj_txt = fuente_reloj.render(formatear_hora(partida.estado_mundo["hora_actual_min"]), True, color_reloj)
    pantalla.blit(reloj_txt, (18, 10))

    completadas = sum(1 for h in partida.mision.hijas if h.completada)
    mision_txt = fuente_normal.render(f"Misiones: {completadas}/{len(partida.mision.hijas)}", True, COLOR_TEXTO)
    pantalla.blit(mision_txt, (ANCHO - mision_txt.get_width() - 18, 18))

    y = 66
    for toast in partida.toasts:
        alpha = min(255, int(toast.tiempo * 180))
        superficie = fuente_chica.render(toast.texto, True, COLOR_TEXTO)
        superficie.set_alpha(alpha)
        pantalla.blit(superficie, (ANCHO // 2 - superficie.get_width() // 2, y))
        y += 22

    pygame.draw.rect(pantalla, (16, 20, 42), (0, ALTO - 34, ANCHO, 34))
    x = 12
    for objeto in partida.inventario.objetos:
        pygame.draw.rect(pantalla, COLOR_ACENTO, (x, ALTO - 28, 22, 22), border_radius=4)
        letra = fuente_chica.render(objeto["icono"], True, (30, 20, 5))
        pantalla.blit(letra, (x + 7, ALTO - 26))
        x += 28

    ayuda = fuente_chica.render("WASD: moverte  |  ESPACIO: interactuar  |  Z: deshacer  |  F: buscar libro", True, (150, 156, 190))
    pantalla.blit(ayuda, (ANCHO - ayuda.get_width() - 12, ALTO - 26))


def dibujar_menu(pantalla, fuentes, puntajes):
    pantalla.fill(COLOR_FONDO)
    titulo = fuentes["titulo"].render("9PM", True, COLOR_ACENTO)
    pantalla.blit(titulo, (ANCHO // 2 - titulo.get_width() // 2, 110))
    subtitulo = fuentes["normal"].render(
        "No dejes que la universidad te saque a las 9. Resuelve tus pendientes y vete a tiempo.",
        True, COLOR_TEXTO,
    )
    pantalla.blit(subtitulo, (ANCHO // 2 - subtitulo.get_width() // 2, 190))

    aviso = fuentes["normal"].render("Presiona ENTER para jugar", True, COLOR_TEXTO)
    pantalla.blit(aviso, (ANCHO // 2 - aviso.get_width() // 2, 250))

    if puntajes:
        y = 320
        encabezado = fuentes["normal"].render("Mejores partidas:", True, COLOR_ACENTO)
        pantalla.blit(encabezado, (ANCHO // 2 - encabezado.get_width() // 2, y))
        y += 34
        for p in puntajes[:3]:
            linea = f"{p['puntos']} pts — {p['resultado']} — {p['hora_final']}"
            texto = fuentes["chica"].render(linea, True, COLOR_TEXTO)
            pantalla.blit(texto, (ANCHO // 2 - texto.get_width() // 2, y))
            y += 24


def dibujar_fin(pantalla, fuentes, partida):
    pantalla.fill(COLOR_FONDO)
    color = COLOR_ACENTO if partida.gano else COLOR_PELIGRO
    titulo_txt = "¡Llegaste a casa!" if partida.gano else "Te expulsaron del campus"
    titulo = fuentes["titulo"].render(titulo_txt, True, color)
    pantalla.blit(titulo, (ANCHO // 2 - titulo.get_width() // 2, 150))

    motivo = fuentes["normal"].render(partida.motivo_fin, True, COLOR_TEXTO)
    pantalla.blit(motivo, (ANCHO // 2 - motivo.get_width() // 2, 220))

    puntaje = partida.calcular_puntaje()
    resumen = fuentes["normal"].render(f"Puntaje: {puntaje['puntos']} pts", True, COLOR_TEXTO)
    pantalla.blit(resumen, (ANCHO // 2 - resumen.get_width() // 2, 260))

    aviso = fuentes["normal"].render("ENTER para volver al menú", True, COLOR_TEXTO)
    pantalla.blit(aviso, (ANCHO // 2 - aviso.get_width() // 2, 320))


# --------------------------------------------------------------------------
# Bucle principal
# --------------------------------------------------------------------------
def main():
    pygame.init()
    pygame.display.set_caption("9PM")
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    reloj = pygame.time.Clock()

    fuentes = {
        "titulo": pygame.font.SysFont("segoeui", 52, bold=True),
        "reloj": pygame.font.SysFont("consolas", 30, bold=True),
        "normal": pygame.font.SysFont("segoeui", 20),
        "chica": pygame.font.SysFont("segoeui", 15),
    }

    estrellas = [(random.randint(0, ANCHO), random.randint(0, ALTO - 100), random.randint(1, 2)) for _ in range(90)]
    mapa = crear_mapa_universidad()
    glows = {nombre: crear_glow(46, SALAS_COLOR[nombre]) for nombre in mapa.posiciones}
    glow_linterna = crear_glow(120, (255, 221, 130), alpha_max=55)
    glow_peligro = crear_glow(RADIO_DETECCION + 10, COLOR_PELIGRO, alpha_max=40)

    puntajes = ordenar_puntajes(cargar_puntajes())

    estado_juego = MENU
    partida = None

    ejecutando = True
    while ejecutando:
        dt = reloj.tick(FPS) / 1000.0

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    ejecutando = False
                elif estado_juego == MENU and evento.key == pygame.K_RETURN:
                    partida = Partida(mapa, fuentes)
                    estado_juego = JUGANDO
                elif estado_juego == JUGANDO and evento.key == pygame.K_SPACE:
                    partida.interactuar()
                elif estado_juego == JUGANDO and evento.key == pygame.K_z:
                    partida.deshacer_movimiento()
                elif estado_juego == JUGANDO and evento.key == pygame.K_f:
                    partida.buscar_en_inventario("libro")
                elif estado_juego == FIN and evento.key == pygame.K_RETURN:
                    estado_juego = MENU

        if estado_juego == JUGANDO:
            teclas = pygame.key.get_pressed()
            partida.actualizar(dt, teclas)
            if partida.terminado:
                puntajes = guardar_puntaje(partida.calcular_puntaje(), puntajes)
                estado_juego = FIN

        if estado_juego == MENU:
            dibujar_menu(pantalla, fuentes, puntajes)
        elif estado_juego == JUGANDO:
            dibujar_fondo_noche(pantalla, estrellas)
            dibujar_mapa(pantalla, mapa, glows)
            dibujar_vigilante(pantalla, partida.vigilante, partida.estado_mundo["toque_queda_activo"], glow_peligro)
            dibujar_jugador(pantalla, partida.jugador, glow_linterna)
            dibujar_etiquetas(pantalla, mapa, fuentes["chica"])
            dibujar_hud(pantalla, partida, fuentes)
        elif estado_juego == FIN:
            dibujar_fin(pantalla, fuentes, partida)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
