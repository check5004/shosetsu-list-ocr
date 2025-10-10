"""
Unit tests for the DataManager module.
"""

import pytest
from pathlib import Path
import tempfile
import pandas as pd
from src.data_manager import DataManager


class TestDataManager:
    """DataManagerクラスのテスト"""
    
    def test_initialization(self):
        """初期化のテスト"""
        dm = DataManager("test_output.csv")
        assert dm.output_path == Path("test_output.csv")
        assert len(dm.extracted_texts) == 0
        assert dm.get_count() == 0
    
    def test_add_text_new_data(self, capsys):
        """新規データ追加のテスト"""
        dm = DataManager()
        
        # 新規データを追加
        result = dm.add_text("テストデータ1")
        assert result is True
        assert dm.get_count() == 1
        
        # ターミナル出力を確認
        captured = capsys.readouterr()
        assert "[新規データ検出]" in captured.out
        assert "テストデータ1" in captured.out
    
    def test_add_text_duplicate(self, capsys):
        """重複データのテスト"""
        dm = DataManager()
        
        # 最初の追加
        dm.add_text("重複テスト")
        assert dm.get_count() == 1
        
        # 重複データを追加
        result = dm.add_text("重複テスト")
        assert result is False
        assert dm.get_count() == 1  # 件数は変わらない
    
    def test_add_text_with_whitespace(self):
        """空白を含むテキストの正規化テスト"""
        dm = DataManager()
        
        # 前後に空白があるテキスト
        dm.add_text("  テスト  ")
        assert dm.get_count() == 1
        
        # 同じテキスト（空白なし）は重複として扱われる
        result = dm.add_text("テスト")
        assert result is False
        assert dm.get_count() == 1
    
    def test_add_text_empty_string(self):
        """空文字列のテスト"""
        dm = DataManager()
        
        # 空文字列
        result = dm.add_text("")
        assert result is False
        assert dm.get_count() == 0
        
        # 空白のみ
        result = dm.add_text("   ")
        assert result is False
        assert dm.get_count() == 0
        
        # None
        result = dm.add_text(None)
        assert result is False
        assert dm.get_count() == 0
    
    def test_export_to_csv_with_data(self, capsys):
        """データありのCSV出力テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"
            dm = DataManager(str(output_path))
            
            # データを追加
            dm.add_text("データ1")
            dm.add_text("データ2")
            dm.add_text("データ3")
            
            # CSV出力
            dm.export_to_csv()
            
            # ファイルが作成されたか確認
            assert output_path.exists()
            
            # CSVの内容を確認
            df = pd.read_csv(output_path)
            assert len(df) == 3
            assert "extracted_text" in df.columns
            assert set(df["extracted_text"]) == {"データ1", "データ2", "データ3"}
            
            # ターミナル出力を確認
            captured = capsys.readouterr()
            assert "CSVファイルを出力しました" in captured.out
            assert "3件" in captured.out
    
    def test_export_to_csv_no_data(self, capsys):
        """データなしのCSV出力テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"
            dm = DataManager(str(output_path))
            
            # データなしで出力
            dm.export_to_csv()
            
            # ファイルは作成されない
            assert not output_path.exists()
            
            # ターミナル出力を確認
            captured = capsys.readouterr()
            assert "データは抽出されませんでした" in captured.out
    
    def test_export_to_csv_creates_directory(self):
        """出力ディレクトリの自動作成テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "test_output.csv"
            dm = DataManager(str(output_path))
            
            # データを追加
            dm.add_text("テストデータ")
            
            # CSV出力（ディレクトリが自動作成される）
            dm.export_to_csv()
            
            # ファイルが作成されたか確認
            assert output_path.exists()
            assert output_path.parent.exists()
    
    def test_get_count(self):
        """データ件数取得のテスト"""
        dm = DataManager()
        
        assert dm.get_count() == 0
        
        dm.add_text("データ1")
        assert dm.get_count() == 1
        
        dm.add_text("データ2")
        assert dm.get_count() == 2
        
        # 重複は件数に含まれない
        dm.add_text("データ1")
        assert dm.get_count() == 2
    
    def test_csv_sorted_output(self):
        """CSV出力がソートされているかのテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"
            dm = DataManager(str(output_path))
            
            # 順不同でデータを追加
            dm.add_text("C")
            dm.add_text("A")
            dm.add_text("B")
            
            # CSV出力
            dm.export_to_csv()
            
            # CSVの内容を確認（ソートされているはず）
            df = pd.read_csv(output_path)
            assert list(df["extracted_text"]) == ["A", "B", "C"]
