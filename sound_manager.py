"""
sound_manager.py  –  SoundManager (Procedural audio via numpy + pygame.sndarray)
No external audio files required – all sounds synthesized via waveform synthesis

Changes:
  - Reads actual sample rate from pygame.mixer (not hardcoded 44100)
  - If mixer is not ready → runs as silent no-op without crashing
  - Adjusts array format to match the initialized mixer settings
"""

import numpy as np
import pygame

SFX_VOL    = 0.70
MASTER_VOL = 0.55


# ════════════════════════════════════════════════════════════
#  Synthesis helpers
# ════════════════════════════════════════════════════════════

def _make_sound(arr: np.ndarray, sr: int, mixer_channels: int) -> pygame.mixer.Sound:
    arr = np.clip(arr, -1.0, 1.0).astype(np.float32)
    if mixer_channels == 2:
        pcm = np.column_stack([arr, arr])
    else:
        pcm = arr.reshape(-1, 1)
    pcm = (pcm * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(pcm)


def _envelope(n, attack, decay, sustain_level, release, sr):
    a = max(1, int(attack  * sr))
    d = max(1, int(decay   * sr))
    r = max(1, int(release * sr))
    s_len = max(0, n - a - d - r)
    env = np.zeros(n, dtype=np.float32)
    env[:a]                          = np.linspace(0, 1, a)
    env[a:a+d]                       = np.linspace(1, sustain_level, d)
    env[a+d:a+d+s_len]               = sustain_level
    tail_start = a + d + s_len
    tail_end   = min(tail_start + r, n)
    env[tail_start:tail_end]         = np.linspace(sustain_level, 0, tail_end - tail_start)
    return env


def _sine(freq, n, sr):
    t = np.arange(n, dtype=np.float32) / sr
    return np.sin(2 * np.pi * freq * t).astype(np.float32)


def _square(freq, n, duty=0.5, sr=44100):
    t = np.arange(n, dtype=np.float32) / sr
    return np.where((t * freq % 1) < duty, 1.0, -1.0).astype(np.float32)


def _noise(n):
    return np.random.uniform(-1, 1, n).astype(np.float32)


def _sweep(f0, f1, n, sr):
    freqs = np.linspace(f0, f1, n, dtype=np.float32)
    phase = np.cumsum(freqs / sr * 2 * np.pi)
    return np.sin(phase).astype(np.float32)


# ════════════════════════════════════════════════════════════
#  Sound effects by type
# ════════════════════════════════════════════════════════════

def _build_shoot(sr, ch):
    n  = int(sr * 0.10)
    sw = _sweep(900, 200, n, sr) * 0.55
    ns = _noise(n) * 0.45
    return _make_sound((sw + ns) * _envelope(n, 0.002, 0.04, 0.0, 0.06, sr) * SFX_VOL, sr, ch)

def _build_shoot_heavy(sr, ch):
    n  = int(sr * 0.22)
    ns = _noise(n) * 0.70
    lo = _sweep(300, 60, n, sr) * 0.50
    return _make_sound((ns + lo) * _envelope(n, 0.003, 0.08, 0.0, 0.13, sr) * SFX_VOL, sr, ch)

def _build_shoot_laser(sr, ch):
    n  = int(sr * 0.14)
    sw = _sweep(3200, 800, n, sr) * 0.60
    sq = _square(1600, n, 0.3, sr) * 0.30
    return _make_sound((sw + sq) * _envelope(n, 0.001, 0.05, 0.0, 0.09, sr) * SFX_VOL, sr, ch)

def _build_hit_enemy(sr, ch):
    n    = int(sr * 0.07)
    ns   = _noise(n) * 0.60
    tone = _sine(180, n, sr) * 0.50
    return _make_sound((ns + tone) * _envelope(n, 0.001, 0.03, 0.0, 0.04, sr) * SFX_VOL * 0.85, sr, ch)

def _build_hit_player(sr, ch):
    n  = int(sr * 0.18)
    ns = _noise(n) * 0.65
    sw = _sweep(400, 80, n, sr) * 0.55
    return _make_sound((ns + sw) * _envelope(n, 0.002, 0.06, 0.0, 0.12, sr) * SFX_VOL, sr, ch)

def _build_enemy_die(sr, ch):
    n  = int(sr * 0.15)
    sw = _sweep(600, 80, n, sr) * 0.55
    ns = _noise(n) * 0.35
    return _make_sound((sw + ns) * _envelope(n, 0.001, 0.04, 0.0, 0.11, sr) * SFX_VOL, sr, ch)

def _build_boss_die(sr, ch):
    n      = int(sr * 0.70)
    ns     = _noise(n) * 0.75
    lo     = _sweep(250, 30, n, sr) * 0.50
    rumble = _sine(55, n, sr) * 0.40
    return _make_sound((ns + lo + rumble) * _envelope(n, 0.01, 0.15, 0.2, 0.54, sr) * SFX_VOL, sr, ch)

def _build_item_pickup(sr, ch):
    dur = 0.08
    n   = int(sr * dur)
    out = np.zeros(int(sr * dur * 3), dtype=np.float32)
    for i, f in enumerate([523, 659, 784]):
        t0  = int(i * sr * dur)
        seg = _sine(f, n, sr) * _envelope(n, 0.002, 0.02, 0.3, 0.06, sr) * 0.55
        end = min(t0 + n, len(out))
        out[t0:end] += seg[:end - t0]
    return _make_sound(out * SFX_VOL, sr, ch)

def _build_level_up(sr, ch):
    dur = 0.09
    n   = int(sr * dur)
    out = np.zeros(int(sr * dur * 5), dtype=np.float32)
    for i, f in enumerate([523, 659, 784, 1047]):
        t0  = int(i * sr * dur * 0.9)
        seg = (_sine(f, n, sr) + _sine(f * 2, n, sr) * 0.3) * _envelope(n, 0.002, 0.03, 0.4, 0.07, sr) * 0.5
        end = min(t0 + n, len(out))
        out[t0:end] += seg[:end - t0]
    return _make_sound(out * SFX_VOL, sr, ch)

def _build_portal_open(sr, ch):
    n   = int(sr * 0.55)
    sw  = _sweep(200, 1800, n, sr) * 0.50
    sw2 = _sweep(800, 200,  n, sr) * 0.30
    ns  = _noise(n) * 0.15
    return _make_sound((sw + sw2 + ns) * _envelope(n, 0.05, 0.20, 0.25, 0.30, sr) * SFX_VOL, sr, ch)

def _build_player_die(sr, ch):
    n  = int(sr * 0.85)
    sw = _sweep(440, 55, n, sr) * 0.55
    ns = _noise(n) * 0.30
    return _make_sound((sw + ns) * _envelope(n, 0.01, 0.20, 0.15, 0.65, sr) * SFX_VOL, sr, ch)

def _build_menu_click(sr, ch):
    n  = int(sr * 0.045)
    sq = _square(900, n, 0.4, sr) * 0.35
    return _make_sound(sq * _envelope(n, 0.001, 0.015, 0.0, 0.03, sr) * SFX_VOL * 0.8, sr, ch)

def _build_shop_buy(sr, ch):
    dur = 0.06
    n   = int(sr * dur)
    out = np.zeros(int(sr * dur * 3), dtype=np.float32)
    for i, f in enumerate([784, 1047, 1319]):
        t0  = int(i * sr * dur * 0.85)
        seg = _sine(f, n, sr) * _envelope(n, 0.001, 0.02, 0.2, 0.05, sr) * 0.5
        end = min(t0 + n, len(out))
        out[t0:end] += seg[:end - t0]
    return _make_sound(out * SFX_VOL, sr, ch)

def _build_skill_dash(sr, ch):
    n  = int(sr * 0.16)
    ns = _noise(n) * 0.55
    sw = _sweep(1200, 300, n, sr) * 0.40
    return _make_sound((ns + sw) * _envelope(n, 0.003, 0.05, 0.0, 0.11, sr) * SFX_VOL, sr, ch)

def _build_skill_star(sr, ch):
    n  = int(sr * 0.20)
    sw = _sweep(2000, 600, n, sr) * 0.45
    sq = _square(1200, n, 0.3, sr) * 0.25
    ns = _noise(n) * 0.20
    return _make_sound((sw + sq + ns) * _envelope(n, 0.002, 0.07, 0.0, 0.13, sr) * SFX_VOL, sr, ch)

def _build_skill_frenzy(sr, ch):
    n  = int(sr * 0.30)
    ns = _noise(n) * 0.60
    sw = _sweep(300, 2400, n, sr) * 0.40
    return _make_sound((ns + sw) * _envelope(n, 0.01, 0.10, 0.15, 0.19, sr) * SFX_VOL, sr, ch)

def _build_no_mana(sr, ch):
    n  = int(sr * 0.14)
    sq = _square(180, n, 0.6, sr) * 0.50
    ns = _noise(n) * 0.20
    return _make_sound((sq + ns) * _envelope(n, 0.002, 0.04, 0.2, 0.10, sr) * SFX_VOL * 0.75, sr, ch)

def _build_heal(sr, ch):
    dur = 0.09
    n   = int(sr * dur)
    out = np.zeros(int(sr * dur * 3), dtype=np.float32)
    for i, f in enumerate([659, 784, 988]):
        t0  = int(i * sr * dur * 0.9)
        seg = _sine(f, n, sr) * _envelope(n, 0.003, 0.03, 0.3, 0.08, sr) * 0.45
        end = min(t0 + n, len(out))
        out[t0:end] += seg[:end - t0]
    return _make_sound(out * SFX_VOL, sr, ch)


# ════════════════════════════════════════════════════════════
#  SoundManager
# ════════════════════════════════════════════════════════════

class SoundManager:
    """
    Generates and plays all sounds via procedural synthesis.
    If no audio device is present → runs as a silent no-op without crashing.

    Usage:
        sfx = SoundManager()
        sfx.play("shoot")
    """

    _BUILDERS = {
        "shoot":        _build_shoot,
        "shoot_heavy":  _build_shoot_heavy,
        "shoot_laser":  _build_shoot_laser,
        "hit_enemy":    _build_hit_enemy,
        "hit_player":   _build_hit_player,
        "enemy_die":    _build_enemy_die,
        "boss_die":     _build_boss_die,
        "item_pickup":  _build_item_pickup,
        "level_up":     _build_level_up,
        "portal_open":  _build_portal_open,
        "player_die":   _build_player_die,
        "menu_click":   _build_menu_click,
        "shop_buy":     _build_shop_buy,
        "skill_dash":   _build_skill_dash,
        "skill_star":   _build_skill_star,
        "skill_frenzy": _build_skill_frenzy,
        "no_mana":      _build_no_mana,
        "heal":         _build_heal,
    }

    _CD_CONFIG = {
        "shoot":        0.06,
        "shoot_heavy":  0.12,
        "shoot_laser":  0.10,
        "hit_enemy":    0.04,
        "hit_player":   0.20,
        "enemy_die":    0.05,
        "boss_die":     0.0,
        "item_pickup":  0.0,
        "level_up":     0.0,
        "portal_open":  0.0,
        "player_die":   0.0,
        "menu_click":   0.10,
        "shop_buy":     0.0,
        "skill_dash":   0.0,
        "skill_star":   0.0,
        "skill_frenzy": 0.0,
        "no_mana":      0.60,
        "heal":         0.0,
    }

    def __init__(self):
        self._enabled   = False
        self._vol       = MASTER_VOL
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._cooldowns: dict[str, float] = {k: 0.0 for k in self._BUILDERS}

        # ── Check and initialize mixer ──────────────────────────
        init_info = pygame.mixer.get_init()
        if not init_info:
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                init_info = pygame.mixer.get_init()
            except Exception as e:
                print(f"[SoundManager] ⚠ init failed: {e} – no audio")
                return

        if not init_info:
            print("[SoundManager] ⚠ No audio device found – running silently")
            return

        sr, size, ch = init_info
        print(f"[SoundManager] ✅ mixer ready – {sr} Hz / {'stereo' if ch==2 else 'mono'}")

        # ── Build all sounds using actual sr/ch values ──────────
        for name, builder in self._BUILDERS.items():
            try:
                self._sounds[name] = builder(sr, ch)
            except Exception as e:
                print(f"[SoundManager] ⚠ '{name}': {e}")

        if self._sounds:
            self._enabled = True
            print(f"[SoundManager] Loaded {len(self._sounds)}/{len(self._BUILDERS)} sounds successfully")

    # ── Public API ────────────────────────────────────────────

    def play(self, name: str, volume: float = 1.0):
        if not self._enabled:
            return
        if self._cooldowns.get(name, 0.0) > 0:
            return
        snd = self._sounds.get(name)
        if snd is None:
            return
        try:
            snd.set_volume(volume * self._vol)
            snd.play()
            self._cooldowns[name] = self._CD_CONFIG.get(name, 0.0)
        except Exception:
            pass

    def update(self, dt: float):
        for k in self._cooldowns:
            if self._cooldowns[k] > 0:
                self._cooldowns[k] = max(0.0, self._cooldowns[k] - dt)

    def set_enabled(self, val: bool):
        self._enabled = val
        if not val:
            try:
                pygame.mixer.stop()
            except Exception:
                pass

    def toggle(self) -> bool:
        new_val = (not self._enabled) if self._sounds else False
        self.set_enabled(new_val)
        return self._enabled

    def set_volume(self, vol: float):
        self._vol = max(0.0, min(1.0, vol))

    @property
    def enabled(self) -> bool:
        return self._enabled

    # ── Convenience ──────────────────────────────────────────

    def play_shoot(self, weapon=None):
        if weapon is None:
            self.play("shoot"); return
        fx  = getattr(weapon, "effect", {}) or {}
        pat = fx.get("pattern", "single")
        if pat in ("laser", "laser_double"):
            self.play("shoot_laser")
        elif pat in ("spread5", "spread3"):
            self.play("shoot_heavy")
        else:
            self.play("shoot")

    def play_skill(self, stype: str):
        mapping = {"dash": "skill_dash", "star_spread": "skill_star", "rapid_fire": "skill_frenzy"}
        self.play(mapping.get(stype, "menu_click"))