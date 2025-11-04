import pygame
import math
import random
from typing import Tuple, List

# --- Gradient palettes (random per game) ---
GRADIENT_SETS = [
    ((255, 105, 180), (255, 165, 0)),     # pink → orange
    ((0, 191, 255), (65, 105, 225)),      # light → royal blue
    ((255, 0, 128), (255, 215, 0)),       # magenta → gold
    ((0, 255, 200), (0, 128, 255)),       # teal → sky
    ((255, 99, 71), (255, 255, 0)),       # tomato → yellow
]
def random_gradient_colors() -> Tuple[Tuple[int,int,int], Tuple[int,int,int]]:
    return random.choice(GRADIENT_SETS)

# --- Given circle (gold rim, black fill, white number) ---
def draw_cell_circle(screen, x, y, size, value=None, font=None, line_width_ratio=0.6):
    center = (x + size // 2, y + size // 2)
    line_width = size * line_width_ratio
    radius = int(line_width / 2)                   # match line thickness visually
    border_width = max(1, int(size * 0.02))        # thin golden rim

    pygame.draw.circle(screen, (0, 0, 0), center, radius)
    pygame.draw.circle(screen, (212, 175, 55), center, radius, border_width)
    if value is not None and font is not None:
        txt = font.render(str(value), True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=center))

# --- Continuous HD gradient polyline (under circles) ---
def draw_gradient_polyline(surface, points: List[Tuple[int,int]], width: int,
                           color_start: Tuple[int,int,int],
                           color_end: Tuple[int,int,int]):
    if len(points) < 2:
        return
    SSAA = 2
    swidth = int(width * SSAA)

    spoints: List[Tuple[int,int]] = []
    for i in range(1, len(points)):
        x1, y1 = points[i-1]; x2, y2 = points[i]
        dx, dy = x2 - x1, y2 - y1
        seg_len = max(1, int(math.hypot(dx, dy) * SSAA))
        for s in range(seg_len):
            t = s / seg_len
            xi = int((x1 + t * dx) * SSAA)
            yi = int((y1 + t * dy) * SSAA)
            spoints.append((xi, yi))
    x_end, y_end = points[-1]
    spoints.append((int(x_end * SSAA), int(y_end * SSAA)))

    minx = min(p[0] for p in spoints); miny = min(p[1] for p in spoints)
    maxx = max(p[0] for p in spoints); maxy = max(p[1] for p in spoints)
    pad = swidth + 4
    W = (maxx - minx) + 2*pad; H = (maxy - miny) + 2*pad
    ssurf = pygame.Surface((max(W,1), max(H,1)), pygame.SRCALPHA)

    total_steps = len(spoints)
    for i, (sx, sy) in enumerate(spoints):
        t = i / (total_steps - 1)
        r = int(color_start[0] + t * (color_end[0] - color_start[0]))
        g = int(color_start[1] + t * (color_end[1] - color_start[1]))
        b = int(color_start[2] + t * (color_end[2] - color_start[2]))
        lx = sx - minx + pad; ly = sy - miny + pad
        pygame.draw.circle(ssurf, (r, g, b, 255), (lx, ly), int(swidth * 0.45))  # slightly tight for less bloom

    smooth = pygame.transform.smoothscale(ssurf, (ssurf.get_width()//SSAA, ssurf.get_height()//SSAA))
    dest_x = (minx - pad) / SSAA; dest_y = (miny - pad) / SSAA
    surface.blit(smooth, (dest_x, dest_y), special_flags=pygame.BLEND_PREMULTIPLIED)
