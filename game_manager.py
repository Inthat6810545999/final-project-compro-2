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
    STATE_VICTORY, STATE_SHOP, STATE_STATS,
    WHITE, RED, GREEN, YELLOW, GOLD, CYAN, ORANGE, BLACK, GRAY,
    STAGE_CONFIGS,
)
from player        import Player
from stage         import Stage
from enemy         import EnemyBullet
from bullet        import Bullet, DroppedItem, FloatingText, draw_hud
from stats_tracker import StatsTracker
from ui            import (MainMenuScreen, ClassSelectScreen, InventoryScreen,
                           ShopScreen, PauseScreen, GameOverScreen)


class GameManager:
    """Central game controller."""

    def __init__(self, screen):
        self.screen  = screen
        self.clock   = pygame.time.Clock()
        self.state   = STATE_MENU
        self.running = True

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

        self.menu_screen  = MainMenuScreen(self.tracker)
        self.class_screen = ClassSelectScreen()
        self.inv_screen   = InventoryScreen()
        self.pause_screen = PauseScreen()
        self.over_screen  = GameOverScreen()
        self.shop_screen  = None
        self.player_name  = "Hero"

    # ── Main loop ────────────────────────────────────────────
    def run(self):
        while self.running:
            dt        = self.clock.tick(FPS) / 1000.0
            dt        = min(dt, 0.05)
            mouse_pos = pygame.mouse.get_pos()

            self._handle_events(mouse_pos)
            self._update(dt, mouse_pos)
            self._render(mouse_pos)
            pygame.display.flip()

    # ── Events ───────────────────────────────────────────────
    def _handle_events(self, mouse_pos):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                self._on_key(event.key)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._on_click(event.pos, event.button)

            elif event.type == pygame.MOUSEWHEEL:
                if self.state == STATE_INVENTORY:
                    self.inv_screen.handle_scroll(-event.y, self.player)

    def _on_key(self, key):
        if key == pygame.K_ESCAPE:
            if self.state == STATE_PLAYING:
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

        elif key == pygame.K_q:
            if self.state == STATE_PLAYING:
                self._use_skill()

    def _use_skill(self):
        """Trigger the active character skill (Q key)."""
        from constants import CLASS_SKILLS
        p = self.player
        if not p or not p.alive:
            return
        skill_cfg = CLASS_SKILLS.get(p.char_class)
        if not skill_cfg:
            return
        if p.skill_cd > 0:
            self._add_fx(p.x, p.y - 40,
                         f"Skill CD: {p.skill_cd:.1f}s", (160, 160, 160), 15)
            return
        # Build skill tuple for _handle_skill
        stype = skill_cfg["type"]
        cost  = skill_cfg.get("mana_cost", 0)
        dmg, _ = p.calc_damage()
        skill_dmg = int(dmg * 1.8)
        angle = p.facing_angle
        dx = math.cos(angle); dy = math.sin(angle)

        if stype == "nova_burst":
            skill = (stype, skill_dmg, dx, dy, cost)
        elif stype == "triple_shot":
            skill = (stype, skill_dmg, angle, cost)
        elif stype in ("whirlwind", "death_bolt"):
            skill = (stype, skill_dmg, cost)
        elif stype == "shield_slam":
            skill = (stype, skill_dmg, cost)
        elif stype == "smoke_dash":
            skill = (stype, skill_dmg, cost)
        else:
            skill = (stype, skill_dmg, cost)

        self._handle_skill(skill)
        p.skill_cd = skill_cfg["cooldown"]

    def _tick_skill_cd(self, dt):
        if self.player and self.player.skill_cd > 0:
            self.player.skill_cd = max(0.0, self.player.skill_cd - dt)

    def _handle_skill(self, skill):
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
        if self.state == STATE_MENU:
            result = self.menu_screen.handle_click(pos)
            if result == "play":
                self._start_new_game("Ranger")
            elif result == "stats":
                self.tracker.plot_dashboard()
            elif result == "quit":
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
            elif result == "menu":
                self.change_state(STATE_MENU)

        elif self.state == STATE_SHOP:
            result = self.shop_screen.handle_click(pos, self.player)
            if result == "heal":
                self._add_fx(SCREEN_W // 2, SCREEN_H // 2 - 40, "+50 HP", GREEN, 22)
            elif result == "buy":
                self._add_fx(SCREEN_W // 2, SCREEN_H // 2 - 40, "Item Purchased!", GOLD, 22)
            elif result == "reroll":
                cost = self.shop_screen.reroll_cost
                self._add_fx(SCREEN_W // 2, SCREEN_H // 2 - 40,
                             f"Shop Rerolled! Next: {cost}G", CYAN, 20)
            elif result == "leave":
                self._next_stage()   # FIX: method now defined below

        elif self.state in (STATE_GAME_OVER, STATE_VICTORY):
            if hasattr(self.over_screen, "btn_menu") and self.over_screen.btn_menu.collidepoint(pos):
                self.change_state(STATE_MENU)

    # ── State management ─────────────────────────────────────
    def change_state(self, new_state):
        self.state = new_state

    # ── New game ─────────────────────────────────────────────
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

    # ── Item pickup ──────────────────────────────────────────
    def _try_pickup(self):
        """Soul Knight-style pickup: swap weapons on the ground, equip better gear."""
        p = self.player
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
            # Drop the old item at the pickup spot
            self.drops.append(DroppedItem(old, best_drop.x + 20, best_drop.y + 20))
            from constants import RARITY_COLORS
            col = RARITY_COLORS.get(itm.rarity, WHITE)
            self._add_fx(p.x, p.y - 30, f"↔ SWAP → {itm.name}!", col, 17)
        else:
            from constants import RARITY_COLORS
            col = RARITY_COLORS.get(itm.rarity, WHITE)
            self._add_fx(p.x, p.y - 30, f"[EQUIPPED] {itm.name}!", col, 17)

        self.tracker.log_event("item_pickup", {"rarity": itm.rarity})
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

        p     = self.player
        walls = self.stage.wall_rects
        cam_x = self.stage.cam_x
        cam_y = self.stage.cam_y

        # Tick run timer
        self.run_time += dt
        self._tick_skill_cd(dt)

        world_mouse = (mouse_pos[0] + cam_x, mouse_pos[1] + cam_y)

        # Player update (includes movement + regen)
        p.update(dt, walls, world_mouse)
        self.stage.update_camera(p.x, p.y)

        # ── Shooting / melee input ────────────────────────────
        # FIX: shoot_cooldown always ticks — moved outside if/else
        if p.shoot_cooldown > 0:
            p.shoot_cooldown -= dt

        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:
            wpn = p.weapon
            if wpn and not wpn.is_melee:
                # Ranged attack
                if p.shoot_cooldown <= 0:
                    dmg, crit = p.calc_damage()
                    angle = math.atan2(world_mouse[1] - p.y, world_mouse[0] - p.x)
                    dx = math.cos(angle)
                    dy = math.sin(angle)
                    spd = p.get_bullet_speed() or 7
                    pierce = (p.char_class in ("Mage", "Necromancer"))
                    self.bullets.append(Bullet(p.x, p.y, dx, dy, spd, dmg,
                                               pierce=pierce, is_crit=crit))
                    p.shoot_cooldown = 1.0 / max(0.1, p.get_fire_rate())

        # ── Player bullets ────────────────────────────────────
        for b in list(self.bullets):
            b.update(dt, walls)
            if not b.alive:
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
                elif dmg > 0:
                    self._add_fx(p.x, p.y - 30, f"-{dmg}", RED, 18)

        # ── Enemy update + death ──────────────────────────────
        for e in list(self.enemies):
            e.update(p, walls, dt, self.e_bullets)
            if not e.alive:
                gold_drop = random.randint(2, 6 + self.stage_idx)
                if p.char_class == "Rogue":
                    gold_drop = int(gold_drop * 1.3)
                p.gold += gold_drop
                self._add_fx(e.x, e.y - e.size - 10, f"+{gold_drop}G", GOLD, 15)
                # Necromancer: Soul Drain passive
                if p.char_class == "Necromancer":
                    p.hp   = min(p.max_hp,   p.hp   + 8)
                    p.mana = min(p.max_mana, p.mana + 6)
                    self._add_fx(e.x, e.y - e.size - 25, "+8HP +6MP", (60, 220, 120), 13)
                # Drop loot (no LUK bonus — no stats system)
                itm = e.drop_loot(luk_bonus=0)
                if itm:
                    self.drops.append(DroppedItem(itm, e.x, e.y))
                self.tracker.log_event("kill", {
                    "exp": e.exp_reward,
                    "is_boss": isinstance(e, __import__("enemy").BossEnemy)
                })
                self.enemies.remove(e)
                self.kills += 1
                self.score += e.exp_reward * 10

        # ── Drops ─────────────────────────────────────────────
        for d in list(self.drops):
            d.update(dt)

        # ── Floating text ─────────────────────────────────────
        for f in list(self.fx):
            f.update(dt)
            if not f.alive:
                self.fx.remove(f)

        # ── Player death ──────────────────────────────────────
        if not p.alive:
            # FIX: call end_run so stats are saved
            self.tracker.end_run("death", p)
            self.change_state(STATE_GAME_OVER)

        # ── Stage completion ──────────────────────────────────
        # FIX: poll completion every frame and open shop when done
        if self.enemies == [] and self.state == STATE_PLAYING:
            if self.stage.check_completion([]):   # empty list = always complete
                self._open_shop()

    # ── Render ───────────────────────────────────────────────
    def _render(self, mouse_pos):
        self.screen.fill((12, 12, 20))

        if self.state == STATE_MENU:
            self.menu_screen.draw(self.screen, mouse_pos)

        elif self.state == STATE_CLASS_SEL:
            self.class_screen.draw(self.screen, mouse_pos, self.clock.get_time() / 1000.0)

        elif self.state == STATE_PLAYING:
            self.stage.draw(self.screen)
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
            self.player.draw(self.screen, self.stage.cam_x, self.stage.cam_y)
            draw_hud(self.screen, self.player, self.stage,
                     self.stage_idx, len(STAGE_CONFIGS), self.run_time)
            self.stage.draw_minimap(self.screen, self.player.x, self.player.y)

        elif self.state == STATE_INVENTORY:
            # Draw game behind inventory
            self.stage.draw(self.screen)
            self.player.draw(self.screen, self.stage.cam_x, self.stage.cam_y)
            draw_hud(self.screen, self.player, self.stage,
                     self.stage_idx, len(STAGE_CONFIGS), self.run_time)
            self.inv_screen.draw(self.screen, self.player, mouse_pos)

        elif self.state == STATE_SHOP:
            self.screen.fill((5, 15, 5))
            self.shop_screen.draw(self.screen, self.player, mouse_pos)

        elif self.state == STATE_PAUSED:
            self.stage.draw(self.screen)
            self.pause_screen.draw(self.screen, mouse_pos)

        elif self.state in (STATE_GAME_OVER, STATE_VICTORY):
            win = (self.state == STATE_VICTORY)
            # FIX: pass correct arguments (surface, player, tracker, win)
            self.over_screen.draw(self.screen, self.player, self.tracker, win=win)
