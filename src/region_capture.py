"""
Region capture module for capturing a specific screen region.

This module provides functionality to capture a specific rectangular region
of the screen instead of a specific window.
"""

from typing import Optional, Tuple
import numpy as np
import mss
import cv2


class RegionCapture:
    """
    Screen region capture class.
    
    Captures a specific rectangular region of the screen.
    """
    
    def __init__(self, region: Tuple[int, int, int, int]):
        """
        Initialize RegionCapture.
        
        Args:
            region: Tuple of (x, y, width, height) defining the capture region
        """
        self.x, self.y, self.width, self.height = region
        self.sct = mss.mss()
        
        # Create monitor dict for mss
        self.monitor = {
            'left': self.x,
            'top': self.y,
            'width': self.width,
            'height': self.height
        }
    
    def __del__(self):
        """Cleanup mss resources."""
        if hasattr(self, 'sct'):
            self.sct.close()
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture the current frame from the specified region.
        
        Returns:
            numpy array in BGR format (OpenCV compatible) or None if capture fails
        """
        try:
            # Capture the region
            screenshot = self.sct.grab(self.monitor)
            
            # Convert to numpy array
            frame = np.array(screenshot)
            
            # Convert BGRA to BGR (remove alpha channel)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            return frame
        
        except Exception as e:
            print(f"Error capturing region: {e}")
            return None
    
    def get_region_info(self) -> dict:
        """
        Get information about the capture region.
        
        Returns:
            Dictionary with region information
        """
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height
        }
