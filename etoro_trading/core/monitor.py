# -*- coding: utf-8 -*-
"""
監控持倉模組
定時檢查持倉、發送摘要
"""
import time
from .etoro_client import EToroClient
from .portfolio import get_positions, get_balance, format_portfolio_summary
from .strategy import check_stop_loss, check_take_profit


def monitor_loop(
    interval_seconds: int = 300,
    stop_loss_pct: float | None = None,
    take_profit_pct: float | None = 20.0,
    keep_ratio: float = 1 / 3,
    on_tick=None,
):
    """
    監控迴圈
    interval_seconds: 檢查間隔（秒）
    stop_loss_pct: 止損百分比，None 則不執行
    take_profit_pct: 止盈百分比，None 則不執行
    keep_ratio: 每標的至少保留倉位比例（1/3=保留 1/3，0=不保留）
    on_tick: 每次檢查時的回呼函數，接收 (summary_str, positions, balance)
    """
    client = EToroClient()

    while True:
        try:
            balance = get_balance(client)
            positions = get_positions(client)
            summary = format_portfolio_summary(client)

            # 止損（None 則不執行）
            if stop_loss_pct is not None:
                closed_sl = check_stop_loss(stop_loss_pct, client)
                if closed_sl:
                    for item in closed_sl:
                        print(f"[止損] 已平倉 position_id={item['position']['position_id']}")

            # 止盈（按標的分組、選單筆止盈、保留 keep_ratio）
            if take_profit_pct is not None:
                closed_tp = check_take_profit(
                    take_profit_pct, client,
                    keep_ratio=keep_ratio,
                )
                if closed_tp:
                    for item in closed_tp:
                        pos_id = item["position"]["position_id"]
                        units = item.get("units_sold", "")
                        print(f"[止盈] 已平倉 position_id={pos_id} units={units}")

            if on_tick:
                on_tick(summary, positions, balance)

            print(summary)
            print(f"\n下次檢查: {interval_seconds} 秒後...")

        except Exception as e:
            print(f"監控錯誤: {e}")

        time.sleep(interval_seconds)


def quick_status(client: EToroClient | None = None) -> str:
    """快速狀態摘要（單次）"""
    return format_portfolio_summary(client)
