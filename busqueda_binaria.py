def busqueda_binaria(lista_ordenada, objetivo):
    """Busca un objetivo en una lista ordenada, revisando la mitad cada vez."""
    inicio = 0
    fin = len(lista_ordenada) - 1
    iteracion = 0
    while inicio <= fin:
        iteracion += 1
        medio = (inicio + fin) // 2
        if lista_ordenada[medio] == objetivo:
            return medio, iteracion
        elif lista_ordenada[medio] < objetivo:
            inicio = medio + 1
        else:
            fin = medio - 1
    return None, iteracion


# --- Programa principal ---
lista = [3, 7, 12, 18, 25, 33, 41, 50, 58, 67, 75, 84, 91, 99]
posicion, pasos = busqueda_binaria(lista, 58)
print("Posición: " + str(posicion) + ", pasos: " + str(pasos))