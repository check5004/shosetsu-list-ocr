#!/usr/bin/env python3
"""
実際のスクリーンショット画像を使用したテストスクリプト

Requirements: 2.3, 4.3
"""

import cv2
from pathlib import Path
from src.object_detector import ObjectDetector
from src.ocr_processor import OCRProcessor


def main():
    # 画像パス
    image_path = Path("temp/test_screenshot/スクリーンショット 2025-10-10 15.45.26.jpeg")
    
    if not image_path.exists():
        print(f"❌ 画像が見つかりません: {image_path}")
        return
    
    print(f"📷 画像を読み込み中: {image_path}")
    frame = cv2.imread(str(image_path))
    
    if frame is None:
        print("❌ 画像の読み込みに失敗しました")
        return
    
    print(f"✅ 画像サイズ: {frame.shape[1]}x{frame.shape[0]}")
    print()
    
    # YOLOv8モデルの確認
    model_path = Path("models/best.pt")
    if not model_path.exists():
        print(f"❌ YOLOv8モデルが見つかりません: {model_path}")
        print("物体検出をスキップします")
        detector = None
    else:
        print("🔍 YOLOv8モデルを読み込み中...")
        detector = ObjectDetector(str(model_path), confidence_threshold=0.3)  # しきい値を下げて検出しやすく
        print(f"✅ モデル読み込み完了（デバイス: {detector.device}）")
        print(f"   信頼度しきい値: 0.3")
        print()
    
    # OCRプロセッサの初期化
    try:
        print("📝 OCRプロセッサを初期化中...")
        ocr_processor = OCRProcessor(lang='jpn', margin=5)
        print("✅ OCRプロセッサ初期化完了")
        print()
    except RuntimeError as e:
        print(f"⚠️  OCRプロセッサの初期化に失敗: {e}")
        print("物体検出のみを実行します")
        print()
        ocr_processor = None
    
    # 物体検出を実行
    if detector:
        print("🎯 物体検出を実行中...")
        detections = detector.detect(frame)
        print(f"✅ {len(detections)}個のリストアイテムを検出")
        print()
        
        if detections:
            # Y座標でソート
            sorted_detections = ObjectDetector.sort_by_y_coordinate(detections)
            
            print("=" * 80)
            print("検出結果とOCR抽出テキスト")
            print("=" * 80)
            
            for i, bbox in enumerate(sorted_detections, 1):
                print(f"\n📌 検出 #{i}")
                print(f"   位置: ({bbox.x1}, {bbox.y1}) → ({bbox.x2}, {bbox.y2})")
                print(f"   信頼度: {bbox.confidence:.2f}")
                
                # OCR実行（OCRプロセッサが利用可能な場合のみ）
                if ocr_processor:
                    text = ocr_processor.extract_text(frame, bbox)
                    
                    if text:
                        print(f"   📝 抽出テキスト:")
                        for line in text.split('\n'):
                            print(f"      {line}")
                    else:
                        print(f"   ⚠️  テキストが抽出できませんでした")
                else:
                    print(f"   ⚠️  OCR未実行（Tesseract未インストール）")
            
            print("\n" + "=" * 80)
            
            # 検出結果を画像に描画
            output_image = frame.copy()
            for bbox in sorted_detections:
                cv2.rectangle(
                    output_image,
                    (bbox.x1, bbox.y1),
                    (bbox.x2, bbox.y2),
                    (0, 255, 0),
                    2
                )
                cv2.putText(
                    output_image,
                    f"{bbox.confidence:.2f}",
                    (bbox.x1, bbox.y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2
                )
            
            # 結果を保存
            output_path = Path("temp/test_screenshot/detection_result.jpg")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), output_image)
            print(f"\n💾 検出結果を保存: {output_path}")
        else:
            print("⚠️  リストアイテムが検出されませんでした")
    else:
        print("⚠️  物体検出をスキップしました（モデルが見つかりません）")
        print("OCRのみをテストする場合は、手動でバウンディングボックスを指定してください")


if __name__ == "__main__":
    main()
