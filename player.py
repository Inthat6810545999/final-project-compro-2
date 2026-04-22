"""
player.py  –  Player (Soul Knight style: no base_stats, no leveling, weapon = damage source)
"""
import math
import random
import os
import pygame
from pygame.locals import K_w, K_a, K_s, K_d, K_UP, K_DOWN, K_LEFT, K_RIGHT
from constants import CLASSES, SCREEN_W, SCREEN_H, HUD_H, WHITE, RED, GOLD, CYAN
from item import make_starting_weapon

_rnd = random.Random()

_SPRITE      = None
_SPRITE_FLIP = None

# ── Gun sprite system ─────────────────────────────────────────────────────────
# PNG files must sit in the same folder as player.py
# Filename convention: replace spaces with underscores, e.g. "Hand_Pistol.png"
# Images should face RIGHT; black backgrounds are auto-removed at load time.

_GUN_CACHE: dict = {}   # weapon_name -> Surface | None

# Display size (w, h) per gun shape — tweak to taste
_GUN_SIZE = {
    "pistol":   (40, 24),   # ลดจาก (52,36) — พอดีตัว
    "revolver": (44, 26),
    "smg":      (44, 22),
    "shotgun":  (50, 28),
    "rifle":    (56, 22),
    "sniper":   (64, 18),
    "launcher": (52, 32),
    "minigun":  (54, 30),
}

# ── Armor visual definitions — Dark Fantasy palette (matches ui.py) ───────────
# c1=primary  c2=dark/shadow  c3=highlight/light
# pc=particle color  pa=particle alpha  pr=particle spawn rate/sec  aura=(r,g,b,a)
_ARMOR_STYLES = {
    "Cloth Robe":    {"style": "robe",   "c1": (158,148,132), "c2": (108,100, 88), "c3": (195,185,165),
                      "pc": (158,148,132), "pa": 110, "pr": 0.0, "aura": None},
    "Leather Armor": {"style": "leather","c1": (105, 70, 30), "c2": ( 72, 46, 16), "c3": (148,100, 48),
                      "pc": (120, 80, 38), "pa": 160, "pr": 0.0, "aura": None},
    "Chainmail":     {"style": "chain",  "c1": (128,140,155), "c2": ( 85, 95,110), "c3": (195,210,228),
                      "pc": ( 78,148,198), "pa": 200, "pr": 1.5, "aura": ( 80,148,180, 16)},
    "Plate Armor":   {"style": "plate",  "c1": (185,195,212), "c2": (138,148,162), "c3": (232,240,255),
                      "pc": (200,212,235), "pa": 210, "pr": 2.0, "aura": (162,172,192, 20)},
    "Shadow Cloak":  {"style": "shadow", "c1": ( 65, 20,108), "c2": ( 35,  8, 75), "c3": (140, 55,198),
                      "pc": (118, 38,178), "pa": 215, "pr": 5.5, "aura": ( 95, 18,158, 30)},
    "Dragon Scale":  {"style": "dragon", "c1": (192, 70, 16), "c2": (145, 40,  8), "c3": (255,125, 38),
                      "pc": (252,115, 28), "pa": 228, "pr": 6.5, "aura": (195, 78, 18, 35)},
    "Aegis Plate":   {"style": "aegis",  "c1": (198,162, 78), "c2": (145,110, 36), "c3": (245,215,125),
                      "pc": (225,192, 82), "pa": 228, "pr": 7.5, "aura": (198,162, 78, 42)},
    "Void Robe":     {"style": "void",   "c1": ( 70, 15,122), "c2": ( 35,  5, 76), "c3": (155, 52,215),
                      "pc": (138, 38,205), "pa": 232, "pr": 9.0, "aura": ( 98, 16,178, 48)},
}

def _remove_black_bg(surf: "pygame.Surface") -> "pygame.Surface":
    """Make near-black pixels transparent (for PNGs without alpha channel)."""
    surf = surf.convert_alpha()
    try:
        # Fast path: numpy surfarray
        import numpy as np
        rgb   = pygame.surfarray.pixels3d(surf)          # (w, h, 3) uint8
        alpha = pygame.surfarray.pixels_alpha(surf)      # (w, h)    uint8
        mask  = (rgb[:, :, 0] < 45) & (rgb[:, :, 1] < 45) & (rgb[:, :, 2] < 45)
        alpha[mask] = 0
        del rgb, alpha   # release surface lock
    except Exception:
        # Slow fallback: pixel-by-pixel via get_at / set_at
        w, h = surf.get_size()
        for x in range(w):
            for y in range(h):
                c = surf.get_at((x, y))
                if c.r < 45 and c.g < 45 and c.b < 45:
                    surf.set_at((x, y), (0, 0, 0, 0))
    return surf

def _load_gun_sprite(weapon_name: str, gun_shape: str):
    """Return cached Surface for weapon, or None if PNG not found."""
    if weapon_name in _GUN_CACHE:
        return _GUN_CACHE[weapon_name]
    filename = weapon_name.replace(" ", "_").replace("-", "-") + ".png"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path     = os.path.join(base_dir, "sprite", "gun_sprite", filename)
    print(f"[gun] Looking for: {path}")
    print(f"[gun] File exists: {os.path.exists(path)}")
    surf     = None
    if os.path.exists(path):
        try:
            raw  = pygame.image.load(path).convert_alpha()
            raw  = _remove_black_bg(raw)
            w, h = _GUN_SIZE.get(gun_shape, (56, 32))
            surf = pygame.transform.smoothscale(raw, (w, h))
            print(f"[gun] Loaded {filename} → {w}×{h}")
        except Exception as e:
            print(f"[gun] Failed to load {filename}: {e}")
    _GUN_CACHE[weapon_name] = surf
    return surf

def _load_sprite():
    global _SPRITE, _SPRITE_FLIP
    if _SPRITE is not None:
        return
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sprite", "entity_sprite", "Sausageguy.png")
    try:
        img = pygame.image.load(path).convert_alpha()
        _SPRITE      = pygame.transform.smoothscale(img, (94, 94))
        _SPRITE_FLIP = pygame.transform.flip(_SPRITE, True, False)
    except Exception as e:
        print(f"[player] Could not load Sausageguy.png: {e}")
        _SPRITE = None


# ═══════════════════════════════════════════════════════════════
#  ARMOR VISUAL OVERLAY SYSTEM  —  Dark Fantasy Theme
#  mirrors ui.py color palette: stone / blood / ash-gold / frost
# ═══════════════════════════════════════════════════════════════



class Player:
    RADIUS = 28

    def __init__(self, name, char_class):
        self.name       = name
        self.char_class = char_class
        cfg             = CLASSES[char_class]

        play_h  = SCREEN_H - HUD_H
        self.x  = SCREEN_W / 2
        self.y  = play_h   / 2
        self.speed = cfg["speed"]

        self.max_hp    = cfg["base_hp"]
        self.hp        = self.max_hp
        self.max_armor = cfg.get("max_armor", 70)
        self.armor     = self.max_armor
        self.max_mana  = cfg.get("max_mana", 300)
        self.mana      = self.max_mana

        self.base_damage = cfg.get("base_damage", 15)
        self.crit_chance = 0.08
        self.crit_mult   = 1.8
        self.move_speed  = self.speed
        self.aspd_mult   = 1.0

        self.equipment = {
            "weapon":    make_starting_weapon(char_class),
            "armor":     None,
            "accessory": None,
        }

        self.inventory: list = []
        self.gold  = 0
        self.alive = True

        self.shoot_cooldown = 0.0
        self.facing_angle   = 0.0
        self.facing_right   = True
        self.skill_cd       = [0.0, 0.0, 0.0]  # one per skill slot

        self.iframe_timer = 0.0
        self.IFRAME_DUR   = 0.35

        self.total_damage_dealt = 0
        self.items_collected    = 0

        self.color   = cfg["color"]
        self.passive = cfg.get("passive", "")

        self._armor_regen_timer = 0.0

        # Passive mana regen: 8 mana/sec, starts after 2s without shooting
        self.mana_regen_rate   = 8.0   # mana per second (ปรับค่าได้)
        self.mana_regen_delay  = 2.0   # วินาทีหลังยิงค่อย regen
        self._mana_regen_timer = 0.0   # นับขึ้นตลอด, reset เมื่อยิง

        # ── Armor visual FX system ────────────────────────────────────
        self._armor_particles: list = []
        self._armor_ptimer    = 0.0
        self._armor_phase     = 0.0   # oscillation phase for pulse/glow


        _load_sprite()

    @property
    def weapon(self):
        return self.equipment.get("weapon")

    @property
    def defense(self):
        arm = self.equipment.get("armor")
        return arm.defense if arm else 0

    @property
    def stats(self):
        return {}

    def equip(self, item, slot=None):
        """Equip an item, or unequip a slot when item is None.

        All stat application / removal goes through here — one path only.
        Usage:
            player.equip(weapon_obj)          # equip weapon
            player.equip(armor_obj)           # equip armor
            player.equip(None, slot="armor")  # unequip armor
        """
        if item is None:
            # Unequip
            if slot is None:
                return None
            old = self.equipment.get(slot)
            if old and hasattr(old, "remove_effect"):
                old.remove_effect(self)
            self.equipment[slot] = None
            return old
        slot = item.item_type
        old  = self.equipment.get(slot)
        if old and hasattr(old, "remove_effect"):
            old.remove_effect(self)
        self.equipment[slot] = item
        if hasattr(item, "apply_effect"):
            item.apply_effect(self)
        return old

    def collect_item(self, item):
        self.inventory.append(item)
        self.items_collected += 1

    def take_damage(self, raw_damage):
        if self.iframe_timer > 0:
            return 0
        dodge = 0.05
        if _rnd.random() < dodge:
            return -1
        leftover = raw_damage
        if self.armor > 0:
            absorbed = min(self.armor, leftover)
            self.armor -= absorbed
            leftover   -= absorbed
            self._armor_regen_timer = 0.0
        hp_lost = 0
        if leftover > 0:
            self.hp   = max(0, self.hp - leftover)
            hp_lost   = leftover
        self.iframe_timer = self.IFRAME_DUR
        if self.hp <= 0:
            self.alive = False
        return hp_lost

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def calc_damage(self):
        wpn  = self.weapon
        base = wpn.damage if wpn else self.base_damage
        base = max(1, int(base * _rnd.uniform(0.92, 1.08)))
        crit = (_rnd.random() < self.crit_chance)
        mult = self.crit_mult if crit else 1.0
        dmg  = max(1, int(base * mult))
        self.total_damage_dealt += dmg
        return dmg, crit

    def get_bullet_speed(self):
        wpn = self.weapon
        if not wpn or wpn.is_melee:
            return 0
        spd = wpn.bullet_speed
        return spd

    def get_fire_rate(self):
        wpn = self.weapon
        if not wpn or wpn.is_melee:
            return 0
        return wpn.fire_rate * self.aspd_mult

    def move(self, dx, dy, walls):
        if dx == 0 and dy == 0:
            return
        length = math.hypot(dx, dy)
        dx /= length; dy /= length
        nx = self.x + dx * self.move_speed
        ny = self.y + dy * self.move_speed
        r  = self.RADIUS
        cx = cy = True
        for wall in walls:
            if wall.left < nx + r and wall.right  > nx - r and \
               wall.top  < self.y + r and wall.bottom > self.y - r:
                cx = False
            if wall.left < self.x + r and wall.right  > self.x - r and \
               wall.top  < ny + r and wall.bottom > ny - r:
                cy = False
        if cx: self.x = nx
        if cy: self.y = ny

    def update(self, dt, walls, mouse_pos=None, frozen=False):
        if self.iframe_timer > 0:
            self.iframe_timer -= dt

        if not frozen:
            keys = pygame.key.get_pressed()
            dx   = int(keys[K_d] or keys[K_RIGHT]) - int(keys[K_a] or keys[K_LEFT])
            dy   = int(keys[K_s] or keys[K_DOWN])  - int(keys[K_w] or keys[K_UP])
            if dx != 0 or dy != 0:
                self.move(dx, dy, walls)

        if mouse_pos:
            self.facing_angle = math.atan2(mouse_pos[1] - self.y, mouse_pos[0] - self.x)
            self.facing_right = (mouse_pos[0] >= self.x)

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt

        self._armor_regen_timer += dt
        if self._armor_regen_timer > 1.0:
            self.armor = min(self.max_armor, self.armor + 12.0 * dt)

        # ── Mana regen ────────────────────────────────────────────
        self._mana_regen_timer += dt
        if self._mana_regen_timer >= self.mana_regen_delay and self.mana < self.max_mana:
            self.mana = min(self.max_mana, self.mana + self.mana_regen_rate * dt)

        self._update_armor_fx(dt)

    def draw(self, surface, cam_x=0, cam_y=0):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        r  = self.RADIUS

        # Drop shadow — ปรับขึ้นมา (เดิม sy+34 → sy+24)
        feet_y  = sy + 24
        shadow_s = pygame.Surface((60, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_s, (0, 0, 0, 90), (0, 0, 60, 14))
        surface.blit(shadow_s, (sx - 30, feet_y - 4))

        if _SPRITE is not None:
            sprite = _SPRITE if self.facing_right else _SPRITE_FLIP
            w, h = sprite.get_size()

            if self.iframe_timer > 0:
                # Circular flash blended ONTO the sprite copy so it respects sprite shape
                t = pygame.time.get_ticks()
                flash_copy = sprite.copy()
                flash_s = pygame.Surface((w, h), pygame.SRCALPHA)
                # Circle centered on the character body (slightly below sprite center)
                char_cx, char_cy = w // 2, int(h * 0.52)
                char_r = int(w * 0.44)
                if (t // 60) % 2 == 0:
                    pygame.draw.circle(flash_s, (255, 255, 255, 160), (char_cx, char_cy), char_r)
                else:
                    pygame.draw.circle(flash_s, (255, 100, 100, 100), (char_cx, char_cy), char_r)
                flash_copy.blit(flash_s, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
                surface.blit(flash_copy, (sx - w // 2, sy - h // 2))
            else:
                surface.blit(sprite, (sx - w // 2, sy - h // 2))

        else:
            col = (255, 80, 80) if self.iframe_timer > 0 else self.color
            # Glow ring
            gr = r + 6
            gw = pygame.Surface((gr*2+4,gr*2+4), pygame.SRCALPHA)
            pygame.draw.circle(gw, (*col,50), (gr+2,gr+2), gr)
            surface.blit(gw, (sx-gr-2, sy-gr-2))
            pygame.draw.circle(surface, col, (sx, sy), r)
            pygame.draw.circle(surface, WHITE, (sx, sy), r, 2)
            # Highlight
            hi = tuple(min(255,c+80) for c in col)
            pygame.draw.circle(surface, hi, (sx-r//4, sy-r//4), r//4)

        # ── Draw armor overlay + FX ───────────────────────────────────
        self._draw_armor(surface, sx, sy)

        # ── Draw gun model ────────────────────────────────────
        self._draw_gun(surface, sx, sy, r)

    def _draw_gun(self, surface, sx, sy, r):
        """Draw gun sprite (PNG) rotated toward cursor; falls back to polygon."""
        import math
        wpn = self.weapon
        if not wpn or wpn.is_melee:
            return
        fx = wpn.effect if hasattr(wpn, 'effect') else {}

        gun_shape = fx.get("gun_shape", "pistol")
        gun_color = fx.get("gun_color", (160, 160, 180))
        dark_col  = tuple(max(0, c - 60) for c in gun_color)

        angle = self.facing_angle

        # ── Sprite path ───────────────────────────────────────
        gun_surf = _load_gun_sprite(wpn.name, gun_shape)
        if gun_surf is not None:
            angle_deg = math.degrees(angle)
            base = pygame.transform.flip(gun_surf, False, True) if not self.facing_right else gun_surf
            rotated = pygame.transform.rotozoom(base, -angle_deg, 1.0)
            rw, rh  = rotated.get_size()
            offset = r + 4
            gx = sx + int(math.cos(angle) * offset) - rw // 2
            gy = sy + int(math.sin(angle) * offset) - rh // 2
            surface.blit(rotated, (gx, gy))
            return

        # ── Polygon fallback ──────────────────────────────────
        ox     = sx + int(math.cos(angle) * (r - 4))
        oy     = sy + int(math.sin(angle) * (r - 4))
        cos_a  = math.cos(angle)
        sin_a  = math.sin(angle)
        perp_x = -sin_a
        perp_y =  cos_a

        def pt(forward, side):
            return (int(ox + cos_a * forward + perp_x * side),
                    int(oy + sin_a * forward + perp_y * side))

        if gun_shape == "pistol" or gun_shape == "revolver":
            barrel_len = 18 if gun_shape == "revolver" else 14
            w = 4 if gun_shape == "revolver" else 3
            points = [pt(0, -w), pt(barrel_len, -w), pt(barrel_len, w), pt(0, w)]
            pygame.draw.polygon(surface, gun_color, points)
            pygame.draw.polygon(surface, dark_col,  points, 1)
            # Grip
            grip = [pt(-4, -w), pt(0, -w), pt(0, w+2), pt(-4, w+2)]
            pygame.draw.polygon(surface, dark_col, grip)

        elif gun_shape == "smg":
            points = [pt(0, -3), pt(16, -3), pt(16, 3), pt(0, 3)]
            pygame.draw.polygon(surface, gun_color, points)
            pygame.draw.polygon(surface, dark_col,  points, 1)
            # Stock
            stock = [pt(-8, -3), pt(0, -3), pt(0, 3), pt(-8, 2)]
            pygame.draw.polygon(surface, dark_col, stock)
            # Mag
            mag = [pt(-4, 3), pt(0, 3), pt(0, 8), pt(-4, 8)]
            pygame.draw.polygon(surface, dark_col, mag)

        elif gun_shape == "shotgun":
            # Wide double barrel
            for off in (-2, 2):
                pts = [pt(0, off-2), pt(22, off-2), pt(22, off+2), pt(0, off+2)]
                pygame.draw.polygon(surface, gun_color, pts)
            pygame.draw.circle(surface, dark_col, pt(22, -2), 3)
            pygame.draw.circle(surface, dark_col, pt(22,  2), 3)
            # Stock
            stock = [pt(-10, -4), pt(0, -4), pt(0, 4), pt(-10, 3)]
            pygame.draw.polygon(surface, dark_col, stock)

        elif gun_shape == "rifle":
            points = [pt(0, -3), pt(26, -3), pt(26, 3), pt(0, 3)]
            pygame.draw.polygon(surface, gun_color, points)
            pygame.draw.polygon(surface, dark_col,  points, 1)
            # Stock
            stock = [pt(-12, -3), pt(0, -3), pt(0, 3), pt(-12, 2)]
            pygame.draw.polygon(surface, dark_col, stock)
            # Mag
            mag = [pt(-6, 3), pt(-1, 3), pt(-1, 9), pt(-6, 9)]
            pygame.draw.polygon(surface, dark_col, mag)

        elif gun_shape == "sniper":
            # Long thin barrel
            points = [pt(0, -2), pt(34, -2), pt(34, 2), pt(0, 2)]
            pygame.draw.polygon(surface, gun_color, points)
            pygame.draw.polygon(surface, dark_col,  points, 1)
            # Scope
            scope = [pt(8, -5), pt(18, -5), pt(18, -2), pt(8, -2)]
            pygame.draw.polygon(surface, (40, 40, 60), scope)
            pygame.draw.polygon(surface, (100, 200, 255), scope, 1)
            # Stock
            stock = [pt(-14, -2), pt(0, -2), pt(0, 2), pt(-14, 2)]
            pygame.draw.polygon(surface, dark_col, stock)

        elif gun_shape == "launcher":
            # Big wide tube
            points = [pt(0, -6), pt(28, -6), pt(28, 6), pt(0, 6)]
            pygame.draw.polygon(surface, gun_color, points)
            pygame.draw.polygon(surface, dark_col,  points, 2)
            # Muzzle ring
            pygame.draw.circle(surface, dark_col, pt(28, 0), 6, 2)
            # Grip
            grip = [pt(-6, -4), pt(0, -4), pt(0, 6), pt(-6, 6)]
            pygame.draw.polygon(surface, dark_col, grip)

        elif gun_shape == "minigun":
            # 3 rotating barrels
            for i, off in enumerate((-4, 0, 4)):
                col_v = gun_color if i == 1 else dark_col
                pts = [pt(0, off-2), pt(24, off-2), pt(24, off+2), pt(0, off+2)]
                pygame.draw.polygon(surface, col_v, pts)
            # Motor block
            block = [pt(-4, -6), pt(4, -6), pt(4, 6), pt(-4, 6)]
            pygame.draw.polygon(surface, dark_col, block)

    # ═══════════════════════════════════════════════════════════════
    #  ARMOR VISUAL FX SYSTEM  (Dark Fantasy theme)
    # ═══════════════════════════════════════════════════════════════

    def _update_armor_fx(self, dt):
        """Spawn & update armor particles each frame."""
        import random as _r
        self._armor_phase = (self._armor_phase + dt * 2.2) % (math.pi * 2)

        # Age + move existing particles
        self._armor_particles = [
            p for p in self._armor_particles
            if (p.__setitem__("life", p["life"] - dt / p["ml"]) or True)
            and p["life"] > 0
        ]
        for p in self._armor_particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            # All particles drift upward slightly
            p["vy"] -= 14 * dt

        # Spawn new particles based on equipped armor
        arm = self.equipment.get("armor")
        if arm is None:
            return
        sd = _ARMOR_STYLES.get(arm.name)
        if sd is None or sd["pr"] <= 0:
            return

        self._armor_ptimer += dt
        interval = 1.0 / sd["pr"]
        while self._armor_ptimer >= interval:
            self._armor_ptimer -= interval
            self._spawn_armor_particle(sd, _r)

    def _spawn_armor_particle(self, sd, _r):
        style = sd["style"]
        px, py = self.x, self.y
        pc, pa = sd["pc"], sd["pa"]

        if style == "chain":
            p = {"x": px + _r.choice([-22, 22]) + _r.uniform(-6, 6),
                 "y": py + _r.uniform(-14, 12),
                 "vx": _r.uniform(-10, 10), "vy": _r.uniform(-28, -10),
                 "life": 1.0, "ml": _r.uniform(0.4, 0.8),
                 "col": pc, "a": pa, "sz": _r.uniform(1.5, 3.0), "type": "spark"}

        elif style == "plate":
            p = {"x": px + _r.uniform(-22, 22), "y": py + _r.uniform(-18, 14),
                 "vx": _r.uniform(-14, 14), "vy": _r.uniform(-32, -14),
                 "life": 1.0, "ml": _r.uniform(0.25, 0.55),
                 "col": pc, "a": pa, "sz": _r.uniform(1.0, 2.5), "type": "spark"}

        elif style == "shadow":
            p = {"x": px + _r.uniform(-28, 28), "y": py + _r.uniform(8, 28),
                 "vx": _r.uniform(-5, 5), "vy": _r.uniform(-38, -18),
                 "life": 1.0, "ml": _r.uniform(0.7, 1.4),
                 "col": pc, "a": int(pa * 0.65), "sz": _r.uniform(4.0, 9.0), "type": "smoke"}

        elif style == "dragon":
            side = _r.choice([-1, 1])
            p = {"x": px + side * _r.uniform(14, 30) + _r.uniform(-4, 4),
                 "y": py + _r.uniform(-20, 2),
                 "vx": _r.uniform(-12, 12), "vy": _r.uniform(-55, -28),
                 "life": 1.0, "ml": _r.uniform(0.25, 0.65),
                 "col": pc, "a": pa, "sz": _r.uniform(2.0, 5.0), "type": "ember"}

        elif style == "aegis":
            angle = _r.uniform(0, math.pi * 2)
            dist  = _r.uniform(16, 38)
            p = {"x": px + math.cos(angle) * dist,
                 "y": py + math.sin(angle) * dist * 0.7,
                 "vx": _r.uniform(-8, 8), "vy": _r.uniform(-38, -16),
                 "life": 1.0, "ml": _r.uniform(0.5, 1.1),
                 "col": pc, "a": pa, "sz": _r.uniform(2.0, 5.5), "type": "star"}

        elif style == "void":
            angle = _r.uniform(0, math.pi * 2)
            dist  = _r.uniform(18, 40)
            p = {"x": px + math.cos(angle) * dist,
                 "y": py + math.sin(angle) * dist * 0.55,
                 "vx": _r.uniform(-4, 4), "vy": _r.uniform(-18, -6),
                 "life": 1.0, "ml": _r.uniform(0.9, 1.8),
                 "col": pc, "a": int(pa * 0.55), "sz": _r.uniform(3.0, 8.0), "type": "orb"}
        else:
            return

        self._armor_particles.append(p)

    # ── Master armor draw ─────────────────────────────────────────────────────
    # ทุกชุดวาดลง canvas ขนาดเท่ากัน 80×96 px  (cx=40, cy=44 = จุดกึ่งกลางหน้าอก)
    # ปรับตำแหน่งทั้งหมดได้ที่ _ARM_BLIT_OX / _ARM_BLIT_OY
    _ARM_CW      = 80    # canvas width
    _ARM_CH      = 96    # canvas height
    _ARM_CX      = 40    # chest center X inside canvas
    _ARM_CY      = 44    # chest center Y inside canvas
    _ARM_BLIT_OX = 40    # blit offset X  (surface.blit at sx - _ARM_BLIT_OX)
    _ARM_BLIT_OY = 28    # blit offset Y  (surface.blit at sy - _ARM_BLIT_OY)  ← ลดเพื่อเลื่อนลง

    def _draw_armor(self, surface, sx, sy):
        """Draw armor overlay on the player sprite — Dark Fantasy theme."""
        arm = self.equipment.get("armor")
        if arm is None:
            return
        sd = _ARMOR_STYLES.get(arm.name)
        if sd is None:
            return

        t     = pygame.time.get_ticks() / 1000.0
        phase = self._armor_phase
        c1, c2, c3 = sd["c1"], sd["c2"], sd["c3"]

        # ── 1. Aura glow (Rare+) ──────────────────────────────────────
        aura = sd.get("aura")
        if aura:
            ar, ag, ab, aa = aura
            pulse_a = int(aa * (0.65 + 0.35 * math.sin(phase)))
            ar_r    = 40 + int(5 * math.sin(phase * 1.4))
            gs = pygame.Surface((ar_r * 2 + 4, ar_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(gs, (ar, ag, ab, pulse_a),
                               (ar_r + 2, ar_r + 2), ar_r)
            pygame.draw.circle(gs, (ar, ag, ab, pulse_a // 3),
                               (ar_r + 2, ar_r + 2), ar_r - 8)
            surface.blit(gs, (sx - ar_r - 2, sy - ar_r - 2))

        # ── 2. Particles ──────────────────────────────────────────────
        for p in self._armor_particles:
            frac  = max(0.0, p["life"])
            alpha = int(p["a"] * frac)
            if alpha <= 0:
                continue
            sz    = max(1, int(p["sz"] * (0.4 + 0.6 * frac)))
            col   = p["col"]
            pw    = int(p["x"] - (self.x - sx))
            ph_y  = int(p["y"] - (self.y - sy))
            d     = sz * 2 + 4

            ptype = p["type"]
            buf   = pygame.Surface((d, d), pygame.SRCALPHA)

            if ptype == "spark":
                pygame.draw.circle(buf, (*col, alpha),     (sz + 2, sz + 2), sz)
                pygame.draw.circle(buf, (*col, min(255, alpha + 60)),
                                   (sz + 2, sz + 2), max(1, sz // 2))

            elif ptype == "ember":
                # Hot core → cooler edge
                hot = tuple(min(255, c + 80) for c in col)
                pygame.draw.circle(buf, (*hot, alpha),  (sz + 2, sz + 2), max(1, sz // 2))
                pygame.draw.circle(buf, (*col, alpha // 2), (sz + 2, sz + 2), sz)

            elif ptype == "smoke":
                pygame.draw.circle(buf, (*col, alpha // 2), (sz + 2, sz + 2), sz)

            elif ptype == "orb":
                pygame.draw.circle(buf, (*col, alpha // 2), (sz + 2, sz + 2), sz)
                inner = max(1, sz * 2 // 3)
                bright = tuple(min(255, c + 70) for c in col)
                pygame.draw.circle(buf, (*bright, alpha), (sz + 2, sz + 2), inner)

            elif ptype == "star":
                pts_s = [
                    (sz + 2, 2),
                    (sz + 2 + sz // 2, sz + 2),
                    (sz + 2, d - 2),
                    (sz + 2 - sz // 2, sz + 2),
                ]
                bright = tuple(min(255, c + 60) for c in col)
                pygame.draw.polygon(buf, (*bright, alpha), pts_s)

            surface.blit(buf, (pw - sz - 2, ph_y - sz - 2))

        # ── 3. Armor shape — วาดลง canvas ขนาดคงที่แล้ว blit ──────────
        style  = sd["style"]
        canvas = pygame.Surface((self._ARM_CW, self._ARM_CH), pygame.SRCALPHA)
        cx, cy = self._ARM_CX, self._ARM_CY
        if   style == "robe":    self._armor_robe(canvas, cx, cy - 11, c1, c2, c3, t)
        elif style == "leather": self._armor_leather(canvas, cx, cy - 11, c1, c2, c3)
        elif style == "chain":   self._armor_chain(canvas, cx, cy - 1, c1, c2, c3, t)
        elif style == "plate":   self._armor_plate(canvas, cx, cy, c1, c2, c3, t)
        elif style == "shadow":  self._armor_shadow(canvas, cx, cy - 1, c1, c2, c3, t)
        elif style == "dragon":  self._armor_dragon(canvas, cx, cy - 1, c1, c2, c3, t)
        elif style == "aegis":   self._armor_aegis(canvas, cx, cy, c1, c2, c3, t)
        elif style == "void":    self._armor_void(canvas, cx, cy - 1, c1, c2, c3, t)
        surface.blit(canvas, (sx - self._ARM_BLIT_OX, sy - self._ARM_BLIT_OY))

    # ── Per-armor draw routines ───────────────────────────────────────────────

    def _armor_robe(self, canvas, cx, cy, c1, c2, c3, t):
        """Cloth Robe — robe body with belt."""
        belt = (82, 62, 38)
        buckle = (c1[0]//2, c1[1]//2, c1[2]//2)
        # Robe body
        robe = pygame.Surface((53, 36), pygame.SRCALPHA)
        pts = [(4, 0),(49, 0),(53, 36),(0, 36)]
        pygame.draw.polygon(robe, (*c1, 255), pts)
        pygame.draw.polygon(robe, (*c2, 255), pts, 2)
        pygame.draw.line(robe, (*c2, 255), (26, 0), (26, 14), 1)
        canvas.blit(robe, (cx - 26, cy - 4))
        # Collar fold
        col_s = pygame.Surface((30, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(col_s, (*c3, 255), (0, 0, 30, 10))
        pygame.draw.ellipse(col_s, (*c2, 255), (0, 0, 30, 10), 1)
        canvas.blit(col_s, (cx - 15, cy - 5))
        # Belt
        belt_s = pygame.Surface((49, 5), pygame.SRCALPHA)
        pygame.draw.rect(belt_s, (*belt, 255), (0, 0, 49, 5), border_radius=2)
        canvas.blit(belt_s, (cx - 24, cy + 9))
        pygame.draw.rect(canvas, (*buckle, 255), (cx - 4, cy + 7, 8, 7), border_radius=1)

    def _armor_leather(self, canvas, cx, cy, c1, c2, c3):
        """Leather Armor — chest + shoulder pads + belt."""
        rivet = (155, 125, 55)
        # Chest
        chest = pygame.Surface((50, 26), pygame.SRCALPHA)
        pts = [(3, 0),(47, 0),(50, 26),(0, 26)]
        pygame.draw.polygon(chest, (*c1, 255), pts)
        pygame.draw.polygon(chest, (*c2, 255), pts, 2)
        pygame.draw.line(chest, (*c2, 255), (25, 0), (25, 26), 1)
        canvas.blit(chest, (cx - 25, cy - 4))
        # Belt strap
        belt = pygame.Surface((54, 6), pygame.SRCALPHA)
        pygame.draw.rect(belt, (*c2, 255), (0, 0, 54, 6), border_radius=2)
        canvas.blit(belt, (cx - 27, cy + 20))
        pygame.draw.rect(canvas, (*rivet, 255), (cx - 4, cy + 18, 8, 9), border_radius=2)

    def _armor_chain(self, canvas, cx, cy, c1, c2, c3, t):
        """Chainmail — interlocked rings + shimmer (no shoulder rings)."""
        lw, lh = 6, 4
        for row in range(8):
            for col in range(8):
                ox  = (row % 2) * 3
                lx  = cx - 23 + col * lw + ox
                ly  = cy - 14 + row * lh
                ring = pygame.Surface((lw + 2, lh + 2), pygame.SRCALPHA)
                pygame.draw.ellipse(ring, (*c1, 255), (0, 0, lw + 2, lh + 2))
                pygame.draw.ellipse(ring, (*c2, 255), (0, 0, lw + 2, lh + 2), 1)
                canvas.blit(ring, (lx, ly))
        # Shimmer highlight
        sa = int(50 + 40 * math.sin(t * 2.8))
        sh = pygame.Surface((44, 24), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (*c3, sa), (0, 0, 44, 24))
        canvas.blit(sh, (cx - 22, cy - 13))

    def _armor_plate(self, canvas, cx, cy, c1, c2, c3, t):
        """Plate Armor — breastplate + shine (no pauldrons)."""
        # Breastplate
        pl = pygame.Surface((48, 32), pygame.SRCALPHA)
        pts = [(5, 0),(43, 0),(48, 9),(48, 28),(24, 32),(0, 28),(0, 9)]
        pygame.draw.polygon(pl, (*c1, 255), pts)
        pygame.draw.line(pl, (*c2, 255), (24, 0), (24, 32), 2)   # center ridge
        pygame.draw.line(pl, (*c3, 255), (5, 3), (43, 3), 2)     # top shine
        pygame.draw.polygon(pl, (*c2, 255), pts, 1)
        canvas.blit(pl, (cx - 24, cy - 15))
        # Pulse shine
        pa2 = int(35 + 28 * math.sin(t * 1.8))
        shine = pygame.Surface((48, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(shine, (*c3, pa2), (0, 0, 48, 12))
        canvas.blit(shine, (cx - 24, cy - 14))

    def _armor_shadow(self, canvas, cx, cy, c1, c2, c3, t):
        """Shadow Cloak — short cloak (torso only), narrow fit."""
        # Cloak body — narrowed to 50px wide
        cl = pygame.Surface((55, 28), pygame.SRCALPHA)
        wave = int(3 * math.sin(t * 1.4))
        pts  = [(8 + wave, 0),(47 - wave, 0),(53, 28),(2, 28),(0, 14)]
        pygame.draw.polygon(cl, (*c2, 255), pts)
        for fx in (14, 27, 41):
            wv = int(2 * math.sin(t * 1.6 + fx * 0.25))
            pygame.draw.line(cl, (*c1, 255), (fx, 0), (fx + wv, 28), 1)
        pygame.draw.polygon(cl, (*c1, 255), pts, 1)
        canvas.blit(cl, (cx - 27, cy - 14))
        # Cloak collar trim
        trim = pygame.Surface((55, 9), pygame.SRCALPHA)
        pygame.draw.rect(trim, (*c3, 255), (0, 0, 55, 9), border_radius=3)
        canvas.blit(trim, (cx - 27, cy - 14))

    def _armor_dragon(self, canvas, cx, cy, c1, c2, c3, t):
        """Dragon Scale — chest scales only."""
        sw, sh = 11, 8
        rows = [
            (cx - 23, cy - 14, 6),
            (cx - 26, cy -  7, 6),
            (cx - 23, cy,      6),
        ]
        for rx, ry, cnt in rows:
            for i in range(cnt):
                lx = rx + i * (sw - 3)
                sc = pygame.Surface((sw + 2, sh + 2), pygame.SRCALPHA)
                pygame.draw.ellipse(sc, (*c1, 255), (0, 0, sw + 2, sh + 2))
                pygame.draw.ellipse(sc, (*c3, 255), (1, 1, sw,     sh // 2))
                pygame.draw.ellipse(sc, (*c2, 255), (0, 0, sw + 2, sh + 2), 1)
                canvas.blit(sc, (lx, ry))
        # Inner ember glow
        ga = int(28 + 22 * math.sin(t * 2.6))
        glow = pygame.Surface((54, 32), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (*c3, ga), (0, 0, 54, 32))
        canvas.blit(glow, (cx - 27, cy - 15))

    def _armor_aegis(self, canvas, cx, cy, c1, c2, c3, t):
        """Aegis Plate — legendary gold armor with holy cross emblem + radiance."""
        # Outer holy radiance (fitted to canvas)
        ra = int(38 + 28 * math.sin(t * 1.7))
        rad = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(rad, (*c1, ra // 3), (40, 40), 38)
        pygame.draw.circle(rad, (*c3, ra // 6), (40, 40), 28)
        canvas.blit(rad, (cx - 40, cy - 40))
        # Gold breastplate — wider
        pl = pygame.Surface((50, 34), pygame.SRCALPHA)
        pts = [(5, 0),(45, 0),(50, 9),(50, 30),(25, 34),(0, 30),(0, 9)]
        pygame.draw.polygon(pl, (*c1, 255), pts)
        # Engraved lines
        pygame.draw.line(pl, (*c3, 255), (5, 3),  (45, 3),  2)
        pygame.draw.line(pl, (*c3, 255), (25, 0),  (25, 34), 2)
        # Holy cross emblem
        cx_e, cy_e = 25, 16
        cross_col = (*c3, 255)
        for dx2, dy2, dx3, dy3 in [(-8,0,8,0),(0,-8,0,8)]:
            pygame.draw.line(pl, cross_col,
                             (cx_e + dx2, cy_e + dy2),
                             (cx_e + dx3, cy_e + dy3), 2)
        pygame.draw.circle(pl, (*c3, 255), (cx_e, cy_e), 4)
        pygame.draw.circle(pl, (*c2, 255), (cx_e, cy_e), 4, 1)
        # Ray burst
        for i in range(8):
            ang = t * 0.6 + i * math.pi / 4
            x1 = cx_e + int(math.cos(ang) * 5)
            y1 = cy_e + int(math.sin(ang) * 5)
            x2 = cx_e + int(math.cos(ang) * 11)
            y2 = cy_e + int(math.sin(ang) * 11)
            pygame.draw.line(pl, (*c3, 255), (x1, y1), (x2, y2), 1)
        pygame.draw.polygon(pl, (*c2, 255), pts, 1)
        canvas.blit(pl, (cx - 25, cy - 16))
        # Pulse shine band
        pa2 = int(42 + 35 * math.sin(t * 2.0))
        sh_s = pygame.Surface((50, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(sh_s, (*c3, pa2), (0, 0, 50, 14))
        canvas.blit(sh_s, (cx - 25, cy - 15))

    def _armor_void(self, canvas, cx, cy, c1, c2, c3, t):
        """Void Robe — short cloak (torso) + sigil + orbiting orbs."""
        # Void cloak — wider
        cl = pygame.Surface((76, 30), pygame.SRCALPHA)
        wave = int(3 * math.sin(t * 1.2))
        pts  = [(10 + wave, 0),(66 - wave, 0),(73, 30),(3, 30),(0, 15)]
        pygame.draw.polygon(cl, (*c2, 255), pts)
        for i in range(10):
            hx = int(5 + (i * 6.3) % 66)
            hy = int(3 + (i * 8.7) % 26)
            pygame.draw.circle(cl, (0, 0, 0, 255), (hx, hy), 2)
            pygame.draw.circle(cl, (*c3, 255),     (hx, hy), 1)
        pygame.draw.polygon(cl, (*c1, 255), pts, 1)
        canvas.blit(cl, (cx - 38, cy - 13))
        # Rotating void sigil on chest
        sig = pygame.Surface((30, 30), pygame.SRCALPHA)
        for i in range(6):
            ang = t * 0.9 + i * math.pi / 3
            x1  = 15 + int(math.cos(ang) * 5)
            y1  = 15 + int(math.sin(ang) * 5)
            x2  = 15 + int(math.cos(ang + math.pi) * 11)
            y2  = 15 + int(math.sin(ang + math.pi) * 11)
            pygame.draw.line(sig, (*c3, 255), (x1, y1), (x2, y2), 1)
        pygame.draw.circle(sig, (*c1, 255), (15, 15), 4)
        pygame.draw.circle(sig, (*c3, 255), (15, 15), 2)
        canvas.blit(sig, (cx - 15, cy - 7))
        # 3 orbiting void orbs (clamped to canvas bounds)
        for i in range(3):
            ang      = t * 1.6 + i * (math.pi * 2 / 3)
            orb_x    = cx + int(math.cos(ang) * 30)
            orb_y    = cy + int(math.sin(ang) * 18)
            orb_a    = int(155 + 90 * math.sin(t * 2.2 + i * 1.4))
            orb_sz   = 5 + int(2 * math.sin(t * 3.1 + i))
            ob       = pygame.Surface((orb_sz * 2 + 6, orb_sz * 2 + 6), pygame.SRCALPHA)
            bright   = tuple(min(255, c + 80) for c in c3)
            pygame.draw.circle(ob, (*c3,  orb_a // 2), (orb_sz + 3, orb_sz + 3), orb_sz)
            pygame.draw.circle(ob, (*bright, orb_a),   (orb_sz + 3, orb_sz + 3), orb_sz // 2)
            canvas.blit(ob, (orb_x - orb_sz - 3, orb_y - orb_sz - 3))

    def can_use_mana(self, amount):
        return self.mana >= amount

    def use_mana(self, amount):
        if self.can_use_mana(amount):
            self.mana -= amount
            self._mana_regen_timer = 0.0   # reset delay หลังยิง
            return True
        return False