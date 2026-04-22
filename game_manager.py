"""
game_manager.py  –  GameManager (central controller)
Fixes applied:
  - Player bullet → enemy collision loop added
  - Enemy bullet → player collision loop added
  - Player gains EXP and gold on kills
  - Melee damage dealt to nearby enemies + timer reset
  - shoot_cooldown always ticks down (not just in else branch)
  - _try_pickup() defined
  - _next_stage() defined
  - stage completion checked every frame
  - GameOverScreen.draw() called with correct arguments
  - StatsTracker.end_run() called on death/victory
"""
import math
import random
import pygame
from constants import (
    FPS, SCREEN_W, SCREEN_H, HUD_H,
    STATE_MENU, STATE_CLASS_SEL, STATE_PLAYING,
    STATE_INVENTORY, STATE_PAUSED, STATE_GAME_OVER,
    STATE_VICTORY, STATE_SHOP, STATE_STATS, STATE_RANGE,
    WHITE, RED, GREEN, YELLOW, GOLD, CYAN, ORANGE, BLACK, GRAY,
    STAGE_CONFIGS,
)
from player        import Player
from stage         import Stage
from enemy         import EnemyBullet
from bullet        import Bullet, DroppedItem, FloatingText, draw_hud, Portal, LaserBeam
from stats_tracker import StatsTracker
from ui            import (MainMenuScreen, ClassSelectScreen, InventoryScreen,
                           ShopScreen, PauseScreen, GameOverScreen,
                           ShootingRangeScreen)
from sound_manager import SoundManager


class GameManager:
    """Central game controller."""

    def __init__(self, screen):
        self.screen      = screen
        self.clock       = pygame.time.Clock()
        self.state       = STATE_MENU
        self.running     = True
        self._fullscreen = False

        self.tracker = StatsTracker()

        self.player    = None
        self.stage     = None
        self.stage_idx = 0
        self.enemies   = []
        self.bullets   = []
        self.e_bullets = []
        self.drops     = []
        self.fx        = []

        self.score    = 0
        self.kills    = 0
        self.run_time = 0.0   # seconds elapsed this run

        # ── New features ──────────────────────────────────────
        self.portal          = None          # Portal object after stage cleared
        self._last_enemy_pos = (640, 360)    # position of last enemy killed
        self.shake_timer     = 0.0           # screen-shake duration remaining
        self.shake_mag       = 0             # shake magnitude in pixels
        self.boss_clear_timer = 0.0          # green overlay + checkmark duration

        # ── Boss cinematic system ──────────────────────────────
        self.boss_entity          = None     # reference to live BossEnemy
        self.boss_spawn_timer     = 0.0      # spawn intro overlay (counts down)
        self.boss_ready_timer     = 0.0      # "GET READY" freeze after cinematic
        self.boss_death_timer     = 0.0      # death explosion overlay (counts down)
        self.boss_death_particles = []       # explosion particles list

        # ── Sound ─────────────────────────────────────────────
        self.sfx = SoundManager()

        self.menu_screen  = MainMenuScreen(self.tracker)
        self.range_screen = ShootingRangeScreen()
        self._frame_events = []
        self.class_screen = ClassSelectScreen()
        self.inv_screen   = InventoryScreen()
        self.pause_screen = PauseScreen()
        self.over_screen  = GameOverScreen()
        self.shop_screen  = None
        self.player_name  = "Hero"

    # ── Boss cinematic methods ────────────────────────────────

    def _draw_boss_hpbar(self, surface):
        """Cinematic boss HP bar — Dark Fantasy style matching main menu / pause."""
        boss = self.boss_entity
        if not boss or not boss.alive:
            return
        pct   = boss.hp / max(1, boss.max_hp)
        phase = getattr(boss, "phase", 1)
        t     = pygame.time.get_ticks() / 1000.0
        pulse = math.sin(t * 3.2) * 0.5 + 0.5   # 0 → 1

        # ── Dark Fantasy palette (matches ui.py) ─────────────
        DF_BG      = (14,  10,   6)
        DF_BG2     = (22,  16,  10)
        DF_GOLD    = (200, 165,  80)
        DF_GOLD_B  = (240, 205, 100)
        DF_GOLD_D  = (110,  82,  30)
        DF_BLOOD   = (160,  32,  32)
        DF_BLOOD_B = (210,  55,  40)
        DF_CRIMSON = (110,  18,  18)
        DF_STONE   = (38,  30,  22)
        DF_STONE2  = (55,  44,  30)
        DF_BONE    = (210, 195, 165)
        DF_SILVER  = (170, 162, 148)
        DF_ORANGE  = (230, 110,  30)

        bar_w  = 760
        bar_h  = 22
        bar_x  = (SCREEN_W - bar_w) // 2
        bar_y  = SCREEN_H - HUD_H - bar_h - 18

        panel_x = bar_x - 32
        panel_y = bar_y - 36
        panel_w = bar_w + 64
        panel_h = bar_h + 58

        # ── Phase-2 outer glow ────────────────────────────────
        if phase == 2:
            glow_a = int(40 + 35 * pulse)
            for gw in (10, 6, 3):
                gs = pygame.Surface((panel_w + gw*4, panel_h + gw*4), pygame.SRCALPHA)
                pygame.draw.rect(gs, (DF_ORANGE[0], DF_ORANGE[1], DF_ORANGE[2], glow_a),
                                 (0, 0, panel_w + gw*4, panel_h + gw*4), gw, border_radius=6)
                surface.blit(gs, (panel_x - gw*2, panel_y - gw*2))

        # ── Stone panel background ─────────────────────────────
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((*DF_BG, 220))
        surface.blit(panel, (panel_x, panel_y))

        # Stone texture strips (horizontal)
        for iy in range(0, panel_h, 14):
            st = pygame.Surface((panel_w, 1), pygame.SRCALPHA)
            st.fill((*DF_STONE, 60))
            surface.blit(st, (panel_x, panel_y + iy))

        # Outer border — gold with corner rivets
        border_col = DF_GOLD_B if phase == 2 else DF_GOLD
        pygame.draw.rect(surface, border_col,
                         (panel_x, panel_y, panel_w, panel_h), 2, border_radius=4)
        # Blood inner border
        pygame.draw.rect(surface, DF_BLOOD,
                         (panel_x + 3, panel_y + 3, panel_w - 6, panel_h - 6), 1, border_radius=3)

        # Corner rivets
        for (rx2, ry2) in [(panel_x+6, panel_y+6), (panel_x+panel_w-6, panel_y+6),
                           (panel_x+6, panel_y+panel_h-6), (panel_x+panel_w-6, panel_y+panel_h-6)]:
            pygame.draw.circle(surface, DF_GOLD_D,  (rx2, ry2), 5)
            pygame.draw.circle(surface, DF_GOLD,    (rx2, ry2), 5, 2)
            pygame.draw.circle(surface, DF_GOLD_B,  (rx2-1, ry2-1), 2)

        # ── Fonts (impact = dark fantasy feel) ───────────────
        try:
            nm_font  = pygame.font.SysFont("impact", 20)
            hp_font  = pygame.font.SysFont("impact", 14)
            ph_font  = pygame.font.SysFont("impact", 13)
        except Exception:
            nm_font  = pygame.font.Font(None, 22)
            hp_font  = pygame.font.Font(None, 16)
            ph_font  = pygame.font.Font(None, 15)

        # ── Boss name ─────────────────────────────────────────
        name_col = DF_GOLD_B if phase == 2 else DF_GOLD
        # Shadow
        nm_shd = nm_font.render(boss.enemy_type, True, (0, 0, 0))
        surface.blit(nm_shd, (bar_x + 2, panel_y + 8 + 2))
        nm_surf = nm_font.render(boss.enemy_type, True, name_col)
        surface.blit(nm_surf, (bar_x, panel_y + 8))

        # ── Phase label (right-aligned) ───────────────────────
        if phase == 2:
            flash_c = int(140 + 80 * abs(math.sin(t * 5)))
            ph_col  = (255, flash_c, 20)
            ph_str  = "[ PHASE 2 - ENRAGED ]"
        else:
            ph_col  = DF_SILVER
            ph_str  = "[ PHASE 1 ]"
        ph_surf = ph_font.render(ph_str, True, ph_col)
        surface.blit(ph_surf, (bar_x + bar_w - ph_surf.get_width(), panel_y + 10))

        # ── Rune divider line under name row ─────────────────
        div_y = panel_y + 30
        pygame.draw.line(surface, DF_GOLD_D, (bar_x, div_y), (bar_x + bar_w, div_y), 1)
        # Diamond accent
        cx3 = bar_x + bar_w // 2
        pts_d = [(cx3, div_y - 4), (cx3 + 5, div_y), (cx3, div_y + 4), (cx3 - 5, div_y)]
        pygame.draw.polygon(surface, DF_GOLD, pts_d)

        # ── HP bar track ──────────────────────────────────────
        pygame.draw.rect(surface, DF_CRIMSON,
                         (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2), border_radius=4)
        pygame.draw.rect(surface, (12, 4, 4),
                         (bar_x, bar_y, bar_w, bar_h), border_radius=4)

        # ── HP fill — gradient ────────────────────────────────
        fill_w = max(0, int(bar_w * pct))
        if fill_w > 0:
            if pct > 0.60:
                base_col = DF_BLOOD_B if phase == 1 else DF_ORANGE
            elif pct > 0.30:
                base_col = (200, 40, 20) if phase == 1 else (240, 90, 10)
            else:
                fl = abs(math.sin(t * 8))
                base_col = (255, int(15 + 45 * fl), 0)

            if phase == 2:
                base_col = tuple(min(255, c + 40) for c in base_col)

            # Draw gradient fill (left darker, right brighter)
            for px2 in range(fill_w):
                frac = px2 / max(1, fill_w)
                r = min(255, int(base_col[0] * (0.7 + 0.3 * frac)))
                g = min(255, int(base_col[1] * (0.5 + 0.5 * frac)))
                b = int(base_col[2])
                pygame.draw.line(surface, (r, g, b), (bar_x + px2, bar_y), (bar_x + px2, bar_y + bar_h))

            # Shine strip on top
            shine_surf = pygame.Surface((fill_w, bar_h // 3), pygame.SRCALPHA)
            shine_surf.fill((*DF_GOLD_B, 35))
            surface.blit(shine_surf, (bar_x, bar_y))

            # Phase-2 pulsing glow overlay
            if phase == 2:
                g_a = int(40 + 35 * pulse)
                gsurf2 = pygame.Surface((fill_w, bar_h), pygame.SRCALPHA)
                gsurf2.fill((*base_col, g_a))
                surface.blit(gsurf2, (bar_x, bar_y))

        # ── Segment markers at 25 / 50 / 75% ─────────────────
        for seg in (0.25, 0.50, 0.75):
            mx = bar_x + int(bar_w * seg)
            pygame.draw.line(surface, DF_GOLD_D, (mx, bar_y), (mx, bar_y + bar_h), 2)
            # Small diamond tick
            pts_s = [(mx, bar_y - 4), (mx + 3, bar_y), (mx, bar_y + 4), (mx - 3, bar_y)]
            pygame.draw.polygon(surface, DF_GOLD_D, pts_s)

        # ── HP text ───────────────────────────────────────────
        hp_txt  = f"{max(0, boss.hp):,}  /  {boss.max_hp:,}"
        hp_shd  = hp_font.render(hp_txt, True, (0, 0, 0))
        hp_surf = hp_font.render(hp_txt, True, DF_BONE)
        hx = bar_x + bar_w // 2 - hp_surf.get_width() // 2
        hy = bar_y + bar_h // 2 - hp_surf.get_height() // 2
        surface.blit(hp_shd, (hx + 1, hy + 1))
        surface.blit(hp_surf, (hx, hy))

        # ── Outer bar border ──────────────────────────────────
        brd = DF_GOLD_B if phase == 2 else DF_GOLD
        pygame.draw.rect(surface, brd,
                         (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2), 2, border_radius=4)

    def _draw_boss_spawn_cinematic(self, surface):
        """3-second cinematic intro when boss room is entered — dark fantasy theme."""
        import math as _math
        t = self.boss_spawn_timer       # counts DOWN 3.0 → 0
        if t <= 0 or not self.boss_entity:
            return

        # ── Palette (dark fantasy — matches main menu / pause) ─
        DF_BG      = (10,  6,  2)
        DF_GOLD    = (212, 175, 55)
        DF_GOLD2   = (255, 215, 80)
        DF_BLOOD   = (140, 20, 20)
        DF_BLOOD2  = (200, 40, 10)
        DF_STONE   = (42,  34, 28)
        DF_STONE2  = (62,  50, 40)
        DF_SILVER  = (180, 170, 160)

        cx = SCREEN_W // 2
        cy = SCREEN_H // 2

        # ── Slide / ease progress ─────────────────────────────
        slide_frac = max(0.0, min(1.0, (3.0 - t) / 1.0))
        ease       = 1.0 - (1.0 - slide_frac) ** 3
        hp_ease    = max(0.0, min(1.0, (3.0 - t - 0.6) / 0.8))   # HP bar appears later

        # ── Full-screen vignette overlay ──────────────────────
        vig_alpha = int(min(210, 210 * min(1.0, t / 2.2)))
        vig = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        vig.fill((0, 0, 0, vig_alpha))
        surface.blit(vig, (0, 0))

        # ── Horizontal scan-lines (eerie) ─────────────────────
        if t > 0.8:
            scan_alpha = int(min(60, 60 * (t - 0.8) / 0.8))
            for iy in range(0, SCREEN_H, 10):
                s = pygame.Surface((SCREEN_W, 1), pygame.SRCALPHA)
                s.fill((180, 10, 0, scan_alpha))
                surface.blit(s, (0, iy))

        # ── Top + bottom gold/blood cinematic bars ────────────
        bar_h = 36
        bar_alpha = int(min(240, ease * 255))
        for by, col in [(0, DF_BLOOD), (SCREEN_H - bar_h, DF_BLOOD)]:
            bs = pygame.Surface((SCREEN_W, bar_h), pygame.SRCALPHA)
            bs.fill((*col, bar_alpha))
            surface.blit(bs, (0, by))
        # Gold trim lines on bars
        if ease > 0.1:
            trim_a = int(min(255, ease * 255))
            for by in [bar_h, SCREEN_H - bar_h - 1]:
                ts = pygame.Surface((SCREEN_W, 2), pygame.SRCALPHA)
                ts.fill((*DF_GOLD, trim_a))
                surface.blit(ts, (0, by))

        # ── Fonts ─────────────────────────────────────────────
        try:
            title_font = pygame.font.SysFont("impact", 62)
            sub_font   = pygame.font.SysFont("impact", 24)
            phase_font = pygame.font.SysFont("impact", 20)
            hp_font    = pygame.font.SysFont("impact", 18)
        except Exception:
            title_font = pygame.font.Font(None, 72)
            sub_font   = pygame.font.Font(None, 28)
            phase_font = pygame.font.Font(None, 24)
            hp_font    = pygame.font.Font(None, 22)

        # ── Boss name slide in from top ───────────────────────
        base_y  = cy - 52
        slide_y = int(-100 + (base_y + 100) * ease)

        boss_name = self.boss_entity.enemy_type
        phase_num = getattr(self.boss_entity, "phase", 1)

        # Shadow layer
        shd = title_font.render(boss_name, True, (0, 0, 0))
        shd.set_alpha(int(ease * 200))
        surface.blit(shd, (cx - shd.get_width() // 2 + 3, slide_y + 3))
        # Gold gradient: inner lighter gold
        nm_col = (int(212 + 43 * ease), int(175 + 40 * ease), int(55 * (1 - ease * 0.3)))
        nm = title_font.render(boss_name, True, nm_col)
        nm.set_alpha(int(ease * 255))
        surface.blit(nm, (cx - nm.get_width() // 2, slide_y))

        # ── "— B O S S —" header ──────────────────────────────
        if ease > 0.3:
            hdr_a = int(min(255, (ease - 0.3) / 0.7 * 255))
            hdr = sub_font.render("—  B O S S  —", True, DF_BLOOD2)
            hdr.set_alpha(hdr_a)
            surface.blit(hdr, (cx - hdr.get_width() // 2, slide_y - 40))

        # ── Decorative horizontal rule under name ─────────────
        if ease > 0.5:
            rule_a = int(min(255, (ease - 0.5) / 0.5 * 255))
            rule_w = int(min(420, nm.get_width() + 80) * ease)
            rule_surf = pygame.Surface((rule_w, 2), pygame.SRCALPHA)
            rule_surf.fill((*DF_GOLD, rule_a))
            surface.blit(rule_surf, (cx - rule_w // 2, slide_y + nm.get_height() + 4))

        # ── Phase label ───────────────────────────────────────
        if ease > 0.55:
            ph_a = int(min(255, (ease - 0.55) / 0.45 * 255))
            phase_label = f"[ PHASE {phase_num} ]"
            ph_col = (220, 150, 60) if phase_num >= 2 else DF_SILVER
            ph = phase_font.render(phase_label, True, ph_col)
            ph.set_alpha(ph_a)
            surface.blit(ph, (cx - ph.get_width() // 2, slide_y + nm.get_height() + 14))

        # ── Corner rune accents ───────────────────────────────
        if ease > 0.4:
            rune_a   = int(min(180, (ease - 0.4) / 0.6 * 180))
            rune_sz  = 18
            rune_col = (*DF_GOLD, rune_a)
            margin   = 12
            for rx, ry, dx, dy in [
                (margin, bar_h + margin, 1, 1),
                (SCREEN_W - margin, bar_h + margin, -1, 1),
                (margin, SCREEN_H - bar_h - margin, 1, -1),
                (SCREEN_W - margin, SCREEN_H - bar_h - margin, -1, -1),
            ]:
                rs = pygame.Surface((rune_sz * 2, rune_sz * 2), pygame.SRCALPHA)
                pygame.draw.line(rs, rune_col,
                    (rune_sz, rune_sz), (rune_sz + dx * rune_sz, rune_sz), 2)
                pygame.draw.line(rs, rune_col,
                    (rune_sz, rune_sz), (rune_sz, rune_sz + dy * rune_sz), 2)
                surface.blit(rs, (rx - rune_sz, ry - rune_sz))

        # ── Boss HP Bar panel (dark fantasy styled) ───────────
        if hp_ease > 0:
            bw   = 560
            bh_p = 36   # panel height
            bx   = cx - bw // 2
            # Slide up from below
            by_base = cy + 90
            by      = int(by_base + 40 * (1.0 - hp_ease))

            # Stone panel background
            panel = pygame.Surface((bw, bh_p + 32), pygame.SRCALPHA)
            panel_alpha = int(hp_ease * 230)

            # Outer glow for phase 2
            if phase_num >= 2:
                pulse = 0.5 + 0.5 * _math.sin(t * 6)
                glow_a = int(hp_ease * 80 * pulse)
                glow = pygame.Surface((bw + 20, bh_p + 52), pygame.SRCALPHA)
                glow.fill((220, 100, 20, glow_a))
                surface.blit(glow, (bx - 10, by - 10))

            # Panel fill (stone dark)
            panel.fill((*DF_STONE, panel_alpha))
            surface.blit(panel, (bx, by))

            # Gold border (outer)
            border_a = int(hp_ease * 255)
            pygame.draw.rect(surface, (*DF_GOLD, border_a),
                             (bx - 1, by - 1, bw + 2, bh_p + 34), 2,
                             border_radius=3)
            # Blood inner border
            pygame.draw.rect(surface, (*DF_BLOOD, border_a),
                             (bx + 2, by + 2, bw - 4, bh_p + 28), 1,
                             border_radius=2)

            # Boss name label row
            boss_hp   = getattr(self.boss_entity, "hp",     1)
            boss_maxhp = getattr(self.boss_entity, "max_hp", boss_hp) or 1
            hp_ratio  = max(0.0, min(1.0, boss_hp / boss_maxhp))

            lbl = hp_font.render(boss_name, True, DF_GOLD2)
            lbl.set_alpha(border_a)
            surface.blit(lbl, (bx + 10, by + 5))

            ph_tag_str = f"  [ PHASE {phase_num} ]"
            ph_tag_col = (220, 120, 40) if phase_num >= 2 else DF_SILVER
            ph_tag = hp_font.render(ph_tag_str, True, ph_tag_col)
            ph_tag.set_alpha(border_a)
            surface.blit(ph_tag, (bx + 10 + lbl.get_width(), by + 5))

            # HP numbers right-aligned
            hp_txt = hp_font.render(f"{boss_hp} / {boss_maxhp}", True, DF_SILVER)
            hp_txt.set_alpha(border_a)
            surface.blit(hp_txt, (bx + bw - hp_txt.get_width() - 10, by + 5))

            # HP bar track
            bar_y    = by + 26
            bar_x    = bx + 8
            bar_fill_w = bw - 16
            bar_fh   = 16

            # Track bg
            track = pygame.Surface((bar_fill_w, bar_fh), pygame.SRCALPHA)
            track.fill((20, 10, 10, int(hp_ease * 220)))
            surface.blit(track, (bar_x, bar_y))

            # Fill gradient (blood red → dark orange near 0)
            filled_w = int(bar_fill_w * hp_ratio * hp_ease)
            if filled_w > 0:
                for px in range(filled_w):
                    frac   = px / max(1, bar_fill_w)
                    # color: deep crimson left, brighter red right
                    r = int(160 + 80 * frac)
                    g = int(20  + 20 * (1 - frac))
                    b = 10
                    fill_col = (r, g, b, int(hp_ease * 220))
                    fs = pygame.Surface((1, bar_fh), pygame.SRCALPHA)
                    fs.fill(fill_col)
                    surface.blit(fs, (bar_x + px, bar_y))

            # Segment markers at 25/50/75%
            for seg in [0.25, 0.5, 0.75]:
                mx = bar_x + int(bar_fill_w * seg)
                ms = pygame.Surface((2, bar_fh), pygame.SRCALPHA)
                ms.fill((0, 0, 0, int(hp_ease * 160)))
                surface.blit(ms, (mx, bar_y))

            # Bar border
            pygame.draw.rect(surface, (*DF_GOLD, int(hp_ease * 180)),
                             (bar_x - 1, bar_y - 1, bar_fill_w + 2, bar_fh + 2), 1)

    def _draw_boss_ready_overlay(self, surface):
        """1.5-second 'GET READY!' freeze overlay after boss cinematic ends."""
        import math as _math
        t  = self.boss_ready_timer   # counts DOWN 1.5 → 0
        if t <= 0:
            return
        total = 1.5
        prog  = 1.0 - t / total      # 0 → 1 over the 1.5 s

        DF_GOLD   = (212, 175, 55)
        DF_GOLD2  = (255, 225, 100)
        DF_BLOOD  = (140, 20, 20)
        cx = SCREEN_W // 2
        cy = SCREEN_H // 2

        # ── Dark overlay ──────────────────────────────────────
        ov_alpha = int(min(160, 160 * min(1.0, prog / 0.2)))
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, ov_alpha))
        surface.blit(ov, (0, 0))

        # ── Gold/blood cinematic bars ─────────────────────────
        bar_h   = 36
        bar_alpha = int(min(240, prog / 0.15 * 240))
        for by, col in [(0, DF_BLOOD), (SCREEN_H - bar_h, DF_BLOOD)]:
            bs = pygame.Surface((SCREEN_W, bar_h), pygame.SRCALPHA)
            bs.fill((*col, bar_alpha))
            surface.blit(bs, (0, by))
        # Gold trim
        for by in [bar_h, SCREEN_H - bar_h - 1]:
            ts = pygame.Surface((SCREEN_W, 2), pygame.SRCALPHA)
            ts.fill((*DF_GOLD, bar_alpha))
            surface.blit(ts, (0, by))

        # ── "GET READY!" text ─────────────────────────────────
        try:
            big_font = pygame.font.SysFont("impact", 72)
            sub_font = pygame.font.SysFont("impact", 22)
        except Exception:
            big_font = pygame.font.Font(None, 82)
            sub_font = pygame.font.Font(None, 26)

        # Pulse scale effect on text
        pulse  = 1.0 + 0.04 * _math.sin(prog * _math.pi * 6)
        fade_a = int(min(255, prog / 0.25 * 255))

        # Shadow
        shd = big_font.render("GET READY!", True, (0, 0, 0))
        shd.set_alpha(int(fade_a * 0.6))
        surface.blit(shd, (cx - shd.get_width() // 2 + 4, cy - 36 + 4))
        # Gold main text
        grt = big_font.render("GET READY!", True, DF_GOLD2)
        grt.set_alpha(fade_a)
        surface.blit(grt, (cx - grt.get_width() // 2, cy - 36))

        # ── Countdown sub-text ────────────────────────────────
        if prog > 0.2:
            sub_a   = int(min(200, (prog - 0.2) / 0.2 * 200))
            seconds = max(0.0, t)
            sub_str = f"Battle begins in  {seconds:.1f}s"
            sub     = sub_font.render(sub_str, True, (200, 190, 160))
            sub.set_alpha(sub_a)
            surface.blit(sub, (cx - sub.get_width() // 2, cy + 28))

        # ── Decorative rule ───────────────────────────────────
        if prog > 0.3:
            rule_a = int(min(200, (prog - 0.3) / 0.3 * 200))
            rule_w = int(min(360, 360 * (prog - 0.3) / 0.4))
            for ry in [cy - 46, cy + 22]:
                rs = pygame.Surface((rule_w, 2), pygame.SRCALPHA)
                rs.fill((*DF_GOLD, rule_a))
                surface.blit(rs, (cx - rule_w // 2, ry))

    def _draw_boss_death_overlay(self, surface):
        """'BOSS DEFEATED!' flash overlay (first 2 s of death timer)."""
        t = self.boss_death_timer       # counts DOWN 3.2 → 0
        if t <= 0 or t > 2.8:
            return
        # Show text from t=2.8 down to 0 with fade
        alpha = int(255 * min(1.0, t / 0.6))     # fade out in last 0.6 s
        try:
            big_font = pygame.font.SysFont("Arial", 58, bold=True)
            sub_font = pygame.font.SysFont("Arial", 24, bold=True)
        except Exception:
            big_font = pygame.font.Font(None, 66)
            sub_font = pygame.font.Font(None, 28)

        # Golden flash tint
        flash = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        flash.fill(pygame.Color(255, 200, 40, max(0, min(255, int(alpha * 0.25)))))
        surface.blit(flash, (0, 0))

        txt   = "BOSS DEFEATED!"
        shd   = big_font.render(txt, True, (0, 0, 0))
        shd.set_alpha(alpha)
        main  = big_font.render(txt, True, (255, 230, 50))
        main.set_alpha(alpha)
        cx    = SCREEN_W // 2
        cy    = SCREEN_H // 2 - 30
        surface.blit(shd, (cx - shd.get_width() // 2 + 4, cy + 4))
        surface.blit(main, (cx - main.get_width() // 2, cy))

        sub   = sub_font.render("— stage cleared —", True, (200, 200, 255))
        sub.set_alpha(alpha)
        surface.blit(sub, (cx - sub.get_width() // 2, cy + 64))

    def _draw_boss_death_particles(self, surface):
        """Draw world-space explosion particles for boss death."""
        cam_x = self.stage.cam_x
        cam_y = self.stage.cam_y
        for _p in self.boss_death_particles:
            life_frac = _p["life"] / _p["max_life"]
            alpha     = int(255 * life_frac)
            sz        = max(2, int(_p["size"] * life_frac))
            sx        = int(_p["x"] - cam_x)
            sy        = int(_p["y"] - cam_y)
            if -sz <= sx <= SCREEN_W + sz and -sz <= sy <= SCREEN_H + sz:
                ps = pygame.Surface((sz * 2 + 2, sz * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(ps, (*_p["color"], alpha), (sz + 1, sz + 1), sz)
                surface.blit(ps, (sx - sz - 1, sy - sz - 1))

    # ── Main loop ────────────────────────────────────────────
    def run(self):
        while self.running:
            dt        = self.clock.tick(FPS) / 1000.0
            dt        = min(dt, 0.05)
            mouse_pos = pygame.mouse.get_pos()

            self._dt = dt
            self._mouse_pos = mouse_pos
            self._handle_events(mouse_pos)
            self._update(dt, mouse_pos)
            self._render(mouse_pos, dt)
            pygame.display.flip()

    # ── Events ───────────────────────────────────────────────
    def _handle_events(self, mouse_pos):
        self._frame_events = []
        for event in pygame.event.get():
            self._frame_events.append(event)
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                self._on_key(event.key)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._on_click(event.pos, event.button)

            elif event.type == pygame.MOUSEWHEEL:
                if self.state == STATE_RANGE:
                    self.range_screen.handle_scroll(event.y)
                elif self.state == STATE_INVENTORY:
                    self.inv_screen.handle_scroll(-event.y, self.player)

    def _on_key(self, key):
        if key == pygame.K_ESCAPE:
            if self.state == STATE_RANGE:
                self.change_state(STATE_MENU)
            elif self.state == STATE_PLAYING:
                self.change_state(STATE_PAUSED)
            elif self.state == STATE_INVENTORY:
                self.change_state(STATE_PLAYING)
            elif self.state in (STATE_PAUSED, STATE_SHOP):
                self.change_state(STATE_PLAYING)

        elif key == pygame.K_TAB:
            if self.state == STATE_PLAYING:
                self.change_state(STATE_INVENTORY)
            elif self.state == STATE_INVENTORY:
                self.change_state(STATE_PLAYING)

        elif key == pygame.K_e:
            if self.state == STATE_PLAYING:
                self._try_pickup()

        elif key == pygame.K_SPACE:
            if self.state == STATE_PLAYING:
                self._use_skill(0)

        elif key == pygame.K_f:
            if self.state == STATE_PLAYING:
                self._use_skill(1)

        elif key == pygame.K_r:
            if self.state == STATE_PLAYING:
                self._use_skill(2)

        elif key == pygame.K_F11:
            self._toggle_fullscreen()

        elif key == pygame.K_m:
            on = self.sfx.toggle()
            # brief visual notice (only when playing)
            if self.state == STATE_PLAYING and self.player:
                msg = "🔊 Sound ON" if on else "🔇 Sound OFF"
                self._add_fx(SCREEN_W // 2, 80, msg, (220, 220, 80), 20)

    def _toggle_fullscreen(self):
        self._fullscreen = not self._fullscreen
        if self._fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

    def _use_skill(self, idx=0):
        """Trigger skill at slot idx (0=Q Dash, 1=F Star Shot, 2=R Frenzy)."""
        from constants import CLASS_SKILLS
        p = self.player
        if not p or not p.alive:
            return
        skills = CLASS_SKILLS.get(p.char_class, [])
        if idx >= len(skills):
            return
        skill_cfg = skills[idx]
        if p.skill_cd[idx] > 0:
            self._add_fx(p.x, p.y - 40,
                         f"{skill_cfg['name']} CD: {p.skill_cd[idx]:.1f}s",
                         (160, 160, 160), 14)
            return
        stype = skill_cfg["type"]
        self._handle_skill_new(stype, skill_cfg)
        self.sfx.play_skill(stype)
        p.skill_cd[idx] = skill_cfg["cooldown"]

    def _tick_skill_cd(self, dt):
        if self.player:
            cds = self.player.skill_cd
            if not isinstance(cds, (list, tuple)):
                return
            for i in range(len(cds)):
                if cds[i] > 0:
                    cds[i] = max(0.0, cds[i] - dt)

    def _handle_skill_new(self, stype, cfg):
        """Handle the 3 new Sausage Man skills with visual effects."""
        p = self.player
        col = cfg.get("color", (255, 255, 255))

        # ── DASH ─────────────────────────────────────────────────
        if stype == "dash":
            keys = pygame.key.get_pressed()
            from pygame.locals import K_w, K_a, K_s, K_d, K_UP, K_DOWN, K_LEFT, K_RIGHT
            mdx = int(keys[K_d] or keys[K_RIGHT]) - int(keys[K_a] or keys[K_LEFT])
            mdy = int(keys[K_s] or keys[K_DOWN])  - int(keys[K_w] or keys[K_UP])
            if mdx == 0 and mdy == 0:
                mdx = math.cos(p.facing_angle)
                mdy = math.sin(p.facing_angle)
            d = math.hypot(mdx, mdy) or 1
            mdx /= d; mdy /= d

            # Spawn afterimage ghost trail at old position every 30 px
            walls = self.stage.wall_rects
            steps = 5
            step_dist = 28
            ox, oy = p.x, p.y
            for s in range(1, steps + 1):
                tx = ox + mdx * step_dist * s
                ty = oy + mdy * step_dist * s
                r  = p.RADIUS
                if not any(w.left < tx + r and w.right > tx - r and
                           w.top  < ty + r and w.bottom > ty - r for w in walls):
                    p.x, p.y = tx, ty
                else:
                    break
                # Ghost trail particle
                self._add_fx(tx, ty, "·", col, 20)

            p.iframe_timer = 0.3   # brief invincibility during dash
            self._add_fx(p.x, p.y - 36, "DASH!", col, 22)

        # ── STAR SPREAD ──────────────────────────────────────────
        elif stype == "star_spread":
            from bullet import Bullet
            angle = p.facing_angle
            dmg, crit = p.calc_damage()
            star_dmg = int(dmg * 1.4)
            spd = (p.get_bullet_speed() or 7) * 1.1
            star_col = (255, 220, 60)
            spread_angles = [angle - math.radians(28), angle, angle + math.radians(28)]
            barrel_offset = p.RADIUS + 16
            for a in spread_angles:
                bdx = math.cos(a); bdy = math.sin(a)
                bx = p.x + bdx * barrel_offset
                by = p.y + bdy * barrel_offset
                b = Bullet(bx, by, bdx, bdy, spd, star_dmg,
                           pierce=False, is_crit=False, color=star_col, size=10)
                self.bullets.append(b)
            # Sparkle FX: ring of star texts
            for i in range(8):
                a2 = math.tau / 8 * i
                fx_x = p.x + math.cos(a2) * 40
                fx_y = p.y + math.sin(a2) * 40
                self._add_fx(fx_x, fx_y, "+EXP", (255, 240, 80), 14)
            self._add_fx(p.x, p.y - 40, "STAR SHOT!", col, 22)

        # ── RAPID FIRE (FRENZY) ───────────────────────────────────
        elif stype == "rapid_fire":
            dur = cfg.get("duration", 3.0)
            p._frenzy_timer   = dur
            p._frenzy_mult    = 2.5
            # Burst of lightning sparks around player
            for i in range(10):
                a3 = math.tau / 10 * i
                fx_x = p.x + math.cos(a3) * 48
                fx_y = p.y + math.sin(a3) * 48
                self._add_fx(fx_x, fx_y, "!", col, 19)
            self._add_fx(p.x, p.y - 42, "FRENZY! 3s", col, 24)

    def _handle_skill(self, skill):
        """Legacy skill handler kept for compatibility."""
        if not skill or self.player is None:
            return
        t = skill[0]
        p = self.player

        if t == "whirlwind":
            # Berserker: massive spin damage to all nearby
            dmg  = skill[1]
            cost = skill[2] if len(skill) > 2 else 12
            if cost and not p.use_mana(cost):
                self._add_fx(p.x, p.y - 40, "No Mana!", (100, 100, 255), 18)
                return
            hit = 0
            for e in self.enemies:
                if e.alive and math.hypot(e.x - p.x, e.y - p.y) < 110:
                    actual = e.take_damage(dmg)
                    self._add_fx(e.x, e.y - e.size, f"{actual}", (255, 120, 0))
                    hit += 1
            if hit:
                self._add_fx(p.x, p.y - 50, "WHIRLWIND!", (255, 140, 0), 22)

        elif t == "shield_slam":
            # Knight: push + damage + restore armor
            dmg  = skill[1]
            cost = skill[2] if len(skill) > 2 else 15
            if cost and not p.use_mana(cost):
                self._add_fx(p.x, p.y - 40, "No Mana!", (100, 100, 255), 18)
                return
            for e in self.enemies:
                if e.alive and math.hypot(e.x - p.x, e.y - p.y) < 90:
                    e.take_damage(dmg)
                    # Knockback
                    dx = e.x - p.x; dy = e.y - p.y
                    d = math.hypot(dx, dy) or 1
                    e.x += (dx / d) * 60; e.y += (dy / d) * 60
            p.armor = min(p.max_armor, p.armor + 30)
            self._add_fx(p.x, p.y - 50, "SHIELD SLAM! +30 Armor", (0, 220, 220), 20)

        elif t == "nova_burst":
            # Mage: AoE explosion around player
            dmg, dx, dy = skill[1], skill[2], skill[3]
            cost = skill[4] if len(skill) > 4 else 30
            if cost and not p.use_mana(cost):
                self._add_fx(p.x, p.y - 40, "No Mana!", (100, 100, 255), 18)
                return
            hit = 0
            for e in self.enemies:
                if e.alive and math.hypot(e.x - p.x, e.y - p.y) < 140:
                    actual = e.take_damage(int(dmg * 1.5))
                    self._add_fx(e.x, e.y - e.size, f"{actual}", (180, 80, 255))
                    hit += 1
            self._add_fx(p.x, p.y - 50, f"NOVA BURST! ({hit} hit)", (160, 60, 255), 22)

        elif t == "death_bolt":
            # Necromancer: homing bolt to nearest enemy
            dmg = skill[1]
            cost = skill[2] if len(skill) > 2 else 25
            if cost and not p.use_mana(cost):
                self._add_fx(p.x, p.y - 40, "No Mana!", (100, 100, 255), 18)
                return
            nearest = None
            best_d  = 9999
            for e in self.enemies:
                if e.alive:
                    d = math.hypot(e.x - p.x, e.y - p.y)
                    if d < best_d:
                        best_d = d; nearest = e
            if nearest:
                dx = nearest.x - p.x; dy = nearest.y - p.y
                dist = math.hypot(dx, dy) or 1
                b = Bullet(p.x, p.y, dx / dist, dy / dist, 10, dmg, pierce=False, is_crit=True)
                b._homing_target = nearest
                self.bullets.append(b)
                self._add_fx(p.x, p.y - 40, "DEATH BOLT!", (60, 220, 120), 20)

        elif t == "triple_shot":
            # Ranger: 3 arrows spread
            dmg, angle = skill[1], skill[2]
            cost = skill[3] if len(skill) > 3 else 10
            if cost and not p.use_mana(cost):
                self._add_fx(p.x, p.y - 40, "No Mana!", (100, 100, 255), 18)
                return
            for offset in (-0.25, 0, 0.25):
                dx = math.cos(angle + offset)
                dy = math.sin(angle + offset)
                self.bullets.append(Bullet(p.x, p.y, dx, dy, 9, dmg))
            self._add_fx(p.x, p.y - 40, "TRIPLE SHOT!", (80, 255, 80), 20)

        elif t == "smoke_dash":
            # Rogue: dash through enemies dealing damage + iframes
            dmg  = skill[1]
            angle = p.facing_angle
            cost = skill[2] if len(skill) > 2 else 18
            if cost and not p.use_mana(cost):
                self._add_fx(p.x, p.y - 40, "No Mana!", (100, 100, 255), 18)
                return
            dash_dist = 120
            dx = math.cos(angle) * dash_dist
            dy = math.sin(angle) * dash_dist
            p.x += dx; p.y += dy
            p.iframe_timer = 0.5   # 0.5s invincibility
            hit = 0
            for e in self.enemies:
                if e.alive and math.hypot(e.x - p.x, e.y - p.y) < 60:
                    e.take_damage(dmg)
                    hit += 1
            self._add_fx(p.x, p.y - 50, f"SMOKE DASH! ({hit} hit)", (80, 160, 255), 22)

    def _on_click(self, pos, button):
        if self.state == STATE_PLAYING:
            # HUD pause button click
            pb = getattr(self, "_hud_pause_btn", None)
            if pb and pb.collidepoint(pos):
                self.change_state(STATE_PAUSED)
                return

        if self.state == STATE_MENU:
            result = self.menu_screen.handle_click(pos)
            if result == "play":
                self.sfx.play("menu_click")
                self._start_new_game("Sausage Man")
            elif result == "range":
                self.sfx.play("menu_click")
                self.range_screen._reset()
                self.range_screen.set_player(self.player if self.player else __import__("player").Player("Hero", "Sausage Man"))
                self.change_state(STATE_RANGE)
            elif result == "stats":
                self.sfx.play("menu_click")
                self.tracker.plot_dashboard()
            elif result == "quit":
                self.sfx.play("menu_click")
                self.running = False

        elif self.state == STATE_CLASS_SEL:
            result = self.class_screen.handle_click(pos)
            if result == "back":
                self.change_state(STATE_MENU)
            elif result and result != "back":
                self._start_new_game(result)

        elif self.state == STATE_INVENTORY:
            self.inv_screen.handle_click(pos, self.player)

        elif self.state == STATE_PAUSED:
            result = self.pause_screen.handle_click(pos)
            if result == "resume":
                self.change_state(STATE_PLAYING)
            elif result == "restart":
                self._restart_game()
            elif result == "menu":
                self.change_state(STATE_MENU)

        elif self.state == STATE_SHOP:
            result = self.shop_screen.handle_click(pos, self.player)
            if result == "heal":
                self.sfx.play("heal")
                self._add_fx(SCREEN_W // 2, SCREEN_H // 2 - 40, "+50 HP", GREEN, 22)
            elif result == "buy":
                self.sfx.play("shop_buy")
                self._add_fx(SCREEN_W // 2, SCREEN_H // 2 - 40, "Item Purchased!", GOLD, 22)
            elif result == "reroll":
                self.sfx.play("menu_click")
                cost = self.shop_screen.reroll_cost
                self._add_fx(SCREEN_W // 2, SCREEN_H // 2 - 40,
                             f"Shop Rerolled! Next: {cost}G", CYAN, 20)
            elif result == "leave":
                self.sfx.play("menu_click")
                self._next_stage()   # FIX: method now defined below

        elif self.state == STATE_RANGE:
            mouse_buttons = pygame.mouse.get_pressed()
            mouse_buttons = pygame.mouse.get_pressed()
            self.range_screen.update(self._dt, self._frame_events, self._mouse_pos, mouse_buttons)
            result = self.range_screen.handle_click(pos)
            if result == "menu":
                self.change_state(STATE_MENU)

        elif self.state in (STATE_GAME_OVER, STATE_VICTORY):
            result = self.over_screen.handle_click(pos)
            if result == "menu":
                self.change_state(STATE_MENU)
            elif result == "restart":
                self._restart_game()

    # ── State management ─────────────────────────────────────
    def change_state(self, new_state):
        self.state = new_state

    # ── New game ─────────────────────────────────────────────
    def _restart_game(self):
        """Restart with the same class from stage 1."""
        if self.player:
            char_class = self.player.char_class
            self._start_new_game(char_class)

    def _start_new_game(self, char_class):
        self.player    = Player(self.player_name, char_class)
        self.stage_idx = 0
        self.kills     = 0
        self.score     = 0
        self.run_time  = 0.0
        self.player.gold = 60
        self._load_stage(0)
        self.tracker.start_run(self.player)
        self.change_state(STATE_PLAYING)

    def _load_stage(self, idx):
        self.stage    = Stage(idx)
        start_room    = self.stage.rooms[0]
        self.player.x = float(start_room.cx)
        self.player.y = float(start_room.cy)
        self.enemies   = self.stage.spawn_enemies(stage_level=idx + 1, skip_room=start_room)
        self.bullets   = []
        self.e_bullets = []
        self.drops     = []
        self.fx        = []
        self.portal    = None   # clear portal from previous stage
        self._last_enemy_pos = (float(start_room.cx), float(start_room.cy))
        # Assign each enemy a home_room so they stay in their own room
        for e in self.enemies:
            e.home_room = self.stage.get_room_at(e.x, e.y)
        # ── Detect boss for this stage ────────────────────────
        from enemy import BossEnemy as _BE
        self.boss_entity      = None
        self.boss_spawn_timer = 0.0
        self.boss_ready_timer = 0.0
        self.boss_death_timer = 0.0
        self.boss_death_particles = []
        self.boss_unlock_flash  = 0.0   # screen-flash timer when boss door opens
        self.boss_door_arrow_t  = 0.0   # how long to show the direction arrow
        self.cam_pan_timer      = 0.0   # camera pan to boss door timer
        for e in self.enemies:
            if isinstance(e, _BE):
                self.boss_entity = e
                break
        # ── Fallback: ถ้าหาบอสไม่เจอ (เช่น boss_room ไม่ถูก assign) ให้ force-spawn ──
        if self.boss_entity is None:
            from constants import STAGE_CONFIGS
            from enemy import make_enemy
            cfg = STAGE_CONFIGS[idx] if idx < len(STAGE_CONFIGS) else STAGE_CONFIGS[-1]
            boss_type = cfg.get("boss", "Elder Treant")
            boss_room = self.stage.boss_room
            if boss_room is None:
                # เลือกห้องที่ใหญ่สุด — แต่ห้ามเป็น rooms[0] (spawn room)
                non_start = self.stage.rooms[1:]
                candidates = non_start if non_start else self.stage.rooms
                boss_room = max(candidates, key=lambda r: r.rect.w * r.rect.h)
                boss_room.is_boss = True
                self.stage.boss_room = boss_room
            new_boss = make_enemy(boss_type, float(boss_room.cx), float(boss_room.cy), idx + 1)
            new_boss.home_room = boss_room
            self.enemies.append(new_boss)
            self.boss_entity = new_boss

        # ── Lock boss room door until all other rooms are cleared ─
        # IMPORTANT: call close_room_doors() FIRST (while doors_open=True) so
        # door_rects get added to wall_rects for solid collision. Then set locked.
        if self.stage.boss_room:
            self.stage.close_room_doors(self.stage.boss_room)
            self.stage.boss_room.door_locked = True

    def _push_enemies_from_doors(self, room):
        """Before closing doors: nudge any enemy on a door tile toward room centre."""
        from constants import TILE
        for dr in room.door_rects:
            dr_cx = dr.x + dr.w / 2
            dr_cy = dr.y + dr.h / 2
            for e in self.enemies:
                if not e.alive:
                    continue
                if (abs(e.x - dr_cx) < e.size + TILE and
                        abs(e.y - dr_cy) < e.size + TILE):
                    dx = room.cx - e.x
                    dy = room.cy - e.y
                    dist = math.hypot(dx, dy) or 1
                    e.x += (dx / dist) * (TILE * 2.0 + e.size)
                    e.y += (dy / dist) * (TILE * 2.0 + e.size)

    # ── Item pickup ──────────────────────────────────────────
    def _try_pickup(self):
        """Soul Knight-style pickup: swap weapons on the ground, equip better gear.
        Also handles health fountain interaction."""
        p = self.player

        # ── Fountain interaction (E near fountain) ────────────
        cur_room = self.stage.get_room_at(p.x, p.y)
        if cur_room and cur_room.near_fountain(p):
            healed = cur_room.use_fountain(p)
            if healed > 0:
                self._add_fx(p.x, p.y - 40, f"+{healed} HP", (255, 80, 80), 22)
                self._add_fx(p.x, p.y - 65, "HEALED!", (255, 160, 160), 16)
                self.sfx.play("heal")
            return

        best_drop = None
        best_dist = 9999
        for d in self.drops:
            if d.alive and d.can_pickup(p):
                dist = math.hypot(d.x - p.x, d.y - p.y)
                if dist < best_dist:
                    best_dist = dist
                    best_drop = d

        if best_drop is None:
            return

        itm  = best_drop.item
        slot = itm.item_type

        # Soul Knight weapon swap: always equip, drop old weapon back on ground
        old = p.equipment.get(slot)
        p.equip(itm)

        if old is not None:
            self.drops.append(DroppedItem(old, best_drop.x + 20, best_drop.y + 20))
            from constants import RARITY_COLORS
            col = RARITY_COLORS.get(itm.rarity, WHITE)
            self._add_fx(p.x, p.y - 30, f"SWAP -> {itm.name}!", col, 17)
        else:
            from constants import RARITY_COLORS
            col = RARITY_COLORS.get(itm.rarity, WHITE)
            self._add_fx(p.x, p.y - 30, f"[EQUIPPED] {itm.name}!", col, 17)

        self.tracker.log_event("item_pickup", {"rarity": itm.rarity})
        self.sfx.play("item_pickup")
        best_drop.alive = False
        self.drops.remove(best_drop)

    # ── Stage progression ────────────────────────────────────
    def _open_shop(self):
        self.shop_screen = ShopScreen(self.stage_idx, self.player.char_class)
        self.change_state(STATE_SHOP)

    def _next_stage(self):
        """FIX: was called but never defined."""
        self.tracker.log_event("stage_clear", {"stage": self.stage_idx + 1})
        self.stage_idx += 1
        if self.stage_idx >= len(STAGE_CONFIGS):
            # All stages cleared — victory!
            self.tracker.end_run("victory", self.player)
            self.change_state(STATE_VICTORY)
        else:
            self._load_stage(self.stage_idx)
            self.change_state(STATE_PLAYING)

    # ── Floating text helper ──────────────────────────────────
    def _add_fx(self, x, y, msg, color, size=18):
        self.fx.append(FloatingText(x, y, msg, color, size))

    # ── Update ───────────────────────────────────────────────
    def _update(self, dt, mouse_pos):
        if self.state != STATE_PLAYING:
            return

        # ── Boss cinematic freeze ──────────────────────────────
        # During boss_spawn_timer: full freeze (cinematic playing)
        # During boss_ready_timer: freeze + "GET READY!" overlay
        if self.boss_spawn_timer > 0:
            self.sfx.update(dt)
            self.boss_spawn_timer = max(0.0, self.boss_spawn_timer - dt)
            if self.boss_spawn_timer <= 0:
                self.boss_ready_timer = 1.5   # start "GET READY" freeze
            return
        if self.boss_ready_timer > 0:
            self.sfx.update(dt)
            self.boss_ready_timer = max(0.0, self.boss_ready_timer - dt)
            return

        p     = self.player
        walls = self.stage.wall_rects
        cam_x = self.stage.cam_x
        cam_y = self.stage.cam_y

        # Tick run timer
        self.run_time += dt
        self._tick_skill_cd(dt)
        self.sfx.update(dt)

        world_mouse = (mouse_pos[0] + cam_x, mouse_pos[1] + cam_y)

        # Player update — freeze movement during boss-door cinematic pan
        _in_pan = getattr(self, 'cam_pan_timer', 0.0) > 0
        if _in_pan:
            p.update(dt, walls, world_mouse, frozen=True)   # regen still ticks; no movement
        else:
            p.update(dt, walls, world_mouse)
        # ── Camera: cinematic pan to boss door on unlock ──────────
        pan_t = getattr(self, 'cam_pan_timer', 0.0)
        PAN_DUR = 6.0   # total cinematic length (seconds)
        SLIDE   = 1.5   # slide-in duration
        HOLD    = 3.0   # hold-at-boss-door duration
        SLIDE_B = PAN_DUR - SLIDE - HOLD  # slide-back duration (1.5 s)

        if pan_t > 0 and self.stage.boss_room:
            bx, by = self.stage.boss_room.cx, self.stage.boss_room.cy
            px0, py0 = getattr(self, '_pan_origin', (p.x, p.y))

            if pan_t > HOLD + SLIDE_B:                   # ── sliding TO boss ──
                frac = (PAN_DUR - pan_t) / SLIDE
                frac = max(0.0, min(1.0, frac))
                frac = frac * frac * (3 - 2 * frac)      # smoothstep
                vx = px0 + (bx - px0) * frac
                vy = py0 + (by - py0) * frac
                # Shake burst the moment we arrive (one-shot)
                if frac >= 0.98 and not getattr(self, '_pan_arrived_shake', False):
                    self.shake_timer = 0.55
                    self.shake_mag   = 14
                    self._pan_arrived_shake = True

            elif pan_t > SLIDE_B:                        # ── holding at boss ──
                vx, vy = bx, by
                # Pulse shake while holding to feel alive
                if not hasattr(self, '_pan_hold_shake_cd'):
                    self._pan_hold_shake_cd = 0.0
                self._pan_hold_shake_cd -= dt
                if self._pan_hold_shake_cd <= 0:
                    self.shake_timer = 0.18
                    self.shake_mag   = 5
                    self._pan_hold_shake_cd = 0.8

            else:                                        # ── sliding BACK ──
                frac = pan_t / SLIDE_B
                frac = max(0.0, min(1.0, frac))
                frac = frac * frac * (3 - 2 * frac)
                vx = p.x + (bx - p.x) * frac
                vy = p.y + (by - p.y) * frac

            self.stage.update_camera(vx, vy)
        else:
            self.stage.update_camera(p.x, p.y)
            # Clean up one-shot flags when pan ends
            self._pan_arrived_shake = False
            if hasattr(self, '_pan_hold_shake_cd'):
                del self._pan_hold_shake_cd
        self.stage.update(dt)

        # ── Room door / fountain management ───────────────────
        cur_room = self.stage.get_room_at(p.x, p.y)
        if cur_room:
            cur_room.visited = True   # mark visited as soon as player steps in
            alive_in_room = cur_room.enemies_alive_in(self.enemies)
            if alive_in_room:
                # FIX 1: don't close if player is still standing in the doorway
                player_in_doorway = any(
                    dr.inflate(p.RADIUS * 2, p.RADIUS * 2).collidepoint(p.x, p.y)
                    for dr in cur_room.door_rects
                )
                if not player_in_doorway:
                    # FIX 2: push any enemy that overlaps a door tile into the room
                    #         so they never get clipped inside the wall
                    for e in self.enemies:
                        if not e.alive:
                            continue
                        for dr in cur_room.door_rects:
                            if math.hypot(e.x - dr.centerx, e.y - dr.centery) < e.size + 24:
                                # Nudge toward room centre
                                ddx = cur_room.cx - e.x
                                ddy = cur_room.cy - e.y
                                dist = math.hypot(ddx, ddy) or 1
                                e.x += (ddx / dist) * (e.size + 28)
                                e.y += (ddy / dist) * (e.size + 28)
                    self.stage.close_room_doors(cur_room)
                    # Soul Knight: activate all enemies in this room now
                    for e in self.enemies:
                        if e.alive and not e.activated:
                            hr = getattr(e, "home_room", None)
                            if hr is cur_room:
                                e.activated = True
                                # ── Boss spawn cinematic ───────────────
                                from enemy import BossEnemy as _BE
                                if isinstance(e, _BE):
                                    self.boss_spawn_timer = 3.0
            else:
                if not cur_room.doors_open:
                    self.stage.open_room_doors(cur_room)
                cur_room.cleared = True

        # ── Boss room: unlock when all other rooms are cleared ───
        boss_room = self.stage.boss_room
        if boss_room and getattr(boss_room, 'door_locked', False):
            non_boss = [r for r in self.stage.rooms if not r.is_boss]
            if all(r.cleared for r in non_boss):
                boss_room.door_locked = False
                self.stage.open_room_doors(boss_room)
                self._add_fx(boss_room.cx, boss_room.cy - 80,
                             "BOSS ROOM UNLOCKED!", (255, 200, 50), 26)
                self.sfx.play("portal_open")
                # Cinematic camera pan — 6-second dramatic sweep
                self.cam_pan_timer      = 6.0
                self.boss_unlock_flash  = 5.5   # flash lasts longer
                self.boss_door_arrow_t  = 9.0   # arrow shows 9 s
                self._pan_origin        = (p.x, p.y)   # remember where player was
                self._pan_arrived_shake = False
            else:
                # แสดง warning เมื่อเข้าใกล้ประตู boss room ที่ยัง locked
                if boss_room.door_rects:
                    for dr in boss_room.door_rects:
                        if math.hypot(p.x - dr.centerx, p.y - dr.centery) < 80:
                            remaining = sum(1 for r in non_boss if not r.cleared)
                            if not getattr(self, '_boss_lock_warn_cd', 0) > 0:
                                self._add_fx(p.x, p.y - 54,
                                             f"Clear {remaining} more room(s) first!",
                                             (255, 180, 40), 18)
                                self._boss_lock_warn_cd = 2.0
                            break

        # ── Tick boss lock warning cooldown ──────────────────────
        if getattr(self, '_boss_lock_warn_cd', 0) > 0:
            self._boss_lock_warn_cd = max(0.0, self._boss_lock_warn_cd - dt)

        # ── Tick boss-unlock screen effects ──────────────────────
        if getattr(self, 'boss_unlock_flash', 0) > 0:
            self.boss_unlock_flash = max(0.0, self.boss_unlock_flash - dt * 1.8)
        if getattr(self, 'cam_pan_timer', 0) > 0:
            self.cam_pan_timer = max(0.0, self.cam_pan_timer - dt)
        if getattr(self, 'boss_door_arrow_t', 0) > 0:
            self.boss_door_arrow_t = max(0.0, self.boss_door_arrow_t - dt)

        # ── ห้องใครห้องมัน: keep enemies inside their home room ──
        from constants import TILE as _TILE
        for e in self.enemies:
            hr = getattr(e, "home_room", None)
            if hr is None or hr.doors_open or not hr.door_rects:
                continue
            # If enemy drifted onto (or through) a closed door tile, push back
            for dr in hr.door_rects:
                if math.hypot(e.x - dr.centerx, e.y - dr.centery) < e.size + _TILE:
                    ddx = hr.cx - e.x
                    ddy = hr.cy - e.y
                    dist = math.hypot(ddx, ddy) or 1
                    e.x += (ddx / dist) * (_TILE + e.size)
                    e.y += (ddy / dist) * (_TILE + e.size)
                    break

        # ── Shooting / melee input ────────────────────────────
        # FIX: shoot_cooldown always ticks — moved outside if/else
        if p.shoot_cooldown > 0:
            p.shoot_cooldown -= dt

        # ── Shooting / melee input ────────────────────────────
        # FIX: shoot_cooldown always ticks — moved outside if/else
        if p.shoot_cooldown > 0:
            p.shoot_cooldown -= dt

        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:
            wpn = p.weapon
            if wpn and not wpn.is_melee:
                # Ranged attack
                frenzy_mult = getattr(p, '_frenzy_mult', 1.0) if getattr(p, '_frenzy_timer', 0) > 0 else 1.0
                if p.shoot_cooldown <= 0:
                    wpn = p.weapon
                    mana_cost = wpn.mana_cost if wpn and hasattr(wpn, "mana_cost") else 2
                    if not p.can_use_mana(mana_cost):
                        # Flash "No Mana!" once (not every frame)
                        if not getattr(p, '_no_mana_fx_cd', 0) > 0:
                            self._add_fx(p.x, p.y - 45, "No Mana!", (80, 120, 255), 16)
                            self.sfx.play("no_mana")
                            p._no_mana_fx_cd = 0.6
                    else:
                        p.use_mana(mana_cost)
                        dmg, crit = p.calc_damage()
                        angle = math.atan2(world_mouse[1] - p.y, world_mouse[0] - p.x)
                        spd   = p.get_bullet_speed() or 7
                        fx    = wpn.effect if hasattr(wpn, 'effect') and wpn.effect else {}
                        pat   = fx.get("pattern", "single")
                        pierce = fx.get("pierce", False) or pat == "pierce"
                        col   = fx.get("bullet_color", (255, 230, 80))
                        bsz   = fx.get("bullet_size", 5)
                        barrel_offset = p.RADIUS + 16

                        def _spawn_bullet(ang, dmg=dmg, crit=crit):
                            dx = math.cos(ang); dy = math.sin(ang)
                            bx = p.x + dx * barrel_offset
                            by = p.y + dy * barrel_offset
                            self.bullets.append(Bullet(bx, by, dx, dy, spd, dmg,
                                                       pierce=pierce, is_crit=crit,
                                                       color=col, size=bsz))

                        sp = lambda a: a + (random.random() - 0.5) * 0.22

                        if pat in ("single", "pierce"):
                            _spawn_bullet(angle)
                        elif pat == "double":
                            _spawn_bullet(angle + 0.09)
                            _spawn_bullet(angle - 0.09)
                        elif pat == "spread3":
                            for i in (-1, 0, 1):
                                _spawn_bullet(angle + i * 0.20)
                        elif pat == "spread5":
                            for i in range(-2, 3):
                                _spawn_bullet(sp(angle + i * 0.15))
                        elif pat == "spread_random":
                            _spawn_bullet(sp(angle))
                        elif pat == "burst3":
                            # Fire first shot now; queue remaining 2 on player
                            _spawn_bullet(angle)
                            p._burst_queue   = 2
                            p._burst_timer   = 0.0
                            p._burst_angle   = angle
                            p._burst_args    = (spd, pierce, col, bsz, barrel_offset)

                        # ── LASER patterns — instant hitscan ──────────
                        elif pat in ("laser", "laser_double"):
                            laser_col     = fx.get("laser_color", col)
                            laser_width   = fx.get("laser_width", 3)
                            laser_life    = fx.get("laser_lifetime", 0.16)
                            laser_range   = 1400          # max beam reach in pixels

                            def _fire_laser_beam(ang):
                                """Cast a ray, deal dmg to all enemies hit, spawn LaserBeam FX."""
                                ddx = math.cos(ang); ddy = math.sin(ang)
                                ox  = p.x + ddx * barrel_offset
                                oy  = p.y + ddy * barrel_offset

                                # --- Ray-march to first wall or map edge ---
                                end_x, end_y = ox + ddx * laser_range, oy + ddy * laser_range
                                step = 12
                                steps_n = int(laser_range / step)
                                hit_wall = False
                                for si in range(1, steps_n + 1):
                                    rx = ox + ddx * step * si
                                    ry = oy + ddy * step * si
                                    for wall in walls:
                                        if wall.collidepoint(rx, ry):
                                            end_x = rx - ddx * step
                                            end_y = ry - ddy * step
                                            hit_wall = True
                                            break
                                    if hit_wall:
                                        break
                                    # Map edge check
                                    from constants import TILE as _T, MAP_W as _MW, MAP_H as _MH
                                    if rx < 0 or rx > _MW * _T or ry < 0 or ry > _MH * _T:
                                        end_x, end_y = rx, ry
                                        break

                                # --- Hit all enemies along the beam ---
                                hit_enemies = set()
                                blen = math.hypot(end_x - ox, end_y - oy)
                                for e in self.enemies:
                                    if not e.alive:
                                        continue
                                    # Project enemy onto beam line
                                    ex = e.x - ox; ey = e.y - oy
                                    t_proj = ex * ddx + ey * ddy
                                    if t_proj < 0 or t_proj > blen:
                                        continue
                                    perp_dist = abs(ex * ddy - ey * ddx)
                                    if perp_dist < e.size + laser_width + 2:
                                        d_val, crit_v = p.calc_damage()
                                        actual = e.take_damage(d_val)
                                        hit_enemies.add(id(e))
                                        c_col  = GOLD if crit_v else WHITE
                                        label  = f"{'CRIT! ' if crit_v else ''}{actual}"
                                        self._add_fx(e.x, e.y - e.size, label, c_col)
                                        self.tracker.log_event("damage", {
                                            "amount": actual, "is_crit": crit_v,
                                            "enemy_type": e.enemy_type
                                        })

                                # Spawn visual beam
                                self.bullets.append(
                                    LaserBeam(ox, oy, end_x, end_y,
                                              color=laser_col,
                                              width=laser_width,
                                              lifetime=laser_life)
                                )

                            _fire_laser_beam(angle)
                            if pat == "laser_double":
                                _fire_laser_beam(angle + 0.09)
                                _fire_laser_beam(angle - 0.09)

                        else:
                            _spawn_bullet(angle)

                        p.shoot_cooldown = (1.0 / max(0.1, p.get_fire_rate())) / frenzy_mult

                        # ── เสียงยิง ───────────────────────────────────────
                        self.sfx.play_shoot(wpn)

                        # ── Per-weapon screen shake ────────────────────
                        shake_mag, shake_dur = fx.get("shake", (3, 0.10))
                        if frenzy_mult > 1.0:
                            shake_mag = int(shake_mag * 1.5)
                            shake_dur = max(shake_dur, 0.12)
                        if shake_mag > 0:
                            self.shake_timer = max(self.shake_timer, shake_dur)
                            self.shake_mag   = max(self.shake_mag,   shake_mag)

        # ── Burst queue flush (burst3 follow-up shots) ─────────
        if getattr(p, '_burst_queue', 0) > 0:
            p._burst_timer -= dt
            if p._burst_timer <= 0:
                spd, pierce, col, bsz, barrel_offset = p._burst_args
                ang = p._burst_angle
                dx = math.cos(ang); dy = math.sin(ang)
                bx = p.x + dx * barrel_offset; by = p.y + dy * barrel_offset
                dmg_b, crit_b = p.calc_damage()
                self.bullets.append(Bullet(bx, by, dx, dy, spd, dmg_b,
                                           pierce=pierce, is_crit=crit_b,
                                           color=col, size=bsz))
                p._burst_queue -= 1
                p._burst_timer  = 0.07

        # ── Player bullets ────────────────────────────────────
        # Figure out which room the player is currently in (may be None = corridor)
        player_room = self.stage.get_room_at(p.x, p.y)

        for b in list(self.bullets):
            b.update(dt, walls)
            if not b.alive:
                self.bullets.remove(b)
                continue

            # LaserBeam is a pure visual — skip collision checks
            if isinstance(b, LaserBeam):
                continue

            # ── ROOM BARRIER: bullet enters a room the player isn't in → stop ──
            bullet_room = self.stage.get_room_at(b.x, b.y)
            if bullet_room is not None and bullet_room is not player_room:
                # Spawn a small spark effect at the boundary and kill the bullet
                self._add_fx(b.x, b.y, "✕", (180, 120, 60), 14)
                b.alive = False
                self.bullets.remove(b)
                continue
            # FIX: bullet → enemy collision
            for e in list(self.enemies):
                if not e.alive:
                    continue
                if id(e) in b.hit_set:
                    continue
                dist = math.hypot(b.x - e.x, b.y - e.y)
                if dist < b.radius + e.size:
                    actual = e.take_damage(b.damage)
                    b.hit_set.add(id(e))
                    col   = GOLD if b.is_crit else WHITE
                    label = f"{'CRIT! ' if b.is_crit else ''}{actual}"
                    self._add_fx(e.x, e.y - e.size, label, col)
                    self.sfx.play("hit_enemy")
                    self.tracker.log_event("damage", {
                        "amount": actual, "is_crit": b.is_crit,
                        "enemy_type": e.enemy_type
                    })
                    if not b.pierce:
                        b.alive = False
                        break

        # ── Enemy bullets ─────────────────────────────────────
        for eb in list(self.e_bullets):
            eb.update(dt, walls)
            if not eb.alive:
                self.e_bullets.remove(eb)
                continue
            # FIX: enemy bullet → player collision
            if math.hypot(eb.x - p.x, eb.y - p.y) < eb.radius + p.RADIUS:
                dmg = p.take_damage(eb.damage)
                eb.alive = False
                if dmg == -1:
                    self._add_fx(p.x, p.y - 30, "DODGE!", CYAN, 20)
                elif dmg >= 0:   # armor-absorbed (0) OR HP lost (>0) — both count as a hit
                    self.sfx.play("hit_player")
                    # ── Screen shake on ANY hit (armor or HP) ─
                    self.shake_timer = 0.28
                    self.shake_mag   = 7
                    # ── Fire-rate boost ────────────────────────
                    if not getattr(p, '_fire_boost_timer', 0) > 0:
                        p.aspd_mult = getattr(p, 'aspd_mult', 1.0) * 1.6
                    p._fire_boost_timer = 3.5

        # ── Enemy update + death ──────────────────────────────
        for e in list(self.enemies):
            e.update(p, walls, dt, self.e_bullets)
            if not e.alive:
                self._last_enemy_pos = (e.x, e.y)   # track for portal spawn
                gold_drop = random.randint(2, 6 + self.stage_idx)
                p.gold += gold_drop
                self._add_fx(e.x, e.y - e.size - 10, f"+{gold_drop}G", GOLD, 15)
                # Mana drop: 35% chance, boss always drops mana
                from enemy import BossEnemy
                is_boss = isinstance(e, BossEnemy)
                mana_roll = random.random()
                if is_boss or mana_roll < 0.60:
                    mana_amt = random.randint(8, 18) if not is_boss else random.randint(25, 40)
                    p.mana = min(p.max_mana, p.mana + mana_amt)
                    self._add_fx(e.x, e.y - e.size - 26, f"+{mana_amt} MP", (80, 160, 255), 15)
                # Drop loot
                itm = e.drop_loot(luk_bonus=0)
                if itm:
                    self.drops.append(DroppedItem(itm, e.x, e.y))
                self.tracker.log_event("kill", {
                    "exp": e.exp_reward,
                    "is_boss": isinstance(e, __import__("enemy").BossEnemy)
                })
                # ── เสียงศัตรูตาย ──────────────────────────────────
                from enemy import BossEnemy as _BE
                if isinstance(e, _BE):
                    self.sfx.play("boss_die")
                    # ✅ mark boss room cleared → minimap turns green + ✔
                    if hasattr(self.stage, "boss_room"):
                        self.stage.boss_room.cleared = True
                    # ── Boss death cinematic ───────────────────────
                    self.boss_death_timer = 3.2
                    self.boss_entity      = None
                    # Spawn explosion particles in world-space
                    import math as _m
                    for _i in range(60):
                        _ang = _m.tau * _i / 60 + random.uniform(-0.12, 0.12)
                        _spd = random.uniform(70, 300)
                        _col = random.choice([
                            (255, 80, 0), (255, 210, 0), (255, 40, 40),
                            (255, 160, 60), (220, 220, 255),
                        ])
                        _life = random.uniform(0.5, 2.5)
                        self.boss_death_particles.append({
                            "x": e.x, "y": e.y,
                            "dx": _m.cos(_ang) * _spd,
                            "dy": _m.sin(_ang) * _spd,
                            "color": _col,
                            "size": random.randint(4, 16),
                            "life": _life,
                            "max_life": _life,
                        })
                    # Big screen shake
                    self.shake_timer = 1.0
                    self.shake_mag   = 18
                else:
                    self.sfx.play("enemy_die")
                self.enemies.remove(e)
                self.kills += 1
                self.score += e.exp_reward * 10

        # ── Drops ─────────────────────────────────────────────
        for d in list(self.drops):
            d.update(dt)

        # ── Portal update & enter ─────────────────────────────
        if self.portal:
            self.portal.update(dt)
            if self.portal.can_enter(p):
                self.portal = None
                self._open_shop()

        # ── Floating text ─────────────────────────────────────
        for f in list(self.fx):
            f.update(dt)
            if not f.alive:
                self.fx.remove(f)

        # ── Screen-shake tick ─────────────────────────────────
        if self.shake_timer > 0:
            self.shake_timer = max(0.0, self.shake_timer - dt)

        # ── Boss cinematic ticks ───────────────────────────────
        if self.boss_death_timer > 0:
            self.boss_death_timer = max(0.0, self.boss_death_timer - dt)
            # Move particles in world space
            for _p in self.boss_death_particles:
                _p["x"]   += _p["dx"] * dt
                _p["y"]   += _p["dy"] * dt
                _p["life"] -= dt
            self.boss_death_particles = [
                _p for _p in self.boss_death_particles if _p["life"] > 0
            ]

        # ── Boss clear overlay tick ────────────────────────────
        if self.boss_clear_timer > 0:
            self.boss_clear_timer = max(0.0, self.boss_clear_timer - dt)

        # ── Fire-rate boost tick ───────────────────────────────
        if hasattr(p, '_fire_boost_timer') and p._fire_boost_timer > 0:
            p._fire_boost_timer -= dt
            if p._fire_boost_timer <= 0:
                p.aspd_mult = max(1.0, p.aspd_mult / 1.6)

        # ── No-mana FX cooldown tick ───────────────────────────
        if hasattr(p, '_no_mana_fx_cd') and p._no_mana_fx_cd > 0:
            p._no_mana_fx_cd = max(0.0, p._no_mana_fx_cd - dt)

        # ── Frenzy timer tick ──────────────────────────────────
        if hasattr(p, '_frenzy_timer') and p._frenzy_timer > 0:
            p._frenzy_timer = max(0.0, p._frenzy_timer - dt)
            if p._frenzy_timer <= 0:
                p._frenzy_mult = 1.0
                self._add_fx(p.x, p.y - 40, "Frenzy ended", (180, 100, 30), 14)

        # ── Player death ──────────────────────────────────────
        if not p.alive:
            # FIX: call end_run so stats are saved
            self.sfx.play("player_die")
            self.tracker.end_run("death", p)
            self.change_state(STATE_GAME_OVER)

        # ── Stage completion: spawn portal on last enemy ───────
        if self.enemies == [] and self.state == STATE_PLAYING and self.portal is None:
            if self.stage.check_completion([]):
                px, py = self._last_enemy_pos
                self.portal = Portal(px, py)
                self._add_fx(px, py - 50, "PORTAL OPENED!", (200, 120, 255), 22)
                self.sfx.play("portal_open")

    # ── Render ───────────────────────────────────────────────
    def _draw_boss_unlock_fx(self, surface):
        """
        Dark-fantasy boss-door unlock cinematic — matches main menu / pause palette.

        Timeline (PAN_DUR = 6 s, counts DOWN):
          6.0 → 4.5  SLIDE_IN  : camera sweeps to boss door
                                  banner = 'THE DOOR IS OPENING...'
                                  (real door tiles visible in background, split-open anim)
          4.5 → 1.5  HOLD      : camera rests at boss door
                                  banner = 'ALL ROOMS CLEARED'
          1.5 → 0    SLIDE_BACK: camera returns to player
                                  banner = 'GET READY FOR BATTLE'

        NOTE FOR FUTURE PROMPTS
        -----------------------
        • All rendered strings use ASCII only — no Unicode emoji/symbols
          (⚔ ⚡ ★ ◆ → etc. render as squares on most system fonts).
        • Dark-fantasy palette tokens: DF_BG, DF_GOLD, DF_BLOOD, DF_STONE,
          DF_BONE, DF_SILVER — keep consistent with ui.py and boss HP bar.
        • Letterbox bars: 80 px top + bottom, gold inner edge, ease in/out 0.4 s.
        • NO fake door graphic overlay — the camera pans to show the real boss-door
          tiles which have their own split-open animation in stage.py.
          Do NOT add a door graphic block here in the future.
        """
        import math as _math

        pan_t   = getattr(self, 'cam_pan_timer', 0.0)
        flash_a = getattr(self, 'boss_unlock_flash', 0.0)
        if pan_t <= 0 and flash_a <= 0:
            return

        # ── Timing constants ──────────────────────────────────────
        PAN_DUR  = 6.0
        SLIDE    = 1.5   # camera slides to door
        HOLD     = 3.0   # camera holds at door
        SLIDE_B  = PAN_DUR - SLIDE - HOLD   # = 1.5 s return slide
        t_now    = pygame.time.get_ticks() / 1000.0
        w, h     = surface.get_size()

        # ── Dark-fantasy palette (mirrors ui.py tokens) ───────────
        DF_BG      = (10,   7,   4)
        DF_BG2     = (20,  14,   8)
        DF_GOLD    = (200, 165,  80)
        DF_GOLD_B  = (240, 205, 100)
        DF_GOLD_D  = (110,  82,  30)
        DF_BLOOD   = (160,  32,  32)
        DF_BLOOD_B = (210,  55,  40)
        DF_CRIMSON = (110,  18,  18)
        DF_STONE   = (38,   30,  22)
        DF_STONE2  = (58,   46,  30)
        DF_BONE    = (210, 195, 165)
        DF_SILVER  = (170, 162, 148)
        DF_PARCH   = (185, 165, 130)

        # ── Phase flags ───────────────────────────────────────────
        in_slide_in   = pan_t > SLIDE_B + HOLD          # 6.0 → 4.5
        in_hold       = SLIDE_B < pan_t <= SLIDE_B + HOLD  # 4.5 → 1.5
        in_slide_back = pan_t <= SLIDE_B                # 1.5 → 0

        # ── Global fade-in/out alpha ──────────────────────────────
        b_alpha = 1.0
        if pan_t > PAN_DUR - 0.35:
            b_alpha = (PAN_DUR - pan_t) / 0.35
        elif pan_t < 0.45:
            b_alpha = pan_t / 0.45
        b_alpha = max(0.0, min(1.0, b_alpha))

        pulse_hold = (0.88 + 0.12 * _math.sin(t_now * 3.8)) if in_hold else 1.0

        # ══════════════════════════════════════════════════════════
        # 1. LETTERBOX BARS — 80 px cinematic bars top + bottom
        # ══════════════════════════════════════════════════════════
        bar_frac = 1.0
        if pan_t > PAN_DUR - 0.4:
            bar_frac = (PAN_DUR - pan_t) / 0.4
        elif pan_t < 0.4:
            bar_frac = pan_t / 0.4
        bar_frac = max(0.0, min(1.0, bar_frac))
        LB_H = int(80 * bar_frac)   # letterbox bar height

        if LB_H > 0:
            # Solid dark base
            pygame.draw.rect(surface, DF_BG,  (0, 0,        w, LB_H))
            pygame.draw.rect(surface, DF_BG,  (0, h - LB_H, w, LB_H))
            # Stone texture strips
            for iy in range(0, LB_H, 12):
                st = pygame.Surface((w, 1), pygame.SRCALPHA)
                st.fill((*DF_STONE, 50))
                surface.blit(st, (0, iy))
                surface.blit(st, (0, h - LB_H + iy))
            # Gold inner edge line
            ga = int(200 * bar_frac * b_alpha)
            gl = pygame.Surface((w, 2), pygame.SRCALPHA)
            gl.fill((*DF_GOLD, ga))
            surface.blit(gl, (0, LB_H))
            surface.blit(gl, (0, h - LB_H - 2))
            # Thinner blood line just inside gold
            bl_s = pygame.Surface((w, 1), pygame.SRCALPHA)
            bl_s.fill((*DF_BLOOD, int(120 * bar_frac)))
            surface.blit(bl_s, (0, LB_H + 2))
            surface.blit(bl_s, (0, h - LB_H - 4))

        # ══════════════════════════════════════════════════════════
        # 2. VIGNETTE — darkens screen edges (always when pan_t > 0)
        # ══════════════════════════════════════════════════════════
        vig_a = int(100 * b_alpha)
        if vig_a > 0:
            vig = pygame.Surface((w, h), pygame.SRCALPHA)
            for band, mul in [(90, 1.0), (50, 0.5), (25, 0.22)]:
                ba = int(vig_a * mul)
                if ba > 0:
                    vig.fill((*DF_BG, ba), (0,       0,       w,    band))
                    vig.fill((*DF_BG, ba), (0,       h-band,  w,    band))
                    vig.fill((*DF_BG, ba), (0,       0,       band, h   ))
                    vig.fill((*DF_BG, ba), (w-band,  0,       band, h   ))
            surface.blit(vig, (0, 0))

        # ══════════════════════════════════════════════════════════
        # 3. GOLDEN FLASH — border wash on first unlock moment
        # ══════════════════════════════════════════════════════════
        if flash_a > 0:
            fa = int(180 * flash_a * flash_a)
            if fa > 0:
                fl = pygame.Surface((w, h), pygame.SRCALPHA)
                for thick, mul in [(70, 1.0), (40, 0.5), (20, 0.22)]:
                    ba = max(0, min(255, int(fa * mul)))
                    if ba > 0:
                        c = (*DF_GOLD_B, ba)
                        fl.fill(c, (0,        0,        w,     thick))
                        fl.fill(c, (0,        h-thick,  w,     thick))
                        fl.fill(c, (0,        0,        thick, h    ))
                        fl.fill(c, (w-thick,  0,        thick, h    ))
                ca = max(0, min(255, int(fa * 0.08)))
                fl.fill((*DF_GOLD, ca))
                surface.blit(fl, (0, 0))

        # ══════════════════════════════════════════════════════════
        # 4. TORCH GLOWS — corners of the letterbox bars
        # ══════════════════════════════════════════════════════════
        if LB_H > 0 and b_alpha > 0.2:
            torch_pulse = 0.7 + 0.3 * _math.sin(t_now * 5.1)
            torch_a = int(60 * b_alpha * torch_pulse)
            for tx in (80, w - 80):
                for ty in (LB_H // 2, h - LB_H // 2):
                    tg = pygame.Surface((60, 60), pygame.SRCALPHA)
                    for tr in (28, 18, 10):
                        ta = max(0, int(torch_a * (28 - tr) / 28))
                        pygame.draw.circle(tg, (*DF_GOLD, ta), (30, 30), tr)
                    surface.blit(tg, (tx - 30, ty - 30))

        # ══════════════════════════════════════════════════════════
        # 5. MAIN STONE PANEL — centered banner area
        # ══════════════════════════════════════════════════════════
        try:
            big_font  = pygame.font.SysFont("impact", 52)
            sub_font  = pygame.font.SysFont("impact", 20)
            tiny_font = pygame.font.SysFont("impact", 14)
        except Exception:
            big_font  = pygame.font.Font(None, 58)
            sub_font  = pygame.font.Font(None, 24)
            tiny_font = pygame.font.Font(None, 18)

        # ── Banner text selection ─────────────────────────────────
        if in_slide_back:
            main_str = "GET READY FOR BATTLE"
            main_col = DF_BLOOD_B
            sub_str  = "The final guardian awaits..."
            sub_col  = DF_SILVER
        elif in_hold:
            main_str = "BOSS ROOM UNLOCKED"
            main_col = DF_GOLD_B
            sub_str  = "ALL ROOMS CLEARED  -  THE FINAL CHALLENGE AWAITS"
            sub_col  = DF_PARCH
        else:
            main_str = "BOSS ROOM UNLOCKED"
            main_col = DF_GOLD
            sub_str  = "THE DOOR IS OPENING..."
            sub_col  = DF_SILVER

        main_surf = big_font.render(main_str, True, main_col)
        sub_surf  = sub_font.render(sub_str,  True, sub_col)

        # Panel geometry (sits in the middle third of the screen)
        panel_w  = max(main_surf.get_width() + 120, 680)
        panel_h  = 120
        panel_x  = w // 2 - panel_w // 2
        panel_y  = h // 2 - panel_h // 2

        final_a = int(255 * b_alpha * pulse_hold)

        # Stone panel background
        ps = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        ps.fill((*DF_BG, int(220 * b_alpha)))
        # Horizontal stone texture strips
        for iy in range(0, panel_h, 14):
            ps.fill((*DF_STONE, 40), (0, iy, panel_w, 1))
        surface.blit(ps, (panel_x, panel_y))

        # Gold outer border
        border_col = DF_GOLD_B if in_hold else DF_GOLD
        pygame.draw.rect(surface, border_col,
                         (panel_x, panel_y, panel_w, panel_h), 2, border_radius=4)
        # Blood inner border
        pygame.draw.rect(surface, DF_BLOOD,
                         (panel_x + 3, panel_y + 3, panel_w - 6, panel_h - 6), 1, border_radius=3)

        # Corner rivets
        for (rx, ry) in [(panel_x + 7, panel_y + 7),
                         (panel_x + panel_w - 7, panel_y + 7),
                         (panel_x + 7, panel_y + panel_h - 7),
                         (panel_x + panel_w - 7, panel_y + panel_h - 7)]:
            pygame.draw.circle(surface, DF_GOLD_D, (rx, ry), 5)
            pygame.draw.circle(surface, DF_GOLD,   (rx, ry), 5, 2)
            pygame.draw.circle(surface, DF_GOLD_B, (rx - 1, ry - 1), 2)

        # ── Main title text ───────────────────────────────────────
        tx = w // 2 - main_surf.get_width() // 2
        ty = panel_y + 18

        # Carved shadow
        shd = big_font.render(main_str, True, (0, 0, 0))
        shd_s = pygame.Surface(shd.get_size(), pygame.SRCALPHA)
        shd_s.blit(shd, (0, 0)); shd_s.set_alpha(final_a)
        surface.blit(shd_s, (tx + 3, ty + 3))

        # Gold outline pass
        out_col = DF_GOLD_D if in_slide_back else DF_GOLD_D
        for ox, oy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            out = big_font.render(main_str, True, out_col)
            out_s = pygame.Surface(out.get_size(), pygame.SRCALPHA)
            out_s.blit(out, (0, 0)); out_s.set_alpha(int(final_a * 0.6))
            surface.blit(out_s, (tx + ox, ty + oy))

        # Main text
        ms = pygame.Surface(main_surf.get_size(), pygame.SRCALPHA)
        ms.blit(main_surf, (0, 0)); ms.set_alpha(final_a)
        surface.blit(ms, (tx, ty))

        # ── Rune divider line under title ─────────────────────────
        div_y = ty + main_surf.get_height() + 4
        line_a = int(160 * b_alpha * pulse_hold)
        ls = pygame.Surface((panel_w - 40, 2), pygame.SRCALPHA)
        ls.fill((*DF_GOLD_D, line_a))
        surface.blit(ls, (panel_x + 20, div_y))
        # Diamond center accent
        cx_d = w // 2
        pts_d = [(cx_d, div_y - 4), (cx_d + 6, div_y + 1),
                 (cx_d, div_y + 6), (cx_d - 6, div_y + 1)]
        da_s = pygame.Surface((20, 14), pygame.SRCALPHA)
        pygame.draw.polygon(da_s, (*DF_GOLD, line_a), [(p[0] - cx_d + 10, p[1] - div_y + 4) for p in pts_d])
        surface.blit(da_s, (cx_d - 10, div_y - 4))

        # ── Subtitle text ─────────────────────────────────────────
        sx2 = w // 2 - sub_surf.get_width() // 2
        sy2 = div_y + 10
        subs = pygame.Surface(sub_surf.get_size(), pygame.SRCALPHA)
        subs.blit(sub_surf, (0, 0)); subs.set_alpha(int(final_a * 0.90))
        surface.blit(subs, (sx2, sy2))

        # ── Hold-phase outer gold divider lines (full-width) ──────
        if in_hold:
            fw_a = int(140 * b_alpha * pulse_hold)
            for ly in (panel_y - 8, panel_y + panel_h + 6):
                fls = pygame.Surface((w - 100, 1), pygame.SRCALPHA)
                fls.fill((*DF_GOLD_D, fw_a))
                surface.blit(fls, (50, ly))

        # NOTE FOR FUTURE PROMPTS
        # Section 6 (fake door graphic overlay) was intentionally removed.
        # The camera pans to the actual boss-room door tiles, which have their
        # own split-open animation (stage.py Room._draw_door_opening_anim).
        # Do NOT add a door graphic overlay here — the real tiles are visible.

        # ══════════════════════════════════════════════════════════
        # 7. SLIDE-BACK PHASE — blood-red pulsing "GET READY" warning
        # ══════════════════════════════════════════════════════════
        if in_slide_back and pan_t < SLIDE_B * 0.80:
            pulse2 = 0.55 + 0.45 * abs(_math.sin(t_now * 7.5))
            try:
                warn_font = pygame.font.SysFont("impact", 44)
            except Exception:
                warn_font = pygame.font.Font(None, 50)
            warn_text = warn_font.render("-- GET READY --", True, DF_BLOOD_B)
            wa = int(255 * (pan_t / (SLIDE_B * 0.80)) * pulse2 * b_alpha)
            if wa > 0:
                ws = pygame.Surface(warn_text.get_size(), pygame.SRCALPHA)
                ws.blit(warn_text, (0, 0)); ws.set_alpha(wa)
                surface.blit(ws, (w // 2 - warn_text.get_width() // 2,
                                  panel_y - warn_text.get_height() - 14))

    def _draw_boss_door_arrow(self, surface):
        """Screen-edge arrow pointing toward boss door, fades out after 6 s."""
        t = getattr(self, 'boss_door_arrow_t', 0.0)
        if t <= 0:
            return
        boss_room = getattr(self.stage, 'boss_room', None)
        if boss_room is None:
            return

        # Convert boss room center to screen space
        bsx = boss_room.cx - self.stage.cam_x
        bsy = boss_room.cy - self.stage.cam_y
        w, h = surface.get_size()
        from constants import HUD_H
        play_h = h - HUD_H

        # If boss door is already on screen, skip the arrow
        MARGIN = 60
        if MARGIN < bsx < w - MARGIN and MARGIN < bsy < play_h - MARGIN:
            return

        # Direction from screen center to boss room
        cx, cy = w / 2, play_h / 2
        dx, dy = bsx - cx, bsy - cy
        dist = math.hypot(dx, dy) or 1
        nx, ny = dx / dist, dy / dist

        # Clamp arrow to screen edge
        EDGE = 52
        if abs(nx) > abs(ny):
            t_x = (w - EDGE if nx > 0 else EDGE)
            t_y = cy + ny * ((t_x - cx) / (nx or 1e-9))
            t_y = max(EDGE, min(play_h - EDGE, t_y))
        else:
            t_y = (play_h - EDGE if ny > 0 else EDGE)
            t_x = cx + nx * ((t_y - cy) / (ny or 1e-9))
            t_x = max(EDGE, min(w - EDGE, t_x))

        arrow_x, arrow_y = int(t_x), int(t_y)
        angle = math.degrees(math.atan2(ny, nx))

        # Alpha pulses & fades
        pulse = 0.75 + 0.25 * math.sin(pygame.time.get_ticks() / 220.0)
        fade  = min(1.0, t / 1.5)           # fade in at start
        fade  = min(fade, min(1.0, t))      # fade out at end
        alpha = int(255 * pulse * fade)

        # Draw arrow shape on a small surface then rotate
        A_W, A_H = 44, 28
        arr_surf = pygame.Surface((A_W + 12, A_H + 12), pygame.SRCALPHA)
        gold   = (255, 210, 40, alpha)
        gold_d = (120, 80, 0, alpha)
        # Arrow head (triangle pointing right)
        pts = [
            (A_W + 6,  (A_H + 12) // 2),          # tip
            (A_W // 2, 4),                          # top
            (A_W // 2, (A_H + 12) // 2 - 5),       # notch top
            (4,        (A_H + 12) // 2 - 5),        # shaft top-left
            (4,        (A_H + 12) // 2 + 5),        # shaft bot-left
            (A_W // 2, (A_H + 12) // 2 + 5),        # notch bot
            (A_W // 2, A_H + 8),                    # bottom
        ]
        pygame.draw.polygon(arr_surf, gold_d, pts)
        inner = [(x + 2, y) for x, y in pts]
        pygame.draw.polygon(arr_surf, gold, pts)
        pygame.draw.polygon(arr_surf, pygame.Color(255, 255, 180, max(0, min(255, int(alpha)))), pts, 2)

        rotated = pygame.transform.rotate(arr_surf, -angle)
        rw, rh = rotated.get_size()
        surface.blit(rotated, (arrow_x - rw // 2, arrow_y - rh // 2))

        # Small "BOSS" label below arrow
        try:
            fnt = pygame.font.SysFont("impact", 14)
        except Exception:
            fnt = pygame.font.Font(None, 16)
        lbl = fnt.render("BOSS", True, (255, 230, 80))
        ls = pygame.Surface(lbl.get_size(), pygame.SRCALPHA)
        ls.blit(lbl, (0, 0))
        ls.set_alpha(alpha)
        offset_x = int(ny * 26)   # perpendicular nudge
        offset_y = int(-nx * 26)
        surface.blit(ls, (arrow_x - lbl.get_width() // 2 + offset_x,
                          arrow_y - lbl.get_height() // 2 + offset_y))

    def _render(self, mouse_pos, dt=0.016):
        self.screen.fill((12, 12, 20))

        if self.state == STATE_MENU:
            self.menu_screen.draw(self.screen, mouse_pos)

        elif self.state == STATE_CLASS_SEL:
            self.class_screen.draw(self.screen, mouse_pos, self.clock.get_time() / 1000.0)

        elif self.state == STATE_PLAYING:
            # ── Screen shake offset ───────────────────────────
            import random as _rnd2
            sk_ox = sk_oy = 0
            if self.shake_timer > 0:
                m = int(self.shake_mag * (self.shake_timer / 0.28))
                sk_ox = _rnd2.randint(-m, m)
                sk_oy = _rnd2.randint(-m, m)

            # Draw everything to main surface (cam already shifted by shake)
            orig_cam_x = self.stage.cam_x
            orig_cam_y = self.stage.cam_y
            self.stage.cam_x += sk_ox
            self.stage.cam_y += sk_oy

            self.stage.draw(self.screen, player=self.player)
            for e in self.enemies:
                e.draw(self.screen, self.stage.cam_x, self.stage.cam_y)
            for d in self.drops:
                d.draw(self.screen, self.stage.cam_x, self.stage.cam_y, player=self.player)
            for b in self.bullets:
                b.draw(self.screen, self.stage.cam_x, self.stage.cam_y)
            for eb in self.e_bullets:
                eb.draw(self.screen, self.stage.cam_x, self.stage.cam_y)
            for f in self.fx:
                f.draw(self.screen, self.stage.cam_x, self.stage.cam_y)
            if self.portal:
                self.portal.draw(self.screen, self.stage.cam_x, self.stage.cam_y)
            self.player.draw(self.screen, self.stage.cam_x, self.stage.cam_y)

            self.stage.cam_x = orig_cam_x
            self.stage.cam_y = orig_cam_y

            self._hud_pause_btn = draw_hud(self.screen, self.player, self.stage,
                     self.stage_idx, len(STAGE_CONFIGS), self.run_time)
            self.stage.draw_minimap(self.screen, self.player.x, self.player.y)

            # ── Boss UI & cinematics (drawn on top of HUD) ─────
            # HP bar แสดงเฉพาะหลังจากเข้าห้องบอสแล้วเท่านั้น (boss.activated = True)
            # ซ่อนระหว่าง spawn cinematic และ ready overlay เพื่อไม่ให้ซ้อนกัน
            in_boss_cinematic = self.boss_spawn_timer > 0 or self.boss_ready_timer > 0
            if (self.boss_entity and self.boss_entity.alive
                    and getattr(self.boss_entity, 'activated', False)
                    and not in_boss_cinematic):
                self._draw_boss_hpbar(self.screen)
            if self.boss_death_particles:
                self._draw_boss_death_particles(self.screen)
            if self.boss_death_timer > 0:
                self._draw_boss_death_overlay(self.screen)
            if self.boss_spawn_timer > 0:
                self._draw_boss_spawn_cinematic(self.screen)
            if self.boss_ready_timer > 0:
                self._draw_boss_ready_overlay(self.screen)
            # ── Boss-door unlock screen fx (always on top) ─────
            self._draw_boss_unlock_fx(self.screen)
            self._draw_boss_door_arrow(self.screen)

        elif self.state == STATE_INVENTORY:
            # Draw game behind inventory
            self.stage.draw(self.screen, player=self.player)
            self.player.draw(self.screen, self.stage.cam_x, self.stage.cam_y)
            draw_hud(self.screen, self.player, self.stage,
                     self.stage_idx, len(STAGE_CONFIGS), self.run_time)
            self.inv_screen.draw(self.screen, self.player, mouse_pos)

        elif self.state == STATE_SHOP:
            self.screen.fill((5, 15, 5))
            self.shop_screen.draw(self.screen, self.player, mouse_pos)

        elif self.state == STATE_PAUSED:
            self.stage.draw(self.screen, player=self.player)
            self.pause_screen.draw(self.screen, mouse_pos)

        elif self.state == STATE_RANGE:
            mouse_buttons = pygame.mouse.get_pressed()
            self.range_screen.update(dt, self._frame_events, mouse_pos, mouse_buttons)
            self.range_screen.draw(self.screen, mouse_pos)

        elif self.state in (STATE_GAME_OVER, STATE_VICTORY):
            win = (self.state == STATE_VICTORY)
            # FIX: pass correct arguments (surface, player, tracker, win)
            self.over_screen.draw(self.screen, self.player, self.tracker, win=win)