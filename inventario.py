"""Semana 3: lista de objetos que el jugador va recogiendo por el campus."""


class Inventario:
    def __init__(self, capacidad_maxima=6):
        self.objetos = []
        self.capacidad_maxima = capacidad_maxima

    def agregar(self, objeto):
        if len(self.objetos) >= self.capacidad_maxima:
            return False
        self.objetos.append(objeto)
        return True

    def quitar(self, nombre_objeto):
        for objeto in self.objetos:
            if objeto["nombre"] == nombre_objeto:
                self.objetos.remove(objeto)
                return objeto
        return None

    def tiene(self, nombre_objeto):
        return any(o["nombre"] == nombre_objeto for o in self.objetos)

    def esta_lleno(self):
        return len(self.objetos) >= self.capacidad_maxima
