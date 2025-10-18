"""
レコードテーブル管理モジュール

このモジュールは、抽出されたレコードをTreeviewテーブルで表示し、
インライン編集、削除、確定などの操作を提供します。
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional, Callable
from src.hierarchical_data_manager import HierarchicalDataManager, StructuredRecord


# 行の背景色定義（ダークモード対応）
COLORS = {
    'confirmed': '#2d4a2d',      # 暗い緑系（確定済み）
    'error': '#4a2d2d',          # 暗い赤系（エラー）
    'unconfirmed': '#4a4a2d',    # 暗い黄系（未確認）
    'normal': '#2b2b2b'          # ダークグレー（通常）
}

# テキスト色定義（ダークモード対応）
TEXT_COLORS = {
    'confirmed': '#90ee90',      # 明るい緑（確定済み）
    'error': '#ff6b6b',          # 明るい赤（エラー）
    'unconfirmed': '#ffd700',    # 明るい黄色（未確認）
    'normal': '#e0e0e0'          # 明るいグレー（通常）
}


class RecordTableManager:
    """
    レコードテーブル管理クラス
    
    Treeviewを使用したテーブル表示、インライン編集、
    行の選択・削除を管理します。
    """
    
    def __init__(self, parent: tk.Widget, data_manager: HierarchicalDataManager):
        """
        RecordTableManagerを初期化
        
        Args:
            parent: 親ウィジェット
            data_manager: データマネージャーへの参照
        """
        self.parent = parent
        self.data_manager = data_manager
        self.tree: Optional[ttk.Treeview] = None
        
        # インライン編集用の状態
        self.edit_entry: Optional[tk.Entry] = None
        self.editing_item: Optional[str] = None
        self.editing_column: Optional[str] = None
        
        # コールバック関数（外部から設定可能）
        self.on_confirm_callback: Optional[Callable[[str], None]] = None
        self.on_delete_callback: Optional[Callable[[str], None]] = None
        
        print("RecordTableManager初期化完了")

    def create_table(self) -> ttk.Treeview:
        """
        テーブルウィジェットを作成
        
        Treeviewウィジェットを作成し、列を定義してスクロールバーを追加します。
        
        列定義:
            - confirmed: 確認チェックボックス
            - title: タイトル
            - progress: 進捗
            - last_read_date: 最終読書日
            - site_name: サイト名
            - error_status: エラーステータス
            - actions: アクション（編集・削除ボタン）
        
        Returns:
            作成されたTreeviewウィジェット
        """
        # フレームを作成
        frame = ttk.Frame(self.parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 列定義
        columns = (
            'confirmed',
            'title',
            'progress',
            'last_read_date',
            'site_name',
            'error_status',
            'actions'
        )
        
        # ダークモード用のスタイルを設定
        style = ttk.Style()
        style.theme_use('default')
        
        # Treeviewのスタイルを設定
        style.configure(
            "Treeview",
            background=COLORS['normal'],
            foreground=TEXT_COLORS['normal'],
            fieldbackground=COLORS['normal'],
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading",
            background="#1e1e1e",
            foreground="#e0e0e0",
            borderwidth=1
        )
        style.map('Treeview', background=[('selected', '#404040')])
        
        # Treeviewを作成
        self.tree = ttk.Treeview(
            frame,
            columns=columns,
            show='headings',
            selectmode='extended'  # 複数選択を許可
        )
        
        # 列ヘッダーを設定
        self.tree.heading('confirmed', text='✓', anchor=tk.CENTER)
        self.tree.heading('title', text='タイトル', anchor=tk.W)
        self.tree.heading('progress', text='進捗', anchor=tk.CENTER)
        self.tree.heading('last_read_date', text='最終読書日', anchor=tk.CENTER)
        self.tree.heading('site_name', text='サイト', anchor=tk.CENTER)
        self.tree.heading('error_status', text='エラー', anchor=tk.CENTER)
        self.tree.heading('actions', text='アクション', anchor=tk.CENTER)
        
        # 列幅を設定
        self.tree.column('confirmed', width=40, minwidth=40, stretch=False)
        self.tree.column('title', width=300, minwidth=150)
        self.tree.column('progress', width=80, minwidth=60)
        self.tree.column('last_read_date', width=100, minwidth=80)
        self.tree.column('site_name', width=100, minwidth=80)
        self.tree.column('error_status', width=100, minwidth=80)
        self.tree.column('actions', width=150, minwidth=100)
        
        # 垂直スクロールバーを追加
        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        # 水平スクロールバーを追加
        hsb = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscrollcommand=hsb.set)
        
        # グリッド配置
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        # フレームのグリッド設定
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # イベントバインディング
        self.tree.bind('<Double-Button-1>', self.on_double_click)
        
        print("テーブルウィジェット作成完了")
        
        return self.tree

    def populate_table(
        self,
        records: Optional[List[StructuredRecord]] = None,
        filter_type: str = "all",
        sort_column: Optional[str] = None,
        sort_direction: str = "asc"
    ) -> None:
        """
        テーブルにレコードを表示
        
        フィルタリング、ソート、スタイリングを適用してレコードを表示します。
        
        Args:
            records: 表示するレコードリスト（Noneの場合はdata_managerから取得）
            filter_type: フィルタータイプ
                        - "all": すべて
                        - "error": エラーのみ
                        - "no_error": エラーなし
                        - "unconfirmed": 未確認のみ
            sort_column: ソート列名（None の場合はソートなし）
            sort_direction: ソート方向（"asc" または "desc"）
        """
        if self.tree is None:
            print("⚠️  テーブルが作成されていません")
            return
        
        # レコードを取得
        if records is None:
            records = self.data_manager.records
        
        # フィルタリング
        filtered_records = self._apply_filter(records, filter_type)
        
        # ソート
        if sort_column:
            filtered_records = self._apply_sort(filtered_records, sort_column, sort_direction)
        
        # テーブルをクリア
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # レコードを追加
        for record in filtered_records:
            self._insert_record(record)
        
        print(f"テーブル更新: {len(filtered_records)}件表示 (フィルター: {filter_type})")
    
    def _apply_filter(
        self,
        records: List[StructuredRecord],
        filter_type: str
    ) -> List[StructuredRecord]:
        """
        フィルタリングを適用
        
        Args:
            records: レコードリスト
            filter_type: フィルタータイプ
        
        Returns:
            フィルタリングされたレコードリスト
        """
        if filter_type == "all":
            return records
        elif filter_type == "error":
            return [r for r in records if r.error_status != "OK"]
        elif filter_type == "no_error":
            return [r for r in records if r.error_status == "OK"]
        elif filter_type == "unconfirmed":
            return [r for r in records if not r.confirmed]
        else:
            print(f"⚠️  不明なフィルタータイプ: {filter_type}")
            return records
    
    def _apply_sort(
        self,
        records: List[StructuredRecord],
        sort_column: str,
        sort_direction: str
    ) -> List[StructuredRecord]:
        """
        ソートを適用
        
        Args:
            records: レコードリスト
            sort_column: ソート列名
            sort_direction: ソート方向（"asc" または "desc"）
        
        Returns:
            ソートされたレコードリスト
        """
        # 列名をフィールド名にマッピング
        column_mapping = {
            'confirmed': 'confirmed',
            'title': 'title',
            'progress': 'progress',
            'last_read_date': 'last_read_date',
            'site_name': 'site_name',
            'error_status': 'error_status'
        }
        
        field_name = column_mapping.get(sort_column)
        if not field_name:
            print(f"⚠️  不明なソート列: {sort_column}")
            return records
        
        # ソート実行
        reverse = (sort_direction == "desc")
        try:
            sorted_records = sorted(
                records,
                key=lambda r: getattr(r, field_name) or "",
                reverse=reverse
            )
            return sorted_records
        except Exception as e:
            print(f"⚠️  ソートエラー: {e}")
            return records
    
    def _insert_record(self, record: StructuredRecord) -> None:
        """
        レコードをテーブルに挿入
        
        Args:
            record: 挿入するレコード
        """
        # 確認チェックマーク
        confirmed_mark = '✓' if record.confirmed else ''
        
        # エラーステータスの表示
        error_display = 'OK' if record.error_status == 'OK' else record.error_status
        
        # アクションボタンの表示（テキストのみ）
        actions = '編集 | 削除 | 確定'
        
        # 行を挿入
        item_id = self.tree.insert(
            '',
            tk.END,
            iid=record.list_item_id,
            values=(
                confirmed_mark,
                record.title,
                record.progress,
                record.last_read_date,
                record.site_name,
                error_display,
                actions
            )
        )
        
        # 行のスタイリングを適用
        self.apply_row_styling(item_id, record)

    def on_double_click(self, event) -> None:
        """
        セルダブルクリック処理（インライン編集開始）
        
        ダブルクリックされたセルのインライン編集を開始します。
        確定済みレコードの編集は防止されます。
        
        Args:
            event: クリックイベント
        """
        if self.tree is None:
            return
        
        # クリック位置のアイテムと列を取得
        region = self.tree.identify_region(event.x, event.y)
        if region != 'cell':
            return
        
        item_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        
        if not item_id or not column:
            return
        
        # 列インデックスを取得（#1, #2, ... の形式）
        column_index = int(column.replace('#', '')) - 1
        column_names = ['confirmed', 'title', 'progress', 'last_read_date', 'site_name', 'error_status', 'actions']
        
        if column_index < 0 or column_index >= len(column_names):
            return
        
        column_name = column_names[column_index]
        
        # 編集不可の列をチェック
        if column_name in ['confirmed', 'error_status', 'actions']:
            # actionsカラムの場合、クリック位置に応じて処理
            if column_name == 'actions':
                self._handle_action_click(item_id, event)
            return
        
        # レコードを取得
        record = self._get_record_by_id(item_id)
        if not record:
            return
        
        # 確定済みレコードの編集を防止
        if record.confirmed:
            messagebox.showwarning(
                "編集不可",
                "確定済みレコードは編集できません。\n編集するには、まず確定を解除してください。"
            )
            return
        
        # 既存の編集エントリーがあれば削除
        if self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None
        
        # セルの位置とサイズを取得
        x, y, width, height = self.tree.bbox(item_id, column)
        
        # 現在の値を取得
        current_value = self.tree.set(item_id, column_name)
        
        # 編集用のEntryウィジェットを作成
        self.edit_entry = tk.Entry(self.tree)
        self.edit_entry.insert(0, current_value)
        self.edit_entry.select_range(0, tk.END)
        self.edit_entry.focus()
        
        # 編集状態を保存
        self.editing_item = item_id
        self.editing_column = column_name
        
        # イベントバインディング
        self.edit_entry.bind('<Return>', self.on_edit_complete)
        self.edit_entry.bind('<Escape>', lambda e: self._cancel_edit())
        self.edit_entry.bind('<FocusOut>', self.on_edit_complete)
        
        # Entryを配置
        self.edit_entry.place(x=x, y=y, width=width, height=height)
        
        print(f"編集開始: {column_name} = '{current_value}'")
    
    def on_edit_complete(self, event) -> None:
        """
        編集完了処理
        
        編集された値を検証し、データマネージャーに保存します。
        
        Args:
            event: イベント
        """
        if not self.edit_entry or not self.editing_item or not self.editing_column:
            return
        
        # 新しい値を取得
        new_value = self.edit_entry.get().strip()
        
        # レコードを取得
        record = self._get_record_by_id(self.editing_item)
        if not record:
            self._cancel_edit()
            return
        
        # 値の検証
        if self.editing_column == 'title' and not new_value:
            messagebox.showerror("入力エラー", "タイトルは空にできません")
            self.edit_entry.focus()
            return
        
        # データマネージャーを更新
        try:
            self.data_manager.update_record(
                self.editing_item,
                **{self.editing_column: new_value}
            )
            
            # テーブル表示を更新
            self.tree.set(self.editing_item, self.editing_column, new_value)
            
            print(f"編集完了: {self.editing_column} = '{new_value}'")
            
        except Exception as e:
            messagebox.showerror("更新エラー", f"レコードの更新に失敗しました:\n{e}")
        
        # 編集エントリーを削除
        self._cancel_edit()
    
    def _cancel_edit(self) -> None:
        """
        編集をキャンセル
        """
        if self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None
        
        self.editing_item = None
        self.editing_column = None
    
    def _handle_action_click(self, item_id: str, event) -> None:
        """
        アクション列のクリック処理
        
        クリック位置に応じて、編集・削除・確定のいずれかを実行します。
        
        Args:
            item_id: アイテムID
            event: クリックイベント
        """
        # 簡易的な実装: 列全体のクリックで確定を実行
        # より詳細な実装は後で追加可能
        self.on_confirm_click(item_id)
    
    def _get_record_by_id(self, list_item_id: str) -> Optional[StructuredRecord]:
        """
        IDからレコードを取得
        
        Args:
            list_item_id: レコードID
        
        Returns:
            レコード（見つからない場合はNone）
        """
        for record in self.data_manager.records:
            if record.list_item_id == list_item_id:
                return record
        return None

    def on_delete_click(self, item_id: Optional[str] = None) -> None:
        """
        削除ボタンクリック処理
        
        選択されたレコードを削除します。確定済みレコードの削除は防止されます。
        複数選択削除もサポートします。
        
        Args:
            item_id: 削除するアイテムID（Noneの場合は選択中のアイテムを削除）
        """
        if self.tree is None:
            return
        
        # 削除対象のアイテムIDを取得
        if item_id:
            item_ids = [item_id]
        else:
            item_ids = self.tree.selection()
        
        if not item_ids:
            messagebox.showwarning("選択なし", "削除するレコードを選択してください")
            return
        
        # 確定済みレコードのチェック
        confirmed_records = []
        deletable_records = []
        
        for iid in item_ids:
            record = self._get_record_by_id(iid)
            if record:
                if record.confirmed:
                    confirmed_records.append(record.title)
                else:
                    deletable_records.append(iid)
        
        # 確定済みレコードがある場合は警告
        if confirmed_records:
            messagebox.showwarning(
                "削除不可",
                f"以下の確定済みレコードは削除できません:\n\n" +
                "\n".join(f"- {title}" for title in confirmed_records[:5]) +
                (f"\n... 他{len(confirmed_records) - 5}件" if len(confirmed_records) > 5 else "") +
                "\n\n削除するには、まず確定を解除してください。"
            )
        
        if not deletable_records:
            return
        
        # 削除確認ダイアログ
        count = len(deletable_records)
        message = f"{count}件のレコードを削除しますか？\n\nこの操作は取り消せません。"
        
        if count <= 3:
            # 3件以下の場合はタイトルを表示
            titles = []
            for iid in deletable_records:
                record = self._get_record_by_id(iid)
                if record:
                    titles.append(record.title or "(タイトルなし)")
            message += "\n\n削除対象:\n" + "\n".join(f"- {t}" for t in titles)
        
        result = messagebox.askyesno("削除確認", message)
        
        if not result:
            return
        
        # データマネージャーから削除
        try:
            self.data_manager.delete_records(deletable_records)
            
            # テーブルから削除
            for iid in deletable_records:
                self.tree.delete(iid)
            
            print(f"✅ {count}件のレコードを削除しました")
            
            # コールバックを呼び出し
            if self.on_delete_callback:
                for iid in deletable_records:
                    self.on_delete_callback(iid)
            
        except Exception as e:
            messagebox.showerror("削除エラー", f"レコードの削除に失敗しました:\n{e}")

    def on_confirm_click(self, item_id: str) -> None:
        """
        確定ボタンクリック処理
        
        レコードを確定します。類似レコードが存在する場合は
        重複検出モーダルを表示します。
        
        Args:
            item_id: 確定するアイテムID
        """
        if self.tree is None:
            return
        
        # レコードを取得
        record = self._get_record_by_id(item_id)
        if not record:
            messagebox.showerror("エラー", "レコードが見つかりません")
            return
        
        # 既に確定済みの場合
        if record.confirmed:
            # 確定解除の確認
            result = messagebox.askyesno(
                "確定解除",
                f"レコード「{record.title}」の確定を解除しますか？\n\n"
                "確定を解除すると、編集・削除が可能になります。"
            )
            
            if result:
                try:
                    self.data_manager.unconfirm_record(item_id)
                    
                    # テーブル表示を更新
                    self.tree.set(item_id, 'confirmed', '')
                    self.apply_row_styling(item_id, record)
                    
                    print(f"🔓 確定解除: {record.title}")
                    
                except Exception as e:
                    messagebox.showerror("エラー", f"確定解除に失敗しました:\n{e}")
            
            return
        
        # 類似レコードを検索
        similar_records = self.data_manager.find_similar_records(
            record.title,
            threshold=0.70  # 確定時は少し低めのしきい値を使用
        )
        
        # 自分自身を除外
        similar_records = [(r, sim) for r, sim in similar_records if r.list_item_id != item_id]
        
        # 類似レコードが存在する場合
        if similar_records:
            print(f"🔍 類似レコード検出: {len(similar_records)}件")
            
            # コールバックを呼び出し（重複検出モーダルを表示）
            if self.on_confirm_callback:
                self.on_confirm_callback(item_id)
            else:
                # コールバックが設定されていない場合は直接確定
                self._confirm_record_directly(item_id, record)
        else:
            # 類似レコードがない場合は直接確定
            self._confirm_record_directly(item_id, record)
    
    def _confirm_record_directly(self, item_id: str, record: StructuredRecord) -> None:
        """
        レコードを直接確定（重複検出なし）
        
        Args:
            item_id: アイテムID
            record: レコード
        """
        try:
            self.data_manager.confirm_record(item_id)
            
            # テーブル表示を更新
            self.tree.set(item_id, 'confirmed', '✓')
            self.apply_row_styling(item_id, record)
            
            print(f"✅ レコード確定: {record.title}")
            
            messagebox.showinfo(
                "確定完了",
                f"レコード「{record.title}」を確定しました。\n\n"
                "確定されたレコードは編集・削除から保護されます。"
            )
            
        except Exception as e:
            messagebox.showerror("エラー", f"確定に失敗しました:\n{e}")

    def apply_row_styling(self, item_id: str, record: StructuredRecord) -> None:
        """
        行のスタイリングを適用
        
        レコードの状態に応じて背景色を設定します：
        - 確定済み: 緑系
        - エラー: 赤系
        - 未確認: 黄系
        - 通常: 白
        
        Args:
            item_id: TreeviewアイテムID
            record: レコードデータ
        """
        if self.tree is None:
            return
        
        # 優先順位: 確定済み > エラー > 未確認 > 通常
        if record.confirmed:
            tag = 'confirmed'
        elif record.error_status != 'OK':
            tag = 'error'
        elif not record.confirmed:
            tag = 'unconfirmed'
        else:
            tag = 'normal'
        
        # タグを設定
        self.tree.item(item_id, tags=(tag,))
        
        # タグの色を設定（初回のみ）
        if not hasattr(self, '_tags_configured'):
            self._configure_tags()
            self._tags_configured = True
    
    def _configure_tags(self) -> None:
        """
        タグの色設定を行う
        """
        if self.tree is None:
            return
        
        self.tree.tag_configure('confirmed', background=COLORS['confirmed'], foreground=TEXT_COLORS['confirmed'])
        self.tree.tag_configure('error', background=COLORS['error'], foreground=TEXT_COLORS['error'])
        self.tree.tag_configure('unconfirmed', background=COLORS['unconfirmed'], foreground=TEXT_COLORS['unconfirmed'])
        self.tree.tag_configure('normal', background=COLORS['normal'], foreground=TEXT_COLORS['normal'])
        
        print("行スタイリング設定完了")
