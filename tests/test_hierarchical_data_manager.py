"""
Unit tests for the HierarchicalDataManager module.
"""

import pytest
from pathlib import Path
import tempfile
import pandas as pd
from src.hierarchical_data_manager import HierarchicalDataManager, StructuredRecord
from src.hierarchical_detector import HierarchicalDetectionResult
from src.object_detector import DetectionResult


class TestStructuredRecord:
    """StructuredRecordデータクラスのテスト"""
    
    def test_initialization(self):
        """初期化のテスト"""
        record = StructuredRecord(
            list_item_id="list_item_001",
            title="テストタイトル",
            progress="50%",
            last_read_date="2024-01-01",
            site_name="テストサイト",
            image_path="output/images/list_item_001.png",
            error_status="OK"
        )
        
        assert record.list_item_id == "list_item_001"
        assert record.title == "テストタイトル"
        assert record.progress == "50%"
        assert record.last_read_date == "2024-01-01"
        assert record.site_name == "テストサイト"
        assert record.image_path == "output/images/list_item_001.png"
        assert record.error_status == "OK"


class TestHierarchicalDataManager:
    """HierarchicalDataManagerクラスのテスト"""
    
    def test_initialization(self):
        """初期化のテスト"""
        dm = HierarchicalDataManager(
            output_path="test_output.csv",
            similarity_threshold=0.8
        )
        
        assert dm.output_path == Path("test_output.csv")
        assert dm.similarity_threshold == 0.8
        assert len(dm.records) == 0
        assert len(dm.titles) == 0
    
    def test_initialization_default_values(self):
        """デフォルト値での初期化テスト"""
        dm = HierarchicalDataManager()
        
        assert dm.output_path == Path("output/hierarchical_data.csv")
        assert dm.similarity_threshold == 0.75
    
    def test_is_duplicate_exact_match(self):
        """完全一致の重複チェックテスト"""
        dm = HierarchicalDataManager()
        dm.titles = ["転生したらスライムだった件"]
        
        # 完全一致は重複
        assert dm._is_duplicate("転生したらスライムだった件") is True
    
    def test_is_duplicate_similar_match(self):
        """類似文字列の重複チェックテスト"""
        dm = HierarchicalDataManager(similarity_threshold=0.75)
        dm.titles = ["転生したらスライムだった件"]
        
        # OCR誤認識を想定（「っ」→「つ」）
        assert dm._is_duplicate("転生したらスライムだつた件") is True
    
    def test_is_duplicate_different_text(self):
        """異なる文字列の重複チェックテスト"""
        dm = HierarchicalDataManager()
        dm.titles = ["転生したらスライムだった件"]
        
        # 全く異なるタイトルは重複ではない
        assert dm._is_duplicate("無職転生") is False
    
    def test_is_duplicate_empty_title(self):
        """空文字列の重複チェックテスト"""
        dm = HierarchicalDataManager()
        dm.titles = ["テストタイトル"]
        
        # 空文字列は重複ではない
        assert dm._is_duplicate("") is False
        assert dm._is_duplicate(None) is False
    
    def test_is_duplicate_threshold_sensitivity(self):
        """しきい値による重複判定の感度テスト"""
        # 厳しいしきい値（0.9）
        dm_strict = HierarchicalDataManager(similarity_threshold=0.9)
        dm_strict.titles = ["転生したらスライムだった件"]
        
        # 緩いしきい値（0.6）
        dm_loose = HierarchicalDataManager(similarity_threshold=0.6)
        dm_loose.titles = ["転生したらスライムだった件"]
        
        test_title = "転生したらスライム"
        
        # 厳しいしきい値では重複と判定されない可能性がある
        # 緩いしきい値では重複と判定される可能性が高い
        strict_result = dm_strict._is_duplicate(test_title)
        loose_result = dm_loose._is_duplicate(test_title)
        
        # 緩い方が重複と判定しやすい
        assert loose_result is True or strict_result is False
    
    def test_add_record_new_data(self, capsys):
        """新規レコード追加のテスト"""
        dm = HierarchicalDataManager()
        
        # HierarchicalDetectionResultを作成
        list_item = DetectionResult(
            x1=0, y1=0, x2=100, y2=100,
            confidence=0.9, class_id=0, class_name="list-item"
        )
        hierarchical_result = HierarchicalDetectionResult(
            list_item_id="list_item_001",
            list_item_bbox=list_item
        )
        hierarchical_result.title = DetectionResult(
            x1=10, y1=10, x2=90, y2=30,
            confidence=0.85, class_id=1, class_name="title"
        )
        
        ocr_texts = {
            'title': 'テストタイトル',
            'progress': '50%',
            'last_read_date': '2024-01-01',
            'site_name': 'テストサイト'
        }
        
        # レコードを追加
        result = dm.add_record(
            hierarchical_result,
            ocr_texts,
            "output/images/list_item_001.png"
        )
        
        assert result is True
        assert len(dm.records) == 1
        assert len(dm.titles) == 1
        assert dm.titles[0] == 'テストタイトル'
        
        # ターミナル出力を確認
        captured = capsys.readouterr()
        assert "新規データ検出" in captured.out
        assert "テストタイトル" in captured.out
    
    def test_add_record_duplicate(self, capsys):
        """重複レコードのテスト"""
        dm = HierarchicalDataManager()
        
        # 最初のレコード
        list_item1 = DetectionResult(
            x1=0, y1=0, x2=100, y2=100,
            confidence=0.9, class_id=0, class_name="list-item"
        )
        hierarchical_result1 = HierarchicalDetectionResult(
            list_item_id="list_item_001",
            list_item_bbox=list_item1
        )
        
        ocr_texts1 = {
            'title': '転生したらスライムだった件',
            'progress': '50%',
            'last_read_date': '2024-01-01',
            'site_name': 'テストサイト'
        }
        
        dm.add_record(hierarchical_result1, ocr_texts1, "image1.png")
        assert len(dm.records) == 1
        
        # 重複レコード（OCR誤認識を想定）
        list_item2 = DetectionResult(
            x1=0, y1=100, x2=100, y2=200,
            confidence=0.9, class_id=0, class_name="list-item"
        )
        hierarchical_result2 = HierarchicalDetectionResult(
            list_item_id="list_item_002",
            list_item_bbox=list_item2
        )
        
        ocr_texts2 = {
            'title': '転生したらスライムだつた件',  # 「っ」→「つ」
            'progress': '60%',
            'last_read_date': '2024-01-02',
            'site_name': 'テストサイト'
        }
        
        result = dm.add_record(hierarchical_result2, ocr_texts2, "image2.png")
        
        assert result is False
        assert len(dm.records) == 1  # 件数は変わらない
        
        # 重複検出メッセージを確認
        captured = capsys.readouterr()
        assert "重複検出" in captured.out
    
    def test_add_record_empty_title(self):
        """タイトルなしのレコード追加テスト"""
        dm = HierarchicalDataManager()
        
        list_item = DetectionResult(
            x1=0, y1=0, x2=100, y2=100,
            confidence=0.9, class_id=0, class_name="list-item"
        )
        hierarchical_result = HierarchicalDetectionResult(
            list_item_id="list_item_001",
            list_item_bbox=list_item
        )
        
        ocr_texts = {
            'title': '',  # タイトルなし
            'progress': '50%',
            'last_read_date': '2024-01-01',
            'site_name': 'テストサイト'
        }
        
        result = dm.add_record(hierarchical_result, ocr_texts, "image.png")
        
        # タイトルなしでも追加される
        assert result is True
        assert len(dm.records) == 1
        assert dm.records[0].title == ''
    
    def test_add_record_with_error_status(self):
        """エラーステータス付きレコードのテスト"""
        dm = HierarchicalDataManager()
        
        # titleが欠損しているHierarchicalDetectionResult
        list_item = DetectionResult(
            x1=0, y1=0, x2=100, y2=100,
            confidence=0.9, class_id=0, class_name="list-item"
        )
        hierarchical_result = HierarchicalDetectionResult(
            list_item_id="list_item_001",
            list_item_bbox=list_item
        )
        # titleはNone（欠損）
        hierarchical_result.last_read_date = DetectionResult(
            x1=10, y1=40, x2=90, y2=60,
            confidence=0.8, class_id=3, class_name="last_read_date"
        )
        hierarchical_result.site_name = DetectionResult(
            x1=10, y1=70, x2=90, y2=90,
            confidence=0.8, class_id=4, class_name="site_name"
        )
        
        ocr_texts = {
            'title': '',
            'progress': '',
            'last_read_date': '2024-01-01',
            'site_name': 'テストサイト'
        }
        
        result = dm.add_record(hierarchical_result, ocr_texts, "image.png")
        
        assert result is True
        assert dm.records[0].error_status == "missing_title"
    
    def test_export_to_csv_with_data(self, capsys):
        """データありのCSV出力テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"
            dm = HierarchicalDataManager(str(output_path))
            
            # テストデータを追加
            for i in range(3):
                list_item = DetectionResult(
                    x1=0, y1=i*100, x2=100, y2=(i+1)*100,
                    confidence=0.9, class_id=0, class_name="list-item"
                )
                hierarchical_result = HierarchicalDetectionResult(
                    list_item_id=f"list_item_{i+1:03d}",
                    list_item_bbox=list_item
                )
                hierarchical_result.title = DetectionResult(
                    x1=10, y1=10, x2=90, y2=30,
                    confidence=0.85, class_id=1, class_name="title"
                )
                hierarchical_result.last_read_date = DetectionResult(
                    x1=10, y1=40, x2=90, y2=60,
                    confidence=0.8, class_id=3, class_name="last_read_date"
                )
                hierarchical_result.site_name = DetectionResult(
                    x1=10, y1=70, x2=90, y2=90,
                    confidence=0.8, class_id=4, class_name="site_name"
                )
                
                # 類似度が低くなるように異なるタイトルを使用
                titles = ['転生したらスライムだった件', '無職転生', 'オーバーロード']
                ocr_texts = {
                    'title': titles[i],
                    'progress': f'{(i+1)*30}%',
                    'last_read_date': f'2024-01-0{i+1}',
                    'site_name': f'サイト{i+1}'
                }
                
                dm.add_record(
                    hierarchical_result,
                    ocr_texts,
                    f"output/images/list_item_{i+1:03d}.png"
                )
            
            # CSV出力
            dm.export_to_csv()
            
            # ファイルが作成されたか確認
            assert output_path.exists()
            
            # CSVの内容を確認
            df = pd.read_csv(output_path)
            assert len(df) == 3
            assert "list_item_id" in df.columns
            assert "title" in df.columns
            assert "progress" in df.columns
            assert "last_read_date" in df.columns
            assert "site_name" in df.columns
            assert "image_path" in df.columns
            assert "error_status" in df.columns
            
            # データの確認
            assert set(df["title"]) == {"転生したらスライムだった件", "無職転生", "オーバーロード"}
            assert all(df["error_status"] == "OK")
            
            # ターミナル出力を確認
            captured = capsys.readouterr()
            assert "CSV出力完了" in captured.out
            assert "総件数: 3" in captured.out
            assert "正常: 3" in captured.out
            assert "エラー: 0" in captured.out
    
    def test_export_to_csv_no_data(self, capsys):
        """データなしのCSV出力テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"
            dm = HierarchicalDataManager(str(output_path))
            
            # データなしで出力
            dm.export_to_csv()
            
            # ファイルは作成されない
            assert not output_path.exists()
            
            # ターミナル出力を確認
            captured = capsys.readouterr()
            assert "出力するデータがありません" in captured.out
    
    def test_export_to_csv_with_errors(self, capsys):
        """エラーありのCSV出力テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"
            dm = HierarchicalDataManager(str(output_path))
            
            # 正常なレコード
            list_item1 = DetectionResult(
                x1=0, y1=0, x2=100, y2=100,
                confidence=0.9, class_id=0, class_name="list-item"
            )
            hierarchical_result1 = HierarchicalDetectionResult(
                list_item_id="list_item_001",
                list_item_bbox=list_item1
            )
            hierarchical_result1.title = DetectionResult(
                x1=10, y1=10, x2=90, y2=30,
                confidence=0.85, class_id=1, class_name="title"
            )
            hierarchical_result1.last_read_date = DetectionResult(
                x1=10, y1=40, x2=90, y2=60,
                confidence=0.8, class_id=3, class_name="last_read_date"
            )
            hierarchical_result1.site_name = DetectionResult(
                x1=10, y1=70, x2=90, y2=90,
                confidence=0.8, class_id=4, class_name="site_name"
            )
            
            dm.add_record(
                hierarchical_result1,
                {'title': 'タイトル1', 'progress': '50%', 'last_read_date': '2024-01-01', 'site_name': 'サイト1'},
                "image1.png"
            )
            
            # エラーレコード（titleが欠損）
            list_item2 = DetectionResult(
                x1=0, y1=100, x2=100, y2=200,
                confidence=0.9, class_id=0, class_name="list-item"
            )
            hierarchical_result2 = HierarchicalDetectionResult(
                list_item_id="list_item_002",
                list_item_bbox=list_item2
            )
            # titleはNone
            hierarchical_result2.last_read_date = DetectionResult(
                x1=10, y1=40, x2=90, y2=60,
                confidence=0.8, class_id=3, class_name="last_read_date"
            )
            hierarchical_result2.site_name = DetectionResult(
                x1=10, y1=70, x2=90, y2=90,
                confidence=0.8, class_id=4, class_name="site_name"
            )
            
            dm.add_record(
                hierarchical_result2,
                {'title': '', 'progress': '', 'last_read_date': '2024-01-02', 'site_name': 'サイト2'},
                "image2.png"
            )
            
            # CSV出力
            dm.export_to_csv()
            
            # CSVの内容を確認
            df = pd.read_csv(output_path)
            assert len(df) == 2
            
            # エラーステータスの確認
            assert df.iloc[0]["error_status"] == "OK"
            assert df.iloc[1]["error_status"] == "missing_title"
            
            # ターミナル出力を確認
            captured = capsys.readouterr()
            assert "総件数: 2" in captured.out
            assert "正常: 1" in captured.out
            assert "エラー: 1" in captured.out
            assert "missing_title: 1件" in captured.out
    
    def test_export_to_csv_creates_directory(self):
        """出力ディレクトリの自動作成テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "test_output.csv"
            dm = HierarchicalDataManager(str(output_path))
            
            # テストデータを追加
            list_item = DetectionResult(
                x1=0, y1=0, x2=100, y2=100,
                confidence=0.9, class_id=0, class_name="list-item"
            )
            hierarchical_result = HierarchicalDetectionResult(
                list_item_id="list_item_001",
                list_item_bbox=list_item
            )
            hierarchical_result.title = DetectionResult(
                x1=10, y1=10, x2=90, y2=30,
                confidence=0.85, class_id=1, class_name="title"
            )
            hierarchical_result.last_read_date = DetectionResult(
                x1=10, y1=40, x2=90, y2=60,
                confidence=0.8, class_id=3, class_name="last_read_date"
            )
            hierarchical_result.site_name = DetectionResult(
                x1=10, y1=70, x2=90, y2=90,
                confidence=0.8, class_id=4, class_name="site_name"
            )
            
            dm.add_record(
                hierarchical_result,
                {'title': 'テスト', 'progress': '50%', 'last_read_date': '2024-01-01', 'site_name': 'サイト'},
                "image.png"
            )
            
            # CSV出力（ディレクトリが自動作成される）
            dm.export_to_csv()
            
            # ファイルが作成されたか確認
            assert output_path.exists()
            assert output_path.parent.exists()
