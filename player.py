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

def _load_sprite():
    global _SPRITE, _SPRITE_FLIP
    if _SPRITE is not None:
        return
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Sausageguy.png")
    try:
        img = pygame.image.load(path).convert_alpha()
        _SPRITE      = pygame.transform.smoothscale(img, (72, 72))
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

        if char_class == "Ranger":
            self.crit_chance += 0.12
        elif char_class == "Rogue":
            self.crit_chance += 0.10
            self.crit_mult    = 2.5

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
        self.skill_cd       = 0.0

        self.iframe_timer = 0.0
        self.IFRAME_DUR   = 0.35

        self.total_damage_dealt = 0
        self.items_collected    = 0
        self.level = 1

        self.color   = cfg["color"]
        self.passive = cfg.get("passive", "")

        self._armor_regen_timer = 0.0
        self._mana_regen_timer  = 0.0

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
        dodge = 0.11 if self.char_class == "Rogue" else 0.03
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
        if self.char_class == "Ranger":
            spd *= 1.2
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

        if self.skill_cd > 0:
            self.skill_cd = max(0.0, self.skill_cd - dt)

        self._armor_regen_timer += dt
        if self._armor_regen_timer > 1.0:
            self.armor = min(self.max_armor, self.armor + 12.0 * dt)

        self._mana_regen_timer += dt
        if self._mana_regen_timer > 0.2:
            self.mana = min(self.max_mana, self.mana + 10 * dt)

    def draw(self, surface, cam_x=0, cam_y=0):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        r  = self.RADIUS

        if _SPRITE is not None:
            sprite = _SPRITE if self.facing_right else _SPRITE_FLIP
            if self.iframe_timer > 0:
                flash = sprite.copy()
                flash.fill((255, 80, 80, 160), special_flags=pygame.BLEND_RGBA_MULT)
                sprite = flash
            w, h = sprite.get_size()
            surface.blit(sprite, (sx - w // 2, sy - h // 2))
        else:
            col = (255, 80, 80) if self.iframe_timer > 0 else self.color
            pygame.draw.circle(surface, col, (sx, sy), r)
            pygame.draw.circle(surface, WHITE, (sx, sy), r, 2)

        ex = sx + int(math.cos(self.facing_angle) * (r + 6))
        ey = sy + int(math.sin(self.facing_angle) * (r + 6))
        pygame.draw.circle(surface, (255, 255, 100), (ex, ey), 4)

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
