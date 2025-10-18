"""
Tesseract OCRを使用したテキスト抽出モジュール

このモジュールは、検出された領域から日本語テキストを抽出し、
クリーンアップ処理を行います。
"""

from typing import Optional
import numpy as np
import cv2
import pytesseract
from src.object_detector import DetectionResult


class OCRProcessor:
    """
    Tesseract OCRを使用したテキスト抽出クラス
    
    検出されたバウンディングボックス領域から日本語テキストを抽出し、
    前処理とクリーンアップを行います。
    """
    
    def __init__(self, lang: str = 'jpn', margin: int = 5, min_bbox_size: int = 20):
        """
        OCRProcessorを初期化
        
        Args:
            lang: OCR言語コード（デフォルト: 'jpn'）
            margin: 切り出し時のマージン（ピクセル、デフォルト: 5）
            min_bbox_size: 最小バウンディングボックスサイズ（ピクセル、デフォルト: 20）
        """
        self.lang = lang
        self.margin = margin
        self.min_bbox_size = min_bbox_size
        
        # Tesseractの動作確認
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            raise RuntimeError(
                f"Tesseract OCRが正しくインストールされていません: {e}\n"
                f"macOSの場合: brew install tesseract tesseract-lang"
            )

    def extract_text(self, frame: np.ndarray, bbox: DetectionResult, remove_newlines: bool = False) -> str:
        """
        バウンディングボックス領域からテキストを抽出
        
        Args:
            frame: 元画像（BGR形式のnumpy配列）
            bbox: バウンディングボックス情報
            remove_newlines: 改行を削除するか（titleフィールド用）
        
        Returns:
            抽出されたテキスト（クリーンアップ済み）
            OCR失敗時は空文字列を返す
        """
        try:
            # バウンディングボックスのサイズチェック（小さすぎる領域はスキップ）
            bbox_width = bbox.x2 - bbox.x1
            bbox_height = bbox.y2 - bbox.y1
            
            if bbox_width < self.min_bbox_size or bbox_height < self.min_bbox_size:
                return ""
            
            # 画像の高さと幅を取得
            height, width = frame.shape[:2]
            
            # マージンを追加した座標を計算（画像境界内に収める）
            x1 = max(0, bbox.x1 - self.margin)
            y1 = max(0, bbox.y1 - self.margin)
            x2 = min(width, bbox.x2 + self.margin)
            y2 = min(height, bbox.y2 + self.margin)
            
            # バウンディングボックス領域を切り出す
            cropped_image = frame[y1:y2, x1:x2]
            
            # 切り出した画像が空でないことを確認
            if cropped_image.size == 0:
                return ""
            
            # OCR実行（最適化設定）
            # --psm 6: 単一の均一なテキストブロックを想定
            # --oem 3: デフォルトのOCRエンジンモード（LSTM）
            text = pytesseract.image_to_string(
                cropped_image,
                lang=self.lang,
                config='--psm 6 --oem 3'
            )
            
            # テキストをクリーンアップ
            cleaned_text = self.cleanup_text(text, remove_newlines=remove_newlines)
            
            return cleaned_text
            
        except Exception as e:
            # OCR失敗時はエラーをキャッチして空文字列を返す
            print(f"OCR処理でエラーが発生しました: {e}")
            return ""

    @staticmethod
    def cleanup_text(text: str, remove_newlines: bool = False) -> str:
        """
        抽出されたテキストをクリーンアップ
        
        空白文字の正規化と短すぎるテキストのフィルタリングを行います。
        
        Args:
            text: 生のOCR結果
            remove_newlines: 改行を削除するか（titleフィールド用）
        
        Returns:
            正規化されたテキスト（2文字以下の場合は空文字列）
        """
        if not text:
            return ""
        
        # 空白文字を正規化
        import re
        
        if remove_newlines:
            # 改行を削除（titleフィールド用）
            text = text.replace('\n', ' ').replace('\r', ' ')
            # 連続する空白を1つに
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
        else:
            # 各行ごとに処理（改行を保持）
            lines = text.split('\n')
            cleaned_lines = []
            
            for line in lines:
                # 行の前後の空白を削除
                line = line.strip()
                # 連続する空白を1つに
                line = re.sub(r'\s+', ' ', line)
                if line:
                    cleaned_lines.append(line)
            
            # 改行で結合
            text = '\n'.join(cleaned_lines)
        
        # 2文字以下のテキストをフィルタリング
        if len(text) <= 2:
            return ""
        
        return text

    @staticmethod
    def preprocess_image(image: np.ndarray) -> np.ndarray:
        """
        OCR精度向上のための画像前処理
        
        グレースケール変換とコントラスト調整を行います。
        
        Args:
            image: 入力画像（BGR形式）
        
        Returns:
            前処理済み画像（グレースケール）
        """
        # グレースケール変換
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # コントラスト調整（CLAHE: Contrast Limited Adaptive Histogram Equalization）
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        return enhanced
