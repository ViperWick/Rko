# -*- coding: utf-8 -*-
"""
eToro Alpha Portfolios 定期追蹤

eToro 不提供投資組合持倉的公開 API，需手動在 alpha_portfolios.json 填入成分股。
此腳本用 yfinance 取得價格，計算各組合的模擬報酬並輸出報告。

使用方式：
  1. 編輯 etoro_trading/data/alpha_portfolios.json，在 symbols 填入各組合的成分股
  2. 執行：python -m etoro_trading.scripts.track_alpha_portfolios
  3. 可設定排程（如每週一）定期執行

成分股取得：登入 eToro → 投資組合 → 選擇組合 → 基本情況/持倉 分頁
"""
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CONFIG_FILE = DATA_DIR / "alpha_portfolios.json"
OUTPUT_FILE = DATA_DIR / "alpha_portfolios_tracking.json"
OUTPUT_CSV = DATA_DIR / "alpha_portfolios_tracking.csv"


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {"portfolios": []}
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))


def fetch_portfolio_return(symbols: list[str], lookback_days: int = 20) -> dict | None:
    """用 yfinance 取得等權重組合的報酬"""
    if not symbols:
        return None
    try:
        import yfinance as yf
        import pandas as pd
    except ImportError:
        print("請安裝: pip install yfinance pandas")
        return None

    symbols = [s.strip().upper() for s in symbols if s.strip()]
    if not symbols:
        return None

    try:
        # 逐檔下載較穩定
        closes = []
        for s in symbols:
            t = yf.Ticker(s)
            h = t.history(period=f"{lookback_days + 10}d")
            if h is not None and len(h) >= lookback_days and "Close" in h.columns:
                closes.append(h["Close"].rename(s))
        if not closes:
            return None

        close = pd.concat(closes, axis=1).ffill().bfill()
        close = close.tail(lookback_days)
        if close.isna().all().any() or (close <= 0).any().any():
            return None

        # 等權重日報酬累積
        ret = (close / close.shift(1)).fillna(1).mean(axis=1).prod() - 1
        return {
            "return_pct": ret * 100,
            "lookback_days": lookback_days,
            "symbols_count": len(symbols),
        }
    except Exception:
        return None


def run_tracking():
    config = load_config()
    portfolios = config.get("portfolios", [])
    if not portfolios:
        print("請先在 alpha_portfolios.json 填入各組合的 symbols")
        return

    results = []
    now = datetime.now().isoformat()[:19]

    for p in portfolios:
        pid = p.get("id", "")
        name = p.get("name", pid)
        symbols = p.get("symbols", [])
        if not symbols:
            results.append({
                "id": pid,
                "name": name,
                "return_20d_pct": None,
                "symbols_count": 0,
                "note": "未設定成分股，請從 eToro 頁面複製",
            })
            continue

        r = fetch_portfolio_return(symbols, lookback_days=20)
        if r:
            results.append({
                "id": pid,
                "name": name,
                "return_20d_pct": round(r["return_pct"], 2),
                "symbols_count": r["symbols_count"],
                "note": None,
            })
        else:
            results.append({
                "id": pid,
                "name": name,
                "return_20d_pct": None,
                "symbols_count": len(symbols),
                "note": "無法取得報酬（請確認代碼正確）",
            })

    report = {"updated_at": now, "portfolios": results}

    # 輸出 JSON
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已輸出：{OUTPUT_FILE}")

    # 輸出 CSV（方便匯入試算表）
    try:
        import csv
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["組合", "近 20 日報酬 %", "成分股數", "備註", "更新時間"])
            for r in results:
                w.writerow([
                    r["name"],
                    r["return_20d_pct"] if r["return_20d_pct"] is not None else "",
                    r["symbols_count"],
                    r["note"] or "",
                    now,
                ])
        print(f"已輸出：{OUTPUT_CSV}")
    except Exception as e:
        print(f"CSV 輸出失敗：{e}")

    # 顯示摘要
    print("\n【Alpha Portfolios 追蹤摘要】")
    print(f"更新時間：{now}")
    for r in results:
        ret_str = f"{r['return_20d_pct']:+.1f}%" if r["return_20d_pct"] is not None else "—"
        print(f"  {r['name']}: {ret_str} ({r['symbols_count']} 檔)")
    return report


if __name__ == "__main__":
    run_tracking()
