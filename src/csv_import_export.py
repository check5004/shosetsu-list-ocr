"""
CSV入出力ハンドラーモジュール

このモジュールは、HierarchicalDataManagerのレコードをCSVファイルに
エクスポート・インポートする機能を提供します。
"""

from typing import Optional, Tuple, List
from pathlib import Path
import pandas as pd

from src.hierarchical_data_manager import HierarchicalDataManager, StructuredRecord


class CSVImportExport:
    """
    CSV入出力ハンドラークラス
    
    HierarchicalDataManagerのレコードをCSVファイルにエクスポートし、
    CSVファイルからレコードをインポートする機能を提供します。
    確認ステータスを含むすべてのフィールドを保持します。
    """
    
    def __init__(self, data_manager: HierarchicalDataManager):
        """
        CSVImportExportを初期化
        
        Args:
            data_manager: データマネージャーへの参照
        """
        self.data_manager = data_manager
        
        # 必須列の定義
        self.required_columns = [
            'list_item_id',
            'title',
            'progress',
            'last_read_date',
            'site_name',
            'image_path',
            'error_status'
        ]
        
        # オプション列（確認ステータス）
        self.optional_columns = [
            'confirmed',
            'confirmed_at'
        ]
        
        print("CSVImportExport初期化完了")

    def export_to_csv(self, filepath: Optional[str] = None) -> bool:
        """
        CSVにエクスポート
        
        data_managerのレコードをCSVファイルにエクスポートします。
        確認ステータスを含むすべてのフィールドをエクスポートします。
        
        Args:
            filepath: 出力ファイルパス（Noneの場合はdata_managerのデフォルトパス使用）
        
        Returns:
            成功した場合True、失敗した場合False
        """
        try:
            # レコードが空の場合
            if not self.data_manager.records:
                print("⚠️  エクスポートするレコードがありません")
                return False
            
            # ファイルパスの決定
            if filepath is None:
                filepath = str(self.data_manager.output_path)
            
            output_path = Path(filepath)
            
            # DataFrameに変換
            df = pd.DataFrame([vars(record) for record in self.data_manager.records])
            
            # 出力ディレクトリを作成
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # CSV出力（UTF-8エンコーディング）
            df.to_csv(output_path, index=False, encoding='utf-8')
            
            # 統計情報を取得
            stats = self.data_manager.get_statistics()
            
            print(f"\n✅ CSVエクスポート完了: {output_path}")
            print(f"📊 エクスポート統計:")
            print(f"   - 総件数: {stats['total']}")
            print(f"   - 確定済み: {stats['confirmed']}")
            print(f"   - エラー: {stats['error']}")
            print(f"   - 未確認: {stats['unconfirmed']}")
            
            return True
            
        except Exception as e:
            print(f"❌ CSVエクスポートエラー: {e}")
            return False

    def validate_csv_format(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        CSV形式を検証
        
        読み込んだDataFrameが必須列を持ち、データ型が正しいかを検証します。
        
        Args:
            df: 読み込んだDataFrame
        
        Returns:
            (有効フラグ, エラーメッセージ)のタプル
            有効な場合は(True, "")、無効な場合は(False, エラーメッセージ)
        """
        # 必須列の存在確認
        missing_columns = []
        for col in self.required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            error_msg = f"必須列が不足しています: {', '.join(missing_columns)}"
            return False, error_msg
        
        # データ型の検証
        try:
            # list_item_idは文字列型
            if not df['list_item_id'].dtype == 'object':
                return False, "list_item_idは文字列型である必要があります"
            
            # title, progress, last_read_date, site_name, image_path, error_statusは文字列型
            string_columns = ['title', 'progress', 'last_read_date', 'site_name', 'image_path', 'error_status']
            for col in string_columns:
                if not df[col].dtype == 'object':
                    return False, f"{col}は文字列型である必要があります"
            
            # confirmedがある場合はブール型または文字列型（"True"/"False"）
            if 'confirmed' in df.columns:
                if df['confirmed'].dtype not in ['object', 'bool']:
                    return False, "confirmedはブール型または文字列型である必要があります"
            
            # confirmed_atがある場合は文字列型またはNone
            if 'confirmed_at' in df.columns:
                if not df['confirmed_at'].dtype == 'object':
                    return False, "confirmed_atは文字列型である必要があります"
            
        except Exception as e:
            return False, f"データ型検証エラー: {e}"
        
        # レコード数の確認
        if len(df) == 0:
            return False, "CSVファイルにレコードが含まれていません"
        
        return True, ""

    def import_from_csv(self, filepath: str, overwrite: bool = False) -> Tuple[bool, str]:
        """
        CSVからインポート
        
        CSVファイルからレコードを読み込み、data_managerに追加します。
        確認ステータスを含むすべてのフィールドを復元します。
        
        Args:
            filepath: 入力ファイルパス
            overwrite: 既存データを上書きするか（Trueの場合、既存データをクリア）
        
        Returns:
            (成功フラグ, メッセージ)のタプル
        """
        try:
            # ファイルの存在確認
            input_path = Path(filepath)
            if not input_path.exists():
                return False, f"ファイルが見つかりません: {filepath}"
            
            # CSVを読み込み
            df = pd.read_csv(input_path, encoding='utf-8')
            
            # CSV形式を検証
            is_valid, error_msg = self.validate_csv_format(df)
            if not is_valid:
                return False, f"CSV形式エラー: {error_msg}"
            
            # 既存データがある場合の処理
            if self.data_manager.records and not overwrite:
                return False, "既存データが存在します。上書きする場合はoverwrite=Trueを指定してください"
            
            # 上書きの場合、既存データをクリア
            if overwrite:
                self.data_manager.records.clear()
                self.data_manager.titles.clear()
                print("🔄 既存データをクリアしました")
            
            # レコードをインポート
            imported_count = 0
            for _, row in df.iterrows():
                # confirmedフィールドの処理（文字列からブール値に変換）
                confirmed = False
                if 'confirmed' in row:
                    confirmed_value = row['confirmed']
                    if isinstance(confirmed_value, bool):
                        confirmed = confirmed_value
                    elif isinstance(confirmed_value, str):
                        confirmed = confirmed_value.lower() in ['true', '1', 'yes']
                    elif pd.notna(confirmed_value):
                        confirmed = bool(confirmed_value)
                
                # confirmed_atフィールドの処理（NaNをNoneに変換）
                confirmed_at = None
                if 'confirmed_at' in row and pd.notna(row['confirmed_at']):
                    confirmed_at = str(row['confirmed_at'])
                
                # StructuredRecordを作成
                record = StructuredRecord(
                    list_item_id=str(row['list_item_id']),
                    title=str(row['title']) if pd.notna(row['title']) else '',
                    progress=str(row['progress']) if pd.notna(row['progress']) else '',
                    last_read_date=str(row['last_read_date']) if pd.notna(row['last_read_date']) else '',
                    site_name=str(row['site_name']) if pd.notna(row['site_name']) else '',
                    image_path=str(row['image_path']) if pd.notna(row['image_path']) else '',
                    error_status=str(row['error_status']) if pd.notna(row['error_status']) else 'OK',
                    confirmed=confirmed,
                    confirmed_at=confirmed_at
                )
                
                # レコードを追加
                self.data_manager.records.append(record)
                
                # タイトルリストに追加（重複チェック用）
                if record.title:
                    self.data_manager.titles.append(record.title)
                
                imported_count += 1
            
            success_msg = f"✅ CSVインポート完了: {imported_count}件のレコードをインポートしました"
            print(success_msg)
            
            # 統計情報を表示
            stats = self.data_manager.get_statistics()
            print(f"📊 インポート後の統計:")
            print(f"   - 総件数: {stats['total']}")
            print(f"   - 確定済み: {stats['confirmed']}")
            print(f"   - エラー: {stats['error']}")
            print(f"   - 未確認: {stats['unconfirmed']}")
            
            return True, success_msg
            
        except Exception as e:
            error_msg = f"CSVインポートエラー: {e}"
            print(f"❌ {error_msg}")
            return False, error_msg
