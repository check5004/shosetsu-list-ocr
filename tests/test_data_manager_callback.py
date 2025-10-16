#!/usr/bin/env python3
"""
DataManagerのコールバック機能のテスト
"""

from src.data_manager import DataManager


def test_callback():
    """コールバック機能のテスト"""
    print("=== DataManager Callback Test ===\n")
    
    # コールバック関数
    detected_texts = []
    
    def on_new_text(text: str):
        detected_texts.append(text)
        print(f"コールバック呼び出し: {text}")
    
    # DataManagerを初期化（コールバック付き）
    dm = DataManager(output_path="test_output.csv", on_new_text_callback=on_new_text)
    
    # テスト1: 新規テキストの追加
    print("\nTest 1: 新規テキストの追加")
    result1 = dm.add_text("テストテキスト1")
    print(f"結果: {result1} (期待値: True)")
    assert result1 == True, "新規テキストはTrueを返すべき"
    assert len(detected_texts) == 1, "コールバックが1回呼ばれるべき"
    assert detected_texts[0] == "テストテキスト1", "正しいテキストが渡されるべき"
    print("✓ Test 1 passed")
    
    # テスト2: 重複テキストの追加
    print("\nTest 2: 重複テキストの追加")
    result2 = dm.add_text("テストテキスト1")
    print(f"結果: {result2} (期待値: False)")
    assert result2 == False, "重複テキストはFalseを返すべき"
    assert len(detected_texts) == 1, "コールバックは呼ばれないべき"
    print("✓ Test 2 passed")
    
    # テスト3: 複数の新規テキスト
    print("\nTest 3: 複数の新規テキスト")
    dm.add_text("テストテキスト2")
    dm.add_text("テストテキスト3")
    assert len(detected_texts) == 3, "コールバックが3回呼ばれるべき"
    print("✓ Test 3 passed")
    
    # テスト4: コールバックなしのDataManager
    print("\nTest 4: コールバックなしのDataManager")
    dm_no_callback = DataManager(output_path="test_output2.csv")
    result4 = dm_no_callback.add_text("テストテキスト4")
    print(f"結果: {result4} (期待値: True)")
    assert result4 == True, "コールバックなしでも動作すべき"
    print("✓ Test 4 passed")
    
    print("\n=== All tests passed! ===")


if __name__ == "__main__":
    test_callback()
