# 修正: GUIの抽出データログ表示

## 問題
タスク6のエラーハンドリング実装後、GUIアプリケーションの「抽出データログ」に新規テキストが表示されなくなっていました。

## 原因
`DataManager.add_text()`メソッドは新規テキストを検出しても、GUIアプリケーションに通知する仕組みがありませんでした。以前の実装では、この通知機能が欠けていました。

## 解決策
コールバックパターンを実装して、新規テキスト検出時にGUIアプリケーションに通知する仕組みを追加しました。

## 実装内容

### 1. DataManager (`src/data_manager.py`)

#### コールバック機能の追加

```python
from typing import Set, Callable, Optional

class DataManager:
    def __init__(self, output_path: str = "book_data_realtime.csv", 
                 on_new_text_callback: Optional[Callable[[str], None]] = None):
        """
        Args:
            output_path: 出力CSVファイルのパス
            on_new_text_callback: 新規テキスト追加時に呼び出されるコールバック関数
        """
        self.output_path = Path(output_path)
        self.extracted_texts: Set[str] = set()
        self.on_new_text_callback = on_new_text_callback
```

#### add_text()メソッドの改善

```python
def add_text(self, text: str) -> bool:
    # ... 既存の処理 ...
    
    # 新規データとして追加
    self.extracted_texts.add(normalized_text)
    
    # ターミナルに出力
    print(f"[新規データ検出] {normalized_text}")
    
    # コールバックを呼び出し
    if self.on_new_text_callback:
        try:
            self.on_new_text_callback(normalized_text)
        except Exception as e:
            print(f"[警告] コールバック実行エラー: {e}")
    
    return True
```

**特徴:**
- コールバックはオプショナル（後方互換性を維持）
- コールバック実行時のエラーは警告として記録し、処理は継続
- 新規テキストの場合のみコールバックを呼び出し

### 2. PipelineProcessor (`src/pipeline_processor.py`)

#### コンストラクタの拡張

```python
def __init__(self, config: AppConfig, performance_mode: str = "balanced",
             on_new_text_callback: Optional[Callable[[str], None]] = None):
    """
    Args:
        config: アプリケーション設定
        performance_mode: パフォーマンスモード
        on_new_text_callback: 新規テキスト検出時のコールバック関数
    """
    self.config = config
    self.mode = get_performance_mode(performance_mode)
    self.on_new_text_callback = on_new_text_callback
```

#### DataManager初期化時にコールバックを渡す

```python
def _initialize_components(self) -> None:
    # ... 他のコンポーネント初期化 ...
    
    # データマネージャー
    self.data_manager = DataManager(
        output_path=self.config.output_csv,
        on_new_text_callback=self.on_new_text_callback
    )
```

### 3. GUI Application (`src/gui_app.py`)

#### コールバック関数の実装

```python
def _on_new_text_detected(self, text: str):
    """新規テキスト検出時のコールバック
    
    Args:
        text: 検出された新規テキスト
    """
    # ログキューに新規テキストを追加
    self.log_queue.put((f"[新規] {text}", 'new'))
```

#### PipelineProcessor初期化時にコールバックを渡す

```python
def _start_processing_with_mode(self, mode_key: str):
    try:
        # PipelineProcessorを初期化
        self.pipeline_processor = PipelineProcessor(
            config=self.config,
            performance_mode=mode_key,
            on_new_text_callback=self._on_new_text_detected  # コールバックを渡す
        )
```

## データフロー

```
[OCR処理]
    ↓
[DataManager.add_text()]
    ↓
[新規テキスト検出]
    ↓
[on_new_text_callback() 呼び出し]
    ↓
[GUI._on_new_text_detected()]
    ↓
[log_queue.put()]
    ↓
[GUI._process_queues()]
    ↓
[ログテキストウィジェットに表示]
```

## テスト結果

### 1. コールバック機能のテスト (`test_data_manager_callback.py`)

```
Test 1: 新規テキストの追加 ✓ PASSED
Test 2: 重複テキストの追加 ✓ PASSED
Test 3: 複数の新規テキスト ✓ PASSED
Test 4: コールバックなしのDataManager ✓ PASSED

=== All tests passed! ===
```

### 2. エラーハンドリングテスト (`test_error_handling.py`)

既存のエラーハンドリングテストも引き続き成功：

```
Total: 5 passed, 0 failed out of 5 tests
```

## 後方互換性

この実装は完全に後方互換性があります：

1. **コールバックはオプショナル**: `on_new_text_callback`を指定しない場合、従来通り動作
2. **既存のAPIは変更なし**: `add_text()`の戻り値や動作は変更なし
3. **エラー時も安全**: コールバック実行エラーは警告として記録し、処理は継続

## 利点

### 1. 疎結合
- DataManagerはGUIの実装詳細を知る必要がない
- コールバックパターンで柔軟な通知が可能

### 2. 拡張性
- 複数のコールバックを追加可能（将来の拡張）
- 異なるUIフレームワークでも同じDataManagerを使用可能

### 3. テスタビリティ
- コールバック機能を独立してテスト可能
- モックコールバックで動作を検証可能

## まとめ

GUIの抽出データログ表示機能を修正しました：

- ✓ DataManagerにコールバック機能を追加
- ✓ PipelineProcessorでコールバックを中継
- ✓ GUIアプリケーションでコールバックを実装
- ✓ 後方互換性を維持
- ✓ 全てのテストが成功
- ✓ エラーハンドリングも適切に実装

これで、新規テキストが検出されると、GUIの「抽出データログ」に即座に表示されるようになりました。
