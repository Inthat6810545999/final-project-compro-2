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
STATE_RANGE      = "shooting_range"
STATE_LEVEL_UP   = "level_up"

# ── Player classes ────────────────────────────────────────────
CLASSES = {
    "Sausage Man": {
        "color": (240, 60, 120),
        "base_hp": 130,
        "max_armor": 80,
        "max_mana": 100,
        "speed": 3.8,
        "base_damage": 16,
        "fire_rate": 0.75,
        "bullet_speed": 10,
        "description": "The legendary Sausage Man. Ready for anything.",
        "passive": "Sausage Spirit: Balanced stats. Never gives up.",
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
    # Soul Knight balance — DPS target per rarity (single-shot equiv):
    #   Common ~22-32 │ Rare ~38-55 │ Epic ~65-110 │ Legendary ~110-180
    # Spread/burst weapons: per-pellet dmg × pellets × rate ≈ target DPS
    # Mana cost: 1-2 (very fast) │ 3-4 (normal) │ 5-7 (spread) │ 8-12 (epic) │ 12-16 (legendary)

    # ── COMMON ──────────────────────────────────────────────────────
    ("Hand Pistol",   12, 2.00, 12, "Common", LIGHT_GRAY, "Snappy starter pistol",     "Any", {},
     {"pattern":"single",       "bullet_color":(255,230,80),  "bullet_size":5,  "gun_shape":"pistol",   "gun_color":(160,160,180), "pierce":False, "mana_cost":2}),
    # DPS: 12×2.0 = 24

    ("Revolver",      32, 0.65, 12, "Common", GOLD,       "Slow but hits hard",        "Any", {},
     {"pattern":"single",       "bullet_color":(255,200,50),  "bullet_size":8,  "gun_shape":"revolver", "gun_color":(180,140,40),  "pierce":False, "mana_cost":3}),
    # DPS: 32×0.65 = 20.8 (lower DPS but high burst)

    ("SMG",            7, 5.00, 14, "Common", CYAN,       "Ultra-rapid spray",         "Any", {},
     {"pattern":"single",       "bullet_color":(80,220,255),  "bullet_size":4,  "gun_shape":"smg",      "gun_color":(40,120,160),  "pierce":False, "mana_cost":1}),
    # DPS: 7×5.0 = 35 (high rate compensates low dmg)

    ("Sawed-Off",     18, 0.55, 9,  "Common", ORANGE,     "3-pellet close range blast","Any", {},
     {"pattern":"spread3",      "bullet_color":(255,140,40),  "bullet_size":6,  "gun_shape":"shotgun",  "gun_color":(120,80,30),   "pierce":False, "mana_cost":5}),
    # DPS: 18×3×0.55 = 29.7

    ("Hunting Rifle", 28, 0.80, 17, "Common", BROWN,      "Accurate medium-range shot","Any", {},
     {"pattern":"single",       "bullet_color":(200,160,80),  "bullet_size":5,  "gun_shape":"rifle",    "gun_color":(100,60,20),   "pierce":False, "mana_cost":3}),
    # DPS: 28×0.80 = 22.4

    ("Flare Gun",     22, 0.40,  7, "Common", ORANGE,     "Slow scorching flare",      "Any", {},
     {"pattern":"single",       "bullet_color":(255,80,20),   "bullet_size":10, "gun_shape":"pistol",   "gun_color":(160,80,40),   "pierce":False, "mana_cost":4}),
    # DPS: 22×0.40 = 8.8 (low DPS, large bullet — niche/fun)

    # ── RARE ────────────────────────────────────────────────────────
    ("AK-47",         16, 3.00, 14, "Rare",   GREEN,      "High-rate assault rifle",   "Any", {},
     {"pattern":"single",       "bullet_color":(180,255,80),  "bullet_size":5,  "gun_shape":"rifle",    "gun_color":(50,100,30),   "pierce":False, "mana_cost":2}),
    # DPS: 16×3.0 = 48

    ("Shotgun",       20, 0.45, 10, "Rare",   GRAY,       "5-pellet wide spread",      "Any", {},
     {"pattern":"spread5",      "bullet_color":(220,180,80),  "bullet_size":6,  "gun_shape":"shotgun",  "gun_color":(80,80,80),    "pierce":False, "mana_cost":7}),
    # DPS: 20×5×0.45 = 45

    ("Sniper Rifle",  60, 0.35, 26, "Rare",   LIGHT_GRAY, "Piercing long-range shot",  "Any", {},
     {"pattern":"pierce",       "bullet_color":(255,255,255), "bullet_size":4,  "gun_shape":"sniper",   "gun_color":(60,60,70),    "pierce":True,  "mana_cost":6}),
    # DPS: 60×0.35 = 21 (low sustain, high single-target burst + pierce)

    ("Plasma Pistol", 28, 1.20, 15, "Rare",   CYAN,       "Plasma bolts, decent rate", "Any", {},
     {"pattern":"single",       "bullet_color":(0,220,255),   "bullet_size":7,  "gun_shape":"pistol",   "gun_color":(0,120,160),   "pierce":False, "mana_cost":4}),
    # DPS: 28×1.2 = 33.6

    ("Dual Pistols",  14, 1.50, 13, "Rare",   GOLD,       "2 bullets per shot",        "Any", {},
     {"pattern":"double",       "bullet_color":(255,220,60),  "bullet_size":5,  "gun_shape":"pistol",   "gun_color":(160,120,30),  "pierce":False, "mana_cost":4}),
    # DPS: 14×2×1.5 = 42

    ("Dart Gun",      20, 2.20, 15, "Rare",   PURPLE,     "Rapid silent darts",        "Any", {},
     {"pattern":"single",       "bullet_color":(180,60,220),  "bullet_size":4,  "gun_shape":"pistol",   "gun_color":(80,30,120),   "pierce":False, "mana_cost":2}),
    # DPS: 20×2.2 = 44

    # ── EPIC ────────────────────────────────────────────────────────
    ("Grenade Launcher",65, 0.45, 8, "Epic",  ORANGE,     "Huge explosive slug",       "Any", {},
     {"pattern":"single",       "bullet_color":(255,100,0),   "bullet_size":14, "gun_shape":"launcher", "gun_color":(120,60,20),   "pierce":False, "mana_cost":8}),
    # DPS: 65×0.45 = 29.25 (low DPS but massive single hit / area)

    ("Lightning Gun", 55, 0.75, 14, "Epic",   CYAN,       "Piercing electric bolt",    "Any", {},
     {"pattern":"pierce",       "bullet_color":(100,220,255), "bullet_size":6,  "gun_shape":"rifle",    "gun_color":(20,80,120),   "pierce":True,  "mana_cost":8}),
    # DPS: 55×0.75 = 41.25 + pierce bonus

    ("Railgun Mk1",   72, 0.32, 26, "Epic",   LIGHT_BLUE, "Hyper-fast armor-piercing", "Any", {},
     {"pattern":"pierce",       "bullet_color":(180,230,255), "bullet_size":4,  "gun_shape":"sniper",   "gun_color":(30,60,100),   "pierce":True,  "mana_cost":9}),
    # DPS: 72×0.32 = 23 (pierce + burst)

    ("Assault Rifle", 22, 2.00, 15, "Epic",   GREEN,      "3-shot burst, rapid fire",  "Any", {},
     {"pattern":"burst3",       "bullet_color":(150,255,100), "bullet_size":5,  "gun_shape":"rifle",    "gun_color":(40,80,30),    "pierce":False, "mana_cost":4}),
    # DPS: 22×3×(1/cooldown) ≈ burst heavy

    ("Laser Rifle",   50, 0.60, 22, "Epic",   RED,        "Thin fast piercing laser",  "Any", {},
     {"pattern":"pierce",       "bullet_color":(255,50,50),   "bullet_size":3,  "gun_shape":"sniper",   "gun_color":(120,20,20),   "pierce":True,  "mana_cost":8}),
    # DPS: 50×0.60 = 30 + pierce

    ("Minigun",       10, 8.00, 13, "Epic",   YELLOW,     "Insane fire rate, slight spread","Any", {},
     {"pattern":"spread_random","bullet_color":(255,240,80),  "bullet_size":4,  "gun_shape":"minigun",  "gun_color":(100,100,40),  "pierce":False, "mana_cost":1}),
    # DPS: 10×8.0 = 80 (spread lowers effective DPS)

    # ── LEGENDARY ───────────────────────────────────────────────────
    ("Void Cannon",   95, 0.65, 14, "Legendary", PURPLE,     "Void orb, pierces all",     "Any", {},
     {"pattern":"pierce",       "bullet_color":(180,0,255),   "bullet_size":15, "gun_shape":"launcher", "gun_color":(80,0,120),    "pierce":True,  "mana_cost":14}),
    # DPS: 95×0.65 = 61.75 + pierce

    ("Twin Blaster",  80, 0.80, 14, "Legendary", LIGHT_BLUE, "2 massive energy bolts",    "Any", {},
     {"pattern":"double",       "bullet_color":(80,180,255),  "bullet_size":11, "gun_shape":"launcher", "gun_color":(30,80,160),   "pierce":False, "mana_cost":12}),
    # DPS: 80×2×0.80 = 128

    ("Dragon Cannon", 75, 0.75, 13, "Legendary", RED,        "3 exploding fire shots",    "Any", {},
     {"pattern":"spread3",      "bullet_color":(255,60,0),    "bullet_size":12, "gun_shape":"launcher", "gun_color":(140,30,0),    "pierce":False, "mana_cost":12}),
    # DPS: 75×3×0.75 = 168.75

    ("Wind Striker",  70, 1.20, 20, "Legendary", CYAN,       "Rapid burst — triple shots","Any", {},
     {"pattern":"burst3",       "bullet_color":(150,255,220), "bullet_size":7,  "gun_shape":"rifle",    "gun_color":(30,140,120),  "pierce":False, "mana_cost":10}),

    ("Railgun Mk2",  130, 0.30, 30, "Legendary", LIGHT_BLUE, "Pierces entire map",        "Any", {},
     {"pattern":"pierce",       "bullet_color":(220,240,255), "bullet_size":5,  "gun_shape":"sniper",   "gun_color":(20,40,80),    "pierce":True,  "mana_cost":16}),
    # DPS: 130×0.30 = 39 + all pierce

    ("Infinity Blaster",85,1.00, 16, "Legendary", GOLD,      "Golden double, all pierce", "Any", {},
     {"pattern":"double",       "bullet_color":(255,200,0),   "bullet_size":10, "gun_shape":"launcher", "gun_color":(140,100,0),   "pierce":True,  "mana_cost":13}),
    # DPS: 85×2×1.0 = 170
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
    # (name, rarity, color, effect_desc, stat_bonus)  — keys are direct Player attrs
    ("Iron Ring",      "Common",    GRAY,       "+5 ATK",              {"base_damage": 5}),
    ("Speed Boots",    "Common",    BROWN,      "+0.4 Move Speed",     {"move_speed": 0.4}),
    ("HP Talisman",    "Rare",      RED,        "+30 Max HP",          {"max_hp": 30}),
    ("Mana Crystal",   "Rare",      LIGHT_BLUE, "+25 Max Mana",        {"max_mana": 25}),
    ("Lucky Charm",    "Epic",      GOLD,       "+8% Crit Chance",     {"crit_chance": 0.08}),
    ("Berserker Ring", "Epic",      RED,        "+12 ATK, -20 Max HP", {"base_damage": 12, "max_hp": -20}),
    ("God's Amulet",   "Legendary", GOLD,       "+10 ATK, +40 HP, +0.5 Spd", {"base_damage": 10, "max_hp": 40, "move_speed": 0.5}),
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
# Each class has a list of 3 skills — keys Q / F / R
CLASS_SKILLS = {
    "Sausage Man": [
        {
            "name": "Dash",
            "key": "Q",
            "cooldown": 4.0,
            "mana_cost": 15,
            "type": "dash",
            "color": (0, 220, 200),
            "description": "Dash forward quickly.",
        },
        {
            "name": "Star Shot",
            "key": "F",
            "cooldown": 6.0,
            "mana_cost": 25,
            "type": "star_spread",
            "color": (255, 210, 0),
            "description": "Fire 3 star bullets in a spread.",
        },
        {
            "name": "Frenzy",
            "key": "R",
            "cooldown": 8.0,
            "mana_cost": 20,
            "type": "rapid_fire",
            "duration": 3.0,
            "color": (255, 100, 30),
            "description": "Fire rate x2.5 for 3 seconds.",
        },
    ],
}
