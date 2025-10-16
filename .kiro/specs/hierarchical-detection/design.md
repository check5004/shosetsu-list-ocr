# Design Document

## Overview

本設計は、既存のリアルタイムOCRアプリケーションに階層的検出機能を追加するものです。list-item内部の詳細要素（title、progress、last_read_date、site_name）を個別に検出し、親子関係を判定して構造化されたデータを出力します。

### Key Design Decisions

1. **フラットな検出モデル**: 5つのクラスを同階層で学習し、モデル自体には階層構造を持たせない
2. **ポスト処理での階層化**: 推論後にIoU計算と座標判定で親子関係を構築
3. **曖昧マッチング**: OCRの誤認識を考慮した文字列類似度ベースの重複排除
4. **セッション管理**: タイムスタンプベースのフォルダで画像を管理し、ZIP圧縮で保存
5. **エラートラッキング**: 必須項目の欠損をerror_status列で記録
6. **データ拡張の強化**: 少量データ（9枚）での過学習を防ぐため、積極的な拡張を適用

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Main Application (GUI)                      │
│                    (src/gui_app.py)                          │
└───────────┬─────────────────────────────────────────────────┘
            │
            ├─► Model Selection
            │   ├─ Legacy Model (list-item only)
            │   └─ Hierarchical Model (5 classes)
            │
            ├─► WindowCapture Module (既存)
            │
            ├─► HierarchicalDetector Module (新規)
            │   ├─ YOLOv8 Model Loader (5 classes)
            │   ├─ Inference Engine
            │   ├─ Parent-Child Relationship Builder
            │   └─ IoU Calculator
            │
            ├─► OCR Module (既存・拡張)
            │   ├─ Tesseract OCR Engine
            │   └─ Text Cleanup
            │
            ├─► HierarchicalDataManager Module (新規)
            │   ├─ Fuzzy Duplicate Detection
            │   ├─ Structured CSV Export
            │   └─ Error Status Tracking
            │
            ├─► SessionManager Module (新規)
            │   ├─ Timestamp-based Folder Creation
            │   ├─ Image Cropping & Saving
            │   └─ ZIP Compression
            │
            └─► Visualization Module (既存・拡張)
                ├─ Multi-class Bounding Box Rendering
                └─ Statistics Display
```

### Data Flow

```
[Target Window Capture]
      ↓
[YOLOv8 Hierarchical Detection]
      ↓
[5 Classes Detection Results]
  ├─ list-item (parent)
  ├─ title (child)
  ├─ progress (child)
  ├─ last_read_date (child)
  └─ site_name (child)
      ↓
[Parent-Child Relationship Builder]
  ├─ Calculate IoU for overlapping list-items
  ├─ Assign each child to parent with highest IoU
  └─ Flag orphaned children
      ↓
[For each list-item:]
  ├─ [Crop & Save Image] → [Session Folder]
  ├─ [OCR on each child element]
  ├─ [Validate required fields]
  ├─ [Fuzzy Duplicate Check]
  └─ [Build Structured Record]
      ↓
[Structured Data Set] → [CSV Export with Error Status]
      ↓
[ZIP Compression of Session Folder]
```

## Components and Interfaces

### 1. HierarchicalDetector Module (新規)

**Purpose**: 5クラスの検出と親子関係の構築

**Key Classes**:

```python
@dataclass
class HierarchicalDetectionResult:
    """階層的検出結果"""
    list_item_id: str
    list_item_bbox: DetectionResult
    title: Optional[DetectionResult] = None
    progress: Optional[DetectionResult] = None
    last_read_date: Optional[DetectionResult] = None
    site_name: Optional[DetectionResult] = None
    orphaned_children: List[DetectionResult] = field(default_factory=list)
    
    def has_required_fields(self) -> bool:
        """必須フィールドが揃っているかチェック"""
        return all([self.title, self.last_read_date, self.site_name])
    
    def get_error_status(self) -> str:
        """エラーステータスを取得"""
        missing = []
        if not self.title:
            missing.append("missing_title")
        if not self.last_read_date:
            missing.append("missing_last_read_date")
        if not self.site_name:
            missing.append("missing_site_name")
        return ", ".join(missing) if missing else "OK"


class HierarchicalDetector:
    """
    5クラス検出と階層構造の構築を担当
    """
    def __init__(self, model_path: str, confidence_threshold: float = 0.6, iou_threshold: float = 0.5):
        """
        Args:
            model_path: 5クラス学習済みモデルのパス
            confidence_threshold: 検出の信頼度しきい値
            iou_threshold: 親子関係判定のIoUしきい値
        """
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.class_names = ['list-item', 'title', 'progress', 'last_read_date', 'site_name']
    
    def detect(self, frame: np.ndarray) -> List[HierarchicalDetectionResult]:
        """
        フレームから階層的検出を実行
        
        Args:
            frame: 入力画像
        
        Returns:
            階層的検出結果のリスト
        """
        # YOLOv8推論
        results = self.model(frame, conf=self.confidence_threshold, verbose=False)
        
        # 検出結果を分類
        list_items = []
        children = {'title': [], 'progress': [], 'last_read_date': [], 'site_name': []}
        
        for result in results[0].boxes.data:
            x1, y1, x2, y2, conf, cls = result
            class_name = self.class_names[int(cls)]
            detection = DetectionResult(
                x1=int(x1), y1=int(y1), x2=int(x2), y2=int(y2),
                confidence=float(conf), class_id=int(cls), class_name=class_name
            )
            
            if class_name == 'list-item':
                list_items.append(detection)
            else:
                children[class_name].append(detection)
        
        # 親子関係を構築
        return self._build_hierarchy(list_items, children)
    
    def _build_hierarchy(
        self, 
        list_items: List[DetectionResult], 
        children: Dict[str, List[DetectionResult]]
    ) -> List[HierarchicalDetectionResult]:
        """
        親子関係を構築
        
        Args:
            list_items: list-item検出結果
            children: 子要素検出結果の辞書
        
        Returns:
            階層的検出結果のリスト
        """
        hierarchical_results = []
        
        for idx, list_item in enumerate(list_items):
            result = HierarchicalDetectionResult(
                list_item_id=f"list_item_{idx:03d}",
                list_item_bbox=list_item
            )
            
            # 各子要素クラスについて、最適な親を見つける
            for child_class, child_list in children.items():
                best_child = None
                best_iou = 0.0
                
                for child in child_list:
                    iou = self._calculate_iou(list_item, child)
                    if iou > best_iou and iou >= self.iou_threshold:
                        best_iou = iou
                        best_child = child
                
                # 結果に割り当て
                if best_child:
                    setattr(result, child_class, best_child)
                    # 使用済みとしてマーク（複数のlist-itemに割り当てられないように）
                    child_list.remove(best_child)
            
            hierarchical_results.append(result)
        
        # 孤立した子要素を記録
        for child_class, child_list in children.items():
            if child_list:
                print(f"⚠️  孤立した{child_class}要素: {len(child_list)}件")
        
        return hierarchical_results
    
    @staticmethod
    def _calculate_iou(box1: DetectionResult, box2: DetectionResult) -> float:
        """
        2つのbounding box間のIoUを計算
        
        Args:
            box1: 1つ目のbounding box
            box2: 2つ目のbounding box
        
        Returns:
            IoU値（0.0〜1.0）
        """
        # 交差領域の座標
        x1_inter = max(box1.x1, box2.x1)
        y1_inter = max(box1.y1, box2.y1)
        x2_inter = min(box1.x2, box2.x2)
        y2_inter = min(box1.y2, box2.y2)
        
        # 交差領域の面積
        if x2_inter < x1_inter or y2_inter < y1_inter:
            return 0.0
        
        inter_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)
        
        # 各boxの面積
        box1_area = (box1.x2 - box1.x1) * (box1.y2 - box1.y1)
        box2_area = (box2.x2 - box2.x1) * (box2.y2 - box2.y1)
        
        # 和領域の面積
        union_area = box1_area + box2_area - inter_area
        
        # IoU
        return inter_area / union_area if union_area > 0 else 0.0
```

### 2. SessionManager Module (新規)

**Purpose**: セッション単位での画像管理とZIP圧縮

**Key Classes**:

```python
class SessionManager:
    """
    セッション単位での画像管理を担当
    """
    def __init__(self, base_output_dir: str = "output/sessions"):
        """
        Args:
            base_output_dir: セッションフォルダの基底ディレクトリ
        """
        self.base_output_dir = Path(base_output_dir)
        self.session_folder: Optional[Path] = None
        self.session_timestamp: Optional[str] = None
        self.image_counter = 0
    
    def start_session(self) -> Path:
        """
        新しいセッションを開始
        
        Returns:
            セッションフォルダのパス
        """
        from datetime import datetime
        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_folder = self.base_output_dir / self.session_timestamp
        self.session_folder.mkdir(parents=True, exist_ok=True)
        self.image_counter = 0
        print(f"📁 セッション開始: {self.session_folder}")
        return self.session_folder
    
    def save_list_item_image(
        self, 
        frame: np.ndarray, 
        bbox: DetectionResult, 
        margin: int = 5
    ) -> str:
        """
        list-item領域を切り出して保存
        
        Args:
            frame: 元画像
            bbox: list-itemのbounding box
            margin: マージン（ピクセル）
        
        Returns:
            保存した画像の相対パス
        """
        if not self.session_folder:
            raise RuntimeError("セッションが開始されていません")
        
        # マージン付きで切り出し
        x1 = max(0, bbox.x1 - margin)
        y1 = max(0, bbox.y1 - margin)
        x2 = min(frame.shape[1], bbox.x2 + margin)
        y2 = min(frame.shape[0], bbox.y2 + margin)
        
        cropped = frame[y1:y2, x1:x2]
        
        # ファイル名生成
        self.image_counter += 1
        filename = f"list_item_{self.image_counter:03d}.jpg"
        filepath = self.session_folder / filename
        
        # 保存
        cv2.imwrite(str(filepath), cropped)
        
        # 相対パスを返す
        return f"sessions/{self.session_timestamp}/{filename}"
    
    def end_session(self) -> Optional[Path]:
        """
        セッションを終了し、ZIP圧縮
        
        Returns:
            ZIPファイルのパス（圧縮成功時）
        """
        if not self.session_folder or not self.session_folder.exists():
            print("⚠️  セッションフォルダが存在しません")
            return None
        
        import shutil
        
        # ZIP圧縮
        zip_path = self.base_output_dir / f"{self.session_timestamp}.zip"
        print(f"🗜️  セッションフォルダを圧縮中: {zip_path}")
        
        try:
            shutil.make_archive(
                str(zip_path.with_suffix('')),
                'zip',
                self.session_folder
            )
            print(f"✅ 圧縮完了: {zip_path}")
            
            # 元のフォルダを削除（オプション）
            # shutil.rmtree(self.session_folder)
            # print(f"🗑️  元のフォルダを削除: {self.session_folder}")
            
            return zip_path
        except Exception as e:
            print(f"❌ ZIP圧縮エラー: {e}")
            return None
    
    def open_session_folder(self) -> None:
        """
        セッションフォルダをFinderで開く（macOS）
        """
        if not self.session_folder or not self.session_folder.exists():
            print("⚠️  セッションフォルダが存在しません")
            return
        
        import subprocess
        subprocess.run(["open", str(self.session_folder)])
```

### 3. HierarchicalDataManager Module (新規)

**Purpose**: 曖昧マッチングによる重複排除と構造化データ管理

**Key Classes**:

```python
@dataclass
class StructuredRecord:
    """構造化されたレコード"""
    list_item_id: str
    title: str
    progress: str
    last_read_date: str
    site_name: str
    image_path: str
    error_status: str


class HierarchicalDataManager:
    """
    階層的データの管理とCSV出力を担当
    """
    def __init__(
        self, 
        output_path: str = "output/hierarchical_data.csv",
        similarity_threshold: float = 0.75
    ):
        """
        Args:
            output_path: 出力CSVファイルのパス
            similarity_threshold: 重複判定の類似度しきい値（0.0〜1.0）
        """
        self.output_path = output_path
        self.similarity_threshold = similarity_threshold
        self.records: List[StructuredRecord] = []
        self.titles: List[str] = []  # 曖昧マッチング用
    
    def add_record(
        self, 
        hierarchical_result: HierarchicalDetectionResult,
        ocr_texts: Dict[str, str],
        image_path: str
    ) -> bool:
        """
        レコードを追加（重複チェック付き）
        
        Args:
            hierarchical_result: 階層的検出結果
            ocr_texts: OCRで抽出されたテキストの辞書
            image_path: 切り出し画像のパス
        
        Returns:
            新規データの場合True、重複の場合False
        """
        title = ocr_texts.get('title', '')
        
        # 曖昧マッチングで重複チェック
        if title and self._is_duplicate(title):
            return False
        
        # レコード作成
        record = StructuredRecord(
            list_item_id=hierarchical_result.list_item_id,
            title=title,
            progress=ocr_texts.get('progress', ''),
            last_read_date=ocr_texts.get('last_read_date', ''),
            site_name=ocr_texts.get('site_name', ''),
            image_path=image_path,
            error_status=hierarchical_result.get_error_status()
        )
        
        self.records.append(record)
        if title:
            self.titles.append(title)
        
        return True
    
    def _is_duplicate(self, title: str) -> bool:
        """
        曖昧マッチングで重複チェック
        
        Args:
            title: チェックするタイトル
        
        Returns:
            重複の場合True
        """
        from difflib import SequenceMatcher
        
        for existing_title in self.titles:
            similarity = SequenceMatcher(None, title, existing_title).ratio()
            if similarity >= self.similarity_threshold:
                print(f"🔄 重複検出: '{title}' ≈ '{existing_title}' (類似度: {similarity:.2f})")
                return True
        
        return False
    
    def export_to_csv(self) -> None:
        """
        構造化データをCSVファイルに出力
        """
        if not self.records:
            print("⚠️  出力するデータがありません")
            return
        
        import pandas as pd
        
        # DataFrameに変換
        df = pd.DataFrame([vars(record) for record in self.records])
        
        # CSV出力
        output_path = Path(self.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        # 統計情報
        total = len(self.records)
        errors = len([r for r in self.records if r.error_status != "OK"])
        success = total - errors
        
        print(f"✅ CSV出力完了: {output_path}")
        print(f"📊 統計情報:")
        print(f"   - 総件数: {total}")
        print(f"   - 正常: {success}")
        print(f"   - エラー: {errors}")
```

### 4. Training Module (新規)

**Purpose**: 5クラスモデルの学習

**Implementation**:

```python
def train_hierarchical_model():
    """
    階層的検出用の5クラスモデルを学習
    """
    from ultralytics import YOLO
    import torch
    
    # デバイス設定
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    
    # データセット設定
    data_yaml = "temp/shosetsu-list-item_dataset_v2/data.yaml"
    
    # モデルロード
    model = YOLO("yolov8n.pt")
    
    # 学習設定（既存設定を再利用 + データ拡張強化）
    results = model.train(
        data=data_yaml,
        epochs=100,
        imgsz=1280,
        batch=4,
        device=device,
        patience=20,
        project="models",
        name="hierarchical-detection",
        exist_ok=True,
        verbose=True,
        # データ拡張設定（強化版）
        augment=True,
        hsv_h=0.02,      # 色相の変動（やや増加）
        hsv_s=0.8,       # 彩度の変動（増加）
        hsv_v=0.5,       # 明度の変動（増加）
        degrees=15,      # 回転（増加）
        translate=0.15,  # 平行移動（増加）
        scale=0.6,       # スケール（増加）
        flipud=0.0,      # 上下反転（不適切）
        fliplr=0.0,      # 左右反転（不適切）
        mosaic=1.0,      # モザイク拡張
        mixup=0.1,       # Mixup拡張（追加）
        copy_paste=0.1,  # Copy-Paste拡張（追加）
    )
    
    return results
```

## Data Models

### YOLO Annotation Format (5 Classes)

```yaml
# data.yaml
path: temp/shosetsu-list-item_dataset_v2
train: obj_train_data
val: obj_train_data

nc: 5

names:
  0: list-item
  1: title
  2: progress
  3: last_read_date
  4: site_name
```

### Annotation File Format

```
# 各画像に対応する.txtファイル
# Format: <class_id> <x_center> <y_center> <width> <height> (normalized 0-1)

# Example: IMG_1307.txt
0 0.501062 0.248689 0.997876 0.080154  # list-item
1 0.250000 0.230000 0.450000 0.030000  # title
2 0.850000 0.250000 0.120000 0.020000  # progress
3 0.250000 0.270000 0.200000 0.020000  # last_read_date
4 0.750000 0.270000 0.150000 0.020000  # site_name
```

### CSV Output Format

```csv
list_item_id,title,progress,last_read_date,site_name,image_path,error_status
list_item_001,転生したらスライムだった件,38/768,4週間前,カクヨム,sessions/20251016_143022/list_item_001.jpg,OK
list_item_002,無職転生,120/250,,小説家になろう,sessions/20251016_143022/list_item_002.jpg,missing_last_read_date
```

## Error Handling

### Error Categories

1. **検出エラー**
   - 必須子要素の欠損 → error_status列に記録
   - 孤立した子要素 → 警告ログ出力
   - IoU計算エラー → デフォルト値（0.0）使用

2. **OCRエラー**
   - OCR処理失敗 → 空文字列を返して継続
   - 極端に短いテキスト → 警告ログ出力

3. **セッション管理エラー**
   - 画像保存失敗 → エラーログ出力、処理継続
   - ZIP圧縮失敗 → エラーログ出力、元フォルダは保持

## Testing Strategy

### Unit Testing

1. **IoU計算ロジック**
   - 完全一致（IoU=1.0）
   - 部分重複（0.0 < IoU < 1.0）
   - 非重複（IoU=0.0）

2. **曖昧マッチング**
   - 完全一致（similarity=1.0）
   - 部分一致（0.7 < similarity < 1.0）
   - 非一致（similarity < 0.7）

3. **親子関係構築**
   - 1対1の親子関係
   - 複数の子要素を持つ親
   - 孤立した子要素

### Integration Testing

1. **全体フロー**
   - 検出 → 階層化 → OCR → 重複チェック → CSV出力
   - セッション開始 → 画像保存 → ZIP圧縮

2. **エラーケース**
   - 必須項目欠損時の処理
   - 重複データの処理
   - 孤立要素の処理

## Configuration

### Extended AppConfig

```python
@dataclass
class AppConfig:
    # 既存設定
    model_path: str = "models/best.pt"
    confidence_threshold: float = 0.6
    
    # 新規設定
    hierarchical_model_path: str = "models/hierarchical_best.pt"
    use_hierarchical_detection: bool = False
    iou_threshold: float = 0.5
    similarity_threshold: float = 0.75
    session_output_dir: str = "output/sessions"
    hierarchical_csv_output: str = "output/hierarchical_data.csv"
```

## GUI Integration

### New UI Components

1. **モデル選択ラジオボタン**
   - 既存モデル（list-item全体）
   - 階層的モデル（5クラス）

2. **画像フォルダ管理パネル**
   - 「画像フォルダを開く」ボタン
   - 保存先ディレクトリ設定（オプション）

3. **統計情報の拡張**
   - 各クラスの検出数
   - エラー件数 / 正常件数
   - 類似度しきい値スライダー

## Performance Considerations

1. **IoU計算の最適化**
   - NumPyのベクトル化演算を活用
   - 不要な計算をスキップ

2. **曖昧マッチングの最適化**
   - 既存タイトル数が多い場合、インデックス化を検討
   - しきい値による早期リターン

3. **画像保存の非同期化**
   - 別スレッドで画像保存を実行（オプション）
   - メインループのブロッキングを回避

## Future Enhancements

1. **アノテーション支援ツール**
   - 検出結果を元に半自動アノテーション
   - 再学習データの効率的な作成

2. **信頼度ベースのフィルタリング**
   - 低信頼度の検出結果を手動確認用にフラグ
   - 人間によるレビューワークフロー

3. **多言語対応**
   - 英語、中国語などの小説サイトに対応
   - OCR言語の自動切り替え
