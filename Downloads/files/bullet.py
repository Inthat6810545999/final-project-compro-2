"""
bullet.py  –  Player bullet projectile + HUD updated to HP/Armor/Mana bars
"""
import math
import pygame
from constants import (
    YELLOW, CYAN, WHITE, RED, GREEN, GOLD,
    SCREEN_W, SCREEN_H, HUD_H, DARK_GRAY, BLACK,
    RARITY_COLORS, GRAY, ORANGE, PURPLE, LIGHT_BLUE
)

# ─────────────────────────────────────────────────────────────
class Bullet:
    """Player-fired projectile."""

    def __init__(self, x, y, dx, dy, speed, damage, pierce=False, is_crit=False):
        self.x      = float(x)
        self.y      = float(y)
        self.dx     = dx
        self.dy     = dy
        self.speed  = speed
        self.damage = damage
        self.pierce = pierce      # Mage passive: pierce 1 enemy
        self.is_crit= is_crit
        self.alive  = True
        self.radius = 6
        self.hit_set = set()      # enemies already hit (for pierce)

    def update(self, dt, walls):
        self.x += self.dx * self.speed * 60 * dt
        self.y += self.dy * self.speed * 60 * dt

        # Wall collision
        for wall in walls:
            if wall.collidepoint(self.x, self.y):
                self.alive = False
                return

        # Screen bounds
        play_h = SCREEN_H - HUD_H
        if self.x < 0 or self.x > SCREEN_W * 3 or self.y < 0 or self.y > play_h * 3:
            self.alive = False

    def draw(self, surface, cam_x=0, cam_y=0):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        col  = GOLD   if self.is_crit else YELLOW
        col2 = ORANGE if self.is_crit else WHITE
        pygame.draw.circle(surface, col,  (sx, sy), self.radius)
        pygame.draw.circle(surface, col2, (sx, sy), self.radius - 3)


# ─────────────────────────────────────────────────────────────
class DroppedItem:
    """Item lying on the floor waiting to be picked up."""

    RADIUS = 14

    def __init__(self, item, x, y):
        self.item  = item
        self.x     = float(x)
        self.y     = float(y)
        self.alive = True
        self._bob  = 0.0   # for bobbing animation

    def update(self, dt):
        self._bob += dt * 3.0

    def draw(self, surface, cam_x=0, cam_y=0):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y) + int(math.sin(self._bob) * 3)
        r  = self.RADIUS
        col = self.item.rarity_color
        pygame.draw.circle(surface, col, (sx, sy), r)
        pygame.draw.circle(surface, WHITE, (sx, sy), r, 2)
        # Type letter
        font = _small_font()
        letter = self.item.item_type[0].upper()
        surf = font.render(letter, True, BLACK)
        surface.blit(surf, (sx - surf.get_width()//2, sy - surf.get_height()//2))

    def can_pickup(self, player):
        dist = math.hypot(self.x - player.x, self.y - player.y)
        return dist < self.RADIUS + player.RADIUS + 10


# ─────────────────────────────────────────────────────────────
class FloatingText:
    """Damage / EXP number that floats up and fades."""

    def __init__(self, x, y, text, color, size=18):
        self.x      = float(x)
        self.y      = float(y)
        self.text   = text
        self.color  = color
        self.size   = size
        self.life   = 1.0
        self.alive  = True

    def update(self, dt):
        self.y    -= 40 * dt
        self.life -= dt
        if self.life <= 0:
            self.alive = False

    def draw(self, surface, cam_x=0, cam_y=0):
        alpha = int(255 * self.life)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        font  = _font(self.size)
        surf  = font.render(self.text, True, self.color)
        ts    = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        ts.fill((0, 0, 0, 0))
        ts.blit(surf, (0, 0))
        ts.set_alpha(alpha)
        surface.blit(ts, (sx - surf.get_width()//2, sy))


# ─────────────────────────────────────────────────────────────
# HUD drawing
# ─────────────────────────────────────────────────────────────
_fc = {}
def _font(size=18):
    key = ("f", size)
    if key not in _fc:
        _fc[key] = pygame.font.SysFont("Arial", size, bold=True)
    return _fc[key]

def _small_font():
    return _font(14)

def _draw_bar(surface, x, y, w, h, value, maximum, color, back=(20,20,30)):
    pygame.draw.rect(surface, back, (x, y, w, h), border_radius=6)
    pct = max(0.0, min(1.0, value / max(1e-6, maximum)))
    fill_w = int((w - 4) * pct)
    pygame.draw.rect(surface, color, (x+2, y+2, fill_w, h-4), border_radius=5)
    pygame.draw.rect(surface, (80,80,100), (x, y, w, h), 2, border_radius=6)

def draw_hud(surface, player, stage, current_stage_idx, total_stages):
    """Draw the bottom HUD bar with HP / Armor / Mana."""
    hud_y  = SCREEN_H - HUD_H
    hud_rect = pygame.Rect(0, hud_y, SCREEN_W, HUD_H)
    pygame.draw.rect(surface, (15, 15, 25), hud_rect)
    pygame.draw.line(surface, (60, 60, 100), (0, hud_y), (SCREEN_W, hud_y), 2)

    big   = _font(20)
    small = _font(15)

    # Bars layout
    pad = 18
    bar_w = 260
    bar_h = 18
    x0 = pad
    y0 = hud_y + 16

    # HP
    text_surf = big.render("HP", True, RED)
    surface.blit(text_surf, (x0, y0 - 2))
    _draw_bar(surface, x0 + 40, y0, bar_w, bar_h, player.hp, player.max_hp, RED)

    # Armor (shield)
    ax = x0 + 40 + bar_w + 24
    text_surf = big.render("ARMOR", True, CYAN)
    surface.blit(text_surf, (ax - 6, y0 - 2))
    _draw_bar(surface, ax + 70, y0, 180, bar_h, player.armor, player.max_armor, CYAN)

    # Mana
    mx = ax + 70 + 180 + 24
    text_surf = big.render("MANA", True, BLUE)
    surface.blit(text_surf, (mx - 6, y0 - 2))
    _draw_bar(surface, mx + 50, y0, 220, bar_h, player.mana, player.max_mana, BLUE)

    # Simple stage text on right
    s = small.render(f"Stage {current_stage_idx+1}/{total_stages}", True, (200,200,220))
    surface.blit(s, (SCREEN_W - 160, hud_y + 12))