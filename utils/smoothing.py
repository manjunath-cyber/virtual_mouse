class Smoothener:

    def __init__(self, alpha=0.2):

        self.alpha = alpha
        self.prev_x = 0
        self.prev_y = 0

    def smooth(self, x, y):

        curr_x = self.prev_x + (x - self.prev_x) * self.alpha
        curr_y = self.prev_y + (y - self.prev_y) * self.alpha

        self.prev_x = curr_x
        self.prev_y = curr_y

        return int(curr_x), int(curr_y)
