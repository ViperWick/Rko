# -*- coding: utf-8 -*-
"""
List positions and take-profit candidates (profit >= 20%).
Prefers live API data (per-position pnl) for correct PnL%; falls back to portfolio_summary.json.
Run: python -m etoro_trading.scripts.list_positions_and_tp_candidates
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
SUMMARY_FILE = DATA_DIR / "portfolio_summary.json"

TAKE_PROFIT_PCT = 20.0


def fetch_from_api():
    """從 eToro API 直接讀取持倉，用每筆的 pnl 計算損益%（正確來源）"""
    try:
        from etoro_trading.core.etoro_client import EToroClient
        from etoro_trading.core.portfolio import get_balance, get_positions
        from etoro_trading.core.instrument_map import resolve_ids
    except Exception:
        return None
    try:
        client = EToroClient()
        balance = get_balance(client)
        positions = get_positions(client)
    except Exception:
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
    if total_amount and (total_pnl == 0 and unrealized != 0):
        for iid, d in by_inst.items():
            d["_alloc_pnl"] = (d["amount"] / total_amount) * unrealized
    else:
        for iid, d in by_inst.items():
            d["_alloc_pnl"] = d["pnl"]
    by_symbol = []
    for iid, d in by_inst.items():
        amt = d["amount"]
        pnl = d["_alloc_pnl"]
        current_value = amt + pnl
        pnl_pct = round((pnl / amt * 100), 1) if amt else 0.0
        by_symbol.append({
            "symbol": id_to_symbol.get(iid, "ID:" + str(iid)),
            "name": id_to_name.get(iid, ""),
            "amount": round(amt, 2),
            "pnl": round(pnl, 2),
            "current_value": round(current_value, 2),
            "positions": d["count"],
            "pnl_pct": pnl_pct,
        })
    by_symbol.sort(key=lambda x: -x["amount"])
    cash = balance.get("credit", 0)
    total_equity = cash + sum(r["current_value"] for r in by_symbol)
    cash_pct = round(cash / total_equity * 100, 1) if total_equity else 0
    for r in by_symbol:
        r["pnl_share_pct"] = round((r["pnl"] / unrealized * 100), 1) if unrealized != 0 else 0
    return {
        "balance": dict(balance, credit=cash),
        "by_symbol": by_symbol,
        "total_equity": round(total_equity, 2),
        "cash_pct": cash_pct,
        "total_unrealized_pnl": unrealized,
        "source": "api",
    }


def load_summary():
    if not SUMMARY_FILE.exists():
        print("Not found:", SUMMARY_FILE)
        print("Run first: python -m etoro_trading.scripts.export_portfolio_summary")
        return None
    return json.loads(SUMMARY_FILE.read_text(encoding="utf-8"))


def get_pnl_pct(row):
    """PnL%: prefer API pnl (keep sign), else derive from current_value."""
    amt = row.get("amount") or 0
    if amt <= 0:
        return 0.0
    pnl = row.get("pnl")
    if pnl is not None and pnl != 0:
        return round(pnl / amt * 100, 1)
    cv = row.get("current_value")
    if cv is not None:
        return round((cv - amt) / amt * 100, 1)
    return 0.0


def main():
    data = fetch_from_api()
    if not data:
        data = load_summary()
        if not data:
            return 1
        data["source"] = "json"
    balance = data.get("balance", {})
    total_unreal = data.get("total_unrealized_pnl") or balance.get("unrealized_pnl", 0) or 0
    if data.get("source") == "json":
        for row in data.get("by_symbol", []):
            row["pnl_pct"] = get_pnl_pct(row)
            pnl_d = row.get("pnl") if row.get("pnl") != 0 else (row.get("current_value", 0) - row.get("amount", 0))
            row["pnl"] = pnl_d
            row["pnl_share_pct"] = round((pnl_d / total_unreal * 100), 1) if total_unreal != 0 else 0
    by_symbol = data.get("by_symbol", [])
    cash = balance.get("credit", 0)
    total_equity = data.get("total_equity", 0) or (cash + sum(r.get("current_value", r.get("amount", 0)) for r in by_symbol))
    cash_pct = data.get("cash_pct") if "cash_pct" in data else (round(cash / total_equity * 100, 1) if total_equity else 0)
    if data.get("source") == "api":
        print("(Data from eToro API, PnL% from position pnl)")
    else:
        print("(Data from portfolio_summary.json)")

    for row in by_symbol:
        row["pnl_pct"] = get_pnl_pct(row)

    tp_candidates = [r for r in by_symbol if (r.get("pnl_pct") or 0) >= TAKE_PROFIT_PCT]
    positive_pct = [r for r in by_symbol if 0 <= (r.get("pnl_pct") or 0) < TAKE_PROFIT_PCT]
    negative_pct = [r for r in by_symbol if (r.get("pnl_pct") or 0) < 0]
    tp_candidates.sort(key=lambda x: -(x.get("pnl_pct") or 0))
    positive_pct.sort(key=lambda x: -(x.get("pnl_pct") or 0))
    negative_pct.sort(key=lambda x: -(x.get("pnl_pct") or 0))

    def print_rows(rows, with_name=False):
        for i, r in enumerate(rows, 1):
            pct = r.get("pnl_pct") or 0
            share = r.get("pnl_share_pct", 0) or 0
            pnl_d = r.get("pnl", 0) or 0
            if with_name:
                print("  {:2}. {:10} {:22} | amount ${:>8,.0f} | value ${:>8,.0f} | PnL ${:>8,.0f} | {:>+5.1f}% | 佔總{:>5.1f}% | {} 筆".format(
                    i, r["symbol"], (r.get("name") or "")[:22], r["amount"], r["current_value"], pnl_d, pct, share, r.get("positions", 0)))
            else:
                print("  {:2}. {:10} | amount ${:>8,.0f} | value ${:>8,.0f} | PnL ${:>8,.0f} | {:>+5.1f}% | 佔總{:>5.1f}% | {} 筆".format(
                    i, r["symbol"], r["amount"], r["current_value"], pnl_d, pct, share, r.get("positions", 0)))

    print("=" * 72)
    print("eToro positions: [1] Take-profit candidates | [2] Positive % | [3] Negative %")
    print("=" * 72)
    total_unreal = data.get("total_unrealized_pnl") or balance.get("unrealized_pnl", 0) or 0
    print("\n[Account]")
    print("  Cash: ${:,.2f}".format(cash))
    print("  Total Unrealized PnL: ${:,.2f}".format(total_unreal))
    print("  Equity: ${:,.2f}".format(total_equity))
    print("  Cash %: {}%".format(cash_pct))
    print("  Symbols: {}".format(len(by_symbol)))
    print("\n[Rule] Cash < 15% and position profit >= {}% -> take profit, keep 1/3".format(TAKE_PROFIT_PCT))
    print("  Current cash {}% -> ".format(cash_pct), end="")
    if cash_pct >= 25:
        print(">= 25%, no TP.")
    elif cash_pct < 15:
        print("< 15%, consider TP.")
    else:
        print("15-25%.")

    print("\n" + "-" * 72)
    print("1. Take-profit candidates (profit >= {}%)  count: {}".format(TAKE_PROFIT_PCT, len(tp_candidates)))
    print("-" * 72)
    if not tp_candidates:
        print("  (none)")
    else:
        print_rows(tp_candidates, with_name=True)

    print("\n" + "-" * 72)
    print("2. Positive % (profit but < {}%)  count: {}".format(TAKE_PROFIT_PCT, len(positive_pct)))
    print("-" * 72)
    if not positive_pct:
        print("  (none)")
    else:
        print_rows(positive_pct)

    print("\n" + "-" * 72)
    print("3. Negative % (loss)  count: {}".format(len(negative_pct)))
    print("-" * 72)
    if not negative_pct:
        print("  (none)")
    else:
        print_rows(negative_pct)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    md_path = DOCS_DIR / "positions_and_tp_list.md"
    lines = [
        "# eToro positions and take-profit list",
        "",
        "Generated by list_positions_and_tp_candidates.py",
        "",
        "## Account",
        "",
        "- Cash: ${:,.2f}".format(cash),
        "- Equity: ${:,.2f}".format(total_equity),
        "- Cash %: {}%".format(cash_pct),
        "- Symbols: {}".format(len(by_symbol)),
        "",
        "## Rule: Cash < 15% and profit >= {}% -> TP, keep 1/3".format(TAKE_PROFIT_PCT),
        "",
        "---",
        "",
        "## 1. Take-profit candidates (profit >= 20%)",
        "",
        "| # | Symbol | Name | Amount | Value | PnL(USD) | PnL% | 佔總盈虧% | Positions |",
        "|---|--------|------|--------|-------|----------|------|-----------|------------|",
    ]
    for i, r in enumerate(tp_candidates, 1):
        pct = r.get("pnl_pct") or 0
        share = r.get("pnl_share_pct", 0) or 0
        pnl_d = r.get("pnl", 0) or 0
        lines.append("| {} | {} | {} | {:,.0f} | {:,.0f} | {:,.0f} | {:+.1f}% | {}% | {} |".format(
            i, r["symbol"], r.get("name", ""), r["amount"], r["current_value"], pnl_d, pct, share, r.get("positions", 0)))
    if not tp_candidates:
        lines.append("| (none) | | | | | | |")

    lines.extend([
        "",
        "## 2. Positive % (profit but < 20%)",
        "",
        "| # | Symbol | Amount | Value | PnL(USD) | PnL% | 佔總盈虧% | Positions |",
        "|---|--------|--------|-------|----------|------|-----------|------------|",
    ])
    for i, r in enumerate(positive_pct, 1):
        pct = r.get("pnl_pct") or 0
        share = r.get("pnl_share_pct", 0) or 0
        pnl_d = r.get("pnl", 0) or 0
        lines.append("| {} | {} | {:,.0f} | {:,.0f} | {:,.0f} | {:+.1f}% | {}% | {} |".format(
            i, r["symbol"], r["amount"], r["current_value"], pnl_d, pct, share, r.get("positions", 0)))
    if not positive_pct:
        lines.append("| (none) | | | | | |")

    lines.extend([
        "",
        "## 3. Negative % (loss)",
        "",
        "| # | Symbol | Amount | Value | PnL(USD) | PnL% | 佔總盈虧% | Positions |",
        "|---|--------|--------|-------|----------|------|-----------|------------|",
    ])
    for i, r in enumerate(negative_pct, 1):
        pct = r.get("pnl_pct") or 0
        share = r.get("pnl_share_pct", 0) or 0
        pnl_d = r.get("pnl", 0) or 0
        lines.append("| {} | {} | {:,.0f} | {:,.0f} | {:,.0f} | {:+.1f}% | {}% | {} |".format(
            i, r["symbol"], r["amount"], r["current_value"], pnl_d, pct, share, r.get("positions", 0)))
    if not negative_pct:
        lines.append("| (none) | | | | | |")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print("\nWritten: {}".format(md_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
