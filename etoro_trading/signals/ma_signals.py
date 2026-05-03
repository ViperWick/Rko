# -*- coding: utf-8 -*-
"""
60 日均線訊號 — 趨勢過濾邏輯

買入：價格 > MA60 且偏離均線 2–3% 以上（順勢加碼）
賣出：搭配止盈止損，或價跌破均線時可考慮減倉
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.etoro_client import EToroClient

try:
    import yfinance as yf
    HAS_YF = True
except ImportError:
    HAS_YF = False


@dataclass
class MA60Signal:
    """60 日均線訊號"""
    symbol: str
    price: float
    ma60: float
    deviation_pct: float  # (price - ma60) / ma60 * 100
    signal: str           # "buy" | "hold" | "skip"
    reason: str


def _get_candles_etoro(
    client: "EToroClient",
    symbol: str,
    count: int = 80,
) -> list[dict] | None:
    """從 eToro API 取得日 K 線"""
    try:
        instrument_id = client.get_instrument_id(symbol)
        candles = client.get_candles(
            instrument_id=instrument_id,
            interval="OneDay",
            count=count,
            direction="desc",  # 新→舊
        )
        return candles if candles and len(candles) >= 60 else None
    except Exception:
        return None


def _get_candles_yf(symbol: str, count: int = 80) -> list[dict] | None:
    """從 yfinance 取得日 K 線（備援）"""
    if not HAS_YF:
        return None
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=f"{count + 20}d")
        if hist is None or len(hist) < 60:
            return None
        hist = hist.tail(count)
        candles = [{"close": float(row["Close"])} for _, row in hist.iterrows()]
        return candles[::-1]  # 新→舊（與 eToro desc 一致）
    except Exception:
        return None


def get_ma60_signal(
    symbol: str,
    client: "EToroClient" | None = None,
    min_deviation_pct: float = 2.0,
    ma_period: int = 60,
) -> MA60Signal | None:
    """
    計算 60 日均線訊號

    邏輯：
    - 價格 > MA60 且偏離 ≥ min_deviation_pct% → buy（順勢加碼）
    - 價格 > MA60 但偏離不足 → hold（可買但不加碼）
    - 價格 ≤ MA60 → skip（趨勢不明，跳過）

    Args:
        symbol: 標的代碼（如 GLD, NVDA）
        client: eToro 客戶端，若無則用 yfinance
        min_deviation_pct: 最小偏離門檻（預設 2%）
        ma_period: 均線週期（預設 60）
    """
    candles = None
    if client:
        candles = _get_candles_etoro(client, symbol, count=ma_period + 20)
    if not candles and HAS_YF:
        candles = _get_candles_yf(symbol, count=ma_period + 20)

    if not candles or len(candles) < ma_period:
        return None

    # 最新收盤價（eToro 用小寫 close）
    price = float(candles[0].get("close", candles[0].get("Close", 0)))
    if price <= 0:
        return None

    # 計算 MA60（最近 60 根 K 線的收盤均價）
    closes = []
    for c in candles[:ma_period]:
        v = c.get("close") or c.get("Close")
        if v is not None:
            closes.append(float(v))
    if len(closes) < ma_period:
        return None

    ma60 = sum(closes) / len(closes)
    if ma60 <= 0:
        return None

    deviation_pct = (price - ma60) / ma60 * 100

    # 訊號判斷
    if price <= ma60:
        signal = "skip"
        reason = f"價 {price:.2f} ≤ MA60 {ma60:.2f}，趨勢不明，跳過"
    elif deviation_pct >= min_deviation_pct:
        signal = "buy"
        reason = f"價 {price:.2f} > MA60 {ma60:.2f}，偏離 +{deviation_pct:.1f}% >= {min_deviation_pct}%，順勢加碼"
    else:
        signal = "hold"
        reason = f"價 {price:.2f} > MA60 {ma60:.2f}，偏離 +{deviation_pct:.1f}% 不足 {min_deviation_pct}%，可買但不加碼"

    return MA60Signal(
        symbol=symbol,
        price=price,
        ma60=ma60,
        deviation_pct=deviation_pct,
        signal=signal,
        reason=reason,
    )


def should_buy_ma60(signal: MA60Signal | None) -> bool:
    """是否建議買入（價格 > MA60 且偏離足夠）"""
    return signal is not None and signal.signal == "buy"


def get_dca_multiplier_ma60(signal: MA60Signal | None) -> float:
    """
    依 60 日均線訊號回傳 DCA 金額倍數
    - buy: 1.2（加碼 20%）
    - hold: 1.0（正常）
    - skip: 0（不買）
    """
    if signal is None:
        return 1.0
    if signal.signal == "buy":
        return 1.2
    if signal.signal == "skip":
        return 0.0
    return 1.0
