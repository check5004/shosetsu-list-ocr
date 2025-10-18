"""
データエディターウィンドウモジュール

このモジュールは、抽出されたレコードを表形式で表示し、
編集・削除・確定・ソート・フィルタリング機能を提供する
独立したウィンドウを実装します。
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, List
from dataclasses import dataclass
from pathlib import Path

from src.hierarchical_data_manager import HierarchicalDataManager, StructuredRecord
from src.record_table_manager import RecordTableManager
from src.csv_import_export import CSVImportExport
from src.duplicate_detection_modal import DuplicateDetectionModal


@dataclass
class EditAction:
    """
    編集アクション（Undo用）
    
    Attributes:
        timestamp: 編集タイムスタンプ
        record_id: レコードID
        field: 編集されたフィールド
        old_value: 編集前の値
        new_value: 編集後の値
    """
    timestamp: str
    record_id: str
    field: str
    old_value: str
    new_value: str


class DataEditorWindow:
    """
    データエディターウィンドウクラス
    
    抽出されたレコードを表形式で表示し、編集・削除・確定・
    ソート・フィルタリング機能を提供します。
    """
    
    def __init__(self, parent: tk.Tk, data_manager: HierarchicalDataManager):
        """
        DataEditorWindowを初期化
        
        Args:
            parent: 親ウィンドウ
            data_manager: データマネージャーへの参照
        """
        self.parent = parent
        self.data_manager = data_manager
        
        # Toplevelウィンドウを作成
        self.window = tk.Toplevel(parent)
        self.window.title("📊 データエディター")
        self.window.geometry("1200x700")
        
        # ダークモード対応の背景色を設定
        self.window.configure(bg='#2b2b2b')
        
        # コンポーネントの初期化
        self.table_manager = RecordTableManager(self.window, data_manager)
        self.csv_handler = CSVImportExport(data_manager)
        
        # UI components
        self.toolbar: Optional[ttk.Frame] = None
        self.filter_var: Optional[tk.StringVar] = None
        self.stats_labels: dict = {}
        
        # State
        self.current_filter: str = "all"
        self.current_sort_column: Optional[str] = None
        self.current_sort_direction: str = "asc"
        self.edit_history: List[EditAction] = []
        
        # UIをセットアップ
        self._setup_ui()
        
        # コールバックを設定
        self.table_manager.on_confirm_callback = self._on_confirm_with_duplicate_check
        self.table_manager.on_delete_callback = self._on_delete_refresh
        
        # 初期データを表示
        self.refresh_table()
        
        print("DataEditorWindow初期化完了")
    
    def _setup_ui(self) -> None:
        """
        UIコンポーネントをセットアップ
        """
        # ツールバーをセットアップ
        self.setup_toolbar()
        
        # テーブル表示エリアをセットアップ
        self._setup_table_area()
        
        # キーボードショートカットをセットアップ
        self._setup_keyboard_shortcuts()
        
        print("UI セットアップ完了")

    def setup_toolbar(self) -> None:
        """
        ツールバーを実装
        
        インポート・エクスポートボタン、フィルタードロップダウン、
        統計情報表示エリアを追加します。
        """
        # ツールバーフレームを作成
        self.toolbar = ttk.Frame(self.window)
        self.toolbar.pack(fill=tk.X, padx=10, pady=5)
        
        # 左側: インポート・エクスポートボタン
        left_frame = ttk.Frame(self.toolbar)
        left_frame.pack(side=tk.LEFT, fill=tk.X)
        
        ttk.Button(
            left_frame,
            text="📥 インポート",
            command=self.on_import_csv
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            left_frame,
            text="📤 エクスポート",
            command=self.on_export_csv
        ).pack(side=tk.LEFT, padx=2)
        
        # セパレーター
        ttk.Separator(left_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # フィルタードロップダウン
        ttk.Label(left_frame, text="フィルター:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.filter_var = tk.StringVar(value="all")
        filter_combo = ttk.Combobox(
            left_frame,
            textvariable=self.filter_var,
            values=["all", "error", "no_error", "unconfirmed"],
            state="readonly",
            width=15
        )
        filter_combo.pack(side=tk.LEFT, padx=2)
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self.on_filter_changed())
        
        # フィルター表示名のマッピング
        filter_combo.configure(values=[
            ("all", "すべて"),
            ("error", "エラーのみ"),
            ("no_error", "エラーなし"),
            ("unconfirmed", "未確認のみ")
        ])
        
        # 実際の値を設定
        filter_combo['values'] = ["all", "error", "no_error", "unconfirmed"]
        
        # セパレーター
        ttk.Separator(left_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Undoボタン
        ttk.Button(
            left_frame,
            text="↶ 元に戻す",
            command=self.on_undo
        ).pack(side=tk.LEFT, padx=2)
        
        # 右側: 統計情報表示エリア
        right_frame = ttk.Frame(self.toolbar)
        right_frame.pack(side=tk.RIGHT, fill=tk.X)
        
        # 統計情報ラベル
        stats_frame = ttk.Frame(right_frame)
        stats_frame.pack(side=tk.RIGHT)
        
        self.stats_labels['total'] = ttk.Label(stats_frame, text="総件数: 0")
        self.stats_labels['total'].pack(side=tk.LEFT, padx=5)
        
        self.stats_labels['confirmed'] = ttk.Label(stats_frame, text="確定: 0")
        self.stats_labels['confirmed'].pack(side=tk.LEFT, padx=5)
        
        self.stats_labels['error'] = ttk.Label(stats_frame, text="エラー: 0")
        self.stats_labels['error'].pack(side=tk.LEFT, padx=5)
        
        self.stats_labels['unconfirmed'] = ttk.Label(stats_frame, text="未確認: 0")
        self.stats_labels['unconfirmed'].pack(side=tk.LEFT, padx=5)
        
        print("ツールバーセットアップ完了")
    
    def _setup_table_area(self) -> None:
        """
        テーブル表示エリアを実装
        
        RecordTableManagerを統合し、テーブルを配置します。
        """
        # テーブルを作成
        self.table_manager.create_table()
        
        # 列ヘッダーのクリックイベントをバインド
        if self.table_manager.tree:
            for col in ['confirmed', 'title', 'progress', 'last_read_date', 'site_name', 'error_status']:
                self.table_manager.tree.heading(
                    col,
                    command=lambda c=col: self.on_column_header_click(c)
                )
        
        print("テーブル表示エリアセットアップ完了")
    
    def on_filter_changed(self) -> None:
        """
        フィルター変更処理
        
        フィルタータイプに応じてテーブルを更新し、
        フィルタリングされたレコード数を表示します。
        """
        if not self.filter_var:
            return
        
        # 現在のフィルターを更新
        self.current_filter = self.filter_var.get()
        
        # テーブルを更新
        self.refresh_table()
        
        # フィルタリングされたレコード数を表示
        filtered_count = len(self._get_filtered_records())
        total_count = len(self.data_manager.records)
        
        print(f"フィルター変更: {self.current_filter} ({filtered_count}/{total_count}件)")
    
    def on_column_header_click(self, column: str) -> None:
        """
        列ヘッダークリック処理（ソート）
        
        クリックされた列でソートし、ソート方向を切り替えます。
        現在のソート列と方向を視覚的に表示します。
        
        Args:
            column: クリックされた列名
        """
        # 同じ列の場合はソート方向を切り替え
        if self.current_sort_column == column:
            self.current_sort_direction = "desc" if self.current_sort_direction == "asc" else "asc"
        else:
            self.current_sort_column = column
            self.current_sort_direction = "asc"
        
        # テーブルを更新
        self.refresh_table()
        
        # ソート方向のインジケーターを更新
        self._update_sort_indicator()
        
        print(f"ソート: {column} ({self.current_sort_direction})")
    
    def _update_sort_indicator(self) -> None:
        """
        ソート方向のインジケーターを更新
        
        現在のソート列のヘッダーに矢印を表示します。
        """
        if not self.table_manager.tree or not self.current_sort_column:
            return
        
        # すべての列ヘッダーをリセット
        column_names = {
            'confirmed': '✓',
            'title': 'タイトル',
            'progress': '進捗',
            'last_read_date': '最終読書日',
            'site_name': 'サイト',
            'error_status': 'エラー',
            'actions': 'アクション'
        }
        
        for col, name in column_names.items():
            if col == self.current_sort_column:
                # ソート中の列に矢印を追加
                arrow = "↑" if self.current_sort_direction == "asc" else "↓"
                self.table_manager.tree.heading(col, text=f"{name} {arrow}")
            else:
                self.table_manager.tree.heading(col, text=name)
    
    def on_import_csv(self) -> None:
        """
        CSVインポート処理
        
        ファイル選択ダイアログを表示し、CSVファイルからレコードをインポートします。
        成功/失敗のフィードバックを表示します。
        """
        # ファイル選択ダイアログを表示
        filepath = filedialog.askopenfilename(
            title="CSVファイルを選択",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=Path("output").absolute()
        )
        
        if not filepath:
            return
        
        # 既存データがある場合は上書き確認
        overwrite = False
        if self.data_manager.records:
            result = messagebox.askyesnocancel(
                "既存データの処理",
                "既存のデータが存在します。\n\n"
                "「はい」: 既存データを上書き\n"
                "「いいえ」: インポートをキャンセル"
            )
            
            if result is None:  # キャンセル
                return
            
            overwrite = result
        
        # CSVをインポート
        success, message = self.csv_handler.import_from_csv(filepath, overwrite=overwrite)
        
        if success:
            # テーブルを更新
            self.refresh_table()
            messagebox.showinfo("インポート完了", message)
        else:
            messagebox.showerror("インポートエラー", message)
    
    def on_export_csv(self) -> None:
        """
        CSVエクスポート処理
        
        ファイル保存ダイアログを表示し、レコードをCSVファイルにエクスポートします。
        成功/失敗のフィードバックを表示します。
        """
        # デフォルトのファイル名を生成
        default_filename = self.data_manager.output_path.name
        
        # ファイル保存ダイアログを表示
        filepath = filedialog.asksaveasfilename(
            title="CSVファイルを保存",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=Path("output").absolute(),
            initialfile=default_filename
        )
        
        if not filepath:
            return
        
        # CSVをエクスポート
        success = self.csv_handler.export_to_csv(filepath)
        
        if success:
            messagebox.showinfo(
                "エクスポート完了",
                f"CSVファイルを保存しました:\n{filepath}"
            )
        else:
            messagebox.showerror(
                "エクスポートエラー",
                "CSVファイルの保存に失敗しました"
            )

    def _update_statistics(self) -> None:
        """
        統計情報表示を更新
        
        総レコード数、確定済み、エラー、未確認を表示します。
        リアルタイムで更新されます。
        """
        stats = self.data_manager.get_statistics()
        
        self.stats_labels['total'].config(text=f"総件数: {stats['total']}")
        self.stats_labels['confirmed'].config(text=f"確定: {stats['confirmed']}")
        self.stats_labels['error'].config(text=f"エラー: {stats['error']}")
        self.stats_labels['unconfirmed'].config(text=f"未確認: {stats['unconfirmed']}")
    
    def _setup_keyboard_shortcuts(self) -> None:
        """
        キーボードショートカットを実装
        
        削除（Delete）、編集（F2）、確定（Ctrl+Enter）などのショートカットを実装します。
        """
        # Deleteキー: 削除
        self.window.bind('<Delete>', lambda e: self._on_delete_shortcut())
        
        # F2キー: 編集（ダブルクリックと同じ動作）
        self.window.bind('<F2>', lambda e: self._on_edit_shortcut())
        
        # Ctrl+Enter: 確定
        self.window.bind('<Control-Return>', lambda e: self._on_confirm_shortcut())
        
        # Ctrl+Z: Undo
        self.window.bind('<Control-z>', lambda e: self.on_undo())
        
        print("キーボードショートカット設定完了")
    
    def _on_delete_shortcut(self) -> None:
        """
        Deleteキーショートカット処理
        """
        if self.table_manager.tree:
            selected = self.table_manager.tree.selection()
            if selected:
                self.table_manager.on_delete_click()
    
    def _on_edit_shortcut(self) -> None:
        """
        F2キーショートカット処理（編集開始）
        """
        if self.table_manager.tree:
            selected = self.table_manager.tree.selection()
            if len(selected) == 1:
                # 最初の編集可能な列（title）を編集
                item_id = selected[0]
                # ダブルクリックイベントをシミュレート
                # 実装の簡略化のため、メッセージを表示
                messagebox.showinfo(
                    "編集",
                    "セルをダブルクリックして編集してください"
                )
    
    def _on_confirm_shortcut(self) -> None:
        """
        Ctrl+Enterキーショートカット処理（確定）
        """
        if self.table_manager.tree:
            selected = self.table_manager.tree.selection()
            if len(selected) == 1:
                item_id = selected[0]
                self.table_manager.on_confirm_click(item_id)
    
    def on_undo(self) -> None:
        """
        Undo機能の実装
        
        EditActionを使用した編集履歴の管理を行い、
        最後の編集を取り消します。
        """
        if not self.edit_history:
            messagebox.showinfo("Undo", "元に戻す操作がありません")
            return
        
        # 最後の編集アクションを取得
        action = self.edit_history.pop()
        
        try:
            # 元の値に戻す
            self.data_manager.update_record(
                action.record_id,
                **{action.field: action.old_value}
            )
            
            # テーブルを更新
            self.refresh_table()
            
            print(f"Undo: {action.field} = '{action.old_value}'")
            
            messagebox.showinfo(
                "Undo完了",
                f"編集を取り消しました:\n{action.field} = '{action.old_value}'"
            )
            
        except Exception as e:
            messagebox.showerror("Undoエラー", f"編集の取り消しに失敗しました:\n{e}")
    
    def _on_confirm_with_duplicate_check(self, item_id: str) -> None:
        """
        確定処理（重複検出付き）
        
        類似レコードが存在する場合は重複検出モーダルを表示します。
        
        Args:
            item_id: 確定するアイテムID
        """
        # レコードを取得
        record = None
        for r in self.data_manager.records:
            if r.list_item_id == item_id:
                record = r
                break
        
        if not record:
            messagebox.showerror("エラー", "レコードが見つかりません")
            return
        
        # 類似レコードを検索
        similar_records = self.data_manager.find_similar_records(
            record.title,
            threshold=0.70
        )
        
        # 自分自身を除外
        similar_records = [(r, sim) for r, sim in similar_records if r.list_item_id != item_id]
        
        if similar_records:
            # 重複検出モーダルを表示
            modal = DuplicateDetectionModal(
                self.window,
                record,
                similar_records,
                self.data_manager
            )
            
            result = modal.show()
            
            if result:
                # 確定成功
                self.refresh_table()
                print(f"✅ レコード確定（重複削除あり）: {record.title}")
        else:
            # 類似レコードがない場合は直接確定
            try:
                self.data_manager.confirm_record(item_id)
                self.refresh_table()
                
                messagebox.showinfo(
                    "確定完了",
                    f"レコード「{record.title}」を確定しました。"
                )
                
                print(f"✅ レコード確定: {record.title}")
                
            except Exception as e:
                messagebox.showerror("エラー", f"確定に失敗しました:\n{e}")
    
    def _on_delete_refresh(self, item_id: str) -> None:
        """
        削除後のリフレッシュ処理
        
        Args:
            item_id: 削除されたアイテムID
        """
        # テーブルと統計情報を更新
        self.refresh_table()
    
    def refresh_table(self) -> None:
        """
        テーブル表示を更新
        
        現在のフィルターとソート設定を適用してテーブルを更新します。
        統計情報も更新します。
        """
        # フィルタリングされたレコードを取得
        filtered_records = self._get_filtered_records()
        
        # テーブルを更新
        self.table_manager.populate_table(
            records=filtered_records,
            filter_type=self.current_filter,
            sort_column=self.current_sort_column,
            sort_direction=self.current_sort_direction
        )
        
        # 統計情報を更新
        self._update_statistics()
        
        # ソートインジケーターを更新
        if self.current_sort_column:
            self._update_sort_indicator()
    
    def _get_filtered_records(self) -> List[StructuredRecord]:
        """
        フィルタリングされたレコードを取得
        
        Returns:
            フィルタリングされたレコードリスト
        """
        records = self.data_manager.records
        
        if self.current_filter == "all":
            return records
        elif self.current_filter == "error":
            return [r for r in records if r.error_status != "OK"]
        elif self.current_filter == "no_error":
            return [r for r in records if r.error_status == "OK"]
        elif self.current_filter == "unconfirmed":
            return [r for r in records if not r.confirmed]
        else:
            return records
