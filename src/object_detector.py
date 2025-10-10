"""
YOLOv8を使用した物体検出モジュール

このモジュールは、学習済みYOLOv8モデルを使用してリスト項目を検出します。
Apple Silicon MPS対応で最適化されています。
"""

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
import numpy as np
import torch
from ultralytics import YOLO


@dataclass
class DetectionResult:
    """
    物体検出結果を表すデータクラス
    
    Attributes:
        x1: バウンディングボックスの左上X座標
        y1: バウンディングボックスの左上Y座標
        x2: バウンディングボックスの右下X座標
        y2: バウンディングボックスの右下Y座標
        confidence: 検出の信頼度 (0.0-1.0)
        class_id: クラスID
        class_name: クラス名
    """
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    class_id: int
    class_name: str


class ObjectDetector:
    """
    YOLOv8ベースの物体検出クラス
    
    学習済みYOLOv8モデルを使用してフレーム内のlist-itemを検出します。
    Apple Silicon環境ではMPS（Metal Performance Shaders）を活用して高速化します。
    """
    
    def __init__(self, model_path: str, confidence_threshold: float = 0.6):
        """
        ObjectDetectorを初期化
        
        Args:
            model_path: YOLOv8モデルファイル（best.pt）のパス
            confidence_threshold: 検出の信頼度しきい値（デフォルト: 0.6）
        
        Raises:
            FileNotFoundError: モデルファイルが存在しない場合
            RuntimeError: モデルのロードに失敗した場合
        """
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        
        # モデルファイルの存在チェック
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"モデルファイルが見つかりません: {self.model_path}\n"
                f"YOLOv8モデル（best.pt）を {self.model_path} に配置してください。"
            )
        
        # YOLOv8モデルのロード
        try:
            self.model = YOLO(str(self.model_path))
            
            # Apple Silicon MPS対応
            if torch.backends.mps.is_available():
                self.device = "mps"
                print("Apple Silicon MPS を使用します")
            elif torch.cuda.is_available():
                self.device = "cuda"
                print("CUDA を使用します")
            else:
                self.device = "cpu"
                print("CPU を使用します")
            
            # モデルをデバイスに転送
            self.model.to(self.device)
            print(f"YOLOv8モデルをロードしました: {self.model_path}")
            
        except Exception as e:
            raise RuntimeError(f"モデルのロードに失敗しました: {e}")
    
    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        """
        フレーム内の物体を検出
        
        Args:
            frame: 入力画像（BGR形式のnumpy配列）
        
        Returns:
            検出結果のリスト（座標、信頼度、クラス情報を含む）
        """
        if self.model is None:
            raise RuntimeError("モデルが初期化されていません")
        
        # YOLOv8で推論実行（verbose=Falseで出力を抑制）
        results = self.model(frame, verbose=False, device=self.device)
        
        detections = []
        
        # 検出結果を処理
        for result in results:
            boxes = result.boxes
            
            for box in boxes:
                # 信頼度フィルタリング
                confidence = float(box.conf[0])
                if confidence < self.confidence_threshold:
                    continue
                
                # バウンディングボックスの座標を取得
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                
                # クラス情報を取得
                class_id = int(box.cls[0])
                class_name = result.names[class_id]
                
                # DetectionResultオブジェクトを作成
                detection = DetectionResult(
                    x1=int(x1),
                    y1=int(y1),
                    x2=int(x2),
                    y2=int(y2),
                    confidence=confidence,
                    class_id=class_id,
                    class_name=class_name
                )
                
                detections.append(detection)
        
        return detections
    
    @staticmethod
    def sort_by_y_coordinate(detections: List[DetectionResult]) -> List[DetectionResult]:
        """
        検出結果をY座標でソート（上から下）
        
        Args:
            detections: 検出結果のリスト
        
        Returns:
            Y座標（y1）でソートされた検出結果のリスト
        """
        return sorted(detections, key=lambda d: d.y1)
