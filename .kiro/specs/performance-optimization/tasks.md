# Implementation Plan

- [x] 1. パフォーマンス計測基盤の実装

  - `src/performance_monitor.py`を作成し、PerformanceMonitor クラスを実装
  - タイマー機能（start_timer/end_timer）を実装
  - FPS カウンター機能を実装
  - パフォーマンスレポート生成機能を実装
  - _Requirements: 1.1, 1.2, 5.1, 5.2_

- [x] 2. キャッシング機構の実装
- [x] 2.1 DetectionCache クラスの実装

  - `src/detection_cache.py`を作成
  - フレームハッシュ計算機能を実装
  - キャッシュエントリの管理（TTL、類似度判定）を実装
  - should_skip_detection/get_cached_detections/update_cache メソッドを実装
  - _Requirements: 2.2, 4.1_

- [x] 2.2 OCRCache クラスの実装

  - `src/ocr_cache.py`を作成
  - バウンディングボックスの近似一致判定機能を実装
  - キャッシュキー生成とキャッシュ管理を実装
  - get_cached_text/update_cache メソッドを実装
  - _Requirements: 4.1, 4.2_

- [x] 3. パフォーマンスモード設定の実装

  - `src/performance_mode.py`を作成
  - PerformanceMode データクラスを定義
  - 3 つのプリセット（fast/balanced/accurate）を定義
  - モード切り替え機能を実装
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 4. パイプラインプロセッサの実装
- [x] 4.1 PipelineProcessor クラスの基本構造

  - `src/pipeline_processor.py`を作成
  - クラスの初期化（キュー、スレッド、キャッシュの初期化）を実装
  - start/stop メソッドの基本構造を実装
  - _Requirements: 2.3, 3.3_

- [x] 4.2 キャプチャスレッドの実装

  - \_capture_loop メソッドを実装
  - ウィンドウキャプチャを独立スレッドで実行
  - フレームキューへの非ブロッキング追加を実装
  - パフォーマンス計測を統合
  - _Requirements: 2.1, 3.1, 5.2_

- [x] 4.3 検出スレッドの実装

  - \_detection_loop メソッドを実装
  - フレームキューからの取得と物体検出を実行
  - 検出キャッシュの統合（キャッシュヒット時はスキップ）
  - 検出結果キューへの送信を実装
  - パフォーマンス計測を統合
  - _Requirements: 2.2, 3.1, 5.2_

- [x] 4.4 並列 OCR 処理の実装

  - \_process_ocr_parallel メソッドを実装
  - ThreadPoolExecutor を使用した並列 OCR 処理を実装
  - OCR キャッシュの統合（キャッシュヒット時は再利用）
  - 優先度付き処理（Y 座標順）を実装
  - データマネージャーへの結果送信を実装
  - パフォーマンス計測を統合
  - _Requirements: 3.2, 4.1, 4.3_

- [x] 4.5 表示キューの統合

  - 検出結果を描画したフレームを表示キューに送信
  - フレームスキップ戦略を実装（古いフレームを破棄）
  - _Requirements: 2.3_

- [x] 5. GUI 統合
- [x] 5.1 パフォーマンスモード選択 UI の追加

  - `src/gui_app.py`にパフォーマンスモード選択コンボボックスを追加
  - モード変更時の動作を実装
  - _Requirements: 6.1_

- [x] 5.2 PipelineProcessor の統合

  - RealtimeOCRGUI クラスに PipelineProcessor を統合
  - \_start_processing/\_stop_processing メソッドを更新
  - 既存の処理ループを新しいパイプラインに置き換え
  - _Requirements: 2.3, 3.1, 3.2_

- [x] 5.3 パフォーマンス統計表示の追加

  - FPS 表示を更新（リアルタイム計測値を使用）
  - 各処理ステップの平均実行時間を表示
  - キャッシュヒット率を表示
  - _Requirements: 5.1, 5.2_

- [x] 5.4 表示キューからのフレーム取得

  - \_process_queues メソッドを更新
  - 表示キューから最新フレームを取得して表示
  - _Requirements: 2.3_

- [x] 6. エラーハンドリングとクリーンアップ

  - 各スレッドでの例外処理を実装
  - stop()メソッドでの適切なリソースクリーンアップを実装
  - キュータイムアウトとデッドロック防止を実装
  - キャッシュエラー時のフォールバック処理を実装
  - _Requirements: 1.3_

- [x] 7. 設定ファイルへのパフォーマンス設定追加

  - `src/config.py`の AppConfig にパフォーマンス関連設定を追加
  - デフォルト値を設定
  - _Requirements: 6.1_

- [x] 8. ドキュメント更新

  - README.md にパフォーマンス改善の説明を追加
  - パフォーマンスモードの使い方を記載
  - 期待される FPS と推奨設定を記載
  - _Requirements: 5.3_

- [ ] 9. 動作確認とパフォーマンス検証

  - 実際の iPhone ミラーリング画面で動作確認
  - FPS が 5FPS 以上達成されているか検証
  - 各パフォーマンスモードでの動作確認
  - キャッシュヒット率の確認
  - _Requirements: 5.1, 5.3_

- [ ] 10. 最適化とチューニング
  - ボトルネックが残っている場合、追加の最適化を実施
  - キャッシュ TTL やスレッド数などのパラメータ調整
  - メモリ使用量の確認と最適化
  - _Requirements: 1.1, 1.2, 1.3_
