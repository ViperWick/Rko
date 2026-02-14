"""
螺旋週期 × 均值回歸 × 納什均衡 — 通用世界模型
Universal World Model: Spiral Cycle + Mean Reversion + Nash Equilibrium
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass


# ============ 1. 螺旋週期 (Spiral Cycle) ============

@dataclass
class SpiralParams:
    """螺旋週期參數"""
    period: float          # 基礎週期長度
    amplitude: float       # 振幅
    drift: float           # 每圈漂移（螺旋的「爬升」速度）
    phase: float = 0       # 初始相位


def spiral_value(t: float, params: SpiralParams) -> float:
    """
    計算螺旋週期在時間 t 的值
    螺旋 = 週期波動 + 線性漂移（每圈不同高度）
    """
    cycle = np.sin(2 * np.pi * t / params.period + params.phase)
    drift_component = params.drift * (t / params.period)
    return params.amplitude * cycle + drift_component


def spiral_position(t: float, params: SpiralParams) -> Tuple[float, float]:
    """
    螺旋在 2D 平面的位置 (x, y)
    x = 半徑 * cos(角度), y = 半徑 * sin(角度)
    半徑隨時間增加 = 螺旋
    """
    angle = 2 * np.pi * t / params.period + params.phase
    radius = params.amplitude + params.drift * t
    x = radius * np.cos(angle)
    y = radius * np.sin(angle)
    return (x, y)


# ============ 2. 均值回歸 (Mean Reversion) ============

@dataclass
class MeanReversionParams:
    """均值回歸參數（Ornstein-Uhlenbeck 型）"""
    mean: float            # 長期均值
    speed: float           # 回歸速度 (越大回歸越快)
    volatility: float      # 波動率


def mean_reversion_step(
    current: float,
    params: MeanReversionParams,
    dt: float = 0.01,
    noise: Optional[float] = None
) -> float:
    """
    均值回歸單步更新
    dX = speed * (mean - X) * dt + volatility * dW
    """
    drift = params.speed * (params.mean - current) * dt
    if noise is None:
        noise = np.random.normal(0, 1)
    diffusion = params.volatility * np.sqrt(dt) * noise
    return current + drift + diffusion


def mean_reversion_path(
    initial: float,
    params: MeanReversionParams,
    steps: int = 1000,
    dt: float = 0.01
) -> np.ndarray:
    """生成均值回歸路徑"""
    path = np.zeros(steps + 1)
    path[0] = initial
    for i in range(steps):
        path[i + 1] = mean_reversion_step(path[i], params, dt)
    return path


# ============ 3. 納什均衡 (Nash Equilibrium) ============

def find_pure_nash(payoff_a: np.ndarray, payoff_b: np.ndarray) -> List[Tuple[int, int]]:
    """
    尋找純策略納什均衡
    payoff_a[i,j] = 玩家A在(i,j)策略組合下的報酬
    payoff_b[i,j] = 玩家B在(i,j)策略組合下的報酬
    返回所有純策略納什均衡的 (row, col) 索引
    """
    n_rows, n_cols = payoff_a.shape
    equilibria = []

    for i in range(n_rows):
        for j in range(n_cols):
            # A 在給定 B 選 j 時，選 i 是否最優
            a_best = all(payoff_a[i, j] >= payoff_a[k, j] for k in range(n_rows))
            # B 在給定 A 選 i 時，選 j 是否最優
            b_best = all(payoff_b[i, j] >= payoff_b[i, k] for k in range(n_cols))
            if a_best and b_best:
                equilibria.append((i, j))

    return equilibria


def best_response(payoff: np.ndarray, opponent_strategy: np.ndarray, player: str = 'row') -> np.ndarray:
    """
    計算對對手策略的最佳回應（混合策略）
    opponent_strategy: 對手的混合策略機率分佈
    """
    if player == 'row':
        # 我們是行玩家，對手是列
        expected = payoff @ opponent_strategy
    else:
        expected = opponent_strategy @ payoff
    best = np.argmax(expected)
    br = np.zeros_like(opponent_strategy)
    br[best] = 1.0
    return br


# ============ 4. 整合世界模型 ============

@dataclass
class WorldModelState:
    """世界模型狀態"""
    time: float
    spiral_value: float
    mean_reversion_value: float
    nash_equilibria: List[Tuple[int, int]]


class IntegratedWorldModel:
    """
    整合模型：在螺旋週期的時間軸上，
    均值回歸變量圍繞均衡波動，
    多方博弈可能處於納什均衡
    """

    def __init__(
        self,
        spiral_params: SpiralParams,
        mean_reversion_params: MeanReversionParams,
        payoff_a: Optional[np.ndarray] = None,
        payoff_b: Optional[np.ndarray] = None,
    ):
        self.spiral = spiral_params
        self.mean_reversion = mean_reversion_params
        self.payoff_a = payoff_a
        self.payoff_b = payoff_b
        self._mr_value = mean_reversion_params.mean  # 當前均值回歸狀態

    def step(self, t: float, dt: float = 0.01) -> WorldModelState:
        """推進一個時間步"""
        # 螺旋週期
        spiral_val = spiral_value(t, self.spiral)

        # 均值回歸（可選：讓均值受螺旋調制）
        modulated_mean = self.mean_reversion.mean + 0.1 * spiral_val  # 輕微耦合
        params = MeanReversionParams(
            mean=modulated_mean,
            speed=self.mean_reversion.speed,
            volatility=self.mean_reversion.volatility
        )
        self._mr_value = mean_reversion_step(self._mr_value, params, dt)

        # 納什均衡（靜態，不隨時間變）
        nash = []
        if self.payoff_a is not None and self.payoff_b is not None:
            nash = find_pure_nash(self.payoff_a, self.payoff_b)

        return WorldModelState(
            time=t,
            spiral_value=spiral_val,
            mean_reversion_value=self._mr_value,
            nash_equilibria=nash
        )

    def simulate(self, T: float, dt: float = 0.01) -> Dict[str, np.ndarray]:
        """模擬完整時間序列"""
        steps = int(T / dt)
        times = np.zeros(steps + 1)
        spiral_vals = np.zeros(steps + 1)
        mr_vals = np.zeros(steps + 1)

        self._mr_value = self.mean_reversion.mean
        for i in range(steps + 1):
            t = i * dt
            state = self.step(t, dt)
            times[i] = state.time
            spiral_vals[i] = state.spiral_value
            mr_vals[i] = state.mean_reversion_value

        return {
            'time': times,
            'spiral': spiral_vals,
            'mean_reversion': mr_vals,
        }


# ============ 5. 便捷分析函數 ============

def analyze_situation(
    has_cycle: bool = True,
    has_equilibrium: bool = True,
    has_players: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    情境分析：根據現象特徵推薦使用哪個子模型
    """
    recommendation = []
    if has_cycle:
        recommendation.append("螺旋週期：識別週期長度與演進方向")
    if has_equilibrium:
        recommendation.append("均值回歸：估計長期均值與回歸速度")
    if has_players:
        recommendation.append("納什均衡：建立報酬矩陣，尋找穩定策略組合")

    return {
        "recommendation": recommendation,
        "model_priority": "spiral" if has_cycle else ("mean_reversion" if has_equilibrium else "nash"),
        **kwargs
    }
