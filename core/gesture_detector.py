import math

<<<<<<< HEAD

class GestureDetector:
    # Landmark IDs
    THUMB_TIP  = 4
    INDEX_TIP  = 8
    MIDDLE_TIP = 12
    RING_TIP   = 16
    PINKY_TIP  = 20

    THUMB_MCP  = 2
    INDEX_MCP  = 5
    MIDDLE_MCP = 9
    RING_MCP   = 13
    PINKY_MCP  = 17

    INDEX_PIP  = 6
    MIDDLE_PIP = 10
    RING_PIP   = 14
    PINKY_PIP  = 18

    WRIST = 0

    @staticmethod
    def distance(lm_a, lm_b):
        return math.hypot(lm_b[1] - lm_a[1], lm_b[2] - lm_a[2])

    @staticmethod
    def finger_up(landmarks, tip_id, pip_id):
        """True if finger is extended (tip above pip in y)."""
        tip = landmarks[tip_id]
        pip = landmarks[pip_id]
        return tip[2] < pip[2]

    def detect(self, landmarks):
        if not landmarks or len(landmarks) < 21:
            return {"gesture": "none"}

        lm = {l[0]: l for l in landmarks}

        index_up  = self.finger_up(lm, self.INDEX_TIP,  self.INDEX_PIP)
        middle_up = self.finger_up(lm, self.MIDDLE_TIP, self.MIDDLE_PIP)
        ring_up   = self.finger_up(lm, self.RING_TIP,   self.RING_PIP)
        pinky_up  = self.finger_up(lm, self.PINKY_TIP,  self.PINKY_PIP)

        ix, iy = lm[self.INDEX_TIP][1],  lm[self.INDEX_TIP][2]
        tx, ty = lm[self.THUMB_TIP][1],  lm[self.THUMB_TIP][2]
        mx, my = lm[self.MIDDLE_TIP][1], lm[self.MIDDLE_TIP][2]

        pinch_dist   = math.hypot(ix - tx, iy - ty)   # index ↔ thumb
        m_pinch_dist = math.hypot(mx - tx, my - ty)   # middle ↔ thumb

        gesture = "move"

        # ── Right Click ───────────────────────────────────────────────────
        # MUST come before left_click check.
        # Gesture: middle finger + thumb pinch, index finger DOWN (folded).
        # Checking index_up==False disambiguates from left-click where
        # index is also near thumb.
        if m_pinch_dist < 40 and not index_up and middle_up:
            gesture = "right_click"

        # ── Left Click ────────────────────────────────────────────────────
        # index finger + thumb pinch, middle finger NOT pinching.
        # Extra guard: m_pinch_dist must be clearly larger so right-click
        # and left-click don't fight each other.
        elif pinch_dist < 40 and index_up and m_pinch_dist > 50:
            gesture = "left_click"

        # ── Double Click ──────────────────────────────────────────────────
        # index + middle both up AND close together (tips nearly touching)
        elif index_up and middle_up and not ring_up and not pinky_up:
            im_dist = math.hypot(ix - mx, iy - my)
            if im_dist < 30:
                gesture = "double_click"
            else:
                gesture = "scroll"   # spread apart = scroll mode

        # ── Grab / Drag ───────────────────────────────────────────────────
        elif not index_up and not middle_up and not ring_up and not pinky_up:
            gesture = "grab"

        # ── Idle ──────────────────────────────────────────────────────────
        elif not index_up:
            gesture = "idle"

        # ── Move (default: index up alone) ────────────────────────────────
        # (already set as default above)

        return {
            "gesture":      gesture,
            "index_pos":    (ix, iy),
            "thumb_pos":    (tx, ty),
            "middle_pos":   (mx, my),
            "pinch_dist":   pinch_dist,
            "m_pinch_dist": m_pinch_dist,
            "fingers_up":   [index_up, middle_up, ring_up, pinky_up],
        }
=======
class GestureDetector:

    @staticmethod
    def calculate_distance(x1, y1, x2, y2):
        return math.hypot(x2 - x1, y2 - y1)

    @staticmethod
    def is_click(distance, threshold=30):
        return distance < threshold
>>>>>>> ddeb125b298a36543638c2209f87b34e9388c6bb
