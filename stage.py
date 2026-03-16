"""
stage.py  –  Stage & Room generation using BSP (OOP Class 4)
"""
import random
import math
import pygame
from constants import (
    STAGE_CONFIGS, TILE, SCREEN_W, SCREEN_H, HUD_H,
    DARK_GRAY, GRAY, WHITE, BLACK, GREEN, YELLOW,
    DARK_BROWN, BROWN, DARK_RED, DARK_GREEN, LIGHT_BLUE, PURPLE
)
from enemy import make_enemy


# ─────────────────────────────────────────────────────────────
# BSP helpers
# ─────────────────────────────────────────────────────────────
class BSPNode:
    MIN_ROOM = 5   # minimum room dimension in tiles

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.left  = None
        self.right = None
        self.room  = None   # pygame.Rect in tile coords

    def split(self, depth=0):
        if depth <= 0:
            self._make_room()
            return
        # Choose split axis (prefer the longer dimension)
        if self.w > self.h:
            # vertical split
            min_split = self.MIN_ROOM + 1
            if self.w < min_split * 2:
                self._make_room()
                return
            cut = random.randint(min_split, self.w - min_split)
            self.left  = BSPNode(self.x,       self.y, cut,          self.h)
            self.right = BSPNode(self.x + cut,  self.y, self.w - cut, self.h)
        else:
            # horizontal split
            min_split = self.MIN_ROOM + 1
            if self.h < min_split * 2:
                self._make_room()
                return
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
        if self.room:
            return [self.room]
        rooms = []
        if self.left:  rooms += self.left.get_rooms()
        if self.right: rooms += self.right.get_rooms()
        return rooms

    def get_room_for_self(self):
        """Return a representative room (leftmost leaf)."""
        if self.room:
            return self.room
        if self.left:
            return self.left.get_room_for_self()
        if self.right:
            return self.right.get_room_for_self()

    def connect(self):
        """Connect sibling nodes with corridors."""
        corridors = []
        if self.left and self.right:
            corridors += self.left.connect()
            corridors += self.right.connect()
            ra = self.left.get_room_for_self()
            rb = self.right.get_room_for_self()
            if ra and rb:
                # Centre points
                ax = ra.centerx
                ay = ra.centery
                bx = rb.centerx
                by = rb.centery
                # L-shaped corridor (2 tiles wide)
                corridors.append(pygame.Rect(min(ax, bx), ay - 1, abs(ax - bx) + 1, 2))
                corridors.append(pygame.Rect(bx - 1, min(ay, by), 2, abs(ay - by) + 1))
        return corridors


# ─────────────────────────────────────────────────────────────
class Room:
    """A single room: floor tiles + walls + spawn points."""

    def __init__(self, rect, is_boss=False):
        self.rect      = rect      # pygame.Rect in tile coords
        self.is_boss   = is_boss
        self.cleared   = False
        self.visited   = False
        # Pixel centre (for spawning enemies / player)
        self.cx = (rect.x + rect.w // 2) * TILE + TILE // 2
        self.cy = (rect.y + rect.h // 2) * TILE + TILE // 2

    def get_spawn_points(self, n):
        """Return n random pixel positions inside the room."""
        pts = []
        for _ in range(n):
            tx = random.randint(self.rect.x + 1, self.rect.right - 2)
            ty = random.randint(self.rect.y + 1, self.rect.bottom - 2)
            pts.append((tx * TILE + TILE // 2, ty * TILE + TILE // 2))
        return pts


# ─────────────────────────────────────────────────────────────
class Stage:
    """
    Manages the generation, layout, and state of a dungeon stage.
    Uses BSP for procedural room + corridor generation.
    """

    MAP_W = 32   # tiles
    MAP_H = 24   # tiles

    def __init__(self, stage_id):
        cfg = STAGE_CONFIGS[stage_id]
        self.stage_id    = stage_id
        self.stage_name  = cfg["name"]
        self.theme       = cfg["theme"]
        self.theme_color = cfg["color"]
        self.enemy_types = cfg["enemy_types"]
        self.boss_type   = cfg["boss"]
        self.completed   = False

        # Generate the map
        self.tilemap     = []       # 2D list: 0=wall 1=floor
        self.wall_rects  = []       # pygame.Rect list for collision
        self.rooms       = []       # list[Room]
        self.boss_room   = None
        self.corridors   = []       # pygame.Rect in tile coords

        self.generate_rooms()

        # Camera offset (pixels)
        self.cam_x = 0.0
        self.cam_y = 0.0

    # ── BSP generation ────────────────────────────────────────
    def generate_rooms(self):
        root = BSPNode(1, 1, self.MAP_W - 2, self.MAP_H - 2)
        root.split(depth=3)
        raw_rooms  = root.get_rooms()
        raw_corridors = root.connect()

        # Build tile map
        self.tilemap = [[0] * self.MAP_W for _ in range(self.MAP_H)]
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

        # Build wall rects for collision
        self.wall_rects = []
        for ty in range(self.MAP_H):
            for tx in range(self.MAP_W):
                if self.tilemap[ty][tx] == 0:
                    self.wall_rects.append(pygame.Rect(tx * TILE, ty * TILE, TILE, TILE))

        # Wrap raw rooms into Room objects
        self.rooms = [Room(r) for r in raw_rooms]
        # Boss room = largest room
        self.boss_room = max(self.rooms, key=lambda r: r.rect.w * r.rect.h)
        self.boss_room.is_boss = True

    # ── Enemy spawning ────────────────────────────────────────
    def spawn_enemies(self, stage_level, skip_room=None):
        """
        Spawn enemies in all rooms except skip_room.
        One Elite Shooter is placed in a dedicated room (not boss room).
        Returns list of Enemy objects.
        """
        from constants import STAGE_CONFIGS
        cfg          = STAGE_CONFIGS[self.stage_id] if self.stage_id < len(STAGE_CONFIGS) else {}
        elite_type   = cfg.get("elite_shooter")
        # Pick a room for the elite (middle-sized, not boss, not skip)
        eligible     = [r for r in self.rooms if not r.is_boss and r is not skip_room]
        elite_room   = None
        if eligible and elite_type:
            # prefer a room with moderate size
            eligible_sorted = sorted(eligible,
                key=lambda r: abs(r.rect.w * r.rect.h - 40), reverse=False)
            elite_room = eligible_sorted[len(eligible_sorted) // 2]

        enemies = []
        for room in self.rooms:
            if room is skip_room:
                continue
            count = 3 + self.stage_id * 1
            if room.is_boss:
                # Spawn boss
                bx, by = room.cx, room.cy
                boss = make_enemy(self.boss_type, bx, by, stage_level)
                enemies.append(boss)
                # Extra minions around boss
                for pt in room.get_spawn_points(3):
                    e_type = random.choice(self.enemy_types)
                    enemies.append(make_enemy(e_type, pt[0], pt[1], stage_level))
            elif room is elite_room and elite_type:
                # Spawn the Elite Shooter at room center
                enemies.append(make_enemy(elite_type, room.cx, room.cy, stage_level))
                # Fewer regular enemies in elite room
                for pt in room.get_spawn_points(max(1, count - 1)):
                    e_type = random.choice(self.enemy_types)
                    enemies.append(make_enemy(e_type, pt[0], pt[1], stage_level))
            else:
                for pt in room.get_spawn_points(count):
                    e_type = random.choice(self.enemy_types)
                    enemies.append(make_enemy(e_type, pt[0], pt[1], stage_level))
        return enemies

    def check_completion(self, enemies):
        return all(not e.alive for e in enemies)

    def get_boss_room(self):
        return self.boss_room

    # ── Camera ───────────────────────────────────────────────
    def update_camera(self, player_x, player_y):
        play_h  = SCREEN_H - HUD_H
        target_x = player_x - SCREEN_W / 2
        target_y = player_y - play_h / 2
        max_x   = self.MAP_W * TILE - SCREEN_W
        max_y   = self.MAP_H * TILE - play_h
        self.cam_x = max(0, min(target_x, max_x))
        self.cam_y = max(0, min(target_y, max_y))

    # ── Draw ─────────────────────────────────────────────────
    def draw(self, surface):
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
                    # Subtle grid
                    pygame.draw.rect(surface, (floor_col[0]-10, floor_col[1]-10, floor_col[2]-10),
                                     (sx, sy, TILE, TILE), 1)
                else:
                    pygame.draw.rect(surface, wall_col, (sx, sy, TILE, TILE))
                    # Wall highlight
                    pygame.draw.rect(surface, (min(255,wall_col[0]+20), min(255,wall_col[1]+20), min(255,wall_col[2]+20)),
                                     (sx, sy, TILE, TILE), 2)

    def _floor_color(self):
        theme_floors = {
            "forest":  (60,  90,  40),
            "dungeon": (55,  55,  65),
            "volcano": (80,  45,  30),
            "sky":     (70,  100, 130),
            "chaos":   (60,  40,  80),
        }
        return theme_floors.get(self.theme, (60, 60, 60))

    def _wall_color(self):
        theme_walls = {
            "forest":  (30,  55,  20),
            "dungeon": (30,  30,  40),
            "volcano": (50,  25,  15),
            "sky":     (40,  65,  90),
            "chaos":   (35,  20,  50),
        }
        return theme_walls.get(self.theme, (30, 30, 30))

    # ── Minimap ───────────────────────────────────────────────
    def draw_minimap(self, surface, px, py, size=120):
        """Draw a small top-right minimap."""
        mx = SCREEN_W - size - 8
        my = 8
        mini_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        mini_surf.fill((0, 0, 0, 160))

        scale = size / max(self.MAP_W * TILE, self.MAP_H * TILE)
        for room in self.rooms:
            rx = int(room.rect.x * TILE * scale)
            ry = int(room.rect.y * TILE * scale)
            rw = max(3, int(room.rect.w * TILE * scale))
            rh = max(3, int(room.rect.h * TILE * scale))
            col = (180, 60, 60) if room.is_boss else (100, 100, 140)
            pygame.draw.rect(mini_surf, col, (rx, ry, rw, rh))

        # Player dot
        pdx = int(px * scale)
        pdy = int(py * scale)
        pygame.draw.circle(mini_surf, (0, 255, 100), (pdx, pdy), 3)

        pygame.draw.rect(mini_surf, (200, 200, 200), (0, 0, size, size), 1)
        surface.blit(mini_surf, (mx, my))
