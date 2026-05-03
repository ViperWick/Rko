# -*- coding: utf-8 -*-
"""
組合 × 策略討論摘要 — 讀取 eToro 組合與各標的訊號，產出「當前形勢適合什麼策略」的討論用文字
供使用者複製後與 AI agent 討論
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .etoro_client import EToroClient


@dataclass
class HoldingBrief:
    """單一標的持倉 + 訊號摘要"""
    symbol: str
    amount: float
    pnl: float
    pnl_pct: float
    composite_score: float | None  # 1-10
    recommendation: str | None      # 加碼/正常/減量
    suggested_mult: float | None


@dataclass
class PortfolioStrategyBriefing:
    """組合策略討論摘要"""
    credit: float
    total_equity: float
    cash_pct: float
    unrealized_pnl: float
    holdings: list[HoldingBrief] = field(default_factory=list)
    summary_text: str = ""          # 一段話：當前形勢與建議
    discussion_prompt: str = ""     # 可貼給 AI 繼續討論的完整文字


def get_portfolio_strategy_briefing(client: "EToroClient") -> PortfolioStrategyBriefing | None:
    """
    讀取 eToro 組合與各持倉標的的綜合評分，產出策略討論摘要。
    回傳的 discussion_prompt 可直接複製到與 AI 的對話，繼續討論「最近形勢適合什麼策略」。
    """
    from .portfolio import get_balance, get_positions
    from .instrument_map import resolve_ids
    from .composite_score import get_composite_score

    balance = get_balance(client)
    positions = get_positions(client)

    credit = balance.get("credit", 0) or 0
    unrealized_pnl = balance.get("unrealized_pnl", 0) or 0
    positions_value = sum(p.get("amount", 0) or 0 for p in positions)
    total_equity = credit + positions_value
    cash_pct = (credit / total_equity * 100) if total_equity > 0 else 100.0

    # 按 instrument_id 彙總
    by_inst: dict[int, dict] = {}
    for p in positions:
        iid = p.get("instrument_id")
        if not iid:
            continue
        if iid not in by_inst:
            by_inst[iid] = {"amount": 0, "pnl": 0}
        by_inst[iid]["amount"] += p.get("amount", 0) or 0
        by_inst[iid]["pnl"] += p.get("pnl", 0) or 0

    id_to_symbol, _ = resolve_ids(client, list(by_inst.keys()))
    holdings: list[HoldingBrief] = []

    for iid, d in by_inst.items():
        symbol = id_to_symbol.get(iid)
        if not symbol:
            symbol = f"ID{iid}"
        amount = d["amount"]
        pnl = d["pnl"]
        pnl_pct = (pnl / amount * 100) if amount else 0.0

        comp = None
        try:
            comp = get_composite_score(symbol, client)
        except Exception:
            pass

        if comp:
            holdings.append(HoldingBrief(
                symbol=symbol,
                amount=amount,
                pnl=pnl,
                pnl_pct=pnl_pct,
                composite_score=comp.score,
                recommendation=comp.recommendation,
                suggested_mult=comp.suggested_mult,
            ))
        else:
            holdings.append(HoldingBrief(
                symbol=symbol,
                amount=amount,
                pnl=pnl,
                pnl_pct=pnl_pct,
                composite_score=None,
                recommendation=None,
                suggested_mult=None,
            ))

    # 依持倉金額排序（大→小）
    holdings.sort(key=lambda h: h.amount, reverse=True)

    # 產出一段話：當前形勢與建議
    lines = []
    if cash_pct < 20:
        lines.append(f"目前現金比例約 {cash_pct:.1f}%，偏低，建議暫停或減量 DCA，保留現金。")
    elif cash_pct >= 30:
        lines.append(f"目前現金比例約 {cash_pct:.1f}%，有空間執行 DCA。")
    else:
        lines.append(f"目前現金比例約 {cash_pct:.1f}%，可考慮減量 DCA 或觀望。")

    rec_counts = {"加碼": 0, "正常": 0, "減量": 0}
    scored = [h for h in holdings if h.recommendation]
    for h in scored:
        rec_counts[h.recommendation] = rec_counts.get(h.recommendation, 0) + 1
    if scored:
        if rec_counts.get("減量", 0) >= len(scored) / 2:
            lines.append("持倉標的多數綜合評分偏保守或減量，近期形勢較適合：減量 DCA、或優先觀望。")
        elif rec_counts.get("加碼", 0) >= len(scored) / 2:
            lines.append("持倉標的多數綜合評分偏加碼，可考慮：正常至略加碼 DCA、或選評分高的標的加碼。")
        else:
            lines.append("持倉標的訊號混合，建議：維持正常 DCA，或依單一標的評分個別加減碼。")

    summary_text = " ".join(lines)

    # 可貼給 AI 的討論用完整文字
    prompt_lines = [
        "【我的 eToro 組合與當前訊號 — 請根據以下資料與我討論「最近形勢適合什麼策略」】",
        "",
        "## 組合概況",
        f"- 可用餘額: ${credit:,.2f}",
        f"- 持倉市值（投入）約: ${positions_value:,.2f}",
        f"- 未實現損益: ${unrealized_pnl:,.2f}",
        f"- 現金比例: {cash_pct:.1f}%",
        "",
        "## 各持倉標的與綜合評分（eToro 數據，1–10 分；建議：加碼/正常/減量）",
    ]
    for h in holdings:
        if h.composite_score is not None and h.recommendation:
            prompt_lines.append(
                f"- **{h.symbol}** 投入 ${h.amount:,.0f}，損益 {h.pnl_pct:+.1f}% | "
                f"綜合評分 {h.composite_score}/10 → **{h.recommendation}**（建議 DCA 倍數 {h.suggested_mult}x）"
            )
        else:
            prompt_lines.append(f"- **{h.symbol}** 投入 ${h.amount:,.0f}，損益 {h.pnl_pct:+.1f}% | 未取得訊號")
    prompt_lines.extend([
        "",
        "## 系統摘要",
        summary_text,
        "",
        "請根據以上我的實際組合與各標的當前訊號，與我討論：最近形勢比較適合用哪種策略（例如純 DCA、或依訊號加減碼、止盈止損節奏等），以及有沒有要特別注意的標的。",
    ])
    discussion_prompt = "\n".join(prompt_lines)

    return PortfolioStrategyBriefing(
        credit=credit,
        total_equity=total_equity,
        cash_pct=cash_pct,
        unrealized_pnl=unrealized_pnl,
        holdings=holdings,
        summary_text=summary_text,
        discussion_prompt=discussion_prompt,
    )
