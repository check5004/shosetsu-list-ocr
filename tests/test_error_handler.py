"""
エラーハンドリングモジュールのテストコード
"""

import sys
import signal
from io import StringIO
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.error_handler import ErrorHandler


class TestErrorHandler:
    """ErrorHandlerクラスのテスト"""
    
    def test_handle_initialization_error_exits_program(self):
        """初期化エラーがプログラムを終了することを確認"""
        error = FileNotFoundError("Model file not found")
        context = "モデルファイルのロード"
        
        with pytest.raises(SystemExit) as exc_info:
            with patch('sys.stdout', new=StringIO()) as fake_out:
                ErrorHandler.handle_initialization_error(error, context)
        
        assert exc_info.value.code == 1
    
    def test_handle_initialization_error_prints_message(self):
        """初期化エラーがメッセージを出力することを確認"""
        error = FileNotFoundError("Model file not found")
        context = "モデルファイルのロード"
        
        with pytest.raises(SystemExit):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                ErrorHandler.handle_initialization_error(error, context)
                output = fake_out.getvalue()
                assert "初期化エラー" in output
                assert context in output
                assert "FileNotFoundError" in output
    
    def test_handle_runtime_error_continues_execution(self):
        """実行時エラーがプログラムを継続することを確認"""
        error = ValueError("OCR failed")
        context = "OCR処理"
        
        # 例外が発生しないことを確認
        with patch('sys.stdout', new=StringIO()) as fake_out:
            ErrorHandler.handle_runtime_error(error, context)
            output = fake_out.getvalue()
            assert "警告" in output
            assert context in output
    
    def test_handle_runtime_error_verbose_mode(self):
        """実行時エラーの詳細モードを確認"""
        error = ValueError("OCR failed")
        context = "OCR処理"
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            ErrorHandler.handle_runtime_error(error, context, verbose=True)
            output = fake_out.getvalue()
            assert "ValueError" in output
            assert "OCR failed" in output
    
    def test_handle_runtime_error_non_verbose_mode(self):
        """実行時エラーの非詳細モードを確認"""
        error = ValueError("OCR failed")
        context = "OCR処理"
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            ErrorHandler.handle_runtime_error(error, context, verbose=False)
            output = fake_out.getvalue()
            assert "ValueError" not in output
            assert context in output
    
    def test_handle_graceful_shutdown_with_data_manager(self):
        """データマネージャーを使用したシャットダウンを確認"""
        mock_data_manager = Mock()
        mock_data_manager.export_to_csv = Mock()
        
        with patch('cv2.destroyAllWindows') as mock_cv2:
            with patch('sys.stdout', new=StringIO()) as fake_out:
                ErrorHandler.handle_graceful_shutdown(data_manager=mock_data_manager)
                output = fake_out.getvalue()
                
                # データマネージャーのexport_to_csvが呼ばれたことを確認
                mock_data_manager.export_to_csv.assert_called_once()
                
                # cv2.destroyAllWindowsが呼ばれたことを確認
                mock_cv2.assert_called_once()
                
                # 出力メッセージを確認
                assert "シャットダウン中" in output
                assert "CSV" in output
    
    def test_handle_graceful_shutdown_with_cleanup_callback(self):
        """クリーンアップコールバックを使用したシャットダウンを確認"""
        mock_callback = Mock()
        
        with patch('cv2.destroyAllWindows'):
            with patch('sys.stdout', new=StringIO()):
                ErrorHandler.handle_graceful_shutdown(cleanup_callback=mock_callback)
                
                # コールバックが呼ばれたことを確認
                mock_callback.assert_called_once()
    
    def test_handle_graceful_shutdown_handles_csv_export_error(self):
        """CSV出力エラーを処理することを確認"""
        mock_data_manager = Mock()
        mock_data_manager.export_to_csv = Mock(side_effect=Exception("CSV error"))
        
        with patch('cv2.destroyAllWindows'):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                # 例外が発生しないことを確認
                ErrorHandler.handle_graceful_shutdown(data_manager=mock_data_manager)
                output = fake_out.getvalue()
                assert "CSV出力中にエラー" in output
    
    def test_handle_graceful_shutdown_handles_cv2_error(self):
        """OpenCVエラーを処理することを確認"""
        with patch('cv2.destroyAllWindows', side_effect=Exception("CV2 error")):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                # 例外が発生しないことを確認
                ErrorHandler.handle_graceful_shutdown()
                output = fake_out.getvalue()
                assert "ウィンドウクローズ中にエラー" in output
    
    def test_setup_signal_handlers(self):
        """シグナルハンドラの設定を確認"""
        mock_data_manager = Mock()
        
        with patch('signal.signal') as mock_signal:
            ErrorHandler.setup_signal_handlers(data_manager=mock_data_manager)
            
            # signal.signalが2回呼ばれたことを確認（SIGINTとSIGTERM）
            assert mock_signal.call_count == 2
            
            # SIGINTとSIGTERMが設定されたことを確認
            calls = mock_signal.call_args_list
            signal_types = [call[0][0] for call in calls]
            assert signal.SIGINT in signal_types
            assert signal.SIGTERM in signal_types
    
    def test_log_error(self):
        """エラーログ出力を確認"""
        error = RuntimeError("Unexpected error")
        context = "メイン処理"
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            ErrorHandler.log_error(error, context)
            output = fake_out.getvalue()
            
            assert "予期しないエラー" in output
            assert context in output
            assert "RuntimeError" in output
            assert "Unexpected error" in output
            assert "スタックトレース" in output
