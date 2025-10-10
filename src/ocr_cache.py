"""
OCR結果キャッシュモジュール

このモジュールは、OCR処理結果をキャッシュして、同じ領域に対する
重複OCR処理を避けることでパフォーマンスを向上させます。
"""

from dataclasses import dataclass
from typing import Dict, Optional
import time

from src.object_detector import DetectionResult


@dataclass
class CachedOCRResult:
    """
    キャッシュされたOCR結果を表すデータクラス
    
    Attributes:
        text: OCRで抽出されたテキスト
        bbox: バウンディングボックス情報
        timestamp: キャッシュ作成時刻（Unix時間）
    """
    text: str
    bbox: DetectionResult
    timestamp: float


class OCRCache:
    """
    OCR結果キャッシュクラス
    
    バウンディングボックスの座標が近似している領域のOCR結果を再利用することで、
    OCR処理の実行回数を削減します。
    """
    
    def __init__(self, position_tolerance: int = 10, ttl: float = 2.0):
        """
        OCRCacheを初期化
        
        Args:
            position_tolerance: 座標の許容誤差（ピクセル）。デフォルトは10ピクセル
            ttl: キャッシュの有効期限（秒）。デフォルトは2.0秒
        """
        self.cache: Dict[str, CachedOCRResult] = {}
        self.position_tolerance = position_tolerance
        self.ttl = ttl
        self._cache_hits = 0
        self._cache_misses = 0
    
    def get_cached_text(self, bbox: DetectionResult) -> Optional[str]:
        """
        座標が近い領域のキャッシュされたテキストを取得
        
        Args:
            bbox: 検出結果（バウンディングボックス情報）
        
        Returns:
            キャッシュされたテキスト。キャッシュが存在しない場合はNone
        """
        current_time = time.time()
        
        # キャッシュ内の全エントリをチェック
        for cache_key, cached_result in list(self.cache.items()):
            # 有効期限チェック
            if current_time - cached_result.timestamp > self.ttl:
                # 期限切れのエントリを削除
                del self.cache[cache_key]
                continue
            
            # バウンディングボックスの近似一致判定
            if self._is_bbox_similar(bbox, cached_result.bbox):
                self._cache_hits += 1
                return cached_result.text
        
        # キャッシュミス
        self._cache_misses += 1
        return None
    
    def update_cache(self, bbox: DetectionResult, text: str) -> None:
        """
        OCR結果をキャッシュに追加
        
        Args:
            bbox: 検出結果（バウンディングボックス情報）
            text: OCRで抽出されたテキスト
        """
        cache_key = self._get_cache_key(bbox)
        
        self.cache[cache_key] = CachedOCRResult(
            text=text,
            bbox=bbox,
            timestamp=time.time()
        )
    
    def get_cache_stats(self) -> dict:
        """
        キャッシュ統計情報を取得
        
        Returns:
            キャッシュヒット率などの統計情報
        """
        total = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total if total > 0 else 0.0
        
        return {
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'hit_rate': hit_rate,
            'cache_size': len(self.cache)
        }
    
    def reset_stats(self) -> None:
        """キャッシュ統計をリセット"""
        self._cache_hits = 0
        self._cache_misses = 0
    
    def clear(self) -> None:
        """キャッシュをクリア"""
        self.cache.clear()
    
    def cleanup_expired(self) -> int:
        """
        期限切れのキャッシュエントリを削除
        
        Returns:
            削除されたエントリ数
        """
        current_time = time.time()
        expired_keys = []
        
        for cache_key, cached_result in self.cache.items():
            if current_time - cached_result.timestamp > self.ttl:
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)
    
    def _is_bbox_similar(self, bbox1: DetectionResult, bbox2: DetectionResult) -> bool:
        """
        2つのバウンディングボックスが近似しているか判定
        
        各座標の差が許容誤差以内であれば、近似していると判定します。
        
        Args:
            bbox1: 1つ目のバウンディングボックス
            bbox2: 2つ目のバウンディングボックス
        
        Returns:
            True: 近似している
            False: 近似していない
        """
        return (
            abs(bbox1.x1 - bbox2.x1) <= self.position_tolerance and
            abs(bbox1.y1 - bbox2.y1) <= self.position_tolerance and
            abs(bbox1.x2 - bbox2.x2) <= self.position_tolerance and
            abs(bbox1.y2 - bbox2.y2) <= self.position_tolerance
        )
    
    def _get_cache_key(self, bbox: DetectionResult) -> str:
        """
        バウンディングボックスからキャッシュキーを生成
        
        座標を許容誤差で丸めることで、近似した座標に対して
        同じキーを生成します。
        
        Args:
            bbox: バウンディングボックス情報
        
        Returns:
            キャッシュキー（文字列）
        """
        # 座標を許容誤差で丸める
        tolerance = self.position_tolerance
        x1_rounded = (bbox.x1 // tolerance) * tolerance
        y1_rounded = (bbox.y1 // tolerance) * tolerance
        x2_rounded = (bbox.x2 // tolerance) * tolerance
        y2_rounded = (bbox.y2 // tolerance) * tolerance
        
        return f"{x1_rounded}_{y1_rounded}_{x2_rounded}_{y2_rounded}"
