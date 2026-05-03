# -*- coding: utf-8 -*-
"""
取得基本面與估值數據（營收、市值、P/E、P/S 等）
供策略估值參考。eToro 不提供此類數據，需用外部來源。
執行: python -m etoro_trading.scripts.fetch_fundamentals
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_FILE = DATA_DIR / "fundamentals.json"

SYMBOLS = [
    "GLD", "NKE", "CRM", "IBM", "UNH",
    "PLTR", "MSFT", "NVDA", "ACN", "ARKK", "PAVE",
    "IONQ", "AMD", "SHOP",
]


def fetch_via_yfinance(symbols: list[str]) -> list[dict]:
    """使用 yfinance 取得基本面（免 API key）"""
    try:
        import yfinance as yf
    except ImportError:
        raise ImportError("請安裝: pip install yfinance")

    results = []
    for sym in symbols:
        try:
            t = yf.Ticker(sym)
            info = t.info
            if not info or info.get("regularMarketPrice") is None:
                continue
            rev = info.get("totalRevenue") or info.get("revenue")
            rev_prev = info.get("revenueGrowth")  # 有時直接給 growth
            rev_growth = None
            if rev_prev is not None and isinstance(rev_prev, (int, float)):
                rev_growth = rev_prev
            # 若有年度財報可算 YoY
            try:
                inc = t.income_stmt
                if inc is not None and not inc.empty and "Total Revenue" in inc.index:
                    revs = inc.loc["Total Revenue"].dropna()
                    if len(revs) >= 2:
                        rev_growth = (revs.iloc[0] - revs.iloc[1]) / revs.iloc[1] if revs.iloc[1] else None
            except Exception:
                pass

            row = {
                "symbol": sym,
                "price": info.get("regularMarketPrice") or info.get("currentPrice"),
                "marketCap": info.get("marketCap"),
                "revenue": rev,
                "revenueGrowth": rev_growth,
                "peRatio": info.get("trailingPE") or info.get("forwardPE"),
                "priceToSales": info.get("priceToSalesTrailing12Months"),
                "trailingEps": info.get("trailingEps"),
            }
            results.append(row)
        except Exception as e:
            print(f"  跳過 {sym}: {e}")
    return results


def main():
    print("取得基本面與估值數據...")
    print("（eToro 不提供此類數據，使用外部來源）\n")

    try:
        data = fetch_via_yfinance(SYMBOLS)
    except ImportError as e:
        print(str(e))
        return 1

    if not data:
        print("無法取得任何數據")
        return 1

    # 輸出表格
    print(f"{'代碼':<6} {'股價':>10} {'市值(B)':>10} {'營收(B)':>10} {'營收增長':>10} {'P/E':>8} {'P/S':>8}")
    print("-" * 70)
    for r in data:
        price = r.get("price") or 0
        mc = (r.get("marketCap") or 0) / 1e9
        rev = (r.get("revenue") or 0) / 1e9
        gr = r.get("revenueGrowth")
        gr_str = f"{gr*100:.1f}%" if gr is not None else "—"
        pe = r.get("peRatio")
        pe_str = f"{pe:.1f}" if pe is not None else "—"
        ps = r.get("priceToSales")
        ps_str = f"{ps:.1f}" if ps is not None else "—"
        print(f"{r['symbol']:<6} {price:>10.2f} {mc:>10.2f} {rev:>10.2f} {gr_str:>10} {pe_str:>8} {ps_str:>8}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n已儲存至 {OUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
