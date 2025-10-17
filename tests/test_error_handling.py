#!/usr/bin/env python3
"""
エラーハンドリングとクリーンアップのテスト

このスクリプトは、PipelineProcessorのエラーハンドリングと
リソースクリーンアップ機能をテストします。
"""

import time
import logging
from src.config import AppConfig
from src.pipeline_processor import PipelineProcessor

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_normal_start_stop():
    """正常な起動と停止のテスト"""
    logger.info("=== Test 1: Normal start and stop ===")
    
    try:
        config = AppConfig()
        config.target_window_title = "iPhone"
        
        processor = PipelineProcessor(config, performance_mode="balanced")
        
        logger.info("Starting pipeline...")
        processor.start()
        
        logger.info("Pipeline running, waiting 3 seconds...")
        time.sleep(3)
        
        logger.info("Stopping pipeline...")
        processor.stop()
        
        logger.info("✓ Test 1 passed: Normal start and stop")
        return True
        
    except Exception as e:
        logger.error(f"✗ Test 1 failed: {e}")
        return False


def test_quick_start_stop():
    """素早い起動と停止のテスト（デッドロック防止）"""
    logger.info("=== Test 2: Quick start and stop ===")
    
    try:
        config = AppConfig()
        config.target_window_title = "iPhone"
        
        processor = PipelineProcessor(config, performance_mode="fast")
        
        logger.info("Starting pipeline...")
        processor.start()
        
        logger.info("Immediately stopping pipeline...")
        time.sleep(0.1)  # 100ms待機
        processor.stop()
        
        logger.info("✓ Test 2 passed: Quick start and stop")
        return True
        
    except Exception as e:
        logger.error(f"✗ Test 2 failed: {e}")
        return False


def test_multiple_stop_calls():
    """複数回のstop呼び出しのテスト"""
    logger.info("=== Test 3: Multiple stop calls ===")
    
    try:
        config = AppConfig()
        config.target_window_title = "iPhone"
        
        processor = PipelineProcessor(config, performance_mode="balanced")
        
        logger.info("Starting pipeline...")
        processor.start()
        
        time.sleep(1)
        
        logger.info("Stopping pipeline (1st call)...")
        processor.stop()
        
        logger.info("Stopping pipeline again (2nd call)...")
        processor.stop()
        
        logger.info("Stopping pipeline again (3rd call)...")
        processor.stop()
        
        logger.info("✓ Test 3 passed: Multiple stop calls handled gracefully")
        return True
        
    except Exception as e:
        logger.error(f"✗ Test 3 failed: {e}")
        return False


def test_performance_report_after_stop():
    """停止後のパフォーマンスレポート取得のテスト"""
    logger.info("=== Test 4: Performance report after stop ===")
    
    try:
        config = AppConfig()
        config.target_window_title = "iPhone"
        
        processor = PipelineProcessor(config, performance_mode="balanced")
        
        logger.info("Starting pipeline...")
        processor.start()
        
        time.sleep(2)
        
        logger.info("Getting performance report while running...")
        report1 = processor.get_performance_report()
        logger.info(f"Report while running: FPS={report1.get('fps', 0):.2f}")
        
        logger.info("Stopping pipeline...")
        processor.stop()
        
        logger.info("Getting performance report after stop...")
        report2 = processor.get_performance_report()
        logger.info(f"Report after stop: FPS={report2.get('fps', 0):.2f}")
        
        logger.info("✓ Test 4 passed: Performance report accessible after stop")
        return True
        
    except Exception as e:
        logger.error(f"✗ Test 4 failed: {e}")
        return False


def test_is_running_status():
    """is_running()ステータスのテスト"""
    logger.info("=== Test 5: is_running() status ===")
    
    try:
        config = AppConfig()
        config.target_window_title = "iPhone"
        
        processor = PipelineProcessor(config, performance_mode="balanced")
        
        logger.info("Checking status before start...")
        if processor.is_running():
            logger.error("✗ Test 5 failed: is_running() should be False before start")
            return False
        
        logger.info("Starting pipeline...")
        processor.start()
        
        time.sleep(0.5)
        
        logger.info("Checking status while running...")
        if not processor.is_running():
            logger.error("✗ Test 5 failed: is_running() should be True while running")
            processor.stop()
            return False
        
        logger.info("Stopping pipeline...")
        processor.stop()
        
        time.sleep(0.5)
        
        logger.info("Checking status after stop...")
        if processor.is_running():
            logger.error("✗ Test 5 failed: is_running() should be False after stop")
            return False
        
        logger.info("✓ Test 5 passed: is_running() status correct")
        return True
        
    except Exception as e:
        logger.error(f"✗ Test 5 failed: {e}")
        return False


def main():
    """メインテスト実行"""
    logger.info("Starting error handling and cleanup tests...")
    logger.info("=" * 60)
    
    results = []
    
    # Test 1: 正常な起動と停止
    results.append(("Normal start/stop", test_normal_start_stop()))
    time.sleep(1)
    
    # Test 2: 素早い起動と停止
    results.append(("Quick start/stop", test_quick_start_stop()))
    time.sleep(1)
    
    # Test 3: 複数回のstop呼び出し
    results.append(("Multiple stop calls", test_multiple_stop_calls()))
    time.sleep(1)
    
    # Test 4: 停止後のパフォーマンスレポート
    results.append(("Performance report after stop", test_performance_report_after_stop()))
    time.sleep(1)
    
    # Test 5: is_running()ステータス
    results.append(("is_running() status", test_is_running_status()))
    
    # 結果サマリー
    logger.info("=" * 60)
    logger.info("Test Results Summary:")
    logger.info("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info("=" * 60)
    logger.info(f"Total: {passed} passed, {failed} failed out of {len(results)} tests")
    logger.info("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
