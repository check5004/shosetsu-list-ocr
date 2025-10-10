"""
Visualizerモジュールのテスト
"""

import pytest
import numpy as np
import cv2
from src.visualizer import Visualizer
from src.object_detector import DetectionResult


class TestVisualizer:
    """Visualizerクラスのテスト"""
    
    def test_init(self):
        """初期化のテスト"""
        visualizer = Visualizer()
        assert visualizer.window_name == "Real-time Detection"
        assert visualizer._window_created is False
        
        # カスタムウィンドウ名
        custom_visualizer = Visualizer(window_name="Custom Window")
        assert custom_visualizer.window_name == "Custom Window"
    
    def test_draw_detections_empty(self):
        """検出結果が空の場合の描画テスト"""
        visualizer = Visualizer()
        
        # テスト用のダミー画像を作成
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 検出結果なしで描画
        result = visualizer.draw_detections(frame, [])
        
        # 元画像と同じサイズであることを確認
        assert result.shape == frame.shape
        
        # 元画像が変更されていないことを確認
        assert np.array_equal(frame, np.zeros((480, 640, 3), dtype=np.uint8))
    
    def test_draw_detections_single(self):
        """単一の検出結果の描画テスト"""
        visualizer = Visualizer()
        
        # テスト用のダミー画像を作成
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # テスト用の検出結果を作成
        detection = DetectionResult(
            x1=100,
            y1=100,
            x2=200,
            y2=200,
            confidence=0.95,
            class_id=0,
            class_name="list-item"
        )
        
        # 描画を実行
        result = visualizer.draw_detections(frame, [detection])
        
        # 結果が元画像と異なることを確認（描画されている）
        assert not np.array_equal(result, frame)
        
        # 元画像が変更されていないことを確認
        assert np.array_equal(frame, np.zeros((480, 640, 3), dtype=np.uint8))
        
        # バウンディングボックスの位置に緑色のピクセルがあることを確認
        # 矩形の左上の線上のピクセルをチェック
        assert result[100, 100, 1] > 0  # 緑チャンネル
    
    def test_draw_detections_multiple(self):
        """複数の検出結果の描画テスト"""
        visualizer = Visualizer()
        
        # テスト用のダミー画像を作成
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # テスト用の検出結果を複数作成
        detections = [
            DetectionResult(
                x1=50,
                y1=50,
                x2=150,
                y2=150,
                confidence=0.95,
                class_id=0,
                class_name="list-item"
            ),
            DetectionResult(
                x1=200,
                y1=200,
                x2=300,
                y2=300,
                confidence=0.85,
                class_id=0,
                class_name="list-item"
            ),
        ]
        
        # 描画を実行
        result = visualizer.draw_detections(frame, detections)
        
        # 結果が元画像と異なることを確認
        assert not np.array_equal(result, frame)
        
        # 両方のバウンディングボックスが描画されていることを確認
        assert result[50, 50, 1] > 0  # 1つ目の矩形
        assert result[200, 200, 1] > 0  # 2つ目の矩形
    
    def test_cleanup(self):
        """クリーンアップのテスト"""
        visualizer = Visualizer()
        
        # クリーンアップを実行
        visualizer.cleanup()
        
        # ウィンドウが作成されていない状態に戻ることを確認
        assert visualizer._window_created is False
    
    def test_show_frame_returns_true_by_default(self):
        """show_frameがデフォルトでTrueを返すことのテスト"""
        visualizer = Visualizer()
        
        # テスト用のダミー画像を作成
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # show_frameを呼び出し（実際にはウィンドウは表示されない環境でテスト）
        # 注: CI環境ではディスプレイがないため、このテストは環境依存
        try:
            result = visualizer.show_frame(frame)
            # キー入力がない場合はTrueを返すはず
            assert result is True
        except cv2.error:
            # ディスプレイがない環境ではスキップ
            pytest.skip("No display available for testing")
        finally:
            visualizer.cleanup()
