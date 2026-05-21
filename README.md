<<<<<<< HEAD
# 🖱️ Virtual Mouse — Enhanced Edition

Control your entire computer using nothing but your webcam and hand gestures. Built with MediaPipe, OpenCV, and PyAutoGUI.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Cursor Movement** | Index finger steers the cursor with smoothed tracking |
| **Left Click** | Pinch index + thumb together |
| **Right Click** | Pinch middle finger + thumb |
| **Double Click** | Bring index + middle fingertips close together |
| **Scroll** | Raise index + middle fingers, move hand up/down |
| **Grab / Drag** | Close all fingers into a fist |
| **Live HUD** | FPS counter, gesture badge, pinch meter, finger indicators |
| **Real-time Tuning** | `+`/`-` keys adjust smoothing on the fly |
| **Click Cooldown** | Prevents accidental rapid-fire clicks |
| **Margin Zone** | Edge-of-frame jitter ignored for stable tracking |

---

## 🗂️ Project Structure

```
virtual-mouse/
├── main.py                  # Entry point
├── requirements.txt
│
├── core/
│   ├── hand_tracker.py      # MediaPipe hand detection
│   ├── mouse_controller.py  # PyAutoGUI mouse actions
│   └── gesture_detector.py  # Gesture classification logic
│
└── utils/
    ├── smoothing.py         # EMA smoother + click cooldown
    └── hud.py               # OpenCV HUD overlay renderer
```

---

## ⚙️ Setup

### 1. Create virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run
=======
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
>>>>>>> ddeb125b298a36543638c2209f87b34e9388c6bb

```bash
python main.py
```

---

<<<<<<< HEAD
## 🎮 Gesture Reference

| Gesture | Action |
|---|---|
| ☝️ Index finger up | Move cursor |
| 👆 Index + Thumb pinch | Left click |
| ✌️ Middle + Thumb pinch | Right click |
| ⚡ Index + Middle close together | Double click |
| ↕️ Index + Middle spread (move up/down) | Scroll |
| ✊ All fingers closed | Grab / drag |
| ✋ No fingers up | Idle (pause tracking) |

---

## ⌨️ Keyboard Shortcuts (while running)

| Key | Action |
|---|---|
| `q` | Quit |
| `r` | Reset smoother (fix stuck cursor) |
| `+` / `=` | Increase responsiveness (less smoothing) |
| `-` | Increase smoothness (more smoothing) |

---

## 🛠️ Configuration

Edit the config block at the top of `main.py`:

```python
CAMERA_INDEX    = 0      # 0 = default webcam, 1 = external
FRAME_WIDTH     = 1280   # Camera resolution
FRAME_HEIGHT    = 720
SMOOTHING_ALPHA = 0.18   # 0.05 (smooth) → 0.5 (responsive)
CLICK_COOLDOWN  = 0.45   # Seconds between allowed clicks
SCROLL_SPEED    = 4      # Scroll lines per event
```

---

## 🔧 Troubleshooting

**Webcam not opening**
```python
cap = cv2.VideoCapture(1)  # Try index 1 or 2
```

**Cursor too jittery**
- Press `-` to increase smoothing
- Or lower `SMOOTHING_ALPHA` in config

**Too many accidental clicks**
- Increase `CLICK_COOLDOWN` (e.g., `0.7`)

**Low FPS**
- Lower resolution: set `FRAME_WIDTH = 640`, `FRAME_HEIGHT = 480`

---

## 🧠 Concepts You'll Learn

- **Computer Vision** with OpenCV
- **Hand Tracking** with MediaPipe
- **Gesture Classification** with landmark geometry
- **Human-Computer Interaction (HCI)**
- **Signal Smoothing** with Exponential Moving Average
- **Real-time AI pipelines**

---

## 🚀 Ideas to Extend

- **AI Gesture Commands** — ✌️ = Open Chrome, 👍 = Volume Up
- **Virtual Keyboard** — Gesture-based typing
- **Multi-Hand Mode** — One hand moves, one hand shortcuts
- **Presentation Mode** — Left/right swipe for slides
- **AR Annotations** — Draw on screen with your finger

---

## 🛠️ Technologies

- [Python 3.8+](https://python.org)
- [OpenCV](https://opencv.org)
- [MediaPipe](https://mediapipe.dev)
- [PyAutoGUI](https://pyautogui.readthedocs.io)
- [NumPy](https://numpy.org)
=======
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
>>>>>>> ddeb125b298a36543638c2209f87b34e9388c6bb
