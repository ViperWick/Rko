# -*- coding: utf-8 -*-
"""
自動下單模組
"""
from .etoro_client import EToroClient


def buy(client: EToroClient | None = None, symbol: str = "", amount: float = 0, **kwargs) -> dict:
    """買入（開多倉）"""
    c = client or EToroClient()
    return c.open_position_by_amount(symbol, amount, is_buy=True, **kwargs)


def sell(client: EToroClient | None = None, symbol: str = "", amount: float = 0, **kwargs) -> dict:
    """賣出（開空倉）"""
    c = client or EToroClient()
    return c.open_position_by_amount(symbol, amount, is_buy=False, **kwargs)


def close(client: EToroClient | None = None, position_id: int = 0, units: float | None = None) -> dict:
    """平倉"""
    c = client or EToroClient()
    return c.close_position(position_id, units_to_deduct=units)
