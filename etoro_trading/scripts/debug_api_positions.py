# -*- coding: utf-8 -*-
"""
Debug: 印出 eToro API 持倉的原始欄位，確認是否有 pnL 等
稽核: 比對程式碼讀取的欄位與 API 實際回傳
執行: python -m etoro_trading.scripts.debug_api_positions
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


def _type_str(v):
    if v is None:
        return "None"
    if isinstance(v, dict):
        return f"dict(keys={list(v.keys())[:8]}{'...' if len(v) > 8 else ''})"
    if isinstance(v, list):
        return f"list(len={len(v)})"
    return f"{type(v).__name__}({repr(v)[:50]})"


def main():
    try:
        from etoro_trading.core.etoro_client import EToroClient
        from etoro_trading.core.portfolio import get_balance, get_positions, get_orders
    except Exception as e:
        print("Import error:", e)
        return 1
    try:
        client = EToroClient()
        data = client.get_portfolio()
    except Exception as e:
        print("API error:", e)
        return 1

    # ---------- 1. 頂層結構 ----------
    print("=" * 70)
    print("1. API 頂層 keys（實際回傳）")
    print("=" * 70)
    top_keys = list(data.keys())
    print("  ", top_keys)
    for k in ["credits", "credit", "clientPortfolio"]:
        if k in data:
            v = data[k]
            print(f"  data[{k!r}] = {_type_str(v)}")

    cp = data.get("clientPortfolio", {})
    if cp:
        print("\n  clientPortfolio keys:", list(cp.keys())[:25])
        # 文件用 credits，程式用 credit
        credit_val = cp.get("credit") or cp.get("credits")
        credits_val = data.get("credits") if "credits" in data else None
        print(f"  clientPortfolio.credit = {credit_val!r}")
        print(f"  data.credits (文件範例) = {credits_val!r}")
        upnl = cp.get("unrealizedPnL")
        print(f"  clientPortfolio.unrealizedPnL = {_type_str(upnl)}")
        if isinstance(upnl, dict) and "pnL" in upnl:
            print("    -> WARNING: unrealizedPnL 是物件！程式預期為數字，會得到 0 或錯誤")

    # ---------- 2. get_balance 使用的欄位 ----------
    print("\n" + "=" * 70)
    print("2. get_balance 對照")
    print("=" * 70)
    balance = get_balance(client)
    print("  程式輸出: credit=%s, unrealized_pnl=%s, positions_count=%s, orders_count=%s" % (
        balance.get("credit"), balance.get("unrealized_pnl"),
        balance.get("positions_count"), balance.get("orders_count")))
    direct = len(cp.get("positions", []))
    mirror_pos = sum(len(m.get("positions", [])) for m in cp.get("mirrors", []))
    total_pos = direct + mirror_pos
    print("  實際持倉數: cp.positions=%d, mirrors.positions 合計=%d, 總計=%d" % (direct, mirror_pos, total_pos))
    if balance.get("positions_count") != total_pos:
        print("  -> 差異: positions_count 未包含 mirror 持倉，目前僅算 cp.positions")

    # ---------- 3. 持倉欄位對照 ----------
    print("\n" + "=" * 70)
    print("3. Position 欄位對照（第一筆持倉）")
    print("=" * 70)
    positions = list(cp.get("positions", []))
    for m in cp.get("mirrors", []):
        positions.extend(m.get("positions", []))
    if positions:
        p = positions[0]
        checks = [
            ("positionId / positionID", p.get("positionId") or p.get("positionID")),
            ("instrumentId / instrumentID", p.get("instrumentId") or p.get("instrumentID")),
            ("amount", p.get("amount")),
            ("unrealizedPnL 型別", type(p.get("unrealizedPnL")).__name__),
            ("unrealizedPnL.pnL", p.get("unrealizedPnL", {}).get("pnL") if isinstance(p.get("unrealizedPnL"), dict) else "N/A"),
        ]
        for label, val in checks:
            print("  %s: %s" % (label, val))
        print("  完整 keys:", list(p.keys()))

    # ---------- 4. Orders 結構 ----------
    print("\n" + "=" * 70)
    print("4. Orders 結構")
    print("=" * 70)
    orders_raw = cp.get("orders", [])
    ofo = cp.get("ordersForOpen", [])
    ofc = cp.get("ordersForClose", [])
    print("  orders: %d 筆" % len(orders_raw))
    print("  ordersForOpen: %d 筆" % len(ofo))
    print("  ordersForClose: %d 筆" % len(ofc))
    if ofo and len(ofo) > 0:
        print("  ordersForOpen[0] keys:", list(ofo[0].keys())[:12])

    # ---------- 5. 彙總問題清單 ----------
    print("\n" + "=" * 70)
    print("5. 稽核結論（可能問題）")
    print("=" * 70)
    issues = []
    if balance.get("positions_count") != total_pos:
        issues.append("positions_count 未含 mirror 持倉")
    upnl_cp = cp.get("unrealizedPnL")
    if isinstance(upnl_cp, dict):
        issues.append("clientPortfolio.unrealizedPnL 是物件，get_balance 用 cp.get('unrealizedPnL',0) 可能得到錯誤值")
    if not issues:
        print("  未發現明顯問題")
    else:
        for i, t in enumerate(issues, 1):
            print("  [%d] %s" % (i, t))
    return 0


if __name__ == "__main__":
    sys.exit(main())
