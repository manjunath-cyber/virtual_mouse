"""
Virtual Mouse — Enhanced Edition  (low-latency build)
======================================================
Gesture controls:
  ☝  Index up alone          → Move cursor
  🤌  Index + Thumb pinch    → Left click
  ✌  Middle + Thumb pinch   → Right click
  ⚡  Index + Middle close   → Double click
  🤞  Index + Middle spread  → Scroll (move hand up / down)
  ✊  All fingers closed      → Grab / drag

Keyboard:
  q        Quit
  r        Reset smoother  (re-enables adaptive mode)
  + / =    More responsive  (raises alpha floor)
  -        Smoother         (lowers alpha floor)
  d        Toggle deadzone  (on/off)
  m        Toggle margin zone visualisation
  h        Toggle HUD
"""

import cv2
import sys
import time

from core.hand_tracker     import HandTracker
from core.mouse_controller import MouseController
from core.gesture_detector import GestureDetector
from utils.smoothing       import Smoothener, ClickCooldown
from utils.hud             import HUDRenderer


# ═══════════════════════════════════════════════════════════════════════════
#  CONFIG  — tune these without touching the rest of the code
# ═══════════════════════════════════════════════════════════════════════════
CAMERA_INDEX   = 0

FRAME_WIDTH    = 424
FRAME_HEIGHT   = 240

# Smoother — lower alpha = smoother but slower, higher = responsive but shaky
# DEADZONE is the most important anti-shake setting: raise it if still shaky
ALPHA_MIN      = 0.30   # was 0.75 — lower = much less jitter at rest
ALPHA_MAX      = 0.85   # was 1.0  — cap responsiveness so it never goes raw
DEADZONE       = 8      # was 1    — freeze cursor if finger moves < 8px (kills tremor)
VEL_SCALE      = 40     # was 15   — smoother ramp-up over more distance

MARGIN         = 60     # was 30   — larger dead border = calmer edge tracking

CLICK_COOLDOWN = 0.5    # was 0.45 — slightly longer to avoid accidental clicks
SCROLL_SPEED   = 3
SCROLL_DT      = 0.10
SCROLL_THRESH  = 12
# ═══════════════════════════════════════════════════════════════════════════

# Landmark connections for drawing the hand skeleton manually
HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),       # thumb
    (0,5),(5,6),(6,7),(7,8),       # index
    (5,9),(9,10),(10,11),(11,12),  # middle
    (9,13),(13,14),(14,15),(15,16),# ring
    (13,17),(17,18),(18,19),(19,20),# pinky
    (0,17),                         # palm base
]

GESTURE_COLORS = {
    "move":         (0,   220, 110),
    "left_click":   (0,   180, 255),
    "right_click":  (255, 140,   0),
    "double_click": (220,   0, 220),
    "scroll":       (255, 220,   0),
    "grab":         (255,  80,  80),
    "idle":         (140, 140, 140),
    "none":         (80,   80,  80),
}

GESTURE_LABELS = {
    "move":         "MOVE",
    "left_click":   "LEFT CLICK",
    "right_click":  "RIGHT CLICK",
    "double_click": "DOUBLE CLICK",
    "scroll":       "SCROLL",
    "grab":         "GRAB",
    "idle":         "IDLE",
    "none":         "---",
}


def draw_hand(frame, landmarks, gesture, gesture_info):
    """Draw full hand skeleton + highlighted fingertips. Clear and readable."""
    if not landmarks:
        return

    lm = {l[0]: l for l in landmarks}
    pts = {idx: (x, y) for idx, x, y in landmarks}

    gesture_color = GESTURE_COLORS.get(gesture, (180, 180, 180))

    # ── Skeleton lines ────────────────────────────────────────────────────
    for a, b in HAND_CONNECTIONS:
        if a in pts and b in pts:
            cv2.line(frame, pts[a], pts[b], (60, 180, 60), 2, cv2.LINE_AA)

    # ── All landmark dots ─────────────────────────────────────────────────
    for idx, (x, y) in pts.items():
        cv2.circle(frame, (x, y), 4, (200, 200, 200), -1, cv2.LINE_AA)

    # ── Fingertip highlights (bigger, colored) ────────────────────────────
    TIPS = [4, 8, 12, 16, 20]
    for tip_id in TIPS:
        if tip_id in pts:
            cv2.circle(frame, pts[tip_id], 10, gesture_color, 2, cv2.LINE_AA)
            cv2.circle(frame, pts[tip_id], 4,  gesture_color, -1, cv2.LINE_AA)

    # ── Index fingertip crosshair (cursor anchor point) ───────────────────
    if 8 in pts:
        ix, iy = pts[8]
        length = 18
        cv2.line(frame, (ix - length, iy), (ix - 6, iy), gesture_color, 2, cv2.LINE_AA)
        cv2.line(frame, (ix + 6,  iy), (ix + length, iy), gesture_color, 2, cv2.LINE_AA)
        cv2.line(frame, (ix, iy - length), (ix, iy - 6), gesture_color, 2, cv2.LINE_AA)
        cv2.line(frame, (ix, iy + 6),  (ix, iy + length), gesture_color, 2, cv2.LINE_AA)

    # ── Pinch line between index and thumb ────────────────────────────────
    if 4 in pts and 8 in pts:
        line_col = (0, 80, 255) if gesture == "left_click" else (60, 60, 60)
        cv2.line(frame, pts[4], pts[8], line_col, 2, cv2.LINE_AA)

    # ── Gesture label near wrist ──────────────────────────────────────────
    if 0 in pts:
        wx, wy = pts[0]
        label = GESTURE_LABELS.get(gesture, gesture.upper())
        # Dark background for readability
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (wx - 4, wy + 10), (wx + tw + 6, wy + th + 18),
                      (0, 0, 0), -1)
        cv2.putText(frame, label, (wx, wy + th + 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, gesture_color, 2, cv2.LINE_AA)


def draw_mini_hud(frame, gesture, fps, pinch_dist, fingers_up):
    """Compact always-visible HUD in top-left corner."""
    h, w = frame.shape[:2]
    gesture_color = GESTURE_COLORS.get(gesture, (180, 180, 180))

    # Semi-transparent background panel
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (200, 110), (10, 10, 20), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    cv2.rectangle(frame, (0, 0), (200, 110), gesture_color, 1)

    # FPS
    fps_color = (0, 220, 80) if fps >= 24 else (0, 180, 255) if fps >= 15 else (0, 60, 255)
    cv2.putText(frame, f"FPS: {fps}", (8, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, fps_color, 1, cv2.LINE_AA)

    # Gesture
    label = GESTURE_LABELS.get(gesture, gesture.upper())
    cv2.putText(frame, label, (8, 48),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, gesture_color, 2, cv2.LINE_AA)

    # Pinch bar
    bar_fill = int(min(pinch_dist / 120.0, 1.0) * 182)
    cv2.rectangle(frame, (8, 58), (190, 70), (40, 40, 40), -1)
    cv2.rectangle(frame, (8, 58), (8 + bar_fill, 70), gesture_color, -1)
    cv2.putText(frame, "PINCH", (8, 84),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 100, 100), 1, cv2.LINE_AA)

    # Finger indicators
    names = ["I", "M", "R", "P"]
    for i, (name, up) in enumerate(zip(names, fingers_up)):
        fc = (0, 220, 110) if up else (60, 60, 60)
        cv2.circle(frame, (20 + i * 42, 100), 7, fc, -1, cv2.LINE_AA)
        cv2.putText(frame, name, (14 + i * 42, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, (200, 200, 200), 1, cv2.LINE_AA)


def main():
    # ── Camera ────────────────────────────────────────────────────────────
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera {CAMERA_INDEX}.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS,          60)
    cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)

    # ── Components ────────────────────────────────────────────────────────
    tracker  = HandTracker(
        max_num_hands=1,
        min_detection_confidence=0.55,
        min_tracking_confidence=0.55,
    )
    mouse    = MouseController(margin=MARGIN)
    detector = GestureDetector()
    smoother = Smoothener(alpha_min=ALPHA_MIN, alpha_max=ALPHA_MAX,
                          vel_scale=VEL_SCALE, deadzone=DEADZONE)
    cooldown = ClickCooldown(cooldown_sec=CLICK_COOLDOWN)

    # ── State ─────────────────────────────────────────────────────────────
    scroll_ref_y  = None
    last_scroll_t = 0.0
    show_margin   = False
    show_hud      = True
    locked_pos    = None   # (sx, sy) frozen during click gestures

    # FPS tracking
    fps_times = []
    fps_val   = 0

    print("[INFO] Virtual Mouse running. Press 'q' to quit, 'h' to toggle HUD.")
    print(f"[INFO] DEADZONE={DEADZONE}px  ALPHA={ALPHA_MIN}~{ALPHA_MAX}  "
          f"VEL_SCALE={VEL_SCALE}")
    print("[INFO] If still shaky: press '-' key to increase smoothing.")

    while True:
        # ── Grab latest frame ──────────────────────────────────────────────
        cap.grab()
        success, frame = cap.read()
        if not success:
            continue

        # FPS calc
        now = time.time()
        fps_times.append(now)
        fps_times = [t for t in fps_times if now - t < 1.0]
        fps_val = len(fps_times)

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # ── Detect (draw=False — we draw manually below, much cleaner) ────
        frame     = tracker.find_hands(frame, draw=False)
        landmarks = tracker.get_landmarks(frame)

        if not landmarks:
            cv2.putText(frame, "Show your hand to the camera", (10, h // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 60, 255), 2, cv2.LINE_AA)
            cv2.imshow("Virtual Mouse", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue

        n_hands      = tracker.num_hands()
        gesture_info = detector.detect(landmarks)
        gesture      = gesture_info.get("gesture", "none")

        # ── Draw full hand skeleton + labels ──────────────────────────────
        draw_hand(frame, landmarks, gesture, gesture_info)

        # ── Mini HUD ──────────────────────────────────────────────────────
        if show_hud:
            draw_mini_hud(
                frame, gesture, fps_val,
                gesture_info.get("pinch_dist", 100),
                gesture_info.get("fingers_up", [False]*4)
            )

        # ── Act ───────────────────────────────────────────────────────────
        CLICK_GESTURES = ("left_click", "right_click", "double_click")

        if gesture in ("move", "left_click", "right_click",
                       "double_click", "scroll", "grab"):

            ix, iy = gesture_info["index_pos"]
            t = time.time()

            if gesture in CLICK_GESTURES:
                # ── CURSOR LOCK: freeze position on click entry ────────────
                # When a click gesture starts, snap the smoother to the
                # last known stable position and stop updating it.
                # This prevents the fingertip's pinch motion from dragging
                # the cursor while the click fires.
                if locked_pos is None:
                    # First frame of this click — capture current position
                    locked_pos = (
                        int(smoother.prev_x) if smoother.prev_x else ix,
                        int(smoother.prev_y) if smoother.prev_y else iy,
                    )
                sx, sy = locked_pos
                mouse.move_mouse(sx, sy, w, h)

                if gesture == "left_click" and cooldown.ready():
                    mouse.left_click()
                    cooldown.register()
                elif gesture == "right_click" and cooldown.ready():
                    mouse.right_click()
                    cooldown.register()
                elif gesture == "double_click" and cooldown.ready():
                    mouse.double_click()
                    cooldown.register()

            else:
                # ── Normal movement — release lock ─────────────────────────
                locked_pos = None
                sx, sy = smoother.smooth(ix, iy)
                mouse.move_mouse(sx, sy, w, h)

                if gesture == "scroll":
                    if scroll_ref_y is None:
                        scroll_ref_y = iy
                    elif t - last_scroll_t >= SCROLL_DT:
                        delta = scroll_ref_y - iy
                        if abs(delta) >= SCROLL_THRESH:
                            mouse.scroll("up" if delta > 0 else "down", SCROLL_SPEED)
                            scroll_ref_y  = iy
                            last_scroll_t = t
                else:
                    scroll_ref_y = None

        elif gesture == "idle":
            locked_pos = None
            smoother.reset()
            scroll_ref_y = None
        else:
            locked_pos = None
            scroll_ref_y = None

        # ── Margin rectangle ──────────────────────────────────────────────
        if show_margin:
            m = MARGIN
            cv2.rectangle(frame, (m, m), (w - m, h - m), (80, 80, 80), 1)
            cv2.putText(frame, "ACTIVE ZONE", (m + 4, m + 14),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (80, 80, 80), 1)

        cv2.imshow("Virtual Mouse", frame)

        # ── Keys ──────────────────────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            smoother.reset()
            print("[INFO] Smoother reset.")
        elif key in (ord('+'), ord('=')):
            smoother.alpha = min(smoother.alpha + 0.05, 0.95)
            print(f"[INFO] Alpha → {smoother.alpha:.2f}")
        elif key == ord('-'):
            smoother.alpha = max(smoother.alpha - 0.05, 0.05)
            print(f"[INFO] Alpha → {smoother.alpha:.2f}")
        elif key == ord('d'):
            smoother.deadzone = 0 if smoother.deadzone > 0 else DEADZONE
            print(f"[INFO] Deadzone {'ON (' + str(DEADZONE) + 'px)' if smoother.deadzone else 'OFF'}")
        elif key == ord('m'):
            show_margin = not show_margin
        elif key == ord('h'):
            show_hud = not show_hud

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Stopped.")


if __name__ == "__main__":
    main()