"""Checkpoint 2: partida guionada que genera la evidencia de ejecución.

Juega una partida real de 9PM sin abrir ventana: usa la misma clase Partida y
los mismos métodos que llaman el teclado y el ratón (`torre_enviar` recibe lo
que el jugador escribiría en el menú de la Torre). Al terminar guarda:

    docs/evidencia_checkpoint2.txt    texto de la consola de la partida
    docs/capturas/cp2_*.png           capturas reales de Pygame

    .venv\\Scripts\\python.exe evidencia_checkpoint2.py

No modifica puntajes.json. La semilla fija hace que la Torre y el orden de
los eventos sean siempre los mismos, para que la evidencia sea reproducible.
"""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
from collections import defaultdict
from pathlib import Path

import pygame

pygame.init()
pygame.display.set_mode((960, 640))

import main
from mazmorra import camino_desde_raiz

SEMILLA = 1
CARPETA = Path(__file__).parent / 'docs'
CAPTURAS = CARPETA / 'capturas'
SIN_TECLAS = defaultdict(bool)

fuentes = {k: pygame.font.SysFont('consolas', n)
           for k, n in [('titulo', 52), ('reloj', 30), ('normal', 20), ('chica', 15)]}
pantalla = pygame.Surface((960, 640))
boton = main.BotonInventario((main.ANCHO - 178, 8, 160, 40))


def terminar_transicion(p):
    while p.en_transicion:
        p.actualizar(.3, SIN_TECLAS)


def capturar(p, nombre, panel=None):
    """Dibuja la pantalla igual que el bucle principal y la guarda."""
    if p.ubicacion == 'torre':
        main.dibujar_torre(pantalla, p, 0.0, (-1, -1))
    else:
        camara = main.calcular_camara(p.jugador.pos, *p.mundo_actual_size())
        main.dibujar_overworld(pantalla, camara, fuentes['chica'])
        main.dibujar_objetos_mundo(pantalla, p.objetos_mundo, p.jugador.pos, 0, camara)
        main.dibujar_interactivos(pantalla, p.interactivos, p.jugador.pos, 0, camara)
        main.dibujar_vigilante(pantalla, p.vigilante, False, main.crear_glow(85, (224, 76, 76), 40), camara)
        main.dibujar_jugador(pantalla, p.jugador, None, camara, {}, 0)
        main.dibujar_hud(pantalla, p, fuentes)
    boton.dibujar(pantalla, len(p.inventario.objetos), p.inventario.capacidad_maxima, False)
    if panel:
        panel(pantalla, p)
    pygame.image.save(pantalla, CAPTURAS / f'cp2_{nombre}.png')


def escribir(p, *textos):
    """Lo que el jugador escribe en el menú de la Torre, seguido de ENTER."""
    for texto in textos:
        p.torre_enviar(texto)


def numero_de(p, sala):
    """Número que tiene `sala` en el submenú "Moverse" que está abierto."""
    return str(next(i for i, (_, nombre) in enumerate(p.opciones_submenu, 1) if nombre == sala))


def ir_a(p, sala):
    escribir(p, '1')
    escribir(p, numero_de(p, sala))


def main_evidencia():
    CAPTURAS.mkdir(parents=True, exist_ok=True)
    p = main.Partida(main.crear_mapa_universidad(), fuentes, semilla=SEMILLA, eco_consola=True)
    torre = p.torre

    # Caso límite: deshacer con el historial vacío (tecla Z en el campus).
    p.deshacer_accion()

    # Campus: recoger el libro del lobby (acción "recoger" en la pila).
    libro = next(o for o in p.objetos_mundo if o['nombre'] == 'libro')
    p.jugador.x, p.jugador.y = libro['pos']
    p.interactuar()

    # Subir por las gradas: entra a la Torre (acción "mover" en la pila).
    p.jugador.x, p.jugador.y = (924, 704)
    p.actualizar(.016, SIN_TECLAS)
    terminar_transicion(p)
    capturar(p, '01_torre_generada')

    # Casos límite del menú principal: texto, 0, negativo, fuera de rango.
    escribir(p, 'abc', '0', '-1', '12')
    capturar(p, '02_opciones_invalidas')

    # Tres movimientos hacia una de las salas marcadas (las más profundas).
    objetivo = torre['profundas'][0]
    camino = camino_desde_raiz(torre['raiz'], objetivo, torre['hijos'])
    ir_a(p, camino[1])
    # Casos límite del submenú: sala que no existe y sala no conectada.
    escribir(p, '1', 'Sótano secreto', '-3', '9', objetivo)
    escribir(p, numero_de(p, camino[2]))
    capturar(p, '03_movimiento_evento_turnos')
    ir_a(p, camino[3])

    # Deshacer: vuelve de verdad a la sala anterior.
    escribir(p, '4')
    capturar(p, '04_deshacer_vuelve')
    ir_a(p, camino[3])

    # Sala marcada: el objeto perdido entra al inventario del Checkpoint 1.
    escribir(p, '2')
    capturar(p, '05_recoger_objeto')

    # Historial, turnos y eventos en pantalla.
    escribir(p, '6')
    capturar(p, '06_historial', main.dibujar_panel_historial)
    p.panel_activo = None
    escribir(p, '7')
    capturar(p, '07_turnos', main.dibujar_panel_turnos)
    p.panel_activo = None
    escribir(p, '8')
    capturar(p, '08_eventos', main.dibujar_panel_eventos)
    p.panel_activo = None

    # Ir y volver hasta vaciar la cola de eventos (caso límite: cola vacía).
    while p.eventos_torre and not p.terminado:
        ir_a(p, camino[2])
        if p.eventos_torre and not p.terminado:
            ir_a(p, camino[3])
    if not p.terminado:
        ir_a(p, camino[2])
        escribir(p, '8')
        capturar(p, '09_cola_vacia', main.dibujar_panel_eventos)
        p.panel_activo = None

    # Deshacer varias (Guía 5: deshacer_multiples) y volver al rellano.
    if not p.terminado:
        escribir(p, '5', '2')
        while p.sala_torre != torre['raiz'] and not p.terminado:
            ir_a(p, torre['padres'][p.sala_torre])
    # Bajar por las gradas al campus y abrir el historial con H.
    if not p.terminado:
        escribir(p, '1')
        escribir(p, numero_de(p, 'Bajar por las gradas al campus'))
        terminar_transicion(p)
        p.panel_activo = 'historial'
        p._mostrar_historial()
        capturar(p, '10_campus_historial', main.dibujar_panel_historial)

    texto = '\n'.join(p.consola) + '\n'
    (CARPETA / 'evidencia_checkpoint2.txt').write_text(texto, encoding='utf-8')
    print(f'\nEvidencia guardada en {CARPETA / "evidencia_checkpoint2.txt"} y {CAPTURAS}')


if __name__ == '__main__':
    main.imprimir_seguro('=== Evidencia Checkpoint 2 (partida guionada, semilla %d) ===' % SEMILLA)
    main_evidencia()
    pygame.quit()
