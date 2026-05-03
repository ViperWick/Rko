# -*- coding: utf-8 -*-
"""
檢查昨日持倉標的的價格變動，並依策略規則給出建議
執行: python -m etoro_trading.scripts.check_yesterday_changes
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    import yfinance as yf
    import pandas as pd
    HAS_YF = True
except ImportError:
    HAS_YF = False

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PORTFOLIO_FILE = DATA_DIR / "portfolio_summary.json"

# eToro 符號 → yfinance 符號對照（部分需轉換）
SYMBOL_MAP = {
    "TEP.PA": "TEP.PA",   # 巴黎
    "SAP.DE": "SAP.DE",   # 法蘭克福
    "RDW.US": "RDW",      # 美國
    "SOL": "SOL-USD",     # Solana 加密貨幣
    "STRK": "STRK-USD",   # Starknet
    "SUI": "SUI-USD",     # Sui
    "FET": "FET-USD",     # Fetch.ai
    "NEAR": "NEAR-USD",   # Near
    "HBAR": "HBAR-USD",   # Hedera
    "ALGO": "ALGO-USD",   # Algorand
    "XLM": "XLM-USD",     # Stellar
    "TRX": "TRX-USD",     # Tron
    "XRP": "XRP-USD",     # Ripple
}


def get_yf_symbol(sym: str) -> str:
    """轉換為 yfinance 可查詢的符號"""
    return SYMBOL_MAP.get(sym, sym)


def fetch_yesterday_changes(symbols: list[str], top_n: int = 30) -> list[dict]:
    """取得昨日各標的的價格變動"""
    if not HAS_YF:
        return []

    results = []
    # 取最近 5 個交易日以確保有昨日資料
    end_date = datetime.now()
    start_date = end_date - timedelta(days=10)

    for sym in symbols[:top_n]:
        yf_sym = get_yf_symbol(sym)
        try:
            ticker = yf.Ticker(yf_sym)
            hist = ticker.history(start=start_date, end=end_date)
            if hist is None or len(hist) < 2:
                results.append({"symbol": sym, "change_pct": None, "error": "無足夠資料"})
                continue

            hist = hist.sort_index()
            # 取最近兩個交易日
            last_two = hist.tail(2)
            if len(last_two) < 2:
                results.append({"symbol": sym, "change_pct": None, "error": "交易日不足"})
                continue

            prev_close = last_two.iloc[-2]["Close"]
            curr_close = last_two.iloc[-1]["Close"]
            if prev_close and prev_close > 0:
                change_pct = (curr_close / prev_close - 1) * 100
                results.append({
                    "symbol": sym,
                    "change_pct": round(change_pct, 2),
                    "prev_close": prev_close,
                    "curr_close": curr_close,
                })
            else:
                results.append({"symbol": sym, "change_pct": None, "error": "價格異常"})
        except Exception as e:
            results.append({"symbol": sym, "change_pct": None, "error": str(e)[:50]})

    return results


def main():
    if not PORTFOLIO_FILE.exists():
        print("找不到 portfolio_summary.json，請先執行 export_portfolio_summary")
        return 1

    data = json.loads(PORTFOLIO_FILE.read_text(encoding="utf-8"))
    by_symbol = data.get("by_symbol", [])
    symbols = [r["symbol"] for r in by_symbol]

    print("=" * 70)
    print("eToro 持倉 — 昨日價格變動與策略建議")
    print("=" * 70)
    print(f"\n總資產: ${data.get('total_equity', 0):,.2f}")
    print(f"現金比例: {data.get('cash_pct', 0)}%")
    print(f"未實現損益: ${data.get('balance', {}).get('unrealized_pnl', 0):,.2f}")
    print()

    if not HAS_YF:
        print("請安裝 yfinance: pip install yfinance")
        return 1

    print("正在取得昨日價格變動（前 40 檔）...")
    changes = fetch_yesterday_changes(symbols, top_n=40)

    # 分類
    gainers = [c for c in changes if c.get("change_pct") is not None and c["change_pct"] > 0]
    losers = [c for c in changes if c.get("change_pct") is not None and c["change_pct"] < 0]
    flat = [c for c in changes if c.get("change_pct") is not None and c["change_pct"] == 0]
    errors = [c for c in changes if c.get("change_pct") is None]

    # 依變動幅度排序
    gainers.sort(key=lambda x: x["change_pct"], reverse=True)
    losers.sort(key=lambda x: x["change_pct"])

    print("\n" + "-" * 70)
    print("[+] 昨日上漲（前 15）")
    print("-" * 70)
    for c in gainers[:15]:
        print(f"  {c['symbol']:10} +{c['change_pct']:>6.2f}%")

    print("\n" + "-" * 70)
    print("[-] 昨日下跌（前 15）")
    print("-" * 70)
    for c in losers[:15]:
        print(f"  {c['symbol']:10} {c['change_pct']:>6.2f}%")

    if errors:
        print(f"\n（{len(errors)} 檔無法取得資料，多為非美股或特殊標的）")

    # 策略建議
    print("\n" + "=" * 70)
    print("策略建議（依您的規則）")
    print("=" * 70)

    cash_pct = data.get("cash_pct", 0)
    balance = data.get("balance", {})

    print("\n【現金本位】")
    if cash_pct >= 25:
        print("  [OK] 現金 >= 25% -> 不止盈，可執行 ETF / 槓桿 ETF 加倉")
    elif cash_pct < 15:
        print("  [!] 現金 < 15% -> 需止盈補充現金，優先賣出獲利 >= 20% 的持倉，保留 1/3")
    else:
        print("  [*] 現金 15-25% -> 觀察中，現金不足時再止盈")

    print("\n【資產區塊動作】")
    print("  • 股票：只減不加 — 不新開倉，止盈時減倉")
    print("  • ETF：加倉 — 價 > MA60 且偏離 ≥ 2% 時順勢加碼")
    print("  • 槓桿 ETF (TQQQ 等)：加倉 — 回撤 25%/35%/45% 分批買跌")
    print("  • 加密貨幣：暫不動 — 質押利息，不加倉")

    print("\n【依昨日變動的具體建議】")
    # 找出持倉中的 ETF
    etf_list = ["GLD", "QYLD", "ARKK", "PAVE", "ARKX", "WQTM", "UEC", "TQQQ", "SOXL", "CQQQ", "KWEB", "ARKF", "COPX", "CLOU", "URA", "SLV"]
    portfolio_etfs = [s for s in symbols if s in etf_list]

    if portfolio_etfs:
        print(f"  持倉中的 ETF：{', '.join(portfolio_etfs[:10])}")
        etf_changes = {c["symbol"]: c["change_pct"] for c in changes if c["symbol"] in etf_list and c.get("change_pct") is not None}
        for sym, chg in sorted(etf_changes.items(), key=lambda x: x[1]):
            if chg < -3:
                print(f"    - {sym}: 昨跌 {chg:.1f}% -> 若接近底部有止跌訊號，可分批加碼")
            elif chg > 5:
                print(f"    - {sym}: 昨漲 {chg:.1f}% -> 漲多不追，等回調或 MA60 順勢訊號")
    else:
        print("  持倉以股票與加密貨幣為主，ETF 較少")

    # 股票減倉建議（依持倉分析）
    reduce_candidates = ["NKE", "BBBY", "PLUG", "BLNK", "TDOC", "PYPL"]
    in_portfolio = [s for s in reduce_candidates if s in symbols]
    if in_portfolio:
        print(f"\n  減倉候選（依持倉分析）：{', '.join(in_portfolio)}")
        print("    -> 現金不足時，優先止盈這些獲利 >= 20% 的標的")

    print("\n【本週可執行】")
    if cash_pct < 15:
        print("  1. 檢視是否有獲利 ≥ 20% 的持倉可止盈（保留 1/3）")
        print("  2. 暫停 DCA，先補充現金")
    elif cash_pct >= 25:
        print("  1. 檢查 GLD、ARKK、PAVE 等 ETF 的 MA60 訊號")
        print("  2. 若有順勢訊號（價 > MA60 且偏離 ≥ 2%），可執行 DCA")
        print("  3. 檢查 TQQQ、SOXL 是否達回撤門檻（買跌）")
    else:
        print("  1. 維持觀察，現金 15–25% 區間")
        print("  2. 每週檢查持倉與止盈觸及狀況")

    print("\n" + "=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
