"""
パフォーマンス計測モジュール

リアルタイムOCRアプリケーションのパフォーマンスを計測・監視するためのクラスを提供します。
各処理ステップの実行時間、FPS、キャッシュヒット率などのメトリクスを収集します。
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import deque


@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""
    fps: float = 0.0
    avg_capture_time: float = 0.0
    avg_detection_time: float = 0.0
    avg_ocr_time: float = 0.0
    avg_display_time: float = 0.0
    cache_hit_rate: float = 0.0
    frames_processed: int = 0
    frames_skipped: int = 0


class FPSCounter:
    """FPSカウンター"""
    
    def __init__(self, window_size: int = 30):
        """
        FPSカウンターを初期化
        
        Args:
            window_size: FPS計算に使用する直近のフレーム数
        """
        self.window_size = window_size
        self.frame_times: deque = deque(maxlen=window_size)
        self.last_update_time: Optional[float] = None
    
    def update(self) -> float:
        """
        フレームを記録してFPSを計算
        
        Returns:
            現在のFPS
        """
        current_time = time.time()
        
        if self.last_update_time is not None:
            frame_time = current_time - self.last_update_time
            self.frame_times.append(frame_time)
        
        self.last_update_time = current_time
        
        return self.get_fps()
    
    def get_fps(self) -> float:
        """
        現在のFPSを取得
        
        Returns:
            FPS値（フレームタイムが記録されていない場合は0.0）
        """
        if len(self.frame_times) == 0:
            return 0.0
        
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        
        if avg_frame_time == 0:
            return 0.0
        
        return 1.0 / avg_frame_time
    
    def reset(self) -> None:
        """FPSカウンターをリセット"""
        self.frame_times.clear()
        self.last_update_time = None


class PerformanceMonitor:
    """パフォーマンス計測クラス"""
    
    def __init__(self, history_size: int = 100):
        """
        パフォーマンスモニターを初期化
        
        Args:
            history_size: 各メトリクスの履歴保持数
        """
        self.history_size = history_size
        self.metrics: Dict[str, deque] = {}
        self.timers: Dict[str, float] = {}
        self.fps_counter = FPSCounter()
        
        # カウンター
        self.frames_processed = 0
        self.frames_skipped = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    def start_timer(self, name: str) -> None:
        """
        タイマーを開始
        
        Args:
            name: タイマー名（例: "capture", "detection", "ocr"）
        """
        self.timers[name] = time.time()
    
    def end_timer(self, name: str) -> float:
        """
        タイマーを終了し、経過時間を記録
        
        Args:
            name: タイマー名
            
        Returns:
            経過時間（秒）
            
        Raises:
            KeyError: 指定されたタイマーが開始されていない場合
        """
        if name not in self.timers:
            raise KeyError(f"Timer '{name}' was not started")
        
        start_time = self.timers[name]
        elapsed = time.time() - start_time
        
        # メトリクスに記録
        if name not in self.metrics:
            self.metrics[name] = deque(maxlen=self.history_size)
        
        self.metrics[name].append(elapsed)
        
        # タイマーをクリア
        del self.timers[name]
        
        return elapsed
    
    def get_average(self, name: str) -> float:
        """
        指定されたメトリクスの平均値を取得
        
        Args:
            name: メトリクス名
            
        Returns:
            平均値（データがない場合は0.0）
        """
        if name not in self.metrics or len(self.metrics[name]) == 0:
            return 0.0
        
        return sum(self.metrics[name]) / len(self.metrics[name])
    
    def update_fps(self) -> float:
        """
        FPSを更新
        
        Returns:
            現在のFPS
        """
        self.frames_processed += 1
        return self.fps_counter.update()
    
    def record_frame_skip(self) -> None:
        """フレームスキップを記録"""
        self.frames_skipped += 1
    
    def record_cache_hit(self) -> None:
        """キャッシュヒットを記録"""
        self.cache_hits += 1
    
    def record_cache_miss(self) -> None:
        """キャッシュミスを記録"""
        self.cache_misses += 1
    
    def get_cache_hit_rate(self) -> float:
        """
        キャッシュヒット率を取得
        
        Returns:
            キャッシュヒット率（0.0-1.0）
        """
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        
        return self.cache_hits / total
    
    def get_report(self) -> Dict[str, Any]:
        """
        パフォーマンスレポートを取得
        
        Returns:
            パフォーマンスメトリクスを含む辞書
        """
        return {
            'fps': self.fps_counter.get_fps(),
            'avg_capture_time': self.get_average('capture'),
            'avg_detection_time': self.get_average('detection'),
            'avg_ocr_time': self.get_average('ocr'),
            'avg_display_time': self.get_average('display'),
            'cache_hit_rate': self.get_cache_hit_rate(),
            'frames_processed': self.frames_processed,
            'frames_skipped': self.frames_skipped,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
        }
    
    def get_metrics_object(self) -> PerformanceMetrics:
        """
        パフォーマンスメトリクスをデータクラスとして取得
        
        Returns:
            PerformanceMetricsオブジェクト
        """
        report = self.get_report()
        return PerformanceMetrics(
            fps=report['fps'],
            avg_capture_time=report['avg_capture_time'],
            avg_detection_time=report['avg_detection_time'],
            avg_ocr_time=report['avg_ocr_time'],
            avg_display_time=report['avg_display_time'],
            cache_hit_rate=report['cache_hit_rate'],
            frames_processed=report['frames_processed'],
            frames_skipped=report['frames_skipped'],
        )
    
    def reset(self) -> None:
        """全てのメトリクスをリセット"""
        self.metrics.clear()
        self.timers.clear()
        self.fps_counter.reset()
        self.frames_processed = 0
        self.frames_skipped = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    def print_report(self) -> None:
        """パフォーマンスレポートをコンソールに出力"""
        report = self.get_report()
        
        print("\n" + "="*50)
        print("パフォーマンスレポート")
        print("="*50)
        print(f"FPS: {report['fps']:.2f}")
        print(f"処理フレーム数: {report['frames_processed']}")
        print(f"スキップフレーム数: {report['frames_skipped']}")
        print("-"*50)
        print(f"平均キャプチャ時間: {report['avg_capture_time']*1000:.2f} ms")
        print(f"平均検出時間: {report['avg_detection_time']*1000:.2f} ms")
        print(f"平均OCR時間: {report['avg_ocr_time']*1000:.2f} ms")
        print(f"平均表示時間: {report['avg_display_time']*1000:.2f} ms")
        print("-"*50)
        
        # 合計処理時間とボトルネック分析
        total_time = (report['avg_capture_time'] + report['avg_detection_time'] + 
                     report['avg_ocr_time'] + report['avg_display_time'])
        
        if total_time > 0:
            print("処理時間の内訳:")
            print(f"  キャプチャ: {report['avg_capture_time']/total_time*100:.1f}%")
            print(f"  検出: {report['avg_detection_time']/total_time*100:.1f}%")
            print(f"  OCR: {report['avg_ocr_time']/total_time*100:.1f}%")
            print(f"  表示: {report['avg_display_time']/total_time*100:.1f}%")
            print(f"合計処理時間: {total_time*1000:.2f} ms")
            print(f"理論最大FPS: {1.0/total_time:.2f}")
        
        print("-"*50)
        print(f"キャッシュヒット率: {report['cache_hit_rate']*100:.1f}%")
        print(f"キャッシュヒット数: {report['cache_hits']}")
        print(f"キャッシュミス数: {report['cache_misses']}")
        
        # ボトルネック警告
        if report['avg_detection_time'] > 0.2:
            print("\n⚠️  警告: 検出処理が遅い（>200ms）")
        if report['avg_ocr_time'] > 0.3:
            print("⚠️  警告: OCR処理が遅い（>300ms）")
        if report['cache_hit_rate'] < 0.5:
            print("⚠️  警告: キャッシュヒット率が低い（<50%）")
        
        print("="*50 + "\n")
