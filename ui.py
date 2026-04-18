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
        self.btn_play  = button(surface, bx, 200, bw, bh, "NEW GAME",
                                pygame.Rect(bx, 200, bw, bh).collidepoint(mouse_pos), GREEN)
        self.btn_range = button(surface, bx, 262, bw, bh, "SHOOTING RANGE",
                                pygame.Rect(bx, 262, bw, bh).collidepoint(mouse_pos), (160, 80, 200))
        self.btn_stats = button(surface, bx, 324, bw, bh, "STATISTICS",
                                pygame.Rect(bx, 324, bw, bh).collidepoint(mouse_pos), BLUE)
        self.btn_quit  = button(surface, bx, 386, bw, bh, "QUIT",
                                pygame.Rect(bx, 386, bw, bh).collidepoint(mouse_pos), RED)

        summary = self.tracker.get_summary()
        panel(surface, SCREEN_W//2 - 200, 455, 400, 120, fill=(15, 15, 30))
        if summary.get("total_runs", 0) > 0:
            text(surface, f"Total Runs: {summary['total_runs']}    Victories: {summary['victories']}",
                 SCREEN_W//2, 468, 17, LIGHT_GRAY, center=True)
            text(surface, f"Best Score: {summary['best_score']:,}",
                 SCREEN_W//2, 491, 17, GOLD, center=True)
            text(surface, f"Avg Kills:  {summary['avg_kills']}    Max Level: {summary['max_level']}",
                 SCREEN_W//2, 514, 17, LIGHT_GRAY, center=True)
            text(surface, f"Avg Run Time: {summary['avg_duration']}s",
                 SCREEN_W//2, 537, 17, LIGHT_GRAY, center=True)
        else:
            text(surface, "No runs yet. Play to collect statistics!",
                 SCREEN_W//2, 503, 17, GRAY, center=True)

        # Updated: I → TAB
        text(surface,
             "WASD: Move   LClick: Attack   E: Pick Up   TAB: Inventory   ESC: Pause",
             SCREEN_W//2, SCREEN_H-30, 14, GRAY, center=True)

    def handle_click(self, pos):
        if self.btn_play.collidepoint(pos):   return "play"
        if self.btn_range.collidepoint(pos):  return "range"
        if self.btn_stats.collidepoint(pos):  return "stats"
        if self.btn_quit.collidepoint(pos):   return "quit"
        return None


# ─────────────────────────────────────────────────────────────
class ClassSelectScreen:
    """
    Single character select: Sausage Man.
    Shows animated sprite, stats, and skill info.
    """

    def __init__(self):
        self.selected   = "Sausage Man"
        self._anim_t    = 0.0

    def _draw_sausage_sprite(self, surface, cx, cy, t, scale=1.0):
        """Draw an animated Sausage Man sprite."""
        bcol = (240, 60, 120)
        acol = (160, 20, 60)
        dcol = (255, 180, 200)

        bob = int(math.sin(t * 4) * 2 * scale)
        r   = int(14 * scale)

        # Shadow
        pygame.draw.ellipse(surface, (10, 10, 20),
                            (cx - r, cy + r * 2 + bob + 2, r * 2, int(r * 0.5)))

        # Legs
        leg_swing = int(math.sin(t * 6) * 4 * scale)
        leg_r     = int(5 * scale)
        pygame.draw.circle(surface, acol, (cx - int(4*scale), cy + r + bob + int(4*scale) + leg_swing), leg_r)
        pygame.draw.circle(surface, acol, (cx + int(4*scale), cy + r + bob + int(4*scale) - leg_swing), leg_r)

        # Body
        pygame.draw.circle(surface, bcol, (cx, cy + bob), r)
        pygame.draw.circle(surface, acol, (cx, cy + bob), r, int(2*scale))

        # Sausage segment lines
        for off in (-int(4*scale), 0, int(4*scale)):
            pygame.draw.line(surface, acol,
                             (cx - r + 2, cy + bob + off),
                             (cx + r - 2, cy + bob + off), max(1, int(scale)))

        # Eyes
        eye_off = int(4 * scale)
        eye_r   = max(2, int(3 * scale))
        pygame.draw.circle(surface, (240, 240, 255), (cx - eye_off, cy + bob - int(3*scale)), eye_r)
        pygame.draw.circle(surface, (240, 240, 255), (cx + eye_off, cy + bob - int(3*scale)), eye_r)
        pygame.draw.circle(surface, (20, 20, 40),    (cx - eye_off, cy + bob - int(3*scale)), max(1, eye_r-1))
        pygame.draw.circle(surface, (20, 20, 40),    (cx + eye_off, cy + bob - int(3*scale)), max(1, eye_r-1))

        # Gun
        shoot_angle = math.sin(t * 2) * 0.15
        wx = cx + int(r * math.cos(shoot_angle))
        wy = cy + bob + int(r * 0.3 * math.sin(shoot_angle))
        gun_pts = [(wx, wy - int(2*scale)), (wx + int(16*scale), wy - int(2*scale)),
                   (wx + int(16*scale), wy + int(2*scale)), (wx, wy + int(2*scale))]
        pygame.draw.polygon(surface, dcol, gun_pts)

    def draw(self, surface, mouse_pos, dt=0.016):
        self._anim_t += dt

        surface.fill((6, 8, 18))

        text(surface, "SELECT CHARACTER", SCREEN_W//2, 18, 38, GOLD, bold=True, center=True)
        pygame.draw.line(surface, (40, 60, 120), (60, 65), (SCREEN_W-60, 65), 2)

        from constants import CLASSES, CLASS_SKILLS
        cfg   = CLASSES["Sausage Man"]
        skill = CLASS_SKILLS.get("Sausage Man", {})

        # Single centered card
        card_w, card_h = 200, 260
        cx = SCREEN_W//2 - card_w//2
        cy = 80
        glow_a = int(60 + 30 * math.sin(self._anim_t * 3))
        glow_surf = pygame.Surface((card_w+8, card_h+8), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*cfg["color"], glow_a), (0, 0, card_w+8, card_h+8), 4, border_radius=12)
        surface.blit(glow_surf, (cx-4, cy-4))
        pygame.draw.rect(surface, (35, 45, 75),  (cx, cy, card_w, card_h), border_radius=10)
        pygame.draw.rect(surface, cfg["color"],   (cx, cy, card_w, card_h), 3, border_radius=10)

        # Animated sprite in card
        self._draw_sausage_sprite(surface, cx + card_w//2, cy + 100, self._anim_t * 2.0, scale=2.0)

        text(surface, "Sausage Man", cx + card_w//2, cy + card_h - 72,
             18, cfg["color"], bold=True, center=True)
        text(surface, "Any Weapon", cx + card_w//2, cy + card_h - 46, 13, GRAY, center=True)
        spd_int = min(5, max(1, int(cfg["speed"])))
        pips = "".join("●" if i < spd_int else "○" for i in range(5))
        text(surface, f"SPD {pips}", cx + card_w//2, cy + card_h - 24, 12, (100, 200, 100), center=True)

        self.char_rects = {"Sausage Man": pygame.Rect(cx, cy, card_w, card_h)}

        # Detail panel
        detail_y = cy + card_h + 18
        detail_h = SCREEN_H - detail_y - 60

        prev_w = 200
        prev_x = SCREEN_W//2 - 440
        stat_x = prev_x + prev_w + 20
        stat_w = SCREEN_W//2 + 440 - stat_x

        panel(surface, prev_x, detail_y, prev_w, detail_h, fill=(12, 14, 28), border=cfg["color"])
        self._draw_sausage_sprite(surface, prev_x + prev_w//2, detail_y + detail_h//2 - 10,
                                  self._anim_t * 2.0, scale=2.8)
        text(surface, "Sausage Man", prev_x + prev_w//2, detail_y + detail_h - 36,
             18, cfg["color"], bold=True, center=True)

        panel(surface, stat_x, detail_y, stat_w, detail_h, fill=(10, 12, 24), border=(40, 50, 100))
        sy = detail_y + 10

        text(surface, cfg["description"], stat_x + 10, sy, 13, LIGHT_GRAY)
        sy += 22
        pygame.draw.line(surface, (30, 40, 80), (stat_x + 8, sy), (stat_x + stat_w - 8, sy))
        sy += 8

        text(surface, "RESOURCES", stat_x + 10, sy, 13, CYAN, bold=True)
        sy += 18
        for lbl, val, maxv, col in [
            ("HP",    cfg["base_hp"],          200, RED),
            ("Armor", cfg.get("max_armor", 80),140, CYAN),
            ("Mana",  cfg.get("max_mana", 130),200, BLUE),
            ("Speed", int(cfg["speed"] * 20),  100, GREEN),
        ]:
            text(surface, lbl, stat_x + 10, sy, 12, col, bold=True)
            bw2 = stat_w - 80
            pygame.draw.rect(surface, (20, 20, 35), (stat_x + 54, sy + 2, bw2, 11), border_radius=4)
            fw = int(bw2 * min(1.0, val / maxv))
            if fw > 0:
                pygame.draw.rect(surface, col, (stat_x + 54, sy + 2, fw, 11), border_radius=4)
            text(surface, str(val), stat_x + 58 + bw2, sy, 11, WHITE)
            sy += 18

        pygame.draw.line(surface, (30, 40, 80), (stat_x + 8, sy + 2), (stat_x + stat_w - 8, sy + 2))
        sy += 10

        text(surface, "STARTER WEAPON", stat_x + 10, sy, 13, CYAN, bold=True)
        sy += 18
        text(surface, "Sausage Gun", stat_x + 10, sy, 13, GOLD, bold=True)
        sy += 16
        text(surface, "DMG 14  Rate 0.80/s  Rapid fire", stat_x + 10, sy, 11, LIGHT_GRAY)
        sy += 20

        pygame.draw.line(surface, (30, 40, 80), (stat_x + 8, sy + 2), (stat_x + stat_w - 8, sy + 2))
        sy += 10

        text(surface, "PASSIVE", stat_x + 10, sy, 13, YELLOW, bold=True)
        sy += 16
        ptext = cfg.get("passive", "")
        for chunk in [ptext[i:i+48] for i in range(0, len(ptext), 48)]:
            text(surface, chunk, stat_x + 10, sy, 11, LIGHT_GRAY)
            sy += 14

        pygame.draw.line(surface, (30, 40, 80), (stat_x + 8, sy + 2), (stat_x + stat_w - 8, sy + 2))
        sy += 10

        text(surface, "SKILL  [Q]", stat_x + 10, sy, 13, (80, 200, 255), bold=True)
        sy += 16
        if skill:
            text(surface, skill.get("name", ""), stat_x + 10, sy, 14, (120, 220, 255), bold=True)
            text(surface, f"CD:{int(skill.get('cooldown',4))}s  MP:{skill.get('mana_cost',20)}",
                 stat_x + 10, sy + 16, 11, ORANGE)
            sy += 30
            sk_desc = skill.get("description", "")
            for chunk in [sk_desc[i:i+48] for i in range(0, len(sk_desc), 48)]:
                text(surface, chunk, stat_x + 10, sy, 11, LIGHT_GRAY)
                sy += 14

        # Bottom buttons
        self.btn_back = button(surface, 30, SCREEN_H - 54, 120, 40, "BACK", False, GRAY)
        play_hover = pygame.Rect(SCREEN_W - 230, SCREEN_H - 54, 200, 40).collidepoint(mouse_pos)
        self.btn_play = button(surface, SCREEN_W - 230, SCREEN_H - 54, 200, 40,
                               "PLAY  Sausage Man", play_hover, GREEN)

        text(surface,
             "Q: Skill   WASD: Move   Click: Attack   E: Pick Up   TAB: Inventory",
             SCREEN_W//2, SCREEN_H - 16, 12, GRAY, center=True)

    def handle_click(self, pos):
        for cname, rect in self.char_rects.items():
            if rect.collidepoint(pos):
                self.selected = cname
                return None

        if hasattr(self, "btn_play") and self.btn_play and self.btn_play.collidepoint(pos):
            return "Sausage Man"

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

        # Character badge
        cls_col = (240, 60, 120)
        panel(surface, rx, ry, rw, 28, fill=(40, 10, 20), border=cls_col)
        text(surface, "Sausage Man", rx+8, ry+6, 14, cls_col, bold=True)
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
            text(surface, f"Rate {int(wpn.fire_rate)}/s", rx, ry, 13, LIGHT_GRAY)
            ry += 18
            text(surface, f"Spd  {wpn.bullet_speed}", rx, ry, 13, CYAN)
            ry += 18
        else:
            text(surface, "— no weapon —", rx, ry, 13, GRAY)
            ry += 18

        text(surface, f"CRIT  {int(player.crit_chance*100)}%  x{int(player.crit_mult)}", rx, ry, 13, GOLD)
        ry += 18
        text(surface, f"DEF   {player.defense}", rx, ry, 13, LIGHT_GRAY)
        ry += 18
        text(surface, f"SPD   {int(player.move_speed)}", rx, ry, 13, GREEN)
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

    def __init__(self, stage_id, char_class="Sausage Man"):
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
                parts.append(f"Rate {int(itm.fire_rate)}/s")
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
        import math, time

        # ── Dimmed overlay ────────────────────────────────────
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # ── Card panel ────────────────────────────────────────
        card_w, card_h = 360, 380
        card_x = SCREEN_W // 2 - card_w // 2
        card_y = SCREEN_H // 2 - card_h // 2
        panel(surface, card_x, card_y, card_w, card_h,
              fill=(12, 12, 28), border=(80, 80, 160))

        # ── Pulsing title ─────────────────────────────────────
        pulse = int(math.sin(time.time() * 3) * 6)
        text(surface, "||  PAUSED", SCREEN_W // 2,
             card_y + 30 + pulse, 38, GOLD, bold=True, center=True)

        # Divider
        pygame.draw.line(surface, (60, 60, 120),
                         (card_x + 24, card_y + 88),
                         (card_x + card_w - 24, card_y + 88), 2)

        # ── Hint text ─────────────────────────────────────────
        text(surface, "Press  ESC  to resume", SCREEN_W // 2,
             card_y + 100, 14, (140, 140, 180), center=True)

        # ── Buttons ───────────────────────────────────────────
        bw, bh = 280, 52
        bx = SCREEN_W // 2 - bw // 2
        gap = 68

        by1 = card_y + 140
        by2 = by1 + gap
        by3 = by2 + gap

        h1 = pygame.Rect(bx, by1, bw, bh).collidepoint(mouse_pos)
        h2 = pygame.Rect(bx, by2, bw, bh).collidepoint(mouse_pos)
        h3 = pygame.Rect(bx, by3, bw, bh).collidepoint(mouse_pos)

        self.btn_resume  = button(surface, bx, by1, bw, bh, "RESUME",
                                  h1, (30, 160, 60))
        self.btn_restart = button(surface, bx, by2, bw, bh, "RESTART",
                                  h2, (180, 100, 20))
        self.btn_menu    = button(surface, bx, by3, bw, bh, "EXIT TO MENU",
                                  h3, (160, 30, 30))

        # ── F11 hint ──────────────────────────────────────────
        text(surface, "F11 - Toggle Fullscreen", SCREEN_W // 2,
             card_y + card_h - 28, 13, (100, 100, 140), center=True)

    def handle_click(self, pos):
        if hasattr(self, "btn_resume")  and self.btn_resume.collidepoint(pos):  return "resume"
        if hasattr(self, "btn_restart") and self.btn_restart.collidepoint(pos): return "restart"
        if hasattr(self, "btn_menu")    and self.btn_menu.collidepoint(pos):    return "menu"
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
            ("Hero",     "Sausage Man"),
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


# ─────────────────────────────────────────────────────────────
class ShootingRangeScreen:
    """Shooting range — uses real Player + real Weapon objects from the game."""

    RARITY_COLOR = {
        "Common":    (180, 184, 200),
        "Rare":      (100, 180, 255),
        "Epic":      (160, 80,  240),
        "Legendary": (255, 200, 0),
    }
    PANEL_W = 230
    PLAY_W  = SCREEN_W - 230
    PLAY_H  = SCREEN_H - HUD_H

    def __init__(self):
        from item import Weapon
        from constants import WEAPON_POOL
        self._weapon_list = []
        for entry in WEAPON_POOL:
            effect = entry[9] if len(entry) > 9 else None
            w = Weapon(entry[0], entry[1], entry[2], entry[3],
                       entry[4], entry[5], entry[6], "Any", entry[8], effect)
            self._weapon_list.append(w)
        self.player = None
        self._reset()

    def set_player(self, player):
        self.player = player
        if self._weapon_list:
            self.player.equipment["weapon"] = self._weapon_list[self.wpn_idx]
            self.player.shoot_cooldown = 0.0

    def _reset(self):
        import random as _r
        self._rnd     = _r.Random()
        self.wpn_idx  = 0
        self.bullets  = []
        self.floats   = []
        self.burst_left  = 0
        self.burst_timer = 0.0
        self._burst_ang = 0.0
        self._burst_col = (255,230,80)
        self._burst_sz  = 6
        self._burst_spd = 7
        self.total_dmg = self.total_hits = self.total_crits = 0
        self.holding   = False
        self.mouse     = (400, self.PLAY_H // 2)
        self.last_msg  = ""
        self._btn_back = None
        self._wpn_btns = []
        self._scroll   = 0.0
        self._scroll_max = 0
        # DPS tracking
        self._dps_log     = []    # list of [elapsed_time, damage]
        self._elapsed     = 0.0   # total time since reset
        self._dps_window  = 3.0   # rolling window in seconds
        self._current_dps = 0.0
        self._peak_dps    = 0.0
        self.px = 160
        self.py = self.PLAY_H // 2
        self.targets = [
            {"x": self.PLAY_W - 420 + col*90, "y": 160 + row*180,
             "hp": 300, "max_hp": 300, "hit_flash": 0.0, "r": 32}
            for row in range(2) for col in range(4)
        ]

    def _current_weapon(self):
        if self._weapon_list:
            return self._weapon_list[self.wpn_idx]
        return None

    def _spawn(self, angle, col, size, spd, pierce, is_crit=False, dmg=1):
        from bullet import Bullet
        dx = math.cos(angle); dy = math.sin(angle)
        barrel = 32
        bx = self.px + dx * barrel
        by = self.py + dy * barrel
        b = Bullet(bx, by, dx, dy, spd, dmg,
                   pierce=pierce, is_crit=is_crit, color=col, size=size)
        self.bullets.append(b)

    def _shoot(self):
        p = self.player
        if p is None:
            return
        wpn = self._current_weapon()
        if wpn is None or wpn.is_melee:
            return
        if not p.can_use_mana(wpn.mana_cost):
            return
        p.use_mana(wpn.mana_cost)
        dmg, crit = p.calc_damage()
        p.shoot_cooldown = 1.0 / max(0.1, p.get_fire_rate())

        ang = math.atan2(self.mouse[1] - self.py, self.mouse[0] - self.px)
        fx  = wpn.effect or {}
        col = fx.get("bullet_color", (255, 230, 80))
        sz  = fx.get("bullet_size", 6)
        spd = p.get_bullet_speed() or 7
        pierce = fx.get("pierce", False)
        pat = fx.get("pattern", "single")
        sp = lambda a: a + (self._rnd.random() - 0.5) * 0.22

        if pat in ("single", "pierce"):
            self._spawn(ang, col, sz, spd, pierce or pat=="pierce", crit, dmg)
        elif pat == "double":
            self._spawn(ang+0.09, col, sz, spd, False, crit, dmg)
            self._spawn(ang-0.09, col, sz, spd, False, crit, dmg)
        elif pat == "spread3":
            for i in (-1, 0, 1):
                self._spawn(ang+i*0.20, col, sz, spd, False, crit, dmg)
        elif pat == "spread5":
            for i in range(-2, 3):
                self._spawn(sp(ang+i*0.15), col, sz, spd, False, crit, dmg)
        elif pat == "spread_random":
            self._spawn(sp(ang), col, sz, spd, False, crit, dmg)
        elif pat == "burst3":
            self.burst_left = 3
            self.burst_timer = 0.0
            self._burst_ang = ang
            self._burst_col = col
            self._burst_sz  = sz
            self._burst_spd = spd
            self._spawn(ang, col, sz, spd, False, crit, dmg)
            self.burst_left -= 1
        if crit:
            self.total_crits += 1

    def _select_weapon(self, idx):
        self.wpn_idx = idx % len(self._weapon_list)
        if self.player and self._weapon_list:
            self.player.equipment["weapon"] = self._weapon_list[self.wpn_idx]
            self.player.shoot_cooldown = 0.0
        self.burst_left = 0

    def update(self, dt, events, mouse_pos, mouse_buttons):
        p = self.player
        self.mouse = mouse_pos
        mx, my = mouse_pos
        self.holding = bool(mouse_buttons[0] and mx < self.PLAY_W)
        if p is None:
            return
        self._elapsed += dt
        p.mana = min(p.max_mana, p.mana + 18 * dt)
        if p.shoot_cooldown > 0:
            p.shoot_cooldown -= dt
        if self.burst_left > 0:
            self.burst_timer -= dt
            if self.burst_timer <= 0:
                self._spawn(self._burst_ang, self._burst_col,
                            self._burst_sz, self._burst_spd, False)
                self.burst_left -= 1
                self.burst_timer = 0.07
        if self.holding and p.shoot_cooldown <= 0 and self.burst_left == 0:
            self._shoot()
        for b in self.bullets:
            b.update(dt, [])
            for t in self.targets:
                if id(t) in b.hit_set:
                    continue
                if math.hypot(b.x-t["x"], b.y-t["y"]) < t["r"]+b.radius:
                    if not b.pierce:
                        b.alive = False
                    b.hit_set.add(id(t))
                    t["hit_flash"] = 0.15
                    dmg = b.damage; crit = b.is_crit
                    t["hp"] = max(0, t["hp"] - dmg)
                    if t["hp"] <= 0:
                        t["hp"] = t["max_hp"]
                    self.total_dmg += dmg; self.total_hits += 1
                    # Log hit for DPS calculation
                    self._dps_log.append([self._elapsed, dmg])
                    label = ("CRIT! " if crit else "") + str(dmg)
                    self.floats.append({"x": t["x"]+self._rnd.randint(-20,20),
                        "y": t["y"]-40, "text": label, "life": 1.0, "crit": crit})
                    wpn_name = self._current_weapon().name if self._current_weapon() else "?"
                    self.last_msg = ("CRITICAL! " if crit else "") + f"Hit {dmg} with {wpn_name}"
            if b.alive and not (0 < b.x < self.PLAY_W and 0 < b.y < self.PLAY_H):
                b.alive = False
        self.bullets = [b for b in self.bullets if b.alive]
        for t in self.targets:
            if t["hit_flash"] > 0:
                t["hit_flash"] -= dt
        self.floats = [f for f in self.floats if f["life"] > 0]
        for f in self.floats:
            f["y"] -= 50*dt; f["life"] -= dt*1.2
        # Recalculate rolling DPS (last _dps_window seconds)
        cutoff = self._elapsed - self._dps_window
        self._dps_log = [e for e in self._dps_log if e[0] >= cutoff]
        window_actual = min(self._elapsed, self._dps_window)
        if window_actual > 0:
            self._current_dps = sum(e[1] for e in self._dps_log) / window_actual
        else:
            self._current_dps = 0.0
        if self._current_dps > self._peak_dps:
            self._peak_dps = self._current_dps
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_q:
                    self._select_weapon(self.wpn_idx - 1)
                elif ev.key == pygame.K_e:
                    self._select_weapon(self.wpn_idx + 1)

    def handle_click(self, pos):
        if self._btn_back and self._btn_back.collidepoint(pos):
            return "menu"
        for rect, idx in self._wpn_btns:
            if rect.collidepoint(pos):
                self._select_weapon(idx)
        return None

    def handle_scroll(self, y_offset):
        self._scroll = max(0, min(self._scroll_max, self._scroll - y_offset*22))

    def draw(self, surface, mouse_pos):
        p = self.player
        pw = self.PLAY_W
        surface.fill((10,10,24))
        for gx in range(0, pw, 60):
            pygame.draw.line(surface,(18,18,38),(gx,0),(gx,self.PLAY_H))
        for gy in range(0, self.PLAY_H, 60):
            pygame.draw.line(surface,(18,18,38),(0,gy),(pw,gy))
        pygame.draw.line(surface,(40,40,80),(pw,0),(pw,self.PLAY_H),2)
        for t in self.targets:
            fl = t["hit_flash"] > 0
            tx, ty, r = int(t["x"]), int(t["y"]), t["r"]
            body_col  = (255,80,80)   if fl else (200,50,50)
            shade_col = (255,140,140) if fl else (240,100,100)
            pygame.draw.ellipse(surface,(10,10,20),(tx-r,ty+r-4,r*2,int(r*0.5)))
            pygame.draw.circle(surface, body_col,  (tx,ty), r)
            pygame.draw.circle(surface, shade_col, (tx,ty), r, 2)
            for off in (-int(r*0.28), 0, int(r*0.28)):
                pygame.draw.line(surface,(160,30,30),(tx-r+3,ty+off),(tx+r-3,ty+off),1)
            eo=int(r*0.28); er=max(2,int(r*0.18))
            pygame.draw.circle(surface,(240,240,255),(tx-eo,ty-eo),er)
            pygame.draw.circle(surface,(240,240,255),(tx+eo,ty-eo),er)
            pygame.draw.circle(surface,(20,20,40),(tx-eo,ty-eo),max(1,er-1))
            pygame.draw.circle(surface,(20,20,40),(tx+eo,ty-eo),max(1,er-1))
            if fl:
                ov=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
                pygame.draw.circle(ov,(255,255,255,120),(r,r),r)
                surface.blit(ov,(tx-r,ty-r))
            bw2=r*2; bx2=tx-r; by2=ty+r+5
            pygame.draw.rect(surface,(30,30,30),(bx2,by2,bw2,7),border_radius=3)
            hp_w=int(bw2*t["hp"]/max(1,t["max_hp"]))
            hpc=(60,220,60) if t["hp"]>t["max_hp"]*0.5 else ((220,200,40) if t["hp"]>t["max_hp"]*0.25 else (220,60,60))
            if hp_w>0: pygame.draw.rect(surface,hpc,(bx2+1,by2+1,hp_w-2,5),border_radius=2)
        for b in self.bullets:
            b.draw(surface)
        for f in self.floats:
            alpha=int(255*max(0.0,f["life"]))
            col=(255,220,0) if f["crit"] else (255,255,255)
            sz=22 if f["crit"] else 15
            fsurf=F(sz,bold=f["crit"]).render(f["text"],True,col)
            ts=pygame.Surface(fsurf.get_size(),pygame.SRCALPHA)
            ts.blit(fsurf,(0,0)); ts.set_alpha(alpha)
            surface.blit(ts,(int(f["x"])-fsurf.get_width()//2,int(f["y"])))
        ang=math.atan2(self.mouse[1]-self.py,self.mouse[0]-self.px)
        sx,sy=self.px,self.py
        facing_right=(self.mouse[0]>=self.px)
        from player import _load_sprite
        import player as _pmod
        _load_sprite()
        _sprite=_pmod._SPRITE; _sprite_flip=_pmod._SPRITE_FLIP
        if _sprite is not None:
            sprite=_sprite if facing_right else _sprite_flip
            w2,h2=sprite.get_size()
            surface.blit(sprite,(sx-w2//2,sy-h2//2))
        else:
            pygame.draw.circle(surface,(224,56,120),(sx,sy),22)
        wpn=self._current_weapon()
        R=28
        if wpn and p:
            # Sync player facing so _draw_gun() uses the correct angle/direction
            p.facing_angle = ang
            p.facing_right = facing_right
            # _draw_gun has both PNG-sprite path AND polygon fallback for every gun shape
            p._draw_gun(surface, sx, sy, R)
        pygame.draw.rect(surface,(12,12,28),(0,0,pw,52))
        if wpn:
            wc=self.RARITY_COLOR.get(wpn.rarity,WHITE)
            text(surface,wpn.name,12,8,16,wc,bold=True)
            pat=(wpn.effect or {}).get("pattern","single")
            text(surface,f"DMG {wpn.damage}   RATE {wpn.fire_rate:.2f}/s   MANA {wpn.mana_cost}   [{pat}]",12,28,12,GRAY)
        bx3=pw-220
        mana_val=p.mana if p else 0; mana_max=p.max_mana if p else 100
        text(surface,f"MANA {int(mana_val)}/{int(mana_max)}",bx3,10,12,CYAN)
        _bar(surface,bx3,26,200,12,mana_val,mana_max,CYAN)
        # ── Bottom stats bar ──────────────────────────────────────────────
        bar_y = self.PLAY_H - 44
        pygame.draw.rect(surface,(10,10,22),(0,bar_y,pw,44))
        pygame.draw.line(surface,(40,40,80),(0,bar_y),(pw,bar_y),1)
        # DPS (rolling 3s) — colour: green→yellow→red by magnitude
        dps = self._current_dps
        if dps >= 200:   dps_col = (255, 80,  80)
        elif dps >= 80:  dps_col = (255, 200, 40)
        else:            dps_col = (80,  220, 80)
        text(surface, f"DPS  {dps:>6.1f}", 14, bar_y+6, 15, dps_col, bold=True)
        text(surface, f"PEAK {self._peak_dps:>6.1f}", 14, bar_y+24, 12, (180,180,220))
        # Centre: total stats
        text(surface,f"TOTAL DMG: {self.total_dmg}   HITS: {self.total_hits}   CRITS: {self.total_crits}",
             pw//2, bar_y+14, 13, LIGHT_GRAY, center=True)
        # Right: last hit message
        if self.last_msg:
            text(surface, self.last_msg, pw-12, bar_y+14, 13, GOLD,
                 **{"center": False} if True else {})
        poff=pw+4
        pygame.draw.rect(surface,(8,8,20),(pw,0,self.PANEL_W,self.PLAY_H))
        text(surface,"Q / E  to cycle",poff+self.PANEL_W//2,8,11,GRAY,center=True)
        text(surface,"WEAPONS",poff+self.PANEL_W//2,22,14,WHITE,bold=True,center=True)
        self._btn_back=button(surface,poff+8,self.PLAY_H-48,self.PANEL_W-16,38,"EXIT TO MENU",
            pygame.Rect(poff+8,self.PLAY_H-48,self.PANEL_W-16,38).collidepoint(mouse_pos),RED,size=14)
        lt,lb,ih=42,self.PLAY_H-60,54
        vis=(lb-lt)//ih
        self._scroll_max=max(0,(len(self._weapon_list)-vis)*ih)
        self._wpn_btns=[]
        clip=pygame.Rect(poff,lt,self.PANEL_W,lb-lt)
        surface.set_clip(clip)
        for i,wd in enumerate(self._weapon_list):
            wy=lt+i*ih-int(self._scroll)
            if wy+ih<lt or wy>lb: continue
            rect=pygame.Rect(poff+4,wy+2,self.PANEL_W-8,ih-4)
            sel=(i==self.wpn_idx); hov=rect.collidepoint(mouse_pos)
            rc=self.RARITY_COLOR.get(wd.rarity,WHITE)
            bg=(30,20,50) if sel else ((20,20,36) if hov else (14,14,26))
            pygame.draw.rect(surface,bg,rect,border_radius=6)
            bc=rc if sel else ((50,50,80) if hov else (28,28,48))
            pygame.draw.rect(surface,bc,rect,2 if sel else 1,border_radius=6)
            text(surface,wd.name,poff+10,wy+6,12,rc,bold=sel)
            text(surface,f"DMG {wd.damage}  |  {wd.fire_rate:.1f}/s",poff+10,wy+22,11,LIGHT_GRAY)
            text(surface,wd.rarity,poff+10,wy+36,10,rc)
            self._wpn_btns.append((rect,i))
        surface.set_clip(None)