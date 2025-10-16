# プロジェクト構成

このドキュメントは、プロジェクトのディレクトリ構成とファイルの役割を説明します。

## ディレクトリ構成

```
shosetsu-list-ocr/
├── .git/                   # Gitリポジトリ
├── .kiro/                  # Kiro IDE設定
│   ├── specs/             # 機能仕様書
│   └── steering/          # ステアリングルール
├── config/                 # 設定ファイル
│   └── dataset.yaml       # YOLOv8データセット設定
├── docs/                   # ドキュメント
│   ├── DEVELOPMENT.md     # 開発ガイド
│   ├── error_handling_implementation.md
│   ├── gui_testing_guide.md
│   ├── hierarchical_model_training.md
│   ├── integration_test_results.md
│   ├── project_structure.md (このファイル)
│   └── implementation_notes/  # 実装メモ
│       ├── BUGFIX_BOUNDING_BOX_FPS.md
│       ├── FIX_GUI_LOG_DISPLAY.md
│       ├── IMPLEMENTATION_SUMMARY_TASK14.md
│       ├── IMPLEMENTATION_TASK6_ERROR_HANDLING.md
│       └── TESTING_GUI_PREVIEW.md
├── models/                 # 学習済みモデル
│   ├── best.pt            # 既存モデル（list-item全体）
│   ├── hierarchical_best.pt  # 階層的モデル（5クラス）
│   └── hierarchical-detection/  # 学習結果
├── output/                 # 出力ファイル
│   ├── hierarchical_data.csv  # 階層的検出CSV
│   └── sessions/          # セッションフォルダ
├── scripts/                # スクリプト
│   ├── train_hierarchical_model.py  # 階層的モデル学習
│   ├── train_yolov8.py    # 既存モデル学習
│   └── debug/             # デバッグスクリプト
│       └── debug_annotations.py
├── src/                    # ソースコード
│   ├── config.py          # 設定管理
│   ├── data_manager.py    # データ管理（既存）
│   ├── detection_cache.py # 検出キャッシュ
│   ├── error_handler.py   # エラーハンドリング
│   ├── gui_app.py         # GUIアプリケーション
│   ├── hierarchical_data_manager.py  # 階層的データ管理
│   ├── hierarchical_detector.py      # 階層的検出器
│   ├── hierarchical_ocr_processor.py # 階層的OCR処理
│   ├── hierarchical_pipeline.py      # 階層的パイプライン
│   ├── iou_calculator.py  # IoU計算
│   ├── object_detector.py # 物体検出
│   ├── ocr_cache.py       # OCRキャッシュ
│   ├── ocr_processor.py   # OCR処理
│   ├── performance_mode.py # パフォーマンスモード
│   ├── performance_monitor.py # パフォーマンス監視
│   ├── pipeline_processor.py  # パイプライン処理
│   ├── realtime_ocr_app.py    # リアルタイムOCRアプリ
│   ├── session_manager.py     # セッション管理
│   ├── visualizer.py      # 可視化
│   └── window_capture.py  # ウィンドウキャプチャ
├── temp/                   # 一時ファイル
│   ├── annotations/       # アノテーションデータ
│   └── test_screenshot/   # テスト用スクリーンショット
├── tests/                  # テストコード
│   ├── __init__.py
│   ├── test_cache_modules.py
│   ├── test_data_manager_callback.py
│   ├── test_data_manager.py
│   ├── test_error_handler.py
│   ├── test_error_handling.py
│   ├── test_gui_hierarchical.py
│   ├── test_gui_states.py
│   ├── test_hierarchical_data_manager.py
│   ├── test_hierarchical_integration.py
│   ├── test_object_detector.py
│   ├── test_ocr_processor.py
│   ├── test_performance_monitor.py
│   ├── test_real_image.py
│   ├── test_visualizer.py
│   └── test_window_capture.py
├── venv/                   # Python仮想環境
├── .gitignore             # Git除外設定
├── README.md              # プロジェクトREADME
└── requirements.txt       # Python依存関係

```

## ファイルの役割

### ルートディレクトリ

| ファイル | 説明 |
|---------|------|
| README.md | プロジェクトの概要、セットアップ手順、使用方法 |
| requirements.txt | Python依存パッケージのリスト |
| .gitignore | Git管理から除外するファイル・ディレクトリ |
| book_data_realtime.csv | 既存モードのCSV出力（デフォルト） |
| yolov8n.pt | YOLOv8ベースモデル |

### docs/ - ドキュメント

| ファイル | 説明 |
|---------|------|
| DEVELOPMENT.md | 開発ガイド（環境構築、開発フロー） |
| error_handling_implementation.md | エラーハンドリング実装の詳細 |
| gui_testing_guide.md | GUI動作確認の手動テストガイド |
| hierarchical_model_training.md | 階層的モデル学習の詳細ガイド |
| integration_test_results.md | 統合テスト結果のまとめ |
| project_structure.md | プロジェクト構成の説明（このファイル） |

### docs/implementation_notes/ - 実装メモ

| ファイル | 説明 |
|---------|------|
| BUGFIX_BOUNDING_BOX_FPS.md | バウンディングボックス・FPS表示のバグ修正 |
| FIX_GUI_LOG_DISPLAY.md | GUIログ表示の修正 |
| IMPLEMENTATION_SUMMARY_TASK14.md | タスク14実装のまとめ |
| IMPLEMENTATION_TASK6_ERROR_HANDLING.md | タスク6エラーハンドリング実装 |
| TESTING_GUI_PREVIEW.md | GUIプレビュー機能のテスト |

### scripts/ - スクリプト

| ファイル | 説明 |
|---------|------|
| train_hierarchical_model.py | 階層的検出用5クラスモデルの学習スクリプト |
| train_yolov8.py | 既存モデル（list-item全体）の学習スクリプト |
| debug/debug_annotations.py | アノテーションデータのデバッグスクリプト |

### src/ - ソースコード

#### コア機能

| ファイル | 説明 |
|---------|------|
| config.py | アプリケーション設定の管理 |
| realtime_ocr_app.py | リアルタイムOCRアプリケーションのメインエントリポイント |
| gui_app.py | GUIアプリケーション（Tkinter） |

#### 既存モード（list-item全体検出）

| ファイル | 説明 |
|---------|------|
| object_detector.py | YOLOv8を使用した物体検出 |
| ocr_processor.py | Tesseractを使用したOCR処理 |
| data_manager.py | データ管理と重複排除 |
| pipeline_processor.py | パイプライン処理 |

#### 階層的モード（5クラス検出）

| ファイル | 説明 |
|---------|------|
| hierarchical_detector.py | 5クラス（list-item, title, progress, last_read_date, site_name）の検出 |
| hierarchical_ocr_processor.py | 階層的検出結果に対するOCR処理 |
| hierarchical_data_manager.py | 階層的データの管理と重複排除 |
| hierarchical_pipeline.py | 階層的検出パイプライン |
| iou_calculator.py | IoU（Intersection over Union）計算 |
| session_manager.py | セッション管理（画像保存・ZIP圧縮） |

#### ユーティリティ

| ファイル | 説明 |
|---------|------|
| window_capture.py | macOSウィンドウキャプチャ（Quartz） |
| visualizer.py | 検出結果の可視化 |
| error_handler.py | エラーハンドリング |
| performance_monitor.py | パフォーマンス監視 |
| performance_mode.py | パフォーマンスモード設定 |
| detection_cache.py | 検出結果のキャッシュ |
| ocr_cache.py | OCR結果のキャッシュ |

### tests/ - テストコード

#### ユニットテスト

| ファイル | 説明 |
|---------|------|
| test_object_detector.py | 物体検出のテスト |
| test_ocr_processor.py | OCR処理のテスト |
| test_data_manager.py | データ管理のテスト |
| test_error_handler.py | エラーハンドリングのテスト |
| test_visualizer.py | 可視化のテスト |
| test_window_capture.py | ウィンドウキャプチャのテスト |
| test_hierarchical_data_manager.py | 階層的データ管理のテスト |

#### 統合テスト

| ファイル | 説明 |
|---------|------|
| test_hierarchical_integration.py | 階層的検出機能の統合テスト |
| test_gui_hierarchical.py | GUI階層的検出機能のテスト |
| test_real_image.py | 実画像を使用したテスト |

#### その他のテスト

| ファイル | 説明 |
|---------|------|
| test_cache_modules.py | キャッシュモジュールのテスト |
| test_data_manager_callback.py | データマネージャコールバックのテスト |
| test_error_handling.py | エラーハンドリングのテスト |
| test_gui_states.py | GUI状態管理のテスト |
| test_performance_monitor.py | パフォーマンス監視のテスト |

## 実行方法

### アプリケーションの起動

```bash
# GUIアプリケーション
python src/gui_app.py

# CLIアプリケーション（既存モード）
python src/realtime_ocr_app.py
```

### モデルの学習

```bash
# 階層的モデル（5クラス）
python scripts/train_hierarchical_model.py

# 既存モデル（list-item全体）
python scripts/train_yolov8.py
```

### テストの実行

```bash
# すべてのテストを実行
pytest tests/

# 特定のテストを実行
pytest tests/test_hierarchical_integration.py

# 統合テスト
python tests/test_hierarchical_integration.py
python tests/test_gui_hierarchical.py
```

## 開発ワークフロー

1. **機能開発**: `.kiro/specs/`で仕様を定義
2. **実装**: `src/`にコードを追加
3. **テスト**: `tests/`にテストを追加
4. **ドキュメント**: `docs/`にドキュメントを追加
5. **実装メモ**: `docs/implementation_notes/`に記録

## 注意事項

- **仮想環境**: 必ず`venv/`を使用してください
- **Git管理**: ファイル移動は`git mv`を使用してください
- **テスト**: 新機能追加時は必ずテストを書いてください
- **ドキュメント**: 重要な変更は`docs/`に記録してください

## 関連ドキュメント

- [README.md](../README.md): プロジェクト概要
- [DEVELOPMENT.md](DEVELOPMENT.md): 開発ガイド
- [hierarchical_model_training.md](hierarchical_model_training.md): モデル学習ガイド
- [gui_testing_guide.md](gui_testing_guide.md): GUIテストガイド
- [integration_test_results.md](integration_test_results.md): 統合テスト結果
