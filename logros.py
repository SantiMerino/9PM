"""Logros (insignias) de la noche.

Cada logro se gana una sola vez por partida: se guarda en un diccionario
clave -> logro (consulta O(1) para no repetirlo) y además se encola para que
la pantalla lo muestre uno por uno.
"""

LOGROS = {
    "primer_encargo": {"titulo": "Primer paso", "texto": "Completaste tu primer encargo de la noche.",
                       "icono": "estrella", "puntos": 25},
    "rama_completa": {"titulo": "Rama completa", "texto": "Terminaste toda una rama del árbol de misiones.",
                      "icono": "arbol", "puntos": 75},
    "todos_encargos": {"titulo": "Noctámbulo", "texto": "Los 13 encargos listos antes de irte.",
                       "icono": "luna", "puntos": 150},
    "labia_de_oro": {"titulo": "Labia de oro", "texto": "Convenciste al vigilante en una discusión.",
                     "icono": "burbuja", "puntos": 50},
    "impecable": {"titulo": "Cara de póker", "texto": "Le ganaste al vigilante sin perder credibilidad.",
                  "icono": "mascara", "puntos": 100},
    "escapista": {"titulo": "Escapista", "texto": "Saliste corriendo de una discusión... y funcionó.",
                  "icono": "rayo", "puntos": 30},
    "terraza": {"titulo": "Salida secreta", "texto": "Escapaste del campus por la terraza.",
                "icono": "llave", "puntos": 60},
}

COLORES_ICONO = {
    "estrella": (241, 199, 116), "arbol": (104, 196, 128), "luna": (176, 168, 238),
    "burbuja": (110, 165, 184), "mascara": (226, 124, 172), "rayo": (249, 228, 82),
    "llave": (233, 167, 92), "encargo": (241, 199, 116),
}


class RegistroLogros:
    def __init__(self):
        self.obtenidos = {}     # clave -> logro
        self.cola = []          # logros por mostrar en pantalla

    def otorgar(self, clave, titulo=None, texto=None, puntos=None, icono=None):
        """Otorga el logro si no lo tenías. Devuelve el logro o None. O(1)."""
        if clave in self.obtenidos:
            return None
        base = dict(LOGROS.get(clave, {"titulo": clave, "texto": "", "icono": "encargo", "puntos": 0}))
        if titulo is not None:
            base["titulo"] = titulo
        if texto is not None:
            base["texto"] = texto
        if puntos is not None:
            base["puntos"] = puntos
        if icono is not None:
            base["icono"] = icono
        base["clave"] = clave
        self.obtenidos[clave] = base
        self.cola.append(dict(base, t=0.0))
        return base

    def insignia_encargo(self, mision):
        """Insignia por completar un encargo (no suma puntos: ya cuentan en recompensa_rama)."""
        return self.otorgar(f"encargo:{mision.ubicacion}", titulo=mision.titulo,
                            texto=f"Encargo completado · +{mision.recompensa} pts de recompensa",
                            puntos=0, icono="encargo")

    def tiene(self, clave):
        return clave in self.obtenidos

    def puntos(self):
        return sum(l["puntos"] for l in self.obtenidos.values())

    def especiales(self):
        """Logros que no son insignias de encargo, en el orden en que se ganaron."""
        return [l for c, l in self.obtenidos.items() if not c.startswith("encargo:")]

    def actualizar(self, dt, duracion=3.4):
        """Avanza el logro que se está mostrando y lo saca al terminar."""
        if self.cola:
            self.cola[0]["t"] += dt
            if self.cola[0]["t"] >= duracion:
                self.cola.pop(0)

    @property
    def mostrando(self):
        return self.cola[0] if self.cola else None
