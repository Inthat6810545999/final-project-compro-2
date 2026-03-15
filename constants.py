"""
constants.py  –  All game-wide constants and configuration
"""

# ── Screen ────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1024, 768
FPS = 60
TITLE = "Sausage Man: Legends of Midgard"

# ── Tile ─────────────────────────────────────────────────────
TILE = 48
ROOM_COLS = 17   # tiles wide per room (visible area)
ROOM_ROWS = 13   # tiles tall per room

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
    "Warrior": {
        "color": RED,
        "base_stats": {"STR": 8, "AGI": 4, "VIT": 8, "INT": 2, "DEX": 4, "LUK": 3},
        "hp_per_vit": 12,
        "base_hp": 150,
        "speed": 3.0,
        "description": "Tank melee fighter. High HP and strength.",
        "passive": "Iron Skin: Reduce all incoming damage by 10%.",
    },
    "Mage": {
        "color": PURPLE,
        "base_stats": {"STR": 2, "AGI": 4, "VIT": 3, "INT": 10, "DEX": 5, "LUK": 4},
        "hp_per_vit": 8,
        "base_hp": 90,
        "speed": 3.2,
        "description": "Powerful spellcaster. High magic damage.",
        "passive": "Arcane Mind: +20% spell damage, bullets pierce one enemy.",
    },
    "Ranger": {
        "color": GREEN,
        "base_stats": {"STR": 4, "AGI": 8, "VIT": 4, "INT": 3, "DEX": 9, "LUK": 6},
        "hp_per_vit": 9,
        "base_hp": 110,
        "speed": 4.0,
        "description": "Swift ranged attacker. High crit and speed.",
        "passive": "Eagle Eye: +15% crit chance, +20% bullet speed.",
    },
}

# ── Stages ───────────────────────────────────────────────────
STAGE_CONFIGS = [
    {"id": 0, "name": "Forest of Trials",   "theme": "forest",   "color": DARK_GREEN,  "enemy_types": ["Slime", "Wolf"],          "boss": "Elder Treant"},
    {"id": 1, "name": "Dungeon of Shadows",  "theme": "dungeon",  "color": DARK_GRAY,   "enemy_types": ["Skeleton", "Bat"],        "boss": "Bone Overlord"},
    {"id": 2, "name": "Volcanic Fortress",   "theme": "volcano",  "color": DARK_RED,    "enemy_types": ["FireImp", "Golem"],       "boss": "Lava Titan"},
    {"id": 3, "name": "Sky Citadel",         "theme": "sky",      "color": LIGHT_BLUE,  "enemy_types": ["Harpy", "StormMage"],     "boss": "Storm Sovereign"},
    {"id": 4, "name": "Final Chamber",       "theme": "chaos",    "color": PURPLE,      "enemy_types": ["EliteHybrid", "Wraith"], "boss": "Demon King Baldr"},
]

# ── Enemy stats (base, scales with stage) ────────────────────
# hp / atk / speed / exp — stage 1-2 enemies nerfed for easier early game
ENEMY_DATA = {
    "Slime":      {"hp": 18,  "atk": 3,  "speed": 1.3, "exp": 10,  "color": GREEN,      "size": 20, "ai": "chase",  "range": 0,   "shoot": False},
    "Wolf":       {"hp": 28,  "atk": 6,  "speed": 2.2, "exp": 15,  "color": GRAY,       "size": 22, "ai": "chase",  "range": 0,   "shoot": False},
    "Skeleton":   {"hp": 32,  "atk": 8,  "speed": 1.5, "exp": 18,  "color": WHITE,      "size": 22, "ai": "patrol", "range": 0,   "shoot": False},
    "Bat":        {"hp": 15,  "atk": 5,  "speed": 2.8, "exp": 12,  "color": PURPLE,     "size": 16, "ai": "chase",  "range": 0,   "shoot": False},
    "FireImp":    {"hp": 45,  "atk": 10, "speed": 2.0, "exp": 22,  "color": ORANGE,     "size": 20, "ai": "shoot",  "range": 200, "shoot": True},
    "Golem":      {"hp": 90,  "atk": 14, "speed": 0.9, "exp": 30,  "color": BROWN,      "size": 30, "ai": "chase",  "range": 0,   "shoot": False},
    "Harpy":      {"hp": 40,  "atk": 10, "speed": 3.2, "exp": 25,  "color": CYAN,       "size": 20, "ai": "chase",  "range": 0,   "shoot": False},
    "StormMage":  {"hp": 55,  "atk": 14, "speed": 1.4, "exp": 32,  "color": LIGHT_BLUE, "size": 22, "ai": "shoot",  "range": 250, "shoot": True},
    "EliteHybrid":{"hp": 100, "atk": 22, "speed": 2.8, "exp": 40,  "color": RED,        "size": 24, "ai": "shoot",  "range": 200, "shoot": True},
    "Wraith":     {"hp": 80,  "atk": 20, "speed": 2.0, "exp": 35,  "color": PURPLE,     "size": 22, "ai": "chase",  "range": 0,   "shoot": False},
    # Bosses — slightly more forgiving HP
    "Elder Treant":     {"hp": 280, "atk": 18, "speed": 1.0, "exp": 180, "color": DARK_GREEN, "size": 50, "ai": "boss", "range": 180, "shoot": True},
    "Bone Overlord":    {"hp": 380, "atk": 22, "speed": 1.3, "exp": 220, "color": WHITE,      "size": 50, "ai": "boss", "range": 200, "shoot": True},
    "Lava Titan":       {"hp": 550, "atk": 30, "speed": 1.0, "exp": 280, "color": ORANGE,     "size": 55, "ai": "boss", "range": 220, "shoot": True},
    "Storm Sovereign":  {"hp": 700, "atk": 36, "speed": 1.6, "exp": 340, "color": CYAN,       "size": 55, "ai": "boss", "range": 250, "shoot": True},
    "Demon King Baldr": {"hp": 1000,"atk": 48, "speed": 1.8, "exp": 600, "color": PURPLE,     "size": 60, "ai": "boss", "range": 280, "shoot": True},
}

# ── Item pools ───────────────────────────────────────────────
# Weapon pool: (name, dmg, fire_rate, bullet_speed, rarity, color, desc, weapon_class, stat_bonus)
# stat_bonus: dict of {stat: value} applied when equipped  e.g. {"STR":3,"VIT":2}
WEAPON_POOL = [
    # ── WARRIOR ──────────────────────────────────────────────────────────────────────────────────────────────────────────
    ("Iron Sword",     18, 0,    0,  "Common",    GRAY,       "+3 STR  +2 VIT",                    "Warrior", {"STR":3,"VIT":2}),
    ("Battle Axe",     22, 0,    0,  "Common",    BROWN,      "+4 STR  +1 AGI",                    "Warrior", {"STR":4,"AGI":1}),
    ("Steel Sword",    32, 0,    0,  "Rare",      LIGHT_GRAY, "+6 STR  +3 VIT  +2 DEX",            "Warrior", {"STR":6,"VIT":3,"DEX":2}),
    ("War Hammer",     40, 0,    0,  "Rare",      GRAY,       "+5 STR  +5 VIT  stuns on hit",      "Warrior", {"STR":5,"VIT":5}),
    ("Shadow Blade",   54, 0,    0,  "Epic",      PURPLE,     "+9 STR  +4 AGI  +3 LUK  lifesteal", "Warrior", {"STR":9,"AGI":4,"LUK":3}),
    ("Berserker Axe",  66, 0,    0,  "Epic",      RED,        "+12 STR  +4 VIT  berserk bonus",    "Warrior", {"STR":12,"VIT":4}),
    ("Excalibur",      92, 0,    0,  "Legendary", GOLD,       "+15 STR  +10 VIT  +8 DEX  +5 LUK",  "Warrior", {"STR":15,"VIT":10,"DEX":8,"LUK":5}),
    ("Ragnarok Sword", 115,0,    0,  "Legendary", RED,        "+18 STR  +8 VIT  +6 AGI  cleave",   "Warrior", {"STR":18,"VIT":8,"AGI":6}),

    # ── MAGE ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
    ("Magic Wand",     16, 0.5,  8,  "Common",    LIGHT_BLUE, "+3 INT  +2 DEX",                    "Mage",    {"INT":3,"DEX":2}),
    ("Fire Wand",      20, 0.5,  8,  "Common",    ORANGE,     "+4 INT  +1 LUK",                    "Mage",    {"INT":4,"LUK":1}),
    ("Ice Staff",      30, 0.45, 8,  "Rare",      CYAN,       "+6 INT  +3 DEX  +2 AGI  slows",     "Mage",    {"INT":6,"DEX":3,"AGI":2}),
    ("Fire Staff",     36, 0.5,  9,  "Rare",      ORANGE,     "+7 INT  +3 VIT  burn DoT",          "Mage",    {"INT":7,"VIT":3}),
    ("Chaos Staff",    52, 0.55, 10, "Epic",      PURPLE,     "+11 INT  +5 DEX  +4 LUK  chaos dmg","Mage",    {"INT":11,"DEX":5,"LUK":4}),
    ("Thunder Staff",  62, 0.6,  10, "Epic",      CYAN,       "+13 INT  +5 AGI  chain lightning",  "Mage",    {"INT":13,"AGI":5}),
    ("Void Staff",     88, 0.65, 12, "Legendary", PURPLE,     "+18 INT  +8 DEX  +6 LUK  void",     "Mage",    {"INT":18,"DEX":8,"LUK":6}),
    ("Arcane Catalyst",102,0.7,  12, "Legendary", LIGHT_BLUE, "+20 INT  +10 DEX  +5 VIT  dbl cast","Mage",    {"INT":20,"DEX":10,"VIT":5}),

    # ── RANGER ───────────────────────────────────────────────────────────────────────────────────────────────────────────
    ("Short Bow",      15, 0.45, 7,  "Common",    BROWN,      "+3 DEX  +2 AGI",                    "Ranger",  {"DEX":3,"AGI":2}),
    ("Hunter Bow",     19, 0.5,  8,  "Common",    BROWN,      "+4 DEX  +2 LUK",                    "Ranger",  {"DEX":4,"LUK":2}),
    ("Long Bow",       28, 0.55, 9,  "Rare",      GOLD,       "+6 DEX  +4 AGI  +2 LUK",            "Ranger",  {"DEX":6,"AGI":4,"LUK":2}),
    ("Crossbow",       34, 0.5,  10, "Rare",      GRAY,       "+7 DEX  +3 STR  armor-pierce",      "Ranger",  {"DEX":7,"STR":3}),
    ("Thunder Bow",    46, 0.65, 12, "Epic",      CYAN,       "+10 DEX  +6 AGI  +4 LUK  pierce",   "Ranger",  {"DEX":10,"AGI":6,"LUK":4}),
    ("Sniper Bow",     58, 0.4,  16, "Epic",      GREEN,      "+12 DEX  +5 AGI  +6 LUK  +crit",    "Ranger",  {"DEX":12,"AGI":5,"LUK":6}),
    ("Dragon Bow",     78, 0.75, 14, "Legendary", RED,        "+16 DEX  +10 AGI  +6 STR  fire arr","Ranger",  {"DEX":16,"AGI":10,"STR":6}),
    ("Wind Bow",       92, 0.9,  16, "Legendary", CYAN,       "+18 DEX  +12 AGI  +8 LUK  2 arrows","Ranger",  {"DEX":18,"AGI":12,"LUK":8}),
]

ARMOR_POOL = [
    # name, defense, rarity, color, description
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
    # name, effect_desc, rarity, color, stat_bonus
    ("Iron Ring",     "Common",    GRAY,       "+3 STR",         {"STR": 3}),
    ("Speed Boots",   "Common",    BROWN,      "+3 AGI",         {"AGI": 3}),
    ("HP Talisman",   "Rare",      RED,        "+30 Max HP",     {"VIT": 3}),
    ("Mana Crystal",  "Rare",      LIGHT_BLUE, "+5 INT",         {"INT": 5}),
    ("Lucky Charm",   "Epic",      GOLD,       "+8 LUK, +5% crit", {"LUK": 8}),
    ("Berserker Ring","Epic",      RED,        "+10 STR, -5 VIT", {"STR": 10, "VIT": -5}),
    ("God's Amulet",  "Legendary", GOLD,       "+5 all stats",   {"STR": 5, "AGI": 5, "VIT": 5, "INT": 5, "DEX": 5, "LUK": 5}),
]

# ── EXP curve: exp_needed = BASE * level^1.5 ────────────────
EXP_BASE = 25   # lowered from 40 — faster early leveling

# ── Stat effects (multipliers per point) ────────────────────
# Each stat point gives:
STAT_EFFECTS = {
    "STR": {"atk_bonus": 2},      # +2 physical atk per STR
    "AGI": {"speed_bonus": 0.05}, # +0.05 move speed per AGI
    "VIT": {"hp_bonus": 8},       # +8 max HP per VIT
    "INT": {"spell_bonus": 2.5},  # +2.5 magic dmg per INT
    "DEX": {"crit_bonus": 0.005}, # +0.5% crit per DEX
    "LUK": {"drop_bonus": 0.01},  # +1% better loot per LUK
}

# ── Shop prices ──────────────────────────────────────────────
SHOP_HEAL_COST   = 50
SHOP_REROLL_COST = 30   # gold cost to reroll shop items
SHOP_ITEM_MULT   = {"Common": 30, "Rare": 80, "Epic": 180, "Legendary": 400}

# ── UI Layout ────────────────────────────────────────────────
HUD_H     = 80    # bottom HUD height
MINIMAP_S = 120   # minimap size

# ── Skills ───────────────────────────────────────────
CLASS_SKILLS = {
    "Warrior": {
        "name": "Whirlwind",
        "cooldown": 5.0,
        "description": "Spin attack hitting all nearby enemies.",
    },
    "Mage": {
        "name": "Fireball",
        "cooldown": 4.0,
        "description": "Launch explosive fireball.",
    },
    "Ranger": {
        "name": "Triple Shot",
        "cooldown": 3.5,
        "description": "Shoot three arrows at once.",
    }
}