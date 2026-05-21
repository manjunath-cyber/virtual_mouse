<<<<<<< HEAD
import math


class Smoothener:
    """
    Adaptive velocity-aware smoother.

    How it works:
    - Computes the distance the finger moved since last frame.
    - Fast movement  → high alpha (responsive, follows finger instantly).
    - Slow movement  → low alpha  (stable, suppresses tremor).
    - Deadzone       → if delta < deadzone_px, output does not move at all.
      This kills the micro-jitter that makes the cursor look shaky when
      you try to hold still.

    Tuning guide:
      alpha_min  : smoothness floor  (0.1 = very stable, 0.3 = moderate)
      alpha_max  : responsiveness cap (0.6–0.95, higher = snappier)
      vel_scale  : distance (px) at which alpha reaches alpha_max (~40–80)
      deadzone   : radius in cam-pixels below which cursor freezes (3–8)
    """

    def __init__(
        self,
        alpha_min: float = 0.25,
        alpha_max: float = 0.85,
        vel_scale: float = 60.0,
        deadzone: float = 5.0,
    ):
        self.alpha_min = alpha_min
        self.alpha_max = alpha_max
        self.vel_scale = vel_scale
        self.deadzone  = deadzone

        # expose a single "alpha" property so the HUD / key controls
        # can read/write it as before (maps to alpha_min)
        self._alpha_override = None  # None = use adaptive; float = fixed

        self.prev_x: float | None = None
        self.prev_y: float | None = None

    # ── public alias so main.py can do smoother.alpha = X ─────────────────
    @property
    def alpha(self):
        return self._alpha_override if self._alpha_override is not None else self.alpha_min

    @alpha.setter
    def alpha(self, v):
        """
        When the user presses +/- in main.py we receive a value in [0.05, 0.9].
        We treat this as a FIXED alpha override (disables adaptive mode).
        Press 'r' (reset) to re-enable adaptive mode.
        """
        self._alpha_override = float(v)

    # ── core ───────────────────────────────────────────────────────────────
    def smooth(self, x: float, y: float) -> tuple[int, int]:
        if self.prev_x is None:
            self.prev_x, self.prev_y = float(x), float(y)
            return int(x), int(y)

        dx = x - self.prev_x
        dy = y - self.prev_y
        dist = math.hypot(dx, dy)

        # ── Deadzone: freeze output when hand is almost still ──────────────
        if dist < self.deadzone:
            return int(self.prev_x), int(self.prev_y)

        # ── Pick alpha ─────────────────────────────────────────────────────
        if self._alpha_override is not None:
            a = self._alpha_override
        else:
            # Sigmoid-like ramp: low velocity → alpha_min, high → alpha_max
            t = min(dist / self.vel_scale, 1.0)          # 0.0 … 1.0
            a = self.alpha_min + (self.alpha_max - self.alpha_min) * t

        curr_x = self.prev_x + dx * a
        curr_y = self.prev_y + dy * a

        self.prev_x, self.prev_y = curr_x, curr_y
        return int(curr_x), int(curr_y)

    def reset(self):
        self.prev_x = None
        self.prev_y = None
        self._alpha_override = None   # re-enable adaptive mode


class ClickCooldown:
    """Prevents accidental rapid-fire clicks."""

    import time as _time

    def __init__(self, cooldown_sec=0.5):
        self.cooldown = cooldown_sec
        self._last = 0

    def ready(self):
        import time
        return time.time() - self._last >= self.cooldown

    def register(self):
        import time
        self._last = time.time()
=======
class Smoothener:

    def __init__(self, alpha=0.2):

        self.alpha = alpha
        self.prev_x = 0
        self.prev_y = 0

    def smooth(self, x, y):

        curr_x = self.prev_x + (x - self.prev_x) * self.alpha
        curr_y = self.prev_y + (y - self.prev_y) * self.alpha

        self.prev_x = curr_x
        self.prev_y = curr_y

        return int(curr_x), int(curr_y)
>>>>>>> ddeb125b298a36543638c2209f87b34e9388c6bb
