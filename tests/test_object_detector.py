"""
ObjectDetectorモジュールのテストコード

Requirements: 2.3, 2.4, 2.5
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.object_detector import ObjectDetector, DetectionResult


class TestDetectionResult:
    """DetectionResultデータクラスのテストスイート"""
    
    def test_detection_result_creation(self):
        """DetectionResultが正しく作成されることを確認"""
        detection = DetectionResult(
            x1=100,
            y1=200,
            x2=300,
            y2=400,
            confidence=0.85,
            class_id=0,
            class_name="list-item"
        )
        
        assert detection.x1 == 100
        assert detection.y1 == 200
        assert detection.x2 == 300
        assert detection.y2 == 400
        assert detection.confidence == 0.85
        assert detection.class_id == 0
        assert detection.class_name == "list-item"


class TestObjectDetector:
    """ObjectDetectorクラスのテストスイート"""
    
    def test_init_model_not_found(self):
        """モデルファイルが存在しない場合にエラーが発生することを確認 (Requirement 2.2)"""
        non_existent_path = "models/non_existent_model.pt"
        
        with pytest.raises(FileNotFoundError) as exc_info:
            ObjectDetector(non_existent_path)
        
        error_message = str(exc_info.value)
        assert "モデルファイルが見つかりません" in error_message
        assert non_existent_path in error_message
    
    @patch('src.object_detector.YOLO')
    @patch('src.object_detector.torch')
    @patch('src.object_detector.Path.exists')
    def test_init_success_with_mps(self, mock_exists, mock_torch, mock_yolo):
        """Apple Silicon MPS環境での初期化が成功することを確認 (Requirement 2.1)"""
        # モックの設定
        mock_exists.return_value = True
        mock_torch.backends.mps.is_available.return_value = True
        mock_torch.cuda.is_available.return_value = False
        
        mock_model = MagicMock()
        mock_yolo.return_value = mock_model
        
        # ObjectDetectorを初期化
        detector = ObjectDetector("models/best.pt", confidence_threshold=0.7)
        
        # 正しく初期化されたことを確認
        assert detector.confidence_threshold == 0.7
        assert detector.device == "mps"
        mock_model.to.assert_called_once_with("mps")
    
    @patch('src.object_detector.YOLO')
    @patch('src.object_detector.torch')
    @patch('src.object_detector.Path.exists')
    def test_init_success_with_cpu(self, mock_exists, mock_torch, mock_yolo):
        """CPU環境での初期化が成功することを確認 (Requirement 2.1)"""
        # モックの設定
        mock_exists.return_value = True
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = False
        
        mock_model = MagicMock()
        mock_yolo.return_value = mock_model
        
        # ObjectDetectorを初期化
        detector = ObjectDetector("models/best.pt")
        
        # CPUデバイスが選択されたことを確認
        assert detector.device == "cpu"
        mock_model.to.assert_called_once_with("cpu")
    
    @patch('src.object_detector.YOLO')
    @patch('src.object_detector.torch')
    @patch('src.object_detector.Path.exists')
    def test_detect_with_confidence_filtering(self, mock_exists, mock_torch, mock_yolo):
        """信頼度フィルタリングが正しく動作することを確認 (Requirement 2.4)"""
        # モックの設定
        mock_exists.return_value = True
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = False
        
        # YOLOモデルのモック
        mock_model = MagicMock()
        mock_yolo.return_value = mock_model
        
        # 検出結果のモック（信頼度が異なる3つの検出）
        mock_box1 = MagicMock()
        mock_box1.conf = [0.85]  # しきい値以上
        mock_xyxy1 = MagicMock()
        mock_xyxy1.cpu.return_value.numpy.return_value = np.array([100, 200, 300, 400])
        mock_box1.xyxy = [mock_xyxy1]
        mock_box1.cls = [0]
        
        mock_box2 = MagicMock()
        mock_box2.conf = [0.45]  # しきい値以下（除外される）
        mock_xyxy2 = MagicMock()
        mock_xyxy2.cpu.return_value.numpy.return_value = np.array([150, 250, 350, 450])
        mock_box2.xyxy = [mock_xyxy2]
        mock_box2.cls = [0]
        
        mock_box3 = MagicMock()
        mock_box3.conf = [0.72]  # しきい値以上
        mock_xyxy3 = MagicMock()
        mock_xyxy3.cpu.return_value.numpy.return_value = np.array([200, 300, 400, 500])
        mock_box3.xyxy = [mock_xyxy3]
        mock_box3.cls = [0]
        
        mock_result = MagicMock()
        mock_result.boxes = [mock_box1, mock_box2, mock_box3]
        mock_result.names = {0: "list-item"}
        
        mock_model.return_value = [mock_result]
        
        # ObjectDetectorを初期化（しきい値0.6）
        detector = ObjectDetector("models/best.pt", confidence_threshold=0.6)
        
        # ダミー画像で検出を実行
        frame = np.zeros((640, 480, 3), dtype=np.uint8)
        detections = detector.detect(frame)
        
        # しきい値以上の2つのみが検出されることを確認
        assert len(detections) == 2
        assert detections[0].confidence == 0.85
        assert detections[1].confidence == 0.72
    
    @patch('src.object_detector.YOLO')
    @patch('src.object_detector.torch')
    @patch('src.object_detector.Path.exists')
    def test_detect_returns_correct_format(self, mock_exists, mock_torch, mock_yolo):
        """検出結果が正しいフォーマットで返されることを確認 (Requirement 2.3)"""
        # モックの設定
        mock_exists.return_value = True
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = False
        
        # YOLOモデルのモック
        mock_model = MagicMock()
        mock_yolo.return_value = mock_model
        
        # 検出結果のモック
        mock_box = MagicMock()
        mock_box.conf = [0.92]
        mock_xyxy = MagicMock()
        mock_xyxy.cpu.return_value.numpy.return_value = np.array([50.5, 100.7, 250.3, 400.9])
        mock_box.xyxy = [mock_xyxy]
        mock_box.cls = [0]
        
        mock_result = MagicMock()
        mock_result.boxes = [mock_box]
        mock_result.names = {0: "list-item"}
        
        mock_model.return_value = [mock_result]
        
        # ObjectDetectorを初期化
        detector = ObjectDetector("models/best.pt")
        
        # ダミー画像で検出を実行
        frame = np.zeros((640, 480, 3), dtype=np.uint8)
        detections = detector.detect(frame)
        
        # 検出結果の形式を確認
        assert len(detections) == 1
        detection = detections[0]
        
        assert isinstance(detection, DetectionResult)
        assert detection.x1 == 50  # int型に変換されている
        assert detection.y1 == 100
        assert detection.x2 == 250
        assert detection.y2 == 400
        assert detection.confidence == 0.92
        assert detection.class_id == 0
        assert detection.class_name == "list-item"
    
    @patch('src.object_detector.YOLO')
    @patch('src.object_detector.torch')
    @patch('src.object_detector.Path.exists')
    def test_detect_empty_result(self, mock_exists, mock_torch, mock_yolo):
        """検出結果が空の場合の処理を確認 (Requirement 2.3)"""
        # モックの設定
        mock_exists.return_value = True
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = False
        
        # YOLOモデルのモック（検出なし）
        mock_model = MagicMock()
        mock_yolo.return_value = mock_model
        
        mock_result = MagicMock()
        mock_result.boxes = []
        
        mock_model.return_value = [mock_result]
        
        # ObjectDetectorを初期化
        detector = ObjectDetector("models/best.pt")
        
        # ダミー画像で検出を実行
        frame = np.zeros((640, 480, 3), dtype=np.uint8)
        detections = detector.detect(frame)
        
        # 空のリストが返されることを確認
        assert detections == []
    
    def test_sort_by_y_coordinate_ascending(self):
        """Y座標で昇順にソートされることを確認 (Requirement 2.5)"""
        # ソート前の検出結果（Y座標がバラバラ）
        detections = [
            DetectionResult(100, 300, 200, 400, 0.9, 0, "list-item"),  # y1=300
            DetectionResult(100, 100, 200, 200, 0.8, 0, "list-item"),  # y1=100
            DetectionResult(100, 500, 200, 600, 0.85, 0, "list-item"), # y1=500
            DetectionResult(100, 200, 200, 300, 0.95, 0, "list-item"), # y1=200
        ]
        
        # ソート実行
        sorted_detections = ObjectDetector.sort_by_y_coordinate(detections)
        
        # Y座標で昇順にソートされていることを確認
        assert len(sorted_detections) == 4
        assert sorted_detections[0].y1 == 100
        assert sorted_detections[1].y1 == 200
        assert sorted_detections[2].y1 == 300
        assert sorted_detections[3].y1 == 500
    
    def test_sort_by_y_coordinate_empty_list(self):
        """空のリストをソートしても問題ないことを確認 (Requirement 2.5)"""
        detections = []
        sorted_detections = ObjectDetector.sort_by_y_coordinate(detections)
        
        assert sorted_detections == []
    
    def test_sort_by_y_coordinate_single_item(self):
        """1つの要素のリストをソートしても問題ないことを確認 (Requirement 2.5)"""
        detections = [
            DetectionResult(100, 200, 300, 400, 0.9, 0, "list-item")
        ]
        
        sorted_detections = ObjectDetector.sort_by_y_coordinate(detections)
        
        assert len(sorted_detections) == 1
        assert sorted_detections[0].y1 == 200
    
    def test_sort_by_y_coordinate_same_y(self):
        """同じY座標の要素が含まれる場合の処理を確認 (Requirement 2.5)"""
        detections = [
            DetectionResult(100, 200, 200, 300, 0.9, 0, "list-item"),
            DetectionResult(300, 200, 400, 300, 0.8, 0, "list-item"),
            DetectionResult(500, 100, 600, 200, 0.85, 0, "list-item"),
        ]
        
        sorted_detections = ObjectDetector.sort_by_y_coordinate(detections)
        
        # Y座標でソートされていることを確認
        assert sorted_detections[0].y1 == 100
        assert sorted_detections[1].y1 == 200
        assert sorted_detections[2].y1 == 200
    
    def test_sort_by_y_coordinate_preserves_data(self):
        """ソート後も元のデータが保持されることを確認 (Requirement 2.5)"""
        detections = [
            DetectionResult(100, 300, 200, 400, 0.9, 0, "list-item"),
            DetectionResult(150, 100, 250, 200, 0.8, 0, "list-item"),
        ]
        
        sorted_detections = ObjectDetector.sort_by_y_coordinate(detections)
        
        # 最初の要素（y1=100）のデータを確認
        assert sorted_detections[0].x1 == 150
        assert sorted_detections[0].x2 == 250
        assert sorted_detections[0].confidence == 0.8
        
        # 2番目の要素（y1=300）のデータを確認
        assert sorted_detections[1].x1 == 100
        assert sorted_detections[1].x2 == 200
        assert sorted_detections[1].confidence == 0.9


class TestObjectDetectorIntegration:
    """統合テスト（実際のモデルとサンプル画像を使用）"""
    
    @pytest.mark.skipif(
        not Path("models/best.pt").exists(),
        reason="YOLOv8モデルファイル（models/best.pt）が存在しないため、スキップ"
    )
    def test_detect_with_real_model_and_sample_image(self):
        """
        実際のYOLOv8モデルとサンプル画像を使用した検出テスト (Requirement 2.3)
        
        注意: このテストは models/best.pt が存在する環境でのみ実行されます。
        """
        # ObjectDetectorを初期化
        detector = ObjectDetector("models/best.pt", confidence_threshold=0.5)
        
        # サンプル画像を作成（実際のテストでは実画像を使用）
        # 640x480のダミー画像
        sample_image = np.random.randint(0, 255, (640, 480, 3), dtype=np.uint8)
        
        # 検出を実行
        detections = detector.detect(sample_image)
        
        # 検出結果の型を確認
        assert isinstance(detections, list)
        
        # 検出があった場合、各要素がDetectionResultであることを確認
        for detection in detections:
            assert isinstance(detection, DetectionResult)
            assert 0 <= detection.confidence <= 1.0
            assert detection.x1 < detection.x2
            assert detection.y1 < detection.y2
    
    @pytest.mark.skipif(
        not Path("models/best.pt").exists() or not Path("temp/shosetsu-list-item/obj_train_data").exists(),
        reason="モデルファイルまたはトレーニング画像が存在しないため、スキップ"
    )
    def test_detect_with_training_images(self):
        """
        トレーニング画像を使用した検出テスト (Requirement 2.3, 2.4)
        
        注意: このテストは実際のトレーニング画像が存在する環境でのみ実行されます。
        """
        import cv2
        
        # ObjectDetectorを初期化
        detector = ObjectDetector("models/best.pt", confidence_threshold=0.6)
        
        # トレーニング画像ディレクトリから画像を読み込み
        train_dir = Path("temp/shosetsu-list-item/obj_train_data")
        image_files = list(train_dir.glob("*.jpg")) + list(train_dir.glob("*.png"))
        
        if not image_files:
            pytest.skip("トレーニング画像が見つかりません")
        
        # 最初の画像でテスト
        test_image_path = image_files[0]
        frame = cv2.imread(str(test_image_path))
        
        assert frame is not None, f"画像の読み込みに失敗: {test_image_path}"
        
        # 検出を実行
        detections = detector.detect(frame)
        
        # 検出結果を確認
        assert isinstance(detections, list)
        
        # 検出があった場合、信頼度がしきい値以上であることを確認
        for detection in detections:
            assert detection.confidence >= 0.6
            assert detection.class_name == "list-item"
            
            # バウンディングボックスが画像内に収まっていることを確認
            height, width = frame.shape[:2]
            assert 0 <= detection.x1 < width
            assert 0 <= detection.y1 < height
            assert 0 < detection.x2 <= width
            assert 0 < detection.y2 <= height
