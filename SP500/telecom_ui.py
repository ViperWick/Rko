import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import yfinance as yf
import pandas as pd
import numpy as np
from ta.trend import MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

class StockAnalysisUI:
    def __init__(self, root):
        self.root = root
        self.root.title("美股交易策略分析系統")
        self.root.geometry("1200x800")
        
        # 設置中文字體
        self.chinese_font = ("Microsoft YaHei UI", 10)
        
        # 定義行業分類
        self.sectors = {
            "科技": ["軟體服務", "硬體設備", "半導體", "網路服務"],
            "金融": ["銀行", "保險", "資產管理", "金融科技"],
            "醫療保健": ["製藥", "生物科技", "醫療設備", "醫療服務"],
            "消費": ["零售", "電商", "餐飲", "娛樂媒體"],
            "工業": ["製造", "運輸", "航空航天", "國防"],
            "能源": ["石油天然���", "再生能源", "公用事業"],
            "原物料": ["化工", "礦業", "金屬"],
            "電信": ["通訊服務", "電信設備"],
            "房地產": ["房地產開發", "不動產投資信託"],
        }
        
        # 預設股票分類
        self.stock_by_sectors = {
            "科技": {
                'AAPL': 'Apple Inc.',
                'MSFT': 'Microsoft Corporation',
                'GOOGL': 'Alphabet Inc.',
                'NVDA': 'NVIDIA Corporation',
                'AMD': 'Advanced Micro Devices Inc.',
                'INTC': 'Intel Corporation',
                'META': 'Meta Platforms Inc.',
            },
            "金融": {
                'JPM': 'JPMorgan Chase & Co.',
                'BAC': 'Bank of America Corp.',
                'WFC': 'Wells Fargo & Co.',
                'V': 'Visa Inc.',
                'MA': 'Mastercard Inc.',
            },
            "醫療保健": {
                'JNJ': 'Johnson & Johnson',
                'PFE': 'Pfizer Inc.',
                'UNH': 'UnitedHealth Group Inc.',
                'MRK': 'Merck & Co.',
                'ABBV': 'AbbVie Inc.',
            },
            "消費": {
                'AMZN': 'Amazon.com Inc.',
                'PG': 'Procter & Gamble Co.',
                'KO': 'Coca-Cola Co.',
                'PEP': 'PepsiCo Inc.',
                'WMT': 'Walmart Inc.',
                'NFLX': 'Netflix Inc.',
            },
            "工業": {
                'BA': 'Boeing Co.',
                'CAT': 'Caterpillar Inc.',
                'GE': 'General Electric Co.',
                'MMM': '3M Co.',
                'HON': 'Honeywell International Inc.',
            },
            "能源": {
                'XOM': 'Exxon Mobil Corporation',
                'CVX': 'Chevron Corporation',
                'COP': 'ConocoPhillips',
                'SLB': 'Schlumberger NV',
                'EOG': 'EOG Resources Inc.',
            },
            "原物料": {
                'LIN': 'Linde plc',
                'FCX': 'Freeport-McMoRan Inc.',
                'DOW': 'Dow Inc.',
                'APD': 'Air Products & Chemicals Inc.',
                'NEM': 'Newmont Corporation',
            },
            "電信": {
                'T': 'AT&T Inc.',
                'VZ': 'Verizon Communications Inc.',
                'TMUS': 'T-Mobile US Inc.',
                'CSCO': 'Cisco Systems Inc.',
                'QCOM': 'Qualcomm Inc.',
            },
            "房地產": {
                'AMT': 'American Tower Corp.',
                'PLD': 'Prologis Inc.',
                'CCI': 'Crown Castle Inc.',
                'EQIX': 'Equinix Inc.',
                'SPG': 'Simon Property Group Inc.',
            }
        }
        
        # 創建主要佈局
        self.create_main_layout()
        
    def create_main_layout(self):
        """創建主要佈局"""
        # 創建左側設置面板
        settings_frame = ttk.LabelFrame(self.root, text="策略設置")
        settings_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # 修改股票選擇區域
        stock_frame = ttk.LabelFrame(settings_frame, text="股票選擇")
        stock_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 添加行業分類選擇
        ttk.Label(stock_frame, text="行業分類:").pack(anchor='w', padx=5, pady=2)
        self.sector_var = tk.StringVar()
        self.sector_combo = ttk.Combobox(stock_frame,
                                        textvariable=self.sector_var,
                                        values=list(self.sectors.keys()),
                                        state="readonly")
        self.sector_combo.pack(fill=tk.X, padx=5, pady=2)
        
        # 添加股票選擇
        ttk.Label(stock_frame, text="選擇股票:").pack(anchor='w', padx=5, pady=2)
        self.stock_var = tk.StringVar()
        self.stock_combo = ttk.Combobox(stock_frame,
                                       textvariable=self.stock_var,
                                       state="readonly")
        self.stock_combo.pack(fill=tk.X, padx=5, pady=2)
        
        # 綁定事件
        self.sector_combo.bind('<<ComboboxSelected>>', self.update_stock_list)
        
        # 初始化股票數據
        self.load_index_components()
        
        # 回測期間
        ttk.Label(settings_frame, text="回測期間:").pack(anchor='w', padx=5, pady=2)
        self.period_var = tk.StringVar(value="1年")
        ttk.Combobox(settings_frame,
                     textvariable=self.period_var,
                     values=["6個月", "1年", "3年", "5年"],
                     state="readonly").pack(fill=tk.X, padx=5, pady=2)
        
        # 策略選擇
        ttk.Label(settings_frame, text="交易策略:").pack(anchor='w', padx=5, pady=2)
        self.strategy_var = tk.StringVar(value="均線交叉")
        self.strategy_combo = ttk.Combobox(settings_frame,
                                         textvariable=self.strategy_var,
                                         values=["均線交叉", "RSI策略", "MACD策略", 
                                                "布林通道", "價格突破", "量價關係",
                                                "KD指標", "移動止損"],
                                         state="readonly")
        self.strategy_combo.pack(fill=tk.X, padx=5, pady=2)
        
        # 創建參數框架
        self.params_frame = ttk.LabelFrame(settings_frame, text="策略參數")
        self.params_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 綁定策略選擇事件
        self.strategy_combo.bind('<<ComboboxSelected>>', self.update_strategy_params)
        
        # 初始化策略參數
        self.create_strategy_params()
        
        # 開始回測按鈕
        ttk.Button(settings_frame, text="開始回測", 
                   command=self.run_backtest).pack(pady=10)
        
        # 創建右側結果顯示區域
        result_frame = ttk.Frame(self.root)
        result_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 回測結果圖表
        self.fig, (self.price_ax, self.signal_ax) = plt.subplots(2, 1, figsize=(10, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=result_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 回測結果文字說明
        self.result_text = scrolledtext.ScrolledText(
            result_frame, wrap=tk.WORD, height=10, font=self.chinese_font
        )
        self.result_text.pack(fill=tk.X, pady=5)
    
    def create_strategy_params(self):
        """創建策略參數控件"""
        self.strategy_params = {
            "均線交叉": {
                "短均線": tk.StringVar(value="5"),
                "長均線": tk.StringVar(value="20")
            },
            "RSI策略": {
                "RSI週期": tk.StringVar(value="14"),
                "超買閾值": tk.StringVar(value="70"),
                "超賣閾值": tk.StringVar(value="30")
            },
            "MACD策略": {
                "快線週期": tk.StringVar(value="12"),
                "慢線週期": tk.StringVar(value="26"),
                "信號週期": tk.StringVar(value="9")
            },
            "布林通道": {
                "移動平均期": tk.StringVar(value="20"),
                "標準差倍數": tk.StringVar(value="2")
            },
            "價格突破": {
                "突破週期": tk.StringVar(value="20"),
                "確認天數": tk.StringVar(value="3")
            },
            "量價關係": {
                "均量週期": tk.StringVar(value="20"),
                "放量倍數": tk.StringVar(value="2")
            },
            "KD指標": {
                "K週期": tk.StringVar(value="9"),
                "D週期": tk.StringVar(value="3"),
                "RSV週期": tk.StringVar(value="3")
            },
            "移動止損": {
                "ATR週期": tk.StringVar(value="14"),
                "止倍數": tk.StringVar(value="2")
            }
        }
        self.update_strategy_params(None)
    
    def update_strategy_params(self, event):
        """更新策略參數顯示"""
        # 清除現有參數
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        
        # 獲取當前策略
        strategy = self.strategy_var.get()
        
        # 顯示相應的參數設置
        row = 0
        for param_name, param_var in self.strategy_params[strategy].items():
            ttk.Label(self.params_frame, text=param_name+":").grid(row=row, column=0, padx=5, pady=2)
            ttk.Entry(self.params_frame, textvariable=param_var, width=8).grid(row=row, column=1, padx=5, pady=2)
            row += 1
    
    def calculate_signals(self, data, strategy):
        """計算交易信號"""
        try:
            if strategy == "均線交叉":
                short_ma = int(self.strategy_params[strategy]["短期均線"].get())
                long_ma = int(self.strategy_params[strategy]["長期均線"].get())
                data['MA_Short'] = data['Close'].rolling(window=short_ma).mean()
                data['MA_Long'] = data['Close'].rolling(window=long_ma).mean()
                data['Signal'] = 0
                data.loc[data['MA_Short'] > data['MA_Long'], 'Signal'] = 1
                data.loc[data['MA_Short'] < data['MA_Long'], 'Signal'] = -1
                
            elif strategy == "RSI策略":
                period = int(self.strategy_params[strategy]["RSI週期"].get())
                overbought = int(self.strategy_params[strategy]["超買閾值"].get())
                oversold = int(self.strategy_params[strategy]["超賣閾值"].get())
                rsi = RSIIndicator(data['Close'], window=period)
                data['RSI'] = rsi.rsi()
                data['Signal'] = 0
                data.loc[data['RSI'] < oversold, 'Signal'] = 1
                data.loc[data['RSI'] > overbought, 'Signal'] = -1
                
            elif strategy == "MACD策略":
                fast = int(self.strategy_params[strategy]["快線週期"].get())
                slow = int(self.strategy_params[strategy]["慢線週期"].get())
                signal = int(self.strategy_params[strategy]["信號週期"].get())
                macd = MACD(data['Close'], window_fast=fast, window_slow=slow, window_sign=signal)
                data['MACD'] = macd.macd()
                data['Signal_Line'] = macd.macd_signal()
                data['Signal'] = 0
                data.loc[data['MACD'] > data['Signal_Line'], 'Signal'] = 1
                data.loc[data['MACD'] < data['Signal_Line'], 'Signal'] = -1
                
            elif strategy == "布林通道":
                window = int(self.strategy_params[strategy]["移動平均期"].get())
                std_dev = float(self.strategy_params[strategy]["標準差倍數"].get())
                bb = BollingerBands(data['Close'], window=window, window_dev=std_dev)
                data['BB_upper'] = bb.bollinger_hband()
                data['BB_lower'] = bb.bollinger_lband()
                data['Signal'] = 0
                data.loc[data['Close'] < data['BB_lower'], 'Signal'] = 1
                data.loc[data['Close'] > data['BB_upper'], 'Signal'] = -1
                
            return data
            
        except Exception as e:
            raise ValueError(f"計算{strategy}信號時發生錯誤：{str(e)}")

    def run_backtest(self):
        """執行回測"""
        try:
            # 檢查是否選擇了股票
            stock_text = self.stock_var.get()
            if not stock_text:
                messagebox.showwarning("警告", "請先選擇股票")
                return
            
            # 獲取股票代碼（只取代碼部分）
            symbol = stock_text.split(' - ')[0].strip()
            
            # 獲取回測參數
            period_map = {"6個月": "6mo", "1年": "1y", "3年": "3y", "5年": "5y"}
            period = period_map[self.period_var.get()]
            strategy = self.strategy_var.get()
            
            # 顯示載入提示
            self.root.config(cursor="wait")
            self.root.update()
            
            try:
                # 獲取股票數據
                stock = yf.Ticker(symbol)
                data = stock.history(period=period)
                
                if len(data) == 0:
                    raise ValueError(f"無法獲取 {symbol} 的股票數據")
                    
                # 計算交易信號
                data = self.calculate_signals(data, strategy)
                
                # 計算回測結果
                data['Returns'] = data['Close'].pct_change()
                data['Strategy_Returns'] = data['Signal'].shift(1) * data['Returns']
                data['Cumulative_Returns'] = (1 + data['Returns']).cumprod()
                data['Strategy_Cumulative_Returns'] = (1 + data['Strategy_Returns']).cumprod()
                
                # 計算績效指標
                total_return = (data['Strategy_Cumulative_Returns'].iloc[-1] - 1) * 100
                annual_return = (total_return / (len(data) / 252))
                sharpe_ratio = np.sqrt(252) * (data['Strategy_Returns'].mean() / data['Strategy_Returns'].std())
                max_drawdown = (data['Strategy_Cumulative_Returns'] / data['Strategy_Cumulative_Returns'].cummax() - 1).min() * 100
                
                # 更新圖表和結果
                self.update_charts(data, strategy, symbol)
                self.update_results_text(symbol, strategy, total_return, annual_return, sharpe_ratio, max_drawdown, data)
                
            except Exception as e:
                raise Exception(f"處理股票數據時發生錯誤：{str(e)}")
            finally:
                # 恢復鼠標
                self.root.config(cursor="")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"執行回測時發生錯誤：\n{str(e)}")
            # 清空圖表
            self.price_ax.clear()
            self.signal_ax.clear()
            self.canvas.draw()
            # 清空結果文字
            self.result_text.delete(1.0, tk.END)
    
    def update_charts(self, data, strategy, symbol):
        """更新圖表顯示"""
        self.price_ax.clear()
        self.signal_ax.clear()
        
        # 繪製股價和指標
        self.price_ax.plot(data.index, data['Close'], label='股價', color='black')
        if strategy == "均線交叉":
            self.price_ax.plot(data.index, data['MA_Short'], label='短期均線', color='red')
            self.price_ax.plot(data.index, data['MA_Long'], label='長期均線', color='blue')
        elif strategy == "布林通道":
            self.price_ax.plot(data.index, data['BB_upper'], label='上軌', color='red')
            self.price_ax.plot(data.index, data['BB_lower'], label='下軌', color='blue')
        
        # 繪製策略收益
        self.signal_ax.plot(data.index, data['Cumulative_Returns'], label='買入持有', color='gray')
        self.signal_ax.plot(data.index, data['Strategy_Cumulative_Returns'], label='策略收益', color='green')
        
        # 設置圖表格式
        self.price_ax.set_title(f"{symbol} - {strategy}策略回測結果")
        self.price_ax.legend()
        self.price_ax.grid(True)
        self.signal_ax.legend()
        self.signal_ax.grid(True)
        self.fig.tight_layout()
        self.canvas.draw()
    
    def update_results_text(self, symbol, strategy, total_return, annual_return, sharpe_ratio, max_drawdown, data):
        """更新回測結果文字"""
        result_text = f"""
【回測結果摘要】
測股票: {symbol}
測試策略: {strategy}
測試期間: {self.period_var.get()}

【績效指標】
總收益率: {total_return:.2f}%
年化收益: {annual_return:.2f}%
夏普比率: {sharpe_ratio:.2f}
最大回撤: {max_drawdown:.2f}%

【交易統計】
交易次數: {(data['Signal'].diff() != 0).sum()}
勝率: {(data['Strategy_Returns'] > 0).mean()*100:.2f}%
平均收益: {data['Strategy_Returns'].mean()*100:.4f}%
收益標準差: {data['Strategy_Returns'].std()*100:.4f}%
"""
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result_text)

    def load_index_components(self):
        """載入股票數據"""
        self.stock_var = tk.StringVar()
        self.update_stock_list(None)

    def update_stock_list(self, event=None):
        """更新股票列表"""
        try:
            sector = self.sector_var.get()
            if not sector:  # 如果沒有選擇行業
                self.stock_combo['values'] = []
                self.stock_combo.set('')
                return
            
            # 獲取該行業的股票
            stocks = self.stock_by_sectors.get(sector, {})
            
            # 創建顯示列表
            stock_list = [f"{symbol} - {name}" for symbol, name in stocks.items()]
            
            # 更新股票下拉選單
            self.stock_combo['values'] = stock_list
            if stock_list:
                self.stock_combo.set(stock_list[0])
            else:
                self.stock_combo.set('')
                
        except Exception as e:
            messagebox.showerror("錯誤", f"更新股票列表時發生錯誤：{str(e)}")

def main():
    root = tk.Tk()
    app = StockAnalysisUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 