"""
階層的データ管理モジュール

このモジュールは、階層的検出結果から構造化されたレコードを管理し、
曖昧マッチングによる重複排除とCSV出力を行います。
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path
from difflib import SequenceMatcher
import pandas as pd

from src.hierarchical_detector import HierarchicalDetectionResult


@dataclass
class StructuredRecord:
    """
    構造化されたレコードを表すデータクラス
    
    list-item単位で抽出されたデータを構造化して保持します。
    
    Attributes:
        list_item_id: list-itemの一意識別子
        title: タイトルテキスト
        progress: 読書進捗テキスト
        last_read_date: 最終読書日時テキスト
        site_name: サイト名テキスト
        image_path: 切り出し画像の相対パス
        error_status: エラーステータス（"OK"または欠損フィールド名）
    """
    list_item_id: str
    title: str
    progress: str
    last_read_date: str
    site_name: str
    image_path: str
    error_status: str


class HierarchicalDataManager:
    """
    階層的データ管理クラス
    
    階層的検出結果から構造化されたレコードを管理し、
    曖昧マッチングによる重複排除とCSV出力を行います。
    
    OCRの誤認識を考慮した文字列類似度ベースの重複チェックにより、
    同じ小説のデータが複数回保存されることを防ぎます。
    """
    
    def __init__(
        self,
        output_path: str = "output/hierarchical_data.csv",
        similarity_threshold: float = 0.75
    ):
        """
        HierarchicalDataManagerを初期化
        
        Args:
            output_path: 出力CSVファイルのパス（デフォルト: "output/hierarchical_data.csv"）
            similarity_threshold: 重複判定の類似度しきい値（0.0〜1.0、デフォルト: 0.75）
                                 この値以上の類似度を持つタイトルは重複と判定されます
        """
        self.output_path = Path(output_path)
        self.similarity_threshold = similarity_threshold
        self.records: List[StructuredRecord] = []
        self.titles: List[str] = []  # 曖昧マッチング用のタイトルリスト
        
        print(f"HierarchicalDataManager初期化:")
        print(f"  - 出力パス: {self.output_path}")
        print(f"  - 類似度しきい値: {self.similarity_threshold}")

    
    def _is_duplicate(self, title: str) -> bool:
        """
        曖昧マッチングで重複チェック
        
        difflib.SequenceMatcher を使用して文字列類似度を計算し、
        既存のタイトルと比較します。類似度がしきい値以上の場合、
        重複と判定します。
        
        OCRの誤認識（例: 「転生したらスライムだった件」と「転生したらスライムだつた件」）
        を考慮した柔軟な重複チェックを実現します。
        
        Args:
            title: チェックするタイトル文字列
        
        Returns:
            重複の場合True、新規の場合False
        """
        if not title:
            return False
        
        for existing_title in self.titles:
            # SequenceMatcherで類似度を計算
            similarity = SequenceMatcher(None, title, existing_title).ratio()
            
            # 類似度がしきい値以上の場合、重複と判定
            if similarity >= self.similarity_threshold:
                print(f"🔄 重複検出: '{title}' ≈ '{existing_title}' (類似度: {similarity:.2f})")
                return True
        
        return False

    
    def add_record(
        self,
        hierarchical_result: HierarchicalDetectionResult,
        ocr_texts: Dict[str, str],
        image_path: str
    ) -> bool:
        """
        レコードを追加（重複チェック付き）
        
        曖昧マッチングで重複チェックを実行し、新規データの場合のみ
        StructuredRecordを作成してリストに追加します。
        
        Args:
            hierarchical_result: 階層的検出結果
            ocr_texts: OCRで抽出されたテキストの辞書
                      キー: 'title', 'progress', 'last_read_date', 'site_name'
            image_path: 切り出し画像の相対パス
        
        Returns:
            新規データとして追加された場合True、重複でスキップされた場合False
        """
        title = ocr_texts.get('title', '')
        
        # 曖昧マッチングで重複チェック
        if title and self._is_duplicate(title):
            return False
        
        # StructuredRecordを作成
        record = StructuredRecord(
            list_item_id=hierarchical_result.list_item_id,
            title=title,
            progress=ocr_texts.get('progress', ''),
            last_read_date=ocr_texts.get('last_read_date', ''),
            site_name=ocr_texts.get('site_name', ''),
            image_path=image_path,
            error_status=hierarchical_result.get_error_status()
        )
        
        # レコードを追加
        self.records.append(record)
        
        # タイトルリストに追加（次回の重複チェック用）
        if title:
            self.titles.append(title)
        
        # 新規データ検出メッセージを表示
        print(f"✨ 新規データ検出: {title if title else '(タイトルなし)'}")
        
        return True

    
    def export_to_csv(self) -> None:
        """
        構造化データをCSVファイルに出力
        
        pandasを使用してDataFrameを作成し、UTF-8エンコーディングで
        CSVファイルに出力します。出力後、統計情報（総件数、正常件数、
        エラー件数）をターミナルに表示します。
        
        CSV列:
            - list_item_id: list-itemの一意識別子
            - title: タイトルテキスト
            - progress: 読書進捗テキスト
            - last_read_date: 最終読書日時テキスト
            - site_name: サイト名テキスト
            - image_path: 切り出し画像の相対パス
            - error_status: エラーステータス（"OK"または欠損フィールド名）
        """
        if not self.records:
            print("⚠️  出力するデータがありません")
            return
        
        # DataFrameに変換
        df = pd.DataFrame([vars(record) for record in self.records])
        
        # 出力ディレクトリを作成
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # CSV出力（UTF-8エンコーディング）
        df.to_csv(self.output_path, index=False, encoding='utf-8')
        
        # 統計情報を計算
        total = len(self.records)
        success = len([r for r in self.records if r.error_status == "OK"])
        errors = total - success
        
        # 統計情報を表示
        print(f"\n✅ CSV出力完了: {self.output_path}")
        print(f"📊 統計情報:")
        print(f"   - 総件数: {total}")
        print(f"   - 正常: {success}")
        print(f"   - エラー: {errors}")
        
        # エラーの内訳を表示
        if errors > 0:
            error_types = {}
            for record in self.records:
                if record.error_status != "OK":
                    error_types[record.error_status] = error_types.get(record.error_status, 0) + 1
            
            print(f"   エラー内訳:")
            for error_type, count in error_types.items():
                print(f"     - {error_type}: {count}件")
