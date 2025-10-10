"""
GUI application module for the real-time OCR application - Simplified version.
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from pathlib import Path
from typing import Optional
import threading
import queue
from datetime import datetime
import cv2
from PIL import Image, ImageTk

from config import AppConfig
from window_capture import WindowCapture
from object_detector import ObjectDetector
from ocr_processor import OCRProcessor
from data_manager import DataManager
from error_handler import ErrorHandler


class RealtimeOCRGUI:
    """Tkinter-based GUI for the real-time OCR application."""
    
    def __init__(self, root: tk.Tk):
        """Initialize the GUI application."""
        self.root = root
        self.root.title("リアルタイムOCRアプリケーション")
        self.root.geometry("1200x800")
        
        # Application state
        self.config = AppConfig()
        self.is_running = False
        self.is_paused = False
        self.preview_active = False  # プレビュー表示中
        self.processing_active = False  # 物体検知・OCR処理中
        self.processing_thread: Optional[threading.Thread] = None
        self.preview_thread: Optional[threading.Thread] = None
        
        # Processing components
        self.window_capture: Optional[WindowCapture] = None
        self.object_detector: Optional[ObjectDetector] = None
        self.ocr_processor: Optional[OCRProcessor] = None
        self.data_manager: Optional[DataManager] = None
        
        # Statistics
        self.stats = {
            'unique_count': 0,
            'total_detections': 0,
            'new_detections': 0,
            'duplicate_detections': 0,
            'frames_processed': 0,
            'start_time': None,
            'fps': 0.0,
            'last_fps_update': None,
            'frame_count_for_fps': 0
        }
        
        # Thread communication
        self.frame_queue = queue.Queue(maxsize=2)
        self.log_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.preview_stop_event = threading.Event()
        self.processing_stop_event = threading.Event()
        self.state_lock = threading.Lock()
        
        # Setup GUI
        self._setup_ui()
        
        # Start queue processing
        self._process_queues()
    
    def _setup_ui(self):
        """Setup the main UI layout."""
        # Configure root grid
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=2)
        self.root.rowconfigure(0, weight=1)
        
        # Left panel
        left_frame = ttk.Frame(self.root, padding="10")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Right panel
        right_frame = ttk.Frame(self.root, padding="10")
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Setup panels
        self._setup_left_panel(left_frame)
        self._setup_right_panel(right_frame)
    
    def _get_available_windows(self):
        """Get list of available windows."""
        try:
            from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionAll, kCGNullWindowID
            
            window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionAll, kCGNullWindowID)
            
            system_keywords = ['Window Server', 'Dock', 'Menubar', 'StatusBar', 'Item-0']
            filtered = []
            seen = set()
            
            for window in window_list:
                title = window.get('kCGWindowName', '')
                
                if not title or title in seen:
                    continue
                
                # Skip system windows
                if any(keyword in title for keyword in system_keywords):
                    continue
                
                filtered.append(title)
                seen.add(title)
            
            return sorted(filtered) if filtered else ['iPhone', 'iPhoneミラーリング']
        except Exception as e:
            print(f"Warning: Could not get window list: {e}")
            return ['iPhone', 'iPhoneミラーリング']
    
    def _refresh_windows(self):
        """Refresh the list of available windows."""
        self.available_windows = self._get_available_windows()
        self.window_combo['values'] = self.available_windows
        
        # If current value is not in list, set to first item
        if self.window_title_var.get() not in self.available_windows and self.available_windows:
            self.window_title_var.set(self.available_windows[0])
    
    def _setup_left_panel(self, parent):
        """Setup left panel with config, controls, and stats."""
        # Config section
        config_group = ttk.LabelFrame(parent, text="設定", padding="10")
        config_group.pack(fill=tk.X, pady=(0, 10))
        
        # Window title
        ttk.Label(config_group, text="ウィンドウタイトル:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.window_title_var = tk.StringVar(value=self.config.target_window_title)
        
        # Create frame for combobox and refresh button
        window_frame = ttk.Frame(config_group)
        window_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        window_frame.columnconfigure(0, weight=1)
        
        # Get available windows
        self.available_windows = self._get_available_windows()
        
        # Combobox for window selection
        self.window_combo = ttk.Combobox(
            window_frame,
            textvariable=self.window_title_var,
            values=self.available_windows,
            width=22
        )
        self.window_combo.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Refresh button
        ttk.Button(window_frame, text="🔄", command=self._refresh_windows, width=3).grid(row=0, column=1, padx=(5, 0))
        
        # Confidence
        ttk.Label(config_group, text="信頼度:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.confidence_var = tk.DoubleVar(value=self.config.confidence_threshold)
        ttk.Scale(config_group, from_=0.0, to=1.0, variable=self.confidence_var, orient=tk.HORIZONTAL).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        # OCR language
        ttk.Label(config_group, text="OCR言語:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.ocr_lang_var = tk.StringVar(value=self.config.ocr_lang)
        ttk.Combobox(config_group, textvariable=self.ocr_lang_var, values=['jpn', 'eng', 'jpn+eng'], state='readonly', width=27).grid(row=2, column=1, pady=5, padx=5)
        
        config_group.columnconfigure(1, weight=1)
        
        # Control section
        control_group = ttk.LabelFrame(parent, text="制御", padding="10")
        control_group.pack(fill=tk.X, pady=(0, 10))
        
        # Window selection button
        window_btn_frame = ttk.Frame(control_group)
        window_btn_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.select_window_btn = ttk.Button(window_btn_frame, text="ウィンドウを選択してプレビュー", command=self._select_window_and_preview)
        self.select_window_btn.pack(side=tk.LEFT, padx=5)
        
        # Processing control buttons
        btn_frame = ttk.Frame(control_group)
        btn_frame.pack(fill=tk.X)
        
        self.start_stop_btn = ttk.Button(btn_frame, text="開始", command=self._toggle_start_stop, state=tk.DISABLED)
        self.start_stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.pause_resume_btn = ttk.Button(btn_frame, text="一時停止", command=self._toggle_pause_resume, state=tk.DISABLED)
        self.pause_resume_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="CSV出力", command=self._export_csv).pack(side=tk.LEFT, padx=5)
        
        # Status
        status_frame = ttk.Frame(control_group)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(status_frame, text="ステータス:").pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="停止中")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, font=('TkDefaultFont', 10, 'bold'))
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Stats section
        stats_group = ttk.LabelFrame(parent, text="統計情報", padding="10")
        stats_group.pack(fill=tk.BOTH, expand=True)
        
        self.unique_count_var = tk.StringVar(value="0")
        self.frames_var = tk.StringVar(value="0")
        self.new_detections_var = tk.StringVar(value="0")
        
        ttk.Label(stats_group, text="ユニークデータ:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(stats_group, textvariable=self.unique_count_var).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(stats_group, text="処理フレーム:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(stats_group, textvariable=self.frames_var).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(stats_group, text="新規検出:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(stats_group, textvariable=self.new_detections_var, foreground='green').grid(row=2, column=1, sticky=tk.W, pady=2)
        
        self.fps_var = tk.StringVar(value="0.0")
        ttk.Label(stats_group, text="FPS:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Label(stats_group, textvariable=self.fps_var, foreground='blue').grid(row=3, column=1, sticky=tk.W, pady=2)
        
        self._update_stats()
    
    def _setup_right_panel(self, parent):
        """Setup right panel with preview and log."""
        # Preview section
        preview_group = ttk.LabelFrame(parent, text="プレビュー", padding="10")
        preview_group.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.preview_canvas = tk.Canvas(preview_group, bg='black', width=640, height=480)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        self.current_photo = None
        
        # Log section
        log_group = ttk.LabelFrame(parent, text="抽出データログ", padding="10")
        log_group.pack(fill=tk.BOTH, expand=True)
        
        # Counters
        counter_frame = ttk.Frame(log_group)
        counter_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.new_count_var = tk.StringVar(value="0")
        self.duplicate_count_var = tk.StringVar(value="0")
        self.total_count_var = tk.StringVar(value="0")
        
        ttk.Label(counter_frame, text="新規:").pack(side=tk.LEFT)
        ttk.Label(counter_frame, textvariable=self.new_count_var, foreground='green').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(counter_frame, text="重複:").pack(side=tk.LEFT)
        ttk.Label(counter_frame, textvariable=self.duplicate_count_var, foreground='orange').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(counter_frame, text="合計:").pack(side=tk.LEFT)
        ttk.Label(counter_frame, textvariable=self.total_count_var).pack(side=tk.LEFT)
        
        # Log text
        self.log_text = scrolledtext.ScrolledText(log_group, wrap=tk.WORD, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self.log_text.tag_config('new', foreground='green')
        self.log_text.tag_config('duplicate', foreground='orange')
        self.log_text.tag_config('error', foreground='red')
        self.log_text.tag_config('info', foreground='blue')
    
    def _select_window_and_preview(self):
        """Select window and start preview."""
        current_state = self._get_current_state()
        
        if current_state in ["preview", "processing", "paused"]:
            # Stop everything
            if current_state in ["processing", "paused"]:
                self._stop_processing()
            self._stop_preview()
            self._set_state("stopped")
        else:
            # Start preview
            try:
                self.config.target_window_title = self.window_title_var.get()
                self.window_capture = WindowCapture(window_title=self.config.target_window_title)
                
                if self.window_capture.find_window() is None:
                    raise RuntimeError(f"ウィンドウが見つかりません: {self.config.target_window_title}")
                
                self._start_preview()
                self._set_state("preview")
            except Exception as e:
                messagebox.showerror("エラー", str(e))
                self._set_state("stopped")
    
    def _toggle_start_stop(self):
        """Toggle start/stop."""
        current_state = self._get_current_state()
        
        if current_state in ["preview"]:
            self._start_processing()
        elif current_state in ["processing", "paused"]:
            self._stop_processing()
    
    def _update_status_color(self, color: str):
        """Update status label color."""
        self.status_label.config(foreground=color)
    
    def _get_current_state(self) -> str:
        """Get current application state."""
        with self.state_lock:
            if self.processing_active:
                if self.is_paused:
                    return "paused"
                return "processing"
            elif self.preview_active:
                return "preview"
            else:
                return "stopped"
    
    def _set_state(self, state: str):
        """Set application state with proper UI updates."""
        with self.state_lock:
            if state == "stopped":
                self.preview_active = False
                self.processing_active = False
                self.is_paused = False
                self.status_var.set("停止中")
                self._update_status_color("black")
                self.select_window_btn.config(text="ウィンドウを選択してプレビュー")
                self.start_stop_btn.config(state=tk.DISABLED)
                self.pause_resume_btn.config(state=tk.DISABLED)
            elif state == "preview":
                self.preview_active = True
                self.processing_active = False
                self.is_paused = False
                self.status_var.set("プレビュー中")
                self._update_status_color("blue")
                self.select_window_btn.config(text="プレビューを停止")
                self.start_stop_btn.config(state=tk.NORMAL, text="開始")
                self.pause_resume_btn.config(state=tk.DISABLED)
            elif state == "processing":
                self.preview_active = True
                self.processing_active = True
                self.is_paused = False
                self.status_var.set("処理中")
                self._update_status_color("green")
                self.start_stop_btn.config(text="停止")
                self.pause_resume_btn.config(state=tk.NORMAL, text="一時停止")
            elif state == "paused":
                self.preview_active = True
                self.processing_active = True
                self.is_paused = True
                self.status_var.set("一時停止中")
                self._update_status_color("orange")
                self.pause_resume_btn.config(text="再開")
    
    def _toggle_pause_resume(self):
        """Toggle pause/resume."""
        current_state = self._get_current_state()
        
        if current_state == "processing":
            self._set_state("paused")
        elif current_state == "paused":
            self._set_state("processing")
    
    def _start_preview(self):
        """Start preview loop (capture only)."""
        self.preview_stop_event.clear()
        self.preview_thread = threading.Thread(target=self._preview_loop, daemon=True)
        self.preview_thread.start()
    
    def _stop_preview(self):
        """Stop preview loop."""
        self.preview_stop_event.set()
        if self.preview_thread:
            self.preview_thread.join(timeout=2.0)
        
        # Clear preview
        self.preview_canvas.delete("all")
        self.current_photo = None
    
    def _preview_loop(self):
        """Preview loop - capture and display only."""
        try:
            while not self.preview_stop_event.is_set():
                if self.window_capture is None:
                    break
                
                # Skip preview if processing is active (processing loop handles display)
                current_state = self._get_current_state()
                if current_state in ["processing", "paused"]:
                    self.preview_stop_event.wait(0.1)
                    continue
                
                # Capture frame
                frame = self.window_capture.capture_frame()
                
                if frame is None:
                    continue
                
                # Send frame to display
                try:
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    pass
                
                # Small delay to control frame rate
                self.preview_stop_event.wait(0.033)  # ~30 FPS
        except Exception as e:
            self.log_queue.put((f"プレビューエラー: {str(e)}", 'error'))
    
    def _start_processing(self):
        """Start processing (detection + OCR)."""
        current_state = self._get_current_state()
        if current_state not in ["preview"]:
            messagebox.showwarning("警告", "先にウィンドウを選択してプレビューを開始してください")
            return
        
        self.config.confidence_threshold = self.confidence_var.get()
        self.config.ocr_lang = self.ocr_lang_var.get()
        
        try:
            self.data_manager = DataManager(output_path=self.config.output_csv)
            self.object_detector = ObjectDetector(model_path=self.config.model_path, confidence_threshold=self.config.confidence_threshold)
            self.ocr_processor = OCRProcessor(lang=self.config.ocr_lang, margin=self.config.ocr_margin)
        except Exception as e:
            messagebox.showerror("初期化エラー", str(e))
            return
        
        self.stats['start_time'] = datetime.now()
        self.stats['frames_processed'] = 0
        self.stats['new_detections'] = 0
        self.stats['fps'] = 0.0
        self.stats['last_fps_update'] = None
        self.stats['frame_count_for_fps'] = 0
        
        self.processing_stop_event.clear()
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        
        self._set_state("processing")
    
    def _stop_processing(self):
        """Stop processing (but keep preview running)."""
        self.processing_stop_event.set()
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)
        
        self._set_state("preview")
    
    def _export_csv(self):
        """Export to CSV."""
        if self.data_manager:
            try:
                self.data_manager.export_to_csv()
                messagebox.showinfo("成功", f"CSVに出力しました: {self.config.output_csv}")
            except Exception as e:
                messagebox.showerror("エラー", str(e))
    
    def _processing_loop(self):
        """Processing loop - detection and OCR only."""
        try:
            frame_start_time = datetime.now()
            
            while not self.processing_stop_event.is_set():
                if self.is_paused:
                    self.processing_stop_event.wait(0.1)
                    continue
                
                # Capture frame
                if self.window_capture is None:
                    break
                
                frame = self.window_capture.capture_frame()
                
                if frame is None:
                    continue
                
                # Calculate FPS
                current_time = datetime.now()
                self.stats['frame_count_for_fps'] += 1
                
                if self.stats['last_fps_update'] is None:
                    self.stats['last_fps_update'] = current_time
                
                time_diff = (current_time - self.stats['last_fps_update']).total_seconds()
                if time_diff >= 1.0:  # Update FPS every second
                    self.stats['fps'] = self.stats['frame_count_for_fps'] / time_diff
                    self.stats['frame_count_for_fps'] = 0
                    self.stats['last_fps_update'] = current_time
                
                # Detect objects
                detections = self.object_detector.detect(frame)
                self.stats['frames_processed'] += 1
                
                # Process OCR for each detection
                for detection in detections:
                    text = self.ocr_processor.extract_text(frame, detection)
                    if text:
                        is_new = self.data_manager.add_text(text)
                        self.log_queue.put((text, 'new' if is_new else 'duplicate'))
                        if is_new:
                            self.stats['new_detections'] += 1
                
                # Draw detections on frame
                frame_copy = frame.copy()
                for detection in detections:
                    try:
                        cv2.rectangle(
                            frame_copy,
                            (int(detection.x1), int(detection.y1)),
                            (int(detection.x2), int(detection.y2)),
                            (0, 255, 0),
                            2
                        )
                    except Exception:
                        pass  # Skip drawing if error
                
                # Send frame to display (override preview frame)
                try:
                    # Clear queue and put new frame
                    while not self.frame_queue.empty():
                        try:
                            self.frame_queue.get_nowait()
                        except queue.Empty:
                            break
                    self.frame_queue.put_nowait(frame_copy)
                except queue.Full:
                    pass
                
                # No delay - run as fast as possible to maximize FPS
        except Exception as e:
            self.log_queue.put((f"処理エラー: {str(e)}", 'error'))
    
    def _process_queues(self):
        """Process queues."""
        # Process frames
        try:
            while True:
                frame = self.frame_queue.get_nowait()
                self._update_preview(frame)
        except queue.Empty:
            pass
        
        # Process logs
        try:
            while True:
                message, tag = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message + '\n', tag)
                self.log_text.see(tk.END)
                
                # Update counters
                if tag == 'new':
                    current = int(self.new_count_var.get())
                    self.new_count_var.set(str(current + 1))
                elif tag == 'duplicate':
                    current = int(self.duplicate_count_var.get())
                    self.duplicate_count_var.set(str(current + 1))
                
                total = int(self.new_count_var.get()) + int(self.duplicate_count_var.get())
                self.total_count_var.set(str(total))
        except queue.Empty:
            pass
        
        self.root.after(100, self._process_queues)
    
    def _update_preview(self, frame):
        """Update preview canvas."""
        if frame is None:
            return
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)
        
        # Resize to fit canvas
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        if canvas_width > 1 and canvas_height > 1:
            image.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(image=image)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(canvas_width//2, canvas_height//2, anchor=tk.CENTER, image=photo)
        self.current_photo = photo
    
    def _update_stats(self):
        """Update statistics."""
        if self.data_manager:
            self.unique_count_var.set(str(self.data_manager.get_count()))
        self.frames_var.set(str(self.stats['frames_processed']))
        self.new_detections_var.set(str(self.stats['new_detections']))
        self.fps_var.set(f"{self.stats['fps']:.1f}")
        
        self.root.after(1000, self._update_stats)
    
    def run(self):
        """Start the GUI main loop."""
        self.root.mainloop()


def main():
    """Main entry point for GUI application."""
    root = tk.Tk()
    app = RealtimeOCRGUI(root)
    app.run()


if __name__ == "__main__":
    main()
