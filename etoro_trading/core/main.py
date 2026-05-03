# -*- coding: utf-8 -*-
"""
eToro 交易程式 - 主程式與 CLI
功能：查詢資產、自動下單、簡單策略、監控持倉
"""
import argparse
import sys

from .config import get_config
from .etoro_client import EToroClient
from .portfolio import format_portfolio_summary, get_positions
from .trading import buy, sell, close
from .strategy import dca_buy, dca_buy_with_ma60, check_stop_loss, check_take_profit
from ..signals.ma_signals import get_ma60_signal
from .monitor import monitor_loop, quick_status


def cmd_portfolio(args):
    """查詢資產"""
    print(quick_status())
    return 0


def cmd_buy(args):
    """買入"""
    try:
        result = buy(symbol=args.symbol, amount=args.amount)
        print("下單成功:", result)
        return 0
    except Exception as e:
        print(f"下單失敗: {e}", file=sys.stderr)
        return 1


def cmd_sell(args):
    """賣出（開空倉）"""
    try:
        result = sell(symbol=args.symbol, amount=args.amount)
        print("下單成功:", result)
        return 0
    except Exception as e:
        print(f"下單失敗: {e}", file=sys.stderr)
        return 1


def cmd_close(args):
    """平倉"""
    try:
        result = close(position_id=args.position_id, units=args.units)
        print("平倉成功:", result)
        return 0
    except Exception as e:
        print(f"平倉失敗: {e}", file=sys.stderr)
        return 1


def cmd_dca(args):
    """定額定投"""
    try:
        result = dca_buy(symbol=args.symbol, amount=args.amount)
        print("定投成功:", result)
        return 0
    except Exception as e:
        print(f"定投失敗: {e}", file=sys.stderr)
        return 1


def cmd_ma60_signal(args):
    """查詢 60 日均線訊號（不下單，可用 yfinance 無需 API）"""
    try:
        client = None
        try:
            from .etoro_client import EToroClient
            client = EToroClient()
        except Exception:
            pass  # 無 API 時用 yfinance
        sig = get_ma60_signal(
            args.symbol,
            client=client,
            min_deviation_pct=args.deviation or 2.0,
        )
        if sig is None:
            print(f"無法取得 {args.symbol} 的 60 日均線訊號（需 yfinance，或資料不足）")
            return 1
        print(f"{sig.symbol}: 價 {sig.price:.2f} | MA60 {sig.ma60:.2f} | 偏離 {sig.deviation_pct:+.1f}%")
        print(f"訊號: {sig.signal} — {sig.reason}")
        return 0
    except Exception as e:
        print(f"查詢失敗: {e}", file=sys.stderr)
        return 1


def cmd_dca_ma60(args):
    """定額定投 + 60 日均線過濾（價>MA60且偏離≥2%才買）"""
    try:
        result = dca_buy_with_ma60(
            symbol=args.symbol,
            amount=args.amount,
            use_filter=True,
            min_deviation_pct=args.deviation or 2.0,
        )
        if result is None:
            print("60日均線訊號：跳過（價≤MA60 或偏離不足）")
            return 0
        print("定投成功:", result)
        return 0
    except Exception as e:
        print(f"定投失敗: {e}", file=sys.stderr)
        return 1


def cmd_monitor(args):
    """監控持倉（止盈可分批，止損可關閉）"""
    try:
        stop_loss = None if args.no_stop_loss else args.stop_loss
        monitor_loop(
            interval_seconds=args.interval,
            stop_loss_pct=stop_loss,
            take_profit_pct=args.take_profit if args.take_profit else None,
            keep_ratio=args.keep_ratio,
        )
        return 0
    except KeyboardInterrupt:
        print("\n已停止監控")
        return 0
    except Exception as e:
        print(f"監控錯誤: {e}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="eToro 交易程式 - 查詢資產、下單、策略、監控",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  python -m etoro_trading portfolio           # 查詢資產
  python -m etoro_trading buy BTC 100        # 買入 100 美元 BTC
  python -m etoro_trading sell AAPL 50       # 賣空 50 美元 AAPL
  python -m etoro_trading close 12345678     # 平倉 position_id
  python -m etoro_trading dca BTC 50         # 定投 50 美元 BTC
  python -m etoro_trading ma60-signal GLD    # 查詢 GLD 的 60 日均線訊號
  python -m etoro_trading dca-ma60 GLD 50    # 60日均線過濾定投（價>MA60且偏離≥2%）
  python -m etoro_trading monitor --no-stop-loss --keep-ratio 0.333   # 止盈保留1/3、不設止損
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="指令")

    # portfolio
    subparsers.add_parser("portfolio", help="查詢資產與持倉")

    # buy
    p_buy = subparsers.add_parser("buy", help="買入（開多倉）")
    p_buy.add_argument("symbol", help="標的代碼，如 BTC、AAPL")
    p_buy.add_argument("amount", type=float, help="金額（美元）")

    # sell
    p_sell = subparsers.add_parser("sell", help="賣出（開空倉）")
    p_sell.add_argument("symbol", help="標的代碼")
    p_sell.add_argument("amount", type=float, help="金額（美元）")

    # close
    p_close = subparsers.add_parser("close", help="平倉")
    p_close.add_argument("position_id", type=int, help="持倉 ID")
    p_close.add_argument("--units", type=float, default=None, help="平倉單位數（不填則全部）")

    # dca
    p_dca = subparsers.add_parser("dca", help="定額定投")
    p_dca.add_argument("symbol", help="標的代碼")
    p_dca.add_argument("amount", type=float, help="每次投入金額（美元）")

    # ma60-signal
    p_ma = subparsers.add_parser("ma60-signal", help="查詢 60 日均線訊號（不下單）")
    p_ma.add_argument("symbol", help="標的代碼")
    p_ma.add_argument("--deviation", type=float, default=2.0, help="偏離門檻%%（預設2）")

    # dca-ma60
    p_dca_ma = subparsers.add_parser("dca-ma60", help="定投+60日均線過濾（價>MA60且偏離≥2%%）")
    p_dca_ma.add_argument("symbol", help="標的代碼")
    p_dca_ma.add_argument("amount", type=float, help="每次投入金額（美元）")
    p_dca_ma.add_argument("--deviation", type=float, default=2.0, help="最小偏離門檻%%（預設2）")

    # monitor
    p_mon = subparsers.add_parser("monitor", help="監控持倉（止盈，止損可關閉）")
    p_mon.add_argument("--interval", type=int, default=300, help="檢查間隔（秒），預設 300")
    p_mon.add_argument("--stop-loss", type=float, default=None, help="止損%%，如 -10 表示虧 10%% 平倉；不設則不執行")
    p_mon.add_argument("--no-stop-loss", action="store_true", help="明確關閉止損（波動大時建議）")
    p_mon.add_argument("--take-profit", type=float, default=20, help="止盈%%，如 20 表示賺 20%% 平倉")
    p_mon.add_argument("--keep-ratio", type=float, default=0.333, help="每標的至少保留倉位比例，0.333=保留1/3，0=不保留")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # 驗證設定（ma60-signal 可只用 yfinance，不需 API）
    if args.command != "ma60-signal":
        try:
            get_config()
        except ValueError as e:
            print(f"設定錯誤: {e}", file=sys.stderr)
            print("請複製 .env.example 為 .env 並填入 ETORO_API_KEY、ETORO_USER_KEY", file=sys.stderr)
            return 1

    handlers = {
        "portfolio": cmd_portfolio,
        "buy": cmd_buy,
        "sell": cmd_sell,
        "close": cmd_close,
        "dca": cmd_dca,
        "ma60-signal": cmd_ma60_signal,
        "dca-ma60": cmd_dca_ma60,
        "monitor": cmd_monitor,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
