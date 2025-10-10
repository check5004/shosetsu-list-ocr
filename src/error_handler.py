"""
エラーハンドリングモジュール

このモジュールは、アプリケーション全体のエラー処理を統一的に管理します。
初期化エラー、実行時エラー、安全なシャットダウンの各ハンドラを提供します。
"""

import sys
import signal
from typing import Optional, Callable, Any
import cv2


class ErrorHandler:
    """
    アプリケーション全体のエラーハンドリングを担当するクラス
    
    Requirements:
    - 8.1: モデルのロードに失敗する場合のエラー処理
    - 8.2: ウィンドウの取得に失敗する場合のエラー処理
    - 8.3: OCR処理でエラーが発生する場合の継続処理
    - 8.4: ユーザーが強制終了する場合の安全なクリーンアップ
    - 8.5: 予期しないエラーのログ出力
    """
    
    @staticmethod
    def handle_initialization_error(error: Exception, context: str) -> None:
        """
        初期化エラーの処理
        
        モデルのロード失敗、ウィンドウの取得失敗など、
        アプリケーションの起動を継続できない致命的なエラーを処理します。
        エラーメッセージを表示してプログラムを終了します。
        
        Args:
            error: 発生した例外
            context: エラーが発生したコンテキスト（説明文）
        
        Requirements: 8.1, 8.2
        """
        print(f"\n{'='*60}")
        print(f"初期化エラー: {context}")
        print(f"{'='*60}")
        print(f"詳細: {type(error).__name__}: {error}")
        print(f"{'='*60}\n")
        sys.exit(1)
    
    @staticmethod
    def handle_runtime_error(error: Exception, context: str, verbose: bool = True) -> None:
        """
        実行時エラーの処理（継続可能）
        
        OCR処理の失敗など、処理を継続できるエラーを処理します。
        警告メッセージを表示しますが、プログラムは継続します。
        
        Args:
            error: 発生した例外
            context: エラーが発生したコンテキスト（説明文）
            verbose: 詳細なエラー情報を表示するかどうか
        
        Requirements: 8.3, 8.5
        """
        if verbose:
            print(f"警告: {context} - {type(error).__name__}: {error}")
        else:
            print(f"警告: {context}")
    
    @staticmethod
    def handle_graceful_shutdown(
        data_manager: Optional[Any] = None,
        cleanup_callback: Optional[Callable[[], None]] = None
    ) -> None:
        """
        安全なシャットダウン処理
        
        ユーザーによる終了（'q'キーまたはCtrl+C）時に、
        データの保存とリソースのクリーンアップを行います。
        
        Args:
            data_manager: DataManagerインスタンス（CSV出力用）
            cleanup_callback: 追加のクリーンアップ処理を行うコールバック関数
        
        Requirements: 8.4
        """
        print("\n" + "="*60)
        print("シャットダウン中...")
        print("="*60)
        
        # データの保存
        if data_manager is not None:
            try:
                data_manager.export_to_csv()
                print("✓ データをCSVファイルに保存しました")
            except Exception as e:
                print(f"✗ CSV出力中にエラーが発生しました: {e}")
        
        # OpenCVウィンドウのクリーンアップ
        try:
            cv2.destroyAllWindows()
            print("✓ 表示ウィンドウをクローズしました")
        except Exception as e:
            print(f"✗ ウィンドウクローズ中にエラーが発生しました: {e}")
        
        # 追加のクリーンアップ処理
        if cleanup_callback is not None:
            try:
                cleanup_callback()
                print("✓ クリーンアップ処理を完了しました")
            except Exception as e:
                print(f"✗ クリーンアップ中にエラーが発生しました: {e}")
        
        print("="*60)
        print("アプリケーションを終了しました")
        print("="*60 + "\n")
    
    @staticmethod
    def setup_signal_handlers(
        data_manager: Optional[Any] = None,
        cleanup_callback: Optional[Callable[[], None]] = None
    ) -> None:
        """
        シグナルハンドラの設定
        
        Ctrl+C（SIGINT）やSIGTERMを受信した際に、
        安全なシャットダウン処理を実行するようにします。
        
        Args:
            data_manager: DataManagerインスタンス（CSV出力用）
            cleanup_callback: 追加のクリーンアップ処理を行うコールバック関数
        
        Requirements: 8.4
        """
        def signal_handler(signum: int, frame: Any) -> None:
            """シグナル受信時のハンドラ"""
            ErrorHandler.handle_graceful_shutdown(data_manager, cleanup_callback)
            sys.exit(0)
        
        # SIGINT（Ctrl+C）とSIGTERMのハンドラを設定
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    @staticmethod
    def log_error(error: Exception, context: str) -> None:
        """
        予期しないエラーのログ出力
        
        デバッグ用に詳細なエラー情報を出力します。
        
        Args:
            error: 発生した例外
            context: エラーが発生したコンテキスト（説明文）
        
        Requirements: 8.5
        """
        print(f"\n{'='*60}")
        print(f"予期しないエラー: {context}")
        print(f"{'='*60}")
        print(f"エラータイプ: {type(error).__name__}")
        print(f"エラーメッセージ: {error}")
        
        # スタックトレースの表示（デバッグ用）
        import traceback
        print("\nスタックトレース:")
        traceback.print_exc()
        print(f"{'='*60}\n")
