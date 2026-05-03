# -*- coding: utf-8 -*-
"""
eToro 交易程式 — 簡易展示頁（不需 API 金鑰，給別人看介面與功能）
執行: streamlit run etoro_trading/ui/app_ui_demo.py  (從專案根目錄)
"""
import sys
from pathlib import Path

_pkg_root = Path(__file__).resolve().parent.parent
_repo_root = _pkg_root.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

import json
import streamlit as st

CONFIG_DIR = _pkg_root / "data"
STRATEGY_CONFIG_FILE = CONFIG_DIR / "strategy_config.json"
API_COMMANDS_FILE = CONFIG_DIR / "api_commands.json"
PPT_IMAGES = Path(__file__).resolve().parent / "ppt_images"


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


st.set_page_config(page_title="eToro 交易程式 — 展示", page_icon="📈", layout="wide")

st.markdown("""
<style>
    .demo-banner { background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); padding: 1rem 1.5rem; border-radius: 12px; color: white; margin-bottom: 1.5rem; }
    .demo-banner p { margin: 0.3rem 0; }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="demo-banner"><strong>📌 簡易展示模式</strong><p>此頁面不需 eToro API 金鑰，僅展示介面與功能說明。要使用完整功能（查資產、下單等），請執行 '
    '<code>streamlit run etoro_trading/ui/app_ui.py</code> 並設定 API 金鑰。</p></div>',
    unsafe_allow_html=True,
)

st.title("eToro 交易程式")
st.caption("透過 eToro API 管理資產：查詢、下單、策略、監控")

# 功能總覽
with st.expander("📋 功能總覽", expanded=True):
    st.markdown("""
    | 功能 | 說明 |
    |------|------|
    | **查詢資產** | 餘額、持倉、PnL、訂單 |
    | **自動下單** | 買入、賣出、平倉 |
    | **簡單策略** | 定額定投、止盈止損、60 日均線過濾 |
    | **監控持倉** | 定時檢查、自動止盈止損 |
    """)

# 策略總覽（從 strategy_config.json）
cfg = load_json(STRATEGY_CONFIG_FILE)
if cfg:
    st.subheader(f"📋 {cfg.get('title', '策略總覽')}")
    st.caption(f"更新：{cfg.get('updated_at', '')}")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**資產動作**")
        for item in cfg.get("asset_actions", []):
            emoji = "🟢" if "加倉" in item.get("action", "") else "🔴" if "減" in item.get("action", "") else "⏸"
            st.write(f"{emoji} **{item['asset']}**：{item['action']} — {item['desc']}")
    with col2:
        st.markdown("**賣出規則**")
        for item in cfg.get("sell_rules", []):
            st.write(f"• {item['condition']} → {item['action']}")
    with st.expander("📊 ETF 買入清單（順勢）", expanded=True):
        for e in cfg.get("etf_buy_list", []):
            st.write(f"**{e['symbol']}** {e['weight']} | {e['role']} | 單筆 {e['amount']}")
    with st.expander("⚡ 槓桿 ETF（買跌）"):
        for e in cfg.get("leverage_etf", []):
            st.write(f"**{e['symbol']}** | 單筆 {e['amount']} | {e['trigger']}")
    st.markdown("---")

# API 指令對照（精簡）
api_data = load_json(API_COMMANDS_FILE)
if api_data:
    st.subheader("🔗 eToro API 與本介面對應")
    st.caption(api_data.get("description", ""))
    for cmd in api_data.get("commands", [])[:6]:
        st.write(f"• **{cmd.get('name', '')}** — {cmd.get('ui_action', '')}")
    st.markdown("---")

# UI 截圖預覽
st.subheader("📸 介面預覽")
if PPT_IMAGES.is_dir():
    images = [
        ("策略總覽", "etoro_ui_strategy_overview.png"),
        ("投資組合", "etoro_ui_portfolio.png"),
        ("交易介面", "etoro_ui_trading.png"),
    ]
    for title, fname in images:
        p = PPT_IMAGES / fname
        if p.exists():
            st.markdown(f"**{title}**")
            st.image(str(p), use_container_width=True)
            st.caption("")
else:
    st.info("介面截圖位於 ui/ppt_images/，可自行加入專案後在此顯示。")

st.markdown("---")
st.caption(
    "完整功能請執行：`streamlit run etoro_trading/ui/app_ui.py` 並在 eToro 取得 API 金鑰。本程式僅供學習與個人使用，投資有風險。"
)
