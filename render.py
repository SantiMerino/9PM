"""Letterbox / logical-resolution helpers for 9PM."""

from __future__ import annotations

import pygame

# Logical (game) resolution — camera, HUD, and all gameplay coords use this.
LOGICAL_W, LOGICAL_H = 960, 640

# Default OS window size (larger; content is letterboxed).
VENTANA_W, VENTANA_H = 1280, 720


def crear_ventana(ancho=VENTANA_W, alto=VENTANA_H, fullscreen=False):
    """Create a resizable display surface (letterboxing done in presentar)."""
    if fullscreen:
        return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    return pygame.display.set_mode((ancho, alto), pygame.RESIZABLE)


def crear_superficie_logica():
    return pygame.Surface((LOGICAL_W, LOGICAL_H))


def letterbox_rect(win_w, win_h, logical_w=LOGICAL_W, logical_h=LOGICAL_H):
    """Return (dest_rect, scale) for nearest-neighbor letterboxed blit."""
    if win_w <= 0 or win_h <= 0:
        return pygame.Rect(0, 0, logical_w, logical_h), 1.0
    scale = min(win_w / logical_w, win_h / logical_h)
    dw = max(1, int(logical_w * scale))
    dh = max(1, int(logical_h * scale))
    ox = (win_w - dw) // 2
    oy = (win_h - dh) // 2
    return pygame.Rect(ox, oy, dw, dh), scale


def presentar(ventana, logica, win_size):
    """Fill black, scale logical surface nearest-neighbor into letterbox."""
    win_w, win_h = win_size
    ventana.fill((0, 0, 0))
    dest, _scale = letterbox_rect(win_w, win_h)
    if dest.w == LOGICAL_W and dest.h == LOGICAL_H and dest.x == 0 and dest.y == 0:
        ventana.blit(logica, (0, 0))
    else:
        escalada = pygame.transform.scale(logica, (dest.w, dest.h))
        ventana.blit(escalada, dest.topleft)
    pygame.display.flip()


def ventana_a_logico(mx, my, win_size):
    """Map window mouse coords → logical coords (or None if in black bars)."""
    win_w, win_h = win_size
    dest, scale = letterbox_rect(win_w, win_h)
    if scale <= 0:
        return None
    if not dest.collidepoint(mx, my):
        return None
    lx = (mx - dest.x) / scale
    ly = (my - dest.y) / scale
    return lx, ly


def evento_con_pos_logica(evento, win_size):
    """Return a shallow copy of mouse events with .pos remapped to logical."""
    if evento.type not in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
        return evento
    mapped = ventana_a_logico(*evento.pos, win_size)
    if mapped is None:
        return None
    # pygame.event.Event is immutable-ish; build a dict proxy via Event()
    attrs = dict(evento.__dict__)
    attrs["pos"] = (int(mapped[0]), int(mapped[1]))
    if hasattr(evento, "rel") and evento.type == pygame.MOUSEMOTION:
        _, scale = letterbox_rect(*win_size)
        if scale > 0:
            attrs["rel"] = (evento.rel[0] / scale, evento.rel[1] / scale)
    return pygame.event.Event(evento.type, attrs)
