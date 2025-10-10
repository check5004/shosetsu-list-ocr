# リアルタイムOCRアプリケーション

macOS上で動作するリアルタイムOCRシステムです。指定されたウィンドウ（iPhoneシミュレータやミラーリングアプリ）をキャプチャし、YOLOv8で小説リスト項目を検出、Tesseract OCRで日本語テキストを抽出し、CSV形式で保存します。

## 機能概要

- **リアルタイムウィンドウキャプチャ**: 指定したウィンドウを継続的にキャプチャ
- **YOLOv8物体検出**: 学習済みモデルでリスト項目を検出
- **日本語OCR**: Tesseract OCRで日本語テキストを抽出
- **重複排除**: 自動的に重複データを除外
- **CSV出力**: 抽出データをCSV形式で保存
- **リアルタイムプレビュー**: 検出結果を視覚的に確認

## システム要件

- **OS**: macOS 11.0 (Big Sur) 以降
- **CPU**: Apple Silicon (M1/M2/M3) または Intel
- **Python**: 3.9 以降
- **Tesseract OCR**: 4.0 以降

## インストール手順

### 1. Homebrewのインストール（未インストールの場合）

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Tesseract OCRのインストール

```bash
brew install tesseract tesseract-lang
```

日本語言語データが含まれていることを確認:

```bash
tesseract --list-langs
```

出力に`jpn`が含まれていればOKです。

### 3. Python仮想環境の作成（推奨）

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. 依存関係のインストール

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. YOLOv8モデルの配置

学習済みYOLOv8モデル（`best.pt`）を以下のパスに配置してください:

```
models/best.pt
```

または、設定ファイルでモデルパスを指定できます。

## macOS権限設定

このアプリケーションは画面をキャプチャするため、macOSの**画面収録権限**が必要です。

### 権限の付与手順

1. **システム環境設定**を開く
2. **セキュリティとプライバシー**を選択
3. **プライバシー**タブをクリック
4. 左側のリストから**画面収録**を選択
5. 鍵アイコンをクリックして変更を許可
6. **ターミナル**（またはPythonを実行するアプリ）にチェックを入れる
7. アプリケーションを再起動

### 権限が付与されていない場合

初回実行時に権限を求めるダイアログが表示されます。権限を付与後、アプリケーションを再起動してください。

## 使用方法

### 基本的な使い方

```bash
# 仮想環境をアクティベート（作成した場合）
source venv/bin/activate

# アプリケーションを実行
python src/realtime_ocr_app.py
```

### 設定のカスタマイズ

`src/config.py`で以下の設定を変更できます:

- **model_path**: YOLOv8モデルファイルのパス
- **target_window_title**: キャプチャ対象のウィンドウタイトル（部分一致）
- **confidence_threshold**: 検出の信頼度しきい値（0.0-1.0）
- **output_csv**: 出力CSVファイル名
- **ocr_lang**: OCR言語（デフォルト: `jpn`）

### 終了方法

- **'q'キー**: プレビューウィンドウで'q'キーを押すと終了
- **Ctrl+C**: ターミナルでCtrl+Cを押すと安全に終了

終了時に抽出されたデータが自動的にCSVファイルに保存されます。

## プロジェクト構造

```
.
├── src/                    # ソースコード
│   ├── realtime_ocr_app.py # メインアプリケーション
│   ├── window_capture.py   # ウィンドウキャプチャモジュール
│   ├── object_detector.py  # YOLOv8物体検出モジュール
│   ├── ocr_processor.py    # OCRモジュール
│   ├── data_manager.py     # データ管理モジュール
│   ├── visualizer.py       # 可視化モジュール
│   ├── error_handler.py    # エラーハンドリングモジュール
│   └── config.py           # 設定管理
├── config/                 # 設定ファイル（オプション）
├── models/                 # YOLOv8モデルファイル
│   └── best.pt            # 学習済みモデル
├── output/                 # 出力ファイル
│   └── book_data_realtime.csv
├── requirements.txt        # Python依存関係
└── README.md              # このファイル
```

## トラブルシューティング

### ウィンドウが見つからない

**エラー**: `Error: Window not found`

**解決策**:
1. ターゲットウィンドウが開いていることを確認
2. ウィンドウタイトルが正しいか確認（部分一致で検索されます）
3. 利用可能なウィンドウリストを確認して、正しいタイトルを指定

### Tesseractが見つからない

**エラー**: `TesseractNotFoundError`

**解決策**:
```bash
brew install tesseract tesseract-lang
```

インストール後、Tesseractのパスを確認:
```bash
which tesseract
```

### 画面収録権限エラー

**エラー**: 画面がキャプチャできない

**解決策**:
1. システム環境設定 > セキュリティとプライバシー > プライバシー > 画面収録
2. ターミナル（またはPythonアプリ）に権限を付与
3. アプリケーションを再起動

### モデルファイルが見つからない

**エラー**: `Model file not found`

**解決策**:
1. `best.pt`ファイルが`models/`ディレクトリに存在することを確認
2. または、`src/config.py`で正しいパスを指定

### OCR精度が低い

**対策**:
1. ウィンドウのサイズを大きくする
2. 画面の解像度を上げる
3. `ocr_margin`パラメータを調整（デフォルト: 5ピクセル）
4. 画像前処理を有効化（`OCRProcessor.preprocess_image()`）

### パフォーマンスが遅い

**対策**:
1. `confidence_threshold`を上げて検出数を減らす
2. Apple Silicon環境でMPS（Metal Performance Shaders）が有効か確認
3. 不要なアプリケーションを閉じてリソースを確保

## 開発情報

### テストの実行

```bash
pytest tests/
```

### コードフォーマット

```bash
black src/
```

### 型チェック

```bash
mypy src/
```

## ライセンス

このプロジェクトは個人使用を目的としています。

## サポート

問題が発生した場合は、以下を確認してください:
1. すべての依存関係が正しくインストールされているか
2. macOSの画面収録権限が付与されているか
3. YOLOv8モデルファイルが正しい場所に配置されているか
4. Tesseract OCRが正しくインストールされているか
