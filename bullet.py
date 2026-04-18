"""
bullet.py  –  Player bullet projectile + HUD updated to HP/Armor/Mana bars
"""
import math
import pygame
from constants import (
    YELLOW, CYAN, WHITE, RED, GREEN, GOLD,
    SCREEN_W, SCREEN_H, HUD_H, DARK_GRAY, BLACK,
    RARITY_COLORS, GRAY, ORANGE, PURPLE, LIGHT_BLUE,
    BLUE,          # FIX: was missing, needed for Mana bar in draw_hud
    TILE, MAP_W, MAP_H,  # FIX: used for correct bullet out-of-bounds check
)


# ─────────────────────────────────────────────────────────────
class Bullet:
    """Player-fired projectile."""

    def __init__(self, x, y, dx, dy, speed, damage, pierce=False, is_crit=False,
                 color=None, size=6):
        self.x       = float(x)
        self.y       = float(y)
        self.dx      = dx
        self.dy      = dy
        self.speed   = speed
        self.damage  = damage
        self.pierce  = pierce
        self.is_crit = is_crit
        self.alive   = True
        self.radius  = size
        self.color   = color or (255, 230, 80)
        self.hit_set = set()

    def update(self, dt, walls):
        self.x += self.dx * self.speed * 60 * dt
        self.y += self.dy * self.speed * 60 * dt
        for wall in walls:
            if wall.collidepoint(self.x, self.y):
                self.alive = False
                return
        map_w = MAP_W * TILE
        map_h = MAP_H * TILE
        if self.x < 0 or self.x > map_w or self.y < 0 or self.y > map_h:
            self.alive = False

    def draw(self, surface, cam_x=0, cam_y=0):
        sx  = int(self.x - cam_x)
        sy  = int(self.y - cam_y)
        col = tuple(min(255, c + 80) for c in self.color) if self.is_crit else self.color
        glow = pygame.Surface((self.radius*4, self.radius*4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*col, 60), (self.radius*2, self.radius*2), self.radius*2)
        surface.blit(glow, (sx - self.radius*2, sy - self.radius*2))
        pygame.draw.circle(surface, col, (sx, sy), self.radius)
        core_col = tuple(min(255, c + 100) for c in col)
        pygame.draw.circle(surface, core_col, (sx, sy), max(1, self.radius - 3))


# ─────────────────────────────────────────────────────────────
class DroppedItem:
    """Item lying on the floor waiting to be picked up."""

    RADIUS = 14

    def __init__(self, item, x, y):
        self.item  = item
        self.x     = float(x)
        self.y     = float(y)
        self.alive = True
        self._bob  = 0.0

    def update(self, dt):
        self._bob += dt * 3.0

    def draw(self, surface, cam_x=0, cam_y=0, player=None):
        sx  = int(self.x - cam_x)
        sy  = int(self.y - cam_y) + int(math.sin(self._bob) * 3)
        r   = self.RADIUS
        col = self.item.rarity_color

        # Outer glow for rarity
        glow_r = r + 5 + int(math.sin(self._bob * 2) * 2)
        glow_surf = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*col, 60), (glow_r + 2, glow_r + 2), glow_r)
        surface.blit(glow_surf, (sx - glow_r - 2, sy - glow_r - 2))

        pygame.draw.circle(surface, col, (sx, sy), r)
        pygame.draw.circle(surface, WHITE, (sx, sy), r, 2)
        font   = _small_font()
        letter = self.item.item_type[0].upper()
        surf   = font.render(letter, True, BLACK)
        surface.blit(surf, (sx - surf.get_width() // 2, sy - surf.get_height() // 2))

        # ── E-pickup prompt when player is nearby ─────────────
        if player and self.can_pickup(player):
            # Animated pulsing circle
            pulse = int(math.sin(self._bob * 5) * 3)
            pygame.draw.circle(surface, GOLD, (sx, sy), r + 8 + pulse, 2)

            # "E" key badge
            badge_x = sx + r + 2
            badge_y = sy - r - 2
            badge_r = pygame.Rect(badge_x - 2, badge_y - 2, 22, 22)
            pygame.draw.rect(surface, (20, 20, 30), badge_r, border_radius=4)
            pygame.draw.rect(surface, GOLD,         badge_r, 2, border_radius=4)
            e_surf = _font(13).render("E", True, GOLD)
            surface.blit(e_surf, (badge_x + 1, badge_y + 1))

            # Item name tooltip
            name_font = _font(11)
            name_surf = name_font.render(self.item.name, True, col)
            nx = sx - name_surf.get_width() // 2
            ny = sy - r - 24
            # Dark background
            bg = pygame.Surface((name_surf.get_width() + 6, name_surf.get_height() + 4), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))
            surface.blit(bg, (nx - 3, ny - 2))
            surface.blit(name_surf, (nx, ny))

    def can_pickup(self, player):
        dist = math.hypot(self.x - player.x, self.y - player.y)
        return dist < self.RADIUS + player.RADIUS + 10


# ─────────────────────────────────────────────────────────────
class FloatingText:
    """Damage / EXP number that floats up and fades."""

    def __init__(self, x, y, text, color, size=18):
        self.x     = float(x)
        self.y     = float(y)
        self.text  = text
        self.color = color
        self.size  = size
        self.life  = 1.0
        self.alive = True

    def update(self, dt):
        self.y    -= 40 * dt
        self.life -= dt
        if self.life <= 0:
            self.alive = False

    def draw(self, surface, cam_x=0, cam_y=0):
        alpha = int(255 * self.life)
        sx    = int(self.x - cam_x)
        sy    = int(self.y - cam_y)
        font  = _font(self.size)
        surf  = font.render(self.text, True, self.color)
        ts    = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        ts.fill((0, 0, 0, 0))
        ts.blit(surf, (0, 0))
        ts.set_alpha(alpha)
        surface.blit(ts, (sx - surf.get_width() // 2, sy))


# ─────────────────────────────────────────────────────────────
# Font helpers
# ─────────────────────────────────────────────────────────────
_fc = {}

def _font(size=18):
    key = ("f", size)
    if key not in _fc:
        _fc[key] = pygame.font.SysFont("Arial", size, bold=True)
    return _fc[key]

def _small_font():
    return _font(14)


# ─────────────────────────────────────────────────────────────
# HUD drawing
# ─────────────────────────────────────────────────────────────
def _draw_heart(surface, cx, cy, size, color):
    s = size // 2
    pygame.draw.circle(surface, color, (cx - s//2, cy - s//4), s//2)
    pygame.draw.circle(surface, color, (cx + s//2, cy - s//4), s//2)
    points = [(cx - s, cy - s//4), (cx, cy + s), (cx + s, cy - s//4)]
    pygame.draw.polygon(surface, color, points)

def _draw_shield(surface, cx, cy, size, color):
    w, h = size, int(size * 1.2)
    points = [
        (cx - w//2, cy - h//2), (cx + w//2, cy - h//2),
        (cx + w//2, cy), (cx, cy + h//2), (cx - w//2, cy),
    ]
    pygame.draw.polygon(surface, color, points)

def _draw_diamond(surface, cx, cy, size, color):
    s = size // 2
    pygame.draw.polygon(surface, color,
        [(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)])

def _draw_sk_bar(surface, x, y, w, h, value, maximum, fill_col, back=(10, 10, 20)):
    pygame.draw.rect(surface, back, (x, y, w, h), border_radius=h//2)
    pygame.draw.rect(surface, (60, 60, 80), (x, y, w, h), 1, border_radius=h//2)
    pct    = max(0.0, min(1.0, value / max(1e-6, maximum)))
    fill_w = max(0, int((w - 4) * pct))
    if fill_w > 0:
        pygame.draw.rect(surface, fill_col,
                         (x + 2, y + 2, fill_w, h - 4), border_radius=(h-4)//2)
        bright = tuple(min(255, c + 60) for c in fill_col)
        pygame.draw.rect(surface, bright,
                         (x + 2, y + 2, fill_w, (h-4)//3), border_radius=(h-4)//2)

def draw_hud(surface, player, stage, current_stage_idx, total_stages, run_time=0.0):
    from constants import CLASS_SKILLS

    # TOP-LEFT Soul Knight bars
    ICON  = 18
    BAR_W = 150
    BAR_H = 16
    PAD   = 6
    ROW_H = BAR_H + PAD
    PX, PY = 8, 8
    PW = ICON + 8 + BAR_W + 6
    PH = ROW_H * 3 + PAD

    panel_surf = pygame.Surface((PW, PH), pygame.SRCALPHA)
    panel_surf.fill((0, 0, 0, 130))
    pygame.draw.rect(panel_surf, (80, 80, 120, 180), (0, 0, PW, PH), 2, border_radius=10)
    surface.blit(panel_surf, (PX, PY))

    num_font = _font(12)
    rows = [
        (_draw_heart,   (220, 50,  50),  player.hp,    player.max_hp),
        (_draw_shield,  (50,  210, 210), player.armor, player.max_armor),
        (_draw_diamond, (80,  120, 255), player.mana,  player.max_mana),
    ]
    for i, (icon_fn, col, val, maxv) in enumerate(rows):
        row_y  = PY + PAD + i * ROW_H
        icon_x = PX + ICON // 2 + 4
        icon_y = row_y + BAR_H // 2
        icon_fn(surface, icon_x, icon_y, ICON, col)
        bar_x = PX + ICON + 10
        _draw_sk_bar(surface, bar_x, row_y, BAR_W, BAR_H, val, maxv, col)
        txt = num_font.render(f"{int(val)}/{int(maxv)}", True, WHITE)
        surface.blit(txt, (bar_x + BAR_W//2 - txt.get_width()//2,
                           row_y + BAR_H//2 - txt.get_height()//2))

    # BOTTOM HUD strip
    hud_y    = SCREEN_H - HUD_H
    hud_rect = pygame.Rect(0, hud_y, SCREEN_W, HUD_H)
    pygame.draw.rect(surface, (12, 12, 22), hud_rect)
    pygame.draw.line(surface, (60, 60, 110), (0, hud_y), (SCREEN_W, hud_y), 2)

    inf_font = _font(14)

    # Skill button
    skill_cfg  = CLASS_SKILLS.get(player.char_class, {})
    skill_name = skill_cfg.get("name", "Skill")
    skill_cd   = getattr(player, "skill_cd", 0)
    skill_max  = skill_cfg.get("cooldown", 5.0)
    sk_ready   = (skill_cd <= 0)
    sk_x = 14
    sk_col  = (40, 180, 255) if sk_ready else (50, 50, 80)
    sk_bord = (80, 220, 255) if sk_ready else (80, 80, 120)
    pygame.draw.rect(surface, sk_col,  (sk_x, hud_y + 8, 52, 52), border_radius=8)
    pygame.draw.rect(surface, sk_bord, (sk_x, hud_y + 8, 52, 52), 2, border_radius=8)
    if not sk_ready:
        fill_h = int(52 * (skill_cd / max(0.01, skill_max)))
        cd_overlay = pygame.Surface((52, max(1, fill_h)), pygame.SRCALPHA)
        cd_overlay.fill((0, 0, 0, 140))
        surface.blit(cd_overlay, (sk_x, hud_y + 8))
    q_surf = _font(11).render("Q", True, WHITE)
    surface.blit(q_surf, (sk_x + 4, hud_y + 10))
    sn_surf = _font(10).render(skill_name[:7], True, WHITE)
    surface.blit(sn_surf, (sk_x + 26 - sn_surf.get_width()//2, hud_y + 24))
    if not sk_ready:
        cd_surf = _font(13).render(f"{int(skill_cd)}", True, YELLOW)
        surface.blit(cd_surf, (sk_x + 26 - cd_surf.get_width()//2, hud_y + 38))
    else:
        rdy_surf = _font(10).render("READY", True, (80, 255, 80))
        surface.blit(rdy_surf, (sk_x + 26 - rdy_surf.get_width()//2, hud_y + 40))

    # Pause button
    pb_w, pb_h = 52, 52
    pb_x = SCREEN_W - pb_w - 14
    pb_y = hud_y + 8
    pb_rect   = pygame.Rect(pb_x, pb_y, pb_w, pb_h)
    mouse_pos = pygame.mouse.get_pos()
    pb_hover  = pb_rect.collidepoint(mouse_pos)
    pb_fill   = (80, 80, 120) if pb_hover else (40, 40, 70)
    pb_border = (160, 160, 220) if pb_hover else (90, 90, 140)
    pygame.draw.rect(surface, pb_fill,   pb_rect, border_radius=8)
    pygame.draw.rect(surface, pb_border, pb_rect, 2, border_radius=8)
    bar_col = WHITE if pb_hover else (180, 180, 220)
    pygame.draw.rect(surface, bar_col, (pb_x + 14, pb_y + 13, 8, 26), border_radius=2)
    pygame.draw.rect(surface, bar_col, (pb_x + 30, pb_y + 13, 8, 26), border_radius=2)
    esc_s = _font(9).render("ESC", True, (160, 160, 200))
    surface.blit(esc_s, (pb_x + pb_w//2 - esc_s.get_width()//2, pb_y + pb_h - 13))

    # Right info
    mins = int(run_time) // 60
    secs = int(run_time) % 60
    time_str = f"{mins:02d}:{secs:02d}"
    right_lines = [
        (f"Stage {current_stage_idx+1}/{total_stages}", (180, 180, 220)),
        (f"Lv.{player.level}   {player.gold}G",        GOLD),
        (f"  {time_str}",                               (160, 220, 160)),
    ]
    ry = hud_y + 6
    for line, col in right_lines:
        s = inf_font.render(line, True, col)
        surface.blit(s, (SCREEN_W - pb_w - 24 - s.get_width(), ry))
        ry += 22

    return pb_rect
