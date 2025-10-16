"""
パフォーマンスモニターの動作確認テスト
"""

import time
from src.performance_monitor import PerformanceMonitor, FPSCounter


def test_fps_counter():
    """FPSカウンターのテスト"""
    print("FPSカウンターのテスト...")
    fps_counter = FPSCounter(window_size=10)
    
    # 10フレームをシミュレート（約30FPS）
    for _ in range(10):
        fps_counter.update()
        time.sleep(1/30)  # 30FPS相当
    
    fps = fps_counter.get_fps()
    print(f"  計測FPS: {fps:.2f} (期待値: ~30)")
    assert 25 < fps < 35, f"FPSが期待範囲外: {fps}"
    print("  ✓ FPSカウンターは正常に動作しています")


def test_performance_monitor():
    """パフォーマンスモニターのテスト"""
    print("\nパフォーマンスモニターのテスト...")
    monitor = PerformanceMonitor(history_size=10)
    
    # タイマー機能のテスト
    monitor.start_timer("test_operation")
    time.sleep(0.1)  # 100ms待機
    elapsed = monitor.end_timer("test_operation")
    print(f"  計測時間: {elapsed*1000:.2f} ms (期待値: ~100ms)")
    assert 90 < elapsed * 1000 < 110, f"計測時間が期待範囲外: {elapsed*1000}ms"
    
    # 平均値のテスト
    for i in range(5):
        monitor.start_timer("capture")
        time.sleep(0.01 * (i + 1))  # 10ms, 20ms, 30ms, 40ms, 50ms
        monitor.end_timer("capture")
    
    avg_capture = monitor.get_average("capture")
    print(f"  平均キャプチャ時間: {avg_capture*1000:.2f} ms (期待値: ~30ms)")
    assert 25 < avg_capture * 1000 < 35, f"平均時間が期待範囲外: {avg_capture*1000}ms"
    
    # FPS更新のテスト
    for _ in range(10):
        monitor.update_fps()
        time.sleep(0.033)  # 約30FPS
    
    # キャッシュヒット率のテスト
    monitor.record_cache_hit()
    monitor.record_cache_hit()
    monitor.record_cache_hit()
    monitor.record_cache_miss()
    
    hit_rate = monitor.get_cache_hit_rate()
    print(f"  キャッシュヒット率: {hit_rate*100:.1f}% (期待値: 75%)")
    assert abs(hit_rate - 0.75) < 0.01, f"ヒット率が期待値と異なる: {hit_rate}"
    
    # レポート生成のテスト
    report = monitor.get_report()
    print(f"  レポート生成: ✓")
    print(f"    - FPS: {report['fps']:.2f}")
    print(f"    - 処理フレーム数: {report['frames_processed']}")
    print(f"    - キャッシュヒット率: {report['cache_hit_rate']*100:.1f}%")
    
    # メトリクスオブジェクトのテスト
    metrics = monitor.get_metrics_object()
    print(f"  メトリクスオブジェクト: ✓")
    print(f"    - FPS: {metrics.fps:.2f}")
    print(f"    - 平均キャプチャ時間: {metrics.avg_capture_time*1000:.2f} ms")
    
    print("  ✓ パフォーマンスモニターは正常に動作しています")


def test_performance_report():
    """パフォーマンスレポート出力のテスト"""
    print("\nパフォーマンスレポート出力のテスト...")
    monitor = PerformanceMonitor()
    
    # サンプルデータを生成
    for _ in range(20):
        monitor.start_timer("capture")
        time.sleep(0.01)
        monitor.end_timer("capture")
        
        monitor.start_timer("detection")
        time.sleep(0.05)
        monitor.end_timer("detection")
        
        monitor.start_timer("ocr")
        time.sleep(0.03)
        monitor.end_timer("ocr")
        
        monitor.update_fps()
        
        if _ % 3 == 0:
            monitor.record_cache_hit()
        else:
            monitor.record_cache_miss()
    
    # レポートを出力
    monitor.print_report()
    print("  ✓ レポート出力は正常に動作しています")


if __name__ == "__main__":
    print("="*60)
    print("パフォーマンスモニター 動作確認テスト")
    print("="*60)
    
    try:
        test_fps_counter()
        test_performance_monitor()
        test_performance_report()
        
        print("\n" + "="*60)
        print("全てのテストが成功しました！ ✓")
        print("="*60)
    except AssertionError as e:
        print(f"\n✗ テスト失敗: {e}")
    except Exception as e:
        print(f"\n✗ エラー発生: {e}")
        import traceback
        traceback.print_exc()
