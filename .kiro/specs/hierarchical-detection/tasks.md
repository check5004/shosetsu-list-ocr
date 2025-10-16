# Implementation Plan

- [x] 1. データセット準備と学習環境のセットアップ

  - temp/shosetsu-list-item_dataset_v2 のアノテーションデータを確認
  - data.yaml ファイルを作成し、5 クラス（list-item, title, progress, last_read_date, site_name）を定義
  - アノテーション形式が YOLO 形式（class_id x_center y_center width height）であることを確認
  - _Requirements: 1.1, 1.2, 10.2_

- [x] 2. 階層的検出モデルの学習

  - train_hierarchical_model.py スクリプトを作成
  - 既存の train_yolov8.py の設定を参考に、データ拡張パラメータを強化（hsv_h, hsv_s, hsv_v, degrees, translate, scale, mosaic, mixup, copy_paste）
  - YOLOv8n モデルをベースに、temp/shosetsu-list-item_dataset_v2 で学習を実行
  - 学習済みモデルを models/hierarchical_best.pt として保存
  - 学習結果（mAP、precision、recall）を確認
  - _Requirements: 1.3, 1.4, 1.5, 1.6, 1.7, 10.1, 10.3, 10.4, 10.5, 10.6, 10.7_

- [-] 3. IoU 計算ロジックの実装
- [x] 3.1 IoU 計算関数を実装

  - src/iou_calculator.py を作成
  - calculate_iou()関数を実装（2 つの bounding box 間の IoU 計算）
  - 交差領域、和領域の計算ロジックを実装
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [ ]\* 3.2 IoU 計算の単体テストを作成

  - tests/test_iou_calculator.py を作成
  - 完全一致（IoU=1.0）、部分重複、非重複（IoU=0.0）のテストケースを実装
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 12.4_

- [x] 4. HierarchicalDetector モジュールの実装
- [x] 4.1 データクラスの定義

  - src/hierarchical_detector.py を作成
  - HierarchicalDetectionResult データクラスを定義
  - has_required_fields()メソッドと get_error_status()メソッドを実装
  - _Requirements: 2.7, 4.3, 4.4_

- [x] 4.2 HierarchicalDetector クラスの基本構造を作成

  - HierarchicalDetector クラスを定義
  - 初期化メソッドを実装（モデルロード、しきい値設定）
  - 5 クラスの class_names を定義
  - _Requirements: 1.1, 2.1_

- [x] 4.3 検出と分類ロジックを実装

  - detect()メソッドを実装
  - YOLOv8 推論を実行し、5 クラスの検出結果を取得
  - 検出結果を list-item と子要素に分類
  - _Requirements: 2.1, 2.2_

- [x] 4.4 親子関係構築ロジックを実装

  - \_build_hierarchy()メソッドを実装
  - 各子要素について、IoU が最大かつしきい値以上の list-item を親として紐付け
  - 孤立した子要素を検出し、警告ログを出力
  - _Requirements: 2.3, 2.4, 2.5, 2.6, 2.7_

- [ ]\* 4.5 HierarchicalDetector の単体テストを作成

  - tests/test_hierarchical_detector.py を作成
  - 親子関係構築ロジックのテストケースを実装
  - _Requirements: 2.3, 2.4, 2.5, 2.6, 2.7, 12.5_

- [x] 5. SessionManager モジュールの実装
- [x] 5.1 SessionManager クラスの基本構造を作成

  - src/session_manager.py を作成
  - SessionManager クラスを定義
  - 初期化メソッドを実装（base_output_dir 設定）
  - _Requirements: 5.1_

- [x] 5.2 セッション開始機能を実装

  - start_session()メソッドを実装
  - タイムスタンプ（YYYYMMDD_HHMMSS）を生成
  - セッション専用フォルダを作成（output/sessions/YYYYMMDD_HHMMSS/）
  - _Requirements: 5.1_

- [x] 5.3 画像切り出しと保存機能を実装

  - save_list_item_image()メソッドを実装
  - マージン付きで bounding box 領域を切り出し
  - 一意のファイル名（list_item_001.jpg 等）を生成
  - セッションフォルダに保存
  - 相対パスを返す
  - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.9_

- [x] 5.4 セッション終了と ZIP 圧縮機能を実装

  - end_session()メソッドを実装
  - セッションフォルダを ZIP ファイルに圧縮
  - 圧縮完了後、元のフォルダを削除（オプション）
  - エラーハンドリングを実装
  - _Requirements: 5.6, 5.7, 5.9_

- [x] 5.5 Finder でフォルダを開く機能を実装

  - open_session_folder()メソッドを実装
  - macOS の open コマンドを使用して Finder で開く
  - _Requirements: 11.6, 11.7_

- [x] 6. .gitignore 設定の更新

  - .gitignore ファイルに output/sessions/ディレクトリを追加
  - ZIP ファイルも除外設定に追加（\*.zip）
  - _Requirements: 5.10_

- [ ] 7. HierarchicalDataManager モジュールの実装
- [ ] 7.1 データクラスと HierarchicalDataManager クラスの基本構造を作成

  - src/hierarchical_data_manager.py を作成
  - StructuredRecord データクラスを定義
  - HierarchicalDataManager クラスを定義
  - 初期化メソッドを実装（similarity_threshold 設定）
  - _Requirements: 4.1, 7.1, 7.10_

- [ ] 7.2 曖昧マッチングによる重複チェック機能を実装

  - \_is_duplicate()メソッドを実装
  - difflib.SequenceMatcher を使用して文字列類似度を計算
  - 類似度がしきい値以上の場合、重複と判定
  - 重複検出時、類似度と既存タイトルをログ出力
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.8_

- [ ] 7.3 レコード追加機能を実装

  - add_record()メソッドを実装
  - 曖昧マッチングで重複チェックを実行
  - 新規データの場合、StructuredRecord を作成してリストに追加
  - 新規データ検出時、ターミナルにメッセージを表示
  - _Requirements: 7.6, 7.7, 7.9_

- [ ] 7.4 CSV 出力機能を実装

  - export_to_csv()メソッドを実装
  - pandas を使用して DataFrame を作成
  - UTF-8 エンコーディングで CSV 出力
  - 統計情報（総件数、正常件数、エラー件数）を表示
  - _Requirements: 4.1, 4.2, 4.7, 4.8, 4.9_

- [ ]\* 7.5 HierarchicalDataManager の単体テストを作成

  - tests/test_hierarchical_data_manager.py を作成
  - 曖昧マッチングのテストケースを実装
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 12.4_

- [ ] 8. OCR 統合機能の実装
- [ ] 8.1 階層的検出結果に対する OCR 処理を実装

  - src/hierarchical_ocr_processor.py を作成
  - process_hierarchical_detection()関数を実装
  - 各子要素（title、progress、last_read_date、site_name）の bounding box に対して OCR 処理を実行
  - 既存の OCRProcessor モジュールを再利用
  - OCR エラー時は空文字列を返して処理を継続
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 9. 設定管理の拡張
- [ ] 9.1 AppConfig データクラスを拡張

  - src/config.py を更新
  - 階層的検出関連の設定項目を追加（hierarchical_model_path, use_hierarchical_detection, iou_threshold, similarity_threshold, session_output_dir, hierarchical_csv_output）
  - デフォルト値を設定
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 10. パイプライン処理の統合
- [ ] 10.1 階層的検出パイプラインを実装

  - src/hierarchical_pipeline.py を作成
  - HierarchicalPipeline クラスを定義
  - 全体フロー（検出 → 階層化 → OCR → 画像保存 → 重複チェック → レコード追加）を実装
  - エラーハンドリングを実装
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [ ] 10.2 セッション開始・終了処理を統合

  - パイプライン開始時に SessionManager.start_session()を呼び出し
  - パイプライン終了時に SessionManager.end_session()を呼び出し
  - CSV 出力を実行
  - _Requirements: 5.1, 5.6, 5.7, 4.8_

- [ ] 11. GUI アプリケーションの拡張
- [ ] 11.1 モデル選択機能を追加

  - src/gui_app.py を更新
  - モデル選択ラジオボタンを追加（既存モデル vs 階層的モデル）
  - 選択に応じて使用するパイプラインを切り替え
  - _Requirements: 11.1, 11.2, 11.3_

- [ ] 11.2 画像フォルダ管理パネルを追加

  - 「画像フォルダを開く」ボタンを追加
  - ボタン押下時、SessionManager.open_session_folder()を呼び出し
  - 画像保存先ディレクトリ設定オプションを追加（オプション）
  - _Requirements: 11.6, 11.7, 11.8, 11.9_

- [ ] 11.3 統計情報パネルを拡張

  - 各クラスの検出数を個別に表示（list-item 数、title 検出数等）
  - エラー件数と正常件数を表示
  - 類似度しきい値スライダーを追加
  - _Requirements: 11.5, 7.10_

- [ ] 11.4 階層的検出モード時のプレビュー表示を実装

  - 5 クラスの bounding box を異なる色で描画
  - 各クラスのラベルを表示
  - _Requirements: 11.4_

- [ ] 12. エラーハンドリングの強化

  - 孤立した子要素の警告ログ出力
  - IoU 計算エラー時のデフォルト値使用
  - 画像切り出し失敗時のエラーログ出力と処理継続
  - OCR 処理エラー時の空文字列返却と処理継続
  - 予期しないエラーのログ出力と処理継続
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 13. ドキュメントの更新
- [ ] 13.1 README.md を更新

  - 階層的検出機能の説明を追加
  - 学習データセットの準備方法を記載
  - アノテーション形式とクラスラベルの定義を記載
  - 新しい GUI 機能の使用方法を記載
  - _Requirements: 12.1, 12.2, 12.3_

- [ ] 13.2 学習スクリプトのドキュメントを作成

  - train_hierarchical_model.py に docstring を追加
  - データ拡張パラメータの説明を記載
  - 学習結果の確認方法を記載
  - _Requirements: 12.2, 12.3_

- [ ] 14. 統合テストと動作確認
- [ ] 14.1 サンプル画像を使用した全体フローのテスト

  - temp/test_screenshot/内の画像を使用
  - 階層的検出 → OCR → CSV 出力の全体フローを確認
  - セッションフォルダの作成と ZIP 圧縮を確認
  - _Requirements: 12.6_

- [ ] 14.2 エラーケースの動作確認

  - 必須項目欠損時の error_status 記録を確認
  - 重複データの曖昧マッチング動作を確認
  - 孤立要素の警告ログ出力を確認
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 14.3 GUI での動作確認

  - モデル選択機能の動作確認
  - 画像フォルダを開く機能の動作確認
  - 統計情報の表示確認
  - 類似度しきい値スライダーの動作確認
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

- [ ] 15. 最終調整とリリース準備
  - 信頼度しきい値、IoU しきい値、類似度しきい値の最適化
  - エラーメッセージの改善
  - パフォーマンスの確認（フレームレート、メモリ使用量）
  - README.md の最終更新（実際の動作結果を反映）
  - サンプル CSV 出力の追加
  - _Requirements: 8.1, 8.2, 8.3, 8.4_
