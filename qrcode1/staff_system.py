import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import cv2
from pyzbar.pyzbar import decode
import json
import sqlite3
from datetime import datetime
from ttkbootstrap import Style

class StaffSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Q-pi 主辦方掃描系統")
        self.root.geometry("800x600")
        
        # 設置主題
        self.style = Style(theme='cosmo')
        self.style.configure('Custom.TFrame', background='#1a237e')
        self.style.configure('Custom.TLabel', background='#1a237e', foreground='white')
        self.style.configure('Orange.TButton', background='#ff8f00')
        
        # 設置字體
        self.chinese_font = ("Microsoft YaHei UI", 12)
        self.title_font = ("Microsoft YaHei UI", 16, "bold")
        
        self.create_main_layout()
        
    def create_main_layout(self):
        main_frame = ttk.Frame(self.root, style='Custom.TFrame')
        main_frame.pack(fill='both', expand=True)
        
        # 標題
        ttk.Label(
            main_frame,
            text="主辦��掃描系統",
            font=self.title_font,
            style='Custom.TLabel'
        ).pack(pady=20)
        
        # 掃描區域
        scan_frame = ttk.Frame(main_frame, style='Custom.TFrame')
        scan_frame.pack(pady=20)
        
        ttk.Button(
            scan_frame,
            text="開啟掃描器",
            style='Orange.TButton',
            command=self.start_scanner
        ).pack(pady=10)
        
        self.result_label = ttk.Label(
            scan_frame,
            text="等待掃描...",
            font=self.chinese_font,
            style='Custom.TLabel'
        )
        self.result_label.pack(pady=20)
        
        # 狀態按鈕
        status_frame = ttk.Frame(scan_frame, style='Custom.TFrame')
        status_frame.pack(pady=20)
        
        ttk.Button(
            status_frame,
            text="報到成功",
            style='Orange.TButton',
            command=lambda: self.update_status("已報到")
        ).pack(side='left', padx=10)
        
        ttk.Button(
            status_frame,
            text="報到失敗",
            style='Orange.TButton',
            command=lambda: self.update_status("報到失敗")
        ).pack(side='left', padx=10)

    def start_scanner(self):
        # 這裡實現掃描器功能
        # 使用opencv讀取攝像頭並解析QR碼
        pass

    def update_status(self, status):
        # 更新資料庫中的報到狀態
        conn = sqlite3.connect('qrcode_system.db')
        c = conn.cursor()
        # 更新狀態邏輯
        conn.close()
        
        self.result_label.configure(text=f"選手報到{status}")

def main():
    root = tk.Tk()
    app = StaffSystem(root)
    root.mainloop()

if __name__ == "__main__":
    main() 