# -*- coding: utf-8 -*-
"""
eToro K 線資料 — 統一用 eToro API 取價，供各訊號模組使用
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .etoro_client import EToroClient


def get_candles(
    client: "EToroClient",
    symbol: str,
    count: int = 100,
) -> list[dict] | None:
    """
    用 eToro API 取得日 K 線（新→舊）。
    回傳 list[dict]，每筆含 open, high, low, close (float)。
    """
    try:
        instrument_id = client.get_instrument_id(symbol)
        raw = client.get_candles(
            instrument_id=instrument_id,
            interval="OneDay",
            count=min(count, 1000),
            direction="desc",
        )
        if not raw or len(raw) < 2:
            return None
        out = []
        for c in raw:
            o = _float(c, "open")
            h = _float(c, "high")
            low = _float(c, "low")
            cl = _float(c, "close")
            if o is None or h is None or low is None or cl is None or cl <= 0:
                continue
            out.append({"open": o, "high": h, "low": low, "close": cl})
        return out if len(out) >= 2 else None
    except Exception:
        return None


def _float(d: dict, key: str) -> float | None:
    v = d.get(key) or d.get(key.capitalize())
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
