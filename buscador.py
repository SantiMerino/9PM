"""Semana 11: búsqueda de objetos dentro del inventario del jugador."""


def buscar_por_nombre(inventario, texto):
    """Búsqueda lineal: filtra objetos cuyo nombre contiene 'texto'."""
    texto = texto.lower()
    return [o for o in inventario.objetos if texto in o["nombre"].lower()]


def busqueda_binaria_por_nombre(objetos_ordenados, nombre):
    """Búsqueda binaria; requiere que la lista venga ordenada alfabéticamente."""
    bajo, alto = 0, len(objetos_ordenados) - 1
    while bajo <= alto:
        medio = (bajo + alto) // 2
        actual = objetos_ordenados[medio]["nombre"]
        if actual == nombre:
            return objetos_ordenados[medio]
        if actual < nombre:
            bajo = medio + 1
        else:
            alto = medio - 1
    return None
