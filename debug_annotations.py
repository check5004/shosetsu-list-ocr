#!/usr/bin/env python3
"""
アノテーションのデバッグスクリプト
YOLO形式のアノテーションを可視化
"""

import cv2
from pathlib import Path


def yolo_to_bbox(yolo_line, img_width, img_height):
    """YOLO形式（正規化座標）をピクセル座標に変換"""
    parts = yolo_line.strip().split()
    class_id = int(parts[0])
    center_x = float(parts[1]) * img_width
    center_y = float(parts[2]) * img_height
    width = float(parts[3]) * img_width
    height = float(parts[4]) * img_height
    
    x1 = int(center_x - width / 2)
    y1 = int(center_y - height / 2)
    x2 = int(center_x + width / 2)
    y2 = int(center_y + height / 2)
    
    return class_id, x1, y1, x2, y2


def main():
    # トレーニング画像とアノテーションのパス
    image_path = Path("temp/shosetsu-list-item_dataset/obj_train_data/IMG_1307.png")
    annotation_path = Path("temp/shosetsu-list-item_dataset/obj_train_data/IMG_1307.txt")
    
    # 画像を読み込み
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"❌ 画像が読み込めません: {image_path}")
        return
    
    height, width = image.shape[:2]
    print(f"画像サイズ: {width}x{height}")
    print()
    
    # アノテーションを読み込み
    with open(annotation_path, 'r') as f:
        lines = f.readlines()
    
    print(f"アノテーション数: {len(lines)}")
    print()
    
    # 各アノテーションを描画
    for i, line in enumerate(lines, 1):
        class_id, x1, y1, x2, y2 = yolo_to_bbox(line, width, height)
        
        print(f"検出 {i}:")
        print(f"  YOLO形式: {line.strip()}")
        print(f"  ピクセル座標: ({x1}, {y1}) → ({x2}, {y2})")
        print(f"  サイズ: {x2-x1}x{y2-y1}")
        print()
        
        # 矩形を描画
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 3)
        cv2.putText(
            image,
            f"#{i}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            2
        )
    
    # 結果を保存
    output_path = Path("temp/annotation_debug.jpg")
    cv2.imwrite(str(output_path), image)
    print(f"✅ アノテーション可視化を保存: {output_path}")
    
    # 画像を開く
    import subprocess
    subprocess.run(["open", str(output_path)])


if __name__ == "__main__":
    main()
