# -*- coding: utf-8 -*-
"""
波動度訊號 — 依近期波動調整 DCA 金額
資料來源：eToro API（需傳入 client）
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.etoro_client import EToroClient


@dataclass
class VolatilitySignal:
    symbol: str
    vol_pct: float   # 日報酬標準差 * 100
    signal: str      # "buy_more" | "buy_less" | "neutral"
    reason: str


def get_volatility_signal(
    symbol: str,
    client: "EToroClient",
    lookback_days: int = 20,
    high_vol_pct: float = 3.0,
    very_high_vol_pct: float = 5.0,
) -> VolatilitySignal | None:
    """
    用 eToro API 取價，依近 N 日收盤報酬標準差：高波動減量、低波動略加碼。
    """
    from ..core.etoro_candles import get_candles
    candles = get_candles(client, symbol, count=lookback_days + 5)
    if not candles or len(candles) < lookback_days:
        return None
    use = candles[:lookback_days]
    closes = [c["close"] for c in use]
    pct_changes = []
    for i in range(len(closes) - 1):
        if closes[i + 1] and closes[i + 1] > 0:
            pct_changes.append((closes[i] - closes[i + 1]) / closes[i + 1])
    if len(pct_changes) < 2:
        return None
    mean_ = sum(pct_changes) / len(pct_changes)
    vol_pct = (sum((x - mean_) ** 2 for x in pct_changes) / len(pct_changes)) ** 0.5 * 100

    if vol_pct >= very_high_vol_pct:
        signal = "buy_less"
        reason = f"近{lookback_days}日波動 {vol_pct:.2f}% ≥ {very_high_vol_pct}%，極高 → 減量"
    elif vol_pct >= high_vol_pct:
        signal = "buy_less"
        reason = f"近{lookback_days}日波動 {vol_pct:.2f}% ≥ {high_vol_pct}%，偏高 → 減量"
    elif vol_pct < 1.0:
        signal = "buy_more"
        reason = f"近{lookback_days}日波動 {vol_pct:.2f}% 偏低 → 略加碼"
    else:
        signal = "neutral"
        reason = f"近{lookback_days}日波動 {vol_pct:.2f}% → 正常"
    return VolatilitySignal(symbol=symbol, vol_pct=vol_pct, signal=signal, reason=reason)


def get_dca_multiplier_volatility(signal: VolatilitySignal | None) -> float:
    """高波動減量 0.6、極高 0.5、低波動加碼 1.1、其餘 1.0"""
    if signal is None:
        return 1.0
    if signal.signal == "buy_more":
        return 1.1
    if signal.signal == "buy_less":
        # 可依 vol_pct 再細分：極高 0.5、一般高 0.6
        return 0.6
    return 1.0
