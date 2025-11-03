# framework/utils.py
import os
import pygame

RICHTUNGEN = ["up", "right", "down", "left"]

def richtung_offset(r):
    if r == "up": return (0, -1)
    if r == "down": return (0, 1)
    if r == "left": return (-1, 0)
    if r == "right": return (1, 0)
    #return (0, 0)

def richtung_offset2(r):
    if r == "up": return (0, 1)
    if r == "down": return (0, -1)
    if r == "left": return (1, 0)
    if r == "right": return (-1, 0)
    #return (0, 0)

def lade_sprite(pfad, feldgroesse=64):
    # Display für convert_alpha absichern
    if not pygame.display.get_init():
        pygame.display.init()
    if not pygame.display.get_surface():
        pygame.display.set_mode((1, 1))

    if pfad and os.path.exists(pfad):
        try:
            return pygame.image.load(pfad).convert_alpha()
        except Exception as e:
            print(f"[Warnung] Konnte Sprite nicht laden {pfad}: {e}")
    # Fallback: rotes Platzhalterbild
    surf = pygame.Surface((feldgroesse, feldgroesse), pygame.SRCALPHA)
    surf.fill((200, 0, 0, 160))
    pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 2)
    return surf
