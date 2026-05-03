# -*- coding: utf-8 -*-
"""
eToro 交易程式 - Web UI 介面
執行（專案根目錄）: streamlit run etoro_trading/ui/app_ui.py
或雙擊: etoro_trading/啟動檔/run_ui.bat
"""
import sys
from pathlib import Path

# 套件根 = etoro_trading/；其上層 = repo 根（供 sys.path）
_pkg_root = Path(__file__).resolve().parent.parent
_repo_root = _pkg_root.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

# 優先載入 .env（Streamlit 啟動時工作目錄可能不同）
_env_file = _pkg_root / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        pass

import json
import streamlit as st
from etoro_trading.core.etoro_client import EToroClient
from etoro_trading.core.instrument_map import resolve_ids
from etoro_trading.core.portfolio import get_balance, get_positions
from etoro_trading.core.risk_score import calc_risk_score
from etoro_trading.core.trading import buy, sell, close
from etoro_trading.core.strategy import dca_buy, dca_buy_with_signal, check_stop_loss, check_take_profit


CONFIG_DIR = _pkg_root / "data"
POSITION_CONFIG_FILE = CONFIG_DIR / "position_config.json"
STRATEGY_CONFIG_FILE = CONFIG_DIR / "strategy_config.json"
API_COMMANDS_FILE = CONFIG_DIR / "api_commands.json"

DEFAULT_POSITION_CONFIG = {
    "min_cash_pct": 20.0,   # 最低現金比例：低於此暫停 DCA
    "target_cash_pct": 30.0,  # 目標現金比例：高於此可執行 DCA
    "max_dca_per_trade": 400.0,  # 單筆 DCA 上限 (USD)
}


def load_position_config() -> dict:
    """讀取倉位評估水位設定"""
    try:
        if POSITION_CONFIG_FILE.exists():
            return json.loads(POSITION_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return DEFAULT_POSITION_CONFIG.copy()


def save_position_config(cfg: dict) -> bool:
    """儲存倉位評估水位設定"""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        POSITION_CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def load_strategy_config() -> dict | None:
    """讀取策略配置（供 UI 顯示）"""
    try:
        if STRATEGY_CONFIG_FILE.exists():
            return json.loads(STRATEGY_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def load_api_commands() -> dict | None:
    """讀取 eToro API 指令對照（供 UI 顯示）"""
    try:
        if API_COMMANDS_FILE.exists():
            return json.loads(API_COMMANDS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def render_api_commands():
    """顯示 eToro 官方 API 指令對照（可執行動作與本介面對應）"""
    data = load_api_commands()
    if not data:
        st.info("API 指令對照載入中…（請確認 data/api_commands.json 存在）")
        return

    st.subheader(data.get("title", "eToro API 指令對照"))
    st.caption(data.get("description", ""))
    st.caption(f"更新：{data.get('updated_at', '')}")

    commands = data.get("commands", [])
    if not commands:
        st.warning("尚無指令資料")
        return

    for cmd in commands:
        with st.expander(f"**{cmd.get('name', '')}** — {cmd.get('endpoint', '')}", expanded=False):
            st.write("**API 說明**：", cmd.get("api_summary", ""))
            st.write("**本介面對應**：", cmd.get("ui_action", ""))
            doc_link = cmd.get("doc_link")
            if doc_link:
                st.markdown(f"[📄 官方文件]({doc_link})")
    st.markdown("---")


def render_strategy_overview():
    """顯示策略總覽（固定顯示在 UI 中）"""
    cfg = load_strategy_config()
    if not cfg:
        st.info("策略配置載入中…（請確認 data/strategy_config.json 存在）")
        return

    with st.container():
        st.markdown("---")
        st.subheader(f"📋 {cfg.get('title', '策略總覽')}")
        st.caption(f"更新：{cfg.get('updated_at', '')}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**資產動作**")
            for item in cfg.get("asset_actions", []):
                action_emoji = "🟢" if "加倉" in item.get("action", "") else "🔴" if "減" in item.get("action", "") else "⏸"
                st.write(f"{action_emoji} **{item['asset']}**：{item['action']} — {item['desc']}")

        with col2:
            st.markdown("**賣出規則**")
            for item in cfg.get("sell_rules", []):
                st.write(f"• {item['condition']} → {item['action']}")

        with st.expander("📊 ETF 買入清單（順勢）", expanded=True):
            for e in cfg.get("etf_buy_list", []):
                st.write(f"**{e['symbol']}** {e['weight']} | {e['role']} | 單筆 {e['amount']}")

        with st.expander("⚡ 槓桿 ETF（買跌）", expanded=True):
            for e in cfg.get("leverage_etf", []):
                st.write(f"**{e['symbol']}** | 單筆 {e['amount']} | {e['trigger']}")

        st.markdown("---")


def pick_watchlist(client) -> list[dict]:
    """從持倉中挑選 5 檔適合 20 週均線策略測試的標的"""
    positions = get_positions(client)
    if not positions:
        return []

    by_instrument = {}
    for p in positions:
        iid = p.get("instrument_id")
        if not iid:
            continue
        if iid not in by_instrument:
            by_instrument[iid] = {"amount": 0, "positions": 0}
        by_instrument[iid]["amount"] += p.get("amount", 0)
        by_instrument[iid]["positions"] += 1

    sorted_ids = sorted(by_instrument.keys(), key=lambda x: by_instrument[x]["amount"], reverse=True)[:10]
    id_to_symbol, id_to_name = resolve_ids(client, sorted_ids)

    result = []
    for iid in sorted_ids[:5]:
        result.append({
            "instrument_id": iid,
            "name": id_to_name.get(iid, f"ID:{iid}"),
            "symbol": id_to_symbol.get(iid, ""),
            "amount": by_instrument[iid]["amount"],
        })
    return result

st.set_page_config(page_title="eToro 交易", page_icon="📈", layout="wide")

# 自訂樣式
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-value { font-size: 1.8rem; font-weight: bold; }
    .metric-label { font-size: 0.9rem; opacity: 0.9; }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


def init_client():
    """初始化 API 客戶端"""
    # 優先使用 session 中手動輸入的金鑰
    if "etoro_api_key" in st.session_state and "etoro_user_key" in st.session_state:
        if st.session_state["etoro_api_key"] and st.session_state["etoro_user_key"]:
            try:
                return EToroClient(
                    api_key=st.session_state["etoro_api_key"],
                    user_key=st.session_state["etoro_user_key"],
                )
            except Exception as e:
                st.error(f"連線失敗: {e}")
                return None

    try:
        return EToroClient()
    except Exception as e:
        return None


def render_key_form():
    """顯示金鑰輸入表單"""
    st.error("❌ 無法連線：請在下方輸入 eToro API 金鑰（需為 Real 真實帳戶金鑰）")
    with st.form("api_key_form"):
        api_key = st.text_input("公用金鑰 (Public Key)", type="password", placeholder="從 eToro 頁面上方複製")
        user_key = st.text_input("已生成金鑰 (User Key)", type="password", placeholder="從 eToro 下方「已生成金鑰」複製")
        if st.form_submit_button("🔑 儲存並連線"):
            if api_key and user_key:
                st.session_state["etoro_api_key"] = api_key.strip()
                st.session_state["etoro_user_key"] = user_key.strip()
                st.success("金鑰已儲存！")
                st.rerun()
            else:
                st.warning("請填寫兩個金鑰")


def render_portfolio(client):
    """顯示投資組合"""
    st.subheader("📊 帳戶概覽")
    try:
        balance = get_balance(client)
        positions = get_positions(client)

        # 總資產 = 現金 + 持倉市值（以投入金額估算）
        credit = balance["credit"]
        positions_value = sum(p.get("amount", 0) for p in positions)
        total_equity = credit + positions_value
        cash_pct = (credit / total_equity * 100) if total_equity > 0 else 100.0

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("可用餘額", f"${credit:,.2f}")
        with col2:
            st.metric("現金比例", f"{cash_pct:.1f}%", help="現金 ÷ 總資產")
        with col3:
            pnl = balance["unrealized_pnl"]
            st.metric("未實現損益", f"${pnl:,.2f}", delta=f"{pnl:+.2f}" if pnl else None)
        with col4:
            st.metric("持倉數", balance["positions_count"])
        with col5:
            st.metric("待處理訂單", balance["orders_count"])

        # 風險評分
        by_inst_risk = {}
        for p in positions:
            iid = p.get("instrument_id")
            if not iid:
                continue
            if iid not in by_inst_risk:
                by_inst_risk[iid] = {"amount": 0, "pnl": 0}
            by_inst_risk[iid]["amount"] += p.get("amount", 0) or 0
            by_inst_risk[iid]["pnl"] += p.get("pnl", 0) or 0
        id_to_sym, _ = resolve_ids(client, list(by_inst_risk.keys()))
        by_symbol_risk = []
        for iid, d in by_inst_risk.items():
            amt, pnl = d["amount"], d["pnl"]
            cv = amt + pnl
            pnl_pct = round((pnl / amt * 100), 1) if amt else 0.0
            by_symbol_risk.append({
                "symbol": id_to_sym.get(iid, f"ID:{iid}"),
                "amount": amt,
                "current_value": cv,
                "pnl_pct": pnl_pct,
            })
        corr_file = _pkg_root / "data" / "correlation_matrix.csv"
        try:
            risk_result = calc_risk_score(
                by_symbol=by_symbol_risk,
                cash=credit,
                total_equity=total_equity,
                total_unrealized_pnl=balance.get("unrealized_pnl", 0),
                correlation_file=corr_file if corr_file.exists() else None,
            )
            with st.expander("⚠️ 風險評分", expanded=True):
                st.metric("綜合風險", f"{risk_result.overall:.1f}/100", risk_result.summary)
                for d in risk_result.dimensions:
                    st.caption(f"**{d.name}** {d.score:.1f} — {d.detail}")
        except Exception as ex:
            with st.expander("⚠️ 風險評分"):
                st.warning(f"計算失敗: {ex}")

        # 倉位評估水位（依使用者設定）
        cfg = load_position_config()
        min_pct = cfg.get("min_cash_pct", 20)
        target_pct = cfg.get("target_cash_pct", 30)
        with st.expander("📐 倉位評估水位", expanded=True):
            st.caption("依您設定的最低/目標現金比例評估 DCA 建議")
            if cash_pct < min_pct:
                st.warning(f"⚠️ 現金 {cash_pct:.1f}% < 最低 {min_pct}% → **建議暫停 DCA**，保留現金")
            elif cash_pct >= target_pct:
                st.success(f"✅ 現金 {cash_pct:.1f}% ≥ 目標 {target_pct}% → **可執行 DCA**")
            else:
                st.info(f"📊 現金 {cash_pct:.1f}% 介於 {min_pct}%–{target_pct}% → 可減量 DCA 或觀望")
            st.write(f"總資產約 ${total_equity:,.0f} | 持倉市值約 ${positions_value:,.0f}")

        # Alpha Portfolios 追蹤
        alpha_file = _pkg_root / "data" / "alpha_portfolios_tracking.json"
        if alpha_file.exists():
            try:
                alpha_data = json.loads(alpha_file.read_text(encoding="utf-8"))
                with st.expander("📊 Alpha Portfolios 追蹤（近 20 日模擬報酬）"):
                    for p in alpha_data.get("portfolios", []):
                        ret = p.get("return_20d_pct")
                        ret_str = f"{ret:+.1f}%" if ret is not None else "—"
                        st.write(f"**{p.get('name', '')}** — {ret_str} ({p.get('symbols_count', 0)} 檔)")
                    st.caption(f"更新：{alpha_data.get('updated_at', '')} | 成分股需手動填入 alpha_portfolios.json")
            except Exception:
                pass

        # 實驗觀察名單
        with st.expander("📌 20 週均線策略 - 實驗觀察名單（從持倉挑選 5 檔）"):
            try:
                watchlist = pick_watchlist(client)
                if not watchlist:
                    st.info("無持倉可挑選")
                else:
                    for i, w in enumerate(watchlist, 1):
                        st.write(f"**{i}. {w['name']}** ({w['symbol']}) — 持倉 ${w['amount']:,.0f}")
                    st.caption("以上 5 檔可作為 20 週均線策略的測試標的")
            except Exception as e:
                st.error(str(e))

        st.subheader("📋 持倉明細（依盈虧分類）")
        if not positions:
            st.info("目前無持倉")
        else:
            # 彙總依標的，計算 pnl_pct 並分成三類
            by_inst = {}
            for p in positions:
                iid = p.get("instrument_id")
                if not iid:
                    continue
                if iid not in by_inst:
                    by_inst[iid] = {"amount": 0, "pnl": 0, "count": 0}
                by_inst[iid]["amount"] += p.get("amount", 0) or 0
                by_inst[iid]["pnl"] += p.get("pnl", 0) or 0
                by_inst[iid]["count"] += 1
            ids = list(by_inst.keys())
            id_to_symbol, id_to_name = resolve_ids(client, ids)
            by_symbol = []
            for iid, d in by_inst.items():
                amt, pnl = d["amount"], d["pnl"]
                cv = amt + pnl
                pnl_pct = round((pnl / amt * 100), 1) if amt else 0.0
                by_symbol.append({
                    "symbol": id_to_symbol.get(iid, f"ID:{iid}"),
                    "name": id_to_name.get(iid, ""),
                    "amount": round(amt, 2),
                    "pnl": round(pnl, 2),
                    "current_value": round(cv, 2),
                    "pnl_pct": pnl_pct,
                    "positions": d["count"],
                })
            by_symbol.sort(key=lambda x: -x["amount"])
            TAKE_PROFIT_PCT = 20.0
            tp_candidates = [r for r in by_symbol if (r.get("pnl_pct") or 0) >= TAKE_PROFIT_PCT]
            positive = [r for r in by_symbol if 0 <= (r.get("pnl_pct") or 0) < TAKE_PROFIT_PCT]
            negative = [r for r in by_symbol if (r.get("pnl_pct") or 0) < 0]
            tp_candidates.sort(key=lambda x: -(x.get("pnl_pct") or 0))
            positive.sort(key=lambda x: -(x.get("pnl_pct") or 0))
            negative.sort(key=lambda x: (x.get("pnl_pct") or 0))

            def to_table(rows, with_name=False):
                if with_name:
                    return [{"#": i, "代碼": r["symbol"], "名稱": (r.get("name") or "")[:20], "投入": f"${r['amount']:,.0f}", "淨值": f"${r['current_value']:,.0f}", "PnL": f"${r['pnl']:,.0f}", "PnL%": f"{r.get('pnl_pct',0):+.1f}%", "筆數": r.get("positions", 0)} for i, r in enumerate(rows, 1)]
                return [{"#": i, "代碼": r["symbol"], "投入": f"${r['amount']:,.0f}", "淨值": f"${r['current_value']:,.0f}", "PnL": f"${r['pnl']:,.0f}", "PnL%": f"{r.get('pnl_pct',0):+.1f}%", "筆數": r.get("positions", 0)} for i, r in enumerate(rows, 1)]

            st.markdown("#### 1️⃣ 止盈候選（獲利 ≥ 20%）")
            if tp_candidates:
                st.dataframe(to_table(tp_candidates, with_name=True), use_container_width=True, hide_index=True)
            else:
                st.caption("（無）")
            st.markdown("#### 2️⃣ 正報酬（0% < 獲利 < 20%）")
            if positive:
                st.dataframe(to_table(positive), use_container_width=True, hide_index=True)
            else:
                st.caption("（無）")
            st.markdown("#### 3️⃣ 負報酬（虧損）")
            if negative:
                st.dataframe(to_table(negative), use_container_width=True, hide_index=True)
            else:
                st.caption("（無）")
        return positions
    except Exception as e:
        st.error(f"取得資料失敗: {e}")
        return []


def render_trade(client, positions):
    """交易區塊"""
    st.subheader("💹 交易")
    tab1, tab2, tab3 = st.tabs(["買入", "賣出", "平倉"])

    with tab1:
        with st.form("buy_form"):
            buy_symbol = st.text_input("標的代碼", "BTC", placeholder="如 BTC, AAPL, ETH")
            buy_amount = st.number_input("金額 (USD)", min_value=1.0, value=100.0, step=10.0)
            if st.form_submit_button("🟢 買入"):
                try:
                    result = buy(client, symbol=buy_symbol, amount=buy_amount)
                    st.success(f"下單成功！{result}")
                except Exception as e:
                    st.error(str(e))

    with tab2:
        with st.form("sell_form"):
            sell_symbol = st.text_input("標的代碼（賣空）", "AAPL", placeholder="如 AAPL, TSLA")
            sell_amount = st.number_input("金額 (USD)", min_value=1.0, value=50.0, step=10.0)
            if st.form_submit_button("🔴 賣出（開空倉）"):
                try:
                    result = sell(client, symbol=sell_symbol, amount=sell_amount)
                    st.success(f"下單成功！{result}")
                except Exception as e:
                    st.error(str(e))

    with tab3:
        closable = [p for p in positions if p.get("position_id")]
        if not closable:
            st.info("無可平倉的持倉（跟單持倉可能無法在此平倉）")
        else:
            with st.form("close_form"):
                pos_options = {f"ID:{p['position_id']} | ${p['amount']:,.0f} | 損益:${p['pnl']:,.2f}": p["position_id"] for p in closable}
                selected = st.selectbox("選擇持倉", options=list(pos_options.keys()))
                close_all = st.checkbox("全部平倉", value=True)
                units = None if close_all else st.number_input("平倉單位數", min_value=0.01, value=0.0, step=0.1)
                if st.form_submit_button("⏹ 平倉"):
                    pos_id = pos_options.get(selected) if selected in pos_options else list(pos_options.values())[0] if pos_options else None
                    if not pos_id:
                        st.error("請選擇持倉")
                    else:
                        try:
                            result = close(client, position_id=pos_id, units=units if units else None)
                            st.success(f"平倉成功！{result}")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))


def _render_signal_preview(symbol: str, signal_type: str, client):
    """在策略頁預覽單一或綜合訊號（資料來自 eToro API）"""
    if signal_type == "composite":
        mults = []
        try:
            from etoro_trading.signals.retail_signals import get_momentum_signal, get_dca_multiplier
            sig = get_momentum_signal(symbol, client)
            m = get_dca_multiplier(sig)
            mults.append(("零售動量", m, sig.reason if sig else "—"))
        except Exception:
            mults.append(("零售動量", 1.0, "取得失敗"))
        try:
            from etoro_trading.signals.breakout_signals import get_breakout_signal, get_dca_multiplier_breakout
            sig = get_breakout_signal(symbol, client)
            m = get_dca_multiplier_breakout(sig)
            mults.append(("突破", m, sig.reason if sig else "—"))
        except Exception:
            mults.append(("突破", 1.0, "取得失敗"))
        try:
            from etoro_trading.signals.rsi_signals import get_rsi_signal, get_dca_multiplier_rsi
            sig = get_rsi_signal(symbol, client)
            m = get_dca_multiplier_rsi(sig)
            mults.append(("RSI", m, sig.reason if sig else "—"))
        except Exception:
            mults.append(("RSI", 1.0, "取得失敗"))
        try:
            from etoro_trading.signals.volatility_signals import get_volatility_signal, get_dca_multiplier_volatility
            sig = get_volatility_signal(symbol, client)
            m = get_dca_multiplier_volatility(sig)
            mults.append(("波動度", m, sig.reason if sig else "—"))
        except Exception:
            mults.append(("波動度", 1.0, "取得失敗"))
        final = min(m for _, m, _ in mults)
        st.write(f"**{symbol}** 綜合：取最保守倍數 = **{final}x**")
        for name, m, reason in mults:
            st.caption(f"• {name}: {m}x — {reason}")
        st.caption(f"實際 DCA 金額 = 原金額 × {final}")
        return
    if signal_type == "retail":
        from etoro_trading.signals.retail_signals import get_momentum_signal, get_dca_multiplier
        sig = get_momentum_signal(symbol, client)
        if not sig:
            st.warning("無法取得訊號（請確認標的代碼正確）")
            return
        mult = get_dca_multiplier(sig)
        st.write(f"**{sig.symbol}** | 近 20 日報酬 {sig.momentum_20d_pct:+.1f}% | 訊號: **{sig.signal}**")
        st.caption(sig.reason)
        st.caption(f"DCA 倍數: {mult}x")
        return
    if signal_type == "breakout":
        from etoro_trading.signals.breakout_signals import get_breakout_signal, get_dca_multiplier_breakout
        sig = get_breakout_signal(symbol, client)
        if not sig:
            st.warning("無法取得訊號（請確認標的代碼正確）")
            return
        mult = get_dca_multiplier_breakout(sig)
        st.write(f"**{sig.symbol}** | 收盤 {sig.close:.2f} | 20日高/低 {sig.high_20d:.2f} / {sig.low_20d:.2f} | 訊號: **{sig.signal}**")
        st.caption(sig.reason)
        st.caption(f"DCA 倍數: {mult}x")
        return
    if signal_type == "rsi":
        from etoro_trading.signals.rsi_signals import get_rsi_signal, get_dca_multiplier_rsi
        sig = get_rsi_signal(symbol, client)
        if not sig:
            st.warning("無法取得訊號（請確認標的代碼正確）")
            return
        mult = get_dca_multiplier_rsi(sig)
        st.write(f"**{sig.symbol}** | RSI(14) = {sig.rsi:.1f} | 訊號: **{sig.signal}**")
        st.caption(sig.reason)
        st.caption(f"DCA 倍數: {mult}x")
        return
    if signal_type == "volatility":
        from etoro_trading.signals.volatility_signals import get_volatility_signal, get_dca_multiplier_volatility
        sig = get_volatility_signal(symbol, client)
        if not sig:
            st.warning("無法取得訊號（請確認標的代碼正確）")
            return
        mult = get_dca_multiplier_volatility(sig)
        st.write(f"**{sig.symbol}** | 近 20 日波動 {sig.vol_pct:.2f}% | 訊號: **{sig.signal}**")
        st.caption(sig.reason)
        st.caption(f"DCA 倍數: {mult}x")
        return


def load_valuation_suggestions():
    """從 fundamentals.json 讀取估值建議，供 DCA 參考"""
    try:
        fund_file = _pkg_root / "data" / "fundamentals.json"
        if not fund_file.exists():
            return []
        data = json.loads(fund_file.read_text(encoding="utf-8"))
        suggestions = []
        for r in data:
            sym = r.get("symbol", "")
            pe = r.get("peRatio")
            ps = r.get("priceToSales")
            rg = r.get("revenueGrowth")
            if pe is not None and pe > 0:
                if pe < 15:
                    suggestions.append((sym, "便宜", "可加碼"))
                elif pe <= 25:
                    suggestions.append((sym, "合理", "可加碼"))
                else:
                    suggestions.append((sym, "偏貴", "觀望"))
            elif rg is not None and rg > 0.2 and ps is not None:
                if ps < 5:
                    suggestions.append((sym, "可考慮", "可加碼"))
                elif ps < 15:
                    suggestions.append((sym, "觀望", "減量"))
                else:
                    suggestions.append((sym, "暫緩", "跳過"))
            else:
                suggestions.append((sym, "—", "—"))
        return suggestions
    except Exception:
        return []


def render_strategy(client):
    """策略區塊"""
    st.subheader("📌 策略與自動下單")

    # 綜合評分（當前適合怎麼做）
    with st.expander("📊 綜合評分 — 當前適合怎麼做（eToro 數據）", expanded=True):
        st.caption("輸入標的後查詢：彙總零售動量、突破、RSI、波動度，給出 1–10 分與建議。")
        comp_symbol = st.text_input("標的", "GLD", key="composite_symbol", placeholder="如 GLD, NKE")
        if st.button("查詢綜合評分", key="query_composite"):
            try:
                from etoro_trading.core.composite_score import get_composite_score
                result = get_composite_score(comp_symbol.strip(), client)
                if not result:
                    st.warning("無法取得數據（請確認標的可在 eToro 搜尋到）")
                else:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("綜合分數", f"{result.score}/10", help="10=強烈加碼、5=正常、1=強烈減量")
                    with col2:
                        st.metric("當前建議", result.recommendation, help="依四項指標平均")
                    with col3:
                        st.metric("建議 DCA 倍數", f"{result.suggested_mult}x", help="原金額 × 此倍數")
                    st.info(result.summary)
                    st.write("**各指標**")
                    for row in result.indicators:
                        st.caption(f"• **{row.name}** {row.value} → {row.signal} ({row.mult}x) — {row.reason}")
            except Exception as e:
                st.error(str(e))

    # 與 AI 討論：直接讀取組合，產出「當前形勢適合什麼策略」的討論摘要
    with st.expander("🤖 與 AI 討論 — 根據我的組合與當前訊號（讀取 eToro 數據）", expanded=True):
        st.caption("讀取你的 eToro 持倉與各標的綜合評分，產出摘要。可複製下方文字貼到與 Cursor/AI 的對話，繼續討論「最近形勢適合什麼策略」。")
        if st.button("產生策略討論摘要（讀取我的組合）", key="gen_briefing"):
            try:
                from etoro_trading.core.portfolio_strategy_briefing import get_portfolio_strategy_briefing
                new_brief = get_portfolio_strategy_briefing(client)
                st.session_state["strategy_briefing"] = new_brief
            except Exception as e:
                st.error(str(e))
                st.session_state.pop("strategy_briefing", None)
        brief = st.session_state.get("strategy_briefing")
        if brief:
            st.write("**組合概況**")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("可用餘額", f"${brief.credit:,.2f}")
            with c2:
                st.metric("現金比例", f"{brief.cash_pct:.1f}%")
            with c3:
                st.metric("未實現損益", f"${brief.unrealized_pnl:,.2f}")
            st.write("**各持倉與綜合評分**")
            for h in brief.holdings:
                if h.composite_score is not None and h.recommendation:
                    st.caption(f"**{h.symbol}** 投入 ${h.amount:,.0f}，損益 {h.pnl_pct:+.1f}% → 評分 {h.composite_score}/10 **{h.recommendation}**（DCA 倍數 {h.suggested_mult}x）")
                else:
                    st.caption(f"**{h.symbol}** 投入 ${h.amount:,.0f}，損益 {h.pnl_pct:+.1f}% — 未取得訊號")
            st.info(brief.summary_text)
            st.write("**複製以下內容到與 AI 的對話，繼續討論策略**")
            st.code(brief.discussion_prompt, language=None)
            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d")
            save_path = _pkg_root / "docs" / f"策略討論_{date_str}.md"
            if st.button("儲存摘要到檔案（可在 Cursor 用 @ 提到此檔）", key="save_briefing"):
                try:
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    save_path.write_text(brief.discussion_prompt, encoding="utf-8")
                    st.success(f"已儲存至 {save_path.name}，在 Cursor 可 @ 此檔案與 AI 討論。")
                except Exception as e:
                    st.error(str(e))
        elif "strategy_briefing" in st.session_state and st.session_state["strategy_briefing"] is None:
            st.warning("無法產出摘要（請確認已連線 eToro）")

    strategy_type = st.selectbox(
        "選擇策略",
        ["定額定投 (DCA)", "止損檢查", "止盈檢查", "一鍵執行（DCA + 止盈止損）"],
        help="選定後在下方設定參數並執行",
    )

    st.divider()

    if strategy_type == "定額定投 (DCA)":
        dca_cfg = load_position_config()
        max_dca = dca_cfg.get("max_dca_per_trade", 400)
        use_retail_signal = st.checkbox(
            "📊 啟用訊號優化（依市場動作加減碼）",
            value=True,
            help="可選：零售動量、突破、RSI、波動度或綜合（取最保守）",
        )
        dca_signal_type = "retail"
        if use_retail_signal:
            dca_signal_type = st.selectbox(
                "訊號類型",
                ["retail", "breakout", "rsi", "volatility", "composite"],
                format_func=lambda x: {"retail": "零售動量（跌多加碼）", "breakout": "突破（收盤>20日高加碼）", "rsi": "RSI（超賣加碼）", "volatility": "波動度（高波動減量）", "composite": "綜合（四者取最保守）"}[x],
                key="dca_signal_type",
            )
        with st.form("dca_form"):
            st.caption("每月固定日期投入固定金額，不需擇時")
            dca_symbol = st.text_input("標的代碼", "GLD", placeholder="如 GLD, NKE, MSFT")
            dca_amount = st.number_input("金額 (USD)", min_value=100.0, value=min(300.0, max_dca), step=50.0, help=f"依水位設定，建議單筆 ≤ ${max_dca:,.0f}")
            if st.form_submit_button("🟢 執行 DCA 買入"):
                try:
                    if use_retail_signal:
                        result = dca_buy_with_signal(symbol=dca_symbol, amount=dca_amount, client=client, use_signal=True, signal_type=dca_signal_type)
                        st.success(f"定投成功！{result}")
                    else:
                        result = dca_buy(symbol=dca_symbol, amount=dca_amount, client=client)
                        st.success(f"定投成功！{result}")
                except Exception as e:
                    st.error(str(e))

        with st.expander("📊 訊號預覽（輸入標的後可查各訊號）"):
            preview_sym = st.text_input("查詢標的", "GLD", key="signal_preview")
            preview_type = st.selectbox(
                "預覽類型",
                ["retail", "breakout", "rsi", "volatility", "composite"],
                format_func=lambda x: {"retail": "零售動量", "breakout": "突破", "rsi": "RSI", "volatility": "波動度", "composite": "綜合（四者）"}[x],
                key="preview_signal_type",
            )
            if st.button("查詢訊號", key="query_signal"):
                try:
                    _render_signal_preview(preview_sym, preview_type, client)
                except Exception as e:
                    st.error(str(e))

        with st.expander("📋 估值建議（可參考後選擇 DCA 標的）"):
            suggestions = load_valuation_suggestions()
            if suggestions:
                for sym, judge, action in suggestions[:14]:
                    st.write(f"**{sym}** — {judge} → {action}")
                st.caption("先執行 fetch_fundamentals 與 calc_valuation_simple 可更新數據")
            else:
                st.info("請先執行 fetch_fundamentals 取得基本面數據")

    elif strategy_type == "止損檢查":
        st.caption("檢查持倉，虧損達門檻時自動平倉")
        stop_pct = st.number_input("止損門檻 (%)", value=-10.0, step=1.0, help="如 -10 表示虧 10% 平倉")
        if st.button("🔴 執行止損檢查"):
            closed = check_stop_loss(stop_pct, client)
            if closed:
                st.warning(f"已平倉 {len(closed)} 筆持倉")
                for item in closed:
                    st.write(f"  - position_id={item['position']['position_id']}")
            else:
                st.info("無持倉觸及止損")

    elif strategy_type == "止盈檢查":
        st.caption("檢查持倉，獲利達門檻時自動平倉")
        profit_pct = st.number_input("止盈門檻 (%)", value=20.0, step=1.0, help="如 20 表示賺 20% 平倉")
        if st.button("🟢 執行止盈檢查"):
            closed = check_take_profit(profit_pct, client)
            if closed:
                st.success(f"已平倉 {len(closed)} 筆持倉")
                for item in closed:
                    st.write(f"  - position_id={item['position']['position_id']}")
            else:
                st.info("無持倉觸及止盈")

    elif strategy_type == "一鍵執行（DCA + 止盈止損）":
        batch_cfg = load_position_config()
        batch_max = batch_cfg.get("max_dca_per_trade", 400)
        batch_use_signal = st.checkbox("📊 一鍵執行時啟用訊號優化", value=True, key="batch_signal")
        batch_signal_type = "retail"
        if batch_use_signal:
            batch_signal_type = st.selectbox(
                "訊號類型",
                ["retail", "breakout", "rsi", "volatility", "composite"],
                format_func=lambda x: {"retail": "零售動量", "breakout": "突破", "rsi": "RSI", "volatility": "波動度", "composite": "綜合（最保守）"}[x],
                key="batch_signal_type",
            )
        st.caption("流程：止損檢查 → 止盈檢查 → DCA 買入（建議每月一次）")

        # 第一步：建立「策略草稿」，不立即下單
        with st.form("batch_form"):
            dca_symbol = st.text_input("DCA 標的", "GLD")
            dca_amount = st.number_input(
                "DCA 金額 (USD)",
                min_value=100.0,
                value=min(300.0, batch_max),
                step=50.0,
                help=f"建議 ≤ ${batch_max:,.0f}",
            )
            stop_pct = st.number_input("止損 (%)", value=-10.0, step=1.0)
            profit_pct = st.number_input("止盈 (%)", value=20.0, step=1.0)

            prepared = st.form_submit_button("▶ 建立策略草稿（不下單）")
            if prepared:
                st.session_state["batch_plan"] = {
                    "symbol": dca_symbol,
                    "amount": float(dca_amount),
                    "stop_pct": float(stop_pct),
                    "profit_pct": float(profit_pct),
                    "use_signal": bool(batch_use_signal),
                    "signal_type": batch_signal_type,
                }
                for k in ("batch_edit_symbol", "batch_edit_amount", "batch_edit_stop", "batch_edit_profit", "batch_edit_signal", "batch_edit_signal_type"):
                    st.session_state.pop(k, None)
                st.success("已建立策略草稿，可在下方修改數值後再確認執行。")

        # 第二步：顯示草稿（可編輯數值），提供「確認後執行」按鈕
        plan = st.session_state.get("batch_plan")
        if plan:
            with st.expander("📝 策略草稿（可修改數值，確認後再執行）", expanded=True):
                st.caption("可直接在下方更改參數，改完再按「✅ 確認執行」。")
                edit_symbol = st.text_input("DCA 標的", value=plan["symbol"], key="batch_edit_symbol")
                edit_amount = st.number_input(
                    "DCA 金額 (USD)",
                    min_value=50.0,
                    value=float(plan["amount"]),
                    step=50.0,
                    key="batch_edit_amount",
                )
                edit_stop = st.number_input("止損 (%)", value=float(plan["stop_pct"]), step=1.0, key="batch_edit_stop")
                edit_profit = st.number_input("止盈 (%)", value=float(plan["profit_pct"]), step=1.0, key="batch_edit_profit")
                edit_signal = st.checkbox("啟用訊號優化", value=bool(plan["use_signal"]), key="batch_edit_signal")
                signal_type_options = ["retail", "breakout", "rsi", "volatility", "composite"]
                default_signal_idx = signal_type_options.index(plan.get("signal_type", "retail")) if plan.get("signal_type") in signal_type_options else 0
                edit_signal_type = st.selectbox(
                    "訊號類型",
                    signal_type_options,
                    index=default_signal_idx,
                    format_func=lambda x: {"retail": "零售動量", "breakout": "突破", "rsi": "RSI", "volatility": "波動度", "composite": "綜合"}[x],
                    key="batch_edit_signal_type",
                )

                if st.button("✅ 確認執行上述策略"):
                    try:
                        closed_sl = check_stop_loss(edit_stop, client)
                        closed_tp = check_take_profit(edit_profit, client)
                        if edit_signal:
                            result = dca_buy_with_signal(
                                symbol=edit_symbol.strip(),
                                amount=edit_amount,
                                client=client,
                                use_signal=True,
                                signal_type=edit_signal_type,
                            )
                        else:
                            result = dca_buy(
                                symbol=edit_symbol.strip(),
                                amount=edit_amount,
                                client=client,
                            )
                        msg = []
                        if closed_sl:
                            msg.append(f"止損平倉 {len(closed_sl)} 筆")
                        if closed_tp:
                            msg.append(f"止盈平倉 {len(closed_tp)} 筆")
                        msg.append(f"DCA 買入 {edit_symbol} ${edit_amount:,.0f} 成功")
                        st.success(" | ".join(msg))
                        st.session_state.pop("batch_plan", None)
                        for k in ("batch_edit_symbol", "batch_edit_amount", "batch_edit_stop", "batch_edit_profit", "batch_edit_signal", "batch_edit_signal_type"):
                            st.session_state.pop(k, None)
                    except Exception as e:
                        st.error(str(e))

        # 策略參考（所有策略類型都可看）
        with st.expander("📚 網上策略參考（可自行對照調整數值）"):
            st.markdown("""
**DCA 定投（eToro / 一般）**
- 每月固定金額、不擇時；單筆建議 $25–$5,000，分散多標的。
- 研究顯示長期 DCA 優於擇時；可依估值微調金額，但避免頻繁改動。

**止盈 / 止損比例（常見參考）**
- **止盈**：20%–25% 獲利了結（如 O'Neil 法則：成長股突破後常漲約 20–25% 再整理）。
- **止損**：虧損 7%–10% 出場，避免單筆虧損擴大。
- **風險報酬比**：止盈距離建議 ≥ 止損的 2 倍（例如止損 10%、止盈 20%）。
- **移動止損**：可考慮 10%–12% 或 15%–20%，依波動與標的調整。

**本程式預設**：止損 -10%、止盈 +20%，可於上方草稿區自行修改後再確認執行。
            """)
            ref_path = _pkg_root / "docs" / "網上策略參考.md"
            if ref_path.exists():
                st.caption(f"完整整理見：docs/{ref_path.name}")


def main():
    st.title("📈 eToro 交易管理")
    st.caption("查詢資產、下單、策略、監控")

    client = init_client()

    if client is None:
        render_key_form()
        st.stop()

    # 側邊欄
    with st.sidebar:
        st.header("導航")
        page = st.radio("", ["投資組合", "交易", "策略", "API 指令"], label_visibility="collapsed")
        st.divider()

        with st.expander("📐 倉位評估水位設定", expanded=False):
            cfg = load_position_config()
            min_pct = st.number_input("最低現金比例 (%)", value=float(cfg.get("min_cash_pct", 20)), min_value=5.0, max_value=80.0, step=1.0, help="低於此比例時暫停 DCA")
            target_pct = st.number_input("目標現金比例 (%)", value=float(cfg.get("target_cash_pct", 30)), min_value=10.0, max_value=90.0, step=1.0, help="高於此比例時可執行 DCA")
            max_dca = st.number_input("單筆 DCA 上限 (USD)", value=float(cfg.get("max_dca_per_trade", 400)), min_value=100.0, step=50.0)
            if st.button("💾 儲存水位設定"):
                new_cfg = {"min_cash_pct": min_pct, "target_cash_pct": target_pct, "max_dca_per_trade": max_dca}
                if save_position_config(new_cfg):
                    st.success("已儲存")
                else:
                    st.error("儲存失敗")
            st.caption("建議：最低 20%、目標 30%（依交易規則）")

        st.divider()
        if st.button("🔄 重新整理"):
            st.rerun()
        st.divider()
        with st.expander("❓ 介面說明"):
            st.markdown("""
            **倉位評估水位**：先設定最低/目標現金%、單筆 DCA 上限，作為策略基準  

            **投資組合**：查看餘額、持倉、現金比例、水位評估  
            **交易**：買入、賣出、平倉  
            **策略**：選擇策略後一鍵執行（DCA、止損、止盈、一鍵執行）  
            **API 指令**：eToro 官方 API 指令對照，每項對應本介面操作或官方文件連結  

            **清除金鑰**：移除已儲存的 API 金鑰，需重新輸入才能連線
            """)
        if "etoro_api_key" in st.session_state:
            st.caption("已使用手動輸入的金鑰 (Real)")
            if st.button("🔒 清除金鑰"):
                for k in ["etoro_api_key", "etoro_user_key"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()

    # 策略總覽（固定顯示）
    render_strategy_overview()

    # 主內容
    positions = render_portfolio(client)

    if page == "投資組合":
        pass  # 已在上方顯示
    elif page == "交易":
        render_trade(client, positions)
    elif page == "策略":
        render_strategy(client)
    elif page == "API 指令":
        render_api_commands()


if __name__ == "__main__":
    main()
