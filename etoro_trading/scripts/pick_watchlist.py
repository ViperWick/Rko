# -*- coding: utf-8 -*-
"""
從目前持倉中挑選 5 檔適合做 20 週均線策略測試的標的
執行: python -m etoro_trading.scripts.pick_watchlist
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from etoro_trading.core.etoro_client import EToroClient
from etoro_trading.core.portfolio import get_positions

# 對照表路徑
MAP_FILE = Path(__file__).resolve().parent.parent / "data" / "instrument_ids.json"

# 內建常見標的（無 JSON 時使用）
DEFAULT_IDS = {
    100000: ("BTC", "Bitcoin"),
    100001: ("ETH", "Ethereum"),
    100017: ("ADA", "Cardano"),
    1839: ("CRM", "Salesforce"),
    1001: ("AAPL", "Apple"),
    1111: ("TSLA", "Tesla"),
    1137: ("NVDA", "NVIDIA"),
    1004: ("MSFT", "Microsoft"),
    1002: ("GOOG", "Google"),
    1005: ("AMZN", "Amazon"),
    1003: ("META", "Meta"),
}


def load_id_map():
    """載入對照表（JSON 優先，否則用內建）"""
    if MAP_FILE.exists():
        try:
            data = json.loads(MAP_FILE.read_text(encoding="utf-8"))
            return {int(k): tuple(v) for k, v in data.items()}
        except Exception:
            pass
    return dict(DEFAULT_IDS)


def main():
    try:
        client = EToroClient()
    except Exception as e:
        print(f"連線失敗: {e}")
        print("請確認 .env 已設定 ETORO_API_KEY 和 ETORO_USER_KEY")
        return 1

    positions = get_positions(client)
    if not positions:
        print("目前無持倉，無法挑選")
        return 1

    # 依金額彙總
    by_instrument = {}
    for p in positions:
        iid = p.get("instrument_id")
        if not iid:
            continue
        by_instrument[iid] = by_instrument.get(iid, 0) + p.get("amount", 0)

    sorted_ids = sorted(by_instrument.keys(), key=lambda x: by_instrument[x], reverse=True)[:5]

    # 載入對照表 + 少量 search 補齊未知的（加延遲避免限流）
    id_map = load_id_map()
    symbols_to_try = ["NEE", "XEL", "SO", "DUK", "D", "AEP", "SRE", "WEC", "ES", "EIX", "ED", "DTE", "PEG", "EXC", "AWK"]
    for s in symbols_to_try:
        if len([x for x in sorted_ids if x not in id_map]) == 0:
            break
        try:
            inst = client.search_instrument(s)
            if inst:
                iid = inst.get("instrumentId") or inst.get("instrumentID")
                if iid in sorted_ids and iid not in id_map:
                    id_map[iid] = (s, inst.get("instrumentDisplayName", inst.get("internalSymbolFull", s)))
            time.sleep(1)
        except Exception:
            pass

    print("=" * 50)
    print("從您持倉中挑選的 5 檔實驗觀察對象")
    print("（依持倉金額排序，適合做 20 週均線策略測試）")
    print("=" * 50)

    for i, iid in enumerate(sorted_ids, 1):
        amount = by_instrument[iid]
        if iid in id_map:
            sym, name = id_map[iid]
            print(f"\n{i}. {name} ({sym})")
        else:
            print(f"\n{i}. ID:{iid}")
        print(f"   持倉金額: ${amount:,.0f}")

    print("\n" + "=" * 50)
    print("以上 5 檔可作為 20 週均線策略的測試標的")
    return 0


if __name__ == "__main__":
    sys.exit(main())
