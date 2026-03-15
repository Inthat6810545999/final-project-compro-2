"""
ui.py  –  All UI screens: Main Menu, Class Select, Inventory,
          Shop, Level-Up, Pause, Game Over, Victory, Stats
"""
import pygame
from constants import (
    SCREEN_W, SCREEN_H, HUD_H, CLASSES, RARITY_COLORS,
    SHOP_HEAL_COST, SHOP_ITEM_MULT, SHOP_REROLL_COST,
    BLACK, WHITE, GRAY, DARK_GRAY, RED, GREEN, BLUE, CYAN,
    YELLOW, GOLD, PURPLE, ORANGE, LIGHT_GRAY, LIGHT_BLUE
)
from item import make_weapon, make_armor, make_accessory, make_random_item
import random


# ── Font helpers ─────────────────────────────────────────────
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

def panel(surf, x, y, w, h, fill=(20,20,40), border=BLUE, radius=8):
    r = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surf, fill, r, border_radius=radius)
    pygame.draw.rect(surf, border, r, 2, border_radius=radius)
    return r

def button(surf, x, y, w, h, label, hover=False, color=BLUE, size=18):
    fill = (min(255, color[0]+40), min(255, color[1]+40), min(255, color[2]+40)) if hover else (color[0]//2, color[1]//2, color[2]//2)
    r    = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surf, fill, r, border_radius=6)
    pygame.draw.rect(surf, color, r, 2, border_radius=6)
    s = F(size, True).render(label, True, WHITE)
    surf.blit(s, (x + w//2 - s.get_width()//2, y + h//2 - s.get_height()//2))
    return r


# ─────────────────────────────────────────────────────────────
class MainMenuScreen:
    def __init__(self, tracker):
        self.tracker = tracker

    def draw(self, surface, mouse_pos):
        surface.fill((8, 8, 20))
        # Title
        text(surface, "SAUSAGE MAN", SCREEN_W//2, 80, 64, GOLD, bold=True, center=True)
        text(surface, "LEGENDS OF MIDGARD", SCREEN_W//2, 148, 28, CYAN, bold=True, center=True)

        # Decorative line
        pygame.draw.line(surface, BLUE, (120, 185), (SCREEN_W-120, 185), 2)

        # Buttons
        bw, bh, bx = 260, 52, SCREEN_W//2 - 130
        self.btn_play  = button(surface, bx, 220, bw, bh, "NEW GAME",   (mouse_pos[1]>220 and mouse_pos[1]<272 and abs(mouse_pos[0]-SCREEN_W//2)<130), GREEN)
        self.btn_stats = button(surface, bx, 290, bw, bh, "STATISTICS", (mouse_pos[1]>290 and mouse_pos[1]<342 and abs(mouse_pos[0]-SCREEN_W//2)<130), BLUE)
        self.btn_quit  = button(surface, bx, 360, bw, bh, "QUIT",       (mouse_pos[1]>360 and mouse_pos[1]<412 and abs(mouse_pos[0]-SCREEN_W//2)<130), RED)

        # Stats summary
        summary = self.tracker.get_summary()
        panel(surface, SCREEN_W//2 - 200, 430, 400, 120, fill=(15,15,30))
        if summary.get("total_runs", 0) > 0:
            text(surface, f"Total Runs: {summary['total_runs']}    Victories: {summary['victories']}", SCREEN_W//2, 445, 17, LIGHT_GRAY, center=True)
            text(surface, f"Best Score: {summary['best_score']:,}", SCREEN_W//2, 468, 17, GOLD, center=True)
            text(surface, f"Avg Kills:  {summary['avg_kills']}    Max Level: {summary['max_level']}", SCREEN_W//2, 491, 17, LIGHT_GRAY, center=True)
            text(surface, f"Avg Run Time: {summary['avg_duration']}s", SCREEN_W//2, 514, 17, LIGHT_GRAY, center=True)
        else:
            text(surface, "No runs yet. Play to collect statistics!", SCREEN_W//2, 478, 17, GRAY, center=True)

        text(surface, "WASD/Arrows: Move   LClick: Attack   E: Pick Up   I: Inventory   ESC: Pause", SCREEN_W//2, SCREEN_H-30, 14, GRAY, center=True)

    def handle_click(self, pos):
        if self.btn_play.collidepoint(pos):   return "play"
        if self.btn_stats.collidepoint(pos):  return "stats"
        if self.btn_quit.collidepoint(pos):   return "quit"
        return None


# ─────────────────────────────────────────────────────────────
class ClassSelectScreen:
    def __init__(self):
        self.selected = None

    def draw(self, surface, mouse_pos):
        surface.fill((8, 8, 20))
        text(surface, "CHOOSE YOUR CLASS", SCREEN_W//2, 40, 36, GOLD, bold=True, center=True)
        pygame.draw.line(surface, BLUE, (80, 90), (SCREEN_W-80, 90), 2)

        self.class_rects = {}
        classes = list(CLASSES.keys())
        card_w, card_h = 270, 340
        total_w = len(classes) * card_w + (len(classes)-1) * 20
        start_x = SCREEN_W//2 - total_w//2

        for i, cname in enumerate(classes):
            cfg = CLASSES[cname]
            cx  = start_x + i * (card_w + 20)
            cy  = 110
            hover = pygame.Rect(cx, cy, card_w, card_h).collidepoint(mouse_pos)
            fill  = (30, 30, 55) if not hover else (45, 45, 75)
            r = panel(surface, cx, cy, card_w, card_h, fill=fill, border=cfg["color"])
            self.class_rects[cname] = r

            # Class avatar circle
            pygame.draw.circle(surface, cfg["color"], (cx + card_w//2, cy + 70), 40)
            pygame.draw.circle(surface, WHITE, (cx + card_w//2, cy + 70), 40, 3)
            text(surface, cname[0], cx + card_w//2, cy + 55, 36, WHITE, bold=True, center=True)

            text(surface, cname, cx + card_w//2, cy + 118, 22, cfg["color"], bold=True, center=True)
            text(surface, cfg["description"], cx + 10, cy + 148, 14, LIGHT_GRAY)

            # Stats
            stats = cfg["base_stats"]
            sy = cy + 185
            for stat, val in stats.items():
                bar_fill = int(120 * val / 12)
                col = {"STR": RED, "AGI": GREEN, "VIT": ORANGE,
                       "INT": BLUE, "DEX": CYAN, "LUK": GOLD}.get(stat, WHITE)
                text(surface, f"{stat}", cx + 14, sy, 14, col)
                pygame.draw.rect(surface, (40,40,60), (cx+50, sy+2, 120, 10))
                pygame.draw.rect(surface, col, (cx+50, sy+2, bar_fill, 10))
                text(surface, str(val), cx+175, sy, 14, WHITE)
                sy += 20

            # Passive
            text(surface, "Passive:", cx+10, cy+308, 13, YELLOW)
            # Wrap passive text
            ptext = cfg.get("passive", "")
            text(surface, ptext[:40], cx+10, cy+322, 11, LIGHT_GRAY)

        # Confirm
        self.btn_back = button(surface, 30, SCREEN_H-60, 120, 40, "BACK", False, GRAY)

    def handle_click(self, pos):
        for cname, rect in self.class_rects.items():
            if rect.collidepoint(pos):
                return cname
        if hasattr(self, "btn_back") and self.btn_back.collidepoint(pos):
            return "back"
        return None


# ─────────────────────────────────────────────────────────────
class InventoryScreen:
    def __init__(self):
        self.selected_idx = 0
        self.scroll = 0

    def draw(self, surface, player, mouse_pos):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        surface.blit(overlay, (0, 0))

        W, H = 760, 560
        ox = SCREEN_W//2 - W//2
        oy = SCREEN_H//2 - H//2
        panel(surface, ox, oy, W, H, fill=(12,12,28), border=BLUE)
        text(surface, "INVENTORY", ox + W//2, oy+12, 26, GOLD, bold=True, center=True)

        # Equipment slots
        text(surface, "EQUIPPED:", ox+14, oy+50, 16, CYAN, bold=True)
        slot_names = ["weapon", "armor", "accessory"]
        for si, slot in enumerate(slot_names):
            itm = player.equipment.get(slot)
            ex  = ox + 14 + si * 240
            ey  = oy + 70
            col = RARITY_COLORS.get(itm.rarity, WHITE) if itm else GRAY
            panel(surface, ex, ey, 220, 52, fill=(20,20,40), border=col)
            text(surface, slot.upper(), ex+8, ey+4, 12, GRAY)
            text(surface, itm.name if itm else "— empty —", ex+8, ey+22, 15, col if itm else GRAY)
            if itm:
                if hasattr(itm, "damage"):
                    text(surface, f"DMG {itm.damage}", ex+8, ey+38, 12, LIGHT_GRAY)
                elif hasattr(itm, "defense"):
                    text(surface, f"DEF {itm.defense}", ex+8, ey+38, 12, LIGHT_GRAY)

        pygame.draw.line(surface, (40,40,80), (ox+14, oy+132), (ox+W-14, oy+132))

        # Inventory list
        text(surface, f"BACKPACK ({len(player.inventory)} items):", ox+14, oy+138, 16, CYAN, bold=True)
        visible = 8
        self.item_rects = {}
        self.equip_btns = {}

        for idx in range(visible):
            real_idx = idx + self.scroll
            if real_idx >= len(player.inventory):
                break
            itm = player.inventory[real_idx]
            iy  = oy + 162 + idx * 46
            col = RARITY_COLORS.get(itm.rarity, WHITE)
            is_sel = (real_idx == self.selected_idx)

            # Check if this weapon can be equipped by this class
            can_equip = True
            lock_msg  = ""
            if hasattr(itm, "can_equip"):
                can_equip, lock_msg = itm.can_equip(player)

            fill = (35, 35, 65) if is_sel else ((30,10,10) if not can_equip else (18,18,36))
            border_col = GRAY if not can_equip else col
            r = panel(surface, ox+14, iy, 480, 40, fill=fill, border=border_col)
            self.item_rects[real_idx] = r

            name_col = GRAY if not can_equip else col
            label = f"[{itm.rarity[0]}] {itm.name}"
            if not can_equip:
                label += f"  🔒 {lock_msg}"
            text(surface, label, ox+22, iy+6, 16, name_col, bold=is_sel)
            text(surface, itm.description[:50], ox+22, iy+24, 12, LIGHT_GRAY)

            # Equip button — greyed out if class mismatch
            eq_col = GREEN if can_equip else (60,60,60)
            eb = button(surface, ox+504, iy+6, 80, 28,
                        "EQUIP" if can_equip else "LOCKED",
                        pygame.Rect(ox+504, iy+6, 80, 28).collidepoint(mouse_pos) and can_equip,
                        eq_col, 14)
            self.equip_btns[real_idx] = (eb, can_equip)

            # Sell button
            sb = button(surface, ox+594, iy+6, 80, 28, f"SELL {itm.sell_price}G",
                        pygame.Rect(ox+594, iy+6, 80, 28).collidepoint(mouse_pos), ORANGE, 13)
            self.item_rects[f"sell_{real_idx}"] = sb

        # Stats panel — Ragnarok style
        text(surface, "BASE STATS", ox+686, oy+138, 14, CYAN, bold=True)
        stat_y = oy + 157
        stat_colors = {"STR": RED, "AGI": GREEN, "VIT": ORANGE,
                       "INT": BLUE, "DEX": CYAN, "LUK": GOLD}
        for stat, val in player.stats.items():
            col = stat_colors.get(stat, WHITE)
            text(surface, f"{stat}", ox+686, stat_y, 14, col, bold=True)
            # bar
            bar_fill = min(140, int(140 * val / 99))
            pygame.draw.rect(surface, (30,30,50), (ox+718, stat_y+2, 60, 11))
            pygame.draw.rect(surface, col,        (ox+718, stat_y+2, bar_fill*60//140, 11))
            text(surface, str(val), ox+782, stat_y, 14, WHITE)
            stat_y += 20

        # Divider
        pygame.draw.line(surface, (40,40,80), (ox+686, stat_y+2), (ox+W-10, stat_y+2))
        stat_y += 8

        # Derived combat stats
        text(surface, "COMBAT STATS", ox+686, stat_y, 13, YELLOW, bold=True); stat_y += 18
        atk_val  = getattr(player, "matk", player.atk) if player.char_class == "Mage" else player.atk
        atk_lbl  = "MATK" if player.char_class == "Mage" else "ATK"
        aspd     = getattr(player, "aspd_mult", 1.0)
        crit_pct = int(player.crit_chance * 100)
        crit_mul = getattr(player, "crit_mult", 1.5)
        dodge    = int(getattr(player, "dodge", 0) * 100)
        derived = [
            (atk_lbl,   str(atk_val),               RED),
            ("DEF",     str(player.defense),         LIGHT_GRAY),
            ("ASPD",    f"{aspd:.2f}x",              GREEN),
            ("CRIT",    f"{crit_pct}% x{crit_mul:.1f}", GOLD),
            ("DODGE",   f"{dodge}%",                 CYAN),
            ("SPD",     f"{player.move_speed:.1f}",  GREEN),
            ("MAX HP",  str(player.max_hp),          ORANGE),
        ]
        for lbl, val, col in derived:
            text(surface, f"{lbl}:", ox+686, stat_y, 13, LIGHT_GRAY)
            text(surface, val,       ox+730, stat_y, 13, col, bold=True)
            stat_y += 18

        # Stat points
        if player.stat_points > 0:
            text(surface, f"FREE POINTS: {player.stat_points}", ox+698, stat_y+28, 15, GOLD, bold=True)
            sp_y = stat_y + 50
            self.stat_btns = {}
            for stat in player.stats:
                col = {"STR": RED, "AGI": GREEN, "VIT": ORANGE,
                       "INT": BLUE, "DEX": CYAN, "LUK": GOLD}.get(stat, WHITE)
                br = button(surface, ox+695, sp_y, 80, 22, f"+{stat}",
                            pygame.Rect(ox+695, sp_y, 80, 22).collidepoint(mouse_pos), col, 12)
                self.stat_btns[stat] = br
                sp_y += 26
        else:
            self.stat_btns = {}

        # Close hint
        text(surface, "Press I or ESC to close", ox+W//2, oy+H-24, 14, GRAY, center=True)

    def handle_click(self, pos, player):
        # Equip buttons
        for idx, (btn, can_equip) in self.equip_btns.items():
            if btn.collidepoint(pos):
                if not can_equip:
                    return "locked"   # blocked — wrong class
                itm = player.inventory[idx]
                old = player.equip(itm)
                player.inventory.pop(idx)
                if old:
                    player.inventory.append(old)
                return "equip"
        # Sell buttons
        for key, r in self.item_rects.items():
            if isinstance(key, str) and key.startswith("sell_"):
                if r.collidepoint(pos):
                    idx = int(key.split("_")[1])
                    if idx < len(player.inventory):
                        itm = player.inventory.pop(idx)
                        player.gold += itm.sell_price
                    return "sell"
        # Select item
        for idx, r in self.item_rects.items():
            if isinstance(idx, int) and r.collidepoint(pos):
                self.selected_idx = idx
        # Stat point buttons
        for stat, r in self.stat_btns.items():
            if r.collidepoint(pos):
                player.allocate_stat(stat)
                return "stat"
        return None

    def handle_scroll(self, direction, player):
        max_scroll = max(0, len(player.inventory) - 8)
        self.scroll = max(0, min(self.scroll + direction, max_scroll))


# ─────────────────────────────────────────────────────────────
class ShopScreen:
    def __init__(self, stage_id, char_class="Warrior"):
        self.stage_id   = stage_id
        self.char_class = char_class
        self.reroll_cost = SHOP_REROLL_COST
        self._gen_items(stage_id, char_class)

    def _gen_items(self, stage_id, char_class):
        """Generate shop items: weapons are class-specific, armor/acc are shared."""
        rarities = ["Common", "Common", "Rare", "Rare", "Epic"]
        if stage_id >= 3:
            rarities = ["Rare", "Rare", "Epic", "Epic", "Legendary"]
        self.shop_items = [
            make_weapon(random.choice(rarities), weapon_class=char_class),
            make_weapon(random.choice(rarities), weapon_class=char_class),
            make_armor(random.choice(rarities)),
            make_accessory(random.choice(rarities)),
            make_random_item(),
        ]
        self.prices = [SHOP_ITEM_MULT.get(i.rarity, 30) for i in self.shop_items]

    def draw(self, surface, player, mouse_pos):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0,0,0,200))
        surface.blit(overlay, (0,0))

        W, H = 860, 530
        ox = SCREEN_W//2 - W//2
        oy = SCREEN_H//2 - H//2
        panel(surface, ox, oy, W, H, fill=(10,18,10), border=GREEN)
        text(surface, "SHOP", ox+W//2, oy+10, 28, GOLD, bold=True, center=True)

        # Gold + reroll info bar
        can_reroll = player.gold >= self.reroll_cost
        text(surface, f"Gold: {player.gold} G", ox+16, oy+46, 18, GOLD)

        # Reroll button (top-right inside panel)
        reroll_col = GOLD if can_reroll else GRAY
        self.btn_reroll = button(surface, ox+W-180, oy+38, 164, 34,
                                 f"REROLL  ({self.reroll_cost}G)",
                                 pygame.Rect(ox+W-180, oy+38, 164, 34).collidepoint(mouse_pos),
                                 reroll_col, 14)

        # Heal button
        can_heal = player.gold >= SHOP_HEAL_COST
        self.heal_btn = button(surface, ox+16, oy+82, 220, 34,
                               f"HEAL 50 HP  ({SHOP_HEAL_COST}G)",
                               pygame.Rect(ox+16, oy+82, 220, 34).collidepoint(mouse_pos),
                               RED if can_heal else GRAY, 14)

        # Class tag
        cls_col = {"Warrior": RED, "Mage": PURPLE, "Ranger": GREEN}.get(player.char_class, WHITE)
        text(surface, f"Weapons shown for: {player.char_class}", ox+260, oy+89, 13, cls_col)

        pygame.draw.line(surface, (30,60,30), (ox+14, oy+124), (ox+W-14, oy+124))

        # Shop items
        self.buy_btns = {}
        for i, itm in enumerate(self.shop_items):
            iy  = oy + 134 + i * 72
            if itm is None:
                panel(surface, ox+14, iy, W-28, 60, fill=(10,10,10), border=GRAY)
                text(surface, "— SOLD OUT —", ox+22, iy+20, 16, GRAY)
                continue

            col = RARITY_COLORS.get(itm.rarity, WHITE)

            # Check equip restriction for weapons
            can_use   = True
            lock_note = ""
            if hasattr(itm, "weapon_class") and itm.weapon_class not in ("Any", player.char_class):
                can_use   = False
                lock_note = f"  ⚠ {itm.weapon_class} only"

            fill_col = (15,25,15) if can_use else (25,10,10)
            panel(surface, ox+14, iy, W-28, 60, fill=fill_col, border=col)

            # Item name + rarity
            name_col = col if can_use else GRAY
            text(surface, f"[{itm.rarity}] {itm.name}{lock_note}", ox+22, iy+5, 17, name_col, bold=True)
            text(surface, itm.description[:70], ox+22, iy+26, 12, LIGHT_GRAY)

            # Stats line
            stats_parts = []
            if hasattr(itm, "damage"):
                stats_parts.append(f"DMG:{itm.damage}")
            if hasattr(itm, "defense"):
                stats_parts.append(f"DEF:{itm.defense}")
            if hasattr(itm, "fire_rate") and itm.fire_rate > 0:
                stats_parts.append(f"Rate:{itm.fire_rate:.1f}/s")
            # Show stat bonuses in gold colour
            stat_bonus = getattr(itm, "stat_bonus", {})
            if stat_bonus:
                sb_str = "  ".join(f"+{v}{k}" for k,v in stat_bonus.items() if v > 0)
                if sb_str:
                    stats_parts.append(sb_str)
            if stats_parts:
                text(surface, "  ".join(stats_parts[:3]), ox+22, iy+43, 12, ORANGE)
                if len(stats_parts) > 3:
                    text(surface, "  ".join(stats_parts[3:]), ox+22, iy+54, 11, GOLD)

            price = self.prices[i]
            can_buy = player.gold >= price and can_use
            bb = button(surface, ox+W-152, iy+13, 132, 34,
                        f"BUY  {price}G",
                        pygame.Rect(ox+W-152, iy+13, 132, 34).collidepoint(mouse_pos),
                        GREEN if can_buy else GRAY, 14)
            self.buy_btns[i] = (bb, can_use)

        self.btn_leave = button(surface, ox+W//2-90, oy+H-50, 180, 38,
                                "LEAVE SHOP",
                                pygame.Rect(ox+W//2-90, oy+H-50, 180, 38).collidepoint(mouse_pos),
                                BLUE)

    def handle_click(self, pos, player):
        # Heal
        if self.heal_btn.collidepoint(pos):
            if player.gold >= SHOP_HEAL_COST:
                player.gold -= SHOP_HEAL_COST
                player.heal(50)
                return "heal"

        # Reroll — costs gold, regenerates entire shop
        if self.btn_reroll.collidepoint(pos):
            if player.gold >= self.reroll_cost:
                player.gold      -= self.reroll_cost
                self.reroll_cost  = int(self.reroll_cost * 1.5)  # price goes up each reroll
                self._gen_items(self.stage_id, player.char_class)
                return "reroll"

        # Buy items
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
        overlay.fill((0,0,0,160))
        surface.blit(overlay, (0,0))
        text(surface, "PAUSED", SCREEN_W//2, 200, 52, GOLD, bold=True, center=True)
        bw, bh, bx = 220, 48, SCREEN_W//2 - 110
        self.btn_resume = button(surface, bx, 290, bw, bh, "RESUME", pygame.Rect(bx,290,bw,bh).collidepoint(mouse_pos), GREEN)
        self.btn_menu   = button(surface, bx, 356, bw, bh, "MAIN MENU", pygame.Rect(bx,356,bw,bh).collidepoint(mouse_pos), BLUE)

    def handle_click(self, pos):
        if hasattr(self, "btn_resume") and self.btn_resume.collidepoint(pos): return "resume"
        if hasattr(self, "btn_menu")   and self.btn_menu.collidepoint(pos):   return "menu"
        return None


# ─────────────────────────────────────────────────────────────
class GameOverScreen:
    def draw(self, surface, player, tracker, win=False):
        surface.fill((5,0,0) if not win else (0,5,10))
        title = "VICTORY!" if win else "GAME OVER"
        col   = GOLD if win else RED
        text(surface, title, SCREEN_W//2, 80, 64, col, bold=True, center=True)

        summary = tracker.current_run
        cy = 180
        pairs = [
            ("Score",      f"{summary.get('score',0):,}"),
            ("Class",      player.char_class),
            ("Level",      player.level),
            ("Enemies",    summary.get("enemies_defeated", 0)),
            ("Damage",     f"{summary.get('total_damage',0):,}"),
            ("Items",      summary.get("items_collected", 0)),
            ("Gold",       player.gold),
            ("Duration",   f"{summary.get('duration_sec',0)}s"),
            ("Stage",      summary.get("stage_reached", 1)),
        ]
        panel(surface, SCREEN_W//2-200, cy-10, 400, len(pairs)*32+20, fill=(15,15,30))
        for label, val in pairs:
            text(surface, f"{label}:", SCREEN_W//2-180, cy, 18, LIGHT_GRAY)
            text(surface, str(val),    SCREEN_W//2+80,  cy, 18, WHITE)
            cy += 30

        bw, bx = 200, SCREEN_W//2-100
        self.btn_menu   = button(surface, bx, cy+20, bw, 44, "MAIN MENU", False, BLUE)
