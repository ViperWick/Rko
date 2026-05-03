# -*- coding: utf-8 -*-
"""
計算測試標的的報酬率相關性矩陣（使用 eToro K 線 API）
執行: python -m etoro_trading.scripts.calc_correlation
需安裝: pip install pandas
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAP_FILE = DATA_DIR / "instrument_ids.json"

# 測試標的（與 交易規則與參數.md 一致）
SYMBOLS = [
    "GLD", "NKE", "CRM", "IBM", "UNH",
    "PLTR", "MSFT", "NVDA", "ACN", "ARKK", "PAVE",
    "IONQ", "AMD", "SHOP",
]


def load_symbol_to_id() -> dict[str, int]:
    """從 instrument_ids.json 建立 symbol -> id 對照（取 internalSymbolFull 第一欄）"""
    mapping = {}
    if MAP_FILE.exists():
        data = json.loads(MAP_FILE.read_text(encoding="utf-8"))
        for iid, pair in data.items():
            if isinstance(pair, (list, tuple)) and len(pair) >= 1:
                sym = str(pair[0]).upper()
                mapping[sym] = int(iid)
    return mapping


def main():
    try:
        import pandas as pd
    except ImportError:
        print("請先安裝: pip install pandas")
        return 1

    try:
        from etoro_trading.core.etoro_client import EToroClient
        client = EToroClient()
    except Exception as e:
        print(f"連線失敗: {e}")
        return 1

    symbol_to_id = load_symbol_to_id()
    closes = {}  # symbol -> {date: close}

    print(f"從 eToro 取得 {len(SYMBOLS)} 檔標的過去 1 年日 K 線...")
    for i, sym in enumerate(SYMBOLS):
        sym_upper = sym.upper()
        try:
            iid = symbol_to_id.get(sym_upper)
            if iid is None:
                inst = client.search_instrument(sym_upper)
                if not inst:
                    print(f"  跳過 {sym}: 找不到標的")
                    continue
                iid = inst.get("instrumentId") or inst.get("instrumentID")
                symbol_to_id[sym_upper] = iid
                time.sleep(1.0)

            candles = client.get_candles(iid, interval="OneDay", count=365, direction="desc")
            if not candles:
                print(f"  跳過 {sym}: 無 K 線資料")
                continue

            # 轉成 date -> close
            series = {}
            for c in candles:
                from_date = c.get("fromDate", "")
                close = c.get("close")
                if from_date and close is not None:
                    try:
                        dt = pd.Timestamp(from_date).normalize()
                        series[dt] = float(close)
                    except Exception:
                        pass
            if series:
                closes[sym_upper] = series
                print(f"  + {sym}: {len(series)} 筆")
            else:
                print(f"  跳過 {sym}: 無有效收盤價")

            time.sleep(1.0)  # 限流
        except Exception as e:
            print(f"  跳過 {sym}: {e}")
        if (i + 1) % 5 == 0:
            print(f"  進度: {i+1}/{len(SYMBOLS)}")

    if len(closes) < 2:
        print("有效標的不足 2 檔，無法計算相關性")
        return 1

    # 合併成 DataFrame，以日期為 index
    df = pd.DataFrame(closes)
    df = df.sort_index()
    df = df.dropna(how="all").ffill().bfill()
    df = df.dropna(how="any")

    if len(df) < 30:
        print("有效交易日不足 30 天，無法計算相關性")
        return 1

    # 日報酬率
    ret = df.pct_change().dropna()
    corr = ret.corr()

    print("\n=== 報酬率相關性矩陣（eToro 日 K 線，過去 1 年） ===\n")
    print(corr.round(3).to_string())

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_file = DATA_DIR / "correlation_matrix.csv"
    corr.to_csv(out_file, encoding="utf-8-sig")
    print(f"\n已儲存至 {out_file}")

    valid = list(corr.columns)

    # 高相關對（>0.7）
    print("\n=== 高相關對（>0.7）===")
    high = []
    for i, a in enumerate(valid):
        for b in valid[i + 1 :]:
            v = corr.loc[a, b]
            if v > 0.7:
                high.append((a, b, round(v, 3)))
    for a, b, v in sorted(high, key=lambda x: -x[2]):
        print(f"  {a} - {b}: {v}")

    # 低相關對（<0.3）
    print("\n=== 低相關對（<0.3，分散佳）===")
    low = []
    for i, a in enumerate(valid):
        for b in valid[i + 1 :]:
            v = corr.loc[a, b]
            if v < 0.3:
                low.append((a, b, round(v, 3)))
    for a, b, v in sorted(low, key=lambda x: x[2])[:20]:
        print(f"  {a} - {b}: {v}")
    if len(low) > 20:
        print(f"  ... 共 {len(low)} 對")

    return 0


if __name__ == "__main__":
    sys.exit(main())
