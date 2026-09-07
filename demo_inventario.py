"""Checkpoint 1: evidencia de ejecucion del inventario (agregar, usar y soltar).

Corre este script de forma independiente (sin abrir la ventana del juego) para
demostrar que `Inventario` (inventario.py) funciona con una LISTA de Python:
agregar objetos, usarlos (consumirlos) y soltarlos, respetando la capacidad
maxima de la mochila y los casos limite (mochila llena / objeto que no esta).

    cd 9PM
    python demo_inventario.py
"""

from inventario import Inventario
from ui_inventario import crear_objeto


def separador(titulo):
    print(f"\n--- {titulo} ---")


def main():
    inventario = Inventario(capacidad_maxima=3)

    separador("1. Inventario vacio")
    print("Objetos:", inventario.nombres())

    separador("2. AGREGAR objetos (recoger) -> list.append()")
    for nombre in ["libro", "usb", "cafe"]:
        agregado = inventario.agregar(crear_objeto(nombre))
        print(f"agregar('{nombre}'): {'OK' if agregado else 'RECHAZADO (mochila llena)'}")
    print("Objetos actuales:", inventario.nombres())

    separador("3. Caso limite: AGREGAR con la mochila llena")
    agregado = inventario.agregar(crear_objeto("llaves"))
    print("agregar('llaves') con mochila llena:", "OK" if agregado else "RECHAZADO")
    print("esta_lleno():", inventario.esta_lleno())

    separador("4. Consultar antes de USAR -> tiene()")
    print("tiene('libro'):", inventario.tiene("libro"))
    print("tiene('llaves'):", inventario.tiene("llaves"))

    separador("5. USAR un objeto (se consume: sale de la lista) -> list.remove()")
    usado = inventario.usar("libro")
    print("usar('libro') devolvio:", usado["titulo"] if usado else None)
    print("Objetos despues de usar:", inventario.nombres())

    separador("6. SOLTAR un objeto (se tira: sale de la lista) -> list.remove()")
    soltado = inventario.soltar("usb")
    print("soltar('usb') devolvio:", soltado["titulo"] if soltado else None)
    print("Objetos despues de soltar:", inventario.nombres())

    separador("7. Casos limite: USAR y SOLTAR algo que ya no esta")
    print("usar('libro'):", inventario.usar("libro"))
    print("soltar('usb'):", inventario.soltar("usb"))

    separador("8. Ahora hay espacio: AGREGAR las llaves que antes se rechazaron")
    agregado = inventario.agregar(crear_objeto("llaves"))
    print("agregar('llaves'):", "OK" if agregado else "RECHAZADO")
    print("Objetos finales:", inventario.nombres())


if __name__ == "__main__":
    main()
