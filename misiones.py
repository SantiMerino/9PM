"""Misiones del campus: árbol y progreso ordenado por estaciones físicas.

Cada misión tiene UN solo padre (``padre``) y una lista de hijas (``hijas``),
así que el conjunto de misiones es un árbol y no un grafo: no hay ciclos y
cada encargo depende de un único encargo anterior.
"""


class Mision:
    def __init__(self, titulo, descripcion, ubicacion=None, pasos=(),
                 recompensa=0, efecto=None, es_raiz=False):
        self.titulo = titulo
        self.descripcion = descripcion
        self.ubicacion = ubicacion      # id de la sala donde se hace el encargo
        self.es_raiz = es_raiz          # la raíz es un contenedor, no un encargo
        self.completada = False
        self.hijas = []
        self.padre = None               # un solo padre -> es árbol, no grafo
        self.pasos = tuple(pasos)
        self.paso = 0
        self.recompensa = recompensa    # puntos al completarla
        self.efecto = efecto            # dict para el estado del mundo o None

    def __repr__(self):
        return f"Mision({self.titulo!r}, {self.ubicacion!r})"

    # La raíz contenedora no se completa a mano: está completada solo cuando
    # todas sus descendientes lo están. Las demás guardan su propio valor.
    @property
    def completada(self):
        if self.es_raiz:
            return all(h.todas_completas() for h in self.hijas)
        return self._completada

    @completada.setter
    def completada(self, valor):
        self._completada = bool(valor)

    def agregar_submision(self, mision):
        """Cuelga `mision` debajo de esta y le asigna su padre. O(h).

        Devuelve la misión agregada, o None si no se pudo: si no es una
        Mision, si ya tiene padre (tendría dos y dejaría de ser árbol) o si
        es esta misma o una de sus ancestras (formaría un ciclo).
        """
        if not isinstance(mision, Mision) or mision.padre is not None:
            return None
        ancestra = self
        while ancestra is not None:
            if ancestra is mision:
                return None
            ancestra = ancestra.padre
        mision.padre = self
        self.hijas.append(mision)
        return mision

    def desbloqueada(self):
        """True si se puede hacer ya: no tiene padre, su padre es la raíz o
        su padre está completada. El juego lo revisa antes de dejar avanzar
        un paso de la estación. O(1)."""
        padre = self.padre
        return (padre is None or padre.es_raiz or padre.padre is None
                or padre.completada)

    def nivel(self):
        """0 para la raíz, 1 para sus hijas, etc. Sube por los padres. O(h)."""
        nivel, actual = 0, self.padre
        while actual is not None:
            nivel, actual = nivel + 1, actual.padre
        return nivel

    def completar(self): self.completada = True

    def todas_completas(self):
        return self.completada and all(h.todas_completas() for h in self.hijas)

    def pendientes(self):
        return ([] if self.completada else [self]) + [p for h in self.hijas for p in h.pendientes()]

    @property
    def objetivo_actual(self):
        return 'Completada' if self.completada else self.pasos[self.paso] if self.pasos else self.descripcion


# Orden de los primeros tres conservado para las referencias de Partida.
ENCARGOS = [
    ('biblioteca','Préstamo de medianoche',('Devolver el libro del lobby en el mostrador',)),
    ('lab_siemens','Puesta en marcha',('Revisar el extintor junto a la entrada','Activar el panel PLC de la mesa 1','Imprimir el informe con la USB de R101')),
    ('sala_reuniones','Una última firma',('Hablar con el profesor junto a su escritorio',)),
    ('r101','Entrega digital',('Consultar la guía en la pizarra','Validar el archivo en el PC')),
    ('r102','Cálculo pendiente',('Leer el ejercicio de la pizarra','Entregar la solución en el escritorio')),
    ('r103','Redes conectadas',('Revisar el esquema de red','Probar la conexión en el PC')),
    ('r104','Bitácora de física',('Leer la medición en el osciloscopio','Registrar el resultado en el escritorio')),
    ('r105','Última exposición',('Revisar la presentación en el PC','Entregar las notas en el escritorio')),
    ('lab_click','Respaldo completo',('Revisar el servidor','Confirmar el respaldo en el PC')),
    ('lab_spark','Señal estable',('Leer la señal del osciloscopio','Calibrar el módulo de control')),
    ('lab_kite','Prototipo listo',('Inspeccionar el brazo del prototipo','Validar el diseño en el PC')),
    ('cafeteria','Cierre de caja',('Revisar la cafetera','Registrar el cierre en el mostrador')),
    ('bodega','Todo en su lugar',('Revisar la caja de componentes','Registrar el inventario en el PC')),
]
def crear_mision_principal():
    m=Mision('Salir del campus','Completa los encargos del primer nivel y sal por el lobby o la terraza.','lobby')
    for sala,titulo,pasos in ENCARGOS:
        m.agregar_submision(Mision(titulo,' · '.join(pasos),sala,pasos))
    return m


# ---------------------------------------------------------------------------
# Árbol de misiones del juego (Checkpoint 3)
# ---------------------------------------------------------------------------
#
# Salir del campus (lobby)  [raíz]
# └── Préstamo de medianoche (biblioteca)
#     ├── Una última firma (sala_reuniones)
#     │   ├── Cálculo pendiente (r102)
#     │   └── Última exposición (r105)
#     │       └── Bitácora de física (r104)
#     ├── Entrega digital (r101)
#     │   ├── Puesta en marcha (lab_siemens)
#     │   │   └── Prototipo listo (lab_kite)
#     │   └── Redes conectadas (r103)
#     │       └── Respaldo completo (lab_click)
#     └── Cierre de caja (cafeteria)
#         └── Todo en su lugar (bodega)
#             └── Señal estable (lab_spark)
#
# Las dependencias salen del juego: con el libro de la biblioteca arranca la
# noche, la USB de R101 se usa en el Lab Siemens, el profesor firma antes de
# las entregas de aulas y la cafetería se cierra antes de ordenar la bodega.

# (sala del encargo, sala del encargo del que depende). None = cuelga de la
# raíz. Van en preorden para que cada padre exista antes que sus hijas.
DEPENDENCIAS = [
    ('biblioteca', None),
    ('sala_reuniones', 'biblioteca'),
    ('r102', 'sala_reuniones'),
    ('r105', 'sala_reuniones'),
    ('r104', 'r105'),
    ('r101', 'biblioteca'),
    ('lab_siemens', 'r101'),
    ('lab_kite', 'lab_siemens'),
    ('r103', 'r101'),
    ('lab_click', 'r103'),
    ('cafeteria', 'biblioteca'),
    ('bodega', 'cafeteria'),
    ('lab_spark', 'bodega'),
]

# Efecto en el diccionario del mundo al completar el encargo. Las tuplas de
# puertas van ordenadas alfabéticamente (contrato con estado_mundo.py).
EFECTOS = {
    'biblioteca': {'apaga': 'biblioteca'},
    'cafeteria': {'abre': ('terraza', 'terraza_n')},
}

# Recompensa = 10 puntos por nivel: nivel 1 = 10, nivel 2 = 20, ... nivel 4 = 40.
# Los encargos más profundos valen más porque exigen completar toda su rama antes.
RECOMPENSA_POR_NIVEL = 10


def crear_arbol_misiones_juego():
    """Arma el árbol de misiones con dependencias a partir de ENCARGOS.

    Usa los mismos 13 encargos (títulos, salas y pasos) y los cuelga según
    DEPENDENCIAS debajo de una raíz contenedora «Salir del campus». Cada
    llamada crea objetos nuevos, así cada partida tiene su propio árbol.
    Queda con 4 niveles debajo de la raíz. O(n).
    """
    raiz = Mision('Salir del campus',
                  'Completa los encargos del primer nivel y sal por el lobby o la terraza.',
                  'lobby', es_raiz=True)
    datos = {sala: (titulo, pasos) for sala, titulo, pasos in ENCARGOS}
    por_sala = {}
    for sala, sala_padre in DEPENDENCIAS:
        titulo, pasos = datos[sala]
        efecto = EFECTOS.get(sala)
        mision = Mision(titulo, ' · '.join(pasos), sala, pasos,
                        efecto=dict(efecto) if efecto else None)
        padre = raiz if sala_padre is None else por_sala[sala_padre]
        padre.agregar_submision(mision)
        mision.recompensa = RECOMPENSA_POR_NIVEL * mision.nivel()
        por_sala[sala] = mision
    return raiz
