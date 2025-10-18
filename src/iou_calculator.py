"""
IoU（Intersection over Union）計算モジュール

このモジュールは、2つのbounding box間のIoUを計算する機能を提供します。
階層的検出において、子要素と親要素の重なり度合いを判定するために使用されます。
"""

from typing import Union
from src.object_detector import DetectionResult


def calculate_containment_ratio(
    parent_box: Union[DetectionResult, tuple],
    child_box: Union[DetectionResult, tuple]
) -> float:
    """
    子要素が親要素にどれだけ含まれているかを計算（包含率）
    
    包含率 = 交差面積 / 子要素の面積
    
    この指標は、子要素が親要素の内部にどれだけ含まれているかを表します。
    IoUと異なり、親要素が大きく子要素が小さい場合でも高い値を返します。
    
    Args:
        parent_box: 親要素のbounding box（DetectionResultまたは(x1, y1, x2, y2)のタプル）
        child_box: 子要素のbounding box（DetectionResultまたは(x1, y1, x2, y2)のタプル）
    
    Returns:
        包含率（0.0〜1.0の範囲）
        - 0.0: 子要素が親要素に全く含まれていない
        - 1.0: 子要素が完全に親要素に含まれている
        - 0.0 < ratio < 1.0: 子要素が部分的に親要素に含まれている
        エラー時はデフォルト値0.0を返す
    
    Examples:
        >>> from src.object_detector import DetectionResult
        >>> parent = DetectionResult(x1=0, y1=0, x2=100, y2=100, confidence=0.9, class_id=0, class_name="parent")
        >>> child = DetectionResult(x1=10, y1=10, x2=90, y2=30, confidence=0.8, class_id=1, class_name="child")
        >>> ratio = calculate_containment_ratio(parent, child)
        >>> print(f"包含率: {ratio:.2f}")
        包含率: 1.00  # 子要素が完全に親要素に含まれている
    """
    try:
        # DetectionResultオブジェクトの場合は座標を抽出
        if isinstance(parent_box, DetectionResult):
            x1_p, y1_p, x2_p, y2_p = parent_box.x1, parent_box.y1, parent_box.x2, parent_box.y2
        else:
            x1_p, y1_p, x2_p, y2_p = parent_box
        
        if isinstance(child_box, DetectionResult):
            x1_c, y1_c, x2_c, y2_c = child_box.x1, child_box.y1, child_box.x2, child_box.y2
        else:
            x1_c, y1_c, x2_c, y2_c = child_box
        
        # 座標の妥当性チェック
        if x2_p <= x1_p or y2_p <= y1_p:
            raise ValueError(f"親要素の座標が無効です: ({x1_p}, {y1_p}, {x2_p}, {y2_p})")
        if x2_c <= x1_c or y2_c <= y1_c:
            raise ValueError(f"子要素の座標が無効です: ({x1_c}, {y1_c}, {x2_c}, {y2_c})")
        
        # 交差領域（Intersection）の座標を計算
        x1_inter = max(x1_p, x1_c)
        y1_inter = max(y1_p, y1_c)
        x2_inter = min(x2_p, x2_c)
        y2_inter = min(y2_p, y2_c)
        
        # 交差領域の面積を計算
        if x2_inter < x1_inter or y2_inter < y1_inter:
            return 0.0
        
        inter_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)
        
        # 子要素の面積を計算
        child_area = (x2_c - x1_c) * (y2_c - y1_c)
        
        # 包含率を計算
        if child_area <= 0:
            return 0.0
        
        containment_ratio = inter_area / child_area
        
        # 包含率の範囲チェック（0.0〜1.0）
        if not (0.0 <= containment_ratio <= 1.0):
            raise ValueError(f"計算された包含率が範囲外です: {containment_ratio}")
        
        return containment_ratio
        
    except Exception as e:
        # 計算エラー時はデフォルト値（0.0）を返す
        print(f"⚠️  包含率計算で予期しないエラーが発生（デフォルト値0.0を返す）: {e}")
        return 0.0


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
        エラー時はデフォルト値0.0を返す
    
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
    try:
        # DetectionResultオブジェクトの場合は座標を抽出
        if isinstance(box1, DetectionResult):
            x1_1, y1_1, x2_1, y2_1 = box1.x1, box1.y1, box1.x2, box1.y2
        else:
            x1_1, y1_1, x2_1, y2_1 = box1
        
        if isinstance(box2, DetectionResult):
            x1_2, y1_2, x2_2, y2_2 = box2.x1, box2.y1, box2.x2, box2.y2
        else:
            x1_2, y1_2, x2_2, y2_2 = box2
        
        # 座標の妥当性チェック
        if x2_1 <= x1_1 or y2_1 <= y1_1:
            raise ValueError(f"box1の座標が無効です: ({x1_1}, {y1_1}, {x2_1}, {y2_1})")
        if x2_2 <= x1_2 or y2_2 <= y1_2:
            raise ValueError(f"box2の座標が無効です: ({x1_2}, {y1_2}, {x2_2}, {y2_2})")
        
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
        
        # IoUの範囲チェック（0.0〜1.0）
        if not (0.0 <= iou <= 1.0):
            raise ValueError(f"計算されたIoU値が範囲外です: {iou}")
        
        return iou
        
    except Exception as e:
        # IoU計算エラー時はデフォルト値（0.0）を返す
        print(f"⚠️  IoU計算で予期しないエラーが発生（デフォルト値0.0を返す）: {e}")
        return 0.0
