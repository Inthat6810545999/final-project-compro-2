# Sausage Man: Legends of Midgard
### Top-Down Roguelite Action RPG — Python / Pygame Year Project

---

## Quick Start

```bash
# 1. Install dependencies
pip install pygame numpy pandas matplotlib seaborn

# 2. Run the game
python main.py
```

---

## Controls

| Key / Button       | Action                          |
|--------------------|---------------------------------|
| WASD / Arrow Keys  | Move character                  |
| Left Mouse Click   | Attack / Shoot toward cursor    |
| E                  | Pick up item on the ground      |
| I                  | Open inventory & stats screen   |
| ESC                | Pause / Close menu              |

---

## Game Structure

### Classes
| Class       | Description                              |
|-------------|------------------------------------------|
| Warrior     | Tank melee. High HP. Iron Skin passive.  |
| Mage        | Spellcaster. Pierce bullets. AoE damage. |
| Ranger      | Swift ranged. High crit & speed.         |

### Stages (5 total)
1. **Forest of Trials** — Slimes, Wolves → Boss: Elder Treant
2. **Dungeon of Shadows** — Skeletons, Bats → Boss: Bone Overlord
3. **Volcanic Fortress** — Fire Imps, Golems → Boss: Lava Titan
4. **Sky Citadel** — Harpies, Storm Mages → Boss: Storm Sovereign
5. **Final Chamber** — Elite Hybrids, Wraiths → Boss: Demon King Baldr

### Between Stages
After clearing a stage, a **Shop** opens. Spend gold to:
- Heal 50 HP
- Buy weapons, armor, or accessories

---

## RPG Progression

### Stats (Ragnarok Online style)
| Stat | Effect                        |
|------|-------------------------------|
| STR  | +2 physical attack per point  |
| AGI  | +0.05 move speed per point    |
| VIT  | +8 max HP per point           |
| INT  | +2.5 magic damage per point   |
| DEX  | +0.5% crit chance per point   |
| LUK  | +1% better loot drops         |

Gain **3 stat points** on each level up. Allocate via inventory screen.

### Equipment Slots
- **Weapon** — Melee or ranged (fire rate, damage)
- **Armor** — Defense bonus
- **Accessory** — Stat bonuses

### Item Rarities
Common → Rare → **Epic** → **Legendary**

---

## Statistics Dashboard

Run the game, play several sessions, then click **STATISTICS** on the main menu
to open the Matplotlib dashboard. It charts:

1. Score per Run (line chart)
2. Enemies Defeated (histogram)
3. Avg Score by Class (bar)
4. Run Duration (histogram)
5. Stage Completion Rate (stacked bar)
6. Kills vs Damage (scatter)

Data is saved to `stats/gameplay_data.csv` and `stats/combat_log.csv`.

---

## OOP Class Structure

```
GameManager          # Controller — owns game loop
├── Player           # Hero: movement, combat, leveling, inventory
├── Stage            # BSP dungeon generation, camera, minimap
│   └── Room         # Single room with spawn points
├── Enemy (base)     # AI state machine (IDLE/PATROL/CHASE/ATTACK/FLEE)
│   ├── MeleeEnemy   # Chases and melees
│   ├── RangedEnemy  # Keeps distance, fires projectiles
│   └── BossEnemy    # Multi-phase boss, spread shots
├── Item (base)      # Collectible items
│   ├── Weapon       # Melee or ranged
│   ├── Armor        # Defense equipment
│   └── Accessory    # Stat-bonus rings/boots
└── StatsTracker     # CSV logging + Matplotlib dashboard
```

---

## Algorithms Used

| Algorithm              | Location               |
|------------------------|------------------------|
| A*-style pathfinding   | Enemy.update()         |
| FSM (5 states)         | Enemy.change_ai_state()|
| BSP room generation    | Stage.generate_rooms() |
| Weighted random loot   | Enemy.drop_loot()      |
| Ragnarok damage formula| Player.calc_damage()   |
| AABB collision         | Player.move()          |
| Polynomial EXP curve   | Player.gain_exp()      |

---

## Project Files

```
sausage_man/
├── main.py            # Entry point
├── constants.py       # All config, colors, enemy/item data
├── game_manager.py    # GameManager class (controller)
├── player.py          # Player class
├── enemy.py           # Enemy / MeleeEnemy / RangedEnemy / BossEnemy
├── item.py            # Item / Weapon / Armor / Accessory + factory
├── stage.py           # Stage / Room + BSP generator
├── bullet.py          # Bullet, DroppedItem, FloatingText, HUD
├── stats_tracker.py   # StatsTracker (CSV + Matplotlib)
├── ui.py              # All UI screens
├── requirements.txt
├── README.md
└── stats/             # Auto-created — CSV data files
```
