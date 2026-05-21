import cv2
import mediapipe as mp

class HandTracker:
    def __init__(self,
                 model_path='hand_landmarker.task',
                 max_num_hands=1,
                 min_detection_confidence=0.7,
                 min_tracking_confidence=0.7):
        
        BaseOptions = mp.tasks.BaseOptions
        HandLandmarker = mp.tasks.vision.HandLandmarker
        HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=VisionRunningMode.IMAGE,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence)
            
        self.landmarker = HandLandmarker.create_from_options(options)
        self.results = None
        
        self.HAND_CONNECTIONS = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (5, 9), (9, 10), (10, 11), (11, 12),
            (9, 13), (13, 14), (14, 15), (15, 16),
            (13, 17), (0, 17), (17, 18), (18, 19), (19, 20)
        ]

    def find_hands(self, frame, draw=True):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        
        self.results = self.landmarker.detect(mp_image)
        
        if draw and self.results and self.results.hand_landmarks:
            for hand_landmarks in self.results.hand_landmarks:
                h, w, c = frame.shape
                
                # Draw connections
                for connection in self.HAND_CONNECTIONS:
                    p1 = hand_landmarks[connection[0]]
                    p2 = hand_landmarks[connection[1]]
                    cx1, cy1 = int(p1.x * w), int(p1.y * h)
                    cx2, cy2 = int(p2.x * w), int(p2.y * h)
                    cv2.line(frame, (cx1, cy1), (cx2, cy2), (0, 255, 0), 2)
                    
                # Draw points
                for lm in hand_landmarks:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(frame, (cx, cy), 5, (0, 0, 255), cv2.FILLED)
                    
        return frame

    def get_landmarks(self, frame):
        landmark_list = []
        if self.results and self.results.hand_landmarks:
            hand = self.results.hand_landmarks[0]
            h, w, c = frame.shape
            for idx, lm in enumerate(hand):
                cx, cy = int(lm.x * w), int(lm.y * h)
                landmark_list.append((idx, cx, cy))
        return landmark_list
