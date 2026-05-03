# -*- coding: utf-8 -*-
"""
簡易估值測算（適合低頻、每月檢查）
依 fundamentals.json 的 P/E、P/S、營收增長，產出 貴/合理/便宜 判斷
執行: python -m etoro_trading.scripts.calc_valuation_simple
需先執行: python -m etoro_trading.scripts.fetch_fundamentals
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FUND_FILE = DATA_DIR / "fundamentals.json"


def judge_mature(pe: float | None, ps: float | None) -> str:
    """成熟型：有穩定獲利"""
    if pe is None or pe <= 0:
        return "—"
    if pe < 15:
        return "便宜"
    if pe <= 25:
        return "合理"
    return "偏貴"


def judge_growth(ps: float | None, rev_growth: float | None) -> str:
    """成長型：營收高增長"""
    if ps is None and rev_growth is None:
        return "—"
    rev_pct = (rev_growth * 100) if rev_growth is not None else 0
    if ps is None:
        return "—"
    if rev_pct > 20 and ps < 5:
        return "可考慮"
    if rev_pct > 15 and ps < 15:
        return "觀望"
    if ps > 15 or rev_pct < 10:
        return "暫緩"
    return "觀望"


def judge_peg(pe: float | None, rev_growth: float | None) -> str:
    """PEG 概念：P/E ÷ 營收增長%"""
    if pe is None or rev_growth is None or rev_growth <= 0:
        return "—"
    rev_pct = rev_growth * 100
    peg = pe / rev_pct
    if peg < 1.5:
        return "尚可"
    if peg > 2:
        return "偏貴"
    return "觀望"


def main():
    if not FUND_FILE.exists():
        print("請先執行: python -m etoro_trading.scripts.fetch_fundamentals")
        return 1

    data = json.loads(FUND_FILE.read_text(encoding="utf-8"))
    print("\n=== 簡易估值測算（適合每月檢查） ===\n")
    print(f"{'標的':<6} {'P/E':>8} {'P/S':>8} {'營收增長':>10} {'成熟型':>8} {'成長型':>8} {'PEG':>6} {'建議':>8}")
    print("-" * 75)

    for r in data:
        sym = r.get("symbol", "")
        pe = r.get("peRatio")
        ps = r.get("priceToSales")
        rg = r.get("revenueGrowth")

        pe_str = f"{pe:.1f}" if pe is not None else "—"
        ps_str = f"{ps:.1f}" if ps is not None else "—"
        rg_str = f"{rg*100:.1f}%" if rg is not None else "—"

        mature = judge_mature(pe, ps)
        growth = judge_growth(ps, rg)
        peg = judge_peg(pe, rg)

        # 綜合建議：ETF 跳過，成熟型優先看 mature，成長型看 growth
        if rg is not None and rg > 0.2 and ps is not None and ps > 5:
            suggestion = growth
        elif pe is not None:
            suggestion = mature
        else:
            suggestion = "—"

        print(f"{sym:<6} {pe_str:>8} {ps_str:>8} {rg_str:>10} {mature:>8} {growth:>8} {peg:>6} {suggestion:>8}")

    print("\n說明：成熟型看 P/E；成長型看 P/S+營收增長；PEG = P/E ÷ 營收增長%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
