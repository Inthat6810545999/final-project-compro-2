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
class LaserBeam:
    """
    Instant hit-scan laser beam — visual effect only.
    Damage is applied immediately on creation; this class just renders the beam.
    Lifetime ~0.18 s then fades out.
    """

    def __init__(self, x1, y1, x2, y2, color=(255, 60, 60), width=3, lifetime=0.18):
        self.x1      = float(x1)
        self.y1      = float(y1)
        self.x2      = float(x2)
        self.y2      = float(y2)
        self.color   = color
        self.width   = width
        self.life    = lifetime
        self.max_life = lifetime
        self.alive   = True

    def update(self, dt, walls=None):
        self.life -= dt
        if self.life <= 0:
            self.alive = False

    def draw(self, surface, cam_x=0, cam_y=0):
        if not self.alive:
            return
        alpha_ratio = self.life / self.max_life          # 1 → 0
        alpha       = int(255 * alpha_ratio)

        sx1 = int(self.x1 - cam_x)
        sy1 = int(self.y1 - cam_y)
        sx2 = int(self.x2 - cam_x)
        sy2 = int(self.y2 - cam_y)

        length  = math.hypot(sx2 - sx1, sy2 - sy1)
        if length < 1:
            return

        # ── Outer glow layer (wide, faint) ───────────────────
        glow_w = self.width * 4
        glow_col = (*self.color, max(0, int(alpha * 0.35)))
        beam_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.line(beam_surf, glow_col, (sx1, sy1), (sx2, sy2), glow_w)

        # ── Mid layer ─────────────────────────────────────────
        mid_col = (*self.color, max(0, int(alpha * 0.75)))
        pygame.draw.line(beam_surf, mid_col, (sx1, sy1), (sx2, sy2), max(1, self.width))

        # ── Core (white-hot centre) ───────────────────────────
        core_col = (min(255, self.color[0] + 80),
                    min(255, self.color[1] + 80),
                    min(255, self.color[2] + 80), alpha)
        pygame.draw.line(beam_surf, core_col, (sx1, sy1), (sx2, sy2), max(1, self.width - 1))

        surface.blit(beam_surf, (0, 0))

        # ── Impact flash at end point ─────────────────────────
        if alpha_ratio > 0.6:
            flash_r = int((self.width + 4) * alpha_ratio)
            flash_surf = pygame.Surface((flash_r * 4, flash_r * 4), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (*self.color, int(alpha * 0.8)),
                               (flash_r * 2, flash_r * 2), flash_r * 2)
            surface.blit(flash_surf, (sx2 - flash_r * 2, sy2 - flash_r * 2))


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
class Portal:
    """Warp portal that spawns on last enemy killed — walk into it to proceed."""

    RADIUS = 30

    def __init__(self, x, y):
        self.x     = float(x)
        self.y     = float(y)
        self.alive = True
        self._bob  = 0.0

    def update(self, dt):
        self._bob += dt * 2.2

    def can_enter(self, player):
        return math.hypot(self.x - player.x, self.y - player.y) < self.RADIUS + player.RADIUS

    def draw(self, surface, cam_x=0, cam_y=0):
        t  = self._bob
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y) + int(math.sin(t * 0.8) * 4)
        r  = self.RADIUS  # 30

        # ── Soul Knight style portal ──────────────────────────
        # 1) Far outer glow (soft teal halo)
        for gr, ga in [(r + 26, 30), (r + 18, 55), (r + 10, 90)]:
            g = pygame.Surface((gr*2+4, gr*2+4), pygame.SRCALPHA)
            pygame.draw.circle(g, (0, 220, 200, ga), (gr+2, gr+2), gr)
            surface.blit(g, (sx - gr - 2, sy - gr - 2))

        # 2) Stone ring frame (dark grey outer band)
        STONE  = (60, 65, 75)
        STONE2 = (90, 95, 110)
        pygame.draw.circle(surface, STONE,  (sx, sy), r + 6)
        pygame.draw.circle(surface, STONE2, (sx, sy), r + 6, 3)

        # 3) Crystal/gem studs on the frame (8 evenly spaced)
        GEM_COL = (0, 230, 210)
        GEM_BRIGHT = (180, 255, 250)
        pulse_sz = 1 + int(math.sin(t * 4) * 0.8)
        for i in range(8):
            a  = t * 0.6 + i * math.pi / 4
            gx = sx + int(math.cos(a) * (r + 4))
            gy = sy + int(math.sin(a) * (r + 4))
            pygame.draw.circle(surface, GEM_COL,   (gx, gy), 4 + pulse_sz)
            pygame.draw.circle(surface, GEM_BRIGHT, (gx, gy), 2)

        # 4) Inner dark vortex background
        pygame.draw.circle(surface, (5, 15, 25), (sx, sy), r + 2)

        # 5) Swirling vortex arcs (Soul Knight spinning lines)
        VORTEX_COLS = [(0, 210, 190), (0, 160, 220), (100, 240, 230)]
        for layer, col in enumerate(VORTEX_COLS):
            arc_r = r - 2 - layer * 6
            if arc_r < 4:
                continue
            arc_surf = pygame.Surface((arc_r*2+4, arc_r*2+4), pygame.SRCALPHA)
            start_a  = int(math.degrees(t * 1.5 + layer * 1.2)) % 360
            arc_col  = (*col, 200 - layer * 40)
            pygame.draw.arc(arc_surf, arc_col,
                            (2, 2, arc_r*2, arc_r*2),
                            math.radians(start_a),
                            math.radians(start_a + 200),
                            3 - layer)
            surface.blit(arc_surf, (sx - arc_r - 2, sy - arc_r - 2))

        # 6) Reverse arc (opposite spin)
        rev_r = r - 10
        if rev_r > 4:
            rev_surf = pygame.Surface((rev_r*2+4, rev_r*2+4), pygame.SRCALPHA)
            ra = int(math.degrees(-t * 2.2)) % 360
            pygame.draw.arc(rev_surf, (180, 255, 245, 160),
                            (2, 2, rev_r*2, rev_r*2),
                            math.radians(ra), math.radians(ra + 150), 2)
            surface.blit(rev_surf, (sx - rev_r - 2, sy - rev_r - 2))

        # 7) Bright centre core (Soul Knight portal heart)
        core_r = 8 + int(math.sin(t * 5) * 2)
        core_g = pygame.Surface((core_r*2+4, core_r*2+4), pygame.SRCALPHA)
        pygame.draw.circle(core_g, (200, 255, 250, 180), (core_r+2, core_r+2), core_r)
        surface.blit(core_g, (sx - core_r - 2, sy - core_r - 2))
        pygame.draw.circle(surface, WHITE, (sx, sy), 3)

        # 8) Floating star particles inside vortex
        import random as _pr
        _pr.seed(int(t * 6))
        for _ in range(5):
            px2 = sx + _pr.randint(-(r-8), r-8)
            py2 = sy + _pr.randint(-(r-8), r-8)
            pr2 = _pr.randint(1, 3)
            pa  = _pr.randint(100, 220)
            ps  = pygame.Surface((pr2*2+2, pr2*2+2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (220, 255, 250, pa), (pr2+1, pr2+1), pr2)
            surface.blit(ps, (px2 - pr2 - 1, py2 - pr2 - 1))

        # 9) Label above
        lbl = _font(13).render("NEXT STAGE", True, (180, 255, 245))
        surface.blit(lbl, (sx - lbl.get_width()//2, sy - r - 26))

        # 10) Pulsing "E" badge
        pulse = int(math.sin(t * 5) * 2)
        bx, by = sx + r + 4, sy - 12
        badge  = pygame.Rect(bx - 2, by - 2, 22 + pulse, 22 + pulse)
        pygame.draw.rect(surface, (5, 20, 25),   badge, border_radius=4)
        pygame.draw.rect(surface, (0, 220, 200), badge, 2, border_radius=4)
        e_s = _font(13).render("E", True, (0, 220, 200))
        surface.blit(e_s, (bx + 3, by + 1))


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

    # ── Frenzy screen border effect ───────────────────────────
    frenzy_active = getattr(player, '_frenzy_timer', 0) > 0
    if frenzy_active:
        ft = player._frenzy_timer
        pulse = abs(math.sin(ft * 8)) * 80
        border_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for bw in range(1, 14):
            alpha = int((14 - bw) * 4 + pulse * 0.3)
            pygame.draw.rect(border_surf, (255, 120, 0, alpha),
                             (bw, bw, SCREEN_W - bw*2, SCREEN_H - bw*2), 2)
        surface.blit(border_surf, (0, 0))
        # Frenzy timer bar at top
        bar_w = int((SCREEN_W - 40) * (ft / 3.0))
        pygame.draw.rect(surface, (80, 30, 0),  (20, 4, SCREEN_W - 40, 8), border_radius=4)
        pygame.draw.rect(surface, (255, 140, 0), (20, 4, bar_w, 8), border_radius=4)
        label = _font(11).render("⚡ FRENZY", True, (255, 200, 80))
        surface.blit(label, (SCREEN_W // 2 - label.get_width() // 2, 14))

    # ── TOP-LEFT: HP / Armor / Mana bars ─────────────────────
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

    # ── BOTTOM HUD strip ──────────────────────────────────────
    hud_y    = SCREEN_H - HUD_H
    hud_rect = pygame.Rect(0, hud_y, SCREEN_W, HUD_H)
    pygame.draw.rect(surface, (12, 12, 22), hud_rect)
    pygame.draw.line(surface, (60, 60, 110), (0, hud_y), (SCREEN_W, hud_y), 2)

    inf_font = _font(14)

    # ── CENTER: 3 skill slots ─────────────────────────────────
    skills     = CLASS_SKILLS.get(player.char_class, [])
    skill_cds  = getattr(player, 'skill_cd', [0.0, 0.0, 0.0])
    SLOT_W, SLOT_H = 58, 58
    SLOT_GAP   = 10
    KEY_LABELS = ["SPC", "F", "R"]
    total_w    = len(skills) * SLOT_W + (len(skills) - 1) * SLOT_GAP
    start_x    = SCREEN_W // 2 - total_w // 2
    slot_y     = hud_y + (HUD_H - SLOT_H) // 2

    for idx, sk in enumerate(skills):
        sx   = start_x + idx * (SLOT_W + SLOT_GAP)
        cd   = skill_cds[idx] if idx < len(skill_cds) else 0
        cdmax = sk.get("cooldown", 5.0)
        ready = (cd <= 0)
        col   = sk.get("color", (100, 180, 255))

        # Is this skill active? (frenzy glow)
        is_active = (sk["type"] == "rapid_fire" and frenzy_active)

        # Slot background
        bg_col   = (int(col[0]*0.18), int(col[1]*0.18), int(col[2]*0.18))
        brd_col  = col if ready else (70, 70, 90)
        if is_active:
            brd_col = (255, 200, 0)

        # Glow when ready
        if ready and not is_active:
            glow = pygame.Surface((SLOT_W + 8, SLOT_H + 8), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*col, 50), (0, 0, SLOT_W + 8, SLOT_H + 8), border_radius=12)
            surface.blit(glow, (sx - 4, slot_y - 4))

        # Active frenzy pulsing glow
        if is_active:
            pulse_a = int(abs(math.sin(pygame.time.get_ticks() / 120)) * 120 + 40)
            glow2 = pygame.Surface((SLOT_W + 16, SLOT_H + 16), pygame.SRCALPHA)
            pygame.draw.rect(glow2, (255, 180, 0, pulse_a), (0, 0, SLOT_W + 16, SLOT_H + 16), border_radius=14)
            surface.blit(glow2, (sx - 8, slot_y - 8))

        pygame.draw.rect(surface, bg_col,  (sx, slot_y, SLOT_W, SLOT_H), border_radius=10)
        pygame.draw.rect(surface, brd_col, (sx, slot_y, SLOT_W, SLOT_H), 2, border_radius=10)

        # Cooldown overlay (fills from bottom)
        if not ready:
            fill_h = int(SLOT_H * (cd / max(0.01, cdmax)))
            ov = pygame.Surface((SLOT_W - 4, max(1, fill_h)), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 160))
            surface.blit(ov, (sx + 2, slot_y + SLOT_H - fill_h))

        # Key label (top-left corner badge)
        key_font_size = 9 if KEY_LABELS[idx] == "SPC" else 11
        key_s = _font(key_font_size).render(KEY_LABELS[idx], True, WHITE)
        surface.blit(key_s, (sx + 4, slot_y + 3))

        # Skill icon emoji / symbol
        icon_map = {"dash": "💨", "star_spread": "★", "rapid_fire": "⚡"}
        icon_txt = icon_map.get(sk["type"], "?")
        icon_s   = _font(20).render(icon_txt, True, col if ready else (120, 120, 140))
        surface.blit(icon_s, (sx + SLOT_W//2 - icon_s.get_width()//2, slot_y + 10))

        # Skill name
        nm_s = _font(9).render(sk["name"][:7], True, col if ready else (120, 120, 140))
        surface.blit(nm_s, (sx + SLOT_W//2 - nm_s.get_width()//2, slot_y + 36))

        # CD countdown or READY
        if not ready:
            cd_s = _font(13).render(f"{cd:.1f}", True, YELLOW)
            surface.blit(cd_s, (sx + SLOT_W//2 - cd_s.get_width()//2, slot_y + SLOT_H - 18))
        else:
            rd_s = _font(8).render("READY", True, (80, 255, 120))
            surface.blit(rd_s, (sx + SLOT_W//2 - rd_s.get_width()//2, slot_y + SLOT_H - 14))

    # ── Pause button (right) ──────────────────────────────────
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

    # ── Right info (above pause) ──────────────────────────────
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