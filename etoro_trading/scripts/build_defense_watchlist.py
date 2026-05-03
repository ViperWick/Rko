# -*- coding: utf-8 -*-
"""
建立防務板塊 eToro 自選股
1. 查詢 eToro 是否有這些標的
2. 匯出 JSON（含 instrument_id）與 CSV 供策略使用
執行: python -m etoro_trading.scripts.build_defense_watchlist
"""
import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
WATCHLIST_JSON = DATA_DIR / "defense_sector_watchlist.json"
OUT_JSON = DATA_DIR / "defense_sector_etoro.json"
OUT_CSV = DOCS_DIR / "defense_sector_etoro.csv"


def load_watchlist() -> dict:
    path = WATCHLIST_JSON
    if not path.exists():
        print("缺少 defense_sector_watchlist.json")
        return {"companies": []}
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_on_etoro(client, candidates: list[str]) -> dict | None:
    """依序嘗試 symbol_candidates，回傳第一個找到的 instrument"""
    for sym in candidates:
        try:
            inst = client.search_instrument(sym)
            if inst and (inst.get("instrumentId") or inst.get("instrumentID")):
                return inst
        except Exception:
            pass
        time.sleep(0.5)
    return None


def main():
    try:
        from etoro_trading.core.etoro_client import EToroClient
    except ImportError as e:
        print(f"Import error: {e}")
        return 1
    try:
        client = EToroClient()
    except Exception as e:
        print(f"API 連線失敗: {e}")
        return 1

    data = load_watchlist()
    companies = data.get("companies", [])
    if not companies:
        print("無公司清單可查詢")
        return 1

    found = []
    for c in companies:
        name = c.get("name", "")
        candidates = c.get("symbol_candidates", [])
        inst = resolve_on_etoro(client, candidates) if candidates else None
        if inst:
            iid = inst.get("instrumentId") or inst.get("instrumentID")
            sym = inst.get("internalSymbolFull", candidates[0] if candidates else "")
            found.append({
                "country": c.get("country", ""),
                "name": name,
                "products": c.get("products", ""),
                "role": c.get("role", ""),
                "symbol": sym,
                "instrument_id": iid,
            })
            print(f"  + {name}: {sym} (ID {iid})")
        else:
            print(f"  - {name}: 找不到")
        time.sleep(1.0)

    # 更新 watchlist 的 resolved 欄位
    data["resolved"] = found
    data["updated_at"] = time.strftime("%Y-%m-%d")

    # 匯出 JSON
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n已匯出 JSON: {OUT_JSON}")

    # 匯出 CSV
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    if found:
        with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["country", "name", "symbol", "instrument_id", "products", "role"])
            w.writeheader()
            w.writerows(found)
        print(f"已匯出 CSV: {OUT_CSV}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
