"""
可視化モジュール

このモジュールは、検出結果のリアルタイム表示を担当します。
OpenCVを使用してバウンディングボックスを描画し、ウィンドウに表示します。
"""

from typing import List, TYPE_CHECKING
import numpy as np
import cv2
from src.object_detector import DetectionResult

if TYPE_CHECKING:
    from src.hierarchical_detector import HierarchicalDetectionResult


class Visualizer:
    """
    検出結果の描画とウィンドウ表示を担当するクラス
    
    OpenCVを使用して検出されたバウンディングボックスを描画し、
    リアルタイムでウィンドウに表示します。
    """
    
    def __init__(self, window_name: str = "Real-time Detection"):
        """
        Visualizerを初期化
        
        Args:
            window_name: 表示ウィンドウの名前（デフォルト: "Real-time Detection"）
        """
        self.window_name = window_name
        self._window_created = False
    
    def draw_detections(self, frame: np.ndarray, detections: List[DetectionResult]) -> np.ndarray:
        """
        フレームに検出結果を描画
        
        Args:
            frame: 元画像（BGR形式のnumpy配列）
            detections: 検出結果のリスト
        
        Returns:
            描画済みの画像（元画像のコピー）
        """
        # 元画像を変更しないようにコピーを作成
        annotated_frame = frame.copy()
        
        # 各検出結果に対してバウンディングボックスを描画
        for detection in detections:
            # 緑色の矩形を描画（BGR形式: (0, 255, 0)）
            cv2.rectangle(
                annotated_frame,
                (detection.x1, detection.y1),
                (detection.x2, detection.y2),
                color=(0, 255, 0),
                thickness=2
            )
            
            # 信頼度とクラス名をラベルとして表示（オプション）
            label = f"{detection.class_name}: {detection.confidence:.2f}"
            
            # ラベルの背景を描画
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            label_y = detection.y1 - 10 if detection.y1 - 10 > 10 else detection.y1 + 20
            
            cv2.rectangle(
                annotated_frame,
                (detection.x1, label_y - label_size[1] - 5),
                (detection.x1 + label_size[0], label_y + 5),
                color=(0, 255, 0),
                thickness=-1  # 塗りつぶし
            )
            
            # ラベルテキストを描画
            cv2.putText(
                annotated_frame,
                label,
                (detection.x1, label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),  # 黒色のテキスト
                1,
                cv2.LINE_AA
            )
        
        return annotated_frame
    
    def show_frame(self, frame: np.ndarray) -> bool:
        """
        フレームを表示し、キー入力をチェック
        
        Args:
            frame: 表示する画像（BGR形式のnumpy配列）
        
        Returns:
            継続する場合True、'q'キーが押された場合False
        """
        # ウィンドウを作成（初回のみ）
        if not self._window_created:
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            self._window_created = True
        
        # フレームを表示
        cv2.imshow(self.window_name, frame)
        
        # キー入力をチェック（1ms待機）
        key = cv2.waitKey(1) & 0xFF
        
        # 'q'キーが押された場合はFalseを返す
        if key == ord('q'):
            return False
        
        return True
    
    def cleanup(self) -> None:
        """
        ウィンドウをクローズしてリソースを解放
        """
        cv2.destroyAllWindows()
        self._window_created = False
    
    def close(self) -> None:
        """
        ウィンドウをクローズ（cleanupのエイリアス）
        """
        self.cleanup()
    
    def draw_hierarchical_detections(
        self, 
        frame: np.ndarray, 
        hierarchical_results: List['HierarchicalDetectionResult']
    ) -> np.ndarray:
        """
        階層的検出結果をフレームに描画
        
        5つのクラス（list-item, title, progress, last_read_date, site_name）を
        異なる色で描画し、各クラスのラベルを表示します。
        
        Args:
            frame: 元画像（BGR形式のnumpy配列）
            hierarchical_results: 階層的検出結果のリスト
        
        Returns:
            描画済みの画像（元画像のコピー）
        """
        # 元画像を変更しないようにコピーを作成
        annotated_frame = frame.copy()
        
        # クラスごとの色を定義（BGR形式）
        class_colors = {
            'list-item': (0, 255, 0),      # 緑
            'title': (255, 0, 0),           # 青
            'progress': (0, 255, 255),      # 黄色
            'last_read_date': (255, 0, 255),  # マゼンタ
            'site_name': (0, 165, 255)      # オレンジ
        }
        
        # 各階層的検出結果に対して描画
        for hierarchical_result in hierarchical_results:
            # list-item（親）を描画
            self._draw_detection_box(
                annotated_frame,
                hierarchical_result.list_item_bbox,
                class_colors['list-item'],
                thickness=3  # 親は太い線で描画
            )
            
            # 子要素を描画
            for child_class in ['title', 'progress', 'last_read_date', 'site_name']:
                child_detection = getattr(hierarchical_result, child_class, None)
                if child_detection:
                    self._draw_detection_box(
                        annotated_frame,
                        child_detection,
                        class_colors[child_class],
                        thickness=2
                    )
        
        return annotated_frame
    
    def _draw_detection_box(
        self,
        frame: np.ndarray,
        detection: DetectionResult,
        color: tuple,
        thickness: int = 2
    ) -> None:
        """
        単一の検出結果をフレームに描画（内部ヘルパーメソッド）
        
        Args:
            frame: 描画対象の画像（in-place変更）
            detection: 検出結果
            color: 描画色（BGR形式のタプル）
            thickness: 線の太さ
        """
        # バウンディングボックスを描画
        cv2.rectangle(
            frame,
            (detection.x1, detection.y1),
            (detection.x2, detection.y2),
            color=color,
            thickness=thickness
        )
        
        # クラス名と信頼度をラベルとして表示
        label = f"{detection.class_name}: {detection.confidence:.2f}"
        
        # ラベルの背景を描画
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        label_y = detection.y1 - 10 if detection.y1 - 10 > 10 else detection.y1 + 20
        
        cv2.rectangle(
            frame,
            (detection.x1, label_y - label_size[1] - 5),
            (detection.x1 + label_size[0], label_y + 5),
            color=color,
            thickness=-1  # 塗りつぶし
        )
        
        # ラベルテキストを描画
        cv2.putText(
            frame,
            label,
            (detection.x1, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),  # 白色のテキスト
            1,
            cv2.LINE_AA
        )
    
    def __del__(self):
        """
        デストラクタ: オブジェクト破棄時にウィンドウをクローズ
        """
        self.cleanup()
