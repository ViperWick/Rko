import tkinter as tk
from tkinter import ttk, messagebox
import qrcode
from PIL import Image, ImageTk
import datetime
import json
import random
import string
from ttkbootstrap import Style
import sqlite3
import os
from datetime import datetime

class QRCodeSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Q-pi 比賽報到系統")
        self.root.geometry("800x600")
        
        # 設置深藍色主題
        self.style = Style(theme='cosmo')
        self.style.configure('Custom.TFrame', background='#1a237e')
        self.style.configure('Custom.TLabel', background='#1a237e', foreground='white')
        self.style.configure('Orange.TButton', background='#ff8f00')
        
        # 設置中文字體
        self.chinese_font = ("Microsoft YaHei UI", 12)
        self.title_font = ("Microsoft YaHei UI", 16, "bold")
        
        # 初始化資料庫
        self.init_database()
        
        # 創建主要框架
        self.create_main_layout()
        
    def init_database(self):
        """初始化資料庫"""
        self.conn = sqlite3.connect('qrcode_system.db')
        c = self.conn.cursor()
        
        # 先刪除舊的資料表（如果存在）
        c.execute('DROP TABLE IF EXISTS participants')
        
        # 創建新的資料表
        c.execute('''CREATE TABLE participants
                    (id_number TEXT PRIMARY KEY,
                     player_id TEXT,
                     name TEXT,
                     category TEXT,
                     qr_code TEXT,
                     check_in_status TEXT,
                     check_in_time TEXT)''')
        self.conn.commit()
        
        # 添加測試數據
        self.add_test_data()
        
    def add_test_data(self):
        """添加測試數據"""
        test_data = [
            ('A123456789', None, '宋宛蓉', '29歲以下女雙', None, '未報到', None),
            ('B987654321', None, '陳慧馨', '29歲以下女雙', None, '未報到', None)
        ]
        
        c = self.conn.cursor()
        for data in test_data:
            try:
                c.execute('''INSERT INTO participants 
                            (id_number, player_id, name, category, qr_code, check_in_status, check_in_time)
                            VALUES (?, ?, ?, ?, ?, ?, ?)''', data)
                self.conn.commit()
            except sqlite3.IntegrityError:
                continue
        
    def create_main_layout(self):
        """創建主要佈局"""
        # 身分證輸入框
        self.id_frame = ttk.Frame(self.root, style='Custom.TFrame')
        self.id_frame.pack(fill='both', expand=True)
        
        # Logo
        ttk.Label(
            self.id_frame,
            text="Q-pi",
            font=("Microsoft YaHei UI", 24, "bold"),
            style='Custom.TLabel'
        ).pack(pady=(40,0))
        
        ttk.Label(
            self.id_frame,
            text="2024體育全國羽球錦標賽\nQ-pi 比賽報到系統",
            font=self.title_font,
            style='Custom.TLabel'
        ).pack(pady=20)
        
        # 身分證輸入
        input_frame = ttk.Frame(self.id_frame, style='Custom.TFrame')
        input_frame.pack(pady=20)
        
        self.id_entry = ttk.Entry(
            input_frame,
            font=self.chinese_font,
            width=30,
            justify='center'
        )
        self.id_entry.insert(0, "請輸入身分證字號後五碼")
        self.id_entry.pack(pady=10)
        
        # 綁定點擊事件
        self.id_entry.bind('<FocusIn>', self.clear_placeholder)
        self.id_entry.bind('<FocusOut>', self.restore_placeholder)
        
        # 送出按鈕
        submit_btn = ttk.Button(
            input_frame,
            text="送出",
            style='Orange.TButton',
            command=self.verify_id
        )
        submit_btn.pack(pady=10)
        
        # 版權信息
        ttk.Label(
            self.id_frame,
            text="Q-pi 報到系統 © Copyright 2024 ParamitaDigital | All Rights Reserved",
            font=("Microsoft YaHei UI", 8),
            style='Custom.TLabel'
        ).pack(side='bottom', pady=20)
        
    def clear_placeholder(self, event):
        """清除預設文字"""
        if self.id_entry.get() == "請輸入身分證字號後五碼":
            self.id_entry.delete(0, tk.END)
            
    def restore_placeholder(self, event):
        """恢復預設文字"""
        if not self.id_entry.get():
            self.id_entry.insert(0, "請輸入身分證字號後五碼")
            
    def verify_id(self):
        """驗證身分證並生成QR碼"""
        id_number = self.id_entry.get()
        
        if id_number == "請輸入身分證字號後五碼" or len(id_number) != 5:
            messagebox.showerror("錯誤", "請輸入正確的身分證字號後五碼")
            return
        
        # 檢查資料庫
        c = self.conn.cursor()
        c.execute('SELECT * FROM participants WHERE id_number LIKE ?', ('%' + id_number,))
        participant = c.fetchone()
        
        if participant:
            # 生成選手編號（如果還沒有的話）
            if not participant[1]:  # player_id is None
                player_id = self.generate_player_id()
                c.execute('UPDATE participants SET player_id = ? WHERE id_number = ?',
                         (player_id, participant[0]))
                self.conn.commit()
            else:
                player_id = participant[1]
                
            # 生成QR碼
            self.generate_qr_ticket(participant[2], player_id, participant[3])
        else:
            messagebox.showerror("錯誤", "找不到此身分證號碼，請確認後重試")
            
    def generate_player_id(self):
        """生成唯一的選手編號"""
        prefix = 'J'
        number = ''.join(random.choices(string.digits, k=9))
        return f"{prefix}{number}"
        
    def generate_qr_ticket(self, name, player_id, category):
        """生成電子票券"""
        # QR碼數據
        qr_data = {
            "name": name,
            "player_id": player_id,
            "category": category,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 生成QR碼
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # 創建票券窗口
        ticket_window = tk.Toplevel(self.root)
        ticket_window.title("電子票券")
        ticket_window.geometry("400x600")
        
        # 添加票券內容
        ttk.Label(
            ticket_window,
            text="Q-pi TICKET",
            font=self.title_font
        ).pack(pady=(20,10))
        
        ttk.Label(
            ticket_window,
            text=f"{name}",
            font=self.chinese_font
        ).pack(pady=5)
        
        ttk.Label(
            ticket_window,
            text=f"選手編號：{player_id}",
            font=self.chinese_font
        ).pack(pady=5)
        
        ttk.Label(
            ticket_window,
            text=category,
            font=self.chinese_font
        ).pack(pady=5)
        
        # QR碼圖片
        qr_photo = ImageTk.PhotoImage(qr_image)
        qr_label = ttk.Label(ticket_window, image=qr_photo)
        qr_label.image = qr_photo
        qr_label.pack(pady=20)
        
        # 下載按鈕
        ttk.Button(
            ticket_window,
            text="下載至手機",
            style='Orange.TButton',
            command=lambda: self.save_ticket(qr_image, player_id)
        ).pack(pady=10)

    def save_ticket(self, qr_image, player_id):
        """保存電子票券"""
        # 創建tickets目錄（如果不存在）
        if not os.path.exists('tickets'):
            os.makedirs('tickets')
            
        # 保存QR碼圖片
        filename = f"tickets/ticket_{player_id}.png"
        qr_image.save(filename)
        messagebox.showinfo("成功", f"電子票券已保存至：{filename}")

def main():
    root = tk.Tk()
    app = QRCodeSystem(root)
    root.mainloop()

if __name__ == "__main__":
    main() 