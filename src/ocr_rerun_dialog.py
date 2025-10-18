"""
OCR再実行ダイアログモジュール

このモジュールは、保存されたlist-item画像に対してOCRを再実行し、
パラメータを調整してレコードを更新する機能を提供します。
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Optional, Dict
import cv2
import numpy as np
from PIL import Image, ImageTk

from src.hierarchical_data_manager import StructuredRecord
from src.hierarchical_detector import HierarchicalDetector
from src.ocr_processor import OCRProcessor
from src.hierarchical_ocr_processor import process_hierarchical_detection
from src.config import AppConfig


class OCRRerunDialog:
    """
    OCR再実行ダイアログクラス
    
    保存されたlist-item画像を読み込み、パラメータを調整して
    OCRを再実行し、レコードを更新します。
    """
    
    def __init__(self, parent: tk.Widget, record: StructuredRecord, config: AppConfig):
        """
        OCRRerunDialogを初期化
        
        Args:
            parent: 親ウィジェット
            record: 対象レコード
            config: アプリケーション設定
        """
        self.parent = parent
        self.record = record
        self.config = config
        
        # 初期化成功フラグ
        self.initialized = False
        
        # ダイアログウィンドウを作成
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"OCR再実行 - {record.list_item_id}")
        self.dialog.geometry("900x700")
        self.dialog.configure(bg='#2b2b2b')
        
        # パラメータ
        self.ocr_lang_var = tk.StringVar(value=config.ocr_lang)
        
        # 画像とプレビュー
        self.original_image: Optional[np.ndarray] = None
        self.processed_image: Optional[np.ndarray] = None
        self.preview_photo: Optional[ImageTk.PhotoImage] = None
        
        # OCR結果
        self.ocr_results: Dict[str, str] = {}
        
        # UIをセットアップ
        self._setup_ui()
        
        # 画像を読み込み
        if not self._load_image():
            messagebox.showerror(
                "エラー",
                f"画像ファイルが見つかりません:\n{record.image_path}\n\n"
                "OCR再実行を行うには、元の画像ファイルが必要です。"
            )
            self.dialog.destroy()
            return
        
        # 初期プレビューを生成
        self._update_preview()
        
        # 初期化成功
        self.initialized = True
    
    def _setup_ui(self) -> None:
        """UIコンポーネントをセットアップ"""
        # 左側: パラメータ調整パネル
        left_frame = ttk.Frame(self.dialog)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
        
        self._setup_parameter_panel(left_frame)
        
        # 右側: プレビューパネル
        right_frame = ttk.Frame(self.dialog)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self._setup_preview_panel(right_frame)
    
    def _setup_parameter_panel(self, parent: ttk.Frame) -> None:
        """パラメータ調整パネルをセットアップ"""
        # タイトル
        ttk.Label(parent, text="OCRパラメータ", font=('TkDefaultFont', 12, 'bold')).pack(pady=(0, 10))
        
        # OCR言語
        ttk.Label(parent, text="OCR言語:").pack(anchor=tk.W, pady=(10, 0))
        ttk.Combobox(
            parent,
            textvariable=self.ocr_lang_var,
            values=['jpn', 'eng', 'jpn+eng'],
            state='readonly'
        ).pack(fill=tk.X, pady=5)
        
        # ボタン
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(
            button_frame,
            text="OCR実行",
            command=self._run_ocr
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="適用",
            command=self._apply_results
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="キャンセル",
            command=self.dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
    
    def _setup_preview_panel(self, parent: ttk.Frame) -> None:
        """プレビューパネルをセットアップ"""
        # タイトル
        ttk.Label(parent, text="プレビュー", font=('TkDefaultFont', 12, 'bold')).pack(pady=(0, 10))
        
        # プレビューキャンバス
        self.preview_canvas = tk.Canvas(parent, bg='black', width=600, height=400)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        # OCR結果表示エリア
        ttk.Label(parent, text="OCR結果:", font=('TkDefaultFont', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        
        self.result_text = tk.Text(parent, height=10, wrap=tk.WORD, bg='#1e1e1e', fg='#e0e0e0')
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def _load_image(self) -> bool:
        """
        保存されたlist-item画像を読み込み
        
        Returns:
            成功した場合True、失敗した場合False
        """
        # 相対パスの場合、output/プレフィックスを追加
        image_path = Path(self.record.image_path)
        if not image_path.is_absolute() and not image_path.exists():
            # output/プレフィックスを試す
            image_path = Path('output') / self.record.image_path
        
        if not image_path.exists():
            return False
        
        # 画像を読み込み
        self.original_image = cv2.imread(str(image_path))
        
        if self.original_image is None:
            return False
        
        return True
    
    def _update_preview(self) -> None:
        """プレビューを更新"""
        if self.original_image is None:
            return
        
        try:
            # 元の画像をそのまま使用
            self.processed_image = self.original_image.copy()
            
            # プレビュー画像を作成
            self._display_preview(self.processed_image)
            
        except Exception as e:
            print(f"プレビュー更新エラー: {e}")
    
    def _display_preview(self, image: np.ndarray) -> None:
        """プレビューキャンバスに画像を表示"""
        # RGB変換（グレースケールの場合）
        if len(image.shape) == 2:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        else:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # PIL Imageに変換
        pil_image = Image.fromarray(image_rgb)
        
        # キャンバスサイズを取得（設定値を使用）
        canvas_width = self.preview_canvas.winfo_reqwidth()
        canvas_height = self.preview_canvas.winfo_reqheight()
        
        # サイズが取得できない場合は設定値を使用
        if canvas_width <= 1:
            canvas_width = 600
        if canvas_height <= 1:
            canvas_height = 400
        
        # キャンバスサイズに合わせてリサイズ
        pil_image.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)
        
        # PhotoImageに変換
        self.preview_photo = ImageTk.PhotoImage(image=pil_image)
        
        # キャンバスに表示
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            anchor=tk.CENTER,
            image=self.preview_photo
        )
    
    def _run_ocr(self) -> None:
        """OCRを実行"""
        if self.original_image is None:
            return
        
        try:
            # 階層的検出器を初期化
            detector = HierarchicalDetector(
                model_path=self.config.hierarchical_model_path,
                confidence_threshold=self.config.confidence_threshold,
                containment_threshold=self.config.containment_threshold
            )
            
            # OCRプロセッサを初期化
            ocr_processor = OCRProcessor(
                lang=self.ocr_lang_var.get(),
                margin=self.config.ocr_margin,
                min_bbox_width=15,
                min_bbox_height=8
            )
            
            # 階層的検出を実行
            print(f"🔍 物体検知開始...")
            hierarchical_results = detector.detect(self.original_image)
            print(f"✅ 物体検知完了: {len(hierarchical_results)}個のlist-itemを検出")
            
            if not hierarchical_results:
                messagebox.showwarning("警告", "list-itemが検出されませんでした")
                return
            
            # 最初のlist-itemを使用（通常は1つのみ）
            hierarchical_result = hierarchical_results[0]
            print(f"📦 list-item: {hierarchical_result.list_item_bbox}")
            print(f"   - title領域: {len(hierarchical_result.title_bboxes)}個")
            print(f"   - progress領域: {len(hierarchical_result.progress_bboxes)}個")
            print(f"   - last_read_date領域: {len(hierarchical_result.last_read_date_bboxes)}個")
            print(f"   - site_name領域: {len(hierarchical_result.site_name_bboxes)}個")
            
            # OCR処理を実行
            print(f"📝 OCR処理開始...")
            self.ocr_results = process_hierarchical_detection(
                self.original_image,
                hierarchical_result,
                ocr_processor
            )
            print(f"✅ OCR処理完了")
            
            # 結果を表示
            self._display_ocr_results()
            
            messagebox.showinfo(
                "成功",
                f"OCRが完了しました\n\n"
                f"検出されたlist-item: {len(hierarchical_results)}個\n"
                f"title領域: {len(hierarchical_result.title_bboxes)}個\n"
                f"progress領域: {len(hierarchical_result.progress_bboxes)}個\n"
                f"last_read_date領域: {len(hierarchical_result.last_read_date_bboxes)}個\n"
                f"site_name領域: {len(hierarchical_result.site_name_bboxes)}個"
            )
            
        except Exception as e:
            messagebox.showerror("エラー", f"OCR実行エラー: {str(e)}")
            print(f"OCR実行エラー: {e}")
    
    def _display_ocr_results(self) -> None:
        """OCR結果を表示"""
        self.result_text.delete('1.0', tk.END)
        
        result_lines = []
        result_lines.append(f"タイトル: {self.ocr_results.get('title', '(なし)')}")
        result_lines.append(f"進捗: {self.ocr_results.get('progress', '(なし)')}")
        result_lines.append(f"最終読書日: {self.ocr_results.get('last_read_date', '(なし)')}")
        result_lines.append(f"サイト名: {self.ocr_results.get('site_name', '(なし)')}")
        
        self.result_text.insert('1.0', '\n'.join(result_lines))
    
    def _apply_results(self) -> None:
        """OCR結果をレコードに適用"""
        if not self.ocr_results:
            messagebox.showwarning("警告", "先にOCRを実行してください")
            return
        
        # レコードを更新
        self.record.title = self.ocr_results.get('title', '')
        self.record.progress = self.ocr_results.get('progress', '')
        self.record.last_read_date = self.ocr_results.get('last_read_date', '')
        self.record.site_name = self.ocr_results.get('site_name', '')
        
        # エラーステータスを更新
        missing_fields = []
        if not self.record.title:
            missing_fields.append('missing_title')
        if not self.record.last_read_date:
            missing_fields.append('missing_last_read_date')
        if not self.record.site_name:
            missing_fields.append('missing_site_name')
        
        self.record.error_status = ', '.join(missing_fields) if missing_fields else 'OK'
        
        messagebox.showinfo("成功", "レコードを更新しました")
        self.dialog.destroy()
