"""
item.py  –  Item base class and subclasses (Weapon, Armor, Accessory)
Updated so accessory/weapon stat bonuses map to the Player's new attributes
(hp/armor/mana/atk/etc.). Legacy stat keys (STR/AGI/VIT/INT/DEX/LUK)
are mapped sensibly.
"""
import random
from constants import (
    RARITY_COLORS, WHITE, GRAY
)

# Mapping legacy RPG stats to new attributes.
_LEGACY_MAP = {
    "STR": ("atk", lambda v: v),          # +STR -> +atk
    "VIT": ("max_hp", lambda v: v * 8),   # +VIT -> +max_hp
    "AGI": ("move_speed", lambda v: v * 0.06),  # small speed
    "INT": ("max_mana", lambda v: v * 8),       # +INT -> +mana
    "DEX": ("crit_chance", lambda v: v * 0.001),# small crit
    "LUK": ("drop_luck", lambda v: v * 0.01),   # soft luck (unused)
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
        lines = [
            f"{self.name}  [{self.rarity}]",
            f"Type: {self.item_type.capitalize()}",
            self.description,
            f"Sell: {self.sell_price} G",
        ]
        return lines

    def compare(self, other):
        """Return dict of stat differences vs. another item."""
        return {}

    def apply_effect(self, player):
        """Called when item is equipped. If item has 'stat_bonus' dict,
        attempt to apply values intelligently to new player attributes.
        """
        if not hasattr(self, "stat_bonus") or not self.stat_bonus:
            return
        for key, val in self.stat_bonus.items():
            # If player already has the attribute, add directly
            if hasattr(player, key):
                current = getattr(player, key)
                try:
                    setattr(player, key, current + val)
                except Exception:
                    pass
                continue
            # Legacy mapping
            if key in _LEGACY_MAP:
                attr, fn = _LEGACY_MAP[key]
                add = fn(val)
                if hasattr(player, attr):
                    setattr(player, attr, getattr(player, attr) + add)
            else:
                # try common names: hp, max_hp, armor, max_armor, mana, max_mana, atk, crit_chance
                if hasattr(player, key):
                    setattr(player, key, getattr(player, key) + val)

    def remove_effect(self, player):
        """Revert the effects applied by apply_effect. Mirrors the logic above."""
        if not hasattr(self, "stat_bonus") or not self.stat_bonus:
            return
        for key, val in self.stat_bonus.items():
            if hasattr(player, key):
                setattr(player, key, getattr(player, key) - val)
                continue
            if key in _LEGACY_MAP:
                attr, fn = _LEGACY_MAP[key]
                add = fn(val)
                if hasattr(player, attr):
                    setattr(player, attr, getattr(player, attr) - add)
            else:
                if hasattr(player, key):
                    setattr(player, key, getattr(player, key) - val)


class Weapon(Item):
    """Ranged or melee weapon. Each weapon belongs to one class only."""

    def __init__(self, name, damage, fire_rate, bullet_speed, rarity, color,
                 description, weapon_class="Any", stat_bonus=None):
        price = {"Common": 25, "Rare": 70, "Epic": 160, "Legendary": 380}.get(rarity, 25)
        super().__init__(name, "weapon", rarity, color, description, price)
        self.damage       = damage
        self.fire_rate    = fire_rate
        self.bullet_speed = bullet_speed
        self.is_melee     = (fire_rate == 0)
        self.weapon_class = weapon_class
        self.stat_bonus   = stat_bonus or {}   # e.g. {"STR":6,"VIT":3}

    def can_equip(self, player):
        if self.weapon_class == "Any":
            return True, ""
        if player.char_class != self.weapon_class:
            return False, f"Requires {self.weapon_class} class!"
        return True, ""

    def get_tooltip(self):
        lines = super().get_tooltip()
        lines.insert(2, f"Damage: {self.damage}")
        lines.insert(3, f"Class:  {self.weapon_class}")
        if self.is_melee:
            lines.insert(4, "Style: Melee")
        else:
            lines.insert(4, f"Rate: {self.fire_rate:.1f}/s  Spd: {self.bullet_speed}")
        if self.stat_bonus:
            bonus_str = "  ".join(f"+{v}{k}" for k, v in self.stat_bonus.items())
            lines.insert(5, f"Bonus: {bonus_str}")
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
        self.stat_bonus  = stat_bonus   # dict e.g. {"STR": 3}
        self.effect_desc = effect_desc

    def get_tooltip(self):
        lines = super().get_tooltip()
        bonus_str = "  ".join(f"+{v} {k}" for k, v in self.stat_bonus.items() if v > 0)
        if bonus_str:
            lines.insert(2, f"Bonus: {bonus_str}")
        return lines
    def make_starting_weapon(char_class):

        if char_class == "Warrior":
            return Weapon(
                "Iron Sword",
                18,
                0,
                0,
                "Common",
                (180,180,180),
                "Starter sword",
                "Warrior",
                {"STR":3,"VIT":2}
            )

        elif char_class == "Mage":
            return Weapon(
                "Magic Wand",
                16,
                0.5,
                8,
                "Common",
                (100,180,255),
                "Starter wand",
                "Mage",
                {"INT":3,"DEX":2}
            )

        else:
            return Weapon(
                "Short Bow",
                15,
                0.45,
                7,
                "Common",
                (139,90,43),
                "Starter bow",
                "Ranger",
                {"DEX":3,"AGI":2}
            )