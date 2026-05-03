# -*- coding: utf-8 -*-
"""
簡單策略模組
內建：定額定投、止盈止損、零售訊號優化（逆向/動量）、60日均線過濾
"""
from .etoro_client import EToroClient
from .portfolio import get_positions, get_balance
from .trading import buy, sell, close


def dca_buy(
    symbol: str,
    amount: float,
    client: EToroClient | None = None,
) -> dict:
    """
    定額定投（Dollar Cost Averaging）
    每月/每週固定金額買入
    """
    return buy(client, symbol=symbol, amount=amount, leverage=1)


def dca_buy_with_signal(
    symbol: str,
    amount: float,
    client: EToroClient | None = None,
    use_signal: bool = True,
    signal_type: str = "retail",
) -> dict:
    """
    定額定投 + 可選訊號優化

    signal_type:
    - "retail": 零售動量（跌多加碼、漲多減量）
    - "breakout": 突破（收盤>20日高加碼、<20日低減量）
    - "rsi": RSI 14日（<30加碼、>70減量）
    - "volatility": 波動度（高波動減量、低波動略加碼）
    - "composite": 綜合（取各訊號倍數的最小值，最保守）
    """
    if use_signal and signal_type and client:
        try:
            mult = _get_signal_multiplier(symbol, signal_type, client)
            amount = max(amount * mult, 10)  # 至少 10 USD
        except Exception:
            pass
    return buy(client, symbol=symbol, amount=amount, leverage=1)


def _get_signal_multiplier(symbol: str, signal_type: str, client: EToroClient) -> float:
    """依 signal_type 回傳 DCA 倍數（1.0 = 不變），資料來自 eToro API"""
    if signal_type == "retail":
        from ..signals.retail_signals import get_momentum_signal, get_dca_multiplier
        return get_dca_multiplier(get_momentum_signal(symbol, client))
    if signal_type == "breakout":
        from ..signals.breakout_signals import get_breakout_signal, get_dca_multiplier_breakout
        return get_dca_multiplier_breakout(get_breakout_signal(symbol, client))
    if signal_type == "rsi":
        from ..signals.rsi_signals import get_rsi_signal, get_dca_multiplier_rsi
        return get_dca_multiplier_rsi(get_rsi_signal(symbol, client))
    if signal_type == "volatility":
        from ..signals.volatility_signals import get_volatility_signal, get_dca_multiplier_volatility
        return get_dca_multiplier_volatility(get_volatility_signal(symbol, client))
    if signal_type == "composite":
        mults = []
        try:
            from ..signals.retail_signals import get_momentum_signal, get_dca_multiplier
            mults.append(get_dca_multiplier(get_momentum_signal(symbol, client)))
        except Exception:
            mults.append(1.0)
        try:
            from ..signals.breakout_signals import get_breakout_signal, get_dca_multiplier_breakout
            mults.append(get_dca_multiplier_breakout(get_breakout_signal(symbol, client)))
        except Exception:
            mults.append(1.0)
        try:
            from ..signals.rsi_signals import get_rsi_signal, get_dca_multiplier_rsi
            mults.append(get_dca_multiplier_rsi(get_rsi_signal(symbol, client)))
        except Exception:
            mults.append(1.0)
        try:
            from ..signals.volatility_signals import get_volatility_signal, get_dca_multiplier_volatility
            mults.append(get_dca_multiplier_volatility(get_volatility_signal(symbol, client)))
        except Exception:
            mults.append(1.0)
        return min(mults) if mults else 1.0
    return 1.0


def dca_buy_with_ma60(
    symbol: str,
    amount: float,
    client: EToroClient | None = None,
    use_filter: bool = True,
    min_deviation_pct: float = 2.0,
) -> dict | None:
    """
    定額定投 + 60 日均線過濾（順勢加碼）

    邏輯：
    - 價 > MA60 且偏離 ≥ 2% → 加碼 20% 買入
    - 價 > MA60 但偏離不足 → 正常買入
    - 價 ≤ MA60 → 跳過（不買）

    Args:
        symbol: 標的代碼
        amount: 基礎金額（USD）
        client: eToro 客戶端
        use_filter: 是否啟用 60 日均線過濾
        min_deviation_pct: 最小偏離門檻（預設 2%）
    """
    if use_filter:
        try:
            from ..signals.ma_signals import get_ma60_signal, get_dca_multiplier_ma60
            c = client or EToroClient()
            sig = get_ma60_signal(symbol, client=c, min_deviation_pct=min_deviation_pct)
            mult = get_dca_multiplier_ma60(sig)
            if mult == 0:
                return None  # 跳過，不買
            amount = max(amount * mult, 10)
        except Exception:
            pass
    return buy(client, symbol=symbol, amount=amount, leverage=1)


def check_stop_loss(
    loss_threshold_pct: float = -10.0,
    client: EToroClient | None = None,
) -> list[dict]:
    """
    檢查持倉是否觸及止損
    loss_threshold_pct: 虧損百分比閾值（例如 -10 表示虧 10% 時平倉）
    回傳被平倉的持倉列表
    """
    c = client or EToroClient()
    positions = get_positions(c)
    closed = []

    for p in positions:
        amount = p.get("amount", 0) or 1
        pnl = p.get("pnl", 0)
        if amount <= 0:
            continue
        pnl_pct = (pnl / amount) * 100
        if pnl_pct <= loss_threshold_pct:
            try:
                result = close(c, position_id=p["position_id"])
                closed.append({"position": p, "result": result})
            except Exception as e:
                closed.append({"position": p, "error": str(e)})

    return closed


def check_take_profit(
    profit_threshold_pct: float = 20.0,
    client: EToroClient | None = None,
    keep_ratio: float = 1 / 3,
) -> list[dict]:
    """
    檢查持倉是否觸及止盈（按標的分組、選單筆止盈、保留倉位）

    邏輯：
    - 按 instrument_id（標的）分組
    - 每標的至少保留 keep_ratio（預設 1/3）倉位，讓長期翻倍
    - 優先止盈「獲利%最高」的那幾筆（eToro 可選單筆平倉）
    - 看的是「單筆」損益，不是總倉位損益

    Args:
        profit_threshold_pct: 獲利%閾值（如 20 表示賺 20% 才考慮止盈）
        keep_ratio: 每標的至少保留比例（0.333 = 保留 1/3，0 = 不保留）
    """
    c = client or EToroClient()
    positions = get_positions(c)
    closed = []

    # 只做多
    long_positions = [p for p in positions if p.get("is_buy", True)]

    # 按 instrument_id 分組
    from collections import defaultdict
    by_symbol = defaultdict(list)
    for p in long_positions:
        inst_id = p.get("instrument_id")
        if inst_id is None:
            continue
        amount = p.get("amount", 0) or 1
        pnl = p.get("pnl", 0)
        units = p.get("units", 0) or 0
        if amount <= 0 or units <= 0:
            continue
        pnl_pct = (pnl / amount) * 100
        p["_pnl_pct"] = pnl_pct
        by_symbol[inst_id].append(p)

    for inst_id, group in by_symbol.items():
        total_units = sum(p["units"] for p in group)
        keep_units = total_units * keep_ratio
        max_sell_units = total_units - keep_units

        if max_sell_units <= 0:
            continue

        # 達標的持倉，按獲利% 高到低排序（優先止盈賺最多的那幾筆）
        eligible = [p for p in group if p["_pnl_pct"] >= profit_threshold_pct]
        eligible.sort(key=lambda x: x["_pnl_pct"], reverse=True)

        sold_units = 0.0
        for p in eligible:
            if sold_units >= max_sell_units:
                break
            units = p.get("units", 0) or 0
            to_sell = min(units, max_sell_units - sold_units)
            if to_sell <= 0:
                continue
            try:
                if to_sell >= units:
                    result = close(c, position_id=p["position_id"])
                else:
                    result = close(c, position_id=p["position_id"], units=to_sell)
                closed.append({"position": p, "result": result, "units_sold": to_sell})
                sold_units += to_sell
            except Exception as e:
                closed.append({"position": p, "error": str(e)})

    return closed
