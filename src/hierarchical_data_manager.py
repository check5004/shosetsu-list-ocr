"""
階層的データ管理モジュール

このモジュールは、階層的検出結果から構造化されたレコードを管理し、
曖昧マッチングによる重複排除とCSV出力を行います。
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from difflib import SequenceMatcher
from datetime import datetime
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
        confirmed: 確認済みフラグ（ユーザーが確認済みとしてロックしたか）
        confirmed_at: 確認日時（ISO 8601形式、例: "2024-12-01T12:30:00"）
    """
    list_item_id: str
    title: str
    progress: str
    last_read_date: str
    site_name: str
    image_path: str
    error_status: str
    confirmed: bool = False
    confirmed_at: Optional[str] = None


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
        
        タイトルが空の場合は追加されません（必須条件）。
        
        Args:
            hierarchical_result: 階層的検出結果
            ocr_texts: OCRで抽出されたテキストの辞書
                      キー: 'title', 'progress', 'last_read_date', 'site_name'
            image_path: 切り出し画像の相対パス
        
        Returns:
            新規データとして追加された場合True、重複またはタイトルなしでスキップされた場合False
        """
        title = ocr_texts.get('title', '').strip()
        
        # タイトルが空の場合はスキップ（必須条件）
        if not title:
            print(f"⚠️  タイトルなしのためスキップ: {hierarchical_result.list_item_id}")
            return False
        
        # 曖昧マッチングで重複チェック
        if self._is_duplicate(title):
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
        self.titles.append(title)
        
        # 新規データ検出メッセージを表示
        print(f"✨ 新規データ検出: {title}")
        
        return True

    
    def export_to_csv(self) -> None:
        """
        構造化データをCSVファイルに出力
        
        pandasを使用してDataFrameを作成し、UTF-8エンコーディングで
        CSVファイルに出力します。出力後、統計情報（総件数、正常件数、
        エラー件数、確定済み件数）をターミナルに表示します。
        
        CSV列:
            - list_item_id: list-itemの一意識別子
            - title: タイトルテキスト
            - progress: 読書進捗テキスト
            - last_read_date: 最終読書日時テキスト
            - site_name: サイト名テキスト
            - image_path: 切り出し画像の相対パス
            - error_status: エラーステータス（"OK"または欠損フィールド名）
            - confirmed: 確認済みフラグ
            - confirmed_at: 確認日時（ISO 8601形式）
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
        stats = self.get_statistics()
        success = len([r for r in self.records if r.error_status == "OK"])
        
        # 統計情報を表示
        print(f"\n✅ CSV出力完了: {self.output_path}")
        print(f"📊 統計情報:")
        print(f"   - 総件数: {stats['total']}")
        print(f"   - 正常: {success}")
        print(f"   - エラー: {stats['error']}")
        print(f"   - 確定済み: {stats['confirmed']}")
        print(f"   - 未確認: {stats['unconfirmed']}")
        
        # エラーの内訳を表示
        if stats['error'] > 0:
            error_types = {}
            for record in self.records:
                if record.error_status != "OK":
                    error_types[record.error_status] = error_types.get(record.error_status, 0) + 1
            
            print(f"   エラー内訳:")
            for error_type, count in error_types.items():
                print(f"     - {error_type}: {count}件")

    
    def confirm_record(self, list_item_id: str) -> None:
        """
        レコードを確定
        
        指定されたlist_item_idのレコードを確認済みとしてマークし、
        確認日時を記録します。確定されたレコードは編集・削除から
        保護されます。
        
        Args:
            list_item_id: 確定するレコードのID
        
        Raises:
            ValueError: 指定されたIDのレコードが存在しない場合
        """
        for record in self.records:
            if record.list_item_id == list_item_id:
                record.confirmed = True
                record.confirmed_at = datetime.now().isoformat()
                print(f"✅ レコード確定: {record.title} (ID: {list_item_id})")
                return
        
        raise ValueError(f"レコードが見つかりません: {list_item_id}")

    
    def unconfirm_record(self, list_item_id: str) -> None:
        """
        レコードの確定を解除
        
        指定されたlist_item_idのレコードの確認済みフラグを解除し、
        編集・削除を可能にします。
        
        Args:
            list_item_id: 解除するレコードのID
        
        Raises:
            ValueError: 指定されたIDのレコードが存在しない場合
        """
        for record in self.records:
            if record.list_item_id == list_item_id:
                record.confirmed = False
                record.confirmed_at = None
                print(f"🔓 レコード確定解除: {record.title} (ID: {list_item_id})")
                return
        
        raise ValueError(f"レコードが見つかりません: {list_item_id}")

    
    def find_similar_records(
        self,
        title: str,
        threshold: Optional[float] = None
    ) -> List[Tuple[StructuredRecord, float]]:
        """
        類似レコードを検索
        
        指定されたタイトルと類似度の高いレコードを検索します。
        SequenceMatcherを使用して文字列類似度を計算し、
        しきい値以上の類似度を持つレコードを返します。
        
        Args:
            title: 検索するタイトル
            threshold: 類似度しきい値（Noneの場合はインスタンスのデフォルト値を使用）
        
        Returns:
            (レコード, 類似度)のタプルのリスト（類似度の降順でソート）
        """
        if not title:
            return []
        
        # しきい値が指定されていない場合はデフォルト値を使用
        if threshold is None:
            threshold = self.similarity_threshold
        
        similar_records = []
        
        for record in self.records:
            if not record.title:
                continue
            
            # 類似度を計算
            similarity = SequenceMatcher(None, title, record.title).ratio()
            
            # しきい値以上の場合、リストに追加
            if similarity >= threshold:
                similar_records.append((record, similarity))
        
        # 類似度の降順でソート
        similar_records.sort(key=lambda x: x[1], reverse=True)
        
        return similar_records

    
    def update_record(self, list_item_id: str, **kwargs) -> None:
        """
        レコードを更新
        
        指定されたlist_item_idのレコードの任意のフィールドを更新します。
        
        Args:
            list_item_id: 更新するレコードのID
            **kwargs: 更新するフィールドと値
                     (例: title="新しいタイトル", progress="50%")
        
        Raises:
            ValueError: 指定されたIDのレコードが存在しない場合、
                       または無効なフィールド名が指定された場合
        """
        for record in self.records:
            if record.list_item_id == list_item_id:
                # 有効なフィールドのみ更新
                valid_fields = {
                    'title', 'progress', 'last_read_date', 'site_name',
                    'image_path', 'error_status', 'confirmed', 'confirmed_at'
                }
                
                for field, value in kwargs.items():
                    if field not in valid_fields:
                        raise ValueError(f"無効なフィールド名: {field}")
                    
                    setattr(record, field, value)
                
                print(f"📝 レコード更新: {record.title} (ID: {list_item_id})")
                return
        
        raise ValueError(f"レコードが見つかりません: {list_item_id}")

    
    def delete_records(self, list_item_ids: List[str]) -> None:
        """
        複数レコードを一括削除
        
        指定されたlist_item_idのリストに対応するレコードを削除します。
        削除されたレコードのタイトルもtitlesリストから削除されます。
        
        Args:
            list_item_ids: 削除するレコードのIDリスト
        """
        deleted_count = 0
        
        for list_item_id in list_item_ids:
            # レコードを検索して削除
            for i, record in enumerate(self.records):
                if record.list_item_id == list_item_id:
                    # タイトルリストからも削除
                    if record.title in self.titles:
                        self.titles.remove(record.title)
                    
                    # レコードを削除
                    deleted_record = self.records.pop(i)
                    deleted_count += 1
                    print(f"🗑️  レコード削除: {deleted_record.title} (ID: {list_item_id})")
                    break
        
        if deleted_count > 0:
            print(f"✅ {deleted_count}件のレコードを削除しました")

    
    def get_statistics(self) -> Dict[str, int]:
        """
        統計情報を取得
        
        レコードの統計情報を計算して返します。
        
        Returns:
            統計情報の辞書:
                - total: 総レコード数
                - confirmed: 確定済みレコード数
                - error: エラーのあるレコード数
                - unconfirmed: 未確認レコード数
        """
        total = len(self.records)
        confirmed = len([r for r in self.records if r.confirmed])
        error = len([r for r in self.records if r.error_status != "OK"])
        unconfirmed = len([r for r in self.records if not r.confirmed])
        
        return {
            'total': total,
            'confirmed': confirmed,
            'error': error,
            'unconfirmed': unconfirmed
        }
