"""
stage.py  –  Stage & Room generation using BSP
  + VISUAL OVERHAUL: procedural tile textures, ambient particles,
    3-D wall depth shadows, flickering torches, improved minimap
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

DOOR_ANIM_DUR = 2.2   # seconds for boss-door opening animation

# ── TILE TEXTURE CACHE ──────────────────────────────────────────────────────
_TILE_CACHE: dict = {}
_SHADOW_TOP  = None
_SHADOW_LEFT = None

_FLOOR_BASES = {
    "forest":  [(52,78,34),(58,88,40),(48,72,30),(62,92,44),(55,82,38),(50,75,32),(60,88,42),(45,68,28)],
    "dungeon": [(50,50,60),(45,45,55),(55,55,65),(42,42,52),(58,58,70),(48,48,58),(52,52,62),(40,40,50)],
    "volcano": [(72,40,24),(80,44,28),(68,36,20),(85,48,30),(76,42,26),(70,38,22),(82,46,28),(65,33,18)],
    "sky":     [(60,90,120),(65,96,128),(55,84,112),(70,102,136),(62,92,122),(58,88,118),(67,98,130),(52,80,108)],
    "chaos":   [(52,32,68),(58,36,76),(48,28,62),(64,40,82),(54,34,70),(50,30,65),(60,38,78),(44,26,60)],
}
_WALL_BASES = {
    "forest":  [(24,42,16),(28,48,18),(20,36,14),(30,50,20)],
    "dungeon": [(28,28,36),(24,24,32),(32,32,40),(22,22,30)],
    "volcano": [(48,22,12),(54,26,14),(44,18,10),(58,30,16)],
    "sky":     [(36,56,80),(40,62,88),(32,50,72),(44,68,96)],
    "chaos":   [(30,16,44),(34,20,50),(26,12,38),(38,24,56)],
}

def _init_shadows():
    global _SHADOW_TOP, _SHADOW_LEFT
    if _SHADOW_TOP is not None:
        return
    _SHADOW_TOP = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    for y in range(TILE // 2):
        alpha = int(110 * (1 - y / (TILE / 2)) ** 1.6)
        pygame.draw.line(_SHADOW_TOP, (0, 0, 0, alpha), (0, y), (TILE, y))
    _SHADOW_LEFT = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    for x in range(TILE // 2):
        alpha = int(70 * (1 - x / (TILE / 2)) ** 1.4)
        pygame.draw.line(_SHADOW_LEFT, (0, 0, 0, alpha), (x, 0), (x, TILE))

def _make_floor_tile(theme, variant):
    bases = _FLOOR_BASES.get(theme, _FLOOR_BASES["dungeon"])
    base_col = bases[variant % len(bases)]
    surf = pygame.Surface((TILE, TILE))
    surf.fill(base_col)
    rng = random.Random(hash(theme) ^ (variant * 31337))
    if theme == "forest":
        dark_g  = (max(0,base_col[0]-14), max(0,base_col[1]-18), max(0,base_col[2]-10))
        light_g = (min(255,base_col[0]+18), min(255,base_col[1]+24), min(255,base_col[2]+12))
        for _ in range(18):
            gx=rng.randint(2,TILE-3); gy=rng.randint(2,TILE-3); gr=rng.randint(2,6)
            gc = dark_g if rng.random()<0.5 else light_g
            pygame.draw.ellipse(surf, gc, (gx-gr//2, gy-gr//3, gr, gr//2+1))
        if rng.random() < 0.18:
            fx=rng.randint(6,TILE-6); fy=rng.randint(6,TILE-6)
            petal = (220,180,80) if rng.random()<0.5 else (220,100,140)
            for i in range(4):
                a = i*math.pi/2
                pygame.draw.circle(surf, petal, (int(fx+math.cos(a)*3), int(fy+math.sin(a)*3)), 2)
            pygame.draw.circle(surf, (255,240,60), (fx,fy), 2)
        for _ in range(rng.randint(0,3)):
            pygame.draw.circle(surf,(80,70,50),(rng.randint(4,TILE-4),rng.randint(4,TILE-4)),rng.randint(1,3))
    elif theme == "dungeon":
        mortar = (max(0,base_col[0]-20), max(0,base_col[1]-20), max(0,base_col[2]-22))
        stone  = (min(255,base_col[0]+12), min(255,base_col[1]+12), min(255,base_col[2]+14))
        for row in range(0,TILE,22):
            pygame.draw.line(surf, mortar, (0,row), (TILE,row), 2)
        for row in range(2):
            offset = 18 if row==0 else 6
            for col in range(offset, TILE, 36):
                pygame.draw.line(surf, mortar, (col,row*22), (col,(row+1)*22), 2)
        if rng.random() < 0.25:
            cx=rng.randint(4,TILE-4); cy=rng.randint(4,TILE-4)
            pts = [(cx,cy)]
            for _ in range(rng.randint(2,4)):
                pts.append((pts[-1][0]+rng.randint(-8,8), pts[-1][1]+rng.randint(-6,6)))
            for i in range(len(pts)-1):
                pygame.draw.line(surf,(20,20,28),pts[i],pts[i+1],1)
        for _ in range(6):
            pygame.draw.circle(surf,stone,(rng.randint(2,TILE-2),rng.randint(2,TILE-2)),1)
    elif theme == "volcano":
        dark_rock=(max(0,base_col[0]-20),max(0,base_col[1]-12),max(0,base_col[2]-8))
        crack_col=(200,80,10); lava_glow=(255,140,30)
        for _ in range(8):
            rx=rng.randint(0,TILE-1); ry=rng.randint(0,TILE-1); rr=rng.randint(3,10)
            pygame.draw.circle(surf,dark_rock,(rx,ry),rr)
        for _ in range(rng.randint(1,3)):
            cx=rng.randint(4,TILE-4); cy=rng.randint(4,TILE-4)
            for _ in range(rng.randint(2,5)):
                ex=cx+rng.randint(-20,20); ey=cy+rng.randint(-20,20)
                pygame.draw.line(surf,crack_col,(cx,cy),(ex,ey),2)
                pygame.draw.line(surf,lava_glow,(cx,cy),(ex,ey),1)
        if rng.random() < 0.10:
            lx=rng.randint(8,TILE-8); ly=rng.randint(8,TILE-8); lr=rng.randint(4,9)
            pygame.draw.ellipse(surf,(220,60,0),(lx-lr,ly-lr//2,lr*2,lr))
            pygame.draw.ellipse(surf,(255,150,20),(lx-lr//2,ly-lr//4,lr,lr//2))
    elif theme == "sky":
        cloud_col=(min(255,base_col[0]+22),min(255,base_col[1]+24),min(255,base_col[2]+28))
        wisp_col=(min(255,base_col[0]+40),min(255,base_col[1]+42),min(255,base_col[2]+50))
        for _ in range(5):
            pygame.draw.circle(surf,cloud_col,(rng.randint(0,TILE),rng.randint(0,TILE)),rng.randint(6,18))
        for _ in range(3):
            wx=rng.randint(4,TILE-4); wy=rng.randint(4,TILE-4)
            pygame.draw.ellipse(surf,wisp_col,(wx-8,wy-3,16,6))
        if variant % 3 == 0:
            pygame.draw.rect(surf,(180,155,80),(0,0,TILE,TILE),1)
    elif theme == "chaos":
        crack_col=(140,60,200); glow_col=(200,80,255)
        for _ in range(rng.randint(2,5)):
            cx=rng.randint(4,TILE-4); cy=rng.randint(4,TILE-4)
            for _ in range(rng.randint(2,4)):
                ex=cx+rng.randint(-24,24); ey=cy+rng.randint(-24,24)
                pygame.draw.line(surf,crack_col,(cx,cy),(ex,ey),2)
                pygame.draw.line(surf,glow_col,(cx,cy),(ex,ey),1)
        for _ in range(rng.randint(0,3)):
            nx=rng.randint(4,TILE-4); ny=rng.randint(4,TILE-4)
            pygame.draw.circle(surf,glow_col,(nx,ny),3)
            pygame.draw.circle(surf,(255,200,255),(nx,ny),1)
    return surf.convert()

def _make_wall_tile(theme, variant, has_face=False):
    bases = _WALL_BASES.get(theme, _WALL_BASES["dungeon"])
    base_col = bases[variant % len(bases)]
    surf = pygame.Surface((TILE, TILE))
    surf.fill(base_col)
    rng = random.Random(hash(theme) ^ (variant * 99991) ^ (int(has_face)*12345))
    face_start = TILE * 3 // 4
    if theme == "dungeon":
        mortar=(max(0,base_col[0]-10),max(0,base_col[1]-10),max(0,base_col[2]-12))
        block_col=(min(255,base_col[0]+16),min(255,base_col[1]+16),min(255,base_col[2]+20))
        for y in range(0,TILE,24): pygame.draw.line(surf,mortar,(0,y),(TILE,y),2)
        for row,offset in enumerate([0,12]):
            for x in range(offset,TILE,36): pygame.draw.line(surf,mortar,(x,row*24),(x,(row+1)*24),2)
        for _ in range(8):
            sc=rng.choice([block_col,mortar])
            pygame.draw.circle(surf,sc,(rng.randint(2,TILE-2),rng.randint(2,TILE-2)),rng.randint(1,3))
    elif theme == "forest":
        bark_col=(min(255,base_col[0]+20),min(255,base_col[1]+14),max(0,base_col[2]-4))
        moss_col=(min(255,base_col[0]+10),min(255,base_col[1]+28),max(0,base_col[2]+8))
        for x in range(0,TILE,rng.randint(6,12)):
            pygame.draw.line(surf,bark_col,(x,0),(x+rng.randint(-2,2),TILE),1)
        for _ in range(rng.randint(2,5)):
            pygame.draw.circle(surf,moss_col,(rng.randint(2,TILE-2),rng.randint(2,TILE-2)),rng.randint(2,5))
    elif theme == "volcano":
        sheen=(min(255,base_col[0]+30),min(255,base_col[1]+18),min(255,base_col[2]+10))
        lava=(180,60,10)
        for _ in range(4):
            px=rng.randint(0,TILE); py=rng.randint(0,TILE)
            qx=px+rng.randint(-16,16); qy=py+rng.randint(-16,16)
            pygame.draw.line(surf,sheen,(px,py),(qx,qy),rng.randint(1,3))
        if rng.random()<0.35:
            lx=rng.randint(2,TILE-2); ly=rng.randint(2,TILE//2)
            pygame.draw.line(surf,lava,(lx,ly),(lx+rng.randint(-6,6),TILE-2),2)
    elif theme == "sky":
        col1=(min(255,base_col[0]+30),min(255,base_col[1]+30),min(255,base_col[2]+35))
        col2=(min(255,base_col[0]+50),min(255,base_col[1]+52),min(255,base_col[2]+60))
        for x in range(0,TILE,18):
            pygame.draw.line(surf,col1,(x,0),(x,TILE),rng.randint(1,3))
            if x+4<TILE: pygame.draw.line(surf,col2,(x+2,0),(x+2,TILE),1)
        pygame.draw.line(surf,(180,155,80),(0,2),(TILE,2),2)
    elif theme == "chaos":
        col1=(min(255,base_col[0]+35),min(255,base_col[1]+20),min(255,base_col[2]+50))
        for _ in range(rng.randint(2,5)):
            ax=rng.randint(0,TILE); ay=rng.randint(0,TILE)
            bx=ax+rng.randint(-30,30); by=ay+rng.randint(-30,30)
            pygame.draw.line(surf,col1,(ax,ay),(bx,by),rng.randint(1,2))
        for _ in range(rng.randint(0,2)):
            pygame.draw.circle(surf,(200,80,255),(rng.randint(4,TILE-4),rng.randint(4,TILE-4)),2)
    hi=(min(255,base_col[0]+40),min(255,base_col[1]+40),min(255,base_col[2]+45))
    pygame.draw.line(surf,hi,(0,0),(TILE,0),3)
    pygame.draw.line(surf,hi,(0,1),(TILE,1),1)
    if has_face:
        face_col=(min(255,base_col[0]+35),min(255,base_col[1]+32),min(255,base_col[2]+38))
        pygame.draw.rect(surf,face_col,(0,face_start,TILE,TILE-face_start))
        pygame.draw.line(surf,(max(0,base_col[0]-20),max(0,base_col[1]-20),max(0,base_col[2]-22)),
                         (0,face_start),(TILE,face_start),2)
    return surf.convert()

def _get_floor(theme, tx, ty):
    variant=(tx*7+ty*11)%8
    key=("floor",theme,variant)
    if key not in _TILE_CACHE: _TILE_CACHE[key]=_make_floor_tile(theme,variant)
    return _TILE_CACHE[key]

def _get_wall(theme, tx, ty, has_face):
    variant=(tx*5+ty*9)%4
    key=("wall",theme,variant,has_face)
    if key not in _TILE_CACHE: _TILE_CACHE[key]=_make_wall_tile(theme,variant,has_face)
    return _TILE_CACHE[key]

# ── AMBIENT PARTICLES ───────────────────────────────────────────────────────
class AmbientParticle:
    __slots__=("x","y","vx","vy","life","max_life","radius","color","alpha","theme","angle","spin")
    def __init__(self, x, y, theme):
        self.x=float(x); self.y=float(y); self.theme=theme; self.spin=0.0
        if theme=="forest":
            self.color=random.choice([(80,140,40),(60,110,30),(140,100,30),(180,130,40)])
            self.vx=random.uniform(-0.4,0.4); self.vy=random.uniform(0.3,0.9)
            self.radius=random.randint(2,4); self.life=random.uniform(2.0,4.0)
            self.angle=random.uniform(0,math.tau); self.spin=random.uniform(-1.5,1.5)
        elif theme=="volcano":
            self.color=random.choice([(255,160,30),(255,80,10),(255,220,80)])
            self.vx=random.uniform(-0.6,0.6); self.vy=random.uniform(-1.2,-0.5)
            self.radius=random.randint(1,3); self.life=random.uniform(0.8,2.0); self.angle=0.0
        elif theme=="dungeon":
            v=random.randint(30,80); self.color=(v,v,v+20)
            self.vx=random.uniform(-0.15,0.15); self.vy=random.uniform(-0.3,-0.1)
            self.radius=1; self.life=random.uniform(2.5,5.0); self.angle=0.0
        elif theme=="sky":
            self.color=random.choice([(200,230,255),(180,210,255),(240,248,255)])
            self.vx=random.uniform(-0.5,0.5); self.vy=random.uniform(-0.2,0.2)
            self.radius=random.randint(2,5); self.life=random.uniform(2.0,4.0); self.angle=0.0
        else:  # chaos
            a=random.uniform(0,math.tau); s=random.uniform(0.5,1.4)
            self.vx=math.cos(a)*s; self.vy=math.sin(a)*s
            self.color=random.choice([(200,80,255),(255,60,200),(140,40,255)])
            self.radius=random.randint(1,3); self.life=random.uniform(0.5,1.5); self.angle=0.0
        self.max_life=self.life; self.alpha=255

    def update(self, dt):
        self.life-=dt
        if self.life<=0: return False
        if self.theme=="forest":
            self.vx=math.sin(self.life*1.8)*0.5
            self.x+=self.vx*60*dt; self.y+=self.vy*60*dt; self.angle+=self.spin*dt
        elif self.theme=="volcano":
            self.vy*=(1-0.4*dt); self.x+=self.vx*60*dt; self.y+=self.vy*60*dt; self.vy+=0.1*dt
        else:
            self.x+=self.vx*60*dt; self.y+=self.vy*60*dt
        ratio=self.life/self.max_life
        self.alpha=int(255*min(1.0,ratio*3.0)*ratio)
        return True

    def draw(self, surface, cam_x, cam_y):
        sx=int(self.x-cam_x); sy=int(self.y-cam_y)
        if self.radius<=0 or self.alpha<=0: return
        if self.theme=="forest" and self.radius>=3:
            s=pygame.Surface((self.radius*4+4,self.radius*4+4),pygame.SRCALPHA)
            cx,cy=self.radius*2+2,self.radius*2+2
            pygame.draw.ellipse(s,(*self.color,self.alpha),(cx-self.radius,cy-self.radius//2,self.radius*2,self.radius))
            rot=pygame.transform.rotate(s,math.degrees(self.angle))
            rw,rh=rot.get_size(); surface.blit(rot,(sx-rw//2,sy-rh//2))
        else:
            gs=pygame.Surface((self.radius*4+2,self.radius*4+2),pygame.SRCALPHA)
            pygame.draw.circle(gs,(*self.color,self.alpha),(self.radius*2+1,self.radius*2+1),self.radius)
            surface.blit(gs,(sx-self.radius*2-1,sy-self.radius*2-1))
# ── DOOR-OPEN PARTICLE ──────────────────────────────────────────────────────
class DoorOpenParticle:
    """Short-lived spark / debris for boss-door opening VFX."""
    __slots__ = ("x","y","vx","vy","life","max_life","color","radius","alpha","kind")

    def __init__(self, x, y, color, kind="spark"):
        self.x = float(x); self.y = float(y)
        self.color = color; self.kind = kind
        angle  = random.uniform(0, math.tau)
        speed  = random.uniform(70, 260)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(10, 90)
        self.radius   = random.randint(2, 7) if kind == "spark" else random.randint(3, 10)
        self.life     = random.uniform(0.35, 0.90)
        self.max_life = self.life
        self.alpha    = 255

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            return False
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy  += 180 * dt          # gravity pull
        self.vx  *= (1 - 1.5 * dt)   # air drag
        ratio = self.life / self.max_life
        self.alpha = int(255 * ratio * ratio)
        return True

    def draw(self, surface, cam_x, cam_y):
        sx = int(self.x - cam_x); sy = int(self.y - cam_y)
        if self.alpha <= 0 or self.radius <= 0:
            return
        s = pygame.Surface((self.radius * 2 + 2, self.radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, self.alpha),
                           (self.radius + 1, self.radius + 1), self.radius)
        surface.blit(s, (sx - self.radius - 1, sy - self.radius - 1))


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
        self.door_locked = False  # True = permanently locked until boss-room prerequisite met

        # Boss-door opening animation
        self.door_opening       = False  # True while animation plays
        self.door_anim_t        = 0.0    # counts down from DOOR_ANIM_DUR
        self.door_anim_particles: list = []

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
        # Boss-door opening animation tick
        if self.door_opening:
            self.door_anim_t = max(0.0, self.door_anim_t - dt)
            self.door_anim_particles = [p for p in self.door_anim_particles if p.update(dt)]
            if self.door_anim_t <= 0 and not self.door_anim_particles:
                self.door_opening = False

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
    def draw_doors(self, surface, cam_x, cam_y, theme="dungeon"):
        # Boss-door opening animation takes priority
        if self.door_opening and self.door_rects:
            self._draw_door_opening_anim(surface, cam_x, cam_y, theme)
            return
        if (self.doors_open and not self.door_locked) or not self.door_rects:
            return
        t = pygame.time.get_ticks() / 1000.0

        # Theme-specific magic barrier colour
        THEME_MAGIC = {
            "forest":  (60,  220,  80),
            "dungeon": (160,  80, 255),
            "volcano": (255, 100,  20),
            "sky":     ( 80, 190, 255),
            "chaos":   (220,  40, 200),
        }
        magic = THEME_MAGIC.get(theme, (160, 80, 255))

        # Iron / stone palette
        STONE_D  = (35, 35, 42)
        STONE_M  = (58, 60, 72)
        STONE_H  = (90, 95, 115)
        IRON_D   = (22, 24, 30)
        IRON_M   = (50, 54, 66)
        IRON_H   = (105, 115, 138)
        IRON_SH  = (185, 195, 218)

        pulse = math.sin(t * 2.8) * 0.5 + 0.5   # 0 → 1

        for dr in self.door_rects:
            sx = dr.x - int(cam_x)
            sy = dr.y - int(cam_y)
            w, h = dr.w, dr.h
            FRAME = 10  # stone frame thickness

            # ── 1. Stone frame background ──────────────────────
            pygame.draw.rect(surface, STONE_D, (sx, sy, w, h))

            # Carved stone border strips
            pygame.draw.rect(surface, STONE_M, (sx,          sy,          w,     FRAME))
            pygame.draw.rect(surface, STONE_M, (sx,          sy+h-FRAME,  w,     FRAME))
            pygame.draw.rect(surface, STONE_M, (sx,          sy,          FRAME, h))
            pygame.draw.rect(surface, STONE_M, (sx+w-FRAME,  sy,          FRAME, h))

            # Stone top-left bevel highlights
            pygame.draw.line(surface, STONE_H, (sx+1, sy+1), (sx+w-2, sy+1), 2)
            pygame.draw.line(surface, STONE_H, (sx+1, sy+1), (sx+1, sy+h-2), 2)
            # Bottom-right shadow
            pygame.draw.line(surface, IRON_D,  (sx+w-2, sy+2), (sx+w-2, sy+h-1), 2)
            pygame.draw.line(surface, IRON_D,  (sx+2, sy+h-2), (sx+w-1, sy+h-2), 2)

            # Stone seams on frame strips
            for bx in range(sx+FRAME+10, sx+w-FRAME, 20):
                pygame.draw.line(surface, STONE_D, (bx, sy+2),      (bx, sy+FRAME-2),     1)
                pygame.draw.line(surface, STONE_D, (bx, sy+h-FRAME+2), (bx, sy+h-2),      1)
            for by in range(sy+FRAME+10, sy+h-FRAME, 20):
                pygame.draw.line(surface, STONE_D, (sx+2, by),      (sx+FRAME-2, by),     1)
                pygame.draw.line(surface, STONE_D, (sx+w-FRAME+2, by), (sx+w-2, by),      1)

            # ── 2. Inner gate void ─────────────────────────────
            ix = sx + FRAME; iy = sy + FRAME
            iw = w - FRAME*2; ih = h - FRAME*2
            pygame.draw.rect(surface, (6, 4, 12), (ix, iy, iw, ih))

            # ── 3. Magical energy field ────────────────────────
            # Base glow fill
            en = pygame.Surface((iw, ih), pygame.SRCALPHA)
            en.fill((*magic, int(30 + pulse * 45)))
            surface.blit(en, (ix, iy))

            # Moving shimmer stripe across barrier
            shim_y = int((t * 55) % (ih + 20)) - 10
            for sy2 in range(max(0, shim_y - 4), min(ih, shim_y + 5)):
                a = int(60 * (1 - abs(sy2 - shim_y) / 5.0))
                sl = pygame.Surface((iw, 1), pygame.SRCALPHA)
                sl.fill((*magic, a))
                surface.blit(sl, (ix, iy + sy2))

            # ── 4. Iron bars (vertical) ────────────────────────
            bar_count = max(3, iw // 14)
            bar_thick = 6
            spacing   = iw / bar_count

            for i in range(bar_count + 1):
                bx_c = ix + int(i * spacing)
                bx_l = bx_c - bar_thick // 2
                # Main body
                pygame.draw.rect(surface, IRON_M, (bx_l, iy, bar_thick, ih))
                # Left edge highlight
                pygame.draw.line(surface, IRON_H,
                                 (bx_l + 1, iy + 3), (bx_l + 1, iy + ih - 3), 2)
                # Specular flash near top
                pygame.draw.line(surface, IRON_SH,
                                 (bx_l + 1, iy + 4), (bx_l + 2, iy + 14), 1)
                # Right edge shadow
                pygame.draw.line(surface, IRON_D,
                                 (bx_l + bar_thick - 1, iy), (bx_l + bar_thick - 1, iy + ih), 1)
                # Pointed tip at top  ▲
                tip_half = bar_thick // 2
                pts_t = [(bx_c, iy - tip_half - 2),
                         (bx_l - 1, iy + tip_half),
                         (bx_l + bar_thick, iy + tip_half)]
                pygame.draw.polygon(surface, IRON_H,  pts_t)
                pygame.draw.polygon(surface, IRON_SH, pts_t, 1)
                # Pointed tip at bottom  ▼
                pts_b = [(bx_c, iy + ih + tip_half + 2),
                         (bx_l - 1, iy + ih - tip_half),
                         (bx_l + bar_thick, iy + ih - tip_half)]
                pygame.draw.polygon(surface, IRON_H,  pts_b)
                pygame.draw.polygon(surface, IRON_SH, pts_b, 1)

            # ── 5. Horizontal reinforcing bars ─────────────────
            for rel_y in [ih // 3, ih * 2 // 3]:
                rby = iy + rel_y
                pygame.draw.rect(surface, IRON_M,  (ix, rby - 3, iw, 6))
                pygame.draw.line(surface, IRON_H,  (ix, rby - 2), (ix + iw, rby - 2), 1)
                pygame.draw.line(surface, IRON_SH, (ix, rby - 2), (ix + iw//4, rby - 2), 1)
                pygame.draw.line(surface, IRON_D,  (ix, rby + 2), (ix + iw, rby + 2), 1)

            # ── 6. Corner bolts ────────────────────────────────
            for cbx, cby in [(ix-1, iy-1), (ix+iw, iy-1),
                             (ix-1, iy+ih), (ix+iw, iy+ih)]:
                pygame.draw.circle(surface, IRON_D,  (cbx, cby), 5)
                pygame.draw.circle(surface, IRON_M,  (cbx, cby), 5, 2)
                pygame.draw.circle(surface, IRON_SH, (cbx-1, cby-1), 2)

            # ── 7. Pulsing magic outer glow ────────────────────
            for gsize in (5, 3, 1):
                ga = int((70 - gsize * 10) * (0.5 + pulse * 0.5))
                gs = pygame.Surface((w + gsize*4, h + gsize*4), pygame.SRCALPHA)
                pygame.draw.rect(gs, (*magic, ga),
                                 (0, 0, w+gsize*4, h+gsize*4), gsize, border_radius=5)
                surface.blit(gs, (sx - gsize*2, sy - gsize*2))

            # ── 8. Pulsing warning skull ───────────────────────
            cx2 = sx + w // 2; cy2 = sy + h // 2
            skull_a = int(140 + pulse * 100)
            # Head
            sk = pygame.Surface((22, 22), pygame.SRCALPHA)
            pygame.draw.circle(sk, (255, 50, 50, skull_a), (11, 9), 8)
            # Jaw
            pygame.draw.rect(sk, (255, 50, 50, skull_a), (4, 14, 14, 6), border_radius=3)
            # Eye holes
            pygame.draw.circle(sk, (0, 0, 0, 220), (7,  8), 2)
            pygame.draw.circle(sk, (0, 0, 0, 220), (15, 8), 2)
            # Nose hole
            pygame.draw.rect(sk, (0, 0, 0, 180), (9, 11, 4, 3), border_radius=1)
            surface.blit(sk, (cx2 - 11, cy2 - 11))

            # ── 9. Boss-lock overlay (gold chains + lock + label) ──
            if self.door_locked:
                DF_GOLD   = (200, 165,  80)
                DF_GOLD_B = (255, 215,  60)
                DF_STONE  = (30,  22,  14)

                # Darken the whole door further
                dark = pygame.Surface((w, h), pygame.SRCALPHA)
                dark.fill((0, 0, 0, 80))
                surface.blit(dark, (sx, sy))

                # Gold chain lines (diagonal cross)
                chain_col = (*DF_GOLD, int(180 + pulse * 60))
                for seg in range(0, max(w, h), 12):
                    # top-left to bottom-right
                    cs = pygame.Surface((4, 4), pygame.SRCALPHA)
                    cs.fill(chain_col)
                    surface.blit(cs, (sx + seg % w, sy + seg % h))
                chain_s = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.line(chain_s, (*DF_GOLD, 160), (0, 0), (w, h), 3)
                pygame.draw.line(chain_s, (*DF_GOLD, 160), (w, 0), (0, h), 3)
                # Small chain links along diagonals
                for i in range(5):
                    frac = (i + 1) / 6
                    lx = int(frac * w); ly2 = int(frac * h)
                    pygame.draw.circle(chain_s, (*DF_GOLD_B, 200), (lx, ly2), 4)
                    pygame.draw.circle(chain_s, (*DF_GOLD_B, 200), (w - lx, ly2), 4)
                surface.blit(chain_s, (sx, sy))

                # Lock icon in centre
                lk_w, lk_h = 24, 28
                lk_x = cx2 - lk_w // 2
                lk_y = cy2 - lk_h // 2 - 4
                # Lock shackle (arc)
                arc_rect = pygame.Rect(lk_x + 4, lk_y - 8, lk_w - 8, 20)
                pygame.draw.arc(surface, DF_GOLD_B, arc_rect, 0, math.pi, 4)
                # Lock body
                pygame.draw.rect(surface, DF_STONE,  (lk_x, lk_y + 6,  lk_w, lk_h - 6), border_radius=4)
                pygame.draw.rect(surface, DF_GOLD_B, (lk_x, lk_y + 6,  lk_w, lk_h - 6), 2, border_radius=4)
                # Keyhole
                pygame.draw.circle(surface, (0, 0, 0), (cx2, lk_y + 14), 4)
                pygame.draw.rect(surface,   (0, 0, 0), (cx2 - 2, lk_y + 14, 4, 7))

                # "BOSS" label below lock
                try:
                    lbl_f = pygame.font.SysFont("impact", 13)
                except Exception:
                    lbl_f = pygame.font.Font(None, 15)
                lbl_pulse_a = int(160 + pulse * 95)
                lbl_s = lbl_f.render("BOSS", True, DF_GOLD_B)
                lbl_surf = pygame.Surface((lbl_s.get_width(), lbl_s.get_height()), pygame.SRCALPHA)
                lbl_surf.blit(lbl_s, (0, 0))
                lbl_surf.set_alpha(lbl_pulse_a)
                surface.blit(lbl_surf, (cx2 - lbl_s.get_width() // 2, lk_y + lk_h + 2))





    # ── Boss-door opening animation ───────────────────────────
    def _draw_door_opening_anim(self, surface, cam_x, cam_y, theme):
        """
        Cinematic SPLIT-OPEN boss-door animation.
        The two door panel halves slide apart (left panel → left, right panel → right)
        with a bright gold flash at the crack, expanding shockwave ring, and particles.

        Phase 0-15%  : bright central flash (chains shatter)
        Phase 0-70%  : golden shockwave ring expands outward
        Phase 10-100%: left & right door halves slide apart, fade at edges
        Phase 0-100% : spark/chunk particles fly
        """
        THEME_MAGIC = {
            "forest":  (60,  220,  80),
            "dungeon": (160,  80, 255),
            "volcano": (255, 100,  20),
            "sky":     ( 80, 190, 255),
            "chaos":   (220,  40, 200),
        }
        magic = THEME_MAGIC.get(theme, (160, 80, 255))
        gold  = (255, 215, 60)

        progress = 1.0 - max(0.0, self.door_anim_t) / DOOR_ANIM_DUR  # 0 → 1

        STONE_D  = (35, 35, 42)
        STONE_M  = (58, 60, 72)
        STONE_H  = (90, 95, 115)
        IRON_M   = (50, 54, 66)
        IRON_H   = (105, 115, 138)
        IRON_SH  = (185, 195, 218)
        IRON_D   = (22, 24, 30)
        FRAME    = 10

        # Ease-out curve for sliding panels (fast start, decelerates)
        def ease_out(t):
            return 1.0 - (1.0 - t) ** 3

        for dr in self.door_rects:
            sx = dr.x - int(cam_x)
            sy = dr.y - int(cam_y)
            w, h = dr.w, dr.h
            ix = sx + FRAME; iy = sy + FRAME
            iw = w - FRAME * 2; ih = h - FRAME * 2
            cx2 = sx + w // 2; cy2 = sy + h // 2

            # How far each panel slides (half the door width + a bit extra)
            slide_progress = ease_out(max(0.0, (progress - 0.10) / 0.90))
            max_slide = w // 2 + 8   # slides fully off its original half
            slide_px  = int(slide_progress * max_slide)

            # Panel alpha fades as it slides away
            panel_alpha = max(0, int(255 * (1.0 - slide_progress * 0.85)))

            # ── 1. Stone outer frame (stays fixed, fades last) ─
            frame_alpha = max(0, int(255 * (1.0 - progress * 0.65)))
            if frame_alpha > 0:
                fs = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.rect(fs, (*STONE_D, frame_alpha), (0, 0, w, h))
                pygame.draw.rect(fs, (*STONE_M, frame_alpha), (0, 0, w, FRAME))
                pygame.draw.rect(fs, (*STONE_M, frame_alpha), (0, h - FRAME, w, FRAME))
                pygame.draw.rect(fs, (*STONE_M, frame_alpha), (0, 0, FRAME, h))
                pygame.draw.rect(fs, (*STONE_M, frame_alpha), (w - FRAME, 0, FRAME, h))
                pygame.draw.line(fs, (*STONE_H, frame_alpha), (1, 1), (w - 2, 1), 2)
                pygame.draw.line(fs, (*STONE_H, frame_alpha), (1, 1), (1, h - 2), 2)
                surface.blit(fs, (sx, sy))

            if iw > 0 and ih > 0:
                # ── 2. Inner void revealed behind panels ──────
                void_surf = pygame.Surface((iw, ih))
                void_surf.fill((6, 4, 12))
                # Glow from inside (magic light pouring through the gap)
                gap_glow_a = int(180 * slide_progress)
                if gap_glow_a > 0:
                    gg = pygame.Surface((iw, ih), pygame.SRCALPHA)
                    gg.fill((*magic, gap_glow_a))
                    void_surf.blit(gg, (0, 0))
                surface.blit(void_surf, (ix, iy))

                # ── 3. LEFT door panel slides LEFT ────────────
                if panel_alpha > 0:
                    half_w = iw // 2
                    # Build the left door-panel surface
                    lp = pygame.Surface((half_w, ih), pygame.SRCALPHA)
                    # Background fill
                    pygame.draw.rect(lp, (*IRON_M, panel_alpha), (0, 0, half_w, ih))
                    # Vertical bars on left panel
                    bar_thick = 5
                    bar_count = max(2, half_w // 13)
                    spacing   = half_w / bar_count
                    for i in range(bar_count):
                        bx_c = int(i * spacing) + int(spacing / 2)
                        bx_l = max(0, bx_c - bar_thick // 2)
                        bw   = min(bar_thick, half_w - bx_l)
                        pygame.draw.rect(lp, (*IRON_D, panel_alpha), (bx_l, 0, bw, ih))
                        pygame.draw.line(lp, (*IRON_H, panel_alpha), (bx_l + 1, 3), (bx_l + 1, ih - 3), 1)
                        pygame.draw.line(lp, (*IRON_SH, min(panel_alpha, 180)), (bx_l + 1, 4), (bx_l + 2, 12), 1)
                    # Horizontal crossbar
                    for rel_y in [ih // 3, ih * 2 // 3]:
                        pygame.draw.rect(lp, (*IRON_D, panel_alpha), (0, rel_y - 3, half_w, 5))
                        pygame.draw.line(lp, (*IRON_H, panel_alpha), (0, rel_y - 2), (half_w, rel_y - 2), 1)
                    # Right edge of left panel — bright seam glows gold as it opens
                    seam_a = min(panel_alpha, int(255 * slide_progress))
                    if seam_a > 10:
                        pygame.draw.line(lp, (*gold, seam_a), (half_w - 1, 0), (half_w - 1, ih), 2)
                    # Blit left panel shifted LEFT by slide_px
                    surface.blit(lp, (ix - slide_px, iy))

                    # ── 4. RIGHT door panel slides RIGHT ──────
                    rp = pygame.Surface((half_w, ih), pygame.SRCALPHA)
                    pygame.draw.rect(rp, (*IRON_M, panel_alpha), (0, 0, half_w, ih))
                    for i in range(bar_count):
                        bx_c = int(i * spacing) + int(spacing / 2)
                        bx_l = max(0, bx_c - bar_thick // 2)
                        bw   = min(bar_thick, half_w - bx_l)
                        pygame.draw.rect(rp, (*IRON_D, panel_alpha), (bx_l, 0, bw, ih))
                        pygame.draw.line(rp, (*IRON_H, panel_alpha), (bx_l + 1, 3), (bx_l + 1, ih - 3), 1)
                        pygame.draw.line(rp, (*IRON_SH, min(panel_alpha, 180)), (bx_l + 1, 4), (bx_l + 2, 12), 1)
                    for rel_y in [ih // 3, ih * 2 // 3]:
                        pygame.draw.rect(rp, (*IRON_D, panel_alpha), (0, rel_y - 3, half_w, 5))
                        pygame.draw.line(rp, (*IRON_H, panel_alpha), (0, rel_y - 2), (half_w, rel_y - 2), 1)
                    # Left edge seam glow
                    if seam_a > 10:
                        pygame.draw.line(rp, (*gold, seam_a), (0, 0), (0, ih), 2)
                    # Blit right panel shifted RIGHT by slide_px
                    surface.blit(rp, (ix + half_w + slide_px, iy))

                # ── 5. Bright gold crack/seam between panels ──
                # Fades in quickly then fades out as gap widens
                seam_peak  = 0.25
                if progress < seam_peak:
                    crack_a = int(255 * (progress / seam_peak))
                else:
                    crack_a = int(255 * max(0.0, 1.0 - (progress - seam_peak) / 0.40))
                if crack_a > 0:
                    crack_w = max(2, int(slide_px * 2))
                    crack_surf = pygame.Surface((crack_w + 8, ih + 8), pygame.SRCALPHA)
                    for gw, ga_mul in [(crack_w + 8, 0.15), (crack_w // 2 + 4, 0.35), (4, 0.80)]:
                        pygame.draw.rect(crack_surf, (*gold, int(crack_a * ga_mul)),
                                         ((crack_w + 8 - gw) // 2, 0, gw, ih + 8))
                    surface.blit(crack_surf, (cx2 - (crack_w + 8) // 2, iy - 4))

            # ── 6. Expanding shockwave ring ────────────────────
            if progress < 0.70:
                t_norm  = progress / 0.70
                ring_r  = int(t_norm * max(w, h) * 1.3)
                ring_a  = int(230 * (1.0 - t_norm) ** 1.8)
                if ring_r > 0 and ring_a > 0:
                    for thickness, col, a_mul in [
                        (10, gold,            1.0),
                        (5,  (255, 255, 200), 0.65),
                        (20, gold,            0.25),
                    ]:
                        rs = pygame.Surface((ring_r * 2 + 6, ring_r * 2 + 6), pygame.SRCALPHA)
                        pygame.draw.circle(rs, (*col, int(ring_a * a_mul)),
                                           (ring_r + 3, ring_r + 3), ring_r, thickness)
                        surface.blit(rs, (cx2 - ring_r - 3, cy2 - ring_r - 3))

            # ── 7. Central flash on initial break ─────────────
            if progress < 0.18:
                flash_a = int(255 * (1.0 - progress / 0.18) ** 2)
                fl = pygame.Surface((w + 24, h + 24), pygame.SRCALPHA)
                fl.fill((*gold, flash_a))
                surface.blit(fl, (sx - 12, sy - 12))

            # ── 8. Outer gold glow rect ────────────────────────
            if progress < 0.55:
                gout_a = int(160 * (1.0 - progress / 0.55))
                for gs2 in (7, 4, 1):
                    gg2 = pygame.Surface((w + gs2 * 4, h + gs2 * 4), pygame.SRCALPHA)
                    pygame.draw.rect(gg2, (*gold, int(gout_a * (0.25 + gs2 * 0.10))),
                                     (0, 0, w + gs2 * 4, h + gs2 * 4), gs2, border_radius=6)
                    surface.blit(gg2, (sx - gs2 * 2, sy - gs2 * 2))

        # Draw particles on top of everything
        for p in self.door_anim_particles:
            p.draw(surface, cam_x, cam_y)


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
        self._amb_particles = []
        self._amb_timer = 0.0
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

        # ── Room budget per stage ──────────────────────────────
        # Stage 1 : hub + 4 spokes + 1 sec           =  6 rooms max
        # Stage 2 : hub + 4 spokes + 2 sec           =  7 rooms max
        # Stage 3 : hub + 4 spokes + 3 sec           =  8 rooms max
        # Stage 4 : hub + 4 spokes + 4 sec + 1 ter   = 10 rooms max
        # Stage 5+: hub + 4 spokes + 4 sec + 2+ ter  = 11+ rooms max
        # stage_id is 0-based: 0=stage1, 1=stage2, ...
        max_primary   = 4   # always 4 primary spokes (N/S/E/W)
        max_secondary = {0: 1, 1: 2, 2: 3}.get(self.stage_id, 4)
        max_tertiary  = max(0, self.stage_id - 1)   # 0,0,1,2,3 for stages 0-4

        # ── 3) Primary spokes N/S/E/W from hub ────────────────
        dirs = ["N", "S", "E", "W"]
        random.shuffle(dirs)
        placed = []   # list of (dir, room_rect)
        primary_spoke_rects = []   # track primary spoke room_rects for boss selection
        for d in dirs[:max_primary]:
            r = branch(d, hub)
            if r:
                placed.append((d, r))
                primary_spoke_rects.append(r)  # direct child of hub → boss candidate

        # ── 3b) Pick boss spoke BEFORE branching so we can exclude it ──
        # Boss room = largest primary spoke (connected only to hub, nothing branches from it)
        boss_spoke_rect = max(primary_spoke_rects, key=lambda r: r.w * r.h) if primary_spoke_rects else None

        # ── 4) Secondary branches — skip boss spoke as parent ──
        perp_map = {
            "N": ["E", "W"], "S": ["E", "W"],
            "E": ["N", "S"], "W": ["N", "S"],
        }
        secondary = []
        sec_count = 0
        for par_d, par_r in placed:
            if sec_count >= max_secondary:
                break
            if par_r is boss_spoke_rect:
                continue   # boss room connects ONLY to hub — no children
            perps = perp_map[par_d][:]
            random.shuffle(perps)
            for pd in perps:
                r2 = branch(pd, par_r,
                            corr_len=random.randint(4, 8),
                            rw=random.randint(6, 9),
                            rh=random.randint(5, 8))
                if r2:
                    secondary.append((pd, r2))
                    sec_count += 1
                    break   # one secondary per spoke

        # ── 5) Tertiary branches (stage ≥ 4) — also skip boss spoke ──
        if max_tertiary > 0:
            all_placed = placed + secondary
            random.shuffle(all_placed)
            ter_count = 0
            for par_d, par_r in all_placed:
                if ter_count >= max_tertiary:
                    break
                if par_r is boss_spoke_rect:
                    continue   # never extend from boss room
                for td in [par_d] + perp_map[par_d]:
                    r3 = branch(td, par_r,
                                corr_len=random.randint(4, 7),
                                rw=random.randint(5, 8),
                                rh=random.randint(5, 7))
                    if r3:
                        ter_count += 1
                        break

        # ── 6) Build wall_rects from tilemap ──────────────────
        self.wall_rects = []
        for ty in range(self.MAP_H):
            for tx in range(self.MAP_W):
                if self.tilemap[ty][tx] == 0:
                    self.wall_rects.append(pygame.Rect(tx*TILE, ty*TILE, TILE, TILE))

        self.rooms = [Room(r) for r in room_rects]
        # boss_room = the pre-selected spoke (no child rooms branch from it)
        primary_room_objs = [
            rm for rm in self.rooms
            if any(rm.rect == pr for pr in primary_spoke_rects)
        ]
        if boss_spoke_rect is not None:
            boss_match = [rm for rm in primary_room_objs if rm.rect == boss_spoke_rect]
            self.boss_room = boss_match[0] if boss_match else max(primary_room_objs or self.rooms[1:], key=lambda r: r.rect.w * r.rect.h)
        else:
            self.boss_room = max(primary_room_objs or self.rooms[1:], key=lambda r: r.rect.w * r.rect.h)
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
        """Remove door rects from wall_rects, trigger opening animation for boss rooms."""
        # ── Boss door: fire animation BEFORE the early-return check ──────────
        # Boss room starts with doors_open=True (never closed), so we must
        # trigger the animation here regardless of doors_open state.
        if room.is_boss and room.door_rects and not room.door_opening:
            room.door_opening = True
            room.door_anim_t  = DOOR_ANIM_DUR
            room.door_anim_particles.clear()
            gold_cols  = [(255, 215,  60), (255, 255, 160), (255, 180,  30)]
            magic_cols = [(200, 120, 255), (255,  80, 200), (120, 200, 255), (255, 255, 200)]
            for dr in room.door_rects:
                cx, cy = dr.centerx, dr.centery
                # Emit particles from the full height of each door tile
                for _ in range(50):                       # dense sparks
                    col = random.choice(gold_cols + magic_cols)
                    # Randomize y along door height for spread
                    emit_y = dr.y + random.randint(0, dr.h)
                    room.door_anim_particles.append(
                        DoorOpenParticle(cx, emit_y, col, kind="spark"))
                for _ in range(15):                       # larger debris chunks
                    col = random.choice(gold_cols)
                    emit_y = dr.y + random.randint(0, dr.h)
                    room.door_anim_particles.append(
                        DoorOpenParticle(cx, emit_y, col, kind="chunk"))

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
                # no extra mobs spawned in boss room — boss fights alone
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
        # Ambient particle spawning
        self._amb_timer += dt
        if self._amb_timer >= 0.13 and len(self._amb_particles) < 80:
            self._amb_timer = 0.0
            play_h = SCREEN_H - HUD_H
            start_tx = int(self.cam_x // TILE)
            start_ty = int(self.cam_y // TILE)
            end_tx = start_tx + SCREEN_W // TILE + 2
            end_ty = start_ty + play_h  // TILE + 2
            for _ in range(3):
                tx = random.randint(max(0, start_tx), min(self.MAP_W-1, end_tx))
                ty = random.randint(max(0, start_ty), min(self.MAP_H-1, end_ty))
                if self.tilemap[ty][tx] == 1:
                    wx = tx*TILE + random.randint(0, TILE)
                    wy = ty*TILE + random.randint(0, TILE)
                    self._amb_particles.append(AmbientParticle(wx, wy, self.theme))
                    break
        self._amb_particles = [p for p in self._amb_particles if p.update(dt)]

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
        _init_shadows()
        # PASS 1: blit procedural tile textures
        for ty in range(max(0, start_ty), min(self.MAP_H, end_ty)):
            for tx in range(max(0, start_tx), min(self.MAP_W, end_tx)):
                sx = tx * TILE - int(self.cam_x)
                sy = ty * TILE - int(self.cam_y)
                if self.tilemap[ty][tx] == 1:
                    surface.blit(_get_floor(self.theme, tx, ty), (sx, sy))
                else:
                    below = (ty+1 < self.MAP_H and self.tilemap[ty+1][tx] == 1)
                    surface.blit(_get_wall(self.theme, tx, ty, below), (sx, sy))
        # PASS 2: depth shadows where wall meets floor
        for ty in range(max(0, start_ty), min(self.MAP_H, end_ty)):
            for tx in range(max(0, start_tx), min(self.MAP_W, end_tx)):
                if self.tilemap[ty][tx] == 0:
                    continue
                sx = tx * TILE - int(self.cam_x)
                sy = ty * TILE - int(self.cam_y)
                if ty > 0 and self.tilemap[ty-1][tx] == 0:
                    surface.blit(_SHADOW_TOP, (sx, sy))
                if tx > 0 and self.tilemap[ty][tx-1] == 0:
                    surface.blit(_SHADOW_LEFT, (sx, sy))
        # Ambient particles
        for p in self._amb_particles:
            p.draw(surface, self.cam_x, self.cam_y)
        # Fountains, doors, torches
        for room in self.rooms:
            room.draw_fountain(surface, self.cam_x, self.cam_y, player)
            room.draw_doors(surface, self.cam_x, self.cam_y, self.theme)
        self._draw_torches(surface)

    def _draw_torches(self, surface):
        """Flickering flame torch with warm glow."""
        t = pygame.time.get_ticks() / 1000.0
        for wx, wy in getattr(self, "_torch_positions", []):
            sx = int(wx - self.cam_x)
            sy = int(wy - self.cam_y)
            play_h = SCREEN_H - HUD_H
            if sx < -30 or sx > SCREEN_W+30 or sy < -30 or sy > play_h+30:
                continue
            seed = wx * 0.037 + wy * 0.019
            flicker = math.sin(t*7.3+seed)*0.15 + math.sin(t*13.1+seed)*0.08
            pulse = 0.85 + flicker
            # Outer warm halo
            glow_r = int(26 * pulse)
            gs = pygame.Surface((glow_r*2+6, glow_r*2+6), pygame.SRCALPHA)
            pygame.draw.circle(gs, (255,180,60,45), (glow_r+3,glow_r+3), glow_r)
            surface.blit(gs, (sx-glow_r-3, sy-glow_r-3))
            in_r = int(12*pulse)
            ins = pygame.Surface((in_r*2+4,in_r*2+4), pygame.SRCALPHA)
            pygame.draw.circle(ins,(255,220,100,80),(in_r+2,in_r+2),in_r)
            surface.blit(ins,(sx-in_r-2,sy-in_r-2))
            # Wall bracket
            pygame.draw.rect(surface,(80,70,60),(sx-4,sy+2,8,5),border_radius=2)
            pygame.draw.rect(surface,(50,45,38),(sx-4,sy+2,8,5),1,border_radius=2)
            # Flame layers
            flame_h = int(12*pulse); flame_w = int(7*pulse)
            pygame.draw.ellipse(surface,(200,80,10),(sx-flame_w,sy-flame_h,flame_w*2,flame_h))
            pygame.draw.ellipse(surface,(255,150,20),(sx-flame_w+2,sy-flame_h+3,flame_w*2-4,flame_h-3))
            pygame.draw.ellipse(surface,(255,240,100),(sx-flame_w+4,sy-flame_h+5,flame_w*2-8,max(1,flame_h-5)))
            if flame_h > 8:
                pygame.draw.circle(surface,(255,255,230),(sx,sy-flame_h+2),2)

    def _floor_color(self):
        return {"forest":(60,90,40),"dungeon":(55,55,65),"volcano":(80,45,30),
                "sky":(70,100,130),"chaos":(60,40,80)}.get(self.theme,(60,60,60))

    def _wall_color(self):
        return {"forest":(30,55,20),"dungeon":(30,30,40),"volcano":(50,25,15),
                "sky":(40,65,90),"chaos":(35,20,50)}.get(self.theme,(30,30,30))

    # ── Minimap ───────────────────────────────────────────────
    def draw_minimap(self, surface, px, py, size=124):
        mx = SCREEN_W - size - 8
        my = 8
        # Background panel
        panel = pygame.Surface((size+4, size+4), pygame.SRCALPHA)
        pygame.draw.rect(panel,(0,0,0,180),(0,0,size+4,size+4),border_radius=6)
        pygame.draw.rect(panel,(60,70,100,200),(0,0,size+4,size+4),2,border_radius=6)
        surface.blit(panel,(mx-2,my-2))
        mini_surf = pygame.Surface((size,size), pygame.SRCALPHA)
        scale = size / max(self.MAP_W*TILE, self.MAP_H*TILE)
        tile_px = max(1, int(TILE//3*scale*3))
        # Draw floor tiles
        for ty in range(0, self.MAP_H, 3):
            for tx in range(0, self.MAP_W, 3):
                if self.tilemap[ty][tx] == 1:
                    rx=int(tx*TILE*scale); ry=int(ty*TILE*scale)
                    pygame.draw.rect(mini_surf,(55,65,80,200),(rx,ry,tile_px,tile_px))
        # Draw rooms
        for room in self.rooms:
            rx=int(room.rect.x*TILE*scale); ry=int(room.rect.y*TILE*scale)
            rw=max(4,int(room.rect.w*TILE*scale)); rh=max(4,int(room.rect.h*TILE*scale))
            boss_cleared = room.is_boss and room.cleared
            if boss_cleared:
                col=(20,140,50,240); bcol=(80,255,120,255)
            elif room.is_boss:
                col=(200,40,40,230); bcol=(255,80,80,255)
            elif room.cleared:
                col=(30,100,50,220); bcol=(50,160,80,255)
            else:
                col=(35,40,60,200); bcol=(60,70,110,255)
            pygame.draw.rect(mini_surf,col,(rx,ry,rw,rh),border_radius=2)
            pygame.draw.rect(mini_surf,bcol,(rx,ry,rw,rh),1,border_radius=2)
            cx_m=rx+rw//2; cy_m=ry+rh//2
            if boss_cleared and rw>=5:
                # ✔ large bright green checkmark with outline
                pts=[(cx_m-3,cy_m+1),(cx_m-1,cy_m+3),(cx_m+4,cy_m-3)]
                pygame.draw.lines(mini_surf,(0,80,20,255),False,pts,2)
                pygame.draw.lines(mini_surf,(120,255,140,255),False,pts,1)
            elif room.is_boss and rw>=6:
                pygame.draw.circle(mini_surf,(255,60,60,255),(cx_m,cy_m),max(2,rw//4))
            elif room.cleared and rw>=5:
                pygame.draw.line(mini_surf,(80,255,120,255),(cx_m-2,cy_m),(cx_m,cy_m+2),1)
                pygame.draw.line(mini_surf,(80,255,120,255),(cx_m,cy_m+2),(cx_m+3,cy_m-2),1)
        # Player dot
        pdx=max(2,min(size-3,int(px*scale))); pdy=max(2,min(size-3,int(py*scale)))
        pygame.draw.circle(mini_surf,(0,200,100,120),(pdx,pdy),5)
        pygame.draw.circle(mini_surf,(0,255,120,255),(pdx,pdy),3)
        pygame.draw.circle(mini_surf,(255,255,255,255),(pdx,pdy),1)
        surface.blit(mini_surf,(mx,my))
        # Legend
        fnt=pygame.font.SysFont("Arial",9,bold=True)
        legend=[((200,40,40),"BOSS"),((30,100,50),"✔ Clear")]
        lx=mx; ly=my+size+3
        for col,label in legend:
            pygame.draw.rect(surface,col,(lx,ly,7,7),border_radius=1)
            ls=fnt.render(label,True,(160,170,200)); surface.blit(ls,(lx+9,ly-1)); lx+=9+ls.get_width()+4
        # Stage name
        nfnt=pygame.font.SysFont("Arial",10,bold=True)
        ns=nfnt.render(self.stage_name,True,(180,195,230))
        surface.blit(ns,(mx+size//2-ns.get_width()//2,my-14))