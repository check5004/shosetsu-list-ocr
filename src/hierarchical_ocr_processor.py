"""
階層的検出結果に対するOCR処理モジュール

このモジュールは、HierarchicalDetectorで検出された各子要素
（title、progress、last_read_date、site_name）に対してOCR処理を実行し、
テキストを抽出します。
"""

from typing import Dict, List
import numpy as np
from src.hierarchical_detector import HierarchicalDetectionResult
from src.ocr_processor import OCRProcessor


def process_hierarchical_detection(
    frame: np.ndarray,
    hierarchical_result: HierarchicalDetectionResult,
    ocr_processor: OCRProcessor
) -> Dict[str, str]:
    """
    階層的検出結果に対してOCR処理を実行
    
    各子要素（title、progress、last_read_date、site_name）のbounding boxに対して
    OCR処理を実行し、抽出されたテキストを辞書形式で返します。
    
    Args:
        frame: 元画像（BGR形式のnumpy配列）
        hierarchical_result: 階層的検出結果
        ocr_processor: OCRProcessorインスタンス
    
    Returns:
        各子要素のテキストを含む辞書
        例: {'title': '転生したらスライムだった件', 'progress': '38/768', ...}
        検出されなかった要素やOCRエラー時は空文字列
    """
    ocr_texts = {
        'title': '',
        'progress': '',
        'last_read_date': '',
        'site_name': ''
    }
    
    # 各子要素に対してOCR処理を実行
    child_elements = [
        ('title', hierarchical_result.title),
        ('progress', hierarchical_result.progress),
        ('last_read_date', hierarchical_result.last_read_date),
        ('site_name', hierarchical_result.site_name)
    ]
    
    for element_name, detection_result in child_elements:
        if detection_result is not None:
            try:
                # OCR処理を実行
                text = ocr_processor.extract_text(frame, detection_result)
                ocr_texts[element_name] = text
                
                # デバッグ情報（空でない場合のみ）
                if text:
                    print(f"  {element_name}: {text}")
                    
            except Exception as e:
                # OCR処理エラー時は空文字列を返して処理を継続
                print(f"❌ {element_name}のOCR処理でエラーが発生（空文字列を返して処理を継続）: {e}")
                print(f"   bbox: ({detection_result.x1}, {detection_result.y1}, "
                      f"{detection_result.x2}, {detection_result.y2})")
                ocr_texts[element_name] = ''
        else:
            # 検出されなかった要素は空文字列
            ocr_texts[element_name] = ''
    
    return ocr_texts


def process_hierarchical_detections_batch(
    frame: np.ndarray,
    hierarchical_results: List[HierarchicalDetectionResult],
    ocr_processor: OCRProcessor
) -> List[Dict[str, str]]:
    """
    複数の階層的検出結果に対してOCR処理を一括実行
    
    Args:
        frame: 元画像（BGR形式のnumpy配列）
        hierarchical_results: 階層的検出結果のリスト
        ocr_processor: OCRProcessorインスタンス
    
    Returns:
        各検出結果のOCRテキスト辞書のリスト
    """
    ocr_results = []
    
    for idx, hierarchical_result in enumerate(hierarchical_results):
        print(f"\n📖 list-item {idx + 1}/{len(hierarchical_results)} のOCR処理中...")
        
        try:
            ocr_texts = process_hierarchical_detection(
                frame,
                hierarchical_result,
                ocr_processor
            )
            ocr_results.append(ocr_texts)
            
        except Exception as e:
            # 予期しないエラーが発生した場合も処理を継続
            print(f"❌ list-item {idx + 1} の処理で予期しないエラーが発生（処理を継続）: {e}")
            print(f"   エラー詳細: {type(e).__name__}")
            # 空の辞書を追加
            ocr_results.append({
                'title': '',
                'progress': '',
                'last_read_date': '',
                'site_name': ''
            })
    
    return ocr_results
