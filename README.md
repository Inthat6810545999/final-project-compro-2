# Sausage Man: Legends of Midgard

## Project Description

- **Project by:** Inthat Niramarn (6810545999)
- **Game Genre:** Top-Down Action Shooter / Roguelite

A fast-paced top-down shooter built with Pygame where you play as the legendary Sausage Man, battling through 5 procedurally-generated stages filled with enemies, elite shooters, and powerful bosses. Collect weapons, armor, and accessories, manage your mana, and use special skills to survive the Legends of Midgard.

---

## Installation

Clone this project:
```sh
git clone https://github.com/<your-username>/sausage-man-legends-of-midgard.git
cd sausage-man-legends-of-midgard
```

**Windows:**
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Mac / Linux:**
```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Running Guide

After activating the Python environment, run the game with:

**Windows:**
```bat
python main.py
```

**Mac / Linux:**
```sh
python3 main.py
```

> **Note:** The game requires an audio device for sound. If none is found, the game will run silently without crashing.

---

## Tutorial / Usage

| Control | Action |
|---|---|
| `W A S D` / Arrow Keys | Move the character |
| `Left Click` | Shoot / Attack toward cursor |
| `E` | Pick up item on the ground |
| `I` | Open / close inventory |
| `Q` | Use Skill 1 — Dash |
| `F` | Use Skill 2 — Star Shot |
| `R` | Use Skill 3 — Frenzy |
| `ESC` | Pause / Back |
| `M` | Toggle sound on/off |

**Basic loop:**
1. From the Main Menu, select **New Game** to start.
2. Fight through enemies in each stage room.
3. Defeat all enemies to open the **portal** to the next stage.
4. Pick up dropped items (`E`) and manage your loadout via Inventory (`I`).
5. Visit the **Shop** between stages to buy upgrades with gold.
6. Defeat the **Boss** at the end of each stage to progress.
7. Survive all 5 stages to achieve **Victory**!

---

## Game Features

- **5 Themed Stages** — Forest, Dungeon, Volcano, Sky Citadel, and Final Chamber, each with unique enemies and a boss.
- **30+ Weapons** across 4 rarities (Common → Legendary), including pistols, shotguns, snipers, lasers, and rocket launchers. Each weapon has unique bullet patterns: single, spread, pierce, burst, and laser beam.
- **8 Armor Sets** with animated visual overlays (particles, glows, and auras) drawn procedurally onto the player sprite.
- **7 Accessories** providing passive stat bonuses (ATK, HP, speed, crit chance, etc.).
- **3 Active Skills** — Dash, Star Shot, and Frenzy — each with a cooldown and mana cost.
- **Enemy AI** — Enemies use state-machine AI (Idle → Patrol → Chase → Attack → Flee) and shoot back at the player.
- **Elite Shooters & Bosses** — Each stage has a unique elite enemy type and a boss with cinematic intro/death sequences and screen shake.
- **Procedural Audio** — All sound effects are synthesized in real-time using NumPy waveforms. No external audio files needed.
- **Statistics Dashboard** — Gameplay data (score, kills, damage, duration, stage reached) is saved to CSV and visualized in a 6-panel Matplotlib dashboard.
- **Shooting Range** — A practice mode accessible from the main menu to test weapons.
- **Inventory & Shop System** — Collect items, compare equipment, equip/unequip gear, and buy items with gold.

---

## Known Bugs

- Some enemy PNG sprites may fail to load if the `sprite/entity_sprite/` folder is missing or incomplete; the game falls back to drawn shapes.
- Gun PNG sprites require a `sprite/gun_sprite/` subfolder; missing files fall back to polygon rendering.
- Armor regen visual and certain particle effects may appear offset slightly depending on screen resolution.

---

## Unfinished Works

- Additional character classes beyond Sausage Man were planned but not implemented.
- **Boss multi-phase behaviors** — Bosses currently have a single attack pattern. Planned work includes adding phase transitions (e.g., enrage at 50% HP), new attack patterns per phase, and unique telegraphed moves for each of the 5 stage bosses.
- **Skill effect icons & visual feedback** — The HUD skill slots (Dash, Star Shot, Frenzy) lack distinctive logos/icons. Planned work includes drawing per-skill icon art and adding cast animations (e.g., flash overlay, screen-edge glow) so the player can clearly see which skill was activated.
- **Item pickup 2D model preview** — When the player picks up or hovers over a weapon, armor, or accessory, there is no visual representation of the item itself. Planned work includes rendering a small rotating sprite/model of the item (gun shape, armor silhouette, accessory icon) in the pickup tooltip or as a world-space billboard.
- **Improved visual effects** — Several particle effects (bullet impacts, armor auras, portal swirl, boss death explosion) need polish. Planned work includes higher-density particle systems, additive blending, and screen-space distortion effects for key moments.
- **Game balance pass** — Enemy HP, damage values, weapon damage scaling, and gold economy need tuning based on playtesting data. Planned work includes reviewing the statistics dashboard data across multiple runs and adjusting per-stage difficulty curves, weapon tier power gaps, and boss health pools.
- All 5 stages and core gameplay loop are fully functional and complete.

---

## External Sources

1. **Pygame** — https://www.pygame.org — Game framework (LGPL License)
2. **NumPy** — https://numpy.org — Procedural audio synthesis (BSD License)
3. **Pandas** — https://pandas.pydata.org — Data handling (BSD License)
4. **Matplotlib** — https://matplotlib.org — Statistics visualization (PSF-based License)
5. **Seaborn** — https://seaborn.pydata.org — Plot styling (BSD License)
6. **Sausageguy.png** — Player character sprite (original artwork for this project)