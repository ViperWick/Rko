#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量子計算學習筆記管理系統 - 運行腳本
"""

from quantum_learning_notes import QuantumLearningNotes

def interactive_menu():
    """互動式菜單"""
    notes_manager = QuantumLearningNotes()
    
    while True:
        print("\n" + "="*50)
        print("🚀 量子計算學習筆記管理系統")
        print("="*50)
        print("1. 📊 查看學習概覽")
        print("2. 📖 查看模組詳情")
        print("3. ➕ 添加新模組")
        print("4. 📝 添加筆記")
        print("5. 💪 添加實踐練習")
        print("6. ✅ 標記模組完成")
        print("7. 🔍 搜索筆記")
        print("8. 📤 導出筆記")
        print("9. 🚪 退出")
        print("-"*50)
        
        choice = input("請選擇操作 (1-9): ").strip()
        
        if choice == "1":
            notes_manager.display_overview()
            
        elif choice == "2":
            module_id = input("請輸入模組ID (例如: module_1): ").strip()
            notes_manager.display_module_detail(module_id)
            
        elif choice == "3":
            module_id = input("模組ID: ").strip()
            title = input("模組標題: ").strip()
            content = input("模組內容: ").strip()
            print("學習目標 (每行一個，輸入空行結束):")
            objectives = []
            while True:
                obj = input().strip()
                if not obj:
                    break
                objectives.append(obj)
            
            notes_manager.add_module(module_id, title, content, objectives)
            
        elif choice == "4":
            module_id = input("模組ID: ").strip()
            note = input("筆記內容: ").strip()
            notes_manager.add_note_to_module(module_id, note)
            
        elif choice == "5":
            module_id = input("模組ID: ").strip()
            exercise = input("實踐練習: ").strip()
            notes_manager.add_practice_exercise(module_id, exercise)
            
        elif choice == "6":
            module_id = input("模組ID: ").strip()
            completion = input("完成度 (0-100): ").strip()
            try:
                completion = int(completion)
                notes_manager.mark_module_completed(module_id, completion)
            except ValueError:
                print("❌ 請輸入有效的數字")
                
        elif choice == "7":
            keyword = input("搜索關鍵詞: ").strip()
            notes_manager.search_notes(keyword)
            
        elif choice == "8":
            notes_manager.export_notes("txt")
            
        elif choice == "9":
            print("👋 感謝使用量子計算學習筆記管理系統！")
            break
            
        else:
            print("❌ 無效選擇，請重新輸入")
        
        input("\n按Enter鍵繼續...")

if __name__ == "__main__":
    interactive_menu()
