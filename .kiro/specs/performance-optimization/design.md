# Design Document

## Overview

現在のリアルタイムOCRアプリケーションは、1FPS未満のパフォーマンスで動作しています。コードレビューの結果、以下の主要なボトルネックが特定されました：

### 特定されたボトルネック

1. **同期的な処理フロー**: `gui_app.py`の`_processing_loop`では、キャプチャ→検出→OCR→描画が全て同期的に実行されている
2. **OCR処理の重複**: 同じ領域が連続して検出されても、毎回OCR処理を実行している
3. **全検出領域の逐次OCR処理**: 複数の検出領域に対して、forループで逐次的にOCR処理を実行している
4. **フレームキューの非効率**: `maxsize=2`のキューで、処理が遅い場合にフレームがブロックされる可能性がある

### パフォーマンス目標

- **現状**: < 1 FPS
- **目標**: ≥ 5 FPS
- **理想**: 10-15 FPS（リアルタイム体験）

## Architecture

### 新しい処理パイプライン

```
[キャプチャスレッド] → [フレームキューA] → [検出スレッド] → [検出結果キューB] → [OCRスレッドプール] → [データマネージャー]
                                                                                                    ↓
[表示スレッド] ← [表示キューC] ←────────────────────────────────────────────────────────────────────┘
```

### スレッド構成

1. **キャプチャスレッド**: ウィンドウキャプチャのみを担当（30FPS目標）
2. **検出スレッド**: YOLOv8による物体検出（10-15FPS目標）
3. **OCRワーカープール**: 複数スレッドで並列OCR処理（ThreadPoolExecutor使用）
4. **表示スレッド**: GUIへのフレーム表示（メインスレッド）

### キャッシング戦略

1. **検出結果キャッシュ**: 連続する類似フレームで検出をスキップ
2. **OCR結果キャッシュ**: 同じ領域（座標の近似一致）のOCR結果を再利用
3. **フレームスキップ**: 処理が追いつかない場合、古いフレームを破棄

## Components and Interfaces

### 1. PerformanceMonitor クラス

パフォーマンス計測とモニタリングを担当。

```python
class PerformanceMonitor:
    """パフォーマンス計測クラス"""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.fps_counter = FPSCounter()
    
    def start_timer(self, name: str) -> None:
        """タイマー開始"""
    
    def end_timer(self, name: str) -> float:
        """タイマー終了、経過時間を返す"""
    
    def get_average(self, name: str) -> float:
        """平均実行時間を取得"""
    
    def update_fps(self) -> float:
        """FPSを更新して返す"""
    
    def get_report(self) -> Dict[str, Any]:
        """パフォーマンスレポートを取得"""
```

### 2. DetectionCache クラス

検出結果のキャッシング。

```python
class DetectionCache:
    """検出結果キャッシュ"""
    
    def __init__(self, ttl: float = 0.5, similarity_threshold: float = 0.95):
        self.cache: Optional[CacheEntry] = None
        self.ttl = ttl  # Time to live (seconds)
        self.similarity_threshold = similarity_threshold
    
    def should_skip_detection(self, frame: np.ndarray) -> bool:
        """フレームが類似している場合、検出をスキップすべきか判定"""
    
    def get_cached_detections(self) -> Optional[List[DetectionResult]]:
        """キャッシュされた検出結果を取得"""
    
    def update_cache(self, frame: np.ndarray, detections: List[DetectionResult]) -> None:
        """キャッシュを更新"""
```

### 3. OCRCache クラス

OCR結果のキャッシング。

```python
class OCRCache:
    """OCR結果キャッシュ"""
    
    def __init__(self, position_tolerance: int = 10):
        self.cache: Dict[str, CachedOCRResult] = {}
        self.position_tolerance = position_tolerance
    
    def get_cached_text(self, bbox: DetectionResult) -> Optional[str]:
        """座標が近い領域のキャッシュされたテキストを取得"""
    
    def update_cache(self, bbox: DetectionResult, text: str) -> None:
        """OCR結果をキャッシュに追加"""
    
    def _get_cache_key(self, bbox: DetectionResult) -> str:
        """バウンディングボックスからキャッシュキーを生成"""
```

### 4. PipelineProcessor クラス

新しいパイプライン処理を管理。

```python
class PipelineProcessor:
    """パイプライン処理マネージャー"""
    
    def __init__(self, config: AppConfig, performance_mode: str = "balanced"):
        self.config = config
        self.performance_mode = performance_mode
        
        # Components
        self.window_capture: Optional[WindowCapture] = None
        self.object_detector: Optional[ObjectDetector] = None
        self.ocr_processor: Optional[OCRProcessor] = None
        self.data_manager: Optional[DataManager] = None
        
        # Caches
        self.detection_cache = DetectionCache()
        self.ocr_cache = OCRCache()
        
        # Performance
        self.performance_monitor = PerformanceMonitor()
        
        # Threads and queues
        self.frame_queue: queue.Queue = queue.Queue(maxsize=2)
        self.detection_queue: queue.Queue = queue.Queue(maxsize=5)
        self.display_queue: queue.Queue = queue.Queue(maxsize=2)
        
        self.capture_thread: Optional[threading.Thread] = None
        self.detection_thread: Optional[threading.Thread] = None
        self.ocr_executor: Optional[ThreadPoolExecutor] = None
        
        self.stop_event = threading.Event()
    
    def start(self) -> None:
        """パイプライン処理を開始"""
    
    def stop(self) -> None:
        """パイプライン処理を停止"""
    
    def _capture_loop(self) -> None:
        """キャプチャスレッドのメインループ"""
    
    def _detection_loop(self) -> None:
        """検出スレッドのメインループ"""
    
    def _process_ocr_parallel(self, frame: np.ndarray, detections: List[DetectionResult]) -> None:
        """OCR処理を並列実行"""
```

### 5. パフォーマンスモード設定

```python
@dataclass
class PerformanceMode:
    """パフォーマンスモード設定"""
    name: str
    frame_skip: int  # N フレームに1回処理
    detection_cache_enabled: bool
    ocr_cache_enabled: bool
    ocr_workers: int
    max_detections_per_frame: int

# プリセット
PERFORMANCE_MODES = {
    "fast": PerformanceMode(
        name="高速",
        frame_skip=2,  # 2フレームに1回
        detection_cache_enabled=True,
        ocr_cache_enabled=True,
        ocr_workers=4,
        max_detections_per_frame=5
    ),
    "balanced": PerformanceMode(
        name="バランス",
        frame_skip=1,  # 全フレーム処理
        detection_cache_enabled=True,
        ocr_cache_enabled=True,
        ocr_workers=3,
        max_detections_per_frame=10
    ),
    "accurate": PerformanceMode(
        name="高精度",
        frame_skip=1,
        detection_cache_enabled=False,
        ocr_cache_enabled=False,
        ocr_workers=2,
        max_detections_per_frame=20
    )
}
```

## Data Models

### CacheEntry

```python
@dataclass
class CacheEntry:
    """キャッシュエントリ"""
    timestamp: float
    frame_hash: int  # フレームの簡易ハッシュ
    detections: List[DetectionResult]
```

### CachedOCRResult

```python
@dataclass
class CachedOCRResult:
    """キャッシュされたOCR結果"""
    text: str
    bbox: DetectionResult
    timestamp: float
```

### PerformanceMetrics

```python
@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""
    fps: float
    avg_capture_time: float
    avg_detection_time: float
    avg_ocr_time: float
    avg_display_time: float
    cache_hit_rate: float
    frames_processed: int
    frames_skipped: int
```

## Error Handling

### エラー処理戦略

1. **スレッドエラー**: 各スレッドで例外をキャッチし、エラーキューに送信
2. **キュータイムアウト**: `queue.get(timeout=1.0)`を使用して、デッドロックを防止
3. **リソースクリーンアップ**: `stop()`メソッドで全スレッドを適切に終了
4. **フォールバック**: キャッシュエラー時は通常処理にフォールバック

### エラーログ

```python
class PipelineError(Exception):
    """パイプライン処理エラー"""
    pass

# エラーハンドリング例
try:
    result = self.detection_cache.get_cached_detections()
except Exception as e:
    logger.warning(f"Cache error, falling back to detection: {e}")
    result = self.object_detector.detect(frame)
```

## Testing Strategy

### パフォーマンステスト

1. **ベンチマークテスト**: 各処理ステップの実行時間を計測
2. **負荷テスト**: 連続実行時のFPS安定性を検証
3. **キャッシュ効果テスト**: キャッシュ有無でのパフォーマンス比較

### テストケース

```python
def test_performance_improvement():
    """パフォーマンス改善を検証"""
    # Before: 同期処理
    fps_before = measure_fps_sync()
    
    # After: パイプライン処理
    fps_after = measure_fps_pipeline()
    
    assert fps_after >= 5.0, f"FPS目標未達: {fps_after}"
    assert fps_after > fps_before * 3, "3倍以上の改善が必要"

def test_cache_effectiveness():
    """キャッシュの効果を検証"""
    processor = PipelineProcessor(config, performance_mode="balanced")
    
    # 同じフレームを連続処理
    for _ in range(10):
        processor.process_frame(test_frame)
    
    metrics = processor.performance_monitor.get_report()
    assert metrics['cache_hit_rate'] > 0.7, "キャッシュヒット率が低い"

def test_parallel_ocr():
    """並列OCR処理を検証"""
    # 複数検出領域での処理時間を計測
    start = time.time()
    results = process_ocr_parallel(frame, detections)
    elapsed = time.time() - start
    
    # 逐次処理との比較
    start = time.time()
    results_seq = process_ocr_sequential(frame, detections)
    elapsed_seq = time.time() - start
    
    assert elapsed < elapsed_seq * 0.6, "並列処理の効果が不十分"
```

## Implementation Notes

### フレームハッシュの計算

フレーム類似度判定のため、軽量なハッシュを使用：

```python
def compute_frame_hash(frame: np.ndarray) -> int:
    """フレームの簡易ハッシュを計算"""
    # ダウンサンプリングして高速化
    small = cv2.resize(frame, (64, 64))
    # 平均ハッシュ
    avg = small.mean()
    binary = (small > avg).astype(np.uint8)
    return hash(binary.tobytes())
```

### 座標の近似一致判定

OCRキャッシュのため、座標の近似一致を判定：

```python
def is_bbox_similar(bbox1: DetectionResult, bbox2: DetectionResult, tolerance: int = 10) -> bool:
    """2つのバウンディングボックスが近似しているか判定"""
    return (
        abs(bbox1.x1 - bbox2.x1) <= tolerance and
        abs(bbox1.y1 - bbox2.y1) <= tolerance and
        abs(bbox1.x2 - bbox2.x2) <= tolerance and
        abs(bbox1.y2 - bbox2.y2) <= tolerance
    )
```

### スレッドセーフなキュー操作

```python
def safe_queue_put(q: queue.Queue, item: Any, timeout: float = 0.1) -> bool:
    """タイムアウト付きキュー追加"""
    try:
        q.put(item, timeout=timeout)
        return True
    except queue.Full:
        return False

def safe_queue_get(q: queue.Queue, timeout: float = 1.0) -> Optional[Any]:
    """タイムアウト付きキュー取得"""
    try:
        return q.get(timeout=timeout)
    except queue.Empty:
        return None
```

## Performance Optimization Techniques

### 1. フレームスキップ戦略

```python
# 処理が追いつかない場合、古いフレームを破棄
while not self.frame_queue.empty():
    try:
        self.frame_queue.get_nowait()  # 古いフレームを破棄
    except queue.Empty:
        break
frame = self.frame_queue.get()  # 最新フレームを取得
```

### 2. 適応的キャッシュTTL

```python
# FPSに応じてキャッシュTTLを調整
if current_fps < 3.0:
    self.detection_cache.ttl = 1.0  # 長めに保持
elif current_fps > 10.0:
    self.detection_cache.ttl = 0.3  # 短めに保持
```

### 3. 優先度付きOCR処理

```python
# 画面上部の検出領域を優先的に処理
detections_sorted = sorted(detections, key=lambda d: d.y1)
for detection in detections_sorted[:max_detections]:
    # OCR処理
```

## Integration with Existing Code

### GUI統合

`gui_app.py`の`RealtimeOCRGUI`クラスに以下を追加：

```python
class RealtimeOCRGUI:
    def __init__(self, root: tk.Tk):
        # ...existing code...
        
        # パフォーマンスモード選択
        self.performance_mode_var = tk.StringVar(value="balanced")
        
        # パイプラインプロセッサ
        self.pipeline_processor: Optional[PipelineProcessor] = None
    
    def _start_processing(self):
        """パイプライン処理を開始"""
        self.pipeline_processor = PipelineProcessor(
            config=self.config,
            performance_mode=self.performance_mode_var.get()
        )
        self.pipeline_processor.start()
    
    def _update_performance_stats(self):
        """パフォーマンス統計を更新"""
        if self.pipeline_processor:
            metrics = self.pipeline_processor.performance_monitor.get_report()
            self.fps_var.set(f"{metrics['fps']:.1f}")
            # その他のメトリクスも更新
```

### 後方互換性

既存のCLIモード（`realtime_ocr_app.py`）は維持し、GUIモードでのみ新しいパイプライン処理を使用。

## Expected Performance Improvements

### 予測される改善効果

| 最適化手法 | 予測改善率 | 根拠 |
|-----------|----------|------|
| 並列処理（キャプチャ/検出分離） | +100% | 処理のオーバーラップ |
| OCR並列化（4ワーカー） | +200% | 4コア活用 |
| 検出キャッシュ | +50% | 類似フレームでの検出スキップ |
| OCRキャッシュ | +100% | 同一領域の再処理回避 |
| フレームスキップ | +30% | 処理負荷軽減 |

### 総合予測

- **現状**: < 1 FPS
- **改善後**: 8-12 FPS（8-12倍の改善）
- **目標達成**: ✓ 5 FPS以上

### 段階的な改善計画

1. **Phase 1**: パフォーマンス計測の実装 → ボトルネック確認
2. **Phase 2**: 並列処理の導入 → 3-5 FPS達成
3. **Phase 3**: キャッシング実装 → 8-10 FPS達成
4. **Phase 4**: 最適化とチューニング → 10-15 FPS達成
