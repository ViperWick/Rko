# -*- coding: utf-8 -*-
"""
綜合評分 — 彙總零售動量、突破、RSI、波動度，給出當前建議
資料來源：eToro API（需傳入 client）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .etoro_client import EToroClient


@dataclass
class IndicatorRow:
    """單一指標結果"""
    name: str
    value: str       # 顯示用，如 "動量 -5.2%", "RSI 45", "突破 區間內"
    signal: str      # buy_more | neutral | buy_less
    mult: float
    reason: str


@dataclass
class CompositeScore:
    """綜合評分結果"""
    symbol: str
    score: float       # 1–10，10=強烈加碼、5=正常、1=強烈減量
    recommendation: str  # "加碼" | "正常" | "減量"
    summary: str       # 一句話說明
    indicators: list[IndicatorRow] = field(default_factory=list)
    suggested_mult: float = 1.0  # 建議 DCA 倍數


def get_composite_score(symbol: str, client: "EToroClient") -> CompositeScore | None:
    """
    用 eToro API 取價，計算四項指標並彙總為綜合評分。
    - 零售動量、突破、RSI、波動度 各得一個倍數
    - 綜合分數 = 依平均倍數換算 1–10 分
    - 建議：加碼 / 正常 / 減量 + 建議倍數
    """
    indicators: list[IndicatorRow] = []
    mults: list[float] = []

    # 零售動量
    try:
        from ..signals.retail_signals import get_momentum_signal, get_dca_multiplier
        sig = get_momentum_signal(symbol, client)
        if sig:
            m = get_dca_multiplier(sig)
            mults.append(m)
            indicators.append(IndicatorRow(
                name="零售動量",
                value=f"{sig.momentum_20d_pct:+.1f}%",
                signal=sig.signal,
                mult=m,
                reason=sig.reason,
            ))
    except Exception:
        pass

    # 突破
    try:
        from ..signals.breakout_signals import get_breakout_signal, get_dca_multiplier_breakout
        sig = get_breakout_signal(symbol, client)
        if sig:
            m = get_dca_multiplier_breakout(sig)
            mults.append(m)
            indicators.append(IndicatorRow(
                name="突破",
                value=f"{sig.close:.2f} vs [{sig.low_20d:.2f}–{sig.high_20d:.2f}]",
                signal=sig.signal,
                mult=m,
                reason=sig.reason,
            ))
    except Exception:
        pass

    # RSI
    try:
        from ..signals.rsi_signals import get_rsi_signal, get_dca_multiplier_rsi
        sig = get_rsi_signal(symbol, client)
        if sig:
            m = get_dca_multiplier_rsi(sig)
            mults.append(m)
            indicators.append(IndicatorRow(
                name="RSI",
                value=f"{sig.rsi:.1f}",
                signal=sig.signal,
                mult=m,
                reason=sig.reason,
            ))
    except Exception:
        pass

    # 波動度
    try:
        from ..signals.volatility_signals import get_volatility_signal, get_dca_multiplier_volatility
        sig = get_volatility_signal(symbol, client)
        if sig:
            m = get_dca_multiplier_volatility(sig)
            mults.append(m)
            indicators.append(IndicatorRow(
                name="波動度",
                value=f"{sig.vol_pct:.2f}%",
                signal=sig.signal,
                mult=m,
                reason=sig.reason,
            ))
    except Exception:
        pass

    if not mults:
        return None

    avg_mult = sum(mults) / len(mults)
    # 倍數 0.5~1.2 對應 分數 1~10：1.2→10, 1.0→5, 0.5→1
    score = 1.0 + (avg_mult - 0.5) / 0.7 * 9.0
    score = max(1.0, min(10.0, score))

    if score >= 7.0:
        recommendation = "加碼"
        summary = "多數指標偏多，可考慮加碼或正常偏多 DCA。"
    elif score <= 3.0:
        recommendation = "減量"
        summary = "多數指標偏空或保守，建議減量或觀望。"
    else:
        recommendation = "正常"
        summary = "指標中性，維持正常 DCA 即可。"

    return CompositeScore(
        symbol=symbol,
        score=round(score, 1),
        recommendation=recommendation,
        summary=summary,
        indicators=indicators,
        suggested_mult=round(avg_mult, 2),
    )
