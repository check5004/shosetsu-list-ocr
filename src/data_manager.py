"""
Data management module for the real-time OCR application.

This module handles duplicate detection and CSV export of extracted text data.
"""

from pathlib import Path
from typing import Set, Callable, Optional
import pandas as pd


class DataManager:
    """
    抽出データの管理とCSV出力を担当するクラス。
    
    Setベースの重複管理により、O(1)の重複チェックを実現します。
    
    Attributes:
        output_path: 出力CSVファイルのパス
        extracted_texts: 抽出されたユニークなテキストのセット
        on_new_text_callback: 新規テキスト追加時のコールバック関数
    """
    
    def __init__(self, output_path: str = "book_data_realtime.csv", 
                 on_new_text_callback: Optional[Callable[[str], None]] = None):
        """
        DataManagerを初期化します。
        
        Args:
            output_path: 出力CSVファイルのパス（デフォルト: "book_data_realtime.csv"）
            on_new_text_callback: 新規テキスト追加時に呼び出されるコールバック関数
        """
        self.output_path = Path(output_path)
        self.extracted_texts: Set[str] = set()
        self.on_new_text_callback = on_new_text_callback
    
    def add_text(self, text: str) -> bool:
        """
        テキストを追加します（重複チェック付き）。
        
        新規データの場合はターミナルに出力し、コールバックを呼び出します。
        
        Args:
            text: 抽出されたテキスト
        
        Returns:
            新規データの場合True、重複の場合False
        """
        # 空文字列やNoneは無視
        if not text or not text.strip():
            return False
        
        # テキストを正規化（前後の空白を削除）
        normalized_text = text.strip()
        
        # 重複チェック（O(1)）
        if normalized_text in self.extracted_texts:
            return False
        
        # 新規データとして追加
        self.extracted_texts.add(normalized_text)
        
        # ターミナルに出力
        print(f"[新規データ検出] {normalized_text}")
        
        # コールバックを呼び出し
        if self.on_new_text_callback:
            try:
                self.on_new_text_callback(normalized_text)
            except Exception as e:
                print(f"[警告] コールバック実行エラー: {e}")
        
        return True
    
    def export_to_csv(self) -> None:
        """
        抽出されたデータをCSVファイルに出力します。
        
        pandasを使用してDataFrameを作成し、"extracted_text"列で出力します。
        データ件数も表示します。
        """
        count = self.get_count()
        
        if count == 0:
            print("\nデータは抽出されませんでした。")
            return
        
        # 出力ディレクトリが存在しない場合は作成
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # DataFrameを作成
        df = pd.DataFrame({
            'extracted_text': sorted(self.extracted_texts)  # ソートして出力
        })
        
        # CSVに出力
        df.to_csv(self.output_path, index=False, encoding='utf-8-sig')
        
        print(f"\nCSVファイルを出力しました: {self.output_path}")
        print(f"抽出されたデータ件数: {count}件")
    
    def get_count(self) -> int:
        """
        抽出されたユニークなテキストの数を取得します。
        
        Returns:
            データ件数
        """
        return len(self.extracted_texts)
