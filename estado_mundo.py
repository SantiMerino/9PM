"""Semana 15: diccionario con el estado global del mundo (la noche del juego)."""


def crear_estado_inicial():
    return {
        "hora_actual_min": 20 * 60 + 15,   # 20:15
        "hora_toque_queda_min": 21 * 60,   # 21:00
        "toque_queda_activo": False,
        "luces_encendidas": {
            "biblioteca": True,
            "cafeteria": True,
            "laboratorio": True,
            "auditorio": True,
        },
        "vigilante_alerta": False,
    }


def avanzar_tiempo(estado, minutos):
    estado["hora_actual_min"] += minutos
    if estado["hora_actual_min"] >= estado["hora_toque_queda_min"]:
        estado["toque_queda_activo"] = True


def formatear_hora(minutos_desde_medianoche):
    h = (minutos_desde_medianoche // 60) % 24
    m = minutos_desde_medianoche % 60
    return f"{h:02d}:{m:02d}"
