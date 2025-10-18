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

from src.config import AppConfig
from src.window_capture import WindowCapture
from src.object_detector import ObjectDetector
from src.ocr_processor import OCRProcessor
from src.data_manager import DataManager
from src.error_handler import ErrorHandler
from src.pipeline_processor import PipelineProcessor
from src.performance_mode import get_available_modes
from src.hierarchical_pipeline import HierarchicalPipeline
from src.session_manager import SessionManager
from src.visualizer import Visualizer
from src.data_editor_window import DataEditorWindow


class ToolTip:
    """ツールチップを表示するクラス"""
    
    def __init__(self, widget, text):
        """
        ツールチップを初期化
        
        Args:
            widget: ツールチップを表示するウィジェット
            text: 表示するテキスト
        """
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        
        # マウスイベントをバインド
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        """ツールチップを表示"""
        if self.tooltip_window or not self.text:
            return
        
        # ウィジェットの位置を取得
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        # トップレベルウィンドウを作成
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # ラベルを作成（ダークテーマ対応）
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            justify=tk.LEFT,
            background="#2b2b2b",  # ダークグレー背景
            foreground="#e0e0e0",  # 明るいグレー文字
            relief=tk.SOLID,
            borderwidth=1,
            font=("TkDefaultFont", 9),
            wraplength=300
        )
        label.pack()
    
    def hide_tooltip(self, event=None):
        """ツールチップを非表示"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class RealtimeOCRGUI:
    """Tkinter-based GUI for the real-time OCR application."""
    
    def __init__(self, root: tk.Tk):
        """Initialize the GUI application."""
        self.root = root
        self.root.title("リアルタイムOCRアプリケーション")
        self.root.geometry("1200x1000")
        
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
        self.pipeline_processor: Optional[PipelineProcessor] = None
        self.hierarchical_pipeline: Optional[HierarchicalPipeline] = None
        self.session_manager: Optional[SessionManager] = None
        self.visualizer: Optional[Visualizer] = None
        self.data_editor_window: Optional[DataEditorWindow] = None
        
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
    
    def _on_performance_mode_changed(self, event=None):
        """パフォーマンスモード変更時のハンドラ"""
        # Get selected mode key from display value
        selected_display = self.performance_mode_combo.get()
        # Extract key from "key (name)" format
        mode_key = selected_display.split(' (')[0]
        
        # If processing is active, restart with new mode
        current_state = self._get_current_state()
        if current_state in ["processing", "paused"]:
            # Show confirmation dialog
            if messagebox.askyesno(
                "モード変更",
                "パフォーマンスモードを変更すると処理が再起動されます。続行しますか？"
            ):
                self._stop_processing()
                # Wait a bit for cleanup
                self.root.after(500, lambda: self._start_processing_with_mode(mode_key))
            else:
                # Revert to previous mode
                # This is a simplified approach - in production you'd track the previous mode
                pass
    
    def _setup_left_panel(self, parent):
        """Setup left panel with config, controls, and stats."""
        # Config section
        config_group = ttk.LabelFrame(parent, text="設定", padding="10")
        config_group.pack(fill=tk.X, pady=(0, 10))
        
        # Model selection
        model_label_frame = ttk.Frame(config_group)
        model_label_frame.grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(model_label_frame, text="検出モデル:").pack(side=tk.LEFT)
        model_hint = ttk.Label(model_label_frame, text=" ℹ️", foreground="cyan", cursor="hand2")
        model_hint.pack(side=tk.LEFT)
        ToolTip(model_hint,
                "使用する検出モデルを選択します。\n\n"
                "既存モデル:\n"
                "  - list-item全体を1つのラベルとして検出\n"
                "  - シンプルで高速\n\n"
                "階層的モデル:\n"
                "  - list-item内の詳細要素を個別に検出\n"
                "  - title、progress、last_read_date、site_nameを抽出\n"
                "  - 構造化されたCSV出力")
        
        self.detection_mode_var = tk.StringVar(value="legacy")
        model_frame = ttk.Frame(config_group)
        model_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Radiobutton(model_frame, text="既存モデル", variable=self.detection_mode_var, 
                       value="legacy").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(model_frame, text="階層的モデル", variable=self.detection_mode_var, 
                       value="hierarchical").pack(side=tk.LEFT, padx=5)
        
        # Window title
        ttk.Label(config_group, text="ウィンドウタイトル:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.window_title_var = tk.StringVar(value=self.config.target_window_title)
        
        # Create frame for combobox and refresh button
        window_frame = ttk.Frame(config_group)
        window_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
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
        confidence_label_frame = ttk.Frame(config_group)
        confidence_label_frame.grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Label(confidence_label_frame, text="信頼度:").pack(side=tk.LEFT)
        confidence_hint = ttk.Label(confidence_label_frame, text=" ℹ️", foreground="cyan", cursor="hand2")
        confidence_hint.pack(side=tk.LEFT)
        ToolTip(confidence_hint, 
                "物体検出の信頼度しきい値です。\n"
                "高い値: 検出数が減り、FPSが向上しますが、見逃しが増えます\n"
                "低い値: 検出数が増えますが、FPSが低下します\n"
                "推奨: 0.6〜0.7")
        
        self.confidence_var = tk.DoubleVar(value=self.config.confidence_threshold)
        confidence_scale_frame = ttk.Frame(config_group)
        confidence_scale_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Scale(confidence_scale_frame, from_=0.0, to=1.0, variable=self.confidence_var, 
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(confidence_scale_frame, textvariable=self.confidence_var, 
                 width=5).pack(side=tk.LEFT, padx=(5, 0))
        
        # OCR language
        ocr_lang_label_frame = ttk.Frame(config_group)
        ocr_lang_label_frame.grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Label(ocr_lang_label_frame, text="OCR言語:").pack(side=tk.LEFT)
        ocr_lang_hint = ttk.Label(ocr_lang_label_frame, text=" ℹ️", foreground="cyan", cursor="hand2")
        ocr_lang_hint.pack(side=tk.LEFT)
        ToolTip(ocr_lang_hint,
                "OCRで認識する言語を選択します。\n"
                "jpn: 日本語のみ（高速）\n"
                "eng: 英語のみ\n"
                "jpn+eng: 日本語と英語（やや低速）")
        
        self.ocr_lang_var = tk.StringVar(value=self.config.ocr_lang)
        ttk.Combobox(config_group, textvariable=self.ocr_lang_var, values=['jpn', 'eng', 'jpn+eng'], 
                    state='readonly', width=27).grid(row=3, column=1, pady=5, padx=5)
        
        # Performance mode
        perf_mode_label_frame = ttk.Frame(config_group)
        perf_mode_label_frame.grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Label(perf_mode_label_frame, text="パフォーマンスモード:").pack(side=tk.LEFT)
        perf_mode_hint = ttk.Label(perf_mode_label_frame, text=" ℹ️", foreground="cyan", cursor="hand2")
        perf_mode_hint.pack(side=tk.LEFT)
        ToolTip(perf_mode_hint,
                "処理速度と精度のバランスを選択します。\n\n"
                "高速: FPS優先（10-15 FPS目標）\n"
                "  - フレームスキップ有効\n"
                "  - キャッシュを積極活用\n\n"
                "バランス: 標準設定（5-10 FPS目標）\n"
                "  - 全フレーム処理\n"
                "  - キャッシュ有効\n\n"
                "高精度: 精度優先（3-5 FPS目標）\n"
                "  - キャッシュ無効\n"
                "  - 毎回検出とOCR実行")
        
        self.performance_mode_var = tk.StringVar(value="balanced")
        available_modes = get_available_modes()
        mode_display_values = [f"{key} ({name})" for key, name in available_modes.items()]
        self.performance_mode_combo = ttk.Combobox(
            config_group,
            textvariable=self.performance_mode_var,
            values=list(available_modes.keys()),
            state='readonly',
            width=27
        )
        self.performance_mode_combo.grid(row=4, column=1, pady=5, padx=5)
        
        # Display mode names in combobox
        self.performance_mode_combo['values'] = mode_display_values
        self.performance_mode_combo.set("balanced (バランス)")
        
        # Bind mode change event
        self.performance_mode_combo.bind('<<ComboboxSelected>>', self._on_performance_mode_changed)
        
        config_group.columnconfigure(1, weight=1)
        
        # Advanced settings section (collapsible)
        advanced_group = ttk.LabelFrame(parent, text="詳細設定（パフォーマンスチューニング）", padding="10")
        advanced_group.pack(fill=tk.X, pady=(0, 10))
        
        # Detection cache TTL
        detection_ttl_label_frame = ttk.Frame(advanced_group)
        detection_ttl_label_frame.grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Label(detection_ttl_label_frame, text="検出キャッシュTTL (秒):").pack(side=tk.LEFT)
        detection_ttl_hint = ttk.Label(detection_ttl_label_frame, text=" ℹ️", foreground="cyan", cursor="hand2")
        detection_ttl_hint.pack(side=tk.LEFT)
        ToolTip(detection_ttl_hint,
                "検出結果をキャッシュする有効期限です。\n\n"
                "長い値（1.0秒以上）:\n"
                "  ✓ キャッシュヒット率が上がりFPS向上\n"
                "  ✗ 新規項目の検出が遅れる\n\n"
                "短い値（0.5秒以下）:\n"
                "  ✓ 新規項目を素早く検出\n"
                "  ✗ キャッシュヒット率が下がりFPS低下\n\n"
                "推奨: 0.5〜1.0秒")
        
        self.detection_cache_ttl_var = tk.DoubleVar(value=self.config.detection_cache_ttl)
        detection_ttl_frame = ttk.Frame(advanced_group)
        detection_ttl_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Scale(detection_ttl_frame, from_=0.3, to=2.0, variable=self.detection_cache_ttl_var, 
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(detection_ttl_frame, textvariable=self.detection_cache_ttl_var, 
                 width=5).pack(side=tk.LEFT, padx=(5, 0))
        
        # Detection cache similarity
        detection_sim_label_frame = ttk.Frame(advanced_group)
        detection_sim_label_frame.grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Label(detection_sim_label_frame, text="フレーム類似度:").pack(side=tk.LEFT)
        detection_sim_hint = ttk.Label(detection_sim_label_frame, text=" ℹ️", foreground="cyan", cursor="hand2")
        detection_sim_hint.pack(side=tk.LEFT)
        ToolTip(detection_sim_hint,
                "フレームが類似していると判定するしきい値です。\n\n"
                "高い値（0.95以上）:\n"
                "  ✓ より確実に変化を検出\n"
                "  ✗ キャッシュヒット率が下がる\n\n"
                "低い値（0.90以下）:\n"
                "  ✓ キャッシュヒット率が上がりFPS向上\n"
                "  ✗ 変化を見逃す可能性\n\n"
                "推奨: 0.90〜0.95")
        
        self.detection_similarity_var = tk.DoubleVar(value=self.config.detection_cache_similarity)
        detection_sim_frame = ttk.Frame(advanced_group)
        detection_sim_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Scale(detection_sim_frame, from_=0.85, to=0.98, variable=self.detection_similarity_var,
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(detection_sim_frame, textvariable=self.detection_similarity_var,
                 width=5).pack(side=tk.LEFT, padx=(5, 0))
        
        # OCR cache position tolerance
        ocr_pos_label_frame = ttk.Frame(advanced_group)
        ocr_pos_label_frame.grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Label(ocr_pos_label_frame, text="OCR位置許容範囲 (px):").pack(side=tk.LEFT)
        ocr_pos_hint = ttk.Label(ocr_pos_label_frame, text=" ℹ️", foreground="cyan", cursor="hand2")
        ocr_pos_hint.pack(side=tk.LEFT)
        ToolTip(ocr_pos_hint,
                "OCR結果をキャッシュする際の位置の許容誤差です。\n\n"
                "大きい値（15px以上）:\n"
                "  ✓ OCRキャッシュヒット率が上がる\n"
                "  ✗ 異なる項目を同一と誤認する可能性\n\n"
                "小さい値（10px以下）:\n"
                "  ✓ より正確にキャッシュ判定\n"
                "  ✗ キャッシュヒット率が下がる\n\n"
                "推奨: 10〜15ピクセル")
        
        self.ocr_position_tolerance_var = tk.IntVar(value=self.config.ocr_cache_position_tolerance)
        ocr_pos_frame = ttk.Frame(advanced_group)
        ocr_pos_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Scale(ocr_pos_frame, from_=5, to=25, variable=self.ocr_position_tolerance_var,
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(ocr_pos_frame, textvariable=self.ocr_position_tolerance_var,
                 width=5).pack(side=tk.LEFT, padx=(5, 0))
        
        # Apply button
        ttk.Button(advanced_group, text="設定を適用", command=self._apply_advanced_settings).grid(
            row=3, column=0, columnspan=2, pady=(10, 0))
        
        # Help text
        help_text = ttk.Label(advanced_group, text="※ 設定変更後、処理を再起動すると反映されます", 
                             font=('TkDefaultFont', 8), foreground='gray')
        help_text.grid(row=4, column=0, columnspan=2, pady=(5, 0))
        
        advanced_group.columnconfigure(1, weight=1)
        
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
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.start_stop_btn = ttk.Button(btn_frame, text="開始", command=self._toggle_start_stop, state=tk.DISABLED)
        self.start_stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.pause_resume_btn = ttk.Button(btn_frame, text="一時停止", command=self._toggle_pause_resume, state=tk.DISABLED)
        self.pause_resume_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="CSV出力", command=self._export_csv).pack(side=tk.LEFT, padx=5)
        
        # Image folder management (for hierarchical mode)
        image_folder_frame = ttk.Frame(control_group)
        image_folder_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.open_folder_btn = ttk.Button(image_folder_frame, text="📁 画像フォルダを開く", 
                                         command=self._open_session_folder)
        self.open_folder_btn.pack(side=tk.LEFT, padx=5)
        
        folder_hint = ttk.Label(image_folder_frame, text="ℹ️", foreground="cyan", cursor="hand2")
        folder_hint.pack(side=tk.LEFT)
        ToolTip(folder_hint,
                "階層的検出モードで切り出された\n"
                "list-item画像が保存されているフォルダを開きます。\n"
                "タイムスタンプ付きのセッションフォルダが格納されている\n"
                "親ディレクトリが開きます。")
        
        # Data editor button (for hierarchical mode)
        data_editor_frame = ttk.Frame(control_group)
        data_editor_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.data_editor_btn = ttk.Button(data_editor_frame, text="📊 データエディター", 
                                         command=self._open_data_editor)
        self.data_editor_btn.pack(side=tk.LEFT, padx=5)
        
        editor_hint = ttk.Label(data_editor_frame, text="ℹ️", foreground="cyan", cursor="hand2")
        editor_hint.pack(side=tk.LEFT)
        ToolTip(editor_hint,
                "抽出されたデータを表形式で表示し、\n"
                "編集・削除・確定・フィルタリングを行えます。\n"
                "階層的検出モードで処理を開始した後に使用できます。")
        
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
        ttk.Label(stats_group, textvariable=self.fps_var, foreground='cyan').grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # Hierarchical mode specific stats
        ttk.Separator(stats_group, orient='horizontal').grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(stats_group, text="階層的検出統計:", font=('TkDefaultFont', 9, 'bold')).grid(
            row=5, column=0, columnspan=2, sticky=tk.W, pady=(5, 2))
        
        self.list_item_count_var = tk.StringVar(value="0")
        ttk.Label(stats_group, text="  list-item検出数:").grid(row=6, column=0, sticky=tk.W, pady=2)
        ttk.Label(stats_group, textvariable=self.list_item_count_var).grid(row=6, column=1, sticky=tk.W, pady=2)
        
        self.title_count_var = tk.StringVar(value="0")
        ttk.Label(stats_group, text="  title検出数:").grid(row=7, column=0, sticky=tk.W, pady=2)
        ttk.Label(stats_group, textvariable=self.title_count_var).grid(row=7, column=1, sticky=tk.W, pady=2)
        
        self.error_count_var = tk.StringVar(value="0")
        self.success_count_var = tk.StringVar(value="0")
        ttk.Label(stats_group, text="  正常レコード:").grid(row=8, column=0, sticky=tk.W, pady=2)
        ttk.Label(stats_group, textvariable=self.success_count_var, foreground='green').grid(row=8, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(stats_group, text="  エラーレコード:").grid(row=9, column=0, sticky=tk.W, pady=2)
        ttk.Label(stats_group, textvariable=self.error_count_var, foreground='red').grid(row=9, column=1, sticky=tk.W, pady=2)
        
        # Similarity threshold slider (for hierarchical mode)
        ttk.Separator(stats_group, orient='horizontal').grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        similarity_label_frame = ttk.Frame(stats_group)
        similarity_label_frame.grid(row=11, column=0, columnspan=2, sticky=tk.W, pady=2)
        ttk.Label(similarity_label_frame, text="類似度しきい値:").pack(side=tk.LEFT)
        similarity_hint = ttk.Label(similarity_label_frame, text=" ℹ️", foreground="cyan", cursor="hand2")
        similarity_hint.pack(side=tk.LEFT)
        ToolTip(similarity_hint,
                "階層的検出モードでの重複判定に使用する\n"
                "文字列類似度のしきい値です。\n\n"
                "高い値（0.8以上）:\n"
                "  ✓ より確実に重複を検出\n"
                "  ✗ 類似した別作品を重複と誤認する可能性\n\n"
                "低い値（0.7以下）:\n"
                "  ✓ 別作品を正しく区別\n"
                "  ✗ OCR誤認識による重複を見逃す可能性\n\n"
                "推奨: 0.75〜0.80")
        
        self.similarity_threshold_var = tk.DoubleVar(value=self.config.similarity_threshold)
        similarity_frame = ttk.Frame(stats_group)
        similarity_frame.grid(row=12, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        ttk.Scale(similarity_frame, from_=0.6, to=0.9, variable=self.similarity_threshold_var,
                 orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(similarity_frame, textvariable=self.similarity_threshold_var,
                 width=5).pack(side=tk.LEFT, padx=(5, 0))
        
        # Performance metrics
        ttk.Separator(stats_group, orient='horizontal').grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.avg_capture_var = tk.StringVar(value="0.0ms")
        ttk.Label(stats_group, text="平均キャプチャ時間:").grid(row=5, column=0, sticky=tk.W, pady=2)
        ttk.Label(stats_group, textvariable=self.avg_capture_var, font=('TkDefaultFont', 8)).grid(row=5, column=1, sticky=tk.W, pady=2)
        
        self.avg_detection_var = tk.StringVar(value="0.0ms")
        ttk.Label(stats_group, text="平均検出時間:").grid(row=6, column=0, sticky=tk.W, pady=2)
        ttk.Label(stats_group, textvariable=self.avg_detection_var, font=('TkDefaultFont', 8)).grid(row=6, column=1, sticky=tk.W, pady=2)
        
        self.avg_ocr_var = tk.StringVar(value="0.0ms")
        ttk.Label(stats_group, text="平均OCR時間:").grid(row=7, column=0, sticky=tk.W, pady=2)
        ttk.Label(stats_group, textvariable=self.avg_ocr_var, font=('TkDefaultFont', 8)).grid(row=7, column=1, sticky=tk.W, pady=2)
        
        self.cache_hit_rate_var = tk.StringVar(value="0.0%")
        ttk.Label(stats_group, text="キャッシュヒット率:").grid(row=8, column=0, sticky=tk.W, pady=2)
        ttk.Label(stats_group, textvariable=self.cache_hit_rate_var, foreground='purple').grid(row=8, column=1, sticky=tk.W, pady=2)
        
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
        self.log_text.tag_config('info', foreground='cyan')
    
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
    
    def _apply_advanced_settings(self):
        """詳細設定を適用"""
        try:
            # 設定を更新
            self.config.detection_cache_ttl = round(self.detection_cache_ttl_var.get(), 2)
            self.config.detection_cache_similarity = round(self.detection_similarity_var.get(), 2)
            self.config.ocr_cache_position_tolerance = int(self.ocr_position_tolerance_var.get())
            
            # 処理中の場合は再起動を促す
            current_state = self._get_current_state()
            if current_state in ["processing", "paused"]:
                if messagebox.askyesno(
                    "設定適用",
                    "設定を反映するには処理を再起動する必要があります。今すぐ再起動しますか？"
                ):
                    # 処理を停止して再起動
                    self._stop_processing()
                    self.root.after(500, self._start_processing)
                else:
                    messagebox.showinfo("設定適用", "設定は保存されました。次回の処理開始時に反映されます。")
            else:
                messagebox.showinfo("設定適用", "設定が保存されました。")
            
            # ログに記録
            self.log_queue.put((
                f"詳細設定を更新: TTL={self.config.detection_cache_ttl}s, "
                f"類似度={self.config.detection_cache_similarity}, "
                f"位置許容={self.config.ocr_cache_position_tolerance}px",
                'info'
            ))
            
        except Exception as e:
            messagebox.showerror("エラー", f"設定の適用に失敗しました: {str(e)}")
    
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
        
        # Get mode key from display value
        selected_display = self.performance_mode_combo.get()
        mode_key = selected_display.split(' (')[0]
        
        self._start_processing_with_mode(mode_key)
    
    def _start_processing_with_mode(self, mode_key: str):
        """指定されたモードで処理を開始
        
        Args:
            mode_key: パフォーマンスモードキー（"fast", "balanced", "accurate"）
        """
        self.config.confidence_threshold = self.confidence_var.get()
        self.config.ocr_lang = self.ocr_lang_var.get()
        self.config.target_window_title = self.window_title_var.get()
        
        # 詳細設定を反映
        self.config.detection_cache_ttl = round(self.detection_cache_ttl_var.get(), 2)
        self.config.detection_cache_similarity = round(self.detection_similarity_var.get(), 2)
        self.config.ocr_cache_position_tolerance = int(self.ocr_position_tolerance_var.get())
        
        # 検出モードを取得
        detection_mode = self.detection_mode_var.get()
        
        try:
            if detection_mode == "hierarchical":
                # 階層的検出モードの場合
                self._start_hierarchical_processing()
            else:
                # 既存モード（legacy）の場合
                self._start_legacy_processing(mode_key)
            
        except Exception as e:
            self.log_queue.put((f"初期化エラー: {str(e)}", 'error'))
            messagebox.showerror("初期化エラー", str(e))
            # クリーンアップ
            self._cleanup_processing_components()
            return
        
        self.stats['start_time'] = datetime.now()
        self.stats['frames_processed'] = 0
        self.stats['new_detections'] = 0
        self.stats['fps'] = 0.0
        self.stats['last_fps_update'] = None
        self.stats['frame_count_for_fps'] = 0
        
        # 表示更新スレッドを開始
        self.processing_stop_event.clear()
        self.processing_thread = threading.Thread(target=self._display_loop, daemon=True)
        self.processing_thread.start()
        
        self._set_state("processing")
    
    def _start_legacy_processing(self, mode_key: str):
        """既存モード（legacy）で処理を開始
        
        Args:
            mode_key: パフォーマンスモードキー
        """
        # PipelineProcessorを初期化
        self.pipeline_processor = PipelineProcessor(
            config=self.config,
            performance_mode=mode_key,
            on_new_text_callback=self._on_new_text_detected
        )
        
        # パイプライン処理を開始
        self.pipeline_processor.start()
        
        # データマネージャーへの参照を保持
        self.data_manager = self.pipeline_processor.data_manager
        
        self.log_queue.put(("既存モードで処理を開始しました", 'info'))
    
    def _start_hierarchical_processing(self):
        """階層的検出モードで処理を開始"""
        # 類似度しきい値を設定に反映
        self.config.similarity_threshold = round(self.similarity_threshold_var.get(), 2)
        
        # HierarchicalPipelineを初期化
        self.hierarchical_pipeline = HierarchicalPipeline(config=self.config)
        
        # パイプライン処理を開始
        self.hierarchical_pipeline.start()
        
        # データマネージャーへの参照を保持（階層的データマネージャー）
        self.data_manager = self.hierarchical_pipeline.data_manager
        
        # セッションマネージャーへの参照を保持
        self.session_manager = self.hierarchical_pipeline.session_manager
        
        # Visualizerを初期化（階層的検出結果の描画用）
        if not self.visualizer:
            self.visualizer = Visualizer()
        
        self.log_queue.put((f"階層的検出モードで処理を開始しました（類似度しきい値: {self.config.similarity_threshold}）", 'info'))
    
    def _cleanup_processing_components(self):
        """処理コンポーネントをクリーンアップ"""
        if self.pipeline_processor:
            try:
                self.pipeline_processor.stop()
            except Exception:
                pass
            self.pipeline_processor = None
        
        if self.hierarchical_pipeline:
            try:
                self.hierarchical_pipeline.stop()
            except Exception:
                pass
            self.hierarchical_pipeline = None
        
        self.data_manager = None
        self.session_manager = None
    
    def _stop_processing(self):
        """Stop processing (but keep preview running)."""
        try:
            # パイプラインプロセッサを停止（既存モード）
            if self.pipeline_processor:
                try:
                    self.pipeline_processor.stop()
                except Exception as e:
                    self.log_queue.put((f"パイプライン停止エラー: {str(e)}", 'error'))
                finally:
                    self.pipeline_processor = None
            
            # 階層的パイプラインを停止
            if self.hierarchical_pipeline:
                try:
                    self.hierarchical_pipeline.stop()
                except Exception as e:
                    self.log_queue.put((f"階層的パイプライン停止エラー: {str(e)}", 'error'))
                finally:
                    self.hierarchical_pipeline = None
            
            # 表示スレッドを停止
            self.processing_stop_event.set()
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=2.0)
                if self.processing_thread.is_alive():
                    self.log_queue.put(("表示スレッドが正常に停止しませんでした", 'warning'))
            
            self._set_state("preview")
            
        except Exception as e:
            self.log_queue.put((f"処理停止エラー: {str(e)}", 'error'))
    
    def _export_csv(self):
        """Export to CSV."""
        if self.data_manager:
            try:
                self.data_manager.export_to_csv()
                # 出力パスを取得（既存モードと階層的モードで異なる）
                if self.hierarchical_pipeline:
                    output_path = self.config.hierarchical_csv_output
                else:
                    output_path = self.config.output_csv
                messagebox.showinfo("成功", f"CSVに出力しました: {output_path}")
            except Exception as e:
                messagebox.showerror("エラー", str(e))
    
    def _open_session_folder(self):
        """画像出力フォルダをFinderで開く"""
        try:
            import subprocess
            # タイムスタンプ付きフォルダが格納されている親ディレクトリを開く
            output_dir = Path(self.config.hierarchical_output_dir)
            
            if not output_dir.exists():
                messagebox.showwarning("警告", f"出力フォルダが存在しません: {output_dir}")
                return
            
            # macOSのFinderでフォルダを開く
            subprocess.run(['open', str(output_dir)], check=True)
            
        except Exception as e:
            messagebox.showerror("エラー", f"フォルダを開けませんでした: {str(e)}")
    
    def _open_data_editor(self):
        """データエディターを開く"""
        from src.hierarchical_data_manager import HierarchicalDataManager
        from src.csv_import_export import CSVImportExport
        
        # データマネージャーが存在しない場合、CSVから読み込みを試みる
        if not self.data_manager or not isinstance(self.data_manager, HierarchicalDataManager):
            # CSVファイルが存在するか確認
            csv_path = Path(self.config.hierarchical_csv_output)
            if csv_path.exists():
                # 一時的なデータマネージャーを作成してCSVを読み込む
                try:
                    temp_data_manager = HierarchicalDataManager(
                        output_path=str(csv_path),
                        similarity_threshold=self.config.similarity_threshold
                    )
                    csv_handler = CSVImportExport(temp_data_manager)
                    success, message = csv_handler.import_from_csv(str(csv_path), overwrite=True)
                    
                    if not success:
                        messagebox.showerror("エラー", f"CSVの読み込みに失敗しました: {message}")
                        return
                    
                    # データエディターを開く
                    if self.data_editor_window and self.data_editor_window.window.winfo_exists():
                        self.data_editor_window.window.lift()
                        self.data_editor_window.window.focus_force()
                    else:
                        self.data_editor_window = DataEditorWindow(self.root, temp_data_manager, self.config)
                        self.log_queue.put((f"CSVからデータを読み込みました: {csv_path}", 'info'))
                    return
                except Exception as e:
                    messagebox.showerror("エラー", f"CSVの読み込みに失敗しました: {str(e)}")
                    return
            else:
                messagebox.showwarning(
                    "警告", 
                    f"データがありません。\n\n"
                    f"以下のいずれかを実行してください：\n"
                    f"1. 階層的検出モードで処理を開始\n"
                    f"2. 既存のCSVファイルを配置: {csv_path}"
                )
                return
        
        # 既に開いている場合はフォーカス
        if self.data_editor_window and self.data_editor_window.window.winfo_exists():
            self.data_editor_window.window.lift()
            self.data_editor_window.window.focus_force()
        else:
            # 新規作成
            try:
                self.data_editor_window = DataEditorWindow(self.root, self.data_manager, self.config)
                self.log_queue.put(("データエディターを開きました", 'info'))
            except Exception as e:
                messagebox.showerror("エラー", f"データエディターを開けませんでした: {str(e)}")
                self.log_queue.put((f"データエディターエラー: {str(e)}", 'error'))
    
    def _on_new_text_detected(self, text: str):
        """新規テキスト検出時のコールバック
        
        Args:
            text: 検出された新規テキスト
        """
        # ログキューに新規テキストを追加
        self.log_queue.put((f"[新規] {text}", 'new'))
    
    def _display_loop(self):
        """Display loop - get frames from pipeline and display."""
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        try:
            while not self.processing_stop_event.is_set():
                try:
                    if self.is_paused:
                        self.processing_stop_event.wait(0.1)
                        continue
                    
                    # 階層的モードか既存モードかを判定
                    if self.hierarchical_pipeline:
                        # 階層的モードの場合
                        frame = self._process_hierarchical_frame()
                    elif self.pipeline_processor:
                        # 既存モードの場合
                        frame = self._process_legacy_frame()
                    else:
                        break
                    
                    if frame is not None:
                        # フレームを表示キューに送信
                        try:
                            # Clear queue and put new frame
                            while not self.frame_queue.empty():
                                try:
                                    self.frame_queue.get_nowait()
                                except queue.Empty:
                                    break
                            self.frame_queue.put_nowait(frame)
                        except queue.Full:
                            pass
                        
                        self.stats['frames_processed'] += 1
                        consecutive_errors = 0  # 成功したらリセット
                    
                    # データマネージャーから新規検出数を取得
                    if self.data_manager:
                        try:
                            if hasattr(self.data_manager, 'get_count'):
                                current_count = self.data_manager.get_count()
                            else:
                                # 階層的データマネージャーの場合
                                current_count = len(self.data_manager.records)
                            self.stats['new_detections'] = current_count
                        except Exception as dm_error:
                            self.log_queue.put((f"データマネージャーエラー: {str(dm_error)}", 'warning'))
                
                except Exception as e:
                    consecutive_errors += 1
                    self.log_queue.put((f"表示ループエラー (試行 {consecutive_errors}/{max_consecutive_errors}): {str(e)}", 'error'))
                    
                    if consecutive_errors >= max_consecutive_errors:
                        self.log_queue.put(("連続エラーが多すぎるため、表示ループを停止します", 'error'))
                        break
                    
                    self.processing_stop_event.wait(0.1)
                
        except Exception as e:
            self.log_queue.put((f"表示ループの致命的エラー: {str(e)}", 'error'))
        
        finally:
            # クリーンアップ
            self._cleanup_processing_components()
    
    def _process_legacy_frame(self):
        """既存モードでフレームを処理
        
        Returns:
            処理済みフレーム（表示用）
        """
        if not self.pipeline_processor.is_running():
            self.log_queue.put(("パイプラインが停止しました", 'warning'))
            return None
        
        # 表示キューから最新フレームを取得
        frame = self.pipeline_processor.get_display_frame(timeout=0.1)
        return frame
    
    def _process_hierarchical_frame(self):
        """階層的モードでフレームを処理
        
        Returns:
            処理済みフレーム（表示用）
        """
        if not self.window_capture:
            return None
        
        # フレームをキャプチャ
        frame = self.window_capture.capture_frame()
        
        if frame is None:
            return None
        
        # 階層的検出を実行（描画用に結果を取得）
        try:
            hierarchical_results = self.hierarchical_pipeline.detector.detect(frame)
            
            # パイプライン処理を実行（データ保存など）
            # 注: process_frameは内部でdetectを再度呼び出すが、
            # ここでは表示用に結果を先に取得している
            self.hierarchical_pipeline.process_frame(frame)
            
            # 検出結果を描画（表示用のフレームを作成）
            display_frame = frame
            if hierarchical_results and self.visualizer:
                display_frame = self.visualizer.draw_hierarchical_detections(frame, hierarchical_results)
            
            return display_frame
            
        except Exception as e:
            self.log_queue.put((f"階層的処理エラー: {str(e)}", 'error'))
            return frame
    
    def _process_queues(self):
        """Process queues.
        
        表示キューから最新フレームを取得して表示します。
        パイプラインプロセッサが有効な場合、処理済みフレームが
        _display_loopを通じてこのキューに送信されます。
        """
        # Process frames - 表示キューから最新フレームを取得
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
            if hasattr(self.data_manager, 'get_count'):
                # 既存モードのデータマネージャー
                self.unique_count_var.set(str(self.data_manager.get_count()))
            else:
                # 階層的データマネージャー
                self.unique_count_var.set(str(len(self.data_manager.records)))
        
        self.frames_var.set(str(self.stats['frames_processed']))
        self.new_detections_var.set(str(self.stats['new_detections']))
        
        # 階層的検出モードの統計情報を更新
        if self.hierarchical_pipeline:
            try:
                stats = self.hierarchical_pipeline.get_statistics()
                
                # list-item検出数（総レコード数）
                self.list_item_count_var.set(str(stats.get('total_records', 0)))
                
                # title検出数（エラーでないレコード数）
                success_count = stats.get('total_records', 0) - stats.get('error_records', 0)
                self.title_count_var.set(str(success_count))
                
                # 正常レコード数とエラーレコード数
                self.success_count_var.set(str(success_count))
                self.error_count_var.set(str(stats.get('error_records', 0)))
                
            except Exception as e:
                # エラーが発生した場合はデフォルト値を使用
                pass
        else:
            # 階層的モードでない場合は0を表示
            self.list_item_count_var.set("0")
            self.title_count_var.set("0")
            self.success_count_var.set("0")
            self.error_count_var.set("0")
        
        # パイプラインプロセッサからパフォーマンスメトリクスを取得
        if self.pipeline_processor:
            try:
                report = self.pipeline_processor.get_performance_report()
                
                # FPS（リアルタイム計測値を使用）
                self.fps_var.set(f"{report.get('fps', 0.0):.1f}")
                
                # 各処理ステップの平均実行時間
                avg_capture = report.get('avg_capture_time', 0.0) * 1000  # ms
                avg_detection = report.get('avg_detection_time', 0.0) * 1000  # ms
                avg_ocr = report.get('avg_ocr_time', 0.0) * 1000  # ms
                
                self.avg_capture_var.set(f"{avg_capture:.1f}ms")
                self.avg_detection_var.set(f"{avg_detection:.1f}ms")
                self.avg_ocr_var.set(f"{avg_ocr:.1f}ms")
                
                # キャッシュヒット率
                cache_hit_rate = report.get('cache_hit_rate', 0.0) * 100  # %
                self.cache_hit_rate_var.set(f"{cache_hit_rate:.1f}%")
                
            except Exception as e:
                # エラーが発生した場合はデフォルト値を使用
                pass
        else:
            # パイプラインプロセッサが無い場合は従来のFPS計算
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
