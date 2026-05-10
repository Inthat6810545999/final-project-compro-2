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
        "base_hp":      150,    # ↑ 130→150  (more survivability)
        "max_armor":     85,    # ↑ 80→85
        "max_mana":     320,    # ↑ 300→320  (more skill usage)
        "speed":        3.8,
        "base_damage":   18,    # ↑ 16→18    (early game feels better)
        "fire_rate":    0.75,
        "bullet_speed":  10,
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
    # ── Stage 1: Forest ── light intro, forgiving
    "Slime":       {"hp": 28,  "atk": 5,  "speed": 1.3, "exp": 12,  "color": GREEN,      "size": 20, "ai": "shoot", "range": 180, "shoot": True},
    "Wolf":        {"hp": 42,  "atk": 8,  "speed": 2.2, "exp": 18,  "color": GRAY,       "size": 22, "ai": "shoot", "range": 160, "shoot": True},
    # ── Stage 2: Dungeon ── moderate, punishes sloppy play
    "Skeleton":    {"hp": 52,  "atk": 11, "speed": 1.6, "exp": 22,  "color": WHITE,      "size": 22, "ai": "shoot", "range": 200, "shoot": True},
    "Bat":         {"hp": 24,  "atk": 7,  "speed": 3.0, "exp": 14,  "color": PURPLE,     "size": 16, "ai": "shoot", "range": 150, "shoot": True},
    # ── Stage 3: Volcano ── tanky + hard hits
    "FireImp":     {"hp": 62,  "atk": 13, "speed": 2.0, "exp": 26,  "color": ORANGE,     "size": 20, "ai": "shoot", "range": 200, "shoot": True},
    "Golem":       {"hp": 130, "atk": 20, "speed": 0.9, "exp": 36,  "color": BROWN,      "size": 30, "ai": "shoot", "range": 140, "shoot": True},
    # ── Stage 4: Sky Citadel ── fast + high damage
    "Harpy":       {"hp": 68,  "atk": 15, "speed": 3.2, "exp": 30,  "color": CYAN,       "size": 20, "ai": "shoot", "range": 180, "shoot": True},
    "StormMage":   {"hp": 78,  "atk": 18, "speed": 1.4, "exp": 38,  "color": LIGHT_BLUE, "size": 22, "ai": "shoot", "range": 260, "shoot": True},
    # ── Stage 5: Final Chamber ── elite-tier mobs
    "EliteHybrid": {"hp": 130, "atk": 26, "speed": 2.8, "exp": 50,  "color": RED,        "size": 24, "ai": "shoot", "range": 210, "shoot": True},
    "Wraith":      {"hp": 105, "atk": 23, "speed": 2.1, "exp": 44,  "color": PURPLE,     "size": 22, "ai": "shoot", "range": 200, "shoot": True},
    # ── Elite Shooters (1 per stage, sub-boss tier) ──────────────────────
    "GunnerElite":  {"hp": 160, "atk": 19, "speed": 1.6, "exp": 95,  "color": (255, 80,  180), "size": 26, "ai": "elite_shoot", "range": 300, "shoot": True, "elite": True},
    "SniperElite":  {"hp": 130, "atk": 26, "speed": 1.2, "exp": 105, "color": (80,  240, 255), "size": 24, "ai": "elite_shoot", "range": 400, "shoot": True, "elite": True},
    "BurstElite":   {"hp": 185, "atk": 15, "speed": 2.0, "exp": 100, "color": (255, 180, 50),  "size": 26, "ai": "elite_shoot", "range": 270, "shoot": True, "elite": True},
    "MissileElite": {"hp": 210, "atk": 21, "speed": 1.4, "exp": 115, "color": (180, 60,  255), "size": 28, "ai": "elite_shoot", "range": 330, "shoot": True, "elite": True},
    "OmniElite":    {"hp": 260, "atk": 24, "speed": 1.8, "exp": 140, "color": (255, 60,  60),  "size": 30, "ai": "elite_shoot", "range": 360, "shoot": True, "elite": True},
    # ── Bosses ── designed to be epic, multi-phase feeling fights ────────
    "Elder Treant":     {"hp": 360,  "atk": 20, "speed": 1.0, "exp": 210, "color": DARK_GREEN, "size": 50, "ai": "boss", "range": 180, "shoot": True},
    "Bone Overlord":    {"hp": 500,  "atk": 25, "speed": 1.3, "exp": 260, "color": WHITE,      "size": 50, "ai": "boss", "range": 210, "shoot": True},
    "Lava Titan":       {"hp": 720,  "atk": 33, "speed": 1.0, "exp": 330, "color": ORANGE,     "size": 55, "ai": "boss", "range": 230, "shoot": True},
    "Storm Sovereign":  {"hp": 960,  "atk": 39, "speed": 1.6, "exp": 420, "color": CYAN,       "size": 55, "ai": "boss", "range": 260, "shoot": True},
    "Demon King Baldr": {"hp": 1500, "atk": 50, "speed": 1.8, "exp": 750, "color": PURPLE,     "size": 60, "ai": "boss", "range": 290, "shoot": True},
}

# ── Item pools ───────────────────────────────────────────────
# (name, dmg, fire_rate, bullet_speed, rarity, color, desc, weapon_class, stat_bonus)
WEAPON_POOL = [
    # Format: (name, dmg, fire_rate, bullet_spd, rarity, color, desc, class, stat_bonus, effect)
    # Soul Knight balance — DPS target per rarity (single-shot equiv):
    #   Common ~22-32 │ Rare ~38-55 │ Epic ~65-110 │ Legendary ~110-180
    # Spread/burst weapons: per-pellet dmg × pellets × rate ≈ target DPS
    # Mana cost: 1-2 (very fast) │ 3-4 (normal) │ 5-7 (spread) │ 8-12 (epic) │ 12-16 (legendary)
    # shake: (magnitude_px, duration_sec) — tuned per weapon feel

    # ── COMMON ──────────────────────────────────────────────────────
    ("Hand Pistol",   12, 2.00, 12, "Common", LIGHT_GRAY, "Snappy starter pistol",     "Any", {},
     {"pattern":"single",       "bullet_color":(255,230,80),  "bullet_size":5,  "gun_shape":"pistol",   "gun_color":(160,160,180), "pierce":False, "mana_cost":2,  "shake":(3, 0.08)}),

    ("Revolver",      32, 0.65, 12, "Common", GOLD,       "Slow but hits hard",        "Any", {},
     {"pattern":"single",       "bullet_color":(255,200,50),  "bullet_size":8,  "gun_shape":"revolver", "gun_color":(180,140,40),  "pierce":False, "mana_cost":3,  "shake":(5, 0.15)}),

    ("SMG",            7, 5.00, 14, "Common", CYAN,       "Ultra-rapid spray",         "Any", {},
     {"pattern":"single",       "bullet_color":(80,220,255),  "bullet_size":4,  "gun_shape":"smg",      "gun_color":(40,120,160),  "pierce":False, "mana_cost":1,  "shake":(1, 0.05)}),

    ("Sawed-Off",     18, 0.55, 9,  "Common", ORANGE,     "3-pellet close range blast","Any", {},
     {"pattern":"spread3",      "bullet_color":(255,140,40),  "bullet_size":6,  "gun_shape":"shotgun",  "gun_color":(120,80,30),   "pierce":False, "mana_cost":5}),
    # DPS: 18×3×0.55 = 29.7

    ("Hunting Rifle", 28, 0.80, 17, "Common", BROWN,      "Accurate medium-range shot","Any", {},
     {"pattern":"single",       "bullet_color":(200,160,80),  "bullet_size":5,  "gun_shape":"rifle",    "gun_color":(100,60,20),   "pierce":False, "mana_cost":3,  "shake":(4, 0.12)}),

    ("Flare Gun",     22, 0.40,  7, "Common", ORANGE,     "Slow scorching flare",      "Any", {},
     {"pattern":"single",       "bullet_color":(255,80,20),   "bullet_size":10, "gun_shape":"pistol",   "gun_color":(160,80,40),   "pierce":False, "mana_cost":4,  "shake":(4, 0.12)}),

    # ── COMMON LASER ────────────────────────────────────────────────
    ("Laser Pistol",  18, 1.60,  0, "Common", RED,        "Instant laser beam, low dmg","Any", {},
     {"pattern":"laser",        "bullet_color":(255,60,60),   "bullet_size":2,  "gun_shape":"pistol",   "gun_color":(180,20,20),   "pierce":True,  "mana_cost":3,  "shake":(2, 0.09),
      "laser_color":(255,80,80),   "laser_width":2,  "laser_lifetime":0.14}),
    # DPS: 18×1.6 = 28.8 (instant hit, no travel time — tuned down slightly)

    # ── RARE ────────────────────────────────────────────────────────
    ("AK-47",         16, 3.00, 14, "Rare",   GREEN,      "High-rate assault rifle",   "Any", {},
     {"pattern":"single",       "bullet_color":(180,255,80),  "bullet_size":5,  "gun_shape":"rifle",    "gun_color":(50,100,30),   "pierce":False, "mana_cost":2,  "shake":(2, 0.06)}),

    ("Shotgun",       20, 0.45, 10, "Rare",   GRAY,       "5-pellet wide spread",      "Any", {},
     {"pattern":"spread5",      "bullet_color":(220,180,80),  "bullet_size":6,  "gun_shape":"shotgun",  "gun_color":(80,80,80),    "pierce":False, "mana_cost":7,  "shake":(7, 0.18)}),

    ("Sniper Rifle",  60, 0.35, 26, "Rare",   LIGHT_GRAY, "Piercing long-range shot",  "Any", {},
     {"pattern":"pierce",       "bullet_color":(255,255,255), "bullet_size":4,  "gun_shape":"sniper",   "gun_color":(60,60,70),    "pierce":True,  "mana_cost":6,  "shake":(8, 0.22)}),

    ("Plasma Pistol", 28, 1.20, 15, "Rare",   CYAN,       "Plasma bolts, decent rate", "Any", {},
     {"pattern":"single",       "bullet_color":(0,220,255),   "bullet_size":7,  "gun_shape":"pistol",   "gun_color":(0,120,160),   "pierce":False, "mana_cost":4,  "shake":(3, 0.09)}),

    ("Dual Pistols",  14, 1.50, 13, "Rare",   GOLD,       "2 bullets per shot",        "Any", {},
     {"pattern":"double",       "bullet_color":(255,220,60),  "bullet_size":5,  "gun_shape":"pistol",   "gun_color":(160,120,30),  "pierce":False, "mana_cost":4,  "shake":(3, 0.09)}),

    ("Dart Gun",      20, 2.20, 15, "Rare",   PURPLE,     "Rapid silent darts",        "Any", {},
     {"pattern":"single",       "bullet_color":(180,60,220),  "bullet_size":4,  "gun_shape":"pistol",   "gun_color":(80,30,120),   "pierce":False, "mana_cost":2,  "shake":(1, 0.05)}),

    # ── RARE LASER ──────────────────────────────────────────────────
    ("Laser Carbine", 32, 1.20,  0, "Rare",   CYAN,       "Rapid cyan laser beam",     "Any", {},
     {"pattern":"laser",        "bullet_color":(0,255,220),   "bullet_size":2,  "gun_shape":"rifle",    "gun_color":(0,140,130),   "pierce":True,  "mana_cost":4,  "shake":(3, 0.10),
      "laser_color":(0,240,210),   "laser_width":3,  "laser_lifetime":0.15}),
    # DPS: 32×1.2 = 38.4

    # ── EPIC ────────────────────────────────────────────────────────
    ("Grenade Launcher",65, 0.45, 8, "Epic",  ORANGE,     "Huge explosive slug",       "Any", {},
     {"pattern":"single",       "bullet_color":(255,100,0),   "bullet_size":14, "gun_shape":"launcher", "gun_color":(120,60,20),   "pierce":False, "mana_cost":8,  "shake":(10, 0.28)}),

    ("Lightning Gun", 55, 0.75, 14, "Epic",   CYAN,       "Piercing electric bolt",    "Any", {},
     {"pattern":"pierce",       "bullet_color":(100,220,255), "bullet_size":6,  "gun_shape":"rifle",    "gun_color":(20,80,120),   "pierce":True,  "mana_cost":8,  "shake":(5, 0.14)}),

    ("Railgun Mk1",   72, 0.32, 26, "Epic",   LIGHT_BLUE, "Hyper-fast armor-piercing", "Any", {},
     {"pattern":"pierce",       "bullet_color":(180,230,255), "bullet_size":4,  "gun_shape":"sniper",   "gun_color":(30,60,100),   "pierce":True,  "mana_cost":9,  "shake":(9, 0.24)}),

    ("Assault Rifle", 22, 2.00, 15, "Epic",   GREEN,      "3-shot burst, rapid fire",  "Any", {},
     {"pattern":"burst3",       "bullet_color":(150,255,100), "bullet_size":5,  "gun_shape":"rifle",    "gun_color":(40,80,30),    "pierce":False, "mana_cost":4,  "shake":(3, 0.08)}),

    # ── EPIC LASER — replaces old pierce "Laser Rifle" ──────────────
    ("Laser Rifle",   50, 0.60,  0, "Epic",   RED,        "Instant piercing red laser","Any", {},
     {"pattern":"laser",        "bullet_color":(255,30,30),   "bullet_size":3,  "gun_shape":"sniper",   "gun_color":(120,20,20),   "pierce":True,  "mana_cost":8,  "shake":(6, 0.16),
      "laser_color":(255,50,50),   "laser_width":4,  "laser_lifetime":0.17}),
    # DPS: 50×0.60 = 30 (instant) + pierce all enemies in line

    ("Minigun",       10, 8.00, 13, "Epic",   YELLOW,     "Insane fire rate, slight spread","Any", {},
     {"pattern":"spread_random","bullet_color":(255,240,80),  "bullet_size":4,  "gun_shape":"minigun",  "gun_color":(100,100,40),  "pierce":False, "mana_cost":1,  "shake":(2, 0.04)}),

    # ── LEGENDARY ───────────────────────────────────────────────────
    ("Void Cannon",   95, 0.65, 14, "Legendary", PURPLE,     "Void orb, pierces all",     "Any", {},
     {"pattern":"pierce",       "bullet_color":(180,0,255),   "bullet_size":15, "gun_shape":"launcher", "gun_color":(80,0,120),    "pierce":True,  "mana_cost":14, "shake":(11, 0.28)}),

    ("Twin Blaster",  80, 0.80, 14, "Legendary", LIGHT_BLUE, "2 massive energy bolts",    "Any", {},
     {"pattern":"double",       "bullet_color":(80,180,255),  "bullet_size":11, "gun_shape":"launcher", "gun_color":(30,80,160),   "pierce":False, "mana_cost":12, "shake":(8, 0.22)}),

    ("Dragon Cannon", 75, 0.75, 13, "Legendary", RED,        "3 exploding fire shots",    "Any", {},
     {"pattern":"spread3",      "bullet_color":(255,60,0),    "bullet_size":12, "gun_shape":"launcher", "gun_color":(140,30,0),    "pierce":False, "mana_cost":12, "shake":(9, 0.24)}),

    ("Wind Striker",  70, 1.20, 20, "Legendary", CYAN,       "Rapid burst — triple shots","Any", {},
     {"pattern":"burst3",       "bullet_color":(150,255,220), "bullet_size":7,  "gun_shape":"rifle",    "gun_color":(30,140,120),  "pierce":False, "mana_cost":10, "shake":(5, 0.12)}),

    ("Railgun Mk2",  130, 0.30, 30, "Legendary", LIGHT_BLUE, "Pierces entire map",        "Any", {},
     {"pattern":"pierce",       "bullet_color":(220,240,255), "bullet_size":5,  "gun_shape":"sniper",   "gun_color":(20,40,80),    "pierce":True,  "mana_cost":16, "shake":(12, 0.30)}),

    ("Infinity Blaster",85,1.00, 16, "Legendary", GOLD,      "Golden double, all pierce", "Any", {},
     {"pattern":"double",       "bullet_color":(255,200,0),   "bullet_size":10, "gun_shape":"launcher", "gun_color":(140,100,0),   "pierce":True,  "mana_cost":13, "shake":(9, 0.24)}),

    # ── LEGENDARY LASER — dual beam, max drama ───────────────────────
    ("Photon Cannon", 90, 0.70,  0, "Legendary", GOLD,       "Twin gold laser beams",     "Any", {},
     {"pattern":"laser_double", "bullet_color":(255,220,0),   "bullet_size":4,  "gun_shape":"launcher", "gun_color":(160,120,0),   "pierce":True,  "mana_cost":14, "shake":(10, 0.26),
      "laser_color":(255,230,60),  "laser_width":5,  "laser_lifetime":0.20}),
    # DPS: 90×2×0.70 = 126 (twin beams, both pierce)
]

ARMOR_POOL = [
    # (name, defense, rarity, color, description)
    ("Cloth Robe",    4,  "Common",    LIGHT_GRAY, "Light cloth armor."),
    ("Leather Armor", 8,  "Common",    BROWN,      "Basic leather protection."),
    ("Chainmail",     13, "Rare",      GRAY,       "Metal chain links."),
    ("Plate Armor",   18, "Rare",      LIGHT_GRAY, "Heavy steel plate."),
    ("Shadow Cloak",  22, "Epic",      PURPLE,     "+20 AGI, dodge 10%."),
    ("Dragon Scale",  28, "Epic",      ORANGE,     "Fire resistance +30%."),
    ("Aegis Plate",   40, "Legendary", GOLD,       "Blocks 1 hit every 10 sec."),
    ("Void Robe",     32, "Legendary", PURPLE,     "+50% spell power."),
]

ACCESSORY_POOL = [
    # (name, rarity, color, effect_desc, stat_bonus)  — keys are direct Player attrs
    ("Iron Ring",      "Common",    GRAY,       "+6 ATK",                      {"base_damage": 6}),
    ("Speed Boots",    "Common",    BROWN,      "+0.5 Move Speed",             {"move_speed": 0.5}),
    ("HP Talisman",    "Rare",      RED,        "+35 Max HP",                  {"max_hp": 35}),
    ("Mana Crystal",   "Rare",      LIGHT_BLUE, "+30 Max Mana",                {"max_mana": 30}),
    ("Lucky Charm",    "Epic",      GOLD,       "+10% Crit Chance",            {"crit_chance": 0.10}),
    ("Berserker Ring", "Epic",      RED,        "+15 ATK, -20 Max HP",         {"base_damage": 15, "max_hp": -20}),
    ("God's Amulet",   "Legendary", GOLD,       "+12 ATK, +50 HP, +0.5 Spd",  {"base_damage": 12, "max_hp": 50, "move_speed": 0.5}),
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
            "cooldown": 3.5,       # ↓ 4.0→3.5  (more frequent, feels snappier)
            "mana_cost": 12,       # ↓ 15→12    (less punishing)
            "type": "dash",
            "color": (0, 220, 200),
            "description": "Dash forward quickly. Brief invincibility.",
        },
        {
            "name": "Star Shot",
            "key": "F",
            "cooldown": 5.5,       # ↓ 6.0→5.5
            "mana_cost": 20,       # ↓ 25→20
            "type": "star_spread",
            "color": (255, 210, 0),
            "description": "Fire 3 star bullets in a spread.",
        },
        {
            "name": "Frenzy",
            "key": "R",
            "cooldown": 9.0,       # ↑ 8.0→9.0  (duration is strong, needs longer cd)
            "mana_cost": 22,       # ↑ 20→22
            "type": "rapid_fire",
            "duration": 3.5,       # ↑ 3.0→3.5  (feels more rewarding per use)
            "color": (255, 100, 30),
            "description": "Fire rate x2.5 for 3.5 seconds.",
        },
    ],
}