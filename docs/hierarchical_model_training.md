# 階層的検出モデルの学習手順

このドキュメントでは、5クラス（list-item, title, progress, last_read_date, site_name）を検出する階層的検出モデルの学習手順を説明します。

## 前提条件

- Python 3.9以上がインストールされていること
- 仮想環境（venv）がセットアップされていること
- 必要なパッケージがインストールされていること（ultralytics, torch等）
- アノテーション済みデータセットが準備されていること

## データセット構造

```
temp/shosetsu-list-item_dataset_v2/
├── data.yaml                    # データセット設定ファイル
└── obj_train_data/              # 学習データディレクトリ
    ├── IMG_1307.png             # 画像ファイル
    ├── IMG_1307.txt             # アノテーションファイル（YOLO形式）
    ├── IMG_1308.png
    ├── IMG_1308.txt
    └── ...
```

### data.yaml の設定

```yaml
# Dataset root path (absolute path from workspace root)
path: temp/shosetsu-list-item_dataset_v2

# Training and validation data paths (relative to 'path')
train: obj_train_data
val: obj_train_data  # 少量データのため、学習データを検証にも使用

# Number of classes
nc: 5

# Class names (must match the order in annotation files)
names:
  0: list-item
  1: title
  2: progress
  3: last_read_date
  4: site_name
```

**重要**: `path`は絶対パス（ワークスペースルートからの相対パス）を指定してください。相対パス（`.`）を使用するとエラーになります。

## 学習スクリプト

### 実行方法

```bash
# 仮想環境をアクティベート
source venv/bin/activate

# 学習スクリプトを実行
python scripts/train_hierarchical_model.py
```

または、仮想環境をアクティベートせずに直接実行：

```bash
./venv/bin/python scripts/train_hierarchical_model.py
```

### 学習設定

| パラメータ | 値 | 説明 |
|----------|-----|------|
| モデル | YOLOv8n | 最も軽量なnanoモデル |
| エポック数 | 100 | Early stoppingで自動終了 |
| 画像サイズ | 1280 | 元画像のアスペクト比を考慮 |
| バッチサイズ | 4 | 画像サイズが大きいため小さめに設定 |
| Patience | 20 | 20エポック改善がなければ停止 |
| デバイス | mps/cuda/cpu | 自動検出 |

### データ拡張設定

少量データ（10枚）での過学習を防ぐため、データ拡張を強化しています：

| パラメータ | 値 | 説明 |
|----------|-----|------|
| hsv_h | 0.02 | 色相の変動（やや増加） |
| hsv_s | 0.8 | 彩度の変動（増加） |
| hsv_v | 0.5 | 明度の変動（増加） |
| degrees | 15 | 回転角度（増加） |
| translate | 0.15 | 平行移動（増加） |
| scale | 0.6 | スケール変動（増加） |
| mosaic | 1.0 | モザイク拡張（有効） |
| mixup | 0.0 | Mixup拡張（無効 - 安定性のため） |
| copy_paste | 0.0 | Copy-Paste拡張（無効 - 安定性のため） |
| flipud | 0.0 | 上下反転（無効 - テキストには不適切） |
| fliplr | 0.0 | 左右反転（無効 - テキストには不適切） |

**注意**: MixupとCopy-Pasteは学習中にエラーを引き起こす可能性があるため無効化しています。

## 学習結果

### 出力ファイル

学習完了後、以下のファイルが生成されます：

```
models/
├── hierarchical_best.pt                    # メインで使用するモデル（17.7 MB）
└── hierarchical-detection/                 # 学習結果ディレクトリ
    ├── weights/
    │   ├── best.pt                         # ベストモデル
    │   └── last.pt                         # 最終エポックのモデル
    ├── results.csv                         # 学習曲線データ
    ├── labels.jpg                          # ラベル分布の可視化
    ├── train_batch0.jpg                    # 学習バッチの可視化
    ├── train_batch1.jpg
    └── train_batch2.jpg
```

### 精度指標

典型的な学習結果（10枚の画像、エポック34でEarly stopping）：

| 指標 | 値 | 説明 |
|------|-----|------|
| mAP50 | 86.26% | IoU閾値0.5での平均精度（高精度） |
| mAP50-95 | 42.87% | IoU閾値0.5-0.95での平均精度 |
| Precision | 70.71% | 検出の正確性 |
| Recall | 81.80% | 検出の網羅性（検出漏れが少ない） |

### 結果の確認

```bash
# 学習曲線をCSVで確認
cat models/hierarchical-detection/results.csv

# Pythonで詳細を確認
python -c "
import pandas as pd
df = pd.read_csv('models/hierarchical-detection/results.csv')
print(df[['epoch', 'metrics/mAP50(B)', 'metrics/precision(B)', 'metrics/recall(B)']].tail(10))
"

# モデルの読み込みテスト
python -c "
from ultralytics import YOLO
model = YOLO('models/hierarchical_best.pt')
print(f'クラス数: {len(model.names)}')
print(f'クラス名: {list(model.names.values())}')
"
```

## トラブルシューティング

### エラー: Dataset images not found

**症状**: `missing path '/path/to/obj_train_data'`

**原因**: data.yamlの`path`が相対パス（`.`）になっている

**解決策**: data.yamlの`path`を絶対パス（ワークスペースルートからの相対パス）に変更
```yaml
path: temp/shosetsu-list-item_dataset_v2  # ✅ 正しい
# path: .                                  # ❌ エラーになる
```

### エラー: shape mismatch during training

**症状**: `RuntimeError: shape mismatch: value tensor of shape [X] cannot be broadcast to indexing result of shape [Y]`

**原因**: MixupまたはCopy-Paste拡張とYOLOv8の互換性問題

**解決策**: scripts/train_hierarchical_model.pyで`mixup=0.0`と`copy_paste=0.0`に設定（既に対応済み）

### 学習が遅い

**症状**: 1エポックに数分以上かかる

**原因**: 
- CPUで学習している
- 画像サイズが大きい
- バッチサイズが大きすぎる

**解決策**:
1. Apple Silicon MacならMPSが有効か確認
2. 画像サイズを640に下げる（`imgsz=640`）
3. バッチサイズを2に下げる（`batch=2`）

### 過学習の兆候

**症状**: 学習データの精度は高いが、検証データの精度が低い

**解決策**:
1. データ拡張パラメータをさらに強化
2. エポック数を減らす
3. より多くの学習データを追加

## 再学習の手順

既存のモデルを削除して、最初から学習をやり直す場合：

```bash
# 既存の学習結果を削除
rm -rf models/hierarchical-detection
rm -f models/hierarchical_best.pt

# 学習を再実行
./venv/bin/python scripts/train_hierarchical_model.py
```

## 次のステップ

学習が完了したら：

1. **結果の可視化を確認**
   - `models/hierarchical-detection/labels.jpg` - ラベル分布
   - `models/hierarchical-detection/train_batch*.jpg` - 学習バッチ

2. **モデルのテスト**
   - テスト画像で検出精度を確認
   - IoU計算ロジックの実装に進む

3. **精度が不十分な場合**
   - アノテーションの見直し
   - 学習データの追加
   - データ拡張パラメータの調整

## 参考情報

- YOLOv8公式ドキュメント: https://docs.ultralytics.com/
- データ拡張の詳細: https://docs.ultralytics.com/modes/train/#augmentation
- トレーニングパラメータ: https://docs.ultralytics.com/modes/train/#train-settings
