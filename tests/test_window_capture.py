"""
WindowCaptureモジュールのテストコード

Requirements: 1.1, 1.2, 1.3
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.window_capture import WindowCapture


class TestWindowCapture:
    """WindowCaptureクラスのテストスイート"""
    
    def test_init(self):
        """初期化が正しく行われることを確認"""
        window_title = "TestWindow"
        capture = WindowCapture(window_title)
        
        assert capture.window_title == window_title
        assert capture.window_info is None
        assert capture.sct is not None
    
    @patch('src.window_capture.CGWindowListCopyWindowInfo')
    def test_list_all_windows_success(self, mock_cg_window):
        """全ウィンドウのリスト取得が成功することを確認 (Requirement 1.1)"""
        # モックデータの準備
        mock_cg_window.return_value = [
            {
                'kCGWindowName': 'Window 1',
                'kCGWindowOwnerName': 'App1'
            },
            {
                'kCGWindowName': 'Window 2',
                'kCGWindowOwnerName': 'App2'
            },
            {
                'kCGWindowName': '',  # 空のタイトル（除外される）
                'kCGWindowOwnerName': 'App3'
            },
            {
                'kCGWindowName': 'Window 1',  # 重複（1つにまとめられる）
                'kCGWindowOwnerName': 'App1'
            }
        ]
        
        windows = WindowCapture.list_all_windows()
        
        # 空のタイトルと重複が除外され、ソートされていることを確認
        assert len(windows) == 2
        assert 'Window 1 (App1)' in windows
        assert 'Window 2 (App2)' in windows
    
    @patch('src.window_capture.CGWindowListCopyWindowInfo')
    def test_list_all_windows_empty(self, mock_cg_window):
        """ウィンドウが存在しない場合の処理を確認"""
        mock_cg_window.return_value = []
        
        windows = WindowCapture.list_all_windows()
        
        assert windows == []
    
    @patch('src.window_capture.CGWindowListCopyWindowInfo')
    def test_find_window_success(self, mock_cg_window):
        """ウィンドウ検索が成功することを確認 (Requirement 1.1)"""
        # モックデータの準備
        mock_cg_window.return_value = [
            {
                'kCGWindowName': 'iPhone 15 Pro',
                'kCGWindowOwnerName': 'Simulator',
                'kCGWindowBounds': {
                    'X': 100,
                    'Y': 200,
                    'Width': 400,
                    'Height': 800
                }
            }
        ]
        
        capture = WindowCapture("iPhone")
        window_info = capture.find_window()
        
        # ウィンドウ情報が正しく取得されることを確認
        assert window_info is not None
        assert window_info['x'] == 100
        assert window_info['y'] == 200
        assert window_info['width'] == 400
        assert window_info['height'] == 800
        assert window_info['title'] == 'iPhone 15 Pro'
        assert window_info['owner'] == 'Simulator'
        
        # インスタンス変数にも保存されていることを確認
        assert capture.window_info == window_info
    
    @patch('src.window_capture.CGWindowListCopyWindowInfo')
    def test_find_window_case_insensitive(self, mock_cg_window):
        """ウィンドウ検索が大文字小文字を区別しないことを確認 (Requirement 1.1)"""
        mock_cg_window.return_value = [
            {
                'kCGWindowName': 'iPhone 15 Pro',
                'kCGWindowOwnerName': 'Simulator',
                'kCGWindowBounds': {
                    'X': 100,
                    'Y': 200,
                    'Width': 400,
                    'Height': 800
                }
            }
        ]
        
        # 小文字で検索
        capture = WindowCapture("iphone")
        window_info = capture.find_window()
        
        assert window_info is not None
        assert window_info['title'] == 'iPhone 15 Pro'
    
    @patch('src.window_capture.CGWindowListCopyWindowInfo')
    def test_find_window_partial_match(self, mock_cg_window):
        """ウィンドウ検索が部分一致で動作することを確認 (Requirement 1.1)"""
        mock_cg_window.return_value = [
            {
                'kCGWindowName': 'iPhone 15 Pro - iOS 17.0',
                'kCGWindowOwnerName': 'Simulator',
                'kCGWindowBounds': {
                    'X': 100,
                    'Y': 200,
                    'Width': 400,
                    'Height': 800
                }
            }
        ]
        
        # 部分一致で検索
        capture = WindowCapture("iPhone 15")
        window_info = capture.find_window()
        
        assert window_info is not None
        assert 'iPhone 15 Pro' in window_info['title']
    
    @patch('src.window_capture.CGWindowListCopyWindowInfo')
    def test_find_window_not_found(self, mock_cg_window):
        """ウィンドウが見つからない場合のエラー処理を確認 (Requirement 1.2)"""
        mock_cg_window.return_value = [
            {
                'kCGWindowName': 'Other Window',
                'kCGWindowOwnerName': 'OtherApp',
                'kCGWindowBounds': {
                    'X': 0,
                    'Y': 0,
                    'Width': 100,
                    'Height': 100
                }
            }
        ]
        
        capture = WindowCapture("NonExistentWindow")
        
        # RuntimeErrorが発生することを確認
        with pytest.raises(RuntimeError) as exc_info:
            capture.find_window()
        
        # エラーメッセージに利用可能なウィンドウリストが含まれることを確認
        error_message = str(exc_info.value)
        assert "NonExistentWindow" in error_message
        assert "利用可能なウィンドウ" in error_message
        assert "Other Window" in error_message
    
    @patch('src.window_capture.mss.mss')
    def test_capture_frame_success(self, mock_mss_class):
        """フレームキャプチャが成功することを確認 (Requirement 1.3)"""
        # モックの設定
        mock_sct = MagicMock()
        mock_mss_class.return_value = mock_sct
        
        # モックスクリーンショットデータ（BGRA形式）
        mock_screenshot = MagicMock()
        mock_screenshot.__array__ = lambda: np.zeros((800, 400, 4), dtype=np.uint8)
        mock_sct.grab.return_value = mock_screenshot
        
        # WindowCaptureインスタンスを作成
        capture = WindowCapture("TestWindow")
        
        # ウィンドウ情報を手動で設定
        capture.window_info = {
            'x': 100,
            'y': 200,
            'width': 400,
            'height': 800,
            'title': 'TestWindow',
            'owner': 'TestApp'
        }
        
        # フレームをキャプチャ
        frame = capture.capture_frame()
        
        # 正しい座標でgrabが呼ばれたことを確認
        mock_sct.grab.assert_called_once()
        call_args = mock_sct.grab.call_args[0][0]
        assert call_args['left'] == 100
        assert call_args['top'] == 200
        assert call_args['width'] == 400
        assert call_args['height'] == 800
        
        # BGR形式（3チャンネル）に変換されていることを確認
        assert frame.shape == (800, 400, 3)
        assert frame.dtype == np.uint8
    
    def test_capture_frame_without_window_info(self):
        """ウィンドウ情報なしでキャプチャするとエラーになることを確認"""
        capture = WindowCapture("TestWindow")
        
        # window_infoが設定されていない状態でcapture_frameを呼ぶ
        with pytest.raises(RuntimeError) as exc_info:
            capture.capture_frame()
        
        error_message = str(exc_info.value)
        assert "ウィンドウ情報が設定されていません" in error_message
        assert "find_window()" in error_message
    
    @patch('src.window_capture.mss.mss')
    def test_bgra_to_bgr_conversion(self, mock_mss_class):
        """BGRA→BGR変換が正しく行われることを確認 (Requirement 1.3)"""
        # モックの設定
        mock_sct = MagicMock()
        mock_mss_class.return_value = mock_sct
        
        # BGRAデータを作成（B=100, G=150, R=200, A=255）
        bgra_data = np.zeros((100, 100, 4), dtype=np.uint8)
        bgra_data[:, :, 0] = 100  # B
        bgra_data[:, :, 1] = 150  # G
        bgra_data[:, :, 2] = 200  # R
        bgra_data[:, :, 3] = 255  # A
        
        mock_screenshot = MagicMock()
        mock_screenshot.__array__ = lambda: bgra_data
        mock_sct.grab.return_value = mock_screenshot
        
        capture = WindowCapture("TestWindow")
        capture.window_info = {
            'x': 0,
            'y': 0,
            'width': 100,
            'height': 100,
            'title': 'TestWindow',
            'owner': 'TestApp'
        }
        
        frame = capture.capture_frame()
        
        # BGRの3チャンネルのみが残っていることを確認
        assert frame.shape == (100, 100, 3)
        
        # 色の値が正しく保持されていることを確認
        assert np.all(frame[:, :, 0] == 100)  # B
        assert np.all(frame[:, :, 1] == 150)  # G
        assert np.all(frame[:, :, 2] == 200)  # R
    
    @patch('src.window_capture.mss.mss')
    def test_destructor_cleanup(self, mock_mss_class):
        """デストラクタでリソースがクリーンアップされることを確認"""
        mock_sct = MagicMock()
        mock_mss_class.return_value = mock_sct
        
        capture = WindowCapture("TestWindow")
        
        # デストラクタを明示的に呼び出し
        capture.__del__()
        
        # closeが呼ばれたことを確認
        mock_sct.close.assert_called_once()


class TestWindowCaptureIntegration:
    """統合テスト（実際のシステムとの連携が必要な場合）"""
    
    @pytest.mark.skip(reason="実際のウィンドウが必要なため、手動テストで実行")
    def test_real_window_capture(self):
        """
        実際のウィンドウでのキャプチャテスト
        
        注意: このテストは実際にiPhoneシミュレータなどのウィンドウが
        起動している環境でのみ実行可能です。
        """
        capture = WindowCapture("iPhone")
        
        # ウィンドウを検索
        window_info = capture.find_window()
        assert window_info is not None
        
        # フレームをキャプチャ
        frame = capture.capture_frame()
        assert frame is not None
        assert len(frame.shape) == 3
        assert frame.shape[2] == 3  # BGR
