"""Misiones del campus: árbol y progreso ordenado por estaciones físicas."""
class Mision:
    def __init__(self,titulo,descripcion,ubicacion=None,pasos=()):
        self.titulo=titulo
        self.descripcion=descripcion
        self.ubicacion=ubicacion
        self.completada=False
        self.hijas=[]
        self.pasos=tuple(pasos)
        self.paso=0
    def agregar_submision(self,mision): self.hijas.append(mision)
    def completar(self): self.completada=True
    def todas_completas(self): return self.completada and all(h.todas_completas() for h in self.hijas)
    def pendientes(self):
        return ([] if self.completada else [self])+[p for h in self.hijas for p in h.pendientes()]
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
