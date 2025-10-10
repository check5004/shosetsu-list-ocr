#!/usr/bin/env python3
"""
リアルタイムOCRアプリケーション

macOS上で指定されたウィンドウをリアルタイムでキャプチャし、
YOLOv8で物体検出、Tesseract OCRでテキスト抽出を行い、
重複を排除してCSVファイルに保存します。

Requirements: 7.1, 7.2
"""

import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import load_config, AppConfig
from src.window_capture import WindowCapture
from src.object_detector import ObjectDetector
from src.ocr_processor import OCRProcessor
from src.data_manager import DataManager
from src.visualizer import Visualizer
from src.error_handler import ErrorHandler


def main():
    """
    メインアプリケーション関数
    
    アプリケーションの初期化、メインループの実行、終了処理を行います。
    
    Requirements: 2.1, 2.2, 1.1, 1.2, 8.1, 8.2
    """
    print("="*60)
    print("リアルタイムOCRアプリケーション")
    print("="*60)
    
    # 設定の読み込み
    print("\n[1/6] 設定を読み込んでいます...")
    config = load_config()
    print(f"✓ 設定を読み込みました")
    print(config)
    
    # 設定の検証
    is_valid, error_message = config.validate()
    if not is_valid:
        ErrorHandler.handle_initialization_error(
            ValueError(error_message),
            "設定の検証に失敗しました"
        )
    
    print("\n✓ 設定の検証に成功しました")
    
    # YOLOv8モデルのロード
    print("\n[2/6] YOLOv8モデルをロードしています...")
    try:
        detector = ObjectDetector(
            model_path=config.model_path,
            confidence_threshold=config.confidence_threshold
        )
        print("✓ YOLOv8モデルのロードに成功しました")
    except Exception as e:
        ErrorHandler.handle_initialization_error(e, "YOLOv8モデルのロードに失敗しました")
    
    # ウィンドウキャプチャの初期化
    print(f"\n[3/6] ウィンドウを検索しています（タイトル: '{config.target_window_title}'）...")
    try:
        window_capture = WindowCapture(config.target_window_title)
        window_info = window_capture.find_window()
        print(f"✓ ウィンドウを見つけました: {window_info['title']} ({window_info['owner']})")
        print(f"  位置: ({window_info['x']}, {window_info['y']})")
        print(f"  サイズ: {window_info['width']}x{window_info['height']}")
    except Exception as e:
        ErrorHandler.handle_initialization_error(e, "ウィンドウの検索に失敗しました")
    
    # OCRプロセッサの初期化
    print(f"\n[4/6] OCRプロセッサを初期化しています（言語: {config.ocr_lang}）...")
    try:
        ocr_processor = OCRProcessor(
            lang=config.ocr_lang,
            margin=config.ocr_margin
        )
        print("✓ OCRプロセッサの初期化に成功しました")
    except Exception as e:
        ErrorHandler.handle_initialization_error(e, "OCRプロセッサの初期化に失敗しました")
    
    # データマネージャーの初期化
    print(f"\n[5/6] データマネージャーを初期化しています...")
    data_manager = DataManager(output_path=config.output_csv)
    print(f"✓ データマネージャーの初期化に成功しました")
    print(f"  出力先: {config.output_csv}")
    
    # ビジュアライザーの初期化
    print(f"\n[6/6] ビジュアライザーを初期化しています...")
    visualizer = Visualizer(window_name=config.display_window_name)
    print("✓ ビジュアライザーの初期化に成功しました")
    
    print("\n" + "="*60)
    print("初期化が完了しました")
    print("="*60)
    print("\n操作方法:")
    print("  - 'q'キーを押すと終了します")
    print("  - Ctrl+Cでも終了できます")
    print("="*60)
    
    # シグナルハンドラの設定（Ctrl+C対応）
    ErrorHandler.setup_signal_handlers(
        data_manager=data_manager,
        cleanup_callback=visualizer.cleanup
    )
    
    # メインループ
    print("\nリアルタイム処理を開始します...\n")
    
    try:
        frame_count = 0
        
        while True:
            frame_count += 1
            
            # ウィンドウキャプチャ
            try:
                frame = window_capture.capture_frame()
            except Exception as e:
                ErrorHandler.handle_runtime_error(e, "ウィンドウキャプチャに失敗しました")
                continue
            
            # 物体検出
            try:
                detections = detector.detect(frame)
            except Exception as e:
                ErrorHandler.handle_runtime_error(e, "物体検出に失敗しました")
                continue
            
            # 検出結果のソート（Y座標で上から下）
            if detections:
                detections = ObjectDetector.sort_by_y_coordinate(detections)
            
            # OCR処理（各バウンディングボックスに対して）
            for detection in detections:
                try:
                    # テキスト抽出
                    text = ocr_processor.extract_text(frame, detection)
                    
                    # テキストの長さチェック
                    if len(text) < config.min_text_length:
                        continue
                    
                    # 重複チェックとデータ追加
                    data_manager.add_text(text)
                    
                except Exception as e:
                    ErrorHandler.handle_runtime_error(
                        e,
                        "OCR処理に失敗しました",
                        verbose=False
                    )
                    continue
            
            # 検出結果の描画
            try:
                annotated_frame = visualizer.draw_detections(frame, detections)
            except Exception as e:
                ErrorHandler.handle_runtime_error(e, "描画処理に失敗しました")
                annotated_frame = frame
            
            # フレーム表示
            try:
                should_continue = visualizer.show_frame(annotated_frame)
                if not should_continue:
                    print("\n'q'キーが押されました。終了します...")
                    break
            except Exception as e:
                ErrorHandler.handle_runtime_error(e, "フレーム表示に失敗しました")
                break
    
    except KeyboardInterrupt:
        print("\n\nCtrl+Cが押されました。終了します...")
    
    except Exception as e:
        ErrorHandler.log_error(e, "予期しないエラーが発生しました")
    
    finally:
        # 終了処理
        ErrorHandler.handle_graceful_shutdown(
            data_manager=data_manager,
            cleanup_callback=visualizer.cleanup
        )


if __name__ == "__main__":
    main()
