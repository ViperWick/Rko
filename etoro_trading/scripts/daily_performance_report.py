# -*- coding: utf-8 -*-
"""
今日組合表現 + 市場分析報告
- 查詢組合現況與今日損益（若已設定 ETORO_USERNAME）
- 以主要指數/標的當日變動推估「市場今日」表現
- 產出簡短文字分析
執行: python -m etoro_trading.scripts.daily_performance_report
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    import yfinance as yf
    HAS_YF = True
except ImportError:
    HAS_YF = False

from etoro_trading.core.config import get_config
from etoro_trading.core.etoro_client import EToroClient
from etoro_trading.core.instrument_map import resolve_ids
from etoro_trading.core.portfolio import get_balance, get_positions


# 用於「市場今日」的指數/標的（yfinance 代碼）
MARKET_SYMBOLS = [
    ("SPY", "標普 500"),
    ("QQQ", "納斯達克 100"),
    ("BTC-USD", "比特幣"),
    ("ETH-USD", "以太坊"),
]


def _get_num(obj: dict, keys: list, default=0):
    for k in keys:
        if k in obj and obj[k] is not None:
            try:
                return float(obj[k])
            except (TypeError, ValueError):
                pass
    return default


def get_portfolio_by_symbol(client: EToroClient):
    """持倉依標的彙總，回傳 (balance, rows_by_symbol)。"""
    balance = get_balance(client)
    positions = get_positions(client)
    by_inst = {}
    for p in positions:
        iid = p.get("instrument_id")
        if not iid:
            continue
        if iid not in by_inst:
            by_inst[iid] = {"amount": 0, "pnl": 0, "count": 0}
        by_inst[iid]["amount"] += p.get("amount", 0)
        by_inst[iid]["pnl"] += p.get("pnl", 0)
        by_inst[iid]["count"] += 1

    id_to_symbol, id_to_name = resolve_ids(client, list(by_inst.keys()))
    total_amount = sum(d["amount"] for d in by_inst.values())
    unrealized = balance.get("unrealized_pnl", 0)
    rows = []
    for iid, data in by_inst.items():
        amt = data["amount"]
        pnl = data["pnl"]
        if pnl != 0:
            current_value = amt + pnl
        elif total_amount and unrealized != 0:
            current_value = amt + (amt / total_amount) * unrealized
        else:
            current_value = amt
        pnl_pct = round((pnl / amt * 100), 1) if amt and pnl != 0 else (
            round((current_value - amt) / amt * 100, 1) if amt else 0
        )
        rows.append({
            "symbol": id_to_symbol.get(iid, f"ID:{iid}"),
            "amount": amt,
            "pnl": pnl,
            "current_value": current_value,
            "pnl_pct": pnl_pct,
        })
    rows.sort(key=lambda x: x["amount"], reverse=True)
    return balance, rows


def fetch_today_gain(client: EToroClient, username: str) -> float | None:
    """取得「今日」損益（當日 gain）。若 API 回傳 Period 則為單日合計。"""
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        data = client.get_daily_gain(username, today, today, period_type="Daily")
        if isinstance(data, list) and len(data) > 0:
            return float(data[0].get("gain", 0))
        if isinstance(data, dict) and "gain" in data:
            return float(data["gain"])
        return 0.0
    except Exception:
        return None


def fetch_market_today() -> list[dict]:
    """取得主要指數/標的「最近一個交易日」較前一日之漲跌幅（%）。"""
    if not HAS_YF:
        return []
    end = datetime.now()
    start = end - timedelta(days=10)
    results = []
    for symbol, name in MARKET_SYMBOLS:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start, end=end, auto_adjust=True)
            if hist is None or len(hist) < 2:
                results.append({"symbol": symbol, "name": name, "change_pct": None})
                continue
            hist = hist.sort_index()
            last_two = hist.tail(2)
            if len(last_two) < 2:
                results.append({"symbol": symbol, "name": name, "change_pct": None})
                continue
            prev = last_two.iloc[-2]["Close"]
            curr = last_two.iloc[-1]["Close"]
            if prev and prev > 0:
                change_pct = (curr / prev - 1) * 100
                results.append({
                    "symbol": symbol,
                    "name": name,
                    "change_pct": round(change_pct, 2),
                    "prev_close": prev,
                    "curr_close": curr,
                })
            else:
                results.append({"symbol": symbol, "name": name, "change_pct": None})
        except Exception:
            results.append({"symbol": symbol, "name": name, "change_pct": None})
    return results


def analyze_market_tone(market_changes: list[dict]) -> str:
    """根據主要指數當日變動給一句簡短市場氛圍描述。"""
    valid = [m for m in market_changes if m.get("change_pct") is not None]
    if not valid:
        return "今日主要指數資料不足，無法判斷市場氛圍。"
    avg = sum(m["change_pct"] for m in valid) / len(valid)
    up = [m for m in valid if m["change_pct"] > 0]
    down = [m for m in valid if m["change_pct"] < 0]
    if avg >= 0.5:
        return "今日風險資產普遍偏多，標普/納指與加密貨幣多數上漲，市場情緒偏樂觀。"
    if avg <= -0.5:
        return "今日風險資產普遍承壓，主要指數與加密多數下跌，市場情緒偏謹慎。"
    if up and down:
        return "今日主要指數漲跌互見，市場呈區間震盪、方向不明。"
    return "今日主要市場變動不大，整體偏中性。"


def analyze_portfolio_vs_market(
    today_gain: float | None,
    unrealized_pnl: float,
    total_equity: float,
    market_changes: list[dict],
) -> str:
    """組合表現與市場的簡短對比分析。"""
    lines = []
    if today_gain is not None:
        if total_equity and total_equity > 0:
            today_pct = (today_gain / total_equity) * 100
            lines.append(f"今日組合損益約 {today_pct:+.2f}%（約 ${today_gain:+,.2f}）。")
        else:
            lines.append(f"今日組合損益約 ${today_gain:+,.2f}。")
    else:
        lines.append("今日組合損益需設定 ETORO_USERNAME 並使用 eToro 每日績效 API 才能取得。")

    valid_market = [m for m in market_changes if m.get("change_pct") is not None]
    if valid_market:
        avg_market = sum(m["change_pct"] for m in valid_market) / len(valid_market)
        lines.append(f"主要市場今日平均變動約 {avg_market:+.2f}%。")
        if today_gain is not None and total_equity and total_equity > 0:
            today_pct = (today_gain / total_equity) * 100
            if today_pct > avg_market + 0.3:
                lines.append("您的組合今日表現優於大盤平均。")
            elif today_pct < avg_market - 0.3:
                lines.append("您的組合今日表現落後大盤平均，可能與持倉結構或個股波動有關。")
            else:
                lines.append("您的組合今日表現與大盤平均接近。")

    if unrealized_pnl < -1000:
        lines.append("目前未實現虧損較大，建議留意持倉集中度與止損紀律。")
    return " ".join(lines)


def main():
    print("=" * 60)
    print("今日組合表現與市場分析")
    print("=" * 60)

    cfg = get_config()
    client = EToroClient()
    balance, by_symbol = get_portfolio_by_symbol(client)

    total_invested = sum(r["amount"] for r in by_symbol)
    total_equity = balance["credit"] + total_invested
    unrealized = balance.get("unrealized_pnl", 0)

    # ----- 組合現況 -----
    print("\n【一、組合現況】")
    print(f"  可用餘額: ${balance['credit']:,.2f}")
    print(f"  持倉市值（投入）: ${total_invested:,.2f}")
    print(f"  未實現損益: ${unrealized:+,.2f}")
    print(f"  總資產約: ${total_equity:,.2f}")
    print(f"  持倉筆數: {balance['positions_count']}")

    # ----- 今日損益（若有 username） -----
    today_gain = None
    username = cfg.get("username")
    if username:
        print("\n【二、今日損益】")
        try:
            today_gain = fetch_today_gain(client, username)
            if today_gain is not None:
                print(f"  今日損益: ${today_gain:+,.2f}")
            else:
                print("  無法取得今日損益（API 無資料或非交易日）。")
        except Exception as e:
            print(f"  取得今日損益失敗: {e}")
    else:
        print("\n【二、今日損益】")
        print("  請在 .env 設定 ETORO_USERNAME（eToro 用戶名）以取得每日損益。")

    # ----- 市場今日 -----
    print("\n【三、市場今日】（最近一個交易日較前一日漲跌幅）")
    if HAS_YF:
        market_changes = fetch_market_today()
        for m in market_changes:
            cp = m.get("change_pct")
            if cp is not None:
                print(f"  {m['name']} ({m['symbol']}): {cp:+.2f}%")
            else:
                print(f"  {m['name']} ({m['symbol']}): 無資料")
    else:
        market_changes = []
        print("  請安裝 yfinance: pip install yfinance")

    # ----- 簡短分析 -----
    print("\n【四、簡短分析】")
    print("  市場氛圍: " + analyze_market_tone(market_changes))
    print("  組合與市場: " + analyze_portfolio_vs_market(
        today_gain, unrealized, total_equity, market_changes
    ))

    # 寫出 JSON 供其他程式使用（可選）
    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "updated_at": datetime.now().isoformat()[:19],
        "balance": balance,
        "total_equity": round(total_equity, 2),
        "unrealized_pnl": unrealized,
        "today_gain": today_gain,
        "market_today": [
            {"symbol": m["symbol"], "name": m["name"], "change_pct": m.get("change_pct")}
            for m in (market_changes if HAS_YF else [])
        ],
    }
    out_file = out_dir / "daily_performance_report.json"
    out_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n報告已寫入: {out_file}")

    print("\n" + "=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
