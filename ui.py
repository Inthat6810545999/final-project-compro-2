"""
ui.py  –  All UI screens
Changes:
  - InventoryScreen: replaced Ragnarok STR/AGI/VIT stats panel with
    Soul Knight style resource bars (HP, Armor, Mana) + combat stats
  - MainMenuScreen: updated hint text (I → TAB)
  - ClassSelectScreen: Soul Knight resource preview bars
  - ShopScreen: cleaner layout, "CONTINUE →" button
"""
import pygame
from constants import (
    SCREEN_W, SCREEN_H, HUD_H, CLASSES, RARITY_COLORS,
    SHOP_HEAL_COST, SHOP_ITEM_MULT, SHOP_REROLL_COST,
    BLACK, WHITE, GRAY, DARK_GRAY, RED, GREEN, BLUE, CYAN,
    YELLOW, GOLD, PURPLE, ORANGE, LIGHT_GRAY, LIGHT_BLUE,
)
from item import make_weapon, make_armor, make_accessory, make_random_item
import random
import math

# ── Font helpers ──────────────────────────────────────────────
_fc = {}
def F(size, bold=False):
    key = (size, bold)
    if key not in _fc:
        _fc[key] = pygame.font.SysFont("Arial", size, bold=bold)
    return _fc[key]

def text(surf, msg, x, y, size=20, color=WHITE, bold=False, center=False):
    s = F(size, bold).render(str(msg), True, color)
    if center:
        x -= s.get_width() // 2
    surf.blit(s, (x, y))
    return s.get_width(), s.get_height()

def panel(surf, x, y, w, h, fill=(20, 20, 40), border=BLUE, radius=8):
    r = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surf, fill, r, border_radius=radius)
    pygame.draw.rect(surf, border, r, 2, border_radius=radius)
    return r

def button(surf, x, y, w, h, label, hover=False, color=BLUE, size=18):
    fill = (min(255, color[0]+40), min(255, color[1]+40), min(255, color[2]+40)) \
           if hover else (color[0]//2, color[1]//2, color[2]//2)
    r = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surf, fill, r, border_radius=6)
    pygame.draw.rect(surf, color, r, 2, border_radius=6)
    s = F(size, True).render(label, True, WHITE)
    surf.blit(s, (x + w//2 - s.get_width()//2, y + h//2 - s.get_height()//2))
    return r

def _bar(surf, x, y, w, h, val, maximum, color, bg=(20, 20, 30)):
    """Reusable filled progress bar."""
    pygame.draw.rect(surf, bg, (x, y, w, h), border_radius=5)
    pct    = max(0.0, min(1.0, val / max(1e-6, maximum)))
    fill_w = max(0, int((w - 4) * pct))
    if fill_w:
        pygame.draw.rect(surf, color, (x+2, y+2, fill_w, h-4), border_radius=4)
    pygame.draw.rect(surf, (80, 80, 100), (x, y, w, h), 1, border_radius=5)


# ─────────────────────────────────────────────────────────────
class MainMenuScreen:
    def __init__(self, tracker):
        self.tracker = tracker

    def draw(self, surface, mouse_pos):
        surface.fill((8, 8, 20))
        text(surface, "SAUSAGE MAN", SCREEN_W//2, 80, 64, GOLD, bold=True, center=True)
        text(surface, "LEGENDS OF MIDGARD", SCREEN_W//2, 148, 28, CYAN, bold=True, center=True)
        pygame.draw.line(surface, BLUE, (120, 185), (SCREEN_W-120, 185), 2)

        bw, bh, bx = 260, 52, SCREEN_W//2 - 130
        self.btn_play  = button(surface, bx, 220, bw, bh, "NEW GAME",
                                pygame.Rect(bx, 220, bw, bh).collidepoint(mouse_pos), GREEN)
        self.btn_stats = button(surface, bx, 290, bw, bh, "STATISTICS",
                                pygame.Rect(bx, 290, bw, bh).collidepoint(mouse_pos), BLUE)
        self.btn_quit  = button(surface, bx, 360, bw, bh, "QUIT",
                                pygame.Rect(bx, 360, bw, bh).collidepoint(mouse_pos), RED)

        summary = self.tracker.get_summary()
        panel(surface, SCREEN_W//2 - 200, 430, 400, 120, fill=(15, 15, 30))
        if summary.get("total_runs", 0) > 0:
            text(surface, f"Total Runs: {summary['total_runs']}    Victories: {summary['victories']}",
                 SCREEN_W//2, 445, 17, LIGHT_GRAY, center=True)
            text(surface, f"Best Score: {summary['best_score']:,}",
                 SCREEN_W//2, 468, 17, GOLD, center=True)
            text(surface, f"Avg Kills:  {summary['avg_kills']}    Max Level: {summary['max_level']}",
                 SCREEN_W//2, 491, 17, LIGHT_GRAY, center=True)
            text(surface, f"Avg Run Time: {summary['avg_duration']}s",
                 SCREEN_W//2, 514, 17, LIGHT_GRAY, center=True)
        else:
            text(surface, "No runs yet. Play to collect statistics!",
                 SCREEN_W//2, 478, 17, GRAY, center=True)

        # Updated: I → TAB
        text(surface,
             "WASD: Move   LClick: Attack   E: Pick Up   TAB: Inventory   ESC: Pause",
             SCREEN_W//2, SCREEN_H-30, 14, GRAY, center=True)

    def handle_click(self, pos):
        if self.btn_play.collidepoint(pos):   return "play"
        if self.btn_stats.collidepoint(pos):  return "stats"
        if self.btn_quit.collidepoint(pos):   return "quit"
        return None


# ─────────────────────────────────────────────────────────────
class ClassSelectScreen:
    """
    Soul Knight style character select:
    - Left panel: scrollable character roster with animated preview
    - Right panel: detailed stats, passive, skill info
    - Animated character sprite (shooting/melee) in preview box
    """

    # Character visual definitions (shape, colors, accessories)
    CHAR_VISUALS = {
        "Mage": {
            "body_col":   (140, 50,  220),
            "armor_col":  (60,  20,  100),
            "detail_col": (200, 120, 255),
            "weapon":     "staff",
        },
        "Necromancer": {
            "body_col":   (60,  180, 120),
            "armor_col":  (20,  60,  40),
            "detail_col": (120, 255, 180),
            "weapon":     "staff",
        },
        "Ranger": {
            "body_col":   (50,  190, 80),
            "armor_col":  (30,  80,  30),
            "detail_col": (180, 255, 120),
            "weapon":     "bow",
        },
        "Rogue": {
            "body_col":   (80,  160, 220),
            "armor_col":  (20,  50,  80),
            "detail_col": (150, 210, 255),
            "weapon":     "bow",
        },
    }

    STAT_LABELS = ["STR", "AGI", "VIT", "INT", "DEX", "LUK"]
    STAT_COLORS = {
        "STR": (220, 80,  80),
        "AGI": (80,  220, 80),
        "VIT": (220, 180, 60),
        "INT": (140, 80,  240),
        "DEX": (80,  200, 220),
        "LUK": (255, 215, 0),
    }

    def __init__(self):
        self.selected    = None
        self.hovered     = None
        self._anim_t     = 0.0
        self._char_list  = list(CLASSES.keys())

    def _draw_character_sprite(self, surface, cx, cy, char_name, t, scale=1.0):
        """Draw an animated pixel-art style character at (cx,cy)."""
        vis  = self.CHAR_VISUALS.get(char_name, self.CHAR_VISUALS["Mage"])
        wpn  = vis["weapon"]
        bcol = vis["body_col"]
        acol = vis["armor_col"]
        dcol = vis["detail_col"]

        # Body bob animation
        bob = int(math.sin(t * 4) * 2 * scale)
        r   = int(14 * scale)

        # Shadow
        pygame.draw.ellipse(surface, (10, 10, 20),
                            (cx - r, cy + r * 2 + bob + 2, r * 2, int(r * 0.5)))

        # Legs (walk animation)
        leg_swing = int(math.sin(t * 6) * 4 * scale)
        leg_r     = int(5 * scale)
        pygame.draw.circle(surface, acol, (cx - int(4*scale), cy + r + bob + int(4*scale) + leg_swing), leg_r)
        pygame.draw.circle(surface, acol, (cx + int(4*scale), cy + r + bob + int(4*scale) - leg_swing), leg_r)

        # Body
        pygame.draw.circle(surface, bcol, (cx, cy + bob), r)
        pygame.draw.circle(surface, acol, (cx, cy + bob), r, int(2*scale))

        # Armor plate detail
        arm_r = int(r * 0.65)
        pygame.draw.ellipse(surface, acol,
                            (cx - arm_r, cy + bob - int(4*scale), arm_r*2, int(arm_r*1.2)))

        # Eyes
        eye_off = int(4 * scale)
        eye_r   = max(2, int(3 * scale))
        pygame.draw.circle(surface, (240, 240, 255), (cx - eye_off, cy + bob - int(3*scale)), eye_r)
        pygame.draw.circle(surface, (240, 240, 255), (cx + eye_off, cy + bob - int(3*scale)), eye_r)
        pygame.draw.circle(surface, (20, 20, 40),    (cx - eye_off, cy + bob - int(3*scale)), max(1, eye_r-1))
        pygame.draw.circle(surface, (20, 20, 40),    (cx + eye_off, cy + bob - int(3*scale)), max(1, eye_r-1))

        # Weapon
        shoot_angle = math.sin(t * 2) * 0.15
        wx = cx + int(r * math.cos(shoot_angle))
        wy = cy + bob + int(r * 0.3 * math.sin(shoot_angle))

        if wpn == "staff":
            # Staff: long rod + orb
            sx, sy = wx + int(16*scale), wy - int(20*scale)
            pygame.draw.line(surface, dcol, (sx, sy + int(36*scale)), (sx, sy), int(3*scale))
            orb_col = (200, 120, 255) if char_name == "Mage" else (80, 255, 160)
            orb_r   = int(6 * scale)
            orb_glow = int(math.sin(t * 5) * 1.5 + 8)
            pygame.draw.circle(surface, orb_col, (sx, sy), orb_r + orb_glow // 3)
            pygame.draw.circle(surface, (240, 220, 255), (sx, sy), orb_r)
        elif wpn == "bow":
            # Bow: arc shape
            bx, by = wx + int(18*scale), wy
            bow_r = int(12 * scale)
            pygame.draw.arc(surface, dcol,
                            (bx - bow_r, by - bow_r, bow_r * 2, bow_r * 2),
                            -0.8, 0.8, int(2*scale))
            # String
            pygame.draw.line(surface, (200, 200, 200),
                             (bx + int(bow_r * 0.6), by - int(bow_r * 0.7)),
                             (bx + int(bow_r * 0.6), by + int(bow_r * 0.7)), 1)

        # Class-specific detail
        if char_name == "Mage":
            # Wizard hat
            hat_pts = [
                (cx - int(12*scale), cy + bob - r + int(2*scale)),
                (cx + int(12*scale), cy + bob - r + int(2*scale)),
                (cx + int(8*scale),  cy + bob - r - int(4*scale)),
                (cx,                 cy + bob - r - int(20*scale)),
                (cx - int(8*scale),  cy + bob - r - int(4*scale)),
            ]
            pygame.draw.polygon(surface, (60, 20, 100), hat_pts)
            pygame.draw.polygon(surface, dcol, hat_pts, int(2*scale))
        elif char_name == "Necromancer":
            # Hood
            hood_pts = [
                (cx - int(13*scale), cy + bob - r + int(2*scale)),
                (cx + int(13*scale), cy + bob - r + int(2*scale)),
                (cx + int(10*scale), cy + bob - r - int(8*scale)),
                (cx,                 cy + bob - r - int(14*scale)),
                (cx - int(10*scale), cy + bob - r - int(8*scale)),
            ]
            pygame.draw.polygon(surface, (20, 60, 40), hood_pts)
            pygame.draw.polygon(surface, dcol, hood_pts, int(2*scale))
        elif char_name == "Ranger":
            # Quiver on back
            pygame.draw.rect(surface, BROWN if 'BROWN' in dir() else (139,90,43),
                             (cx + r - int(2*scale), cy + bob - int(8*scale),
                              int(8*scale), int(20*scale)), border_radius=2)
        elif char_name == "Rogue":
            # Mask
            pygame.draw.rect(surface, (20, 50, 80),
                             (cx - int(8*scale), cy + bob - int(2*scale),
                              int(16*scale), int(5*scale)), border_radius=2)
            pygame.draw.rect(surface, dcol,
                             (cx - int(8*scale), cy + bob - int(2*scale),
                              int(16*scale), int(5*scale)), 1, border_radius=2)

    def draw(self, surface, mouse_pos, dt=0.016):
        self._anim_t += dt

        surface.fill((6, 8, 18))

        # Title
        text(surface, "SELECT CHARACTER", SCREEN_W//2, 18, 38, GOLD, bold=True, center=True)
        pygame.draw.line(surface, (40, 60, 120), (60, 65), (SCREEN_W-60, 65), 2)

        chars      = self._char_list
        n          = len(chars)
        card_w     = 150
        card_h     = 200
        gap        = 12
        total_w    = n * card_w + (n-1) * gap
        start_x    = SCREEN_W//2 - total_w//2
        roster_y   = 75

        self.char_rects = {}

        for i, cname in enumerate(chars):
            cfg   = CLASSES[cname]
            cx    = start_x + i * (card_w + gap)
            cy    = roster_y
            hover = pygame.Rect(cx, cy, card_w, card_h).collidepoint(mouse_pos)
            sel   = (self.selected == cname)

            # Card background
            if sel:
                fill   = (35, 45, 75)
                border = cfg["color"]
                bw     = 3
            elif hover:
                fill   = (25, 32, 55)
                border = tuple(min(255, c + 60) for c in cfg["color"])
                bw     = 2
            else:
                fill   = (15, 18, 35)
                border = tuple(c // 2 for c in cfg["color"])
                bw     = 1

            pygame.draw.rect(surface, fill,   (cx, cy, card_w, card_h), border_radius=10)
            pygame.draw.rect(surface, border, (cx, cy, card_w, card_h), bw, border_radius=10)

            if sel:
                # Glow effect
                glow_surf = pygame.Surface((card_w+8, card_h+8), pygame.SRCALPHA)
                glow_a    = int(60 + 30 * math.sin(self._anim_t * 3))
                pygame.draw.rect(glow_surf, (*cfg["color"], glow_a),
                                 (0, 0, card_w+8, card_h+8), 4, border_radius=12)
                surface.blit(glow_surf, (cx-4, cy-4))

            # Animated character sprite in card
            anim_speed = 1.5 if sel else (0.8 if hover else 0.3)
            self._draw_character_sprite(
                surface, cx + card_w//2, cy + 80, cname,
                self._anim_t * anim_speed, scale=1.4
            )

            # Name
            text(surface, cname, cx + card_w//2, cy + card_h - 72,
                 16, cfg["color"], bold=True, center=True)

            # Weapon category badge
            wcat = cfg.get("weapon_class", "Any")
            wcat_col = {
                "Warrior": (220, 80, 80),
                "Mage":    (160, 80, 255),
                "Ranger":  (80, 200, 80),
            }.get(wcat, GRAY)
            badge_w = 80
            bx = cx + card_w//2 - badge_w//2
            pygame.draw.rect(surface, (wcat_col[0]//3, wcat_col[1]//3, wcat_col[2]//3),
                             (bx, cy + card_h - 52, badge_w, 18), border_radius=4)
            pygame.draw.rect(surface, wcat_col, (bx, cy + card_h - 52, badge_w, 18), 1, border_radius=4)
            text(surface, wcat, cx + card_w//2, cy + card_h - 51,
                 12, wcat_col, center=True)

            # Speed pip row
            spd_int = min(5, max(1, int(cfg["speed"])))
            pips    = ""
            for p_i in range(5):
                pips += "●" if p_i < spd_int else "○"
            text(surface, f"SPD {pips}", cx + card_w//2, cy + card_h - 28,
                 11, (100, 200, 100), center=True)

            self.char_rects[cname] = pygame.Rect(cx, cy, card_w, card_h)

        # ── Detail panel (right side below cards) ────────────
        if self.selected:
            cfg    = CLASSES[self.selected]
            vis    = self.CHAR_VISUALS.get(self.selected, {})
            from constants import CLASS_SKILLS
            skill  = CLASS_SKILLS.get(self.selected, {})

            detail_y = roster_y + card_h + 18
            detail_h = SCREEN_H - detail_y - 60

            # Split into left (big preview) and right (stats)
            prev_w = 200
            prev_x = SCREEN_W//2 - 440
            stat_x = prev_x + prev_w + 20
            stat_w = SCREEN_W//2 + 440 - stat_x

            # Big preview box
            panel(surface, prev_x, detail_y, prev_w, detail_h,
                  fill=(12, 14, 28), border=cfg["color"])

            # Animated character (large)
            self._draw_character_sprite(
                surface,
                prev_x + prev_w//2,
                detail_y + detail_h//2 - 10,
                self.selected,
                self._anim_t * 2.0,
                scale=2.2
            )

            # Character name below sprite
            text(surface, self.selected,
                 prev_x + prev_w//2, detail_y + detail_h - 36,
                 18, cfg["color"], bold=True, center=True)

            # ── Stats column ──────────────────────────────────
            panel(surface, stat_x, detail_y, stat_w, detail_h,
                  fill=(10, 12, 24), border=(40, 50, 100))

            sy = detail_y + 10

            # Description
            text(surface, cfg["description"], stat_x + 10, sy, 13, LIGHT_GRAY)
            sy += 22

            pygame.draw.line(surface, (30, 40, 80),
                             (stat_x + 8, sy), (stat_x + stat_w - 8, sy))
            sy += 8

            # ── Resource bars ─────────────────────────────────
            text(surface, "RESOURCES", stat_x + 10, sy, 13, CYAN, bold=True)
            sy += 18
            res = [
                ("HP",    cfg["base_hp"],           200, RED),
                ("Armor", cfg.get("max_armor", 80), 140, CYAN),
                ("Mana",  cfg.get("max_mana", 120), 200, BLUE),
                ("Speed", int(cfg["speed"] * 20),   100, GREEN),
            ]
            for lbl, val, maxv, col in res:
                text(surface, lbl, stat_x + 10, sy, 12, col, bold=True)
                bw2 = stat_w - 80
                pygame.draw.rect(surface, (20, 20, 35), (stat_x + 54, sy + 2, bw2, 11), border_radius=4)
                fw = int(bw2 * min(1.0, val / maxv))
                if fw > 0:
                    pygame.draw.rect(surface, col, (stat_x + 54, sy + 2, fw, 11), border_radius=4)
                text(surface, str(val), stat_x + 58 + bw2, sy, 11, WHITE)
                sy += 18

            pygame.draw.line(surface, (30, 40, 80),
                             (stat_x + 8, sy + 2), (stat_x + stat_w - 8, sy + 2))
            sy += 10

            # ── Starter weapon ────────────────────────────────
            text(surface, "STARTER WEAPON", stat_x + 10, sy, 13, CYAN, bold=True)
            sy += 18
            wpn_info = {
                "Mage":        ("Magic Wand",   16, "0.55/s", "Pierces 1 enemy"),
                "Necromancer": ("Soul Staff",   14, "0.60/s", "Dark bolts"),
                "Ranger":      ("Short Bow",    15, "0.70/s", "Fast arrows"),
                "Rogue":       ("Hand Pistol",  13, "0.80/s", "Rapid fire"),
            }.get(self.selected, ("?", 0, "?", ""))
            text(surface, wpn_info[0], stat_x + 10, sy, 13, GOLD, bold=True)
            sy += 16
            text(surface, f"DMG {wpn_info[1]}  Rate {wpn_info[2]}  {wpn_info[3]}",
                 stat_x + 10, sy, 11, LIGHT_GRAY)
            sy += 20

            pygame.draw.line(surface, (30, 40, 80),
                             (stat_x + 8, sy + 2), (stat_x + stat_w - 8, sy + 2))
            sy += 10

            # ── Passive ───────────────────────────────────────
            text(surface, "PASSIVE", stat_x + 10, sy, 13, YELLOW, bold=True)
            sy += 16
            ptext = cfg.get("passive", "")
            for chunk in [ptext[i:i+48] for i in range(0, len(ptext), 48)]:
                text(surface, chunk, stat_x + 10, sy, 11, LIGHT_GRAY)
                sy += 14

            pygame.draw.line(surface, (30, 40, 80),
                             (stat_x + 8, sy + 2), (stat_x + stat_w - 8, sy + 2))
            sy += 10

            # ── Skill ─────────────────────────────────────────
            text(surface, "SKILL  [Q]", stat_x + 10, sy, 13, (80, 200, 255), bold=True)
            sy += 16
            if skill:
                sk_name = skill.get("name", "")
                sk_cd   = skill.get("cooldown", 5.0)
                sk_mp   = skill.get("mana_cost", 0)
                sk_desc = skill.get("description", "")
                text(surface, f"{sk_name}", stat_x + 10, sy, 14, (120, 220, 255), bold=True)
                text(surface, f"CD:{sk_cd:.1f}s  MP:{sk_mp}",
                     stat_x + 10, sy + 16, 11, ORANGE)
                sy += 30
                for chunk in [sk_desc[i:i+48] for i in range(0, len(sk_desc), 48)]:
                    text(surface, chunk, stat_x + 10, sy, 11, LIGHT_GRAY)
                    sy += 14

        elif not self.selected:
            # No selection prompt
            text(surface, "← Click a character to see details →",
                 SCREEN_W//2, roster_y + card_h + 40, 18, GRAY, center=True)

        # ── Bottom buttons ────────────────────────────────────
        self.btn_back = button(surface, 30, SCREEN_H - 54, 120, 40, "BACK", False, GRAY)

        if self.selected:
            bx2  = SCREEN_W - 230
            col2 = cfg["color"] if self.selected else GRAY
            play_hover = pygame.Rect(bx2, SCREEN_H - 54, 200, 40).collidepoint(mouse_pos)
            self.btn_play = button(surface, bx2, SCREEN_H - 54, 200, 40,
                                   f"PLAY  {self.selected}", play_hover, GREEN)
        else:
            self.btn_play = None

        text(surface,
             "Q: Skill   WASD: Move   Click: Attack   E: Pick Up   TAB: Inventory",
             SCREEN_W//2, SCREEN_H - 16, 12, GRAY, center=True)

    def handle_click(self, pos):
        for cname, rect in self.char_rects.items():
            if rect.collidepoint(pos):
                if self.selected == cname:
                    return cname   # double-click or re-click = confirm
                self.selected = cname
                return None   # just select, don't start game yet

        if hasattr(self, "btn_play") and self.btn_play and self.btn_play.collidepoint(pos):
            if self.selected:
                return self.selected

        if hasattr(self, "btn_back") and self.btn_back.collidepoint(pos):
            return "back"
        return None


# ─────────────────────────────────────────────────────────────
class InventoryScreen:
    """
    Soul Knight style inventory.
    Left  – equipped gear + backpack item list
    Right – HP/Armor/Mana resource bars + combat stats
            (Ragnarok STR/AGI/VIT panel completely removed)
    """

    def __init__(self):
        self.selected_idx = 0
        self.scroll       = 0

    def draw(self, surface, player, mouse_pos):
        # Dim game behind
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        W, H = 840, 590
        ox   = SCREEN_W//2 - W//2
        oy   = SCREEN_H//2 - H//2
        panel(surface, ox, oy, W, H, fill=(10, 10, 24), border=BLUE)
        text(surface, "INVENTORY", ox + W//2, oy + 10, 26, GOLD, bold=True, center=True)

        LEFT_W = 530   # left column width

        # ── Equipment slots (top) ─────────────────────────────
        text(surface, "EQUIPPED", ox+14, oy+46, 15, CYAN, bold=True)
        for si, slot in enumerate(["weapon", "armor", "accessory"]):
            itm  = player.equipment.get(slot)
            ex   = ox + 14 + si * 172
            ey   = oy + 66
            col  = RARITY_COLORS.get(itm.rarity, WHITE) if itm else GRAY
            panel(surface, ex, ey, 162, 54, fill=(18, 18, 38), border=col)
            text(surface, slot.upper(), ex+6, ey+4, 11, GRAY)
            text(surface, (itm.name if itm else "— empty —")[:18],
                 ex+6, ey+20, 14, col if itm else GRAY, bold=bool(itm))
            if itm:
                if hasattr(itm, "damage"):
                    text(surface, f"DMG {itm.damage}", ex+6, ey+38, 11, LIGHT_GRAY)
                elif hasattr(itm, "defense"):
                    text(surface, f"DEF {itm.defense}", ex+6, ey+38, 11, LIGHT_GRAY)

        pygame.draw.line(surface, (40, 40, 80), (ox+14, oy+130), (ox+LEFT_W-10, oy+130))

        # ── Backpack list ─────────────────────────────────────
        text(surface, f"BACKPACK  ({len(player.inventory)} items)",
             ox+14, oy+136, 15, CYAN, bold=True)
        VISIBLE = 7
        self.item_rects = {}
        self.equip_btns = {}

        for idx in range(VISIBLE):
            real_idx = idx + self.scroll
            if real_idx >= len(player.inventory):
                break
            itm    = player.inventory[real_idx]
            iy     = oy + 158 + idx * 50
            col    = RARITY_COLORS.get(itm.rarity, WHITE)
            is_sel = (real_idx == self.selected_idx)

            can_equip, lock_msg = True, ""
            if hasattr(itm, "can_equip"):
                can_equip, lock_msg = itm.can_equip(player)

            fill     = (35, 35, 65) if is_sel else ((28, 8, 8) if not can_equip else (16, 16, 34))
            border_c = GRAY if not can_equip else col
            r = panel(surface, ox+14, iy, LEFT_W-28, 44, fill=fill, border=border_c)
            self.item_rects[real_idx] = r

            label = f"[{itm.rarity[0]}] {itm.name}" + (f"  {lock_msg}" if not can_equip else "")
            text(surface, label[:46], ox+22, iy+5, 15, GRAY if not can_equip else col, bold=is_sel)
            text(surface, itm.description[:54], ox+22, iy+24, 11, LIGHT_GRAY)

            # Equip button
            eq_col = GREEN if can_equip else (50, 50, 50)
            eb = button(surface, ox+LEFT_W-118, iy+8, 74, 26,
                        "EQUIP" if can_equip else "LOCK",
                        pygame.Rect(ox+LEFT_W-118, iy+8, 74, 26).collidepoint(mouse_pos) and can_equip,
                        eq_col, 13)
            self.equip_btns[real_idx] = (eb, can_equip)

            # Sell button
            sb = button(surface, ox+LEFT_W-38, iy+8, 26, 26, "$",
                        pygame.Rect(ox+LEFT_W-38, iy+8, 26, 26).collidepoint(mouse_pos),
                        ORANGE, 13)
            self.item_rects[f"sell_{real_idx}"] = sb

        if len(player.inventory) > VISIBLE:
            text(surface,
                 f"scroll ↑↓  ({self.scroll+1}–{min(self.scroll+VISIBLE, len(player.inventory))}"
                 f" / {len(player.inventory)})",
                 ox+14, oy+H-26, 12, GRAY)

        # ── Vertical divider ──────────────────────────────────
        pygame.draw.line(surface, (40, 40, 80), (ox+LEFT_W, oy+40), (ox+LEFT_W, oy+H-16))

        # ── RIGHT: Character info (no stats / no level) ────────
        rx = ox + LEFT_W + 16
        rw = W - LEFT_W - 26
        ry = oy + 40

        text(surface, "CHARACTER", rx, ry, 15, CYAN, bold=True)
        ry += 24

        # Class badge
        cls_col = {"Mage": PURPLE, "Necromancer": (60,180,120),
                   "Ranger": GREEN, "Rogue": (80,160,220)}.get(player.char_class, WHITE)
        panel(surface, rx, ry, rw, 28, fill=(18, 10, 28), border=cls_col)
        text(surface, player.char_class, rx+8, ry+6, 14, cls_col, bold=True)
        ry += 36

        pygame.draw.line(surface, (40, 40, 70), (rx, ry), (rx+rw, ry))
        ry += 10

        # ── Resource bars ──────────────────────────────────────
        text(surface, "RESOURCES", rx, ry, 13, WHITE, bold=True)
        ry += 18

        for label, val, maxv, col in [
            ("HP",    player.hp,    player.max_hp,    RED),
            ("Armor", player.armor, player.max_armor, CYAN),
            ("Mana",  player.mana,  player.max_mana,  BLUE),
        ]:
            text(surface, label, rx, ry, 13, col, bold=True)
            _bar(surface, rx+48, ry+1, rw-48, 13, val, maxv, col)
            text(surface, f"{int(val)}/{maxv}", rx+50, ry+16, 10, col)
            ry += 32

        pygame.draw.line(surface, (40, 40, 70), (rx, ry), (rx+rw, ry))
        ry += 10

        # ── Weapon info ────────────────────────────────────────
        text(surface, "WEAPON", rx, ry, 13, WHITE, bold=True)
        ry += 18
        wpn = player.weapon
        if wpn:
            wc = RARITY_COLORS.get(wpn.rarity, WHITE)
            text(surface, wpn.name[:22], rx, ry, 13, wc, bold=True)
            ry += 18
            text(surface, f"DMG  {wpn.damage}", rx, ry, 13, RED)
            ry += 18
            text(surface, f"Rate {wpn.fire_rate:.1f}/s", rx, ry, 13, LIGHT_GRAY)
            ry += 18
            text(surface, f"Spd  {wpn.bullet_speed}", rx, ry, 13, CYAN)
            ry += 18
        else:
            text(surface, "— no weapon —", rx, ry, 13, GRAY)
            ry += 18

        text(surface, f"CRIT  {int(player.crit_chance*100)}%  ×{player.crit_mult:.1f}", rx, ry, 13, GOLD)
        ry += 18
        text(surface, f"DEF   {player.defense}", rx, ry, 13, LIGHT_GRAY)
        ry += 18
        text(surface, f"SPD   {player.move_speed:.1f}", rx, ry, 13, GREEN)
        ry += 18

        pygame.draw.line(surface, (40, 40, 70), (rx, ry+4), (rx+rw, ry+4))
        ry += 14

        # ── Passive ────────────────────────────────────────────
        text(surface, "PASSIVE", rx, ry, 12, YELLOW, bold=True)
        ry += 15
        ptext = getattr(player, "passive", "")
        line  = ""
        for w in ptext.split():
            if len(line) + len(w) + 1 <= 27:
                line += ("" if line == "" else " ") + w
            else:
                text(surface, line, rx, ry, 11, LIGHT_GRAY)
                ry += 14
                line = w
        if line:
            text(surface, line, rx, ry, 11, LIGHT_GRAY)

        # Close hint
        text(surface, "TAB / ESC to close", ox + W//2, oy + H - 18, 13, GRAY, center=True)

    def handle_click(self, pos, player):
        for idx, (btn, can_equip) in self.equip_btns.items():
            if btn.collidepoint(pos):
                if not can_equip:
                    return "locked"
                itm = player.inventory[idx]
                old = player.equip(itm)
                player.inventory.pop(idx)
                if old:
                    player.inventory.append(old)
                return "equip"

        for key, r in self.item_rects.items():
            if isinstance(key, str) and key.startswith("sell_"):
                if r.collidepoint(pos):
                    idx = int(key.split("_")[1])
                    if idx < len(player.inventory):
                        itm = player.inventory.pop(idx)
                        player.gold += itm.sell_price
                    return "sell"

        for idx, r in self.item_rects.items():
            if isinstance(idx, int) and r.collidepoint(pos):
                self.selected_idx = idx

        return None

    def handle_scroll(self, direction, player):
        max_scroll = max(0, len(player.inventory) - 7)
        self.scroll = max(0, min(self.scroll + direction, max_scroll))


# ─────────────────────────────────────────────────────────────
class ShopScreen:
    """Opens automatically after each stage is cleared."""

    def __init__(self, stage_id, char_class="Warrior"):
        self.stage_id    = stage_id
        self.char_class  = char_class
        self.reroll_cost = SHOP_REROLL_COST
        self._gen_items(stage_id, char_class)

    def _gen_items(self, stage_id, char_class):
        rarities = ["Common", "Common", "Rare", "Rare", "Epic"]
        if stage_id >= 3:
            rarities = ["Rare", "Rare", "Epic", "Epic", "Legendary"]
        # Soul Knight style: any weapon for any class
        self.shop_items = [
            make_weapon(random.choice(rarities)),
            make_weapon(random.choice(rarities)),
            make_weapon(random.choice(rarities)),
            make_armor(random.choice(rarities)),
            make_accessory(random.choice(rarities)),
        ]
        self.prices = [SHOP_ITEM_MULT.get(i.rarity, 30) for i in self.shop_items]

    def draw(self, surface, player, mouse_pos):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        surface.blit(overlay, (0, 0))

        W, H = 900, 570
        ox   = SCREEN_W//2 - W//2
        oy   = SCREEN_H//2 - H//2
        panel(surface, ox, oy, W, H, fill=(8, 18, 8), border=GREEN)

        text(surface, "SHOP", ox+W//2, oy+10, 28, GOLD, bold=True, center=True)
        text(surface, "Stage cleared!  Spend your gold before continuing.",
             ox+W//2, oy+44, 14, LIGHT_GRAY, center=True)

        # Gold
        text(surface, f"Gold: {player.gold} G", ox+16, oy+68, 18, GOLD, bold=True)

        # HP bar preview
        _bar(surface, ox+180, oy+71, 200, 12, player.hp, player.max_hp, RED)
        text(surface, f"HP {int(player.hp)}/{player.max_hp}", ox+180, oy+85, 10, RED)

        # Reroll button
        can_reroll = player.gold >= self.reroll_cost
        self.btn_reroll = button(surface, ox+W-192, oy+60, 176, 34,
                                 f"REROLL  ({self.reroll_cost}G)",
                                 pygame.Rect(ox+W-192, oy+60, 176, 34).collidepoint(mouse_pos),
                                 GOLD if can_reroll else GRAY, 14)

        # Heal button
        can_heal = player.gold >= SHOP_HEAL_COST
        self.heal_btn = button(surface, ox+16, oy+104, 224, 34,
                               f"HEAL 50 HP  ({SHOP_HEAL_COST}G)",
                               pygame.Rect(ox+16, oy+104, 224, 34).collidepoint(mouse_pos),
                               RED if can_heal else GRAY, 14)

        text(surface, "Pick up any weapon — no class restrictions!",
             ox+265, oy+112, 13, (140, 200, 140))

        pygame.draw.line(surface, (30, 60, 30), (ox+14, oy+146), (ox+W-14, oy+146))

        # Item rows
        self.buy_btns = {}
        for i, itm in enumerate(self.shop_items):
            iy = oy + 154 + i * 74
            if itm is None:
                panel(surface, ox+14, iy, W-28, 62, fill=(10, 10, 10), border=GRAY)
                text(surface, "— SOLD OUT —", ox+24, iy+22, 16, GRAY)
                continue

            col = RARITY_COLORS.get(itm.rarity, WHITE)

            can_use, lock_note = True, ""
            if hasattr(itm, "can_equip"):
                can_use, lock_note = itm.can_equip(player)
                if lock_note:
                    lock_note = "  " + lock_note

            panel(surface, ox+14, iy, W-28, 62,
                  fill=(14, 26, 14) if can_use else (26, 10, 10), border=col)

            name_col = col if can_use else GRAY
            text(surface, f"[{itm.rarity}] {itm.name}{lock_note}",
                 ox+22, iy+4, 17, name_col, bold=True)
            text(surface, itm.description[:74], ox+22, iy+24, 12, LIGHT_GRAY)

            # Stats row
            parts = []
            if hasattr(itm, "damage"):      parts.append(f"DMG {itm.damage}")
            if hasattr(itm, "defense"):     parts.append(f"DEF {itm.defense}")
            if hasattr(itm, "fire_rate") and itm.fire_rate > 0:
                parts.append(f"Rate {itm.fire_rate:.1f}/s")
            sb = getattr(itm, "stat_bonus", {})
            if sb:
                sb_str = "  ".join(f"+{v}{k}" for k, v in sb.items() if v > 0)
                if sb_str:
                    parts.append(sb_str)
            if parts:
                text(surface, "  ·  ".join(parts[:4]), ox+22, iy+44, 11, ORANGE)

            price   = self.prices[i]
            can_buy = player.gold >= price and can_use
            bb = button(surface, ox+W-158, iy+14, 138, 34,
                        f"BUY  {price}G",
                        pygame.Rect(ox+W-158, iy+14, 138, 34).collidepoint(mouse_pos),
                        GREEN if can_buy else GRAY, 14)
            self.buy_btns[i] = (bb, can_use)

        self.btn_leave = button(surface, ox+W//2-96, oy+H-46, 192, 38,
                                "CONTINUE  →",
                                pygame.Rect(ox+W//2-96, oy+H-46, 192, 38).collidepoint(mouse_pos),
                                BLUE)

    def handle_click(self, pos, player):
        if self.heal_btn.collidepoint(pos):
            if player.gold >= SHOP_HEAL_COST:
                player.gold -= SHOP_HEAL_COST
                player.heal(50)
                return "heal"

        if self.btn_reroll.collidepoint(pos):
            if player.gold >= self.reroll_cost:
                player.gold      -= self.reroll_cost
                self.reroll_cost  = int(self.reroll_cost * 1.5)
                self._gen_items(self.stage_id, player.char_class)
                return "reroll"

        for i, (btn, can_use) in self.buy_btns.items():
            if btn.collidepoint(pos):
                price = self.prices[i]
                itm   = self.shop_items[i]
                if itm and can_use and player.gold >= price:
                    player.gold -= price
                    player.collect_item(itm)
                    self.shop_items[i] = None
                    return "buy"

        if self.btn_leave.collidepoint(pos):
            return "leave"
        return None


# ─────────────────────────────────────────────────────────────
class PauseScreen:
    def draw(self, surface, mouse_pos):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))
        text(surface, "PAUSED", SCREEN_W//2, 200, 52, GOLD, bold=True, center=True)
        bw, bh, bx = 220, 48, SCREEN_W//2 - 110
        self.btn_resume = button(surface, bx, 290, bw, bh, "RESUME",
                                 pygame.Rect(bx, 290, bw, bh).collidepoint(mouse_pos), GREEN)
        self.btn_menu   = button(surface, bx, 356, bw, bh, "MAIN MENU",
                                 pygame.Rect(bx, 356, bw, bh).collidepoint(mouse_pos), BLUE)

    def handle_click(self, pos):
        if hasattr(self, "btn_resume") and self.btn_resume.collidepoint(pos): return "resume"
        if hasattr(self, "btn_menu")   and self.btn_menu.collidepoint(pos):   return "menu"
        return None


# ─────────────────────────────────────────────────────────────
class GameOverScreen:
    def draw(self, surface, player, tracker, win=False):
        surface.fill((5, 0, 0) if not win else (0, 5, 12))
        title = "VICTORY!" if win else "GAME OVER"
        col   = GOLD if win else RED
        text(surface, title, SCREEN_W//2, 70, 64, col, bold=True, center=True)

        summary = tracker.current_run
        cy      = 170
        pairs   = [
            ("Score",    f"{summary.get('score', 0):,}"),
            ("Class",    player.char_class),
            ("Level",    player.level),
            ("Enemies",  summary.get("enemies_defeated", 0)),
            ("Damage",   f"{summary.get('total_damage', 0):,}"),
            ("Items",    summary.get("items_collected", 0)),
            ("Gold",     player.gold),
            ("Duration", f"{summary.get('duration_sec', 0)}s"),
            ("Stage",    summary.get("stage_reached", 1)),
        ]
        panel(surface, SCREEN_W//2-210, cy-12, 420, len(pairs)*32+24, fill=(14, 14, 30))
        for label, val in pairs:
            text(surface, f"{label}:", SCREEN_W//2-190, cy, 18, LIGHT_GRAY)
            text(surface, str(val),    SCREEN_W//2+70,  cy, 18, WHITE, bold=True)
            cy += 30

        self.btn_menu = button(surface, SCREEN_W//2-100, cy+20, 200, 44, "MAIN MENU", False, BLUE)
