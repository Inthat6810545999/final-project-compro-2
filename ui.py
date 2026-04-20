"""
ui.py  –  All UI Screens — DARK FANTASY OVERHAUL
==================================================
Design Language:
  · Dark stone panels with gold rivets and worn edges
  · Blood-red, ash-gold, frost-blue color palette — no neon
  · Rune-etched borders and torch-glow ambience
  · Parchment-style text, carved stone headers
  · Heavy shadows, candle flicker, moonlit fog
  · Every screen feels like a medieval grimoire or dungeon hall
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
#  DARK FANTASY DESIGN TOKENS
# ═══════════════════════════════════════════════════════════════

# Backgrounds — aged stone & deep shadow
BG_VOID      = (8,   6,   5)
BG_STONE     = (18,  15,  12)
BG_STONE2    = (24,  20,  16)
BG_PANEL     = (20,  17,  14)
BG_PANEL2    = (28,  23,  18)
BG_ITEM      = (26,  21,  17)

# Accent colors — restrained, earthy, dramatic
DF_GOLD      = (200, 165,  80)   # worn gold
DF_GOLD_DIM  = (130, 100,  45)   # tarnished gold
DF_BLOOD     = (160,  32,  32)   # dried blood red
DF_BLOOD_B   = (200,  50,  50)   # bright blood
DF_CRIMSON   = (130,  20,  20)   # deep crimson
DF_FROST     = ( 80, 150, 180)   # cold frost blue
DF_FROST_DIM = ( 45,  90, 115)   # dim frost
DF_RUNE      = (180, 120,  50)   # rune amber
DF_RUNE_DIM  = (100,  65,  25)   # dim rune
DF_MOSS      = ( 60, 100,  55)   # dungeon moss green
DF_ASH       = (130, 120, 108)   # ash gray
DF_BONE      = (210, 195, 165)   # bone white
DF_PARCH     = (185, 165, 130)   # parchment text
DF_PARCH_DIM = (120, 105,  82)   # muted parchment

# Borders
BORDER_STONE  = (45,  38,  30)
BORDER_GOLD   = (110,  85,  38)
BORDER_BLOOD  = ( 90,  22,  22)

# Text
TEXT_PRIM  = (210, 195, 165)   # parchment/bone
TEXT_DIM   = (130, 115,  90)   # muted stone
TEXT_MUTED = ( 75,  65,  50)   # very dim

# Rarity — muted, earthy
RARITY_GLOW = {
    "Common":    (150, 140, 125),
    "Rare":      ( 70, 130, 180),
    "Epic":      (130,  65, 170),
    "Legendary": (195, 155,  50),
}


# ═══════════════════════════════════════════════════════════════
#  FONT SYSTEM  (unchanged API)
# ═══════════════════════════════════════════════════════════════
_FONT_CACHE: dict = {}

def _font(size: int, style: str = "body") -> pygame.font.Font:
    key = (size, style)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    f = None
    if style == "title":
        for name in ("impact", "arialblack", "arial black", "helvetica"):
            try: f = pygame.font.SysFont(name, size, bold=False); break
            except Exception: pass
        if f is None: f = pygame.font.SysFont("arial", size, bold=True)
    elif style == "mono":
        for name in ("consolas", "couriernew", "courier new", "courier"):
            try: f = pygame.font.SysFont(name, size); break
            except Exception: pass
        if f is None: f = pygame.font.SysFont("arial", size)
    elif style == "bold":
        for name in ("verdana", "tahoma", "calibri", "arial"):
            try: f = pygame.font.SysFont(name, size, bold=True); break
            except Exception: pass
        if f is None: f = pygame.font.SysFont("arial", size, bold=True)
    else:
        for name in ("verdana", "tahoma", "calibri", "arial"):
            try: f = pygame.font.SysFont(name, size); break
            except Exception: pass
        if f is None: f = pygame.font.SysFont("arial", size)
    _FONT_CACHE[key] = f
    return f

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
              size=20, color=TEXT_PRIM, style="body",
              center=False, shadow=False, glow_col=None):
    f  = _font(size, style)
    s  = f.render(str(msg), True, color)
    rx = x - s.get_width() // 2 if center else x
    ry = y
    if glow_col:
        for r in (4, 3, 2):
            gs  = f.render(str(msg), True, glow_col)
            tmp = pygame.Surface(gs.get_size(), pygame.SRCALPHA)
            tmp.blit(gs, (0, 0))
            tmp.set_alpha(22 * r)
            for ox, oy in ((-r, 0), (r, 0), (0, -r), (0, r)):
                surf.blit(tmp, (rx + ox, ry + oy))
    elif shadow:
        ss = f.render(str(msg), True, (0, 0, 0))
        surf.blit(ss, (rx + 2, ry + 2))
    surf.blit(s, (rx, ry))
    return s.get_width(), s.get_height()

def text(surf, msg, x, y, size=20, color=WHITE, bold=False, center=False):
    return draw_text(surf, msg, x, y, size=size, color=color,
                     style="bold" if bold else "body", center=center)


def draw_panel(surf, x, y, w, h,
               fill=BG_PANEL, border=BORDER_STONE,
               radius=8, glow=False, glow_alpha=30):
    """Stone panel with worn edge, optional amber glow."""
    # Outer shadow
    sh = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
    pygame.draw.rect(sh, (0, 0, 0, 70), (0, 0, w + 6, h + 6), border_radius=radius + 3)
    surf.blit(sh, (x - 3, y + 4))
    # Glow halo
    if glow and border != BORDER_STONE:
        for i in (5, 3):
            gs = pygame.Surface((w + i*4, h + i*4), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*border, glow_alpha // i),
                             (0, 0, w+i*4, h+i*4), border_radius=radius+i)
            surf.blit(gs, (x - i*2, y - i*2))
    pygame.draw.rect(surf, fill, (x, y, w, h), border_radius=radius)
    # Inner top highlight (stone gloss)
    hl = pygame.Surface((w - 4, max(2, h // 5)), pygame.SRCALPHA)
    hl.fill((255, 255, 255, 6))
    surf.blit(hl, (x + 2, y + 2))
    pygame.draw.rect(surf, border, (x, y, w, h), 1, border_radius=radius)
    return pygame.Rect(x, y, w, h)

panel = draw_panel   # legacy alias


def draw_button(surf, x, y, w, h, label, hover=False, color=DF_BLOOD, size=16):
    """Stone-carved button with gold lettering."""
    dark  = tuple(max(0, c - 40) for c in color)
    light = tuple(min(255, c + 30) for c in color)
    fill  = tuple(min(255, c + 15) for c in dark) if hover else dark

    r = pygame.Rect(x, y, w, h)
    # Hover glow
    if hover:
        for i in (4, 2):
            gs = pygame.Surface((w+i*4, h+i*4), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*color, 35 // i), (0,0,w+i*4,h+i*4), border_radius=6+i)
            surf.blit(gs, (x-i*2, y-i*2))
    pygame.draw.rect(surf, fill, r, border_radius=5)
    # Top bevel
    shine = pygame.Surface((w-4, max(2, h//4)), pygame.SRCALPHA)
    shine.fill((255, 255, 255, 14 if hover else 6))
    surf.blit(shine, (x+2, y+2))
    pygame.draw.rect(surf, light if hover else color, r, 1, border_radius=5)
    f   = _font(size, "bold")
    s   = f.render(label, True, DF_BONE if hover else TEXT_PRIM)
    sx  = x + w//2 - s.get_width()//2
    sy  = y + h//2 - s.get_height()//2
    sh2 = f.render(label, True, (0, 0, 0))
    surf.blit(sh2, (sx+1, sy+1))
    surf.blit(s, (sx, sy))
    return r

button = draw_button  # legacy alias


def draw_bar(surf, x, y, w, h, val, maximum,
             color, bg=(10, 8, 6)):
    """Dark fantasy health/resource bar — deep shadow track, solid fill."""
    pygame.draw.rect(surf, bg,          (x, y, w, h), border_radius=h//2)
    pygame.draw.rect(surf, (0, 0, 0),   (x+1, y+1, w-2, h//2), border_radius=h//2)
    pct    = max(0.0, min(1.0, val / max(1e-6, maximum)))
    fill_w = max(0, int((w-4) * pct))
    if fill_w:
        pygame.draw.rect(surf, color, (x+2, y+2, fill_w, h-4), border_radius=(h-4)//2)
        sh = pygame.Surface((fill_w, max(2, (h-4)//3)), pygame.SRCALPHA)
        sh.fill((255, 255, 255, 28))
        surf.blit(sh, (x+2, y+2))
    edge = tuple(min(255, c+50) for c in color)
    pygame.draw.rect(surf, edge, (x, y, w, h), 1, border_radius=h//2)

_bar = draw_bar  # legacy alias


# ── Ornament helpers ──────────────────────────────────────────

def _draw_rune_divider(surf, x1, y, x2,
                       col=DF_GOLD_DIM, col2=DF_RUNE_DIM):
    """Double divider line with rune diamond."""
    pygame.draw.line(surf, col,  (x1, y),   (x2, y),   1)
    pygame.draw.line(surf, col2, (x1, y+3), (x2, y+3), 1)
    cx = (x1+x2)//2; cy = y+1
    pts = [(cx, cy-5),(cx+6, cy+1),(cx, cy+7),(cx-6, cy+1)]
    pygame.draw.polygon(surf, DF_GOLD, pts)
    pygame.draw.polygon(surf, (0,0,0), pts, 1)

_draw_ornament_line = _draw_rune_divider   # legacy alias


def _draw_stone_panel(surf, x, y, w, h,
                      border_col=None, radius=10, glow=False):
    """Deep stone panel with carved rivets."""
    bc = border_col or BORDER_STONE
    # Drop shadow
    sh = pygame.Surface((w+8, h+8), pygame.SRCALPHA)
    pygame.draw.rect(sh, (0,0,0,80), (0,0,w+8,h+8), border_radius=radius+3)
    surf.blit(sh, (x-4, y+5))
    # Glow
    if glow and border_col:
        for gi in (5,3):
            gs = pygame.Surface((w+gi*4,h+gi*4), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*bc, 20//gi),(0,0,w+gi*4,h+gi*4), border_radius=radius+gi)
            surf.blit(gs, (x-gi*2, y-gi*2))
    # Body
    pygame.draw.rect(surf, BG_STONE, (x, y, w, h), border_radius=radius)
    # Stone grain (subtle)
    for gy2 in range(y+12, y+h-4, 22):
        gl = pygame.Surface((w-4,1), pygame.SRCALPHA)
        gl.fill((255,255,255,5))
        surf.blit(gl, (x+2, gy2))
    # Inner bevel top
    bev = pygame.Surface((w-4, max(2,h//6)), pygame.SRCALPHA)
    bev.fill((255,255,255,8))
    surf.blit(bev, (x+2, y+2))
    pygame.draw.rect(surf, bc, (x, y, w, h), 1, border_radius=radius)
    # Corner rivets
    for rx2, ry2 in ((x+10, y+10),(x+w-10, y+10),(x+10, y+h-10),(x+w-10, y+h-10)):
        pygame.draw.circle(surf, BORDER_GOLD, (rx2, ry2), 4)
        pygame.draw.circle(surf, DF_GOLD,     (rx2-1, ry2-1), 2)


def _draw_torch_glow(surf, cx, cy, r_outer, alpha_max=40):
    """Warm torch-light radial glow."""
    gs = pygame.Surface((r_outer*2, r_outer*2), pygame.SRCALPHA)
    for r in range(r_outer, 0, -4):
        a = int(alpha_max * (1 - r/r_outer))
        pygame.draw.circle(gs, (220, 130, 30, a), (r_outer, r_outer), r)
    surf.blit(gs, (cx - r_outer, cy - r_outer))


def _draw_bg_dungeon(surf, t=0.0):
    """Dark dungeon background — stone floor, torch light, fog."""
    W, H = surf.get_width(), surf.get_height()
    surf.fill(BG_VOID)

    # Stone tile grid
    tile = 80
    for gx in range(0, W, tile):
        col = (255, 220, 160, 6) if (gx//tile % 3 == 0) else (255,255,255, 3)
        vl = pygame.Surface((1, H), pygame.SRCALPHA)
        vl.fill(col)
        surf.blit(vl, (gx, 0))
    for gy in range(0, H, tile):
        hl = pygame.Surface((W, 1), pygame.SRCALPHA)
        hl.fill((255,255,255,3))
        surf.blit(hl, (0, gy))

    # Torch glows — corners & edges
    torch_positions = [
        (90, 80), (W-90, 80),
        (90, H-80), (W-90, H-80),
        (W//2, 70),
    ]
    for tx, ty in torch_positions:
        pulse = 0.85 + 0.15 * math.sin(t * 3.2 + tx * 0.02)
        r = int(160 * pulse)
        _draw_torch_glow(surf, tx, ty, r, alpha_max=int(28*pulse))

    # Ground fog (bottom strip)
    fog = pygame.Surface((W, 80), pygame.SRCALPHA)
    for fy in range(80):
        a = int((80-fy)/80 * 30)
        pygame.draw.line(fog, (8, 6, 4, a), (0, fy), (W, fy))
    surf.blit(fog, (0, H-80))

    # Vignette
    vig = pygame.Surface((W, H), pygame.SRCALPHA)
    for edge_w in range(120, 0, -6):
        a = int((120-edge_w) * 0.8)
        pygame.draw.rect(vig, (0,0,0,a),
                         (120-edge_w, 120-edge_w,
                          W-2*(120-edge_w), H-2*(120-edge_w)), edge_w)
    surf.blit(vig, (0,0))


def _draw_df_button(surf, x, y, w, h, label, hover=False,
                    col_type="stone", size=18):
    """
    Dark Fantasy primary button.
    col_type: "stone" | "blood" | "frost" | "gold" | "dark"
    """
    palettes = {
        "stone": (BG_STONE2,    (38,32,26),    BORDER_STONE, DF_ASH),
        "blood": ((70,16,16),   (50,10,10),    BORDER_BLOOD, (220,160,140)),
        "frost": ((18,45,65),   (12,30,48),    DF_FROST_DIM, (160,210,230)),
        "gold":  ((55,42,12),   (38,28,8),     DF_GOLD_DIM,  DF_GOLD),
        "dark":  ((14,12,10),   (8,7,6),       (50,42,34),   TEXT_DIM),
    }
    fill, fill_dk, border, text_col = palettes.get(col_type, palettes["stone"])
    fill_cur = tuple(min(255,c+12) for c in fill) if hover else fill
    r = pygame.Rect(x, y, w, h)
    # Shadow
    sh = pygame.Surface((w+4,h+4), pygame.SRCALPHA)
    pygame.draw.rect(sh, (0,0,0,60),(0,0,w+4,h+4), border_radius=8)
    surf.blit(sh, (x-2, y+3))
    # Hover glow
    if hover:
        for gi in (5,3):
            gs = pygame.Surface((w+gi*4,h+gi*4),pygame.SRCALPHA)
            pygame.draw.rect(gs,(*border,22//gi),(0,0,w+gi*4,h+gi*4),border_radius=9+gi)
            surf.blit(gs,(x-gi*2,y-gi*2))
    # Outer border (carved stone frame)
    pygame.draw.rect(surf, tuple(max(0,c-20) for c in border),
                     (x-2,y-2,w+4,h+4), border_radius=8)
    pygame.draw.rect(surf, fill_cur, r, border_radius=6)
    # Top sheen
    sh2 = pygame.Surface((w-4,h//4), pygame.SRCALPHA)
    sh2.fill((255,255,255, 18 if hover else 8))
    surf.blit(sh2, (x+2,y+2))
    # Bottom shadow strip
    bs = pygame.Surface((w-4,h//5), pygame.SRCALPHA)
    bs.fill((*fill_dk, 80))
    surf.blit(bs, (x+2, y+h-h//5-2))
    # Side rivets
    for rx3, ry3 in ((x+9, y+h//2),(x+w-9, y+h//2)):
        pygame.draw.circle(surf, tuple(max(0,c-20) for c in border), (rx3,ry3), 3)
        pygame.draw.circle(surf, DF_GOLD, (rx3,ry3), 1)
    pygame.draw.rect(surf, border, r, 1, border_radius=6)
    # Label
    f  = _font(size, "bold")
    s  = f.render(label, True, text_col if hover else TEXT_PRIM)
    sx = x+w//2-s.get_width()//2
    sy = y+h//2-s.get_height()//2
    sh3 = f.render(label, True, (0,0,0))
    surf.blit(sh3,(sx+1,sy+2))
    surf.blit(s,  (sx, sy))
    return r


# Legacy aliases used throughout
def _draw_forest_button(surf, x, y, w, h, label, hover=False, col_type="green", size=18):
    type_map = {"green":"frost","amber":"gold","red":"blood","stone":"stone","blue":"frost","wood":"stone"}
    return _draw_df_button(surf, x, y, w, h, label, hover, type_map.get(col_type,"stone"), size)

def _draw_palia_button(surf, x, y, w, h, label, hover=False, col_type="green", size=18):
    return _draw_forest_button(surf, x, y, w, h, label, hover, col_type, size)

def _draw_palia_panel(surf, x, y, w, h, radius=12, glow_col=None):
    _draw_stone_panel(surf, x, y, w, h, border_col=glow_col or BORDER_GOLD, radius=radius, glow=bool(glow_col))


def _draw_banner_deco(surf, x1, y, x2, color=None):
    _draw_rune_divider(surf, x1, y, x2, col=color or DF_GOLD_DIM)

def _draw_leaf_deco(surf, cx, cy, t=0.0, count=6, radius=16, color=None):
    """Rune glyph circle decoration (replaces Palia leaves)."""
    color = color or DF_RUNE_DIM
    for i in range(count):
        a = math.tau * i / count + t * 0.4
        lx = cx + int(math.cos(a) * radius)
        ly = cy + int(math.sin(a) * radius)
        pygame.draw.rect(surf, color, (lx-3, ly-3, 6, 6), border_radius=1)
    pygame.draw.circle(surf, DF_GOLD_DIM, (cx, cy), 4)

def _draw_vine_deco(surf, x, y, length, vertical=True, color=None):
    color = color or BORDER_STONE
    pts = []
    for i in range(length//8+1):
        off = int(math.sin(i*1.2)*3)
        if vertical: pts.append((x+off, y+i*8))
        else:        pts.append((x+i*8, y+off))
    if len(pts)>=2:
        pygame.draw.lines(surf, color, False, pts, 1)

def _draw_grid(surf, color=(40,32,24), alpha=8, spacing=80):
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
#  EMBER / ASH PARTICLES  (replace petals)
# ═══════════════════════════════════════════════════════════════
class _Ember:
    __slots__ = ("x","y","vx","vy","life","max_life","size","color")
    _COLORS = [
        (220,120,30),(200,160,40),(180,80,20),(160,50,15),(255,200,80)
    ]
    def __init__(self):
        self._spawn(anywhere=True)
    def _spawn(self, anywhere=False):
        self.x     = random.uniform(0, SCREEN_W)
        self.y     = (random.uniform(0, SCREEN_H) if anywhere
                      else random.uniform(SCREEN_H-20, SCREEN_H))
        self.vx    = random.uniform(-0.6, 0.6)
        self.vy    = random.uniform(-1.5, -0.4)
        ml         = random.uniform(2.5, 6.0)
        self.max_life = ml
        self.life  = ml if anywhere else ml
        self.size  = random.randint(1, 3)
        self.color = random.choice(self._COLORS)
    def update(self, dt):
        self.x += self.vx + math.sin(self.life*2)*0.3
        self.y += self.vy
        self.life -= dt
        if self.life <= 0 or self.y < -10:
            self._spawn()
    def draw(self, surf):
        alpha = int(200 * max(0, self.life/self.max_life))
        ps = pygame.Surface((self.size*2+2,self.size*2+2), pygame.SRCALPHA)
        pygame.draw.circle(ps, (*self.color, alpha), (self.size+1,self.size+1), self.size)
        surf.blit(ps, (int(self.x)-self.size-1, int(self.y)-self.size-1))

_EMBERS = [_Ember() for _ in range(35)]

def _tick_petals(dt):
    for e in _EMBERS:
        e.update(dt)
def _draw_petals(surf):
    for e in _EMBERS:
        e.draw(surf)

_tick_stars     = _tick_petals
_draw_stars     = _draw_petals
_tick_fireflies = _tick_petals
_draw_fireflies = _draw_petals


# ═══════════════════════════════════════════════════════════════
#  SAUSAGE MAN SPRITE HELPER  (unchanged)
# ═══════════════════════════════════════════════════════════════
def _draw_sausage_sprite(surface, cx, cy, t, scale=1.0):
    bcol = (200, 50, 90)
    acol = (120, 15, 45)
    dcol = (230, 160, 175)
    bob  = int(math.sin(t*4.0)*2*scale)
    r    = int(14*scale)
    pygame.draw.ellipse(surface, (0,0,0),
                        (cx-r, cy+r*2+bob+2, r*2, max(4,int(r*0.5))))
    swing = int(math.sin(t*6)*4*scale)
    lr    = int(5*scale)
    pygame.draw.circle(surface, acol, (cx-int(4*scale), cy+r+bob+int(4*scale)+swing), lr)
    pygame.draw.circle(surface, acol, (cx+int(4*scale), cy+r+bob+int(4*scale)-swing), lr)
    pygame.draw.circle(surface, bcol, (cx, cy+bob), r)
    pygame.draw.circle(surface, acol, (cx, cy+bob), r, max(1,int(2*scale)))
    for off in (-int(4*scale), 0, int(4*scale)):
        pygame.draw.line(surface, acol,
                         (cx-r+2, cy+bob+off),(cx+r-2, cy+bob+off), max(1,int(scale)))
    eo = int(4*scale); er = max(2,int(3*scale))
    pygame.draw.circle(surface, (220,215,200), (cx-eo, cy+bob-int(3*scale)), er)
    pygame.draw.circle(surface, (220,215,200), (cx+eo, cy+bob-int(3*scale)), er)
    pygame.draw.circle(surface, (20,16,12),    (cx-eo, cy+bob-int(3*scale)), max(1,er-1))
    pygame.draw.circle(surface, (20,16,12),    (cx+eo, cy+bob-int(3*scale)), max(1,er-1))
    ga  = math.sin(t*2)*0.15
    wx  = cx+int(r*math.cos(ga))
    wy  = cy+bob+int(r*0.3*math.sin(ga))
    gpts = [(wx,wy-int(2*scale)),(wx+int(16*scale),wy-int(2*scale)),
            (wx+int(16*scale),wy+int(2*scale)),(wx,wy+int(2*scale))]
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
        self._logo_y = min(52.0, self._logo_y + 320*dt)
        t = self._t

        # Background dungeon
        _draw_bg_dungeon(surface, t)
        _tick_petals(dt)
        _draw_petals(surface)

        # Moonlight shaft from upper centre
        ray_s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for ray_i in range(-2, 3):
            base = math.radians(90 + ray_i*5)
            pulse= 0.7+0.3*math.sin(t*0.9+ray_i)
            a    = max(0, int(12*pulse - abs(ray_i)*3))
            if a:
                pts = [(SCREEN_W//2+int(math.cos(base-0.04)*10), 0),
                       (SCREEN_W//2+int(math.cos(base+0.04)*10), 0),
                       (SCREEN_W//2+int(math.cos(base+0.04)*SCREEN_W), SCREEN_H),
                       (SCREEN_W//2+int(math.cos(base-0.04)*SCREEN_W), SCREEN_H)]
                pygame.draw.polygon(ray_s, (200,200,255,a), pts)
        surface.blit(ray_s, (0,0))

        # Title
        ly = int(self._logo_y)
        pulse_t = 0.94+0.06*math.sin(t*1.5)
        # Carved shadow
        ts_sh = _font(82,"title").render("SAUSAGE MAN", True, (0,0,0))
        surface.blit(ts_sh, (SCREEN_W//2 - ts_sh.get_width()//2+3, ly+5))
        # Gold outline
        for ox2,oy2 in ((-2,-2),(2,2),(-2,2),(2,-2)):
            draw_text(surface, "SAUSAGE MAN",
                      SCREEN_W//2+ox2, ly+oy2, 82, DF_GOLD_DIM,
                      style="title", center=True)
        # Main title
        draw_text(surface, "SAUSAGE MAN",
                  SCREEN_W//2, ly, 82, DF_BONE,
                  style="title", center=True)
        draw_text(surface, "LEGENDS  OF  MIDGARD",
                  SCREEN_W//2, ly+98, 20, DF_GOLD_DIM, center=True)

        _draw_rune_divider(surface, SCREEN_W//2-220, ly+128, SCREEN_W//2+220)

        # Buttons
        bw, bh, bx = 310, 60, SCREEN_W//2-155
        base_y = 230

        def _hov(by):
            return pygame.Rect(bx, by, bw, bh).collidepoint(mouse_pos)

        by0 = base_y
        self.btn_play  = _draw_df_button(surface, bx, by0, bw, bh,
                                          "NEW GAME", _hov(by0), "blood", 22)
        by1 = by0+74
        self.btn_range = _draw_df_button(surface, bx, by1, bw, bh,
                                          "SHOOTING RANGE", _hov(by1), "frost", 18)
        by2 = by1+74
        self.btn_stats = _draw_df_button(surface, bx, by2, bw, bh,
                                          "STATISTICS", _hov(by2), "stone", 18)
        by3 = by2+74
        self.btn_quit  = _draw_df_button(surface, bx, by3, bw, bh,
                                          "QUIT", _hov(by3), "dark", 18)

        # Records panel
        summary = self.tracker.get_summary()
        px2,py2,pw2,ph2 = SCREEN_W//2-240, by3+80, 480, 120
        _draw_stone_panel(surface, px2, py2, pw2, ph2,
                          border_col=BORDER_GOLD, radius=10)
        _draw_leaf_deco(surface, px2+14, py2+14, t, 4, 10, DF_RUNE_DIM)
        _draw_leaf_deco(surface, px2+pw2-14, py2+14, t, 4, 10, DF_GOLD_DIM)

        if summary.get("total_runs",0) > 0:
            sy2 = py2+10
            draw_text(surface, "CAMPAIGN  RECORDS",
                      SCREEN_W//2, sy2, 12, DF_GOLD, style="bold", center=True)
            sy2 += 22
            _draw_rune_divider(surface, px2+20, sy2, px2+pw2-20)
            sy2 += 14
            half2 = pw2//2-12
            left_s  = [("Runs Played", summary["total_runs"]),
                       ("Victories",   summary["victories"]),
                       ("Best Score",  f"{summary['best_score']:,}")]
            right_s = [("Avg Kills",    summary["avg_kills"]),
                       ("Max Level",    summary["max_level"]),
                       ("Avg Duration", f"{summary['avg_duration']}s")]
            for i,(lbl,val) in enumerate(left_s):
                draw_text(surface, lbl+":", px2+22, sy2+i*24, 11, TEXT_DIM)
                draw_text(surface, str(val), px2+half2-20, sy2+i*24, 12,
                          DF_GOLD if lbl=="Best Score" else TEXT_PRIM, style="mono")
            for i,(lbl,val) in enumerate(right_s):
                rx2 = px2+pw2//2+14
                draw_text(surface, lbl+":", rx2, sy2+i*24, 11, TEXT_DIM)
                draw_text(surface, str(val), rx2+half2-32, sy2+i*24, 12,
                          TEXT_PRIM, style="mono")
        else:
            draw_text(surface, "No runs yet — begin your journey.",
                      SCREEN_W//2, py2+ph2//2-6, 13, TEXT_DIM, center=True)

        # Bottom bar
        pygame.draw.rect(surface, (12,10,8), (0, SCREEN_H-24, SCREEN_W, 24))
        pygame.draw.line(surface, BORDER_GOLD, (0,SCREEN_H-24),(SCREEN_W,SCREEN_H-24),1)
        draw_text(surface,
                  "WASD: Move  |  LClick: Shoot  |  E: Pick Up  |  TAB: Inventory  |  ESC: Pause  |  M: Mute",
                  SCREEN_W//2, SCREEN_H-14, 11, TEXT_MUTED, center=True)

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
        t = self._anim_t

        _draw_bg_dungeon(surface, t)
        _draw_grid(surface, color=(40,32,24), alpha=6, spacing=80)

        draw_text(surface, "SELECT  CHARACTER",
                  SCREEN_W//2, 16, 38, DF_BONE,
                  style="title", center=True, shadow=True)
        _draw_rune_divider(surface, 60, 66, SCREEN_W-60)

        from constants import CLASSES, CLASS_SKILLS
        cfg    = CLASSES["Sausage Man"]
        skills = CLASS_SKILLS.get("Sausage Man", [])

        cw, ch = 210, 265
        cx = SCREEN_W//2 - cw//2
        cy = 84

        pulse = int(40+18*math.sin(t*2.8))
        for i in (6,4,2):
            gs = pygame.Surface((cw+i*4,ch+i*4), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*DF_BLOOD,pulse//i),(0,0,cw+i*4,ch+i*4),border_radius=12+i)
            surface.blit(gs,(cx-i*2,cy-i*2))

        _draw_stone_panel(surface,cx,cy,cw,ch,border_col=DF_BLOOD,radius=12)
        _draw_sausage_sprite(surface, cx+cw//2, cy+105, t*2.0, scale=2.2)

        draw_text(surface, "Sausage Man",
                  cx+cw//2, cy+ch-72, 17, DF_BONE, style="bold", center=True)
        draw_text(surface, "Any Weapon  ·  Balanced",
                  cx+cw//2, cy+ch-50, 11, TEXT_DIM, center=True)
        spd_int = min(5, max(1, int(cfg["speed"])))
        pips = "".join("◆" if i<spd_int else "◇" for i in range(5))
        draw_text(surface, f"SPD  {pips}",
                  cx+cw//2, cy+ch-28, 11, DF_FROST, center=True)

        self.char_rects = {"Sausage Man": pygame.Rect(cx,cy,cw,ch)}

        dy = cy+ch+18
        dh = SCREEN_H - dy - 58

        PREV_W = 200
        prev_x = SCREEN_W//2 - 450
        stat_x = prev_x+PREV_W+16
        stat_w = SCREEN_W//2+450 - stat_x

        _draw_stone_panel(surface, prev_x, dy, PREV_W, dh,
                          border_col=DF_BLOOD, radius=10, glow=True)
        _draw_sausage_sprite(surface, prev_x+PREV_W//2, dy+dh//2-10,
                             t*2.0, scale=2.9)
        draw_text(surface, "Sausage Man",
                  prev_x+PREV_W//2, dy+dh-36, 15, DF_BONE, style="bold", center=True)

        _draw_stone_panel(surface, stat_x, dy, stat_w, dh,
                          border_col=BORDER_STONE, radius=10)
        sy = dy+12

        draw_text(surface, cfg["description"], stat_x+12, sy, 11, TEXT_DIM)
        sy += 20
        _draw_rune_divider(surface, stat_x+8, sy, stat_x+stat_w-8)
        sy += 12

        draw_text(surface, "RESOURCES", stat_x+12, sy, 11, DF_GOLD, style="bold")
        sy += 18
        for lbl,val,maxv,col in [
            ("HP",    cfg["base_hp"],            200, DF_BLOOD_B),
            ("Armor", cfg.get("max_armor",80),   140, DF_ASH),
            ("Mana",  cfg.get("max_mana",130),   200, DF_FROST),
            ("Speed", int(cfg["speed"]*20),      100, DF_MOSS),
        ]:
            draw_text(surface, lbl, stat_x+12, sy, 10, col, style="bold")
            bw2 = stat_w-84
            draw_bar(surface, stat_x+54, sy+2, bw2, 10, val, maxv, col)
            draw_text(surface, str(val), stat_x+58+bw2, sy, 9, col, style="mono")
            sy += 17

        _draw_rune_divider(surface, stat_x+8, sy+2, stat_x+stat_w-8)
        sy += 12

        draw_text(surface, "STARTER WEAPON", stat_x+12, sy, 11, DF_GOLD, style="bold")
        sy += 17
        draw_text(surface, "Hand Pistol", stat_x+12, sy, 13, DF_BONE, style="bold")
        sy += 15
        draw_text(surface, "DMG 12  ·  Rate 2.0/s  ·  Single shot",
                  stat_x+12, sy, 10, TEXT_DIM)
        sy += 20
        _draw_rune_divider(surface, stat_x+8, sy, stat_x+stat_w-8)
        sy += 12

        draw_text(surface, "PASSIVE", stat_x+12, sy, 11, DF_GOLD, style="bold")
        sy += 15
        ptext = cfg.get("passive","")
        for chunk in [ptext[i:i+46] for i in range(0,len(ptext),46)]:
            draw_text(surface, chunk, stat_x+12, sy, 10, TEXT_DIM)
            sy += 13

        _draw_rune_divider(surface, stat_x+8, sy+2, stat_x+stat_w-8)
        sy += 12

        draw_text(surface, "SKILLS", stat_x+12, sy, 11, DF_FROST, style="bold")
        sy += 15
        for skill_cfg in skills[:3]:
            key  = skill_cfg.get("key","Q")
            sn   = skill_cfg.get("name","")
            cd   = skill_cfg.get("cooldown",4)
            mp   = skill_cfg.get("mana_cost",20)
            desc = skill_cfg.get("description","")
            kb = pygame.Rect(stat_x+12, sy, 20, 17)
            pygame.draw.rect(surface, (30,25,18), kb, border_radius=3)
            pygame.draw.rect(surface, BORDER_GOLD, kb, 1, border_radius=3)
            draw_text(surface, key, kb.centerx, kb.top+2, 10, DF_GOLD,
                      style="mono", center=True)
            draw_text(surface, sn,  stat_x+38, sy, 12, DF_BONE, style="bold")
            draw_text(surface, f"CD {int(cd)}s  MP {mp}",
                               stat_x+38, sy+14, 9, DF_RUNE)
            sy += 28
            for chunk in [desc[i:i+44] for i in range(0,len(desc),44)]:
                draw_text(surface, chunk, stat_x+12, sy, 9, TEXT_DIM)
                sy += 12
            sy += 4

        self.btn_back = _draw_df_button(surface, 30, SCREEN_H-52, 120, 38,
                                        "BACK", False, "stone", 14)
        ph_r = pygame.Rect(SCREEN_W-244, SCREEN_H-52, 214, 38)
        self.btn_play = _draw_df_button(surface, ph_r.x, ph_r.y, ph_r.w, ph_r.h,
                                        "PLAY  —  Sausage Man",
                                        ph_r.collidepoint(mouse_pos),
                                        "blood", 16)
        draw_text(surface,
                  "Q/F/R: Skills  ·  WASD: Move  ·  Click: Shoot  ·  E: Pickup  ·  TAB: Inventory",
                  SCREEN_W//2, SCREEN_H-14, 10, TEXT_MUTED, center=True)

    def handle_click(self, pos):
        for cname,rect in self.char_rects.items():
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
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0,0,0,220))
        surface.blit(overlay, (0,0))

        W, H = 860, 600
        ox   = SCREEN_W//2 - W//2
        oy   = SCREEN_H//2 - H//2

        _draw_stone_panel(surface, ox, oy, W, H,
                          border_col=BORDER_GOLD, radius=12, glow=True)

        # Title bar
        pygame.draw.rect(surface, (14,11,9), (ox,oy,W,46), border_radius=12)
        _draw_rune_divider(surface, ox, oy+46, ox+W)
        draw_text(surface, "INVENTORY",
                  ox+W//2, oy+10, 24, DF_GOLD,
                  style="title", center=True, shadow=True)

        LEFT_W = 540

        # Equipment slots
        draw_text(surface, "EQUIPPED", ox+14, oy+54, 11, DF_GOLD_DIM, style="bold")
        for si, slot in enumerate(("weapon","armor","accessory")):
            itm   = player.equipment.get(slot)
            ex    = ox+14+si*176
            ey    = oy+70
            rcol  = RARITY_GLOW.get(itm.rarity,(130,120,100)) if itm else BORDER_STONE
            draw_panel(surface, ex, ey, 165, 54,
                       fill=BG_PANEL2, border=rcol, radius=7,
                       glow=bool(itm), glow_alpha=22)
            draw_text(surface, slot.upper(), ex+7, ey+4, 9, TEXT_MUTED)
            draw_text(surface, (itm.name if itm else "— empty —")[:20],
                      ex+7, ey+18, 12,
                      rcol if itm else (55,48,38), style="bold")
            if itm:
                if hasattr(itm,"damage"):
                    draw_text(surface, f"DMG {itm.damage}", ex+7, ey+36, 9, TEXT_DIM, style="mono")
                elif hasattr(itm,"defense"):
                    draw_text(surface, f"DEF {itm.defense}", ex+7, ey+36, 9, TEXT_DIM, style="mono")

        _draw_rune_divider(surface, ox+14, oy+133, ox+LEFT_W-10)

        # Backpack list
        draw_text(surface, f"BACKPACK  ·  {len(player.inventory)} items",
                  ox+14, oy+140, 11, DF_GOLD_DIM, style="bold")
        VISIBLE = 7
        self.item_rects = {}
        self.equip_btns = {}

        for idx in range(VISIBLE):
            real_idx = idx + self.scroll
            if real_idx >= len(player.inventory):
                break
            itm    = player.inventory[real_idx]
            iy     = oy+158 + idx*50
            rcol   = RARITY_GLOW.get(itm.rarity,(130,120,100))
            is_sel = (real_idx == self.selected_idx)

            can_equip, lock_msg = True, ""
            if hasattr(itm,"can_equip"):
                can_equip, lock_msg = itm.can_equip(player)

            fill = (32,26,20) if is_sel else (22,18,14)
            if not can_equip: fill = (30,10,10)
            r = draw_panel(surface, ox+14, iy, LEFT_W-28, 44,
                           fill=fill, border=rcol if is_sel else BORDER_STONE,
                           radius=6, glow=is_sel, glow_alpha=22)
            self.item_rects[real_idx] = r

            bdr = pygame.Rect(ox+18, iy+13, 17, 17)
            pygame.draw.rect(surface, rcol, bdr, border_radius=3)
            draw_text(surface, itm.rarity[0],
                      bdr.centerx, bdr.top+2, 10, (0,0,0), style="bold", center=True)

            label = f"{itm.name}" + (f"  {lock_msg}" if not can_equip else "")
            draw_text(surface, label[:44], ox+44, iy+6, 13,
                      (70,60,52) if not can_equip else rcol,
                      style="bold" if is_sel else "body")
            draw_text(surface, itm.description[:52], ox+44, iy+26, 9, TEXT_DIM)

            eq_col = DF_MOSS if can_equip else (40,35,30)
            eb = draw_button(surface, ox+LEFT_W-124, iy+9, 74, 26,
                             "EQUIP" if can_equip else "LOCK",
                             pygame.Rect(ox+LEFT_W-124,iy+9,74,26).collidepoint(mouse_pos) and can_equip,
                             eq_col, 11)
            self.equip_btns[real_idx] = (eb, can_equip)

            sb = draw_button(surface, ox+LEFT_W-42, iy+9, 30, 26, "$",
                             pygame.Rect(ox+LEFT_W-42,iy+9,30,26).collidepoint(mouse_pos),
                             DF_GOLD_DIM, 12)
            self.item_rects[f"sell_{real_idx}"] = sb

        if len(player.inventory) > VISIBLE:
            draw_text(surface,
                      f"Scroll ↑↓  ({self.scroll+1}–{min(self.scroll+VISIBLE,len(player.inventory))} / {len(player.inventory)})",
                      ox+14, oy+H-26, 10, TEXT_DIM)

        pygame.draw.line(surface, BORDER_GOLD, (ox+LEFT_W,oy+46),(ox+LEFT_W,oy+H-16),1)

        # RIGHT PANEL
        rx = ox+LEFT_W+16
        rw = W-LEFT_W-26
        ry = oy+50

        draw_text(surface, "CHARACTER", rx, ry, 11, DF_GOLD_DIM, style="bold")
        ry += 20

        draw_panel(surface, rx, ry, rw, 28,
                   fill=(30,10,16), border=DF_BLOOD, radius=5, glow=True, glow_alpha=18)
        draw_text(surface, "Sausage Man", rx+9, ry+6, 13, DF_BONE, style="bold")
        draw_text(surface, f"{player.gold} G", rx+rw-46, ry+8, 11, DF_GOLD, style="mono")
        ry += 38

        _draw_rune_divider(surface, rx, ry, rx+rw)
        ry += 10

        draw_text(surface, "RESOURCES", rx, ry, 10, TEXT_PRIM, style="bold")
        ry += 16
        for lbl,val,maxv,col in [
            ("HP",    player.hp,    player.max_hp,    DF_BLOOD_B),
            ("Armor", player.armor, player.max_armor, DF_ASH),
            ("Mana",  player.mana,  player.max_mana,  DF_FROST),
        ]:
            draw_text(surface, lbl, rx, ry, 11, col, style="bold")
            draw_bar(surface, rx+50, ry+1, rw-50, 12, val, maxv, col)
            draw_text(surface, f"{int(val)}/{maxv}", rx+53, ry+15, 9, col, style="mono")
            ry += 30

        _draw_rune_divider(surface, rx, ry, rx+rw)
        ry += 10

        draw_text(surface, "WEAPON", rx, ry, 10, TEXT_PRIM, style="bold")
        ry += 16
        wpn = player.weapon
        if wpn:
            wc = RARITY_GLOW.get(wpn.rarity, TEXT_PRIM)
            draw_text(surface, wpn.name[:22], rx, ry, 12, wc, style="bold")
            ry += 17
            for lbl,val,col in [
                ("DMG",  wpn.damage,           DF_BLOOD_B),
                ("Rate", f"{int(wpn.fire_rate)}/s", TEXT_DIM),
                ("Spd",  wpn.bullet_speed,     DF_FROST),
            ]:
                draw_text(surface, lbl, rx, ry, 10, TEXT_MUTED)
                draw_text(surface, str(val), rx+46, ry, 11, col, style="mono")
                ry += 16
        else:
            draw_text(surface, "— no weapon —", rx, ry, 11, (55,48,38))
            ry += 17

        ry += 4
        _draw_rune_divider(surface, rx, ry, rx+rw)
        ry += 10

        draw_text(surface, "COMBAT", rx, ry, 10, TEXT_PRIM, style="bold")
        ry += 16
        for lbl,val,col in [
            ("CRIT",  f"{int(player.crit_chance*100)}%  ×{int(player.crit_mult)}", DF_GOLD),
            ("DEF",   player.defense,          DF_ASH),
            ("SPD",   int(player.move_speed),  DF_MOSS),
            ("Gold",  player.gold,             DF_GOLD),
        ]:
            draw_text(surface, lbl, rx, ry, 10, TEXT_MUTED)
            draw_text(surface, str(val), rx+46, ry, 11, col, style="mono")
            ry += 16

        _draw_rune_divider(surface, rx, ry+2, rx+rw)
        ry += 12

        draw_text(surface, "PASSIVE", rx, ry, 10, DF_GOLD, style="bold")
        ry += 14
        ptext = getattr(player,"passive","")
        line = ""
        for w2 in ptext.split():
            if len(line)+len(w2)+1 <= 27:
                line += ("" if line=="" else " ")+w2
            else:
                draw_text(surface, line, rx, ry, 9, TEXT_DIM)
                ry += 12
                line = w2
        if line:
            draw_text(surface, line, rx, ry, 9, TEXT_DIM)

        draw_text(surface, "TAB / ESC  to close",
                  ox+W//2, oy+H-16, 11, TEXT_MUTED, center=True)

    def handle_click(self, pos, player):
        for idx,(btn,can_equip) in self.equip_btns.items():
            if btn.collidepoint(pos):
                if not can_equip: return "locked"
                itm = player.inventory[idx]
                old = player.equip(itm)
                player.inventory.pop(idx)
                if old: player.inventory.append(old)
                return "equip"
        for key,r in self.item_rects.items():
            if isinstance(key,str) and key.startswith("sell_"):
                if r.collidepoint(pos):
                    idx = int(key.split("_")[1])
                    if idx < len(player.inventory):
                        itm = player.inventory.pop(idx)
                        player.gold += itm.sell_price
                    return "sell"
        for idx,r in self.item_rects.items():
            if isinstance(idx,int) and r.collidepoint(pos):
                self.selected_idx = idx
        return None

    def handle_scroll(self, direction, player):
        max_scroll = max(0, len(player.inventory)-7)
        self.scroll = max(0, min(self.scroll+direction, max_scroll))


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
        rarities = ["Common","Common","Rare","Rare","Epic"]
        if stage_id >= 3:
            rarities = ["Rare","Rare","Epic","Epic","Legendary"]
        self.shop_items = [
            make_weapon(random.choice(rarities)),
            make_weapon(random.choice(rarities)),
            make_weapon(random.choice(rarities)),
            make_armor(random.choice(rarities)),
            make_accessory(random.choice(rarities)),
        ]
        self.prices = [SHOP_ITEM_MULT.get(i.rarity,30) for i in self.shop_items]

    def draw(self, surface, player, mouse_pos):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0,0,0,220))
        surface.blit(overlay, (0,0))

        W, H = 920, 580
        ox   = SCREEN_W//2-W//2
        oy   = SCREEN_H//2-H//2

        _draw_stone_panel(surface, ox, oy, W, H,
                          border_col=BORDER_GOLD, radius=12, glow=True)

        # Title bar
        pygame.draw.rect(surface, (12,10,8), (ox,oy,W,48), border_radius=12)
        _draw_rune_divider(surface, ox, oy+48, ox+W)
        draw_text(surface, "THE MERCHANT",
                  ox+W//2, oy+10, 26, DF_GOLD,
                  style="title", center=True, shadow=True)
        draw_text(surface, "Stage cleared — spend your gold wisely.",
                  ox+W//2, oy+42, 11, TEXT_DIM, center=True)

        draw_text(surface, f"GOLD:  {player.gold} G",
                  ox+16, oy+60, 17, DF_GOLD, style="bold")
        draw_bar(surface, ox+148, oy+63, 200, 12,
                 player.hp, player.max_hp, DF_BLOOD_B)
        draw_text(surface, f"HP {int(player.hp)}/{player.max_hp}",
                  ox+152, oy+78, 9, DF_BLOOD_B, style="mono")

        can_reroll = player.gold >= self.reroll_cost
        self.btn_reroll = draw_button(
            surface, ox+W-200, oy+58, 184, 34,
            f"REROLL  ({self.reroll_cost}G)",
            pygame.Rect(ox+W-200,oy+58,184,34).collidepoint(mouse_pos),
            DF_GOLD_DIM if can_reroll else (40,35,28), 13)

        can_heal = player.gold >= SHOP_HEAL_COST
        self.heal_btn = draw_button(
            surface, ox+16, oy+102, 240, 32,
            f"HEAL  50 HP  ({SHOP_HEAL_COST}G)",
            pygame.Rect(ox+16,oy+102,240,32).collidepoint(mouse_pos),
            DF_BLOOD if can_heal else (40,30,28), 13)

        draw_text(surface, "All weapons available — no class restrictions.",
                  ox+272, oy+112, 11, DF_MOSS)

        _draw_rune_divider(surface, ox+14, oy+144, ox+W-14)

        self.buy_btns = {}
        for i, itm in enumerate(self.shop_items):
            iy = oy+152 + i*74

            if itm is None:
                draw_panel(surface, ox+14, iy, W-28, 62,
                           fill=(12,10,8), border=BORDER_STONE, radius=7)
                draw_text(surface, "— SOLD OUT —",
                          ox+W//2, iy+22, 15, (55,48,38), center=True)
                continue

            rcol = RARITY_GLOW.get(itm.rarity, TEXT_PRIM)
            can_use, lock_note = True, ""
            if hasattr(itm,"can_equip"):
                can_use, lock_note = itm.can_equip(player)
                if lock_note: lock_note = "  "+lock_note

            fill_col = (20,18,14) if can_use else (24,10,10)
            draw_panel(surface, ox+14, iy, W-28, 62,
                       fill=fill_col, border=rcol, radius=7,
                       glow=can_use, glow_alpha=16)

            bdr = pygame.Rect(ox+20, iy+10, 38, 16)
            pygame.draw.rect(surface, rcol, bdr, border_radius=3)
            draw_text(surface, itm.rarity, bdr.centerx, bdr.top+2, 9,
                      (0,0,0), style="bold", center=True)

            name_col = rcol if can_use else (55,48,38)
            draw_text(surface, f"{itm.name}{lock_note}",
                      ox+68, iy+5, 16, name_col, style="bold")
            draw_text(surface, itm.description[:72], ox+68, iy+26, 10, TEXT_DIM)

            parts = []
            if hasattr(itm,"damage"):       parts.append(f"DMG {itm.damage}")
            if hasattr(itm,"defense"):      parts.append(f"DEF {itm.defense}")
            if hasattr(itm,"fire_rate") and itm.fire_rate>0:
                parts.append(f"Rate {int(itm.fire_rate)}/s")
            sb = getattr(itm,"stat_bonus",{})
            if sb:
                sb_str = "  ".join(f"+{v} {k}" for k,v in sb.items() if v>0)
                if sb_str: parts.append(sb_str)
            if parts:
                draw_text(surface, "  ·  ".join(parts[:4]),
                          ox+68, iy+46, 9, DF_RUNE, style="mono")

            price   = self.prices[i]
            can_buy = player.gold >= price and can_use
            bb = draw_button(surface, ox+W-164, iy+13, 144, 34,
                             f"BUY  {price} G",
                             pygame.Rect(ox+W-164,iy+13,144,34).collidepoint(mouse_pos),
                             DF_BLOOD if can_buy else (38,30,28), 14)
            self.buy_btns[i] = (bb, can_use)

        self.btn_leave = draw_button(
            surface, ox+W//2-104, oy+H-48, 208, 38,
            "CONTINUE  →",
            pygame.Rect(ox+W//2-104,oy+H-48,208,38).collidepoint(mouse_pos),
            DF_FROST_DIM, 16)

    def handle_click(self, pos, player):
        if self.heal_btn.collidepoint(pos):
            if player.gold >= SHOP_HEAL_COST:
                player.gold -= SHOP_HEAL_COST
                player.heal(50)
                return "heal"
        if self.btn_reroll.collidepoint(pos):
            if player.gold >= self.reroll_cost:
                player.gold      -= self.reroll_cost
                self.reroll_cost  = int(self.reroll_cost*1.5)
                self._gen_items(self.stage_id, player.char_class)
                return "reroll"
        for i,(btn,can_use) in self.buy_btns.items():
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
    def __init__(self):
        self._t = 0.0

    def draw(self, surface, mouse_pos):
        self._t += 0.016
        t = self._t

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0,0,0,170))
        surface.blit(overlay, (0,0))

        # Vignette
        vig = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for ew in range(100,0,-5):
            a = int((100-ew)*1.0)
            pygame.draw.rect(vig,(0,0,0,a),(100-ew,100-ew,
                SCREEN_W-2*(100-ew),SCREEN_H-2*(100-ew)),ew)
        surface.blit(vig,(0,0))

        _tick_petals(0.016)
        _draw_petals(surface)

        cw,ch = 420,440
        cx = SCREEN_W//2 - cw//2
        cy = SCREEN_H//2 - ch//2

        pulse_a = int(20+8*math.sin(t*1.4))
        for gi in (7,4,2):
            gs = pygame.Surface((cw+gi*4,ch+gi*4),pygame.SRCALPHA)
            pygame.draw.rect(gs,(*DF_GOLD,pulse_a//gi),(0,0,cw+gi*4,ch+gi*4),border_radius=14+gi)
            surface.blit(gs,(cx-gi*2,cy-gi*2))

        _draw_stone_panel(surface,cx,cy,cw,ch,border_col=BORDER_GOLD,radius=14)

        _draw_leaf_deco(surface, cx+16,cy+16, t, 5, 12, DF_RUNE_DIM)
        _draw_leaf_deco(surface, cx+cw-16,cy+16, t*1.1, 5, 12, DF_GOLD_DIM)
        _draw_leaf_deco(surface, cx+16,cy+ch-16, t*0.9, 5, 12, DF_GOLD_DIM)
        _draw_leaf_deco(surface, cx+cw-16,cy+ch-16, t*1.2, 5, 12, DF_RUNE_DIM)

        title_y = cy+36
        for ox2,oy2 in ((-2,-2),(2,2),(-2,2),(2,-2)):
            draw_text(surface,"PAUSED",SCREEN_W//2+ox2,title_y+oy2,48,DF_GOLD_DIM,
                      style="title",center=True)
        draw_text(surface,"PAUSED",SCREEN_W//2,title_y,48,DF_BONE,
                  style="title",center=True)

        _draw_rune_divider(surface,cx+26,cy+100,cx+cw-26)
        draw_text(surface,"Press  ESC  to resume",
                  SCREEN_W//2,cy+112,12,TEXT_DIM,center=True)

        bw2,bh2 = 330,62
        bx2 = SCREEN_W//2-bw2//2
        by1 = cy+150; by2 = by1+78; by3 = by2+78

        self.btn_resume  = _draw_df_button(surface,bx2,by1,bw2,bh2,"RESUME",
            pygame.Rect(bx2,by1,bw2,bh2).collidepoint(mouse_pos),"frost",22)
        self.btn_restart = _draw_df_button(surface,bx2,by2,bw2,bh2,"RESTART",
            pygame.Rect(bx2,by2,bw2,bh2).collidepoint(mouse_pos),"stone",22)
        self.btn_menu    = _draw_df_button(surface,bx2,by3,bw2,bh2,"EXIT TO MENU",
            pygame.Rect(bx2,by3,bw2,bh2).collidepoint(mouse_pos),"blood",20)

        draw_text(surface,"F11 — Toggle Fullscreen",
                  SCREEN_W//2,cy+ch-20,10,TEXT_MUTED,center=True)

    def handle_click(self, pos):
        if hasattr(self,"btn_resume")  and self.btn_resume.collidepoint(pos):  return "resume"
        if hasattr(self,"btn_restart") and self.btn_restart.collidepoint(pos): return "restart"
        if hasattr(self,"btn_menu")    and self.btn_menu.collidepoint(pos):    return "menu"
        return None


# ═══════════════════════════════════════════════════════════════
#  GAME OVER / VICTORY SCREEN
# ═══════════════════════════════════════════════════════════════
class GameOverScreen:
    def __init__(self):
        self._t = 0.0

    def draw(self, surface, player, tracker, win=False):
        self._t += 0.016
        t   = self._t
        W, H = surface.get_width(), surface.get_height()

        _draw_bg_dungeon(surface, t)
        _tick_petals(0.016)
        _draw_petals(surface)

        if win:
            # Golden rays of victory
            ray_s = pygame.Surface((W,H),pygame.SRCALPHA)
            for ray_i in range(-4,5):
                base  = math.radians(90+ray_i*8)
                pulse = 0.7+0.3*math.sin(t*1.1+ray_i*0.5)
                a_rr  = max(0,int(22*pulse-abs(ray_i)*4))
                pts   = [(W//2,0),
                         (W//2+int(math.cos(base-0.05)*W*1.5),int(math.sin(base-0.05)*H*1.5)),
                         (W//2+int(math.cos(base+0.05)*W*1.5),int(math.sin(base+0.05)*H*1.5))]
                pygame.draw.polygon(ray_s,(*DF_GOLD,a_rr),pts)
            surface.blit(ray_s,(0,0))
        else:
            # Blood fog rising
            fog = pygame.Surface((W,H),pygame.SRCALPHA)
            for fy in range(H//2,H,2):
                frac  = (fy-H//2)/(H//2)
                pulse = 0.5+0.5*math.sin(t*0.7+fy*0.015)
                a2    = int(40*frac*pulse)
                pygame.draw.line(fog,(140,15,15,a2),(0,fy),(W,fy))
            surface.blit(fog,(0,0))

        # Title
        t_label = "VICTORY!" if win else "GAME OVER"
        t_col2  = DF_GOLD if win else DF_BLOOD_B
        t_sub   = "You are the champion of Midgard!" if win else "Your journey ends here..."

        title_y = 40
        for ox3,oy3 in ((-3,-3),(3,3)):
            draw_text(surface,t_label,W//2+ox3,title_y+oy3,76,
                      DF_GOLD_DIM if win else DF_CRIMSON,style="title",center=True)
        draw_text(surface,t_label,W//2,title_y,76,DF_BONE,
                  style="title",center=True)
        draw_text(surface,t_sub,W//2,132,16,TEXT_DIM,center=True)
        _draw_rune_divider(surface,W//2-260,160,W//2+260,
                           col=DF_GOLD if win else DF_BLOOD)

        # Stats panel
        summary = tracker.current_run
        pairs = [
            ("Score",        f"{summary.get('score',0):,}",          DF_GOLD),
            ("Enemies",      summary.get("enemies_defeated",0),       DF_BLOOD_B),
            ("Total Damage", f"{summary.get('total_damage',0):,}",    DF_ASH),
            ("Items Found",  summary.get("items_collected",0),        DF_FROST),
            ("Gold Earned",  player.gold,                             DF_GOLD),
            ("Duration",     f"{summary.get('duration_sec',0)}s",     TEXT_DIM),
            ("Stage",        f"{summary.get('stage_reached',1)} / 5", DF_RUNE),
        ]

        CW,CH = 600,240
        cpx = W//2-CW//2
        cpy = 174

        _draw_stone_panel(surface,cpx,cpy,CW,CH,
                          border_col=DF_GOLD if win else BORDER_BLOOD,
                          radius=12,glow=True)
        _draw_leaf_deco(surface,cpx+16,cpy+16,t,4,10,DF_RUNE_DIM)
        _draw_leaf_deco(surface,cpx+CW-16,cpy+16,t*1.1,4,10,DF_GOLD_DIM)

        hdr = pygame.Surface((CW-4,36),pygame.SRCALPHA)
        hdr.fill((0,0,0,50))
        surface.blit(hdr,(cpx+2,cpy+2))
        draw_text(surface,"EXPEDITION  SUMMARY",
                  W//2,cpy+12,13,DF_GOLD,style="bold",center=True)
        _draw_rune_divider(surface,cpx+22,cpy+38,cpx+CW-22)

        col_w = CW//2
        for idx4,(lbl4,val4,vcol4) in enumerate(pairs):
            col4 = idx4%2
            row4 = idx4//2
            rx7  = cpx+col4*col_w+18
            ry7  = cpy+48+row4*44
            draw_text(surface,lbl4,  rx7, ry7,   11, TEXT_DIM)
            draw_text(surface,str(val4), rx7, ry7+17, 16, vcol4, style="mono")

        pygame.draw.line(surface,BORDER_GOLD,
                         (cpx+col_w,cpy+46),(cpx+col_w,cpy+CH-8),1)

        # Buttons
        btn_y3 = cpy+CH+28
        rbw,rbh = 230,58

        self.btn_restart = _draw_df_button(
            surface,W//2-rbw-12,btn_y3,rbw,rbh,
            "PLAY AGAIN",False,"blood",20)
        self.btn_menu = _draw_df_button(
            surface,W//2+12,btn_y3,rbw,rbh,
            "MAIN MENU",False,"frost",20)

        draw_text(surface,"Click to continue your journey",
                  W//2,btn_y3+rbh+12,11,TEXT_MUTED,center=True)

    def handle_click(self, pos):
        if hasattr(self,"btn_menu")    and self.btn_menu.collidepoint(pos):    return "menu"
        if hasattr(self,"btn_restart") and self.btn_restart.collidepoint(pos): return "restart"
        return None


# ═══════════════════════════════════════════════════════════════
#  SHOOTING RANGE SCREEN
# ═══════════════════════════════════════════════════════════════
class ShootingRangeScreen:
    RARITY_COLOR = RARITY_GLOW
    PANEL_W = 240
    PLAY_W  = SCREEN_W - 240
    PLAY_H  = SCREEN_H - HUD_H

    def __init__(self):
        from item import Weapon
        from constants import WEAPON_POOL
        self._weapon_list = []
        for entry in WEAPON_POOL:
            effect = entry[9] if len(entry)>9 else None
            w = Weapon(entry[0],entry[1],entry[2],entry[3],
                       entry[4],entry[5],entry[6],"Any",entry[8],effect)
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
        self._burst_col  = (200,170,60)
        self._burst_sz   = 6
        self._burst_spd  = 7
        self.total_dmg   = self.total_hits = self.total_crits = 0
        self.holding     = False
        self.mouse       = (400, self.PLAY_H//2)
        self.last_msg    = ""
        self._btn_back   = None
        self._wpn_btns   = []
        self._scroll     = 0.0
        self._scroll_max = 0
        self._shake_timer= 0.0
        self._shake_mag  = 0
        self._dps_log    = []
        self._elapsed    = 0.0
        self._dps_window = 3.0
        self._current_dps= 0.0
        self._peak_dps   = 0.0
        self.px = 160
        self.py = self.PLAY_H//2
        self.targets = [
            {"x":self.PLAY_W-420+col*90,"y":160+row*180,
             "hp":300,"max_hp":300,"hit_flash":0.0,"r":32}
            for row in range(2) for col in range(4)
        ]

    def _current_weapon(self):
        return self._weapon_list[self.wpn_idx] if self._weapon_list else None

    def _spawn(self, angle, col, size, spd, pierce, is_crit=False, dmg=1):
        from bullet import Bullet
        dx = math.cos(angle); dy = math.sin(angle)
        bx2 = self.px+dx*32; by2 = self.py+dy*32
        b = Bullet(bx2,by2,dx,dy,spd,dmg,pierce=pierce,is_crit=is_crit,color=col,size=size)
        self.bullets.append(b)

    def _shoot(self):
        p = self.player
        if p is None: return
        wpn = self._current_weapon()
        if wpn is None or wpn.is_melee: return
        if not p.can_use_mana(wpn.mana_cost): return
        p.use_mana(wpn.mana_cost)
        dmg,crit = p.calc_damage()
        p.shoot_cooldown = 1.0/max(0.1,p.get_fire_rate())
        ang = math.atan2(self.mouse[1]-self.py,self.mouse[0]-self.px)
        fx  = wpn.effect or {}
        col = fx.get("bullet_color",(200,170,60))
        sz  = fx.get("bullet_size",6)
        spd = p.get_bullet_speed() or 7
        pierce = fx.get("pierce",False)
        pat = fx.get("pattern","single")
        sp  = lambda a: a+(self._rnd.random()-0.5)*0.22
        if pat in ("single","pierce"):
            self._spawn(ang,col,sz,spd,pierce or pat=="pierce",crit,dmg)
        elif pat=="double":
            self._spawn(ang+0.09,col,sz,spd,False,crit,dmg)
            self._spawn(ang-0.09,col,sz,spd,False,crit,dmg)
        elif pat=="spread3":
            for i in (-1,0,1): self._spawn(ang+i*0.20,col,sz,spd,False,crit,dmg)
        elif pat=="spread5":
            for i in range(-2,3): self._spawn(sp(ang+i*0.15),col,sz,spd,False,crit,dmg)
        elif pat=="spread_random":
            self._spawn(sp(ang),col,sz,spd,False,crit,dmg)
        elif pat=="burst3":
            self.burst_left=3; self.burst_timer=0.0; self._burst_ang=ang
            self._burst_col=col; self._burst_sz=sz; self._burst_spd=spd
            self._spawn(ang,col,sz,spd,False,crit,dmg); self.burst_left-=1
        elif pat in ("laser","laser_double"):
            from bullet import LaserBeam
            laser_col   = fx.get("laser_color",col)
            laser_width = fx.get("laser_width",3)
            laser_life  = fx.get("laser_lifetime",0.16)
            laser_range = 1200
            def _fire_range_laser(beam_ang):
                ddx=math.cos(beam_ang); ddy=math.sin(beam_ang)
                ox2=self.px+ddx*32; oy2=self.py+ddy*32
                end_x=ox2+ddx*laser_range; end_y=oy2+ddy*laser_range
                blen=math.hypot(end_x-ox2,end_y-oy2)
                for tgt in self.targets:
                    ex2=tgt["x"]-ox2; ey2=tgt["y"]-oy2
                    t_proj=ex2*ddx+ey2*ddy
                    if t_proj<0 or t_proj>blen: continue
                    perp=abs(ex2*ddy-ey2*ddx)
                    if perp<tgt["r"]+laser_width+2:
                        tgt["hit_flash"]=0.15; tgt["hp"]=max(0,tgt["hp"]-dmg)
                        if tgt["hp"]<=0: tgt["hp"]=tgt["max_hp"]
                        self.total_dmg+=dmg; self.total_hits+=1
                        self._dps_log.append([self._elapsed,dmg])
                        label=("CRIT! " if crit else "")+str(dmg)
                        self.floats.append({"x":tgt["x"]+self._rnd.randint(-20,20),
                            "y":tgt["y"]-40,"text":label,"life":1.0,"crit":crit})
                        wpn_name=wpn.name if wpn else "?"
                        self.last_msg=("CRITICAL! " if crit else "")+f"Hit {dmg} with {wpn_name}"
                self.bullets.append(LaserBeam(ox2,oy2,end_x,end_y,
                                              color=laser_col,width=laser_width,lifetime=laser_life))
            _fire_range_laser(ang)
            if pat=="laser_double":
                _fire_range_laser(ang+0.09); _fire_range_laser(ang-0.09)
        if wpn and hasattr(wpn,"effect") and wpn.effect:
            sh_mag,sh_dur=wpn.effect.get("shake",(3,0.10))
            if sh_mag>0:
                self._shake_timer=max(self._shake_timer,sh_dur)
                self._shake_mag=max(self._shake_mag,sh_mag)
        if crit: self.total_crits+=1
        wpn2=self._current_weapon()
        if wpn2:
            shake_mag,shake_dur=(wpn2.effect or {}).get("shake",(3,0.10))
            self._shake_timer=max(self._shake_timer,shake_dur)
            self._shake_mag=max(self._shake_mag,shake_mag)

    def _select_weapon(self, idx):
        self.wpn_idx = idx%len(self._weapon_list)
        if self.player and self._weapon_list:
            self.player.equipment["weapon"]=self._weapon_list[self.wpn_idx]
            self.player.shoot_cooldown=0.0
        self.burst_left=0

    def update(self, dt, events, mouse_pos, mouse_buttons):
        p = self.player
        self.mouse = mouse_pos
        mx,my = mouse_pos
        self.holding = bool(mouse_buttons[0] and mx<self.PLAY_W)
        if p is None: return
        self._elapsed+=dt
        p.mana=min(p.max_mana,p.mana+18*dt)
        if p.shoot_cooldown>0: p.shoot_cooldown-=dt
        if self._shake_timer>0: self._shake_timer=max(0.0,self._shake_timer-dt)
        if self.burst_left>0:
            self.burst_timer-=dt
            if self.burst_timer<=0:
                self._spawn(self._burst_ang,self._burst_col,
                            self._burst_sz,self._burst_spd,False)
                self.burst_left-=1; self.burst_timer=0.07
        if self.holding and p.shoot_cooldown<=0 and self.burst_left==0:
            self._shoot()
        for b in self.bullets:
            b.update(dt,[])
            if b.__class__.__name__=="LaserBeam": continue
            for tgt in self.targets:
                if id(tgt) in b.hit_set: continue
                if math.hypot(b.x-tgt["x"],b.y-tgt["y"])<tgt["r"]+b.radius:
                    if not b.pierce: b.alive=False
                    b.hit_set.add(id(tgt))
                    tgt["hit_flash"]=0.15
                    dmg=b.damage; crit2=b.is_crit
                    tgt["hp"]=max(0,tgt["hp"]-dmg)
                    if tgt["hp"]<=0: tgt["hp"]=tgt["max_hp"]
                    self.total_dmg+=dmg; self.total_hits+=1
                    self._dps_log.append([self._elapsed,dmg])
                    label=("CRIT! " if crit2 else "")+str(dmg)
                    self.floats.append({"x":tgt["x"]+self._rnd.randint(-20,20),
                        "y":tgt["y"]-40,"text":label,"life":1.0,"crit":crit2})
                    wpn_n=self._current_weapon().name if self._current_weapon() else "?"
                    self.last_msg=("CRITICAL! " if crit2 else "")+f"Hit {dmg} with {wpn_n}"
            if b.alive and b.__class__.__name__!="LaserBeam" and \
               not (0<b.x<self.PLAY_W and 0<b.y<self.PLAY_H):
                b.alive=False
        self.bullets=[b for b in self.bullets if b.alive]
        for tgt in self.targets:
            if tgt["hit_flash"]>0: tgt["hit_flash"]-=dt
        self.floats=[f for f in self.floats if f["life"]>0]
        for f in self.floats:
            f["y"]-=50*dt; f["life"]-=dt*1.2
        if self._shake_timer>0: self._shake_timer=max(0.0,self._shake_timer-dt)
        cutoff=self._elapsed-self._dps_window
        self._dps_log=[e for e in self._dps_log if e[0]>=cutoff]
        window_actual=min(self._elapsed,self._dps_window)
        if window_actual>0: self._current_dps=sum(e[1] for e in self._dps_log)/window_actual
        else: self._current_dps=0.0
        if self._current_dps>self._peak_dps: self._peak_dps=self._current_dps
        for ev in events:
            if ev.type==pygame.KEYDOWN:
                if ev.key==pygame.K_q: self._select_weapon(self.wpn_idx-1)
                elif ev.key==pygame.K_e: self._select_weapon(self.wpn_idx+1)

    def handle_click(self, pos):
        if self._btn_back and self._btn_back.collidepoint(pos): return "menu"
        for rect,idx in self._wpn_btns:
            if rect.collidepoint(pos): self._select_weapon(idx)
        return None

    def handle_scroll(self, y_offset):
        self._scroll=max(0,min(self._scroll_max,self._scroll-y_offset*22))

    def draw(self, surface, mouse_pos):
        p  = self.player
        pw = self.PLAY_W

        sk_ox=sk_oy=0
        if self._shake_timer>0:
            m=int(self._shake_mag*(self._shake_timer/max(0.001,self._shake_mag*0.025+0.08)))
            m=max(1,min(m,self._shake_mag))
            sk_ox=self._rnd.randint(-m,m); sk_oy=self._rnd.randint(-m,m)

        # Play area
        play_surf=pygame.Surface((pw,self.PLAY_H))
        play_surf.fill(BG_VOID)
        for gx in range(0,pw,64):
            pygame.draw.line(play_surf,(22,18,14),(gx,0),(gx,self.PLAY_H))
        for gy in range(0,self.PLAY_H,64):
            pygame.draw.line(play_surf,(22,18,14),(0,gy),(pw,gy))
        pygame.draw.line(play_surf,BORDER_STONE,(pw-1,0),(pw-1,self.PLAY_H),2)

        # Targets (sausage-man-shaped training dummies)
        for tgt in self.targets:
            fl=tgt["hit_flash"]>0
            tx,ty,r=int(tgt["x"]),int(tgt["y"]),tgt["r"]
            body  = (200,160,130) if fl else (140,115,90)
            shade = (230,190,160) if fl else (170,140,110)
            pygame.draw.ellipse(play_surf,(0,0,0),(tx-r,ty+r-4,r*2,max(4,r//2)))
            pygame.draw.circle(play_surf,body, (tx,ty),r)
            pygame.draw.circle(play_surf,shade,(tx,ty),r,2)
            # Cross-hatch on target
            for off in (-int(r*0.3),0,int(r*0.3)):
                pygame.draw.line(play_surf,(100,80,60),(tx-r+3,ty+off),(tx+r-3,ty+off),1)
            # HP bar
            bw3=r*2; bx4=tx-r; by4=ty+r+6
            pygame.draw.rect(play_surf,(14,10,8),(bx4,by4,bw3,7),border_radius=3)
            hp_w=int(bw3*tgt["hp"]/max(1,tgt["max_hp"]))
            hpc=(DF_MOSS if tgt["hp"]>tgt["max_hp"]*0.5
                 else DF_GOLD if tgt["hp"]>tgt["max_hp"]*0.25
                 else DF_BLOOD_B)
            if hp_w>0:
                pygame.draw.rect(play_surf,hpc,(bx4+1,by4+1,hp_w-2,5),border_radius=2)
            if fl:
                ov=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
                pygame.draw.circle(ov,(240,160,80,80),(r,r),r)
                play_surf.blit(ov,(tx-r,ty-r))

        for b in self.bullets:
            b.draw(play_surf,0,0)

        # Floating damage
        for f in self.floats:
            alpha=int(255*max(0.0,f["life"]))
            col   = DF_GOLD if f["crit"] else DF_BONE
            sz    = 21 if f["crit"] else 14
            fsurf = F(sz,bold=f["crit"]).render(f["text"],True,col)
            ts    = pygame.Surface(fsurf.get_size(),pygame.SRCALPHA)
            ts.blit(fsurf,(0,0)); ts.set_alpha(alpha)
            play_surf.blit(ts,(int(f["x"])-fsurf.get_width()//2,int(f["y"])))

        # Player
        ang=math.atan2(self.mouse[1]-self.py,self.mouse[0]-self.px)
        sx,sy=self.px,self.py
        facing_right=(self.mouse[0]>=self.px)
        from player import _load_sprite
        import player as _pmod
        _load_sprite()
        _sprite=_pmod._SPRITE; _sprite_flip=_pmod._SPRITE_FLIP
        if _sprite is not None:
            sprite=_sprite if facing_right else _sprite_flip
            w2,h2=sprite.get_size()
            play_surf.blit(sprite,(sx-w2//2,sy-h2//2))
        else:
            pygame.draw.circle(play_surf,DF_BLOOD_B,(sx,sy),22)
            pygame.draw.circle(play_surf,DF_BONE,(sx,sy),22,2)
        wpn=self._current_weapon()
        if wpn and p:
            p.facing_angle=ang; p.facing_right=facing_right
            p._draw_gun(play_surf,sx,sy,28)

        surface.fill(BG_VOID,(0,0,pw,self.PLAY_H))
        surface.blit(play_surf,(sk_ox,sk_oy))

        # Top HUD
        pygame.draw.rect(surface,(12,10,8),(0,0,pw,54))
        _draw_rune_divider(surface,0,54,pw)
        if wpn:
            wc=RARITY_GLOW.get(wpn.rarity,TEXT_PRIM)
            draw_text(surface,wpn.name,14,8,15,wc,style="bold")
            pat=(wpn.effect or {}).get("pattern","single")
            draw_text(surface,
                      f"DMG {wpn.damage}  ·  RATE {wpn.fire_rate:.2f}/s  ·  MANA {wpn.mana_cost}  ·  [{pat.upper()}]",
                      14,28,10,TEXT_DIM)
        mana_val=p.mana if p else 0
        mana_max=p.max_mana if p else 100
        draw_text(surface,f"MANA  {int(mana_val)}/{int(mana_max)}",pw-218,10,10,DF_FROST)
        draw_bar(surface,pw-218,24,200,11,mana_val,mana_max,DF_FROST)

        # Bottom status
        bar_y=self.PLAY_H-44
        pygame.draw.rect(surface,(12,10,8),(0,bar_y,pw,44))
        _draw_rune_divider(surface,0,bar_y,pw)
        dps=self._current_dps
        dps_col=(DF_BLOOD_B if dps>=200 else DF_GOLD if dps>=80 else DF_MOSS)
        draw_text(surface,f"DPS  {dps:>7.1f}",  14,bar_y+5, 14,dps_col,style="mono")
        draw_text(surface,f"PEAK {self._peak_dps:>7.1f}",14,bar_y+24,10,TEXT_DIM,style="mono")
        draw_text(surface,
                  f"TOTAL {self.total_dmg:,}  ·  HITS {self.total_hits}  ·  CRITS {self.total_crits}",
                  pw//2,bar_y+17,11,TEXT_DIM,center=True)
        if self.last_msg:
            draw_text(surface,self.last_msg,pw-14,bar_y+17,11,DF_GOLD)

        # Weapon sidebar
        poff=pw+4
        pygame.draw.rect(surface,(10,8,6),(pw,0,self.PANEL_W,self.PLAY_H))
        _draw_rune_divider(surface,pw,0,pw,col=BORDER_STONE)  # vertical divider workaround
        pygame.draw.line(surface,BORDER_STONE,(pw,0),(pw,self.PLAY_H),1)

        draw_text(surface,"Q / E  to cycle",poff+self.PANEL_W//2,7,9,TEXT_MUTED,center=True)
        draw_text(surface,"WEAPONS",poff+self.PANEL_W//2,20,13,DF_BONE,style="bold",center=True)

        self._btn_back=draw_button(
            surface,poff+8,self.PLAY_H-50,self.PANEL_W-16,38,
            "EXIT TO MENU",
            pygame.Rect(poff+8,self.PLAY_H-50,self.PANEL_W-16,38).collidepoint(mouse_pos),
            DF_BLOOD,12)

        lt=44; lb=self.PLAY_H-58; ih=54
        vis=(lb-lt)//ih
        self._scroll_max=max(0,(len(self._weapon_list)-vis)*ih)
        self._wpn_btns=[]
        clip=pygame.Rect(poff,lt,self.PANEL_W,lb-lt)
        surface.set_clip(clip)
        for i,wd in enumerate(self._weapon_list):
            wy=lt+i*ih-int(self._scroll)
            if wy+ih<lt or wy>lb: continue
            rect=pygame.Rect(poff+4,wy+2,self.PANEL_W-8,ih-4)
            sel =(i==self.wpn_idx)
            hov =rect.collidepoint(mouse_pos)
            rc  =RARITY_GLOW.get(wd.rarity,TEXT_PRIM)
            bg  =(28,16,14) if sel else ((20,17,14) if hov else (14,12,10))
            pygame.draw.rect(surface,bg,rect,border_radius=5)
            if sel:
                gs2=pygame.Surface((rect.w+4,rect.h+4),pygame.SRCALPHA)
                pygame.draw.rect(gs2,(*rc,30),(0,0,rect.w+4,rect.h+4),border_radius=7)
                surface.blit(gs2,(rect.x-2,rect.y-2))
            pygame.draw.rect(surface,rc if sel else BORDER_STONE,rect,
                             1 if sel else 1,border_radius=5)
            draw_text(surface,wd.name,poff+12,wy+6,11,rc,
                      style="bold" if sel else "body")
            draw_text(surface,f"DMG {wd.damage}  |  {wd.fire_rate:.1f}/s",
                      poff+12,wy+22,9,TEXT_DIM,style="mono")
            dot_col=RARITY_GLOW.get(wd.rarity,(120,110,90))
            pygame.draw.circle(surface,dot_col,(poff+12,wy+40),3)
            draw_text(surface,wd.rarity,poff+20,wy+35,8,dot_col)
            self._wpn_btns.append((rect,i))
        surface.set_clip(None)