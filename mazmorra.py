"""Semana 7: generación recursiva de las salas de un edificio del campus
(por ejemplo, la Torre de Ingeniería con sus pisos y aulas)."""

import random


def generar_piso(nivel, max_niveles, prefijo="Aula"):
    """Genera recursivamente la lista de pisos y aulas de un edificio."""
    if nivel > max_niveles:
        return []
    aulas_en_este_piso = [f"{prefijo} {nivel}-{n}" for n in range(1, random.randint(2, 4))]
    piso_actual = {"piso": nivel, "aulas": aulas_en_este_piso}
    return [piso_actual] + generar_piso(nivel + 1, max_niveles, prefijo)


def generar_edificio(nombre_edificio, max_niveles=4):
    return {"nombre": nombre_edificio, "pisos": generar_piso(1, max_niveles)}
