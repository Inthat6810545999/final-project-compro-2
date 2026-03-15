"""
stats_tracker.py  –  StatsTracker class (OOP Class 5)
Collects gameplay data, saves to CSV, and renders Matplotlib charts.
"""
import os
import csv
import time
import random
import datetime


CSV_DIR    = "stats"
MAIN_CSV   = os.path.join(CSV_DIR, "gameplay_data.csv")
COMBAT_CSV = os.path.join(CSV_DIR, "combat_log.csv")

MAIN_FIELDS = [
    "session_id", "timestamp", "char_class", "outcome",
    "score", "enemies_defeated", "total_damage", "duration_sec",
    "items_collected", "level_reached", "gold_earned",
    "stage_reached", "boss_kills",
]

COMBAT_FIELDS = [
    "session_id", "tick", "damage", "is_crit", "enemy_type",
]


class StatsTracker:
    """
    Handles all gameplay data collection, CSV persistence,
    and Matplotlib visualization.
    """

    def __init__(self):
        os.makedirs(CSV_DIR, exist_ok=True)
        self._ensure_csv(MAIN_CSV, MAIN_FIELDS)
        self._ensure_csv(COMBAT_CSV, COMBAT_FIELDS)

        self.session_id   = None
        self.current_run  = {}
        self.total_runs   = self._count_existing_runs()
        self._combat_buf  = []   # buffer before flush
        self._tick        = 0

    # ── CSV helpers ───────────────────────────────────────────
    @staticmethod
    def _ensure_csv(path, fields):
        if not os.path.exists(path):
            with open(path, "w", newline="") as f:
                csv.DictWriter(f, fieldnames=fields).writeheader()

    def _count_existing_runs(self):
        try:
            with open(MAIN_CSV, "r") as f:
                return max(0, sum(1 for _ in f) - 1)
        except FileNotFoundError:
            return 0

    # ── Run lifecycle ─────────────────────────────────────────
    def start_run(self, player):
        self.session_id  = f"{int(time.time())}_{random.randint(1000,9999)}"
        self.current_run = {
            "session_id":      self.session_id,
            "timestamp":       datetime.datetime.now().isoformat(timespec="seconds"),
            "char_class":      player.char_class,
            "outcome":         "death",
            "score":           0,
            "enemies_defeated":0,
            "total_damage":    0,
            "duration_sec":    0,
            "items_collected": 0,
            "level_reached":   1,
            "gold_earned":     0,
            "stage_reached":   1,
            "boss_kills":      0,
        }
        self._start_time = time.time()
        self._combat_buf = []
        self._tick       = 0

    def log_event(self, event_type, data: dict):
        """Called during gameplay on key events."""
        if event_type == "kill":
            self.current_run["enemies_defeated"] += 1
            if data.get("is_boss"):
                self.current_run["boss_kills"] += 1
            self.current_run["score"] += data.get("exp", 0) * 10

        elif event_type == "damage":
            self.current_run["total_damage"] += data.get("amount", 0)
            self._tick += 1
            self._combat_buf.append({
                "session_id": self.session_id,
                "tick":       self._tick,
                "damage":     data.get("amount", 0),
                "is_crit":    int(data.get("is_crit", False)),
                "enemy_type": data.get("enemy_type", "unknown"),
            })
            if len(self._combat_buf) >= 50:
                self._flush_combat()

        elif event_type == "item_pickup":
            self.current_run["items_collected"] += 1
            rarity = data.get("rarity", "Common")
            rarity_bonus = {"Common": 10, "Rare": 50, "Epic": 150, "Legendary": 500}
            self.current_run["score"] += rarity_bonus.get(rarity, 10)

        elif event_type == "level_up":
            self.current_run["level_reached"] = data.get("level", 1)

        elif event_type == "gold":
            self.current_run["gold_earned"] += data.get("amount", 0)

        elif event_type == "stage_clear":
            stage = data.get("stage", 1)
            if stage > self.current_run["stage_reached"]:
                self.current_run["stage_reached"] = stage
            self.current_run["score"] += stage * 500

    def end_run(self, outcome, player):
        """Called when run ends (death or victory)."""
        self.current_run["outcome"]      = outcome
        self.current_run["duration_sec"] = int(time.time() - self._start_time)
        self.current_run["level_reached"]= player.level
        self.current_run["gold_earned"]  = player.gold
        # Score bonus for victory
        if outcome == "victory":
            self.current_run["score"] *= 2
        self.save_to_csv()
        self._flush_combat()
        self.total_runs += 1

    def save_to_csv(self):
        with open(MAIN_CSV, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=MAIN_FIELDS)
            w.writerow(self.current_run)

    def _flush_combat(self):
        if not self._combat_buf:
            return
        with open(COMBAT_CSV, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COMBAT_FIELDS)
            w.writerows(self._combat_buf)
        self._combat_buf = []

    # ── Summary ───────────────────────────────────────────────
    def get_summary(self):
        """Return dict of aggregate stats from all runs."""
        rows = self._load_rows()
        if not rows:
            return {"total_runs": 0}
        scores  = [int(r["score"])            for r in rows]
        kills   = [int(r["enemies_defeated"]) for r in rows]
        dmg     = [int(r["total_damage"])     for r in rows]
        dur     = [int(r["duration_sec"])     for r in rows]
        levels  = [int(r["level_reached"])    for r in rows]
        wins    = sum(1 for r in rows if r["outcome"] == "victory")
        return {
            "total_runs":    len(rows),
            "victories":     wins,
            "avg_score":     sum(scores) // max(1, len(scores)),
            "best_score":    max(scores) if scores else 0,
            "avg_kills":     sum(kills)  // max(1, len(kills)),
            "avg_damage":    sum(dmg)    // max(1, len(dmg)),
            "avg_duration":  sum(dur)    // max(1, len(dur)),
            "max_level":     max(levels) if levels else 1,
        }

    def _load_rows(self):
        try:
            with open(MAIN_CSV, "r") as f:
                return list(csv.DictReader(f))
        except FileNotFoundError:
            return []

    # ── Visualization ─────────────────────────────────────────
    def plot_dashboard(self):
        """
        Render a 6-panel Matplotlib dashboard.
        Opens a window; call from main menu.
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.gridspec as gridspec
        except ImportError:
            print("matplotlib not installed. Run: pip install matplotlib")
            return

        rows = self._load_rows()
        if not rows:
            print("No gameplay data yet. Play some runs first!")
            return

        scores   = [int(r["score"])            for r in rows]
        kills    = [int(r["enemies_defeated"])  for r in rows]
        dmg      = [int(r["total_damage"])      for r in rows]
        dur      = [int(r["duration_sec"])      for r in rows]
        items    = [int(r["items_collected"])   for r in rows]
        levels   = [int(r["level_reached"])     for r in rows]
        classes  = [r["char_class"]             for r in rows]
        outcomes = [r["outcome"]                for r in rows]
        stages   = [int(r["stage_reached"])     for r in rows]

        fig = plt.figure(figsize=(16, 10))
        fig.suptitle("Sausage Man: Legends of Midgard — Statistics Dashboard",
                     fontsize=16, fontweight="bold", color="#1F3864")
        gs  = gridspec.GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.35)

        # 1) Score per run (line)
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.plot(scores, color="#1F6EBD", linewidth=1.5)
        ax1.fill_between(range(len(scores)), scores, alpha=0.2, color="#1F6EBD")
        ax1.set_title("Score per Run")
        ax1.set_xlabel("Run #")
        ax1.set_ylabel("Score")

        # 2) Enemies defeated histogram
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.hist(kills, bins=10, color="#C0392B", edgecolor="white")
        ax2.set_title("Enemies Defeated (Distribution)")
        ax2.set_xlabel("Kills per Run")
        ax2.set_ylabel("Count")

        # 3) Avg score by class (bar)
        ax3 = fig.add_subplot(gs[0, 2])
        class_names = ["Warrior", "Mage", "Ranger"]
        class_avgs  = []
        colors_bar  = ["#C0392B", "#8E44AD", "#27AE60"]
        for cn in class_names:
            cs = [s for s, c in zip(scores, classes) if c == cn]
            class_avgs.append(sum(cs) // max(1, len(cs)) if cs else 0)
        bars = ax3.bar(class_names, class_avgs, color=colors_bar, edgecolor="white")
        ax3.bar_label(bars, fmt="%d")
        ax3.set_title("Avg Score by Class")
        ax3.set_ylabel("Score")

        # 4) Run duration histogram
        ax4 = fig.add_subplot(gs[1, 0])
        ax4.hist(dur, bins=10, color="#D68910", edgecolor="white")
        ax4.set_title("Run Duration (seconds)")
        ax4.set_xlabel("Duration (s)")
        ax4.set_ylabel("Count")

        # 5) Stage completion rate (bar)
        ax5 = fig.add_subplot(gs[1, 1])
        stage_counts = [stages.count(i) for i in range(1, 6)]
        ax5.bar([f"Stage {i}" for i in range(1, 6)], stage_counts,
                color=["#27AE60","#1F6EBD","#C0392B","#8E44AD","#D4AC0D"],
                edgecolor="white")
        ax5.set_title("Furthest Stage Reached")
        ax5.set_ylabel("Runs")

        # 6) Damage vs kills scatter
        ax6 = fig.add_subplot(gs[1, 2])
        win_mask  = [o == "victory" for o in outcomes]
        lose_mask = [o != "victory" for o in outcomes]
        ax6.scatter([k for k, m in zip(kills, lose_mask) if m],
                    [d for d, m in zip(dmg,   lose_mask) if m],
                    alpha=0.5, color="#C0392B", label="Death", s=30)
        ax6.scatter([k for k, m in zip(kills, win_mask) if m],
                    [d for d, m in zip(dmg,   win_mask) if m],
                    alpha=0.8, color="#27AE60", label="Victory", s=50, marker="*")
        ax6.set_title("Kills vs Damage Dealt")
        ax6.set_xlabel("Enemies Killed")
        ax6.set_ylabel("Total Damage")
        ax6.legend()

        plt.show()
