# -*- coding: utf-8 -*-
"""
匯出整合總表為 Excel 或 Word
執行: python -m etoro_trading.scripts.export_integrated_table
      python -m etoro_trading.scripts.export_integrated_table --word
      python -m etoro_trading.scripts.export_integrated_table --all
需安裝: pip install pandas openpyxl python-docx
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_EXCEL = DATA_DIR / "整合總表.xlsx"
OUT_WORD = DATA_DIR / "整合總表.docx"

# 標的完整資訊（靜態 + 從 fundamentals 動態填入）
MASTER_DATA = [
    {"標的": "GLD", "類型": "ETF", "產業": "黃金", "階段": "一", "波動": "低", "敘事關聯": "避險、抗通膨", "與GLD相關性": "", "高相關對": ""},
    {"標的": "NKE", "類型": "股票", "產業": "消費", "階段": "一", "波動": "中", "敘事關聯": "景氣支撐", "與GLD相關性": -0.06, "高相關對": ""},
    {"標的": "CRM", "類型": "股票", "產業": "科技", "階段": "一", "波動": "中", "敘事關聯": "雲端、SaaS", "與GLD相關性": -0.07, "高相關對": ""},
    {"標的": "IBM", "類型": "股票", "產業": "科技", "階段": "一", "波動": "低", "敘事關聯": "傳統科技", "與GLD相關性": -0.04, "高相關對": ""},
    {"標的": "UNH", "類型": "股票", "產業": "醫療", "階段": "一", "波動": "中", "敘事關聯": "防禦型", "與GLD相關性": 0.05, "高相關對": ""},
    {"標的": "PLTR", "類型": "股票", "產業": "科技", "階段": "二", "波動": "中高", "敘事關聯": "AI、數據平台", "與GLD相關性": 0.07, "高相關對": "ARKK 0.73"},
    {"標的": "MSFT", "類型": "股票", "產業": "科技", "階段": "二", "波動": "中", "敘事關聯": "雲端、AI、資料中心", "與GLD相關性": -0.02, "高相關對": ""},
    {"標的": "NVDA", "類型": "股票", "產業": "科技", "階段": "二", "波動": "高", "敘事關聯": "AI 算力核心", "與GLD相關性": 0.00, "高相關對": ""},
    {"標的": "ACN", "類型": "股票", "產業": "科技", "階段": "二", "波動": "低", "敘事關聯": "顧問、SaaS", "與GLD相關性": -0.12, "高相關對": ""},
    {"標的": "ARKK", "類型": "ETF", "產業": "創新/科技", "階段": "二", "波動": "高", "敘事關聯": "創新、科技主題", "與GLD相關性": 0.09, "高相關對": "PAVE 0.75, SHOP 0.72"},
    {"標的": "PAVE", "類型": "ETF", "產業": "基建", "階段": "二", "波動": "中", "敘事關聯": "基建、資料中心", "與GLD相關性": 0.08, "高相關對": "ARKK 0.75"},
    {"標的": "IONQ", "類型": "股票", "產業": "量子計算", "階段": "三", "波動": "高", "敘事關聯": "量子計算", "與GLD相關性": 0.05, "高相關對": ""},
    {"標的": "AMD", "類型": "股票", "產業": "半導體", "階段": "三", "波動": "高", "敘事關聯": "AI 晶片", "與GLD相關性": 0.12, "高相關對": ""},
    {"標的": "SHOP", "類型": "股票", "產業": "電商", "階段": "三", "波動": "中", "敘事關聯": "", "與GLD相關性": 0.02, "高相關對": "ARKK 0.72"},
]


def main():
    try:
        import pandas as pd
    except ImportError:
        print("請先安裝: pip install pandas")
        return 1

    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, Border, Side
        from openpyxl.utils.dataframe import dataframe_to_rows
    except ImportError:
        print("請先安裝: pip install openpyxl")
        return 1

    # 讀取 fundamentals 補充市值、營收增長、P/E、P/S
    fund_map = {}
    fund_file = DATA_DIR / "fundamentals.json"
    if fund_file.exists():
        for r in json.loads(fund_file.read_text(encoding="utf-8")):
            fund_map[r["symbol"]] = r

    # 合併基本面數據
    for row in MASTER_DATA:
        sym = row["標的"]
        f = fund_map.get(sym, {})
        mc = f.get("marketCap")
        row["市值(B)"] = round(mc / 1e9, 2) if mc else None
        rg = f.get("revenueGrowth")
        row["營收增長"] = f"{rg*100:.1f}%" if rg is not None else None
        row["P/E"] = round(f.get("peRatio"), 1) if f.get("peRatio") else None
        row["P/S"] = round(f.get("priceToSales"), 1) if f.get("priceToSales") else None
        row["股價"] = f.get("price")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    do_excel = "--word" not in sys.argv
    do_word = "--word" in sys.argv or "--all" in sys.argv

    if do_excel:
        with pd.ExcelWriter(OUT_EXCEL, engine="openpyxl") as writer:
            df_overview = pd.DataFrame(MASTER_DATA)
            df_overview = df_overview[["標的", "類型", "產業", "階段", "波動"]]
            df_overview.insert(0, "#", range(1, len(df_overview) + 1))
            df_overview.to_excel(writer, sheet_name="名單總覽", index=False)

            df_full = pd.DataFrame(MASTER_DATA)
            df_full.to_excel(writer, sheet_name="標的完整資訊", index=False)

            df_rules = pd.DataFrame([
                {"項目": "主要趨勢指標", "設定": "20 週均線"},
                {"項目": "過濾條件", "設定": "價格偏離均線 2–3% 以上"},
                {"項目": "策略類型", "設定": "低頻、規則式"},
                {"項目": "手續費（股票）", "設定": "$1／筆，來回 $2"},
                {"項目": "建議單筆", "設定": "≥ $300，理想 $500+"},
                {"項目": "API 限流", "設定": "搜尋間隔約 1.5 秒／標的"},
            ])
            df_rules.to_excel(writer, sheet_name="策略與規則", index=False)

            # 低頻管理＋現金倉位建議
            df_lowfreq = pd.DataFrame([
                {"項目": "推薦策略", "說明": "DCA 每月定投 + 止盈止損每週檢查 + 現金比例規則"},
                {"項目": "每週動作", "說明": "檢查持倉、止盈止損觸及與否（約 5–10 分鐘）"},
                {"項目": "每月動作", "說明": "執行 DCA、檢視現金比例、當月總結（約 30 分鐘）"},
                {"項目": "最低現金比例", "說明": "建議總資產 20–30% 保留現金"},
                {"項目": "不建議", "說明": "RSI、網格、動量突破（需高頻管理）"},
            ])
            df_lowfreq.to_excel(writer, sheet_name="低頻管理建議", index=False)

            # 策略總表
            df_strategies = pd.DataFrame([
                {"#": 1, "策略名稱": "20週均線+偏離過濾", "類型": "趨勢", "買入邏輯": "價>MA20且偏離2-3%", "賣出邏輯": "止盈止損", "已實作": "規劃中"},
                {"#": 2, "策略名稱": "DCA定額定投", "類型": "被動", "買入邏輯": "固定週期固定金額", "賣出邏輯": "止盈止損", "已實作": "✓"},
                {"#": 3, "策略名稱": "止盈止損", "類型": "風控", "買入邏輯": "—", "賣出邏輯": "虧X%止損/賺Y%止盈", "已實作": "✓"},
                {"#": 4, "策略名稱": "均線交叉", "類型": "趨勢", "買入邏輯": "短期MA上穿長期MA", "賣出邏輯": "短期MA下穿長期MA", "已實作": "規劃中"},
                {"#": 5, "策略名稱": "RSI超買超賣", "類型": "均值回歸", "買入邏輯": "RSI<30", "賣出邏輯": "RSI>70", "已實作": "規劃中"},
                {"#": 6, "策略名稱": "布林帶", "類型": "均值回歸", "買入邏輯": "價觸下軌", "賣出邏輯": "價觸上軌", "已實作": "規劃中"},
                {"#": 7, "策略名稱": "動量突破", "類型": "趨勢", "買入邏輯": "價突破N日高點", "賣出邏輯": "跌破N日低點", "已實作": "規劃中"},
                {"#": 8, "策略名稱": "價值平均", "類型": "被動", "買入邏輯": "依目標市值差額加碼", "賣出邏輯": "手動或止盈", "已實作": "規劃中"},
                {"#": 9, "策略名稱": "DCA+均線過濾", "類型": "混合", "買入邏輯": "固定週期買，僅當價>MA", "賣出邏輯": "止盈止損", "已實作": "規劃中"},
                {"#": 10, "策略名稱": "網格交易", "類型": "區間", "買入邏輯": "每跌X%買一檔", "賣出邏輯": "每漲X%賣一檔", "已實作": "規劃中"},
            ])
            df_strategies.to_excel(writer, sheet_name="策略總表", index=False)

            df_diversify = pd.DataFrame([
                {"組合": "NVDA + MSFT + PLTR + ARKK", "相關性": "高", "建議": "科技集中，可加 GLD、UNH 分散"},
                {"組合": "GLD + 任一股票", "相關性": "低", "建議": "分散佳"},
                {"組合": "UNH + 多數標的", "相關性": "低", "建議": "醫療分散效果佳"},
                {"組合": "ARKK + PAVE + SHOP", "相關性": "高", "建議": "三者高度同向，分散有限"},
            ])
            df_diversify.to_excel(writer, sheet_name="分散建議", index=False)

            df_avoid = pd.DataFrame([
                {"標的": "TRUMP / DJT", "原因": "波動極大"},
                {"標的": "SPCE、BNGO", "原因": "小盤股，流動性差"},
                {"標的": "RGTI、QUBT、QBTS、QSI", "原因": "量子股，市值小"},
                {"標的": "TQQQ", "原因": "3 倍槓桿"},
                {"標的": "加密貨幣", "原因": "初期不納入"},
            ])
            df_avoid.to_excel(writer, sheet_name="不建議納入", index=False)

            # 分散板塊
            df_diversify_sectors = pd.DataFrame([
                {"產業": "公用事業", "標的": "NEE, SO, DUK, XEL, AEP, SRE, XLU", "與科技相關性": "低～負", "說明": "最佳分散板塊"},
                {"產業": "消費必需品", "標的": "KO, PEP, WMT, PG, JNJ, XLP", "與科技相關性": "低～中", "說明": "防禦型"},
                {"產業": "能源", "標的": "XOM, CVX, XLE", "與科技相關性": "低", "說明": "與科技不同週期"},
                {"產業": "醫療", "標的": "UNH, JNJ, XLV", "與科技相關性": "中", "說明": "已有 UNH"},
            ])
            df_diversify_sectors.to_excel(writer, sheet_name="分散板塊", index=False)
        print(f"已匯出 Excel: {OUT_EXCEL}")

    if do_word:
        try:
            from docx import Document
            from docx.shared import Pt
            from docx.oxml.ns import qn
            from docx.oxml import OxmlElement

            doc = Document()
            doc.add_heading("eToro 交易策略整合總表", 0)
            doc.add_paragraph("整合策略規則、手續費、測試標的、相關性、基本面。供程式與人工決策參考。")

            def add_table_from_df(df, title):
                doc.add_heading(title, level=1)
                table = doc.add_table(rows=len(df) + 1, cols=len(df.columns))
                table.style = "Table Grid"
                for j, col in enumerate(df.columns):
                    table.rows[0].cells[j].text = str(col)
                for i, row in df.iterrows():
                    for j, col in enumerate(df.columns):
                        v = row[col]
                        table.rows[i + 1].cells[j].text = "" if pd.isna(v) else str(v)
                doc.add_paragraph("")

            df_full = pd.DataFrame(MASTER_DATA)
            add_table_from_df(df_full, "標的完整資訊")

            df_rules = pd.DataFrame([
                {"項目": "主要趨勢指標", "設定": "20 週均線"},
                {"項目": "過濾條件", "設定": "價格偏離均線 2–3% 以上"},
                {"項目": "策略類型", "設定": "低頻、規則式"},
                {"項目": "手續費（股票）", "設定": "$1／筆，來回 $2"},
                {"項目": "建議單筆", "設定": "≥ $300，理想 $500+"},
            ])
            add_table_from_df(df_rules, "策略與規則")

            df_diversify = pd.DataFrame([
                {"組合": "NVDA + MSFT + PLTR + ARKK", "相關性": "高", "建議": "科技集中，可加 GLD、UNH 分散"},
                {"組合": "GLD + 任一股票", "相關性": "低", "建議": "分散佳"},
            ])
            add_table_from_df(df_diversify, "分散建議")

            doc.save(OUT_WORD)
            print(f"已匯出 Word: {OUT_WORD}")
        except ImportError:
            print("Word 匯出需安裝: pip install python-docx")

    return 0


if __name__ == "__main__":
    sys.exit(main())
