"""
重複検出モーダルモジュール

このモジュールは、レコード確定時に類似レコードを検出し、
ユーザーが重複を選択して一括削除できるモーダルダイアログを提供します。
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Tuple, Set, Optional

from src.hierarchical_data_manager import HierarchicalDataManager, StructuredRecord


class DuplicateDetectionModal:
    """
    重複検出モーダルダイアログ
    
    確定時に類似レコードを検出し、ユーザーが重複を選択して
    一括削除できるモーダルを表示します。
    
    Attributes:
        dialog: モーダルダイアログウィンドウ
        confirming_record: 確定するレコード
        similar_records: 類似レコードと類似度のリスト
        data_manager: データマネージャー
        selected_for_deletion: 削除対象として選択されたレコードIDのセット
        result: ユーザーの選択結果（確定: True, キャンセル: False, 未決定: None）
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        confirming_record: StructuredRecord,
        similar_records: List[Tuple[StructuredRecord, float]],
        data_manager: HierarchicalDataManager
    ):
        """
        重複検出モーダルを初期化
        
        Args:
            parent: 親ウィンドウ
            confirming_record: 確定するレコード
            similar_records: 類似レコードと類似度のタプルのリスト
            data_manager: データマネージャー
        """
        self.confirming_record = confirming_record
        self.similar_records = similar_records
        self.data_manager = data_manager
        
        # State
        self.selected_for_deletion: Set[str] = set()
        self.result: Optional[bool] = None
        
        # モーダルダイアログを作成
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("重複検出 - レコード確定")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # UI components（後で初期化）
        self.edit_frame: Optional[ttk.Frame] = None
        self.similar_list: Optional[ttk.Treeview] = None
        
        # 編集用の変数
        self.title_var = tk.StringVar(value=confirming_record.title)
        self.progress_var = tk.StringVar(value=confirming_record.progress)
        self.date_var = tk.StringVar(value=confirming_record.last_read_date)
        self.site_var = tk.StringVar(value=confirming_record.site_name)
        
        # UIをセットアップ
        self.setup_ui()
        
        # ウィンドウを中央に配置
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def setup_ui(self) -> None:
        """
        UIコンポーネントをセットアップ
        
        確定レコード編集エリア、類似レコードリスト、
        確定・キャンセルボタンを配置します。
        """
        # メインフレーム
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # タイトルラベル
        title_label = ttk.Label(
            main_frame,
            text="類似レコードが見つかりました",
            font=("TkDefaultFont", 12, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # 説明ラベル
        description_label = ttk.Label(
            main_frame,
            text="確定するレコードを編集し、削除する重複レコードを選択してください。",
            font=("TkDefaultFont", 9)
        )
        description_label.pack(pady=(0, 10))
        
        # 確定レコード編集エリア
        self._setup_edit_area(main_frame)
        
        # セパレーター
        separator = ttk.Separator(main_frame, orient=tk.HORIZONTAL)
        separator.pack(fill=tk.X, pady=10)
        
        # 類似レコードリスト
        self._setup_similar_list(main_frame)
        
        # ボタンエリア
        self._setup_buttons(main_frame)
    
    def _setup_edit_area(self, parent: ttk.Frame) -> None:
        """
        確定レコード編集エリアをセットアップ
        
        Args:
            parent: 親フレーム
        """
        # 編集エリアフレーム
        self.edit_frame = ttk.LabelFrame(
            parent,
            text="確定するレコード（編集可能）",
            padding="10"
        )
        self.edit_frame.pack(fill=tk.X, pady=(0, 10))
        
        # タイトル
        title_frame = ttk.Frame(self.edit_frame)
        title_frame.pack(fill=tk.X, pady=2)
        ttk.Label(title_frame, text="タイトル:", width=15).pack(side=tk.LEFT)
        title_entry = ttk.Entry(title_frame, textvariable=self.title_var)
        title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 進捗、日付、サイトを横並びに配置
        details_frame = ttk.Frame(self.edit_frame)
        details_frame.pack(fill=tk.X, pady=2)
        
        # 進捗
        progress_frame = ttk.Frame(details_frame)
        progress_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Label(progress_frame, text="進捗:", width=8).pack(side=tk.LEFT)
        progress_entry = ttk.Entry(progress_frame, textvariable=self.progress_var, width=15)
        progress_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 日付
        date_frame = ttk.Frame(details_frame)
        date_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Label(date_frame, text="日付:", width=8).pack(side=tk.LEFT)
        date_entry = ttk.Entry(date_frame, textvariable=self.date_var, width=15)
        date_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # サイト
        site_frame = ttk.Frame(details_frame)
        site_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(site_frame, text="サイト:", width=8).pack(side=tk.LEFT)
        site_entry = ttk.Entry(site_frame, textvariable=self.site_var, width=15)
        site_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _setup_similar_list(self, parent: ttk.Frame) -> None:
        """
        類似レコードリストをセットアップ
        
        Args:
            parent: 親フレーム
        """
        # リストフレーム
        list_frame = ttk.LabelFrame(
            parent,
            text="類似レコード（削除する項目を選択）",
            padding="10"
        )
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Treeviewを作成
        columns = ("title", "progress", "date", "site", "similarity")
        self.similar_list = ttk.Treeview(
            list_frame,
            columns=columns,
            show="tree headings",
            selectmode="none",
            height=8
        )
        
        # 列の設定
        self.similar_list.column("#0", width=30, stretch=False)
        self.similar_list.column("title", width=250, stretch=True)
        self.similar_list.column("progress", width=80, stretch=False)
        self.similar_list.column("date", width=100, stretch=False)
        self.similar_list.column("site", width=100, stretch=False)
        self.similar_list.column("similarity", width=80, stretch=False)
        
        # ヘッダーの設定
        self.similar_list.heading("#0", text="削除")
        self.similar_list.heading("title", text="タイトル")
        self.similar_list.heading("progress", text="進捗")
        self.similar_list.heading("date", text="日付")
        self.similar_list.heading("site", text="サイト")
        self.similar_list.heading("similarity", text="類似度")
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=self.similar_list.yview
        )
        self.similar_list.configure(yscrollcommand=scrollbar.set)
        
        # 配置
        self.similar_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 類似レコードを追加
        for record, similarity in self.similar_records:
            # デフォルトで選択状態にする（類似度が高いものは削除候補）
            is_selected = similarity >= 0.85
            
            item_id = self.similar_list.insert(
                "",
                tk.END,
                text="☑" if is_selected else "☐",
                values=(
                    record.title,
                    record.progress,
                    record.last_read_date,
                    record.site_name,
                    f"{similarity:.2f}"
                ),
                tags=(record.list_item_id,)
            )
            
            # デフォルトで選択されている場合は削除対象に追加
            if is_selected:
                self.selected_for_deletion.add(record.list_item_id)
        
        # クリックイベントをバインド
        self.similar_list.bind("<Button-1>", self._on_list_click)
    
    def _setup_buttons(self, parent: ttk.Frame) -> None:
        """
        ボタンエリアをセットアップ
        
        Args:
            parent: 親フレーム
        """
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X)
        
        # キャンセルボタン
        cancel_button = ttk.Button(
            button_frame,
            text="キャンセル",
            command=self.on_cancel,
            width=15
        )
        cancel_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 確定ボタン
        confirm_button = ttk.Button(
            button_frame,
            text="確定して削除",
            command=self.on_confirm,
            width=15
        )
        confirm_button.pack(side=tk.RIGHT)
        
        # 統計情報ラベル
        selected_count = len(self.selected_for_deletion)
        total_count = len(self.similar_records)
        stats_label = ttk.Label(
            button_frame,
            text=f"削除対象: {selected_count}/{total_count}件",
            font=("TkDefaultFont", 9)
        )
        stats_label.pack(side=tk.LEFT)
        
        # 統計情報を更新するための参照を保持
        self.stats_label = stats_label
    
    def _on_list_click(self, event) -> None:
        """
        リストクリック処理（チェックボックスのトグル）
        
        Args:
            event: クリックイベント
        """
        # クリックされた位置のアイテムを取得
        region = self.similar_list.identify_region(event.x, event.y)
        
        # ツリー列（チェックボックス）がクリックされた場合のみ処理
        if region == "tree":
            item_id = self.similar_list.identify_row(event.y)
            if item_id:
                # レコードIDを取得
                tags = self.similar_list.item(item_id, "tags")
                if tags:
                    record_id = tags[0]
                    
                    # 選択状態をトグル
                    if record_id in self.selected_for_deletion:
                        self.selected_for_deletion.remove(record_id)
                        self.similar_list.item(item_id, text="☐")
                    else:
                        self.selected_for_deletion.add(record_id)
                        self.similar_list.item(item_id, text="☑")
                    
                    # 統計情報を更新
                    self._update_stats()
    
    def _update_stats(self) -> None:
        """統計情報ラベルを更新"""
        selected_count = len(self.selected_for_deletion)
        total_count = len(self.similar_records)
        self.stats_label.config(text=f"削除対象: {selected_count}/{total_count}件")

    def on_confirm(self) -> None:
        """
        確定ボタン処理
        
        - 確定レコードの編集内容を保存
        - 選択された類似レコードを削除
        - 確定レコードをロック
        """
        try:
            # 編集内容を取得
            new_title = self.title_var.get().strip()
            new_progress = self.progress_var.get().strip()
            new_date = self.date_var.get().strip()
            new_site = self.site_var.get().strip()
            
            # タイトルが空の場合はエラー
            if not new_title:
                messagebox.showerror(
                    "入力エラー",
                    "タイトルは必須です。",
                    parent=self.dialog
                )
                return
            
            # 確定レコードを更新
            self.data_manager.update_record(
                self.confirming_record.list_item_id,
                title=new_title,
                progress=new_progress,
                last_read_date=new_date,
                site_name=new_site
            )
            
            # 選択された類似レコードを削除
            if self.selected_for_deletion:
                self.data_manager.delete_records(list(self.selected_for_deletion))
            
            # 確定レコードをロック
            self.data_manager.confirm_record(self.confirming_record.list_item_id)
            
            # 結果を設定
            self.result = True
            
            # ダイアログを閉じる
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror(
                "エラー",
                f"確定処理中にエラーが発生しました:\n{str(e)}",
                parent=self.dialog
            )
    
    def on_cancel(self) -> None:
        """
        キャンセルボタン処理
        
        確定をキャンセルし、ダイアログを閉じます。
        """
        self.result = False
        self.dialog.destroy()

    def show(self) -> bool:
        """
        モーダルを表示して結果を返す
        
        モーダルダイアログとして表示し、ユーザーが確定または
        キャンセルするまで待機します。
        
        Returns:
            確定された場合True、キャンセルされた場合False
        """
        # モーダルとして表示（親ウィンドウをブロック）
        self.dialog.wait_window()
        
        # 結果を返す（Noneの場合はFalseとして扱う）
        return self.result if self.result is not None else False
