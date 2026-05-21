"""
hand_tracker.py — compatible with mediapipe 0.10.x (new Tasks API)
Falls back to the legacy solutions API for older versions automatically.
"""

import cv2
import mediapipe as mp


def _has_solutions():
    """mediapipe < 0.10 exposed mp.solutions; 0.10+ moved to Tasks."""
    try:
        _ = mp.solutions.hands
        return True
    except AttributeError:
        return False


class HandTracker:
    def __init__(
        self,
        max_num_hands: int = 1,
        min_detection_confidence: float = 0.75,
        min_tracking_confidence: float = 0.75,
        static_image_mode: bool = False,
    ):
        self._use_legacy = _has_solutions()
        self.results = None

        if self._use_legacy:
            # ── mediapipe < 0.10  (legacy solutions API) ─────────────────
            self._mp_hands   = mp.solutions.hands
            self._mp_draw    = mp.solutions.drawing_utils
            self._hands      = self._mp_hands.Hands(
                static_image_mode=static_image_mode,
                max_num_hands=max_num_hands,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )
            self._lm_spec    = self._mp_draw.DrawingSpec(
                color=(0, 255, 200), thickness=2, circle_radius=3)
            self._conn_spec  = self._mp_draw.DrawingSpec(
                color=(0, 180, 255), thickness=2)
            print("[HandTracker] Using legacy mediapipe solutions API")

        else:
            # ── mediapipe 0.10+  (Tasks API) ──────────────────────────────
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision as mp_vision
            from mediapipe.tasks.python.vision import (
                HandLandmarker, HandLandmarkerOptions, RunningMode
            )
            import urllib.request, os, tempfile

            # Download the hand landmarker model if not already present
            model_path = os.path.join(
                os.path.dirname(__file__), "hand_landmarker.task"
            )
            if not os.path.exists(model_path):
                url = (
                    "https://storage.googleapis.com/mediapipe-models/"
                    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
                )
                print(f"[HandTracker] Downloading model → {model_path} ...")
                urllib.request.urlretrieve(url, model_path)
                print("[HandTracker] Model downloaded.")

            options = HandLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=model_path),
                running_mode=RunningMode.IMAGE,
                num_hands=max_num_hands,
                min_hand_detection_confidence=min_detection_confidence,
                min_hand_presence_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )
            self._landmarker = HandLandmarker.create_from_options(options)

            # We'll still use drawing_utils if available, else draw manually
            try:
                self._mp_draw   = mp.solutions.drawing_utils
                self._mp_hands  = mp.solutions.hands
                self._draw_avail = True
            except AttributeError:
                self._draw_avail = False

            # Landmark connections (21 points, standard MediaPipe topology)
            self._CONNECTIONS = frozenset([
                (0,1),(1,2),(2,3),(3,4),
                (0,5),(5,6),(6,7),(7,8),
                (5,9),(9,10),(10,11),(11,12),
                (9,13),(13,14),(14,15),(15,16),
                (13,17),(17,18),(18,19),(19,20),(0,17),
            ])

            print("[HandTracker] Using mediapipe 0.10 Tasks API")

    # ── Public interface ──────────────────────────────────────────────────

    def find_hands(self, frame, draw: bool = True):
        """Detect hands in BGR frame, optionally draw landmarks. Returns frame."""
        if self._use_legacy:
            return self._find_legacy(frame, draw)
        else:
            return self._find_tasks(frame, draw)

    def get_landmarks(self, frame, hand_index: int = 0):
        """Return list of (id, x, y) pixel coords for one hand."""
        if self._use_legacy:
            return self._landmarks_legacy(frame, hand_index)
        else:
            return self._landmarks_tasks(frame, hand_index)

    def num_hands(self) -> int:
        if self._use_legacy:
            if self.results and self.results.multi_hand_landmarks:
                return len(self.results.multi_hand_landmarks)
        else:
            if self.results:
                return len(self.results.hand_landmarks)
        return 0

    # ── Legacy backend ────────────────────────────────────────────────────

    def _find_legacy(self, frame, draw):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self._hands.process(rgb)
        if self.results.multi_hand_landmarks and draw:
            for lms in self.results.multi_hand_landmarks:
                self._mp_draw.draw_landmarks(
                    frame, lms,
                    self._mp_hands.HAND_CONNECTIONS,
                    self._lm_spec, self._conn_spec,
                )
        return frame

    def _landmarks_legacy(self, frame, hand_index):
        lm_list = []
        if self.results and self.results.multi_hand_landmarks:
            if hand_index < len(self.results.multi_hand_landmarks):
                hand = self.results.multi_hand_landmarks[hand_index]
                h, w, _ = frame.shape
                for idx, lm in enumerate(hand.landmark):
                    lm_list.append((idx, int(lm.x * w), int(lm.y * h)))
        return lm_list

    # ── Tasks backend ─────────────────────────────────────────────────────

    def _find_tasks(self, frame, draw):
        import mediapipe as mp
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self.results = self._landmarker.detect(mp_img)

        if draw and self.results.hand_landmarks:
            h, w, _ = frame.shape
            for hand_lms in self.results.hand_landmarks:
                pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand_lms]
                # Draw connections
                for a, b in self._CONNECTIONS:
                    cv2.line(frame, pts[a], pts[b], (0, 180, 255), 2)
                # Draw landmark dots
                for x, y in pts:
                    cv2.circle(frame, (x, y), 4, (0, 255, 200), -1)
        return frame

    def _landmarks_tasks(self, frame, hand_index):
        lm_list = []
        if self.results and self.results.hand_landmarks:
            if hand_index < len(self.results.hand_landmarks):
                hand = self.results.hand_landmarks[hand_index]
                h, w, _ = frame.shape
                for idx, lm in enumerate(hand):
                    lm_list.append((idx, int(lm.x * w), int(lm.y * h)))
        return lm_list