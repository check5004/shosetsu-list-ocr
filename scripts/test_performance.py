#!/usr/bin/env python3
"""
パフォーマンステストスクリプト

このスクリプトは、パフォーマンス監視機能をテストし、
メモリ使用量とFPSの計測が正しく動作することを確認します。
"""

import sys
import time
import numpy as np
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.performance_monitor import PerformanceMonitor


def simulate_processing():
    """処理をシミュレート"""
    # 重い処理をシミュレート
    data = np.random.rand(1000, 1000)
    result = np.dot(data, data.T)
    return result


def test_performance_monitor():
    """パフォーマンスモニターのテスト"""
    print("="*60)
    print("パフォーマンス監視機能のテスト")
    print("="*60)
    
    monitor = PerformanceMonitor()
    
    # 30フレーム分の処理をシミュレート
    print("\n30フレーム分の処理をシミュレート中...")
    for i in range(30):
        # キャプチャ処理
        monitor.start_timer('capture')
        time.sleep(0.01)  # 10ms
        monitor.end_timer('capture')
        
        # 検出処理
        monitor.start_timer('detection')
        simulate_processing()
        time.sleep(0.05)  # 50ms
        monitor.end_timer('detection')
        
        # OCR処理
        monitor.start_timer('ocr')
        time.sleep(0.03)  # 30ms
        monitor.end_timer('ocr')
        
        # 表示処理
        monitor.start_timer('display')
        time.sleep(0.005)  # 5ms
        monitor.end_timer('display')
        
        # FPS更新
        fps = monitor.update_fps()
        
        # キャッシュヒット/ミスをランダムに記録
        if i % 3 == 0:
            monitor.record_cache_hit()
        else:
            monitor.record_cache_miss()
        
        # 進捗表示
        if (i + 1) % 10 == 0:
            print(f"  処理済み: {i + 1}/30 フレーム (FPS: {fps:.2f})")
    
    # レポート出力
    print("\n" + "="*60)
    print("テスト完了 - パフォーマンスレポート:")
    print("="*60)
    monitor.print_report()
    
    # メトリクスオブジェクトの取得テスト
    metrics = monitor.get_metrics_object()
    print("\nメトリクスオブジェクト:")
    print(f"  FPS: {metrics.fps:.2f}")
    print(f"  平均キャプチャ時間: {metrics.avg_capture_time*1000:.2f} ms")
    print(f"  平均検出時間: {metrics.avg_detection_time*1000:.2f} ms")
    print(f"  平均OCR時間: {metrics.avg_ocr_time*1000:.2f} ms")
    print(f"  平均表示時間: {metrics.avg_display_time*1000:.2f} ms")
    print(f"  キャッシュヒット率: {metrics.cache_hit_rate*100:.1f}%")
    print(f"  処理フレーム数: {metrics.frames_processed}")
    print(f"  メモリ使用量: {metrics.memory_usage_mb:.1f} MB ({metrics.memory_percent:.1f}%)")
    
    print("\n✅ パフォーマンス監視機能のテストが完了しました")


if __name__ == "__main__":
    test_performance_monitor()
