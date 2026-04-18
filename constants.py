"""
constants.py  –  All game-wide constants and configuration
"""

# ── Screen ────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60
TITLE = "Sausage Man: Legends of Midgard"

# ── Tile ─────────────────────────────────────────────────────
TILE      = 72
ROOM_COLS = 17
ROOM_ROWS = 13

# FIX: export map dimensions so bullet.py can compute correct world bounds
MAP_W = 60   # tiles (mirrors Stage.MAP_W)
MAP_H = 60   # tiles (mirrors Stage.MAP_H)

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
    # Format: (name, dmg, fire_rate, bullet_spd, rarity, color, desc, class, stat_bonus, effect)
    # effect = {pattern, bullet_color, bullet_size, gun_shape, gun_color, pierce}
    # patterns: single | spread3 | spread5 | double | pierce | spread_random | burst3

    # ── COMMON ─────────────────────────────────────────────────────
    ("Hand Pistol",   14, 0.80, 11, "Common", LIGHT_GRAY, "Rapid single shots",        "Any", {},
     {"pattern":"single",       "bullet_color":(255,230,80),  "bullet_size":5,  "gun_shape":"pistol",   "gun_color":(160,160,180), "pierce":False}),
    ("Revolver",      18, 0.50, 10, "Common", GOLD,       "Heavy slow pistol",         "Any", {},
     {"pattern":"single",       "bullet_color":(255,200,50),  "bullet_size":7,  "gun_shape":"revolver", "gun_color":(180,140,40),  "pierce":False}),
    ("SMG",           10, 1.80, 13, "Common", CYAN,       "Ultra-rapid small shots",   "Any", {},
     {"pattern":"single",       "bullet_color":(80,220,255),  "bullet_size":4,  "gun_shape":"smg",      "gun_color":(40,120,160),  "pierce":False}),
    ("Sawed-Off",     20, 0.40, 8,  "Common", ORANGE,     "3-bullet shotgun spread",   "Any", {},
     {"pattern":"spread3",      "bullet_color":(255,140,40),  "bullet_size":6,  "gun_shape":"shotgun",  "gun_color":(120,80,30),   "pierce":False}),
    ("Hunting Rifle", 22, 0.45, 14, "Common", BROWN,      "Accurate single shot",      "Any", {},
     {"pattern":"single",       "bullet_color":(200,160,80),  "bullet_size":5,  "gun_shape":"rifle",    "gun_color":(100,60,20),   "pierce":False}),
    ("Flare Gun",     16, 0.35, 7,  "Common", ORANGE,     "Slow burning flare",        "Any", {},
     {"pattern":"single",       "bullet_color":(255,80,20),   "bullet_size":9,  "gun_shape":"pistol",   "gun_color":(160,80,40),   "pierce":False}),

    # ── RARE ───────────────────────────────────────────────────────
    ("AK-47",         24, 0.90, 13, "Rare",   GREEN,      "High fire rate rifle",      "Any", {},
     {"pattern":"single",       "bullet_color":(180,255,80),  "bullet_size":5,  "gun_shape":"rifle",    "gun_color":(50,100,30),   "pierce":False}),
    ("Shotgun",       28, 0.35, 9,  "Rare",   GRAY,       "5-bullet wide spread",      "Any", {},
     {"pattern":"spread5",      "bullet_color":(220,180,80),  "bullet_size":6,  "gun_shape":"shotgun",  "gun_color":(80,80,80),    "pierce":False}),
    ("Sniper Rifle",  40, 0.28, 22, "Rare",   LIGHT_GRAY, "Ultra-fast piercing shot",  "Any", {},
     {"pattern":"pierce",       "bullet_color":(255,255,255), "bullet_size":4,  "gun_shape":"sniper",   "gun_color":(60,60,70),    "pierce":True}),
    ("Plasma Pistol", 30, 0.65, 14, "Rare",   CYAN,       "Glowing plasma bolts",      "Any", {},
     {"pattern":"single",       "bullet_color":(0,220,255),   "bullet_size":7,  "gun_shape":"pistol",   "gun_color":(0,120,160),   "pierce":False}),
    ("Dual Pistols",  20, 0.70, 12, "Rare",   GOLD,       "Fires 2 bullets at once",   "Any", {},
     {"pattern":"double",       "bullet_color":(255,220,60),  "bullet_size":5,  "gun_shape":"pistol",   "gun_color":(160,120,30),  "pierce":False}),
    ("Dart Gun",      26, 0.85, 13, "Rare",   PURPLE,     "Silent poison darts",       "Any", {},
     {"pattern":"single",       "bullet_color":(180,60,220),  "bullet_size":4,  "gun_shape":"pistol",   "gun_color":(80,30,120),   "pierce":False}),

    # ── EPIC ───────────────────────────────────────────────────────
    ("Grenade Launcher",52, 0.40, 8,"Epic",   ORANGE,     "Slow heavy explosive shot", "Any", {},
     {"pattern":"single",       "bullet_color":(255,100,0),   "bullet_size":12, "gun_shape":"launcher", "gun_color":(120,60,20),   "pierce":False}),
    ("Lightning Gun", 60, 0.60, 13, "Epic",   CYAN,       "Piercing electric bolt",    "Any", {},
     {"pattern":"pierce",       "bullet_color":(100,220,255), "bullet_size":6,  "gun_shape":"rifle",    "gun_color":(20,80,120),   "pierce":True}),
    ("Railgun Mk1",   65, 0.30, 24, "Epic",   LIGHT_BLUE, "Hyper-fast armor-piercing", "Any", {},
     {"pattern":"pierce",       "bullet_color":(180,230,255), "bullet_size":4,  "gun_shape":"sniper",   "gun_color":(30,60,100),   "pierce":True}),
    ("Assault Rifle", 28, 1.10, 14, "Epic",   GREEN,      "3-shot burst each trigger", "Any", {},
     {"pattern":"burst3",       "bullet_color":(150,255,100), "bullet_size":5,  "gun_shape":"rifle",    "gun_color":(40,80,30),    "pierce":False}),
    ("Laser Rifle",   55, 0.50, 20, "Epic",   RED,        "Thin fast laser beam",      "Any", {},
     {"pattern":"pierce",       "bullet_color":(255,50,50),   "bullet_size":3,  "gun_shape":"sniper",   "gun_color":(120,20,20),   "pierce":True}),
    ("Minigun",       18, 2.20, 12, "Epic",   YELLOW,     "Insane fire rate spray",    "Any", {},
     {"pattern":"spread_random","bullet_color":(255,240,80),  "bullet_size":4,  "gun_shape":"minigun",  "gun_color":(100,100,40),  "pierce":False}),

    # ── LEGENDARY ──────────────────────────────────────────────────
    ("Void Cannon",   90, 0.60, 14, "Legendary", PURPLE,     "Huge void orb, pierces all","Any", {},
     {"pattern":"pierce",       "bullet_color":(180,0,255),   "bullet_size":14, "gun_shape":"launcher", "gun_color":(80,0,120),    "pierce":True}),
    ("Twin Blaster",  100,0.70, 14, "Legendary", LIGHT_BLUE, "2 massive energy bolts",   "Any", {},
     {"pattern":"double",       "bullet_color":(80,180,255),  "bullet_size":10, "gun_shape":"launcher", "gun_color":(30,80,160),   "pierce":False}),
    ("Dragon Cannon", 80, 0.70, 13, "Legendary", RED,        "3 exploding fire shots",   "Any", {},
     {"pattern":"spread3",      "bullet_color":(255,60,0),    "bullet_size":11, "gun_shape":"launcher", "gun_color":(140,30,0),    "pierce":False}),
    ("Wind Striker",  90, 0.90, 18, "Legendary", CYAN,       "Triple rapid shots",        "Any", {},
     {"pattern":"burst3",       "bullet_color":(150,255,220), "bullet_size":6,  "gun_shape":"rifle",    "gun_color":(30,140,120),  "pierce":False}),
    ("Railgun Mk2",   120,0.28, 28, "Legendary", LIGHT_BLUE, "Pierces entire map",        "Any", {},
     {"pattern":"pierce",       "bullet_color":(220,240,255), "bullet_size":5,  "gun_shape":"sniper",   "gun_color":(20,40,80),    "pierce":True}),
    ("Infinity Blaster",95,0.85,15, "Legendary", GOLD,       "Endless golden double fire","Any", {},
     {"pattern":"double",       "bullet_color":(255,200,0),   "bullet_size":9,  "gun_shape":"launcher", "gun_color":(140,100,0),   "pierce":True}),
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
