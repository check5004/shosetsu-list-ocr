"""
階層的検出モジュール

このモジュールは、5クラス（list-item, title, progress, last_read_date, site_name）の
検出を行い、親子関係を構築して構造化されたデータを生成します。
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from pathlib import Path
import numpy as np
import torch
from ultralytics import YOLO

from src.object_detector import DetectionResult
from src.iou_calculator import calculate_iou


@dataclass
class HierarchicalDetectionResult:
    """
    階層的検出結果を表すデータクラス
    
    list-item（親）と、その内部に含まれる子要素（title、progress、
    last_read_date、site_name）の検出結果を構造化して保持します。
    
    Attributes:
        list_item_id: list-itemの一意識別子（例: "list_item_001"）
        list_item_bbox: list-itemのbounding box情報
        title: タイトル要素の検出結果（オプション）
        progress: 読書進捗要素の検出結果（オプション）
        last_read_date: 最終読書日時要素の検出結果（オプション）
        site_name: サイト名要素の検出結果（オプション）
        orphaned_children: 親に紐付けられなかった孤立した子要素のリスト
    """
    list_item_id: str
    list_item_bbox: DetectionResult
    title: Optional[DetectionResult] = None
    progress: Optional[DetectionResult] = None
    last_read_date: Optional[DetectionResult] = None
    site_name: Optional[DetectionResult] = None
    orphaned_children: List[DetectionResult] = field(default_factory=list)
    
    def has_required_fields(self) -> bool:
        """
        必須フィールドが揃っているかチェック
        
        必須フィールド: title、last_read_date、site_name
        オプションフィールド: progress
        
        Returns:
            すべての必須フィールドが存在する場合True、それ以外False
        """
        return all([
            self.title is not None,
            self.last_read_date is not None,
            self.site_name is not None
        ])
    
    def get_error_status(self) -> str:
        """
        エラーステータスを取得
        
        必須フィールドの欠損状況を文字列で返します。
        すべての必須フィールドが揃っている場合は "OK" を返します。
        
        Returns:
            エラーステータス文字列
            - "OK": すべての必須フィールドが存在
            - "missing_title": titleが欠損
            - "missing_last_read_date": last_read_dateが欠損
            - "missing_site_name": site_nameが欠損
            - 複数欠損の場合はカンマ区切り（例: "missing_title, missing_site_name"）
        """
        missing = []
        
        if self.title is None:
            missing.append("missing_title")
        if self.last_read_date is None:
            missing.append("missing_last_read_date")
        if self.site_name is None:
            missing.append("missing_site_name")
        
        return ", ".join(missing) if missing else "OK"



class HierarchicalDetector:
    """
    階層的検出クラス
    
    5クラス（list-item, title, progress, last_read_date, site_name）の検出を行い、
    親子関係を構築して構造化されたデータを生成します。
    
    モデル自体には階層構造を持たせず、推論後にIoU計算と座標判定で
    親子関係を判定します。
    """
    
    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.6,
        iou_threshold: float = 0.5
    ):
        """
        HierarchicalDetectorを初期化
        
        Args:
            model_path: 5クラス学習済みYOLOv8モデルファイルのパス
            confidence_threshold: 検出の信頼度しきい値（デフォルト: 0.6）
            iou_threshold: 親子関係判定のIoUしきい値（デフォルト: 0.5）
        
        Raises:
            FileNotFoundError: モデルファイルが存在しない場合
            RuntimeError: モデルのロードに失敗した場合
        """
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        
        # 5クラスの定義
        self.class_names = [
            'list-item',
            'title',
            'progress',
            'last_read_date',
            'site_name'
        ]
        
        # モデルファイルの存在チェック
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"モデルファイルが見つかりません: {self.model_path}\n"
                f"階層的検出用YOLOv8モデルを {self.model_path} に配置してください。"
            )
        
        # YOLOv8モデルのロード
        try:
            self.model = YOLO(str(self.model_path))
            
            # Apple Silicon MPS対応
            if torch.backends.mps.is_available():
                self.device = "mps"
                print("Apple Silicon MPS を使用します（階層的検出）")
            elif torch.cuda.is_available():
                self.device = "cuda"
                print("CUDA を使用します（階層的検出）")
            else:
                self.device = "cpu"
                print("CPU を使用します（階層的検出）")
            
            # モデルをデバイスに転送
            self.model.to(self.device)
            print(f"階層的検出用YOLOv8モデルをロードしました: {self.model_path}")
            
        except Exception as e:
            raise RuntimeError(f"モデルのロードに失敗しました: {e}")

    
    def detect(self, frame: np.ndarray) -> List[HierarchicalDetectionResult]:
        """
        フレームから階層的検出を実行
        
        5クラスすべての検出を行い、親子関係を構築して
        構造化された検出結果を返します。
        
        Args:
            frame: 入力画像（BGR形式のnumpy配列）
        
        Returns:
            階層的検出結果のリスト（各list-itemとその子要素を含む）
        """
        if self.model is None:
            raise RuntimeError("モデルが初期化されていません")
        
        # YOLOv8で推論実行
        results = self.model(
            frame,
            verbose=False,
            device=self.device,
            conf=self.confidence_threshold
        )
        
        # 検出結果をクラスごとに分類
        list_items = []
        children = {
            'title': [],
            'progress': [],
            'last_read_date': [],
            'site_name': []
        }
        
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
                class_name = self.class_names[class_id] if class_id < len(self.class_names) else f"class_{class_id}"
                
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
                
                # list-itemと子要素に分類
                if class_name == 'list-item':
                    list_items.append(detection)
                elif class_name in children:
                    children[class_name].append(detection)
        
        # 親子関係を構築
        hierarchical_results = self._build_hierarchy(list_items, children)
        
        return hierarchical_results

    
    def _build_hierarchy(
        self,
        list_items: List[DetectionResult],
        children: Dict[str, List[DetectionResult]]
    ) -> List[HierarchicalDetectionResult]:
        """
        親子関係を構築
        
        各子要素について、IoUが最大かつしきい値以上のlist-itemを親として紐付けます。
        孤立した子要素（どのlist-itemにも紐付けられない要素）は警告ログを出力します。
        
        Args:
            list_items: list-item検出結果のリスト
            children: 子要素検出結果の辞書（キー: クラス名、値: 検出結果のリスト）
        
        Returns:
            階層的検出結果のリスト（各list-itemとその子要素を含む）
        """
        hierarchical_results = []
        
        # 各list-itemに対して階層的検出結果を作成
        for idx, list_item in enumerate(list_items):
            result = HierarchicalDetectionResult(
                list_item_id=f"list_item_{idx + 1:03d}",
                list_item_bbox=list_item
            )
            hierarchical_results.append(result)
        
        # 各子要素クラスについて、最適な親を見つける
        for child_class, child_list in children.items():
            # 各子要素について処理
            for child in child_list:
                best_parent_idx = -1
                best_iou = 0.0
                
                # すべてのlist-itemとのIoUを計算
                for idx, list_item in enumerate(list_items):
                    try:
                        iou = calculate_iou(list_item, child)
                        
                        # IoUがしきい値以上で、かつ最大の場合
                        if iou >= self.iou_threshold and iou > best_iou:
                            best_iou = iou
                            best_parent_idx = idx
                    except Exception as e:
                        # IoU計算エラー時はデフォルト値（0.0）を使用
                        print(f"⚠️  IoU計算エラー: {e}")
                        continue
                
                # 最適な親が見つかった場合、子要素を割り当て
                if best_parent_idx >= 0:
                    parent_result = hierarchical_results[best_parent_idx]
                    
                    # 既に同じクラスの子要素が割り当てられている場合、
                    # 信頼度が高い方を採用
                    existing_child = getattr(parent_result, child_class, None)
                    if existing_child is None or child.confidence > existing_child.confidence:
                        setattr(parent_result, child_class, child)
                else:
                    # 孤立した子要素を記録
                    print(f"⚠️  孤立した{child_class}要素を検出: "
                          f"confidence={child.confidence:.2f}, "
                          f"bbox=({child.x1}, {child.y1}, {child.x2}, {child.y2})")
        
        # 孤立した子要素の統計を出力
        for child_class, child_list in children.items():
            assigned_count = sum(
                1 for result in hierarchical_results
                if getattr(result, child_class, None) is not None
            )
            orphaned_count = len(child_list) - assigned_count
            
            if orphaned_count > 0:
                print(f"⚠️  {child_class}: {orphaned_count}件の孤立要素")
        
        return hierarchical_results
