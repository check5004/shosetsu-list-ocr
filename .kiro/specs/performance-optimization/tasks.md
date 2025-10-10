# Implementation Plan

- [ ] 1. パフォーマンス計測基盤の実装
  - `src/performance_monitor.py`を作成し、PerformanceMonitorクラスを実装
  - タイマー機能（start_timer/end_timer）を実装
  - FPSカウンター機能を実装
  - パフォーマンスレポート生成機能を実装
  - _Requirements: 1.1, 1.2, 5.1, 5.2_

- [ ] 2. キャッシング機構の実装
- [ ] 2.1 DetectionCacheクラスの実装
  - `src/detection_cache.py`を作成
  - フレームハッシュ計算機能を実装
  - キャッシュエントリの管理（TTL、類似度判定）を実装
  - should_skip_detection/get_cached_detections/update_cacheメソッドを実装
  - _Requirements: 2.2, 4.1_

- [ ] 2.2 OCRCacheクラスの実装
  - `src/ocr_cache.py`を作成
  - バウンディングボックスの近似一致判定機能を実装
  - キャッシュキー生成とキャッシュ管理を実装
  - get_cached_text/update_cacheメソッドを実装
  - _Requirements: 4.1, 4.2_

- [ ] 3. パフォーマンスモード設定の実装
  - `src/performance_mode.py`を作成
  - PerformanceModeデータクラスを定義
  - 3つのプリセット（fast/balanced/accurate）を定義
  - モード切り替え機能を実装
  - _Requirements: 6.1, 6.2, 6.3_

- [ ] 4. パイプラインプロセッサの実装
- [ ] 4.1 PipelineProcessorクラスの基本構造
  - `src/pipeline_processor.py`を作成
  - クラスの初期化（キュー、スレッド、キャッシュの初期化）を実装
  - start/stopメソッドの基本構造を実装
  - _Requirements: 2.3, 3.3_

- [ ] 4.2 キャプチャスレッドの実装
  - _capture_loopメソッドを実装
  - ウィンドウキャプチャを独立スレッドで実行
  - フレームキューへの非ブロッキング追加を実装
  - パフォーマンス計測を統合
  - _Requirements: 2.1, 3.1, 5.2_

- [ ] 4.3 検出スレッドの実装
  - _detection_loopメソッドを実装
  - フレームキューからの取得と物体検出を実行
  - 検出キャッシュの統合（キャッシュヒット時はスキップ）
  - 検出結果キューへの送信を実装
  - パフォーマンス計測を統合
  - _Requirements: 2.2, 3.1, 5.2_

- [ ] 4.4 並列OCR処理の実装
  - _process_ocr_parallelメソッドを実装
  - ThreadPoolExecutorを使用した並列OCR処理を実装
  - OCRキャッシュの統合（キャッシュヒット時は再利用）
  - 優先度付き処理（Y座標順）を実装
  - データマネージャーへの結果送信を実装
  - パフォーマンス計測を統合
  - _Requirements: 3.2, 4.1, 4.3_

- [ ] 4.5 表示キューの統合
  - 検出結果を描画したフレームを表示キューに送信
  - フレームスキップ戦略を実装（古いフレームを破棄）
  - _Requirements: 2.3_

- [ ] 5. GUI統合
- [ ] 5.1 パフォーマンスモード選択UIの追加
  - `src/gui_app.py`にパフォーマンスモード選択コンボボックスを追加
  - モード変更時の動作を実装
  - _Requirements: 6.1_

- [ ] 5.2 PipelineProcessorの統合
  - RealtimeOCRGUIクラスにPipelineProcessorを統合
  - _start_processing/_stop_processingメソッドを更新
  - 既存の処理ループを新しいパイプラインに置き換え
  - _Requirements: 2.3, 3.1, 3.2_

- [ ] 5.3 パフォーマンス統計表示の追加
  - FPS表示を更新（リアルタイム計測値を使用）
  - 各処理ステップの平均実行時間を表示
  - キャッシュヒット率を表示
  - _Requirements: 5.1, 5.2_

- [ ] 5.4 表示キューからのフレーム取得
  - _process_queuesメソッドを更新
  - 表示キューから最新フレームを取得して表示
  - _Requirements: 2.3_

- [ ] 6. エラーハンドリングとクリーンアップ
  - 各スレッドでの例外処理を実装
  - stop()メソッドでの適切なリソースクリーンアップを実装
  - キュータイムアウトとデッドロック防止を実装
  - キャッシュエラー時のフォールバック処理を実装
  - _Requirements: 1.3_

- [ ] 7. 設定ファイルへのパフォーマンス設定追加
  - `src/config.py`のAppConfigにパフォーマンス関連設定を追加
  - デフォルト値を設定
  - _Requirements: 6.1_

- [ ] 8. ドキュメント更新
  - README.mdにパフォーマンス改善の説明を追加
  - パフォーマンスモードの使い方を記載
  - 期待されるFPSと推奨設定を記載
  - _Requirements: 5.3_

- [ ] 9. 動作確認とパフォーマンス検証
  - 実際のiPhoneミラーリング画面で動作確認
  - FPSが5FPS以上達成されているか検証
  - 各パフォーマンスモードでの動作確認
  - キャッシュヒット率の確認
  - _Requirements: 5.1, 5.3_

- [ ] 10. 最適化とチューニング
  - ボトルネックが残っている場合、追加の最適化を実施
  - キャッシュTTLやスレッド数などのパラメータ調整
  - メモリ使用量の確認と最適化
  - _Requirements: 1.1, 1.2, 1.3_
