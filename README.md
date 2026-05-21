# 🖱️ Virtual Mouse — Hand Gesture Edition

Control your entire computer using nothing but your webcam and hand gestures. Built with MediaPipe, OpenCV, and PyAutoGUI. No mouse needed.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Cursor Movement** | Index finger steers the cursor with adaptive smoothing |
| **Left Click** | Pinch index + thumb together |
| **Right Click** | Fold index finger, pinch middle + thumb |
| **Double Click** | Bring index + middle fingertips close together |
| **Scroll** | Raise index + middle fingers, move hand up/down |
| **Grab / Drag** | Close all fingers into a fist |
| **Cursor Lock** | Cursor freezes during clicks — no drift |
| **Live HUD** | FPS counter, gesture label, pinch meter, finger indicators |
| **Real-time Tuning** | `+`/`-` keys adjust smoothing live without restarting |
| **Click Cooldown** | Prevents accidental rapid-fire clicks |
| **Single Hand Mode** | Only tracks one hand — second hand in frame is ignored |

---

## 🗂️ Project Structure

```
virtual-mouse/
├── main.py                   # Entry point
├── requirements.txt
│
├── core/
│   ├── hand_tracker.py       # MediaPipe hand detection (Tasks API + legacy)
│   ├── mouse_controller.py   # Low-latency OS mouse control
│   └── gesture_detector.py   # Gesture classification via landmark geometry
│
└── utils/
    ├── smoothing.py          # Adaptive velocity-aware smoother + click cooldown
    └── hud.py                # OpenCV HUD overlay renderer
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

```bash
python main.py
```

---

## 🎮 Gesture Reference

| Gesture | Action |
|---|---|
| ☝️ Index finger up | Move cursor |
| 🤌 Index + Thumb pinch | Left click |
| ✌️ Middle + Thumb pinch (index folded) | Right click |
| ⚡ Index + Middle fingertips close | Double click |
| ↕️ Index + Middle spread, move up/down | Scroll |
| ✊ All fingers closed | Grab / drag |
| ✋ No fingers up | Idle — pauses tracking |

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|---|---|
| `q` | Quit |
| `r` | Reset smoother (re-enables adaptive mode) |
| `+` / `=` | More responsive (less smoothing) |
| `-` | Smoother (more smoothing) |
| `d` | Toggle deadzone on/off |
| `m` | Toggle margin zone visualisation |
| `h` | Toggle HUD |

---

## 🛠️ Configuration

Edit the config block at the top of `main.py`:

```python
CAMERA_INDEX   = 0      # 0 = default webcam, 1 = external

FRAME_WIDTH    = 424    # Lower = faster inference, less lag
FRAME_HEIGHT   = 240

ALPHA_MIN      = 0.30   # Smoothness when hand is still (lower = more stable)
ALPHA_MAX      = 0.85   # Responsiveness when hand moves fast
DEADZONE       = 8      # Pixels of movement ignored (kills tremor)
VEL_SCALE      = 40     # Distance where alpha reaches maximum

MARGIN         = 60     # Dead border around frame edges
CLICK_COOLDOWN = 0.5    # Seconds between allowed clicks
SCROLL_SPEED   = 3      # Scroll lines per gesture event
```

---

## 🔧 Troubleshooting

**Webcam not opening**
- Change `CAMERA_INDEX = 1` or `2` in config

**Cursor too jittery**
- Press `-` while running to increase smoothing
- Or raise `DEADZONE` in config (e.g. `12`)

**Too many accidental clicks**
- Increase `CLICK_COOLDOWN` (e.g. `0.7`)

**Right click not working**
- Make sure index finger is fully folded down before pinching middle + thumb

**Low FPS**
- Resolution is already optimised at 424×240
- Lower `min_detection_confidence` to `0.35` in `main.py`

---

## 🧠 Concepts Used

- **Computer Vision** with OpenCV
- **Hand Tracking** with MediaPipe Hands (Tasks API)
- **Gesture Classification** via landmark geometry
- **Adaptive Signal Smoothing** — velocity-aware EMA
- **Low-latency OS mouse control** — ctypes on Windows, Quartz on macOS, Xlib on Linux
- **Human-Computer Interaction (HCI)**

---

## 🚀 Ideas to Extend

- **Per-app profiles** — different gestures for Chrome, Photoshop, etc.
- **Custom gesture classifier** — train your own TFLite model
- **Dwell click** — hover in place to auto-click
- **Macro gestures** — gesture triggers a keyboard shortcut
- **AR drawing** — draw on screen with your index finger
- **Two-hand mode** — left hand = modifier keys, right hand = cursor

---

## 🛠️ Technologies

- [Python 3.8+](https://python.org)
- [OpenCV](https://opencv.org)
- [MediaPipe](https://mediapipe.dev)
- [PyAutoGUI](https://pyautogui.readthedocs.io)
- [NumPy](https://numpy.org)