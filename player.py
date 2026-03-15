"""
player.py  –  Player class (converted to HP/Armor/Mana system)
Replaces the old Ragnarok-style stat system with a simpler
HP / Armor (shield) / Mana model similar to Soul Knight.
"""
import math
import random
import pygame
from constants import (
    CLASSES, EXP_BASE, TILE,
    SCREEN_W, SCREEN_H, HUD_H, WHITE, RED, GREEN,
    YELLOW, GOLD, BLUE, PURPLE, GRAY
)
from item import make_starting_weapon

# Random instance used by damage/crit variance
_rnd = random.Random()

class Player:
    """
    Player with: hp, armor (shield that absorbs damage first), mana.
    Keeps some compatibility methods expected by other modules:
      - recalc_derived() : recalculates atk/matk/crit/fire rate from equipment + class
      - allocate_stat() : kept as no-op (stat system removed)
    """

    RADIUS = 16

    def __init__(self, name, char_class):
        self.name       = name
        self.char_class = char_class
        cfg             = CLASSES[char_class]

        # Position (centre of play area)
        play_h = SCREEN_H - HUD_H
        self.x  = SCREEN_W / 2
        self.y  = play_h / 2
        self.speed = cfg["speed"]

        # Leveling
        self.level = 1
        self.exp   = 0
        self.exp_next = self._exp_for_level(2)
        self.skill_cd = 0
        self.skill_data = cfg.get("skill", {})

        # Core resources (Soul Knight style)
        self.max_hp = cfg["base_hp"]
        self.hp = self.max_hp

        # Armor acts as a rechargeable shield
        self.max_armor = 80
        self.armor = self.max_armor

        # Mana/energy for skills
        self.max_mana = 120
        self.mana = self.max_mana

        # Equipment slots
        self.equipment = {
            "weapon":    make_starting_weapon(char_class),
            "armor":     None,
            "accessory": None,
        }

        # Derived combat stats (calculated from equipment + class)
        self.atk        = 10
        self.matk       = 8
        self.crit_chance = 0.05
        self.crit_mult   = 1.5
        self.move_speed  = self.speed
        self.aspd_mult   = 1.0

        self.recalc_derived()

        # Inventory (list of Items)
        self.inventory: list = []
        self.gold     = 0
        self.alive    = True

        # Shooting state
        self.shoot_cooldown = 0.0   # seconds remaining
        self.melee_active   = False
        self.melee_timer    = 0.0
        self.melee_radius   = 55
        self.facing_angle   = 0.0   # radians, toward mouse

        # Iframe (invincibility after hit)
        self.iframe_timer = 0.0
        self.IFRAME_DUR   = 0.35

        # Stats tracking for StatsTracker
        self.total_damage_dealt = 0
        self.items_collected    = 0
        self.steps              = 0

        # Color for rendering
        self.color = cfg["color"]

        # Passive flag
        self.passive = cfg.get("passive", "")

        # Regen timers
        self._armor_regen_timer = 0.0
        self._mana_regen_timer = 0.0

    # ── Derived stat recalculation ───────────────────────────
    def recalc_derived(self):
        """Compute atk/matk/crit/fire-rate and move_speed from equipment + class.
        This keeps compatibility with other modules that call recalc_derived().
        """
        cfg = CLASSES[self.char_class]
        base_stats = cfg.get("base_stats", {})
        base_str = base_stats.get("STR", 2)
        base_int = base_stats.get("INT", 2)
        base_agi = base_stats.get("AGI", 2)
        base_dex = base_stats.get("DEX", 2)
        base_luk = base_stats.get("LUK", 1)

        wpn = self.equipment.get("weapon")
        wpn_dmg = wpn.damage if wpn else 10
        arm = self.equipment.get("armor")
        arm_def = arm.defense if arm else 0

        # Simple formulas: weapon dmg + base STR/INT
        self.atk  = max(1, int(wpn_dmg + base_str))
        self.matk = max(1, int(wpn_dmg + base_int))

        # Crit: base 5% + small LUK/DEX contribution; Ranger keeps the passive
        self.crit_chance = 0.05 + base_luk * 0.002 + base_dex * 0.0005
        if self.char_class == "Ranger":
            self.crit_chance += 0.10
        self.crit_chance = min(0.6, self.crit_chance)

        # Crit multiplier (slight LUK scaling)
        self.crit_mult = 1.5 + base_luk * 0.003

        # Attack speed multiplier simplified: small benefit from AGI
        self.aspd_mult = min(2.0, 1.0 + base_agi * 0.005)

        # Move speed base + class speed
        self.move_speed = self.speed

    # ── Leveling ─────────────────────────────────────────────
    @staticmethod
    def _exp_for_level(lv):
        return int(EXP_BASE * (lv ** 1.5))

    def gain_exp(self, amount):
        self.exp += amount
        leveled = False
        while self.exp >= self.exp_next:
            self.exp -= self.exp_next
            self.level += 1
            self.exp_next = self._exp_for_level(self.level + 1)
            # No stat points in new system; instead give small resource restores
            self.hp = min(self.max_hp, self.hp + 20)
            self.mana = min(self.max_mana, self.mana + 20)
            leveled = True
        return leveled

    def allocate_stat(self, stat):
        """No-op in new system to maintain compatibility with UI calls."""
        return False

    # ── Equipment ─────────────────────────────────────────────
    def equip(self, item):
        slot = item.item_type
        old  = self.equipment.get(slot)
        if old and hasattr(old, "remove_effect"):
            old.remove_effect(self)
        self.equipment[slot] = item
        if hasattr(item, "apply_effect"):
            item.apply_effect(self)
        self.recalc_derived()
        return old   # return old item so caller can add to inventory

    def collect_item(self, item):
        self.inventory.append(item)
        self.items_collected += 1

    # ── Combat / Damage ──────────────────────────────────────
    def take_damage(self, raw_damage):
        """Apply damage: armor absorbs first, leftover to HP.
        Returns:
          -1 => missed/dodged
           0 => absorbed by armor (or iframe)
           n (>0) => actual HP lost
        """
        if self.iframe_timer > 0:
            return 0

        # Simple dodge mechanic: small flat chance (kept small)
        # Keep parity with previous system: use small base chance
        dodge_chance = 0.03
        if _rnd.random() < dodge_chance:
            return -1

        # Warrior passive: reduce incoming damage by 10%
        if self.char_class == "Warrior":
            raw_damage = int(raw_damage * 0.9)

        leftover = raw_damage

        # Armor (shield) absorbs flat amount first
        if self.armor > 0:
            absorbed = min(self.armor, leftover)
            self.armor -= absorbed
            leftover -= absorbed

        # Remaining reduces HP
        hp_lost = 0
        if leftover > 0:
            self.hp = max(0, self.hp - leftover)
            hp_lost = leftover

        self.iframe_timer = self.IFRAME_DUR
        if self.hp <= 0:
            self.alive = False

        return hp_lost

    def calc_damage(self):
        """Return damage for one attack, with minor variance and crit."""
        wpn  = self.equipment.get("weapon")
        # Use matk for mage ranged, atk for everything else
        if self.char_class == "Mage" and wpn and not wpn.is_melee:
            base = self.matk
        else:
            base = self.atk
        variance = _rnd.uniform(0.95, 1.05)
        base = max(1, int(base * variance))

        crit = (_rnd.random() < self.crit_chance)
        dmg  = int(base * (self.crit_mult if crit else 1.0))
        dmg  = max(1, dmg)
        self.total_damage_dealt += dmg
        return dmg, crit

    def get_bullet_speed(self):
        wpn = self.equipment.get("weapon")
        if not wpn or wpn.is_melee:
            return 0
        spd = wpn.bullet_speed
        if self.char_class == "Ranger":
            spd *= 1.2
        return spd

    def get_fire_rate(self):
        wpn = self.equipment.get("weapon")
        if not wpn or wpn.is_melee:
            return 0
        return wpn.fire_rate * self.aspd_mult

    @property
    def weapon(self):
        return self.equipment.get("weapon")

    # ── Movement ─────────────────────────────────────────────
    def move(self, dx, dy, walls):
        if dx == 0 and dy == 0:
            return
        length = math.hypot(dx, dy)
        dx /= length
        dy /= length
        spd = self.move_speed
        nx = self.x + dx * spd
        ny = self.y + dy * spd
        # basic collision with walls (AABB)
        r = self.RADIUS
        can_x = True
        can_y = True
        for wall in walls:
            if (wall.left < nx + r and wall.right  > nx - r and
                    wall.top  < self.y + r and wall.bottom > self.y - r):
                can_x = False
            if (wall.left < self.x + r and wall.right  > self.x - r and
                    wall.top  < ny + r and wall.bottom > ny - r):
                can_y = False
        if can_x:
            self.x = nx
        if can_y:
            self.y = ny

    # ── Update (regen) ───────────────────────────────────────
    def update(self, dt, walls, mouse_pos=None):
        # Iframe timer
        if self.iframe_timer > 0:
            self.iframe_timer -= dt

        # Armor regenerates slowly after short delay
        self._armor_regen_timer += dt
        if self._armor_regen_timer > 1.0:
            self.armor = min(self.max_armor, self.armor + 12 * dt)

        # Mana regen
        self._mana_regen_timer += dt
        if self._mana_regen_timer > 0.2:
            self.mana = min(self.max_mana, self.mana + 10 * dt)

    # ── Skills / resource helpers ────────────────────────────
    def can_use_mana(self, amount):
        return self.mana >= amount

    def use_mana(self, amount):
        if self.can_use_mana(amount):
            self.mana -= amount
            return True
        return False