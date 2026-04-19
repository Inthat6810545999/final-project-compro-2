"""
player.py  –  Player (Soul Knight style: no base_stats, no leveling, weapon = damage source)
"""
import math
import random
import os
import pygame
from pygame.locals import K_w, K_a, K_s, K_d, K_UP, K_DOWN, K_LEFT, K_RIGHT
from constants import CLASSES, EXP_BASE, SCREEN_W, SCREEN_H, HUD_H, WHITE, RED, GOLD, CYAN
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
        self.max_mana  = cfg.get("max_mana", 120)
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
        self.level = 1

        self.color   = cfg["color"]
        self.passive = cfg.get("passive", "")

        self._armor_regen_timer = 0.0
        # No passive mana regen — mana is recovered by killing enemies

        # stat_points kept as 0 for UI compat
        self.stat_points = 0

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

    def equip(self, item):
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

    def update(self, dt, walls, mouse_pos=None):
        if self.iframe_timer > 0:
            self.iframe_timer -= dt

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

    def draw(self, surface, cam_x=0, cam_y=0):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        r  = self.RADIUS

        # Drop shadow — at character feet (character sits in lower ~80% of PNG)
        # With 94px sprite: feet ≈ sy + 34, body width ≈ 52px
        feet_y  = sy + 34
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

    def can_use_mana(self, amount):
        return self.mana >= amount

    def use_mana(self, amount):
        if self.can_use_mana(amount):
            self.mana -= amount
            return True
        return False

    def gain_exp(self, amount):
        return False

    def allocate_stat(self, stat):
        return False

    def recalc_derived(self):
        pass