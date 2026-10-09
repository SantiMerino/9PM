"""Crea un acceso directo de 9PM en el escritorio de Windows (con su ícono).

    .\\.venv\\Scripts\\python.exe crear_acceso_directo.py

Dibuja el ícono en pixel art (un reloj marcando las 9 y el texto 9PM), lo
guarda en assets/9pm.ico y crea "9PM.lnk" en el escritorio. El acceso directo
abre el juego con pythonw.exe del entorno local, así que no aparece la
ventana de la consola. Si el juego se cierra con un error, queda guardado en
error_9pm.log.
"""
import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import pygame

CARPETA = Path(__file__).resolve().parent
ICONO = CARPETA / 'assets' / '9pm.ico'
INK = (28, 43, 57)
CREMA = (237, 231, 205)
ORO = (241, 199, 116)
TEAL = (72, 169, 158)
ROJO = (224, 76, 76)


def dibujar_icono():
    """Ícono de 64x64 en pixel art, ampliado sin suavizado a 256x256."""
    pygame.init()
    s = pygame.Surface((64, 64), pygame.SRCALPHA)
    pygame.draw.rect(s, INK, (2, 2, 60, 60))
    pygame.draw.rect(s, (18, 30, 44), (4, 4, 56, 56))
    pygame.draw.rect(s, TEAL, (2, 2, 60, 60), 2)
    for x, y in ((10, 10), (52, 9), (47, 18), (14, 22)):
        s.set_at((x, y), (150, 176, 190))
    pygame.draw.circle(s, CREMA, (12, 12), 4)
    pygame.draw.circle(s, (18, 30, 44), (14, 11), 3)
    # Reloj marcando las 9 en punto
    pygame.draw.circle(s, INK, (32, 27), 19)
    pygame.draw.circle(s, CREMA, (32, 27), 16)
    for dx, dy in ((0, -13), (13, 0), (0, 13), (-13, 0)):
        pygame.draw.rect(s, INK, (32 + dx - 1, 27 + dy - 1, 2, 2))
    pygame.draw.line(s, INK, (32, 27), (32, 15), 3)
    pygame.draw.line(s, ROJO, (32, 27), (22, 27), 4)
    pygame.draw.rect(s, INK, (31, 26, 3, 3))
    fuente = pygame.font.SysFont('consolas', 15, bold=True)
    for dx, dy, color in ((1, 1, INK), (0, 0, ORO)):
        im = fuente.render('9PM', False, color)
        s.blit(im, im.get_rect(center=(32 + dx, 54 + dy)))
    return pygame.transform.scale(s, (256, 256))


def guardar_ico(superficie, ruta):
    from PIL import Image
    ruta.parent.mkdir(parents=True, exist_ok=True)
    datos = pygame.image.tobytes(superficie, 'RGBA')
    imagen = Image.frombytes('RGBA', superficie.get_size(), datos)
    imagen.save(ruta, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


def crear_lnk():
    """Usa WScript.Shell (PowerShell) para crear el acceso directo."""
    pythonw = CARPETA / '.venv' / 'Scripts' / 'pythonw.exe'
    if not pythonw.exists():
        pythonw = Path(sys.executable).with_name('pythonw.exe')
    script = (
        "$escritorio=[Environment]::GetFolderPath('Desktop');"
        "$lnk=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $escritorio '9PM.lnk'));"
        f"$lnk.TargetPath='{pythonw}';"
        f"$lnk.Arguments='\"{CARPETA / 'main.py'}\"';"
        f"$lnk.WorkingDirectory='{CARPETA}';"
        f"$lnk.IconLocation='{ICONO},0';"
        "$lnk.Description='9PM - Instituto Kriete';"
        "$lnk.Save();"
        "Write-Output (Join-Path $escritorio '9PM.lnk')"
    )
    salida = subprocess.run(['powershell', '-NoProfile', '-Command', script],
                            capture_output=True, text=True, check=True)
    return salida.stdout.strip()


if __name__ == '__main__':
    guardar_ico(dibujar_icono(), ICONO)
    print('Ícono:', ICONO)
    print('Acceso directo:', crear_lnk())
