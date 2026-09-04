"""Checkpoint 1: evidencia de ejecucion del inventario (agregar, usar y soltar).

Corre este script de forma independiente (sin abrir la ventana del juego) para
demostrar que `Inventario` (inventario.py) funciona con listas: agregar
objetos, consultarlos, "usarlos" (comprobar que se tienen) y soltarlos,
respetando la capacidad maxima de la mochila.
"""

from inventario import Inventario
from ui_inventario import crear_objeto


def separador(titulo):
    print(f"\n--- {titulo} ---")


def main():
    inventario = Inventario(capacidad_maxima=3)

    separador("1. Inventario vacio")
    print("Objetos:", [o["nombre"] for o in inventario.objetos])

    separador("2. Agregar objetos (recoger)")
    for nombre in ["libro", "carne_estudiantil", "usb"]:
        objeto = crear_objeto(nombre)
        agregado = inventario.agregar(objeto)
        print(f"Agregar '{nombre}': {'OK' if agregado else 'RECHAZADO (inventario lleno)'}")
    print("Objetos actuales:", [o["nombre"] for o in inventario.objetos])

    separador("3. Inventario lleno: intentar agregar un cuarto objeto")
    objeto_extra = crear_objeto("linterna")
    agregado = inventario.agregar(objeto_extra)
    print(f"Agregar 'linterna' con inventario lleno: {'OK' if agregado else 'RECHAZADO'}")
    print("esta_lleno():", inventario.esta_lleno())

    separador("4. Consultar si se tiene un objeto (usar)")
    print("tiene('libro'):", inventario.tiene("libro"))
    print("tiene('linterna'):", inventario.tiene("linterna"))

    separador("5. Soltar (quitar) un objeto")
    quitado = inventario.quitar("libro")
    print("Se solto:", quitado["titulo"] if quitado else None)
    print("Objetos despues de soltar:", [o["nombre"] for o in inventario.objetos])

    separador("6. Intentar soltar un objeto que ya no se tiene")
    quitado = inventario.quitar("libro")
    print("Resultado:", quitado)

    separador("7. Ahora hay espacio: agregar la linterna que antes fue rechazada")
    agregado = inventario.agregar(objeto_extra)
    print(f"Agregar 'linterna': {'OK' if agregado else 'RECHAZADO'}")
    print("Objetos finales:", [o["nombre"] for o in inventario.objetos])


if __name__ == "__main__":
    main()
