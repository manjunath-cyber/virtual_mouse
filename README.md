# Virtual Mouse using Hand Gestures

Control your computer mouse using only your webcam and hand gestures.

## Features

- Cursor movement
- Click gesture
- Smooth tracking
- FPS counter

## Technologies

- Python
- OpenCV
- MediaPipe
- PyAutoGUI

## Run

```bash
python main.py
```

---

# Common Errors

## Webcam not opening

Try:

```python
cap = cv2.VideoCapture(1)
```

## Cursor too fast

Reduce scaling or smoothing alpha.

## Too many clicks

Add click cooldown:

```python
import time

last_click = time.time()

if time.time() - last_click > 1:
    pyautogui.click()
    last_click = time.time()
```

## Learning Concepts You’ll Gain
- Computer Vision
- Hand Tracking
- Human Computer Interaction (HCI)
- Gesture Recognition
- Real-time AI systems
- OpenCV pipelines

## Next Level Upgrade Ideas

You can turn this into:

- AI Virtual Keyboard
- Gesture Gaming Controller
- Touchless Presentation System
- Smart Home Controller
- AR/VR interaction system

This is actually a strong cybersecurity + AI portfolio project for a student working in practical offensive/security tooling and human-computer interaction.
