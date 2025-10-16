"""
パフォーマンスモード設定モジュール

このモジュールは、リアルタイムOCRアプリケーションのパフォーマンスモードを管理します。
ユーザーは精度とパフォーマンスのバランスを調整できます。
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class PerformanceMode:
    """パフォーマンスモード設定
    
    Attributes:
        name: モード名（表示用）
        frame_skip: Nフレームに1回処理（1=全フレーム処理）
        detection_cache_enabled: 検出結果キャッシュの有効化
        ocr_cache_enabled: OCR結果キャッシュの有効化
        ocr_workers: 並列OCR処理のワーカー数
        max_detections_per_frame: 1フレームあたりの最大検出数
    """
    name: str
    frame_skip: int
    detection_cache_enabled: bool
    ocr_cache_enabled: bool
    ocr_workers: int
    max_detections_per_frame: int
    
    def __post_init__(self):
        """バリデーション"""
        if self.frame_skip < 1:
            raise ValueError(f"frame_skip must be >= 1, got {self.frame_skip}")
        if self.ocr_workers < 1:
            raise ValueError(f"ocr_workers must be >= 1, got {self.ocr_workers}")
        if self.max_detections_per_frame < 1:
            raise ValueError(f"max_detections_per_frame must be >= 1, got {self.max_detections_per_frame}")


# パフォーマンスモードのプリセット定義
PERFORMANCE_MODES: Dict[str, PerformanceMode] = {
    "fast": PerformanceMode(
        name="高速",
        frame_skip=2,  # 2フレームに1回処理
        detection_cache_enabled=True,
        ocr_cache_enabled=True,
        ocr_workers=6,  # 並列度向上
        max_detections_per_frame=8  # 検出数を増やす（5→8）
    ),
    "balanced": PerformanceMode(
        name="バランス",
        frame_skip=1,  # 全フレーム処理
        detection_cache_enabled=True,
        ocr_cache_enabled=True,
        ocr_workers=4,  # 並列度向上
        max_detections_per_frame=12  # 検出数を増やす（8→12）
    ),
    "accurate": PerformanceMode(
        name="高精度",
        frame_skip=1,  # 全フレーム処理
        detection_cache_enabled=False,
        ocr_cache_enabled=False,
        ocr_workers=3,  # 並列度向上
        max_detections_per_frame=20  # 検出数を増やす（15→20）
    )
}


def get_performance_mode(mode_key: str) -> PerformanceMode:
    """パフォーマンスモードを取得
    
    Args:
        mode_key: モードキー（"fast", "balanced", "accurate"）
    
    Returns:
        PerformanceMode: 指定されたモードの設定
    
    Raises:
        ValueError: 無効なモードキーが指定された場合
    """
    if mode_key not in PERFORMANCE_MODES:
        available_modes = ", ".join(PERFORMANCE_MODES.keys())
        raise ValueError(
            f"Invalid performance mode: {mode_key}. "
            f"Available modes: {available_modes}"
        )
    return PERFORMANCE_MODES[mode_key]


def get_available_modes() -> Dict[str, str]:
    """利用可能なモードの一覧を取得
    
    Returns:
        Dict[str, str]: モードキーとモード名のマッピング
    """
    return {key: mode.name for key, mode in PERFORMANCE_MODES.items()}


def validate_mode_key(mode_key: str) -> bool:
    """モードキーの妥当性を検証
    
    Args:
        mode_key: 検証するモードキー
    
    Returns:
        bool: 有効なモードキーの場合True
    """
    return mode_key in PERFORMANCE_MODES
