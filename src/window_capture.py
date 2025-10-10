"""
macOS専用ウィンドウキャプチャモジュール

このモジュールは、macOS環境で特定のウィンドウをリアルタイムでキャプチャする機能を提供します。
Quartzフレームワークを使用してウィンドウを検索し、mssライブラリでスクリーンキャプチャを実行します。
"""

from typing import Optional, List, Dict
import numpy as np
from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionAll, kCGNullWindowID
import mss


class WindowCapture:
    """
    macOS専用のウィンドウキャプチャクラス
    
    指定されたタイトルのウィンドウを検索し、そのウィンドウ領域をリアルタイムでキャプチャします。
    """
    
    def __init__(self, window_title: str):
        """
        WindowCaptureクラスの初期化
        
        Args:
            window_title: キャプチャ対象のウィンドウタイトル（部分一致）
        """
        self.window_title = window_title
        self.window_info: Optional[Dict] = None
        self.sct = mss.mss()
        
    def __del__(self):
        """デストラクタ: mssリソースをクリーンアップ"""
        if hasattr(self, 'sct'):
            self.sct.close()

    @staticmethod
    def list_all_windows() -> List[str]:
        """
        利用可能な全ウィンドウのタイトルを取得
        
        CGWindowListCopyWindowInfoを使用してmacOSの全ウィンドウ情報を取得し、
        タイトルを持つウィンドウのリストを返します。
        
        Returns:
            ウィンドウタイトルのリスト（重複なし）
        """
        window_list = CGWindowListCopyWindowInfo(
            kCGWindowListOptionAll,
            kCGNullWindowID
        )
        
        titles = []
        for window in window_list:
            title = window.get('kCGWindowName', '')
            owner = window.get('kCGWindowOwnerName', '')
            
            # タイトルが存在し、空でない場合のみ追加
            if title and title.strip():
                display_name = f"{title} ({owner})" if owner else title
                titles.append(display_name)
        
        # 重複を削除してソート
        return sorted(list(set(titles)))
    
    def find_window(self) -> Optional[Dict]:
        """
        指定されたタイトルのウィンドウを検索
        
        window_titleに部分一致するウィンドウを検索し、最初に見つかったウィンドウの
        情報（位置、サイズ）を返します。
        
        Returns:
            ウィンドウ情報（x, y, width, height）またはNone
            
        Raises:
            RuntimeError: ウィンドウが見つからない場合
        """
        window_list = CGWindowListCopyWindowInfo(
            kCGWindowListOptionAll,
            kCGNullWindowID
        )
        
        for window in window_list:
            title = window.get('kCGWindowName', '')
            
            # タイトルの部分一致検索（大文字小文字を区別しない）
            if title and self.window_title.lower() in title.lower():
                bounds = window.get('kCGWindowBounds', {})
                
                if bounds:
                    self.window_info = {
                        'x': int(bounds.get('X', 0)),
                        'y': int(bounds.get('Y', 0)),
                        'width': int(bounds.get('Width', 0)),
                        'height': int(bounds.get('Height', 0)),
                        'title': title,
                        'owner': window.get('kCGWindowOwnerName', '')
                    }
                    return self.window_info
        
        # ウィンドウが見つからない場合のエラーハンドリング
        available_windows = self.list_all_windows()
        error_msg = f"ウィンドウ '{self.window_title}' が見つかりません。\n\n"
        error_msg += "利用可能なウィンドウ:\n"
        
        if available_windows:
            for i, win_title in enumerate(available_windows[:20], 1):  # 最大20件表示
                error_msg += f"  {i}. {win_title}\n"
            if len(available_windows) > 20:
                error_msg += f"  ... 他 {len(available_windows) - 20} 件\n"
        else:
            error_msg += "  (ウィンドウが見つかりません)\n"
        
        raise RuntimeError(error_msg)

    def capture_frame(self) -> np.ndarray:
        """
        現在のウィンドウフレームをキャプチャ
        
        mssライブラリを使用してウィンドウ領域をキャプチャし、
        BGR形式のnumpy配列として返します。
        
        Returns:
            BGR形式のnumpy配列（OpenCV互換）
            
        Raises:
            RuntimeError: ウィンドウ情報が設定されていない場合
        """
        if self.window_info is None:
            raise RuntimeError(
                "ウィンドウ情報が設定されていません。先にfind_window()を呼び出してください。"
            )
        
        # ウィンドウ座標からモニター領域を計算
        monitor = {
            'left': self.window_info['x'],
            'top': self.window_info['y'],
            'width': self.window_info['width'],
            'height': self.window_info['height']
        }
        
        # スクリーンキャプチャを実行
        screenshot = self.sct.grab(monitor)
        
        # mssはBGRA形式で返すため、numpy配列に変換
        frame = np.array(screenshot)
        
        # BGRA → BGR変換（OpenCV互換形式）
        # BGRAの4チャンネルからBGRの3チャンネルに変換
        frame_bgr = frame[:, :, :3]  # アルファチャンネルを削除
        
        return frame_bgr
