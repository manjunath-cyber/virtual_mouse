import pyautogui

pyautogui.FAILSAFE = False

class MouseController:
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()

    def move_mouse(self, x, y, cam_width, cam_height):

        screen_x = int((x / cam_width) * self.screen_width)
        screen_y = int((y / cam_height) * self.screen_height)

        pyautogui.moveTo(screen_x, screen_y)
