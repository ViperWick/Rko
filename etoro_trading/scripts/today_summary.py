# -*- coding: utf-8 -*-
"""
今日組合總結腳本

功能：
- 連線 eToro API（使用現有設定與金鑰）
- 取得帳戶餘額與持倉
- 計算現金比例、總資產、主要獲利/虧損標的
- 輸出一份 Markdown 報告到 docs/今日總結_YYYY-MM-DD.md

執行：
    python -m etoro_trading.scripts.today_summary
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from etoro_trading.core.etoro_client import EToroClient
from etoro_trading.core.portfolio import get_balance, get_positions
from etoro_trading.core.instrument_map import resolve_ids


BASE_DIR = Path(__file__).resolve().parents[1]
DOCS_DIR = BASE_DIR / "docs"


def _format_money(x: float | int) -> str:
    return f"${x:,.2f}"


def generate_summary() -> Path:
    """產生今日組合總結，回傳輸出檔案路徑。"""
    client = EToroClient()
    balance = get_balance(client)
    positions = get_positions(client)

    credit = balance["credit"]
    unrealized_pnl = balance["unrealized_pnl"]
    positions_value = sum(p.get("amount", 0) or 0 for p in positions)
    total_equity = credit + positions_value
    cash_pct = (credit / total_equity * 100) if total_equity > 0 else 100.0

    # 依標的彙總盈虧
    by_inst: dict[int, dict] = {}
    for p in positions:
        iid = p.get("instrument_id")
        if not iid:
            continue
        if iid not in by_inst:
            by_inst[iid] = {"amount": 0.0, "pnl": 0.0}
        by_inst[iid]["amount"] += p.get("amount", 0) or 0
        by_inst[iid]["pnl"] += p.get("pnl", 0) or 0

    id_to_symbol, id_to_name = ({}, {})
    if by_inst:
        id_to_symbol, id_to_name = resolve_ids(client, list(by_inst.keys()))

    summary_rows = []
    for iid, d in by_inst.items():
        amt = d["amount"]
        pnl = d["pnl"]
        symbol = id_to_symbol.get(iid, f"ID:{iid}")
        name = id_to_name.get(iid, "")
        pnl_pct = (pnl / amt * 100) if amt else 0.0
        summary_rows.append(
            {
                "instrument_id": iid,
                "symbol": symbol,
                "name": name,
                "amount": amt,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
            }
        )

    # 依損益排序
    top_gain = sorted(summary_rows, key=lambda r: r["pnl"], reverse=True)[:5]
    top_loss = sorted(summary_rows, key=lambda r: r["pnl"])[:5]

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DOCS_DIR / f"今日總結_{date_str}.md"

    lines: list[str] = []
    lines.append(f"# 今日總結 — {date_str}")
    lines.append("")
    lines.append(f"產出時間：{time_str}")
    lines.append("")
    lines.append("## 帳戶概況")
    lines.append("")
    lines.append(f"- **可用餘額**：{_format_money(credit)}")
    lines.append(f"- **持倉市值（以投入金額估算）**：{_format_money(positions_value)}")
    lines.append(f"- **總資產估計**：{_format_money(total_equity)}")
    lines.append(f"- **現金比例**：{cash_pct:.1f}%")
    lines.append(f"- **未實現損益**：{_format_money(unrealized_pnl)}")
    lines.append("")

    lines.append("## 主要獲利標的（前 5 檔，以未實現損益排序）")
    lines.append("")
    if not top_gain or all(r["pnl"] == 0 for r in top_gain):
        lines.append("目前無明顯獲利標的或資料不足。")
    else:
        lines.append("| 標的 | 名稱 | 投入金額 | 未實現損益 | 報酬率 |")
        lines.append("|------|------|----------|------------|--------|")
        for r in top_gain:
            lines.append(
                f"| {r['symbol']} | {r['name']} | "
                f"{_format_money(r['amount'])} | {_format_money(r['pnl'])} | {r['pnl_pct']:+.1f}% |"
            )
    lines.append("")

    lines.append("## 主要虧損標的（前 5 檔，以未實現損益排序）")
    lines.append("")
    if not top_loss or all(r["pnl"] == 0 for r in top_loss):
        lines.append("目前無明顯虧損標的或資料不足。")
    else:
        lines.append("| 標的 | 名稱 | 投入金額 | 未實現損益 | 報酬率 |")
        lines.append("|------|------|----------|------------|--------|")
        for r in top_loss:
            lines.append(
                f"| {r['symbol']} | {r['name']} | "
                f"{_format_money(r['amount'])} | {_format_money(r['pnl'])} | {r['pnl_pct']:+.1f}% |"
            )
    lines.append("")

    lines.append("## 筆記區（請自行補充）")
    lines.append("")
    lines.append("- 今天市場或組合有什麼特別的地方？")
    lines.append("- 有沒有需要調整的標的或倉位？")
    lines.append("- 下次回顧時想看什麼？")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main():
    path = generate_summary()
    print(f"今日總結已輸出：{path}")


if __name__ == "__main__":
    main()

