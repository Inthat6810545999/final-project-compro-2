"""
constants.py  –  All game-wide constants and configuration
"""

# ── Screen ────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1920, 1080
FPS = 60
TITLE = "Sausage Man: Legends of Midgard"

# ── Tile ─────────────────────────────────────────────────────
TILE      = 72
ROOM_COLS = 17
ROOM_ROWS = 13

# FIX: export map dimensions so bullet.py can compute correct world bounds
MAP_W = 32   # tiles (mirrors Stage.MAP_W)
MAP_H = 24   # tiles (mirrors Stage.MAP_H)

# ── Colors ───────────────────────────────────────────────────
BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
GRAY       = (100, 100, 100)
DARK_GRAY  = (40,  40,  40)
LIGHT_GRAY = (180, 180, 180)
RED        = (220, 50,  50)
DARK_RED   = (139, 0,   0)
GREEN      = (50,  200, 80)
DARK_GREEN = (0,   120, 40)
BLUE       = (50,  100, 220)
LIGHT_BLUE = (100, 180, 255)
CYAN       = (0,   220, 220)
YELLOW     = (255, 220, 0)
ORANGE     = (255, 140, 0)
PURPLE     = (160, 32,  240)
PINK       = (255, 105, 180)
GOLD       = (255, 215, 0)
BROWN      = (139, 90,  43)
DARK_BROWN = (80,  50,  20)

# Rarity colors
RARITY_COLORS = {
    "Common":    LIGHT_GRAY,
    "Rare":      LIGHT_BLUE,
    "Epic":      PURPLE,
    "Legendary": GOLD,
}

# ── Game States ───────────────────────────────────────────────
STATE_MENU       = "menu"
STATE_CLASS_SEL  = "class_select"
STATE_PLAYING    = "playing"
STATE_INVENTORY  = "inventory"
STATE_PAUSED     = "paused"
STATE_GAME_OVER  = "game_over"
STATE_VICTORY    = "victory"
STATE_SHOP       = "shop"
STATE_STATS      = "stats"
STATE_LEVEL_UP   = "level_up"

# ── Player classes ────────────────────────────────────────────
CLASSES = {
    "Mage": {
        "color": (140, 50, 220),
        "base_hp": 110,
        "max_armor": 70,
        "max_mana": 180,
        "speed": 3.2,
        "base_damage": 18,
        "fire_rate": 0.55,
        "bullet_speed": 9,
        "description": "Arcane spellcaster. Bullets pierce 1 enemy.",
        "passive": "Arcane Mind: Bullets pierce 1 enemy.",
        "weapon_class": "Any",
    },
    "Necromancer": {
        "color": (60, 180, 120),
        "base_hp": 120,
        "max_armor": 60,
        "max_mana": 160,
        "speed": 3.0,
        "base_damage": 16,
        "fire_rate": 0.60,
        "bullet_speed": 8,
        "description": "Dark summoner. Each kill restores HP and Mana.",
        "passive": "Soul Drain: Each kill restores 8 HP and 6 Mana.",
        "weapon_class": "Any",
    },
    "Ranger": {
        "color": (50, 190, 80),
        "base_hp": 120,
        "max_armor": 80,
        "max_mana": 100,
        "speed": 4.0,
        "base_damage": 15,
        "fire_rate": 0.70,
        "bullet_speed": 11,
        "description": "Swift hunter. High crit and bullet speed.",
        "passive": "Eagle Eye: +15% crit. Bullets move 20% faster.",
        "weapon_class": "Any",
    },
    "Rogue": {
        "color": (80, 160, 220),
        "base_hp": 110,
        "max_armor": 65,
        "max_mana": 110,
        "speed": 4.5,
        "base_damage": 14,
        "fire_rate": 0.80,
        "bullet_speed": 10,
        "description": "Nimble trickster. +8% dodge. Gold drops +30%.",
        "passive": "Shadow Step: +8% dodge. Crits deal ×2.5.",
        "weapon_class": "Any",
    },
}

# ── Stages ───────────────────────────────────────────────────
STAGE_CONFIGS = [
    {"id": 0, "name": "Forest of Trials",   "theme": "forest",  "color": DARK_GREEN, "enemy_types": ["Slime", "Wolf"],           "boss": "Elder Treant",      "elite_shooter": "GunnerElite"},
    {"id": 1, "name": "Dungeon of Shadows",  "theme": "dungeon", "color": DARK_GRAY,  "enemy_types": ["Skeleton", "Bat"],         "boss": "Bone Overlord",     "elite_shooter": "SniperElite"},
    {"id": 2, "name": "Volcanic Fortress",   "theme": "volcano", "color": DARK_RED,   "enemy_types": ["FireImp", "Golem"],        "boss": "Lava Titan",        "elite_shooter": "BurstElite"},
    {"id": 3, "name": "Sky Citadel",         "theme": "sky",     "color": LIGHT_BLUE, "enemy_types": ["Harpy", "StormMage"],      "boss": "Storm Sovereign",   "elite_shooter": "MissileElite"},
    {"id": 4, "name": "Final Chamber",       "theme": "chaos",   "color": PURPLE,     "enemy_types": ["EliteHybrid", "Wraith"],   "boss": "Demon King Baldr",  "elite_shooter": "OmniElite"},
]

# ── Enemy stats ───────────────────────────────────────────────
ENEMY_DATA = {
    "Slime":      {"hp": 22,  "atk": 4,  "speed": 1.3, "exp": 10,  "color": GREEN,      "size": 20, "ai": "shoot", "range": 180, "shoot": True},
    "Wolf":       {"hp": 35,  "atk": 7,  "speed": 2.2, "exp": 15,  "color": GRAY,       "size": 22, "ai": "shoot", "range": 160, "shoot": True},
    "Skeleton":   {"hp": 38,  "atk": 9,  "speed": 1.5, "exp": 18,  "color": WHITE,      "size": 22, "ai": "shoot", "range": 200, "shoot": True},
    "Bat":        {"hp": 18,  "atk": 6,  "speed": 2.8, "exp": 12,  "color": PURPLE,     "size": 16, "ai": "shoot", "range": 150, "shoot": True},
    "FireImp":    {"hp": 45,  "atk": 10, "speed": 2.0, "exp": 22,  "color": ORANGE,     "size": 20, "ai": "shoot", "range": 200, "shoot": True},
    "Golem":      {"hp": 100, "atk": 16, "speed": 0.9, "exp": 30,  "color": BROWN,      "size": 30, "ai": "shoot", "range": 140, "shoot": True},
    "Harpy":      {"hp": 42,  "atk": 11, "speed": 3.2, "exp": 25,  "color": CYAN,       "size": 20, "ai": "shoot", "range": 180, "shoot": True},
    "StormMage":  {"hp": 55,  "atk": 14, "speed": 1.4, "exp": 32,  "color": LIGHT_BLUE, "size": 22, "ai": "shoot", "range": 250, "shoot": True},
    "EliteHybrid":{"hp": 100, "atk": 22, "speed": 2.8, "exp": 40,  "color": RED,        "size": 24, "ai": "shoot", "range": 200, "shoot": True},
    "Wraith":     {"hp": 85,  "atk": 20, "speed": 2.0, "exp": 35,  "color": PURPLE,     "size": 22, "ai": "shoot", "range": 190, "shoot": True},
    # ── Elite Shooters ────────────────────────────────────────────
    "GunnerElite":  {"hp": 120, "atk": 16, "speed": 1.6, "exp": 80,  "color": (255, 80,  180), "size": 26, "ai": "elite_shoot", "range": 300, "shoot": True, "elite": True},
    "SniperElite":  {"hp": 95,  "atk": 22, "speed": 1.2, "exp": 90,  "color": (80,  240, 255), "size": 24, "ai": "elite_shoot", "range": 380, "shoot": True, "elite": True},
    "BurstElite":   {"hp": 140, "atk": 12, "speed": 2.0, "exp": 85,  "color": (255, 180, 50),  "size": 26, "ai": "elite_shoot", "range": 260, "shoot": True, "elite": True},
    "MissileElite": {"hp": 160, "atk": 18, "speed": 1.4, "exp": 95,  "color": (180, 60,  255), "size": 28, "ai": "elite_shoot", "range": 320, "shoot": True, "elite": True},
    "OmniElite":    {"hp": 200, "atk": 20, "speed": 1.8, "exp": 110, "color": (255, 60,  60),  "size": 30, "ai": "elite_shoot", "range": 350, "shoot": True, "elite": True},
    # ── Bosses ────────────────────────────────────────────────────
    "Elder Treant":     {"hp": 280,  "atk": 18, "speed": 1.0, "exp": 180, "color": DARK_GREEN, "size": 50, "ai": "boss", "range": 180, "shoot": True},
    "Bone Overlord":    {"hp": 380,  "atk": 22, "speed": 1.3, "exp": 220, "color": WHITE,      "size": 50, "ai": "boss", "range": 200, "shoot": True},
    "Lava Titan":       {"hp": 550,  "atk": 30, "speed": 1.0, "exp": 280, "color": ORANGE,     "size": 55, "ai": "boss", "range": 220, "shoot": True},
    "Storm Sovereign":  {"hp": 700,  "atk": 36, "speed": 1.6, "exp": 340, "color": CYAN,       "size": 55, "ai": "boss", "range": 250, "shoot": True},
    "Demon King Baldr": {"hp": 1000, "atk": 48, "speed": 1.8, "exp": 600, "color": PURPLE,     "size": 60, "ai": "boss", "range": 280, "shoot": True},
}

# ── Item pools ───────────────────────────────────────────────
# (name, dmg, fire_rate, bullet_speed, rarity, color, desc, weapon_class, stat_bonus)
WEAPON_POOL = [
    # ── COMMON ─────────────────────────────────────────────────────
    ("Magic Wand",      16, 0.55, 9,  "Common",    LIGHT_BLUE, "Pierces 1 enemy",            "Any", {}),
    ("Short Bow",       15, 0.65, 10, "Common",    BROWN,      "Fast light arrows",           "Any", {}),
    ("Hand Pistol",     14, 0.80, 11, "Common",    LIGHT_GRAY, "Rapid-fire pistol",           "Any", {}),
    ("Soul Staff",      15, 0.60, 8,  "Common",    GREEN,      "Dark energy bolts",           "Any", {}),
    ("Fire Wand",       20, 0.50, 8,  "Common",    ORANGE,     "Flaming shots",               "Any", {}),
    ("Hunter Bow",      19, 0.55, 9,  "Common",    BROWN,      "Sturdy hunting bow",          "Any", {}),
    # ── RARE ───────────────────────────────────────────────────────
    ("Ice Staff",       30, 0.50, 9,  "Rare",      CYAN,       "Slowing ice shards",          "Any", {}),
    ("Fire Staff",      36, 0.50, 9,  "Rare",      ORANGE,     "Burn on every hit",           "Any", {}),
    ("Long Bow",        28, 0.60, 10, "Rare",      GOLD,       "High-power bow",              "Any", {}),
    ("Crossbow",        34, 0.55, 11, "Rare",      GRAY,       "Armor-piercing bolts",        "Any", {}),
    ("Plasma Rifle",    32, 0.70, 12, "Rare",      CYAN,       "Rapid plasma shots",          "Any", {}),
    ("Shadow Dart",     26, 0.85, 13, "Rare",      PURPLE,     "Silent poison darts",         "Any", {}),
    # ── EPIC ───────────────────────────────────────────────────────
    ("Chaos Staff",     52, 0.60, 10, "Epic",      PURPLE,     "Chaos energy blasts",         "Any", {}),
    ("Thunder Staff",   62, 0.65, 11, "Epic",      CYAN,       "Chain lightning",             "Any", {}),
    ("Thunder Bow",     46, 0.70, 13, "Epic",      CYAN,       "Electric pierce arrows",      "Any", {}),
    ("Sniper Bow",      58, 0.40, 17, "Epic",      GREEN,      "High-crit long-range",        "Any", {}),
    ("Laser Cannon",    55, 0.50, 15, "Epic",      LIGHT_BLUE, "Focused laser beam",          "Any", {}),
    ("Gatling Wand",    28, 1.30, 11, "Epic",      YELLOW,     "Spray magic bullets fast",    "Any", {}),
    # ── LEGENDARY ──────────────────────────────────────────────────
    ("Void Staff",      88, 0.70, 13, "Legendary", PURPLE,     "Tears reality — pierces all", "Any", {}),
    ("Arcane Catalyst", 102,0.75, 13, "Legendary", LIGHT_BLUE, "Double-cast arcane blasts",   "Any", {}),
    ("Dragon Bow",      78, 0.80, 15, "Legendary", RED,        "Exploding fire arrows",       "Any", {}),
    ("Wind Bow",        92, 0.95, 17, "Legendary", CYAN,       "Fires 2 arrows per shot",     "Any", {}),
    ("Railgun",         120,0.30, 22, "Legendary", LIGHT_BLUE, "Hyper-velocity round",        "Any", {}),
    ("Infinity Wand",   95, 0.85, 14, "Legendary", GOLD,       "Unlimited magical energy",    "Any", {}),
]

ARMOR_POOL = [
    # (name, defense, rarity, color, description)
    ("Cloth Robe",    3,  "Common",    LIGHT_GRAY, "Light cloth armor."),
    ("Leather Armor", 6,  "Common",    BROWN,      "Basic leather protection."),
    ("Chainmail",     10, "Rare",      GRAY,       "Metal chain links."),
    ("Plate Armor",   15, "Rare",      LIGHT_GRAY, "Heavy steel plate."),
    ("Shadow Cloak",  18, "Epic",      PURPLE,     "+20 AGI, dodge 10%."),
    ("Dragon Scale",  25, "Epic",      ORANGE,     "Fire resistance +30%."),
    ("Aegis Plate",   35, "Legendary", GOLD,       "Blocks 1 hit every 10 sec."),
    ("Void Robe",     28, "Legendary", PURPLE,     "+50% spell power."),
]

ACCESSORY_POOL = [
    # (name, rarity, color, effect_desc, stat_bonus)
    ("Iron Ring",      "Common",    GRAY,       "+3 STR",           {"STR": 3}),
    ("Speed Boots",    "Common",    BROWN,      "+3 AGI",           {"AGI": 3}),
    ("HP Talisman",    "Rare",      RED,        "+30 Max HP",       {"VIT": 3}),
    ("Mana Crystal",   "Rare",      LIGHT_BLUE, "+5 INT",           {"INT": 5}),
    ("Lucky Charm",    "Epic",      GOLD,       "+8 LUK, +5% crit", {"LUK": 8}),
    ("Berserker Ring", "Epic",      RED,        "+10 STR, -5 VIT",  {"STR": 10, "VIT": -5}),
    ("God's Amulet",   "Legendary", GOLD,       "+5 all stats",     {"STR": 5, "AGI": 5, "VIT": 5, "INT": 5, "DEX": 5, "LUK": 5}),
]

# ── EXP (kept minimal - no level up UI) ──────────────────────
EXP_BASE = 25

# ── Shop prices ──────────────────────────────────────────────
SHOP_HEAL_COST   = 50
SHOP_REROLL_COST = 30
SHOP_ITEM_MULT   = {"Common": 30, "Rare": 80, "Epic": 180, "Legendary": 400}

# ── UI Layout ────────────────────────────────────────────────
HUD_H     = 80
MINIMAP_S = 120

# ── Skills ───────────────────────────────────────────────────
CLASS_SKILLS = {
    "Knight": {
        "name": "Shield Slam",
        "cooldown": 5.0,
        "mana_cost": 15,
        "description": "Slam forward, stunning nearby enemies. Restores 30 Armor.",
        "type": "shield_slam",
    },
    "Berserker": {
        "name": "Whirlwind",
        "cooldown": 4.0,
        "mana_cost": 12,
        "description": "Spin attack hitting ALL nearby enemies for 3x damage.",
        "type": "whirlwind",
    },
    "Mage": {
        "name": "Nova Burst",
        "cooldown": 4.5,
        "mana_cost": 30,
        "description": "Magic explosion around you, hits all nearby enemies.",
        "type": "nova_burst",
    },
    "Necromancer": {
        "name": "Death Bolt",
        "cooldown": 3.5,
        "mana_cost": 25,
        "description": "Homing dark bolt seeks the nearest enemy.",
        "type": "death_bolt",
    },
    "Ranger": {
        "name": "Triple Shot",
        "cooldown": 3.0,
        "mana_cost": 10,
        "description": "Fire 3 arrows in a spread at once.",
        "type": "triple_shot",
    },
    "Rogue": {
        "name": "Smoke Dash",
        "cooldown": 4.0,
        "mana_cost": 18,
        "description": "Dash through enemies dealing damage + brief invincibility.",
        "type": "smoke_dash",
    },
}
