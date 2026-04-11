import cv2
import mediapipe as mp
import os
import urllib.request
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4), # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8), # Index
    (5, 9), (9, 10), (10, 11), (11, 12), # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20) # Pinky & Base
]

def draw_landmarks_manual(img, landmarks):
    h, w, _ = img.shape
    # Draw connections
    for connection in HAND_CONNECTIONS:
        start_idx, end_idx = connection
        if start_idx < len(landmarks) and end_idx < len(landmarks):
            x1, y1 = int(landmarks[start_idx].x * w), int(landmarks[start_idx].y * h)
            x2, y2 = int(landmarks[end_idx].x * w), int(landmarks[end_idx].y * h)
            cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    # Draw keypoints
    for lm in landmarks:
        x, y = int(lm.x * w), int(lm.y * h)
        cv2.circle(img, (x, y), 5, (0, 0, 255), -1)

class HandTracker:
    def __init__(self, mode=False, max_hands=2, detection_con=0.5, track_con=0.5):
        self.mode = mode
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con
        
        # Download task model if it does not exist
        task_path = "hand_landmarker.task"
        if not os.path.exists(task_path):
            print("Downloading Hand Landmarker Task Model... Please wait...")
            url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
            urllib.request.urlretrieve(url, task_path)
            
        base_options = python.BaseOptions(model_asset_path=task_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=self.max_hands,
            min_hand_detection_confidence=self.detection_con,
            min_hand_presence_confidence=self.track_con,
            min_tracking_confidence=self.track_con)
            
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.tip_ids = [4, 8, 12, 16, 20]
        self.results = None
        
    def find_hands(self, img, draw=True):
        """
        Process the image, find hands, and optionally draw landmarks.
        """
        # Convert the BGR image to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Create a MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        
        # Detect hand landmarks
        self.results = self.detector.detect(mp_image)
        
        if self.results and self.results.hand_landmarks:
            for hand_lms in self.results.hand_landmarks:
                if draw:
                    draw_landmarks_manual(img, hand_lms)
                    
        return img
        
    def get_landmarks(self, img, hand_no=0, draw=False):
        """
        Returns a list of landmarks for a specific hand in format [id, cx, cy].
        """
        lm_list = []
        if self.results and self.results.hand_landmarks:
            if len(self.results.hand_landmarks) > hand_no:
                my_hand = self.results.hand_landmarks[hand_no]
                for id, lm in enumerate(my_hand):
                    h, w, c = img.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list.append([id, cx, cy])
                    if draw:
                        cv2.circle(img, (cx, cy), 7, (255, 0, 255), cv2.FILLED)
        return lm_list
