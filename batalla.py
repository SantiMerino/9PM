"""Batalla de argumentos contra el vigilante (Torre, 2º nivel).

Cuando el vigilante te encuentra en la Torre no te saca de una: te acorrala
con preguntas y tú respondes con excusas. Funciona como un combate por turnos:

- El vigilante tiene SOSPECHA (su "vida"): cada excusa convincente la baja.
- Tú tienes CREDIBILIDAD: cada excusa floja la gasta.
- Cada acusación tiene un tipo y cada excusa también. Igual que en un juego de
  tipos, algunas excusas son súper convincentes contra cierta acusación y
  otras no sirven para nada (tabla EFECTIVIDAD).
- Repetir la misma excusa seguida rinde la mitad: "eso ya me lo dijiste".
- Si llevas un objeto que sirva de prueba (tarjeta, bata, libro...) puedes
  mostrarlo una vez por batalla.

Este módulo no usa pygame: es pura lógica y se prueba sin ventana.
"""

import random

from dificultad import obtener_dificultad

CREDIBILIDAD_MAX = 100
DANO_BASE = 26
PROBABILIDAD_CRITICO = 0.1

# ----------------------------------------------------------------------
# Acusaciones del vigilante
# ----------------------------------------------------------------------
ACUSACIONES = (
    {"texto": "¿Y vos qué hacés aquí arriba a esta hora?", "tipo": "horario", "fuerza": 14},
    {"texto": "Los labs cierran a las 8:30, ¿no sabías?", "tipo": "horario", "fuerza": 15},
    {"texto": "Esta zona es solo para personal autorizado.", "tipo": "zona", "fuerza": 16},
    {"texto": "Pero aquí no deberías estar, viejito.", "tipo": "zona", "fuerza": 14},
    {"texto": "Mmm... ¿y esa mochila tan llena?", "tipo": "sospecha", "fuerza": 13},
    {"texto": "Te vi en las cámaras corriendo por el pasillo.", "tipo": "sospecha", "fuerza": 17},
    {"texto": "¿Y quién te dio permiso de subir?", "tipo": "permiso", "fuerza": 16},
    {"texto": "A ver, enseñame tu carné.", "tipo": "permiso", "fuerza": 15},
)
ACUSACIONES_TOQUE_QUEDA = (
    {"texto": "¡Ya son más de las 9! ¿Qué excusa tenés ahora?", "tipo": "horario", "fuerza": 22},
    {"texto": "Con el campus cerrado, esto ya es reporte.", "tipo": "permiso", "fuerza": 21},
)

# ----------------------------------------------------------------------
# Excusas del estudiante
# ----------------------------------------------------------------------
EXCUSAS = {
    "estudiando": {
        "nombre": "Estoy estudiando",
        "tipo": "academico",
        "frases": ("Es que mañana tengo parcial de Cálculo.",
                   "Estoy repasando, aquí arriba nadie hace ruido.",
                   "Me falta un capítulo nada más, se lo juro."),
    },
    "profe": {
        "nombre": "Un profe me llamó",
        "tipo": "autoridad",
        "frases": ("El ingeniero me pidió que le trajera unas cosas.",
                   "Es que un profesor me llamó, pregúntele.",
                   "La coordinadora me mandó a revisar algo."),
    },
    "ya_me_voy": {
        "nombre": "Ya me iba...",
        "tipo": "calma",
        "frases": ("Tranquilo, ya me iba. Solo recojo mis cosas.",
                   "Cinco minutos y desaparezco, en serio.",
                   "Ya, ya, ya voy saliendo."),
    },
}
EXCUSAS_CARRERA = {
    "computacion": ("Reinicio el servidor", ("Si no reinicio el servidor se cae el Wi-Fi de todo KEY.",
                                             "Estoy corriendo un respaldo, no lo puedo dejar a medias.")),
    "industrial": ("Auditoría de inventario", ("Me tocó contar el inventario del laboratorio.",
                                               "Estoy optimizando la ruta de limpieza, en serio.")),
    "mecatronica": ("El robot se trabó", ("El robot de limpieza se trabó y lo estoy reprogramando.",
                                          "Si no calibro este brazo, mañana no hay práctica.")),
    "quimica": ("Reacción en curso", ("Tengo una reacción corriendo, si la dejo explota... bueno, no explota.",
                                      "Estoy esperando que termine la destilación.")),
}
# Objetos del inventario que sirven de prueba (el primero que tengas se muestra).
EVIDENCIAS = {
    "tarjeta": "Le muestras tu tarjeta de acceso del laboratorio.",
    "bata": "Te pones la bata de laboratorio con toda la seriedad del mundo.",
    "libro": "Le enseñas el libro con la ficha de préstamo.",
    "calculadora": "Le enseñas la calculadora con la tarea a medias.",
    "disco_duro": "Le muestras el disco duro: «son los respaldos del lab».",
    "usb": "Le enseñas la USB con la entrega del proyecto.",
}

# Multiplicador según tipo de acusación -> tipo de excusa.
EFECTIVIDAD = {
    "horario":  {"academico": 0.5, "autoridad": 1.0, "calma": 2.0, "tecnico": 2.0, "evidencia": 1.0},
    "zona":     {"academico": 1.0, "autoridad": 1.0, "calma": 0.5, "tecnico": 2.0, "evidencia": 2.0},
    "sospecha": {"academico": 2.0, "autoridad": 0.5, "calma": 1.0, "tecnico": 1.0, "evidencia": 2.0},
    "permiso":  {"academico": 0.5, "autoridad": 2.0, "calma": 0.5, "tecnico": 1.0, "evidencia": 2.0},
}
REACCIONES = {
    "super": ("Mmm... eso tiene sentido.", "Ah, bueno... no sabía.", "Está bien, está bien..."),
    "normal": ("Ajá... sigue.", "No sé si creerte.", "Hmm."),
    "debil": ("¡No te creo nada!", "¿Me ves cara de qué?", "Esa excusa ya la escuché mil veces."),
}


class Batalla:
    """Estado de una batalla de argumentos.

    Flujo: hay una cola de mensajes (como los textos de un combate por turnos).
    `continuar()` avanza al siguiente; cuando se vacía toca elegir una excusa
    con `elegir(indice)`. Al terminar, `resultado` es "ganaste", "perdiste" o
    "huiste" y `terminada` es True.
    """

    def __init__(self, carrera="computacion", inventario=(), dificultad="normal",
                 toque_queda=False, sala="la Torre", semilla=None):
        self.azar = random.Random(semilla)
        self.config = obtener_dificultad(dificultad)
        self.carrera = carrera if carrera in EXCUSAS_CARRERA else "computacion"
        self.inventario = list(inventario)
        self.toque_queda = toque_queda
        self.sospecha_max = self.config["sospecha"] + (30 if toque_queda else 0)
        self.sospecha = self.sospecha_max
        self.credibilidad = CREDIBILIDAD_MAX
        self.intentos_huir = 0
        self.evidencia_usada = False
        self.ultima_excusa = None
        self.acusacion = None
        self.resultado = None
        self.turno = 0
        self.mensajes = []
        self.fase = "mensajes"          # "mensajes" | "elegir" | "fin"
        self.golpes = []                # ("vigilante" | "jugador", efecto) para la UI
        self.dano_recibido = 0
        pool = list(ACUSACIONES) + (list(ACUSACIONES_TOQUE_QUEDA) if toque_queda else [])
        self._pool = pool
        self._decir(f"¡El vigilante te encontró en {sala}!")
        if toque_queda:
            self._decir("Ya pasó el toque de queda: si pierdes, te saca del campus.")
        self._nueva_acusacion()

    # ------------------------------------------------------------------
    # Mensajes
    # ------------------------------------------------------------------
    def _decir(self, texto):
        self.mensajes.append(texto)

    @property
    def mensaje_actual(self):
        return self.mensajes[0] if self.mensajes else ""

    @property
    def terminada(self):
        return self.fase == "fin"

    def continuar(self):
        """Pasa al siguiente mensaje. Devuelve True si cambió algo."""
        if self.fase != "mensajes":
            return False
        if self.mensajes:
            self.mensajes.pop(0)
        if not self.mensajes:
            self.fase = "fin" if self.resultado else "elegir"
        return True

    # ------------------------------------------------------------------
    # Opciones del jugador
    # ------------------------------------------------------------------
    def _evidencia_disponible(self):
        return next((nombre for nombre in EVIDENCIAS if nombre in self.inventario), None)

    def opciones(self):
        """Las 5 opciones: 4 excusas (menú 2x2) y, al final, salir corriendo.
        Cada una es (clave, nombre, tipo, disponible). La cuarta excusa es la
        prueba si llevas un objeto que sirva y no la usaste; si no, "Ya me iba"."""
        evidencia = self._evidencia_disponible()
        if evidencia and not self.evidencia_usada:
            comodin = ("evidencia", "Mostrar prueba", "evidencia", True)
        else:
            comodin = ("ya_me_voy", EXCUSAS["ya_me_voy"]["nombre"], "calma", True)
        return [
            ("estudiando", EXCUSAS["estudiando"]["nombre"], "academico", True),
            ("profe", EXCUSAS["profe"]["nombre"], "autoridad", True),
            ("carrera", EXCUSAS_CARRERA[self.carrera][0], "tecnico", True),
            comodin,
            ("huir", "Salir corriendo", "huir", True),
        ]

    def efectividad(self, tipo_excusa):
        """Multiplicador de la excusa contra la acusación actual (1.0 si no aplica)."""
        if not self.acusacion:
            return 1.0
        return EFECTIVIDAD.get(self.acusacion["tipo"], {}).get(tipo_excusa, 1.0)

    def elegir(self, indice):
        """Responde con la opción `indice` (0..n-1). Ignora índices inválidos."""
        if self.fase != "elegir":
            return False
        opciones = self.opciones()
        try:
            indice = int(indice)
        except (TypeError, ValueError):
            return False
        if not 0 <= indice < len(opciones):
            return False
        clave, nombre, tipo, disponible = opciones[indice]
        if not disponible:
            return False
        self.fase = "mensajes"
        self.turno += 1
        if clave == "huir":
            self._huir()
        else:
            self._excusa(clave, tipo)
        if not self.mensajes:
            self.fase = "fin" if self.resultado else "elegir"
        return True

    # ------------------------------------------------------------------
    # Turnos
    # ------------------------------------------------------------------
    def _frase(self, clave):
        if clave == "carrera":
            return self.azar.choice(EXCUSAS_CARRERA[self.carrera][1])
        if clave == "evidencia":
            return EVIDENCIAS[self._evidencia_disponible()]
        return self.azar.choice(EXCUSAS[clave]["frases"])

    def _excusa(self, clave, tipo):
        frase = self._frase(clave)
        if clave == "evidencia":
            self.evidencia_usada = True
            self._decir(frase)
        else:
            self._decir(f"TÚ: «{frase}»")
        multiplicador = self.efectividad(tipo)
        repetida = clave == self.ultima_excusa
        self.ultima_excusa = clave
        dano = DANO_BASE * multiplicador * self.azar.uniform(0.85, 1.0)
        if repetida:
            dano *= 0.5
            self._decir("VIGILANTE: «Eso ya me lo dijiste...»")
        critico = self.azar.random() < PROBABILIDAD_CRITICO and not repetida
        if critico:
            dano *= 1.5
        dano = max(1, round(dano))
        self.sospecha = max(0, self.sospecha - dano)
        efecto = "super" if multiplicador > 1 else ("debil" if multiplicador < 1 else "normal")
        self.golpes.append(("vigilante", efecto))
        if critico:
            self._decir("¡Argumento demoledor!")
        if efecto == "super":
            self._decir("¡Súper convincente!")
        elif efecto == "debil":
            self._decir("No suena muy creíble...")
        if self.sospecha == 0:
            self._ganar()
            return
        self._contraataque(efecto)

    def _contraataque(self, efecto):
        fuerza = self.acusacion["fuerza"]
        factor = {"super": 0.5, "normal": 1.0, "debil": 1.6}[efecto]
        dano = max(1, round(fuerza * factor * self.config["dano"] * self.azar.uniform(0.9, 1.1)))
        self.credibilidad = max(0, self.credibilidad - dano)
        self.dano_recibido += dano
        self.golpes.append(("jugador", efecto))
        self._decir(f"VIGILANTE: «{self.azar.choice(REACCIONES[efecto])}»")
        if self.credibilidad == 0:
            self._perder()
            return
        self._nueva_acusacion()

    def _huir(self):
        self.intentos_huir += 1
        probabilidad = min(0.95, self.config["huir"] + 0.1 * (self.intentos_huir - 1))
        if self.azar.random() < probabilidad:
            self._decir("Sales corriendo por la puerta más cercana...")
            self._decir("VIGILANTE: «¡Vení para acá!» Te va a seguir el rastro.")
            self.resultado = "huiste"
            return
        self._decir("Intentas escapar, pero te cierra el paso.")
        if self.acusacion is None:
            self._nueva_acusacion()
        self._contraataque("debil")

    def _nueva_acusacion(self):
        opciones = [a for a in self._pool if a is not self.acusacion] or self._pool
        self.acusacion = self.azar.choice(opciones)
        self._decir(f"VIGILANTE: «{self.acusacion['texto']}»")

    def _ganar(self):
        self._decir("VIGILANTE: «Bueno... está bien. Pero rapidito, ¿eh?»")
        self._decir("Ganaste la discusión. El vigilante vuelve a su reporte.")
        self.resultado = "ganaste"

    def _perder(self):
        self._decir("Te quedaste sin argumentos...")
        if self.toque_queda:
            self._decir("VIGILANTE: «Se acabó. Para afuera, viejito.»")
        else:
            self._decir("VIGILANTE: «Siéntate, que te voy a dar un sermón.»")
        self.resultado = "perdiste"

    @property
    def impecable(self):
        """True si ganaste sin perder credibilidad."""
        return self.resultado == "ganaste" and self.dano_recibido == 0
