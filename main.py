import cv2
import pyautogui
import time

from core.hand_tracker import HandTracker
from core.mouse_controller import MouseController
from core.gesture_detector import GestureDetector
from utils.smoothing import Smoothener

cap = cv2.VideoCapture(0)

tracker = HandTracker()
mouse = MouseController()
smoothener = Smoothener()

prev_time = 0
last_click = time.time()

while True:

    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)

    h, w, c = frame.shape

    frame = tracker.find_hands(frame)

    landmarks = tracker.get_landmarks(frame)

    if landmarks:

        # Index finger tip
        _, ix, iy = landmarks[8]

        # Thumb tip
        _, tx, ty = landmarks[4]

        # Draw circle on index finger
        cv2.circle(frame, (ix, iy), 10, (255, 0, 255), cv2.FILLED)

        # Smooth and move mouse
        sx, sy = smoothener.smooth(ix, iy)
        mouse.move_mouse(sx, sy, w, h)

        # Check for click gesture
        distance = GestureDetector.calculate_distance(
            ix, iy, tx, ty
        )

        if GestureDetector.is_click(distance):
            
            # Click cooldown
            if time.time() - last_click > 1:
                pyautogui.click()
                last_click = time.time()

            cv2.putText(frame,
                        "CLICK",
                        (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        3)

    # Calculate FPS
    curr_time = time.time()
    fps = 1 / (curr_time - prev_time)
    prev_time = curr_time

    cv2.putText(frame,
                f'FPS: {int(fps)}',
                (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 0),
                2)

    cv2.imshow("Virtual Mouse", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
