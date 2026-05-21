import math

class GestureDetector:

    @staticmethod
    def calculate_distance(x1, y1, x2, y2):
        return math.hypot(x2 - x1, y2 - y1)

    @staticmethod
    def is_click(distance, threshold=30):
        return distance < threshold
