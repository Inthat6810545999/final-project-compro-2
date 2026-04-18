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
                # FIX: 3-tile-wide corridors so player & enemies never jam
                corridors.append(pygame.Rect(min(ax,bx), ay-1, abs(ax-bx)+1, 3))
                corridors.append(pygame.Rect(bx-1, min(ay,by), 3, abs(ay-by)+1))
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

            # ── Deep black background ──────────────────────────
            pygame.draw.rect(surface, (10, 6, 4), (sx, sy, w, h))

            # ── Amber/gold colour palette (matches image 1) ────
            pulse   = math.sin(t * 2.2) * 0.08 + 0.92    # 0.84 – 1.0
            DARK    = (int(70  * pulse), int(42  * pulse), int(12 * pulse))
            MID     = (int(140 * pulse), int(88  * pulse), int(28 * pulse))
            HI      = (int(210 * pulse), int(145 * pulse), int(52 * pulse))
            BRIGHT  = (int(245 * pulse), int(195 * pulse), int(90 * pulse))
            OUTLINE = (int(185 * pulse), int(125 * pulse), int(40 * pulse))

            # ── Outer frame ────────────────────────────────────
            pygame.draw.rect(surface, OUTLINE, (sx, sy, w, h), 3)
            # Top bevel highlight
            pygame.draw.line(surface, BRIGHT, (sx+2, sy+1), (sx+w-3, sy+1), 1)
            pygame.draw.line(surface, BRIGHT, (sx+1, sy+1), (sx+1, sy+h-2), 1)

            # ── Vertical planks ────────────────────────────────
            plank_num = max(2, w // 12)
            plank_w   = max(6, (w - 4) // plank_num)

            for i in range(plank_num):
                px = sx + 2 + i * plank_w
                pw = plank_w - 2
                if pw <= 0:
                    continue

                # Body
                pygame.draw.rect(surface, MID,  (px, sy+3, pw, h-6))
                # Left highlight
                pygame.draw.rect(surface, HI,   (px+1, sy+4, max(1, pw//3), h-8))
                # Right shadow
                pygame.draw.rect(surface, DARK, (px+pw-2, sy+3, 2, h-6))
                # Subtle grain lines
                for gy in range(sy+10, sy+h-4, 8):
                    pygame.draw.line(surface, DARK, (px+2, gy), (px+pw-3, gy), 1)

                # ── Spike top (↑ pointing up, like image 1) ────
                half = max(2, pw // 2 - 1)
                tx   = px + pw // 2
                pts_top = [
                    (tx,          sy + 1),           # tip
                    (tx - half,   sy + 3 + half),    # bottom-left
                    (tx + half,   sy + 3 + half),    # bottom-right
                ]
                pygame.draw.polygon(surface, HI,     pts_top)
                pygame.draw.polygon(surface, BRIGHT, pts_top, 1)

                # ── Spike bottom (↓) ───────────────────────────
                pts_bot = [
                    (tx,          sy + h - 1),
                    (tx - half,   sy + h - 3 - half),
                    (tx + half,   sy + h - 3 - half),
                ]
                pygame.draw.polygon(surface, HI,     pts_bot)
                pygame.draw.polygon(surface, BRIGHT, pts_bot, 1)

                # ── Circular rivet in the middle of each plank ─
                ry = sy + h // 2
                pygame.draw.circle(surface, DARK,   (tx, ry), 4)
                pygame.draw.circle(surface, BRIGHT, (tx - 1, ry - 1), 2)

            # ── Centre crossbar ────────────────────────────────
            beam_y = sy + h // 2 - 3
            pygame.draw.rect(surface, DARK,  (sx+2, beam_y,   w-4, 7))
            pygame.draw.rect(surface, MID,   (sx+3, beam_y+1, w-6, 5))
            pygame.draw.rect(surface, BRIGHT,(sx+4, beam_y+1, w-8, 2))

            # ── Pulsing red warning glow on border ─────────────
            glow_a = int(55 + math.sin(t * 3.2) * 38)
            glow_s = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(glow_s, (220, 30, 30, glow_a), (0, 0, w, h), 3)
            surface.blit(glow_s, (sx, sy))





# ─────────────────────────────────────────────────────────────
class Stage:
    MAP_W = 60   # large canvas so rooms have breathing room between them
    MAP_H = 60

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

        self._door_wall_set = set()

        self.generate_rooms()

        self.cam_x = 0.0
        self.cam_y = 0.0

    # ── Soul Knight hub-and-spoke generation ─────────────────
    def generate_rooms(self):
        """
        True Soul Knight style:
          - Tilemap starts ALL walls (0)
          - Rooms are carved as isolated rectangles
          - Narrow 2-tile corridors connect them
          - Walls between rooms are solid — rooms feel separate
        """
        CORR_W = 2     # narrow corridors like Soul Knight
        PAD    = 2     # border keep-out

        self.tilemap = [[0] * self.MAP_W for _ in range(self.MAP_H)]
        self._torch_positions = []

        def carve(x, y, w, h):
            for ty in range(max(PAD, y), min(self.MAP_H - PAD, y + h)):
                for tx in range(max(PAD, x), min(self.MAP_W - PAD, x + w)):
                    self.tilemap[ty][tx] = 1

        def in_bounds(x, y, w, h):
            return (x >= PAD and y >= PAD and
                    x + w <= self.MAP_W - PAD and
                    y + h <= self.MAP_H - PAD)

        room_rects = []

        # ── 1) Central hub room ────────────────────────────────
        hub_w = random.randint(8, 11)
        hub_h = random.randint(7, 10)
        hub_x = (self.MAP_W - hub_w) // 2
        hub_y = (self.MAP_H - hub_h) // 2
        carve(hub_x, hub_y, hub_w, hub_h)
        hub = pygame.Rect(hub_x, hub_y, hub_w, hub_h)
        room_rects.append(hub)

        # ── 2) Branch builder ──────────────────────────────────
        # Each branch = narrow corridor + room at end, Soul Knight style
        # Gap between rooms is enforced by corridor length
        def branch(direction, from_rect, corr_len=None, rw=None, rh=None):
            fr  = from_rect
            cl  = corr_len or random.randint(5, 10)  # corridor length (gap between rooms)
            rw_ = rw or random.randint(7, 11)
            rh_ = rh or random.randint(6, 10)

            # Corridor starts from center of from_rect edge
            cx = fr.x + fr.w // 2 - CORR_W // 2
            cy = fr.y + fr.h // 2 - CORR_W // 2

            if direction == "N":
                corr = pygame.Rect(cx, fr.y - cl, CORR_W, cl)
                room = pygame.Rect(cx - (rw_ - CORR_W) // 2, fr.y - cl - rh_, rw_, rh_)
                torch_t = (corr.x + CORR_W // 2, corr.y + cl // 2)
            elif direction == "S":
                corr = pygame.Rect(cx, fr.y + fr.h, CORR_W, cl)
                room = pygame.Rect(cx - (rw_ - CORR_W) // 2, fr.y + fr.h + cl, rw_, rh_)
                torch_t = (corr.x + CORR_W // 2, corr.y + cl // 2)
            elif direction == "E":
                corr = pygame.Rect(fr.x + fr.w, cy, cl, CORR_W)
                room = pygame.Rect(fr.x + fr.w + cl, cy - (rh_ - CORR_W) // 2, rw_, rh_)
                torch_t = (corr.x + cl // 2, corr.y + CORR_W // 2)
            elif direction == "W":
                corr = pygame.Rect(fr.x - cl, cy, cl, CORR_W)
                room = pygame.Rect(fr.x - cl - rw_, cy - (rh_ - CORR_W) // 2, rw_, rh_)
                torch_t = (corr.x + cl // 2, corr.y + CORR_W // 2)
            else:
                return None

            if not in_bounds(room.x, room.y, room.w, room.h):
                return None
            if not in_bounds(corr.x, corr.y, corr.w, corr.h):
                return None

            # Check room doesn't overlap any existing room (keep rooms isolated)
            padded = room.inflate(2, 2)
            for rr in room_rects:
                if padded.colliderect(rr.inflate(2, 2)):
                    return None

            carve(corr.x, corr.y, corr.w, corr.h)
            carve(room.x,  room.y,  room.w,  room.h)
            room_rects.append(room)

            # Torch at corridor midpoint
            wx = torch_t[0] * TILE + TILE // 2
            wy = torch_t[1] * TILE + TILE // 2
            self._torch_positions.append((wx, wy))
            return room

        # ── 3) Primary spokes N/S/E/W from hub ────────────────
        dirs = ["N", "S", "E", "W"]
        random.shuffle(dirs)
        placed = []   # list of (dir, room_rect)
        for d in dirs:
            r = branch(d, hub)
            if r:
                placed.append((d, r))

        # ── 4) Secondary branches from each spoke room ─────────
        perp_map = {
            "N": ["E", "W"], "S": ["E", "W"],
            "E": ["N", "S"], "W": ["N", "S"],
        }
        secondary = []
        for par_d, par_r in placed:
            perps = perp_map[par_d][:]
            random.shuffle(perps)
            for pd in perps:
                r2 = branch(pd, par_r,
                            corr_len=random.randint(4, 8),
                            rw=random.randint(6, 9),
                            rh=random.randint(5, 8))
                if r2:
                    secondary.append((pd, r2))
                    break   # one secondary per spoke

        # ── 5) Tertiary branches (stage ≥ 2) ───────────────────
        if self.stage_id >= 2:
            all_placed = placed + secondary
            random.shuffle(all_placed)
            for par_d, par_r in all_placed[:2]:
                # try same direction (extend chain) or perpendicular
                for td in [par_d] + perp_map[par_d]:
                    r3 = branch(td, par_r,
                                corr_len=random.randint(4, 7),
                                rw=random.randint(5, 8),
                                rh=random.randint(5, 7))
                    if r3:
                        break

        # ── 6) Build wall_rects from tilemap ──────────────────
        self.wall_rects = []
        for ty in range(self.MAP_H):
            for tx in range(self.MAP_W):
                if self.tilemap[ty][tx] == 0:
                    self.wall_rects.append(pygame.Rect(tx*TILE, ty*TILE, TILE, TILE))

        self.rooms     = [Room(r) for r in room_rects]
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

        # Draw fountains, doors, and corridor torches
        for room in self.rooms:
            room.draw_fountain(surface, self.cam_x, self.cam_y, player)
            room.draw_doors(surface, self.cam_x, self.cam_y)
        self._draw_torches(surface)

    def _draw_torches(self, surface):
        """Draw Soul Knight-style torch/lamp at each corridor-room junction."""
        t = pygame.time.get_ticks() / 1000.0
        for wx, wy in getattr(self, "_torch_positions", []):
            sx = int(wx - self.cam_x)
            sy = int(wy - self.cam_y)
            play_h = SCREEN_H - HUD_H
            if sx < -20 or sx > SCREEN_W + 20 or sy < -20 or sy > play_h + 20:
                continue
            # Glow halo
            pulse = math.sin(t * 3.5 + wx * 0.01) * 0.2 + 0.8
            glow_r = int(18 * pulse)
            glow_s = pygame.Surface((glow_r*2+4, glow_r*2+4), pygame.SRCALPHA)
            pygame.draw.circle(glow_s, (255, 200, 60, 50), (glow_r+2, glow_r+2), glow_r)
            surface.blit(glow_s, (sx - glow_r - 2, sy - glow_r - 2))
            # Lamp body
            pygame.draw.circle(surface, (220, 160, 40), (sx, sy), 7)
            pygame.draw.circle(surface, (255, 220, 100), (sx, sy), 5)
            pygame.draw.circle(surface, (255, 255, 180), (sx-1, sy-1), 2)

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
