# -*- coding: utf-8 -*-
"""
eToro 交易專案 — 統一腳本入口（整合原 scripts 目錄下各獨立程式）

用法（在 repo 根目錄）：
    py -m etoro_trading.scripts --help
    py -m etoro_trading.scripts today-summary
    py -m etoro_trading.scripts export-integrated --all

說明：各子命令仍可直接執行舊模組（例如 py -m etoro_trading.scripts.today_summary），
     行為與整合入口一致。
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# 從任意工作目錄以「檔案路徑」執行時，確保能 import etoro_trading
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _cmd_today_summary(_: argparse.Namespace) -> int:
    from etoro_trading.scripts.today_summary import main as m

    m()
    return 0


def _cmd_export_portfolio(_: argparse.Namespace) -> int:
    from etoro_trading.scripts.export_portfolio_summary import main as m

    return m()


def _cmd_daily_performance(_: argparse.Namespace) -> int:
    from etoro_trading.scripts.daily_performance_report import main as m

    return m()


def _cmd_list_positions_tp(_: argparse.Namespace) -> int:
    from etoro_trading.scripts.list_positions_and_tp_candidates import main as m

    return m()


def _cmd_check_yesterday(_: argparse.Namespace) -> int:
    from etoro_trading.scripts.check_yesterday_changes import main as m

    return m()


def _cmd_fetch_fundamentals(_: argparse.Namespace) -> int:
    from etoro_trading.scripts.fetch_fundamentals import main as m

    return m()


def _cmd_calc_valuation(_: argparse.Namespace) -> int:
    from etoro_trading.scripts.calc_valuation_simple import main as m

    return m()


def _cmd_calc_correlation(_: argparse.Namespace) -> int:
    from etoro_trading.scripts.calc_correlation import main as m

    return m()


def _cmd_calc_risk(_: argparse.Namespace) -> int:
    from etoro_trading.scripts.calc_risk_score import main as m

    return m()


def _cmd_export_integrated(args: argparse.Namespace) -> int:
    from etoro_trading.scripts import export_integrated_table as mod

    old = sys.argv[:]
    try:
        argv = ["export_integrated_table.py"]
        if args.all:
            argv.append("--all")
        elif args.word:
            argv.append("--word")
        sys.argv = argv
        return mod.main()
    finally:
        sys.argv = old


def _cmd_quantum_xlsx(_: argparse.Namespace) -> int:
    from etoro_trading.scripts.export_quantum_watchlist_xlsx import main as m

    m()
    return 0


def _cmd_build_instrument_map(_: argparse.Namespace) -> int:
    from etoro_trading.scripts.build_instrument_map import main as m

    return m()


def _cmd_pick_watchlist(_: argparse.Namespace) -> int:
    from etoro_trading.scripts.pick_watchlist import main as m

    return m()


def _cmd_build_defense(_: argparse.Namespace) -> int:
    from etoro_trading.scripts.build_defense_watchlist import main as m

    return m()


def _cmd_track_alpha(_: argparse.Namespace) -> int:
    from etoro_trading.scripts.track_alpha_portfolios import run_tracking

    run_tracking()
    return 0


def _cmd_simulate_retail(_: argparse.Namespace) -> int:
    from etoro_trading.scripts.simulate_retail_alpha import run_simulation

    run_simulation()
    return 0


def _cmd_generate_analysis(_: argparse.Namespace) -> int:
    from etoro_trading.scripts.generate_analysis_with_values import main as m

    return m()


def _cmd_debug_positions(_: argparse.Namespace) -> int:
    from etoro_trading.scripts.debug_api_positions import main as m

    return m()


def _cmd_ollama_summarize(args: argparse.Namespace) -> int:
    from etoro_trading.scripts.ollama_summarize_automation_log import run_summarize

    base = args.ollama_base_url or os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
    model = args.ollama_model or os.environ.get("OLLAMA_MODEL", "llama3.2")
    return run_summarize(log_path=args.log, base_url=base, model=model)


def _cmd_listen_ollama_summarize(_: argparse.Namespace) -> int:
    """對麥克風說關鍵字後執行 ollama-summarize（需 requirements-voice.txt）。"""
    from etoro_trading.scripts.voice_trigger_ollama_summarize import main as m

    return m()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m etoro_trading.scripts",
        description="eToro 專案統一腳本入口（整合多個工具，一個指令列程式）。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
子命令對照（舊模組仍可直接執行）：
  帳戶／持倉     today-summary, export-portfolio, daily-performance,
                 list-positions-tp, check-yesterday, debug-positions
  研究／匯出     fetch-fundamentals, calc-valuation, calc-correlation, calc-risk,
                 export-integrated, quantum-xlsx, generate-analysis
  資料建置       build-instrument-map, pick-watchlist, build-defense
  其他           track-alpha, simulate-retail, ollama-summarize, listen-ollama-summarize
""".strip(),
    )
    sub = p.add_subparsers(dest="command", required=True)

    def add(name: str, fn, help_text: str):
        sp = sub.add_parser(name, help=help_text, description=help_text)
        sp.set_defaults(_run=fn)
        return sp

    add("today-summary", _cmd_today_summary, "產出今日總結 Markdown（連線 API）")
    add("export-portfolio", _cmd_export_portfolio, "匯出 portfolio_summary.json（連線 API）")
    add("daily-performance", _cmd_daily_performance, "今日組合與市場表現報告（連線 API）")
    add("list-positions-tp", _cmd_list_positions_tp, "持倉與止盈候選清單（終端機 + md）")
    add("check-yesterday", _cmd_check_yesterday, "持倉標的昨日漲跌與策略建議（需先 export-portfolio）")
    add("debug-positions", _cmd_debug_positions, "除錯：印出 API 持倉原始結構")

    add("fetch-fundamentals", _cmd_fetch_fundamentals, "以 yfinance 抓取基本面 → fundamentals.json")
    add("calc-valuation", _cmd_calc_valuation, "依 fundamentals.json 簡易估值（需先 fetch-fundamentals）")
    add("calc-correlation", _cmd_calc_correlation, "標的相關性矩陣（eToro K 線）")
    add("calc-risk", _cmd_calc_risk, "投資組合風險評分（連線 API）")

    sp_int = add("export-integrated", _cmd_export_integrated, "匯出整合總表（Excel / 可選 Word）")
    sp_int.add_argument("--word", action="store_true", help="僅匯出 Word")
    sp_int.add_argument("--all", action="store_true", help="Excel + Word 皆匯出")

    add("quantum-xlsx", _cmd_quantum_xlsx, "產出量子板塊觀察清單 Excel")
    add("generate-analysis", _cmd_generate_analysis, "依 portfolio_summary 更新持倉分析 md")

    add("build-instrument-map", _cmd_build_instrument_map, "建立／擴充 instrument_ids.json（API，慢）")
    add("pick-watchlist", _cmd_pick_watchlist, "從持倉挑 5 檔做均線實驗觀察")
    add("build-defense", _cmd_build_defense, "防務板塊 eToro 解析並匯出 JSON/CSV")

    add("track-alpha", _cmd_track_alpha, "Alpha Portfolios 追蹤（yfinance + alpha_portfolios.json）")
    add("simulate-retail", _cmd_simulate_retail, "散戶 vs AI 策略模擬（示範）")

    sp_ol = add(
        "ollama-summarize",
        _cmd_ollama_summarize,
        "本機 Ollama 摘要最新自動化 log（需 ollama serve）",
    )
    sp_ol.add_argument("--log", type=Path, default=None, help="指定 log；預設最新 daily_*.log")
    sp_ol.add_argument(
        "--ollama-base-url",
        dest="ollama_base_url",
        default=None,
        help="預設由環境變數 OLLAMA_BASE_URL 或 http://127.0.0.1:11434/v1",
    )
    sp_ol.add_argument(
        "--ollama-model",
        dest="ollama_model",
        default=None,
        help="預設由環境變數 OLLAMA_MODEL 或 llama3.2",
    )

    add(
        "listen-ollama-summarize",
        _cmd_listen_ollama_summarize,
        "語音觸發：聽到關鍵字即跑 ollama-summarize（需 pip install -r requirements-voice.txt）",
    )

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    fn = getattr(args, "_run", None)
    if fn is None:
        parser.print_help()
        return 2
    return int(fn(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
