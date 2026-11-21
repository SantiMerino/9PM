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
