"""Música y efectos de 9PM, sintetizados en el momento (sin archivos de audio).

Todo se genera con ondas cuadradas, triangulares y ruido, como un chip de
consola vieja. Si no hay tarjeta de sonido o el mezclador falla, el juego
sigue en silencio: ninguna función de este módulo lanza excepciones.
"""

import math
import os
import random
import threading
from array import array

import pygame

FRECUENCIA = 22050
VOLUMEN_MUSICA = 0.45
VOLUMEN_EFECTOS = 0.7


def _hz(nota):
    """Número MIDI -> frecuencia en Hz (69 = La 440)."""
    return 440.0 * 2 ** ((nota - 69) / 12)


def _onda(forma, fase):
    fase %= 1.0
    if forma == "cuadrada":
        return 1.0 if fase < 0.5 else -1.0
    if forma == "pulso":
        return 1.0 if fase < 0.25 else -1.0
    if forma == "triangular":
        return 4 * fase - 1 if fase < 0.5 else 3 - 4 * fase
    return math.sin(2 * math.pi * fase)


def _pista(notas, duracion_nota, forma, volumen, total):
    """Secuencia de notas MIDI (None = silencio) como lista de floats."""
    muestras = [0.0] * total
    paso = int(duracion_nota * FRECUENCIA)
    for i, nota in enumerate(notas):
        if nota is None:
            continue
        inicio = i * paso
        f = _hz(nota) / FRECUENCIA
        largo = min(paso, total - inicio)
        for j in range(largo):
            envolvente = 1.0 - (j / paso) * 0.7          # decae un poco cada nota
            if j > paso - 120:
                envolvente *= (paso - j) / 120           # sin clics al cortar
            muestras[inicio + j] += _onda(forma, j * f) * volumen * envolvente
    return muestras


def _bateria(golpes, duracion_nota, volumen, total, semilla=7):
    """Golpes de ruido corto (hi-hat / caja) en las posiciones marcadas con 1."""
    azar = random.Random(semilla)
    muestras = [0.0] * total
    paso = int(duracion_nota * FRECUENCIA)
    largo = int(0.04 * FRECUENCIA)
    for i, g in enumerate(golpes):
        if not g:
            continue
        inicio = i * paso
        for j in range(min(largo, total - inicio)):
            muestras[inicio + j] += azar.uniform(-1, 1) * volumen * g * (1 - j / largo)
    return muestras


def _mezclar(*pistas):
    total = max(len(p) for p in pistas)
    return [sum(p[i] for p in pistas if i < len(p)) for i in range(total)]


class Sonido:
    def __init__(self, activo=True):
        self.disponible = False
        self.silencio = not activo
        self.canales = 1
        self.sonidos = {}
        self.musica_actual = None
        self._canal_musica = None
        self._listo = threading.Event()
        if os.environ.get("SDL_AUDIODRIVER") == "dummy":
            return            # sin audio real (pruebas / servidores): ni se sintetiza
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(FRECUENCIA, -16, 1, 512)
            frecuencia, _, canales = pygame.mixer.get_init()
            self.canales = canales
            self.disponible = frecuencia > 0
        except (pygame.error, TypeError):
            self.disponible = False
        if self.disponible:
            threading.Thread(target=self._generar, daemon=True).start()

    # ------------------------------------------------------------------
    # Generación (en un hilo para no congelar el arranque)
    # ------------------------------------------------------------------
    def _sonido(self, muestras):
        datos = array("h")
        for m in muestras:
            v = int(max(-1.0, min(1.0, m)) * 30000)
            datos.extend([v] * self.canales)
        return pygame.mixer.Sound(buffer=datos.tobytes())

    def _generar(self):
        try:
            self.sonidos["logro"] = self._sonido(_mezclar(
                _pista([72, 76, 79, 84, None, 84], 0.09, "cuadrada", 0.35, int(0.62 * FRECUENCIA)),
                _pista([60, None, 67, 72], 0.135, "triangular", 0.3, int(0.62 * FRECUENCIA))))
            self.sonidos["golpe_super"] = self._sonido(
                _pista([76, 83, 88], 0.05, "cuadrada", 0.4, int(0.16 * FRECUENCIA)))
            self.sonidos["golpe"] = self._sonido(
                _pista([69, 72], 0.06, "cuadrada", 0.35, int(0.13 * FRECUENCIA)))
            self.sonidos["golpe_debil"] = self._sonido(
                _pista([64, 58, 52], 0.07, "pulso", 0.4, int(0.22 * FRECUENCIA)))
            self.sonidos["victoria"] = self._sonido(
                _pista([67, 72, 76, 79, 76, 79, 84], 0.11, "cuadrada", 0.35, int(0.8 * FRECUENCIA)))
            self.sonidos["derrota"] = self._sonido(
                _pista([67, 63, 60, 55], 0.2, "triangular", 0.45, int(0.85 * FRECUENCIA)))
            self.sonidos["alarma"] = self._sonido(
                _pista([81, 76, 81, 76, 81, 76], 0.14, "pulso", 0.3, int(0.85 * FRECUENCIA)))
            self.sonidos["batalla"] = self._musica_batalla()
            self.sonidos["campus"] = self._musica_campus(tempo=84, tension=False)
            self.sonidos["toque"] = self._musica_campus(tempo=132, tension=True)
        except Exception:      # si algo falla, el juego sigue sin sonido
            self.disponible = False
        finally:
            self._listo.set()

    def _musica_batalla(self):
        corchea = 60 / 168 / 2
        bajo = []
        for raiz in (45, 43, 41, 40):              # La - Sol - Fa - Mi
            bajo += [raiz, raiz, raiz + 12, raiz] * 2
        melodia = [69, 72, 76, 81, 79, 76, 74, 76,
                   77, 76, 72, 69, 71, 72, 71, 67,
                   65, 69, 72, 77, 76, 72, 69, 72,
                   68, 71, 76, 80, 83, 80, 76, 71]
        total = int(corchea * 32 * FRECUENCIA)
        return self._sonido(_mezclar(
            _pista(bajo, corchea, "triangular", 0.38, total),
            _pista(melodia, corchea, "pulso", 0.16, total),
            _bateria([1, 0, 0.6, 0] * 8, corchea, 0.12, total)))

    def _musica_campus(self, tempo, tension):
        corchea = 60 / tempo / 2
        acordes = ((57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62))   # Lam Fa Do Sol
        arpegio, bajo = [], []
        for a in acordes:
            arpegio += [a[0] + 12, a[1] + 12, a[2] + 12, a[1] + 12] * 2
            bajo += [a[0] - 12, None, None, None, a[0] - 12, None, None, None]
        total = int(corchea * 32 * FRECUENCIA)
        pistas = [_pista(arpegio, corchea, "triangular", 0.17, total),
                  _pista(bajo, corchea, "triangular", 0.3, total)]
        if tension:
            pistas.append(_bateria([1, 0.4] * 16, corchea, 0.08, total))
            pistas.append(_pista([a[0] + 24 if i % 4 == 0 else None
                                  for a in acordes for i in range(8)], corchea, "pulso", 0.07, total))
        return self._sonido(_mezclar(*pistas))

    # ------------------------------------------------------------------
    # Reproducción
    # ------------------------------------------------------------------
    def efecto(self, nombre):
        if self.silencio or not self.disponible or nombre not in self.sonidos:
            return
        try:
            canal = self.sonidos[nombre].play()
            if canal:
                canal.set_volume(VOLUMEN_EFECTOS)
        except pygame.error:
            pass

    def musica(self, nombre):
        """Cambia la música en bucle (None la detiene). No repite si ya suena."""
        if nombre == self.musica_actual and (self._canal_musica is None or self._canal_musica.get_busy()):
            return
        if not self.disponible or nombre not in self.sonidos and nombre is not None:
            self.musica_actual = nombre
            return
        try:
            if self._canal_musica is not None:
                self._canal_musica.fadeout(250)
            self.musica_actual = nombre
            self._canal_musica = None
            if nombre is not None and not self.silencio:
                self._canal_musica = self.sonidos[nombre].play(loops=-1, fade_ms=300)
                if self._canal_musica:
                    self._canal_musica.set_volume(VOLUMEN_MUSICA)
        except pygame.error:
            self._canal_musica = None

    def alternar_silencio(self):
        self.silencio = not self.silencio
        actual = self.musica_actual
        if self.silencio:
            try:
                pygame.mixer.stop()
            except pygame.error:
                pass
            self._canal_musica = None
        else:
            self.musica_actual = None
            self.musica(actual)
        return self.silencio


class SinSonido:
    """Reemplazo mudo para pruebas o cuando no se quiere audio."""
    disponible = False
    silencio = True
    musica_actual = None

    def efecto(self, nombre):
        pass

    def musica(self, nombre):
        self.musica_actual = nombre

    def alternar_silencio(self):
        return True
