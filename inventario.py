"""Semana 3: inventario del jugador implementado con una LISTA de Python.

`self.objetos` es una lista (`[]`); cada objeto es un diccionario con su
nombre, icono, titulo, rareza y descripcion (lo arma `ui_inventario.crear_objeto`).

Las tres operaciones que pide el Checkpoint 1 son metodos sobre esa lista:

    agregar(objeto)   -> recoger: list.append(), respetando la capacidad
    usar(nombre)      -> usar/consumir: busca en la lista y hace list.remove()
    soltar(nombre)    -> soltar/tirar: busca en la lista y hace list.remove()

`usar` y `soltar` hacen lo mismo con la lista (sacar el objeto), pero el juego
las trata distinto: al "usar" el libro en la biblioteca se completa una mision;
al "soltar" un objeto vuelve a aparecer tirado en el mapa para recogerlo luego.
"""


class Inventario:
    def __init__(self, capacidad_maxima=6):
        self.objetos = []                      # <-- la lista de la Semana 3
        self.capacidad_maxima = capacidad_maxima

    # ------------------------------------------------------------------
    # AGREGAR (recoger un objeto y meterlo a la lista)
    # ------------------------------------------------------------------
    def agregar(self, objeto):
        """Mete `objeto` al final de la lista. Devuelve False si la mochila
        ya esta llena (no se agrega nada)."""
        if len(self.objetos) >= self.capacidad_maxima:
            return False
        self.objetos.append(objeto)
        return True

    # ------------------------------------------------------------------
    # USAR (consumir un objeto: sale de la lista y produce un efecto)
    # ------------------------------------------------------------------
    def usar(self, nombre_objeto):
        """Busca el objeto por nombre, lo saca de la lista con list.remove()
        y lo devuelve para que quien llama aplique su efecto. Devuelve None
        si el objeto no esta en la mochila."""
        for objeto in self.objetos:
            if objeto["nombre"] == nombre_objeto:
                self.objetos.remove(objeto)
                return objeto
        return None

    # ------------------------------------------------------------------
    # SOLTAR (tirar un objeto: sale de la lista y queda en el mapa)
    # ------------------------------------------------------------------
    def soltar(self, nombre_objeto):
        """Igual que `usar` a nivel de lista (list.remove()), pero la intencion
        es tirar el objeto, no consumirlo. Devuelve el objeto soltado o None."""
        for objeto in self.objetos:
            if objeto["nombre"] == nombre_objeto:
                self.objetos.remove(objeto)
                return objeto
        return None

    def soltar_ultimo(self):
        """Suelta el ultimo objeto que se recogio (list.pop()). Devuelve None
        si la mochila esta vacia. Lo usa la tecla G del juego."""
        if not self.objetos:
            return None
        return self.objetos.pop()

    # Alias historico: en el codigo viejo se llamaba `quitar`.
    quitar = soltar

    # ------------------------------------------------------------------
    # Consultas sobre la lista
    # ------------------------------------------------------------------
    def tiene(self, nombre_objeto):
        """True si algun objeto de la lista se llama `nombre_objeto`."""
        return any(o["nombre"] == nombre_objeto for o in self.objetos)

    def esta_lleno(self):
        return len(self.objetos) >= self.capacidad_maxima

    def nombres(self):
        """Lista simple de nombres, util para imprimir o depurar."""
        return [o["nombre"] for o in self.objetos]
