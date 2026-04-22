"""
enemy.py  –  Enemy base class + subclasses
AI states: IDLE, PATROL, CHASE, ATTACK, FLEE
Fixes:
  - EnemyBullet.update() now accepts (dt, walls=None) to match game_manager call
  - Hardcoded 80 replaced with HUD_H import
"""
import math
import random
import os
import pygame
from constants import (
    ENEMY_DATA, WHITE, RED, GREEN, YELLOW, ORANGE, BLACK, GRAY,
    SCREEN_W, SCREEN_H, HUD_H,
    MAP_W, MAP_H, TILE,   # FIX: world bounds for bullet out-of-range check
)
from item import make_random_item

# ── PNG sprite mapping ────────────────────────────────────────────────────────
# Maps enemy_type key → PNG filename (place PNGs in same folder as enemy.py)
ENEMY_PNG = {
    "Slime":         "Green_Slime.png",
    "Wolf":          "Wolf.png",
    "Bat":           "Bat_Imp.png",
    "FireImp":       "Bat_Imp.png",
    "Golem":         "Clay_Golem.png",
    "Harpy":         "Harpy.png",
    "StormMage":     "StormMage.png",
    "EliteHybrid":   "Elite_Hybrid.png",
    "Wraith":        "Wraith.png",
    "GunnerElite":   "unner_Elite.png",
    # Bosses
    "Demon King Baldr": "Demon_King_Baldr__Final_Boss_.png",
}

# Module-level image cache — load each PNG only once
_IMG_CACHE: dict = {}


_BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sprite", "entity_sprite")


def _load_enemy_image(enemy_type: str, diameter: int) -> pygame.Surface | None:
    """Return a scaled Surface for enemy_type, or None if PNG not found."""
    fname = ENEMY_PNG.get(enemy_type)
    if not fname:
        return None
    cache_key = (enemy_type, diameter)
    if cache_key in _IMG_CACHE:
        return _IMG_CACHE[cache_key]
    full_path = os.path.join(_BASE_DIR, fname)
    if not os.path.exists(full_path):
        print(f"[enemy] PNG not found: {full_path}")
        _IMG_CACHE[cache_key] = None
        return None
    try:
        img = pygame.image.load(full_path).convert_alpha()
        img = pygame.transform.smoothscale(img, (diameter, diameter))
        _IMG_CACHE[cache_key] = img
        return img
    except Exception as e:
        print(f"[enemy] Failed to load {full_path}: {e}")
        _IMG_CACHE[cache_key] = None
        return None


class Enemy:
    """Base class for all enemy bots."""

    IDLE   = "IDLE"
    PATROL = "PATROL"
    CHASE  = "CHASE"
    ATTACK = "ATTACK"
    FLEE   = "FLEE"

    CHASE_RANGE  = 280
    ATTACK_RANGE = 40
    FLEE_HP_PCT  = 0.15

    def __init__(self, enemy_type, x, y, stage_level=1):
        data = ENEMY_DATA.get(enemy_type, ENEMY_DATA["Slime"])
        self.enemy_type = enemy_type
        self.x          = float(x)
        self.y          = float(y)

        scale       = 1.0 + (stage_level - 1) * 0.18
        self.max_hp = int(data["hp"] * scale)
        self.hp     = self.max_hp
        self.atk    = int(data["atk"] * scale * (3 + stage_level * 0.05))
        self.speed  = data["speed"]
        self.size   = data["size"]
        self.color  = data["color"]
        self.exp_reward  = int(data["exp"] * scale)
        self.shoot_range = data.get("range", 0)
        self.can_shoot   = data.get("shoot", False)

        self.ai_state    = self.IDLE
        self.alive       = True
        self.shoot_timer = 0.0
        self.shoot_cd    = 1.5
        self.patrol_angle = random.uniform(0, math.tau)
        self.patrol_timer = 0.0
        self.hurt_timer  = 0.0
        # Soul Knight style: freeze until player enters the room (door closes)
        self.activated   = False

        # PNG sprite — display size larger than collision radius for visual clarity
        # Small(<=18): x4.5 | Medium(<=24): x4 | Large(>24): x3.5
        if self.size <= 18:
            _diam = int(self.size * 4.5)
        elif self.size <= 24:
            _diam = int(self.size * 4)
        else:
            _diam = int(self.size * 3.5)
        self._sprite_right = _load_enemy_image(enemy_type, _diam)
        self._sprite_left  = (
            pygame.transform.flip(self._sprite_right, True, False)
            if self._sprite_right else None
        )
        self._sprite_hurt_r = None
        self._sprite_hurt_l = None
        self._display_r = _diam  # remember for HP bar offset

        # Facing direction (updated each frame from x movement)
        self._facing_left = False
        self._prev_x      = float(x)

    def change_ai_state(self, new_state):
        self.ai_state = new_state

    def _dist_to_player(self, player):
        return math.hypot(self.x - player.x, self.y - player.y)

    def _move_towards(self, tx, ty, walls, dt):
        dx = tx - self.x
        dy = ty - self.y
        d  = math.hypot(dx, dy)
        if d < 2:
            return
        dx /= d
        dy /= d
        nx = self.x + dx * self.speed * 90 * dt
        ny = self.y + dy * self.speed * 90 * dt
        if not self._collides(nx, self.y, walls):
            self.x = nx
        if not self._collides(self.x, ny, walls):
            self.y = ny

    def _collides(self, x, y, walls):
        r = self.size
        for wall in walls:
            if (wall.left < x + r and wall.right  > x - r and
                    wall.top  < y + r and wall.bottom > y - r):
                return True
        return False

    def update(self, player, walls, dt, bullets_out):
        if not self.alive:
            return
        # Soul Knight: stay frozen until the room door closes (player entered room)
        if not self.activated:
            return
        if self.hurt_timer  > 0: self.hurt_timer  -= dt
        if self.shoot_timer > 0: self.shoot_timer -= dt

        dist = self._dist_to_player(player)

        # State transitions
        if self.hp / self.max_hp < self.FLEE_HP_PCT and self.ai_state != self.FLEE:
            self.change_ai_state(self.FLEE)
        elif dist > self.CHASE_RANGE and self.ai_state not in (self.IDLE, self.PATROL):
            self.change_ai_state(self.PATROL)
        elif dist <= self.CHASE_RANGE:
            if dist <= self.ATTACK_RANGE:
                self.change_ai_state(self.ATTACK)
            else:
                self.change_ai_state(self.CHASE)

        if self.ai_state == self.IDLE:
            self.patrol_timer += dt
            if self.patrol_timer > 2.0:
                self.change_ai_state(self.PATROL)
                self.patrol_timer = 0

        elif self.ai_state == self.PATROL:
            self.patrol_timer += dt
            if self.patrol_timer > 1.5:
                self.patrol_angle += random.uniform(-0.8, 0.8)
                self.patrol_timer  = 0
            tx = self.x + math.cos(self.patrol_angle) * 40
            ty = self.y + math.sin(self.patrol_angle) * 40
            self._move_towards(tx, ty, walls, dt)

        elif self.ai_state == self.CHASE:
            self._move_towards(player.x, player.y, walls, dt)

        elif self.ai_state == self.ATTACK:
            self._do_attack(player, bullets_out, dt, walls)

        elif self.ai_state == self.FLEE:
            dx = self.x - player.x
            dy = self.y - player.y
            d  = math.hypot(dx, dy) or 1
            tx = self.x + (dx / d) * 80
            ty = self.y + (dy / d) * 80
            self._move_towards(tx, ty, walls, dt)

        # Update facing direction — always look toward the player
        self._facing_left = player.x > self.x
        self._prev_x = self.x

    def _do_attack(self, player, bullets_out, dt, walls):
        self._move_towards(player.x, player.y, walls, dt)

    def take_damage(self, amount):
        if not self.alive:
            return 0
        self.hp -= amount
        self.hurt_timer = 0.15
        if self.hp <= 0:
            self.hp    = 0
            self.alive = False
        return int(amount)

    def drop_loot(self, luk_bonus=0):
        drop_chance = 0.40 + luk_bonus * 0.01
        if random.random() < drop_chance:
            # Soul Knight style: 50% chance weapon, 25% armor, 25% accessory
            roll = random.random()
            if roll < 0.50:
                from item import make_weapon
                weights = {"Common": max(1, 50 - luk_bonus*2), "Rare": 20+luk_bonus,
                           "Epic": 6+luk_bonus//2, "Legendary": 1+luk_bonus//5}
                rarity = random.choices(list(weights.keys()), list(weights.values()), k=1)[0]
                return make_weapon(rarity)
            else:
                return make_random_item(luk_bonus)
        return None

    def draw(self, surface, cam_x=0, cam_y=0):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        r  = self.size

        play_h = SCREEN_H - HUD_H
        if sx < -r*4 or sx > SCREEN_W + r*4 or sy < -r*4 or sy > play_h + r*4:
            return

        # Drop shadow under enemy
        shadow_s = pygame.Surface((r*4, r*2), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_s, (0,0,0,70), (0,0,r*4,r*2))
        surface.blit(shadow_s, (sx-r*2, sy+r//2))

        if self._sprite_right:
            base = self._sprite_left if self._facing_left else self._sprite_right
            self._sprite_hurt_r = None
            self._sprite_hurt_l = None

            if self.hurt_timer > 0:
                # Circular white flash blended onto sprite copy — follows sprite shape
                img = base.copy()
                iw, ih = img.get_size()
                flash_s = pygame.Surface((iw, ih), pygame.SRCALPHA)
                flash_r = min(iw, ih) // 2
                pygame.draw.circle(flash_s, (255, 255, 255, 210),
                                   (iw // 2, ih // 2), flash_r)
                img.blit(flash_s, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            else:
                img = base

            draw_rect = img.get_rect(center=(sx, sy))
            surface.blit(img, draw_rect)
            bar_w = img.get_width()
            bx    = sx - bar_w // 2
            by    = draw_rect.top - 8
        else:
            # Fallback: glow circle
            if self.hurt_timer > 0:
                # White flash ring
                fw = pygame.Surface((r*4+4, r*4+4), pygame.SRCALPHA)
                pygame.draw.circle(fw, (255,255,255,160), (r*2+2,r*2+2), r+2)
                surface.blit(fw, (sx-r*2-2, sy-r*2-2))
                col = (255, 180, 180)
            else:
                # Subtle glow matching enemy color
                gw = pygame.Surface((r*4+4, r*4+4), pygame.SRCALPHA)
                pygame.draw.circle(gw, (*self.color, 50), (r*2+2,r*2+2), r*2)
                surface.blit(gw, (sx-r*2-2, sy-r*2-2))
                col = self.color
            pygame.draw.circle(surface, col, (sx, sy), r)
            # Rim highlight
            hi = tuple(min(255, c+70) for c in col)
            pygame.draw.circle(surface, hi, (sx-r//4, sy-r//4), max(2, r//4))
            pygame.draw.circle(surface, BLACK, (sx, sy), r, 2)
            bar_w = r * 2
            bx    = sx - r
            by    = sy - r - 10

        # ── Enhanced HP bar ────────────────────────────────────
        bar_h = 6
        pct = self.hp / max(1, self.max_hp)
        # Background
        pygame.draw.rect(surface, (20,0,0), (bx-1, by-1, bar_w+2, bar_h+2), border_radius=3)
        pygame.draw.rect(surface, (60,0,0), (bx, by, bar_w, bar_h), border_radius=3)
        # Fill gradient (green → yellow → red)
        fill_w = max(0, int(bar_w * pct))
        if fill_w > 0:
            if pct > 0.5:
                bar_col = (min(255, int(255*(1-pct)*2)), 200, 40)
            elif pct > 0.25:
                bar_col = (255, min(255, int(200*pct*4)), 0)
            else:
                bar_col = (255, 30, 30)
            pygame.draw.rect(surface, bar_col, (bx, by, fill_w, bar_h), border_radius=3)
            # Shine
            bright = tuple(min(255, c+60) for c in bar_col)
            pygame.draw.rect(surface, bright, (bx, by, fill_w, bar_h//2), border_radius=3)
        # Border
        pygame.draw.rect(surface, (150,150,180), (bx-1,by-1,bar_w+2,bar_h+2), 1, border_radius=3)


class MeleeEnemy(Enemy):
    ATTACK_RANGE = 38

    def _do_attack(self, player, bullets_out, dt, walls):
        self._move_towards(player.x, player.y, walls, dt)
        if self.shoot_timer <= 0:
            dist = self._dist_to_player(player)
            if dist < self.ATTACK_RANGE + player.RADIUS:
                player.take_damage(self.atk)
                self.shoot_timer = self.shoot_cd


class RangedEnemy(Enemy):
    ATTACK_RANGE = 230
    FLEE_HP_PCT  = 0.20

    def _do_attack(self, player, bullets_out, dt, walls):
        dist      = self._dist_to_player(player)
        # FIX: use a safe preferred distance; shoot_range default is 0
        preferred = max(150, self.shoot_range * 0.7)
        if dist < preferred * 0.5:
            dx = self.x - player.x
            dy = self.y - player.y
            d  = math.hypot(dx, dy) or 1
            tx = self.x + (dx / d) * 60
            ty = self.y + (dy / d) * 60
            self._move_towards(tx, ty, walls, dt)

        if self.shoot_timer <= 0:
            dx = player.x - self.x
            dy = player.y - self.y
            d  = math.hypot(dx, dy) or 1
            bullets_out.append(EnemyBullet(
                self.x, self.y, dx / d, dy / d, speed=5, damage=self.atk,
                color=self.color
            ))
            self.shoot_timer = self.shoot_cd


class BossEnemy(RangedEnemy):
    ATTACK_RANGE = 270
    FLEE_HP_PCT  = 0.0

    def __init__(self, enemy_type, x, y, stage_level=1):
        super().__init__(enemy_type, x, y, stage_level)
        self.shoot_cd    = 1.2
        self.phase       = 1
        self.burst_count = 3
        # Boss gets a much bigger sprite (x6 of collision size)
        boss_diam = int(self.size * 6)
        self._sprite_right = _load_enemy_image(enemy_type, boss_diam)
        self._sprite_left  = (
            pygame.transform.flip(self._sprite_right, True, False)
            if self._sprite_right else None
        )
        self._sprite_hurt_r = None
        self._sprite_hurt_l = None
        # ── Cinematic timers ──────────────────────────────────
        self.spawn_anim_timer  = 2.2   # plays on activation; scales sprite in
        self.phase_flash_timer = 0.0   # orange flash when entering phase 2
        self._boss_diam        = boss_diam

    def update(self, player, walls, dt, bullets_out):
        # Tick cinematic timers
        if self.spawn_anim_timer > 0:
            self.spawn_anim_timer = max(0.0, self.spawn_anim_timer - dt)
        if self.phase_flash_timer > 0:
            self.phase_flash_timer = max(0.0, self.phase_flash_timer - dt)

        if self.hp < self.max_hp * 0.5 and self.phase == 1:
            self.phase             = 2
            self.shoot_cd          = 0.7
            self.burst_count       = 5
            self.speed            *= 1.3
            self.phase_flash_timer = 1.8   # trigger orange screen flash
        super().update(player, walls, dt, bullets_out)

    def _do_attack(self, player, bullets_out, dt, walls):
        self._move_towards(player.x, player.y, walls, dt)
        if self.shoot_timer <= 0:
            base_angle = math.atan2(player.y - self.y, player.x - self.x)
            spread     = math.pi / (5 if self.phase == 1 else 3)
            count      = self.burst_count
            for i in range(count):
                angle = base_angle + spread * (i - count // 2)
                bullets_out.append(EnemyBullet(
                    self.x, self.y,
                    math.cos(angle), math.sin(angle),
                    speed=6, damage=self.atk
                ))
            self.shoot_timer = self.shoot_cd

    def draw(self, surface, cam_x=0, cam_y=0):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        t  = pygame.time.get_ticks() / 1000.0

        # ── Spawn scale-in animation ───────────────────────────
        spawn_t   = self.spawn_anim_timer        # counts DOWN from 2.2 → 0
        spawn_pct = 1.0 - max(0.0, spawn_t / 2.2)   # 0.0 → 1.0 as animation plays

        # ── Phase-2 screen flash overlay ─────────────────────
        if self.phase_flash_timer > 0:
            alpha = int(min(220, self.phase_flash_timer * 160))
            fl = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            fl.fill((255, 80, 0, alpha))
            surface.blit(fl, (0, 0))
            # Big "PHASE 2" label bursting from boss position
            try:
                pf_font = pygame.font.SysFont("Arial", 46, bold=True)
            except Exception:
                pf_font = pygame.font.Font(None, 54)
            pf_surf = pf_font.render("⚡ PHASE 2 ⚡", True, (255, 240, 60))
            surface.blit(pf_surf, (sx - pf_surf.get_width() // 2,
                                   sy - self.size * 4 - 60))

        # ── Base draw (uses parent which handles sprite + HP bar) ─
        # But we intercept to apply spawn scale
        r  = self.size
        ring_col = ORANGE if self.phase == 2 else YELLOW

        # Pulsing aura (skip during spawn)
        if spawn_pct >= 0.5:
            pulse = int(math.sin(t * 5) * 4)
            gw = pygame.Surface(((self.size+20)*2+4,(self.size+20)*2+4), pygame.SRCALPHA)
            aura_alpha = int(35 * min(1.0, (spawn_pct - 0.5) / 0.5))
            pygame.draw.circle(gw, (*ring_col, aura_alpha),
                               (self.size+22, self.size+22), self.size+18+pulse)
            surface.blit(gw, (sx-self.size-22, sy-self.size-22))

        # Drop shadow
        shadow_s = pygame.Surface((r*4, r*2), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_s, (0,0,0,70), (0,0,r*4,r*2))
        surface.blit(shadow_s, (sx-r*2, sy+r//2))

        # ── Draw sprite / fallback circle with spawn scale ──
        raw_right = self._sprite_right
        raw_left  = self._sprite_left
        if raw_right and spawn_pct < 1.0:
            # Scale sprite by spawn_pct (elastic ease-out)
            ease = 1.0 - (1.0 - spawn_pct) ** 3
            orig_w, orig_h = raw_right.get_size()
            sw = max(2, int(orig_w * ease))
            sh = max(2, int(orig_h * ease))
            raw_right = pygame.transform.smoothscale(raw_right, (sw, sh))
            raw_left  = pygame.transform.smoothscale(
                (self._sprite_left or raw_right), (sw, sh))

        if raw_right:
            base = raw_left if self._facing_left else raw_right
            if self.hurt_timer > 0:
                img = base.copy()
                iw, ih = img.get_size()
                flash_s = pygame.Surface((iw, ih), pygame.SRCALPHA)
                flash_r = min(iw, ih) // 2
                pygame.draw.circle(flash_s, (255, 255, 255, 210),
                                   (iw // 2, ih // 2), flash_r)
                img.blit(flash_s, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            else:
                img = base
            draw_rect = img.get_rect(center=(sx, sy))
            surface.blit(img, draw_rect)
            bar_w = img.get_width()
            bx    = sx - bar_w // 2
            by    = draw_rect.top - 8
        else:
            col = self.color
            if self.hurt_timer > 0:
                col = (255, 180, 180)
            scale_r = max(2, int(r * (1.0 - (1.0 - spawn_pct) ** 3)))
            pygame.draw.circle(surface, col, (sx, sy), scale_r)
            bx = sx - r; by = sy - r - 10

        # ── Double rings ─────────────────────────────────────
        if spawn_pct > 0.4:
            pulse = int(math.sin(t * 5) * 4)
            pygame.draw.circle(surface, ring_col, (sx, sy), self.size + 6 + pulse, 3)
            pygame.draw.circle(surface, WHITE, (sx, sy), self.size + 10 + pulse, 1)

        # ── Phase 2: spinning arc decoration ─────────────────
        if self.phase == 2:
            arc_surf = pygame.Surface(((self.size+16)*2+4,(self.size+16)*2+4), pygame.SRCALPHA)
            ar = self.size + 14
            start_a = int(t * 200) % 360
            pygame.draw.arc(arc_surf,(255,80,20,200),(2,2,ar*2,ar*2),
                            math.radians(start_a),math.radians(start_a+120),3)
            pygame.draw.arc(arc_surf,(255,80,20,200),(2,2,ar*2,ar*2),
                            math.radians(start_a+180),math.radians(start_a+300),3)
            surface.blit(arc_surf,(sx-ar-2,sy-ar-2))

        # ── Shockwave ring during spawn ───────────────────────
        if 0.0 < spawn_t < 2.0:
            ring_r = int((2.0 - spawn_t) / 2.0 * 180)
            ring_alpha = max(0, int(120 * (spawn_t / 2.0)))
            sw2 = pygame.Surface((ring_r*2+4, ring_r*2+4), pygame.SRCALPHA)
            pygame.draw.circle(sw2, (*ring_col, ring_alpha), (ring_r+2, ring_r+2), ring_r, 3)
            surface.blit(sw2, (sx - ring_r - 2, sy - ring_r - 2))


class EliteShooterEnemy(RangedEnemy):
    """
    Soul Knight-style Elite Shooter.
    - HP randomized ±40% at spawn
    - Shoots 3–8 bullets in spread/burst/spiral patterns
    - Glowing ring + health bar with special color
    - One spawned per stage in a dedicated room
    """
    ATTACK_RANGE = 320
    FLEE_HP_PCT  = 0.0

    # Pattern names for variety
    PATTERNS = ["spread", "burst", "spiral", "cross", "double_spiral"]

    def __init__(self, enemy_type, x, y, stage_level=1):
        super().__init__(enemy_type, x, y, stage_level)
        # Randomize HP ±40%
        hp_mult = random.uniform(0.6, 1.4)
        self.max_hp = max(60, int(self.max_hp * hp_mult))
        self.hp     = self.max_hp

        # Pick a random attack pattern
        self.pattern     = random.choice(self.PATTERNS)
        self.shoot_cd    = random.uniform(0.9, 1.6)
        self._orbit_ang  = random.uniform(0, math.tau)   # for spiral
        self._phase_timer = 0.0
        self._phase       = 1
        self._ring_pulse  = 0.0

    def update(self, player, walls, dt, bullets_out):
        self._ring_pulse += dt * 4
        self._phase_timer += dt
        # Phase 2 at 50% HP: faster + more bullets
        if self.hp < self.max_hp * 0.5 and self._phase == 1:
            self._phase    = 2
            self.shoot_cd  = max(0.5, self.shoot_cd * 0.65)
            self.speed    *= 1.25
        super().update(player, walls, dt, bullets_out)

    def _do_attack(self, player, bullets_out, dt, walls):
        """Keep preferred distance, use pattern-based shooting."""
        dist = math.hypot(self.x - player.x, self.y - player.y)
        preferred = 200
        if dist < preferred * 0.6:
            dx = self.x - player.x; dy = self.y - player.y
            d  = math.hypot(dx, dy) or 1
            self._move_towards(self.x + (dx/d)*60, self.y + (dy/d)*60, walls, dt)
        elif dist > preferred * 1.3:
            self._move_towards(player.x, player.y, walls, dt)

        if self.shoot_timer <= 0:
            self._fire_pattern(player, bullets_out)
            self.shoot_timer = self.shoot_cd

    def _fire_pattern(self, player, bullets_out):
        base_angle = math.atan2(player.y - self.y, player.x - self.x)
        bullet_count = 5 if self._phase == 1 else 8
        spd  = 5.5 if self._phase == 1 else 6.5
        dmg  = self.atk

        if self.pattern == "spread":
            # Spread fan toward player
            spread = math.pi / (3 if self._phase == 1 else 2.2)
            for i in range(bullet_count):
                angle = base_angle + spread * (i / max(1, bullet_count - 1) - 0.5)
                bullets_out.append(EnemyBullet(self.x, self.y,
                    math.cos(angle), math.sin(angle), spd, dmg, color=self.color))

        elif self.pattern == "burst":
            # 3-round burst with tiny delay (emulate by firing all at once with slight speed diff)
            for i in range(bullet_count):
                offset = random.uniform(-0.18, 0.18)
                s_var  = spd + random.uniform(-0.5, 0.5)
                bullets_out.append(EnemyBullet(self.x, self.y,
                    math.cos(base_angle + offset), math.sin(base_angle + offset), s_var, dmg, color=self.color))

        elif self.pattern == "spiral":
            # Rotating ring of bullets
            self._orbit_ang += math.pi / 4
            for i in range(bullet_count):
                angle = self._orbit_ang + (math.tau / bullet_count) * i
                bullets_out.append(EnemyBullet(self.x, self.y,
                    math.cos(angle), math.sin(angle), spd * 0.9, dmg, color=self.color))

        elif self.pattern == "cross":
            # Cross + diagonals (8-way)
            count = 8 if self._phase == 2 else 4
            for i in range(count):
                angle = (math.tau / count) * i
                bullets_out.append(EnemyBullet(self.x, self.y,
                    math.cos(angle), math.sin(angle), spd, dmg, color=self.color))

        elif self.pattern == "double_spiral":
            # Two interleaved spirals
            self._orbit_ang += math.pi / 6
            half = bullet_count // 2
            for i in range(half):
                for offset in (0, math.pi):
                    angle = self._orbit_ang + (math.tau / half) * i + offset
                    bullets_out.append(EnemyBullet(self.x, self.y,
                        math.cos(angle), math.sin(angle), spd * 0.85, dmg, color=self.color))

    def draw(self, surface, cam_x=0, cam_y=0):
        super().draw(surface, cam_x, cam_y)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        r  = self.size

        # Pulsing glow ring
        pulse = int(math.sin(self._ring_pulse) * 4)
        ring_col = self.color if self._phase == 1 else (255, 80, 80)
        pygame.draw.circle(surface, ring_col, (sx, sy), r + 6 + pulse, 3)
        pygame.draw.circle(surface, (255, 255, 255), (sx, sy), r + 8 + pulse, 1)

        # "ELITE" label above
        try:
            fnt = pygame.font.SysFont("Arial", 10, bold=True)
            lbl = fnt.render("ELITE", True, ring_col)
            surface.blit(lbl, (sx - lbl.get_width()//2, sy - r - 22))
        except Exception:
            pass

        # Phase indicator dot
        if self._phase == 2:
            pygame.draw.circle(surface, (255, 80, 80), (sx, sy - r - 12), 4)


def make_enemy(enemy_type, x, y, stage_level=1):
    data = ENEMY_DATA.get(enemy_type, {})
    ai   = data.get("ai", "shoot")
    if "boss" in ai:
        return BossEnemy(enemy_type, x, y, stage_level)
    elif "elite_shoot" in ai:
        return EliteShooterEnemy(enemy_type, x, y, stage_level)
    else:
        # ALL regular enemies are ranged (Soul Knight style)
        return RangedEnemy(enemy_type, x, y, stage_level)


class EnemyBullet:
    """Projectile fired by an enemy."""

    def __init__(self, x, y, dx, dy, speed=5, damage=10, color=None):
        self.x      = float(x)
        self.y      = float(y)
        self.dx     = dx
        self.dy     = dy
        self.speed  = speed
        self.damage = damage
        self.alive  = True
        self.radius = 10
        self.color  = color or ORANGE

    # FIX: use world map bounds (MAP_W*TILE, MAP_H*TILE) not screen pixels.
    # Bullets live in world-space; SCREEN_W/H caused instant death off-screen.
    def update(self, dt, walls=None):
        self.x += self.dx * self.speed * 60 * dt
        self.y += self.dy * self.speed * 60 * dt

        if walls:
            for wall in walls:
                if wall.collidepoint(self.x, self.y):
                    self.alive = False
                    return

        map_w = MAP_W * TILE
        map_h = MAP_H * TILE
        if self.x < 0 or self.x > map_w or self.y < 0 or self.y > map_h:
            self.alive = False

    def draw(self, surface, cam_x=0, cam_y=0):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        r  = self.radius
        # Outer glow
        gw = pygame.Surface((r*4+4,r*4+4), pygame.SRCALPHA)
        pygame.draw.circle(gw, (*self.color,50), (r*2+2,r*2+2), r*2)
        surface.blit(gw, (sx-r*2-2, sy-r*2-2))
        # Mid ring
        pygame.draw.circle(surface, self.color, (sx, sy), r+1)
        # Body
        pygame.draw.circle(surface, self.color, (sx, sy), r)
        # Inner bright core
        inner = tuple(min(255, c+100) for c in self.color)
        pygame.draw.circle(surface, inner, (sx, sy), max(1, r-2))
        # White hot center dot
        pygame.draw.circle(surface, (255,255,255), (sx,sy), max(1, r-4))