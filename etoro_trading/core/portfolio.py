# -*- coding: utf-8 -*-
"""
查詢資產模組
"""
from .etoro_client import EToroClient


def get_balance(client: EToroClient | None = None) -> dict:
    """取得帳戶餘額與摘要"""
    c = client or EToroClient()
    data = c.get_portfolio()
    cp = data.get("clientPortfolio", {})
    return {
        "credit": cp.get("credit", 0),
        "unrealized_pnl": cp.get("unrealizedPnL", 0),
        "bonus_credit": cp.get("bonusCredit", 0),
        "positions_count": len(cp.get("positions", []))
        + sum(len(m.get("positions", [])) for m in cp.get("mirrors", [])),
        "orders_count": len(cp.get("orders", [])) + len(cp.get("ordersForOpen", [])),
    }


def _get_num(obj: dict, keys: list, default=0):
    """依序嘗試多個 key，取第一個存在且非 None 的數值（API 可能用不同命名）"""
    for k in keys:
        if k in obj and obj[k] is not None:
            try:
                return float(obj[k])
            except (TypeError, ValueError):
                pass
    return default


def get_positions(client: EToroClient | None = None) -> list[dict]:
    """取得所有持倉（含直接持倉與跟單 mirror 持倉），含 API 回傳的每筆損益"""
    c = client or EToroClient()
    data = c.get_portfolio()
    cp = data.get("clientPortfolio", {})
    positions = list(cp.get("positions", []))

    for mirror in cp.get("mirrors", []):
        positions.extend(mirror.get("positions", []))

    result = []
    for p in positions:
        pos_id = p.get("positionId") or p.get("positionID") or p.get("position_id")
        inst_id = p.get("instrumentId") or p.get("instrumentID") or p.get("instrument_id")
        amount = _get_num(p, ["amount", "initialAmountInDollars", "Amount", "InitialAmountInDollars"])
        # API 回傳: 每檔損益在 unrealizedPnL.pnL 或 position 根 pnL
        upnl = p.get("unrealizedPnL")
        if isinstance(upnl, dict):
            pnl = _get_num(upnl, ["pnL", "pnl"])
        else:
            pnl = _get_num(p, ["pnL", "pnl", "PnL", "PNL"])
        result.append({
            "position_id": pos_id,
            "instrument_id": inst_id,
            "is_buy": p.get("isBuy", p.get("is_buy", True)),
            "amount": amount,
            "units": _get_num(p, ["units", "initialUnits", "Units", "InitialUnits"]),
            "open_rate": _get_num(p, ["openRate", "open_rate"]),
            "pnl": pnl,
            "leverage": _get_num(p, ["leverage", "Leverage"], 1),
            "mirror_id": p.get("mirrorId")
            or p.get("mirrorID")
            or p.get("mirror_id"),
        })
    return result


def get_orders(client: EToroClient | None = None) -> dict:
    """取得所有訂單（待開倉、待平倉）"""
    c = client or EToroClient()
    data = c.get_portfolio()
    cp = data.get("clientPortfolio", {})
    return {
        "orders": cp.get("orders", []),
        "orders_for_open": cp.get("ordersForOpen", []),
        "orders_for_close": cp.get("ordersForClose", []),
    }


def format_portfolio_summary(client: EToroClient | None = None) -> str:
    """格式化投資組合摘要（供 CLI 顯示）"""
    balance = get_balance(client)
    positions = get_positions(client)

    lines = [
        "========== 帳戶摘要 ==========",
        f"可用餘額: ${balance['credit']:,.2f}",
        f"未實現損益: ${balance['unrealized_pnl']:,.2f}",
        f"持倉數: {balance['positions_count']}",
        f"待處理訂單: {balance['orders_count']}",
        "",
        "========== 持倉明細 ==========",
    ]

    if not positions:
        lines.append("（無持倉）")
    else:
        for i, p in enumerate(positions, 1):
            direction = "買" if p["is_buy"] else "賣"
            lines.append(
                f"  {i}. ID:{p['position_id']} | {direction} | "
                f"${p['amount']:,.0f} | 單位:{p['units']:.4f} | "
                f"損益: ${p['pnl']:,.2f}"
            )

    return "\n".join(lines)
