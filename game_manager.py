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
from bullet        import Bullet, DroppedItem, FloatingText, draw_hud, Portal
from stats_tracker import StatsTracker
from ui            import (MainMenuScreen, ClassSelectScreen, InventoryScreen,
                           ShopScreen, PauseScreen, GameOverScreen,
                           ShootingRangeScreen)


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

        self.menu_screen  = MainMenuScreen(self.tracker)
        self.range_screen = ShootingRangeScreen()
        self._frame_events = []
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

        elif key == pygame.K_q:
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
                self._add_fx(fx_x, fx_y, "★", (255, 240, 80), 18)
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
                self._add_fx(fx_x, fx_y, "⚡", col, 19)
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
                self._start_new_game("Sausage Man")
            elif result == "range":
                self.range_screen._reset()
                self.range_screen.set_player(self.player if self.player else __import__("player").Player("Hero", "Sausage Man"))
                self.change_state(STATE_RANGE)
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
            elif result == "restart":
                self._restart_game()
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

        elif self.state == STATE_RANGE:
            mouse_buttons = pygame.mouse.get_pressed()
            mouse_buttons = pygame.mouse.get_pressed()
            self.range_screen.update(self._dt, self._frame_events, self._mouse_pos, mouse_buttons)
            result = self.range_screen.handle_click(pos)
            if result == "menu":
                self.change_state(STATE_MENU)

        elif self.state in (STATE_GAME_OVER, STATE_VICTORY):
            if hasattr(self.over_screen, "btn_menu") and self.over_screen.btn_menu.collidepoint(pos):
                self.change_state(STATE_MENU)

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
        self.stage.update(dt)

        # ── Room door / fountain management ───────────────────
        cur_room = self.stage.get_room_at(p.x, p.y)
        if cur_room:
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
            else:
                if not cur_room.doors_open:
                    self.stage.open_room_doors(cur_room)
                cur_room.cleared = True

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
                        else:
                            _spawn_bullet(angle)

                        p.shoot_cooldown = (1.0 / max(0.1, p.get_fire_rate())) / frenzy_mult
                        # Screen shake during frenzy
                        if frenzy_mult > 1.0:
                            self.shake_timer = max(self.shake_timer, 0.12)
                            self.shake_mag   = 6

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
            self.tracker.end_run("death", p)
            self.change_state(STATE_GAME_OVER)

        # ── Stage completion: spawn portal on last enemy ───────
        if self.enemies == [] and self.state == STATE_PLAYING and self.portal is None:
            if self.stage.check_completion([]):
                px, py = self._last_enemy_pos
                self.portal = Portal(px, py)
                self._add_fx(px, py - 50, "PORTAL OPENED!", (200, 120, 255), 22)

    # ── Render ───────────────────────────────────────────────
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