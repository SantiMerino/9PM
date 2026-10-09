"""Semana 7 / Guía 7: la Torre de Laboratorios (2º nivel) generada con RECURSIVIDAD.

Las gradas del campus suben a un segundo nivel cuyos tabiques móviles se
reacomodan cada noche, así que su distribución se genera al iniciar la
partida. Es un árbol: desde el rellano salen pasillos, de cada pasillo salen
salas y algunas salas esconden un cuarto interior.

    Rellano del segundo nivel          nivel 0 (sala principal)
    ├── Pasillo de Vidrio              nivel 1
    │   ├── Sala de Servidores         nivel 2
    │   │   └── Jaula de Racks         nivel 3  <- sala más profunda: tesoro
    │   └── Aula R201                  nivel 2
    └── ...

`generar_salas` sigue el mismo patrón de `generar_salas` de la Guía 7 (lista
de salas + lista de conexiones), con nombres propios en vez de "1.1.2" y con
las adaptaciones de la guía:

    - ramificación variable (Reto D)
    - conteo de salas por nivel (Ejercicio A)
    - marcado de las salas más profundas con un tesoro (Ejercicio B)
    - profundidad real alcanzada (Ejercicio C y reto final)
"""

import random
import unicodedata

NOMBRE_RAIZ = "Rellano del segundo nivel"
PROFUNDIDAD_MAXIMA = 3

NOMBRES_POR_NIVEL = {
    1: ("Pasillo de Vidrio", "Ala de Robótica", "Corredor de Posgrado",
        "Galería de Proyectos", "Pasillo de Servicio"),
    2: ("Laboratorio de Óptica", "Sala de Servidores", "Taller de Impresión 3D",
        "Aula R201", "Aula R202", "Sala de Tutorías", "Archivo de Tesis",
        "Laboratorio de Química Analítica", "Sala de Simulación",
        "Oficina de Coordinación", "Estudio de Grabación", "Laboratorio de Energía"),
    3: ("Cuarto Eléctrico", "Bodega de Reactivos", "Jaula de Racks", "Cuarto Oscuro",
        "Bóveda de Prototipos", "Cabina de Control", "Depósito de Baterías",
        "Closet del Conserje", "Cámara Anecoica"),
}

# (mínimo, máximo) de salas hijas según la profundidad. Con 2-3 pasillos y 2
# salas por pasillo hay siempre al menos 1 + 2 + 4 = 7 salas y profundidad 2;
# el nivel 2 puede tener o no un cuarto interior (0 o 1), así que la
# profundidad real alcanzada puede quedar en 2 o llegar a 3.
RAMIFICACION = {0: (2, 3), 1: (2, 2), 2: (0, 1)}

DESCRIPCIONES = {
    NOMBRE_RAIZ: "Un directorio iluminado muestra el plano del piso. Abajo, las gradas al campus.",
    "Pasillo de Vidrio": "Paredes de vidrio esmerilado; se ve el jardín central de noche.",
    "Ala de Robótica": "Brazos robóticos en reposo, con los LEDs en ámbar.",
    "Corredor de Posgrado": "Afiches de tesis y un dispensador de agua que gotea.",
    "Galería de Proyectos": "Maquetas de la última feria cubiertas con plástico.",
    "Pasillo de Servicio": "Carritos de limpieza y una puerta que dice SOLO PERSONAL.",
    "Laboratorio de Óptica": "Láseres apagados y mesas con aislamiento de vibración.",
    "Sala de Servidores": "Zumbido constante y aire helado. Huele a polvo caliente.",
    "Taller de Impresión 3D": "Tres impresoras siguen trabajando solas.",
    "Aula R201": "Pupitres en filas y una pizarra a medio borrar.",
    "Aula R202": "Alguien dejó la presentación proyectada en la pared.",
    "Sala de Tutorías": "Mesas redondas y un reloj que va dos minutos adelantado.",
    "Archivo de Tesis": "Estantes con tesis empastadas desde 2009.",
    "Laboratorio de Química Analítica": "Campanas extractoras encendidas y frascos rotulados.",
    "Sala de Simulación": "Monitores con modelos de procesos en pausa.",
    "Oficina de Coordinación": "Un escritorio lleno de formularios por firmar.",
    "Estudio de Grabación": "Paneles acústicos y un micrófono con la luz roja apagada.",
    "Laboratorio de Energía": "Paneles solares de prueba y un banco de baterías.",
    "Cuarto Eléctrico": "Tableros con etiquetas amarillas. No toques nada.",
    "Bodega de Reactivos": "Gabinetes con llave y un olor fuerte a alcohol.",
    "Jaula de Racks": "Una reja metálica rodea los equipos de red.",
    "Cuarto Oscuro": "Luz roja tenue y cubetas de revelado.",
    "Bóveda de Prototipos": "Prototipos de otras generaciones, cada uno con su etiqueta.",
    "Cabina de Control": "Consolas de iluminación del auditorio del segundo nivel.",
    "Depósito de Baterías": "Cargadores en fila con luces verdes parpadeando.",
    "Closet del Conserje": "Trapeadores, cubetas y la radio del conserje.",
    "Cámara Anecoica": "Silencio absoluto: escuchas tu propio pulso.",
}

# Objetos perdidos que esperan en las salas más profundas (se ven en ui_inventario).
TESOROS = ("disco_duro", "calculadora", "bata", "trofeo", "tarjeta", "audifonos")


def ramificacion(profundidad, azar):
    """Cuántas salas hijas tendrá una sala en esta profundidad (variable)."""
    minimo, maximo = RAMIFICACION.get(profundidad, (0, 0))
    return azar.randint(minimo, maximo)


def generar_salas(sala_actual, profundidad, max_profundidad, conexiones, salas,
                  niveles, nombres_libres, azar):
    """Genera recursivamente la sala actual y todas sus descendientes.

    - CASO BASE: si `profundidad >= max_profundidad`, la sala se registra y no
      se generan hijas (la recursión se detiene).
    - CASO RECURSIVO: se decide cuántas hijas tiene (ramificación variable) y
      por cada una se toma un nombre del nivel siguiente, se anota la conexión
      (padre, hija) y se llama a `generar_salas` con profundidad + 1.

    Devuelve la profundidad real alcanzada desde esta sala (como el reto
    final de la Guía 7: combina lo que devuelven las llamadas con max()).
    """
    salas.append(sala_actual)
    niveles[sala_actual] = profundidad
    if profundidad >= max_profundidad:                       # caso base
        return profundidad
    alcanzada = profundidad
    for _ in range(ramificacion(profundidad, azar)):         # caso recursivo
        hija = nombres_libres[profundidad + 1].pop()
        conexiones.append((sala_actual, hija))
        alcanzada = max(alcanzada, generar_salas(
            hija, profundidad + 1, max_profundidad, conexiones, salas,
            niveles, nombres_libres, azar))
    return alcanzada


def construir_hijos(salas, conexiones):
    """Diccionario sala -> lista de salas hijas (en el orden en que se generaron)."""
    hijos = {sala: [] for sala in salas}
    for padre, hija in conexiones:
        hijos[padre].append(hija)
    return hijos


def contar_salas(sala_actual, hijos):
    """Total de salas del subárbol (recursivo): 1 + lo que cuenta cada hija."""
    return 1 + sum(contar_salas(hija, hijos) for hija in hijos[sala_actual])


def contar_salas_por_nivel(sala_actual, profundidad, hijos, conteo):
    """Guía 7, Ejercicio A: acumula en `conteo` cuántas salas hay por nivel.
    Caso base implícito: una sala sin hijas no hace llamadas nuevas."""
    conteo[profundidad] = conteo.get(profundidad, 0) + 1
    for hija in hijos[sala_actual]:
        contar_salas_por_nivel(hija, profundidad + 1, hijos, conteo)
    return conteo


def calcular_profundidad_real(sala_actual, profundidad, hijos):
    """Guía 7, Ejercicio C: nivel más profundo que existe debajo de esta sala.
    Con ramificación variable puede ser menor que la profundidad máxima."""
    if not hijos[sala_actual]:                               # caso base
        return profundidad
    return max(calcular_profundidad_real(hija, profundidad + 1, hijos)
               for hija in hijos[sala_actual])


def marcar_salas_profundas(sala_actual, profundidad, profundidad_objetivo, hijos, marcadas):
    """Guía 7, Ejercicio B: agrega a `marcadas` las salas que están en el
    nivel más profundo; ahí el juego esconde los objetos perdidos."""
    if profundidad == profundidad_objetivo:                  # caso base
        marcadas.append(sala_actual)
        return marcadas
    for hija in hijos[sala_actual]:
        marcar_salas_profundas(hija, profundidad + 1, profundidad_objetivo, hijos, marcadas)
    return marcadas


def dibujar_arbol(sala_actual, hijos, prefijo="", es_ultima=True, es_raiz=True, lineas=None,
                  etiqueta=None):
    """Devuelve el árbol como líneas de texto con sangría (recursivo).
    `etiqueta(sala)` puede añadir marcas como el tesoro o el jugador."""
    if lineas is None:
        lineas = []
    marca = etiqueta(sala_actual) if etiqueta else ""
    if es_raiz:
        lineas.append(f"{sala_actual}{marca}")
        prefijo_hijas = ""
    else:
        lineas.append(f"{prefijo}{'└── ' if es_ultima else '├── '}{sala_actual}{marca}")
        prefijo_hijas = prefijo + ("    " if es_ultima else "│   ")
    total = len(hijos[sala_actual])
    for i, hija in enumerate(hijos[sala_actual]):
        dibujar_arbol(hija, hijos, prefijo_hijas, i == total - 1, False, lineas, etiqueta)
    return lineas


def camino_desde_raiz(sala_actual, objetivo, hijos):
    """Lista de salas desde `sala_actual` hasta `objetivo` bajando por el
    árbol, o None si `objetivo` no está debajo (búsqueda recursiva)."""
    if sala_actual == objetivo:                              # caso base
        return [sala_actual]
    for hija in hijos[sala_actual]:
        camino = camino_desde_raiz(hija, objetivo, hijos)
        if camino:
            return [sala_actual] + camino
    return None


def generar_mazmorra(semilla=None, max_profundidad=PROFUNDIDAD_MAXIMA):
    """Genera la Torre completa y le aplica las adaptaciones de la Guía 7.
    Devuelve un diccionario con todo lo que el juego necesita."""
    azar = random.Random(semilla)
    nombres_libres = {nivel: azar.sample(nombres, len(nombres))
                      for nivel, nombres in NOMBRES_POR_NIVEL.items()}
    salas, conexiones, niveles = [], [], {}
    profundidad_real = generar_salas(NOMBRE_RAIZ, 0, max_profundidad, conexiones,
                                     salas, niveles, nombres_libres, azar)
    hijos = construir_hijos(salas, conexiones)
    padres = {hija: padre for padre, hija in conexiones}
    profundas = marcar_salas_profundas(NOMBRE_RAIZ, 0, profundidad_real, hijos, [])
    tesoros = azar.sample(TESOROS, len(TESOROS))
    return {
        "raiz": NOMBRE_RAIZ,
        "salas": salas,
        "conexiones": conexiones,
        "hijos": hijos,
        "padres": padres,
        "niveles": niveles,
        "profundidad_real": profundidad_real,
        "por_nivel": contar_salas_por_nivel(NOMBRE_RAIZ, 0, hijos, {}),
        "profundas": profundas,
        "objetos": {sala: tesoros[i % len(tesoros)] for i, sala in enumerate(profundas)},
    }


# ---------------------------------------------------------------------------
# Consultas que usa main.py para moverse por el árbol
# ---------------------------------------------------------------------------
def existe_sala(mazmorra, nombre):
    """True si la sala existe en la Torre."""
    return nombre in mazmorra["niveles"]


def salas_conectadas(mazmorra, sala):
    """Salas a las que se llega en un paso: sus hijas y, si tiene, su padre."""
    if not existe_sala(mazmorra, sala):
        return []
    conectadas = list(mazmorra["hijos"][sala])
    if sala in mazmorra["padres"]:
        conectadas.append(mazmorra["padres"][sala])
    return conectadas


def estan_conectadas(mazmorra, sala_a, sala_b):
    """True si hay paso directo entre las dos salas."""
    return sala_b in salas_conectadas(mazmorra, sala_a)


def paso_hacia(mazmorra, origen, destino):
    """Siguiente sala en el camino más corto de `origen` a `destino` dentro
    del árbol: baja si el destino está debajo, si no sube al padre."""
    if origen == destino:
        return origen
    camino = camino_desde_raiz(origen, destino, mazmorra["hijos"])
    if camino:
        return camino[1]
    return mazmorra["padres"].get(origen, origen)


def _normalizar(texto):
    sin_tildes = unicodedata.normalize("NFD", texto)
    return "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn").lower().strip()


def buscar_sala(mazmorra, texto):
    """Busca una sala por nombre escrito (sin importar mayúsculas ni tildes).
    Devuelve el nombre exacto o None si no existe."""
    buscado = _normalizar(texto)
    for sala in mazmorra["salas"]:
        if _normalizar(sala) == buscado:
            return sala
    return None
