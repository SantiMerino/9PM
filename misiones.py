"""Semana 14: árbol de misiones. La misión principal ("salir antes del
toque de queda") tiene sub-misiones que hay que resolver por el campus."""


class Mision:
    def __init__(self, titulo, descripcion, ubicacion=None):
        self.titulo = titulo
        self.descripcion = descripcion
        self.ubicacion = ubicacion
        self.completada = False
        self.hijas = []

    def agregar_submision(self, mision):
        self.hijas.append(mision)

    def completar(self):
        self.completada = True

    def todas_completas(self):
        return self.completada and all(h.todas_completas() for h in self.hijas)

    def pendientes(self):
        propias = [] if self.completada else [self]
        for hija in self.hijas:
            propias += hija.pendientes()
        return propias


def crear_mision_principal():
    principal = Mision(
        "Salir antes del toque de queda",
        "Resuelve tus pendientes y llega al parqueadero antes de las 9PM.",
        ubicacion="parqueadero",
    )
    principal.agregar_submision(Mision(
        "Devolver el libro", "Recoge el libro en la entrada y entrégalo en la biblioteca.",
        ubicacion="biblioteca",
    ))
    principal.agregar_submision(Mision(
        "Imprimir el trabajo", "Imprime tu tarea en el laboratorio.",
        ubicacion="laboratorio",
    ))
    principal.agregar_submision(Mision(
        "Hablar con el profesor", "Entrega tu excusa en la oficina del profesor.",
        ubicacion="oficina_profesor",
    ))
    return principal
