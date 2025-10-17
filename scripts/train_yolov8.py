#!/usr/bin/env python3
"""
YOLOv8モデルのトレーニングスクリプト

小説リストアイテム検出用のカスタムモデルをトレーニングします。
"""

from ultralytics import YOLO
from pathlib import Path
import torch


def main():
    print("=" * 80)
    print("YOLOv8 モデルトレーニング - 小説リストアイテム検出")
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
    data_yaml = Path("temp/shosetsu-list-item_dataset/data.yaml")
    
    if not data_yaml.exists():
        print(f"❌ データセット設定ファイルが見つかりません: {data_yaml}")
        return
    
    print(f"📁 データセット設定: {data_yaml}")
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
            name="shosetsu-list-item",
            exist_ok=True,
            verbose=True,
            # データ拡張設定（スマホ画面スクリーンショット用）
            augment=True,
            hsv_h=0.015,  # 色相の変動（画面テーマ変更に対応）
            hsv_s=0.5,    # 彩度の変動（画面の明るさに対応）
            hsv_v=0.3,    # 明度の変動（画面の明るさに対応）
            degrees=0,    # 回転なし（スクリーンは常に正立）
            translate=0.05,  # 平行移動を抑制（画面位置は比較的固定）
            scale=0.3,    # スケール変動を抑制（画面サイズは一定）
            flipud=0.0,   # 上下反転なし（テキストの向きを保持）
            fliplr=0.0,   # 左右反転なし（テキストの向きを保持）
            mosaic=1.0,   # モザイク拡張（多様なレイアウトパターンを学習）
        )
        
        print()
        print("=" * 80)
        print("✅ トレーニング完了！")
        print("=" * 80)
        print()
        
        # 結果の表示
        print("📊 トレーニング結果:")
        print(f"   - 保存先: models/shosetsu-list-item/")
        print(f"   - ベストモデル: models/shosetsu-list-item/weights/best.pt")
        print(f"   - 最終モデル: models/shosetsu-list-item/weights/last.pt")
        print()
        
        # ベストモデルを models/best.pt にコピー
        best_model_path = Path("models/shosetsu-list-item/weights/best.pt")
        target_path = Path("models/best.pt")
        
        if best_model_path.exists():
            import shutil
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(best_model_path, target_path)
            print(f"✅ ベストモデルを {target_path} にコピーしました")
            print()
        
        print("🎉 次のステップ:")
        print("   1. models/shosetsu-list-item/results.png で結果を確認")
        print("   2. test_real_image.py でテスト画像を使って検証")
        print("   3. メインアプリケーション（src/realtime_ocr_app.py）を実行")
        
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ トレーニング中にエラーが発生しました: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
