"""Personajes originales de pixel art con cuatro direcciones y pasos alternos."""
from arte_pixel import personaje
from carreras import obtener_carrera
PERSONAJES=('universitario','universitaria')

def sprite_estudiante(avatar, carrera, direccion='abajo', paso=0, escala=2):
    perfil=obtener_carrera(carrera)
    return personaje(avatar,direccion,paso,escala,perfil.color,perfil.id)
def cargar_sprites_jugador():
    return {k:{'frames':[personaje(k,'abajo',i) for i in range(3)],
        'retrato':personaje(k,'abajo',0,6),
        'etiqueta':k.capitalize(),
        'descripcion':'Mochila lista. Una noche más.' if k=='universitario' else 'Un último recorrido por el campus.'}
        for k in PERSONAJES}
def frame_idle(frames,tiempo_animacion,fps=3):
    return frames[0] if frames else None
