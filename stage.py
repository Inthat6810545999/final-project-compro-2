"""
stage.py  –  Stage & Room generation using BSP
  + Room doors (close on enter, open on clear)
  + Health fountains (random rooms, press E to heal)
"""
import random
import math
import pygame
from constants import (
    STAGE_CONFIGS, TILE, SCREEN_W, SCREEN_H, HUD_H,
    DARK_GRAY, GRAY, WHITE, BLACK, GREEN, YELLOW,
    DARK_BROWN, BROWN, DARK_RED, DARK_GREEN, LIGHT_BLUE, PURPLE, RED, GOLD, ORANGE
)
from enemy import make_enemy


# ─────────────────────────────────────────────────────────────
class BSPNode:
    MIN_ROOM = 5

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.left  = None
        self.right = None
        self.room  = None

    def split(self, depth=0):
        if depth <= 0:
            self._make_room(); return
        if self.w > self.h:
            min_split = self.MIN_ROOM + 1
            if self.w < min_split * 2: self._make_room(); return
            cut = random.randint(min_split, self.w - min_split)
            self.left  = BSPNode(self.x,      self.y, cut,          self.h)
            self.right = BSPNode(self.x + cut, self.y, self.w - cut, self.h)
        else:
            min_split = self.MIN_ROOM + 1
            if self.h < min_split * 2: self._make_room(); return
            cut = random.randint(min_split, self.h - min_split)
            self.left  = BSPNode(self.x, self.y,       self.w, cut)
            self.right = BSPNode(self.x, self.y + cut,  self.w, self.h - cut)
        self.left.split(depth - 1)
        self.right.split(depth - 1)

    def _make_room(self):
        pad = 1
        rw = random.randint(self.MIN_ROOM, max(self.MIN_ROOM, self.w - pad * 2))
        rh = random.randint(self.MIN_ROOM, max(self.MIN_ROOM, self.h - pad * 2))
        rx = self.x + random.randint(pad, max(pad, self.w - rw - pad))
        ry = self.y + random.randint(pad, max(pad, self.h - rh - pad))
        self.room = pygame.Rect(rx, ry, rw, rh)

    def get_rooms(self):
        if self.room: return [self.room]
        rooms = []
        if self.left:  rooms += self.left.get_rooms()
        if self.right: rooms += self.right.get_rooms()
        return rooms

    def get_room_for_self(self):
        if self.room: return self.room
        if self.left:  return self.left.get_room_for_self()
        if self.right: return self.right.get_room_for_self()

    def connect(self):
        corridors = []
        if self.left and self.right:
            corridors += self.left.connect()
            corridors += self.right.connect()
            ra = self.left.get_room_for_self()
            rb = self.right.get_room_for_self()
            if ra and rb:
                ax, ay = ra.centerx, ra.centery
                bx, by = rb.centerx, rb.centery
                corridors.append(pygame.Rect(min(ax,bx), ay-1, abs(ax-bx)+1, 2))
                corridors.append(pygame.Rect(bx-1, min(ay,by), 2, abs(ay-by)+1))
        return corridors


# ─────────────────────────────────────────────────────────────
class Room:
    """Single room with doors and optional health fountain."""

    FOUNTAIN_CHANCE = 0.30   # 30% of eligible rooms get a fountain

    def __init__(self, rect, is_boss=False):
        self.rect    = rect
        self.is_boss = is_boss
        self.cleared = False
        self.visited = False
        self.cx = (rect.x + rect.w // 2) * TILE + TILE // 2
        self.cy = (rect.y + rect.h // 2) * TILE + TILE // 2

        # Door system
        self.door_rects  = []   # list of pygame.Rect (pixel) — corridor entry tiles
        self.doors_open  = True  # start open; close when player enters with enemies

        # Fountain
        self.has_fountain   = False
        self.fountain_used  = False
        self.fountain_x     = self.cx
        self.fountain_y     = self.cy
        self._bob           = 0.0

    def get_spawn_points(self, n):
        pts = []
        for _ in range(n):
            tx = random.randint(self.rect.x + 1, self.rect.right - 2)
            ty = random.randint(self.rect.y + 1, self.rect.bottom - 2)
            pts.append((tx * TILE + TILE // 2, ty * TILE + TILE // 2))
        return pts

    def contains_pixel(self, px, py):
        rx = self.rect.x * TILE
        ry = self.rect.y * TILE
        rw = self.rect.w * TILE
        rh = self.rect.h * TILE
        return rx <= px <= rx + rw and ry <= py <= ry + rh

    def enemies_alive_in(self, enemies):
        return [e for e in enemies if e.alive and self.contains_pixel(e.x, e.y)]

    # ── Fountain interaction ──────────────────────────────────
    def near_fountain(self, player):
        if not self.has_fountain or self.fountain_used:
            return False
        dist = math.hypot(self.fountain_x - player.x, self.fountain_y - player.y)
        return dist < 55

    def use_fountain(self, player):
        if self.fountain_used:
            return 0
        heal = int(player.max_hp * 0.5)
        player.heal(heal)
        self.fountain_used = True
        return heal

    def update(self, dt):
        self._bob += dt * 2.5

    # ── Draw fountain ─────────────────────────────────────────
    def draw_fountain(self, surface, cam_x, cam_y, player=None):
        if not self.has_fountain:
            return
        sx = int(self.fountain_x - cam_x)
        sy = int(self.fountain_y - cam_y) + int(math.sin(self._bob) * 4)

        if self.fountain_used:
            # Greyed out pedestal
            pygame.draw.rect(surface, (60, 60, 60),   (sx-14, sy+6,  28, 16), border_radius=4)
            pygame.draw.rect(surface, (40, 40, 40),   (sx-10, sy-4,  20, 12), border_radius=3)
            pygame.draw.rect(surface, (80, 80, 80),   (sx-14, sy+6,  28, 16), 2, border_radius=4)
            return

        # Glow aura
        t = self._bob
        glow_r = 28 + int(math.sin(t * 2) * 4)
        glow_surf = pygame.Surface((glow_r*2+4, glow_r*2+4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 60, 60, 50), (glow_r+2, glow_r+2), glow_r)
        surface.blit(glow_surf, (sx - glow_r - 2, sy - glow_r - 2))

        # Pedestal base
        pygame.draw.rect(surface, (100, 70, 40),  (sx-14, sy+6,  28, 16), border_radius=4)
        pygame.draw.rect(surface, (140, 100, 60), (sx-14, sy+6,  28, 16), 2, border_radius=4)
        # Column
        pygame.draw.rect(surface, (120, 85, 50),  (sx-10, sy-4,  20, 12), border_radius=3)
        pygame.draw.rect(surface, (160, 120, 70), (sx-10, sy-4,  20, 12), 2, border_radius=3)

        # Heart icon
        hcol = (220, 40, 40)
        hcol2 = (255, 100, 100)
        s = 10
        # Two circles + triangle
        pygame.draw.circle(surface, hcol, (sx-s//2, sy-s//4-2), s//2)
        pygame.draw.circle(surface, hcol, (sx+s//2, sy-s//4-2), s//2)
        pts = [(sx-s, sy-s//4-2), (sx, sy+s-2), (sx+s, sy-s//4-2)]
        pygame.draw.polygon(surface, hcol, pts)
        # Highlight
        pygame.draw.circle(surface, hcol2, (sx-s//2-1, sy-s//4-4), s//4)

        # "E" prompt if player nearby
        if player and self.near_fountain(player):
            pulse = int(math.sin(self._bob * 4) * 2)
            badge = pygame.Rect(sx+14, sy-18, 22+pulse, 22+pulse)
            pygame.draw.rect(surface, (20,20,30), badge, border_radius=4)
            pygame.draw.rect(surface, GOLD, badge, 2, border_radius=4)
            font = pygame.font.SysFont("Arial", 13, bold=True)
            e_surf = font.render("E", True, GOLD)
            surface.blit(e_surf, (badge.x+5+pulse//2, badge.y+3+pulse//2))
            tip = font.render("Heal 50%", True, (255,180,180))
            surface.blit(tip, (sx - tip.get_width()//2, sy - 36))

    # ── Draw doors ────────────────────────────────────────────
    def draw_doors(self, surface, cam_x, cam_y):
        if self.doors_open or not self.door_rects:
            return
        t = pygame.time.get_ticks() / 1000.0
        for dr in self.door_rects:
            sx = dr.x - int(cam_x)
            sy = dr.y - int(cam_y)
            w, h = dr.w, dr.h

            # ── Background: dark stone ────────────────────────
            pygame.draw.rect(surface, (18, 12, 12), (sx, sy, w, h))

            # ── Outer stone frame ─────────────────────────────
            frame_col = (70, 55, 38)
            frame_hi  = (110, 85, 52)
            pygame.draw.rect(surface, frame_col, (sx, sy, w, h), 5)
            pygame.draw.rect(surface, frame_hi,  (sx+1, sy+1, w-2, h-2), 1)

            # ── Vertical iron bars ────────────────────────────
            pulse    = math.sin(t * 2.5) * 0.12 + 0.88   # 0.76 – 1.0
            bar_dark = (50, 55, 65)
            bar_mid  = (int(100 * pulse), int(108 * pulse), int(125 * pulse))
            bar_hi   = (int(170 * pulse), int(185 * pulse), int(210 * pulse))

            num_bars = 3
            bar_w    = 5
            inner_w  = w - 10
            spacing  = inner_w // (num_bars + 1)

            for i in range(num_bars):
                bx = sx + 5 + spacing * (i + 1) - bar_w // 2
                # Shadow side
                pygame.draw.rect(surface, bar_dark, (bx,   sy+5, bar_w,   h-10), border_radius=2)
                # Main bar
                pygame.draw.rect(surface, bar_mid,  (bx,   sy+5, bar_w-1, h-10), border_radius=2)
                # Highlight streak
                pygame.draw.rect(surface, bar_hi,   (bx+1, sy+6, 2,       h-12), border_radius=1)
                # Rivets (top & bottom)
                for ry_off in [h // 5, 4 * h // 5]:
                    cx = bx + bar_w // 2
                    cy = sy + ry_off
                    pygame.draw.circle(surface, bar_mid, (cx, cy), 4)
                    pygame.draw.circle(surface, bar_hi,  (cx-1, cy-1), 2)

            # ── Horizontal crossbar (centre) ──────────────────
            cross_y = sy + h // 2 - 2
            pygame.draw.rect(surface, bar_dark, (sx+5, cross_y,   w-10, 6), border_radius=2)
            pygame.draw.rect(surface, bar_mid,  (sx+5, cross_y,   w-11, 5), border_radius=2)
            pygame.draw.rect(surface, bar_hi,   (sx+6, cross_y+1, w-13, 2))

            # ── Red warning glow border (pulsing) ─────────────
            glow_a = int(70 + math.sin(t * 3) * 45)
            glow_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (200, 30, 30, glow_a), (0, 0, w, h), 3, border_radius=2)
            surface.blit(glow_surf, (sx, sy))



# ─────────────────────────────────────────────────────────────
class Stage:
    MAP_W = 32
    MAP_H = 24

    def __init__(self, stage_id):
        cfg = STAGE_CONFIGS[stage_id]
        self.stage_id    = stage_id
        self.stage_name  = cfg["name"]
        self.theme       = cfg["theme"]
        self.theme_color = cfg["color"]
        self.enemy_types = cfg["enemy_types"]
        self.boss_type   = cfg["boss"]
        self.completed   = False

        self.tilemap    = []
        self.wall_rects = []
        self.rooms      = []
        self.boss_room  = None
        self.corridors  = []

        self._door_wall_set = set()   # ids of wall_rects added for closed doors

        self.generate_rooms()

        self.cam_x = 0.0
        self.cam_y = 0.0

    # ── BSP generation ────────────────────────────────────────
    def generate_rooms(self):
        root = BSPNode(1, 1, self.MAP_W - 2, self.MAP_H - 2)
        root.split(depth=3)
        raw_rooms     = root.get_rooms()
        raw_corridors = root.connect()

        self.tilemap = [[0]*self.MAP_W for _ in range(self.MAP_H)]
        for room in raw_rooms:
            for ty in range(room.y, room.y + room.h):
                for tx in range(room.x, room.x + room.w):
                    if 0 <= ty < self.MAP_H and 0 <= tx < self.MAP_W:
                        self.tilemap[ty][tx] = 1
        for cor in raw_corridors:
            for ty in range(cor.y, cor.y + cor.h):
                for tx in range(cor.x, cor.x + cor.w):
                    if 0 <= ty < self.MAP_H and 0 <= tx < self.MAP_W:
                        self.tilemap[ty][tx] = 1

        self.wall_rects = []
        for ty in range(self.MAP_H):
            for tx in range(self.MAP_W):
                if self.tilemap[ty][tx] == 0:
                    self.wall_rects.append(pygame.Rect(tx*TILE, ty*TILE, TILE, TILE))

        self.rooms     = [Room(r) for r in raw_rooms]
        self.boss_room = max(self.rooms, key=lambda r: r.rect.w * r.rect.h)
        self.boss_room.is_boss = True

        self._build_doors()
        self._assign_fountains()

    # ── Door building ─────────────────────────────────────────
    def _build_doors(self):
        """Find corridor tiles adjacent to each room edge → door_rects."""
        for room in self.rooms:
            r = room.rect
            seen = set()
            for tx in range(r.x, r.x + r.w):
                for ty_offset, ty in [(-1, r.y - 1), (1, r.y + r.h)]:
                    if 0 <= ty < self.MAP_H and self.tilemap[ty][tx] == 1:
                        key = (tx, ty)
                        if key not in seen:
                            seen.add(key)
                            room.door_rects.append(pygame.Rect(tx*TILE, ty*TILE, TILE, TILE))
            for ty in range(r.y, r.y + r.h):
                for tx_offset, tx in [(-1, r.x - 1), (1, r.x + r.w)]:
                    if 0 <= tx < self.MAP_W and self.tilemap[ty][tx] == 1:
                        key = (tx, ty)
                        if key not in seen:
                            seen.add(key)
                            room.door_rects.append(pygame.Rect(tx*TILE, ty*TILE, TILE, TILE))

    # ── Fountain assignment ───────────────────────────────────
    def _assign_fountains(self):
        """Randomly give some non-boss rooms a health fountain."""
        eligible = [r for r in self.rooms if not r.is_boss]
        for room in eligible:
            if random.random() < Room.FOUNTAIN_CHANCE:
                room.has_fountain = True
                # Place fountain offset from center so it doesn't block spawns
                off_x = random.randint(-1, 1) * TILE
                off_y = random.randint(-1, 1) * TILE
                room.fountain_x = room.cx + off_x
                room.fountain_y = room.cy + off_y

    # ── Door state management ─────────────────────────────────
    def close_room_doors(self, room):
        """Add door rects to wall_rects so player can't pass."""
        if not room.doors_open:
            return
        room.doors_open = False
        for dr in room.door_rects:
            self.wall_rects.append(dr)

    def open_room_doors(self, room):
        """Remove door rects from wall_rects."""
        if room.doors_open:
            return
        room.doors_open = True
        for dr in room.door_rects:
            if dr in self.wall_rects:
                self.wall_rects.remove(dr)

    def get_room_at(self, px, py):
        """Return the Room the given pixel position is inside, or None."""
        for room in self.rooms:
            if room.contains_pixel(px, py):
                return room
        return None

    # ── Enemy spawning ────────────────────────────────────────
    def spawn_enemies(self, stage_level, skip_room=None):
        from constants import STAGE_CONFIGS
        cfg        = STAGE_CONFIGS[self.stage_id] if self.stage_id < len(STAGE_CONFIGS) else {}
        elite_type = cfg.get("elite_shooter")
        eligible   = [r for r in self.rooms if not r.is_boss and r is not skip_room]
        elite_room = None
        if eligible and elite_type:
            eligible_sorted = sorted(eligible, key=lambda r: abs(r.rect.w*r.rect.h - 40))
            elite_room = eligible_sorted[len(eligible_sorted)//2]

        enemies = []
        for room in self.rooms:
            if room is skip_room:
                continue
            count = 3 + self.stage_id
            if room.is_boss:
                bx, by = room.cx, room.cy
                enemies.append(make_enemy(self.boss_type, bx, by, stage_level))
                for pt in room.get_spawn_points(3):
                    enemies.append(make_enemy(random.choice(self.enemy_types), pt[0], pt[1], stage_level))
            elif room is elite_room and elite_type:
                enemies.append(make_enemy(elite_type, room.cx, room.cy, stage_level))
                for pt in room.get_spawn_points(max(1, count-1)):
                    enemies.append(make_enemy(random.choice(self.enemy_types), pt[0], pt[1], stage_level))
            else:
                for pt in room.get_spawn_points(count):
                    enemies.append(make_enemy(random.choice(self.enemy_types), pt[0], pt[1], stage_level))
        return enemies

    def check_completion(self, enemies):
        return all(not e.alive for e in enemies)

    def get_boss_room(self):
        return self.boss_room

    def update(self, dt):
        for room in self.rooms:
            room.update(dt)

    # ── Camera ────────────────────────────────────────────────
    def update_camera(self, player_x, player_y):
        play_h   = SCREEN_H - HUD_H
        target_x = player_x - SCREEN_W / 2
        target_y = player_y - play_h / 2
        max_x    = self.MAP_W * TILE - SCREEN_W
        max_y    = self.MAP_H * TILE - play_h
        self.cam_x = max(0, min(target_x, max_x))
        self.cam_y = max(0, min(target_y, max_y))

    # ── Draw ─────────────────────────────────────────────────
    def draw(self, surface, player=None):
        play_h   = SCREEN_H - HUD_H
        start_tx = int(self.cam_x // TILE)
        start_ty = int(self.cam_y // TILE)
        end_tx   = start_tx + SCREEN_W // TILE + 2
        end_ty   = start_ty + play_h  // TILE + 2

        floor_col = self._floor_color()
        wall_col  = self._wall_color()

        for ty in range(max(0, start_ty), min(self.MAP_H, end_ty)):
            for tx in range(max(0, start_tx), min(self.MAP_W, end_tx)):
                sx = tx * TILE - int(self.cam_x)
                sy = ty * TILE - int(self.cam_y)
                if self.tilemap[ty][tx] == 1:
                    pygame.draw.rect(surface, floor_col, (sx, sy, TILE, TILE))
                    pygame.draw.rect(surface,
                        (floor_col[0]-10, floor_col[1]-10, floor_col[2]-10),
                        (sx, sy, TILE, TILE), 1)
                else:
                    pygame.draw.rect(surface, wall_col, (sx, sy, TILE, TILE))
                    pygame.draw.rect(surface,
                        (min(255,wall_col[0]+20), min(255,wall_col[1]+20), min(255,wall_col[2]+20)),
                        (sx, sy, TILE, TILE), 2)

        # Draw fountains and doors
        for room in self.rooms:
            room.draw_fountain(surface, self.cam_x, self.cam_y, player)
            room.draw_doors(surface, self.cam_x, self.cam_y)

    def _floor_color(self):
        return {"forest":(60,90,40),"dungeon":(55,55,65),"volcano":(80,45,30),
                "sky":(70,100,130),"chaos":(60,40,80)}.get(self.theme,(60,60,60))

    def _wall_color(self):
        return {"forest":(30,55,20),"dungeon":(30,30,40),"volcano":(50,25,15),
                "sky":(40,65,90),"chaos":(35,20,50)}.get(self.theme,(30,30,30))

    # ── Minimap ───────────────────────────────────────────────
    def draw_minimap(self, surface, px, py, size=120):
        mx = SCREEN_W - size - 8
        my = 8
        mini_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        mini_surf.fill((0, 0, 0, 160))
        scale = size / max(self.MAP_W*TILE, self.MAP_H*TILE)
        for room in self.rooms:
            rx = int(room.rect.x * TILE * scale)
            ry = int(room.rect.y * TILE * scale)
            rw = max(3, int(room.rect.w * TILE * scale))
            rh = max(3, int(room.rect.h * TILE * scale))
            if room.is_boss:
                col = (180, 60, 60)
            elif room.has_fountain and not room.fountain_used:
                col = (200, 60, 60)   # red dot on minimap = fountain
            elif room.cleared:
                col = (60, 120, 60)
            else:
                col = (100, 100, 140)
            pygame.draw.rect(mini_surf, col, (rx, ry, rw, rh))
            if room.has_fountain and not room.fountain_used:
                # Heart dot
                pygame.draw.circle(mini_surf, (255,80,80), (rx+rw//2, ry+rh//2), 3)
        pdx = int(px * scale)
        pdy = int(py * scale)
        pygame.draw.circle(mini_surf, (0, 255, 100), (pdx, pdy), 3)
        pygame.draw.rect(mini_surf, (200, 200, 200), (0, 0, size, size), 1)
        surface.blit(mini_surf, (mx, my))
