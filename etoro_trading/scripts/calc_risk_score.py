# -*- coding: utf-8 -*-
"""
計算投資組合風險評分（0-100）
執行: python -m etoro_trading.scripts.calc_risk_score
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CORR_FILE = DATA_DIR / "correlation_matrix.csv"


def fetch_portfolio_data():
    """取得持倉彙總（與 list_positions 相同邏輯）"""
    try:
        from etoro_trading.core.etoro_client import EToroClient
        from etoro_trading.core.portfolio import get_balance, get_positions
        from etoro_trading.core.instrument_map import resolve_ids
    except ImportError as e:
        print(f"Import error: {e}")
        return None
    try:
        client = EToroClient()
        balance = get_balance(client)
        positions = get_positions(client)
    except Exception as e:
        print(f"API error: {e}")
        return None
    by_inst = {}
    for p in positions:
        iid = p.get("instrument_id")
        if not iid:
            continue
        if iid not in by_inst:
            by_inst[iid] = {"amount": 0, "pnl": 0, "count": 0}
        by_inst[iid]["amount"] += p.get("amount", 0) or 0
        by_inst[iid]["pnl"] += p.get("pnl", 0) or 0
        by_inst[iid]["count"] += 1
    ids = list(by_inst.keys())
    id_to_symbol, id_to_name = resolve_ids(client, ids)
    total_amount = sum(d["amount"] for d in by_inst.values())
    total_pnl = sum(d["pnl"] for d in by_inst.values())
    unrealized = balance.get("unrealized_pnl", 0) or 0
    if total_amount and total_pnl == 0 and unrealized != 0:
        for d in by_inst.values():
            d["_alloc_pnl"] = (d["amount"] / total_amount) * unrealized
    else:
        for d in by_inst.values():
            d["_alloc_pnl"] = d["pnl"]
    by_symbol = []
    for iid, d in by_inst.items():
        amt, pnl = d["amount"], d["_alloc_pnl"]
        cv = amt + pnl
        pnl_pct = round((pnl / amt * 100), 1) if amt else 0.0
        by_symbol.append({
            "symbol": id_to_symbol.get(iid, f"ID:{iid}"),
            "name": id_to_name.get(iid, ""),
            "amount": round(amt, 2),
            "pnl": round(pnl, 2),
            "current_value": round(cv, 2),
            "pnl_pct": pnl_pct,
            "positions": d["count"],
        })
    by_symbol.sort(key=lambda x: -x["amount"])
    cash = balance.get("credit", 0)
    total_equity = cash + sum(r["current_value"] for r in by_symbol)
    return {
        "by_symbol": by_symbol,
        "cash": cash,
        "total_equity": total_equity,
        "total_unrealized_pnl": unrealized,
    }


def main():
    data = fetch_portfolio_data()
    if not data:
        print("無法取得持倉，請確認 eToro API 連線")
        return 1
    from etoro_trading.core.risk_score import calc_risk_score

    result = calc_risk_score(
        by_symbol=data["by_symbol"],
        cash=data["cash"],
        total_equity=data["total_equity"],
        total_unrealized_pnl=data.get("total_unrealized_pnl", 0),
        correlation_file=CORR_FILE if CORR_FILE.exists() else None,
    )

    print("=" * 60)
    print("投資組合風險評分")
    print("=" * 60)
    print(f"\n綜合風險分數: {result.overall:.1f} / 100  →  {result.summary}")
    print("\n各維度:")
    for d in result.dimensions:
        bar = "#" * int(d.score / 10) + "-" * (10 - int(d.score / 10))
        print(f"  [{bar}] {d.score:5.1f}  {d.name}")
        print(f"       {d.detail}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
