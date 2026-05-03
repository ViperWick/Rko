"""
零售交易行為 vs AI 反向策略 — 簡易模擬

模擬 eToro Alpha Portfolios 的邏輯：
- 散戶：追漲殺跌（漲時買、跌時賣，慢半拍）
- AI：觀察散戶流向，反向或順勢操作
"""
import numpy as np
import pandas as pd
from pathlib import Path

# 可選：有 matplotlib 才畫圖
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "SimHei", "sans-serif"]
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False

# 模擬參數
N_DAYS = 252
N_STOCKS = 5
SEED = 42
np.random.seed(SEED)


def simulate_prices(n_days: int, n_stocks: int) -> pd.DataFrame:
    """模擬股價：隨機漫步 + 輕微趨勢"""
    dates = pd.date_range("2024-01-01", periods=n_days, freq="B")
    returns = np.random.randn(n_days, n_stocks) * 0.02 + 0.0002
    prices = 100 * np.exp(np.cumsum(returns, axis=0))
    return pd.DataFrame(prices, index=dates, columns=[f"股票{i+1}" for i in range(n_stocks)])


def simulate_retail_flow(prices: pd.DataFrame, lag: int = 3) -> pd.DataFrame:
    """
    模擬散戶交易流向（追漲殺跌、慢半拍）
    - 漲了才買 -> 正流向
    - 跌了才賣 -> 負流向
    - lag: 散戶反應延遲天數
    """
    returns = prices.pct_change()
    # 散戶看過去 lag 天的報酬決定買賣：漲了買、跌了賣
    flow = returns.rolling(lag).mean().shift(1)  # 慢一天
    flow = flow.fillna(0)
    return flow


def retail_strategy(prices: pd.DataFrame, flow: pd.DataFrame) -> pd.Series:
    """散戶策略：依流向加減倉，正流向加碼、負流向減碼（追漲殺跌）"""
    weight = flow.rolling(5).mean().fillna(0)
    w_min, w_max = weight.min().min(), weight.max().max()
    if w_max - w_min < 1e-8:
        weight = pd.DataFrame(0.2, index=weight.index, columns=weight.columns)
    else:
        weight = (weight - w_min) / (w_max - w_min)
        weight = weight.fillna(0.2)
    w_sum = weight.shift(1).sum(axis=1).replace(0, 1)
    daily_ret = (prices.pct_change() * weight.shift(1)).sum(axis=1) / w_sum
    daily_ret = daily_ret.fillna(0)
    return (1 + daily_ret).cumprod()


def ai_contrarian_strategy(prices: pd.DataFrame, flow: pd.DataFrame) -> pd.Series:
    """
    AI 反向策略：散戶大買時減碼/避開，散戶大賣時加碼
    簡化：與散戶權重反向
    """
    weight = flow.rolling(5).mean().fillna(0)
    w_min, w_max = weight.min().min(), weight.max().max()
    if w_max - w_min < 1e-8:
        weight = pd.DataFrame(0.2, index=weight.index, columns=weight.columns)
    else:
        weight = (weight - w_min) / (w_max - w_min)
        weight = weight.fillna(0.2)
    ai_weight = (1 - weight).shift(1)
    w_sum = ai_weight.sum(axis=1).replace(0, 1)
    ai_weight = ai_weight.div(w_sum, axis=0).fillna(1 / N_STOCKS)
    daily_ret = (prices.pct_change() * ai_weight).sum(axis=1)
    daily_ret = daily_ret.fillna(0)
    return (1 + daily_ret).cumprod()


def ai_momentum_strategy(prices: pd.DataFrame, flow: pd.DataFrame) -> pd.Series:
    """
    AI 動量策略：順價格勢，忽略散戶流向
    簡化：動量強的多配、動量弱的少配
    """
    ret = prices.pct_change()
    mom = ret.rolling(5).mean().fillna(0)
    weight = (mom - mom.min().min()) / (mom.max().max() - mom.min().min() + 1e-8)
    weight = weight.fillna(0.2)
    w_sum = weight.shift(1).sum(axis=1).replace(0, 1)
    weight = weight.shift(1).div(w_sum, axis=0).fillna(1 / N_STOCKS)
    daily_ret = (prices.pct_change() * weight).sum(axis=1)
    daily_ret = daily_ret.fillna(0)
    return (1 + daily_ret).cumprod()


def buy_and_hold(prices: pd.DataFrame) -> pd.Series:
    """買入持有：等權重"""
    ret = prices.pct_change().mean(axis=1).fillna(0)
    return (1 + ret).cumprod()


def run_simulation():
    print("=" * 50)
    print("零售交易行為 vs AI 策略 — 簡易模擬")
    print("=" * 50)

    prices = simulate_prices(N_DAYS, N_STOCKS)
    flow = simulate_retail_flow(prices)

    # 各策略累積報酬
    bh = buy_and_hold(prices)
    retail = retail_strategy(prices, flow)
    ai_contrarian = ai_contrarian_strategy(prices, flow)
    ai_momentum = ai_momentum_strategy(prices, flow)

    # 績效摘要
    def total_return(s: pd.Series) -> float:
        return (s.iloc[-1] / s.iloc[0] - 1) * 100

    print("\n【累積報酬率】")
    print(f"  買入持有：     {total_return(bh):+.1f}%")
    print(f"  散戶策略：     {total_return(retail):+.1f}%  （追漲殺跌）")
    print(f"  AI 反向：     {total_return(ai_contrarian):+.1f}%  （與散戶反向）")
    print(f"  AI 動量：     {total_return(ai_momentum):+.1f}%  （順價格勢）")

    # 輸出 CSV 供檢視
    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    result = pd.DataFrame({
        "買入持有": bh,
        "散戶策略": retail,
        "AI反向": ai_contrarian,
        "AI動量": ai_momentum,
    })
    result.to_csv(out_dir / "simulate_retail_alpha.csv")
    print(f"\n已輸出：{out_dir / 'simulate_retail_alpha.csv'}")

    if HAS_PLOT:
        fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

        # 上：股價
        axes[0].set_title("模擬股價")
        for c in prices.columns:
            axes[0].plot(prices.index, prices[c], label=c, alpha=0.8)
        axes[0].legend(loc="upper left", fontsize=8)
        axes[0].set_ylabel("價格")
        axes[0].grid(True, alpha=0.3)

        # 下：策略累積報酬
        axes[1].set_title("策略累積報酬（基準=1）")
        axes[1].plot(bh.index, bh, label="買入持有", linewidth=2)
        axes[1].plot(retail.index, retail, label="散戶（追漲殺跌）", linestyle="--")
        axes[1].plot(ai_contrarian.index, ai_contrarian, label="AI 反向", linestyle="-.")
        axes[1].plot(ai_momentum.index, ai_momentum, label="AI 動量", linestyle=":")
        axes[1].legend(loc="upper left", fontsize=8)
        axes[1].set_ylabel("累積報酬")
        axes[1].set_xlabel("日期")
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        plot_path = out_dir / "simulate_retail_alpha.png"
        plt.savefig(plot_path, dpi=120)
        plt.close()
        print(f"已輸出圖表：{plot_path}")

    print("\n說明：散戶模擬為「漲了才買、跌了才賣」，AI 策略嘗試利用此偏誤。")
    print("實際 eToro 使用真實 4,000 萬用戶數據，此為概念演示。")
    return result


if __name__ == "__main__":
    run_simulation()
