# Implementation Plan

- [x] 1. プロジェクト構造とセットアップ

  - プロジェクトディレクトリ構造を作成（src/, config/, models/, output/）
  - requirements.txt ファイルを作成し、必要な依存関係を定義
  - README.md を作成し、インストール手順と macOS 権限設定を記載
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [x] 2. 設定管理モジュールの実装

  - `src/config.py`を作成し、AppConfig データクラスを定義
  - デフォルト設定値を実装（モデルパス、ウィンドウタイトル、OCR 設定など）
  - 設定の検証ロジックを実装
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 3. macOS 専用ウィンドウキャプチャモジュールの実装
- [x] 3.1 WindowCapture クラスの基本構造を作成

  - `src/window_capture.py`を作成
  - WindowCapture クラスを定義し、初期化メソッドを実装
  - _Requirements: 1.1, 1.5_

- [x] 3.2 Quartz を使用したウィンドウ検索機能を実装

  - `list_all_windows()`メソッドを実装（CGWindowListCopyWindowInfo を使用）
  - `find_window()`メソッドを実装（タイトル部分一致検索）
  - ウィンドウが見つからない場合のエラーハンドリング
  - _Requirements: 1.1, 1.2, 8.2_

- [x] 3.3 mss を使用したスクリーンキャプチャ機能を実装

  - `capture_frame()`メソッドを実装
  - ウィンドウ座標からモニター領域を計算
  - BGRA→BGR 変換を実装
  - _Requirements: 1.3, 1.4_

- [x] 3.4 ウィンドウキャプチャのテストコードを作成

  - 単体テストを作成（ウィンドウ検索、キャプチャ）
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 4. YOLOv8 物体検出モジュールの実装
- [x] 4.1 ObjectDetector クラスの基本構造を作成

  - `src/object_detector.py`を作成
  - DetectionResult データクラスを定義
  - ObjectDetector クラスを定義し、初期化メソッドを実装
  - _Requirements: 2.1, 2.6_

- [x] 4.2 YOLOv8 モデルのロードと推論機能を実装

  - モデルファイルの存在チェック
  - YOLOv8 モデルのロード（Apple Silicon MPS 対応）
  - `detect()`メソッドを実装（信頼度フィルタリング含む）
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 9.1_

- [x] 4.3 検出結果のソート機能を実装

  - `sort_by_y_coordinate()`静的メソッドを実装
  - Y 座標（上から下）でソート
  - _Requirements: 2.5_

- [x] 4.4 物体検出のテストコードを作成

  - サンプル画像を使用した検出テスト
  - ソート機能のテスト
  - _Requirements: 2.3, 2.4, 2.5_

- [x] 5. Tesseract OCR モジュールの実装
- [x] 5.1 OCRProcessor クラスの基本構造を作成

  - `src/ocr_processor.py`を作成
  - OCRProcessor クラスを定義し、初期化メソッドを実装
  - _Requirements: 4.3_

- [x] 5.2 画像切り出しと OCR 実行機能を実装

  - `extract_text()`メソッドを実装
  - バウンディングボックスからマージン付きで画像を切り出す
  - Tesseract OCR で日本語テキストを抽出
  - エラーハンドリング（OCR 失敗時は空文字列を返す）
  - _Requirements: 4.1, 4.2, 4.3, 4.6, 4.7_

- [x] 5.3 テキストクリーンアップ機能を実装

  - `cleanup_text()`静的メソッドを実装
  - 空白文字の正規化
  - 2 文字以下のテキストをフィルタリング
  - _Requirements: 4.4, 4.5_

- [x] 5.4 画像前処理機能を実装（オプション）

  - `preprocess_image()`静的メソッドを実装
  - グレースケール変換、コントラスト調整
  - _Requirements: 4.3_

- [x] 5.5 OCR モジュールのテストコードを作成

  - テキストクリーンアップのテスト
  - サンプル画像を使用した OCR テスト
  - _Requirements: 4.3, 4.4, 4.5_

- [ ] 6. データ管理モジュールの実装
- [ ] 6.1 DataManager クラスを作成

  - `src/data_manager.py`を作成
  - DataManager クラスを定義し、初期化メソッドを実装（Set ベースの重複管理）
  - _Requirements: 5.1, 5.2_

- [ ] 6.2 重複チェック機能を実装

  - `add_text()`メソッドを実装
  - Set を使用した O(1)重複チェック
  - 新規データの場合はターミナルに出力
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 6.3 CSV 出力機能を実装

  - `export_to_csv()`メソッドを実装
  - pandas を使用して DataFrame を作成
  - "extracted_text"列で CSV 出力
  - データ件数の表示
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]\* 6.4 データ管理モジュールのテストコードを作成

  - 重複チェックのテスト
  - CSV 出力のテスト
  - _Requirements: 5.1, 5.2, 6.1_

- [ ] 7. 可視化モジュールの実装
- [ ] 7.1 Visualizer クラスを作成

  - `src/visualizer.py`を作成
  - Visualizer クラスを定義し、初期化メソッドを実装
  - _Requirements: 3.1, 3.2_

- [ ] 7.2 検出結果の描画機能を実装

  - `draw_detections()`メソッドを実装
  - 緑色の矩形でバウンディングボックスを描画
  - _Requirements: 3.1_

- [ ] 7.3 フレーム表示とキー入力処理を実装

  - `show_frame()`メソッドを実装
  - OpenCV でウィンドウ表示
  - 'q'キー検出
  - `cleanup()`メソッドを実装（ウィンドウクローズ）
  - _Requirements: 3.2, 3.3, 3.4_

- [ ] 8. エラーハンドリングモジュールの実装

  - `src/error_handler.py`を作成
  - ErrorHandler クラスを作成
  - 初期化エラー、実行時エラー、安全なシャットダウンの各ハンドラを実装
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 9. メインアプリケーションの統合
- [ ] 9.1 メインスクリプトの基本構造を作成

  - `src/realtime_ocr_app.py`を作成
  - main()関数を定義
  - 設定の読み込み
  - _Requirements: 7.1, 7.2_

- [ ] 9.2 初期化処理を実装

  - 各モジュールのインスタンス化
  - YOLOv8 モデルのロード
  - ターゲットウィンドウの検索
  - 初期化エラーのハンドリング
  - _Requirements: 2.1, 2.2, 1.1, 1.2, 8.1, 8.2_

- [ ] 9.3 メインループを実装

  - ウィンドウキャプチャ
  - 物体検出
  - 検出結果のソート
  - OCR 処理（各バウンディングボックスに対して）
  - 重複チェックとデータ追加
  - 検出結果の描画
  - フレーム表示
  - _Requirements: 1.3, 2.3, 2.5, 4.1, 4.2, 4.3, 5.2, 3.1, 3.2, 3.3_

- [ ] 9.4 終了処理を実装

  - 'q'キー押下時の終了
  - Ctrl+C ハンドリング（signal.signal）
  - CSV 出力
  - ウィンドウクローズ
  - 終了メッセージ表示
  - _Requirements: 3.4, 6.1, 6.3, 6.4, 8.4_

- [ ] 10. ドキュメントとセットアップスクリプトの作成
- [ ] 10.1 README.md を更新

  - 機能概要
  - システム要件
  - インストール手順（Homebrew、pip）
  - macOS 画面収録権限の設定手順
  - 使用方法
  - トラブルシューティング
  - _Requirements: 10.1, 10.3, 10.4_

- [ ] 10.2 サンプル設定ファイルを作成

  - `config.example.yaml`を作成
  - 各設定項目の説明をコメントで記載
  - _Requirements: 7.1, 7.2, 7.3_

- [ ]\* 10.3 セットアップスクリプトを作成（オプション）

  - `setup.sh`を作成
  - Homebrew のインストールチェック
  - Tesseract のインストール
  - Python 仮想環境の作成
  - 依存関係のインストール
  - _Requirements: 10.1, 10.2, 10.3_

- [ ] 11. 統合テストと動作確認
- [ ] 11.1 Xcode シミュレータでの動作確認

  - iPhone シミュレータを起動
  - アプリケーションを実行
  - リアルタイム検出の動作確認
  - CSV 出力の確認
  - _Requirements: 1.1, 1.3, 2.3, 4.3, 6.1_

- [ ] 11.2 エラーケースの動作確認

  - モデルファイル不在時のエラー処理
  - ウィンドウが見つからない場合のエラー処理
  - OCR エラー時の継続処理
  - _Requirements: 8.1, 8.2, 8.3_

- [ ]\* 11.3 パフォーマンス測定

  - フレームレート（FPS）の測定
  - OCR 処理時間の測定
  - メモリ使用量の確認
  - _Requirements: 9.1, 9.2, 9.3_

- [ ] 12. 最終調整とドキュメント更新
  - 検出精度の調整（信頼度しきい値の最適化）
  - エラーメッセージの改善
  - README.md の最終更新（実際の動作結果を反映）
  - サンプル CSV 出力の追加
  - _Requirements: 2.4, 7.3, 8.5_
