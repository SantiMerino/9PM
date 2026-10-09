"""Ventajas opcionales de carrera. No bloquean ninguna misión ni cambian requisitos."""
import math
from carreras import obtener_carrera, ESTACIONES_DIGITALES, ESTACIONES_MECANICAS

class HabilidadCarrera:
    def __init__(self,carrera):
        self.perfil=obtener_carrera(carrera)
        self.recarga=0.0
        self.activa=0.0
        self.destello=0.0
        self.destino=None
        self.escena=None

    @property
    def factor_velocidad(self):
        return 1.45 if self.perfil.id=='industrial' and self.activa>0 else 1.0

    def avanzar(self,dt):
        """Devuelve segundos efectivos del reloj, incluso si el buff termina a mitad del frame."""
        ralentizados=min(dt,self.activa) if self.perfil.id=='quimica' else 0
        self.recarga=max(0,self.recarga-dt)
        self.activa=max(0,self.activa-dt)
        self.destello=max(0,self.destello-dt)
        return dt-ralentizados*.5

    def _objetivo(self,p,compatibles):
        if p.ubicacion!='interior': return None
        m=next(m for m in p.mision.hijas if m.ubicacion==p.sala_interior)
        if m.completada or (p.sala_interior,m.paso) not in compatibles: return None
        return next((i for i in p.interior_interactivos if i.get('paso')==m.paso),None)

    def usar(self,p):
        if p.terminado or p.en_transicion or p.panel_activo:
            return False
        if self.recarga>0:
            p._agregar_toast(f'{self.perfil.herramienta}: lista en {math.ceil(self.recarga)} s.')
            return False
        clave=self.perfil.id
        destino=p.jugador.pos
        if clave=='computacion':
            item=self._objetivo(p,ESTACIONES_DIGITALES)
            if item is None:
                p._agregar_toast('Terminal: busca una estación digital pendiente en R101, R103, R105 o Click.')
                return False
            if not p.resolver_estacion(item,alcance=180): return False
            destino=item['pos']
            p._agregar_toast('Acceso remoto: estación digital validada desde tu terminal.')
        elif clave=='mecatronica':
            if p.ubicacion=='pasillo':
                candidatos=[o for o in p.objetos_mundo if not o['recogido'] and math.dist(o['pos'],p.jugador.pos)<=220]
                if not candidatos:
                    p._agregar_toast('Microbot: acércate a un objeto (220 px) o a un equipo de Siemens, Spark o Kite.')
                    return False
                objeto=min(candidatos,key=lambda o:math.dist(o['pos'],p.jugador.pos))
                if not p.recoger_objeto(objeto,alcance=220): return False
                destino=objeto['pos']
                p._agregar_toast('Microbot: objeto recuperado y guardado en tu bolsa.')
            else:
                item=self._objetivo(p,ESTACIONES_MECANICAS)
                if item is None:
                    p._agregar_toast('Microbot: ayuda con el PLC de Siemens, la calibración de Spark y el prototipo de Kite. Sigue el orden de la bitácora.')
                    return False
                if not p.resolver_estacion(item,alcance=160): return False
                destino=item['pos']
                p._agregar_toast('Microbot: equipo calibrado. Estación completada.')
        elif clave=='industrial':
            self.activa=self.perfil.duracion
            p._agregar_toast('Ruta óptima: velocidad +45% durante 12 segundos.')
        elif clave=='quimica':
            self.activa=self.perfil.duracion
            p._agregar_toast('Concentración: el reloj avanza a la mitad durante 12 segundos.')
        self.recarga=self.perfil.recarga
        self.destello=1.2
        self.destino=destino
        self.escena=(p.ubicacion,p.sala_interior)
        return True
