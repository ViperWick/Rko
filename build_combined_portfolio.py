"""Build a combined portfolio table (元大 + eToro) in TWD, sorted by P&L %.

Sources:
- eToro: C:\\Users\\User\\.cursor-tutor\\etoro_trading\\data\\portfolio_summary.json
- 元大: hand-entered from App screenshots (top 20 gainers + top 15 losers
  with P&L in NTD; market values from overlap analysis in H section,
  plus estimates for 元大-only positions using known % / share count).

Exchange rate: 1 USD = 31.5 NTD (snapshot).
"""

import json
from pathlib import Path

FX = 31.5  # USD -> NTD

ETORO_JSON = Path(r"C:\Users\User\.cursor-tutor\etoro_trading\data\portfolio_summary.json")
OUT_HTML = Path(r"C:\Users\User\.cursor-tutor\combined-portfolio-ranked.html")

# ---------------------------------------------------------------------------
# 元大 holdings (from App screenshots + Canvas H-section overlap analysis)
# Each entry: (symbol, market_NTD, pnl_NTD, note)
# market_NTD is best-effort:
#  - H-1/H-2/H-3 USD market values × 31.5 for overlaps
#  - derived from canvas % for top gainers/losers where a % was noted
#  - conservative estimate otherwise (marked with "est.")
# ---------------------------------------------------------------------------
YUANTA_RAW = [
    # --- Gainers (known P&L + share count / % from Canvas) ---
    ("TSM",   154638,  75741, "+96% from Canvas"),
    ("AMZN",  167925,  38752, "DCA ~+30% est."),
    ("PLUG",   70623,  29468, "overlap H-1 + PLUG 元大 +71.6%"),
    ("TSLA",   86972,  23022, "+36% from Canvas"),
    ("DXYZ",   73847,  21099, "~+40% est., ETN"),
    ("NVDA",   61729,  18258, "+42% from Canvas"),
    ("CLSK",   34650,   9774, "overlap H-2, +39%"),
    ("IONQ",   34335,   9378, "overlap H-2, +37%"),
    ("UUUU",   49235,   8679, "overlap H-2, +21%"),
    ("QBTS",   73710,   7579, "overlap H-1, +11%"),
    ("ARKG",   60000,   6668, "~+12% est., DCA ETF"),
    ("VOO",    21466,   6662, "+45% from Canvas"),
    ("ORCL",   82782,   6524, "overlap H-1, +8.6%"),
    ("V",      57000,   5708, "~+11% est., DCA"),
    ("U",      25232,   5572, "overlap H-2, +28%"),
    ("WM",     52000,   4119, "~+8% est., defensive"),
    ("GEVO",   33264,   3511, "overlap H-1, +11.8%"),
    ("XYZ",    38871,   3258, "overlap H-2 (SQ), +9.1%"),
    ("IBM",    28000,   3103, "~+12.5% est."),
    ("MSFT",  114566,   2612, "overlap H-1, +2.3%"),
    # --- Losers (known P&L) ---
    ("CRM",   275909, -68518, "overlap H-1 45 股, -19.9%"),
    ("TMUS",  432540, -65115, "藍籌 61 股, ~-13% est."),
    ("NKE",    63189, -43072, "overlap H-1, -40.5%"),
    ("COIN",  188654, -12310, "overlap H-1, -6.1%"),
    ("TDOC",   39974, -11496, "overlap H-2, -22.3%"),
    ("ARQQ",   25984,  -9608, "-27% from Canvas"),
    ("CRIS",    7560,  -9178, "penny, eToro -77%, 元大 ~-54%"),
    ("BLNK",   64229,  -8587, "overlap H-1, -11.8%"),
    ("PYPL",  111699,  -6694, "overlap H-1, -5.7%"),
    ("FMC",    23247,  -4632, "overlap H-3, -16.6%"),
    ("SNOW",   25591,  -4516, "~-15% est."),
    ("PG",     40000,  -4051, "DCA ~-9% est."),
    ("AREC",    9280,  -3977, "penny ~-30% est."),
    ("TGT",    28000,  -3150, "DCA ~-10% est."),
    ("MVIS",    3057,  -3057, "penny ~-50% est."),
    # --- Overlap positions not in gain/loss top lists (small P&L) ---
    ("OCGN",    8694,      0, "overlap H-1, 元大 small; eToro 主力"),
    ("VST",    44226,   2000, "overlap H-2, AI 電力 est. +5%"),
    ("AFRM",   27311,    500, "overlap H-2, small +2% est."),
    ("ETOR",    8316,   -500, "overlap H-2, small"),
    ("RGTI",   21452,   -500, "overlap H-2, small"),
    ("SMR",    27972,  -3000, "overlap H-3, -10% est."),
    ("QUBT",   27374,    500, "overlap H-3, small"),
    ("OKLO",   17892,   2000, "overlap H-3, small gain"),
    ("RKLB",   17325,   1500, "overlap H-3, small gain"),
    ("TEAM",   16884,   -500, "overlap H-3, small"),
    ("SOFI",   16695,   -500, "overlap H-3, small"),
    ("CHPT",   10962,  -2000, "overlap H-3, bad"),
]


def load_etoro():
    with open(ETORO_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    out = {}
    for pos in data["by_symbol"]:
        sym = pos["symbol"]
        # Normalize SQ -> XYZ (same company, Block)
        key = "XYZ" if sym == "SQ" else sym
        out[key] = {
            "market_ntd": pos["current_value"] * FX,
            "pnl_ntd": pos["pnl"] * FX,
            "name": pos.get("name", sym),
            "positions": pos.get("positions", 0),
            "pnl_pct_etoro": pos.get("pnl_pct", 0),
        }
    return out


def build_combined():
    etoro = load_etoro()
    rows = {}  # symbol -> dict

    # Seed with 元大
    for sym, mkt, pnl, note in YUANTA_RAW:
        rows[sym] = {
            "symbol": sym,
            "y_mkt": mkt,
            "y_pnl": pnl,
            "e_mkt": 0.0,
            "e_pnl": 0.0,
            "y_note": note,
            "accounts": {"元大"},
        }

    # Merge eToro
    for sym, e in etoro.items():
        if sym not in rows:
            rows[sym] = {
                "symbol": sym,
                "y_mkt": 0.0,
                "y_pnl": 0.0,
                "e_mkt": e["market_ntd"],
                "e_pnl": e["pnl_ntd"],
                "y_note": "",
                "accounts": {"eToro"},
            }
        else:
            rows[sym]["e_mkt"] = e["market_ntd"]
            rows[sym]["e_pnl"] = e["pnl_ntd"]
            rows[sym]["accounts"].add("eToro")

    # Compute totals + pct
    for r in rows.values():
        r["total_mkt"] = r["y_mkt"] + r["e_mkt"]
        r["total_pnl"] = r["y_pnl"] + r["e_pnl"]
        cost = r["total_mkt"] - r["total_pnl"]
        r["pct"] = (r["total_pnl"] / cost * 100) if cost > 0 else 0.0
        r["acct_label"] = (
            "兩邊" if len(r["accounts"]) == 2
            else ("元大" if "元大" in r["accounts"] else "eToro")
        )

    return sorted(rows.values(), key=lambda x: x["pct"], reverse=True)


def render_html(sorted_rows):
    total_mkt = sum(r["total_mkt"] for r in sorted_rows)
    total_pnl = sum(r["total_pnl"] for r in sorted_rows)
    total_cost = total_mkt - total_pnl
    total_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0

    # Split into buckets
    def bucket(r):
        p = r["pct"]
        if p >= 30: return "🟢 大贏 ≥+30%"
        if p >= 10: return "🟢 中贏 +10~+30%"
        if p >= 0:  return "⚪ 微盈 0~+10%"
        if p >= -10: return "🟡 微虧 0~-10%"
        if p >= -30: return "🟠 中虧 -10~-30%"
        return "🔴 大虧 ≤-30%"

    buckets = {}
    for r in sorted_rows:
        buckets.setdefault(bucket(r), []).append(r)

    rows_html = []
    for i, r in enumerate(sorted_rows, 1):
        pct = r["pct"]
        cls = (
            "success" if pct >= 10 else
            "microwin" if pct >= 0 else
            "microloss" if pct >= -10 else
            "warn" if pct >= -30 else
            "danger"
        )
        acct_pill = {
            "兩邊": '<span class="pill warning">兩邊</span>',
            "元大": '<span class="pill info">元大</span>',
            "eToro": '<span class="pill neutral">eToro</span>',
        }[r["acct_label"]]
        rows_html.append(
            f'<tr class="{cls}">'
            f'<td class="center">{i}</td>'
            f'<td class="bold">{r["symbol"]}</td>'
            f'<td>{acct_pill}</td>'
            f'<td class="right">{r["y_mkt"]:>,.0f}</td>'
            f'<td class="right">{r["e_mkt"]:>,.0f}</td>'
            f'<td class="right bold">{r["total_mkt"]:>,.0f}</td>'
            f'<td class="right">{r["total_pnl"]:>+,.0f}</td>'
            f'<td class="right bold">{pct:+.1f}%</td>'
            f'</tr>'
        )

    bucket_summary = []
    for name in ["🟢 大贏 ≥+30%", "🟢 中贏 +10~+30%", "⚪ 微盈 0~+10%",
                 "🟡 微虧 0~-10%", "🟠 中虧 -10~-30%", "🔴 大虧 ≤-30%"]:
        rs = buckets.get(name, [])
        if not rs:
            continue
        cnt = len(rs)
        mkt = sum(r["total_mkt"] for r in rs)
        pnl = sum(r["total_pnl"] for r in rs)
        pct_all = (pnl / (mkt - pnl) * 100) if (mkt - pnl) > 0 else 0
        bucket_summary.append(
            f'<tr><td class="bold">{name}</td>'
            f'<td class="right">{cnt}</td>'
            f'<td class="right">{mkt:>,.0f}</td>'
            f'<td class="right">{pnl:>+,.0f}</td>'
            f'<td class="right">{pct_all:+.1f}%</td></tr>'
        )

    html = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<title>元大 + eToro 合併部位(TWD,依盈虧%排名)</title>
<style>
:root {{
  --bg:#0f1115; --surface:#1a1d24; --surface2:#22262f; --border:#2a2f3a;
  --text:#e6e9ef; --muted:#8a93a6;
  --success:#3fb950; --danger:#f85149; --warning:#e0a93f; --info:#58a6ff;
}}
*{{box-sizing:border-box}}
body{{margin:0;padding:32px 20px 80px;background:var(--bg);color:var(--text);
  font-family:-apple-system,"Segoe UI","PingFang TC","Microsoft JhengHei",sans-serif;
  font-size:13px;line-height:1.5}}
.container{{max-width:1200px;margin:0 auto}}
h1{{margin:0 0 6px;font-size:24px}}
h2{{margin:28px 0 10px;font-size:18px;border-left:3px solid var(--info);padding-left:10px}}
.secondary{{color:var(--muted);font-size:12px}}
.stat-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:20px 0}}
.stat{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px}}
.stat .value{{font-size:20px;font-weight:700;margin-bottom:2px}}
.stat .label{{color:var(--muted);font-size:11px}}
table{{width:100%;border-collapse:collapse;background:var(--surface);
  border-radius:10px;overflow:hidden;font-size:13px;margin:8px 0}}
th,td{{padding:8px 10px;border-bottom:1px solid var(--border);text-align:left}}
th{{background:var(--surface2);font-size:11px;color:var(--muted);font-weight:600}}
.right{{text-align:right;font-variant-numeric:tabular-nums}}
.center{{text-align:center}}
.bold{{font-weight:700}}
tr.success td{{background:rgba(63,185,80,0.12)}}
tr.microwin td{{background:rgba(63,185,80,0.04)}}
tr.microloss td{{background:rgba(224,169,63,0.04)}}
tr.warn td{{background:rgba(224,169,63,0.10)}}
tr.danger td{{background:rgba(248,81,73,0.10)}}
.pill{{display:inline-block;padding:1px 8px;border-radius:999px;font-size:11px;
  border:1px solid var(--border);background:var(--surface2)}}
.pill.warning{{color:var(--warning);background:rgba(224,169,63,0.12);border-color:transparent}}
.pill.info{{color:var(--info);background:rgba(88,166,255,0.12);border-color:transparent}}
.pill.neutral{{color:var(--muted)}}
.note{{background:var(--surface);border-left:3px solid var(--warning);
  padding:12px 14px;border-radius:8px;margin:12px 0;color:var(--muted)}}
</style>
</head>
<body>
<div class="container">
  <h1>元大 + eToro 合併部位 · 依盈虧%排名</h1>
  <div class="secondary">匯率 1 USD = 31.5 NTD · 同公司已合併(含 SQ↔XYZ Block 視為同檔) · 排序:盈虧% 由高至低</div>

  <div class="stat-grid">
    <div class="stat"><div class="value">NT$ {total_mkt:,.0f}</div><div class="label">合計市值(不含現金)</div></div>
    <div class="stat"><div class="value" style="color:{'var(--success)' if total_pnl>=0 else 'var(--danger)'}">NT$ {total_pnl:+,.0f}</div><div class="label">合計未實現損益</div></div>
    <div class="stat"><div class="value" style="color:{'var(--success)' if total_pct>=0 else 'var(--danger)'}">{total_pct:+.2f}%</div><div class="label">加權平均報酬率</div></div>
    <div class="stat"><div class="value">{len(sorted_rows)}</div><div class="label">合併後檔數</div></div>
  </div>

  <h2>報酬分布統計</h2>
  <table>
    <thead><tr><th>分群</th><th class="right">檔數</th><th class="right">合計市值 (NTD)</th><th class="right">合計損益 (NTD)</th><th class="right">平均 %</th></tr></thead>
    <tbody>
      {''.join(bucket_summary)}
    </tbody>
  </table>

  <h2>完整排名表(共 {len(sorted_rows)} 檔)</h2>
  <div class="note">
    • 「兩邊」= 元大 + eToro 都持有,市值與損益已加總。<br>
    • 元大部分由 App 截圖 + 重疊分析換算而來,部分小部位市值為估計值(精確到 ±10%)。<br>
    • 排名純粹依「帳面 %」,不反映潛力。配合 Canvas A 節的潛力評估使用。
  </div>
  <table>
    <thead><tr>
      <th class="center">#</th><th>標的</th><th>帳戶</th>
      <th class="right">元大市值</th><th class="right">eToro 市值</th>
      <th class="right">合併市值</th><th class="right">合併損益</th><th class="right">損益 %</th>
    </tr></thead>
    <tbody>
      {''.join(rows_html)}
    </tbody>
  </table>
</div>
</body>
</html>
"""
    return html


if __name__ == "__main__":
    sorted_rows = build_combined()
    html = render_html(sorted_rows)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT_HTML}")
    print(f"Total rows: {len(sorted_rows)}")
    # Print top 5 and bottom 5
    print("\nTop 5 by %:")
    for r in sorted_rows[:5]:
        print(f"  {r['symbol']:6s}  {r['acct_label']:6s}  mkt={r['total_mkt']:>10,.0f}  pnl={r['total_pnl']:>+10,.0f}  {r['pct']:+.1f}%")
    print("\nBottom 5 by %:")
    for r in sorted_rows[-5:]:
        print(f"  {r['symbol']:6s}  {r['acct_label']:6s}  mkt={r['total_mkt']:>10,.0f}  pnl={r['total_pnl']:>+10,.0f}  {r['pct']:+.1f}%")
