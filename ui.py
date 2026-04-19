"""
ui.py  –  All UI Screens — GRAPHICAL OVERHAUL
==============================================
Visual Enhancements:
  · Impact / Consolas / Verdana font hierarchy (no more plain Arial)
  · Neon-glow panels with glass highlights
  · Neon-style buttons with hover glow effects
  · Animated particle starfield on main menu
  · Gradient-style progress bars with shine
  · Glowing title text layers on main menu
  · Decorative ornaments and dividers
  · Scanline atmospheric overlay
  · Rarity-color glow on item cards in shop/inventory
  · Enhanced game-over / victory screen
  · Better stat readout with monospace numbers
"""
import pygame
import math
import random
import time
from constants import (
    SCREEN_W, SCREEN_H, HUD_H, CLASSES, RARITY_COLORS,
    SHOP_HEAL_COST, SHOP_ITEM_MULT, SHOP_REROLL_COST,
    BLACK, WHITE, GRAY, DARK_GRAY, RED, GREEN, BLUE, CYAN,
    YELLOW, GOLD, PURPLE, ORANGE, LIGHT_GRAY, LIGHT_BLUE,
)
from item import make_weapon, make_armor, make_accessory, make_random_item


# ═══════════════════════════════════════════════════════════════
#  DESIGN TOKENS
# ═══════════════════════════════════════════════════════════════
BG_DARK      = (4,   5,  16)
BG_PANEL     = (9,  11,  26)
BG_PANEL2    = (13, 15,  34)
BG_ITEM      = (14, 16,  36)
NEON_PINK    = (255,  40, 120)
NEON_CYAN    = (0,   210, 255)
NEON_GREEN   = (40,  230, 100)
NEON_ORANGE  = (255, 140,  20)
NEON_PURPLE  = (165,  60, 255)
NEON_GOLD    = (255, 205,  30)
NEON_RED     = (255,  50,  70)
TEXT_PRIMARY = (220, 225, 245)
TEXT_DIM     = (120, 130, 160)
TEXT_MUTED   = (60,  70, 100)
BORDER_DIM   = (28,  34,  62)
BORDER_MED   = (48,  58,  98)

# Saturated rarity glow colours
RARITY_GLOW = {
    "Common":    (150, 160, 190),
    "Rare":      (0,   160, 255),
    "Epic":      (180,  50, 255),
    "Legendary": (255,  190,  0),
}


# ═══════════════════════════════════════════════════════════════
#  FONT SYSTEM
# ═══════════════════════════════════════════════════════════════
_FONT_CACHE: dict = {}

def _font(size: int, style: str = "body") -> pygame.font.Font:
    """
    style: 'title'  → Impact / ArialBlack  (heavy display)
           'mono'   → Consolas / Courier    (numbers/stats)
           'body'   → Verdana / Arial       (readable text)
           'bold'   → Verdana bold
    """
    key = (size, style)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    f = None
    if style == "title":
        for name in ("impact", "arialblack", "arial black", "helvetica"):
            try:
                f = pygame.font.SysFont(name, size, bold=False)
                break
            except Exception:
                pass
        if f is None:
            f = pygame.font.SysFont("arial", size, bold=True)
    elif style == "mono":
        for name in ("consolas", "couriernew", "courier new", "lucidaconsole", "courier"):
            try:
                f = pygame.font.SysFont(name, size)
                break
            except Exception:
                pass
        if f is None:
            f = pygame.font.SysFont("arial", size)
    elif style in ("bold",):
        for name in ("verdana", "tahoma", "calibri", "arial"):
            try:
                f = pygame.font.SysFont(name, size, bold=True)
                break
            except Exception:
                pass
        if f is None:
            f = pygame.font.SysFont("arial", size, bold=True)
    else:  # body
        for name in ("verdana", "tahoma", "calibri", "arial"):
            try:
                f = pygame.font.SysFont(name, size)
                break
            except Exception:
                pass
        if f is None:
            f = pygame.font.SysFont("arial", size)
    _FONT_CACHE[key] = f
    return f


# Backwards-compatible shim used by ShootingRangeScreen (calls F(size, bold))
_fc: dict = {}
def F(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _fc:
        _fc[key] = _font(size, "bold" if bold else "body")
    return _fc[key]


# ═══════════════════════════════════════════════════════════════
#  CORE DRAW HELPERS
# ═══════════════════════════════════════════════════════════════

def draw_text(surf, msg, x, y,
              size=20, color=TEXT_PRIMARY, style="body",
              center=False, shadow=False, glow_col=None):
    """Render text; optional drop-shadow or multi-layer glow."""
    f  = _font(size, style)
    s  = f.render(str(msg), True, color)
    rx = x - s.get_width() // 2 if center else x
    ry = y
    if glow_col:
        for r in (4, 3, 2):
            gs  = f.render(str(msg), True, glow_col)
            tmp = pygame.Surface(gs.get_size(), pygame.SRCALPHA)
            tmp.blit(gs, (0, 0))
            tmp.set_alpha(28 * r)
            for ox, oy in ((-r, 0), (r, 0), (0, -r), (0, r)):
                surf.blit(tmp, (rx + ox, ry + oy))
    elif shadow:
        ss = f.render(str(msg), True, (0, 0, 0))
        surf.blit(ss, (rx + 2, ry + 2))
    surf.blit(s, (rx, ry))
    return s.get_width(), s.get_height()


# Old-style `text()` kept for ShootingRangeScreen compatibility
def text(surf, msg, x, y, size=20, color=WHITE, bold=False, center=False):
    return draw_text(surf, msg, x, y, size=size, color=color,
                     style="bold" if bold else "body", center=center)


def draw_panel(surf, x, y, w, h,
               fill=BG_PANEL, border=BORDER_MED,
               radius=10, glow=False, glow_alpha=45):
    """Panel with glass highlight; optional neon outer glow."""
    if glow and border not in (GRAY, BORDER_MED):
        for i in (5, 3, 2):
            gs = pygame.Surface((w + i * 4, h + i * 4), pygame.SRCALPHA)
            a  = glow_alpha // i
            pygame.draw.rect(gs, (*border, a),
                             (0, 0, w + i*4, h + i*4),
                             border_radius=radius + i * 2)
            surf.blit(gs, (x - i*2, y - i*2))
    pygame.draw.rect(surf, fill, (x, y, w, h), border_radius=radius)
    # Top glass highlight
    gl = pygame.Surface((w - 4, max(2, h // 4)), pygame.SRCALPHA)
    gl.fill((255, 255, 255, 10))
    surf.blit(gl, (x + 2, y + 2))
    pygame.draw.rect(surf, border, (x, y, w, h), 2, border_radius=radius)
    return pygame.Rect(x, y, w, h)


# Old-style `panel()` kept for compatibility
def panel(surf, x, y, w, h, fill=(20, 20, 40), border=BLUE, radius=8):
    return draw_panel(surf, x, y, w, h, fill=fill, border=border, radius=radius)


def draw_button(surf, x, y, w, h, label,
                hover=False, color=BLUE, size=16):
    """Neon-framed button; glows on hover."""
    c2 = (color[0] // 3, color[1] // 3, color[2] // 3)
    c3 = tuple(min(255, c + 40) for c in color)
    if hover:
        fill  = tuple(min(255, c + 20) for c in c2)
        bcol  = c3
        # Outer glow
        for i in (4, 2):
            gs = pygame.Surface((w + i*4, h + i*4), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*bcol, 55 // i),
                             (0, 0, w+i*4, h+i*4), border_radius=8+i)
            surf.blit(gs, (x - i*2, y - i*2))
    else:
        fill = c2
        bcol = color
    r = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surf, fill, r, border_radius=7)
    # Shine stripe
    shine = pygame.Surface((w - 4, max(2, h // 3)), pygame.SRCALPHA)
    shine.fill((255, 255, 255, 22 if hover else 10))
    surf.blit(shine, (x + 2, y + 2))
    pygame.draw.rect(surf, bcol, r, 2, border_radius=7)
    f  = _font(size, "bold")
    s  = f.render(label, True, WHITE)
    sx = x + w // 2 - s.get_width()  // 2
    sy = y + h // 2 - s.get_height() // 2
    if hover:
        sh = f.render(label, True, (0, 0, 0))
        surf.blit(sh, (sx + 1, sy + 1))
    surf.blit(s, (sx, sy))
    return r


# Old-style `button()` kept for compatibility
def button(surf, x, y, w, h, label, hover=False, color=BLUE, size=18):
    return draw_button(surf, x, y, w, h, label, hover=hover, color=color, size=size)


def draw_bar(surf, x, y, w, h, val, maximum,
             color, bg=(12, 12, 28)):
    """Progress bar with shine highlight and edge glow."""
    pygame.draw.rect(surf, bg, (x, y, w, h), border_radius=h // 2)
    pygame.draw.rect(surf, (0, 0, 0), (x+1, y+1, w-2, h//2), border_radius=h//2)
    pct    = max(0.0, min(1.0, val / max(1e-6, maximum)))
    fill_w = max(0, int((w - 4) * pct))
    if fill_w:
        pygame.draw.rect(surf, color,
                         (x+2, y+2, fill_w, h-4),
                         border_radius=(h-4)//2)
        # Shine
        sh = pygame.Surface((fill_w, max(2, (h-4)//3)), pygame.SRCALPHA)
        sh.fill((255, 255, 255, 45))
        surf.blit(sh, (x+2, y+2))
        # Right-edge glow
        if fill_w >= 4:
            eg = pygame.Surface((5, h-4), pygame.SRCALPHA)
            eg.fill((*color, 110))
            surf.blit(eg, (x + 2 + fill_w - 3, y + 2))
    lighter = tuple(min(255, c + 60) for c in color)
    pygame.draw.rect(surf, lighter, (x, y, w, h), 1, border_radius=h//2)


# Old-style `_bar()` for compatibility
def _bar(surf, x, y, w, h, val, maximum, color, bg=(20, 20, 30)):
    draw_bar(surf, x, y, w, h, val, maximum, color, bg=bg)


def _draw_ornament_line(surf, x1, y1, x2, y2,
                        col1=NEON_PINK, col2=NEON_CYAN):
    """Double decorative divider line with diamond ornament."""
    pygame.draw.line(surf, col1, (x1, y1),     (x2, y1),     2)
    pygame.draw.line(surf, col2, (x1, y1 + 4), (x2, y1 + 4), 1)
    cx = (x1 + x2) // 2
    cy = y1 + 2
    pts = [(cx, cy-5), (cx+7, cy+1), (cx, cy+7), (cx-7, cy+1)]
    pygame.draw.polygon(surf, NEON_GOLD, pts)
    pygame.draw.polygon(surf, (255, 255, 255), pts, 1)


def _draw_grid(surf, color=(60, 80, 160), alpha=10, spacing=72):
    """Subtle background perspective grid."""
    w, h = surf.get_width(), surf.get_height()
    vl = pygame.Surface((1, h), pygame.SRCALPHA)
    vl.fill((*color, alpha))
    for gx in range(0, w, spacing):
        surf.blit(vl, (gx, 0))
    hl = pygame.Surface((w, 1), pygame.SRCALPHA)
    hl.fill((*color, alpha))
    for gy in range(0, h, spacing):
        surf.blit(hl, (0, gy))


# ═══════════════════════════════════════════════════════════════
#  PARTICLE STARFIELD (main menu)
# ═══════════════════════════════════════════════════════════════
class _Star:
    __slots__ = ("x", "y", "vx", "vy", "size", "alpha", "color")

    def __init__(self):
        self._spawn(True)

    def _spawn(self, anywhere=False):
        self.x     = random.uniform(0, SCREEN_W)
        self.y     = random.uniform(0, SCREEN_H) if anywhere else SCREEN_H + 4
        self.vx    = random.uniform(-0.25, 0.25)
        self.vy    = random.uniform(-0.85, -0.18)
        self.size  = random.randint(1, 3)
        self.alpha = random.randint(50, 190)
        r = random.random()
        self.color = (
            (185, 195, 225) if r < 0.55 else
            (80, 195, 255) if r < 0.78 else
            (255, 150, 210)
        )

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        if self.y < -6 or self.x < -6 or self.x > SCREEN_W + 6:
            self._spawn()

    def draw(self, surf):
        s = pygame.Surface((self.size * 2 + 2, self.size * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, self.alpha),
                           (self.size + 1, self.size + 1), self.size)
        surf.blit(s, (int(self.x) - self.size, int(self.y) - self.size))


_STARS = [_Star() for _ in range(130)]


def _tick_stars(dt):
    for s in _STARS:
        s.update(dt)


def _draw_stars(surf):
    for s in _STARS:
        s.draw(surf)


# ═══════════════════════════════════════════════════════════════
#  SAUSAGE MAN SPRITE HELPER
# ═══════════════════════════════════════════════════════════════
def _draw_sausage_sprite(surface, cx, cy, t, scale=1.0):
    bcol = (240,  60, 120)
    acol = (150,  15,  55)
    dcol = (255, 185, 205)
    bob  = int(math.sin(t * 4.0) * 2 * scale)
    r    = int(14 * scale)
    # Shadow
    pygame.draw.ellipse(surface, (6, 6, 16),
                        (cx - r, cy + r*2 + bob + 2, r*2, max(4, int(r*0.5))))
    # Legs
    swing = int(math.sin(t * 6) * 4 * scale)
    lr    = int(5 * scale)
    pygame.draw.circle(surface, acol, (cx - int(4*scale), cy + r + bob + int(4*scale) + swing), lr)
    pygame.draw.circle(surface, acol, (cx + int(4*scale), cy + r + bob + int(4*scale) - swing), lr)
    # Body
    pygame.draw.circle(surface, bcol, (cx, cy + bob), r)
    pygame.draw.circle(surface, acol, (cx, cy + bob), r, max(1, int(2*scale)))
    for off in (-int(4*scale), 0, int(4*scale)):
        pygame.draw.line(surface, acol,
                         (cx - r + 2, cy + bob + off),
                         (cx + r - 2, cy + bob + off), max(1, int(scale)))
    # Eyes
    eo = int(4 * scale); er = max(2, int(3*scale))
    pygame.draw.circle(surface, (240, 240, 255), (cx - eo, cy + bob - int(3*scale)), er)
    pygame.draw.circle(surface, (240, 240, 255), (cx + eo, cy + bob - int(3*scale)), er)
    pygame.draw.circle(surface, (20, 20, 40),    (cx - eo, cy + bob - int(3*scale)), max(1, er-1))
    pygame.draw.circle(surface, (20, 20, 40),    (cx + eo, cy + bob - int(3*scale)), max(1, er-1))
    # Gun
    ga  = math.sin(t * 2) * 0.15
    wx  = cx + int(r * math.cos(ga))
    wy  = cy + bob + int(r * 0.3 * math.sin(ga))
    gpts = [(wx, wy-int(2*scale)), (wx+int(16*scale), wy-int(2*scale)),
            (wx+int(16*scale), wy+int(2*scale)), (wx, wy+int(2*scale))]
    pygame.draw.polygon(surface, dcol, gpts)


# ═══════════════════════════════════════════════════════════════
#  MAIN MENU SCREEN
# ═══════════════════════════════════════════════════════════════
class MainMenuScreen:
    def __init__(self, tracker):
        self.tracker  = tracker
        self._t       = 0.0
        self._logo_y  = -100.0
        self.btn_play = self.btn_range = self.btn_stats = self.btn_quit = None

    def draw(self, surface, mouse_pos, dt=0.016):
        self._t += dt
        self._logo_y = min(76.0, self._logo_y + 380 * dt)

        # ── Background ──────────────────────────────────────
        surface.fill(BG_DARK)
        _draw_stars(surface)
        _tick_stars(dt)
        _draw_grid(surface, color=(50, 65, 150), alpha=11, spacing=80)

        # Bottom atmospheric glow
        glow_s = pygame.Surface((SCREEN_W, 120), pygame.SRCALPHA)
        for i in range(60):
            a = int(30 * (1 - i / 60))
            pygame.draw.line(glow_s, (255, 40, 120, a),
                             (0, 120-i), (SCREEN_W, 120-i))
        surface.blit(glow_s, (0, SCREEN_H - 120))

        # Top glow
        tg = pygame.Surface((SCREEN_W, 80), pygame.SRCALPHA)
        for i in range(40):
            a = int(20 * (1 - i / 40))
            pygame.draw.line(tg, (0, 210, 255, a), (0, i), (SCREEN_W, i))
        surface.blit(tg, (0, 0))

        # ── Glowing title ───────────────────────────────────
        pulse  = math.sin(self._t * 2.2) * 0.12 + 0.88
        gc     = tuple(int(c * pulse) for c in NEON_PINK)

        ly = int(self._logo_y)
        draw_text(surface, "SAUSAGE MAN",
                  SCREEN_W // 2, ly, 74, gc,
                  style="title", center=True, glow_col=NEON_PINK)
        draw_text(surface, "LEGENDS  OF  MIDGARD",
                  SCREEN_W // 2, ly + 84, 26, NEON_CYAN,
                  center=True, glow_col=NEON_CYAN)

        # Ornament divider below subtitle
        dw  = 500
        dox = SCREEN_W // 2 - dw // 2
        _draw_ornament_line(surface, dox, ly + 120, dox + dw, ly + 120)

        # ── Menu buttons ─────────────────────────────────────
        bw, bh, bx = 290, 58, SCREEN_W // 2 - 145
        base_y = 215

        def _hover(by):
            return pygame.Rect(bx, by, bw, bh).collidepoint(mouse_pos)

        by0 = base_y
        self.btn_play  = draw_button(surface, bx, by0, bw, bh,
                                     "NEW GAME",        _hover(by0), (30, 200, 80),  size=22)
        by1 = by0 + 72
        self.btn_range = draw_button(surface, bx, by1, bw, bh,
                                     "SHOOTING RANGE",  _hover(by1), (140, 50, 220), size=19)
        by2 = by1 + 72
        self.btn_stats = draw_button(surface, bx, by2, bw, bh,
                                     "STATISTICS",      _hover(by2), (0, 160, 220),  size=19)
        by3 = by2 + 72
        self.btn_quit  = draw_button(surface, bx, by3, bw, bh,
                                     "QUIT",            _hover(by3), (200, 40, 60),  size=19)

        # ── Stats panel ──────────────────────────────────────
        summary = self.tracker.get_summary()
        px, py, pw, ph = SCREEN_W//2 - 230, by3 + 80, 460, 136
        draw_panel(surface, px, py, pw, ph,
                   fill=(6, 8, 20), border=BORDER_MED, radius=12, glow=False)

        if summary.get("total_runs", 0) > 0:
            sy = py + 14
            draw_text(surface, "CAMPAIGN  RECORDS",
                      SCREEN_W//2, sy, 12, NEON_CYAN, style="bold", center=True)
            sy += 22
            pygame.draw.line(surface, BORDER_MED, (px+20, sy), (px+pw-20, sy))
            sy += 10

            left_stats = [
                ("Runs Played",  summary["total_runs"]),
                ("Victories",    summary["victories"]),
                ("Best Score",   f"{summary['best_score']:,}"),
            ]
            right_stats = [
                ("Avg Kills",    summary["avg_kills"]),
                ("Max Level",    summary["max_level"]),
                ("Avg Duration", f"{summary['avg_duration']}s"),
            ]
            half = pw // 2 - 10
            for i, (lbl, val) in enumerate(left_stats):
                lx = px + 18
                draw_text(surface, lbl + ":", lx,         sy + i*24, 12, TEXT_DIM)
                draw_text(surface, str(val),  lx + half - 40, sy + i*24, 12,
                          NEON_GOLD if lbl == "Best Score" else TEXT_PRIMARY, style="mono")
            for i, (lbl, val) in enumerate(right_stats):
                rx = px + pw // 2 + 14
                draw_text(surface, lbl + ":", rx,         sy + i*24, 12, TEXT_DIM)
                draw_text(surface, str(val),  rx + half - 40, sy + i*24, 12,
                          TEXT_PRIMARY, style="mono")
        else:
            draw_text(surface,
                      "No runs recorded — forge your legend!",
                      SCREEN_W//2, py + ph//2 - 8, 15, TEXT_DIM, center=True)

        # Controls bar
        pygame.draw.rect(surface, (6, 8, 20), (0, SCREEN_H-28, SCREEN_W, 28))
        pygame.draw.line(surface, BORDER_DIM, (0, SCREEN_H-28), (SCREEN_W, SCREEN_H-28))
        draw_text(surface,
                  "WASD: Move  |  LClick: Shoot  |  E: Pick Up  |  TAB: Inventory  |  ESC: Pause  |  F11: Fullscreen",
                  SCREEN_W//2, SCREEN_H - 20, 11, TEXT_MUTED, center=True)

    def handle_click(self, pos):
        if self.btn_play  and self.btn_play.collidepoint(pos):  return "play"
        if self.btn_range and self.btn_range.collidepoint(pos): return "range"
        if self.btn_stats and self.btn_stats.collidepoint(pos): return "stats"
        if self.btn_quit  and self.btn_quit.collidepoint(pos):  return "quit"
        return None


# ═══════════════════════════════════════════════════════════════
#  CLASS SELECT SCREEN
# ═══════════════════════════════════════════════════════════════
class ClassSelectScreen:
    def __init__(self):
        self.selected   = "Sausage Man"
        self._anim_t    = 0.0
        self.char_rects = {}
        self.btn_play   = None
        self.btn_back   = None

    def draw(self, surface, mouse_pos, dt=0.016):
        self._anim_t += dt

        surface.fill(BG_DARK)
        _draw_grid(surface, color=(50, 60, 140), alpha=10, spacing=80)

        # Header
        draw_text(surface, "SELECT  CHARACTER",
                  SCREEN_W // 2, 18, 40, NEON_GOLD,
                  style="title", center=True, glow_col=NEON_GOLD)
        _draw_ornament_line(surface, 60, 70, SCREEN_W - 60, 70)

        from constants import CLASSES, CLASS_SKILLS
        cfg   = CLASSES["Sausage Man"]
        skills = CLASS_SKILLS.get("Sausage Man", [])

        # ── Character card ───────────────────────────────────
        cw, ch = 210, 270
        cx = SCREEN_W // 2 - cw // 2
        cy = 88

        pulse = int(55 + 25 * math.sin(self._anim_t * 3.2))
        # Outer glow
        for i in (6, 4, 2):
            gs = pygame.Surface((cw + i*4, ch + i*4), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*NEON_PINK, pulse // i),
                             (0, 0, cw+i*4, ch+i*4), border_radius=12+i)
            surface.blit(gs, (cx - i*2, cy - i*2))

        draw_panel(surface, cx, cy, cw, ch,
                   fill=(30, 8, 18), border=NEON_PINK, radius=12)

        _draw_sausage_sprite(surface, cx + cw // 2, cy + 108,
                             self._anim_t * 2.0, scale=2.2)

        draw_text(surface, "Sausage Man",
                  cx + cw // 2, cy + ch - 76,
                  18, NEON_PINK, style="bold", center=True)
        draw_text(surface, "Any Weapon  ·  Balanced",
                  cx + cw // 2, cy + ch - 50,
                  12, TEXT_DIM, center=True)
        spd_int = min(5, max(1, int(cfg["speed"])))
        pips = "".join("●" if i < spd_int else "○" for i in range(5))
        draw_text(surface, f"SPD  {pips}",
                  cx + cw // 2, cy + ch - 28,
                  12, NEON_GREEN, center=True)

        self.char_rects = {"Sausage Man": pygame.Rect(cx, cy, cw, ch)}

        # ── Detail area ───────────────────────────────────────
        dy = cy + ch + 22
        dh = SCREEN_H - dy - 60

        PREV_W = 200
        prev_x = SCREEN_W // 2 - 450
        stat_x = prev_x + PREV_W + 18
        stat_w = SCREEN_W // 2 + 450 - stat_x

        # Preview panel
        draw_panel(surface, prev_x, dy, PREV_W, dh,
                   fill=(14, 4, 10), border=NEON_PINK, radius=10,
                   glow=True, glow_alpha=30)
        _draw_sausage_sprite(surface,
                             prev_x + PREV_W // 2,
                             dy + dh // 2 - 10,
                             self._anim_t * 2.0, scale=2.9)
        draw_text(surface, "Sausage Man",
                  prev_x + PREV_W // 2, dy + dh - 38,
                  16, NEON_PINK, style="bold", center=True)

        # Stats panel
        draw_panel(surface, stat_x, dy, stat_w, dh,
                   fill=(8, 10, 22), border=BORDER_MED, radius=10)
        sy = dy + 12

        draw_text(surface, cfg["description"], stat_x + 12, sy, 12, TEXT_DIM)
        sy += 22
        pygame.draw.line(surface, BORDER_MED,
                         (stat_x+8, sy), (stat_x+stat_w-8, sy))
        sy += 10

        # Resource bars
        draw_text(surface, "RESOURCES", stat_x+12, sy, 12, NEON_CYAN, style="bold")
        sy += 18
        for lbl, val, maxv, col in [
            ("HP",    cfg["base_hp"],              200, (220, 60, 80)),
            ("Armor", cfg.get("max_armor", 80),    140, NEON_CYAN),
            ("Mana",  cfg.get("max_mana", 130),    200, (60, 100, 255)),
            ("Speed", int(cfg["speed"] * 20),      100, NEON_GREEN),
        ]:
            draw_text(surface, lbl, stat_x+12, sy, 11, col, style="bold")
            bw2 = stat_w - 84
            draw_bar(surface, stat_x+54, sy+2, bw2, 11, val, maxv, col)
            draw_text(surface, str(val), stat_x+58+bw2, sy, 10, col, style="mono")
            sy += 18

        pygame.draw.line(surface, BORDER_MED,
                         (stat_x+8, sy+2), (stat_x+stat_w-8, sy+2))
        sy += 12

        # Starter weapon
        draw_text(surface, "STARTER WEAPON", stat_x+12, sy, 12, NEON_CYAN, style="bold")
        sy += 18
        draw_text(surface, "Hand Pistol", stat_x+12, sy, 13, NEON_GOLD, style="bold")
        sy += 16
        draw_text(surface, "DMG 12  ·  Rate 2.0/s  ·  Single shot",
                  stat_x+12, sy, 11, TEXT_DIM)
        sy += 22

        pygame.draw.line(surface, BORDER_MED,
                         (stat_x+8, sy), (stat_x+stat_w-8, sy))
        sy += 10

        # Passive
        draw_text(surface, "PASSIVE", stat_x+12, sy, 12, NEON_GOLD, style="bold")
        sy += 16
        ptext = cfg.get("passive", "")
        for chunk in [ptext[i:i+46] for i in range(0, len(ptext), 46)]:
            draw_text(surface, chunk, stat_x+12, sy, 11, TEXT_DIM)
            sy += 14

        pygame.draw.line(surface, BORDER_MED,
                         (stat_x+8, sy+2), (stat_x+stat_w-8, sy+2))
        sy += 12

        # Skills
        draw_text(surface, "SKILLS", stat_x+12, sy, 12, NEON_CYAN, style="bold")
        sy += 16
        for skill_cfg in skills[:3]:
            key  = skill_cfg.get("key", "Q")
            sn   = skill_cfg.get("name", "")
            cd   = skill_cfg.get("cooldown", 4)
            mp   = skill_cfg.get("mana_cost", 20)
            desc = skill_cfg.get("description", "")
            # Key badge
            kb = pygame.Rect(stat_x+12, sy, 22, 18)
            pygame.draw.rect(surface, (40, 60, 120), kb, border_radius=3)
            pygame.draw.rect(surface, NEON_CYAN,    kb, 1, border_radius=3)
            draw_text(surface, key, kb.centerx, kb.top + 2, 11, NEON_CYAN,
                      style="mono", center=True)
            draw_text(surface, sn,  stat_x+40, sy,    13, (130, 220, 255), style="bold")
            draw_text(surface, f"CD {int(cd)}s  MP {mp}",
                               stat_x+40, sy+14, 10, NEON_ORANGE)
            sy += 30
            for chunk in [desc[i:i+44] for i in range(0, len(desc), 44)]:
                draw_text(surface, chunk, stat_x+12, sy, 10, TEXT_DIM)
                sy += 13
            sy += 4

        # Bottom buttons
        self.btn_back = draw_button(surface, 30, SCREEN_H-54, 120, 40,
                                    "BACK", False, (80, 80, 100), size=15)
        ph_r = pygame.Rect(SCREEN_W-240, SCREEN_H-54, 210, 40)
        self.btn_play = draw_button(surface, ph_r.x, ph_r.y, ph_r.w, ph_r.h,
                                    "PLAY  -  Sausage Man",
                                    ph_r.collidepoint(mouse_pos),
                                    NEON_GREEN, size=17)
        draw_text(surface,
                  "Q/F/R: Skills  ·  WASD: Move  ·  Click: Shoot  ·  E: Pickup  ·  TAB: Inventory",
                  SCREEN_W//2, SCREEN_H-15, 11, TEXT_MUTED, center=True)

    def handle_click(self, pos):
        for cname, rect in self.char_rects.items():
            if rect.collidepoint(pos):
                self.selected = cname
                return None
        if self.btn_play and self.btn_play.collidepoint(pos):
            return "Sausage Man"
        if self.btn_back and self.btn_back.collidepoint(pos):
            return "back"
        return None


# ═══════════════════════════════════════════════════════════════
#  INVENTORY SCREEN
# ═══════════════════════════════════════════════════════════════
class InventoryScreen:
    def __init__(self):
        self.selected_idx = 0
        self.scroll       = 0

    def draw(self, surface, player, mouse_pos):
        # Dim backdrop
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        surface.blit(overlay, (0, 0))

        W, H = 860, 600
        ox   = SCREEN_W // 2 - W // 2
        oy   = SCREEN_H // 2 - H // 2

        draw_panel(surface, ox, oy, W, H,
                   fill=(8, 10, 22), border=(60, 80, 180), radius=14,
                   glow=True, glow_alpha=30)

        # Title bar
        pygame.draw.rect(surface, (14, 16, 36),
                         (ox, oy, W, 46), border_radius=14)
        pygame.draw.line(surface, (50, 70, 160), (ox, oy+46), (ox+W, oy+46))
        draw_text(surface, "INVENTORY",
                  ox + W // 2, oy + 10, 26, NEON_GOLD,
                  style="title", center=True, glow_col=NEON_GOLD)

        LEFT_W = 540

        # ── Equipment slots ───────────────────────────────────
        draw_text(surface, "EQUIPPED", ox+14, oy+54, 12, NEON_CYAN, style="bold")
        for si, slot in enumerate(("weapon", "armor", "accessory")):
            itm   = player.equipment.get(slot)
            ex    = ox + 14 + si * 176
            ey    = oy + 70
            rcol  = RARITY_GLOW.get(itm.rarity, (130, 140, 170)) if itm else BORDER_MED
            draw_panel(surface, ex, ey, 165, 56,
                       fill=(16, 18, 40), border=rcol, radius=8,
                       glow=bool(itm), glow_alpha=25)
            draw_text(surface, slot.upper(), ex+7, ey+5, 10, TEXT_MUTED)
            draw_text(surface,
                      (itm.name if itm else "— empty —")[:20],
                      ex+7, ey+20, 13,
                      rcol if itm else (60, 70, 100), style="bold")
            if itm:
                if hasattr(itm, "damage"):
                    draw_text(surface, f"DMG {itm.damage}", ex+7, ey+38, 10, TEXT_DIM, style="mono")
                elif hasattr(itm, "defense"):
                    draw_text(surface, f"DEF {itm.defense}", ex+7, ey+38, 10, TEXT_DIM, style="mono")

        pygame.draw.line(surface, BORDER_DIM,
                         (ox+14, oy+136), (ox+LEFT_W-10, oy+136))

        # ── Backpack list ─────────────────────────────────────
        draw_text(surface, f"BACKPACK  ·  {len(player.inventory)} items",
                  ox+14, oy+142, 12, NEON_CYAN, style="bold")
        VISIBLE = 7
        self.item_rects = {}
        self.equip_btns = {}

        for idx in range(VISIBLE):
            real_idx = idx + self.scroll
            if real_idx >= len(player.inventory):
                break
            itm    = player.inventory[real_idx]
            iy     = oy + 162 + idx * 50
            rcol   = RARITY_GLOW.get(itm.rarity, (130, 140, 170))
            is_sel = (real_idx == self.selected_idx)

            can_equip, lock_msg = True, ""
            if hasattr(itm, "can_equip"):
                can_equip, lock_msg = itm.can_equip(player)

            fill = (30, 30, 55) if is_sel else (14, 16, 34)
            if not can_equip:
                fill = (28, 10, 10)
            r = draw_panel(surface, ox+14, iy, LEFT_W-28, 44,
                           fill=fill, border=rcol if is_sel else BORDER_DIM,
                           radius=7, glow=is_sel, glow_alpha=30)
            self.item_rects[real_idx] = r

            # Rarity badge
            badge_col = rcol
            bdr = pygame.Rect(ox+18, iy+12, 18, 18)
            pygame.draw.rect(surface, badge_col, bdr, border_radius=3)
            draw_text(surface, itm.rarity[0],
                      bdr.centerx, bdr.top+2, 11, (0,0,0), style="bold", center=True)

            label = f"{itm.name}" + (f"  {lock_msg}" if not can_equip else "")
            draw_text(surface, label[:44], ox+44, iy+6, 14,
                      (80, 80, 90) if not can_equip else rcol,
                      style="bold" if is_sel else "body")
            draw_text(surface, itm.description[:52], ox+44, iy+26, 10, TEXT_DIM)

            eq_col = NEON_GREEN if can_equip else (50, 50, 60)
            eb = draw_button(surface, ox+LEFT_W-125, iy+8, 76, 27,
                             "EQUIP" if can_equip else "LOCK",
                             pygame.Rect(ox+LEFT_W-125, iy+8, 76, 27).collidepoint(mouse_pos) and can_equip,
                             eq_col, 12)
            self.equip_btns[real_idx] = (eb, can_equip)

            sb = draw_button(surface, ox+LEFT_W-42, iy+8, 30, 27, "$",
                             pygame.Rect(ox+LEFT_W-42, iy+8, 30, 27).collidepoint(mouse_pos),
                             NEON_ORANGE, 13)
            self.item_rects[f"sell_{real_idx}"] = sb

        if len(player.inventory) > VISIBLE:
            draw_text(surface,
                      f"Scroll ↑↓  ({self.scroll+1}–{min(self.scroll+VISIBLE, len(player.inventory))} / {len(player.inventory)})",
                      ox+14, oy+H-28, 11, TEXT_DIM)

        # ── Vertical divider ──────────────────────────────────
        pygame.draw.line(surface, BORDER_MED,
                         (ox+LEFT_W, oy+46), (ox+LEFT_W, oy+H-16))

        # ── RIGHT PANEL: Character ────────────────────────────
        rx = ox + LEFT_W + 16
        rw = W - LEFT_W - 26
        ry = oy + 50

        draw_text(surface, "CHARACTER", rx, ry, 12, NEON_CYAN, style="bold")
        ry += 22

        # Class badge
        draw_panel(surface, rx, ry, rw, 30,
                   fill=(30, 8, 18), border=NEON_PINK, radius=6, glow=True, glow_alpha=20)
        draw_text(surface, "Sausage Man", rx+10, ry+7, 14, NEON_PINK, style="bold")
        draw_text(surface, f"Lv {player.level}", rx+rw-46, ry+9, 12, NEON_GOLD, style="mono")
        ry += 40

        pygame.draw.line(surface, BORDER_DIM, (rx, ry), (rx+rw, ry))
        ry += 10

        # Resource bars
        draw_text(surface, "RESOURCES", rx, ry, 11, TEXT_PRIMARY, style="bold")
        ry += 17
        for lbl, val, maxv, col in [
            ("HP",    player.hp,    player.max_hp,    (220, 60, 80)),
            ("Armor", player.armor, player.max_armor, NEON_CYAN),
            ("Mana",  player.mana,  player.max_mana,  (60, 100, 255)),
        ]:
            draw_text(surface, lbl, rx, ry, 12, col, style="bold")
            draw_bar(surface, rx+52, ry+1, rw-52, 13, val, maxv, col)
            draw_text(surface, f"{int(val)}/{maxv}", rx+54, ry+16, 9, col, style="mono")
            ry += 32

        pygame.draw.line(surface, BORDER_DIM, (rx, ry), (rx+rw, ry))
        ry += 10

        # Weapon stats
        draw_text(surface, "WEAPON", rx, ry, 11, TEXT_PRIMARY, style="bold")
        ry += 17
        wpn = player.weapon
        if wpn:
            wc = RARITY_GLOW.get(wpn.rarity, TEXT_PRIMARY)
            draw_text(surface, wpn.name[:22], rx, ry, 13, wc, style="bold")
            ry += 18
            for lbl, val, col in [
                ("DMG",  wpn.damage,       (220, 80, 80)),
                ("Rate", f"{int(wpn.fire_rate)}/s", TEXT_DIM),
                ("Spd",  wpn.bullet_speed, NEON_CYAN),
            ]:
                draw_text(surface, lbl, rx, ry, 11, TEXT_MUTED)
                draw_text(surface, str(val), rx+48, ry, 12, col, style="mono")
                ry += 17
        else:
            draw_text(surface, "— no weapon —", rx, ry, 12, (60, 70, 100))
            ry += 18

        ry += 4
        pygame.draw.line(surface, BORDER_DIM, (rx, ry), (rx+rw, ry))
        ry += 10

        # Combat stats
        draw_text(surface, "COMBAT", rx, ry, 11, TEXT_PRIMARY, style="bold")
        ry += 17
        for lbl, val, col in [
            ("CRIT",  f"{int(player.crit_chance*100)}%  ×{int(player.crit_mult)}", NEON_GOLD),
            ("DEF",   player.defense,             LIGHT_BLUE),
            ("SPD",   int(player.move_speed),     NEON_GREEN),
            ("Gold",  player.gold,                NEON_GOLD),
        ]:
            draw_text(surface, lbl, rx, ry, 11, TEXT_MUTED)
            draw_text(surface, str(val), rx+48, ry, 12, col, style="mono")
            ry += 17

        pygame.draw.line(surface, BORDER_DIM, (rx, ry+2), (rx+rw, ry+2))
        ry += 12

        # Passive
        draw_text(surface, "PASSIVE", rx, ry, 11, NEON_GOLD, style="bold")
        ry += 15
        ptext = getattr(player, "passive", "")
        line = ""
        for w2 in ptext.split():
            if len(line) + len(w2) + 1 <= 27:
                line += ("" if line == "" else " ") + w2
            else:
                draw_text(surface, line, rx, ry, 10, TEXT_DIM)
                ry += 13
                line = w2
        if line:
            draw_text(surface, line, rx, ry, 10, TEXT_DIM)

        # Close hint
        draw_text(surface, "TAB / ESC  to close",
                  ox + W // 2, oy + H - 18, 12, TEXT_DIM, center=True)

    def handle_click(self, pos, player):
        for idx, (btn, can_equip) in self.equip_btns.items():
            if btn.collidepoint(pos):
                if not can_equip:
                    return "locked"
                itm = player.inventory[idx]
                old = player.equip(itm)
                player.inventory.pop(idx)
                if old:
                    player.inventory.append(old)
                return "equip"

        for key, r in self.item_rects.items():
            if isinstance(key, str) and key.startswith("sell_"):
                if r.collidepoint(pos):
                    idx = int(key.split("_")[1])
                    if idx < len(player.inventory):
                        itm = player.inventory.pop(idx)
                        player.gold += itm.sell_price
                    return "sell"

        for idx, r in self.item_rects.items():
            if isinstance(idx, int) and r.collidepoint(pos):
                self.selected_idx = idx

        return None

    def handle_scroll(self, direction, player):
        max_scroll = max(0, len(player.inventory) - 7)
        self.scroll = max(0, min(self.scroll + direction, max_scroll))


# ═══════════════════════════════════════════════════════════════
#  SHOP SCREEN
# ═══════════════════════════════════════════════════════════════
class ShopScreen:
    def __init__(self, stage_id, char_class="Sausage Man"):
        self.stage_id    = stage_id
        self.char_class  = char_class
        self.reroll_cost = SHOP_REROLL_COST
        self._gen_items(stage_id, char_class)

    def _gen_items(self, stage_id, char_class):
        rarities = ["Common", "Common", "Rare", "Rare", "Epic"]
        if stage_id >= 3:
            rarities = ["Rare", "Rare", "Epic", "Epic", "Legendary"]
        self.shop_items = [
            make_weapon(random.choice(rarities)),
            make_weapon(random.choice(rarities)),
            make_weapon(random.choice(rarities)),
            make_armor(random.choice(rarities)),
            make_accessory(random.choice(rarities)),
        ]
        self.prices = [SHOP_ITEM_MULT.get(i.rarity, 30) for i in self.shop_items]

    def draw(self, surface, player, mouse_pos):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 215))
        surface.blit(overlay, (0, 0))

        W, H = 920, 580
        ox   = SCREEN_W // 2 - W // 2
        oy   = SCREEN_H // 2 - H // 2

        draw_panel(surface, ox, oy, W, H,
                   fill=(6, 16, 8), border=NEON_GREEN, radius=14,
                   glow=True, glow_alpha=25)

        # Title bar
        pygame.draw.rect(surface, (8, 22, 10), (ox, oy, W, 48), border_radius=14)
        pygame.draw.line(surface, (30, 80, 40), (ox, oy+48), (ox+W, oy+48))
        draw_text(surface, "SHOP",
                  ox + W // 2, oy + 10, 28, NEON_GOLD,
                  style="title", center=True, glow_col=NEON_GOLD)
        draw_text(surface, "Stage cleared — spend your gold before continuing.",
                  ox + W // 2, oy + 44, 12, TEXT_DIM, center=True)

        # Gold + HP bar
        draw_text(surface, f"GOLD:  {player.gold} G",
                  ox + 16, oy + 60, 18, NEON_GOLD, style="bold")
        draw_bar(surface, ox+150, oy+63, 200, 13,
                 player.hp, player.max_hp, (220, 60, 80))
        draw_text(surface, f"HP {int(player.hp)}/{player.max_hp}",
                  ox+156, oy+79, 10, (220, 60, 80), style="mono")

        # Reroll button
        can_reroll = player.gold >= self.reroll_cost
        self.btn_reroll = draw_button(
            surface, ox+W-200, oy+58, 184, 36,
            f"REROLL  ({self.reroll_cost}G)",
            pygame.Rect(ox+W-200, oy+58, 184, 36).collidepoint(mouse_pos),
            NEON_GOLD if can_reroll else (60, 60, 70), 14)

        # Heal button
        can_heal = player.gold >= SHOP_HEAL_COST
        self.heal_btn = draw_button(
            surface, ox+16, oy+106, 240, 34,
            f"HEAL  50 HP  ({SHOP_HEAL_COST}G)",
            pygame.Rect(ox+16, oy+106, 240, 34).collidepoint(mouse_pos),
            (200, 40, 60) if can_heal else (60, 60, 70), 14)

        draw_text(surface, "All weapons available — no class restrictions!",
                  ox+274, oy+116, 12, (100, 180, 120))

        pygame.draw.line(surface, (28, 60, 32), (ox+14, oy+148), (ox+W-14, oy+148))

        # Item rows
        self.buy_btns = {}
        for i, itm in enumerate(self.shop_items):
            iy = oy + 156 + i * 76

            if itm is None:
                draw_panel(surface, ox+14, iy, W-28, 64,
                           fill=(10, 12, 14), border=BORDER_DIM, radius=8)
                draw_text(surface, "— SOLD OUT —",
                          ox + W // 2, iy + 24, 16, (60, 70, 80), center=True)
                continue

            rcol = RARITY_GLOW.get(itm.rarity, TEXT_PRIMARY)
            can_use, lock_note = True, ""
            if hasattr(itm, "can_equip"):
                can_use, lock_note = itm.can_equip(player)
                if lock_note:
                    lock_note = "  " + lock_note

            fill_col = (10, 22, 12) if can_use else (22, 10, 10)
            draw_panel(surface, ox+14, iy, W-28, 64,
                       fill=fill_col, border=rcol, radius=8,
                       glow=can_use, glow_alpha=18)

            # Rarity badge
            bdr = pygame.Rect(ox+20, iy+10, 40, 18)
            pygame.draw.rect(surface, rcol, bdr, border_radius=4)
            draw_text(surface, itm.rarity, bdr.centerx, bdr.top+2, 10,
                      (0,0,0), style="bold", center=True)

            name_col = rcol if can_use else (60, 70, 80)
            draw_text(surface,
                      f"{itm.name}{lock_note}",
                      ox+70, iy+6, 17, name_col, style="bold")
            draw_text(surface, itm.description[:72], ox+70, iy+28, 11, TEXT_DIM)

            # Stat chips
            parts = []
            if hasattr(itm, "damage"):       parts.append(f"DMG {itm.damage}")
            if hasattr(itm, "defense"):      parts.append(f"DEF {itm.defense}")
            if hasattr(itm, "fire_rate") and itm.fire_rate > 0:
                parts.append(f"Rate {int(itm.fire_rate)}/s")
            sb = getattr(itm, "stat_bonus", {})
            if sb:
                sb_str = "  ".join(f"+{v} {k}" for k, v in sb.items() if v > 0)
                if sb_str:
                    parts.append(sb_str)
            if parts:
                draw_text(surface, "  ·  ".join(parts[:4]),
                          ox+70, iy+48, 10, NEON_ORANGE, style="mono")

            price   = self.prices[i]
            can_buy = player.gold >= price and can_use
            bb = draw_button(surface, ox+W-168, iy+14, 148, 36,
                             f"BUY  {price} G",
                             pygame.Rect(ox+W-168, iy+14, 148, 36).collidepoint(mouse_pos),
                             NEON_GREEN if can_buy else (50, 60, 50), 15)
            self.buy_btns[i] = (bb, can_use)

        self.btn_leave = draw_button(
            surface, ox+W//2-106, oy+H-50, 212, 40,
            "CONTINUE  →",
            pygame.Rect(ox+W//2-106, oy+H-50, 212, 40).collidepoint(mouse_pos),
            (0, 120, 220), 17)

    def handle_click(self, pos, player):
        if self.heal_btn.collidepoint(pos):
            if player.gold >= SHOP_HEAL_COST:
                player.gold -= SHOP_HEAL_COST
                player.heal(50)
                return "heal"
        if self.btn_reroll.collidepoint(pos):
            if player.gold >= self.reroll_cost:
                player.gold      -= self.reroll_cost
                self.reroll_cost  = int(self.reroll_cost * 1.5)
                self._gen_items(self.stage_id, player.char_class)
                return "reroll"
        for i, (btn, can_use) in self.buy_btns.items():
            if btn.collidepoint(pos):
                price = self.prices[i]
                itm   = self.shop_items[i]
                if itm and can_use and player.gold >= price:
                    player.gold -= price
                    player.collect_item(itm)
                    self.shop_items[i] = None
                    return "buy"
        if self.btn_leave.collidepoint(pos):
            return "leave"
        return None


# ═══════════════════════════════════════════════════════════════
#  PAUSE SCREEN
# ═══════════════════════════════════════════════════════════════
class PauseScreen:
    def draw(self, surface, mouse_pos):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        surface.blit(overlay, (0, 0))

        # Vignette
        vg = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.circle(vg, (0, 0, 0, 0),
                           (SCREEN_W//2, SCREEN_H//2), SCREEN_H//2)
        vg.fill((0, 0, 0, 80), special_flags=pygame.BLEND_RGBA_MIN)
        surface.blit(vg, (0, 0))

        cw, ch = 380, 400
        cx = SCREEN_W // 2 - cw // 2
        cy = SCREEN_H // 2 - ch // 2

        # Outer glow
        for i in (6, 4, 2):
            gs = pygame.Surface((cw+i*4, ch+i*4), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*NEON_CYAN, 20//i if i > 1 else 8),
                             (0, 0, cw+i*4, ch+i*4), border_radius=14+i)
            surface.blit(gs, (cx-i*2, cy-i*2))

        draw_panel(surface, cx, cy, cw, ch,
                   fill=(8, 10, 24), border=(60, 80, 180), radius=14)

        pulse = int(math.sin(time.time() * 3.0) * 5)
        draw_text(surface, "PAUSED",
                  SCREEN_W // 2, cy + 28 + pulse, 40,
                  NEON_GOLD, style="title", center=True, glow_col=NEON_GOLD)

        pygame.draw.line(surface, BORDER_MED,
                         (cx+24, cy+90), (cx+cw-24, cy+90), 2)
        draw_text(surface, "Press  ESC  to resume",
                  SCREEN_W//2, cy+100, 13, TEXT_DIM, center=True)

        bw, bh = 290, 55
        bx2 = SCREEN_W // 2 - bw // 2
        gap  = 72

        by1 = cy + 140
        by2 = by1 + gap
        by3 = by2 + gap

        self.btn_resume  = draw_button(
            surface, bx2, by1, bw, bh, "RESUME",
            pygame.Rect(bx2, by1, bw, bh).collidepoint(mouse_pos),
            (30, 170, 70), 20)

        self.btn_restart = draw_button(
            surface, bx2, by2, bw, bh, "RESTART",
            pygame.Rect(bx2, by2, bw, bh).collidepoint(mouse_pos),
            (180, 100, 20), 20)

        self.btn_menu = draw_button(
            surface, bx2, by3, bw, bh, "EXIT TO MENU",
            pygame.Rect(bx2, by3, bw, bh).collidepoint(mouse_pos),
            (180, 30, 40), 18)

        draw_text(surface, "F11 — Toggle Fullscreen",
                  SCREEN_W//2, cy+ch-28, 12, TEXT_MUTED, center=True)

    def handle_click(self, pos):
        if hasattr(self, "btn_resume")  and self.btn_resume.collidepoint(pos):  return "resume"
        if hasattr(self, "btn_restart") and self.btn_restart.collidepoint(pos): return "restart"
        if hasattr(self, "btn_menu")    and self.btn_menu.collidepoint(pos):    return "menu"
        return None


# ═══════════════════════════════════════════════════════════════
#  GAME OVER / VICTORY SCREEN
# ═══════════════════════════════════════════════════════════════
class GameOverScreen:
    def __init__(self):
        self._t = 0.0

    def draw(self, surface, player, tracker, win=False):
        self._t += 0.016   # approx dt; good enough for animation

        W, H = surface.get_width(), surface.get_height()
        t    = self._t

        # ── Background ───────────────────────────────────────
        if win:
            surface.fill((2, 8, 22))
            # Radial gold shimmer
            for i in range(0, 180, 6):
                a = max(0, int(22 * (1 - i / 180) * (0.7 + 0.3 * math.sin(t * 1.8 + i * 0.05))))
                s = pygame.Surface((W, H), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 200, 30, a),
                                   (W // 2, H // 2), max(1, H // 2 - i * 2))
                surface.blit(s, (0, 0))
        else:
            surface.fill((10, 2, 4))
            # Dark red vignette radiate
            for i in range(0, 120, 5):
                a = max(0, int(18 * (1 - i / 120)))
                s = pygame.Surface((W, H), pygame.SRCALPHA)
                pygame.draw.circle(s, (180, 15, 15, a),
                                   (W // 2, H // 2 + 60), max(1, H // 2 + 60 - i * 3))
                surface.blit(s, (0, 0))

        _draw_stars(surface)
        _draw_grid(surface, color=(40, 30, 80), alpha=7, spacing=90)

        # ── Scanline overlay ─────────────────────────────────
        scan = pygame.Surface((W, H), pygame.SRCALPHA)
        for sy2 in range(0, H, 4):
            scan.fill((0, 0, 0, 18), (0, sy2, W, 1))
        surface.blit(scan, (0, 0))

        # ── Big title ─────────────────────────────────────────
        if win:
            t_label = "VICTORY"
            t_col   = NEON_GOLD
            t_sub   = "The Sausage Man conquers Midgard!"
        else:
            t_label = "GAME OVER"
            t_col   = NEON_RED
            t_sub   = "Your legend ends... for now."

        # Title glow layers
        pulse_a = int(180 + 60 * math.sin(t * 2.5))
        for r2 in (10, 7, 4):
            glayer = _font(80, "title").render(t_label, True, t_col)
            tmp = pygame.Surface(glayer.get_size(), pygame.SRCALPHA)
            tmp.blit(glayer, (0, 0))
            tmp.set_alpha(pulse_a // r2)
            gx = W // 2 - glayer.get_width() // 2
            gy = 52
            surface.blit(tmp, (gx - r2, gy - r2))
            surface.blit(tmp, (gx + r2, gy + r2))
        draw_text(surface, t_label, W // 2, 52, 80, t_col,
                  style="title", center=True)

        # Subtitle
        draw_text(surface, t_sub, W // 2, 148, 18, TEXT_DIM, center=True)

        # Ornament line
        lw = 340
        lx = W // 2 - lw // 2
        ly = 180
        pygame.draw.line(surface, t_col, (lx, ly), (lx + lw, ly), 2)
        pygame.draw.line(surface, NEON_CYAN, (lx, ly + 4), (lx + lw, ly + 4), 1)
        # Diamond centre
        dcx, dcy = W // 2, ly + 2
        dpts = [(dcx, dcy-6), (dcx+8, dcy+1), (dcx, dcy+8), (dcx-8, dcy+1)]
        pygame.draw.polygon(surface, NEON_GOLD, dpts)
        pygame.draw.polygon(surface, WHITE, dpts, 1)

        # ── Stats card ───────────────────────────────────────
        summary = tracker.current_run
        pairs = [
            ("Score",        f"{summary.get('score', 0):,}",         NEON_GOLD),
            ("Level",        player.level,                            NEON_GREEN),
            ("Enemies",      summary.get("enemies_defeated", 0),      (220, 100, 100)),
            ("Total Damage", f"{summary.get('total_damage', 0):,}",   NEON_ORANGE),
            ("Items Found",  summary.get("items_collected", 0),       NEON_CYAN),
            ("Gold Earned",  player.gold,                             NEON_GOLD),
            ("Duration",     f"{summary.get('duration_sec', 0)}s",    TEXT_DIM),
            ("Stage",        f"{summary.get('stage_reached', 1)} / 5", TEXT_PRIMARY),
        ]

        # Two-column layout
        CW, CH = 560, len(pairs) // 2 * 44 + 52
        cpx = W // 2 - CW // 2
        cpy = 200

        # Card background with glow
        if win:
            card_border = NEON_GOLD
        else:
            card_border = NEON_RED
        for gi in (6, 3):
            gs = pygame.Surface((CW + gi * 4, CH + gi * 4), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*card_border, 15),
                             (0, 0, CW + gi * 4, CH + gi * 4), border_radius=16 + gi)
            surface.blit(gs, (cpx - gi * 2, cpy - gi * 2))

        draw_panel(surface, cpx, cpy, CW, CH,
                   fill=(10, 12, 28), border=card_border, radius=14, glow=False)

        # Card header bar
        hdr = pygame.Surface((CW, 36), pygame.SRCALPHA)
        hdr.fill((*card_border, 40))
        surface.blit(hdr, (cpx, cpy))
        pygame.draw.line(surface, card_border, (cpx, cpy + 36), (cpx + CW, cpy + 36), 1)
        draw_text(surface, "RUN  SUMMARY",
                  W // 2, cpy + 8, 16, card_border, style="bold", center=True)

        # Rows — 2 columns
        col_w = CW // 2
        for idx2, (lbl, val, vcol) in enumerate(pairs):
            col     = idx2 % 2
            row     = idx2 // 2
            rx2     = cpx + col * col_w + 18
            ry2     = cpy + 48 + row * 42

            # Row tint alternating
            if row % 2 == 0:
                row_s = pygame.Surface((col_w - 8, 38), pygame.SRCALPHA)
                row_s.fill((255, 255, 255, 5))
                surface.blit(row_s, (rx2 - 10, ry2 - 4))

            draw_text(surface, lbl, rx2, ry2, 13, TEXT_DIM)
            draw_text(surface, str(val), rx2, ry2 + 18, 16, vcol, style="mono")

        # Vertical divider in card
        mid_x = cpx + col_w
        pygame.draw.line(surface, BORDER_DIM,
                         (mid_x, cpy + 40), (mid_x, cpy + CH - 8))

        # ── Buttons ──────────────────────────────────────────
        btn_y  = cpy + CH + 26
        btn_cx = W // 2

        # Restart button
        rw, rh = 200, 50
        self.btn_restart = draw_button(
            surface, btn_cx - rw - 10, btn_y, rw, rh,
            "PLAY AGAIN",
            False,
            (30, 160, 70), 18)

        # Main menu button
        self.btn_menu = draw_button(
            surface, btn_cx + 10, btn_y, rw, rh,
            "MAIN MENU",
            False,
            (0, 100, 200), 18)

        # Keyboard hint
        draw_text(surface, "Click a button above to continue",
                  W // 2, btn_y + rh + 14, 12, TEXT_MUTED, center=True)

    def handle_click(self, pos):
        if hasattr(self, "btn_menu")    and self.btn_menu.collidepoint(pos):    return "menu"
        if hasattr(self, "btn_restart") and self.btn_restart.collidepoint(pos): return "restart"
        return None


# ═══════════════════════════════════════════════════════════════
#  SHOOTING RANGE SCREEN  (logic unchanged; visuals polished)
# ═══════════════════════════════════════════════════════════════
class ShootingRangeScreen:
    RARITY_COLOR = {
        "Common":    (180, 184, 200),
        "Rare":      (100, 180, 255),
        "Epic":      (160, 80,  240),
        "Legendary": (255, 200, 0),
    }
    PANEL_W = 240
    PLAY_W  = SCREEN_W - 240
    PLAY_H  = SCREEN_H - HUD_H

    def __init__(self):
        from item import Weapon
        from constants import WEAPON_POOL
        self._weapon_list = []
        for entry in WEAPON_POOL:
            effect = entry[9] if len(entry) > 9 else None
            w = Weapon(entry[0], entry[1], entry[2], entry[3],
                       entry[4], entry[5], entry[6], "Any", entry[8], effect)
            self._weapon_list.append(w)
        self.player = None
        self._reset()

    def set_player(self, player):
        self.player = player
        if self._weapon_list:
            self.player.equipment["weapon"] = self._weapon_list[self.wpn_idx]
            self.player.shoot_cooldown = 0.0

    def _reset(self):
        import random as _r
        self._rnd        = _r.Random()
        self.wpn_idx     = 0
        self.bullets     = []
        self.floats      = []
        self.burst_left  = 0
        self.burst_timer = 0.0
        self._burst_ang  = 0.0
        self._burst_col  = (255, 230, 80)
        self._burst_sz   = 6
        self._burst_spd  = 7
        self.total_dmg   = self.total_hits = self.total_crits = 0
        self.holding     = False
        self.mouse       = (400, self.PLAY_H // 2)
        self.last_msg    = ""
        self._btn_back   = None
        self._wpn_btns   = []
        self._scroll     = 0.0
        self._scroll_max = 0
        self._shake_timer = 0.0
        self._shake_mag   = 0
        self._dps_log     = []
        self._elapsed     = 0.0
        self._dps_window  = 3.0
        self._current_dps = 0.0
        self._peak_dps    = 0.0
        self.px = 160
        self.py = self.PLAY_H // 2
        self.targets = [
            {"x": self.PLAY_W - 420 + col*90, "y": 160 + row*180,
             "hp": 300, "max_hp": 300, "hit_flash": 0.0, "r": 32}
            for row in range(2) for col in range(4)
        ]

    def _current_weapon(self):
        if self._weapon_list:
            return self._weapon_list[self.wpn_idx]
        return None

    def _spawn(self, angle, col, size, spd, pierce, is_crit=False, dmg=1):
        from bullet import Bullet
        dx = math.cos(angle); dy = math.sin(angle)
        barrel = 32
        bx2 = self.px + dx * barrel
        by2 = self.py + dy * barrel
        b = Bullet(bx2, by2, dx, dy, spd, dmg,
                   pierce=pierce, is_crit=is_crit, color=col, size=size)
        self.bullets.append(b)

    def _shoot(self):
        p   = self.player
        if p is None:
            return
        wpn = self._current_weapon()
        if wpn is None or wpn.is_melee:
            return
        if not p.can_use_mana(wpn.mana_cost):
            return
        p.use_mana(wpn.mana_cost)
        dmg, crit = p.calc_damage()
        p.shoot_cooldown = 1.0 / max(0.1, p.get_fire_rate())

        ang = math.atan2(self.mouse[1] - self.py, self.mouse[0] - self.px)
        fx  = wpn.effect or {}
        col = fx.get("bullet_color", (255, 230, 80))
        sz  = fx.get("bullet_size", 6)
        spd = p.get_bullet_speed() or 7
        pierce = fx.get("pierce", False)
        pat = fx.get("pattern", "single")
        sp = lambda a: a + (self._rnd.random() - 0.5) * 0.22

        if pat in ("single", "pierce"):
            self._spawn(ang, col, sz, spd, pierce or pat == "pierce", crit, dmg)
        elif pat == "double":
            self._spawn(ang+0.09, col, sz, spd, False, crit, dmg)
            self._spawn(ang-0.09, col, sz, spd, False, crit, dmg)
        elif pat == "spread3":
            for i in (-1, 0, 1):
                self._spawn(ang+i*0.20, col, sz, spd, False, crit, dmg)
        elif pat == "spread5":
            for i in range(-2, 3):
                self._spawn(sp(ang+i*0.15), col, sz, spd, False, crit, dmg)
        elif pat == "spread_random":
            self._spawn(sp(ang), col, sz, spd, False, crit, dmg)
        elif pat == "burst3":
            self.burst_left  = 3
            self.burst_timer = 0.0
            self._burst_ang  = ang
            self._burst_col  = col
            self._burst_sz   = sz
            self._burst_spd  = spd
            self._spawn(ang, col, sz, spd, False, crit, dmg)
            self.burst_left -= 1
        elif pat in ("laser", "laser_double"):
            from bullet import LaserBeam
            laser_col   = fx.get("laser_color",   col)
            laser_width = fx.get("laser_width",   3)
            laser_life  = fx.get("laser_lifetime", 0.16)
            laser_range = 1200

            def _fire_range_laser(beam_ang):
                ddx = math.cos(beam_ang); ddy = math.sin(beam_ang)
                ox2 = self.px + ddx * 32
                oy2 = self.py + ddy * 32
                end_x = ox2 + ddx * laser_range
                end_y = oy2 + ddy * laser_range
                blen  = math.hypot(end_x - ox2, end_y - oy2)
                for tgt in self.targets:
                    ex2 = tgt["x"] - ox2; ey2 = tgt["y"] - oy2
                    t_proj = ex2 * ddx + ey2 * ddy
                    if t_proj < 0 or t_proj > blen:
                        continue
                    perp = abs(ex2 * ddy - ey2 * ddx)
                    if perp < tgt["r"] + laser_width + 2:
                        tgt["hit_flash"] = 0.15
                        tgt["hp"] = max(0, tgt["hp"] - dmg)
                        if tgt["hp"] <= 0:
                            tgt["hp"] = tgt["max_hp"]
                        self.total_dmg  += dmg
                        self.total_hits += 1
                        self._dps_log.append([self._elapsed, dmg])
                        label = ("CRIT! " if crit else "") + str(dmg)
                        self.floats.append({
                            "x": tgt["x"] + self._rnd.randint(-20, 20),
                            "y": tgt["y"] - 40, "text": label,
                            "life": 1.0, "crit": crit})
                        wpn_name = wpn.name if wpn else "?"
                        self.last_msg = ("CRITICAL! " if crit else "") + f"Hit {dmg} with {wpn_name}"
                self.bullets.append(LaserBeam(ox2, oy2, end_x, end_y,
                                              color=laser_col,
                                              width=laser_width,
                                              lifetime=laser_life))

            _fire_range_laser(ang)
            if pat == "laser_double":
                _fire_range_laser(ang + 0.09)
                _fire_range_laser(ang - 0.09)

        if wpn and hasattr(wpn, "effect") and wpn.effect:
            sh_mag, sh_dur = wpn.effect.get("shake", (3, 0.10))
            if sh_mag > 0:
                self._shake_timer = max(self._shake_timer, sh_dur)
                self._shake_mag   = max(self._shake_mag,   sh_mag)

        if crit:
            self.total_crits += 1

        wpn2 = self._current_weapon()
        if wpn2:
            shake_mag, shake_dur = (wpn2.effect or {}).get("shake", (3, 0.10))
            self._shake_timer = max(self._shake_timer, shake_dur)
            self._shake_mag   = max(self._shake_mag,   shake_mag)

    def _select_weapon(self, idx):
        self.wpn_idx = idx % len(self._weapon_list)
        if self.player and self._weapon_list:
            self.player.equipment["weapon"] = self._weapon_list[self.wpn_idx]
            self.player.shoot_cooldown = 0.0
        self.burst_left = 0

    def update(self, dt, events, mouse_pos, mouse_buttons):
        p = self.player
        self.mouse = mouse_pos
        mx, my = mouse_pos
        self.holding = bool(mouse_buttons[0] and mx < self.PLAY_W)
        if p is None:
            return
        self._elapsed += dt
        p.mana = min(p.max_mana, p.mana + 18 * dt)
        if p.shoot_cooldown > 0:
            p.shoot_cooldown -= dt
        if self._shake_timer > 0:
            self._shake_timer = max(0.0, self._shake_timer - dt)
        if self.burst_left > 0:
            self.burst_timer -= dt
            if self.burst_timer <= 0:
                self._spawn(self._burst_ang, self._burst_col,
                            self._burst_sz, self._burst_spd, False)
                self.burst_left -= 1
                self.burst_timer = 0.07
        if self.holding and p.shoot_cooldown <= 0 and self.burst_left == 0:
            self._shoot()
        for b in self.bullets:
            b.update(dt, [])
            if b.__class__.__name__ == "LaserBeam":
                continue
            for t in self.targets:
                if id(t) in b.hit_set:
                    continue
                if math.hypot(b.x-t["x"], b.y-t["y"]) < t["r"]+b.radius:
                    if not b.pierce:
                        b.alive = False
                    b.hit_set.add(id(t))
                    t["hit_flash"] = 0.15
                    dmg = b.damage; crit2 = b.is_crit
                    t["hp"] = max(0, t["hp"] - dmg)
                    if t["hp"] <= 0:
                        t["hp"] = t["max_hp"]
                    self.total_dmg  += dmg
                    self.total_hits += 1
                    self._dps_log.append([self._elapsed, dmg])
                    label = ("CRIT! " if crit2 else "") + str(dmg)
                    self.floats.append({
                        "x": t["x"]+self._rnd.randint(-20, 20),
                        "y": t["y"]-40, "text": label,
                        "life": 1.0, "crit": crit2})
                    wpn_n = self._current_weapon().name if self._current_weapon() else "?"
                    self.last_msg = ("CRITICAL! " if crit2 else "") + f"Hit {dmg} with {wpn_n}"
            if b.alive and b.__class__.__name__ != "LaserBeam" and \
               not (0 < b.x < self.PLAY_W and 0 < b.y < self.PLAY_H):
                b.alive = False
        self.bullets = [b for b in self.bullets if b.alive]
        for t in self.targets:
            if t["hit_flash"] > 0:
                t["hit_flash"] -= dt
        self.floats = [f for f in self.floats if f["life"] > 0]
        for f in self.floats:
            f["y"] -= 50*dt; f["life"] -= dt*1.2
        if self._shake_timer > 0:
            self._shake_timer = max(0.0, self._shake_timer - dt)
        cutoff = self._elapsed - self._dps_window
        self._dps_log = [e for e in self._dps_log if e[0] >= cutoff]
        window_actual = min(self._elapsed, self._dps_window)
        if window_actual > 0:
            self._current_dps = sum(e[1] for e in self._dps_log) / window_actual
        else:
            self._current_dps = 0.0
        if self._current_dps > self._peak_dps:
            self._peak_dps = self._current_dps
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_q:
                    self._select_weapon(self.wpn_idx - 1)
                elif ev.key == pygame.K_e:
                    self._select_weapon(self.wpn_idx + 1)

    def handle_click(self, pos):
        if self._btn_back and self._btn_back.collidepoint(pos):
            return "menu"
        for rect, idx in self._wpn_btns:
            if rect.collidepoint(pos):
                self._select_weapon(idx)
        return None

    def handle_scroll(self, y_offset):
        self._scroll = max(0, min(self._scroll_max, self._scroll - y_offset*22))

    def draw(self, surface, mouse_pos):
        p = self.player
        pw = self.PLAY_W

        # Shake offset
        sk_ox = sk_oy = 0
        if self._shake_timer > 0:
            m = int(self._shake_mag * (self._shake_timer / max(0.001, self._shake_mag*0.025+0.08)))
            m = max(1, min(m, self._shake_mag))
            sk_ox = self._rnd.randint(-m, m)
            sk_oy = self._rnd.randint(-m, m)

        # ── Play area surface ─────────────────────────────────
        play_surf = pygame.Surface((pw, self.PLAY_H))
        play_surf.fill((6, 7, 18))
        # Grid
        for gx in range(0, pw, 64):
            pygame.draw.line(play_surf, (16, 18, 36), (gx, 0), (gx, self.PLAY_H))
        for gy in range(0, self.PLAY_H, 64):
            pygame.draw.line(play_surf, (16, 18, 36), (0, gy), (pw, gy))
        pygame.draw.line(play_surf, (40, 50, 90), (pw-1, 0), (pw-1, self.PLAY_H), 2)

        # ── Targets ───────────────────────────────────────────
        for t in self.targets:
            fl = t["hit_flash"] > 0
            tx, ty, r = int(t["x"]), int(t["y"]), t["r"]
            body  = (255, 80, 80) if fl else (190, 45, 45)
            shade = (255, 140, 140) if fl else (230, 90, 90)
            # Shadow
            pygame.draw.ellipse(play_surf, (8, 8, 18),
                                (tx-r, ty+r-4, r*2, max(4, r//2)))
            pygame.draw.circle(play_surf, body,  (tx, ty), r)
            pygame.draw.circle(play_surf, shade, (tx, ty), r, 2)
            for off in (-int(r*0.28), 0, int(r*0.28)):
                pygame.draw.line(play_surf, (150, 25, 25),
                                 (tx-r+3, ty+off), (tx+r-3, ty+off), 1)
            eo = int(r*0.28); er = max(2, int(r*0.18))
            pygame.draw.circle(play_surf, (240, 240, 255), (tx-eo, ty-eo), er)
            pygame.draw.circle(play_surf, (240, 240, 255), (tx+eo, ty-eo), er)
            pygame.draw.circle(play_surf, (20, 20, 40),    (tx-eo, ty-eo), max(1, er-1))
            pygame.draw.circle(play_surf, (20, 20, 40),    (tx+eo, ty-eo), max(1, er-1))
            if fl:
                ov = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(ov, (255, 255, 255, 100), (r, r), r)
                play_surf.blit(ov, (tx-r, ty-r))
            # HP bar
            bw3 = r*2; bx4 = tx-r; by4 = ty+r+6
            pygame.draw.rect(play_surf, (20, 20, 28), (bx4, by4, bw3, 8), border_radius=3)
            hp_w = int(bw3 * t["hp"] / max(1, t["max_hp"]))
            hpc  = ((60,220,60) if t["hp"] > t["max_hp"]*0.5
                    else (220,200,40) if t["hp"] > t["max_hp"]*0.25
                    else (220,60,60))
            if hp_w > 0:
                pygame.draw.rect(play_surf, hpc, (bx4+1, by4+1, hp_w-2, 6), border_radius=2)

        # ── Bullets ───────────────────────────────────────────
        for b in self.bullets:
            b.draw(play_surf, 0, 0)

        # ── Floating damage text ──────────────────────────────
        for f in self.floats:
            alpha = int(255 * max(0.0, f["life"]))
            col   = (255, 220, 0) if f["crit"] else TEXT_PRIMARY
            sz    = 22 if f["crit"] else 15
            fsurf = F(sz, bold=f["crit"]).render(f["text"], True, col)
            ts    = pygame.Surface(fsurf.get_size(), pygame.SRCALPHA)
            ts.blit(fsurf, (0, 0))
            ts.set_alpha(alpha)
            play_surf.blit(ts, (int(f["x"]) - fsurf.get_width()//2, int(f["y"])))

        # ── Player + gun ──────────────────────────────────────
        ang           = math.atan2(self.mouse[1]-self.py, self.mouse[0]-self.px)
        sx, sy        = self.px, self.py
        facing_right  = (self.mouse[0] >= self.px)
        from player import _load_sprite
        import player as _pmod
        _load_sprite()
        _sprite      = _pmod._SPRITE
        _sprite_flip = _pmod._SPRITE_FLIP
        if _sprite is not None:
            sprite = _sprite if facing_right else _sprite_flip
            w2, h2 = sprite.get_size()
            play_surf.blit(sprite, (sx-w2//2, sy-h2//2))
        else:
            pygame.draw.circle(play_surf, NEON_PINK, (sx, sy), 22)
            pygame.draw.circle(play_surf, WHITE,     (sx, sy), 22, 2)
        wpn = self._current_weapon()
        if wpn and p:
            p.facing_angle = ang
            p.facing_right = facing_right
            p._draw_gun(play_surf, sx, sy, 28)

        # ── Blit play area with shake ─────────────────────────
        surface.fill((6, 7, 18), (0, 0, pw, self.PLAY_H))
        surface.blit(play_surf, (sk_ox, sk_oy))

        # ── Top HUD bar ───────────────────────────────────────
        pygame.draw.rect(surface, (8, 10, 24), (0, 0, pw, 56))
        pygame.draw.line(surface, BORDER_MED, (0, 56), (pw, 56))
        if wpn:
            wc = self.RARITY_COLOR.get(wpn.rarity, TEXT_PRIMARY)
            draw_text(surface, wpn.name, 14, 8, 16, wc, style="bold")
            pat = (wpn.effect or {}).get("pattern", "single")
            draw_text(surface,
                      f"DMG {wpn.damage}  ·  RATE {wpn.fire_rate:.2f}/s  ·  MANA {wpn.mana_cost}  ·  [{pat.upper()}]",
                      14, 30, 11, TEXT_DIM)
        # Mana bar (top-right)
        mana_val = p.mana if p else 0
        mana_max = p.max_mana if p else 100
        draw_text(surface, f"MANA  {int(mana_val)}/{int(mana_max)}",
                  pw-218, 10, 11, NEON_CYAN)
        draw_bar(surface, pw-218, 26, 200, 12, mana_val, mana_max, (60, 100, 255))

        # ── Bottom status bar ─────────────────────────────────
        bar_y = self.PLAY_H - 46
        pygame.draw.rect(surface, (8, 10, 24), (0, bar_y, pw, 46))
        pygame.draw.line(surface, BORDER_MED, (0, bar_y), (pw, bar_y))

        dps = self._current_dps
        dps_col = ((255, 80, 80) if dps >= 200
                   else (255, 200, 40) if dps >= 80
                   else NEON_GREEN)
        draw_text(surface, f"DPS  {dps:>7.1f}",  14, bar_y+6,  15, dps_col, style="mono")
        draw_text(surface, f"PEAK {self._peak_dps:>7.1f}", 14, bar_y+26, 11,
                  TEXT_DIM, style="mono")
        draw_text(surface,
                  f"TOTAL {self.total_dmg:,}  ·  HITS {self.total_hits}  ·  CRITS {self.total_crits}",
                  pw//2, bar_y+18, 12, TEXT_DIM, center=True)
        if self.last_msg:
            draw_text(surface, self.last_msg, pw-14, bar_y+18, 12, NEON_GOLD)

        # ── Weapon sidebar ────────────────────────────────────
        poff = pw + 4
        pygame.draw.rect(surface, (7, 8, 20), (pw, 0, self.PANEL_W, self.PLAY_H))
        pygame.draw.line(surface, BORDER_MED, (pw, 0), (pw, self.PLAY_H))

        draw_text(surface, "Q / E  to cycle",
                  poff + self.PANEL_W//2, 8, 10, TEXT_DIM, center=True)
        draw_text(surface, "WEAPONS",
                  poff + self.PANEL_W//2, 22, 14, TEXT_PRIMARY, style="bold", center=True)

        self._btn_back = draw_button(
            surface, poff+8, self.PLAY_H-52, self.PANEL_W-16, 40,
            "EXIT TO MENU",
            pygame.Rect(poff+8, self.PLAY_H-52, self.PANEL_W-16, 40).collidepoint(mouse_pos),
            NEON_RED, 13)

        lt = 46; lb = self.PLAY_H - 60; ih = 56
        vis = (lb - lt) // ih
        self._scroll_max = max(0, (len(self._weapon_list) - vis) * ih)
        self._wpn_btns   = []
        clip = pygame.Rect(poff, lt, self.PANEL_W, lb - lt)
        surface.set_clip(clip)
        for i, wd in enumerate(self._weapon_list):
            wy = lt + i * ih - int(self._scroll)
            if wy + ih < lt or wy > lb:
                continue
            rect = pygame.Rect(poff+4, wy+2, self.PANEL_W-8, ih-4)
            sel  = (i == self.wpn_idx)
            hov  = rect.collidepoint(mouse_pos)
            rc   = self.RARITY_COLOR.get(wd.rarity, TEXT_PRIMARY)
            bg   = (28, 10, 40) if sel else ((18, 18, 34) if hov else (12, 12, 24))
            pygame.draw.rect(surface, bg, rect, border_radius=6)
            if sel:
                # Glow
                gs2 = pygame.Surface((rect.w+4, rect.h+4), pygame.SRCALPHA)
                pygame.draw.rect(gs2, (*rc, 40), (0,0,rect.w+4,rect.h+4), border_radius=8)
                surface.blit(gs2, (rect.x-2, rect.y-2))
            pygame.draw.rect(surface, rc if sel else BORDER_DIM, rect,
                             2 if sel else 1, border_radius=6)
            draw_text(surface, wd.name, poff+12, wy+7, 12, rc,
                      style="bold" if sel else "body")
            draw_text(surface,
                      f"DMG {wd.damage}  |  {wd.fire_rate:.1f}/s",
                      poff+12, wy+24, 10, TEXT_DIM, style="mono")
            # Rarity dot
            dot_col = self.RARITY_COLOR.get(wd.rarity, (130, 140, 170))
            pygame.draw.circle(surface, dot_col, (poff+12, wy+42), 4)
            draw_text(surface, wd.rarity, poff+22, wy+37, 9, dot_col)
            self._wpn_btns.append((rect, i))
        surface.set_clip(None)