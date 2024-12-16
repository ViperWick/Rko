import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

class TelecomAnalyzer:
    def __init__(self):
        # 初始化全球電信公司資料
        self.telecom_stocks = {
            # 台灣電信公司
            "2412.TW": "中華電信",
            "3045.TW": "台灣大哥大",
            "4904.TW": "遠傳電信",
            
            # 美國電信公司
            "T": "AT&T",
            "VZ": "Verizon",
            "TMUS": "T-Mobile US",
            
            # 中國電信公司
            "0941.HK": "中國移動",
            "0762.HK": "中國聯通",
            "0728.HK": "中國電信",
            
            # 其他國際電信公司
            "DTEGY": "Deutsche Telekom",
            "VOD": "Vodafone Group"
        }
        
        # 初始化全球電信產業分類
        self.global_telecom = {
            '通訊營運商': {
                '美國': {
                    'VZ': 'Verizon',
                    'T': 'AT&T',
                    'TMUS': 'T-Mobile US'
                },
                '中國': {
                    '0941.HK': '中國移動',
                    '0762.HK': '中國聯通',
                    '0728.HK': '中國電信'
                },
                '歐洲': {
                    'DTEGY': 'Deutsche Telekom',
                    'VOD': 'Vodafone Group'
                },
                '台灣': {
                    '2412.TW': '中華電信',
                    '3045.TW': '台灣大哥大',
                    '4904.TW': '遠傳'
                }
            },
            '設備製造商': {
                '基礎設備': {
                    'ERIC': '愛立信',
                    'NOK': '諾基亞',
                    'CSCO': '思科'
                },
                '終端設備': {
                    'AAPL': '蘋果',
                    '2317.TW': '鴻海'
                }
            },
            '零組件廠商': {
                '射頻元件': {
                    'QRVO': 'Qorvo',
                    'SWKS': 'Skyworks',
                    'AVGO': 'Broadcom'
                },
                '光通訊': {
                    'LITE': 'Lumentum',
                    '3008.TW': '大立光'
                }
            }
        }

        # 產業發展重點
        self.industry_focus = {
            '5G/6G發展': {
                '技術演進': ['毫米波技術', 'Massive MIMO', '網路切片'],
                '應用場景': ['智慧城市', '工業物聯網', '自動駕駛'],
                '市場規模': '預計2025年達到6,670億美元',
                '主要玩家': ['愛立信', '諾基亞', '華為', '三星']
            },
            '衛星通訊': {
                '展重點': ['低軌衛星網路', '太空互聯網', '全球覆蓋'],
                '應用領域': ['偏遠通訊', '航空海運', '應急通訊'],
                '市場前景': '預計2030年達到1,240億美元',
                '代表企業': ['SpaceX Starlink', 'OneWeb', 'Project Kuiper']
            },
            '智慧網路': {
                '關鍵技術': ['AI網路優化', 'SDN/NFV', '邊緣計算'],
                '應用方向': ['智慧家庭', '智慧工廠', '智慧交通'],
                '發展趨勢': ['網路自動化', '虛擬化', '雲原生'],
                '解決方案商': ['思科', 'VMware', '華為']
            }
        }

        # 投資主題
        self.investment_themes = {
            '成長動能': {
                '5G建設': '全球5G基礎建設持續擴張',
                '數位轉型': '企業網路升級需求增加',
                '物聯網': 'IoT設備連網需求成長'
            },
            '產業整合': {
                '併購活動': '產業鏈整合加速',
                '策略聯盟': '跨域合作增加',
                '技術合作': '開放網路架構發展'
            },
            '風險因素': {
                '競爭加劇': '價格戰影響獲利',
                '技術變革': '技術升級投資壓力',
                '監管政策': '各國通訊政策變動'
            }
        }

    def get_company_info(self, category, region=None, company=None):
        """獲取公司資訊"""
        if company:
            # 返回特定公司資訊
            return self._get_detailed_company_info(category, region, company)
        elif region:
            # 返回特定地區所有公司
            return self.global_telecom[category][region]
        else:
            # 返回該類別所有公司
            return self.global_telecom[category]

    def _get_detailed_company_info(self, category, region, company):
        """獲取詳細公司資訊"""
        try:
            stock = yf.Ticker(company)
            info = stock.info
            return {
                '公司名稱': self.global_telecom[category][region][company],
                '股票代碼': company,
                '市值': info.get('marketCap', 'N/A'),
                '本益比': info.get('trailingPE', 'N/A'),
                '殖利率': info.get('dividendYield', 'N/A'),
                '52週高': info.get('fiftyTwoWeekHigh', 'N/A'),
                '52週低': info.get('fiftyTwoWeekLow', 'N/A'),
                '產業分類': category,
                '地區': region
            }
        except:
            return None

    def get_industry_focus(self):
        """獲取產業發展重點"""
        return self.industry_focus

    def get_investment_themes(self):
        """獲取投資主題"""
        return self.investment_themes

    def generate_industry_report(self):
        """生成產業分析報告"""
        try:
            # 初始化報告數據結構
            report = {
                'data': {},
                'metrics': {
                    'market_cap': {},
                    'pe_ratio': {},
                    'dividend_yield': {},
                    'revenue': {}
                }
            }
            
            # 收集所有通訊營運商的數據
            telecom_operators = self.global_telecom['通訊營運商']
            for region in telecom_operators:
                for symbol, name in telecom_operators[region].items():
                    try:
                        # 獲取股票數據
                        stock = yf.Ticker(symbol)
                        info = stock.info
                        history = stock.history(period='1y')
                        
                        # 保存歷史數據
                        if not history.empty:
                            report['data'][symbol] = history
                        
                        # 保存指標數據
                        report['metrics']['market_cap'][symbol] = info.get('marketCap', 0)
                        report['metrics']['pe_ratio'][symbol] = info.get('trailingPE', 0)
                        report['metrics']['dividend_yield'][symbol] = info.get('dividendYield', 0)
                        report['metrics']['revenue'][symbol] = info.get('totalRevenue', 0)
                    except:
                        print(f"無法獲取 {name} ({symbol}) 的數據")
                        continue
            
            return report
        except Exception as e:
            print(f"生成報告時發生錯誤: {str(e)}")
            return {
                'data': {},
                'metrics': {
                    'market_cap': {},
                    'pe_ratio': {},
                    'dividend_yield': {},
                    'revenue': {}
                }
            }

    def get_stock_data(self, period='1y'):
        """獲取股票數據"""
        data = {}
        telecom_operators = self.global_telecom['通訊營運商']
        for region in telecom_operators:
            for symbol in telecom_operators[region]:
                try:
                    stock = yf.Ticker(symbol)
                    data[symbol] = stock.history(period=period)
                except:
                    print(f"無法獲取 {symbol} 的數據")
                    continue
        return data

    def calculate_industry_metrics(self, data):
        """計算產業指標"""
        metrics = {
            'market_cap': {},
            'pe_ratio': {},
            'dividend_yield': {},
            'revenue': {}
        }
        
        telecom_operators = self.global_telecom['通訊營運商']
        for region in telecom_operators:
            for symbol in telecom_operators[region]:
                try:
                    stock = yf.Ticker(symbol)
                    info = stock.info
                    
                    metrics['market_cap'][symbol] = info.get('marketCap', 0)
                    metrics['pe_ratio'][symbol] = info.get('trailingPE', 0)
                    metrics['dividend_yield'][symbol] = info.get('dividendYield', 0)
                    metrics['revenue'][symbol] = info.get('totalRevenue', 0)
                except:
                    print(f"無法獲取 {symbol} 的指標數據")
                    continue
        
        return metrics