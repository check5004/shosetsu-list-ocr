"""キャッシュモジュールの動作確認テスト"""

import numpy as np
import time
from src.detection_cache import DetectionCache
from src.ocr_cache import OCRCache
from src.object_detector import DetectionResult


def test_detection_cache():
    """DetectionCacheの基本動作をテスト"""
    print("=== DetectionCache テスト ===")
    
    cache = DetectionCache(ttl=1.0, similarity_threshold=0.95)
    
    # テストフレームを作成
    frame1 = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    frame2 = frame1.copy()  # 同じフレーム
    frame3 = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)  # 異なるフレーム
    
    # テスト検出結果
    detections = [
        DetectionResult(100, 100, 200, 150, 0.9, 0, "list-item"),
        DetectionResult(100, 200, 200, 250, 0.85, 0, "list-item")
    ]
    
    # 初回はキャッシュミス
    assert not cache.should_skip_detection(frame1), "初回はキャッシュミスのはず"
    cache.update_cache(frame1, detections)
    
    # 同じフレームはキャッシュヒット
    assert cache.should_skip_detection(frame2), "同じフレームはキャッシュヒットのはず"
    cached = cache.get_cached_detections()
    assert cached is not None, "キャッシュされた検出結果を取得できるはず"
    assert len(cached) == 2, "検出結果の数が一致するはず"
    
    # 異なるフレームはキャッシュミス
    assert not cache.should_skip_detection(frame3), "異なるフレームはキャッシュミスのはず"
    
    # 統計情報を確認
    stats = cache.get_cache_stats()
    print(f"キャッシュヒット: {stats['cache_hits']}")
    print(f"キャッシュミス: {stats['cache_misses']}")
    print(f"ヒット率: {stats['hit_rate']:.2%}")
    
    # TTL期限切れテスト
    time.sleep(1.1)
    assert not cache.should_skip_detection(frame2), "TTL期限切れでキャッシュミスのはず"
    
    print("✓ DetectionCache テスト成功\n")


def test_ocr_cache():
    """OCRCacheの基本動作をテスト"""
    print("=== OCRCache テスト ===")
    
    cache = OCRCache(position_tolerance=10, ttl=2.0)
    
    # テストバウンディングボックス
    bbox1 = DetectionResult(100, 100, 200, 150, 0.9, 0, "list-item")
    bbox2 = DetectionResult(105, 102, 198, 148, 0.88, 0, "list-item")  # 近似座標
    bbox3 = DetectionResult(300, 300, 400, 350, 0.92, 0, "list-item")  # 異なる座標
    
    # 初回はキャッシュミス
    text1 = cache.get_cached_text(bbox1)
    assert text1 is None, "初回はキャッシュミスのはず"
    
    # キャッシュに追加
    cache.update_cache(bbox1, "テストテキスト1")
    
    # 同じ座標はキャッシュヒット
    text2 = cache.get_cached_text(bbox1)
    assert text2 == "テストテキスト1", "同じ座標はキャッシュヒットのはず"
    
    # 近似座標もキャッシュヒット
    text3 = cache.get_cached_text(bbox2)
    assert text3 == "テストテキスト1", "近似座標もキャッシュヒットのはず"
    
    # 異なる座標はキャッシュミス
    text4 = cache.get_cached_text(bbox3)
    assert text4 is None, "異なる座標はキャッシュミスのはず"
    
    # 統計情報を確認
    stats = cache.get_cache_stats()
    print(f"キャッシュヒット: {stats['cache_hits']}")
    print(f"キャッシュミス: {stats['cache_misses']}")
    print(f"ヒット率: {stats['hit_rate']:.2%}")
    print(f"キャッシュサイズ: {stats['cache_size']}")
    
    # 期限切れクリーンアップテスト
    time.sleep(2.1)
    expired_count = cache.cleanup_expired()
    print(f"期限切れエントリ削除数: {expired_count}")
    assert expired_count == 1, "1つのエントリが期限切れのはず"
    
    print("✓ OCRCache テスト成功\n")


if __name__ == "__main__":
    test_detection_cache()
    test_ocr_cache()
    print("=== 全テスト成功 ===")
