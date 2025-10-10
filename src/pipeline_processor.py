"""
パイプラインプロセッサモジュール

このモジュールは、リアルタイムOCRアプリケーションの並列処理パイプラインを管理します。
キャプチャ、検出、OCR処理を独立したスレッドで実行し、高いパフォーマンスを実現します。
"""

import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Callable
import logging

import numpy as np

from src.config import AppConfig
from src.window_capture import WindowCapture
from src.object_detector import ObjectDetector, DetectionResult
from src.ocr_processor import OCRProcessor
from src.data_manager import DataManager
from src.detection_cache import DetectionCache
from src.ocr_cache import OCRCache
from src.performance_monitor import PerformanceMonitor
from src.performance_mode import PerformanceMode, get_performance_mode
from src.visualizer import Visualizer

# ロガー設定
logger = logging.getLogger(__name__)


class PipelineProcessor:
    """パイプライン処理マネージャー
    
    キャプチャ、検出、OCR処理を並列実行し、高速なリアルタイムOCR処理を実現します。
    
    処理フロー:
        [キャプチャスレッド] → [フレームキュー] → [検出スレッド] → [検出結果キュー] 
        → [OCRスレッドプール] → [データマネージャー]
                                    ↓
        [表示スレッド] ← [表示キュー] ←┘
    """
    
    def __init__(self, config: AppConfig, performance_mode: str = "balanced",
                 on_new_text_callback: Optional[Callable[[str], None]] = None):
        """
        PipelineProcessorを初期化
        
        Args:
            config: アプリケーション設定
            performance_mode: パフォーマンスモード（"fast", "balanced", "accurate"）
            on_new_text_callback: 新規テキスト検出時のコールバック関数
        """
        self.config = config
        self.mode = get_performance_mode(performance_mode)
        self.on_new_text_callback = on_new_text_callback
        
        # Components
        self.window_capture: Optional[WindowCapture] = None
        self.object_detector: Optional[ObjectDetector] = None
        self.ocr_processor: Optional[OCRProcessor] = None
        self.data_manager: Optional[DataManager] = None
        self.visualizer: Optional[Visualizer] = None
        
        # Caches
        self.detection_cache = DetectionCache() if self.mode.detection_cache_enabled else None
        self.ocr_cache = OCRCache() if self.mode.ocr_cache_enabled else None
        
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()
        
        # Threads and queues
        self.frame_queue: queue.Queue = queue.Queue(maxsize=2)
        self.detection_queue: queue.Queue = queue.Queue(maxsize=5)
        self.display_queue: queue.Queue = queue.Queue(maxsize=2)
        
        self.capture_thread: Optional[threading.Thread] = None
        self.detection_thread: Optional[threading.Thread] = None
        self.ocr_executor: Optional[ThreadPoolExecutor] = None
        
        # Control
        self.stop_event = threading.Event()
        self.frame_counter = 0
        
        logger.info(f"PipelineProcessor initialized with mode: {self.mode.name}")
    
    def start(self) -> None:
        """パイプライン処理を開始
        
        各コンポーネントを初期化し、処理スレッドを起動します。
        
        Raises:
            RuntimeError: コンポーネントの初期化に失敗した場合
        """
        try:
            # コンポーネントの初期化
            self._initialize_components()
            
            # スレッドの起動
            self.stop_event.clear()
            
            # キャプチャスレッド
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                name="CaptureThread",
                daemon=True
            )
            self.capture_thread.start()
            
            # 検出スレッド
            self.detection_thread = threading.Thread(
                target=self._detection_loop,
                name="DetectionThread",
                daemon=True
            )
            self.detection_thread.start()
            
            # OCRスレッドプール
            self.ocr_executor = ThreadPoolExecutor(
                max_workers=self.mode.ocr_workers,
                thread_name_prefix="OCRWorker"
            )
            
            logger.info("Pipeline started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start pipeline: {e}")
            self.stop()
            raise RuntimeError(f"パイプラインの起動に失敗しました: {e}")
    
    def stop(self) -> None:
        """パイプライン処理を停止
        
        全てのスレッドを停止し、リソースをクリーンアップします。
        """
        logger.info("Stopping pipeline...")
        
        try:
            # 停止シグナルを送信
            self.stop_event.set()
            
            # スレッドの終了を待機
            if self.capture_thread and self.capture_thread.is_alive():
                logger.debug("Waiting for capture thread to stop...")
                self.capture_thread.join(timeout=2.0)
                if self.capture_thread.is_alive():
                    logger.warning("Capture thread did not stop gracefully")
            
            if self.detection_thread and self.detection_thread.is_alive():
                logger.debug("Waiting for detection thread to stop...")
                self.detection_thread.join(timeout=2.0)
                if self.detection_thread.is_alive():
                    logger.warning("Detection thread did not stop gracefully")
            
            # OCRスレッドプールのシャットダウン
            if self.ocr_executor:
                logger.debug("Shutting down OCR thread pool...")
                try:
                    self.ocr_executor.shutdown(wait=True, cancel_futures=True)
                except Exception as e:
                    logger.error(f"Error shutting down OCR executor: {e}")
                finally:
                    self.ocr_executor = None
            
            # キューをクリア
            self._clear_queue(self.frame_queue)
            self._clear_queue(self.detection_queue)
            self._clear_queue(self.display_queue)
            
            # コンポーネントのクリーンアップ
            self._cleanup_components()
            
            logger.info("Pipeline stopped successfully")
            
        except Exception as e:
            logger.error(f"Error during pipeline shutdown: {e}")
            # エラーが発生してもクリーンアップを試みる
            try:
                self._cleanup_components()
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {cleanup_error}")
    
    def _initialize_components(self) -> None:
        """コンポーネントを初期化"""
        # ウィンドウキャプチャ
        self.window_capture = WindowCapture(self.config.target_window_title)
        self.window_capture.find_window()
        
        # 物体検出
        self.object_detector = ObjectDetector(
            model_path=self.config.model_path,
            confidence_threshold=self.config.confidence_threshold
        )
        
        # OCR処理
        self.ocr_processor = OCRProcessor(
            lang=self.config.ocr_lang,
            margin=self.config.ocr_margin
        )
        
        # データマネージャー
        self.data_manager = DataManager(
            output_path=self.config.output_csv,
            on_new_text_callback=self.on_new_text_callback
        )
        
        # Visualizer
        self.visualizer = Visualizer(window_name=self.config.display_window_name)
        
        logger.info("All components initialized")
    
    @staticmethod
    def _clear_queue(q: queue.Queue) -> None:
        """キューをクリア
        
        Args:
            q: クリアするキュー
        """
        try:
            while not q.empty():
                try:
                    q.get_nowait()
                except queue.Empty:
                    break
        except Exception as e:
            logger.error(f"Error clearing queue: {e}")
    
    def _cleanup_components(self) -> None:
        """コンポーネントのリソースをクリーンアップ
        
        各コンポーネントが保持しているリソース（ウィンドウ、モデルなど）を
        適切に解放します。
        """
        try:
            # Visualizerのクリーンアップ
            if self.visualizer:
                try:
                    self.visualizer.close()
                except Exception as e:
                    logger.error(f"Error closing visualizer: {e}")
                finally:
                    self.visualizer = None
            
            # WindowCaptureのクリーンアップ
            if self.window_capture:
                try:
                    # WindowCaptureは__del__でクリーンアップされるが、明示的に参照を削除
                    del self.window_capture
                except Exception as e:
                    logger.error(f"Error cleaning up window capture: {e}")
                finally:
                    self.window_capture = None
            
            # その他のコンポーネントの参照をクリア
            self.object_detector = None
            self.ocr_processor = None
            self.data_manager = None
            
            logger.debug("Components cleaned up")
            
        except Exception as e:
            logger.error(f"Error during component cleanup: {e}")
    
    def _capture_loop(self) -> None:
        """キャプチャスレッドのメインループ
        
        ウィンドウキャプチャを独立スレッドで実行し、
        フレームキューに非ブロッキングで追加します。
        """
        logger.info("Capture thread started")
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        try:
            while not self.stop_event.is_set():
                try:
                    # パフォーマンス計測開始
                    self.performance_monitor.start_timer('capture')
                    
                    # フレームをキャプチャ
                    frame = self.window_capture.capture_frame()
                    
                    # パフォーマンス計測終了
                    self.performance_monitor.end_timer('capture')
                    
                    # 成功したらエラーカウンタをリセット
                    consecutive_errors = 0
                    
                    # フレームキューに非ブロッキングで追加
                    # キューが満杯の場合は古いフレームを破棄
                    try:
                        self.frame_queue.put_nowait(frame)
                    except queue.Full:
                        # キューが満杯の場合、古いフレームを破棄して新しいフレームを追加
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put_nowait(frame)
                            self.performance_monitor.record_frame_skip()
                        except (queue.Empty, queue.Full):
                            pass
                    
                    # 30FPS目標で適度にスリープ
                    time.sleep(0.033)  # 約30FPS
                    
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(f"Error in capture loop (attempt {consecutive_errors}/{max_consecutive_errors}): {e}")
                    
                    # 連続エラーが多すぎる場合は停止
                    if consecutive_errors >= max_consecutive_errors:
                        logger.critical("Too many consecutive errors in capture loop, stopping thread")
                        self.stop_event.set()
                        break
                    
                    time.sleep(0.1)  # エラー時は少し待機
        
        except Exception as e:
            logger.critical(f"Fatal error in capture loop: {e}")
            self.stop_event.set()
        
        finally:
            logger.info("Capture thread stopped")
    
    def _detection_loop(self) -> None:
        """検出スレッドのメインループ
        
        フレームキューからフレームを取得し、物体検出を実行します。
        検出キャッシュを使用して重複検出を回避します。
        """
        logger.info("Detection thread started")
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        try:
            while not self.stop_event.is_set():
                try:
                    # フレームキューから取得（タイムアウト付き）
                    try:
                        frame = self.frame_queue.get(timeout=1.0)
                    except queue.Empty:
                        continue
                    
                    # フレームスキップ判定
                    self.frame_counter += 1
                    if self.frame_counter % self.mode.frame_skip != 0:
                        self.performance_monitor.record_frame_skip()
                        continue
                    
                    detections = None
                    
                    # 検出キャッシュが有効な場合（フォールバック処理付き）
                    if self.detection_cache:
                        try:
                            # キャッシュヒット判定
                            if self.detection_cache.should_skip_detection(frame):
                                detections = self.detection_cache.get_cached_detections()
                                if detections is not None:
                                    self.performance_monitor.record_cache_hit()
                                    logger.debug("Detection cache hit")
                                else:
                                    self.performance_monitor.record_cache_miss()
                            else:
                                self.performance_monitor.record_cache_miss()
                        except Exception as cache_error:
                            logger.warning(f"Detection cache error, falling back to detection: {cache_error}")
                            self.performance_monitor.record_cache_miss()
                            detections = None
                    
                    # キャッシュミスまたはキャッシュ無効の場合、検出を実行
                    if detections is None:
                        # パフォーマンス計測開始
                        self.performance_monitor.start_timer('detection')
                        
                        # 物体検出を実行
                        detections = self.object_detector.detect(frame)
                        
                        # パフォーマンス計測終了
                        self.performance_monitor.end_timer('detection')
                        
                        # 検出キャッシュを更新（エラー時はスキップ）
                        if self.detection_cache:
                            try:
                                self.detection_cache.update_cache(frame, detections)
                            except Exception as cache_error:
                                logger.warning(f"Failed to update detection cache: {cache_error}")
                    
                    # 検出数を制限
                    if len(detections) > self.mode.max_detections_per_frame:
                        # Y座標でソートして上位のみ処理
                        detections = ObjectDetector.sort_by_y_coordinate(detections)
                        detections = detections[:self.mode.max_detections_per_frame]
                    
                    # 検出結果キューに送信
                    detection_data = {
                        'frame': frame,
                        'detections': detections
                    }
                    
                    try:
                        self.detection_queue.put_nowait(detection_data)
                    except queue.Full:
                        # キューが満杯の場合、古いデータを破棄
                        try:
                            self.detection_queue.get_nowait()
                            self.detection_queue.put_nowait(detection_data)
                        except (queue.Empty, queue.Full):
                            pass
                    
                    # OCR処理を開始（非同期）
                    if detections:
                        self._process_ocr_parallel(frame, detections)
                    
                    # 検出結果を描画したフレームを表示キューに送信
                    self._send_to_display_queue(frame, detections)
                    
                    # 成功したらエラーカウンタをリセット
                    consecutive_errors = 0
                    
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(f"Error in detection loop (attempt {consecutive_errors}/{max_consecutive_errors}): {e}")
                    
                    # 連続エラーが多すぎる場合は停止
                    if consecutive_errors >= max_consecutive_errors:
                        logger.critical("Too many consecutive errors in detection loop, stopping thread")
                        self.stop_event.set()
                        break
                    
                    time.sleep(0.1)
        
        except Exception as e:
            logger.critical(f"Fatal error in detection loop: {e}")
            self.stop_event.set()
        
        finally:
            logger.info("Detection thread stopped")
    
    def _process_ocr_parallel(self, frame: np.ndarray, detections: List[DetectionResult]) -> None:
        """OCR処理を並列実行
        
        ThreadPoolExecutorを使用して、複数の検出領域に対して
        並列にOCR処理を実行します。
        
        Args:
            frame: 入力フレーム
            detections: 検出結果のリスト
        """
        if not detections or not self.ocr_executor:
            return
        
        # Y座標でソート（上から下へ優先度付き処理）
        sorted_detections = ObjectDetector.sort_by_y_coordinate(detections)
        
        # 各検出領域に対してOCR処理を並列実行
        def process_single_detection(bbox: DetectionResult) -> Optional[str]:
            """単一の検出領域に対してOCR処理を実行"""
            try:
                # OCRキャッシュが有効な場合（フォールバック処理付き）
                if self.ocr_cache:
                    try:
                        cached_text = self.ocr_cache.get_cached_text(bbox)
                        if cached_text is not None:
                            self.performance_monitor.record_cache_hit()
                            logger.debug(f"OCR cache hit for bbox: ({bbox.x1}, {bbox.y1})")
                            return cached_text
                        else:
                            self.performance_monitor.record_cache_miss()
                    except Exception as cache_error:
                        logger.warning(f"OCR cache error, falling back to OCR: {cache_error}")
                        self.performance_monitor.record_cache_miss()
                
                # パフォーマンス計測開始
                self.performance_monitor.start_timer('ocr')
                
                # OCR処理を実行
                text = self.ocr_processor.extract_text(frame, bbox)
                
                # パフォーマンス計測終了
                self.performance_monitor.end_timer('ocr')
                
                # OCRキャッシュを更新（エラー時はスキップ）
                if self.ocr_cache and text:
                    try:
                        self.ocr_cache.update_cache(bbox, text)
                    except Exception as cache_error:
                        logger.warning(f"Failed to update OCR cache: {cache_error}")
                
                return text
                
            except Exception as e:
                logger.error(f"Error in OCR processing for bbox ({bbox.x1}, {bbox.y1}): {e}")
                return None
        
        # 並列OCR処理を実行
        futures = []
        try:
            for bbox in sorted_detections:
                if self.stop_event.is_set():
                    # 停止シグナルが出ている場合は新しいタスクを投入しない
                    break
                future = self.ocr_executor.submit(process_single_detection, bbox)
                futures.append(future)
            
            # 結果を収集してデータマネージャーに送信
            for future in futures:
                if self.stop_event.is_set():
                    # 停止シグナルが出ている場合は残りの結果を待たない
                    future.cancel()
                    continue
                
                try:
                    text = future.result(timeout=5.0)  # 5秒タイムアウト
                    if text and len(text) >= self.config.min_text_length:
                        # データマネージャーに追加
                        try:
                            self.data_manager.add_text(text)
                        except Exception as dm_error:
                            logger.error(f"Error adding text to data manager: {dm_error}")
                except TimeoutError:
                    logger.warning(f"OCR processing timed out after 5 seconds")
                    future.cancel()
                except Exception as e:
                    logger.error(f"Error getting OCR result: {e}")
        
        except Exception as e:
            logger.error(f"Error in parallel OCR processing: {e}")
    
    def get_display_frame(self, timeout: float = 0.1) -> Optional[np.ndarray]:
        """表示用フレームを取得
        
        Args:
            timeout: タイムアウト時間（秒）
        
        Returns:
            表示用フレーム、またはNone
        """
        try:
            return self.display_queue.get(timeout=timeout)
        except queue.Empty:
            return None
        except Exception as e:
            logger.error(f"Error getting display frame: {e}")
            return None
    
    def _send_to_display_queue(self, frame: np.ndarray, detections: List[DetectionResult]) -> None:
        """検出結果を描画したフレームを表示キューに送信
        
        フレームスキップ戦略を実装し、古いフレームを破棄します。
        
        Args:
            frame: 入力フレーム
            detections: 検出結果のリスト
        """
        try:
            # パフォーマンス計測開始
            self.performance_monitor.start_timer('display')
            
            # 検出結果を描画
            annotated_frame = self.visualizer.draw_detections(frame, detections)
            
            # パフォーマンス計測終了
            self.performance_monitor.end_timer('display')
            
            # FPSを更新
            self.performance_monitor.update_fps()
            
            # 表示キューに送信（フレームスキップ戦略）
            # キューが満杯の場合、古いフレームを破棄して最新フレームを追加
            try:
                self.display_queue.put_nowait(annotated_frame)
            except queue.Full:
                # 古いフレームを全て破棄
                try:
                    while not self.display_queue.empty():
                        try:
                            self.display_queue.get_nowait()
                        except queue.Empty:
                            break
                    
                    # 最新フレームを追加
                    self.display_queue.put_nowait(annotated_frame)
                except (queue.Empty, queue.Full) as e:
                    logger.debug(f"Queue operation failed during frame skip: {e}")
        
        except Exception as e:
            logger.error(f"Error sending to display queue: {e}")
    
    def get_performance_report(self) -> dict:
        """パフォーマンスレポートを取得
        
        Returns:
            パフォーマンスメトリクスを含む辞書
        """
        try:
            return self.performance_monitor.get_report()
        except Exception as e:
            logger.error(f"Error getting performance report: {e}")
            return {
                'fps': 0.0,
                'avg_capture_time': 0.0,
                'avg_detection_time': 0.0,
                'avg_ocr_time': 0.0,
                'avg_display_time': 0.0,
                'cache_hit_rate': 0.0,
                'frames_processed': 0,
                'frames_skipped': 0
            }
    
    def is_running(self) -> bool:
        """パイプラインが実行中かどうかを確認
        
        Returns:
            実行中の場合True、それ以外False
        """
        return (
            not self.stop_event.is_set() and
            self.capture_thread is not None and
            self.detection_thread is not None and
            self.ocr_executor is not None
        )
