"""
enemy.py  –  Enemy base class + subclasses
AI states: IDLE, PATROL, CHASE, ATTACK, FLEE
Fixes:
  - EnemyBullet.update() now accepts (dt, walls=None) to match game_manager call
  - Hardcoded 80 replaced with HUD_H import
"""
import math
import random
import pygame
from constants import (
    ENEMY_DATA, WHITE, RED, GREEN, YELLOW, ORANGE, BLACK, GRAY,
    SCREEN_W, SCREEN_H, HUD_H,   # FIX: import HUD_H instead of using magic 80
)
from item import make_random_item


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
        nx = self.x + dx * self.speed * 60 * dt
        ny = self.y + dy * self.speed * 60 * dt
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
        return amount

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

        # FIX: use HUD_H constant instead of magic 80
        play_h = SCREEN_H - HUD_H
        if sx < -r or sx > SCREEN_W + r or sy < -r or sy > play_h + r:
            return

        col = (255, 80, 80) if self.hurt_timer > 0 else self.color
        pygame.draw.circle(surface, col, (sx, sy), r)
        pygame.draw.circle(surface, BLACK, (sx, sy), r, 2)
        pygame.draw.circle(surface, WHITE, (sx - r // 3, sy - r // 4), max(3, r // 5))

        bar_w = r * 2
        bx    = sx - r
        by    = sy - r - 8
        pygame.draw.rect(surface, (80, 0, 0), (bx, by, bar_w, 5))
        fill = int(bar_w * self.hp / max(1, self.max_hp))
        pygame.draw.rect(surface, RED, (bx, by, fill, 5))


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
        preferred = self.shoot_range * 0.7
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

    def update(self, player, walls, dt, bullets_out):
        if self.hp < self.max_hp * 0.5 and self.phase == 1:
            self.phase       = 2
            self.shoot_cd    = 0.7
            self.burst_count = 5
            self.speed      *= 1.3
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
        super().draw(surface, cam_x, cam_y)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        ring_col = ORANGE if self.phase == 2 else YELLOW
        pygame.draw.circle(surface, ring_col, (sx, sy), self.size + 4, 3)


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
        self.radius = 6
        self.color  = color or ORANGE

    # FIX: signature was (self, dt) — game_manager passes (dt, walls)
    def update(self, dt, walls=None):
        self.x += self.dx * self.speed * 60 * dt
        self.y += self.dy * self.speed * 60 * dt

        # Wall collision (optional — only if walls provided)
        if walls:
            for wall in walls:
                if wall.collidepoint(self.x, self.y):
                    self.alive = False
                    return

        # FIX: use HUD_H constant instead of magic 80
        play_h = SCREEN_H - HUD_H
        if self.x < 0 or self.x > SCREEN_W or self.y < 0 or self.y > play_h:
            self.alive = False

    def draw(self, surface, cam_x=0, cam_y=0):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        # Outer glow ring for elite bullets (slightly larger)
        if self.color != ORANGE:
            pygame.draw.circle(surface, self.color, (sx, sy), self.radius + 2)
        pygame.draw.circle(surface, self.color, (sx, sy), self.radius)
        # Inner bright core
        inner = tuple(min(255, c + 80) for c in self.color)
        pygame.draw.circle(surface, inner, (sx, sy), self.radius - 2)
