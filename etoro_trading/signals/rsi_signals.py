# -*- coding: utf-8 -*-
"""
RSI 訊號 — 14 日 RSI 超買超賣
資料來源：eToro API（需傳入 client）
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.etoro_client import EToroClient


@dataclass
class RsiSignal:
    symbol: str
    rsi: float
    signal: str   # "buy_more" | "buy_less" | "neutral"
    reason: str


def _calc_rsi_from_closes(closes: list[float], period: int = 14) -> float | None:
    """從收盤價列表算 RSI：RS = 平均漲幅 / 平均跌幅，RSI = 100 - 100/(1+RS)"""
    if not closes or len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(len(closes) - 1):
        chg = closes[i] - closes[i + 1]  # 新 - 舊（desc 順序）
        gains.append(chg if chg > 0 else 0.0)
        losses.append(-chg if chg < 0 else 0.0)
    use_g = gains[-period:]
    use_l = losses[-period:]
    avg_gain = sum(use_g) / period
    avg_loss = sum(use_l) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def get_rsi_signal(
    symbol: str,
    client: "EToroClient",
    period: int = 14,
) -> RsiSignal | None:
    """
    用 eToro API 取價，算 14 日 RSI：< 30 加碼、> 70 減量、其餘正常。
    """
    from ..core.etoro_candles import get_candles
    candles = get_candles(client, symbol, count=period + 30)
    if not candles or len(candles) < period + 1:
        return None
    closes = [c["close"] for c in candles]
    rsi_val = _calc_rsi_from_closes(closes, period)
    if rsi_val is None:
        return None
    if rsi_val < 30:
        signal = "buy_more"
        reason = f"RSI({period}) = {rsi_val:.1f} < 30，超賣 → 加碼"
    elif rsi_val > 70:
        signal = "buy_less"
        reason = f"RSI({period}) = {rsi_val:.1f} > 70，超買 → 減量"
    else:
        signal = "neutral"
        reason = f"RSI({period}) = {rsi_val:.1f}，區間內 → 正常"
    return RsiSignal(symbol=symbol, rsi=rsi_val, signal=signal, reason=reason)


def get_dca_multiplier_rsi(signal: RsiSignal | None) -> float:
    """超賣加碼 1.2、超買減半 0.5、其餘 1.0"""
    if signal is None:
        return 1.0
    if signal.signal == "buy_more":
        return 1.2
    if signal.signal == "buy_less":
        return 0.5
    return 1.0
