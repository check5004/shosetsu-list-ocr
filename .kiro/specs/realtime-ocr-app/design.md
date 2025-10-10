# Design Document

## Overview

本アプリケーションは、macOS Apple Silicon環境で動作するリアルタイムOCRシステムです。指定されたウィンドウ（iPhoneシミュレータやミラーリングアプリ）をキャプチャし、YOLOv8で小説リスト項目を検出、Tesseract OCRで日本語テキストを抽出し、重複を排除してCSV形式で保存します。

### Key Design Decisions

1. **macOS専用アプローチ**: pygetwindowはmacOSで動作しないため、macOS専用のウィンドウキャプチャ手法を採用
2. **段階的実装**: フェーズ1では`list-item`クラスのみ対応、将来的な拡張性を考慮した設計
3. **リアルタイム処理**: フレームごとに検出→OCR→重複チェックのパイプラインを実行
4. **Apple Silicon最適化**: ネイティブライブラリとMetal対応を活用

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Main Application                         │
│                  (realtime_ocr_app.py)                       │
└───────────┬─────────────────────────────────────────────────┘
            │
            ├─► WindowCapture Module
            │   ├─ macOS Screen Capture API (mss)
            │   └─ Window Selection & Tracking
            │
            ├─► ObjectDetection Module
            │   ├─ YOLOv8 Model Loader
            │   ├─ Inference Engine
            │   └─ Bounding Box Processor
            │
            ├─► OCR Module
            │   ├─ Tesseract OCR Engine
            │   ├─ Image Preprocessing
            │   └─ Text Cleanup
            │
            ├─► DataManager Module
            │   ├─ Duplicate Detection (Set-based)
            │   └─ CSV Export
            │
            └─► Visualization Module
                ├─ OpenCV Display
                └─ Bounding Box Rendering
```

### Data Flow

```
[Target Window]
      ↓
[Screen Capture] → [Frame Buffer]
      ↓
[YOLOv8 Detection] → [Bounding Boxes]
      ↓
[Sort by Y-coordinate]
      ↓
[For each box:]
  ├─ [Crop Image]
  ├─ [OCR Processing]
  ├─ [Text Cleanup]
  └─ [Duplicate Check]
      ↓
[Unique Text Set] → [CSV Export on Exit]
      ↓
[Display with Overlays]
```

## Components and Interfaces

### 1. WindowCapture Module

**Purpose**: macOS環境でウィンドウをキャプチャする

**Key Classes**:

```python
class WindowCapture:
    """
    macOS専用のウィンドウキャプチャクラス
    """
    def __init__(self, window_title: str):
        """
        Args:
            window_title: キャプチャ対象のウィンドウタイトル（部分一致）
        """
        pass
    
    def find_window(self) -> Optional[Dict]:
        """
        指定されたタイトルのウィンドウを検索
        
        Returns:
            ウィンドウ情報（位置、サイズ）またはNone
        """
        pass
    
    def capture_frame(self) -> np.ndarray:
        """
        現在のウィンドウフレームをキャプチャ
        
        Returns:
            BGR形式のnumpy配列
        """
        pass
    
    @staticmethod
    def list_all_windows() -> List[str]:
        """
        利用可能な全ウィンドウのタイトルを取得
        
        Returns:
            ウィンドウタイトルのリスト
        """
        pass
```

**Implementation Notes**:
- **mss**: クロスプラットフォーム対応のスクリーンキャプチャライブラリを使用
- **macOS権限**: 画面収録権限が必要（システム環境設定 > セキュリティとプライバシー > 画面収録）
- **ウィンドウ検索**: `Quartz`（PyObjC）を使用してウィンドウリストを取得し、タイトルで検索
- **代替案**: `pygetwindow`はmacOSで動作しないため、`Quartz.CoreGraphics`の`CGWindowListCopyWindowInfo`を使用

### 2. ObjectDetection Module

**Purpose**: YOLOv8を使用してlist-itemを検出

**Key Classes**:

```python
class ObjectDetector:
    """
    YOLOv8ベースの物体検出クラス
    """
    def __init__(self, model_path: str, confidence_threshold: float = 0.6):
        """
        Args:
            model_path: YOLOv8モデルファイル（best.pt）のパス
            confidence_threshold: 検出の信頼度しきい値
        """
        pass
    
    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        """
        フレーム内の物体を検出
        
        Args:
            frame: 入力画像（BGR形式）
        
        Returns:
            検出結果のリスト（座標、信頼度、クラス）
        """
        pass
    
    @staticmethod
    def sort_by_y_coordinate(detections: List[DetectionResult]) -> List[DetectionResult]:
        """
        検出結果をY座標でソート（上から下）
        
        Args:
            detections: 検出結果のリスト
        
        Returns:
            ソート済みの検出結果
        """
        pass
```

**Data Structures**:

```python
@dataclass
class DetectionResult:
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    class_id: int
    class_name: str
```

**Implementation Notes**:
- **Ultralytics YOLOv8**: `ultralytics`ライブラリを使用
- **Apple Silicon最適化**: PyTorchのMPS（Metal Performance Shaders）バックエンドを活用
- **モデルロード**: 起動時に1回だけロード、推論時は`verbose=False`で出力を抑制
- **信頼度フィルタリング**: しきい値以下の検出結果を除外

### 3. OCR Module

**Purpose**: 検出された領域からテキストを抽出

**Key Classes**:

```python
class OCRProcessor:
    """
    Tesseract OCRを使用したテキスト抽出クラス
    """
    def __init__(self, lang: str = 'jpn', margin: int = 5):
        """
        Args:
            lang: OCR言語（デフォルト: 日本語）
            margin: 切り出し時のマージン（ピクセル）
        """
        pass
    
    def extract_text(self, frame: np.ndarray, bbox: DetectionResult) -> str:
        """
        バウンディングボックス領域からテキストを抽出
        
        Args:
            frame: 元画像
            bbox: バウンディングボックス情報
        
        Returns:
            抽出されたテキスト（クリーンアップ済み）
        """
        pass
    
    @staticmethod
    def preprocess_image(image: np.ndarray) -> np.ndarray:
        """
        OCR精度向上のための画像前処理
        
        Args:
            image: 入力画像
        
        Returns:
            前処理済み画像
        """
        pass
    
    @staticmethod
    def cleanup_text(text: str) -> str:
        """
        抽出されたテキストをクリーンアップ
        
        Args:
            text: 生のOCR結果
        
        Returns:
            正規化されたテキスト
        """
        pass
```

**Implementation Notes**:
- **Tesseract OCR**: `pytesseract`ライブラリを使用
- **日本語対応**: `lang='jpn'`を指定、Homebrewで`tesseract-lang`をインストール
- **マージン**: バウンディングボックスに5ピクセルのマージンを追加して精度向上
- **前処理**: グレースケール変換、コントラスト調整（オプション）
- **テキストクリーンアップ**: 空白の正規化、2文字以下のテキストを除外
- **エラーハンドリング**: OCR失敗時は空文字列を返し、処理を継続

### 4. DataManager Module

**Purpose**: データの重複排除とCSV出力

**Key Classes**:

```python
class DataManager:
    """
    抽出データの管理とCSV出力を担当
    """
    def __init__(self, output_path: str = "book_data_realtime.csv"):
        """
        Args:
            output_path: 出力CSVファイルのパス
        """
        self.extracted_texts: Set[str] = set()
        self.output_path = output_path
    
    def add_text(self, text: str) -> bool:
        """
        テキストを追加（重複チェック）
        
        Args:
            text: 抽出されたテキスト
        
        Returns:
            新規データの場合True、重複の場合False
        """
        pass
    
    def export_to_csv(self) -> None:
        """
        抽出されたデータをCSVファイルに出力
        """
        pass
    
    def get_count(self) -> int:
        """
        抽出されたユニークなテキストの数を取得
        
        Returns:
            データ件数
        """
        pass
```

**Implementation Notes**:
- **重複排除**: Pythonの`set`を使用してO(1)の重複チェック
- **CSV出力**: `pandas`を使用してDataFrameを作成し、`to_csv()`で出力
- **列名**: `extracted_text`という単一列
- **終了時出力**: プログラム終了時（'q'キー押下またはCtrl+C）にCSVを保存

### 5. Visualization Module

**Purpose**: 検出結果のリアルタイム表示

**Key Classes**:

```python
class Visualizer:
    """
    検出結果の描画とウィンドウ表示を担当
    """
    def __init__(self, window_name: str = "Real-time Detection"):
        """
        Args:
            window_name: 表示ウィンドウの名前
        """
        pass
    
    def draw_detections(self, frame: np.ndarray, detections: List[DetectionResult]) -> np.ndarray:
        """
        フレームに検出結果を描画
        
        Args:
            frame: 元画像
            detections: 検出結果のリスト
        
        Returns:
            描画済みの画像
        """
        pass
    
    def show_frame(self, frame: np.ndarray) -> bool:
        """
        フレームを表示し、キー入力をチェック
        
        Args:
            frame: 表示する画像
        
        Returns:
            'q'キーが押された場合False、それ以外True
        """
        pass
    
    def cleanup(self) -> None:
        """
        ウィンドウをクローズ
        """
        pass
```

**Implementation Notes**:
- **OpenCV**: `cv2.imshow()`を使用してウィンドウ表示
- **描画**: 緑色（0, 255, 0）の矩形でバウンディングボックスを描画、線幅2
- **キー入力**: `cv2.waitKey(1)`で'q'キーの押下を検出
- **クリーンアップ**: `cv2.destroyAllWindows()`で全ウィンドウを閉じる

### 6. Configuration Module

**Purpose**: アプリケーション設定の管理

**Configuration Structure**:

```python
@dataclass
class AppConfig:
    # Model settings
    model_path: str = "runs/detect/train/weights/best.pt"
    confidence_threshold: float = 0.6
    
    # Window capture settings
    target_window_title: str = "iPhone"
    
    # OCR settings
    ocr_lang: str = "jpn"
    ocr_margin: int = 5
    min_text_length: int = 2
    
    # Output settings
    output_csv: str = "book_data_realtime.csv"
    
    # Display settings
    display_window_name: str = "Real-time Detection"
```

**Implementation Notes**:
- **設定ファイル**: `config.yaml`または`config.json`で外部化（オプション）
- **デフォルト値**: コード内にハードコードされたデフォルト値を使用
- **環境変数**: 環境変数からの設定読み込みをサポート（オプション）

## Data Models

### Detection Pipeline Data Flow

```python
# Input
RawFrame = np.ndarray  # Shape: (height, width, 3), dtype: uint8, format: BGR

# Detection Output
DetectionResult = {
    'x1': int,
    'y1': int,
    'x2': int,
    'y2': int,
    'confidence': float,
    'class_id': int,
    'class_name': str
}

# OCR Output
ExtractedText = str  # Cleaned and normalized text

# Final Output (CSV)
BookDataRecord = {
    'extracted_text': str
}
```

### YOLO Annotation Format

現在使用しているアノテーションデータ（`temp/shosetsu-list-item/`）:

```
Format: YOLO v1.1
Class: list-item (ID: 0)
Annotation: <class_id> <x_center> <y_center> <width> <height> (normalized 0-1)

Example:
0 0.501062 0.248689 0.997876 0.080154
```

## Error Handling

### Error Categories and Strategies

1. **Initialization Errors**
   - モデルファイルが見つからない → エラーメッセージ表示して終了
   - Tesseractがインストールされていない → インストール手順を表示して終了
   - ウィンドウが見つからない → 利用可能なウィンドウリストを表示して終了

2. **Runtime Errors**
   - OCR処理の失敗 → エラーをキャッチして次のフレームに進む
   - ウィンドウが閉じられた → エラーメッセージを表示して終了
   - キャプチャの失敗 → リトライまたはスキップ

3. **User Interruption**
   - Ctrl+C → 安全にクリーンアップしてCSV出力
   - 'q'キー → 正常終了してCSV出力

### Error Handling Implementation

```python
class ErrorHandler:
    @staticmethod
    def handle_initialization_error(error: Exception, context: str) -> None:
        """初期化エラーの処理"""
        print(f"Error: {context}")
        print(f"Details: {error}")
        sys.exit(1)
    
    @staticmethod
    def handle_runtime_error(error: Exception, context: str) -> None:
        """実行時エラーの処理（継続可能）"""
        print(f"Warning: {context} - {error}")
        # 処理を継続
    
    @staticmethod
    def handle_graceful_shutdown(data_manager: DataManager) -> None:
        """安全なシャットダウン処理"""
        print("\nShutting down...")
        data_manager.export_to_csv()
        cv2.destroyAllWindows()
```

## Testing Strategy

### Unit Testing

**Target Modules**:
1. `OCRProcessor.cleanup_text()` - テキスト正規化ロジック
2. `ObjectDetector.sort_by_y_coordinate()` - ソートロジック
3. `DataManager.add_text()` - 重複チェックロジック

**Test Framework**: pytest

### Integration Testing

**Test Scenarios**:
1. モデルロード → 推論 → 結果取得のパイプライン
2. 画像キャプチャ → 検出 → OCR → CSV出力の全体フロー
3. エラーハンドリング（モデルファイル不在、ウィンドウ不在）

### Manual Testing

**Test Cases**:
1. Xcodeシミュレータでの動作確認
2. QuickTimeミラーリングでの動作確認
3. スクロール時のリアルタイム検出
4. 重複排除の動作確認
5. CSV出力の内容確認

### Performance Testing

**Metrics**:
- フレームレート（FPS）
- 検出レイテンシ
- OCR処理時間
- メモリ使用量

**Target**: Apple Silicon Mac（M1/M2/M3）で10 FPS以上

## macOS Specific Considerations

### Screen Recording Permission

macOSでは画面収録に権限が必要:

```
システム環境設定 > セキュリティとプライバシー > プライバシー > 画面収録
```

アプリケーション（ターミナルまたはPython）に権限を付与する必要があります。

### Window Management

**Quartz Framework**を使用したウィンドウ検索:

```python
from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionAll, kCGNullWindowID

def get_window_list():
    window_list = CGWindowListCopyWindowInfo(
        kCGWindowListOptionAll,
        kCGNullWindowID
    )
    return [
        {
            'name': w.get('kCGWindowName', ''),
            'owner': w.get('kCGWindowOwnerName', ''),
            'bounds': w.get('kCGWindowBounds', {})
        }
        for w in window_list
        if w.get('kCGWindowName')
    ]
```

### Apple Silicon Optimization

**PyTorch MPS Backend**:

```python
import torch

# Apple Silicon GPUを使用
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
model = YOLO(model_path)
model.to(device)
```

## Dependencies

### Core Libraries

```
ultralytics>=8.0.0      # YOLOv8
opencv-python>=4.8.0    # 画像処理と表示
pytesseract>=0.3.10     # OCR
pandas>=2.0.0           # CSV出力
mss>=9.0.0              # スクリーンキャプチャ
pyobjc-framework-Quartz>=9.0  # macOSウィンドウ管理
numpy>=1.24.0           # 数値計算
```

### System Requirements

- macOS 11.0 (Big Sur) 以降
- Apple Silicon (M1/M2/M3) または Intel
- Python 3.9 以降
- Tesseract OCR 4.0 以降（Homebrewでインストール）

### Installation Commands

```bash
# Tesseract OCR
brew install tesseract tesseract-lang

# Python dependencies
pip install -r requirements.txt
```

## Future Enhancements

### Phase 2: Fine-grained Detection

**Objective**: list-item内の要素（タイトル、日時、ページ数など）を個別に検出

**Approach**:
1. 追加アノテーション: `title`, `date`, `page`, `subtitle`などのクラスを定義
2. 階層的検出: まず`list-item`を検出し、その内部で細分化されたクラスを検出
3. データ構造化: CSVに複数列（title, date, pageなど）を追加

**Challenges**:
- YOLOv8での入れ子構造の対応可否
- アノテーション作業の増加
- 検出精度の維持

### Additional Features

1. **GUIアプリケーション**: Tkinter/PyQt5でGUIを追加
2. **リアルタイムプレビュー改善**: 検出されたテキストをオーバーレイ表示
3. **データベース連携**: CSVではなくSQLiteやPostgreSQLに保存
4. **自動スクロール**: アプリを自動的にスクロールしてデータ収集
5. **バッチ処理モード**: 複数のスクリーンショットを一括処理
