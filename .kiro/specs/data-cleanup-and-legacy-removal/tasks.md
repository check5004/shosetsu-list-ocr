# Implementation Plan

- [x] 1. OCR テキストの改行削除機能の実装

  - `src/ocr_processor.py`の`cleanup_text()`メソッドを更新
  - `remove_newlines`パラメータを追加し、title フィールド用の改行削除ロジックを実装
  - 改行文字を削除し、連続する空白を 1 つに正規化
  - `src/hierarchical_ocr_processor.py`で title フィールドの OCR 時に`remove_newlines=True`を指定
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 2. HierarchicalDataManager の拡張
- [x] 2.1 StructuredRecord データクラスの拡張

  - `src/hierarchical_data_manager.py`の`StructuredRecord`に`confirmed`と`confirmed_at`フィールドを追加
  - デフォルト値を設定（`confirmed=False`, `confirmed_at=None`）
  - _Requirements: 6.1, 6.10_

- [x] 2.2 レコード確認機能の実装

  - `confirm_record()`メソッドを実装（レコードを確定し、タイムスタンプを記録）
  - `unconfirm_record()`メソッドを実装（確定を解除）
  - _Requirements: 6.2, 6.9_

- [x] 2.3 類似レコード検索機能の実装

  - `find_similar_records()`メソッドを実装
  - 指定されたタイトルと類似度の高いレコードを検索
  - 類似度とともにレコードのリストを返す
  - _Requirements: 6.3_

- [x] 2.4 レコード更新・削除機能の実装

  - `update_record()`メソッドを実装（任意のフィールドを更新）
  - `delete_records()`メソッドを実装（複数レコードを一括削除）
  - _Requirements: 4.2, 5.3_

- [x] 2.5 統計情報取得機能の実装

  - `get_statistics()`メソッドを実装
  - 総レコード数、確定済み数、エラー数、未確認数を返す
  - _Requirements: 11.3_

- [x] 2.6 CSV 出力に確認ステータスを追加

  - `export_to_csv()`メソッドを更新
  - `confirmed`と`confirmed_at`列を CSV 出力に含める
  - _Requirements: 6.10, 6.11_

- [x] 3. CSVImportExport クラスの実装
- [x] 3.1 CSVImportExport クラスの基本構造を作成

  - `src/csv_import_export.py`を作成
  - `CSVImportExport`クラスを定義
  - 初期化メソッドを実装（data_manager への参照を保持）
  - _Requirements: 10.1_

- [x] 3.2 CSV エクスポート機能の実装

  - `export_to_csv()`メソッドを実装
  - pandas を使用して DataFrame を作成
  - 確認ステータスを含むすべてのフィールドをエクスポート
  - ファイルパスが指定されない場合はデフォルトパスを使用
  - _Requirements: 10.2, 10.3, 10.4, 10.5_

- [x] 3.3 CSV インポート機能の実装

  - `import_from_csv()`メソッドを実装
  - pandas を使用して CSV を読み込み
  - 確認ステータスを含むすべてのフィールドを復元
  - 既存データがある場合は上書き確認
  - _Requirements: 10.7, 10.8, 10.9, 10.12_

- [x] 3.4 CSV 形式検証機能の実装

  - `validate_csv_format()`メソッドを実装
  - 必須列の存在確認
  - データ型の検証
  - エラーメッセージの生成
  - _Requirements: 10.10_

- [x] 4. RecordTableManager クラスの実装
- [x] 4.1 RecordTableManager クラスの基本構造を作成

  - `src/record_table_manager.py`を作成
  - `RecordTableManager`クラスを定義
  - 初期化メソッドを実装
  - _Requirements: 3.1_

- [x] 4.2 テーブルウィジェットの作成

  - `create_table()`メソッドを実装
  - Treeview ウィジェットを作成
  - 列を定義（確認、タイトル、進捗、日付、サイト、エラー、アクション）
  - スクロールバーを追加
  - _Requirements: 3.2, 3.3, 3.4_

- [x] 4.3 テーブルへのレコード表示機能の実装

  - `populate_table()`メソッドを実装
  - フィルタリング機能を実装（all, error, no_error, unconfirmed）
  - ソート機能を実装（列名と方向を指定）
  - 行のスタイリングを適用（カラーコーディング）
  - _Requirements: 3.5, 7.2, 7.3, 8.2, 8.3, 11.1_

- [x] 4.4 インライン編集機能の実装

  - `on_double_click()`メソッドを実装（編集開始）
  - `on_edit_complete()`メソッドを実装（編集保存）
  - 確定済みレコードの編集を防止
  - 編集中の視覚的フィードバック
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 4.5 削除機能の実装

  - `on_delete_click()`メソッドを実装
  - 削除確認ダイアログを表示
  - 確定済みレコードの削除を防止
  - 複数選択削除をサポート
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 4.6 確定機能の実装

  - `on_confirm_click()`メソッドを実装
  - 類似レコードを検索
  - 類似レコードが存在する場合は重複検出モーダルを表示
  - 類似レコードがない場合は直接確定
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 4.7 行スタイリング機能の実装

  - `apply_row_styling()`メソッドを実装
  - 確定済み、エラー、未確認、通常のレコードを色分け
  - _Requirements: 6.8, 11.1_

- [x] 5. DuplicateDetectionModal クラスの実装
- [x] 5.1 DuplicateDetectionModal クラスの基本構造を作成

  - `src/duplicate_detection_modal.py`を作成
  - `DuplicateDetectionModal`クラスを定義
  - 初期化メソッドを実装
  - _Requirements: 6.4_

- [x] 5.2 モーダル UI の構築

  - `setup_ui()`メソッドを実装
  - 確定レコード編集エリアを作成（タイトル、進捗、日付、サイト）
  - 類似レコードリストを作成（チェックボックス付き）
  - 確定・キャンセルボタンを配置
  - _Requirements: 6.5, 6.6, 6.7_

- [x] 5.3 確定処理の実装

  - `on_confirm()`メソッドを実装
  - 確定レコードの編集内容を保存
  - 選択された類似レコードを削除
  - 確定レコードをロック
  - _Requirements: 6.2, 6.6, 6.7_

- [x] 5.4 モーダル表示とイベント処理

  - `show()`メソッドを実装
  - モーダルダイアログとして表示
  - ユーザーの選択結果を返す
  - _Requirements: 6.4_

- [x] 6. DataEditorWindow クラスの実装
- [x] 6.1 DataEditorWindow クラスの基本構造を作成

  - `src/data_editor_window.py`を作成
  - `DataEditorWindow`クラスを定義
  - 初期化メソッドを実装（Toplevel ウィンドウを作成）
  - _Requirements: 3.1, 9.3_

- [x] 6.2 ツールバーの実装

  - `setup_toolbar()`メソッドを実装
  - インポートボタンを追加
  - エクスポートボタンを追加
  - フィルタードロップダウンを追加
  - 統計情報表示エリアを追加
  - _Requirements: 10.1, 10.6, 8.1, 11.3_

- [x] 6.3 テーブル表示エリアの実装

  - `RecordTableManager`を統合
  - テーブルを配置
  - リアルタイム更新機能を実装
  - _Requirements: 3.2, 3.5_

- [x] 6.4 フィルタリング機能の実装

  - `on_filter_changed()`メソッドを実装
  - フィルタータイプに応じてテーブルを更新
  - フィルタリングされたレコード数を表示
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 6.5 ソート機能の実装

  - `on_column_header_click()`メソッドを実装
  - クリックされた列でソート
  - ソート方向を切り替え（昇順/降順）
  - 現在のソート列と方向を視覚的に表示
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 6.6 CSV インポート/エクスポート機能の統合

  - `on_import_csv()`メソッドを実装
  - `on_export_csv()`メソッドを実装
  - `CSVImportExport`クラスを使用
  - 成功/失敗のフィードバックを表示
  - _Requirements: 10.1, 10.2, 10.5, 10.6, 10.7, 10.11_

- [x] 6.7 統計情報表示の実装

  - 統計情報パネルを作成
  - 総レコード数、確定済み、エラー、未確認を表示
  - リアルタイムで更新
  - _Requirements: 11.3_

- [x] 6.8 キーボードショートカットの実装

  - 削除（Delete）、編集（F2）、確定（Ctrl+Enter）などのショートカットを実装
  - _Requirements: 11.4_

- [x] 6.9 自動保存機能の実装

  - 編集時に自動的にデータマネージャーに保存
  - _Requirements: 11.5_

- [x] 6.10 Undo 機能の実装

  - `EditAction`を使用した編集履歴の管理
  - Undo ボタンまたはショートカット（Ctrl+Z）の実装
  - _Requirements: 11.6_

- [ ] 7. メイン GUI へのデータエディター統合
- [ ] 7.1 データエディター起動ボタンの追加

  - `src/gui_app.py`の制御パネルに「データエディター」ボタンを追加
  - `_open_data_editor()`メソッドを実装
  - _Requirements: 9.1_

- [ ] 7.2 データエディターウィンドウの管理

  - データエディターウィンドウへの参照を保持
  - 既に開いている場合はフォーカス
  - 閉じて再度開ける機能
  - _Requirements: 9.3, 9.5_

- [ ] 7.3 データ同期の実装

  - メイン GUI とデータエディター間で data_manager を共有
  - リアルタイムでデータを同期
  - _Requirements: 9.2, 9.4_

- [ ] 8. Legacy Mode（既存モデル）の削除
- [ ] 8.1 PipelineProcessor の削除

  - `src/pipeline_processor.py`ファイルを削除
  - 関連するインポートを削除
  - _Requirements: 1.2_

- [ ] 8.2 DataManager の削除

  - `src/data_manager.py`ファイルを削除（階層的版のみ残す）
  - 関連するインポートを削除
  - _Requirements: 1.2_

- [ ] 8.3 GUI から Legacy Mode UI の削除

  - `src/gui_app.py`からモデル選択ラジオボタンを削除
  - `detection_mode_var`変数を削除
  - `_start_legacy_processing()`メソッドを削除
  - Legacy mode 関連のツールチップとヘルプテキストを削除
  - _Requirements: 1.3_

- [ ] 8.4 AppConfig から Legacy Mode 設定の削除

  - `src/config.py`から`model_path`フィールドを削除
  - `src/config.py`から`output_csv`フィールドを削除（階層的版のみ使用）
  - 環境変数関連の削除（`OCR_MODEL_PATH`, `OCR_OUTPUT_CSV`）
  - バリデーションロジックの更新
  - _Requirements: 1.4_

- [ ] 8.5 未使用インポートとデッドコードの削除

  - `src/gui_app.py`から未使用インポートを削除
  - Legacy mode 関連のコメントを削除
  - _Requirements: 1.5, 1.7, 12.4_

- [ ] 8.6 ドキュメントの更新

  - `README.md`から Legacy mode の説明を削除
  - 階層的検出モードのみを使用することを明記
  - _Requirements: 1.6_

- [ ] 9. 動作確認とテスト
- [ ] 9.1 Legacy Mode 削除後の動作確認

  - アプリケーションがエラーなく起動することを確認
  - 階層的検出が正常に動作することを確認
  - CSV 出力が正常に動作することを確認
  - _Requirements: 12.1, 12.2, 12.3_

- [ ] 9.2 OCR 改行削除の動作確認

  - title フィールドの改行が削除されることを確認
  - 他のフィールド（progress, last_read_date, site_name）は改行が保持されることを確認
  - _Requirements: 2.1, 2.4_

- [ ] 9.3 データエディターの動作確認

  - データエディターが正常に開くことを確認
  - レコードが正しく表示されることを確認
  - インライン編集が動作することを確認
  - 削除機能が動作することを確認
  - 確定機能が動作することを確認
  - _Requirements: 3.1, 3.2, 4.1, 5.1, 6.1_

- [ ] 9.4 重複検出モーダルの動作確認

  - 確定時に類似レコードが検出されることを確認
  - モーダルが正しく表示されることを確認
  - 確定レコードの編集が動作することを確認
  - 類似レコードの削除が動作することを確認
  - _Requirements: 6.3, 6.4, 6.5, 6.6, 6.7_

- [ ] 9.5 CSV インポート/エクスポートの動作確認

  - エクスポートが正常に動作することを確認
  - インポートが正常に動作することを確認
  - 確認ステータスが保持されることを確認
  - _Requirements: 10.2, 10.3, 10.8, 10.9_

- [ ] 9.6 フィルタリングとソートの動作確認

  - 各フィルタータイプが正しく動作することを確認
  - 各列のソートが正しく動作することを確認
  - _Requirements: 8.2, 8.3, 7.2, 7.3_

- [ ] 10. 最終調整とドキュメント更新
  - エラーメッセージの改善
  - ツールチップの追加
  - README.md の最終更新（データエディター機能の説明を追加）
  - スクリーンショットの追加（オプション）
  - _Requirements: 11.2, 12.5_
