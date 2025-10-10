# 開発者ガイド

このドキュメントは、リアルタイムOCRアプリケーションの開発に参加する開発者向けのガイドです。

## 開発環境のセットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd shosetsu-list-ocr
```

### 2. 仮想環境の作成

**重要**: このプロジェクトでは必ず仮想環境を使用してください。システムのPython環境を汚染しないようにするためです。

```bash
# 仮想環境を作成
python3 -m venv venv

# 仮想環境を有効化
source venv/bin/activate

# 仮想環境が有効化されると、プロンプトに (venv) が表示されます
(venv) $
```

### 3. 依存関係のインストール

```bash
# pipをアップグレード
pip install --upgrade pip

# プロジェクトの依存関係をインストール
pip install -r requirements.txt
```

### 4. 開発ツールのインストール（オプション）

```bash
# コードフォーマッター
pip install black isort

# 型チェッカー
pip install mypy

# リンター
pip install flake8 pylint
```

## 仮想環境の管理

### 仮想環境の有効化

開発作業を開始する際は、必ず仮想環境を有効化してください:

```bash
source venv/bin/activate
```

### 仮想環境の無効化

作業が終わったら、仮想環境を無効化できます:

```bash
deactivate
```

### 仮想環境を使用せずにコマンドを実行

仮想環境を有効化せずに、直接コマンドを実行することもできます:

```bash
# Pythonスクリプトを実行
./venv/bin/python src/realtime_ocr_app.py

# pytestを実行
./venv/bin/pytest tests/ -v

# pipでパッケージをインストール
./venv/bin/pip install <package-name>
```

## テストの実行

### 全テストの実行

```bash
# 仮想環境を有効化している場合
pytest tests/ -v

# または、直接実行
./venv/bin/pytest tests/ -v
```

### 特定のテストファイルを実行

```bash
pytest tests/test_object_detector.py -v
```

### 特定のテストクラスを実行

```bash
pytest tests/test_object_detector.py::TestObjectDetector -v
```

### 特定のテストメソッドを実行

```bash
pytest tests/test_object_detector.py::TestObjectDetector::test_sort_by_y_coordinate_ascending -v
```

### カバレッジレポート付きで実行

```bash
# カバレッジをインストール（初回のみ）
pip install pytest-cov

# カバレッジレポートを生成
pytest tests/ --cov=src --cov-report=html

# HTMLレポートを開く
open htmlcov/index.html
```

## コードスタイル

### フォーマット

このプロジェクトでは、Pythonの標準的なコーディング規約に従います:

```bash
# blackでコードをフォーマット
black src/ tests/

# isortでimportをソート
isort src/ tests/
```

### 型ヒント

全ての関数には型ヒントを追加してください:

```python
def process_image(image: np.ndarray, threshold: float = 0.6) -> List[DetectionResult]:
    """画像を処理して検出結果を返す"""
    pass
```

### 型チェック

```bash
mypy src/
```

### リンター

```bash
# flake8でコードをチェック
flake8 src/ tests/

# pylintでコードをチェック
pylint src/
```

## プロジェクト構造

```
.
├── .kiro/                  # Kiro IDE設定
│   ├── specs/             # 機能仕様書
│   └── steering/          # ステアリングルール
├── src/                    # ソースコード
│   ├── realtime_ocr_app.py # メインアプリケーション
│   ├── window_capture.py   # ウィンドウキャプチャ
│   ├── object_detector.py  # 物体検出
│   ├── ocr_processor.py    # OCR処理
│   ├── data_manager.py     # データ管理
│   ├── visualizer.py       # 可視化
│   ├── error_handler.py    # エラーハンドリング
│   └── config.py           # 設定管理
├── tests/                  # テストコード
│   ├── test_window_capture.py
│   ├── test_object_detector.py
│   └── README_test_object_detector.md
├── models/                 # YOLOv8モデル
│   └── best.pt
├── output/                 # 出力ファイル
├── venv/                   # 仮想環境（Gitには含まれない）
├── .gitignore             # Git除外設定
├── requirements.txt        # Python依存関係
├── README.md              # ユーザー向けドキュメント
└── DEVELOPMENT.md         # このファイル
```

## Git ワークフロー

### ブランチ戦略

- `main`: 安定版
- `develop`: 開発版
- `feature/*`: 新機能開発
- `bugfix/*`: バグ修正
- `test/*`: テスト追加

### コミットメッセージ

明確で説明的なコミットメッセージを書いてください:

```bash
# 良い例
git commit -m "feat: YOLOv8検出結果のソート機能を追加"
git commit -m "fix: 信頼度フィルタリングのバグを修正"
git commit -m "test: ObjectDetectorのテストケースを追加"
git commit -m "docs: READMEに仮想環境のセットアップ手順を追加"

# 悪い例
git commit -m "update"
git commit -m "fix bug"
```

### プルリクエスト

1. 機能ブランチを作成
2. 変更を実装
3. テストを追加・実行
4. コードをフォーマット
5. プルリクエストを作成
6. レビューを受ける

## トラブルシューティング

### 仮想環境が見つからない

```bash
# 仮想環境を再作成
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 依存関係のバージョン競合

```bash
# 依存関係を再インストール
pip uninstall -y -r <(pip freeze)
pip install -r requirements.txt
```

### テストが失敗する

```bash
# 依存関係が正しくインストールされているか確認
pip list

# 仮想環境を再作成
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# テストを再実行
pytest tests/ -v
```

## ベストプラクティス

### 1. 常に仮想環境を使用

システムのPython環境を汚染しないため、必ず仮想環境を使用してください。

### 2. 依存関係を最新に保つ

新しいパッケージをインストールした場合は、`requirements.txt`を更新してください:

```bash
pip freeze > requirements.txt
```

### 3. テストを書く

新しい機能を追加する際は、必ずテストを書いてください。

### 4. コードレビュー

プルリクエストを作成する前に、自分でコードをレビューしてください。

### 5. ドキュメントを更新

コードの変更に合わせて、ドキュメントも更新してください。

## リソース

- [Python仮想環境ガイド](https://docs.python.org/ja/3/tutorial/venv.html)
- [pytest ドキュメント](https://docs.pytest.org/)
- [YOLOv8 ドキュメント](https://docs.ultralytics.com/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)

## サポート

質問や問題がある場合は、Issueを作成してください。
