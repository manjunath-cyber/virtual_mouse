"""
Virtual Mouse — Enhanced Edition  (low-latency build)
======================================================
Gesture controls:
  ☝  Index up alone          → Move cursor
  🤌  Index + Thumb pinch    → Left click
  ✌  Middle + Thumb pinch   → Right click (index folded down)
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
  Space    Pause / Resume tracking
"""

import cv2
import sys
import time
import threading

from core.hand_tracker     import HandTracker
from core.mouse_controller import MouseController
from core.gesture_detector import GestureDetector
from utils.smoothing       import Smoothener, ClickCooldown
from utils.hud             import HUDRenderer

# Tray icon (optional — gracefully skipped if pystray/pillow not installed)
try:
    from utils.tray import TrayIcon
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("[INFO] pystray/pillow not installed — tray icon disabled.")
    print("[INFO] Install with: pip install pystray pillow")


# ═══════════════════════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════════════════════
CAMERA_INDEX   = 0

FRAME_WIDTH    = 424
FRAME_HEIGHT   = 240

ALPHA_MIN      = 0.30
ALPHA_MAX      = 0.85
DEADZONE       = 8
VEL_SCALE      = 40

MARGIN         = 60

CLICK_COOLDOWN = 0.5
SCROLL_SPEED   = 3
SCROLL_DT      = 0.10
SCROLL_THRESH  = 12
# ═══════════════════════════════════════════════════════════════════════════

HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),
    (9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),
    (0,17),
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
    if not landmarks:
        return
    pts = {idx: (x, y) for idx, x, y in landmarks}
    gesture_color = GESTURE_COLORS.get(gesture, (180, 180, 180))

    for a, b in HAND_CONNECTIONS:
        if a in pts and b in pts:
            cv2.line(frame, pts[a], pts[b], (60, 180, 60), 2, cv2.LINE_AA)

    for idx, (x, y) in pts.items():
        cv2.circle(frame, (x, y), 4, (200, 200, 200), -1, cv2.LINE_AA)

    for tip_id in [4, 8, 12, 16, 20]:
        if tip_id in pts:
            cv2.circle(frame, pts[tip_id], 10, gesture_color, 2, cv2.LINE_AA)
            cv2.circle(frame, pts[tip_id], 4,  gesture_color, -1, cv2.LINE_AA)

    if 8 in pts:
        ix, iy = pts[8]
        length = 18
        cv2.line(frame, (ix - length, iy), (ix - 6, iy), gesture_color, 2, cv2.LINE_AA)
        cv2.line(frame, (ix + 6,  iy), (ix + length, iy), gesture_color, 2, cv2.LINE_AA)
        cv2.line(frame, (ix, iy - length), (ix, iy - 6), gesture_color, 2, cv2.LINE_AA)
        cv2.line(frame, (ix, iy + 6),  (ix, iy + length), gesture_color, 2, cv2.LINE_AA)

    if 4 in pts and 8 in pts:
        line_col = (0, 80, 255) if gesture == "left_click" else (60, 60, 60)
        cv2.line(frame, pts[4], pts[8], line_col, 2, cv2.LINE_AA)

    if 0 in pts:
        wx, wy = pts[0]
        label = GESTURE_LABELS.get(gesture, gesture.upper())
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (wx - 4, wy + 10), (wx + tw + 6, wy + th + 18), (0, 0, 0), -1)
        cv2.putText(frame, label, (wx, wy + th + 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, gesture_color, 2, cv2.LINE_AA)


def draw_mini_hud(frame, gesture, fps, pinch_dist, fingers_up, paused=False):
    gesture_color = GESTURE_COLORS.get(gesture, (180, 180, 180))
    if paused:
        gesture_color = (80, 80, 80)

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (200, 110), (10, 10, 20), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    cv2.rectangle(frame, (0, 0), (200, 110), gesture_color, 1)

    fps_color = (0, 220, 80) if fps >= 24 else (0, 180, 255) if fps >= 15 else (0, 60, 255)
    cv2.putText(frame, f"FPS: {fps}", (8, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, fps_color, 1, cv2.LINE_AA)

    label = "PAUSED" if paused else GESTURE_LABELS.get(gesture, gesture.upper())
    cv2.putText(frame, label, (8, 48),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, gesture_color, 2, cv2.LINE_AA)

    bar_fill = int(min(pinch_dist / 120.0, 1.0) * 182)
    cv2.rectangle(frame, (8, 58), (190, 70), (40, 40, 40), -1)
    cv2.rectangle(frame, (8, 58), (8 + bar_fill, 70), gesture_color, -1)
    cv2.putText(frame, "PINCH", (8, 84),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 100, 100), 1, cv2.LINE_AA)

    names = ["I", "M", "R", "P"]
    for i, (name, up) in enumerate(zip(names, fingers_up)):
        fc = (0, 220, 110) if up and not paused else (60, 60, 60)
        cv2.circle(frame, (20 + i * 42, 100), 7, fc, -1, cv2.LINE_AA)
        cv2.putText(frame, name, (14 + i * 42, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, (200, 200, 200), 1, cv2.LINE_AA)


def main():
    # ── Shared state for tray ──────────────────────────────────────────────
    running = threading.Event()
    running.set()
    paused  = threading.Event()   # set = paused, clear = active

    def on_stop():
        running.clear()

    def on_pause_toggle(active: bool):
        if active:
            paused.clear()
            print("[INFO] Tracking resumed.")
        else:
            paused.set()
            print("[INFO] Tracking paused.")

    # ── Tray icon ──────────────────────────────────────────────────────────
    tray = None
    if TRAY_AVAILABLE:
        tray = TrayIcon(stop_callback=on_stop, pause_callback=on_pause_toggle)
        print("[INFO] System tray icon active — right-click it to pause or exit.")

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
    locked_pos    = None

    fps_times = []
    fps_val   = 0

    print("[INFO] Virtual Mouse running. Press 'q' to quit, Space to pause.")

    while running.is_set():
        cap.grab()
        success, frame = cap.read()
        if not success:
            continue

        now = time.time()
        fps_times.append(now)
        fps_times = [t for t in fps_times if now - t < 1.0]
        fps_val = len(fps_times)

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # ── PAUSED state ──────────────────────────────────────────────────
        if paused.is_set():
            if show_hud:
                draw_mini_hud(frame, "none", fps_val, 100,
                              [False]*4, paused=True)
            # Big centered PAUSED label
            cv2.putText(frame, "PAUSED — Space to resume", (w//2 - 160, h//2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (80, 80, 80), 2, cv2.LINE_AA)
            cv2.imshow("Virtual Mouse", frame)
            key = cv2.waitKey(30) & 0xFF
            if key == ord('q'):
                running.clear()
            elif key == ord(' '):
                paused.clear()
                if tray:
                    tray.set_active(True)
                print("[INFO] Tracking resumed.")
            continue

        # ── Detect ────────────────────────────────────────────────────────
        frame     = tracker.find_hands(frame, draw=False)
        landmarks = tracker.get_landmarks(frame)

        if not landmarks:
            cv2.putText(frame, "Show your hand to the camera", (10, h // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 60, 255), 2, cv2.LINE_AA)
            if show_hud:
                draw_mini_hud(frame, "none", fps_val, 100, [False]*4)
            cv2.imshow("Virtual Mouse", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                running.clear()
            continue

        n_hands      = tracker.num_hands()
        gesture_info = detector.detect(landmarks)
        gesture      = gesture_info.get("gesture", "none")

        draw_hand(frame, landmarks, gesture, gesture_info)

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
                if locked_pos is None:
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
            running.clear()
        elif key == ord(' '):
            paused.set()
            smoother.reset()
            locked_pos = None
            if tray:
                tray.set_active(False)
            print("[INFO] Tracking paused.")
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
            print(f"[INFO] Deadzone {'ON' if smoother.deadzone else 'OFF'}")
        elif key == ord('m'):
            show_margin = not show_margin
        elif key == ord('h'):
            show_hud = not show_hud

    # ── Cleanup ───────────────────────────────────────────────────────────
    cap.release()
    cv2.destroyAllWindows()
    if tray:
        tray.stop()
    print("[INFO] Virtual Mouse stopped.")


if __name__ == "__main__":
    main()