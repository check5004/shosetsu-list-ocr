"""
検出結果キャッシュモジュール

このモジュールは、物体検出結果をキャッシュして、類似フレームでの
重複検出を避けることでパフォーマンスを向上させます。
"""

from dataclasses import dataclass
from typing import List, Optional
import time
import numpy as np
import cv2

from src.object_detector import DetectionResult


@dataclass
class CacheEntry:
    """
    キャッシュエントリを表すデータクラス
    
    Attributes:
        timestamp: キャッシュ作成時刻（Unix時間）
        frame_hash: フレームの簡易ハッシュ値
        detections: 検出結果のリスト
    """
    timestamp: float
    frame_hash: int
    detections: List[DetectionResult]


class DetectionCache:
    """
    検出結果キャッシュクラス
    
    連続する類似フレームで検出結果を再利用することで、
    物体検出の実行回数を削減します。
    """
    
    def __init__(self, ttl: float = 0.5, similarity_threshold: float = 0.95):
        """
        DetectionCacheを初期化
        
        Args:
            ttl: キャッシュの有効期限（秒）。デフォルトは0.5秒
            similarity_threshold: フレーム類似度のしきい値（0.0-1.0）。
                                 デフォルトは0.95（95%類似）
        """
        self.cache: Optional[CacheEntry] = None
        self.ttl = ttl
        self.similarity_threshold = similarity_threshold
        self._cache_hits = 0
        self._cache_misses = 0
    
    def should_skip_detection(self, frame: np.ndarray) -> bool:
        """
        フレームが類似している場合、検出をスキップすべきか判定
        
        Args:
            frame: 入力フレーム（BGR形式のnumpy配列）
        
        Returns:
            True: 検出をスキップすべき（キャッシュを使用）
            False: 検出を実行すべき
        """
        # キャッシュが存在しない場合
        if self.cache is None:
            self._cache_misses += 1
            return False
        
        # キャッシュの有効期限チェック
        current_time = time.time()
        if current_time - self.cache.timestamp > self.ttl:
            self._cache_misses += 1
            return False
        
        # フレームハッシュを計算
        frame_hash = self._compute_frame_hash(frame)
        
        # フレーム類似度を計算
        similarity = self._compute_similarity(frame_hash, self.cache.frame_hash)
        
        # 類似度がしきい値以上ならスキップ
        if similarity >= self.similarity_threshold:
            self._cache_hits += 1
            return True
        else:
            self._cache_misses += 1
            return False
    
    def get_cached_detections(self) -> Optional[List[DetectionResult]]:
        """
        キャッシュされた検出結果を取得
        
        Returns:
            キャッシュされた検出結果のリスト。キャッシュが無効な場合はNone
        """
        if self.cache is None:
            return None
        
        # 有効期限チェック
        current_time = time.time()
        if current_time - self.cache.timestamp > self.ttl:
            return None
        
        return self.cache.detections
    
    def update_cache(self, frame: np.ndarray, detections: List[DetectionResult]) -> None:
        """
        キャッシュを更新
        
        Args:
            frame: 入力フレーム（BGR形式のnumpy配列）
            detections: 検出結果のリスト
        """
        frame_hash = self._compute_frame_hash(frame)
        
        self.cache = CacheEntry(
            timestamp=time.time(),
            frame_hash=frame_hash,
            detections=detections
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
            'hit_rate': hit_rate
        }
    
    def reset_stats(self) -> None:
        """キャッシュ統計をリセット"""
        self._cache_hits = 0
        self._cache_misses = 0
    
    def clear(self) -> None:
        """キャッシュをクリア"""
        self.cache = None
    
    @staticmethod
    def _compute_frame_hash(frame: np.ndarray) -> int:
        """
        フレームの簡易ハッシュを計算
        
        ダウンサンプリングと平均ハッシュアルゴリズムを使用して、
        高速にフレームの特徴を抽出します。
        
        Args:
            frame: 入力フレーム（BGR形式のnumpy配列）
        
        Returns:
            フレームのハッシュ値（整数）
        """
        # ダウンサンプリングして高速化（64x64ピクセル）
        small = cv2.resize(frame, (64, 64))
        
        # グレースケール変換
        if len(small.shape) == 3:
            small = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        
        # 平均ハッシュアルゴリズム
        avg = small.mean()
        binary = (small > avg).astype(np.uint8)
        
        # バイト列からハッシュ値を生成
        return hash(binary.tobytes())
    
    @staticmethod
    def _compute_similarity(hash1: int, hash2: int) -> float:
        """
        2つのハッシュ値の類似度を計算
        
        ハッシュ値が同じ場合は1.0、異なる場合は0.0を返します。
        より高度な類似度計算が必要な場合は、ハミング距離などを使用できます。
        
        Args:
            hash1: 1つ目のハッシュ値
            hash2: 2つ目のハッシュ値
        
        Returns:
            類似度（0.0-1.0）
        """
        # 単純な一致判定
        # より高度な実装では、ハミング距離を使用することも可能
        return 1.0 if hash1 == hash2 else 0.0
