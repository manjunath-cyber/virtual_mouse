import cv2
import numpy as np
import time


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

GESTURE_ICONS = {
    "move":         "☝  MOVE",
    "left_click":   "👆 L-CLICK",
    "right_click":  "✌  R-CLICK",
    "double_click": "⚡ DBL-CLICK",
    "scroll":       "↕  SCROLL",
    "grab":         "✊ GRAB",
    "idle":         "✋ IDLE",
    "none":         "   —",
}


class HUDRenderer:
    def __init__(self):
        self.fps_buffer = []
        self.prev_time = time.time()
        self.gesture_history = []  # recent gesture names
        self.MAX_HISTORY = 5

    def _fps(self):
        now = time.time()
        dt = now - self.prev_time
        self.prev_time = now
        fps = 1.0 / dt if dt > 0 else 0
        self.fps_buffer.append(fps)
        if len(self.fps_buffer) > 10:
            self.fps_buffer.pop(0)
        return int(sum(self.fps_buffer) / len(self.fps_buffer))

    @staticmethod
    def _alpha_rect(frame, x1, y1, x2, y2, color, alpha=0.45):
        """Draw a semi-transparent filled rectangle."""
        overlay = frame.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    @staticmethod
    def _rounded_rect(frame, x1, y1, x2, y2, color, radius=12, thickness=2):
        cv2.rectangle(frame, (x1 + radius, y1), (x2 - radius, y2), color, thickness)
        cv2.rectangle(frame, (x1, y1 + radius), (x2, y2 - radius), color, thickness)
        cv2.ellipse(frame, (x1 + radius, y1 + radius), (radius, radius), 180, 0, 90, color, thickness)
        cv2.ellipse(frame, (x2 - radius, y1 + radius), (radius, radius), 270, 0, 90, color, thickness)
        cv2.ellipse(frame, (x1 + radius, y2 - radius), (radius, radius), 90,  0, 90, color, thickness)
        cv2.ellipse(frame, (x2 - radius, y2 - radius), (radius, radius), 0,   0, 90, color, thickness)

    def render(self, frame, gesture_info, num_hands, smoothed_pos=None):
        h, w, _ = frame.shape
        fps = self._fps()
        gesture = gesture_info.get("gesture", "none")
        color = GESTURE_COLORS.get(gesture, (180, 180, 180))

        # ── Top status bar ────────────────────────────────────────────────
        self._alpha_rect(frame, 0, 0, w, 56, (10, 10, 20), alpha=0.65)
        cv2.line(frame, (0, 56), (w, 56), color, 1)

        # Title
        cv2.putText(frame, "VIRTUAL MOUSE", (16, 36),
                    cv2.FONT_HERSHEY_DUPLEX, 0.75, (220, 220, 220), 1, cv2.LINE_AA)

        # FPS badge
        fps_text = f"FPS {fps:02d}"
        fps_color = (0, 220, 80) if fps >= 24 else (0, 180, 255) if fps >= 15 else (0, 60, 255)
        cv2.putText(frame, fps_text, (w - 120, 36),
                    cv2.FONT_HERSHEY_DUPLEX, 0.65, fps_color, 1, cv2.LINE_AA)

        # Hand count
        hand_text = f"HANDS: {num_hands}"
        cv2.putText(frame, hand_text, (w - 240, 36),
                    cv2.FONT_HERSHEY_DUPLEX, 0.55, (160, 160, 160), 1, cv2.LINE_AA)

        # ── Gesture panel (bottom-left) ───────────────────────────────────
        panel_x, panel_y = 12, h - 100
        self._alpha_rect(frame, panel_x, panel_y, panel_x + 220, h - 12, (10, 10, 20), alpha=0.7)
        self._rounded_rect(frame, panel_x, panel_y, panel_x + 220, h - 12, color, radius=8)

        label = GESTURE_ICONS.get(gesture, gesture.upper())
        cv2.putText(frame, "GESTURE", (panel_x + 10, panel_y + 24),
                    cv2.FONT_HERSHEY_DUPLEX, 0.45, (120, 120, 120), 1, cv2.LINE_AA)
        cv2.putText(frame, label, (panel_x + 10, panel_y + 56),
                    cv2.FONT_HERSHEY_DUPLEX, 0.75, color, 1, cv2.LINE_AA)

        # Pinch distance bar
        pinch = gesture_info.get("pinch_dist", 100)
        bar_w = int(min(pinch / 120.0, 1.0) * 198)
        cv2.rectangle(frame, (panel_x + 10, panel_y + 66), (panel_x + 208, panel_y + 74), (40, 40, 40), -1)
        cv2.rectangle(frame, (panel_x + 10, panel_y + 66), (panel_x + 10 + bar_w, panel_y + 74), color, -1)
        cv2.putText(frame, "PINCH", (panel_x + 10, panel_y + 86),
                    cv2.FONT_HERSHEY_DUPLEX, 0.35, (100, 100, 100), 1, cv2.LINE_AA)

        # ── Cursor crosshair on fingertip ─────────────────────────────────
        if "index_pos" in gesture_info:
            ix, iy = gesture_info["index_pos"]
            cv2.circle(frame, (ix, iy), 14, color, 2, cv2.LINE_AA)
            cv2.circle(frame, (ix, iy), 3,  color, -1, cv2.LINE_AA)
            cv2.line(frame, (ix - 20, iy), (ix - 6, iy), color, 1)
            cv2.line(frame, (ix + 6,  iy), (ix + 20, iy), color, 1)
            cv2.line(frame, (ix, iy - 20), (ix, iy - 6), color, 1)
            cv2.line(frame, (ix, iy + 6),  (ix, iy + 20), color, 1)

        # ── Thumb tip dot ─────────────────────────────────────────────────
        if "thumb_pos" in gesture_info:
            tx, ty = gesture_info["thumb_pos"]
            cv2.circle(frame, (tx, ty), 7, (255, 200, 0), 2, cv2.LINE_AA)

        # ── Pinch line ────────────────────────────────────────────────────
        if "index_pos" in gesture_info and "thumb_pos" in gesture_info:
            ix, iy = gesture_info["index_pos"]
            tx, ty = gesture_info["thumb_pos"]
            line_color = (0, 80, 255) if gesture == "left_click" else (80, 80, 80)
            cv2.line(frame, (ix, iy), (tx, ty), line_color, 1, cv2.LINE_AA)

        # ── Finger indicators (top-right) ─────────────────────────────────
        fingers_up = gesture_info.get("fingers_up", [False, False, False, False])
        names = ["IDX", "MID", "RNG", "PNK"]
        bx, by = w - 80, 70
        for i, (name, up) in enumerate(zip(names, fingers_up)):
            fc = (0, 220, 110) if up else (60, 60, 60)
            cv2.circle(frame, (bx + 30, by + i * 26), 8, fc, -1, cv2.LINE_AA)
            cv2.putText(frame, name, (bx, by + i * 26 + 5),
                        cv2.FONT_HERSHEY_DUPLEX, 0.38, fc, 1, cv2.LINE_AA)

        return frame