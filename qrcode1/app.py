import streamlit as st
from telecom_analysis import TelecomAnalyzer

def main():
    st.set_page_config(page_title="產業分析儀表板", layout="wide")
    st.title("通訊產業分析")
    
    analyzer = TelecomAnalyzer()
    
    # 側邊欄選項
    analysis_period = st.sidebar.selectbox(
        "選擇分析期間",
        ["1個月", "3個月", "6個月", "1年"],
        index=3
    )
    
    period_map = {
        "1個月": "1mo",
        "3個月": "3mo",
        "6個月": "6mo",
        "1年": "1y"
    }
    
    # 獲取分析報告
    report = analyzer.generate_industry_report()
    
    # 顯示產業概況
    st.header("產業概況")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("產業總市值", 
                 f"{sum(report['metrics']['market_cap'].values())/1e9:.2f}十億")
    
    with col2:
        avg_pe = sum(report['metrics']['pe_ratio'].values()) / len(report['metrics']['pe_ratio'])
        st.metric("平均本益比", f"{avg_pe:.2f}")
    
    with col3:
        avg_yield = sum(report['metrics']['dividend_yield'].values()) / len(report['metrics']['dividend_yield'])
        st.metric("平均殖利率", f"{avg_yield*100:.2f}%")
    
    # 顯示股價走勢圖
    st.plotly_chart(report['plot'], use_container_width=True)
    
    # 顯示個股分析
    st.header("個股分析")
    for symbol, name in analyzer.telecom_stocks.items():
        with st.expander(f"{name} ({symbol})"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("市值", f"{report['metrics']['market_cap'][symbol]/1e9:.2f}十億")
                st.metric("本益比", f"{report['metrics']['pe_ratio'][symbol]:.2f}")
            with col2:
                st.metric("殖利率", f"{report['metrics']['dividend_yield'][symbol]*100:.2f}%")

if __name__ == "__main__":
    main() 