"""
game_manager.py  –  GameManager class (OOP Class 6)
Updated to consume player.mana for skills and keep compatibility
with the new Player implementation.
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
    STAGE_CONFIGS
)
from player       import Player
from stage        import Stage
from enemy        import EnemyBullet
from bullet       import Bullet, DroppedItem, FloatingText, draw_hud
from stats_tracker import StatsTracker
from ui           import (MainMenuScreen, ClassSelectScreen, InventoryScreen,
                          ShopScreen, PauseScreen, GameOverScreen)

class GameManager:
    """
    Central game controller using MVC pattern.
    Owns the main loop, delegates rendering and logic to subsystems.
    """

    def __init__(self, screen):
        self.screen  = screen
        self.clock   = pygame.time.Clock()
        self.state   = STATE_MENU
        self.running = True

        # Subsystems
        self.tracker = StatsTracker()

        # Game objects (created on new game)
        self.player      = None
        self.stage       = None
        self.stage_idx   = 0
        self.enemies     = []
        self.bullets     = []       # player bullets
        self.e_bullets   = []       # enemy bullets
        self.drops       = []       # DroppedItem list
        self.fx          = []       # FloatingText list

        # Score
        self.score       = 0
        self.kills       = 0

        # UI screens
        self.menu_screen    = MainMenuScreen(self.tracker)
        self.class_screen   = ClassSelectScreen()
        self.inv_screen     = InventoryScreen()
        self.pause_screen   = PauseScreen()
        self.over_screen    = GameOverScreen()
        self.shop_screen    = None
        self.player_name    = "Hero"

    # ── Main loop ───────────────────────────────────────────
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)   # cap dt to avoid spiral of death
            mouse_pos = pygame.mouse.get_pos()

            self._handle_events(mouse_pos)
            self._update(dt, mouse_pos)
            self._render(mouse_pos)
            pygame.display.flip()

    # ── Event handling ───────────────────────────────────────
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
            elif self.state in (STATE_PAUSED, STATE_INVENTORY, STATE_SHOP):
                self.change_state(STATE_PLAYING)

        elif key == pygame.K_i:
            if self.state == STATE_PLAYING:
                self.change_state(STATE_INVENTORY)
            elif self.state == STATE_INVENTORY:
                self.change_state(STATE_PLAYING)

        elif key == pygame.K_e:
            if self.state == STATE_PLAYING:
                self._try_pickup()

    def _handle_skill(self, skill):
        """Dispatch skill usage; consume player.mana when required."""
        if not skill or self.player is None:
            return

        t = skill[0]

        if t == "whirlwind":
            dmg = skill[1]
            cost = skill[2] if len(skill) > 2 else 0
            if cost and not self.player.use_mana(cost):
                return
            for e in self.enemies:
                if e.alive:
                    dist = math.hypot(e.x - self.player.x, e.y - self.player.y)
                    if dist < 100:
                        e.take_damage(dmg)

        elif t == "fireball":
            dmg, dx, dy = skill[1], skill[2], skill[3]
            cost = skill[4] if len(skill) > 4 else 8
            if cost and not self.player.use_mana(cost):
                return
            self.bullets.append(
                Bullet(self.player.x, self.player.y, dx, dy, 8, dmg)
            )

        elif t == "triple_shot":
            dmg, angle = skill[1], skill[2]
            cost = skill[3] if len(skill) > 3 else 6
            if cost and not self.player.use_mana(cost):
                return
            for offset in [-0.2, 0, 0.2]:
                dx = math.cos(angle + offset)
                dy = math.sin(angle + offset)
                self.bullets.append(
                    Bullet(self.player.x, self.player.y, dx, dy, 7, dmg)
                )

    def _on_click(self, pos, button):
        if self.state == STATE_MENU:
            result = self.menu_screen.handle_click(pos)
            if result == "play":
                self.change_state(STATE_CLASS_SEL)
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

        elif self.state == STATE_PLAYING:
            pass   # attack handled by held mouse in _update

        elif self.state == STATE_INVENTORY:
            result = self.inv_screen.handle_click(pos, self.player)

        elif self.state == STATE_PAUSED:
            result = self.pause_screen.handle_click(pos)
            if result == "resume":
                self.change_state(STATE_PLAYING)
            elif result == "menu":
                self.change_state(STATE_MENU)

        elif self.state == STATE_SHOP:
            result = self.shop_screen.handle_click(pos, self.player)
            if result == "heal":
                self._add_fx(SCREEN_W//2, SCREEN_H//2 - 40, "+50 HP", GREEN, 22)
            elif result == "buy":
                self._add_fx(SCREEN_W//2, SCREEN_H//2 - 40, "Item Purchased!", GOLD, 22)
            elif result == "reroll":
                cost = self.shop_screen.reroll_cost   # already updated to next cost
                self._add_fx(SCREEN_W//2, SCREEN_H//2 - 40,
                             f"Shop Rerolled! Next: {cost}G", CYAN, 20)
            elif result == "leave":
                self._next_stage()

        elif self.state in (STATE_GAME_OVER, STATE_VICTORY):
            if hasattr(self.over_screen, "btn_menu") and self.over_screen.btn_menu.collidepoint(pos):
                self.change_state(STATE_MENU)

    # ── State change ─────────────────────────────────────────
    def change_state(self, new_state):
        self.state = new_state

    # ── New game ─────────────────────────────────────────────
    def _start_new_game(self, char_class):
        self.player    = Player(self.player_name, char_class)
        self.stage_idx = 0
        self.kills     = 0
        self.score     = 0
        # Starter bonus — enough gold for 1 shop item
        self.player.gold        = 60
        self._load_stage(0)
        self.tracker.start_run(self.player)
        self.change_state(STATE_PLAYING)

    def _load_stage(self, idx):
        self.stage    = Stage(idx)
        start_room    = self.stage.rooms[0]
        self.player.x = float(start_room.cx)
        self.player.y = float(start_room.cy)
        # Spawn enemies (skip starting room so player isn't immediately swarmed)
        self.enemies  = self.stage.spawn_enemies(
            stage_level=idx + 1,
            skip_room=start_room
        )
        self.bullets  = []
        self.e_bullets= []
        self.drops    = []
        self.fx       = []

    # ── Update ───────────────────────────────────────────────
    def _update(self, dt, mouse_pos):
        if self.state != STATE_PLAYING:
            return

        p     = self.player
        walls = self.stage.wall_rects
        cam_x = self.stage.cam_x
        cam_y = self.stage.cam_y

        # Convert mouse to world coords
        world_mouse = (mouse_pos[0] + cam_x, mouse_pos[1] + cam_y)

        # Player
        p.update(dt, walls, world_mouse)
        self.stage.update_camera(p.x, p.y)

        # Hold left mouse button to auto-attack
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:
            # Attempt to shoot depending on weapon fire rate
            wpn = p.weapon
            if wpn and not wpn.is_melee:
                if p.shoot_cooldown <= 0:
                    dmg, crit = p.calc_damage()
                    angle = math.atan2(world_mouse[1] - p.y, world_mouse[0] - p.x)
                    dx = math.cos(angle)
                    dy = math.sin(angle)
                    spd = p.get_bullet_speed() or 7
                    self.bullets.append(Bullet(p.x, p.y, dx, dy, spd, dmg, is_crit=crit))
                    p.shoot_cooldown = 1.0 / max(0.1, p.get_fire_rate())
                else:
                    p.shoot_cooldown -= dt
            else:
                # Melee
                if not p.melee_active:
                    p.melee_active = True
                    p.melee_timer = 0.12

        # Update bullets
        for b in list(self.bullets):
            b.update(dt, walls)
            if not b.alive:
                self.bullets.remove(b)

        # Update enemy bullets
        for eb in list(self.e_bullets):
            eb.update(dt, walls)
            if not eb.alive:
                self.e_bullets.remove(eb)

        # Update enemies
        for e in list(self.enemies):
            e.update(p, walls, dt, self.e_bullets)
            if not e.alive:
                # drop loot
                itm = e.drop_loot(luk_bonus=0)
                if itm:
                    self.drops.append(DroppedItem(itm, e.x, e.y))
                self.tracker.log_event("kill", {"exp": e.exp_reward, "is_boss": getattr(e, "is_boss", False)})
                self.enemies.remove(e)
                self.kills += 1

        # Update drops
        for d in list(self.drops):
            d.update(dt)

        # Update fx
        for f in list(self.fx):
            f.update(dt)
            if not f.alive:
                self.fx.remove(f)

    # ── Rendering ────────────────────────────────────────────
    def _render(self, mouse_pos):
        self.screen.fill((12, 12, 20))
        if self.state == STATE_MENU:
            self.menu_screen.draw(self.screen, mouse_pos)
        elif self.state == STATE_CLASS_SEL:
            self.class_screen.draw(self.screen, mouse_pos)
        elif self.state == STATE_PLAYING:
            # draw stage and entities (kept simple)
            self.stage.draw(self.screen)
            # draw enemies
            for e in self.enemies:
                e.draw(self.screen, self.stage.cam_x, self.stage.cam_y)
            # draw items
            for d in self.drops:
                d.draw(self.screen, self.stage.cam_x, self.stage.cam_y)
            # draw bullets
            for b in self.bullets:
                b.draw(self.screen, self.stage.cam_x, self.stage.cam_y)
            # HUD
            draw_hud(self.screen, self.player, self.stage, self.stage_idx, len(STAGE_CONFIGS))
        elif self.state == STATE_INVENTORY:
            self.inv_screen.draw(self.screen, self.player, mouse_pos)
        elif self.state == STATE_PAUSED:
            self.pause_screen.draw(self.screen, mouse_pos)
        elif self.state in (STATE_GAME_OVER, STATE_VICTORY):
            self.over_screen.draw(self.screen, mouse_pos)