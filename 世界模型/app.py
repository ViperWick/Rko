"""
世界模型 — 三大預測類別 UI（含耦合、預測區間、情境、預警）
科技研發 · 生產製造 · 環境汙染與再生
"""

import os
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from city_model import UnifiedCityModel, SCENARIOS, Alert

# ============ 頁面設定 ============
st.set_page_config(
    page_title="世界模型 · 三大預測類別",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============ 自訂樣式 ============
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');
    .main, .stApp, [data-testid="stAppViewContainer"] { font-family: 'Noto Sans TC', sans-serif; }
    h1, h2, h3 { color: #1a1a2e !important; font-weight: 700 !important; }
    p, span, label, .stMarkdown { color: #1a1a2e !important; }
    .city-header {
        background: linear-gradient(90deg, #0ea5e9 0%, #06b6d4 50%, #10b981 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(14, 165, 233, 0.3);
    }
    .city-header h1 { color: white !important; margin: 0; font-size: 2rem; }
    .city-header p { color: rgba(255,255,255,0.95) !important; }
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] { color: #1a1a2e !important; }
    [data-testid="stCaptionContainer"] { color: #333 !important; }
    div[data-testid="stSidebar"] label, div[data-testid="stSidebar"] p,
    div[data-testid="stSidebar"] h2, div[data-testid="stSidebar"] h3 { color: #1a1a2e !important; }
    .alert-warning { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 0.75rem 1rem; border-radius: 6px; margin: 0.5rem 0; }
    .alert-critical { background: #fee2e2; border-left: 4px solid #ef4444; padding: 0.75rem 1rem; border-radius: 6px; margin: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ============ 側邊欄參數 ============
st.sidebar.markdown("## ⚙️ 預測參數")
st.sidebar.markdown("---")

st.sidebar.markdown("### 🎭 情境模擬")
scenario = st.sidebar.selectbox(
    "選擇預設情境",
    options=list(SCENARIOS.keys()),
    index=0,
    help="基準=自訂參數 | 高研發=強化創新 | 嚴格環保=高再生率 | 供應鏈中斷=產能下降 | 綠色轉型=科技+環境優先",
)

st.sidebar.markdown("### 📊 模擬設定")
sim_time = st.sidebar.slider("模擬時間 (年)", 5, 50, 30, 1)
time_step = st.sidebar.slider("時間步長", 0.01, 0.2, 0.05, 0.01)
random_seed = st.sidebar.number_input("隨機種子", 0, 99999, 42, 1)
show_interval = st.sidebar.checkbox("顯示預測區間 (5%~95%)", value=False, help="需執行 Monte Carlo，較耗時")
if show_interval:
    n_sims = st.sidebar.slider("Monte Carlo 模擬次數", 20, 200, 50, 10)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 類別耦合")
coupling = st.sidebar.slider("耦合強度", 0.0, 0.5, 0.15, 0.05, help="科技↔生產↔環境 的互動強度")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔬 科技研發")
tech_period = st.sidebar.slider("創新週期 (年)", 8, 20, 12, 1)
tech_amplitude = st.sidebar.slider("創新振幅", 5.0, 25.0, 15.0, 0.5)
tech_mean = st.sidebar.slider("研發強度均值", 0.3, 0.9, 0.6, 0.05)

st.sidebar.markdown("### 🏭 生產製造")
prod_period = st.sidebar.slider("產能週期 (年)", 4, 12, 7, 1)
prod_amplitude = st.sidebar.slider("產能振幅", 5.0, 20.0, 10.0, 0.5)
prod_mean = st.sidebar.slider("製造產出均值", 0.5, 0.95, 0.75, 0.05)

st.sidebar.markdown("### 🌿 環境汙染與再生")
env_period = st.sidebar.slider("環境週期 (年)", 6, 15, 10, 1)
env_amplitude = st.sidebar.slider("環境振幅", 4.0, 15.0, 8.0, 0.5)
env_mean = st.sidebar.slider("再生率均值", 0.3, 0.8, 0.5, 0.05)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 AI 影響監控")
enable_ai_monitor = st.sidebar.checkbox("啟用 AI 影響監控（旁觀者視角）", value=False, help="對比「無 AI」與「有 AI」情境，監控 AI 造成的改變")
if enable_ai_monitor:
    ai_tech_effect = st.sidebar.slider("AI 對科技影響", 0.0, 2.0, 1.0, 0.1)
    ai_prod_effect = st.sidebar.slider("AI 對生產影響", 0.0, 2.0, 0.8, 0.1)
    ai_env_effect = st.sidebar.slider("AI 對環境影響", 0.0, 2.0, 0.6, 0.1)
    ai_inflection = st.sidebar.slider("AI 採用拐點 (年)", 3, 20, 10, 1, help="約此時 AI 採用率達 50%")

# ============ 主標題 ============
st.markdown("""
<div class="city-header">
    <h1>📊 世界模型 — 三大預測類別</h1>
    <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">
        科技研發 · 生產製造 · 環境汙染與再生 · 類別耦合 · 預測區間 · 情境模擬 · 預警機制 · AI 影響監控
    </p>
</div>
""", unsafe_allow_html=True)

# 情境說明
if scenario != "基準":
    scenario_desc = {
        "高研發投入": "強化科技創新與研發，製造略降，環境改善加速",
        "嚴格環保法規": "高再生率、低產能，環保優先",
        "供應鏈中斷": "產能與研發下降，環境壓力增加",
        "綠色轉型": "科技與環境雙高，製造轉型",
    }
    st.info(f"**{scenario}**：{scenario_desc.get(scenario, '')}")

# ============ 建立模型並模擬 ============
# 情境會覆蓋均值與耦合；基準情境則使用側邊欄數值
s = SCENARIOS.get(scenario, SCENARIOS["基準"])
use_scenario = scenario != "基準"
city = UnifiedCityModel(
    seed=int(random_seed),
    scenario=scenario,
    coupling_strength=float(s["coupling"]) if use_scenario else float(coupling),
    tech_period=float(tech_period),
    tech_amplitude=float(tech_amplitude),
    tech_mean=float(s["tech_mean"]) if use_scenario else float(tech_mean),
    prod_period=float(prod_period),
    prod_amplitude=float(prod_amplitude),
    prod_mean=float(s["prod_mean"]) if use_scenario else float(prod_mean),
    env_period=float(env_period),
    env_amplitude=float(env_amplitude),
    env_mean=float(s["env_mean"]) if use_scenario else float(env_mean),
)

if show_interval:
    with st.spinner("執行 Monte Carlo 模擬中..."):
        result = city.simulate_monte_carlo(T=float(sim_time), dt=float(time_step), n_sims=n_sims, seed_base=int(random_seed))
    single_result = city.simulate(T=float(sim_time), dt=float(time_step))
else:
    result = city.simulate(T=float(sim_time), dt=float(time_step))
    single_result = result

# ============ AI 影響監控（旁觀者視角） ============
observer_data = None
if enable_ai_monitor:
    with st.spinner("計算 AI 影響中（旁觀者視角）..."):
        observer_data = city.simulate_observer_view(
            T=float(sim_time),
            dt=float(time_step),
            ai_tech_effect=float(ai_tech_effect),
            ai_prod_effect=float(ai_prod_effect),
            ai_env_effect=float(ai_env_effect),
            ai_inflection=float(ai_inflection),
            seed=int(random_seed),
        )

# ============ 預警區 ============
st.markdown("## ⚠️ 預警狀態")
current_t = single_result["time"][-1]
alerts = city.check_alerts(t=current_t)

if alerts:
    for a in alerts:
        cls = "alert-critical" if a.severity == "critical" else "alert-warning"
        st.markdown(f'<div class="{cls}"><b>{a.category} · {a.metric}</b>: {a.message}</div>', unsafe_allow_html=True)
else:
    st.success("✅ 目前無預警，各指標均在正常範圍內。")

# ============ 即時預測狀態 ============
st.markdown("## 📍 即時預測狀態")
summary = city.get_city_summary(t=current_t)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🔬 科技研發")
    st.metric("創新週期指數", f"{summary['tech']['創新週期指數']:.1f}")
    st.metric("研發強度", f"{summary['tech']['研發強度']:.2f}")
    st.caption("創新浪潮 × 研發投入 · 受環境再生正向耦合")

with col2:
    st.markdown("### 🏭 生產製造")
    st.metric("產能週期指數", f"{summary['prod']['產能週期指數']:.1f}")
    st.metric("製造產出", f"{summary['prod']['製造產出']:.2f}")
    st.caption("產能循環 × 製造水平 · 受科技正向、環境負向耦合")

with col3:
    st.markdown("### 🌿 環境汙染與再生")
    st.metric("汙染指數", f"{summary['env']['汙染指數']:.1f}")
    st.metric("再生率", f"{summary['env']['再生率']:.2f}")
    st.caption("汙染波動 × 再生能力 · 受生產負向、科技正向耦合")

# ============ 圖表區 ============
st.markdown("---")
st.markdown("## 📈 預測演進圖表")

colors = {
    "tech_cycle": "#6366f1", "tech_level": "#818cf8",
    "prod_cycle": "#f59e0b", "prod_level": "#fbbf24",
    "env_cycle": "#10b981", "env_level": "#34d399",
}

fig = make_subplots(
    rows=3, cols=1,
    subplot_titles=(
        "科技研發：創新週期 vs 研發強度",
        "生產製造：產能週期 vs 製造產出",
        "環境汙染與再生：汙染指數 vs 再生率",
    ),
    vertical_spacing=0.08,
    row_heights=[0.33, 0.33, 0.34],
)

t = single_result["time"]

# 科技研發
fig.add_trace(go.Scatter(x=t, y=single_result["tech_cycle"], name="創新週期", line=dict(color=colors["tech_cycle"])), row=1, col=1)
fig.add_trace(go.Scatter(x=t, y=single_result["tech_level"], name="研發強度", line=dict(color=colors["tech_level"])), row=1, col=1)
if show_interval and "tech_level_p50" in result:
    fig.add_trace(go.Scatter(x=result["time"], y=result["tech_level_p5"], name="5%", line=dict(dash="dot", color=colors["tech_level"], width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=result["time"], y=result["tech_level_p95"], name="95%", line=dict(dash="dot", color=colors["tech_level"], width=1)), row=1, col=1)

# 生產製造
fig.add_trace(go.Scatter(x=t, y=single_result["prod_cycle"], name="產能週期", line=dict(color=colors["prod_cycle"])), row=2, col=1)
fig.add_trace(go.Scatter(x=t, y=single_result["prod_level"], name="製造產出", line=dict(color=colors["prod_level"])), row=2, col=1)
if show_interval and "prod_level_p50" in result:
    fig.add_trace(go.Scatter(x=result["time"], y=result["prod_level_p5"], name="5%", line=dict(dash="dot", color=colors["prod_level"], width=1)), row=2, col=1)
    fig.add_trace(go.Scatter(x=result["time"], y=result["prod_level_p95"], name="95%", line=dict(dash="dot", color=colors["prod_level"], width=1)), row=2, col=1)

# 環境汙染與再生
fig.add_trace(go.Scatter(x=t, y=single_result["env_cycle"], name="汙染指數", line=dict(color=colors["env_cycle"])), row=3, col=1)
fig.add_trace(go.Scatter(x=t, y=single_result["env_level"], name="再生率", line=dict(color=colors["env_level"])), row=3, col=1)
if show_interval and "env_level_p50" in result:
    fig.add_trace(go.Scatter(x=result["time"], y=result["env_level_p5"], name="5%", line=dict(dash="dot", color=colors["env_level"], width=1)), row=3, col=1)
    fig.add_trace(go.Scatter(x=result["time"], y=result["env_level_p95"], name="95%", line=dict(dash="dot", color=colors["env_level"], width=1)), row=3, col=1)

fig.update_layout(
    height=750,
    template="plotly_white",
    paper_bgcolor="rgba(255,255,255,0)",
    plot_bgcolor="rgba(248,249,250,0.8)",
    font=dict(color="#1a1a2e", size=12),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#1a1a2e")),
    margin=dict(t=80),
)
fig.update_xaxes(title_text="時間 (年)", row=3, col=1, title_font=dict(color="#1a1a2e"), tickfont=dict(color="#1a1a2e"))
for r in [1, 2, 3]:
    fig.update_yaxes(title_text="數值", row=r, col=1, title_font=dict(color="#1a1a2e"), tickfont=dict(color="#1a1a2e"))

st.plotly_chart(fig, use_container_width=True)

# ============ AI 影響監控（旁觀者視角） ============
if enable_ai_monitor and observer_data is not None:
    st.markdown("---")
    st.markdown("## 🤖 AI 影響監控 — 旁觀者視角")
    st.caption("從旁觀者角度監控：AI 對各類別造成的改變量（有 AI − 無 AI）隨時間變化")

    # 即時 AI 影響摘要
    n = len(observer_data["time"]) - 1
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("AI 採用率", f"{observer_data['ai_adoption'][n]:.1%}")
    with col2:
        st.metric("科技 · AI 影響", f"{observer_data['tech_ai_delta'][n]:+.3f}")
    with col3:
        st.metric("生產 · AI 影響", f"{observer_data['prod_ai_delta'][n]:+.3f}")
    with col4:
        st.metric("環境 · AI 影響", f"{observer_data['env_ai_delta'][n]:+.3f}")

    # AI 影響時間序列圖
    fig_ai = make_subplots(
        rows=2, cols=1,
        subplot_titles=("AI 採用率 over time", "AI 造成的變化量（Δ = 有 AI − 無 AI）"),
        vertical_spacing=0.15,
        row_heights=[0.35, 0.65],
    )
    t_obs = observer_data["time"]
    fig_ai.add_trace(
        go.Scatter(x=t_obs, y=observer_data["ai_adoption"], name="AI 採用率", line=dict(color="#8b5cf6")),
        row=1, col=1,
    )
    fig_ai.add_trace(
        go.Scatter(x=t_obs, y=observer_data["tech_ai_delta"], name="科技 Δ", line=dict(color="#6366f1")),
        row=2, col=1,
    )
    fig_ai.add_trace(
        go.Scatter(x=t_obs, y=observer_data["prod_ai_delta"], name="生產 Δ", line=dict(color="#f59e0b")),
        row=2, col=1,
    )
    fig_ai.add_trace(
        go.Scatter(x=t_obs, y=observer_data["env_ai_delta"], name="環境 Δ", line=dict(color="#10b981")),
        row=2, col=1,
    )
    fig_ai.add_hline(y=0, line_dash="dot", line_color="gray", row=2, col=1)
    fig_ai.update_layout(
        height=500,
        template="plotly_white",
        font=dict(color="#1a1a2e"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    fig_ai.update_xaxes(title_text="時間 (年)", row=2, col=1)
    fig_ai.update_yaxes(title_text="採用率", row=1, col=1)
    fig_ai.update_yaxes(title_text="Δ 變化量", row=2, col=1)
    st.plotly_chart(fig_ai, use_container_width=True)

    # 基準 vs 有 AI 對比表
    with st.expander("📋 基準 vs 有 AI 對比數據"):
        df_obs = pd.DataFrame({
            "時間": observer_data["time"],
            "AI採用率": observer_data["ai_adoption"],
            "科技_無AI": observer_data["tech_baseline"],
            "科技_有AI": observer_data["tech_with_ai"],
            "科技_Δ": observer_data["tech_ai_delta"],
            "生產_無AI": observer_data["prod_baseline"],
            "生產_有AI": observer_data["prod_with_ai"],
            "生產_Δ": observer_data["prod_ai_delta"],
            "環境_無AI": observer_data["env_baseline"],
            "環境_有AI": observer_data["env_with_ai"],
            "環境_Δ": observer_data["env_ai_delta"],
        })
        st.dataframe(df_obs.round(4), use_container_width=True, height=250)

# ============ 數據表格 ============
st.markdown("---")
st.markdown("## 📋 模擬數據")

df = pd.DataFrame({
    "時間": single_result["time"],
    "科技_創新週期": single_result["tech_cycle"],
    "科技_研發強度": single_result["tech_level"],
    "生產_產能週期": single_result["prod_cycle"],
    "生產_製造產出": single_result["prod_level"],
    "環境_汙染指數": single_result["env_cycle"],
    "環境_再生率": single_result["env_level"],
})
st.dataframe(df.round(3), use_container_width=True, height=300)

# ============ 頁尾 ============
st.markdown("---")
st.caption("世界模型 · 科技研發 · 生產製造 · 環境汙染與再生 · 類別耦合 · 預測區間 · 情境模擬 · 預警機制 · AI 影響監控")
