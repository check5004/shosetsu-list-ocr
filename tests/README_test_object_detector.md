# ObjectDetector テストドキュメント

## 概要

`test_object_detector.py` は、YOLOv8を使用した物体検出モジュール（`src/object_detector.py`）のテストコードです。

## テスト対象の要件

- **Requirement 2.3**: フレーム内の物体検出の実行
- **Requirement 2.4**: 信頼度しきい値によるフィルタリング
- **Requirement 2.5**: Y座標による検出結果のソート

## テストクラス構成

### 1. TestDetectionResult

`DetectionResult` データクラスの基本的な動作をテストします。

- `test_detection_result_creation`: データクラスが正しく作成されることを確認

### 2. TestObjectDetector

`ObjectDetector` クラスの主要機能をモックを使用してテストします。

#### 初期化テスト

- `test_init_model_not_found`: モデルファイルが存在しない場合のエラー処理 (Requirement 2.2)
- `test_init_success_with_mps`: Apple Silicon MPS環境での初期化 (Requirement 2.1)
- `test_init_success_with_cpu`: CPU環境での初期化 (Requirement 2.1)

#### 検出機能テスト

- `test_detect_with_confidence_filtering`: 信頼度フィルタリングの動作確認 (Requirement 2.4)
  - しきい値0.6で、0.85と0.72の検出は通過、0.45は除外されることを確認
  
- `test_detect_returns_correct_format`: 検出結果が正しいフォーマットで返されることを確認 (Requirement 2.3)
  - 座標がint型に変換されていることを確認
  - DetectionResultオブジェクトとして返されることを確認
  
- `test_detect_empty_result`: 検出結果が空の場合の処理 (Requirement 2.3)

#### ソート機能テスト

- `test_sort_by_y_coordinate_ascending`: Y座標で昇順にソートされることを確認 (Requirement 2.5)
  - y1=300, 100, 500, 200 → 100, 200, 300, 500 の順にソート
  
- `test_sort_by_y_coordinate_empty_list`: 空のリストの処理
- `test_sort_by_y_coordinate_single_item`: 単一要素のリストの処理
- `test_sort_by_y_coordinate_same_y`: 同じY座標の要素が含まれる場合の処理
- `test_sort_by_y_coordinate_preserves_data`: ソート後も元のデータが保持されることを確認

### 3. TestObjectDetectorIntegration

実際のYOLOv8モデルとサンプル画像を使用した統合テストです。

- `test_detect_with_real_model_and_sample_image`: 実際のモデルを使用した検出テスト (Requirement 2.3)
  - `models/best.pt` が存在する場合のみ実行
  
- `test_detect_with_training_images`: トレーニング画像を使用した検出テスト (Requirement 2.3, 2.4)
  - `temp/shosetsu-list-item/obj_train_data` の画像を使用
  - 信頼度がしきい値以上であることを確認
  - バウンディングボックスが画像内に収まっていることを確認

## テストの実行方法

### 前提条件

**必ず仮想環境を使用してください**。仮想環境を作成していない場合:

```bash
# プロジェクトルートで仮想環境を作成
python3 -m venv venv

# 仮想環境を有効化
source venv/bin/activate

# 依存関係をインストール
pip install --upgrade pip
pip install -r requirements.txt
```

### 全テストの実行

仮想環境を有効化した状態で:

```bash
pytest tests/test_object_detector.py -v
```

または、仮想環境を有効化せずに直接実行:

```bash
./venv/bin/pytest tests/test_object_detector.py -v
```

### 特定のテストクラスのみ実行

```bash
# ユニットテストのみ（モックを使用）
pytest tests/test_object_detector.py::TestObjectDetector -v

# ソート機能のテストのみ
pytest tests/test_object_detector.py::TestObjectDetector::test_sort_by_y_coordinate_ascending -v
```

### 統合テストの実行

統合テストは実際のモデルファイルが必要です：

```bash
# models/best.pt が存在する場合のみ実行される
pytest tests/test_object_detector.py::TestObjectDetectorIntegration -v
```

## モックの使用

このテストでは、以下のモジュールをモック化しています：

- `YOLO`: YOLOv8モデルのロードと推論
- `torch`: PyTorchのデバイス選択（MPS/CUDA/CPU）
- `Path.exists`: ファイルの存在チェック

これにより、実際のモデルファイルがなくてもユニットテストを実行できます。

## カバレッジ

このテストは以下の機能をカバーしています：

- ✅ モデルの初期化（成功/失敗）
- ✅ デバイス選択（MPS/CUDA/CPU）
- ✅ 物体検出の実行
- ✅ 信頼度フィルタリング
- ✅ 検出結果のフォーマット変換
- ✅ Y座標によるソート
- ✅ エッジケース（空のリスト、単一要素など）
- ✅ 実際のモデルを使用した統合テスト（オプション）

## 注意事項

- 統合テストは `models/best.pt` が存在する環境でのみ実行されます
- トレーニング画像を使用したテストは `temp/shosetsu-list-item/obj_train_data` が存在する場合のみ実行されます
- これらのファイルが存在しない場合、該当するテストは自動的にスキップされます
