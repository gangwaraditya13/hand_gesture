import math

class GestureRecognizer:
    def __init__(self):
        self.tip_ids = [4, 8, 12, 16, 20]

    def fingers_up(self, lm_list):
        """
        Returns a list of 5 integers (0 or 1) representing whether each finger is up or down.
        Order: [Thumb, Index, Middle, Ring, Pinky]
        """
        fingers = []
        if not lm_list:
            return fingers

        # Thumb (Simple heuristic based on x/y coordinates)
        # Using x coordinates for right hand facing camera
        # If the thumb tip x is to the left of the thumb base (for right hand), it's open.
        # But this might fail on left hand. We'll use a simpler condition: 
        # distance from wrist to tip vs wrist to joint
        if lm_list[self.tip_ids[0]][1] > lm_list[self.tip_ids[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # 4 Fingers
        for id in range(1, 5):
            # If tip y is less than pip y, finger is open (up)
            if lm_list[self.tip_ids[id]][2] < lm_list[self.tip_ids[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
                
        return fingers

    def recognize_gesture(self, fingers):
        """
        Returns string literal of detected gesture based on active fingers.
        """
        if not fingers or len(fingers) != 5:
            return "No Hand"
            
        if fingers[1:] == [0, 0, 0, 0]:
            if fingers[0] == 1:
                 return "Thumbs Up"
            else:
                 return "Fist"
        elif fingers[1:] == [1, 1, 1, 1]:
            return "Open Palm"
        elif fingers[1:] == [1, 1, 0, 0]:
            return "Peace Sign"
        else:
            return "Unknown"

    def get_distance(self, p1, p2, lm_list):
        """
        Calculates distance between two landmarks.
        p1 and p2 are landmark IDs (e.g., 4 for thumb tip, 8 for index tip)
        """
        if not lm_list:
            return 0, [0, 0, 0, 0], [0, 0]
            
        x1, y1 = lm_list[p1][1], lm_list[p1][2]
        x2, y2 = lm_list[p2][1], lm_list[p2][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        length = math.hypot(x2 - x1, y2 - y1)
        
        return length, [x1, y1, x2, y2], [cx, cy]
