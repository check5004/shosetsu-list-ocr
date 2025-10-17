#!/usr/bin/env python3
"""
GUI階層的検出機能の自動テストスクリプト

このスクリプトは、GUIアプリケーションの階層的検出機能を
プログラマティックにテストします。

注意: 完全な自動テストは困難なため、主要な機能の初期化と
設定の確認を行います。実際のGUI操作は手動テストガイド
（docs/gui_testing_guide.md）を参照してください。
"""

import sys
from pathlib import Path
import tkinter as tk

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import AppConfig
from src.gui_app import RealtimeOCRGUI


def test_gui_initialization():
    """
    GUIの初期化テスト
    
    テスト内容:
    - GUIウィンドウの作成
    - 設定の読み込み
    - コンポーネントの初期化
    """
    print("=" * 80)
    print("GUI初期化テスト")
    print("=" * 80)
    
    try:
        # Tkinterルートウィンドウを作成
        root = tk.Tk()
        
        # GUIアプリケーションを初期化
        print("\n🚀 GUIアプリケーションを初期化中...")
        app = RealtimeOCRGUI(root)
        
        # 設定を確認
        print(f"\n⚙️  設定確認:")
        print(f"   - 階層的モデルパス: {app.config.hierarchical_model_path}")
        print(f"   - IoUしきい値: {app.config.iou_threshold}")
        print(f"   - 類似度しきい値: {app.config.similarity_threshold}")
        print(f"   - セッション出力ディレクトリ: {app.config.session_output_dir}")
        print(f"   - 階層的CSV出力: {app.config.hierarchical_csv_output}")
        
        # 階層的モデルの存在確認
        hierarchical_model_path = Path(app.config.hierarchical_model_path)
        if hierarchical_model_path.exists():
            print(f"\n✅ 階層的モデルが見つかりました: {hierarchical_model_path}")
        else:
            print(f"\n⚠️  階層的モデルが見つかりません: {hierarchical_model_path}")
            print("   モデルを学習してから再度実行してください。")
        
        # GUIコンポーネントの確認
        print(f"\n📊 GUIコンポーネント確認:")
        
        # モデル選択ラジオボタンの確認
        if hasattr(app, 'detection_mode_var'):
            print(f"   ✓ モデル選択ラジオボタン: {app.detection_mode_var.get()}")
        else:
            print(f"   ✗ モデル選択ラジオボタンが見つかりません")
        
        # 類似度しきい値スライダーの確認
        if hasattr(app, 'similarity_threshold_var'):
            print(f"   ✓ 類似度しきい値スライダー: {app.similarity_threshold_var.get()}")
        else:
            print(f"   ✗ 類似度しきい値スライダーが見つかりません")
        
        # 画像フォルダを開くボタンの確認
        if hasattr(app, 'open_folder_btn'):
            print(f"   ✓ 画像フォルダを開くボタン: 存在")
        else:
            print(f"   ✗ 画像フォルダを開くボタンが見つかりません")
        
        # 統計情報変数の確認
        stats_vars = [
            'list_item_count_var',
            'title_count_var',
            'error_count_var',
            'success_count_var'
        ]
        
        print(f"\n📊 統計情報変数確認:")
        for var_name in stats_vars:
            if hasattr(app, var_name):
                var = getattr(app, var_name)
                print(f"   ✓ {var_name}: {var.get()}")
            else:
                print(f"   ✗ {var_name}が見つかりません")
        
        # ウィンドウを閉じる
        root.destroy()
        
        print("\n" + "=" * 80)
        print("✅ GUI初期化テスト完了")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ GUI初期化テスト中にエラーが発生: {e}")
        import traceback
        print(f"スタックトレース:\n{traceback.format_exc()}")
        return False


def test_config_validation():
    """
    設定の検証テスト
    
    テスト内容:
    - 階層的検出関連の設定値の検証
    - しきい値の範囲チェック
    """
    print("\n" + "=" * 80)
    print("設定検証テスト")
    print("=" * 80)
    
    try:
        # 設定を作成
        config = AppConfig()
        
        # 階層的検出設定を有効化
        config.use_hierarchical_detection = True
        
        # 設定を検証
        print("\n⚙️  設定検証中...")
        is_valid, error_message = config.validate()
        
        if is_valid:
            print("✅ 設定は有効です")
        else:
            print(f"❌ 設定が無効です: {error_message}")
            return False
        
        # しきい値の範囲チェック
        print(f"\n📊 しきい値の範囲チェック:")
        
        # IoUしきい値
        if 0.0 <= config.iou_threshold <= 1.0:
            print(f"   ✓ IoUしきい値: {config.iou_threshold} (有効範囲: 0.0〜1.0)")
        else:
            print(f"   ✗ IoUしきい値: {config.iou_threshold} (範囲外)")
            return False
        
        # 類似度しきい値
        if 0.0 <= config.similarity_threshold <= 1.0:
            print(f"   ✓ 類似度しきい値: {config.similarity_threshold} (有効範囲: 0.0〜1.0)")
        else:
            print(f"   ✗ 類似度しきい値: {config.similarity_threshold} (範囲外)")
            return False
        
        # 信頼度しきい値
        if 0.0 <= config.confidence_threshold <= 1.0:
            print(f"   ✓ 信頼度しきい値: {config.confidence_threshold} (有効範囲: 0.0〜1.0)")
        else:
            print(f"   ✗ 信頼度しきい値: {config.confidence_threshold} (範囲外)")
            return False
        
        print("\n" + "=" * 80)
        print("✅ 設定検証テスト完了")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 設定検証テスト中にエラーが発生: {e}")
        import traceback
        print(f"スタックトレース:\n{traceback.format_exc()}")
        return False


def print_manual_testing_guide():
    """
    手動テストガイドの案内を表示
    """
    print("\n" + "=" * 80)
    print("手動テストガイド")
    print("=" * 80)
    
    print("\n📖 完全なGUI動作確認は手動テストが必要です。")
    print("   詳細な手順は以下のドキュメントを参照してください:")
    print(f"\n   📄 {project_root / 'docs' / 'gui_testing_guide.md'}")
    
    print("\n🚀 GUIアプリケーションを起動するには:")
    print("   $ source venv/bin/activate")
    print("   $ python src/gui_app.py")
    
    print("\n📋 主要なテスト項目:")
    print("   1. モデル選択機能（既存モデル vs 階層的モデル）")
    print("   2. 統計情報の表示（各クラスの検出数）")
    print("   3. 類似度しきい値スライダーの操作")
    print("   4. 画像フォルダを開く機能")
    print("   5. プレビュー表示（5クラスの色分け）")
    print("   6. CSV出力の確認")
    print("   7. セッション管理（フォルダ作成・ZIP圧縮）")
    
    print("\n" + "=" * 80)


def main():
    """
    メイン関数
    
    GUI関連のテストを実行します。
    """
    print("\n" + "=" * 80)
    print("GUI階層的検出機能の自動テスト")
    print("=" * 80)
    
    # 設定検証テスト
    success_config = test_config_validation()
    
    if not success_config:
        print("\n❌ 設定検証テストが失敗しました。")
        return 1
    
    # GUI初期化テスト
    success_gui = test_gui_initialization()
    
    if not success_gui:
        print("\n❌ GUI初期化テストが失敗しました。")
        return 1
    
    # 手動テストガイドの案内
    print_manual_testing_guide()
    
    print("\n" + "=" * 80)
    print("✅ 自動テストが完了しました")
    print("=" * 80)
    print("\n💡 完全なGUI動作確認は手動テストを実施してください。")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
