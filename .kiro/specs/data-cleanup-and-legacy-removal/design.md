# Design Document

## Overview

このデザインドキュメントは、リアルタイムOCRアプリケーションの2つの主要な改善の実装設計を定義します：

1. **既存モデル（Legacy Mode）の完全削除**: 階層的検出モデルに完全移行し、コードベースをシンプル化
2. **データエディター機能の追加**: 抽出データの確認・編集・管理を行うGUIコンポーネント

## Architecture

### 全体アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                      Main GUI Window                         │
│  ┌──────────────────────┐  ┌──────────────────────────────┐ │
│  │   Control Panel      │  │      Preview Canvas          │ │
│  │  - Window Selection  │  │  - Real-time Detection       │ │
│  │  - Start/Stop        │  │  - Bounding Box Display      │ │
│  │  - Settings          │  │                              │ │
│  │  - [Data Editor]     │  │                              │ │
│  └──────────────────────┘  └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Opens
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Editor Window                         │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Toolbar: [Import] [Export] [Filter] [Statistics]       │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              Records Table (Treeview)                    │ │
│  │  ┌────┬────────┬────────┬──────┬──────┬──────┬────────┐ │ │
│  │  │ ✓  │ Title  │Progress│ Date │ Site │Error │Actions │ │ │
│  │  ├────┼────────┼────────┼──────┼──────┼──────┼────────┤ │ │
│  │  │[✓] │ 転生... │ 50%    │12/01 │ Web  │ OK   │[Edit]  │ │ │
│  │  │[ ] │ 異世... │ 30%    │12/02 │ App  │Error │[Del]   │ │ │
│  │  └────┴────────┴────────┴──────┴──────┴──────┴────────┘ │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ On Confirm
                              ▼
┌─────────────────────────────────────────────────────────────┐
│            Duplicate Detection Modal                         │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Confirming Record (Editable):                           │ │
│  │  Title: [転生したらスライムだった件_____________]        │ │
│  │  Progress: [50%___] Date: [12/01___] Site: [Web___]     │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Similar Records (Select to Delete):                     │ │
│  │  [✓] 転生したらスライムだつた件 (Similarity: 0.95)       │ │
│  │  [✓] 転生したらスライムだった (Similarity: 0.88)         │ │
│  │  [ ] 転生貴族の異世界冒険録 (Similarity: 0.72)           │ │
│  └──────────────────────────────────────────────────────────┘ │
│  [Confirm & Delete Selected] [Cancel]                        │
└─────────────────────────────────────────────────────────────┘
```

### コンポーネント構成

#### 削除対象コンポーネント（Legacy Mode関連）

1. **PipelineProcessor** - 既存モードの並列処理パイプライン
2. **DataManager** - 既存モードのシンプルなデータ管理
3. **GUI内のLegacy Mode選択UI** - ラジオボタンとモード切り替えロジック
4. **Config内のmodel_path** - best.ptへの参照

#### 新規コンポーネント

1. **DataEditorWindow** - データ編集用の独立ウィンドウ
2. **DuplicateDetectionModal** - 重複検出・削除モーダル
3. **RecordTableManager** - テーブル表示・編集ロジック
4. **CSVImportExport** - CSV入出力ハンドラー

## Components and Interfaces

### 1. DataEditorWindow

データ編集用のToplevelウィンドウ。

```python
class DataEditorWindow:
    """データエディターウィンドウ
    
    抽出されたレコードを表形式で表示し、編集・削除・確定・
    ソート・フィルタリング機能を提供します。
    """
    
    def __init__(self, parent: tk.Tk, data_manager: HierarchicalDataManager):
        """
        Args:
            parent: 親ウィンドウ
            data_manager: データマネージャーへの参照
        """
        self.window = tk.Toplevel(parent)
        self.data_manager = data_manager
        self.table_manager = RecordTableManager(self.window, data_manager)
        self.csv_handler = CSVImportExport(data_manager)
        
        # UI components
        self.toolbar: ttk.Frame
        self.table: ttk.Treeview
        self.stats_panel: ttk.Frame
        
        # State
        self.current_filter: str = "all"
        self.current_sort_column: Optional[str] = None
        self.current_sort_direction: str = "asc"
        self.edit_history: List[EditAction] = []
    
    def setup_ui(self) -> None:
        """UIコンポーネントをセットアップ"""
        pass
    
    def refresh_table(self) -> None:
        """テーブル表示を更新"""
        pass
    
    def on_import_csv(self) -> None:
        """CSVインポート処理"""
        pass
    
    def on_export_csv(self) -> None:
        """CSVエクスポート処理"""
        pass
    
    def on_filter_changed(self, filter_type: str) -> None:
        """フィルター変更処理"""
        pass
    
    def on_column_header_click(self, column: str) -> None:
        """列ヘッダークリック処理（ソート）"""
        pass
```

### 2. RecordTableManager

テーブル表示と編集ロジックを管理。

```python
class RecordTableManager:
    """レコードテーブル管理クラス
    
    Treeviewを使用したテーブル表示、インライン編集、
    行の選択・削除を管理します。
    """
    
    def __init__(self, parent: tk.Widget, data_manager: HierarchicalDataManager):
        self.parent = parent
        self.data_manager = data_manager
        self.tree: ttk.Treeview
        self.edit_entry: Optional[tk.Entry] = None
        self.editing_item: Optional[str] = None
        self.editing_column: Optional[str] = None
    
    def create_table(self) -> ttk.Treeview:
        """テーブルウィジェットを作成
        
        Returns:
            作成されたTreeviewウィジェット
        """
        pass
    
    def populate_table(self, records: List[StructuredRecord], 
                      filter_type: str = "all",
                      sort_column: Optional[str] = None,
                      sort_direction: str = "asc") -> None:
        """テーブルにレコードを表示
        
        Args:
            records: 表示するレコードリスト
            filter_type: フィルタータイプ（"all", "error", "no_error", "unconfirmed"）
            sort_column: ソート列名
            sort_direction: ソート方向（"asc" or "desc"）
        """
        pass
    
    def on_double_click(self, event) -> None:
        """セルダブルクリック処理（インライン編集開始）"""
        pass
    
    def on_edit_complete(self, event) -> None:
        """編集完了処理"""
        pass
    
    def on_delete_click(self, item_id: str) -> None:
        """削除ボタンクリック処理"""
        pass
    
    def on_confirm_click(self, item_id: str) -> None:
        """確定ボタンクリック処理"""
        pass
    
    def apply_row_styling(self, item_id: str, record: StructuredRecord) -> None:
        """行のスタイリングを適用
        
        Args:
            item_id: TreeviewアイテムID
            record: レコードデータ
        """
        pass
```

### 3. DuplicateDetectionModal

重複検出・削除モーダルダイアログ。

```python
class DuplicateDetectionModal:
    """重複検出モーダルダイアログ
    
    確定時に類似レコードを検出し、ユーザーが重複を選択して
    一括削除できるモーダルを表示します。
    """
    
    def __init__(self, parent: tk.Widget, 
                 confirming_record: StructuredRecord,
                 similar_records: List[Tuple[StructuredRecord, float]],
                 data_manager: HierarchicalDataManager):
        """
        Args:
            parent: 親ウィンドウ
            confirming_record: 確定するレコード
            similar_records: 類似レコードと類似度のリスト
            data_manager: データマネージャー
        """
        self.dialog = tk.Toplevel(parent)
        self.confirming_record = confirming_record
        self.similar_records = similar_records
        self.data_manager = data_manager
        
        # UI components
        self.edit_frame: ttk.Frame  # 確定レコード編集エリア
        self.similar_list: ttk.Treeview  # 類似レコードリスト
        
        # State
        self.selected_for_deletion: Set[str] = set()
        self.result: Optional[bool] = None
    
    def setup_ui(self) -> None:
        """UIをセットアップ"""
        pass
    
    def on_confirm(self) -> None:
        """確定ボタン処理
        
        - 確定レコードの編集を保存
        - 選択された類似レコードを削除
        - 確定レコードをロック
        """
        pass
    
    def on_cancel(self) -> None:
        """キャンセルボタン処理"""
        pass
    
    def show(self) -> bool:
        """モーダルを表示して結果を返す
        
        Returns:
            確定された場合True、キャンセルされた場合False
        """
        pass
```

### 4. CSVImportExport

CSV入出力ハンドラー。

```python
class CSVImportExport:
    """CSV入出力ハンドラー
    
    レコードのCSVエクスポートとインポートを管理します。
    """
    
    def __init__(self, data_manager: HierarchicalDataManager):
        self.data_manager = data_manager
    
    def export_to_csv(self, filepath: Optional[str] = None) -> bool:
        """CSVにエクスポート
        
        Args:
            filepath: 出力ファイルパス（Noneの場合はデフォルトパス使用）
        
        Returns:
            成功した場合True
        """
        pass
    
    def import_from_csv(self, filepath: str, overwrite: bool = False) -> Tuple[bool, str]:
        """CSVからインポート
        
        Args:
            filepath: 入力ファイルパス
            overwrite: 既存データを上書きするか
        
        Returns:
            (成功フラグ, メッセージ)
        """
        pass
    
    def validate_csv_format(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """CSV形式を検証
        
        Args:
            df: 読み込んだDataFrame
        
        Returns:
            (有効フラグ, エラーメッセージ)
        """
        pass
```

### 5. HierarchicalDataManager拡張

既存のHierarchicalDataManagerに確認ステータス機能を追加。

```python
@dataclass
class StructuredRecord:
    """構造化レコード（拡張版）"""
    list_item_id: str
    title: str
    progress: str
    last_read_date: str
    site_name: str
    image_path: str
    error_status: str
    confirmed: bool = False  # 新規追加
    confirmed_at: Optional[str] = None  # 新規追加

class HierarchicalDataManager:
    """階層的データマネージャー（拡張版）"""
    
    def confirm_record(self, list_item_id: str) -> None:
        """レコードを確定
        
        Args:
            list_item_id: 確定するレコードのID
        """
        pass
    
    def unconfirm_record(self, list_item_id: str) -> None:
        """レコードの確定を解除
        
        Args:
            list_item_id: 解除するレコードのID
        """
        pass
    
    def find_similar_records(self, title: str, 
                            threshold: Optional[float] = None) -> List[Tuple[StructuredRecord, float]]:
        """類似レコードを検索
        
        Args:
            title: 検索するタイトル
            threshold: 類似度しきい値（Noneの場合はデフォルト使用）
        
        Returns:
            (レコード, 類似度)のリスト
        """
        pass
    
    def delete_records(self, list_item_ids: List[str]) -> None:
        """複数レコードを削除
        
        Args:
            list_item_ids: 削除するレコードのIDリスト
        """
        pass
    
    def update_record(self, list_item_id: str, **kwargs) -> None:
        """レコードを更新
        
        Args:
            list_item_id: 更新するレコードのID
            **kwargs: 更新するフィールドと値
        """
        pass
    
    def get_statistics(self) -> Dict[str, int]:
        """統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        pass
```

## Data Models

### StructuredRecord（拡張版）

```python
@dataclass
class StructuredRecord:
    """構造化レコード
    
    Attributes:
        list_item_id: 一意識別子
        title: タイトル
        progress: 進捗
        last_read_date: 最終読書日
        site_name: サイト名
        image_path: 画像パス
        error_status: エラーステータス
        confirmed: 確認済みフラグ
        confirmed_at: 確認日時（ISO 8601形式）
    """
    list_item_id: str
    title: str
    progress: str
    last_read_date: str
    site_name: str
    image_path: str
    error_status: str
    confirmed: bool = False
    confirmed_at: Optional[str] = None
```

### EditAction

```python
@dataclass
class EditAction:
    """編集アクション（Undo用）
    
    Attributes:
        timestamp: 編集タイムスタンプ
        record_id: レコードID
        field: 編集されたフィールド
        old_value: 編集前の値
        new_value: 編集後の値
    """
    timestamp: str
    record_id: str
    field: str
    old_value: str
    new_value: str
```

### CSV形式

```csv
list_item_id,title,progress,last_read_date,site_name,image_path,error_status,confirmed,confirmed_at
001,転生したらスライムだった件,50%,2024-12-01,Web小説,sessions/20241201_120000/list_item_001.jpg,OK,true,2024-12-01T12:30:00
002,異世界転生物語,30%,2024-12-02,アプリ,sessions/20241201_120000/list_item_002.jpg,missing_progress,false,
```

## Error Handling

### エラーケース

1. **CSVインポートエラー**
   - 不正なCSV形式
   - 必須列の欠損
   - データ型の不一致
   - 処理: エラーメッセージを表示し、インポートを中止

2. **編集検証エラー**
   - 空のタイトル
   - 不正な日付形式
   - 処理: 編集をキャンセルし、エラーメッセージを表示

3. **確定済みレコードの編集試行**
   - 処理: 警告メッセージを表示し、ロック解除を促す

4. **データマネージャー同期エラー**
   - メインGUIとデータエディター間の同期失敗
   - 処理: 再読み込みを促すメッセージを表示

5. **重複検出エラー**
   - 類似度計算の失敗
   - 処理: エラーをログに記録し、重複検出をスキップ

## Testing Strategy

### ユニットテスト

1. **HierarchicalDataManager拡張機能**
   - `confirm_record()` - 確認フラグの設定
   - `find_similar_records()` - 類似度計算と検索
   - `delete_records()` - 複数削除
   - `update_record()` - レコード更新

2. **CSVImportExport**
   - `export_to_csv()` - エクスポート形式
   - `import_from_csv()` - インポートとデータ復元
   - `validate_csv_format()` - 形式検証

3. **OCRProcessor改行削除**
   - `cleanup_text()` - titleフィールドの改行削除

### 統合テスト

1. **Legacy Mode削除後の動作確認**
   - アプリケーション起動
   - 階層的検出の実行
   - CSV出力

2. **データエディターワークフロー**
   - レコード表示
   - インライン編集
   - 確定と重複検出
   - CSVエクスポート/インポート

3. **フィルタリングとソート**
   - 各フィルタータイプの動作
   - 各列のソート動作

### 手動テスト

1. **UI/UX確認**
   - テーブルの視認性
   - 編集のしやすさ
   - モーダルの使いやすさ

2. **パフォーマンス確認**
   - 大量レコード（100件以上）での動作
   - リアルタイム更新の遅延

## Implementation Notes

### Legacy Mode削除手順

1. **Phase 1: コード削除**
   - `PipelineProcessor`クラスの削除
   - `DataManager`クラスの削除（階層的版のみ残す）
   - GUI内のモード選択UIの削除
   - `_start_legacy_processing()`メソッドの削除

2. **Phase 2: 設定クリーンアップ**
   - `AppConfig.model_path`の削除
   - `AppConfig.output_csv`の削除（階層的版のみ使用）
   - 環境変数関連の削除

3. **Phase 3: インポート整理**
   - 未使用インポートの削除
   - ドキュメント更新

### OCR改行削除実装

```python
# src/ocr_processor.py
@staticmethod
def cleanup_text(text: str, remove_newlines: bool = False) -> str:
    """テキストクリーンアップ
    
    Args:
        text: 生のOCR結果
        remove_newlines: 改行を削除するか（titleフィールド用）
    
    Returns:
        クリーンアップされたテキスト
    """
    if not text:
        return ""
    
    if remove_newlines:
        # 改行を削除（titleフィールド用）
        text = text.replace('\n', ' ').replace('\r', ' ')
    
    # 連続する空白を1つに
    import re
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    if len(text) <= 2:
        return ""
    
    return text
```

### データエディターの起動

```python
# src/gui_app.py
class RealtimeOCRGUI:
    def __init__(self, root: tk.Tk):
        # ...
        self.data_editor_window: Optional[DataEditorWindow] = None
    
    def _setup_control_panel(self, parent):
        # ...
        ttk.Button(parent, text="📊 データエディター", 
                  command=self._open_data_editor).pack(...)
    
    def _open_data_editor(self):
        """データエディターを開く"""
        if self.data_editor_window and self.data_editor_window.window.winfo_exists():
            # 既に開いている場合はフォーカス
            self.data_editor_window.window.lift()
        else:
            # 新規作成
            if self.data_manager:
                self.data_editor_window = DataEditorWindow(self.root, self.data_manager)
            else:
                messagebox.showwarning("警告", "先に処理を開始してください")
```

### カラーコーディング

```python
# 行の背景色
COLORS = {
    'confirmed': '#d4edda',      # 緑系（確定済み）
    'error': '#f8d7da',          # 赤系（エラー）
    'unconfirmed': '#fff3cd',    # 黄系（未確認）
    'normal': '#ffffff'          # 白（通常）
}
```

## Performance Considerations

1. **大量レコードの表示**
   - 仮想スクロール（Treeviewのデフォルト機能）を活用
   - フィルタリングで表示件数を制限

2. **リアルタイム同期**
   - データマネージャーへの参照を共有
   - 変更時にイベント通知（必要に応じて）

3. **類似度計算の最適化**
   - 確定時のみ実行（リアルタイムでは実行しない）
   - しきい値以下は早期リターン

4. **CSV入出力**
   - pandasを使用した高速処理
   - 大容量ファイルの場合はプログレスバー表示
