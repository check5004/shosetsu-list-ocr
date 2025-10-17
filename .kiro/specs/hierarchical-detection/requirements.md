# Requirements Document

## Introduction

このドキュメントは、既存のリアルタイムOCRアプリケーションに対する機能拡張の要件を定義します。現在、本棚のリスト項目全体（list-item）を1つのラベルとして検出するモデルは完成しており、良好な精度で動作しています。

本機能拡張では、list-item内部に含まれる詳細情報（タイトル、読書進捗、最終読書日時、サイト名）を個別に検出し、構造化されたデータとして出力する機能を実装します。最終目標は、約1700作品のデータを別アプリへ移行することです。

### 技術的アプローチ

**モデル構造:**
- 5つのラベル（list-item, title, progress, last_read_date, site_name）をすべて同階層として学習
- モデル自体には階層構造を持たせない

**親子関係の判定:**
- モデルの推論後、プログラム側で座標計算により親子関係を判定
- 子要素（title等）が、どのlist-item（親）のbounding box内に含まれるかを判定
- list-item同士の検出範囲が重複する場合は、IoU（Intersection over Union）を計算し、最も重なりが大きいlist-itemを親として紐付け

**学習データの考慮事項:**
- 提供する学習データはスクリーンショット9枚と非常に少量
- 過学習を防ぐため、データ拡張（Data Augmentation）を積極的に活用
- 明るさ・コントラスト変更、ランダムクロップ、ノイズ追加、Mosaic拡張などを適用
- 未知の小説に対してもレイアウト情報を元に柔軟に判定できる汎用性の高いモデルを構築

## Requirements

### Requirement 1: 多クラス物体検出モデルの学習

**User Story:** As a 開発者, I want list-item、title、progress、last_read_date、site_nameの5つのラベルを同階層で検出できるYOLOv8モデルを学習したい, so that 各要素を個別に認識できる

#### Acceptance Criteria

1. WHEN 学習データセット（temp/shosetsu-list-item_dataset_v2）を準備する THEN システム SHALL 5つのクラスラベルを定義する
2. WHEN アノテーションデータを作成する THEN システム SHALL YOLO形式（class_id x_center y_center width height）で保存する
3. WHEN モデルを学習する THEN システム SHALL YOLOv8を使用して5クラスの検出モデルを訓練する
4. WHEN 学習を実行する THEN システム SHALL 既存の初期バージョンで使用した有効な設定（エポック数、バッチサイズ等）を再利用する
5. WHEN 学習データが少量である THEN システム SHALL データ拡張を積極的に適用する（明るさ、コントラスト、ランダムクロップ、ノイズ、Mosaic等）
6. WHEN モデルが学習される THEN システム SHALL 過学習を防ぎ、未知のデータに対する汎化性能を確保する
7. WHEN 学習が完了する THEN システム SHALL 学習済みモデルファイル（best.pt）を保存する

### Requirement 2: 階層的検出ロジックの実装

**User Story:** As a 開発者, I want 検出された子要素（title等）を適切な親要素（list-item）に紐付けたい, so that 構造化されたデータを生成できる

#### Acceptance Criteria

1. WHEN モデルが推論を実行する THEN システム SHALL 5つのクラスすべての検出結果を取得する
2. WHEN 検出結果を処理する THEN システム SHALL list-itemクラスの検出結果を親候補として抽出する
3. WHEN 子要素（title、progress、last_read_date、site_name）を処理する THEN システム SHALL 各子要素のbounding boxが、どのlist-itemのbounding box内に含まれるかを座標計算で判定する
4. WHEN 子要素が複数のlist-itemに重複して含まれる THEN システム SHALL IoU（Intersection over Union）を計算する
5. WHEN IoUを計算する THEN システム SHALL 最も重なりが大きいlist-itemを親として紐付ける
6. WHEN 子要素がどのlist-itemにも含まれない THEN システム SHALL その子要素を孤立要素として記録する（エラーログまたは警告）
7. WHEN 親子関係が確立される THEN システム SHALL list-item単位でデータを構造化する

### Requirement 3: IoU計算ロジックの実装

**User Story:** As a 開発者, I want 2つのbounding box間のIoUを正確に計算したい, so that 重複する検出結果を適切に処理できる

#### Acceptance Criteria

1. WHEN 2つのbounding boxが与えられる THEN システム SHALL 交差領域（Intersection）の面積を計算する
2. WHEN 交差領域を計算する THEN システム SHALL 2つのboxの重なり部分の座標を特定する
3. WHEN 和領域（Union）を計算する THEN システム SHALL 2つのboxを合わせた全体の面積を計算する（重複部分は1回のみカウント）
4. WHEN IoUを計算する THEN システム SHALL Intersection / Union の値を返す（0.0〜1.0の範囲）
5. WHEN 2つのboxが全く重ならない THEN システム SHALL IoU = 0.0 を返す
6. WHEN 2つのboxが完全に一致する THEN システム SHALL IoU = 1.0 を返す

### Requirement 4: 構造化データの出力

**User Story:** As a ユーザー, I want 抽出されたデータを構造化されたCSV形式で保存したい, so that 各list-itemの詳細情報を個別に確認できる

#### Acceptance Criteria

1. WHEN データを出力する THEN システム SHALL 以下の列を持つCSVファイルを生成する: list_item_id, title, progress, last_read_date, site_name, image_path, error_status
2. WHEN list-item単位でデータを出力する THEN システム SHALL 各list-itemを1行として記録する
3. WHEN 必須子要素（title、last_read_date、site_name）が検出されない THEN システム SHALL error_status列にエラー内容を記録する（例: "missing_title", "missing_last_read_date"）
4. WHEN すべての必須子要素が検出される THEN システム SHALL error_status列を空欄または"OK"として記録する
5. WHEN オプション子要素（progress）が検出されない THEN システム SHALL その列を空欄として記録し、エラーとしては扱わない
6. WHEN 複数の同じクラスの子要素が検出される THEN システム SHALL 最も信頼度の高い検出結果を採用する
7. WHEN CSVファイルを保存する THEN システム SHALL UTF-8エンコーディングを使用する
8. WHEN データ出力が完了する THEN システム SHALL 出力ファイル名と件数をターミナルに表示する
9. WHEN エラーのあるデータが存在する THEN システム SHALL エラー件数と正常件数を個別に表示する

### Requirement 5: list-item領域の画像切り出しと保存

**User Story:** As a ユーザー, I want 検出された各list-itemの領域を画像ファイルとして保存したい, so that 抽出失敗時の原因分析や手動補完、将来的なモデルの再学習データとして活用できる

#### Acceptance Criteria

1. WHEN OCR処理を開始する THEN システム SHALL 開始時のタイムスタンプを使用してセッション専用フォルダを作成する（例: output/sessions/20251016_143022/）
2. WHEN list-itemが検出される THEN システム SHALL そのbounding box領域を元画像から切り出す
3. WHEN 画像を切り出す THEN システム SHALL 適切なマージン（例: 5ピクセル）を追加する
4. WHEN 切り出した画像を保存する THEN システム SHALL 一意のファイル名を生成する（例: list_item_001.jpg）
5. WHEN 画像ファイルを保存する THEN システム SHALL セッション専用フォルダ内に保存する
6. WHEN OCR処理を停止する THEN システム SHALL セッションフォルダ全体をZIPファイルに圧縮する（例: output/sessions/20251016_143022.zip）
7. WHEN ZIP圧縮が完了する THEN システム SHALL 元のセッションフォルダを削除する（オプション）
8. WHEN CSVデータを出力する THEN システム SHALL 対応する切り抜き画像ファイルへの相対パスを列として含める（例: sessions/20251016_143022/list_item_001.jpg）
9. WHEN 画像保存に失敗する THEN システム SHALL エラーをログに記録し、処理を継続する
10. WHEN .gitignoreファイルが存在する THEN システム SHALL output/sessions/ディレクトリを除外設定に追加する

### Requirement 6: OCR処理の統合

**User Story:** As a ユーザー, I want 検出された各子要素からテキストを抽出したい, so that 構造化されたテキストデータを取得できる

#### Acceptance Criteria

1. WHEN 子要素（title、progress、last_read_date、site_name）が検出される THEN システム SHALL 各bounding box領域に対してOCR処理を実行する
2. WHEN OCR処理を実行する THEN システム SHALL 既存のOCRProcessorモジュールを再利用する
3. WHEN テキストが抽出される THEN システム SHALL 空白文字を正規化し、クリーンアップする
4. WHEN OCR処理でエラーが発生する THEN システム SHALL エラーをキャッチし、空文字列を返して処理を継続する
5. WHEN 抽出されたテキストが極端に短い（例: 1文字以下） THEN システム SHALL そのテキストを無視するか警告を出す
6. WHEN 各子要素のテキストが抽出される THEN システム SHALL 対応する列（title、progress等）にテキストを格納する

### Requirement 7: 重複排除ロジックの更新（曖昧マッチング対応）

**User Story:** As a ユーザー, I want OCRの誤認識を考慮した曖昧マッチングでlist-item単位の重複を排除したい, so that 同じ小説のデータが複数回保存されることを防ぎつつ、OCRエラーによる誤判定を回避できる

#### Acceptance Criteria

1. WHEN list-itemのデータが抽出される THEN システム SHALL titleテキストをキーとして重複チェックを実行する
2. WHEN titleと既存データを比較する THEN システム SHALL 文字列類似度を計算する（例: レーベンシュタイン距離、difflib.SequenceMatcher等）
3. WHEN 類似度を計算する THEN システム SHALL 類似度しきい値（デフォルト: 0.7〜0.8）を使用して判定する
4. WHEN 類似度がしきい値以上である THEN システム SHALL 重複と判定し、そのlist-itemをスキップする
5. WHEN 類似度がしきい値未満である THEN システム SHALL 新規データとして扱う
6. WHEN 新規データが追加される THEN システム SHALL データをメモリ内のリストに追加する
7. WHEN 新規データが追加される THEN システム SHALL ターミナルに「新規データ検出」メッセージと類似度情報を表示する
8. WHEN 重複が検出される THEN システム SHALL ターミナルに「重複データ検出」メッセージと類似度、既存タイトルを表示する
9. IF titleが空欄である THEN システム SHALL list-item全体のハッシュ値または座標情報を使用して重複チェックを実行する
10. WHEN 類似度しきい値を設定する THEN システム SHALL 設定ファイルまたはGUIから変更可能にする（0.6〜0.9の範囲）

### Requirement 8: 設定とカスタマイズの拡張

**User Story:** As a ユーザー, I want 新機能に関連する設定をカスタマイズしたい, so that 異なる環境や用途に対応できる

#### Acceptance Criteria

1. WHEN システムが起動する THEN システム SHALL 設定ファイルから以下の項目を読み込む: 新モデルパス、IoUしきい値、画像出力ディレクトリ
2. WHEN IoUしきい値が設定される THEN システム SHALL その値を使用して親子関係の判定を行う（デフォルト: 0.5）
3. WHEN 画像出力ディレクトリが設定される THEN システム SHALL そのディレクトリにlist-item画像を保存する
4. WHEN 設定値が不正である THEN システム SHALL デフォルト値を使用するか、エラーメッセージを表示する

### Requirement 9: エラーハンドリングとロバスト性の強化

**User Story:** As a ユーザー, I want 新機能がエラーに対して適切に対処する, so that 予期しない状況でもクラッシュせずに動作し続ける

#### Acceptance Criteria

1. WHEN 子要素が親list-itemに紐付けられない THEN システム SHALL 警告メッセージをログに出力し、処理を継続する
2. WHEN IoU計算でエラーが発生する THEN システム SHALL エラーをキャッチし、デフォルト値（IoU=0）を使用する
3. WHEN 画像切り出しに失敗する THEN システム SHALL エラーをログに記録し、次のlist-itemの処理に進む
4. WHEN OCR処理でエラーが発生する THEN システム SHALL エラーをキャッチし、空文字列を返して処理を継続する
5. WHEN 予期しないエラーが発生する THEN システム SHALL エラー内容をログに出力し、可能な限り処理を継続する

### Requirement 10: 学習プロセスの実装

**User Story:** As a 開発者, I want 新しいデータセットでモデルを学習するスクリプトを実行したい, so that 5クラス検出モデルを生成できる

#### Acceptance Criteria

1. WHEN 学習スクリプトを実行する THEN システム SHALL temp/shosetsu-list-item_dataset_v2のデータセットを使用する
2. WHEN データセットを読み込む THEN システム SHALL data.yamlファイルから設定を読み込む（クラス名、パス等）
3. WHEN 学習を開始する THEN システム SHALL YOLOv8の学習APIを使用する
4. WHEN 学習パラメータを設定する THEN システム SHALL 既存の初期バージョンで有効だった設定を参考にする（エポック数、バッチサイズ、学習率等）
5. WHEN データ拡張を設定する THEN システム SHALL YOLOv8の拡張オプションを有効化する（hsv_h、hsv_s、hsv_v、degrees、translate、scale、mosaic等）
6. WHEN 学習が完了する THEN システム SHALL 学習済みモデルを指定されたパスに保存する（例: models/hierarchical_best.pt）
7. WHEN 学習結果を確認する THEN システム SHALL 精度指標（mAP、precision、recall）を表示する

### Requirement 11: 既存機能との統合

**User Story:** As a ユーザー, I want 新機能を既存のGUIアプリケーションに統合したい, so that シームレスに使用できる

#### Acceptance Criteria

1. WHEN GUIアプリケーションを起動する THEN システム SHALL モデル選択オプションを提供する（既存モデル vs 新モデル）
2. WHEN 新モデルが選択される THEN システム SHALL 階層的検出ロジックを有効化する
3. WHEN 既存モデルが選択される THEN システム SHALL 従来のlist-item全体検出ロジックを使用する
4. WHEN 新モデルで処理を実行する THEN システム SHALL 構造化されたCSV出力を生成する
5. WHEN GUIで統計情報を表示する THEN システム SHALL 各クラスの検出数を個別に表示する（list-item数、title検出数等）
6. WHEN GUIに画像フォルダ管理機能を追加する THEN システム SHALL 「画像フォルダを開く」ボタンを設置する
7. WHEN 「画像フォルダを開く」ボタンが押される THEN システム SHALL 現在のセッションフォルダをFinderで開く
8. WHEN GUI設定パネルを拡張する THEN システム SHALL 画像保存先ディレクトリの設定オプションを追加する（オプション）
9. WHEN 画像保存先が設定される THEN システム SHALL その設定を保存し、次回起動時に使用する

### Requirement 12: ドキュメントとテスト

**User Story:** As a 開発者, I want 新機能のドキュメントとテストを整備したい, so that 保守性と信頼性を確保できる

#### Acceptance Criteria

1. WHEN ドキュメントを作成する THEN システム SHALL 新機能の使用方法をREADMEに追加する
2. WHEN ドキュメントを作成する THEN システム SHALL 学習データセットの準備方法を記載する
3. WHEN ドキュメントを作成する THEN システム SHALL アノテーション形式とクラスラベルの定義を記載する
4. WHEN テストを作成する THEN システム SHALL IoU計算ロジックの単体テストを実装する
5. WHEN テストを作成する THEN システム SHALL 親子関係判定ロジックの単体テストを実装する
6. WHEN 統合テストを実行する THEN システム SHALL サンプル画像を使用して全体フローをテストする
