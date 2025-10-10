# Requirements Document

## Introduction

このドキュメントは、macOS上で動作するリアルタイムOCRアプリケーションの要件を定義します。本アプリケーションは、指定されたウィンドウ（iPhoneシミュレータやミラーリングされたアプリ）をリアルタイムでキャプチャし、YOLOv8による物体検出とTesseract OCRを用いて読書記録データを抽出し、CSV形式で保存する機能を提供します。

対象環境: macOS (Apple Silicon)

### 段階的アプローチ

**フェーズ1（現在）:** 小説1冊単位での検出
- アノテーションクラス: `list-item`（1クラスのみ）
- 検出対象: 小説1冊分の情報全体（タイトル、最終読書日時、ページ数、最新話サブタイトルなどを含む矩形領域）
- OCR: バウンディングボックス全体のテキストを一括抽出

**フェーズ2（将来）:** 項目内の細分化
- 各list-item内の要素（タイトル、日時、ページ数など）を個別に検出
- 入れ子構造のアノテーション対応の検証が必要
- 実装可否により代替アプローチを検討

## Requirements

### Requirement 1: ウィンドウキャプチャ機能

**User Story:** As a ユーザー, I want macOS上の特定のウィンドウをリアルタイムでキャプチャしたい, so that iPhoneアプリの画面から継続的にデータを抽出できる

#### Acceptance Criteria

1. WHEN ユーザーがウィンドウタイトルを指定する THEN システム SHALL 該当するウィンドウを検索して特定する
2. WHEN 対象ウィンドウが見つからない THEN システム SHALL エラーメッセージと利用可能なウィンドウのリストを表示する
3. WHEN ウィンドウが特定される THEN システム SHALL そのウィンドウの画面をリアルタイムでキャプチャし続ける
4. WHEN ウィンドウの位置やサイズが変更される THEN システム SHALL 自動的に追従してキャプチャを継続する
5. IF macOS Apple Silicon環境である THEN システム SHALL ネイティブに動作する

### Requirement 2: YOLOv8による物体検出

**User Story:** As a ユーザー, I want 学習済みYOLOv8モデルを使用してリスト項目を検出したい, so that OCR対象の領域を正確に特定できる

#### Acceptance Criteria

1. WHEN システムが起動する THEN システム SHALL 指定されたYOLOv8モデル（best.pt）をロードする
2. WHEN モデルファイルが存在しない THEN システム SHALL エラーメッセージを表示して終了する
3. WHEN キャプチャされた画像フレームを受け取る THEN システム SHALL YOLOv8モデルで物体検出を実行する
4. WHEN 検出結果の信頼度がしきい値以上である THEN システム SHALL そのバウンディングボックスを有効な検出として扱う
5. WHEN 複数の項目が検出される THEN システム SHALL Y座標（上から下）の順にソートして処理する
6. WHEN 検出クラスが`list-item`である THEN システム SHALL 小説1冊分の情報全体を含む矩形領域として扱う（フェーズ1）
7. IF 将来的に細分化されたクラス（タイトル、日時など）が追加される THEN システム SHALL 複数クラスの検出に対応できる拡張性を持つ

### Requirement 3: リアルタイム描画とプレビュー

**User Story:** As a ユーザー, I want 検出結果をリアルタイムで視覚的に確認したい, so that システムが正しく動作しているか確認できる

#### Acceptance Criteria

1. WHEN 物体検出が実行される THEN システム SHALL 検出されたバウンディングボックスを画像上に緑色の矩形で描画する
2. WHEN 描画が完了する THEN システム SHALL 結果を別ウィンドウに表示する
3. WHEN フレームが更新される THEN システム SHALL 表示ウィンドウをリアルタイムで更新する
4. WHEN ユーザーが'q'キーを押す THEN システム SHALL プレビューウィンドウを閉じて処理を終了する

### Requirement 4: Tesseract OCRによるテキスト抽出

**User Story:** As a ユーザー, I want 検出された領域から日本語テキストを抽出したい, so that 読書記録データをテキスト化できる

#### Acceptance Criteria

1. WHEN バウンディングボックスが検出される THEN システム SHALL その領域を画像から切り出す
2. WHEN 領域を切り出す THEN システム SHALL 5ピクセルのマージンを追加して精度を向上させる
3. WHEN 切り出された画像を処理する THEN システム SHALL Tesseract OCRで日本語テキストを抽出する
4. WHEN テキストが抽出される THEN システム SHALL 空白文字を正規化してクリーンアップする
5. WHEN 抽出されたテキストが2文字以下である THEN システム SHALL そのテキストを無視する
6. IF OCR処理でエラーが発生する THEN システム SHALL エラーをキャッチして処理を継続する
7. WHEN フェーズ1で`list-item`全体を処理する THEN システム SHALL 小説1冊分の全情報（タイトル、日時、ページ数など）を含む複数行テキストとして抽出する

### Requirement 5: 重複排除とデータ管理

**User Story:** As a ユーザー, I want 抽出されたテキストの重複を自動的に排除したい, so that 同じデータが複数回保存されることを防げる

#### Acceptance Criteria

1. WHEN テキストが抽出される THEN システム SHALL 既に抽出済みかどうかをチェックする
2. WHEN テキストが新規である THEN システム SHALL それをメモリ内のセットに追加する
3. WHEN 新規テキストが追加される THEN システム SHALL ターミナルに「新規データ検出」メッセージを表示する
4. WHEN テキストが重複している THEN システム SHALL それを無視して次の処理に進む

### Requirement 6: CSV出力機能

**User Story:** As a ユーザー, I want 抽出されたデータをCSVファイルとして保存したい, so that 後で分析や移行作業に使用できる

#### Acceptance Criteria

1. WHEN ユーザーが'q'キーで終了する THEN システム SHALL 抽出されたすべてのテキストをCSVファイルに保存する
2. WHEN CSVファイルを作成する THEN システム SHALL "extracted_text"という列名を使用する
3. WHEN データが1件以上ある THEN システム SHALL ファイル名と件数を表示する
4. WHEN データが0件である THEN システム SHALL 「データは抽出されませんでした」というメッセージを表示する
5. IF 出力ファイル名が設定で指定されている THEN システム SHALL その名前でファイルを保存する

### Requirement 7: 設定とカスタマイズ

**User Story:** As a ユーザー, I want アプリケーションの動作を設定ファイルやパラメータでカスタマイズしたい, so that 異なる環境や用途に対応できる

#### Acceptance Criteria

1. WHEN システムが起動する THEN システム SHALL 設定ファイルまたはコード内の定数から設定を読み込む
2. WHEN 設定項目が定義される THEN システム SHALL 以下の項目を含む: モデルパス、ターゲットウィンドウタイトル、出力CSVファイル名、信頼度しきい値
3. WHEN ユーザーが設定を変更する THEN システム SHALL 次回起動時にその設定を使用する
4. IF 設定値が不正である THEN システム SHALL デフォルト値を使用するか、エラーメッセージを表示する

### Requirement 8: エラーハンドリングとロバスト性

**User Story:** As a ユーザー, I want システムがエラーに対して適切に対処する, so that 予期しない状況でもクラッシュせずに動作し続ける

#### Acceptance Criteria

1. WHEN モデルのロードに失敗する THEN システム SHALL エラーメッセージを表示して終了する
2. WHEN ウィンドウの取得に失敗する THEN システム SHALL エラーメッセージと利用可能なウィンドウリストを表示して終了する
3. WHEN OCR処理でエラーが発生する THEN システム SHALL エラーをキャッチして次のフレームの処理を継続する
4. WHEN ユーザーが強制終了する（Ctrl+C） THEN システム SHALL 安全にクリーンアップしてCSVファイルを保存する
5. WHEN 予期しないエラーが発生する THEN システム SHALL エラー内容をログに出力する

### Requirement 9: パフォーマンスと最適化

**User Story:** As a ユーザー, I want アプリケーションがスムーズに動作する, so that リアルタイム処理が実用的な速度で実行される

#### Acceptance Criteria

1. WHEN リアルタイム処理を実行する THEN システム SHALL Apple Silicon環境で最適化されたライブラリを使用する
2. WHEN フレームレートが低下する THEN システム SHALL 処理を継続し、可能な限りフレームをスキップしない
3. WHEN OCR処理が重い THEN システム SHALL 検出された領域のみを処理することで負荷を軽減する
4. IF ユーザーがパフォーマンス問題を報告する THEN システム SHALL OCR処理を無効化するオプションを提供する

### Requirement 10: 依存関係とインストール

**User Story:** As a ユーザー, I want 必要な依存関係を簡単にインストールしたい, so that セットアップ作業を最小限にできる

#### Acceptance Criteria

1. WHEN ユーザーがセットアップを開始する THEN システム SHALL requirements.txtファイルを提供する
2. WHEN requirements.txtが実行される THEN システム SHALL 以下のライブラリをインストールする: ultralytics, opencv-python, pytesseract, pandas, mss, pygetwindow
3. WHEN Tesseract OCRが必要である THEN ドキュメント SHALL Homebrewを使用したインストール手順を提供する
4. WHEN Python仮想環境が推奨される THEN ドキュメント SHALL venvの作成とアクティベート手順を提供する
5. IF Apple Silicon環境である THEN システム SHALL ネイティブにコンパイルされたライブラリを使用する
