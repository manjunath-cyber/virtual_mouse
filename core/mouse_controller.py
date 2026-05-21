"""
MouseController — ultra-low-latency edition
============================================
Uses direct OS APIs for mouse movement instead of PyAutoGUI's moveTo,
which carries Python overhead plus a hidden PAUSE=0.1 default.

Priority:
  Windows  → ctypes SendInput  (< 0.1 ms, no context switch)
  macOS    → Quartz CGEventPost (< 0.5 ms)
  Linux    → python-xlib warp_pointer
  Fallback → PyAutoGUI (original behaviour, safety net)
"""

import sys
import pyautogui

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0


def _build_mover():
    """Return (move_fn, screen_w, screen_h, click_fn, rclick_fn, dclick_fn, scroll_fn)."""
    sw, sh = pyautogui.size()

    # ── Windows ──────────────────────────────────────────────────────────
    if sys.platform == "win32":
        import ctypes
        import ctypes.wintypes as wt

        MOUSEEVENTF_MOVE     = 0x0001
        MOUSEEVENTF_ABSOLUTE = 0x8000
        MOUSEEVENTF_LDOWN    = 0x0002
        MOUSEEVENTF_LUP      = 0x0004
        MOUSEEVENTF_RDOWN    = 0x0008
        MOUSEEVENTF_RUP      = 0x0010
        MOUSEEVENTF_WHEEL    = 0x0800
        INPUT_MOUSE          = 0

        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx",          ctypes.c_long),
                ("dy",          ctypes.c_long),
                ("mouseData",   wt.DWORD),
                ("dwFlags",     wt.DWORD),
                ("time",        wt.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            ]

        class INPUT(ctypes.Structure):
            class _I(ctypes.Union):
                _fields_ = [("mi", MOUSEINPUT)]
            _anonymous_ = ("_i",)
            _fields_ = [("type", wt.DWORD), ("_i", _I)]

        SendInput = ctypes.windll.user32.SendInput

        def _send(flags, dx=0, dy=0, data=0):
            inp = INPUT(type=INPUT_MOUSE,
                        mi=MOUSEINPUT(dx=dx, dy=dy, mouseData=data, dwFlags=flags))
            SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

        def _move(sx, sy):
            _send(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE,
                  dx=int(sx * 65535 / sw), dy=int(sy * 65535 / sh))

        def _click():
            _send(MOUSEEVENTF_LDOWN); _send(MOUSEEVENTF_LUP)

        def _rclick():
            _send(MOUSEEVENTF_RDOWN); _send(MOUSEEVENTF_RUP)

        def _dclick():
            _click(); _click()

        def _scroll(amount):
            _send(MOUSEEVENTF_WHEEL, data=int(amount * 120))

        print("[MouseController] Windows ctypes SendInput")
        return _move, sw, sh, _click, _rclick, _dclick, _scroll

    # ── macOS ─────────────────────────────────────────────────────────────
    if sys.platform == "darwin":
        try:
            import Quartz

            def _cur_pos():
                return Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))

            def _post(kind, pos, btn=0):
                ev = Quartz.CGEventCreateMouseEvent(None, kind, pos, btn)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)

            def _move(sx, sy):
                _post(Quartz.kCGEventMouseMoved,
                      Quartz.CGPoint(x=sx, y=sy),
                      Quartz.kCGMouseButtonLeft)

            def _click():
                p = _cur_pos()
                _post(Quartz.kCGEventLeftMouseDown,  p, Quartz.kCGMouseButtonLeft)
                _post(Quartz.kCGEventLeftMouseUp,    p, Quartz.kCGMouseButtonLeft)

            def _rclick():
                p = _cur_pos()
                _post(Quartz.kCGEventRightMouseDown, p, Quartz.kCGMouseButtonRight)
                _post(Quartz.kCGEventRightMouseUp,   p, Quartz.kCGMouseButtonRight)

            def _dclick(): _click(); _click()

            def _scroll(amount):
                ev = Quartz.CGEventCreateScrollWheelEvent(
                    None, Quartz.kCGScrollEventUnitLine, 1, int(amount))
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)

            print("[MouseController] macOS Quartz CGEvent")
            return _move, sw, sh, _click, _rclick, _dclick, _scroll
        except ImportError:
            pass

    # ── Linux (Xlib) ──────────────────────────────────────────────────────
    if sys.platform.startswith("linux"):
        try:
            from Xlib import display as xdisplay, X
            from Xlib.ext import xtest

            _disp = xdisplay.Display()
            _root = _disp.screen().root

            def _move(sx, sy):
                _root.warp_pointer(int(sx), int(sy))
                _disp.sync()

            def _xbtn(btn, press):
                xtest.fake_input(_disp,
                                  X.ButtonPress if press else X.ButtonRelease, btn)
                _disp.sync()

            def _click():  _xbtn(1, True);  _xbtn(1, False)
            def _rclick(): _xbtn(3, True);  _xbtn(3, False)
            def _dclick(): _click(); _click()

            def _scroll(amount):
                btn = 4 if amount > 0 else 5
                for _ in range(abs(int(amount))):
                    _xbtn(btn, True); _xbtn(btn, False)

            print("[MouseController] Linux Xlib warp_pointer")
            return _move, sw, sh, _click, _rclick, _dclick, _scroll
        except Exception:
            pass

    # ── Fallback ──────────────────────────────────────────────────────────
    print("[MouseController] PyAutoGUI fallback")

    def _move(sx, sy):   pyautogui.moveTo(sx, sy, _pause=False)
    def _click():        pyautogui.click(_pause=False)
    def _rclick():       pyautogui.rightClick(_pause=False)
    def _dclick():       pyautogui.doubleClick(_pause=False)
    def _scroll(amount): pyautogui.scroll(int(amount), _pause=False)
    return _move, sw, sh, _click, _rclick, _dclick, _scroll


_move_fn, _SW, _SH, _click_fn, _rclick_fn, _dclick_fn, _scroll_fn = _build_mover()


class MouseController:
    """
    Maps camera-space coordinates → screen-space and fires OS mouse events.

    margin : pixels trimmed from each edge of the camera frame.
             Keeps the active tracking zone away from shaky frame edges.
             Increase if cursor jitters at screen corners.
    """

    def __init__(self, margin: int = 80):
        self.screen_width  = _SW
        self.screen_height = _SH
        self.margin        = margin

    def move_mouse(self, x: int, y: int, cam_width: int, cam_height: int):
        ew = cam_width  - 2 * self.margin
        eh = cam_height - 2 * self.margin

        nx = max(0.0, min(1.0, (x - self.margin) / ew))
        ny = max(0.0, min(1.0, (y - self.margin) / eh))

        _move_fn(int(nx * self.screen_width), int(ny * self.screen_height))

    def left_click(self):              _click_fn()
    def right_click(self):             _rclick_fn()
    def double_click(self):            _dclick_fn()
    def scroll(self, direction: str, amount: int = 3):
        _scroll_fn(amount if direction == "up" else -amount)