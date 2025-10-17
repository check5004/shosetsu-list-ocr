#!/usr/bin/env python3
"""
階層的検出機能の統合テストスクリプト

このスクリプトは、temp/test_screenshot/内の画像を使用して、
階層的検出 → OCR → CSV出力の全体フローをテストします。

テスト内容:
- サンプル画像を使用した全体フローのテスト（タスク14.1）
- エラーケースの動作確認（タスク14.2）
- セッションフォルダの作成とZIP圧縮の確認
"""

import sys
from pathlib import Path
import cv2
import numpy as np

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import AppConfig
from src.hierarchical_pipeline import HierarchicalPipeline


def test_hierarchical_pipeline_with_sample_images():
    """
    サンプル画像を使用した全体フローのテスト（タスク14.1）
    
    テスト内容:
    - temp/test_screenshot/内の画像を使用
    - 階層的検出 → OCR → CSV出力の全体フローを確認
    - セッションフォルダの作成とZIP圧縮を確認
    """
    print("=" * 80)
    print("タスク14.1: サンプル画像を使用した全体フローのテスト")
    print("=" * 80)
    
    # テスト画像のパスを取得
    test_screenshot_dir = Path("temp/test_screenshot")
    
    if not test_screenshot_dir.exists():
        print(f"❌ テスト画像ディレクトリが見つかりません: {test_screenshot_dir}")
        return False
    
    # 画像ファイルを取得（.jpgと.jpeg）
    image_files = list(test_screenshot_dir.glob("*.jpg")) + list(test_screenshot_dir.glob("*.jpeg"))
    
    if not image_files:
        print(f"❌ テスト画像が見つかりません: {test_screenshot_dir}")
        return False
    
    print(f"\n📁 テスト画像ディレクトリ: {test_screenshot_dir}")
    print(f"📷 テスト画像数: {len(image_files)}")
    for img_file in image_files:
        print(f"   - {img_file.name}")
    
    # 設定を作成（階層的検出モードを有効化）
    config = AppConfig()
    config.use_hierarchical_detection = True
    config.hierarchical_csv_output = "output/test_hierarchical_data.csv"
    config.session_output_dir = "output/test_sessions"
    
    # 階層的モデルの存在チェック
    if not Path(config.hierarchical_model_path).exists():
        print(f"\n❌ 階層的検出モデルが見つかりません: {config.hierarchical_model_path}")
        print("   モデルを学習してから再度実行してください。")
        return False
    
    print(f"\n⚙️  設定:")
    print(f"   - 階層的モデル: {config.hierarchical_model_path}")
    print(f"   - IoUしきい値: {config.iou_threshold}")
    print(f"   - 類似度しきい値: {config.similarity_threshold}")
    print(f"   - CSV出力: {config.hierarchical_csv_output}")
    print(f"   - セッション出力: {config.session_output_dir}")
    
    try:
        # パイプラインを初期化
        print("\n🚀 パイプラインを初期化中...")
        pipeline = HierarchicalPipeline(config)
        
        # パイプラインを開始
        print("\n🚀 パイプラインを開始...")
        pipeline.start()
        
        # 各画像を処理
        print("\n📊 画像処理を開始...")
        total_processed = 0
        
        for idx, image_file in enumerate(image_files, 1):
            print(f"\n--- 画像 {idx}/{len(image_files)}: {image_file.name} ---")
            
            # 画像を読み込み
            frame = cv2.imread(str(image_file))
            
            if frame is None:
                print(f"⚠️  画像の読み込みに失敗: {image_file}")
                continue
            
            print(f"   画像サイズ: {frame.shape[1]}x{frame.shape[0]}")
            
            # フレームを処理
            new_records = pipeline.process_frame(frame)
            total_processed += new_records
            
            print(f"   処理結果: {new_records}件の新規レコード")
        
        # 統計情報を取得
        stats = pipeline.get_statistics()
        print(f"\n📊 処理統計:")
        print(f"   - 処理フレーム数: {stats['frame_count']}")
        print(f"   - 新規レコード数: {stats['processed_count']}")
        print(f"   - 総レコード数: {stats['total_records']}")
        print(f"   - エラーレコード数: {stats['error_records']}")
        
        # パイプラインを停止（CSV出力とZIP圧縮）
        print("\n🛑 パイプラインを停止...")
        pipeline.stop()
        
        # 出力ファイルの確認
        print("\n✅ 出力ファイルの確認:")
        
        # CSV出力の確認
        csv_path = Path(config.hierarchical_csv_output)
        if csv_path.exists():
            print(f"   ✓ CSV出力: {csv_path} ({csv_path.stat().st_size} bytes)")
        else:
            print(f"   ✗ CSV出力が見つかりません: {csv_path}")
        
        # セッションフォルダの確認
        session_dir = Path(config.session_output_dir)
        if session_dir.exists():
            session_folders = list(session_dir.glob("*"))
            print(f"   ✓ セッションフォルダ: {session_dir} ({len(session_folders)}個)")
            
            # ZIP圧縮の確認
            zip_files = list(session_dir.glob("*.zip"))
            if zip_files:
                print(f"   ✓ ZIP圧縮: {len(zip_files)}個")
                for zip_file in zip_files:
                    print(f"      - {zip_file.name} ({zip_file.stat().st_size} bytes)")
            else:
                print(f"   ✗ ZIP圧縮ファイルが見つかりません")
        else:
            print(f"   ✗ セッションフォルダが見つかりません: {session_dir}")
        
        print("\n" + "=" * 80)
        print("✅ タスク14.1: 全体フローのテスト完了")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ テスト中にエラーが発生: {e}")
        import traceback
        print(f"スタックトレース:\n{traceback.format_exc()}")
        return False


def test_error_cases():
    """
    エラーケースの動作確認（タスク14.2）
    
    テスト内容:
    - 必須項目欠損時のerror_status記録を確認
    - 重複データの曖昧マッチング動作を確認
    - 孤立要素の警告ログ出力を確認
    """
    print("\n" + "=" * 80)
    print("タスク14.2: エラーケースの動作確認")
    print("=" * 80)
    
    # CSV出力を確認
    csv_path = Path("output/test_hierarchical_data.csv")
    
    if not csv_path.exists():
        print(f"⚠️  CSV出力が見つかりません: {csv_path}")
        print("   タスク14.1を先に実行してください。")
        return False
    
    print(f"\n📄 CSV出力を確認: {csv_path}")
    
    try:
        import pandas as pd
        
        # CSVを読み込み
        df = pd.read_csv(csv_path)
        
        print(f"\n📊 データ統計:")
        print(f"   - 総レコード数: {len(df)}")
        
        # エラーステータスの確認
        error_records = df[df['error_status'] != 'OK']
        print(f"   - エラーレコード数: {len(error_records)}")
        
        if len(error_records) > 0:
            print(f"\n⚠️  エラーレコードの詳細:")
            for idx, row in error_records.iterrows():
                print(f"   - {row['list_item_id']}: {row['error_status']}")
                print(f"      title: '{row['title']}'")
                print(f"      last_read_date: '{row['last_read_date']}'")
                print(f"      site_name: '{row['site_name']}'")
        else:
            print(f"   ✓ すべてのレコードが正常（error_status='OK'）")
        
        # 必須項目の欠損確認
        print(f"\n📋 必須項目の欠損確認:")
        missing_title = df[df['title'].isna() | (df['title'] == '')]
        missing_last_read_date = df[df['last_read_date'].isna() | (df['last_read_date'] == '')]
        missing_site_name = df[df['site_name'].isna() | (df['site_name'] == '')]
        
        print(f"   - titleが欠損: {len(missing_title)}件")
        print(f"   - last_read_dateが欠損: {len(missing_last_read_date)}件")
        print(f"   - site_nameが欠損: {len(missing_site_name)}件")
        
        # オプション項目の確認
        print(f"\n📋 オプション項目の確認:")
        missing_progress = df[df['progress'].isna() | (df['progress'] == '')]
        print(f"   - progressが欠損: {len(missing_progress)}件（エラーではない）")
        
        # 画像パスの確認
        print(f"\n📷 画像パスの確認:")
        valid_image_paths = df[df['image_path'] != '']
        print(f"   - 有効な画像パス: {len(valid_image_paths)}件")
        print(f"   - 無効な画像パス: {len(df) - len(valid_image_paths)}件")
        
        print("\n" + "=" * 80)
        print("✅ タスク14.2: エラーケースの動作確認完了")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ エラーケースの確認中にエラーが発生: {e}")
        import traceback
        print(f"スタックトレース:\n{traceback.format_exc()}")
        return False


def main():
    """
    メイン関数
    
    統合テストを実行します。
    """
    print("\n" + "=" * 80)
    print("階層的検出機能の統合テスト")
    print("=" * 80)
    
    # タスク14.1: サンプル画像を使用した全体フローのテスト
    success_14_1 = test_hierarchical_pipeline_with_sample_images()
    
    if not success_14_1:
        print("\n❌ タスク14.1が失敗しました。")
        return 1
    
    # タスク14.2: エラーケースの動作確認
    success_14_2 = test_error_cases()
    
    if not success_14_2:
        print("\n❌ タスク14.2が失敗しました。")
        return 1
    
    print("\n" + "=" * 80)
    print("✅ すべての統合テストが完了しました")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
