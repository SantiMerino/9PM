"""9PM — arma el juego completo, importa e integra todos los demás módulos.

Eres un estudiante que se quedó tarde en el Instituto Kriete. Son las 20:15 y a
las 21:00 empieza el toque de queda: si un vigilante te ve después de esa
hora, te expulsan del campus por esa noche. Resuelve los trece encargos
repartidos por aulas, laboratorios y salas de apoyo y sal por
el lobby o la terraza antes de que te atrapen.

Nivel 1: overworld (pasillo + jardín del croquis) + interiores estilo Pokémon
(entrar por la puerta carga SOLO esa sala; el felpudo sur te devuelve).

Nivel 2 (Checkpoint 2): las gradas suben a la Torre de Laboratorios, un árbol
de salas generado con recursividad (mazmorra.py) que se recorre por turnos
desde un menú: cada movimiento queda en el historial (pila, historial.py),
procesa el siguiente evento del mapa y juega una ronda de turnos (colas,
eventos.py). Deshacer te devuelve de verdad a la sala anterior.

Controles:
    WASD / flechas   moverse
    ESPACIO          interactuar / recoger / usar / entrar puerta
    G                soltar el último objeto del inventario
    I / TAB          abrir el inventario
    M / J            mapa / bitácora (pausan el juego)
    H                historial de acciones (pausa el juego)
    Z                deshacer la última acción (pila de historial)
    Torre            escribe el número de la opción y presiona ENTER
    ENTER            confirmar personaje / pantallas finales
    A/D o ←/→        elegir personaje en el menú
    clic             elegir personaje en el menú
    F11              pantalla completa
    ESC              pausa / cerrar paneles
"""

import json
import math
import random
import sys
from pathlib import Path

import pygame

from inventario import Inventario
from historial import (
    crear_accion,
    apilar_accion,
    deshacer_ultima_accion,
    consultar_ultima_accion,
    mostrar_historial,
    deshacer_multiples,
)
from eventos import (
    ColaEventos,
    Evento,
    crear_cola_eventos_torre,
    procesar_siguiente_evento,
    resumen_eventos,
    crear_turnos,
    siguiente_turno,
    simular_turnos,
    ESTUDIANTE,
    VIGILANTE,
    ROBOT,
    ETIQUETAS_TIPO,
)
from mazmorra import (
    generar_mazmorra,
    dibujar_arbol,
    salas_conectadas,
    estan_conectadas,
    existe_sala,
    buscar_sala,
    paso_hacia,
    DESCRIPCIONES,
)
from ranking import ordenar_puntajes
from buscador import buscar_por_nombre
from mapa import crear_mapa_universidad
from mapa_nivel1 import (
    MUNDO_ANCHO,
    MUNDO_ALTO,
    SALAS_RECT,
    NOMBRES,
    PUERTAS,
    GRADAS_TRIGGER,
    SALIDAS,
    SPAWN_LOBBY,
    es_caminable,
    puerta_en,
    punto_en_rect,
)
from interiores import (
    obtener_interior,
    colision_interior,
    en_zona_salida,
    interactivo_cercano,
    dibujar_interior,
    dibujar_interactivos_interior,
)
from misiones import crear_mision_principal
from estado_mundo import crear_estado_inicial, avanzar_tiempo, formatear_hora
from ui_inventario import BotonInventario, PanelInventario, crear_objeto, dibujar_arte, obtener_arte, reiniciar_fuentes, es_tesoro
from ui_torre import (
    dibujar_torre,
    dibujar_panel_historial,
    dibujar_panel_turnos,
    dibujar_panel_eventos,
    objetivo_clic,
)
from tutorial import Tutorial, cargar_progreso, guardar_progreso
from sprites_jugador import PERSONAJES, cargar_sprites_jugador, sprite_estudiante
from carreras import obtener_carrera
from habilidades import HabilidadCarrera
from menu_inicio import PantallaInicio
from arte_pixel import personaje as sprite_personaje, prop, texto, caja, fuente, CREAM, TEAL
from mundo_visual import dibujar_overworld, campus
from hud_campus import dibujar_hud, dibujar_mapa, dibujar_diario, dibujar_pausa, dibujar_efecto_habilidad
from render import (
    LOGICAL_W,
    LOGICAL_H,
    VENTANA_W,
    VENTANA_H,
    crear_ventana,
    crear_superficie_logica,
    presentar,
    ventana_a_logico,
    evento_con_pos_logica,
)

# --------------------------------------------------------------------------
# Configuración general
# --------------------------------------------------------------------------
ANCHO, ALTO = LOGICAL_W, LOGICAL_H  # resolución lógica (cámara / HUD)
FPS = 60

VELOCIDAD_JUGADOR = 190.0
VELOCIDAD_VIGILANTE = 110.0
RADIO_INTERACCION = 55
RADIO_DETECCION = 75
MARGEN_MUNDO = 20
SEGUNDOS_POR_MINUTO_JUEGO = 12.0
MINUTOS_DE_GRACIA_TRAS_TOQUE_QUEDA = 15

# Torre de Laboratorios (nivel 2, por turnos)
PASILLO = "pasillo"
POS_PIE_GRADAS = (GRADAS_TRIGGER[0] + GRADAS_TRIGGER[2] // 2, GRADAS_TRIGGER[1] + GRADAS_TRIGGER[3] + 14)
MINUTOS_POR_RONDA_TORRE = 1      # cada ronda de turnos gasta un minuto del reloj
MINUTOS_SERMON = 3               # lo que cuesta que el vigilante te encuentre antes de las 21:00
TURNOS_ALERTA_ROBOT = 2          # turnos que el vigilante te persigue tras el aviso del robot
TURNOS_REPORTE = 3               # turnos que el vigilante se queda escribiendo tras sermonearte
PUNTOS_POR_TESORO = 150
ECO_CONSOLA = True               # la partida también se narra en la consola
TUTORIAL_AUTOMATICO = True       # el tutorial aparece solo la primera vez

OPCIONES_TORRE = (
    "Moverse",
    "Recoger objeto",
    "Soltar objeto",
    "Deshacer última acción",
    "Deshacer varias",
    "Ver historial",
    "Ver turnos",
    "Ver eventos",
    "Ver inventario",
)

ARCHIVO_PUNTAJES = Path(__file__).parent / "puntajes.json"
ARCHIVO_TUTORIAL = Path(__file__).parent / "tutorial.json"

COLOR_FONDO = (12, 11, 16)
COLOR_TEXTO = (232, 234, 246)
COLOR_ACENTO = (255, 205, 92)
COLOR_PELIGRO = (224, 76, 76)

# Objetos en overworld (lobby / aulas / cafetería)
OBJETOS_MAPA = [
    {"nombre": "libro", "pos": (848, 840)},       # lobby
    {"nombre": "usb", "pos": (584, 560)},         # cerca R101
    {"nombre": "cafe", "pos": (612, 104)},        # cafetería
    {"nombre": "llaves", "pos": (884, 360)},      # jardín
    {"nombre": "paraguas", "pos": (940, 112)},    # terraza
]

# Easter eggs overworld
INTERACTIVOS = [
    {
        "id": "cartel_lobby",
        "pos": (888, 848),
        "mensaje": "Cartel de toque de queda: «A las 21:00 cierran las puertas. Sin excepciones.»",
        "once": True,
    },
    {
        "id": "maquina_cafeteria",
        "pos": (616, 168),
        "mensaje": "La máquina del pasillo parpadea: «ERROR 9PM». Mejor entra a la cafetería.",
        "once": False,
    },
    {
        "id": "banco_jardin",
        "pos": (884, 432),
        "mensaje": "Banco del jardín. Una nota: «Si te quedas dormido aquí, despiertas en Decanato.»",
        "once": False,
    },
    {
        "id": "aviso_labs",
        "pos": (1080, 240),
        "mensaje": "Pasillo de labs: Siemens → Click → Spark → Kite. Casco mental recomendado.",
        "once": True,
    },
]

MENU, JUGANDO, FIN = "menu", "jugando", "fin"

# Transición puerta: freeze → fade out → swap → fade in (+ título opcional)
TRANS_IDLE = "idle"
TRANS_FADE_OUT = "fade_out"
TRANS_FADE_IN = "fade_in"
TRANS_TITLE = "title"
TRANS_HALF = 0.22  # segundos por mitad fade
TRANS_TITLE_DUR = 0.35


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
    superficie = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
    for r in range(radio, 0, -2):
        alpha = int(alpha_max * (1 - r / radio))
        pygame.draw.circle(superficie, (*color, alpha), (radio, radio), r)
    return superficie


def leer_numero(texto, minimo, maximo):
    """Valida lo que el jugador escribió en un menú numerado.
    Devuelve (numero, None) si es válido o (None, mensaje) si no: texto,
    vacío, 0, negativos y números fuera de rango nunca rompen el juego."""
    texto = texto.strip()
    rango = f"Elige un número del {minimo} al {maximo}."
    if not texto:
        return None, f"No escribiste nada. {rango}"
    try:
        numero = int(texto)
    except ValueError:
        return None, f"Opción no válida: «{texto}» no es un número. {rango}"
    if numero < minimo or numero > maximo:
        if numero < 0:
            motivo = f"{numero} es un número negativo"
        elif numero == 0:
            motivo = "0 no es una opción"
        else:
            motivo = f"{numero} está fuera de rango"
        return None, f"Opción no válida: {motivo}. {rango}"
    return numero, None


def imprimir_seguro(linea):
    """print() que no se cae si la consola no soporta algún carácter."""
    try:
        print(linea, flush=True)
    except UnicodeEncodeError:
        codificacion = getattr(sys.stdout, "encoding", None) or "ascii"
        print(linea.encode(codificacion, "replace").decode(codificacion), flush=True)


def nombre_lugar(lugar):
    """Nombre legible de un lugar del historial (campus o Torre)."""
    if lugar == PASILLO:
        return "Pasillo del campus"
    return NOMBRES.get(lugar, lugar)


def calcular_camara(objetivo, mundo_w=MUNDO_ANCHO, mundo_h=MUNDO_ALTO):
    # El mundo ocupa el espacio entre las dos barras del HUD.
    x = ((mundo_w - ANCHO) / 2 if mundo_w < ANCHO else
         min(max(objetivo[0] - ANCHO / 2, 0), mundo_w - ANCHO))
    y = ((mundo_h - 528) / 2 - 64 if mundo_h < 528 else
         min(max(objetivo[1] - 328, -64), mundo_h - 592))
    return x, y


# --------------------------------------------------------------------------
# Entidades
# --------------------------------------------------------------------------
class Jugador:
    def __init__(self, posicion_inicial, personaje="universitario", carrera="computacion"):
        self.x, self.y = posicion_inicial
        self.carrera = obtener_carrera(carrera).id
        self.factor_velocidad = 1.0
        self.distancia_recorrida = 0.0
        self.animacion_paso = 0.0
        self.moviendo = False
        self.direccion = "abajo"
        self.personaje = personaje if personaje in PERSONAJES else "universitario"

    @property
    def pos(self):
        return (self.x, self.y)

    def intentar_mover(self, dt, teclas, puede_estar):
        """Mueve con colisión: prueba ejes por separado (deslizar en paredes)."""
        dx = dy = 0.0
        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
            dx -= 1
        if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
            dx += 1
        if teclas[pygame.K_w] or teclas[pygame.K_UP]:
            dy -= 1
        if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
            dy += 1
        self.moviendo = False
        if dx == 0 and dy == 0:
            return 0.0

        if abs(dx) > abs(dy):
            self.direccion = "derecha" if dx > 0 else "izquierda"
        elif dy != 0:
            self.direccion = "abajo" if dy > 0 else "arriba"

        largo = math.hypot(dx, dy)
        dx, dy = dx / largo, dy / largo
        paso = VELOCIDAD_JUGADOR * self.factor_velocidad * dt

        recorrido = 0.0
        nx = self.x + dx * paso
        if puede_estar(nx, self.y):
            recorrido += abs(nx - self.x)
            self.x = nx
        ny = self.y + dy * paso
        if puede_estar(self.x, ny):
            recorrido += abs(ny - self.y)
            self.y = ny
        self.moviendo = recorrido > 0
        self.animacion_paso += recorrido / 13
        return recorrido


class Vigilante:
    """Patrulla el overworld siguiendo DFS; entre nodos usa BFS."""

    def __init__(self, mapa, sala_inicial="jardin_c"):
        self.mapa = mapa
        recorrido = mapa.dfs(sala_inicial)
        self.ciclo = recorrido + recorrido[-2::-1] if len(recorrido) > 1 else recorrido
        self.indice_objetivo = 1 % len(self.ciclo)
        self.sala_actual = self.ciclo[0]
        self.x, self.y = mapa.posiciones[self.sala_actual]
        self.ruta_actual = []
        self.punto_indice = 0
        self.direccion = "abajo"
        self.congelado = False

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
        if self.congelado:
            return
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
            ddx, ddy = destino[0] - self.x, destino[1] - self.y
            if abs(ddx) > abs(ddy):
                self.direccion = "derecha" if ddx > 0 else "izquierda"
            else:
                self.direccion = "abajo" if ddy > 0 else "arriba"
            self.x += ddx / d * paso
            self.y += ddy / d * paso


class Toast:
    def __init__(self, texto, duracion=3.5):
        self.texto = texto
        self.tiempo = duracion


# --------------------------------------------------------------------------
# Partida
# --------------------------------------------------------------------------
class Partida:
    def __init__(self, mapa, fuentes, personaje="universitario", carrera="computacion",
                 semilla=None, eco_consola=False):
        self.mapa = mapa
        self.fuentes = fuentes
        self.azar = random.Random(semilla)
        self.eco_consola = eco_consola
        self.consola = []          # narración de la partida (también va a la consola)
        self.estado_mundo = crear_estado_inicial()
        self.hora_limite = self.estado_mundo["hora_toque_queda_min"] + MINUTOS_DE_GRACIA_TRAS_TOQUE_QUEDA
        self.jugador = Jugador(SPAWN_LOBBY, personaje=personaje, carrera=carrera)
        self.habilidad = HabilidadCarrera(carrera)
        self.vigilante = Vigilante(mapa, "jardin_c")
        self.inventario = Inventario()
        self.historial = []        # PILA de acciones (historial.py)
        self.eventos = ColaEventos()
        self.mision = crear_mision_principal()
        self.mision_libro, self.mision_lab, self.mision_profesor = self.mision.hijas[:3]
        self.objetos_mundo = [dict(objeto, recogido=False) for objeto in OBJETOS_MAPA]
        self.interactivos = [dict(item, usado=False) for item in INTERACTIVOS]
        self.toasts = []
        self._tiempo_acumulado = 0.0
        self.tiempo_animacion = 0.0
        self.terminado = False
        self.gano = False
        self.motivo_fin = ""

        # Torre de Laboratorios: se genera RECURSIVAMENTE al iniciar la partida
        # y sus eventos del mapa se encolan desde ya (FIFO).
        self.torre = generar_mazmorra(self.azar.randrange(1_000_000))
        self.eventos_torre = crear_cola_eventos_torre(self.azar)
        self.turnos = crear_turnos()
        nivel2 = [s for s in self.torre["salas"] if self.torre["niveles"][s] == 2]
        self.posiciones_torre = {
            VIGILANTE: self.azar.choice(self.torre["hijos"][self.torre["raiz"]]),
            ROBOT: self.azar.choice(nivel2),
        }
        self.objetos_torre = {sala: [obj] for sala, obj in self.torre["objetos"].items()}
        self.sala_torre = None
        self.salas_visitadas = set()
        self.tesoros_revelados = set()
        self.alerta_vigilante = 0
        self.pausa_vigilante = 0
        self.rondas_jugadas = 0
        self.ultimo_evento = None
        self.evento_t = -99.0          # momento del último evento (para el aviso en pantalla)
        self.menu_torre = "principal"   # | "mover" | "soltar" | "deshacer_varias"
        self.opciones_submenu = []
        self.entrada_torre = ""
        self.pedir_inventario = False
        self._encuentros_ronda = set()
        self._robot_contigo = False

        # Pokémon-style location
        self.ubicacion = "pasillo"  # | "interior" | "torre"
        self.sala_interior = None
        self.interior_data = None
        self.interior_interactivos = []
        self.interiores_estado = {}
        self.panel_activo = None
        self._puerta_origen = None
        self._cooldown_puerta = 0.0  # evita re-entrar al salir
        # Transición puerta (state machine)
        self._trans_fase = TRANS_IDLE
        self._trans_t = 0.0
        self._trans_fade = 0.0  # 0..1 negro
        self._trans_titulo = ""
        self._trans_accion = None  # callable diferido al swap

        toque_queda = self.estado_mundo["hora_toque_queda_min"]
        self.eventos.programar(Evento(toque_queda - 10, "aviso", {"texto": "Quedan 10 minutos para el toque de queda."}))
        self.eventos.programar(Evento(toque_queda - 5, "aviso", {"texto": "¡Quedan 5 minutos! Los vigilantes ya están alerta."}))
        self.eventos.programar(Evento(toque_queda, "toque_queda", {"texto": "¡Toque de queda! No dejes que te vean."}))
        self._log("=== 9PM · Instituto Kriete ===")
        self._log(f"Mazmorra generada: Torre de Laboratorios con {len(self.torre['salas'])} salas, "
                  f"profundidad {self.torre['profundidad_real']}.")
        self._log("Salas por nivel: " + ", ".join(
            f"nivel {n}: {c}" for n, c in sorted(self.torre["por_nivel"].items())))
        for linea in dibujar_arbol(self.torre["raiz"], self.torre["hijos"]):
            self._log("  " + linea)
        self._log(f"Eventos del mapa en cola: {len(self.eventos_torre)}. "
                  f"Turnos: {' -> '.join(self.turnos)}.")
        self._agregar_toast("Bienvenido a KEY. Completa 13 encargos y sal antes del cierre. "
                            "Las gradas suben a la Torre (2º nivel). Q herramienta · M mapa · "
                            "J misiones · H historial.")

    # ------------------------------------------------------------------
    # Narración
    # ------------------------------------------------------------------
    def _log(self, texto):
        """Agrega una línea a la narración (consola de la Torre y stdout)."""
        linea = f"[{formatear_hora(self.estado_mundo['hora_actual_min'])}] {texto}"
        self.consola.append(linea)
        if self.eco_consola:
            imprimir_seguro(linea)

    def _agregar_toast(self, texto):
        self._log(texto)
        self.toasts.insert(0, Toast(texto, max(3.5, len(texto) / 28)))
        self.toasts = self.toasts[:4]

    # ------------------------------------------------------------------
    # Historial (pila): registrar y deshacer acciones
    # ------------------------------------------------------------------
    def lugar_actual(self):
        """Id del lugar donde está el jugador: pasillo, sala interior o sala de la Torre."""
        if self.ubicacion == "interior":
            return self.sala_interior
        if self.ubicacion == "torre":
            return self.sala_torre
        return PASILLO

    def _registrar(self, tipo, texto, **datos):
        """Apila una acción en el historial (append)."""
        accion = crear_accion(tipo, texto, formatear_hora(self.estado_mundo["hora_actual_min"]), **datos)
        apilar_accion(self.historial, accion)
        total = len(self.historial)
        self._log(f"  (historial: +{tipo} · {total} {'acción' if total == 1 else 'acciones'} en la pila)")
        return accion

    def deshacer_accion(self):
        """Deshace la acción más reciente (pop) y revierte su efecto.
        Si el historial está vacío, avisa y no pasa nada más."""
        if self.en_transicion or self.terminado:
            return False
        accion = deshacer_ultima_accion(self.historial)
        if accion is None:
            self._agregar_toast("No hay acciones que deshacer: el historial está vacío.")
            return False
        if not self._revertir(accion):
            apilar_accion(self.historial, accion)  # no se pudo: vuelve a la cima
            return False
        return True

    # Nombre histórico de la tecla Z.
    deshacer_movimiento = deshacer_accion

    def acciones_deshacibles_en_torre(self):
        """Cuántas acciones seguidas, desde la cima, ocurrieron dentro de la Torre."""
        cantidad = 0
        for accion in reversed(self.historial):
            if accion["tipo"] == "mover":
                dentro = existe_sala(self.torre, accion["desde"]) and existe_sala(self.torre, accion["hacia"])
            else:
                dentro = accion.get("zona") == "torre"
            if not dentro:
                break
            cantidad += 1
        return cantidad

    def deshacer_varias(self, cantidad):
        """Deshace varias acciones de la Torre con deshacer_multiples (pop x N)."""
        disponibles = self.acciones_deshacibles_en_torre()
        if cantidad < 1 or cantidad > disponibles:
            self._log(f"Solo puedes deshacer entre 1 y {disponibles} acciones de la Torre.")
            return 0
        acciones = deshacer_multiples(self.historial, cantidad)
        for deshechas, accion in enumerate(acciones):
            if self.terminado or not self._revertir(accion):
                # Lo que no se pudo revertir vuelve a la pila en su orden original.
                for pendiente in reversed(acciones[deshechas:]):
                    apilar_accion(self.historial, pendiente)
                return deshechas
        return len(acciones)

    def _revertir(self, accion):
        tipo = accion["tipo"]
        if tipo == "mover":
            return self._revertir_movimiento(accion)
        if tipo == "recoger":
            nombre = accion["objeto"]
            if self.inventario.soltar(nombre) is None:
                self._agregar_toast("No puedes deshacer eso: el objeto ya no está en tu mochila.")
                return False
            if accion.get("zona") == "torre":
                self.objetos_torre.setdefault(accion["sala"], []).append(nombre)
                lugar = accion["sala"]
            else:
                accion["ref"]["recogido"] = False
                lugar = "su sitio en el campus"
            self._agregar_toast(f"Deshaces: {crear_objeto(nombre)['titulo']} vuelve a {lugar}.")
            return True
        if tipo == "soltar":
            nombre = accion["objeto"]
            if self.inventario.esta_lleno():
                self._agregar_toast("No puedes deshacer eso: tu mochila está llena.")
                return False
            if accion.get("zona") == "torre":
                suelo = self.objetos_torre.get(accion["sala"], [])
                if nombre not in suelo:
                    return False
                suelo.reverse(); suelo.remove(nombre); suelo.reverse()
            else:
                if not any(o is accion["ref"] for o in self.objetos_mundo):
                    return False
                self.objetos_mundo = [o for o in self.objetos_mundo if o is not accion["ref"]]
            self.inventario.agregar(crear_objeto(nombre))
            self._agregar_toast(f"Deshaces: {crear_objeto(nombre)['titulo']} vuelve a tu mochila.")
            return True
        if tipo == "usar":
            mision = next(m for m in self.mision.hijas if m.ubicacion == accion["sala"])
            if mision.paso != accion["paso"] + 1 or self.inventario.esta_lleno():
                self._agregar_toast("No puedes deshacer ese uso: la estación ya avanzó.")
                return False
            mision.paso = accion["paso"]
            mision.completada = False
            accion["estacion"]["usado"] = False
            self.inventario.agregar(crear_objeto(accion["objeto"]))
            self._agregar_toast(f"Deshaces: recuperas {crear_objeto(accion['objeto'])['titulo']}; "
                                f"{NOMBRES[accion['sala']]} vuelve a «{mision.objetivo_actual}».")
            return True
        return False

    def _revertir_movimiento(self, accion):
        """Backtracking: devuelve al jugador a la sala de la que vino."""
        desde, hacia = accion["desde"], accion["hacia"]
        if self.lugar_actual() != hacia:
            self._agregar_toast("No puedes deshacer ese movimiento desde aquí.")
            return False
        if existe_sala(self.torre, desde) and self.ubicacion == "torre":
            # Dentro de la Torre: retroceder también gasta tu turno, pero NO
            # procesa un evento nuevo (el del movimiento deshecho se perdió).
            self.sala_torre = desde
            self._log(f"Deshaces el movimiento: vuelves a {desde}.")
            self._jugar_ronda(f"retrocediste a {desde}")
            if not self.terminado:
                self._describir_sala_torre()
        elif existe_sala(self.torre, desde):
            self._log(f"Deshaces el movimiento: subes otra vez a {desde}.")
            self._iniciar_transicion(lambda: self._aplicar_entrar_torre(registrar=False, sala=desde),
                                     titulo="Torre de Laboratorios")
        elif desde == PASILLO and self.ubicacion == "torre":
            self._log("Deshaces el movimiento: bajas por las gradas al campus.")
            self._iniciar_transicion(lambda: self._aplicar_salir_torre(registrar=False))
        elif desde == PASILLO:
            self._log(f"Deshaces el movimiento: sales de {nombre_lugar(hacia)} al pasillo.")
            self._iniciar_transicion(lambda: self._aplicar_salir(registrar=False))
        else:
            self._log(f"Deshaces el movimiento: vuelves a {nombre_lugar(desde)}.")
            self._iniciar_transicion(lambda: self._aplicar_entrar(desde, registrar=False),
                                     titulo=NOMBRES.get(desde, ""))
        return True

    def mundo_actual_size(self):
        if self.ubicacion == "interior" and self.interior_data:
            return self.interior_data["ancho"], self.interior_data["alto"]
        return MUNDO_ANCHO, MUNDO_ALTO

    def _puede_estar_pasillo(self, x, y):
        return es_caminable(x, y)

    def _puede_estar_interior(self, x, y):
        if self.interior_data is None:
            return False
        return not colision_interior(self.interior_data, x, y)

    @property
    def en_transicion(self):
        return self._trans_fase != TRANS_IDLE

    def _iniciar_transicion(self, accion, titulo=""):
        """Freeze → fade out → swap (accion) → fade in → optional title."""
        if self.en_transicion:
            return
        self._trans_accion = accion
        self._trans_titulo = titulo or ""
        self._trans_fase = TRANS_FADE_OUT
        self._trans_t = 0.0
        self._trans_fade = 0.0

    def _aplicar_entrar(self, puerta_id, registrar=True):
        data = PUERTAS[puerta_id]
        nombre = data["interior"]
        sala = obtener_interior(nombre)
        if registrar:
            self._registrar("mover", f"Pasillo → {data['etiqueta']}", desde=PASILLO, hacia=nombre)
        self.ubicacion = "interior"
        self.sala_interior = nombre
        self.interior_interactivos = self.interiores_estado.setdefault(nombre, [dict(it, usado=False) for it in sala.get("interactivos", [])])
        self.interior_data = dict(sala)
        self.interior_data["interactivos"] = self.interior_interactivos
        self._puerta_origen = puerta_id
        self.jugador.x, self.jugador.y = sala["spawn"]
        self.jugador.direccion = "arriba"
        self.vigilante.congelado = True
        m = next(m for m in self.mision.hijas if m.ubicacion == nombre)
        self._agregar_toast(f"{data['etiqueta']}: {m.objetivo_actual}.")

    def _aplicar_salir(self, registrar=True):
        if not self._puerta_origen:
            self.ubicacion = "pasillo"
            self.sala_interior = None
            self.interior_data = None
            self.vigilante.congelado = False
            return
        if registrar:
            self._registrar("mover", f"{NOMBRES[self.sala_interior]} → Pasillo",
                            desde=self.sala_interior, hacia=PASILLO)
        retorno = PUERTAS[self._puerta_origen]["retorno"]
        self.jugador.x, self.jugador.y = retorno
        self.jugador.direccion = "izquierda"
        self.ubicacion = "pasillo"
        self.sala_interior = None
        self.interior_data = None
        self.interior_interactivos = []
        self._puerta_origen = None
        self.vigilante.congelado = False
        self._cooldown_puerta = 0.9
        self._agregar_toast("Volviste al pasillo.")

    def entrar_interior(self, puerta_id):
        if self.en_transicion:
            return
        data = PUERTAS[puerta_id]
        self._iniciar_transicion(
            lambda: self._aplicar_entrar(puerta_id),
            titulo=data.get("etiqueta", ""),
        )

    def salir_interior(self):
        if self.en_transicion:
            return
        self._iniciar_transicion(self._aplicar_salir, titulo="")

    # ------------------------------------------------------------------
    # Reloj y fin de partida
    # ------------------------------------------------------------------
    def _avanzar_minutos(self, minutos):
        """Avanza el reloj minuto a minuto y dispara los avisos que toquen."""
        for _ in range(minutos):
            avanzar_tiempo(self.estado_mundo, 1)
            for evento in self.eventos.eventos_listos(self.estado_mundo["hora_actual_min"]):
                self._agregar_toast(evento.datos["texto"])
        if not self.terminado and self.estado_mundo["hora_actual_min"] >= self.hora_limite:
            self._terminar(False, "Se acabó la noche: te quedaste encerrado en el campus.")

    def _terminar(self, gano, motivo):
        self.terminado, self.gano, self.motivo_fin = True, gano, motivo
        self._log(("VICTORIA: " if gano else "FIN DE LA PARTIDA: ") + motivo)

    # ------------------------------------------------------------------
    # Torre de Laboratorios (nivel 2): mazmorra + historial + eventos + turnos
    # ------------------------------------------------------------------
    def entrar_torre(self):
        if self.en_transicion:
            return
        self._iniciar_transicion(self._aplicar_entrar_torre, titulo="Torre de Laboratorios · 2º nivel")

    def _aplicar_entrar_torre(self, registrar=True, sala=None):
        destino = sala or self.torre["raiz"]
        if registrar:
            self._registrar("mover", f"Pasillo → {destino} (gradas)", desde=PASILLO, hacia=destino)
        self.ubicacion = "torre"
        self.sala_torre = destino
        self.sala_interior = None
        self.interior_data = None
        self.vigilante.congelado = True
        self.menu_torre = "principal"
        self.entrada_torre = ""
        self.salas_visitadas.add(destino)
        self._log("=== Torre de Laboratorios · 2º nivel ===")
        self._log("Aquí el tiempo corre por turnos: cada ronda gasta 1 minuto del reloj.")
        self._describir_sala_torre()
        self._revisar_encuentros()

    def _aplicar_salir_torre(self, registrar=True):
        sala = self.sala_torre
        if registrar:
            self._registrar("mover", f"{sala} → Pasillo (gradas)", desde=sala, hacia=PASILLO)
        self.ubicacion = "pasillo"
        self.sala_torre = None
        self.menu_torre = "principal"
        self.entrada_torre = ""
        self.jugador.x, self.jugador.y = POS_PIE_GRADAS
        self.jugador.direccion = "abajo"
        self.vigilante.congelado = False
        self._cooldown_puerta = 0.9
        self._agregar_toast("Bajaste por las gradas al campus.")

    def bajar_de_torre(self):
        """Salida de la Torre: solo desde el rellano, por las gradas."""
        if self.sala_torre != self.torre["raiz"]:
            self._log("Las gradas están en el rellano: vuelve hasta ahí para bajar.")
            return False
        self._iniciar_transicion(self._aplicar_salir_torre)
        return True

    def mover_en_torre(self, destino):
        """Mueve al jugador a una sala conectada. Valida que exista y que haya
        paso directo; si todo está bien: historial (push) + evento (popleft) +
        ronda de turnos (popleft/append)."""
        actual = self.sala_torre
        if self.ubicacion != "torre" or self.terminado:
            return False
        if not existe_sala(self.torre, destino):
            self._log(f"La sala «{destino}» no existe en la Torre.")
            return False
        if not estan_conectadas(self.torre, actual, destino):
            self._log(f"No hay paso directo de {actual} a {destino}: no están conectadas.")
            return False
        self.sala_torre = destino
        self.salas_visitadas.add(destino)
        self._log(f"Te mueves a: {destino}")
        self._registrar("mover", f"{actual} → {destino}", desde=actual, hacia=destino)
        self._procesar_evento_torre()
        if not self.terminado:
            self._jugar_ronda(f"te moviste a {destino}")
        if not self.terminado:
            self._describir_sala_torre()
        return True

    def _procesar_evento_torre(self):
        """Procesa el SIGUIENTE evento del mapa (popleft) y aplica su efecto."""
        evento = procesar_siguiente_evento(self.eventos_torre)
        self.ultimo_evento = evento
        self.evento_t = self.tiempo_animacion
        if evento is None:
            self._log("Evento: silencio total. La cola de eventos de este piso está vacía.")
            return None
        quedan = len(self.eventos_torre)
        self._log(f"Evento ({evento['tipo']}): {evento['titulo']}. {evento['texto']} "
                  f"({'queda 1 evento' if quedan == 1 else f'quedan {quedan} eventos'})")
        tipo = evento["tipo"]
        if tipo == "trampa":
            self._avanzar_minutos(evento.get("minutos", 1))
        elif tipo == "enemigo":
            origen = self.posiciones_torre[VIGILANTE]
            self.posiciones_torre[VIGILANTE] = paso_hacia(self.torre, origen, self.sala_torre)
            self._log(f"  El vigilante pasa de {origen} a {self.posiciones_torre[VIGILANTE]}.")
            self._revisar_encuentros()
        elif tipo == "camara":
            self.alerta_vigilante = max(self.alerta_vigilante, evento.get("turnos", 3))
        elif tipo == "apagon":
            self.alerta_vigilante = 0
        elif tipo == "cofre":
            ocultos = [s for s, objs in self.objetos_torre.items()
                       if objs and s not in self.tesoros_revelados and s not in self.salas_visitadas]
            if ocultos:
                sala = self.azar.choice(sorted(ocultos))
                self.tesoros_revelados.add(sala)
                self._log(f"  Pista: hay un objeto perdido en {sala}. Quedó marcado en el plano.")
            else:
                self._log("  La nota no dice nada que no sepas.")
        return evento

    def _jugar_ronda(self, accion_estudiante):
        """Una ronda completa del sistema de turnos: cada participante sale del
        frente de la cola (popleft), juega y vuelve al final (append)."""
        self.rondas_jugadas += 1
        self._encuentros_ronda = set()
        self._log(f"Ronda {self.rondas_jugadas} de turnos:")
        jugaron = []
        for _ in range(len(self.turnos)):
            actor = siguiente_turno(self.turnos)
            jugaron.append(actor)
            if actor == ESTUDIANTE:
                self._log(f"  Turno de {ESTUDIANTE}: {accion_estudiante}.")
                self._revisar_encuentros()
            elif actor == VIGILANTE:
                self._turno_vigilante()
            elif actor == ROBOT:
                self._turno_robot()
            if self.terminado:
                return jugaron
        self._avanzar_minutos(MINUTOS_POR_RONDA_TORRE)
        return jugaron

    def _turno_vigilante(self):
        origen = self.posiciones_torre[VIGILANTE]
        if self.pausa_vigilante > 0:
            self.pausa_vigilante -= 1
            self._log(f"  Turno de {VIGILANTE}: se queda en {origen} llenando un reporte.")
            return
        if self.alerta_vigilante > 0:
            destino = paso_hacia(self.torre, origen, self.sala_torre)
            self.alerta_vigilante -= 1
            verbo = "te sigue el rastro hacia"
        else:
            destino = self.azar.choice(salas_conectadas(self.torre, origen))
            verbo = "patrulla hacia"
        self.posiciones_torre[VIGILANTE] = destino
        self._log(f"  Turno de {VIGILANTE}: {verbo} {destino}.")
        self._revisar_encuentros()

    def _turno_robot(self):
        destino = self.azar.choice(salas_conectadas(self.torre, self.posiciones_torre[ROBOT]))
        self.posiciones_torre[ROBOT] = destino
        self._log(f"  Turno de {ROBOT}: trapea {destino}.")
        self._revisar_encuentros()

    def _revisar_encuentros(self):
        """¿Alguien comparte sala con el jugador?"""
        if self.terminado or self.ubicacion != "torre":
            return
        aqui = self.sala_torre
        juntos = self.posiciones_torre[ROBOT] == aqui
        if juntos and not self._robot_contigo:
            # Solo avisa cuando te encuentra; si sigue a tu lado no repite el aviso.
            self.alerta_vigilante = max(self.alerta_vigilante, TURNOS_ALERTA_ROBOT)
            self._log("  ¡BIP BIP! El robot de limpieza te detecta y avisa al vigilante por radio.")
        self._robot_contigo = juntos
        if self.posiciones_torre[VIGILANTE] == aqui and VIGILANTE not in self._encuentros_ronda:
            self._encuentros_ronda.add(VIGILANTE)
            if self.estado_mundo["toque_queda_activo"]:
                self._terminar(False, "El vigilante de la torre te encontró después del toque de queda.")
            elif self.pausa_vigilante == 0:
                self._log("  El vigilante te encuentra: «¿Qué haces aquí arriba?». "
                          f"Te sermonea {MINUTOS_SERMON} minutos y vuelve a su reporte.")
                self.alerta_vigilante = 0
                self.pausa_vigilante = TURNOS_REPORTE
                self._avanzar_minutos(MINUTOS_SERMON)

    def recoger_en_torre(self):
        """Recoge el objeto de la sala actual y lo mete al inventario (lista)."""
        sala = self.sala_torre
        suelo = self.objetos_torre.get(sala, [])
        if not suelo:
            pista = " Los objetos perdidos esperan en las salas más profundas." if sala not in self.torre["profundas"] else ""
            self._log("No hay nada que recoger en esta sala." + pista)
            return False
        nombre = suelo[-1]
        objeto = crear_objeto(nombre)
        if not self.inventario.agregar(objeto):
            self._log("Tu mochila está llena: suelta algo primero (opción 3).")
            return False
        suelo.pop()
        self._log(f"Recogiste: {objeto['titulo']}. Entra a tu inventario "
                  f"({len(self.inventario.objetos)}/{self.inventario.capacidad_maxima}).")
        self._registrar("recoger", f"{objeto['titulo']} en {sala}", objeto=nombre, zona="torre", sala=sala)
        return True

    def soltar_en_torre(self, indice):
        """Suelta el objeto `indice` de la mochila en la sala actual."""
        if not (0 <= indice < len(self.inventario.objetos)):
            self._log("Ese objeto no está en tu mochila.")
            return False
        objeto = self.inventario.soltar(self.inventario.objetos[indice]["nombre"])
        self.objetos_torre.setdefault(self.sala_torre, []).append(objeto["nombre"])
        self._log(f"Soltaste: {objeto['titulo']} en {self.sala_torre}.")
        self._registrar("soltar", f"{objeto['titulo']} en {self.sala_torre}",
                        objeto=objeto["nombre"], zona="torre", sala=self.sala_torre)
        return True

    def _describir_sala_torre(self):
        sala = self.sala_torre
        nivel = self.torre["niveles"][sala]
        self._log(f"Estás en: {sala} (nivel {nivel}). {DESCRIPCIONES.get(sala, '')}")
        conectadas = salas_conectadas(self.torre, sala)
        self._log("Salas conectadas: " + ", ".join(conectadas) +
                  (" · gradas al campus" if sala == self.torre["raiz"] else ""))
        suelo = self.objetos_torre.get(sala, [])
        if suelo:
            marca = " · sala marcada (de las más profundas)" if sala in self.torre["profundas"] else ""
            self._log(f"En el suelo: {crear_objeto(suelo[-1])['titulo']}{marca}. Opción 2 para recogerlo.")

    # -- menú de la Torre (texto + ENTER) -------------------------------
    def prompt_torre(self):
        return {
            "principal": "Opción:",
            "mover": "Elige una sala:",
            "soltar": "¿Qué objeto sueltas?:",
            "deshacer_varias": "¿Cuántas acciones deshaces?:",
        }[self.menu_torre]

    def torre_ir_a_puerta(self, numero):
        """Clic en una puerta: equivale a escribir 1 (Moverse) y su número."""
        if self.menu_torre not in ("principal", "mover"):
            self.torre_cancelar()
        if self.menu_torre == "principal":
            self.torre_enviar("1")
        self.torre_enviar(str(numero))

    def torre_accion(self, numero):
        """Clic en un botón de la barra: equivale a escribir su número."""
        if self.menu_torre != "principal":
            self.torre_cancelar()
        self.torre_enviar(str(numero))

    def torre_cancelar(self):
        if self.menu_torre != "principal":
            self.menu_torre = "principal"
            self._log("Cancelado. Vuelves al menú.")

    def torre_enviar(self, texto):
        """Procesa lo que el jugador escribió en el menú de la Torre."""
        if self.ubicacion != "torre" or self.terminado or self.en_transicion:
            return
        texto = texto.strip()
        self._log(f"> {self.prompt_torre()} {texto}")
        if self.menu_torre == "principal":
            self._opcion_principal(texto)
        elif self.menu_torre == "mover":
            self._opcion_mover(texto)
        elif self.menu_torre == "soltar":
            self._opcion_soltar(texto)
        elif self.menu_torre == "deshacer_varias":
            self._opcion_deshacer_varias(texto)

    def _opcion_principal(self, texto):
        opcion, error = leer_numero(texto, 1, len(OPCIONES_TORRE))
        if error:
            self._log(error)
            return
        if opcion == 1:
            conectadas = salas_conectadas(self.torre, self.sala_torre)
            self.opciones_submenu = [("sala", s) for s in conectadas]
            if self.sala_torre == self.torre["raiz"]:
                self.opciones_submenu.append(("gradas", "Bajar por las gradas al campus"))
            self.opciones_submenu.append(("cancelar", "Cancelar"))
            self._log("Salas conectadas: " + "   ".join(
                f"{i}) {nombre}" for i, (_, nombre) in enumerate(self.opciones_submenu, start=1)))
            self.menu_torre = "mover"
        elif opcion == 2:
            self.recoger_en_torre()
        elif opcion == 3:
            if not self.inventario.objetos:
                self._log("No tienes nada que soltar: tu mochila está vacía.")
                return
            self.opciones_submenu = [("objeto", o["titulo"]) for o in self.inventario.objetos]
            self.opciones_submenu.append(("cancelar", "Cancelar"))
            self._log("Tu mochila: " + "   ".join(
                f"{i}) {nombre}" for i, (_, nombre) in enumerate(self.opciones_submenu, start=1)))
            self.menu_torre = "soltar"
        elif opcion == 4:
            self.deshacer_accion()
        elif opcion == 5:
            disponibles = self.acciones_deshacibles_en_torre()
            if disponibles == 0:
                self._log("No hay acciones de la Torre para deshacer. "
                          "Usa la opción 4 para deshacer la subida por las gradas.")
                return
            self._log(f"Puedes deshacer de 1 a {disponibles} acciones de la Torre (ESC cancela).")
            self.menu_torre = "deshacer_varias"
        elif opcion == 6:
            self._mostrar_historial()
            self.panel_activo = "historial"
        elif opcion == 7:
            self._mostrar_turnos()
            self.panel_activo = "turnos"
        elif opcion == 8:
            self._mostrar_eventos()
            self.panel_activo = "eventos"
        elif opcion == 9:
            self._log("Inventario: " + (", ".join(o["titulo"] for o in self.inventario.objetos) or "vacío") +
                      f" ({len(self.inventario.objetos)}/{self.inventario.capacidad_maxima}).")
            self.pedir_inventario = True

    def _opcion_mover(self, texto):
        try:
            int(texto)
            es_numero = True
        except ValueError:
            es_numero = False
        if texto and not es_numero:
            # También se puede escribir el nombre de la sala.
            sala = buscar_sala(self.torre, texto)
            if sala is None:
                self._log(f"La sala «{texto}» no existe en la Torre. Elige un número de la lista.")
                return
            if self.mover_en_torre(sala):
                self.menu_torre = "principal"
            return
        opcion, error = leer_numero(texto, 1, len(self.opciones_submenu))
        if error:
            self._log(error.replace("Opción no válida", "Esa sala no existe o no está conectada"))
            return
        tipo, valor = self.opciones_submenu[opcion - 1]
        self.menu_torre = "principal"
        if tipo == "cancelar":
            self._log("Te quedas donde estás.")
        elif tipo == "gradas":
            self.bajar_de_torre()
        else:
            self.mover_en_torre(valor)

    def _opcion_soltar(self, texto):
        opcion, error = leer_numero(texto, 1, len(self.opciones_submenu))
        if error:
            self._log(error)
            return
        self.menu_torre = "principal"
        if self.opciones_submenu[opcion - 1][0] == "cancelar":
            self._log("No sueltas nada.")
            return
        self.soltar_en_torre(opcion - 1)

    def _opcion_deshacer_varias(self, texto):
        disponibles = self.acciones_deshacibles_en_torre()
        cantidad, error = leer_numero(texto, 1, max(1, disponibles))
        if error or disponibles == 0:
            self._log(error or "Ya no hay acciones de la Torre para deshacer.")
            return
        self.menu_torre = "principal"
        self.deshacer_varias(cantidad)

    def _mostrar_historial(self):
        ultima = consultar_ultima_accion(self.historial)
        self._log(f"Historial ({len(self.historial)} acciones, de la más reciente a la más antigua):")
        for linea in mostrar_historial(self.historial):
            self._log("  " + linea)
        if ultima:
            self._log(f"  Cima de la pila (lo próximo que se deshace): {ultima['texto']}")

    def _mostrar_turnos(self):
        self._log("Orden actual de la cola de turnos: " + " -> ".join(self.turnos))
        for linea in simular_turnos(list(self.turnos), 6):
            self._log("  " + linea)

    def _mostrar_eventos(self):
        if not self.eventos_torre:
            self._log("La cola de eventos está vacía: los próximos movimientos serán en silencio.")
            return
        resumen = resumen_eventos(self.eventos_torre)
        self._log(f"Eventos pendientes en la cola: {len(self.eventos_torre)} · " + ", ".join(
            f"{ETIQUETAS_TIPO[t]}: {n}" for t, n in resumen.items() if n))

    def _actualizar_transicion(self, dt):
        if self._trans_fase == TRANS_IDLE:
            return
        self._trans_t += dt
        if self._trans_fase == TRANS_FADE_OUT:
            self._trans_fade = min(1.0, self._trans_t / TRANS_HALF)
            if self._trans_t >= TRANS_HALF:
                if self._trans_accion:
                    self._trans_accion()
                    self._trans_accion = None
                self._trans_fase = TRANS_FADE_IN
                self._trans_t = 0.0
                self._trans_fade = 1.0
        elif self._trans_fase == TRANS_FADE_IN:
            self._trans_fade = max(0.0, 1.0 - self._trans_t / TRANS_HALF)
            if self._trans_t >= TRANS_HALF:
                self._trans_fade = 0.0
                if self._trans_titulo:
                    self._trans_fase = TRANS_TITLE
                    self._trans_t = 0.0
                else:
                    self._trans_fase = TRANS_IDLE
        elif self._trans_fase == TRANS_TITLE:
            if self._trans_t >= TRANS_TITLE_DUR:
                self._trans_fase = TRANS_IDLE
                self._trans_titulo = ""

    def _sala_cercana_overworld(self):
        """Sala cuya huella contiene al jugador, o la más cercana."""
        dentro = []
        for nombre, (x, y, w, h) in SALAS_RECT.items():
            if x <= self.jugador.x <= x + w and y <= self.jugador.y <= y + h:
                cx, cy = x + w / 2, y + h / 2
                dentro.append((distancia(self.jugador.pos, (cx, cy)), nombre))
        if dentro:
            dentro.sort()
            return dentro[0][1]
        mejor, mejor_d = None, 120
        for nombre, (x, y, w, h) in SALAS_RECT.items():
            cx, cy = x + w / 2, y + h / 2
            d = distancia(self.jugador.pos, (cx, cy))
            if d < mejor_d:
                mejor, mejor_d = nombre, d
        return mejor

    def _objeto_cercano(self):
        if self.ubicacion != "pasillo":
            return None
        mejor, mejor_dist = None, RADIO_INTERACCION
        for objeto in self.objetos_mundo:
            if objeto["recogido"]:
                continue
            d = distancia(self.jugador.pos, objeto["pos"])
            if d < mejor_dist:
                mejor, mejor_dist = objeto, d
        return mejor

    def _interactivo_cercano_ow(self):
        if self.ubicacion != "pasillo":
            return None
        mejor, mejor_dist = None, RADIO_INTERACCION
        for item in self.interactivos:
            d = distancia(self.jugador.pos, item["pos"])
            if d < mejor_dist:
                mejor, mejor_dist = item, d
        return mejor

    def interactuar(self):
        if self.en_transicion:
            return
        # Gradas: suben a la Torre de Laboratorios (nivel 2)
        if self.ubicacion == "pasillo" and punto_en_rect(self.jugador.x, self.jugador.y, GRADAS_TRIGGER):
            self.entrar_torre()
            return

        # Entrar por puerta (overworld)
        if self.ubicacion == "pasillo":
            pid = puerta_en(self.jugador.x, self.jugador.y, radio=36)
            if pid:
                self.entrar_interior(pid)
                return

            # Salidas del campus
            for sid, sdata in SALIDAS.items():
                if punto_en_rect(self.jugador.x, self.jugador.y, sdata["trigger"]):
                    if all(h.completada for h in self.mision.hijas):
                        self.mision.completar()
                        self._terminar(True, f"Saliste del campus ({sdata['mensaje']}).")
                    else:
                        self._agregar_toast("Todavía tienes pendientes antes de irte.")
                    return

            objeto_mundo = self._objeto_cercano()
            if objeto_mundo is not None:
                self.recoger_objeto(objeto_mundo)
                return

            interactivo = self._interactivo_cercano_ow()
            if interactivo is not None:
                if not (interactivo.get("once") and interactivo.get("usado")):
                    self._agregar_toast(interactivo["mensaje"])
                    if interactivo.get("once"):
                        interactivo["usado"] = True
                    return
            return

        # Interior
        if self.ubicacion == "interior" and self.interior_data:
            if en_zona_salida(self.interior_data, self.jugador.x, self.jugador.y):
                self.salir_interior()
                return

            item = interactivo_cercano(self.interior_data, self.jugador.x, self.jugador.y)
            if item is None:
                self._agregar_toast("Acércate a una estación marcada para interactuar.")
                return
            self.resolver_estacion(item)

    def recoger_objeto(self, objeto_mundo, alcance=RADIO_INTERACCION):
        if (self.ubicacion != "pasillo" or self.en_transicion or objeto_mundo["recogido"]
                or not any(o is objeto_mundo for o in self.objetos_mundo)
                or distancia(self.jugador.pos, objeto_mundo["pos"]) > alcance):
            return False
        objeto = crear_objeto(objeto_mundo["nombre"])
        if not self.inventario.agregar(objeto):
            self._agregar_toast("Tu mochila está llena.")
            return False
        objeto_mundo["recogido"] = True
        self._agregar_toast(f"Recogiste: {objeto['titulo']}.")
        self._registrar("recoger", f"{objeto['titulo']} en el campus",
                        objeto=objeto["nombre"], zona="campus", ref=objeto_mundo)
        return True

    def resolver_estacion(self, item, alcance=50):
        if (self.ubicacion != "interior" or self.en_transicion
                or not any(i is item for i in self.interior_interactivos)):
            return False
        if distancia(self.jugador.pos, item["pos"]) > alcance:
            self._agregar_toast(f"Acércate un poco más a la estación. Alcance de la herramienta: {alcance} px.")
            return False
        paso = item.get("paso")
        if paso is None:
            self._agregar_toast(item["mensaje"])
            return False
        mision = next(m for m in self.mision.hijas if m.ubicacion == self.sala_interior)
        if mision.completada or paso < mision.paso:
            self._agregar_toast("Esta estación ya está completada.")
            return False
        if paso != mision.paso:
            self._agregar_toast("Primero: " + mision.objetivo_actual + ".")
            return False
        requiere = item.get("requiere")
        if requiere and not self.inventario.tiene(requiere):
            lugar = "el lobby" if requiere == "libro" else "el pasillo frente a R101"
            self._agregar_toast(f"Necesitas {requiere}. Lo encontrarás en {lugar}.")
            return False
        if requiere:
            self.inventario.usar(requiere)
        item["usado"] = True
        mision.paso += 1
        if mision.paso == len(mision.pasos):
            mision.completar()
        self._agregar_toast(item["mensaje"])
        if requiere:
            self._registrar("usar", f"{crear_objeto(requiere)['titulo']} en {NOMBRES[self.sala_interior]}",
                            objeto=requiere, sala=self.sala_interior, paso=paso, estacion=item)
        return True

    def soltar_objeto(self):
        if self.ubicacion != "pasillo":
            self._agregar_toast("No puedes soltar objetos dentro de una sala.")
            return
        objeto = self.inventario.soltar_ultimo()
        if objeto is None:
            self._agregar_toast("No tienes nada que soltar.")
            return
        tirado = {
            "nombre": objeto["nombre"],
            "pos": self.jugador.pos,
            "recogido": False,
        }
        self.objetos_mundo.append(tirado)
        self._agregar_toast(f"Soltaste: {objeto['titulo']}.")
        self._registrar("soltar", f"{objeto['titulo']} en el campus",
                        objeto=objeto["nombre"], zona="campus", ref=tirado)

    def buscar_en_inventario(self, texto):
        resultados = buscar_por_nombre(self.inventario, texto)
        if resultados:
            self._agregar_toast(f"Buscador: tienes '{texto}' en el inventario.")
        else:
            self._agregar_toast(f"Buscador: no tienes '{texto}' todavía.")

    def actualizar(self, dt, teclas):
        if self.terminado:
            return

        self.tiempo_animacion += dt
        self._actualizar_transicion(dt)

        # Durante transición: freeze input / movimiento / puertas
        if self.en_transicion:
            for toast in self.toasts:
                toast.tiempo -= dt
            self.toasts = [t for t in self.toasts if t.tiempo > 0]
            return

        # La Torre va por turnos: el reloj solo avanza con cada ronda.
        if self.ubicacion == "torre":
            for toast in self.toasts:
                toast.tiempo -= dt
            self.toasts = [t for t in self.toasts if t.tiempo > 0]
            return

        if self.ubicacion == "pasillo":
            puede = self._puede_estar_pasillo
        else:
            puede = self._puede_estar_interior

        self.jugador.factor_velocidad = self.habilidad.factor_velocidad
        tiempo_reloj = self.habilidad.avanzar(dt)
        recorrido = self.jugador.intentar_mover(min(dt, 0.05), teclas, puede)
        self.jugador.distancia_recorrida += recorrido

        if self._cooldown_puerta > 0:
            self._cooldown_puerta = max(0.0, self._cooldown_puerta - dt)

        # Auto-entrar al pisar trigger de puerta (Pokémon-style)
        if self.ubicacion == "pasillo":
            if self._cooldown_puerta <= 0:
                for pid, pdata in PUERTAS.items():
                    if punto_en_rect(self.jugador.x, self.jugador.y, pdata["trigger"]):
                        self.entrar_interior(pid)
                        return

            if self._cooldown_puerta <= 0 and punto_en_rect(self.jugador.x, self.jugador.y, GRADAS_TRIGGER):
                # Las gradas suben a la Torre de Laboratorios.
                self.entrar_torre()
                return

            # Auto victoria al pisar salida con misiones OK
            for sdata in SALIDAS.values():
                if punto_en_rect(self.jugador.x, self.jugador.y, sdata["trigger"]):
                    if all(h.completada for h in self.mision.hijas):
                        self.mision.completar()
                        self._terminar(True, f"Saliste del campus ({sdata['mensaje']}).")
                        return

        elif self.ubicacion == "interior" and self.interior_data:
            if en_zona_salida(self.interior_data, self.jugador.x, self.jugador.y):
                # Auto-salir al pisar felpudo caminando hacia abajo
                if self.jugador.direccion == "abajo":
                    self.salir_interior()
                    return

        self.vigilante.actualizar(dt)

        self._tiempo_acumulado += tiempo_reloj
        while self._tiempo_acumulado >= SEGUNDOS_POR_MINUTO_JUEGO and not self.terminado:
            self._tiempo_acumulado -= SEGUNDOS_POR_MINUTO_JUEGO
            self._avanzar_minutos(1)

        for toast in self.toasts:
            toast.tiempo -= dt
        self.toasts = [t for t in self.toasts if t.tiempo > 0]

        if self.terminado:
            return
        # Vigilante solo detecta en overworld
        if self.ubicacion == "pasillo" and self.estado_mundo["toque_queda_activo"]:
            if distancia(self.jugador.pos, self.vigilante.pos) < RADIO_DETECCION:
                self._terminar(False, "Un vigilante te vio después del toque de queda.")
            elif self.estado_mundo["hora_actual_min"] >= self.hora_limite:
                self._terminar(False, "Se acabó la noche: te quedaste encerrado en el campus.")
        elif self.estado_mundo["hora_actual_min"] >= self.hora_limite:
            self._terminar(False, "Se acabó la noche: te quedaste encerrado en el campus.")

    def tesoros_en_mochila(self):
        """Objetos perdidos de la Torre que llevas en el inventario."""
        return sum(1 for o in self.inventario.objetos if es_tesoro(o["nombre"]))

    def calcular_puntaje(self):
        completadas = sum(1 for h in self.mision.hijas if h.completada)
        tesoros = self.tesoros_en_mochila()
        puntos = completadas * 100 + tesoros * PUNTOS_POR_TESORO
        if self.gano:
            minutos_restantes = max(0, self.hora_limite - self.estado_mundo["hora_actual_min"])
            puntos += minutos_restantes * 5
        return {
            "nombre": "Jugador",
            "carrera": self.jugador.carrera,
            "personaje": self.jugador.personaje,
            "puntos": puntos,
            "tesoros": tesoros,
            "resultado": "Victoria" if self.gano else "Expulsado",
            "hora_final": formatear_hora(self.estado_mundo["hora_actual_min"]),
        }


def dibujar_objetos_mundo(pantalla, objetos_mundo, jugador_pos, tiempo, camara):
    cam_x, cam_y = camara
    for objeto in objetos_mundo:
        if objeto["recogido"]:
            continue
        x, y = objeto["pos"]
        bamboleo = math.sin(tiempo * 3 + x * 0.05) * 4
        px, py = x - cam_x, y - cam_y + bamboleo
        pygame.draw.ellipse(pantalla, (8, 10, 22), (px - 12, py + 16, 24, 8))
        if distancia(jugador_pos, (x, y)) < RADIO_INTERACCION:
            pygame.draw.circle(pantalla, COLOR_ACENTO, (int(px), int(py + 4)), 24, 2)
        dibujar_arte(pantalla, obtener_arte(crear_objeto(objeto["nombre"])), (int(px), int(py)), 4)


def dibujar_interactivos(pantalla, interactivos, jugador_pos, tiempo, camara):
    for item in interactivos:
        x, y = item["pos"]
        tipo = "banco" if item["id"] == "banco_jardin" else "cartel"
        im = prop(tipo, 48, 28 if tipo == "banco" else 40)
        pantalla.blit(im, im.get_rect(midbottom=(x-camara[0], y-camara[1])))


def dibujar_jugador(pantalla, jugador, glow_linterna, camara, sprites_por_personaje, tiempo_animacion):
    px, py = int(jugador.x-camara[0]), int(jugador.y-camara[1])
    pygame.draw.ellipse(pantalla, (47,74,73), (px-14,py-5,28,10))
    paso = (1 + int(jugador.animacion_paso) % 2) if jugador.moviendo else 0
    im = sprite_estudiante(jugador.personaje, jugador.carrera, jugador.direccion, paso)
    pantalla.blit(im, im.get_rect(midbottom=(px,py)))


def dibujar_vigilante(pantalla, vigilante, activo, glow_peligro, camara):
    px, py = int(vigilante.x-camara[0]), int(vigilante.y-camara[1])
    if activo:
        pantalla.blit(glow_peligro, (px-glow_peligro.get_width()//2,py-glow_peligro.get_height()//2))
    im = sprite_personaje("vigilante", vigilante.direccion, 1+int((vigilante.x+vigilante.y)/13)%2)
    pygame.draw.ellipse(pantalla,(47,74,73),(px-14,py-5,28,10))
    pantalla.blit(im,im.get_rect(midbottom=(px,py)))
    if activo:
        texto(pantalla,"!",(px,py-72),(244,134,102),20,True)


def dibujar_transicion(pantalla, partida, fuentes):
    """Overlay de fade + tarjeta de título (después del mundo, bajo o sobre HUD)."""
    fade = partida._trans_fade
    if fade > 0.001:
        overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(fade * 255)))
        pantalla.blit(overlay, (0, 0))
    if partida._trans_fase == TRANS_TITLE and partida._trans_titulo:
        # breve title card
        t = min(1.0, partida._trans_t / 0.15)
        alpha = int(230 * (1.0 if partida._trans_t < TRANS_TITLE_DUR - 0.15 else max(0, (TRANS_TITLE_DUR - partida._trans_t) / 0.15)))
        card = pygame.Surface((ANCHO, 72), pygame.SRCALPHA)
        pygame.draw.rect(card, (12, 14, 28, alpha), (0, 0, ANCHO, 72))
        pygame.draw.line(card, (*COLOR_ACENTO, alpha), (80, 8), (ANCHO - 80, 8), 2)
        pygame.draw.line(card, (*COLOR_ACENTO, alpha), (80, 64), (ANCHO - 80, 64), 2)
        titulo = fuentes["normal"].render(partida._trans_titulo, True, COLOR_ACENTO)
        titulo.set_alpha(alpha)
        card.blit(titulo, (ANCHO // 2 - titulo.get_width() // 2, 24))
        pantalla.blit(card, (0, ALTO // 2 - 36))


# --------------------------------------------------------------------------
# HUD / menú / fin
# --------------------------------------------------------------------------
def dibujar_menu(pantalla, fuentes, puntajes, sprites_por_personaje, indice_seleccion, tiempo_menu):
    # Entrada conservada para el generador de capturas.
    PantallaInicio().dibujar(pantalla, tiempo_menu)


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
    detalle = fuentes["chica"].render(
        f"Objetos perdidos de la Torre: {puntaje['tesoros']}   ·   "
        f"Acciones en tu historial: {len(partida.historial)}   ·   "
        f"Rondas de turnos: {partida.rondas_jugadas}", True, COLOR_TEXTO)
    pantalla.blit(detalle, (ANCHO // 2 - detalle.get_width() // 2, 296))
    aviso = fuentes["normal"].render("ENTER para volver al menú", True, COLOR_TEXTO)
    pantalla.blit(aviso, (ANCHO // 2 - aviso.get_width() // 2, 340))


def manejar_entrada_torre(partida, ev):
    """Teclado y ratón del menú de la Torre: se escribe el número de la
    opción y se confirma con ENTER (o se hace clic en la opción)."""
    if ev.type == pygame.KEYDOWN:
        if ev.key == pygame.K_ESCAPE:
            if partida.menu_torre != "principal":
                partida.torre_cancelar()
            else:
                partida.panel_activo = "pausa"
        elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            texto, partida.entrada_torre = partida.entrada_torre, ""
            partida.torre_enviar(texto)
        elif ev.key == pygame.K_BACKSPACE:
            partida.entrada_torre = partida.entrada_torre[:-1]
        elif getattr(ev, "unicode", "") and ev.unicode.isprintable() and len(partida.entrada_torre) < 32:
            partida.entrada_torre += ev.unicode
    elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
        destino = objetivo_clic(partida, ev.pos)
        if destino is None:
            return
        tipo, numero = destino
        partida.entrada_torre = ""
        if tipo == "puerta":
            partida.torre_ir_a_puerta(numero)
        elif tipo == "accion":
            partida.torre_accion(numero)
        elif tipo == "submenu":
            partida.torre_enviar(str(numero))
        elif tipo == "cancelar":
            partida.torre_cancelar()


def dibujar_guias(pantalla, partida, camara, tiempo):
    """Flechas doradas sobre lo que el jugador necesita y letrero de las gradas."""
    rebote = math.sin(tiempo * 4) * 5
    necesarios = (("libro", partida.mision_libro), ("usb", partida.mision_lab))
    for nombre, mision in necesarios:
        if mision.completada or partida.inventario.tiene(nombre):
            continue
        for objeto in partida.objetos_mundo:
            if objeto["nombre"] == nombre and not objeto["recogido"]:
                x = objeto["pos"][0] - camara[0]
                y = objeto["pos"][1] - camara[1] - 44 + rebote
                pygame.draw.polygon(pantalla, (28, 43, 57), [(x - 13, y - 14), (x + 13, y - 14), (x, y + 3)])
                pygame.draw.polygon(pantalla, COLOR_ACENTO, [(x - 10, y - 12), (x + 10, y - 12), (x, y)])
                texto(pantalla, nombre.upper(), (int(x), int(y - 24)), COLOR_ACENTO, 11, True)
    gx, gy, gw, gh = GRADAS_TRIGGER
    letrero = pygame.Rect(0, 0, 96, 22)
    letrero.center = (int(gx + gw / 2 - camara[0]), int(gy + gh + 30 - camara[1]))
    pygame.draw.rect(pantalla, (28, 43, 57), letrero.inflate(4, 4))
    pygame.draw.rect(pantalla, COLOR_ACENTO, letrero)
    texto(pantalla, "TORRE 2º", (letrero.centerx + 8, letrero.centery), (28, 43, 57), 12, True)
    ay = letrero.y + 2 + rebote / 2
    pygame.draw.polygon(pantalla, (28, 43, 57),
                        [(letrero.x + 8, ay + 14), (letrero.x + 24, ay + 14), (letrero.x + 16, ay + 3)])


# --------------------------------------------------------------------------
# Bucle principal
# --------------------------------------------------------------------------
def main():
    try:
        # La narración usa tildes y flechas; en consolas viejas se reemplazan.
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    pygame.init()
    # Las fuentes nativas pertenecen a la sesión SDL; no sobreviven a pygame.quit().
    fuente.cache_clear()
    reiniciar_fuentes()
    pygame.display.set_caption("9PM — Instituto Kriete")
    ventana = crear_ventana(VENTANA_W, VENTANA_H)
    win_size = list(ventana.get_size())
    logica = crear_superficie_logica()
    fullscreen = False
    reloj = pygame.time.Clock()

    fuentes = {
        "titulo": pygame.font.SysFont("segoeui", 52, bold=True),
        "reloj": pygame.font.SysFont("consolas", 30, bold=True),
        "normal": pygame.font.SysFont("segoeui", 20),
        "chica": pygame.font.SysFont("segoeui", 15),
    }

    mapa = crear_mapa_universidad()
    glow_linterna = crear_glow(130, (255, 221, 130), alpha_max=55)
    glow_peligro = crear_glow(RADIO_DETECCION + 10, COLOR_PELIGRO, alpha_max=40)

    puntajes = ordenar_puntajes(cargar_puntajes())
    sprites_por_personaje = cargar_sprites_jugador()

    boton_inventario = BotonInventario((ANCHO - 178, 8, 160, 40))
    panel_inventario = PanelInventario(ANCHO, ALTO)

    estado_juego = MENU
    partida = None
    camara = (0, 0)
    inicio = PantallaInicio()
    tiempo_menu = 0.0
    tiempo_ui = 0.0
    tutorial = Tutorial()
    progreso_tutorial = cargar_progreso(ARCHIVO_TUTORIAL) if TUTORIAL_AUTOMATICO else {}

    def marcar_tutorial_visto(contexto):
        progreso_tutorial[contexto] = True
        if TUTORIAL_AUTOMATICO:
            guardar_progreso(ARCHIVO_TUTORIAL, progreso_tutorial)

    def empezar_partida():
        nonlocal partida, panel_inventario, estado_juego
        partida = Partida(mapa, fuentes, personaje=inicio.personaje, carrera=inicio.carrera.id,
                          eco_consola=ECO_CONSOLA)
        panel_inventario = PanelInventario(ANCHO, ALTO, partida.inventario.capacidad_maxima)
        estado_juego = JUGANDO
        tutorial.activo = False
        if TUTORIAL_AUTOMATICO and not progreso_tutorial.get("campus"):
            tutorial.iniciar("campus")

    def toggle_fullscreen():
        nonlocal ventana, fullscreen, win_size
        fullscreen = not fullscreen
        if fullscreen:
            ventana = crear_ventana(fullscreen=True)
        else:
            ventana = crear_ventana(VENTANA_W, VENTANA_H)
        win_size[:] = ventana.get_size()

    def mouse_logico():
        return ventana_a_logico(*pygame.mouse.get_pos(), win_size) or (-1, -1)

    ejecutando = True
    while ejecutando:
        dt = min(reloj.tick(FPS) / 1000.0, 0.05)
        tiempo_ui += dt
        if estado_juego == MENU:
            tiempo_menu += dt

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
                continue

            if evento.type == pygame.VIDEORESIZE and not fullscreen:
                win_size[:] = (max(320, evento.w), max(240, evento.h))
                ventana = crear_ventana(win_size[0], win_size[1])
                win_size[:] = ventana.get_size()
                continue

            # Remap mouse to logical coords for UI hit-tests
            ev = evento
            if evento.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                ev = evento_con_pos_logica(evento, win_size)
                if ev is None:
                    continue

            if estado_juego == JUGANDO:
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_F11:
                    toggle_fullscreen()
                    continue
                if tutorial.activo:
                    if tutorial.manejar_evento(ev) == "fin":
                        marcar_tutorial_visto(tutorial.contexto)
                    continue
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_F1 and not partida.en_transicion:
                    partida.panel_activo = None
                    panel_inventario.cerrar()
                    tutorial.iniciar("torre" if partida.ubicacion == "torre" else "campus")
                    continue
                en_torre = partida.ubicacion == "torre"
                if (ev.type == pygame.KEYDOWN and ev.key in (pygame.K_m, pygame.K_j, pygame.K_h)
                        and not panel_inventario.abierto and not en_torre
                        and partida.panel_activo != "pausa"):
                    panel = {pygame.K_m: "mapa", pygame.K_j: "diario", pygame.K_h: "historial"}[ev.key]
                    partida.panel_activo = None if partida.panel_activo == panel else panel
                    continue
                if partida.panel_activo:
                    if (partida.panel_activo in ("historial", "turnos", "eventos")
                            and ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER)):
                        partida.panel_activo = None
                    if partida.panel_activo == "pausa":
                        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_RETURN:
                            partida.panel_activo = None
                        elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_h:
                            estado_juego = MENU
                            inicio.vista = "inicio"
                        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                            if pygame.Rect(280,282,400,48).collidepoint(ev.pos):
                                partida.panel_activo = None
                            elif pygame.Rect(280,344,400,48).collidepoint(ev.pos):
                                estado_juego = MENU
                                inicio.vista = "inicio"
                            elif pygame.Rect(280,406,400,48).collidepoint(ev.pos):
                                ejecutando = False
                    if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                        partida.panel_activo = None
                    continue
                if (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1
                        and boton_inventario.contiene(ev.pos)):
                    panel_inventario.alternar()
                    continue
                if en_torre:
                    # En la Torre el teclado escribe en el menú: número + ENTER.
                    if panel_inventario.abierto:
                        panel_inventario.manejar_evento(ev)
                    elif not partida.en_transicion:
                        manejar_entrada_torre(partida, ev)
                        if partida.pedir_inventario:
                            partida.pedir_inventario = False
                            panel_inventario.alternar()
                    continue
                if panel_inventario.manejar_evento(ev):
                    continue

            if estado_juego == MENU:
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_F11:
                    toggle_fullscreen()
                    continue
                accion = inicio.manejar_evento(ev)
                if accion == "jugar":
                    empezar_partida()
                elif accion == "salir":
                    ejecutando = False
                continue

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    if estado_juego == JUGANDO:
                        partida.panel_activo = "pausa"
                    else:
                        estado_juego = MENU
                        inicio.vista = "inicio"
                elif ev.key == pygame.K_F11:
                    toggle_fullscreen()
                elif estado_juego == JUGANDO and ev.key == pygame.K_q:
                    partida.habilidad.usar(partida)
                elif estado_juego == JUGANDO and ev.key == pygame.K_SPACE:
                    if partida and not partida.en_transicion:
                        partida.interactuar()
                elif estado_juego == JUGANDO and ev.key == pygame.K_g:
                    if partida and not partida.en_transicion:
                        partida.soltar_objeto()
                elif estado_juego == JUGANDO and ev.key == pygame.K_z:
                    if partida and not partida.en_transicion:
                        partida.deshacer_accion()
                elif estado_juego == JUGANDO and ev.key == pygame.K_f:
                    if partida and not partida.en_transicion:
                        partida.buscar_en_inventario("libro")
                elif estado_juego == FIN and ev.key == pygame.K_RETURN:
                    estado_juego = MENU
                    inicio.vista = "inicio"

        if estado_juego == JUGANDO:
            pos_mouse = mouse_logico()
            boton_inventario.actualizar(pos_mouse)
            panel_inventario.actualizar(dt, pos_mouse)
            if not panel_inventario.abierto and not partida.panel_activo and not tutorial.activo:
                partida.actualizar(dt, pygame.key.get_pressed())
            if (TUTORIAL_AUTOMATICO and partida.ubicacion == "torre" and not partida.en_transicion
                    and not tutorial.activo and not progreso_tutorial.get("torre") and not partida.terminado):
                tutorial.iniciar("torre")
            mw, mh = partida.mundo_actual_size()
            camara = calcular_camara(partida.jugador.pos, mw, mh)
            if partida.terminado:
                puntajes = guardar_puntaje(partida.calcular_puntaje(), puntajes)
                panel_inventario.cerrar()
                estado_juego = FIN

        # --- Dibujar todo a superficie lógica ---
        pantalla = logica
        if estado_juego == MENU:
            inicio.dibujar(pantalla, tiempo_menu, mouse_logico())
        elif estado_juego == JUGANDO:
            if partida.ubicacion == "torre":
                dibujar_torre(pantalla, partida, partida.tiempo_animacion)
            elif partida.ubicacion == "interior" and partida.interior_data:
                pantalla.fill((18, 20, 26))
                dibujar_interior(pantalla, partida.interior_data, camara, fuentes["chica"])
                dibujar_interactivos_interior(
                    pantalla, partida.interior_data, partida.jugador.pos,
                    partida.tiempo_animacion, camara,
                )
                dibujar_jugador(
                    pantalla, partida.jugador, glow_linterna, camara,
                    sprites_por_personaje, partida.tiempo_animacion,
                )
            else:
                dibujar_overworld(pantalla, camara, fuentes["chica"])
                dibujar_objetos_mundo(
                    pantalla, partida.objetos_mundo, partida.jugador.pos,
                    partida.tiempo_animacion, camara,
                )
                dibujar_guias(pantalla, partida, camara, tiempo_ui)
                dibujar_interactivos(
                    pantalla, partida.interactivos, partida.jugador.pos,
                    partida.tiempo_animacion, camara,
                )
                dibujar_vigilante(
                    pantalla, partida.vigilante,
                    partida.estado_mundo["toque_queda_activo"], glow_peligro, camara,
                )
                dibujar_jugador(
                    pantalla, partida.jugador, glow_linterna, camara,
                    sprites_por_personaje, partida.tiempo_animacion,
                )

            if partida.ubicacion != "torre":
                dibujar_efecto_habilidad(pantalla, partida, camara)
            dibujar_transicion(pantalla, partida, fuentes)
            if partida.ubicacion != "torre":
                dibujar_hud(pantalla, partida, fuentes)
            panel_inventario.dibujar(pantalla, partida.inventario)
            boton_inventario.dibujar(
                pantalla,
                len(partida.inventario.objetos),
                partida.inventario.capacidad_maxima,
                panel_inventario.abierto,
            )
            if partida.panel_activo == "mapa":
                dibujar_mapa(pantalla, partida)
            elif partida.panel_activo == "diario":
                dibujar_diario(pantalla, partida)
            elif partida.panel_activo == "historial":
                dibujar_panel_historial(pantalla, partida)
            elif partida.panel_activo == "turnos":
                dibujar_panel_turnos(pantalla, partida)
            elif partida.panel_activo == "eventos":
                dibujar_panel_eventos(pantalla, partida)
            elif partida.panel_activo == "pausa":
                dibujar_pausa(pantalla, partida)
            tutorial.dibujar(pantalla, partida, camara, tiempo_ui)
        elif estado_juego == FIN:
            dibujar_fin(pantalla, fuentes, partida)

        presentar(ventana, logica, win_size)

    # Las fuentes cacheadas mueren con la sesión SDL: se descartan antes de cerrarla.
    fuente.cache_clear()
    reiniciar_fuentes()
    pygame.quit()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        if sys.stdout is None:
            # Abierto con pythonw (acceso directo): no hay consola, el error queda en un archivo.
            import traceback
            (Path(__file__).parent / "error_9pm.log").write_text(traceback.format_exc(), encoding="utf-8")
        raise
