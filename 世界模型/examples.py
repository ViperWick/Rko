"""
世界模型應用範例 — 多領域示範
"""

import os
import numpy as np

# 輸出目錄（與本腳本同目錄）
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
import matplotlib.pyplot as plt
from world_model import (
    SpiralParams, spiral_value, spiral_position,
    MeanReversionParams, mean_reversion_path,
    find_pure_nash, IntegratedWorldModel,
    analyze_situation
)

# 設定中文字體（可選）
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False


# ============ 範例 1：經濟景氣循環 ============

def example_economic_cycle():
    """經濟：景氣循環（螺旋）+ 股價（均值回歸）+ 雙寡占（納什）"""
    print("\n" + "="*50)
    print("範例 1：經濟領域")
    print("="*50)

    # 螺旋：約 7-10 年一輪景氣循環，帶輕微成長漂移
    spiral = SpiralParams(period=8, amplitude=10, drift=0.5)
    t = np.linspace(0, 30, 500)
    cycle = [spiral_value(ti, spiral) for ti in t]

    # 均值回歸：股價圍繞合理本益比
    mr = MeanReversionParams(mean=15, speed=0.3, volatility=2)
    np.random.seed(42)
    price_path = mean_reversion_path(12, mr, steps=500, dt=0.06)

    # 納什：兩家公司定價博弈（囚徒困境型）
    # 合作=低價(1,1), 背叛=高價(0,0)各自最優
    payoff_a = np.array([[3, 0], [5, 1]])  # 公司A
    payoff_b = np.array([[3, 5], [0, 1]])  # 公司B
    nash = find_pure_nash(payoff_a, payoff_b)
    print(f"定價博弈納什均衡: {nash} (策略索引)")

    # 繪圖
    fig, axes = plt.subplots(2, 1, figsize=(10, 6))
    axes[0].plot(t, cycle, label='景氣循環指數（螺旋）')
    axes[0].axhline(0, color='gray', linestyle='--', alpha=0.5)
    axes[0].set_ylabel('景氣指數')
    axes[0].legend()
    axes[0].set_title('螺旋週期：經濟景氣')

    axes[1].plot(price_path, label='本益比（均值回歸）')
    axes[1].axhline(15, color='red', linestyle='--', label='長期均值')
    axes[1].set_xlabel('時間')
    axes[1].set_ylabel('本益比')
    axes[1].legend()
    axes[1].set_title('均值回歸：股價/本益比')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'example_economic.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("已儲存 example_economic.png")


# ============ 範例 2：人際關係 ============

def example_relationship():
    """人際：情緒週期（螺旋）+ 親密度（均值回歸）+ 博弈（納什）"""
    print("\n" + "="*50)
    print("範例 2：人際關係")
    print("="*50)

    # 螺旋：情緒有週期，但每輪可能在不同層次
    spiral = SpiralParams(period=28, amplitude=1, drift=0.02)  # 類月週期
    t = np.linspace(0, 100, 300)
    mood = [spiral_value(ti, spiral) for ti in t]

    # 均值回歸：親密度圍繞某個自然水平
    mr = MeanReversionParams(mean=0.6, speed=0.2, volatility=0.1)
    np.random.seed(123)
    intimacy = mean_reversion_path(0.5, mr, steps=300, dt=0.33)

    # 納什：兩人是否付出（類似信任博弈）
    # 都付出=雙贏, 一方背叛=另一方受損
    payoff_a = np.array([[2, -1], [3, 0]])
    payoff_b = np.array([[2, 3], [-1, 0]])
    nash = find_pure_nash(payoff_a, payoff_b)
    print(f"付出博弈納什均衡: {nash}")

    analysis = analyze_situation(has_cycle=True, has_equilibrium=True, has_players=True)
    print("分析建議:", analysis["recommendation"])


# ============ 範例 3：技術採用 ============

def example_tech_adoption():
    """科技：創新浪潮（螺旋）+ 採用率（均值回歸）+ 平台競爭（納什）"""
    print("\n" + "="*50)
    print("範例 3：技術採用")
    print("="*50)

    # 螺旋：技術成熟度曲線，每波技術有週期
    spiral = SpiralParams(period=15, amplitude=20, drift=3)
    t = np.linspace(0, 50, 400)
    hype = [spiral_value(ti, spiral) for ti in t]

    # 均值回歸：市場佔有率趨向穩定
    mr = MeanReversionParams(mean=0.5, speed=0.15, volatility=0.08)
    np.random.seed(99)
    share = mean_reversion_path(0.2, mr, steps=400, dt=0.125)

    # 納什：兩平台選擇補貼或收費
    payoff_a = np.array([[1, 2], [2, 0]])
    payoff_b = np.array([[1, 2], [2, 0]])
    nash = find_pure_nash(payoff_a, payoff_b)
    print(f"平台策略納什均衡: {nash}")


# ============ 範例 4：整合模型模擬 ============

def example_integrated():
    """完整整合：三模型同時運作"""
    print("\n" + "="*50)
    print("範例 4：整合世界模型模擬")
    print("="*50)

    spiral = SpiralParams(period=5, amplitude=2, drift=0.1)
    mr = MeanReversionParams(mean=10, speed=0.5, volatility=0.5)
    payoff_a = np.array([[2, 0], [0, 1]])
    payoff_b = np.array([[2, 0], [0, 1]])

    model = IntegratedWorldModel(spiral, mr, payoff_a, payoff_b)
    result = model.simulate(T=20, dt=0.05)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(result['time'], result['spiral'], label='螺旋週期')
    ax.plot(result['time'], result['mean_reversion'], label='均值回歸變量')
    ax.axhline(10, color='gray', linestyle='--', alpha=0.5, label='長期均值')
    ax.set_xlabel('時間')
    ax.set_ylabel('數值')
    ax.legend()
    ax.set_title('整合世界模型：螺旋 + 均值回歸')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'example_integrated.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("已儲存 example_integrated.png")


# ============ 範例 5：通用分析工具 ============

def example_analyze_anything():
    """對任意情境進行分析"""
    print("\n" + "="*50)
    print("範例 5：通用情境分析")
    print("="*50)

    scenarios = [
        ("股市漲跌", True, True, False),
        ("國際貿易談判", False, True, True),
        ("季節性銷售", True, True, False),
        ("兩國軍備競賽", False, False, True),
        ("個人習慣養成", True, True, False),
    ]

    for name, cycle, eq, players in scenarios:
        r = analyze_situation(has_cycle=cycle, has_equilibrium=eq, has_players=players)
        print(f"\n【{name}】")
        print("  建議:", r["recommendation"])


# ============ 主程式 ============

if __name__ == "__main__":
    print("\n" + "#"*50)
    print("# 螺旋週期 × 均值回歸 × 納什均衡 — 世界模型範例")
    print("#"*50)

    example_economic_cycle()
    example_relationship()
    example_tech_adoption()
    example_integrated()
    example_analyze_anything()

    print("\n" + "#"*50)
    print("所有範例執行完成！")
    print("#"*50)
