#!/usr/bin/env python3
"""
階層的検出モデルのトレーニングスクリプト

5クラス（list-item, title, progress, last_read_date, site_name）を検出する
YOLOv8モデルをトレーニングします。

少量データ（9枚）での過学習を防ぐため、データ拡張を積極的に活用します。
"""

from ultralytics import YOLO
from pathlib import Path
import torch


def main():
    print("=" * 80)
    print("YOLOv8 階層的検出モデルトレーニング")
    print("=" * 80)
    print()
    
    # デバイス情報を表示
    if torch.backends.mps.is_available():
        device = "mps"
        print("✅ Apple Silicon MPS が利用可能です")
    elif torch.cuda.is_available():
        device = "cuda"
        print("✅ CUDA が利用可能です")
    else:
        device = "cpu"
        print("⚠️  CPU を使用します（トレーニングに時間がかかる可能性があります）")
    
    print(f"🖥️  使用デバイス: {device}")
    print()
    
    # データセット設定ファイルのパス
    data_yaml = Path("temp/shosetsu-list-item_dataset_v2/data.yaml")
    
    if not data_yaml.exists():
        print(f"❌ データセット設定ファイルが見つかりません: {data_yaml}")
        return
    
    print(f"📁 データセット設定: {data_yaml}")
    print()
    
    # データセット情報を表示
    print("📊 データセット情報:")
    print("   - クラス数: 5")
    print("   - クラス: list-item, title, progress, last_read_date, site_name")
    print("   - 学習画像数: 10枚（少量データのため、データ拡張を強化）")
    print()
    
    # YOLOv8 モデルをロード（事前学習済みモデルから開始）
    print("🔄 YOLOv8n（nano）モデルをロード中...")
    model = YOLO("yolov8n.pt")  # nanoモデル（最も軽量）
    print("✅ モデルロード完了")
    print()
    
    # トレーニング設定
    print("⚙️  トレーニング設定:")
    epochs = 100
    imgsz = 1280  # 元画像のアスペクト比を考慮して大きめに
    batch = 4  # 画像サイズが大きいのでバッチサイズを減らす
    patience = 20  # Early stopping
    
    print(f"   - エポック数: {epochs}")
    print(f"   - 画像サイズ: {imgsz}")
    print(f"   - バッチサイズ: {batch}")
    print(f"   - Early stopping patience: {patience}")
    print(f"   - デバイス: {device}")
    print()
    
    # データ拡張設定（強化版・安定化）
    print("🎨 データ拡張設定（強化版・安定化）:")
    print("   - HSV色相変動: 0.02 (やや増加)")
    print("   - HSV彩度変動: 0.8 (増加)")
    print("   - HSV明度変動: 0.5 (増加)")
    print("   - 回転角度: 15度 (増加)")
    print("   - 平行移動: 0.15 (増加)")
    print("   - スケール変動: 0.6 (増加)")
    print("   - モザイク拡張: 1.0 (有効)")
    print("   - Mixup拡張: 0.0 (無効化 - 安定性のため)")
    print("   - Copy-Paste拡張: 0.0 (無効化 - 安定性のため)")
    print("   ※ 上下・左右反転は無効（テキストの向きを保持）")
    print("   ※ MixupとCopy-Pasteは学習の安定性のため無効化")
    print()
    
    # トレーニング開始
    print("🚀 トレーニング開始...")
    print("=" * 80)
    print()
    
    try:
        results = model.train(
            data=str(data_yaml),
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            device=device,
            patience=patience,
            project="models",
            name="hierarchical-detection",
            exist_ok=True,
            verbose=True,
            # データ拡張設定（強化版・安定化）
            augment=True,
            hsv_h=0.02,      # 色相の変動（やや増加）
            hsv_s=0.8,       # 彩度の変動（増加）
            hsv_v=0.5,       # 明度の変動（増加）
            degrees=15,      # 回転（増加）
            translate=0.15,  # 平行移動（増加）
            scale=0.6,       # スケール（増加）
            flipud=0.0,      # 上下反転（テキストには不適切）
            fliplr=0.0,      # 左右反転（テキストには不適切）
            mosaic=1.0,      # モザイク拡張
            mixup=0.0,       # Mixup拡張（安定性のため無効化）
            copy_paste=0.0,  # Copy-Paste拡張（安定性のため無効化）
        )
        
        print()
        print("=" * 80)
        print("✅ トレーニング完了！")
        print("=" * 80)
        print()
        
        # 結果の表示
        print("📊 トレーニング結果:")
        print(f"   - 保存先: models/hierarchical-detection/")
        print(f"   - ベストモデル: models/hierarchical-detection/weights/best.pt")
        print(f"   - 最終モデル: models/hierarchical-detection/weights/last.pt")
        print()
        
        # ベストモデルを models/hierarchical_best.pt にコピー
        best_model_path = Path("models/hierarchical-detection/weights/best.pt")
        target_path = Path("models/hierarchical_best.pt")
        
        if best_model_path.exists():
            import shutil
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(best_model_path, target_path)
            print(f"✅ ベストモデルを {target_path} にコピーしました")
            print()
        
        # 学習結果の精度指標を表示
        print("📈 学習結果の精度指標:")
        results_csv = Path("models/hierarchical-detection/results.csv")
        if results_csv.exists():
            import pandas as pd
            df = pd.read_csv(results_csv)
            
            # 最終エポックの結果を取得
            last_epoch = df.iloc[-1]
            
            # 主要な指標を表示
            metrics = {
                "mAP50": "metrics/mAP50(B)",
                "mAP50-95": "metrics/mAP50-95(B)",
                "Precision": "metrics/precision(B)",
                "Recall": "metrics/recall(B)",
            }
            
            for metric_name, column_name in metrics.items():
                if column_name in df.columns:
                    value = last_epoch[column_name]
                    print(f"   - {metric_name}: {value:.4f}")
            print()
        
        print("🎉 次のステップ:")
        print("   1. models/hierarchical-detection/results.png で学習曲線を確認")
        print("   2. models/hierarchical-detection/confusion_matrix.png で混同行列を確認")
        print("   3. 次のタスク（IoU計算ロジックの実装）に進む")
        print()
        print("💡 ヒント:")
        print("   - 過学習の兆候がある場合は、データ拡張パラメータをさらに調整")
        print("   - 精度が低い場合は、エポック数を増やすか、アノテーションを見直す")
        
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ トレーニング中にエラーが発生しました: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
