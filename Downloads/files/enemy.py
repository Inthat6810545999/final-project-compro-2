"""
enemy.py  –  Enemy base class + subclasses (OOP Class 2)
AI states: IDLE, PATROL, CHASE, ATTACK, FLEE
"""
import math
import random
import pygame
from constants import (
    ENEMY_DATA, WHITE, RED, GREEN, YELLOW, ORANGE, BLACK, GRAY,
    SCREEN_W, SCREEN_H, HUD_H
)
from item import make_random_item


# ─────────────────────────────────────────────────────────────
class Enemy:
    """
    Base class for all enemy bots.
    Subclasses: MeleeEnemy, RangedEnemy, BossEnemy
    """

    # AI States
    IDLE   = "IDLE"
    PATROL = "PATROL"
    CHASE  = "CHASE"
    ATTACK = "ATTACK"
    FLEE   = "FLEE"

    CHASE_RANGE  = 280
    ATTACK_RANGE = 40   # overridden in ranged
    FLEE_HP_PCT  = 0.15

    def __init__(self, enemy_type, x, y, stage_level=1):
        data = ENEMY_DATA.get(enemy_type, ENEMY_DATA["Slime"])
        self.enemy_type = enemy_type
        self.x          = float(x)
        self.y          = float(y)

        scale       = 1.0 + (stage_level - 1) * 0.18
        self.max_hp = int(data["hp"] * scale)
        self.hp     = self.max_hp
        self.atk = int(data["atk"] * scale * (3 + stage_level * 0.05))
        self.speed  = data["speed"]
        self.size   = data["size"]
        self.color  = data["color"]
        self.exp_reward = int(data["exp"] * scale)
        self.shoot_range = data.get("range", 0)
        self.can_shoot   = data.get("shoot", False)

        self.ai_state   = self.IDLE
        self.alive      = True
        self.shoot_timer = 0.0
        self.shoot_cd    = 1.5
        self.patrol_angle = random.uniform(0, math.tau)
        self.patrol_timer = 0.0
        self.hurt_timer  = 0.0

        # Drop flag
        self.loot_table = ["weapon", "armor", "accessory"]

    # ── AI state machine ─────────────────────────────────────
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
        if self.hurt_timer > 0:
            self.hurt_timer -= dt
        if self.shoot_timer > 0:
            self.shoot_timer -= dt

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

        # Execute state
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
        # Default: melee approach
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
        """Return an Item or None based on drop chance."""
        drop_chance = 0.35 + luk_bonus * 0.01
        if random.random() < drop_chance:
            return make_random_item(luk_bonus)
        return None

    def draw(self, surface, cam_x=0, cam_y=0):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        r  = self.size

        # Skip if off screen
        play_h = SCREEN_H - 80
        if sx < -r or sx > SCREEN_W + r or sy < -r or sy > play_h + r:
            return

        # Flash red on hurt
        col = (255, 80, 80) if self.hurt_timer > 0 else self.color
        pygame.draw.circle(surface, col, (sx, sy), r)
        pygame.draw.circle(surface, BLACK, (sx, sy), r, 2)

        # Eye
        pygame.draw.circle(surface, WHITE, (sx - r//3, sy - r//4), max(3, r//5))

        # HP bar
        bar_w = r * 2
        bx    = sx - r
        by    = sy - r - 8
        pygame.draw.rect(surface, (80, 0, 0), (bx, by, bar_w, 5))
        fill  = int(bar_w * self.hp / max(1, self.max_hp))
        pygame.draw.rect(surface, RED, (bx, by, fill, 5))


# ─────────────────────────────────────────────────────────────
class MeleeEnemy(Enemy):
    """Chases and attacks player in melee range."""

    ATTACK_RANGE = 38

    def _do_attack(self, player, bullets_out, dt, walls):
        self._move_towards(player.x, player.y, walls, dt)
        if self.shoot_timer <= 0:
            dist = self._dist_to_player(player)
            if dist < self.ATTACK_RANGE + player.RADIUS:
                player.take_damage(self.atk)
                self.shoot_timer = self.shoot_cd


# ─────────────────────────────────────────────────────────────
class RangedEnemy(Enemy):
    """Keeps distance and fires projectiles."""

    ATTACK_RANGE = 230
    FLEE_HP_PCT  = 0.20

    def _do_attack(self, player, bullets_out, dt, walls):
        dist = self._dist_to_player(player)
        preferred = self.shoot_range * 0.7
        if dist < preferred * 0.5:
            # Too close, back away
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
                self.x, self.y,
                dx / d, dy / d,
                speed=5, damage=self.atk
            ))
            self.shoot_timer = self.shoot_cd


# ─────────────────────────────────────────────────────────────
class BossEnemy(RangedEnemy):
    """Boss: shoots multiple bullets in a spread pattern."""

    ATTACK_RANGE = 270
    FLEE_HP_PCT  = 0.0   # bosses never flee

    def __init__(self, enemy_type, x, y, stage_level=1):
        super().__init__(enemy_type, x, y, stage_level)
        self.shoot_cd   = 1.2
        self.phase      = 1           # phases based on HP
        self.burst_count = 3

    def update(self, player, walls, dt, bullets_out):
        # Phase 2 at <50% HP
        if self.hp < self.max_hp * 0.5 and self.phase == 1:
            self.phase        = 2
            self.shoot_cd     = 0.7
            self.burst_count  = 5
            self.speed       *= 1.3
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
        # Phase indicator ring
        ring_col = ORANGE if self.phase == 2 else YELLOW
        pygame.draw.circle(surface, ring_col, (sx, sy), self.size + 4, 3)


# ─────────────────────────────────────────────────────────────
def make_enemy(enemy_type, x, y, stage_level=1):
    data = ENEMY_DATA.get(enemy_type, {})
    ai   = data.get("ai", "chase")
    if "boss" in ai:
        return BossEnemy(enemy_type, x, y, stage_level)
    elif data.get("shoot", False):
        return RangedEnemy(enemy_type, x, y, stage_level)
    else:
        return MeleeEnemy(enemy_type, x, y, stage_level)


# ─────────────────────────────────────────────────────────────
class EnemyBullet:
    """Projectile fired by an enemy."""

    def __init__(self, x, y, dx, dy, speed=5, damage=10):
        self.x      = float(x)
        self.y      = float(y)
        self.dx     = dx
        self.dy     = dy
        self.speed  = speed
        self.damage = damage
        self.alive  = True
        self.radius = 6

    def update(self, dt):
        self.x += self.dx * self.speed * 60 * dt
        self.y += self.dy * self.speed * 60 * dt
        # Die off screen
        play_h = SCREEN_H - 80
        if self.x < 0 or self.x > SCREEN_W or self.y < 0 or self.y > play_h:
            self.alive = False

    def draw(self, surface, cam_x=0, cam_y=0):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        pygame.draw.circle(surface, ORANGE, (sx, sy), self.radius)
        pygame.draw.circle(surface, (255,200,0), (sx, sy), self.radius - 2)
