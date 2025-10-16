"""
セッション管理モジュール

このモジュールは、OCR処理のセッション単位での画像管理を担当します。
タイムスタンプベースのフォルダ管理、画像の切り出し・保存、ZIP圧縮を提供します。
"""

from pathlib import Path
from typing import Optional
from datetime import datetime
import numpy as np
import cv2
import shutil
import subprocess

from src.object_detector import DetectionResult


class SessionManager:
    """
    セッション単位での画像管理を担当するクラス
    
    セッション開始時にタイムスタンプベースのフォルダを作成し、
    検出されたlist-item領域の画像を保存します。
    セッション終了時にはフォルダをZIP圧縮します。
    """
    
    def __init__(self, base_output_dir: str = "output/sessions"):
        """
        SessionManagerを初期化
        
        Args:
            base_output_dir: セッションフォルダの基底ディレクトリ（デフォルト: "output/sessions"）
        """
        self.base_output_dir = Path(base_output_dir)
        self.session_folder: Optional[Path] = None
        self.session_timestamp: Optional[str] = None
        self.image_counter = 0
    
    def start_session(self) -> Path:
        """
        新しいセッションを開始
        
        タイムスタンプ（YYYYMMDD_HHMMSS）を生成し、
        セッション専用フォルダを作成します。
        
        Returns:
            作成されたセッションフォルダのPath
        """
        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_folder = self.base_output_dir / self.session_timestamp
        self.session_folder.mkdir(parents=True, exist_ok=True)
        self.image_counter = 0
        print(f"📁 セッション開始: {self.session_folder}")
        return self.session_folder
    
    def save_list_item_image(
        self, 
        frame: np.ndarray, 
        bbox: DetectionResult, 
        margin: int = 5
    ) -> str:
        """
        list-item領域を切り出して保存
        
        指定されたbounding box領域をマージン付きで切り出し、
        一意のファイル名で保存します。
        
        Args:
            frame: 元画像（BGR形式のnumpy配列）
            bbox: list-itemのbounding box情報
            margin: 切り出し時に追加するマージン（ピクセル、デフォルト: 5）
        
        Returns:
            保存した画像の相対パス（例: "sessions/20251016_143022/list_item_001.jpg"）
        
        Raises:
            RuntimeError: セッションが開始されていない場合
        """
        if not self.session_folder:
            raise RuntimeError("セッションが開始されていません。start_session()を先に呼び出してください。")
        
        try:
            # マージン付きで切り出し座標を計算
            x1 = max(0, bbox.x1 - margin)
            y1 = max(0, bbox.y1 - margin)
            x2 = min(frame.shape[1], bbox.x2 + margin)
            y2 = min(frame.shape[0], bbox.y2 + margin)
            
            # 座標の妥当性チェック
            if x2 <= x1 or y2 <= y1:
                raise ValueError(
                    f"無効なbounding box座標: x1={x1}, y1={y1}, x2={x2}, y2={y2}"
                )
            
            # 画像を切り出し
            cropped = frame[y1:y2, x1:x2]
            
            # 切り出した画像が空でないかチェック
            if cropped.size == 0:
                raise ValueError("切り出した画像が空です")
            
            # 一意のファイル名を生成
            self.image_counter += 1
            filename = f"list_item_{self.image_counter:03d}.jpg"
            filepath = self.session_folder / filename
            
            # 画像を保存
            success = cv2.imwrite(str(filepath), cropped)
            if not success:
                raise IOError(f"画像の書き込みに失敗しました: {filepath}")
            
            # 相対パスを返す
            return f"sessions/{self.session_timestamp}/{filename}"
            
        except Exception as e:
            # 画像切り出し失敗時のエラーログ出力と処理継続
            print(f"❌ 画像切り出し・保存エラー: {e}")
            print(f"   bbox: ({bbox.x1}, {bbox.y1}, {bbox.x2}, {bbox.y2}), "
                  f"frame shape: {frame.shape}, margin: {margin}")
            # エラー時は空文字列を返して処理を継続
            return ""
    
    def end_session(self) -> Optional[Path]:
        """
        セッションを終了し、ZIP圧縮
        
        セッションフォルダ全体をZIPファイルに圧縮します。
        圧縮完了後、元のフォルダを削除することも可能です（オプション）。
        
        Returns:
            ZIPファイルのPath（圧縮成功時）、失敗時はNone
        """
        if not self.session_folder or not self.session_folder.exists():
            print("⚠️  セッションフォルダが存在しません")
            return None
        
        # ZIP圧縮
        zip_path = self.base_output_dir / f"{self.session_timestamp}.zip"
        print(f"🗜️  セッションフォルダを圧縮中: {zip_path}")
        
        try:
            # shutil.make_archiveを使用してZIP圧縮
            shutil.make_archive(
                str(zip_path.with_suffix('')),  # .zipを除いたパス
                'zip',
                self.session_folder
            )
            print(f"✅ 圧縮完了: {zip_path}")
            
            # 元のフォルダを削除（オプション、コメントアウト）
            # shutil.rmtree(self.session_folder)
            # print(f"🗑️  元のフォルダを削除: {self.session_folder}")
            
            return zip_path
        except Exception as e:
            print(f"❌ ZIP圧縮エラー: {e}")
            return None
    
    def open_session_folder(self) -> None:
        """
        セッションフォルダをFinderで開く（macOS専用）
        
        現在のセッションフォルダをmacOSのFinderで開きます。
        """
        if not self.session_folder or not self.session_folder.exists():
            print("⚠️  セッションフォルダが存在しません")
            return
        
        try:
            subprocess.run(["open", str(self.session_folder)], check=True)
            print(f"📂 Finderでフォルダを開きました: {self.session_folder}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Finderでフォルダを開けませんでした: {e}")
        except FileNotFoundError:
            print("❌ 'open'コマンドが見つかりません（macOS以外の環境では使用できません）")
