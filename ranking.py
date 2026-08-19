"""Semana 9: ordenamiento de los puntajes de las partidas jugadas."""


def ordenar_puntajes(puntajes, clave="puntos", descendente=True):
    """Ordena una lista de dicts {'nombre':, 'puntos':, 'resultado':, 'hora_final':}."""
    return sorted(puntajes, key=lambda p: p[clave], reverse=descendente)


def mejor_puntaje(puntajes):
    ordenados = ordenar_puntajes(puntajes)
    return ordenados[0] if ordenados else None
