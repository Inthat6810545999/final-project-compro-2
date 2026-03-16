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

    def __init__(self, x, y, dx, dy, speed, damage, pierce=False, is_crit=False):
        self.x       = float(x)
        self.y       = float(y)
        self.dx      = dx
        self.dy      = dy
        self.speed   = speed
        self.damage  = damage
        self.pierce  = pierce
        self.is_crit = is_crit
        self.alive   = True
        self.radius  = 6
        self.hit_set = set()   # enemies already hit (for pierce)

    def update(self, dt, walls):
        self.x += self.dx * self.speed * 60 * dt
        self.y += self.dy * self.speed * 60 * dt

        # Wall collision
        for wall in walls:
            if wall.collidepoint(self.x, self.y):
                self.alive = False
                return

        # FIX: use actual map bounds instead of 3× screen size
        map_w = MAP_W * TILE
        map_h = MAP_H * TILE
        if self.x < 0 or self.x > map_w or self.y < 0 or self.y > map_h:
            self.alive = False

    def draw(self, surface, cam_x=0, cam_y=0):
        sx   = int(self.x - cam_x)
        sy   = int(self.y - cam_y)
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
def _draw_bar(surface, x, y, w, h, value, maximum, color, back=(20, 20, 30)):
    pygame.draw.rect(surface, back, (x, y, w, h), border_radius=6)
    pct    = max(0.0, min(1.0, value / max(1e-6, maximum)))
    fill_w = int((w - 4) * pct)
    pygame.draw.rect(surface, color, (x + 2, y + 2, fill_w, h - 4), border_radius=5)
    pygame.draw.rect(surface, (80, 80, 100), (x, y, w, h), 2, border_radius=6)


def draw_hud(surface, player, stage, current_stage_idx, total_stages, run_time=0.0):
    """Draw bottom HUD: HP / Armor / Mana bars + skill cooldown + elapsed time."""
    from constants import CLASS_SKILLS
    hud_y    = SCREEN_H - HUD_H
    hud_rect = pygame.Rect(0, hud_y, SCREEN_W, HUD_H)
    pygame.draw.rect(surface, (15, 15, 25), hud_rect)
    pygame.draw.line(surface, (60, 60, 100), (0, hud_y), (SCREEN_W, hud_y), 2)

    lbl_font = _font(14)
    num_font = _font(13)
    inf_font = _font(14)

    bar_h = 20
    bar_y = hud_y + 12

    # ── HP bar ───────────────────────────────────────────────
    x = 14
    surface.blit(lbl_font.render("HP", True, RED), (x, bar_y + 1))
    bar_x, bar_w = x + 34, 180
    _draw_bar(surface, bar_x, bar_y, bar_w, bar_h,
              player.hp, player.max_hp, RED)
    hp_txt = num_font.render(f"{int(player.hp)}/{player.max_hp}", True, WHITE)
    surface.blit(hp_txt, (bar_x + bar_w//2 - hp_txt.get_width()//2, bar_y + 2))

    # ── Armor bar ────────────────────────────────────────────
    x = bar_x + bar_w + 14
    surface.blit(lbl_font.render("ARM", True, CYAN), (x, bar_y + 1))
    bar_x2, bar_w2 = x + 38, 150
    _draw_bar(surface, bar_x2, bar_y, bar_w2, bar_h,
              player.armor, player.max_armor, CYAN)
    arm_txt = num_font.render(f"{int(player.armor)}/{player.max_armor}", True, WHITE)
    surface.blit(arm_txt, (bar_x2 + bar_w2//2 - arm_txt.get_width()//2, bar_y + 2))

    # ── Mana bar ─────────────────────────────────────────────
    x = bar_x2 + bar_w2 + 14
    surface.blit(lbl_font.render("MP", True, LIGHT_BLUE), (x, bar_y + 1))
    bar_x3, bar_w3 = x + 28, 150
    _draw_bar(surface, bar_x3, bar_y, bar_w3, bar_h,
              player.mana, player.max_mana, BLUE)
    mp_txt = num_font.render(f"{int(player.mana)}/{player.max_mana}", True, WHITE)
    surface.blit(mp_txt, (bar_x3 + bar_w3//2 - mp_txt.get_width()//2, bar_y + 2))

    # ── Skill button (Q) ─────────────────────────────────────
    sk_x = bar_x3 + bar_w3 + 18
    skill_cfg = CLASS_SKILLS.get(player.char_class, {})
    skill_name = skill_cfg.get("name", "Skill")
    skill_cd   = getattr(player, "skill_cd", 0)
    skill_max  = skill_cfg.get("cooldown", 5.0)
    sk_ready   = (skill_cd <= 0)

    sk_col  = (40, 180, 255) if sk_ready else (50, 50, 80)
    sk_bord = (80, 220, 255) if sk_ready else (80, 80, 120)
    pygame.draw.rect(surface, sk_col,  (sk_x, hud_y + 8, 52, 52), border_radius=8)
    pygame.draw.rect(surface, sk_bord, (sk_x, hud_y + 8, 52, 52), 2, border_radius=8)

    # Cooldown fill overlay
    if not sk_ready:
        fill_h = int(52 * (skill_cd / max(0.01, skill_max)))
        pygame.draw.rect(surface, (0, 0, 0, 160),
                         (sk_x, hud_y + 8, 52, fill_h), border_radius=8)

    # Q label
    q_surf = _font(11).render("Q", True, WHITE)
    surface.blit(q_surf, (sk_x + 4, hud_y + 10))

    # Skill name (short)
    short = skill_name[:7]
    sn_surf = _font(10).render(short, True, WHITE)
    surface.blit(sn_surf, (sk_x + 26 - sn_surf.get_width()//2, hud_y + 24))

    # CD number
    if not sk_ready:
        cd_surf = _font(13, ).render(f"{skill_cd:.1f}", True, YELLOW)
        surface.blit(cd_surf, (sk_x + 26 - cd_surf.get_width()//2, hud_y + 38))
    else:
        rdy_surf = _font(10).render("READY", True, (80, 255, 80))
        surface.blit(rdy_surf, (sk_x + 26 - rdy_surf.get_width()//2, hud_y + 40))

    # ── Right side info ───────────────────────────────────────
    mins = int(run_time) // 60
    secs = int(run_time) % 60
    time_str = f"{mins:02d}:{secs:02d}"

    right_lines = [
        (f"Stage {current_stage_idx+1}/{total_stages}",  (180, 180, 220)),
        (f"Lv.{player.level}   {player.gold}G",         GOLD),
        (f"⏱ {time_str}",                                (160, 220, 160)),
    ]
    ry = hud_y + 6
    for line, col in right_lines:
        s = inf_font.render(line, True, col)
        surface.blit(s, (SCREEN_W - s.get_width() - 14, ry))
        ry += 22
