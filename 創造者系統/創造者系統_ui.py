# -*- coding: utf-8 -*-
"""
創造者系統 — 簡易介面
執行: streamlit run 創造者系統/創造者系統_ui.py  (從專案根目錄)
或: cd 創造者系統 && streamlit run 創造者系統_ui.py
"""
import sys
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent

import streamlit as st

st.set_page_config(page_title="創造者系統", page_icon="📋", layout="wide")

st.markdown("""
<style>
    .card { background: #f8f9fa; padding: 1rem 1.2rem; border-radius: 10px; margin: 0.5rem 0; border-left: 4px solid #2d5a87; }
    .card h4 { margin: 0 0 0.3rem 0; color: #1e3a5f; }
</style>
""", unsafe_allow_html=True)

def read_md(name: str) -> str:
    p = BASE / f"{name}.md"
    if not p.exists():
        return f"*（尚無 {name} 或檔案不存在）*"
    try:
        return p.read_text(encoding="utf-8")
    except Exception as e:
        return f"讀取失敗: {e}"

# 側邊選單
st.sidebar.title("📋 創造者系統")
st.sidebar.caption("運轉層入口")
page = st.sidebar.radio(
    "選擇頁面",
    ["總覽", "本週創造者", "產出清單", "探索清單", "專案清單", "發現文檔索引"],
    label_visibility="collapsed",
)

# 總覽
if page == "總覽":
    st.title("創造者系統")
    st.caption("每週／每月節奏、四塊積木、收納與專案一覽")
    st.markdown(read_md("README_創造者系統"))
    st.markdown("---")
    # 一鍵收納
    st.subheader("🔧 發現文檔收納")
    st.caption("把 Word / PPT / Excel / TXT 丟進「發現文檔收納」資料夾後，按下方按鈕更新索引。")
    if st.button("執行收納（更新 發現文檔索引.md）"):
        script = BASE / "收納發現文檔.py"
        if script.exists():
            with st.spinner("執行中…"):
                r = subprocess.run(
                    [sys.executable, str(script)],
                    cwd=str(BASE),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
            if r.returncode == 0:
                st.success(r.stdout or "收納完成。")
            else:
                st.warning(r.stdout or "執行完成，請檢查輸出。")
                if r.stderr:
                    st.code(r.stderr)
        else:
            st.error("找不到 收納發現文檔.py")

elif page == "本週創造者":
    st.title("本週創造者")
    st.caption("本週產出、一件 B/C、探索時間（建議週一填、週末勾選）")
    st.markdown(read_md("本週創造者"))

elif page == "產出清單":
    st.title("我的產出清單")
    st.caption("已發布的內容／工具／連結")
    st.markdown(read_md("我的產出清單"))

elif page == "探索清單":
    st.title("探索清單")
    st.caption("想試的點子、工具、主題；每月清一次")
    st.markdown(read_md("探索清單"))

elif page == "專案清單":
    st.title("專案／程式清單")
    st.caption("程式專案收納（如 eToro 交易程式）")
    st.markdown(read_md("專案清單"))

elif page == "發現文檔索引":
    st.title("發現文檔索引")
    st.caption("由收納腳本自動產生；來源為「發現文檔收納」資料夾內的 .docx / .pptx / .xlsx / .txt")
    st.markdown(read_md("發現文檔索引"))
    st.markdown("---")
    if st.button("🔄 立即執行收納並重新整理"):
        script = BASE / "收納發現文檔.py"
        if script.exists():
            with st.spinner("執行中…"):
                subprocess.run([sys.executable, str(script)], cwd=str(BASE), check=True)
            st.success("已更新。請重新選擇左側「發現文檔索引」以重新載入。")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("完整規則見《創造者系統整合手冊》")
