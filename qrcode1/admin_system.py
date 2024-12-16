import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from ttkbootstrap import Style
import pandas as pd

class AdminSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Q-pi 後台管理系統")
        self.root.geometry("1200x800")
        
        # 設置主題
        self.style = Style(theme='cosmo')
        self.chinese_font = ("Microsoft YaHei UI", 12)
        self.title_font = ("Microsoft YaHei UI", 16, "bold")
        
        self.create_main_layout()
        
    def create_main_layout(self):
        # 功能按鈕區
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(
            button_frame,
            text="建立比賽名稱",
            command=self.create_competition
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame,
            text="匯入參賽名單",
            command=self.import_participants
        ).pack(side='left', padx=5)
        
        # 參賽者列表
        columns = ('項目', '姓名', '��賽編號', '組別', '身分證字號', '生日', '報到狀態')
        self.tree = ttk.Treeview(self.root, columns=columns, show='headings')
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
            
        self.tree.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 載入資料
        self.load_participants()
        
    def create_competition(self):
        # 實現建立比賽功能
        pass
        
    def import_participants(self):
        filename = filedialog.askopenfilename(
            title="選擇Excel檔案",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if filename:
            try:
                df = pd.read_excel(filename)
                self.save_to_database(df)
                self.load_participants()
                messagebox.showinfo("成功", "參賽名單已匯入")
            except Exception as e:
                messagebox.showerror("錯誤", f"匯入失敗：{str(e)}")
                
    def save_to_database(self, df):
        conn = sqlite3.connect('qrcode_system.db')
        df.to_sql('participants', conn, if_exists='append', index=False)
        conn.close()
        
    def load_participants(self):
        conn = sqlite3.connect('qrcode_system.db')
        c = conn.cursor()
        c.execute('SELECT * FROM participants')
        
        # 清空現有數據
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 載入新數據
        for row in c.fetchall():
            self.tree.insert('', 'end', values=row)
            
        conn.close()

def main():
    root = tk.Tk()
    app = AdminSystem(root)
    root.mainloop()

if __name__ == "__main__":
    main() 