import tkinter as tk
from tkinter import ttk, messagebox
import qrcode
from PIL import Image, ImageTk
import json
import datetime
from ttkbootstrap import Style
import sqlite3
import os

class PlayerSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Q-pi 選手報到系統")
        self.root.geometry("800x600")
        
        # 設置深藍色主題
        self.style = Style(theme='cosmo')
        self.style.configure('Custom.TFrame', background='#1a237e')
        self.style.configure('Custom.TLabel', background='#1a237e', foreground='white')
        self.style.configure('Orange.TButton', background='#ff8f00')
        
        # 設置中文字體
        self.chinese_font = ("Microsoft YaHei UI", 12)
        self.title_font = ("Microsoft YaHei UI", 16, "bold")
        
        # 創建主要框架
        self.create_main_layout()
        
    def create_main_layout(self):
        """創建主要佈局"""
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
        if self.id_entry.get() == "請輸入身分證字號後五碼":
            self.id_entry.delete(0, tk.END)
            
    def restore_placeholder(self, event):
        if not self.id_entry.get():
            self.id_entry.insert(0, "請輸入身分證字號後五碼")
            
    def verify_id(self):
        # 連接到共用資料庫
        conn = sqlite3.connect('qrcode_system.db')
        c = conn.cursor()
        
        id_number = self.id_entry.get()
        if id_number == "請輸入身分證字號後五碼" or len(id_number) != 5:
            messagebox.showerror("錯誤", "請輸入正確的身分證字號後五碼")
            return
            
        c.execute('SELECT * FROM participants WHERE id_number LIKE ?', ('%' + id_number,))
        participant = c.fetchone()
        
        if participant:
            self.generate_qr_ticket(participant[2], participant[1], participant[3])
        else:
            messagebox.showerror("錯誤", "找不到此身分證號碼，請確認後重試")
        
        conn.close()

    def generate_qr_ticket(self, name, player_id, category):
        qr_data = {
            "name": name,
            "player_id": player_id,
            "category": category,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # 顯示電子票券
        ticket_window = tk.Toplevel(self.root)
        ticket_window.title("電子票券")
        ticket_window.geometry("400x600")
        
        ttk.Label(ticket_window, text="Q-pi TICKET", font=self.title_font).pack(pady=(20,10))
        ttk.Label(ticket_window, text=name, font=self.chinese_font).pack(pady=5)
        ttk.Label(ticket_window, text=f"選手編號：{player_id}", font=self.chinese_font).pack(pady=5)
        ttk.Label(ticket_window, text=category, font=self.chinese_font).pack(pady=5)
        
        qr_photo = ImageTk.PhotoImage(qr_image)
        qr_label = ttk.Label(ticket_window, image=qr_photo)
        qr_label.image = qr_photo
        qr_label.pack(pady=20)
        
        ttk.Button(
            ticket_window,
            text="下載至手機",
            style='Orange.TButton',
            command=lambda: self.save_ticket(qr_image, player_id)
        ).pack(pady=10)

    def save_ticket(self, qr_image, player_id):
        if not os.path.exists('tickets'):
            os.makedirs('tickets')
        filename = f"tickets/ticket_{player_id}.png"
        qr_image.save(filename)
        messagebox.showinfo("成功", f"電子票券已保存至：{filename}")

def main():
    root = tk.Tk()
    app = PlayerSystem(root)
    root.mainloop()

if __name__ == "__main__":
    main() 