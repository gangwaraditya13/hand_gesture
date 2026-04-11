import pyautogui
import numpy as np
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

class ActionController:
    def __init__(self, screen_width, screen_height):
        # PyAutoGUI Setup
        self.w_scr, self.h_scr = screen_width, screen_height
        pyautogui.FAILSAFE = False # Prevent stopping if mouse goes to corner rapidly
        
        # PyCAW Setup (Volume Control)
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume = cast(interface, POINTER(IAudioEndpointVolume))
            self.vol_range = self.volume.GetVolumeRange()
            self.min_vol = self.vol_range[0]
            self.max_vol = self.vol_range[1]
        except Exception as e:
            print(f"Volume initialization error: {e}")
            self.volume = None
            self.min_vol = -65
            self.max_vol = 0
            
        self.smoothening = 5
        self.ploc_x, self.ploc_y = 0, 0
        self.cloc_x, self.cloc_y = 0, 0
        self.last_gesture = None
        
    def move_cursor(self, x, y, w_cam, h_cam, frame_reduction=100):
        """
        Moves the cursor based on the X,Y coordinates of a tracked point (like index finger tip).
        Includes smoothening and uses a smaller active frame to reach corners.
        """
        # Active frame reduction
        x3 = np.interp(x, (frame_reduction, w_cam - frame_reduction), (0, self.w_scr))
        y3 = np.interp(y, (frame_reduction, h_cam - frame_reduction), (0, self.h_scr))
        
        # Smoothening
        self.cloc_x = self.ploc_x + (x3 - self.ploc_x) / self.smoothening
        self.cloc_y = self.ploc_y + (y3 - self.ploc_y) / self.smoothening
        
        # PyAutoGUI move
        try:
            pyautogui.moveTo(self.w_scr - self.cloc_x, self.cloc_y) # Inverse X for mirror effect
        except:
            pass
            
        self.ploc_x, self.ploc_y = self.cloc_x, self.cloc_y
        
    def click(self):
        """
        Perform a left mouse click.
        """
        pyautogui.click()
        
    def set_volume_by_distance(self, distance, min_dist=20, max_dist=150):
        """
        Sets system volume given a distance (typically between thumb and index).
        """
        if self.volume is None:
            return 0, 400
            
        # Convert volume
        vol = np.interp(distance, [min_dist, max_dist], [self.min_vol, self.max_vol])
        vol_bar = np.interp(distance, [min_dist, max_dist], [400, 150]) 
        vol_per = np.interp(distance, [min_dist, max_dist], [0, 100])
        
        try:
            self.volume.SetMasterVolumeLevel(vol, None)
        except Exception as e:
            pass
            
        return vol_per, vol_bar

    def execute_command(self, gesture):
        """
        Execute discrete commands based on predefined gestures.
        Only fires once when gesture state changes to avoid spamming.
        """
        if gesture == self.last_gesture:
            return
            
        self.last_gesture = gesture
        
        if gesture == "Peace Sign":
            pyautogui.press('nexttrack')
        elif gesture == "Thumbs Up":
            pyautogui.press('playpause')
        elif gesture == "Open Palm":
            pyautogui.press('volumemute')
