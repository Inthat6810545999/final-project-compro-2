"""
item.py  –  Item base class and subclasses (Weapon, Armor, Accessory)
Factory functions: make_weapon, make_armor, make_accessory,
                   make_random_item, make_starting_weapon
"""
import random
from constants import (
    RARITY_COLORS, WHITE, GRAY,
    WEAPON_POOL, ARMOR_POOL, ACCESSORY_POOL,
)

# Mapping legacy RPG stats to new attributes.
_LEGACY_MAP = {
    "STR": ("atk",        lambda v: v),
    "VIT": ("max_hp",     lambda v: v * 8),
    "AGI": ("move_speed", lambda v: v * 0.06),
    "INT": ("max_mana",   lambda v: v * 8),
    "DEX": ("crit_chance",lambda v: v * 0.001),
    "LUK": ("drop_luck",  lambda v: v * 0.01),
}


class Item:
    """Base class for all collectible items."""

    def __init__(self, name, item_type, rarity, color, description, sell_price):
        self.name        = name
        self.item_type   = item_type   # "weapon" | "armor" | "accessory"
        self.rarity      = rarity
        self.color       = color
        self.description = description
        self.sell_price  = sell_price

    @property
    def rarity_color(self):
        return RARITY_COLORS.get(self.rarity, WHITE)

    def get_tooltip(self):
        return [
            f"{self.name}  [{self.rarity}]",
            f"Type: {self.item_type.capitalize()}",
            self.description,
            f"Sell: {self.sell_price} G",
        ]

    def compare(self, other):
        return {}

    def apply_effect(self, player):
        if not hasattr(self, "stat_bonus") or not self.stat_bonus:
            return
        for key, val in self.stat_bonus.items():
            if hasattr(player, key):
                try:
                    setattr(player, key, getattr(player, key) + val)
                except Exception:
                    pass
                continue
            if key in _LEGACY_MAP:
                attr, fn = _LEGACY_MAP[key]
                if hasattr(player, attr):
                    setattr(player, attr, getattr(player, attr) + fn(val))

    def remove_effect(self, player):
        if not hasattr(self, "stat_bonus") or not self.stat_bonus:
            return
        for key, val in self.stat_bonus.items():
            if hasattr(player, key):
                setattr(player, key, getattr(player, key) - val)
                continue
            if key in _LEGACY_MAP:
                attr, fn = _LEGACY_MAP[key]
                if hasattr(player, attr):
                    setattr(player, attr, getattr(player, attr) - fn(val))


class Weapon(Item):
    """Ranged or melee weapon."""

    def __init__(self, name, damage, fire_rate, bullet_speed, rarity, color,
                 description, weapon_class="Any", stat_bonus=None):
        price = {"Common": 25, "Rare": 70, "Epic": 160, "Legendary": 380}.get(rarity, 25)
        super().__init__(name, "weapon", rarity, color, description, price)
        self.damage       = damage
        self.fire_rate    = fire_rate
        self.bullet_speed = bullet_speed
        self.is_melee     = (fire_rate == 0)
        self.weapon_class = weapon_class
        self.stat_bonus   = stat_bonus or {}

    def can_equip(self, player):
        # Soul Knight style: any character can pick up any weapon
        return True, ""

    def get_tooltip(self):
        lines = super().get_tooltip()
        lines.insert(2, f"Damage: {self.damage}")
        lines.insert(3, f"Class:  {self.weapon_class}")
        lines.insert(4, "Style: Melee" if self.is_melee else f"Rate: {self.fire_rate:.1f}/s  Spd: {self.bullet_speed}")
        if self.stat_bonus:
            lines.insert(5, "Bonus: " + "  ".join(f"+{v}{k}" for k, v in self.stat_bonus.items()))
        return lines

    def compare(self, other):
        if not isinstance(other, Weapon):
            return {}
        return {"damage": self.damage - other.damage}


class Armor(Item):
    """Body armor providing defense."""

    def __init__(self, name, defense, rarity, color, description):
        price = {"Common": 20, "Rare": 60, "Epic": 140, "Legendary": 350}.get(rarity, 20)
        super().__init__(name, "armor", rarity, color, description, price)
        self.defense = defense

    def get_tooltip(self):
        lines = super().get_tooltip()
        lines.insert(2, f"Defense: {self.defense}")
        return lines

    def compare(self, other):
        if not isinstance(other, Armor):
            return {}
        return {"defense": self.defense - other.defense}


class Accessory(Item):
    """Ring / amulet / boots with stat bonuses."""

    def __init__(self, name, rarity, color, effect_desc, stat_bonus):
        price = {"Common": 30, "Rare": 80, "Epic": 180, "Legendary": 400}.get(rarity, 30)
        super().__init__(name, "accessory", rarity, color, effect_desc, price)
        self.stat_bonus  = stat_bonus
        self.effect_desc = effect_desc

    def get_tooltip(self):
        lines = super().get_tooltip()
        bonus_str = "  ".join(f"+{v} {k}" for k, v in self.stat_bonus.items() if v > 0)
        if bonus_str:
            lines.insert(2, f"Bonus: {bonus_str}")
        return lines


# ── Module-level factory functions ───────────────────────────────────────────

def make_starting_weapon(char_class):
    """Return the starter gun for a given class."""
    if char_class == "Mage":
        return Weapon("Magic Wand",  16, 0.55, 9,  "Common", (100, 180, 255),
                      "Pierces 1 enemy", "Any", {})
    elif char_class == "Necromancer":
        return Weapon("Soul Staff",  14, 0.60, 8,  "Common", (60, 220, 120),
                      "Dark bolts", "Any", {})
    elif char_class == "Ranger":
        return Weapon("Short Bow",   15, 0.70, 11, "Common", (139, 90, 43),
                      "Fast arrows", "Any", {})
    else:  # Rogue
        return Weapon("Hand Pistol", 13, 0.80, 10, "Common", (160, 160, 180),
                      "Rapid fire", "Any", {})


def make_weapon(rarity="Common", weapon_class=None):
    """Pick a random ranged Weapon from WEAPON_POOL matching rarity."""
    pool = [w for w in WEAPON_POOL if w[4] == rarity and w[2] > 0]  # only ranged (fire_rate > 0)
    if not pool:
        pool = [w for w in WEAPON_POOL if w[2] > 0]  # fallback: any ranged
    if not pool:
        pool = WEAPON_POOL
    entry = random.choice(pool)
    # Force weapon_class to "Any" — Soul Knight style
    return Weapon(entry[0], entry[1], entry[2], entry[3],
                  entry[4], entry[5], entry[6], "Any", entry[8])


def make_armor(rarity="Common"):
    """Pick a random Armor from ARMOR_POOL matching rarity."""
    pool = [a for a in ARMOR_POOL if a[2] == rarity]
    if not pool:
        pool = ARMOR_POOL
    entry = random.choice(pool)
    # entry: (name, defense, rarity, color, description)
    return Armor(entry[0], entry[1], entry[2], entry[3], entry[4])


def make_accessory(rarity="Common"):
    """Pick a random Accessory from ACCESSORY_POOL matching rarity."""
    pool = [a for a in ACCESSORY_POOL if a[1] == rarity]
    if not pool:
        pool = ACCESSORY_POOL
    entry = random.choice(pool)
    # entry: (name, rarity, color, effect_desc, stat_bonus)
    return Accessory(entry[0], entry[1], entry[2], entry[3], entry[4])


def make_random_item(luk_bonus=0):
    """Return a random item (weapon/armor/accessory) with rarity weighted by luk_bonus."""
    # Higher luk_bonus = better rarity odds
    weights = {
        "Common":    max(1, 50 - luk_bonus * 2),
        "Rare":      20 + luk_bonus,
        "Epic":      8  + luk_bonus // 2,
        "Legendary": 2  + luk_bonus // 5,
    }
    rarities = list(weights.keys())
    wts      = [weights[r] for r in rarities]
    rarity   = random.choices(rarities, weights=wts, k=1)[0]

    item_type = random.choice(["weapon", "armor", "accessory"])
    if item_type == "weapon":
        return make_weapon(rarity)
    elif item_type == "armor":
        return make_armor(rarity)
    else:
        return make_accessory(rarity)
