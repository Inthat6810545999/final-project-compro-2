"""
hit_fx.py  –  Hit-impact VFX helpers
=====================================
Drop this file next to game_manager.py, then follow the 3-line patch
instructions at the bottom of this file to wire it into the game.

All effects reuse the existing SkillParticle system in bullet.py —
no new classes or dependencies required.

Effects produced:
  spawn_hit_fx()        – bullet hits enemy  (sparks + ring, crit = flashier)
  spawn_player_hit_fx() – enemy bullet hits player (red sparks + ring)
  spawn_kill_fx()       – enemy dies (bigger burst + orbs)
"""

from __future__ import annotations
import math
import random
from bullet import SkillParticle


# ─────────────────────────────────────────────────────────────────────────────
#  Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _rnd(lo, hi):
    return random.uniform(lo, hi)


def _sp(fx_list: list, **kw):
    """Append a SkillParticle to the given list."""
    fx_list.append(SkillParticle(**kw))


# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────

def spawn_hit_fx(fx_list: list, x: float, y: float,
                 is_crit: bool = False,
                 bullet_color: tuple = (255, 230, 80)) -> None:
    """
    Call when a player bullet hits an enemy.

    Parameters
    ----------
    fx_list      : GameManager.skill_fx  (list of SkillParticle)
    x, y         : world-space impact position
    is_crit      : True for critical hits → bigger, brighter VFX
    bullet_color : colour of the bullet that landed the hit
    """

    # ── 1. Shockwave ring ────────────────────────────────────────────────────
    ring_r   = 52 if is_crit else 32
    ring_col = (255, 240, 80) if is_crit else tuple(min(255, c + 60) for c in bullet_color)
    _sp(fx_list, ptype='ring', x=x, y=y,
        color=ring_col, ring_max_r=ring_r, ring_w=(3 if is_crit else 2),
        life=(0.22 if is_crit else 0.16))

    # ── 2. Spark burst ───────────────────────────────────────────────────────
    n_sparks = 12 if is_crit else 7
    for _ in range(n_sparks):
        angle = _rnd(0, math.tau)
        spd   = _rnd(90, 260) if is_crit else _rnd(60, 180)
        sz    = _rnd(3, 7)    if is_crit else _rnd(2, 5)
        # Mix bullet colour with a bright highlight
        spark_col = (
            min(255, bullet_color[0] + random.randint(0, 80)),
            min(255, bullet_color[1] + random.randint(0, 40)),
            min(255, bullet_color[2] + random.randint(0, 20)),
        )
        _sp(fx_list, ptype='spark',
            x=x, y=y,
            vx=math.cos(angle) * spd,
            vy=math.sin(angle) * spd,
            ay=150,                         # gravity pulls them down
            color=spark_col, size=sz,
            life=_rnd(0.18, 0.40))

    # ── 3. Small orb pop (fleshy hit feel) ───────────────────────────────────
    for _ in range(3 if is_crit else 1):
        angle = _rnd(0, math.tau)
        _sp(fx_list, ptype='orb',
            x=x, y=y,
            vx=math.cos(angle) * _rnd(20, 55),
            vy=math.sin(angle) * _rnd(20, 55),
            color=bullet_color, size=_rnd(5, 10),
            life=_rnd(0.10, 0.22))

    # ── 4. Crit-only: extra white flash ring + star lines ────────────────────
    if is_crit:
        # Bright inner ring that pops first
        _sp(fx_list, ptype='ring', x=x, y=y,
            color=(255, 255, 220), ring_max_r=18, ring_w=4, life=0.10)

        # Star lines: 4 diagonal streaks
        for i in range(4):
            a    = i * (math.pi / 2) + _rnd(-0.15, 0.15)
            dist = _rnd(24, 44)
            x2   = x + math.cos(a) * dist
            y2   = y + math.sin(a) * dist
            _sp(fx_list, ptype='line',
                x=x, y=y, x2=x2, y2=y2,
                color=(255, 255, 160), ring_w=2,
                life=0.14)


# ─────────────────────────────────────────────────────────────────────────────

def spawn_player_hit_fx(fx_list: list, x: float, y: float) -> None:
    """
    Call when an enemy bullet hits the player.
    Red/orange sparks + expanding red ring.
    """

    # Impact ring
    _sp(fx_list, ptype='ring', x=x, y=y,
        color=(255, 50, 30), ring_max_r=44, ring_w=3, life=0.20)

    # Red spark burst
    for _ in range(10):
        angle = _rnd(0, math.tau)
        spd   = _rnd(70, 200)
        col   = random.choice([(255, 60, 40), (255, 140, 40), (220, 30, 20)])
        _sp(fx_list, ptype='spark',
            x=x, y=y,
            vx=math.cos(angle) * spd,
            vy=math.sin(angle) * spd,
            ay=120,
            color=col, size=_rnd(2, 6),
            life=_rnd(0.15, 0.35))

    # Small red flash tint (very brief)
    _sp(fx_list, ptype='flash',
        color=(200, 30, 10), alpha_start=38, life=0.12)


# ─────────────────────────────────────────────────────────────────────────────

def spawn_wall_hit_fx(fx_list: list, x: float, y: float,
                      bullet_dx: float = 0.0, bullet_dy: float = -1.0,
                      bullet_color: tuple = (255, 230, 80)) -> None:
    """
    Call when a bullet hits a wall.

    Parameters
    ----------
    fx_list      : GameManager.skill_fx
    x, y         : world-space impact position (bullet's last position)
    bullet_dx/dy : normalised travel direction of the bullet
                   (used to fan sparks back toward the shooter)
    bullet_color : colour of the bullet
    """
    # ── 1. Small debris ring (tight, fast-fading) ────────────────────────────
    _sp(fx_list, ptype='ring', x=x, y=y,
        color=(180, 160, 120), ring_max_r=18, ring_w=2, life=0.12)

    # ── 2. Stone-dust sparks (grey/tan) fanning back from impact ─────────────
    # Reflect direction: sparks fly opposite to bullet travel + spread
    back_angle = math.atan2(-bullet_dy, -bullet_dx)   # 180° from travel
    dust_cols  = [(200, 185, 150), (160, 145, 110), (220, 200, 160)]
    for _ in range(9):
        spread = _rnd(-0.9, 0.9)                      # ±~52° cone
        angle  = back_angle + spread
        spd    = _rnd(40, 140)
        col    = random.choice(dust_cols)
        sz     = _rnd(2, 5)
        _sp(fx_list, ptype='spark',
            x=x, y=y,
            vx=math.cos(angle) * spd,
            vy=math.sin(angle) * spd,
            ay=180,                                   # gravity
            color=col, size=sz,
            life=_rnd(0.12, 0.28))

    # ── 3. Tiny bullet-colour flash (the bullet itself exploding) ────────────
    for _ in range(4):
        spread = _rnd(-0.5, 0.5)
        angle  = back_angle + spread
        spd    = _rnd(60, 160)
        _sp(fx_list, ptype='spark',
            x=x, y=y,
            vx=math.cos(angle) * spd,
            vy=math.sin(angle) * spd,
            ay=200,
            color=bullet_color, size=_rnd(1.5, 4),
            life=_rnd(0.08, 0.18))


def spawn_kill_fx(fx_list: list, x: float, y: float,
                  is_boss: bool = False) -> None:
    """
    Call when an enemy is killed.
    Bigger burst of orbs + large ring; boss death = even more dramatic.
    """
    burst_r = 90 if is_boss else 55
    n_orbs  = 16 if is_boss else 8
    n_spark = 20 if is_boss else 10

    # Large shockwave ring
    _sp(fx_list, ptype='ring', x=x, y=y,
        color=(255, 200, 50) if is_boss else (200, 200, 200),
        ring_max_r=burst_r, ring_w=(5 if is_boss else 3),
        life=(0.45 if is_boss else 0.28))

    if is_boss:
        _sp(fx_list, ptype='ring', x=x, y=y,
            color=(255, 100, 20), ring_max_r=burst_r * 1.5,
            ring_w=4, life=0.55)

    # Flying orbs in all directions
    for _ in range(n_orbs):
        angle = _rnd(0, math.tau)
        spd   = _rnd(40, 140) if not is_boss else _rnd(60, 200)
        col   = random.choice(
            [(255, 220, 50), (255, 160, 30), (240, 80, 20)]
        ) if is_boss else random.choice(
            [(220, 220, 220), (200, 200, 255), (160, 200, 255)]
        )
        _sp(fx_list, ptype='orb',
            x=x, y=y,
            vx=math.cos(angle) * spd,
            vy=math.sin(angle) * spd - 40,   # slight upward bias
            color=col, size=_rnd(6, 16),
            life=_rnd(0.30, 0.65))

    # Spark shower
    for _ in range(n_spark):
        angle = _rnd(0, math.tau)
        spd   = _rnd(100, 320)
        _sp(fx_list, ptype='spark',
            x=x, y=y,
            vx=math.cos(angle) * spd,
            vy=math.sin(angle) * spd,
            ay=200,
            color=(255, 240, 120), size=_rnd(2, 6),
            life=_rnd(0.20, 0.50))

    if is_boss:
        _sp(fx_list, ptype='flash',
            color=(255, 180, 20), alpha_start=60, life=0.25)


# =============================================================================
#  HOW TO PATCH game_manager.py  (3 changes)
# =============================================================================
#
#  STEP 1 — Add import at top of game_manager.py  (after "from bullet import …")
#  ─────────────────────────────────────────────────────────────────────────────
#  from hit_fx import spawn_hit_fx, spawn_player_hit_fx, spawn_kill_fx, spawn_wall_hit_fx
#
#
#  STEP 2 — Bullet hits enemy  (around line 1710 in game_manager.py)
#  ─────────────────────────────────────────────────────────────────────────────
#  Find this block:
#
#      if dist < b.radius + e.size:
#          actual = e.take_damage(b.damage)
#          b.hit_set.add(id(e))
#          col   = GOLD if b.is_crit else WHITE
#          label = f"{'CRIT! ' if b.is_crit else ''}{actual}"
#          self._add_fx(e.x, e.y - e.size, label, col)
#          self.sfx.play("hit_enemy")
#
#  Add ONE line after  self.sfx.play("hit_enemy"):
#
#          spawn_hit_fx(self.skill_fx, e.x, e.y - e.size // 2,
#                       is_crit=b.is_crit, bullet_color=b.color)
#
#
#  STEP 3 — Enemy bullet hits player  (around line 1730 in game_manager.py)
#  ─────────────────────────────────────────────────────────────────────────────
#  Find this block:
#
#      if math.hypot(eb.x - p.x, eb.y - p.y) < eb.radius + p.RADIUS:
#          dmg = p.take_damage(eb.damage)
#          eb.alive = False
#          if dmg == -1:
#              self._add_fx(p.x, p.y - 30, "DODGE!", CYAN, 20)
#          elif dmg >= 0:
#              self.sfx.play("hit_player")
#
#  Add ONE line after  self.sfx.play("hit_player"):
#
#              spawn_player_hit_fx(self.skill_fx, p.x, p.y)
#
#
#  STEP 4 (optional) — Enemy dies
#  ─────────────────────────────────────────────────────────────────────────────
#  Find this block (around line 1745):
#
#      for e in list(self.enemies):
#          e.update(p, walls, dt, self.e_bullets)
#          if not e.alive:
#              self._last_enemy_pos = (e.x, e.y)
#              gold_drop = random.randint(...)
#
#  Add after the  if not e.alive:  line, BEFORE the gold drop:
#
#              from enemy import BossEnemy as _BEfx
#              spawn_kill_fx(self.skill_fx, e.x, e.y,
#                            is_boss=isinstance(e, _BEfx))
#
# =============================================================================
