"""Carreras KEY y habilidades de juego, independientes del avatar elegido."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Carrera:
    id: str
    nombre: str
    corto: str
    lineas: tuple[str, ...]
    color: tuple[int, int, int]
    herramienta: str
    habilidad: str
    descripcion: str
    recarga: float
    duracion: float = 0

CARRERAS = (
    Carrera('computacion', 'Ingeniería y Ciencias de la Computación Integradas',
        'Computación', ('Ingeniería y Ciencias', 'de la Computación', 'Integradas'),
        (42, 220, 131), 'Terminal portátil', 'Acceso remoto',
        'Completa la siguiente estación digital a hasta 180 px en R101, R103, R105 o Click.', 24),
    Carrera('industrial', 'Ingeniería Industrial y Manufactura Avanzada',
        'Industrial', ('Ingeniería Industrial', 'y Manufactura', 'Avanzada'),
        (239, 239, 40), 'Planificador de rutas', 'Ruta óptima',
        'Muévete un 45% más rápido durante 12 s. Funciona en pasillos e interiores.', 30, 12),
    Carrera('mecatronica', 'Ingeniería Mecatrónica y Robótica',
        'Mecatrónica', ('Ingeniería', 'Mecatrónica', 'y Robótica'),
        (154, 77, 255), 'Microbot auxiliar', 'Asistente robótico',
        'Recoge un objeto a 220 px o activa una estación mecánica compatible a 160 px.', 22),
    Carrera('quimica', 'Ingeniería Química y Procesos Digitales',
        'Química', ('Ingeniería Química', 'y Procesos', 'Digitales'),
        (255, 135, 38), 'Kit de análisis', 'Concentración',
        'El reloj avanza a la mitad durante 12 s. El movimiento mantiene su velocidad.', 30, 12),
)
POR_ID = {c.id: c for c in CARRERAS}

# Son afinidades de diseño de juego; no asignaciones oficiales de laboratorios.
ESTACIONES_DIGITALES = {('r101', 1), ('r103', 1), ('r105', 0), ('lab_click', 0), ('lab_click', 1)}
ESTACIONES_MECANICAS = {('lab_siemens', 1), ('lab_spark', 1), ('lab_kite', 0)}

def obtener_carrera(clave):
    return POR_ID.get(clave, CARRERAS[0])
