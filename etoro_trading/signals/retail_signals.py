# -*- coding: utf-8 -*-
"""
零售行為代理訊號 — 基於價格動量的「散戶偏誤」邏輯
資料來源：eToro API（需傳入 client）
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.etoro_client import EToroClient


@dataclass
class RetailSignal:
    """單一標的的訊號"""
    symbol: str
    momentum_20d_pct: float  # 近 20 日報酬 %
    volatility_20d: float    # 近 20 日波動率
    signal: str              # "buy_more" | "buy_less" | "neutral"
    reason: str


def get_momentum_signal(
    symbol: str,
    client: "EToroClient",
    lookback_days: int = 20,
) -> RetailSignal | None:
    """
    用 eToro API 取價，計算動量訊號。
    - momentum_20d < -5%: 跌多 → 加碼 (buy_more)
    - momentum_20d > +10%: 漲多 → 減量 (buy_less)
    - 其餘: 中性 (neutral)
    """
    from ..core.etoro_candles import get_candles
    candles = get_candles(client, symbol, count=lookback_days + 5)
    if not candles or len(candles) < lookback_days:
        return None
    use = candles[:lookback_days]
    first_close = use[-1]["close"]  # 最舊
    last_close = use[0]["close"]    # 最新
    if first_close <= 0:
        return None
    ret = (last_close / first_close - 1) * 100
    # 波動：日報酬標準差
    closes = [c["close"] for c in use]
    pct_changes = []
    for i in range(len(closes) - 1):
        if closes[i + 1] and closes[i + 1] > 0:
            pct_changes.append((closes[i] - closes[i + 1]) / closes[i + 1])
    vol = (sum((x - sum(pct_changes) / len(pct_changes)) ** 2 for x in pct_changes) / len(pct_changes)) ** 0.5 * 100 if len(pct_changes) > 1 else 0

    if ret < -5:
        signal = "buy_more"
        reason = f"近 {lookback_days} 日跌 {ret:.1f}%，散戶可能恐慌賣 → 逆向加碼"
    elif ret > 10:
        signal = "buy_less"
        reason = f"近 {lookback_days} 日漲 {ret:.1f}%，散戶可能追高 → 減量或跳過"
    else:
        signal = "neutral"
        reason = f"近 {lookback_days} 日報酬 {ret:.1f}% → 正常 DCA"

    return RetailSignal(
        symbol=symbol,
        momentum_20d_pct=ret,
        volatility_20d=vol,
        signal=signal,
        reason=reason,
    )


def get_dca_multiplier(signal: RetailSignal | None) -> float:
    """
    依訊號回傳 DCA 金額倍數
    - buy_more: 1.2（加碼 20%）
    - buy_less: 0.5（減半）
    - neutral: 1.0
    """
    if signal is None:
        return 1.0
    if signal.signal == "buy_more":
        return 1.2
    if signal.signal == "buy_less":
        return 0.5
    return 1.0


def get_stop_loss_adjusted(
    base_pct: float,
    signal: RetailSignal | None,
    volatility_scale: float = 1.0,
) -> float:
    """
    依波動率調整止損門檻
    高波動時放寬止損，避免被震出
    """
    if signal is None:
        return base_pct
    # 波動率 > 3% 時，止損放寬 1.5 倍
    if signal.volatility_20d > 3.0:
        return base_pct * (1.0 + (signal.volatility_20d - 2) * 0.1)
    return base_pct


def get_take_profit_adjusted(
    base_pct: float,
    signal: RetailSignal | None,
) -> float:
    """
    動量強時可提高止盈門檻（讓贏家跑更久）
    """
    if signal is None:
        return base_pct
    if signal.momentum_20d_pct > 15:
        return base_pct * 1.3  # 漲多時提高止盈
    return base_pct
