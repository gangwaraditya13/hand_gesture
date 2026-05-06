import cv2
import threading
import tkinter as tk
from tkinter import ttk
import pyautogui

from hand_tracking import HandTracker
from gesture_recognition import GestureRecognizer
from action_controller import ActionController

class GestureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hand Gesture Controller")
        self.root.geometry("300x250")
        
        self.running = False
        self.active_mode = tk.StringVar(value="None")
        
        # Setup UI
        self.setup_ui()
        
        # Setup modules
        self.tracker = HandTracker(detection_con=0.8, track_con=0.8)
        self.recognizer = GestureRecognizer()
        
        # We need screen dimensions for PyAutoGUI
        w_scr, h_scr = pyautogui.size()
        self.controller = ActionController(w_scr, h_scr)
         
        self.cap = None
        self.thread = None

    def setup_ui(self):
        ttk.Label(self.root, text="Select Control Mode:", font=("Arial", 12)).pack(pady=10)
         
        modes = [
            ("No Action / Debug", "None"),
            ("Cursor Control", "Cursor"),
            ("Volume Control", "Volume"),
            ("Media Commands", "Commands")
        ]
         
        for text, mode in modes:
            ttk.Radiobutton(self.root, text=text, variable=self.active_mode, value=mode).pack(anchor=tk.W, padx=40)
            
        self.start_btn = ttk.Button(self.root, text="Start Camera", command=self.toggle_camera)
        self.start_btn.pack(pady=20)
         
    def toggle_camera(self):
        if self.running:
            self.running = False
            self.start_btn.config(text="Start Camera")
            if self.cap:
                self.cap.release()
            cv2.destroyAllWindows()
        else:
            self.running = True
            self.start_btn.config(text="Stop Camera")
            self.thread = threading.Thread(target=self.run_camera_loop)
            self.thread.daemon = True
            self.thread.start()
             
    def run_camera_loop(self):
        self.cap = cv2.VideoCapture(0)
        w_cam, h_cam = 640, 480
        self.cap.set(3, w_cam)
        self.cap.set(4, h_cam)
        
        while self.running:
            success, img = self.cap.read()
            if not success:
                continue
                
            img = cv2.flip(img, 1) # Mirror image
            img = self.tracker.find_hands(img, draw=True)
            lm_list = self.tracker.get_landmarks(img, draw=False)
            
            mode = self.active_mode.get()
               
            if len(lm_list) != 0:
                fingers = self.recognizer.fingers_up(lm_list)
                gesture = self.recognizer.recognize_gesture(fingers)
                    
                # Draw Gesture Text
                cv2.putText(img, f'Gesture: {gesture}', (10, 30), cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 0, 0), 2)
                cv2.putText(img, f'Mode: {mode}', (10, 60), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 255, 0), 2)
                   
                # Execute actions based on selected mode
                if mode == "Cursor":
                    # Index finger moving
                    if fingers[1] == 1 and fingers[2] == 0:
                        x1, y1 = lm_list[8][1], lm_list[8][2]
                        # Account for mirroring of the image in coordinates!
                        self.controller.move_cursor(w_cam - x1, y1, w_cam, h_cam)
                        cv2.circle(img, (x1, y1), 10, (255, 0, 255), cv2.FILLED)
                            
                    # Clicking (Index and Middle fingers are up and close)
                    if fingers[1] == 1 and fingers[2] == 1:
                        length, line_info, center = self.recognizer.get_distance(8, 12, lm_list)
                        if length < 40:
                            cv2.circle(img, (center[0], center[1]), 15, (0, 255, 0), cv2.FILLED)
                            self.controller.click()
                               
                elif mode == "Volume":
                    # Thumb and Index distance
                    if fingers[0] == 1 and fingers[1] == 1:
                        length, line_info, center = self.recognizer.get_distance(4, 8, lm_list)
                        
                        vol_per, vol_bar = self.controller.set_volume_by_distance(length, min_dist=20, max_dist=200)
                        
                        # Draw Volume Bar
                        cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 3)
                        cv2.rectangle(img, (50, int(vol_bar)), (85, 400), (0, 255, 0), cv2.FILLED)
                        cv2.putText(img, f'{int(vol_per)} %', (40, 450), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 3)
                        
                        # Distance visualization
                        cv2.line(img, (line_info[0], line_info[1]), (line_info[2], line_info[3]), (255, 0, 255), 3)
                        if length < 20: # Visual feedback for min volume
                            cv2.circle(img, (center[0], center[1]), 10, (0, 255, 0), cv2.FILLED)
                            
                elif mode == "Commands":
                    self.controller.execute_command(gesture)

            cv2.imshow("Webcam Feed", img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        self.running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        # Ensure UI resets even if closed via 'q'
        try:
            self.start_btn.config(text="Start Camera")
        except:
            pass

def on_closing(root, app):
    app.running = False
    if app.cap:
        app.cap.release()
    cv2.destroyAllWindows()
    root.destroy()
    exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = GestureApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root, app))
    root.mainloop()
