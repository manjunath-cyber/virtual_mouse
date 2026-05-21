"""
tray.py — System tray icon for Virtual Mouse
============================================
Runs in a background thread. Provides:
  - Start / Pause tracking toggle
  - Exit from taskbar (no need to focus camera window)

Requires: pip install pystray pillow
"""

import threading
import pystray
from PIL import Image, ImageDraw


def _make_icon(active: bool) -> Image.Image:
    """Draw a simple hand icon. Green = active, gray = paused."""
    size = 64
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    color = (0, 200, 80) if active else (120, 120, 120)

    # Palm
    draw.ellipse([16, 28, 48, 56], fill=color)

    # Fingers (five rectangles)
    finger_positions = [12, 20, 28, 36, 44]
    heights          = [10, 6, 4, 6, 10]
    for x, h in zip(finger_positions, heights):
        draw.rectangle([x, h, x + 8, 28], fill=color, outline=color)

    return img


class TrayIcon:
    """
    Spawn with TrayIcon(stop_callback).
    Call .set_active(bool) to update the icon state.
    """

    def __init__(self, stop_callback, pause_callback=None):
        self._stop_cb  = stop_callback
        self._pause_cb = pause_callback
        self._active   = True
        self._icon     = None
        self._thread   = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _build_menu(self):
        status = "Pause tracking" if self._active else "Resume tracking"
        return pystray.Menu(
            pystray.MenuItem(
                "Virtual Mouse",
                None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(status, self._toggle_pause),
            pystray.MenuItem("Exit", self._on_exit),
        )

    def _toggle_pause(self):
        self._active = not self._active
        if self._icon:
            self._icon.icon = _make_icon(self._active)
            self._icon.menu = self._build_menu()
        if self._pause_cb:
            self._pause_cb(self._active)

    def _on_exit(self):
        self._stop_cb()
        if self._icon:
            self._icon.stop()

    def _run(self):
        self._icon = pystray.Icon(
            name  = "VirtualMouse",
            icon  = _make_icon(True),
            title = "Virtual Mouse",
            menu  = self._build_menu(),
        )
        self._icon.run()

    def set_active(self, active: bool):
        self._active = active
        if self._icon:
            self._icon.icon = _make_icon(active)
            self._icon.menu = self._build_menu()

    def stop(self):
        if self._icon:
            self._icon.stop()