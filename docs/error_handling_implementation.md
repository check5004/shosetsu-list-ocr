# エラーハンドリング実装ドキュメント

## 概要

階層的検出機能において、予期しないエラーが発生してもシステムがクラッシュせず、処理を継続できるように、包括的なエラーハンドリングを実装しました。

## 実装された要件

### 要件9.1: 孤立した子要素の警告ログ出力

**実装箇所**: `src/hierarchical_detector.py` - `_build_hierarchy()`メソッド

**動作**:
- 子要素（title、progress、last_read_date、site_name）がどのlist-itemにも紐付けられない場合、警告ログを出力
- 各孤立要素について、クラス名、信頼度、bounding box座標を表示
- 孤立要素の統計情報（クラスごとの件数）を出力

**ログ例**:
```
⚠️  孤立したtitle要素を検出: confidence=0.85, bbox=(100, 200, 300, 220)
⚠️  title: 2件の孤立要素
```

### 要件9.2: IoU計算エラー時のデフォルト値使用

**実装箇所**: 
- `src/iou_calculator.py` - `calculate_iou()`関数
- `src/hierarchical_detector.py` - `_build_hierarchy()`メソッド

**動作**:
- IoU計算中に例外が発生した場合、デフォルト値0.0を返す
- 無効な座標（x2 <= x1 または y2 <= y1）を検出し、エラーメッセージを出力
- IoU値の範囲チェック（0.0〜1.0）を実施
- エラー時は詳細なログ（両方のbounding box座標）を出力

**ログ例**:
```
⚠️  IoU計算エラー（デフォルト値0.0を使用）: box2の座標が無効です: (100, 100, 0, 0)
   list_item bbox: (50, 50, 200, 150)
   child bbox: (100, 100, 0, 0)
```

### 要件9.3: 画像切り出し失敗時のエラーログ出力と処理継続

**実装箇所**:
- `src/session_manager.py` - `save_list_item_image()`メソッド
- `src/hierarchical_pipeline.py` - `_save_list_item_image()`メソッド

**動作**:
- 画像切り出し・保存中に例外が発生した場合、エラーログを出力
- 座標の妥当性チェック（x2 > x1 かつ y2 > y1）を実施
- 切り出した画像が空でないかチェック
- cv2.imwrite()の戻り値をチェックし、書き込み失敗を検出
- エラー時は空文字列を返し、処理を継続
- エラー詳細（bbox座標、フレームサイズ、マージン）を出力

**ログ例**:
```
❌ 画像切り出し・保存エラー: 無効なbounding box座標: x1=100, y1=100, x2=50, y2=50
   bbox: (100, 100, 50, 50), frame shape: (1920, 1080, 3), margin: 5
❌ 画像保存エラー（処理を継続）: 無効なbounding box座標
   list_item_id: list_item_001
```

### 要件9.4: OCR処理エラー時の空文字列返却と処理継続

**実装箇所**:
- `src/hierarchical_ocr_processor.py` - `process_hierarchical_detection()`関数
- `src/hierarchical_ocr_processor.py` - `process_hierarchical_detections_batch()`関数
- `src/hierarchical_pipeline.py` - `_process_ocr()`メソッド

**動作**:
- 各子要素のOCR処理中に例外が発生した場合、エラーログを出力
- エラー時は空文字列を返し、他の要素の処理を継続
- エラー詳細（要素名、bounding box座標）を出力
- バッチ処理時も個別のエラーを捕捉し、全体の処理を継続

**ログ例**:
```
❌ titleのOCR処理でエラーが発生（空文字列を返して処理を継続）: Tesseract OCR failed
   bbox: (100, 200, 300, 220)
❌ OCR処理エラー（空文字列を返して処理を継続）: Unexpected error
   list_item_id: list_item_002
```

### 要件9.5: 予期しないエラーのログ出力と処理継続

**実装箇所**:
- `src/hierarchical_ocr_processor.py` - `process_hierarchical_detections_batch()`関数
- `src/hierarchical_pipeline.py` - `process_frame()`メソッド

**動作**:
- 個別のlist-item処理中に予期しないエラーが発生した場合、エラーログを出力
- エラータイプ（例外クラス名）を表示
- フレーム処理全体でエラーが発生した場合、スタックトレースを出力
- エラー時も次のlist-itemまたはフレームの処理を継続

**ログ例**:
```
❌ list-item 3 の処理で予期しないエラーが発生（処理を継続）: division by zero
   エラー詳細: ZeroDivisionError
   list_item_id: list_item_003

❌ フレーム 42 の処理で予期しないエラーが発生（処理を継続）: Unexpected error
   エラー詳細: RuntimeError
   スタックトレース:
Traceback (most recent call last):
  File "src/hierarchical_pipeline.py", line 123, in process_frame
    ...
```

## エラーハンドリングの設計原則

1. **フェイルセーフ**: エラーが発生しても処理を継続し、可能な限りデータを収集
2. **詳細なログ**: エラーの原因を特定できるよう、詳細な情報を出力
3. **デフォルト値**: エラー時は安全なデフォルト値（0.0、空文字列など）を使用
4. **段階的な処理**: 個別の要素でエラーが発生しても、他の要素の処理は継続
5. **透明性**: すべてのエラーをユーザーに通知し、隠蔽しない

## テスト結果

### IoU計算のエラーハンドリング

```python
# 正常なケース
box1 = DetectionResult(x1=0, y1=0, x2=100, y2=100, ...)
box2 = DetectionResult(x1=50, y1=50, x2=150, y2=150, ...)
iou = calculate_iou(box1, box2)
# 結果: 0.1429

# エラーケース: 無効な座標
box3 = DetectionResult(x1=100, y1=100, x2=0, y2=0, ...)
iou_error = calculate_iou(box1, box3)
# 結果: 0.0（デフォルト値）
# ログ: ⚠️  IoU計算で予期しないエラーが発生（デフォルト値0.0を返す）
```

### モジュールのインポート

すべてのモジュールが正常にインポート可能であることを確認:
- ✅ hierarchical_detector
- ✅ hierarchical_ocr_processor
- ✅ session_manager
- ✅ iou_calculator
- ✅ hierarchical_pipeline

## まとめ

階層的検出機能のすべての主要モジュールに対して、包括的なエラーハンドリングを実装しました。これにより、予期しないエラーが発生してもシステムがクラッシュせず、可能な限りデータを収集し続けることができます。

エラーログは詳細で、問題の原因を特定しやすい形式になっています。また、エラー時も処理を継続することで、約1700作品のデータ移行という大規模なタスクを効率的に実行できます。
