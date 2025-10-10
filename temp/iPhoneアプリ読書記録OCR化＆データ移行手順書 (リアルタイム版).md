# **iPhoneアプリ読書記録OCR化＆データ移行手順書 (リアルタイム版)**

## **1\. 目的と概要**

**（変更点）** macOS上で起動している特定のiPhoneシミュレータやアプリのウィンドウをリアルタイムでキャプチャし、AI（物体検出+OCR）を用いて読書記録（タイトル、進捗など）をテキストデータ化、CSVファイルとして保存することを目的とします。

**技術スタック:**

* **アノテーション**: CVAT (Computer Vision Annotation Tool)
* **物体検出**: YOLOv8
* **OCR**: Tesseract OCR
* **実行環境**: macOS, Docker Desktop, Python

**ワークフロー:**

1. **学習データ収集**: iPhoneアプリのスクリーンショットを複数枚用意する。（**目的**: モデル学習のため）
2. **環境構築**: CVAT、Python開発環境、Tesseract OCR、その他リアルタイム処理に必要なライブラリをセットアップする。
3. **アノテーション**: CVATを使い、スクリーンショットから読書記録の各項目を「物体」として囲む作業を行う。
4. **モデル学習**: アノテーションデータを使い、YOLOv8モデルを学習させて「読書記録の項目」を検出できるようにする。
5. **リアルタイム推論とOCR**: 学習済みモデルを使い、指定したアプリのウィンドウを常時監視。項目を検出し、結果を別ウィンドウに描画しながらOCRでテキストを抽出し続ける。
6. **データ保存**: 抽出したテキストデータの重複を排除し、プログラム終了時にCSVファイルとして出力する。

## **2\. ステップ1: 学習用データ収集 (スクリーンショット)**

**（変更点）** このステップは、リアルタイム検出AIを学習させるためだけに必要です。以前のように動画を撮る必要はありません。

1. macOS上で、テキストを抽出したいiPhoneアプリを起動します。（iPhone実機を接続しQuickTimeでミラーリングするか、Xcodeのシミュレータを使います）
2. リストの様々な箇所で**スクリーンショットを50枚〜200枚程度**撮影し、1つのフォルダにまとめます。
   * macOSのスクリーンショット撮影: Cmd \+ Shift \+ 4 で範囲選択
3. このフォルダを \~/BookDataExtractor/frames\_for\_train のように配置します。

## **3\. ステップ2: 環境構築**

### **3.1. CVATのセットアップ (Docker)**

この手順は変更ありません。以前の手順でセットアップ済みであれば不要です。

\# (未実施の場合)
git clone \[https://github.com/cvat-ai/cvat.git\](https://github.com/cvat-ai/cvat.git)
cd cvat
docker compose up \-d
docker compose exec \-T cvat\_server python3 manage.py createsuperuser \--username admin \--email admin@example.com

### **3.2. Python開発環境とTesseract OCR**

**（変更点）** リアルタイム処理用のライブラリを追加します。

cd \~/BookDataExtractor

**1\. Tesseract OCRのインストール** (変更なし)

brew install tesseract tesseract-lang

2\. Python仮想環境とライブラリのインストール
requirements.txt に mss と pygetwindow を追加します。
\# 仮想環境を作成 (未作成の場合)
python3 \-m venv venv

\# 仮想環境をアクティベート
source venv/bin/activate

\# 必要なライブラリをまとめたファイルを作成 (更新)
cat \<\< EOF \> requirements.txt
ultralytics
opencv-python
pytesseract
pandas
tqdm
mss
pygetwindow
EOF

\# ライブラリを一括インストール
pip install \-r requirements.txt

## **4\. ステップ3: アノテーション (CVAT)**

この手順は変更ありません。ステップ1で収集したスクリーンショット (frames\_for\_train フォルダ内の画像) を使って、以前と同様に list-item のアノテーションを行ってください。完了後、**YOLO 1.1形式でエクスポート**します。

## **5\. ステップ4: YOLOv8モデルの学習**

この手順も変更ありません。アノテーションデータを使い、best.pt という名前の学習済みモデルを作成してください。

## **6\. ステップ5: リアルタイム推論、描画、OCR**

（全面変更）
以前のバッチ処理スクリプトに代わり、リアルタイム処理を行うスクリプトを作成します。
このスクリプトは、指定されたウィンドウをキャプチャし続け、検出結果をオーバーレイ描画したウィンドウを別途表示します。
以下のスクリプトを realtime\_extractor.py として保存してください。

import os
import cv2
import pytesseract
import pandas as pd
import numpy as np
from ultralytics import YOLO
from tqdm import tqdm
import mss
import pygetwindow as gw

\# \--- 設定 \---
MODEL\_PATH \= "runs/detect/train/weights/best.pt"  \# 学習済みモデルのパス
TARGET\_WINDOW\_TITLE \= "iPhone"                    \# キャプチャしたいウィンドウのタイトル（部分一致可）
                                                  \# 例: Xcodeのシミュレータなら "iPhone 15 Pro", QuickTimeならお使いのiPhone名
OUTPUT\_CSV \= "book\_data\_realtime.csv"             \# 出力ファイル名
CONFIDENCE\_THRESHOLD \= 0.6                        \# 検出の信頼度しきい値 (0.0-1.0)
\# \-------------

def main():
    \# モデルをロード
    try:
        model \= YOLO(MODEL\_PATH)
    except Exception as e:
        print(f"Error: モデルの読み込みに失敗しました: {MODEL\_PATH}")
        print(e)
        return

    \# ターゲットウィンドウを検索
    try:
        target\_windows \= gw.getWindowsWithTitle(TARGET\_WINDOW\_TITLE)
        if not target\_windows:
            print(f"Error: タイトルに '{TARGET\_WINDOW\_TITLE}' を含むウィンドウが見つかりません。")
            print("起動中のウィンドウタイトル:", \[w.title for w in gw.getAllWindows() if w.title\])
            return
        window \= target\_windows\[0\]
        print(f"'{window.title}' ウィンドウをキャプチャします。")
    except Exception as e:
        print(f"ウィンドウの取得中にエラーが発生しました: {e}")
        return

    \# 重複を排除しながらテキストを保存するためのset
    extracted\_texts \= set()

    \# スクリーンキャプチャの準備
    sct \= mss.mss()

    print("\\nリアルタイム検出を開始します。'q'キーを押すと終了し、CSVファイルに保存します。")

    try:
        while True:
            \# ウィンドウの位置とサイズを取得
            x, y, width, height \= window.left, window.top, window.width, window.height

            \# モニター情報 (マルチモニター対応)
            monitor \= {"top": y, "left": x, "width": width, "height": height}

            \# ウィンドウをキャプチャ
            img\_sct \= sct.grab(monitor)

            \# mss形式からOpenCV形式(numpy array)に変換
            frame \= np.array(img\_sct)
            frame \= cv2.cvtColor(frame, cv2.COLOR\_BGRA2BGR) \# BGRAからBGRへ変換

            \# 物体検出を実行
            results \= model(frame, verbose=False)
            result \= results\[0\]

            \# 検出されたバウンディングボックスの座標をY座標でソート
            sorted\_boxes \= sorted(result.boxes, key=lambda box: box.xyxy\[0\]\[1\])

            for box in sorted\_boxes:
                if box.conf\[0\] \< CONFIDENCE\_THRESHOLD:
                    continue

                x1, y1, x2, y2 \= \[int(i) for i in box.xyxy\[0\]\]

                \# 検出結果を描画
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2\)

                \# OCR処理 (元の画像から切り出す)
                try:
                    \# 安全マージンを追加
                    crop\_x1 \= max(0, x1 \- 5\)
                    crop\_y1 \= max(0, y1 \- 5\)
                    crop\_x2 \= min(frame.shape\[1\], x2 \+ 5\)
                    crop\_y2 \= min(frame.shape\[0\], y2 \+ 5\)

                    cropped\_img \= frame\[crop\_y1:crop\_y2, crop\_x1:crop\_x2\]

                    text \= pytesseract.image\_to\_string(cropped\_img, lang='jpn')
                    cleaned\_text \= " ".join(text.split()).strip()

                    if cleaned\_text and len(cleaned\_text) \> 2:
                        if cleaned\_text not in extracted\_texts:
                            print(f"新規データ検出: {cleaned\_text}")
                            extracted\_texts.add(cleaned\_text)
                except Exception:
                    pass

            \# 結果をウィンドウに表示
            cv2.imshow(f"Real-time Detection for '{window.title}'", frame)

            \# 'q'キーが押されたらループを抜ける
            if cv2.waitKey(1) & 0xFF \== ord('q'):
                break
    finally:
        \# ループ終了後の処理
        cv2.destroyAllWindows()
        print("\\nリアルタイム検出を終了しました。")

        if extracted\_texts:
            df \= pd.DataFrame(list(extracted\_texts), columns=\["extracted\_text"\])
            df.to\_csv(OUTPUT\_CSV, index=False)
            print(f"重複を除いて {len(extracted\_texts)} 件のデータを抽出し、{OUTPUT\_CSV} に保存しました。")
        else:
            print("データは抽出されませんでした。")

if \_\_name\_\_ \== "\_\_main\_\_":
    main()

### **実行方法**

1. **対象アプリを起動**: 抽出したい小説アプリをXcodeシミュレータやQuickTimeミラーリングでmacOS上に表示させます。
2. **ウィンドウタイトルを確認**: realtime\_extractor.py の TARGET\_WINDOW\_TITLE 変数を、表示されているウィンドウのタイトル（一部でも可）に正確に設定します。
3. **スクリプト実行**: ターミナルで (venv) が有効な状態で、以下のコマンドを実行します。
   python realtime\_extractor.py

4. **確認**: 2つのウィンドウが表示されます。1つはオリジナルのアプリ画面、もう1つは「Real-time Detection for ...」というタイトルで、検出されたリスト項目が緑色の四角で囲まれた画面です。
5. **データ収集**: アプリをゆっくりスクロールさせると、新しいデータが検出されターミナルに出力されます。
6. **終了**: 描画ウィンドウを選択した状態で q キーを押すとプログラムが終了し、book\_data\_realtime.csv が作成されます。

## **7\. トラブルシューティング**

* **ウィンドウが見つからないエラー**: TARGET\_WINDOW\_TITLE が間違っている可能性があります。エラーメッセージに表示される現在起動中のウィンドウタイトル一覧を参考に、正しいタイトルを設定してください。
* **動作がカクカクする/遅い**: リアルタイムOCR処理は負荷が高いです。マシンスペックによっては遅延が発生します。その場合、realtime\_extractor.py のOCR処理部分をコメントアウトすれば、描画だけをスムーズに行うことができます。
* **その他**: 以前のトラブルシューティング項目（OCR精度、検出精度など）も同様に適用されます。