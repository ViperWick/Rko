# -*- coding: utf-8 -*-
"""
突破訊號 — 依收盤價 vs 過去 N 日最高/最低
資料來源：eToro API（需傳入 client）
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.etoro_client import EToroClient


@dataclass
class BreakoutSignal:
    symbol: str
    close: float
    high_20d: float
    low_20d: float
    signal: str   # "buy_more" | "buy_less" | "neutral"
    reason: str


def get_breakout_signal(
    symbol: str,
    client: "EToroClient",
    lookback_days: int = 20,
) -> BreakoutSignal | None:
    """
    用 eToro API 取價。收盤 > N 日最高 → 加碼；收盤 < N 日最低 → 減量；其餘正常。
    """
    from ..core.etoro_candles import get_candles
    candles = get_candles(client, symbol, count=lookback_days + 5)
    if not candles or len(candles) < lookback_days:
        return None
    use = candles[:lookback_days]
    close = use[0]["close"]
    high_20 = max(c["high"] for c in use)
    low_20 = min(c["low"] for c in use)
    if close <= 0:
        return None
    if close > high_20:
        signal = "buy_more"
        reason = f"收盤 {close:.2f} > 近{lookback_days}日最高 {high_20:.2f}，突破 → 加碼"
    elif close < low_20:
        signal = "buy_less"
        reason = f"收盤 {close:.2f} < 近{lookback_days}日最低 {low_20:.2f}，破底 → 減量/觀望"
    else:
        signal = "neutral"
        reason = f"收盤在 {low_20:.2f}–{high_20:.2f} 區間內 → 正常"
    return BreakoutSignal(symbol=symbol, close=close, high_20d=high_20, low_20d=low_20, signal=signal, reason=reason)


def get_dca_multiplier_breakout(signal: BreakoutSignal | None) -> float:
    """突破加碼 1.2、破底減半 0.5、其餘 1.0"""
    if signal is None:
        return 1.0
    if signal.signal == "buy_more":
        return 1.2
    if signal.signal == "buy_less":
        return 0.5
    return 1.0
