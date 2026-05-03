# -*- coding: utf-8 -*-
"""
匯出持倉依標的彙總（供檢視資產）
執行: python -m etoro_trading.scripts.export_portfolio_summary
查不到的 ID 會向 eToro API 查詢，並自動寫入 instrument_ids.json 作為本地資料庫
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from etoro_trading.core.etoro_client import EToroClient
from etoro_trading.core.instrument_map import resolve_ids
from etoro_trading.core.portfolio import get_balance, get_positions


def main():
    client = EToroClient()
    balance = get_balance(client)
    positions = get_positions(client)

    # 依 instrument_id 彙總
    by_inst = {}
    for p in positions:
        iid = p.get("instrument_id")
        if not iid:
            continue
        if iid not in by_inst:
            by_inst[iid] = {"amount": 0, "pnl": 0, "count": 0}
        by_inst[iid]["amount"] += p.get("amount", 0)
        by_inst[iid]["pnl"] += p.get("pnl", 0)
        by_inst[iid]["count"] += 1

    # 取得 symbol 對照：先載入本地，查不到的 ID 向 API 查詢並寫入 instrument_ids.json
    ids = list(by_inst.keys())
    id_to_symbol, id_to_name = resolve_ids(client, ids)

    # 彙總表（含投入金額、損益、預估淨值）
    rows = []
    total_amount = sum(d["amount"] for d in by_inst.values())
    unrealized = balance.get("unrealized_pnl", 0)
    # 當個別 pnl 為 0 時，依投入比例分攤總損益以估算淨值
    for iid, data in by_inst.items():
        sym = id_to_symbol.get(iid, f"ID:{iid}")
        amt = data["amount"]
        pnl = data["pnl"]
        if pnl != 0:
            current_value = amt + pnl
        elif total_amount > 0 and unrealized != 0:
            current_value = amt + (amt / total_amount) * unrealized
        else:
            current_value = amt
        # 損益% 優先用 API 的 pnl（保留正負）；若 pnl=0 則用淨值反推
        if amt and pnl != 0:
            pnl_pct_val = round((pnl / amt * 100), 1)
        elif amt and current_value is not None:
            pnl_pct_val = round((current_value - amt) / amt * 100, 1)
        else:
            pnl_pct_val = 0
        rows.append({
            "symbol": sym,
            "name": id_to_name.get(iid, ""),
            "amount": round(amt, 2),
            "pnl": round(pnl, 2),
            "current_value": round(current_value, 2),
            "positions": data["count"],
            "pnl_pct": pnl_pct_val,
        })

    # 依金額排序
    rows.sort(key=lambda x: x["amount"], reverse=True)

    # 輸出
    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "portfolio_summary.json"
    total_amount = sum(r["amount"] for r in rows)
    result = {
        "balance": balance,
        "total_positions_value": round(total_amount, 2),
        "total_equity": round(balance["credit"] + total_amount, 2),
        "cash_pct": round(balance["credit"] / (balance["credit"] + total_amount) * 100, 1) if (balance["credit"] + total_amount) > 0 else 100,
        "by_symbol": rows[:80],
    }
    out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已匯出: {out_file}")
    print(f"\n可用餘額: ${balance['credit']:,.2f}")
    print(f"未實現損益: ${balance['unrealized_pnl']:,.2f}")
    print(f"持倉市值約: ${total_amount:,.2f}")
    print(f"總資產約: ${result['total_equity']:,.2f}")
    print(f"現金比例: {result['cash_pct']}%")
    print(f"\n前 50 檔持倉（依金額）:")
    print("-" * 70)
    for i, r in enumerate(rows[:50], 1):
        pnl_str = f"+${r['pnl']:,.0f}" if r['pnl'] >= 0 else f"-${abs(r['pnl']):,.0f}"
        print(f"  {i:2}. {r['symbol']:8} | 投入 ${r['amount']:>8,.0f} | 淨值 ${r['current_value']:>8,.0f} | 損益 {pnl_str:>12} ({r['pnl_pct']:>6}%) | {r['positions']} 筆")
    return 0


if __name__ == "__main__":
    sys.exit(main())
