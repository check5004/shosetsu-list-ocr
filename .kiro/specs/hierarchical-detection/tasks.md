# Implementation Plan

- [ ] 1. データセット準備と学習環境のセットアップ
  - temp/shosetsu-list-item_dataset_v2のアノテーションデータを確認
  - data.yamlファイルを作成し、5クラス（list-item, title, progress, last_read_date, site_name）を定義
  - アノテーション形式がYOLO形式（class_id x_center y_center width height）であることを確認
  - _Requirements: 1.1, 1.2, 10.2_

- [ ] 2. 階層的検出モデルの学習
  - train_hierarchical_model.pyスクリプトを作成
  - 既存のtrain_yolov8.pyの設定を参考に、データ拡張パラメータを強化（hsv_h, hsv_s, hsv_v, degrees, translate, scale, mosaic, mixup, copy_paste）
  - YOLOv8nモデルをベースに、temp/shosetsu-list-item_dataset_v2で学習を実行
  - 学習済みモデルをmodels/hierarchical_best.ptとして保存
  - 学習結果（mAP、precision、recall）を確認
  - _Requirements: 1.3, 1.4, 1.5, 1.6, 1.7, 10.1, 10.3, 10.4, 10.5, 10.6, 10.7_

- [ ] 3. IoU計算ロジックの実装
- [ ] 3.1 IoU計算関数を実装
  - src/iou_calculator.pyを作成
  - calculate_iou()関数を実装（2つのbounding box間のIoU計算）
  - 交差領域、和領域の計算ロジックを実装
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [ ]* 3.2 IoU計算の単体テストを作成
  - tests/test_iou_calculator.pyを作成
  - 完全一致（IoU=1.0）、部分重複、非重複（IoU=0.0）のテストケースを実装
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 12.4_

- [ ] 4. HierarchicalDetectorモジュールの実装
- [ ] 4.1 データクラスの定義
  - src/hierarchical_detector.pyを作成
  - HierarchicalDetectionResultデータクラスを定義
  - has_required_fields()メソッドとget_error_status()メソッドを実装
  - _Requirements: 2.7, 4.3, 4.4_

- [ ] 4.2 HierarchicalDetectorクラスの基本構造を作成
  - HierarchicalDetectorクラスを定義
  - 初期化メソッドを実装（モデルロード、しきい値設定）
  - 5クラスのclass_namesを定義
  - _Requirements: 1.1, 2.1_

- [ ] 4.3 検出と分類ロジックを実装
  - detect()メソッドを実装
  - YOLOv8推論を実行し、5クラスの検出結果を取得
  - 検出結果をlist-itemと子要素に分類
  - _Requirements: 2.1, 2.2_

- [ ] 4.4 親子関係構築ロジックを実装
  - _build_hierarchy()メソッドを実装
  - 各子要素について、IoUが最大かつしきい値以上のlist-itemを親として紐付け
  - 孤立した子要素を検出し、警告ログを出力
  - _Requirements: 2.3, 2.4, 2.5, 2.6, 2.7_

- [ ]* 4.5 HierarchicalDetectorの単体テストを作成
  - tests/test_hierarchical_detector.pyを作成
  - 親子関係構築ロジックのテストケースを実装
  - _Requirements: 2.3, 2.4, 2.5, 2.6, 2.7, 12.5_

- [ ] 5. SessionManagerモジュールの実装
- [ ] 5.1 SessionManagerクラスの基本構造を作成
  - src/session_manager.pyを作成
  - SessionManagerクラスを定義
  - 初期化メソッドを実装（base_output_dir設定）
  - _Requirements: 5.1_

- [ ] 5.2 セッション開始機能を実装
  - start_session()メソッドを実装
  - タイムスタンプ（YYYYMMDD_HHMMSS）を生成
  - セッション専用フォルダを作成（output/sessions/YYYYMMDD_HHMMSS/）
  - _Requirements: 5.1_

- [ ] 5.3 画像切り出しと保存機能を実装
  - save_list_item_image()メソッドを実装
  - マージン付きでbounding box領域を切り出し
  - 一意のファイル名（list_item_001.jpg等）を生成
  - セッションフォルダに保存
  - 相対パスを返す
  - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.9_

- [ ] 5.4 セッション終了とZIP圧縮機能を実装
  - end_session()メソッドを実装
  - セッションフォルダをZIPファイルに圧縮
  - 圧縮完了後、元のフォルダを削除（オプション）
  - エラーハンドリングを実装
  - _Requirements: 5.6, 5.7, 5.9_

- [ ] 5.5 Finderでフォルダを開く機能を実装
  - open_session_folder()メソッドを実装
  - macOSのopenコマンドを使用してFinderで開く
  - _Requirements: 11.6, 11.7_

- [ ] 6. .gitignore設定の更新
  - .gitignoreファイルにoutput/sessions/ディレクトリを追加
  - ZIPファイルも除外設定に追加（*.zip）
  - _Requirements: 5.10_

- [ ] 7. HierarchicalDataManagerモジュールの実装
- [ ] 7.1 データクラスとHierarchicalDataManagerクラスの基本構造を作成
  - src/hierarchical_data_manager.pyを作成
  - StructuredRecordデータクラスを定義
  - HierarchicalDataManagerクラスを定義
  - 初期化メソッドを実装（similarity_threshold設定）
  - _Requirements: 4.1, 7.1, 7.10_

- [ ] 7.2 曖昧マッチングによる重複チェック機能を実装
  - _is_duplicate()メソッドを実装
  - difflib.SequenceMatcherを使用して文字列類似度を計算
  - 類似度がしきい値以上の場合、重複と判定
  - 重複検出時、類似度と既存タイトルをログ出力
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.8_

- [ ] 7.3 レコード追加機能を実装
  - add_record()メソッドを実装
  - 曖昧マッチングで重複チェックを実行
  - 新規データの場合、StructuredRecordを作成してリストに追加
  - 新規データ検出時、ターミナルにメッセージを表示
  - _Requirements: 7.6, 7.7, 7.9_

- [ ] 7.4 CSV出力機能を実装
  - export_to_csv()メソッドを実装
  - pandasを使用してDataFrameを作成
  - UTF-8エンコーディングでCSV出力
  - 統計情報（総件数、正常件数、エラー件数）を表示
  - _Requirements: 4.1, 4.2, 4.7, 4.8, 4.9_

- [ ]* 7.5 HierarchicalDataManagerの単体テストを作成
  - tests/test_hierarchical_data_manager.pyを作成
  - 曖昧マッチングのテストケースを実装
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 12.4_

- [ ] 8. OCR統合機能の実装
- [ ] 8.1 階層的検出結果に対するOCR処理を実装
  - src/hierarchical_ocr_processor.pyを作成
  - process_hierarchical_detection()関数を実装
  - 各子要素（title、progress、last_read_date、site_name）のbounding boxに対してOCR処理を実行
  - 既存のOCRProcessorモジュールを再利用
  - OCRエラー時は空文字列を返して処理を継続
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 9. 設定管理の拡張
- [ ] 9.1 AppConfigデータクラスを拡張
  - src/config.pyを更新
  - 階層的検出関連の設定項目を追加（hierarchical_model_path, use_hierarchical_detection, iou_threshold, similarity_threshold, session_output_dir, hierarchical_csv_output）
  - デフォルト値を設定
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 10. パイプライン処理の統合
- [ ] 10.1 階層的検出パイプラインを実装
  - src/hierarchical_pipeline.pyを作成
  - HierarchicalPipelineクラスを定義
  - 全体フロー（検出 → 階層化 → OCR → 画像保存 → 重複チェック → レコード追加）を実装
  - エラーハンドリングを実装
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [ ] 10.2 セッション開始・終了処理を統合
  - パイプライン開始時にSessionManager.start_session()を呼び出し
  - パイプライン終了時にSessionManager.end_session()を呼び出し
  - CSV出力を実行
  - _Requirements: 5.1, 5.6, 5.7, 4.8_

- [ ] 11. GUIアプリケーションの拡張
- [ ] 11.1 モデル選択機能を追加
  - src/gui_app.pyを更新
  - モデル選択ラジオボタンを追加（既存モデル vs 階層的モデル）
  - 選択に応じて使用するパイプラインを切り替え
  - _Requirements: 11.1, 11.2, 11.3_

- [ ] 11.2 画像フォルダ管理パネルを追加
  - 「画像フォルダを開く」ボタンを追加
  - ボタン押下時、SessionManager.open_session_folder()を呼び出し
  - 画像保存先ディレクトリ設定オプションを追加（オプション）
  - _Requirements: 11.6, 11.7, 11.8, 11.9_

- [ ] 11.3 統計情報パネルを拡張
  - 各クラスの検出数を個別に表示（list-item数、title検出数等）
  - エラー件数と正常件数を表示
  - 類似度しきい値スライダーを追加
  - _Requirements: 11.5, 7.10_

- [ ] 11.4 階層的検出モード時のプレビュー表示を実装
  - 5クラスのbounding boxを異なる色で描画
  - 各クラスのラベルを表示
  - _Requirements: 11.4_

- [ ] 12. エラーハンドリングの強化
  - 孤立した子要素の警告ログ出力
  - IoU計算エラー時のデフォルト値使用
  - 画像切り出し失敗時のエラーログ出力と処理継続
  - OCR処理エラー時の空文字列返却と処理継続
  - 予期しないエラーのログ出力と処理継続
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 13. ドキュメントの更新
- [ ] 13.1 README.mdを更新
  - 階層的検出機能の説明を追加
  - 学習データセットの準備方法を記載
  - アノテーション形式とクラスラベルの定義を記載
  - 新しいGUI機能の使用方法を記載
  - _Requirements: 12.1, 12.2, 12.3_

- [ ] 13.2 学習スクリプトのドキュメントを作成
  - train_hierarchical_model.pyにdocstringを追加
  - データ拡張パラメータの説明を記載
  - 学習結果の確認方法を記載
  - _Requirements: 12.2, 12.3_

- [ ] 14. 統合テストと動作確認
- [ ] 14.1 サンプル画像を使用した全体フローのテスト
  - temp/test_screenshot/内の画像を使用
  - 階層的検出 → OCR → CSV出力の全体フローを確認
  - セッションフォルダの作成とZIP圧縮を確認
  - _Requirements: 12.6_

- [ ] 14.2 エラーケースの動作確認
  - 必須項目欠損時のerror_status記録を確認
  - 重複データの曖昧マッチング動作を確認
  - 孤立要素の警告ログ出力を確認
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 14.3 GUIでの動作確認
  - モデル選択機能の動作確認
  - 画像フォルダを開く機能の動作確認
  - 統計情報の表示確認
  - 類似度しきい値スライダーの動作確認
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

- [ ] 15. 最終調整とリリース準備
  - 信頼度しきい値、IoUしきい値、類似度しきい値の最適化
  - エラーメッセージの改善
  - パフォーマンスの確認（フレームレート、メモリ使用量）
  - README.mdの最終更新（実際の動作結果を反映）
  - サンプルCSV出力の追加
  - _Requirements: 8.1, 8.2, 8.3, 8.4_
