"""
Region selector module for selecting screen capture area.

This module provides a GUI for selecting a rectangular region of the screen
to capture for OCR processing.
"""

import tkinter as tk
from typing import Optional, Tuple
import mss
import numpy as np
from PIL import Image, ImageTk, ImageDraw


class RegionSelector:
    """
    GUI for selecting a screen region.
    
    Allows the user to click and drag to select a rectangular region
    of the screen for capture.
    """
    
    def __init__(self):
        """Initialize the region selector."""
        self.selected_region: Optional[Tuple[int, int, int, int]] = None
        self.root: Optional[tk.Tk] = None
    
    def select_region(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Open a fullscreen window to select a region.
        
        Returns:
            Tuple of (x, y, width, height) or None if cancelled
        """
        self.root = tk.Tk()
        self.root.withdraw()  # Hide initially
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Set window to cover entire screen without fullscreen mode
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.root.overrideredirect(True)  # Remove window decorations
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.3)
        self.root.configure(bg='black')
        
        # Capture screenshot
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor
            screenshot = sct.grab(monitor)
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        
        # Create canvas
        self.canvas = tk.Canvas(
            self.root,
            width=screen_width,
            height=screen_height,
            highlightthickness=0
        )
        self.canvas.pack()
        
        # Show window first
        self.root.deiconify()
        self.root.update()
        
        # Display screenshot
        self.photo = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
        # Add instruction text
        self.canvas.create_text(
            screen_width // 2,
            50,
            text="クリック＆ドラッグで領域を選択してください（ESCでキャンセル）",
            fill='white',
            font=('Arial', 20, 'bold')
        )
        
        self.root.update()
        
        # Variables for selection
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        # Bind events
        self.canvas.bind('<Button-1>', self._on_press)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)
        self.root.bind('<Escape>', lambda e: self._cancel())
        
        self.root.mainloop()
        
        return self.selected_region
    
    def _on_press(self, event):
        """Handle mouse press."""
        self.start_x = event.x
        self.start_y = event.y
        
        # Create rectangle
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red', width=3
        )
    
    def _on_drag(self, event):
        """Handle mouse drag."""
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)
    
    def _on_release(self, event):
        """Handle mouse release."""
        if self.start_x is None or self.start_y is None:
            return
        
        # Calculate region
        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)
        
        width = x2 - x1
        height = y2 - y1
        
        # Validate region size
        if width < 50 or height < 50:
            self.canvas.create_text(
                self.root.winfo_screenwidth() // 2,
                100,
                text="領域が小さすぎます。もう一度選択してください。",
                fill='red',
                font=('Arial', 16, 'bold'),
                tags='error'
            )
            self.root.after(2000, lambda: self.canvas.delete('error'))
            return
        
        self.selected_region = (x1, y1, width, height)
        self.root.quit()
        self.root.destroy()
    
    def _cancel(self):
        """Cancel selection."""
        self.selected_region = None
        self.root.quit()
        self.root.destroy()


def select_screen_region() -> Optional[Tuple[int, int, int, int]]:
    """
    Convenience function to select a screen region.
    
    Returns:
        Tuple of (x, y, width, height) or None if cancelled
    """
    selector = RegionSelector()
    return selector.select_region()
