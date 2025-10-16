"""
IoU（Intersection over Union）計算モジュール

このモジュールは、2つのbounding box間のIoUを計算する機能を提供します。
階層的検出において、子要素と親要素の重なり度合いを判定するために使用されます。
"""

from typing import Union
from src.object_detector import DetectionResult


def calculate_iou(
    box1: Union[DetectionResult, tuple],
    box2: Union[DetectionResult, tuple]
) -> float:
    """
    2つのbounding box間のIoU（Intersection over Union）を計算
    
    IoUは2つのboxの重なり度合いを表す指標で、0.0（全く重ならない）から
    1.0（完全に一致）の範囲の値を返します。
    
    Args:
        box1: 1つ目のbounding box（DetectionResultまたは(x1, y1, x2, y2)のタプル）
        box2: 2つ目のbounding box（DetectionResultまたは(x1, y1, x2, y2)のタプル）
    
    Returns:
        IoU値（0.0〜1.0の範囲）
        - 0.0: 2つのboxが全く重ならない
        - 1.0: 2つのboxが完全に一致
        - 0.0 < IoU < 1.0: 部分的に重なる
    
    Examples:
        >>> from src.object_detector import DetectionResult
        >>> box1 = DetectionResult(x1=0, y1=0, x2=100, y2=100, confidence=0.9, class_id=0, class_name="test")
        >>> box2 = DetectionResult(x1=50, y1=50, x2=150, y2=150, confidence=0.8, class_id=0, class_name="test")
        >>> iou = calculate_iou(box1, box2)
        >>> print(f"IoU: {iou:.2f}")
        IoU: 0.14
        
        >>> # タプル形式でも使用可能
        >>> iou = calculate_iou((0, 0, 100, 100), (50, 50, 150, 150))
        >>> print(f"IoU: {iou:.2f}")
        IoU: 0.14
    """
    # DetectionResultオブジェクトの場合は座標を抽出
    if isinstance(box1, DetectionResult):
        x1_1, y1_1, x2_1, y2_1 = box1.x1, box1.y1, box1.x2, box1.y2
    else:
        x1_1, y1_1, x2_1, y2_1 = box1
    
    if isinstance(box2, DetectionResult):
        x1_2, y1_2, x2_2, y2_2 = box2.x1, box2.y1, box2.x2, box2.y2
    else:
        x1_2, y1_2, x2_2, y2_2 = box2
    
    # 交差領域（Intersection）の座標を計算
    # 交差領域の左上座標は、2つのboxの左上座標の最大値
    x1_inter = max(x1_1, x1_2)
    y1_inter = max(y1_1, y1_2)
    
    # 交差領域の右下座標は、2つのboxの右下座標の最小値
    x2_inter = min(x2_1, x2_2)
    y2_inter = min(y2_1, y2_2)
    
    # 交差領域の面積を計算
    # 2つのboxが重ならない場合（x2_inter < x1_inter または y2_inter < y1_inter）、
    # 交差領域は存在しないため、IoU = 0.0を返す
    if x2_inter < x1_inter or y2_inter < y1_inter:
        return 0.0
    
    inter_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)
    
    # 各boxの面積を計算
    box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
    box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
    
    # 和領域（Union）の面積を計算
    # Union = box1の面積 + box2の面積 - 交差領域の面積
    # （交差領域は両方のboxに含まれるため、1回だけカウントする）
    union_area = box1_area + box2_area - inter_area
    
    # IoUを計算
    # union_areaが0の場合（両方のboxの面積が0）は、0.0を返す
    if union_area <= 0:
        return 0.0
    
    iou = inter_area / union_area
    
    return iou
