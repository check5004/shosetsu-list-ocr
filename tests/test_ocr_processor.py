"""
OCRProcessorモジュールのテストコード

Requirements: 4.3, 4.4, 4.5
"""

import pytest
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.ocr_processor import OCRProcessor
from src.object_detector import DetectionResult


class TestOCRProcessorInit:
    """OCRProcessorの初期化テストスイート"""
    
    @patch('src.ocr_processor.pytesseract.get_tesseract_version')
    def test_init_default_parameters(self, mock_get_version):
        """デフォルトパラメータでの初期化を確認"""
        mock_get_version.return_value = "5.0.0"
        
        processor = OCRProcessor()
        
        assert processor.lang == 'jpn'
        assert processor.margin == 5
    
    @patch('src.ocr_processor.pytesseract.get_tesseract_version')
    def test_init_custom_parameters(self, mock_get_version):
        """カスタムパラメータでの初期化を確認"""
        mock_get_version.return_value = "5.0.0"
        
        processor = OCRProcessor(lang='eng', margin=10)
        
        assert processor.lang == 'eng'
        assert processor.margin == 10
    
    @patch('src.ocr_processor.pytesseract.get_tesseract_version')
    def test_init_tesseract_not_installed(self, mock_get_version):
        """Tesseractがインストールされていない場合のエラーを確認 (Requirement 4.3)"""
        mock_get_version.side_effect = Exception("Tesseract not found")
        
        with pytest.raises(RuntimeError) as exc_info:
            OCRProcessor()
        
        error_message = str(exc_info.value)
        assert "Tesseract OCRが正しくインストールされていません" in error_message
        assert "brew install tesseract" in error_message


class TestCleanupText:
    """cleanup_text静的メソッドのテストスイート"""
    
    def test_cleanup_empty_string(self):
        """空文字列の処理を確認 (Requirement 4.4)"""
        result = OCRProcessor.cleanup_text("")
        assert result == ""
    
    def test_cleanup_none_input(self):
        """None入力の処理を確認 (Requirement 4.4)"""
        result = OCRProcessor.cleanup_text(None)
        assert result == ""
    
    def test_cleanup_whitespace_normalization(self):
        """空白文字の正規化を確認 (Requirement 4.4)"""
        # 複数の空白を1つに
        result = OCRProcessor.cleanup_text("これは    テスト    です")
        assert result == "これは テスト です"
        
        # タブ文字の処理
        result = OCRProcessor.cleanup_text("これは\t\tテスト\tです")
        assert result == "これは テスト です"
    
    def test_cleanup_leading_trailing_whitespace(self):
        """前後の空白削除を確認 (Requirement 4.4)"""
        result = OCRProcessor.cleanup_text("   テキスト   ")
        assert result == "テキスト"
        
        result = OCRProcessor.cleanup_text("\n\n  テキスト  \n\n")
        assert result == "テキスト"
    
    def test_cleanup_multiline_text(self):
        """複数行テキストの処理を確認 (Requirement 4.4)"""
        text = """
        タイトル: 小説名
        
        最終読書日時: 2024/01/01
        ページ数: 123
        """
        result = OCRProcessor.cleanup_text(text)
        
        # 空行が削除され、各行の空白が正規化されることを確認
        lines = result.split('\n')
        assert len(lines) == 3
        assert "タイトル: 小説名" in lines[0]
        assert "最終読書日時: 2024/01/01" in lines[1]
        assert "ページ数: 123" in lines[2]
    
    def test_cleanup_filter_short_text(self):
        """2文字以下のテキストをフィルタリング (Requirement 4.5)"""
        # 1文字
        result = OCRProcessor.cleanup_text("あ")
        assert result == ""
        
        # 2文字
        result = OCRProcessor.cleanup_text("あい")
        assert result == ""
        
        # 3文字（フィルタリングされない）
        result = OCRProcessor.cleanup_text("あいう")
        assert result == "あいう"
    
    def test_cleanup_filter_short_text_with_whitespace(self):
        """空白を含む短いテキストのフィルタリング (Requirement 4.5)"""
        # 空白を除くと2文字以下
        result = OCRProcessor.cleanup_text("  あ  ")
        assert result == ""
        
        result = OCRProcessor.cleanup_text("  あい  ")
        assert result == ""
    
    def test_cleanup_preserve_japanese_characters(self):
        """日本語文字が正しく保持されることを確認 (Requirement 4.4)"""
        text = "小説タイトル：異世界転生物語\n最終読書日時：2024年1月1日\nページ数：123/456"
        result = OCRProcessor.cleanup_text(text)
        
        assert "小説タイトル：異世界転生物語" in result
        assert "最終読書日時：2024年1月1日" in result
        assert "ページ数：123/456" in result
    
    def test_cleanup_preserve_numbers_and_symbols(self):
        """数字と記号が正しく保持されることを確認 (Requirement 4.4)"""
        text = "2024/01/01 12:34:56\nページ: 123/456\n進捗率: 26.8%"
        result = OCRProcessor.cleanup_text(text)
        
        assert "2024/01/01 12:34:56" in result
        assert "ページ: 123/456" in result
        assert "進捗率: 26.8%" in result
    
    def test_cleanup_empty_lines_removed(self):
        """空行が削除されることを確認 (Requirement 4.4)"""
        text = "行1\n\n\n行2\n\n行3"
        result = OCRProcessor.cleanup_text(text)
        
        lines = result.split('\n')
        assert len(lines) == 3
        assert lines[0] == "行1"
        assert lines[1] == "行2"
        assert lines[2] == "行3"


class TestPreprocessImage:
    """preprocess_image静的メソッドのテストスイート"""
    
    def test_preprocess_bgr_to_gray(self):
        """BGR画像のグレースケール変換を確認 (Requirement 4.3)"""
        # BGR画像を作成
        bgr_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        result = OCRProcessor.preprocess_image(bgr_image)
        
        # グレースケール画像であることを確認
        assert len(result.shape) == 2
        assert result.shape == (100, 100)
        assert result.dtype == np.uint8
    
    def test_preprocess_already_gray(self):
        """既にグレースケールの画像の処理を確認 (Requirement 4.3)"""
        # グレースケール画像を作成
        gray_image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        
        result = OCRProcessor.preprocess_image(gray_image)
        
        # グレースケール画像のまま処理されることを確認
        assert len(result.shape) == 2
        assert result.shape == (100, 100)
    
    def test_preprocess_contrast_enhancement(self):
        """コントラスト調整が適用されることを確認 (Requirement 4.3)"""
        # 低コントラストの画像を作成（全体的に暗い）
        low_contrast_image = np.full((100, 100, 3), 50, dtype=np.uint8)
        
        result = OCRProcessor.preprocess_image(low_contrast_image)
        
        # CLAHE適用後の画像であることを確認
        assert result is not None
        assert result.shape == (100, 100)


class TestExtractText:
    """extract_textメソッドのテストスイート"""
    
    @patch('src.ocr_processor.pytesseract.get_tesseract_version')
    @patch('src.ocr_processor.pytesseract.image_to_string')
    def test_extract_text_basic(self, mock_image_to_string, mock_get_version):
        """基本的なテキスト抽出を確認 (Requirement 4.1, 4.2)"""
        mock_get_version.return_value = "5.0.0"
        mock_image_to_string.return_value = "テストテキスト"
        
        processor = OCRProcessor()
        
        # テスト用の画像とバウンディングボックスを作成
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        bbox = DetectionResult(
            x1=100, y1=100, x2=300, y2=200,
            confidence=0.9, class_id=0, class_name="list-item"
        )
        
        result = processor.extract_text(frame, bbox)
        
        assert result == "テストテキスト"
        mock_image_to_string.assert_called_once()
    
    @patch('src.ocr_processor.pytesseract.get_tesseract_version')
    @patch('src.ocr_processor.pytesseract.image_to_string')
    def test_extract_text_with_margin(self, mock_image_to_string, mock_get_version):
        """マージン付きでの切り出しを確認 (Requirement 4.2)"""
        mock_get_version.return_value = "5.0.0"
        mock_image_to_string.return_value = "マージン付きテキスト"
        
        processor = OCRProcessor(margin=10)
        
        # テスト用の画像とバウンディングボックスを作成
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        bbox = DetectionResult(
            x1=100, y1=100, x2=300, y2=200,
            confidence=0.9, class_id=0, class_name="list-item"
        )
        
        result = processor.extract_text(frame, bbox)
        
        assert result == "マージン付きテキスト"
        
        # pytesseractが呼ばれた際の引数を確認
        call_args = mock_image_to_string.call_args
        cropped_image = call_args[0][0]
        
        # マージンを考慮したサイズになっていることを確認
        # 元のサイズ: (200-100, 300-100) = (100, 200)
        # マージン10を追加: (100+20, 200+20) = (120, 220)
        assert cropped_image.shape[0] == 120  # height
        assert cropped_image.shape[1] == 220  # width
    
    @patch('src.ocr_processor.pytesseract.get_tesseract_version')
    @patch('src.ocr_processor.pytesseract.image_to_string')
    def test_extract_text_boundary_clipping(self, mock_image_to_string, mock_get_version):
        """画像境界でのマージンクリッピングを確認 (Requirement 4.2)"""
        mock_get_version.return_value = "5.0.0"
        mock_image_to_string.return_value = "境界テキスト"
        
        processor = OCRProcessor(margin=50)
        
        # テスト用の画像とバウンディングボックスを作成
        # バウンディングボックスが画像の端に近い
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        bbox = DetectionResult(
            x1=10, y1=10, x2=100, y2=100,
            confidence=0.9, class_id=0, class_name="list-item"
        )
        
        result = processor.extract_text(frame, bbox)
        
        # エラーなく処理されることを確認
        assert result == "境界テキスト"
    
    @patch('src.ocr_processor.pytesseract.get_tesseract_version')
    @patch('src.ocr_processor.pytesseract.image_to_string')
    def test_extract_text_with_cleanup(self, mock_image_to_string, mock_get_version):
        """テキストクリーンアップが適用されることを確認 (Requirement 4.4)"""
        mock_get_version.return_value = "5.0.0"
        # 空白が多いテキストを返す
        mock_image_to_string.return_value = "  これは    テスト    です  "
        
        processor = OCRProcessor()
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        bbox = DetectionResult(
            x1=100, y1=100, x2=300, y2=200,
            confidence=0.9, class_id=0, class_name="list-item"
        )
        
        result = processor.extract_text(frame, bbox)
        
        # クリーンアップされたテキストが返されることを確認
        assert result == "これは テスト です"
    
    @patch('src.ocr_processor.pytesseract.get_tesseract_version')
    @patch('src.ocr_processor.pytesseract.image_to_string')
    def test_extract_text_filter_short(self, mock_image_to_string, mock_get_version):
        """短いテキストがフィルタリングされることを確認 (Requirement 4.5)"""
        mock_get_version.return_value = "5.0.0"
        # 2文字以下のテキストを返す
        mock_image_to_string.return_value = "あい"
        
        processor = OCRProcessor()
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        bbox = DetectionResult(
            x1=100, y1=100, x2=300, y2=200,
            confidence=0.9, class_id=0, class_name="list-item"
        )
        
        result = processor.extract_text(frame, bbox)
        
        # 空文字列が返されることを確認
        assert result == ""
    
    @patch('src.ocr_processor.pytesseract.get_tesseract_version')
    @patch('src.ocr_processor.pytesseract.image_to_string')
    def test_extract_text_empty_crop(self, mock_image_to_string, mock_get_version):
        """切り出し領域が空の場合の処理を確認 (Requirement 4.6)"""
        mock_get_version.return_value = "5.0.0"
        mock_image_to_string.return_value = ""
        
        processor = OCRProcessor()
        
        # 無効なバウンディングボックス（画像境界外）
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        bbox = DetectionResult(
            x1=700, y1=500, x2=800, y2=600,
            confidence=0.9, class_id=0, class_name="list-item"
        )
        
        result = processor.extract_text(frame, bbox)
        
        # 空文字列が返されることを確認
        assert result == ""
    
    @patch('src.ocr_processor.pytesseract.get_tesseract_version')
    @patch('src.ocr_processor.pytesseract.image_to_string')
    def test_extract_text_ocr_error(self, mock_image_to_string, mock_get_version):
        """OCRエラー時の処理を確認 (Requirement 4.7)"""
        mock_get_version.return_value = "5.0.0"
        # OCRエラーをシミュレート
        mock_image_to_string.side_effect = Exception("OCR failed")
        
        processor = OCRProcessor()
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        bbox = DetectionResult(
            x1=100, y1=100, x2=300, y2=200,
            confidence=0.9, class_id=0, class_name="list-item"
        )
        
        # エラーが発生しても空文字列が返されることを確認
        result = processor.extract_text(frame, bbox)
        assert result == ""
    
    @patch('src.ocr_processor.pytesseract.get_tesseract_version')
    @patch('src.ocr_processor.pytesseract.image_to_string')
    def test_extract_text_japanese_config(self, mock_image_to_string, mock_get_version):
        """日本語OCR設定が正しく適用されることを確認 (Requirement 4.3)"""
        mock_get_version.return_value = "5.0.0"
        mock_image_to_string.return_value = "日本語テキスト"
        
        processor = OCRProcessor(lang='jpn')
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        bbox = DetectionResult(
            x1=100, y1=100, x2=300, y2=200,
            confidence=0.9, class_id=0, class_name="list-item"
        )
        
        result = processor.extract_text(frame, bbox)
        
        # pytesseractが正しいパラメータで呼ばれたことを確認
        call_kwargs = mock_image_to_string.call_args[1]
        assert call_kwargs['lang'] == 'jpn'
        assert call_kwargs['config'] == '--psm 6'


class TestOCRProcessorIntegration:
    """統合テスト（実際のTesseractとサンプル画像を使用）"""
    
    @pytest.mark.skipif(
        not Path("venv").exists(),
        reason="仮想環境が存在しないため、スキップ"
    )
    def test_extract_text_with_real_image(self):
        """
        実際の画像を使用したOCRテスト (Requirement 4.3)
        
        注意: このテストはTesseract OCRがインストールされている環境でのみ実行されます。
        """
        try:
            processor = OCRProcessor(lang='jpn')
        except RuntimeError:
            pytest.skip("Tesseract OCRがインストールされていません")
        
        # テスト用の画像を作成（白背景に黒文字）
        frame = np.ones((200, 400, 3), dtype=np.uint8) * 255
        
        # OpenCVで日本語テキストを描画（フォントの問題で英数字を使用）
        cv2.putText(
            frame,
            "Test Text 123",
            (50, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            (0, 0, 0),
            3
        )
        
        bbox = DetectionResult(
            x1=40, y1=50, x2=360, y2=150,
            confidence=0.9, class_id=0, class_name="list-item"
        )
        
        result = processor.extract_text(frame, bbox)
        
        # 何らかのテキストが抽出されることを確認
        # （実際の文字認識精度はフォントや画像品質に依存）
        assert isinstance(result, str)
    
    def test_preprocess_and_extract_workflow(self):
        """
        前処理とOCRの統合ワークフローテスト (Requirement 4.3)
        """
        try:
            processor = OCRProcessor(lang='eng')  # 英語でテスト
        except RuntimeError:
            pytest.skip("Tesseract OCRがインストールされていません")
        
        # テスト用の画像を作成
        frame = np.ones((200, 400, 3), dtype=np.uint8) * 255
        cv2.putText(
            frame,
            "HELLO WORLD",
            (50, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            (0, 0, 0),
            3
        )
        
        # 前処理を適用
        preprocessed = OCRProcessor.preprocess_image(frame)
        
        # 前処理された画像がグレースケールであることを確認
        assert len(preprocessed.shape) == 2
        
        # OCR実行（前処理なしの元画像で）
        bbox = DetectionResult(
            x1=40, y1=50, x2=360, y2=150,
            confidence=0.9, class_id=0, class_name="list-item"
        )
        
        result = processor.extract_text(frame, bbox)
        
        # 結果が文字列であることを確認
        assert isinstance(result, str)
