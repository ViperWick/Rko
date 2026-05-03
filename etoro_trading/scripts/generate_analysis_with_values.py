# -*- coding: utf-8 -*-
"""
從 portfolio_summary.json 讀取持倉數據，更新持倉公司分析文件中的投入與淨值
執行: python -m etoro_trading.scripts.generate_analysis_with_values
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
SUMMARY_FILE = DATA_DIR / "portfolio_summary.json"
ANALYSIS_FILE = DOCS_DIR / "持倉公司分析_2025.md"


def main():
    if not SUMMARY_FILE.exists():
        print(f"找不到 {SUMMARY_FILE}，請先執行 export_portfolio_summary")
        return 1

    data = json.loads(SUMMARY_FILE.read_text(encoding="utf-8"))
    by_sym = {r["symbol"]: r for r in data.get("by_symbol", [])}

    if not ANALYSIS_FILE.exists():
        print(f"找不到 {ANALYSIS_FILE}")
        return 1

    content = ANALYSIS_FILE.read_text(encoding="utf-8")

    # 在文件開頭加入持倉總表（含投入與淨值）
    lines = []
    lines.append("| # | 標的 | 投入金額 | 當前淨值 | 佔比 |")
    lines.append("|---|------|----------|----------|------|")
    total_val = sum(r["current_value"] for r in data["by_symbol"][:50])
    for i, r in enumerate(data["by_symbol"][:50], 1):
        pct = (r["current_value"] / total_val * 100) if total_val else 0
        lines.append(f"| {i} | {r['symbol']} | ${r['amount']:,.0f} | ${r['current_value']:,.0f} | {pct:.1f}% |")

    table = "\n".join(lines)
    note = "\n> **說明**：淨值依總未實現損益比例分攤估算（API 未回傳個別持倉損益時）。\n"
    insert = f"\n{note}\n{table}\n\n---\n\n"

    # 在 "---" 第一個之後插入表格
    if "---\n\n## 一、大型科技股" in content:
        content = content.replace("---\n\n## 一、大型科技股", insert + "## 一、大型科技股")

    # 更新各小節標題：### N. Name (SYMBOL) — $X,XXX
    # 改為：### N. Name (SYMBOL) — 投入 $X,XXX | 淨值 $Y,YYY
    for r in data["by_symbol"][:50]:
        sym = r["symbol"]
        amt = r["amount"]
        val = r["current_value"]
        # 匹配 ### N. Name (SYMBOL) — $數字
        pat = rf'(### \d+\. [^(]+\({re.escape(sym)}\) — )\$[\d,]+'
        rep = rf'\g<1>投入 ${amt:,.0f} | 淨值 ${val:,.0f}'
        content = re.sub(pat, rep, content)

    ANALYSIS_FILE.write_text(content, encoding="utf-8")
    print(f"已更新 {ANALYSIS_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
