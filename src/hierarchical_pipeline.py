"""
階層的検出パイプラインモジュール

このモジュールは、階層的検出の全体フロー（検出 → 階層化 → OCR → 画像保存 → 
重複チェック → レコード追加）を統合し、エラーハンドリングを含む完全な
パイプライン処理を提供します。
"""

from typing import Optional
import numpy as np

from src.config import AppConfig
from src.hierarchical_detector import HierarchicalDetector
from src.hierarchical_ocr_processor import process_hierarchical_detection
from src.hierarchical_data_manager import HierarchicalDataManager
from src.session_manager import SessionManager
from src.ocr_processor import OCRProcessor


class HierarchicalPipeline:
    """
    階層的検出パイプラインクラス
    
    検出、階層化、OCR、画像保存、重複チェック、レコード追加の
    全体フローを統合し、エラーハンドリングを含む完全なパイプライン処理を提供します。
    
    使用例:
        config = AppConfig()
        pipeline = HierarchicalPipeline(config)
        pipeline.start()
        
        # フレーム処理ループ
        while True:
            frame = capture_frame()
            pipeline.process_frame(frame)
        
        pipeline.stop()
    """
    
    def __init__(self, config: AppConfig):
        """
        HierarchicalPipelineを初期化
        
        Args:
            config: アプリケーション設定
        """
        self.config = config
        
        # 各モジュールを初期化
        print("階層的検出パイプラインを初期化中...")
        
        try:
            # 階層的検出器を初期化
            self.detector = HierarchicalDetector(
                model_path=config.hierarchical_model_path,
                confidence_threshold=config.confidence_threshold,
                containment_threshold=config.containment_threshold
            )
            
            # OCRプロセッサを初期化
            self.ocr_processor = OCRProcessor(
                lang=config.ocr_lang,
                margin=config.ocr_margin,
                min_bbox_size=20
            )
            
            # データマネージャを初期化
            self.data_manager = HierarchicalDataManager(
                output_path=config.hierarchical_csv_output,
                similarity_threshold=config.similarity_threshold
            )
            
            # セッションマネージャを初期化
            self.session_manager = SessionManager(
                base_output_dir=config.session_output_dir
            )
            
            # パイプライン状態
            self.is_running = False
            self.frame_count = 0
            self.processed_count = 0
            
            print("✅ 階層的検出パイプラインの初期化が完了しました")
            
        except Exception as e:
            print(f"❌ パイプラインの初期化に失敗しました: {e}")
            raise
    
    def start(self) -> None:
        """
        パイプラインを開始
        
        セッションを開始し、パイプラインの状態を初期化します。
        """
        if self.is_running:
            print("⚠️  パイプラインは既に実行中です")
            return
        
        try:
            # セッションを開始
            self.session_manager.start_session()
            
            # 状態を初期化
            self.is_running = True
            self.frame_count = 0
            self.processed_count = 0
            
            print("🚀 階層的検出パイプラインを開始しました")
            
        except Exception as e:
            print(f"❌ パイプラインの開始に失敗しました: {e}")
            raise
    
    def process_frame(self, frame: np.ndarray) -> int:
        """
        フレームを処理
        
        全体フロー:
        1. 階層的検出を実行
        2. 各list-itemについて:
           a. 画像を切り出して保存
           b. OCR処理を実行
           c. 重複チェックを実行
           d. 新規データの場合、レコードを追加
        
        Args:
            frame: 入力フレーム（BGR形式のnumpy配列）
        
        Returns:
            処理されたlist-itemの数
        
        Raises:
            RuntimeError: パイプラインが開始されていない場合
        """
        if not self.is_running:
            raise RuntimeError(
                "パイプラインが開始されていません。start()を先に呼び出してください。"
            )
        
        self.frame_count += 1
        
        try:
            # 1. 階層的検出を実行
            hierarchical_results = self.detector.detect(frame)
            
            if not hierarchical_results:
                # 検出結果がない場合はスキップ
                return 0
            
            print(f"\n📊 フレーム {self.frame_count}: {len(hierarchical_results)}件のlist-itemを検出")
            
            # 2. 各list-itemについて処理
            new_records_count = 0
            
            for idx, hierarchical_result in enumerate(hierarchical_results):
                try:
                    # a. 画像を切り出して保存
                    image_path = self._save_list_item_image(
                        frame,
                        hierarchical_result
                    )
                    
                    # b. OCR処理を実行
                    ocr_texts = self._process_ocr(
                        frame,
                        hierarchical_result
                    )
                    
                    # c. 重複チェックとレコード追加
                    is_new = self.data_manager.add_record(
                        hierarchical_result,
                        ocr_texts,
                        image_path
                    )
                    
                    if is_new:
                        new_records_count += 1
                        self.processed_count += 1
                    
                except Exception as e:
                    # 個別のlist-item処理で予期しないエラーが発生しても継続
                    print(f"❌ list-item {idx + 1} の処理で予期しないエラーが発生（処理を継続）: {e}")
                    print(f"   エラー詳細: {type(e).__name__}")
                    print(f"   list_item_id: {hierarchical_result.list_item_id}")
                    continue
            
            if new_records_count > 0:
                print(f"✨ {new_records_count}件の新規データを追加しました（累計: {self.processed_count}件）")
            
            return new_records_count
            
        except Exception as e:
            # フレーム処理全体で予期しないエラーが発生した場合も処理を継続
            print(f"❌ フレーム {self.frame_count} の処理で予期しないエラーが発生（処理を継続）: {e}")
            print(f"   エラー詳細: {type(e).__name__}")
            import traceback
            print(f"   スタックトレース:\n{traceback.format_exc()}")
            return 0
    
    def _save_list_item_image(
        self,
        frame: np.ndarray,
        hierarchical_result
    ) -> str:
        """
        list-item領域を切り出して保存
        
        Args:
            frame: 元画像
            hierarchical_result: 階層的検出結果
        
        Returns:
            保存した画像の相対パス
        """
        try:
            image_path = self.session_manager.save_list_item_image(
                frame,
                hierarchical_result.list_item_bbox,
                margin=5
            )
            return image_path
            
        except Exception as e:
            # 画像保存エラー時はエラーログを出力して処理を継続
            print(f"❌ 画像保存エラー（処理を継続）: {e}")
            print(f"   list_item_id: {hierarchical_result.list_item_id}")
            # エラー時は空のパスを返す
            return ""
    
    def _process_ocr(
        self,
        frame: np.ndarray,
        hierarchical_result
    ) -> dict:
        """
        OCR処理を実行
        
        Args:
            frame: 元画像
            hierarchical_result: 階層的検出結果
        
        Returns:
            OCRで抽出されたテキストの辞書
        """
        try:
            ocr_texts = process_hierarchical_detection(
                frame,
                hierarchical_result,
                self.ocr_processor
            )
            return ocr_texts
            
        except Exception as e:
            # OCR処理エラー時は空文字列を返して処理を継続
            print(f"❌ OCR処理エラー（空文字列を返して処理を継続）: {e}")
            print(f"   list_item_id: {hierarchical_result.list_item_id}")
            return {
                'title': '',
                'progress': '',
                'last_read_date': '',
                'site_name': ''
            }
    
    def stop(self) -> None:
        """
        パイプラインを停止
        
        セッションを終了し、CSV出力を実行します。
        """
        if not self.is_running:
            print("⚠️  パイプラインは実行されていません")
            return
        
        try:
            print("\n🛑 階層的検出パイプラインを停止中...")
            
            # CSV出力を実行
            self.data_manager.export_to_csv()
            
            # セッションを終了（ZIP圧縮）
            self.session_manager.end_session()
            
            # 状態を更新
            self.is_running = False
            
            print(f"✅ パイプラインを停止しました（処理フレーム数: {self.frame_count}、新規レコード数: {self.processed_count}）")
            
        except Exception as e:
            print(f"❌ パイプラインの停止処理でエラーが発生: {e}")
            # エラーが発生しても状態は停止にする
            self.is_running = False
    
    def get_statistics(self) -> dict:
        """
        パイプラインの統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        return {
            'is_running': self.is_running,
            'frame_count': self.frame_count,
            'processed_count': self.processed_count,
            'total_records': len(self.data_manager.records),
            'error_records': len([
                r for r in self.data_manager.records
                if r.error_status != "OK"
            ])
        }
    
    def open_session_folder(self) -> None:
        """
        セッションフォルダをFinderで開く（macOS専用）
        """
        self.session_manager.open_session_folder()
